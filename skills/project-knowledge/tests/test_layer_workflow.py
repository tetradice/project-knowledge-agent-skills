"""固定配置、情報保持、切替失敗時の復旧を実ファイルで検証する。"""

import json
import shutil
import sys
import subprocess
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import layer_workflow as workflow
from project_config import ConfigError, load_config, select_layer


def save_plan(path: Path, data: dict) -> Path:
    """テスト用の固定JSON入力を用意する。"""
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def layer(identifier: str, **kwargs) -> dict:
    """用途が重ならないレイヤー定義を返す。"""
    return {"id": identifier, "name": identifier.title(), "description": f"Store {identifier}; exclude other topics", **kwargs}


def page(path: Path, *, reference: bool = False, sources: list | None = None, body: str = "Claim.") -> None:
    """provenanceを持つConceptまたはReferenceを配置する。"""
    metadata = {"type": "Reference" if reference else "Concept", "status": "stable",
                "generated": {"by": "project-knowledge/3.1.0", "at": "2026-09-15T00:00:00Z"},
                "verified": {"by": "human:test", "at": "2026-09-15T00:00:00Z"}, "sources": sources or []}
    if reference:
        metadata["pk_source_type"] = "reference-document"
    else:
        metadata.update(pk_category="extracted", pk_derivation="direct")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("---\n" + yaml.safe_dump(metadata, sort_keys=False) + "---\n\n" + body + "\n", encoding="utf-8")


def source_project(tmp_path: Path) -> tuple[Path, Path]:
    """通常initと同じテンプレートから分割元を構築する。"""
    root = tmp_path / "project"
    root.mkdir()
    config_text, config = workflow.definitions(root, {"layers": [layer("default")], "write_target": "default"})
    for relative, data in workflow.skeleton(root, config["layers"][0]).items():
        workflow.write_bytes(root / relative, data)
    (root / "project-knowledge.yaml").write_text(config_text, encoding="utf-8")
    docs = root / "project-knowledge" / "docs"
    page(docs / "product.md")
    page(docs / "dev" / "run.md", sources=[{"resource": "references/shared.md", "pk_source_type": "reference-document"},
                                               {"resource": "../../app.txt", "pk_source_type": "project-artifact"}],
         body="Run claim. [Evidence](../references/shared.md#proof)")
    page(docs / "references" / "shared.md", reference=True, body="# Proof\nRaw provenance.")
    (root / "app.txt").write_text("artifact", encoding="utf-8")
    updates = {}
    workflow.rebuild_indexes(root, docs, updates)
    for relative, data in updates.items():
        workflow.write_bytes(root / relative, data)
    return root, docs


def split_plan(tmp_path: Path) -> Path:
    """残留Conceptと共有Referenceを含む配置表を固定する。"""
    return save_plan(tmp_path / "split.json", {
        "source_layer": "default", "layers": [layer("dev")], "reference_policy_checked": True,
        "placements": [
            {"source": "product.md", "layer": "default", "path": "product.md", "reason": "product", "references": []},
            {"source": "dev/run.md", "layer": "dev", "path": "operations/run.md", "reason": "operations", "references": ["references/shared.md"]},
            {"source": "references/shared.md", "layer": "default", "path": "references/shared.md", "reason": "shared", "references": []},
            {"source": "references/shared.md", "layer": "dev", "path": "references/shared.md", "reason": "shared", "references": []},
        ]})


def test_empty_multilayer_and_readonly_registration(tmp_path: Path) -> None:
    """全件準備後に読取り専用も登録し、明示書込み選択を守る。"""
    root = tmp_path / "project"
    definition = save_plan(tmp_path / "layers.json", {"layers": [layer("product", access="read-only"), layer("dev")]})
    workflow.initialize(root, definition, prepare=True)
    assert not (root / "project-knowledge.yaml").exists()
    workflow.initialize(root, definition, empty=True)
    config = load_config(root)
    assert config["write_target"] is None
    assert select_layer(config, "dev", write=True)["id"] == "dev"
    with pytest.raises(ConfigError, match="read-only"):
        select_layer(config, "product", write=True)
    before = workflow.inventory(root, config)
    workflow.initialize(root, definition, empty=True)
    assert workflow.inventory(root, config) == before


def test_normal_initialization_requires_fixed_content_plan(tmp_path: Path) -> None:
    """骨組みだけの通常完了を防ぎ、生成済み本文を再開で保持する。"""
    root = tmp_path / "project"
    definition = save_plan(tmp_path / "layers.json", {"layers": [layer("product"), layer("dev")]})
    workflow.initialize(root, definition, prepare=True)
    docs = root / "project-knowledge-product" / "docs"
    page(docs / "feature.md")
    index = docs / "index.md"
    index.write_text(index.read_text(encoding="utf-8") + "\n- [Feature](feature.md)\n", encoding="utf-8")
    workflow.initialize(root, definition, prepare=True)
    plan = save_plan(tmp_path / "collection.json", {"placements": [
        {"source": "feature from README", "layer": "product", "path": "feature.md", "reason": "user feature", "references": []}],
        "empty_reasons": {"dev": "No supported operational facts"}})
    workflow.initialize(root, definition, plan_path=plan)
    assert (docs / "feature.md").exists()
    assert len(load_config(root)["layers"]) == 2


def test_split_preserves_claim_metadata_sources_and_shared_reference(tmp_path: Path) -> None:
    """移動後も本文・verified・根拠実体を保持し、再適用を冪等にする。"""
    root, docs = source_project(tmp_path)
    before = workflow.validator.split_frontmatter((docs / "dev/run.md").read_text(encoding="utf-8"))[0]
    reference = (docs / "references/shared.md").read_bytes()
    original_config = (root / "project-knowledge.yaml").read_bytes()
    workflow.prepare_split(root, split_plan(tmp_path))
    assert (docs / "dev/run.md").exists()
    assert (root / "project-knowledge.yaml").read_bytes() == original_config
    workflow.apply_split(root)
    moved = root / "project-knowledge-dev/docs/operations/run.md"
    metadata, body, _ = workflow.validator.split_frontmatter(moved.read_text(encoding="utf-8"))
    assert metadata["verified"] == before["verified"]
    assert metadata["generated"] == before["generated"]
    assert "Run claim." in body
    assert metadata["sources"][0]["resource"] == "references/shared.md"
    assert metadata["sources"][1]["resource"] == "../../app.txt"
    assert (root / "project-knowledge-dev/docs/references/shared.md").read_bytes() == reference
    assert (docs / "references/shared.md").read_bytes() == reference
    assert not (docs / "dev/run.md").exists()
    config = load_config(root)
    assert config["write_target"] == "default"
    before = workflow.inventory(root, config)
    workflow.apply_split(root)
    assert workflow.inventory(root, config) == before


def test_split_supports_external_source_and_destination_layers(tmp_path: Path) -> None:
    """外部レイヤー間でも候補、切替、登録を同じ操作記録で完了する。"""
    root, _ = source_project(tmp_path)
    source = tmp_path / "source-knowledge"
    destination = tmp_path / "destination-knowledge"
    shutil.move(str(root / "project-knowledge"), source)
    (source / "app.txt").write_bytes((root / "app.txt").read_bytes())
    config = root / "project-knowledge.yaml"
    config.write_text(config.read_text(encoding="utf-8").replace("./project-knowledge", "../source-knowledge"), encoding="utf-8")
    plan_path = split_plan(tmp_path)
    plan = json.loads(plan_path.read_text())
    plan["layers"][0]["path"] = "../destination-knowledge"
    save_plan(plan_path, plan)
    workflow.prepare_split(root, plan_path)
    workflow.apply_split(root)
    assert (destination / "docs/operations/run.md").is_file()
    assert not (source / "docs/dev/run.md").exists()
    assert [Path(item["resolved_path"]) for item in load_config(root)["layers"]] == [source.resolve(), destination.resolve()]


def test_failed_switch_restores_untracked_files_and_can_resume(tmp_path: Path, monkeypatch) -> None:
    """設定公開の失敗でbytesを復旧し、同じ候補から再適用できる。"""
    root, docs = source_project(tmp_path)
    before = workflow.inventory(root, load_config(root))
    workflow.prepare_split(root, split_plan(tmp_path))
    replace = workflow.replace_file

    def fail_config(path: Path, data: bytes | None) -> None:
        """設定の公開だけを一度失敗させる。"""
        if path == root / "project-knowledge.yaml" and data and b"id: dev" in data:
            raise OSError("injected switch failure")
        replace(path, data)

    monkeypatch.setattr(workflow, "replace_file", fail_config)
    with pytest.raises(OSError, match="injected"):
        workflow.apply_split(root)
    assert workflow.inventory(root, load_config(root)) == before
    assert not (root / workflow.LOCK).exists()
    assert not (root / "project-knowledge-dev").exists()
    monkeypatch.setattr(workflow, "replace_file", replace)
    workflow.apply_split(root)
    assert not (docs / "dev/run.md").exists()


@pytest.mark.parametrize("failure", ["collision", "collision_alias", "readonly", "external", "missing", "policy"])
def test_rejected_split_keeps_originals(tmp_path: Path, failure: str) -> None:
    """衝突・権限・範囲外参照・依存欠落を切替前に止める。"""
    root, docs = source_project(tmp_path)
    path = split_plan(tmp_path)
    plan = json.loads(path.read_text())
    if failure == "collision":
        plan["placements"][3]["path"] = "operations/run.md"
    elif failure == "collision_alias":
        plan["placements"][3]["path"] = "operations/unused/../run.md"
    elif failure == "readonly":
        config = root / "project-knowledge.yaml"
        config.write_text(config.read_text(encoding="utf-8").replace("access: read-write", "access: read-only").replace("write_target: default", "write_target: null"), encoding="utf-8")
    elif failure == "external":
        (root / "README.md").write_text("[Run](project-knowledge/docs/dev/run.md)")
    elif failure == "missing":
        plan["placements"].pop()
    else:
        plan["reference_policy_checked"] = False
    save_plan(path, plan)
    before = (docs / "dev/run.md").read_bytes()
    with pytest.raises(ConfigError):
        workflow.prepare_split(root, path)
    assert (docs / "dev/run.md").read_bytes() == before
    assert not (root / "project-knowledge-dev").exists()


def test_concurrent_input_change_and_lock_block_operations(tmp_path: Path) -> None:
    """候補作成後の追加文書と切替ロックを共通入口で検出する。"""
    root, docs = source_project(tmp_path)
    workflow.prepare_split(root, split_plan(tmp_path))
    page(docs / "new.md")
    with pytest.raises(ConfigError, match="inputs"):
        workflow.apply_split(root)
    (root / workflow.LOCK).write_text(workflow.WORK)
    with pytest.raises(ConfigError, match="in progress"):
        load_config(root)


def test_configuration_comments_and_readonly_new_layer(tmp_path: Path) -> None:
    """既存コメント・権限・明示nullを維持してread-only新規層を公開する。"""
    root, docs = source_project(tmp_path)
    config = root / "project-knowledge.yaml"
    text = config.read_text(encoding="utf-8").replace("layers:\n", "# layer comment\nlayers:\n").replace(
        "write_target: default", "# target comment\nwrite_target: null # manual selection")
    config.write_text(text, encoding="utf-8")
    plan_path = split_plan(tmp_path)
    plan = json.loads(plan_path.read_text())
    plan["layers"][0]["access"] = "read-only"
    save_plan(plan_path, plan)
    workflow.prepare_split(root, plan_path)
    workflow.apply_split(root)
    result = config.read_text(encoding="utf-8")
    assert "# layer comment" in result and "# target comment" in result and "# manual selection" in result
    assert load_config(root)["write_target"] is None
    with pytest.raises(ConfigError, match="read-only"):
        select_layer(load_config(root), "dev", write=True)


def test_retire_source_preserves_history(tmp_path: Path) -> None:
    """明示廃止では全Conceptと元の履歴を指定層へ引き継ぐ。"""
    root, docs = source_project(tmp_path)
    (docs / "log.md").write_text("# Change Log\n\nHistorical decision.\n")
    plan_path = split_plan(tmp_path)
    plan = json.loads(plan_path.read_text())
    plan.update(retire_source=True, history_layer="dev", write_target="dev")
    plan["placements"] = [row for row in plan["placements"] if not (
        row["source"] == "references/shared.md" and row["layer"] == "default")]
    for row in plan["placements"]:
        row["layer"] = "dev"
    save_plan(plan_path, plan)
    workflow.prepare_split(root, plan_path)
    workflow.apply_split(root)
    assert [item["id"] for item in load_config(root)["layers"]] == ["dev"]
    assert "Historical decision." in (root / "project-knowledge-dev/docs/log.md").read_text(encoding="utf-8")
    assert (root / "project-knowledge-dev/docs/product.md").exists()


def test_recovery_after_interruption_preserves_later_edit(tmp_path: Path, monkeypatch) -> None:
    """プロセス中断相当の記録から復旧し、後続編集との競合で停止する。"""
    root, docs = source_project(tmp_path)
    workflow.prepare_split(root, split_plan(tmp_path))
    replace = workflow.replace_file
    recover = workflow.recover

    def interrupt(path: Path, data: bytes | None) -> None:
        """設定公開直前のプロセス中断を模擬する。"""
        if path == root / "project-knowledge.yaml":
            raise OSError("interrupted")
        replace(path, data)

    def no_automatic_recovery(root: Path) -> None:
        """自動復旧も実行されなかった状態を残す。"""
        raise OSError("process stopped")

    monkeypatch.setattr(workflow, "replace_file", interrupt)
    monkeypatch.setattr(workflow, "recover", no_automatic_recovery)
    with pytest.raises(OSError, match="process stopped"):
        workflow.apply_split(root)
    moved = root / "project-knowledge-dev/docs/operations/run.md"
    saved = moved.read_bytes()
    moved.write_text("Later manual edit")
    monkeypatch.setattr(workflow, "replace_file", replace)
    with pytest.raises(ConfigError, match="later edit"):
        recover(root)
    assert moved.read_text() == "Later manual edit"
    assert (root / workflow.LOCK).exists()
    moved.write_bytes(saved)
    recover(root)
    assert (docs / "dev/run.md").exists()
    assert not (root / workflow.LOCK).exists()


@pytest.mark.parametrize("change", ["artifact", "candidate"])
def test_changed_evidence_or_candidate_blocks_switch(tmp_path: Path, change: str) -> None:
    """根拠実体と準備済み候補の改変を適用前に検出する。"""
    root, docs = source_project(tmp_path)
    workflow.prepare_split(root, split_plan(tmp_path))
    path = root / "app.txt" if change == "artifact" else workflow.candidate_path(
        root, workflow.operation_key(root / "project-knowledge-dev/docs/operations/run.md"))
    path.write_text("Changed input")
    with pytest.raises(ConfigError):
        workflow.apply_split(root)
    assert (docs / "dev/run.md").exists()


def test_split_stops_when_reference_not_copied_to_retained_referrer(tmp_path: Path) -> None:
    """残留側が使うReferenceを移動のみで消す計画を拒否する。"""
    root, docs = source_project(tmp_path)
    page(docs / "product.md", sources=[{"resource": "references/shared.md", "pk_source_type": "reference-document"}])
    plan_path = split_plan(tmp_path)
    plan = json.loads(plan_path.read_text())
    plan["placements"] = [row for row in plan["placements"] if not (
        row["source"] == "references/shared.md" and row["layer"] == "default")]
    save_plan(plan_path, plan)
    with pytest.raises(ConfigError, match="accompany"):
        workflow.prepare_split(root, plan_path)


def test_nested_bundle_sources_use_docs_root(tmp_path: Path) -> None:
    """通常validatorも深いConceptのsourceをbundle rootで解決する。"""
    root, docs = source_project(tmp_path)
    findings = []
    metadata, _, _ = workflow.validator.split_frontmatter((docs / "dev/run.md").read_text())
    workflow.validator.check_sources(findings, docs / "dev/run.md", metadata, docs.parent)
    assert findings == []


def test_initialization_rejects_overlap_existing_config_and_missing_plan(tmp_path: Path) -> None:
    """新規パスの重複と不正な既存登録、通常初期化の空完了を拒否する。"""
    root = tmp_path / "project"
    root.mkdir()
    definition = save_plan(tmp_path / "layers.json", {"layers": [layer("product", path="./same"), layer("dev", path="./same/sub")]})
    with pytest.raises(ConfigError):
        workflow.initialize(root, definition, empty=True)
    definition = save_plan(definition, {"layers": [layer("product"), layer("dev")]})
    (root / "project-knowledge.yaml").write_text("broken")
    with pytest.raises(ConfigError, match="registered"):
        workflow.initialize(root, definition, empty=True)
    (root / "project-knowledge.yaml").unlink()
    with pytest.raises(ConfigError, match="empty reason"):
        workflow.initialize(root, definition)
    assert not (root / "project-knowledge.yaml").exists()


def test_cli_initialization_and_split_entrypoints(tmp_path: Path) -> None:
    """公開CLIの引数から準備・登録・分割を最後まで実行できる。"""
    scripts = Path(__file__).resolve().parents[1] / "scripts"
    definition = save_plan(tmp_path / "layers.json", {"layers": [layer("product"), layer("dev")]})
    root = tmp_path / "empty"
    result = subprocess.run([sys.executable, str(scripts / "init_project.py"), str(root),
                             "--layers", str(definition), "--empty"], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    root, docs = source_project(tmp_path)
    plan = split_plan(tmp_path)
    for args in (["--plan", str(plan)], ["--apply"], ["--apply"]):
        result = subprocess.run([sys.executable, str(scripts / "split_project.py"), str(root), *args],
                                capture_output=True, text=True)
        assert result.returncode == 0, result.stderr
    assert not (docs / "dev/run.md").exists()


def test_initialization_resumes_interrupted_skeleton_write(tmp_path: Path, monkeypatch) -> None:
    """骨組み保存直前に中断しても固定定義から不足分だけを補える。"""
    root = tmp_path / "project"
    definition = save_plan(tmp_path / "layers.json", {"layers": [layer("product"), layer("dev")]})
    write = workflow.write_bytes

    def interrupt(path: Path, data: bytes) -> None:
        """未作成のmanifest保存を一度だけ止める。"""
        if path.name == "manifest.yml":
            raise OSError("interrupted skeleton")
        write(path, data)

    monkeypatch.setattr(workflow, "write_bytes", interrupt)
    with pytest.raises(OSError, match="interrupted skeleton"):
        workflow.initialize(root, definition, prepare=True)
    monkeypatch.setattr(workflow, "write_bytes", write)
    workflow.initialize(root, definition, empty=True)
    assert len(load_config(root)["layers"]) == 2


def test_recover_lock_at_start_and_completion_boundaries(tmp_path: Path) -> None:
    """切替前または完了記録直後の中断でも不要な復元なしにロックを解放する。"""
    root, docs = source_project(tmp_path)
    workflow.prepare_split(root, split_plan(tmp_path))
    lock = root / workflow.LOCK
    lock.write_text(workflow.WORK)
    workflow.recover(root)
    assert (docs / "dev/run.md").exists()
    workflow.apply_split(root)
    lock.write_text(workflow.WORK)
    workflow.recover(root)
    assert not lock.exists()
    assert not (docs / "dev/run.md").exists()
    assert len(load_config(root)["layers"]) == 2


def test_legacy_document_relative_sources_migrate_to_docs_root(tmp_path: Path) -> None:
    """旧文書相対sourceを読む互換性を保ち、移動後は正規のdocs基準へ変換する。"""
    root, docs = source_project(tmp_path)
    page(docs / "dev/run.md", sources=[
        {"resource": "../references/shared.md", "pk_source_type": "reference-document"},
        {"resource": "../../../app.txt", "pk_source_type": "project-artifact"}])
    metadata, _, _ = workflow.validator.split_frontmatter((docs / "dev/run.md").read_text())
    findings = []
    workflow.validator.check_sources(findings, docs / "dev/run.md", metadata, docs.parent)
    assert findings == []
    workflow.prepare_split(root, split_plan(tmp_path))
    workflow.apply_split(root)
    metadata, _, _ = workflow.validator.split_frontmatter((root / "project-knowledge-dev/docs/operations/run.md").read_text())
    assert [item["resource"] for item in metadata["sources"]] == ["references/shared.md", "../../app.txt"]
