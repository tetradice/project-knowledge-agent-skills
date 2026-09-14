"""設定入口とファイル変更の境界を実際のCLIで検証する。"""

import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
from project_config import ConfigError, discover_config, load_config, parse_config, select_layer


def run(name: str, *args: object) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPTS / name), *map(str, args)], capture_output=True, text=True)


def config_text(path: str = "./project-knowledge", access: str | None = None) -> str:
    data = {"version": "1.0", "layers": [{"id": "default", "name": "既定", "path": path}]}
    if access:
        data["layers"][0]["access"] = access
    return yaml.safe_dump(data, sort_keys=False)


def snapshot(root: Path) -> dict:
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob("*") if p.is_file()}


def test_generated_config_is_minimal_and_read_write(tmp_path: Path) -> None:
    result = run("init_project.py", tmp_path)
    assert result.returncode == 0, result.stderr
    text = (tmp_path / "project-knowledge.yaml").read_text(encoding="utf-8")
    assert text.splitlines()[0] == "# この設定ファイルは project-knowledge skill で生成されました。"
    assert yaml.safe_load(text) == {"version": "1.0", "layers": [{"id": "default", "name": "既定", "path": "./project-knowledge"}]}
    config = load_config(tmp_path)
    assert config["write_target"] == "default"
    assert config["layers"][0]["access"] == "read-write"
    before = snapshot(tmp_path)
    assert run("init_project.py", tmp_path).returncode == 0
    assert snapshot(tmp_path) == before


def test_prepare_registers_only_after_initial_content(tmp_path: Path) -> None:
    assert run("init_project.py", tmp_path, "--prepare").returncode == 0
    assert not (tmp_path / "project-knowledge.yaml").exists()
    content = tmp_path / "project-knowledge" / "docs" / "initial.md"
    content.write_text("initial knowledge", encoding="utf-8")
    assert run("init_project.py", tmp_path).returncode == 0
    assert content.read_text(encoding="utf-8") == "initial knowledge"
    assert load_config(tmp_path)["version"] == "1.0"


@pytest.mark.parametrize("text", [
    "", "{}", "# comment", "null", "[]", "layers: []",
    'version: 1.0\nlayers: []', 'version: "2.0"\nlayers: []',
    'version: "1.0"', 'version: "1.0"\nlayers: [{}]',
    'version: "1.0"\nlayers: [{id: default}]',
    'version: "1.0"\nlayers: [{path: ./kb}]',
    'version: "1.0"\nlayers: []\nversion: "1.0"',
    'version: "1.0"\nlayers: []\nunknown: true',
    'version: "1.0"\nlayers: &items []',
    'version: "1.0"\nlayers: !!seq []',
    'version: "1.0"\nlayers: []\n---\n{}',
    'version: "1.0"\nlayers: []\n<<: {}',
])
def test_invalid_config_is_never_rewritten(tmp_path: Path, text: str) -> None:
    file = tmp_path / "project-knowledge.yaml"
    file.write_text(text, encoding="utf-8")
    assert run("project_config.py", "--project-root", tmp_path).returncode == 2
    assert run("init_project.py", tmp_path).returncode == 2
    assert file.read_text(encoding="utf-8") == text
    assert not (tmp_path / "project-knowledge").exists()


@pytest.mark.parametrize("description", [None, "", "   ", 123])
def test_nondefault_description_is_required(tmp_path: Path, description: object) -> None:
    data = yaml.safe_load(config_text())
    data["layers"][0]["id"] = "team"
    if description is not None:
        data["layers"][0]["description"] = description
    with pytest.raises(ConfigError, match="description"):
        parse_config(yaml.safe_dump(data), tmp_path / "project-knowledge.yaml")


def test_description_multiline_and_optional_defaults(tmp_path: Path) -> None:
    text = 'version: "1.0"\nlayers:\n  - id: team\n    name: チーム用\n    path: ./kb\n    description: |\n      Team design.\n      Shared decisions.\n'
    config = parse_config(text, tmp_path / "project-knowledge.yaml")
    assert config["layers"][0]["description"] == "Team design.\nShared decisions.\n"
    assert config["write_target"] == "team"
    assert not config["layers"][0]["optional"]
    assert config["layers"][0]["auto_select"]


@pytest.mark.parametrize("path", ["../outside", ".", "/tmp/kb", "C:/kb", "C:kb", "~/kb", "${ROOT}/kb", "./*/kb", "https://host/kb"])
def test_paths_are_project_relative(tmp_path: Path, path: str) -> None:
    with pytest.raises(ConfigError):
        parse_config(config_text(path), tmp_path / "project-knowledge.yaml")


def test_zero_and_multiple_layers(tmp_path: Path) -> None:
    config = parse_config('version: "1.0"\nlayers: []', tmp_path / "project-knowledge.yaml")
    assert config["layers"] == []
    with pytest.raises(ConfigError):
        select_layer(config)
    config = parse_config('version: "1.0"\nlayers: [{id: personal, name: 個人用, path: ./a, description: private}, {id: team, name: チーム用, path: ./b, description: shared}, {id: public, name: 公開用, path: ./c, description: public, auto_select: false}]', tmp_path / "project-knowledge.yaml")
    assert [layer["id"] for layer in config["layers"]] == ["personal", "team", "public"]
    assert config["write_target"] is None


@pytest.mark.parametrize("key,value", [("name", None), ("name", " "), ("name", 1), ("auto_select", "false")])
def test_name_and_auto_select_validation(tmp_path: Path, key: str, value: object) -> None:
    data = yaml.safe_load(config_text())
    data["layers"][0][key] = value
    with pytest.raises(ConfigError):
        parse_config(yaml.safe_dump(data), tmp_path / "project-knowledge.yaml")


@pytest.mark.parametrize("second", [
    {"id": "team", "name": "既定", "path": "./team", "description": "shared"},
    {"id": "team", "name": "default", "path": "./team", "description": "shared"},
    {"id": "team", "name": "チーム用", "path": "./project-knowledge/child", "description": "shared"},
    {"id": "team", "name": "チーム用", "path": "./project-knowledge", "description": "shared"},
])
def test_multiple_layer_collisions_are_rejected(tmp_path: Path, second: dict[str, object]) -> None:
    data = yaml.safe_load(config_text())
    data["layers"].append(second)
    with pytest.raises(ConfigError):
        parse_config(yaml.safe_dump(data), tmp_path / "project-knowledge.yaml")


def test_optional_missing_does_not_hide_broken_manifest(tmp_path: Path) -> None:
    file = tmp_path / "project-knowledge.yaml"
    data = yaml.safe_load(config_text())
    data["layers"][0]["optional"] = True
    file.write_text(yaml.safe_dump(data), encoding="utf-8")
    config = load_config(tmp_path)
    assert not config["layers"][0]["available"]
    with pytest.raises(ConfigError, match="missing"):
        select_layer(config)
    (tmp_path / "project-knowledge").mkdir()
    with pytest.raises(ConfigError):
        load_config(tmp_path)


def test_custom_path_writes_and_null_target(tmp_path: Path) -> None:
    file = tmp_path / "project-knowledge.yaml"
    file.write_text(config_text("./knowledge/team", "read-write"), encoding="utf-8")
    assert run("init_project.py", tmp_path).returncode == 0
    assert not (tmp_path / "project-knowledge").exists()
    root = tmp_path / "knowledge" / "team"
    assert run("validate_knowledge.py", root, "--project-root", tmp_path).returncode == 0
    assert run("detect_changes.py", tmp_path, "--write-snapshot").returncode == 0
    assert (root / ".cache" / "source-snapshot.json").is_file()
    file.write_text(file.read_text(encoding="utf-8") + "write_target: null\n", encoding="utf-8")
    before = snapshot(tmp_path)
    assert run("detect_changes.py", tmp_path, "--write-snapshot").returncode == 2
    assert snapshot(tmp_path) == before
    assert run("detect_changes.py", tmp_path, "--write-snapshot", "--layer", "default").returncode == 0


def test_unregistered_and_read_only_operations_do_not_write(tmp_path: Path) -> None:
    assert run("init_project.py", tmp_path).returncode == 0
    root = tmp_path / "project-knowledge"
    config_path = tmp_path / "project-knowledge.yaml"
    config_path.write_text(config_text(access="read-only"), encoding="utf-8")
    before = snapshot(tmp_path)
    assert run("detect_changes.py", tmp_path).returncode == 0
    assert run("detect_changes.py", tmp_path, "--write-snapshot").returncode == 2
    assert run("policy_settings.py", root / "knowledge-policy.md", "--project-root", tmp_path, "--learning-mode", "manual").returncode == 2
    assert run("validate_knowledge.py", root, "--project-root", tmp_path).returncode == 0
    assert snapshot(tmp_path) == before
    (tmp_path / "project-knowledge.yaml").unlink()
    before = snapshot(tmp_path)
    for command in [
        ("detect_changes.py", tmp_path),
        ("validate_knowledge.py", root, "--project-root", tmp_path),
        ("policy_settings.py", root / "knowledge-policy.md", "--project-root", tmp_path),
    ]:
        assert run(*command).returncode == 2
    assert snapshot(tmp_path) == before


def test_discovery_boundaries_and_explicit_root(tmp_path: Path) -> None:
    (tmp_path / "project-knowledge.yaml").write_text(config_text(), encoding="utf-8")
    child = tmp_path / "child"
    child.mkdir()
    assert discover_config(child) is None
    assert discover_config(child, tmp_path) == tmp_path / "project-knowledge.yaml"
    assert run("project_config.py", "--project-root", child).returncode == 2
    subprocess.run(["git", "init", str(child)], check=True, capture_output=True)
    assert discover_config(child, tmp_path) is None
    nested = child / "nested"
    nested.mkdir()
    (child / "project-knowledge.yaml").write_text('version: "1.0"\nlayers: []', encoding="utf-8")
    assert discover_config(nested) == child / "project-knowledge.yaml"


def test_failed_init_does_not_register(tmp_path: Path) -> None:
    root = tmp_path / "project-knowledge"
    root.mkdir()
    (root / "existing.txt").write_text("keep", encoding="utf-8")
    before = snapshot(tmp_path)
    assert run("init_project.py", tmp_path).returncode != 0
    assert snapshot(tmp_path) == before


def test_external_symlink_is_rejected_before_initialization(tmp_path: Path) -> None:
    project = tmp_path / "project"
    outside = tmp_path / "outside"
    project.mkdir()
    outside.mkdir()
    link = project / "project-knowledge"
    try:
        link.symlink_to(outside, target_is_directory=True)
    except OSError as exc:
        pytest.skip(f"directory symlinks unavailable: {exc}")
    assert run("init_project.py", project).returncode == 2
    assert list(outside.iterdir()) == []
    assert not (project / "project-knowledge.yaml").exists()


@pytest.mark.parametrize("key,value", [("access", "unknown"), ("optional", "false"), ("description", None), ("unknown", True)])
def test_layer_validation(tmp_path: Path, key: str, value: object) -> None:
    data = yaml.safe_load(config_text())
    data["layers"][0][key] = value
    with pytest.raises(ConfigError):
        parse_config(yaml.safe_dump(data), tmp_path / "project-knowledge.yaml")


@pytest.mark.parametrize("target", ["missing", 1, []])
def test_invalid_write_target(tmp_path: Path, target: object) -> None:
    data = yaml.safe_load(config_text())
    data["write_target"] = target
    with pytest.raises(ConfigError, match="write_target"):
        parse_config(yaml.safe_dump(data), tmp_path / "project-knowledge.yaml")


def test_auto_select_false_cannot_be_write_target(tmp_path: Path) -> None:
    data = yaml.safe_load(config_text())
    data["layers"][0]["auto_select"] = False
    data["write_target"] = "default"
    with pytest.raises(ConfigError, match="auto_select"):
        parse_config(yaml.safe_dump(data), tmp_path / "project-knowledge.yaml")


def test_policy_file_must_match_registered_layer(tmp_path: Path) -> None:
    assert run("init_project.py", tmp_path).returncode == 0
    other = tmp_path / "other"
    other.mkdir()
    policy = other / "knowledge-policy.md"
    policy.write_text("not a registered policy", encoding="utf-8")
    result = run("policy_settings.py", policy, "--project-root", tmp_path)
    assert result.returncode == 2
    assert "does not match" in result.stderr
