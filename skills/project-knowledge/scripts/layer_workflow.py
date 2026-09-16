"""確定したレイヤー定義と配置表を適用する。意味の分類は呼出し元が行う。"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import shutil
import time
import uuid
from datetime import date
from pathlib import Path
from urllib.parse import unquote

import yaml

from init_project import TEMPLATES, MANAGED_START, MANAGED_END
from project_config import CONFIG_NAME, ConfigError, load_config, parse_config, select_layer
import validate_knowledge as validator

WORK = ".project-knowledge-operation"
LOCK = ".project-knowledge.lock"
COMMENT = "# この設定ファイルは project-knowledge skill で生成されました。\n"
LAYER_KEYS = ("id", "name", "path", "description", "access", "optional", "auto_select")


def initialize(root: Path, definition_path: Path, *, prepare: bool = False,
               plan_path: Path | None = None, empty: bool = False) -> None:
    """全レイヤーを最終パスで準備し、配置と参照の検査後に登録する。"""
    root.mkdir(parents=True, exist_ok=True)
    if (root / LOCK).exists():
        raise ConfigError("Knowledge operation in progress; recover the interrupted switch first")
    definition = read_json(definition_path)
    config_text, config = definitions(root, definition)
    work = root / WORK
    record_path = work / "record.json"
    if record_path.exists():
        record = read_json(record_path)
        if record["kind"] != "init" or record["definition"] != definition:
            raise ConfigError("another operation or changed layer definition; keep the original definition")
        if record["status"] == "complete":
            assert_snapshot(root, record["completed"])
            print("Initialization already complete")
            return
    else:
        if (root / CONFIG_NAME).exists() or (root / CONFIG_NAME).is_symlink():
            raise ConfigError("project is already registered; use split or explicitly initialize one layer")
        ensure_new_paths(config["layers"])
        if work.exists():
            raise ConfigError(f"unrecognized operation directory: {work}")
        work.mkdir()
        record = {"kind": "init", "definition": definition, "status": "preparing",
                  "created": {}, "baseline": snapshot(root, [root / CONFIG_NAME, root / "AGENTS.md", root / ".gitignore"])}
        save_json(record_path, record)

    # 骨組みは作成済みの内容を記録し、再開時の変更を上書きしない。
    for layer in config["layers"]:
        for key, data in skeleton(root, layer).items():
            path = operation_path(key)
            if path.exists():
                if key not in record["created"]:
                    raise ConfigError(f"unowned initialization file: {display_path(root, path)}")
                continue
            if key in record["created"] and record.get("pending_create") != key:
                raise ConfigError(f"prepared file was removed: {display_path(root, path)}")
            record["created"][key] = digest(data)
            record["pending_create"] = key
            save_json(record_path, record)
            write_bytes(path, data)
            record.pop("pending_create", None)
            save_json(record_path, record)
    if prepare:
        print(f"Prepared {len(config['layers'])} layers; registration pending")
        return
    plan = read_json(plan_path) if plan_path else {"placements": [], "empty_reasons": {}}
    if "plan" in record and (record["plan"] != plan or record["empty"] != empty):
        raise ConfigError("initialization plan changed; resume with the fixed plan")
    validate_initial_plan(root, config, plan, empty)
    record.update(plan=plan, empty=empty)
    save_json(record_path, record)
    findings = inspect_candidates(root, config, {})
    if findings:
        raise ConfigError(f"initialization findings: {findings}")
    updates = managed_files(root, config)
    updates[operation_key(root / CONFIG_NAME)] = config_text.encode("utf-8")
    # 準備後の本文は配置表とともに検査済み。公開前の入力変化も検出する。
    assert_snapshot(root, record["baseline"])
    baseline = inventory(root, config)
    baseline.update(record["baseline"])
    commit_changes(root, record, updates, baseline, config)
    print(f"Initialized {len(config['layers'])} layers")


def prepare_split(root: Path, plan_path: Path) -> None:
    """元を保持して候補と復旧用コピーを作り、適用前検査まで行う。"""
    plan = read_json(plan_path)
    work = root / WORK
    record_path = work / "record.json"
    if record_path.exists():
        record = read_json(record_path)
        if record["kind"] != "split" or record["plan"] != plan:
            raise ConfigError("operation exists; use the saved plan or discard an unapplied candidate explicitly")
        if record["status"] == "complete":
            assert_snapshot(root, record["completed"])
        print(f"Split already {record['status']}; classification was not repeated")
        return
    config = load_config(root)
    source = select_layer(config, plan.get("source_layer"), write=True)
    if not plan.get("source_layer"):
        raise ConfigError("source_layer is required")
    config_text, final_config = definitions(root, plan, existing=config)
    new_layers = [layer for layer in final_config["layers"] if layer["id"] not in {x["id"] for x in config["layers"]}]
    if not new_layers:
        raise ConfigError("split requires new layers")
    ensure_new_paths(new_layers)
    if work.exists():
        raise ConfigError(f"unrecognized operation directory: {work}")
    # 元以外のレイヤーと外部Markdownも読み、書換えを要する参照を漏らさない。
    baseline = inventory(root, config)
    for layer in new_layers:
        baseline[operation_key(Path(layer["resolved_path"]))] = None
    before = inspect_candidates(root, config, {})
    if any(item[2] == "high" for item in before):
        raise ConfigError(f"cannot decide migration with existing structural errors: {before}")
    updates, report = split_candidates(root, config, final_config, source, plan)
    updates.update(managed_files(root, final_config))
    updates[operation_key(root / CONFIG_NAME)] = config_text.encode("utf-8")
    work.mkdir()
    record = {"kind": "split", "plan": plan, "status": "preparing", "baseline": baseline,
              "before_findings": before, "report": report, "updates": {}, "backups": {}}
    # 全入力のbytesを保存し、未追跡文書も復旧可能にする。
    record["inputs"] = {key: encode(operation_path(key).read_bytes()) for key, value in baseline.items() if value is not None}
    save_json(record_path, record)
    store_candidates(root, record, updates)
    after = inspect_candidates(root, final_config, updates)
    new_findings = [item for item in after if item not in before]
    if new_findings:
        record["findings"] = new_findings
        save_json(record_path, record)
        raise ConfigError(f"candidate findings: {new_findings}; source is unchanged")
    assert_snapshot(root, baseline)
    record.update(status="prepared", findings=after, config_text=config_text)
    save_json(record_path, record)
    print(json.dumps({"status": "prepared", "report": report, "existing_findings": before}, ensure_ascii=False))


def apply_split(root: Path) -> None:
    """固定候補を適用し、失敗時は今回の書込みだけを戻す。"""
    record = read_json(root / WORK / "record.json")
    if record["kind"] != "split":
        raise ConfigError("not a split operation")
    if record["status"] == "complete":
        assert_snapshot(root, record["completed"])
        print("Split already complete")
        return
    if record["status"] != "prepared":
        raise ConfigError("candidate is not prepared; recover an interrupted switch first")
    updates = read_candidates(root, record)
    current = load_config(root)
    current_inventory = inventory(root, current)
    expected_inventory = {key: value for key, value in record["baseline"].items() if value is not None}
    if {key: value for key, value in current_inventory.items() if value is not None} != expected_inventory:
        raise ConfigError("project inputs were added, removed or changed; rebuild the candidate")
    config = parse_config(record["config_text"], root / CONFIG_NAME)
    commit_changes(root, record, updates, record["baseline"], config)
    print(json.dumps({"status": "complete", "report": record["report"]}, ensure_ascii=False))


def recover(root: Path) -> None:
    """中断した切替を逆順に復旧し、他者の変更は上書きしない。"""
    record = read_json(root / WORK / "record.json")
    lock = root / LOCK
    if not lock.is_file() or lock.read_text(encoding="utf-8") != WORK:
        raise ConfigError("operation lock does not belong to this journal")
    # 排他取得直後・完了記録直後の中断には、戻すべき書込みがない。
    if record["status"] == "complete":
        assert_snapshot(root, record["completed"])
        for name in ("candidate", "validation"):
            directory = safe_path(root, f"{WORK}/{name}")
            if directory.is_dir():
                shutil.rmtree(directory)
        lock.unlink()
        print("Completed operation confirmed; released its remaining lock")
        return
    if record["status"] in {"prepared", "preparing"} and not record.get("pending"):
        lock.unlink()
        print("Released lock acquired before any switch writes")
        return
    if record["status"] not in {"applying", "recovering"}:
        raise ConfigError("no interrupted switch to recover")
    record["status"] = "recovering"
    save_json(root / WORK / "record.json", record)
    for key in reversed(record.get("pending", [])):
        path = operation_path(key)
        before = record["backups"][key]
        original = decode(before) if before is not None else None
        current = path.read_bytes() if path.is_file() else None
        expected = record["updates"][key]
        if current == original:
            continue
        if (digest(current) if current is not None else None) != expected:
            raise ConfigError(f"recovery conflicts with a later edit: {display_path(root, path)}; lock retained")
        replace_file(path, original)
    for key in sorted(record.get("created_dirs", []), key=lambda x: len(operation_path(x).parts), reverse=True):
        directory = operation_path(key)
        if directory.is_dir() and not any(directory.iterdir()):
            directory.rmdir()
    record["status"] = "prepared" if record["kind"] == "split" else "preparing"
    record["pending"] = []
    save_json(root / WORK / "record.json", record)
    lock.unlink()
    print("Recovered original files; prepared candidates retained")


def definitions(root: Path, data: dict, existing: dict | None = None) -> tuple[str, dict]:
    """新規定義だけに既定値を与え、既存ID・権限・設定コメントを維持する。"""
    new = data.get("layers")
    if not isinstance(new, list) or not new:
        raise ConfigError("layers must contain fixed new layer definitions")
    layers = []
    for item in new:
        if not isinstance(item, dict) or not item.get("id"):
            raise ConfigError("assign and freeze each layer ID before execution")
        layer = dict(item)
        identifier = layer["id"]
        layer.setdefault("path", "./project-knowledge" if identifier == "default" else f"./project-knowledge-{identifier}")
        layer.setdefault("access", "read-write")
        layer.setdefault("optional", False)
        layer.setdefault("auto_select", True)
        if not isinstance(layer.get("description"), str) or not layer["description"].strip():
            raise ConfigError("every new layer needs a storage/exclusion description")
        layers.append(layer)
    old = [] if existing is None else [{key: x[key] for key in LAYER_KEYS} for x in existing["layers"]]
    retire = data.get("retire_source", False)
    if type(retire) is not bool:
        raise ConfigError("retire_source must be boolean")
    if retire:
        old = [x for x in old if x["id"] != data.get("source_layer")]
    target = data.get("write_target", existing["write_target"] if existing else None)
    candidate = {"version": "1.0", "layers": old + layers, "write_target": target}
    text = COMMENT + yaml.safe_dump(candidate, allow_unicode=True, sort_keys=False)
    parsed = parse_config(text, root / CONFIG_NAME)
    if existing:
        # YAMLノードの範囲だけを置換し、元設定のコメントと無関係な値を保持する。
        raw = (root / CONFIG_NAME).read_text(encoding="utf-8")
        node = yaml.compose(raw)
        edits = []
        for key, value in node.value:
            if key.value == "layers":
                if not isinstance(value, yaml.SequenceNode) or not value.value or value.flow_style:
                    raise ConfigError("split requires a nonempty block-style layers list; normalize via config first")
                if retire:
                    for item in value.value:
                        identity = next(v.value for k, v in item.value if k.value == "id")
                        if identity == data["source_layer"]:
                            start = raw.rfind("\n", 0, item.start_mark.index) + 1
                            end = raw.rfind("\n", 0, item.end_mark.index) + 1
                            edits.append((start, end, ""))
                end = value.end_mark.index
                # end_mark は次のroot keyの先頭を指す。
                addition = yaml.safe_dump(layers, allow_unicode=True, sort_keys=False)
                indent = value.start_mark.column
                addition = "".join(" " * indent + line + "\n" for line in addition.splitlines())
                edits.append((end, end, addition))
            if key.value == "write_target":
                rendered = "null" if target is None else json.dumps(target)
                edits.append((value.start_mark.index, value.end_mark.index, rendered))
        if not any(key.value == "write_target" for key, _ in node.value):
            raw += "\nwrite_target: " + ("null" if target is None else json.dumps(target)) + "\n"
        for start, end, replacement in sorted(edits, reverse=True):
            raw = raw[:start] + replacement + raw[end:]
        actual = parse_config(raw, root / CONFIG_NAME)
        if actual != parsed:
            raise ConfigError("comment-preserving config edit did not reproduce the fixed definition")
        text = raw
    return text, parsed


def split_candidates(root: Path, old_config: dict, config: dict, source: dict, plan: dict) -> tuple[dict, list]:
    """全Conceptの一意配置とReference依存の明示配置から候補を作る。"""
    source_docs = Path(source["resolved_path"]) / "docs"
    layers = {x["id"]: x for x in config["layers"]}
    allowed = set(layers) - {x["id"] for x in old_config["layers"]} | {source["id"]}
    rows = plan.get("placements")
    if not isinstance(rows, list):
        raise ConfigError("placements must be a list")
    pages = {p.relative_to(source_docs).as_posix(): p for p in source_docs.rglob("*")
             if p.is_file() and p.name not in {"index.md", "log.md"}}
    mapping: dict[Path, list[tuple[str, Path]]] = {}
    destinations = set()
    report = []
    for row in sorted(rows, key=lambda x: (x["source"], x["layer"], x["path"])):
        if row.get("source") not in pages or row.get("layer") not in allowed or row.get("layer") not in layers:
            raise ConfigError(f"invalid or out-of-scope placement: {row}")
        if not row.get("reason") or not isinstance(row.get("references"), list):
            raise ConfigError("each placement requires reason and references")
        original = pages[row["source"]]
        destination = safe_path(Path(layers[row["layer"]]["resolved_path"]) / "docs", row["path"])
        if destination.name in {"index.md", "log.md"}:
            raise ConfigError("managed pages cannot be placement destinations")
        if destination in destinations:
            raise ConfigError(f"destination collision: {destination}; fix the placement table")
        if row["layer"] == source["id"] and destination != original:
            raise ConfigError("retained source pages must keep their path")
        destinations.add(destination)
        mapping.setdefault(original, []).append((row["layer"], destination))
        report.append(dict(row))
    if set(mapping) != set(pages.values()):
        raise ConfigError("place every source document and asset, including retained files")
    for original, targets in mapping.items():
        if original.suffix.lower() == ".md":
            metadata, _, error = validator.split_frontmatter(original.read_text(encoding="utf-8"))
            if error or not metadata:
                raise ConfigError(f"cannot classify malformed page: {original}")
            if metadata.get("type") != "Reference" and len(targets) != 1:
                raise ConfigError(f"Concept must have exactly one outcome: {original}")
            if metadata.get("type") == "Reference" and len(targets) > 1:
                if not plan.get("reference_policy_checked"):
                    raise ConfigError("confirm shared Reference storage against destination Policies")
                if source["id"] in layers and not any(identifier == source["id"] for identifier, _ in targets):
                    raise ConfigError("shared Reference must retain its original while the source layer remains")
        # 依存Referenceは参照する各レイヤーへ配置する。暗黙のレイヤー間根拠にしない。
        if original.suffix.lower() == ".md":
            for dependency in document_targets(original.read_text(encoding="utf-8"), original, source_docs):
                if dependency not in mapping or dependency.suffix.lower() != ".md":
                    continue
                metadata, _, _ = validator.split_frontmatter(dependency.read_text(encoding="utf-8"))
                if metadata and metadata.get("type") == "Reference":
                    required = {identifier for identifier, _ in targets}
                    available = {identifier for identifier, _ in mapping[dependency]}
                    if not required.issubset(available):
                        raise ConfigError(f"Reference must accompany every referrer: {dependency}")
    updates = {}
    source_policy = (source_docs.parent / "knowledge-policy.md").read_bytes()
    for layer in config["layers"]:
        if layer["id"] in allowed and layer["id"] != source["id"]:
            updates.update(skeleton(root, layer, policy=source_policy))
    # 参照先は最終配置から計算し、一時候補ディレクトリを基準にしない。
    for original, targets in mapping.items():
        for layer_id, destination in targets:
            data = original.read_bytes()
            if original.suffix.lower() == ".md":
                data = rewrite_document(data, original, destination, source_docs,
                                        Path(layers[layer_id]["resolved_path"]) / "docs", mapping, layer_id, layers)
            updates[operation_key(destination)] = data
        if not any(destination == original for _, destination in targets):
            updates[operation_key(original)] = None
    # 元以外の参照元を書き換える必要がある計画は、権限に関係なく範囲外として止める。
    moved = {p for p, targets in mapping.items() if not any(dst == p for _, dst in targets)}
    for path in external_markdown(root, old_config, source_docs):
        base = next((Path(x["resolved_path"]) / "docs" for x in old_config["layers"]
                     if path.is_relative_to(Path(x["resolved_path"]) / "docs")), path.parent)
        if any(target in moved for target in document_targets(path.read_text(encoding="utf-8"), path, base)):
            raise ConfigError(f"external/read-only referrer would require an out-of-scope write: {path}")
    # 履歴の本文を保持し、参照だけは移行後に合わせる。
    old_log = source_docs / "log.md"
    retained = source["id"] in layers
    if retained:
        log = rewrite_document(old_log.read_bytes(), old_log, old_log, source_docs, source_docs,
                               mapping, source["id"], layers)
        updates[operation_key(old_log)] = log
    else:
        history = plan.get("history_layer")
        if history not in layers or history not in allowed:
            raise ConfigError("retiring the source requires a fixed history_layer")
        destination = Path(layers[history]["resolved_path"]) / "docs" / "log.md"
        updates[operation_key(destination)] = rewrite_document(
            old_log.read_bytes(), old_log, destination, source_docs, destination.parent, mapping, history, layers)
        # publish成果物とPolicyを含む旧ディレクトリは履歴保全のため残し、登録だけ解除する。
    for layer in config["layers"]:
        if layer["id"] not in allowed:
            continue
        docs = Path(layer["resolved_path"]) / "docs"
        rebuild_indexes(root, docs, updates)
        key = operation_key(docs / "log.md")
        log = updates.get(key, (docs / "log.md").read_bytes() if (docs / "log.md").exists() else b"# Change Log\n")
        entry = "\n## " + date.today().isoformat() + "\n\nLayer split (" + source["id"] + ")\n\n"
        entry += "\n".join(f"- `{row['source']}` -> `{row['layer']}:{row['path']}`: {row['reason']}" for row in report) + "\n"
        updates[key] = log + entry.encode("utf-8")
        updates[operation_key(docs.parent / "state.yml")] = (TEMPLATES / "state.yml").read_bytes()
        snapshot_path = docs.parent / ".cache" / "source-snapshot.json"
        if snapshot_path.is_file():
            updates[operation_key(snapshot_path)] = None
    # 明示した依存Referenceが同じ移管先で参照可能であることを確認する。
    for row in rows:
        for reference in row["references"]:
            target = safe_path(source_docs, reference)
            if target not in mapping or not any(layer == row["layer"] for layer, _ in mapping[target]):
                raise ConfigError(f"missing dependency placement: {reference} for {row['source']}")
    return updates, report


def rewrite_document(data: bytes, original: Path, destination: Path, old_docs: Path,
                     new_docs: Path, mapping: dict, layer_id: str, layers: dict) -> bytes:
    """本文・metadataを維持し、リンクとsourceのscalarだけを書き換える。"""
    text = data.decode("utf-8")
    newline = "\r\n" if "\r\n" in text else "\n"
    normalized = text.replace("\r\n", "\n")

    def relocate(raw: str, old_base: Path, new_base: Path, *, artifact: bool = False) -> str:
        """URIを保持し、同じ実体または固定された移管先へ相対化する。"""
        if not raw or raw.startswith("#") or validator.is_uri(raw):
            return raw
        value, separator, fragment = raw.partition("#")
        target = (old_base / unquote(value)).resolve()
        if target in mapping and not artifact:
            local = [dst for identifier, dst in mapping[target] if identifier == layer_id]
            if local:
                target = local[0]
            else:
                identifier, target = mapping[target][0]
                if layers[layer_id]["optional"] or layers[identifier]["optional"]:
                    raise ConfigError("cross-layer link requires both layers to be mandatory; retain linked group")
        relative = Path(os.path.relpath(target, new_base)).as_posix()
        return relative + (separator + fragment if separator else "")

    end = normalized.find("\n---\n", 4) if normalized.startswith("---\n") else -1
    header, body = (normalized[:end + 5], normalized[end + 5:]) if end >= 0 else ("", normalized)
    if header:
        yaml_text = normalized[4:end]
        node = yaml.compose(yaml_text)
        metadata = yaml.safe_load(yaml_text)
        edits = []
        for key, value in node.value:
            if key.value != "sources":
                continue
            for index, source in enumerate(value.value):
                for field, scalar in source.value:
                    if field.value == "resource":
                        raw = scalar.value
                        old_base = old_docs
                        if not validator.is_uri(raw):
                            resolved = validator.resolve_source_resource(original, raw, old_docs)
                            if resolved != (old_docs / raw.split("#", 1)[0]).resolve():
                                old_base = original.parent
                        new = relocate(raw, old_base, new_docs,
                                       artifact=metadata["sources"][index].get("pk_source_type") == "project-artifact")
                        if raw != new:
                            edits.append((scalar.start_mark.index, scalar.end_mark.index, json.dumps(new, ensure_ascii=False)))
        for start, stop, value in sorted(edits, reverse=True):
            yaml_text = yaml_text[:start] + value + yaml_text[stop:]
        header = "---\n" + yaml_text + "\n---\n"

    def rewrite_link(match: re.Match) -> str:
        """validatorと共通のinline Markdownリンクを移管先で解決する。"""
        raw = match.group(1)
        return match.group(0).replace("(" + raw + ")", "(" + relocate(raw, original.parent, destination.parent) + ")")

    # reference-styleリンクも定義位置を基準に再計算する。
    body = validator.LINK_PATTERN.sub(rewrite_link, body)
    body = re.sub(r"(?m)^(\s*\[[^\]]+\]:\s*)(\S+)",
                  lambda m: m[1] + relocate(m[2], original.parent, destination.parent), body)
    return (header + body).replace("\n", newline).encode("utf-8")


def inspect_candidates(root: Path, config: dict, updates: dict) -> list:
    """候補の物理パスと最終パスを分離し、形式・参照・到達性を検査する内部入口。"""
    result = []
    temporary = root / WORK / "validation"
    # 通常CLIの登録必須を緩めず、未登録候補だけをこの内部関数で扱う。
    def resolve(path: Path) -> Path:
        """候補ファイルへ写像し、削除候補は存在しないパスに写像する。"""
        key = operation_key(path)
        if key in updates:
            return candidate_path(root, key)
        return path

    if updates:
        for key, data in updates.items():
            if data is not None:
                write_bytes(candidate_path(root, key), data)
            elif candidate_path(root, key).is_file():
                candidate_path(root, key).unlink()
    for layer in config["layers"]:
        final = Path(layer["resolved_path"])
        if layer["optional"] and not final.exists() and not any(operation_path(key).is_relative_to(final) for key in updates):
            continue
        files = virtual_files(root, final, updates)
        structural = []
        # 小さな管理ファイルだけを同じ物理bundleに揃えて既存検査を再利用する。
        check_root = temporary / "bundles" / layer["id"] if updates else final
        if updates:
            # 候補と既存ファイルを同じ仮想bundleへ写し、外部レイヤーも既存validatorで検査する。
            for path in final.rglob("*"):
                if path.is_file() and operation_key(path) not in updates:
                    write_bytes(check_root / path.relative_to(final), path.read_bytes())
            for key, data in updates.items():
                path = operation_path(key)
                if data is not None and path.is_relative_to(final):
                    write_bytes(check_root / path.relative_to(final), data)
        validator.check_manifest(structural, check_root)
        validator.check_knowledge_policy(structural, check_root)
        validator.check_state(structural, check_root)
        docs = final / "docs"
        pages = {path for path in files if path.is_relative_to(docs) and path.suffix.lower() == ".md"}
        graph = {}
        for required in (docs / "index.md", docs / "log.md"):
            if required not in pages:
                result.append((layer["id"], str(required.relative_to(final)), "high", "missing-managed-page"))
        for path in sorted(pages):
            physical = resolve(path)
            text = physical.read_text(encoding="utf-8")
            metadata, body, error = validator.split_frontmatter(text)
            # 形式エラーは最終パス表示へ正規化し、コピー前後で比較可能にする。
            issues = []
            validator.check_reserved(issues, path, docs, metadata, body, error, final)
            if path.name not in {"index.md", "log.md"}:
                validator.check_concept(issues, path, metadata, error, final,
                                        source_root=docs, resolve_target=resolve)
            for issue in issues:
                result.append((layer["id"], path.relative_to(final).as_posix(), issue["severity"], issue["code"]))
            targets = document_targets(text, path, docs, resolve_target=resolve)
            graph[path] = {target for target in targets if target in pages}
            for target in targets:
                if not resolve(target).is_file():
                    result.append((layer["id"], path.relative_to(final).as_posix(), "high", "broken-reference"))
        reached = set()
        pending = [docs / "index.md"]
        while pending:
            path = pending.pop()
            if path in reached:
                continue
            reached.add(path)
            pending.extend(graph.get(path, ()))
        for path in pages - reached - {docs / "log.md"}:
            result.append((layer["id"], path.relative_to(final).as_posix(), "medium", "unreachable"))
        result.extend((layer["id"], item["path"], item["severity"], item["code"]) for item in structural)
    return sorted(set(result))


def commit_changes(root: Path, record: dict, updates: dict, baseline: dict, config: dict) -> None:
    """排他取得後に入力を照合し、write-ahead記録と設定の最終公開で切り替える。"""
    lock = root / LOCK
    with lock.open("x", encoding="utf-8") as stream:
        stream.write(WORK)
    try:
        assert_snapshot(root, baseline)
        if record["kind"] == "split":
            current = inventory(root, load_config(root, _operation=True))
            if {key: value for key, value in current.items() if value is not None} != {
                    key: value for key, value in baseline.items() if value is not None}:
                raise ConfigError("project inputs changed while acquiring the operation lock")
        store_candidates(root, record, updates)
        created_dirs = {operation_key(parent) for key, data in updates.items()
                        if data is not None for parent in operation_path(key).parents
                        if parent != root and not parent.exists()}
        record.update(status="applying", pending=[], created_dirs=sorted(created_dirs))
        save_json(root / WORK / "record.json", record)
        config_key = operation_key(root / CONFIG_NAME)
        order = sorted(key for key in updates if key != config_key) + [config_key]
        for key in order:
            if key not in updates:
                continue
            record["pending"].append(key)
            save_json(root / WORK / "record.json", record)
            replace_file(operation_path(key), updates[key])
        actual = load_config(root, _operation=True)
        if [{key: x[key] for key in LAYER_KEYS} for x in actual["layers"]] != [
                {key: x[key] for key in LAYER_KEYS} for x in config["layers"]] or actual["write_target"] != config["write_target"]:
            raise ConfigError("registered configuration differs from the fixed definition")
        for layer in actual["layers"]:
            if layer["access"] == "read-write" and layer["available"]:
                select_layer(actual, layer["id"], write=True)
        findings = inspect_candidates(root, actual, {})
        if [item for item in findings if list(item) not in record.get("before_findings", []) and item not in record.get("before_findings", [])]:
            raise ConfigError(f"post-switch findings: {findings}")
        completed_record = dict(record, status="complete", completed=inventory(root, actual), pending=[])
        # 成功後は復旧用bytesを破棄し、冪等再実行に必要な指紋と結果だけ残す。
        completed_record.pop("inputs", None)
        completed_record["backups"] = {}
        save_json(root / WORK / "record.json", completed_record)
        record.update(completed_record)
        lock.unlink()
        for name in ("candidate", "validation"):
            directory = safe_path(root, f"{WORK}/{name}")
            if directory.is_dir():
                shutil.rmtree(directory)
    except BaseException:
        if record.get("status") == "applying":
            persisted = read_json(root / WORK / "record.json")
            if persisted["status"] in {"applying", "recovering"}:
                recover(root)
            elif not record.get("pending"):
                lock.unlink()
        elif lock.exists():
            lock.unlink()
        raise


def validate_initial_plan(root: Path, config: dict, plan: dict, empty: bool) -> None:
    """生成済みページと収集候補の一意対応、空レイヤーの理由を確認する。"""
    rows = plan.get("placements", [])
    actual = {}
    for layer in config["layers"]:
        docs = Path(layer["resolved_path"]) / "docs"
        actual[layer["id"]] = {path.relative_to(docs).as_posix() for path in docs.rglob("*.md")
                               if path.name not in {"index.md", "log.md"}}
    if empty and any(actual.values()):
        raise ConfigError("empty initialization contains content pages")
    seen, candidates = set(), set()
    for row in rows:
        key = (row.get("layer"), row.get("path"))
        if key in seen or row.get("source") in candidates or key[0] not in actual or key[1] not in actual[key[0]]:
            raise ConfigError(f"unresolved, duplicate or missing initial placement: {row}")
        if not row.get("source") or not row.get("reason") or not isinstance(row.get("references"), list):
            raise ConfigError("initial placement requires source, reason and references")
        for reference in row["references"]:
            if reference not in actual[key[0]]:
                raise ConfigError(f"initial Reference is missing: {reference}")
        seen.add(key)
        candidates.add(row["source"])
    if seen != {(identifier, page) for identifier, pages in actual.items() for page in pages}:
        raise ConfigError("placement table must cover every generated page")
    for identifier, pages in actual.items():
        if not pages and not empty and not plan.get("empty_reasons", {}).get(identifier):
            raise ConfigError(f"no evidence or explicit empty reason for layer: {identifier}")


def skeleton(root: Path, layer: dict, *, policy: bytes | None = None) -> dict:
    """既存テンプレートと版を使い、レイヤー固有の骨組みを生成する。"""
    directory = Path(layer["resolved_path"])
    names = {"manifest.yml": "manifest.yml", "knowledge-policy.md": "knowledge-policy.md",
             "state.yml": "state.yml", "docs/index.md": "index.md", "docs/log.md": "log.md",
             "docs/references/index.md": "reference-index.md",
             "docs/references/user-statements/index.md": "user-statements-index.md",
             "docs/references/interactions/index.md": "interactions-index.md", ".gitignore": "project.gitignore"}
    files = {operation_key(directory / name): (TEMPLATES / template).read_bytes() for name, template in names.items()}
    index_key = operation_key(directory / "docs/index.md")
    policy_key = operation_key(directory / "knowledge-policy.md")
    files[index_key] = files[index_key].replace(b"{{project_name}}", layer["name"].encode("utf-8"))
    files[policy_key] = (policy if policy is not None else files[policy_key]) + (
        "\n\n## レイヤーの保存範囲\n\n" + layer["description"] + "\n").encode("utf-8")
    return files


def rebuild_indexes(root: Path, docs: Path, updates: dict) -> None:
    """各索引をその子ページへ接続し、全ページをroot indexから到達可能にする。"""
    files = {p for p in virtual_files(root, docs, updates) if p.suffix.lower() == ".md"}
    directories = {docs} | {parent for path in files for parent in path.parents if parent.is_relative_to(docs)}
    for directory in sorted(directories):
        entries = sorted({p for p in files if p.parent == directory and p.name != "index.md"}
                         | {child / "index.md" for child in directories if child.parent == directory})
        text = ('---\nokf_version: "0.2"\n---\n\n' if directory == docs else "")
        text += "# " + ("Knowledge" if directory == docs else directory.name) + "\n\n"
        text += "".join(f"- [{path.relative_to(directory).as_posix()}]({path.relative_to(directory).as_posix()})\n" for path in entries)
        updates[operation_key(directory / "index.md")] = text.encode("utf-8")


def managed_files(root: Path, config: dict) -> dict:
    """管理ブロックを一つに保ち、全レイヤーのlocal stateをignoreする。"""
    result = {}
    agents = (TEMPLATES / "agents-block.md").read_text(encoding="utf-8").strip()
    ignores = [f"/{layer_relative(root, layer)}/{suffix}" for layer in config["layers"]
               if Path(layer["resolved_path"]).is_relative_to(root)
               for suffix in ("state.yml", ".cache/")]
    ignores += [f"/{WORK}/", f"/{LOCK}"]
    for filename, start, end, block in (
        ("AGENTS.md", MANAGED_START, MANAGED_END, agents),
        (".gitignore", "# project-knowledge:start", "# project-knowledge:end",
         "# project-knowledge:start\n" + "\n".join(ignores) + "\n# project-knowledge:end"),
    ):
        path = root / filename
        current = path.read_text(encoding="utf-8") if path.exists() else ""
        if current.count(start) != current.count(end) or current.count(start) > 1:
            raise ConfigError(f"ambiguous managed block in {filename}")
        updated = re.sub(re.escape(start) + r".*?" + re.escape(end), lambda _: block, current, flags=re.DOTALL) if start in current else current.rstrip() + ("\n\n" if current else "") + block + "\n"
        result[operation_key(root / filename)] = updated.encode("utf-8")
    return result


def document_targets(text: str, path: Path, docs: Path, resolve_target=None) -> set[Path]:
    """本文リンクとbundle root相対sourceを同じ依存集合へ集める。"""
    metadata, body, _ = validator.split_frontmatter(text)
    links = validator.LINK_PATTERN.findall(body)
    links += re.findall(r"(?m)^\s*\[[^\]]+\]:\s*(\S+)", body)
    targets = {(path.parent / unquote(value.split("#", 1)[0])).resolve() for value in links
               if value and not value.startswith("#") and not validator.is_uri(value)}
    if metadata and isinstance(metadata.get("sources"), list):
        for source in metadata["sources"]:
            value = source.get("resource") if isinstance(source, dict) else None
            if isinstance(value, str) and value and not validator.is_uri(value):
                targets.add(validator.resolve_source_resource(path, unquote(value), docs, resolve_target))
    return targets


def external_markdown(root: Path, config: dict, source_docs: Path) -> list[Path]:
    """対象外レイヤーとproject内Markdownの参照元を列挙する。"""
    excluded = {".git", WORK, "node_modules", ".venv", ".cache"}
    return sorted(p for p in root.rglob("*.md") if not p.is_relative_to(source_docs)
                  and not excluded.intersection(p.relative_to(root).parts))


def inventory(root: Path, config: dict) -> dict:
    """設定・管理情報・全レイヤー・外部参照元の指紋を採取する。"""
    paths = [root / CONFIG_NAME, root / "AGENTS.md", root / ".gitignore"]
    for layer in config["layers"]:
        directory = Path(layer["resolved_path"])
        paths.extend(p for p in directory.rglob("*") if p.is_file())
    paths.extend(external_markdown(root, config, root / "__no_source__"))
    for path in list(paths):
        if path.suffix.lower() != ".md" or not path.is_file():
            continue
        docs = next((Path(layer["resolved_path"]) / "docs" for layer in config["layers"]
                     if path.is_relative_to(Path(layer["resolved_path"]) / "docs")), path.parent)
        for target in document_targets(path.read_text(encoding="utf-8"), path, docs):
            if target.is_file() and (target.is_relative_to(root) or any(
                    target.is_relative_to(Path(layer["resolved_path"])) for layer in config["layers"])):
                paths.append(target)
    return snapshot(root, paths)


def snapshot(root: Path, paths: list[Path]) -> dict:
    """登録済み対象のbytesに対する指紋を絶対パスで記録する。"""
    result = {}
    for path in sorted(set(paths)):
        key = operation_key(path)
        result[key] = digest(path.read_bytes()) if path.is_file() else None
    return result


def assert_snapshot(root: Path, baseline: dict) -> None:
    """観測済みファイルの変更、削除、新規パスの占有を検出する。"""
    for key, expected in baseline.items():
        path = operation_path(key)
        actual = digest(path.read_bytes()) if path.is_file() else None
        if actual != expected or (expected is None and path.exists()):
            raise ConfigError(f"input changed since preparation: {display_path(root, path)}; rebuild the candidate")


def store_candidates(root: Path, record: dict, updates: dict) -> None:
    """候補と原本を保存し、再開時には候補の指紋も照合する。"""
    for key, data in updates.items():
        path = operation_path(key)
        record.setdefault("backups", {})[key] = encode(path.read_bytes()) if path.is_file() else None
        record.setdefault("updates", {})[key] = digest(data) if data is not None else None
        if data is not None:
            write_bytes(candidate_path(root, key), data)
    save_json(root / WORK / "record.json", record)


def read_candidates(root: Path, record: dict) -> dict:
    """記録した候補だけを読み、生成後の候補改変を拒否する。"""
    updates = {}
    for key, expected in record["updates"].items():
        data = candidate_path(root, key).read_bytes() if expected is not None else None
        if data is not None and digest(data) != expected:
            raise ConfigError(f"candidate was edited: {display_path(root, operation_path(key))}")
        updates[key] = data
    return updates


def virtual_files(root: Path, directory: Path, updates: dict) -> set[Path]:
    """実ファイルへ候補の作成・削除を重ねた最終ファイル集合を返す。"""
    files = {p for p in directory.rglob("*") if p.is_file()}
    for key, data in updates.items():
        path = operation_path(key)
        if path.is_relative_to(directory):
            if data is None:
                files.discard(path)
            else:
                files.add(path)
    return files


def ensure_new_paths(layers: list) -> None:
    """未所有の既存ディレクトリへ新規レイヤーを書き込まない。"""
    for layer in layers:
        path = Path(layer["resolved_path"])
        if path.exists() or path.is_symlink():
            raise ConfigError(f"new layer destination already exists: {path}")


def safe_path(root: Path, relative: str) -> Path:
    """操作の境界外とsymlink/junction経由の書込みを拒否する。"""
    if not isinstance(relative, str) or not relative or "\\" in relative or ":" in relative:
        raise ConfigError(f"invalid relative path: {relative}")
    path = root / relative
    if path.is_absolute() and not path.is_relative_to(root):
        raise ConfigError(f"path outside operation: {relative}")
    resolved = path.resolve()
    if resolved == root.resolve() or not resolved.is_relative_to(root.resolve()) or resolved != Path(os.path.abspath(path)):
        raise ConfigError(f"unsafe path: {relative}")
    for parent in (path, *path.parents):
        if parent == root:
            break
        if parent.is_symlink() or (hasattr(parent, "is_junction") and parent.is_junction()):
            raise ConfigError(f"linked operation path: {relative}")
    return resolved


def layer_relative(root: Path, layer: dict) -> str:
    """解決済みレイヤーをプロジェクト相対表記にする。"""
    return Path(layer["resolved_path"]).relative_to(root).as_posix()


def operation_key(path: Path) -> str:
    """切替対象を、プロジェクト外でも衝突しない正規化済み絶対パスで識別する。"""
    return str(path.resolve())


def operation_path(key: str) -> Path:
    """操作記録の絶対パスだけを復元する。"""
    path = Path(key)
    if not path.is_absolute():
        raise ConfigError(f"invalid operation path: {key}")
    return path


def candidate_path(root: Path, key: str) -> Path:
    """外部パスを作業ディレクトリへ安全な固定名で対応付ける。"""
    return root / WORK / "candidate" / hashlib.sha256(key.encode("utf-8")).hexdigest()


def display_path(root: Path, path: Path) -> str:
    """プロジェクト内は相対、外部は解決済み絶対パスで表示する。"""
    resolved = path.resolve()
    return resolved.relative_to(root).as_posix() if resolved.is_relative_to(root) else str(resolved)


def replace_file(path: Path, data: bytes | None) -> None:
    """同一ディレクトリの一時ファイルから一件だけ置換する。"""
    if data is None:
        if path.exists():
            path.unlink()
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + "." + uuid.uuid4().hex + ".pk-switch")
    with temporary.open("xb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    try:
        # Windowsの短時間の共有違反だけを再試行し、原本の削除へフォールバックしない。
        for attempt in range(10):
            try:
                os.replace(temporary, path)
                break
            except PermissionError as exc:
                if getattr(exc, "winerror", None) not in {5, 32} or attempt == 9:
                    raise
                time.sleep(0.05 * (attempt + 1))
    finally:
        temporary.unlink(missing_ok=True)


def write_bytes(path: Path, data: bytes) -> None:
    """操作所有の候補ファイルを保存する。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def read_json(path: Path) -> dict:
    """操作入力はJSON mappingとして読む。"""
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ConfigError("operation input must be a JSON object")
    return value


def save_json(path: Path, value: dict) -> None:
    """復旧記録を途中までのJSONとして残さない。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    replace_file(path, json.dumps(value, ensure_ascii=False, indent=2).encode("utf-8"))


def digest(data: bytes) -> str:
    """再開と競合検出用の内容指紋を返す。"""
    return hashlib.sha256(data).hexdigest()


def encode(data: bytes) -> str:
    """原本の文字コードと改行を失わず記録する。"""
    return base64.b64encode(data).decode("ascii")


def decode(data: str) -> bytes:
    """復旧用の原本bytesを復元する。"""
    return base64.b64decode(data)
