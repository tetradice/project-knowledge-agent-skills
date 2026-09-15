# /// script
# requires-python = ">=3.11"
# dependencies = ["PyYAML>=6.0,<7"]
# ///

"""必須のルート設定から利用するProject Knowledgeを解決する。"""

from __future__ import annotations

import argparse
import json
import os
import re
import stat
import subprocess
import sys
from pathlib import Path, PureWindowsPath

import yaml

CONFIG_NAME = "project-knowledge.yaml"
CONFIG_VERSION = "1.0"


class ConfigError(ValueError):
    """未登録、不正設定、利用できないレイヤーを表す。"""


def discover_config(start: Path, workspace_root: Path | None = None) -> Path | None:
    """Gitまたはworkspaceの境界内で最寄りの設定を探す。"""

    current = start.resolve()
    boundary = workspace_root.resolve() if workspace_root else current
    # Git管理外では呼び出し元のworkspace境界だけを使用
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"], cwd=current,
            capture_output=True, text=True, check=False,
        )
        if result.returncode == 0:
            boundary = Path(result.stdout.strip()).resolve()
            if workspace_root and workspace_root.resolve().is_relative_to(boundary):
                boundary = workspace_root.resolve()
    except FileNotFoundError:
        pass
    if not current.is_relative_to(boundary):
        raise ConfigError("start directory is outside workspace boundary")
    while True:
        candidate = current / CONFIG_NAME
        if candidate.exists() or candidate.is_symlink():
            return candidate
        if current == boundary:
            return None
        current = current.parent


def parse_config(text: str, config_path: Path, *, resolve_symlinks: bool = True) -> dict:
    """副作用なしで設定の構文、型、省略値、パスを解決する。"""

    def fail(key: str, detail: str) -> None:
        raise ConfigError(f"{config_path}: {key}: {detail}")

    # 独自タグや参照構文と重複キーを読み込み前に拒否
    try:
        for token in yaml.scan(text):
            if isinstance(token, (yaml.tokens.AnchorToken, yaml.tokens.AliasToken, yaml.tokens.TagToken)):
                fail(f"line {token.start_mark.line + 1}", "tags, anchors and aliases are unsupported")
        node = yaml.compose(text)
        _check_mapping_nodes(node, config_path)
        data = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        fail("YAML", str(exc))
    if not isinstance(data, dict):
        fail("root", "must be a mapping")
    if set(data) - {"version", "layers", "write_target"}:
        fail("root", f"unknown keys: {set(data) - {'version', 'layers', 'write_target'}}")
    if data.get("version") != CONFIG_VERSION or not isinstance(data.get("version"), str):
        fail("version", 'must be the string "1.0"; never upgraded automatically')
    if not isinstance(data.get("layers"), list):
        fail("layers", "required list")
    # 実行時に使うレイヤーを正規化し、暗黙のパスは作らない
    root = config_path.parent.resolve()
    layers = []
    for index, item in enumerate(data["layers"]):
        key = f"layers[{index}]"
        if not isinstance(item, dict):
            fail(key, "must be a mapping")
        allowed_keys = {"id", "name", "path", "description", "access", "optional", "auto_select"}
        if set(item) - allowed_keys:
            fail(key, f"unknown layer keys: {set(item) - allowed_keys}")
        identifier = item.get("id")
        if not isinstance(identifier, str) or not re.fullmatch(r"[a-z][a-z0-9_-]*", identifier):
            fail(key + ".id", "required identifier matching [a-z][a-z0-9_-]*")
        name = item.get("name")
        if not isinstance(name, str) or not name.strip():
            fail(key + ".name", "required nonblank display name")
        description = item.get("description", "")
        if not isinstance(description, str) or (identifier != "default" and not description.strip()):
            fail(key + ".description", "must be a string; non-default IDs require a nonblank description")
        path = item.get("path")
        if not isinstance(path, str) or not path.strip():
            fail(key + ".path", "required nonblank relative path")
        if PureWindowsPath(path).drive or path.startswith(("/", "~")) or any(c in path for c in "\\:$%*?[]\x00"):
            fail(key + ".path", "must be a project-relative path without expansion or glob")
        resolved = (root / path).resolve() if resolve_symlinks else Path(os.path.abspath(root / path))
        if resolved == root or not resolved.is_relative_to(root):
            fail(key + ".path", "must be a directory strictly inside the project")
        access = item.get("access", "read-write")
        if access not in ("read-only", "read-write"):
            fail(key + ".access", "must be read-only or read-write")
        optional = item.get("optional", False)
        if type(optional) is not bool:
            fail(key + ".optional", "must be boolean")
        auto_select = item.get("auto_select", True)
        if type(auto_select) is not bool:
            fail(key + ".auto_select", "must be boolean")
        layers.append({"id": identifier, "name": name, "path": path, "resolved_path": str(resolved),
                       "description": description, "access": access, "optional": optional,
                       "auto_select": auto_select})

    for index, layer in enumerate(layers):
        other_layers = layers[:index] + layers[index + 1:]
        if any(other["id"] == layer["id"] for other in other_layers):
            fail(f"layers[{index}].id", "must be unique")
        if any(other["name"] == layer["name"] for other in other_layers):
            fail(f"layers[{index}].name", "must be unique")
        if any(other["id"] == layer["name"] for other in other_layers):
            fail(f"layers[{index}].name", "must not match another layer ID")
        path = Path(layer["resolved_path"])
        if any(path == Path(other["resolved_path"]) for other in other_layers):
            fail(f"layers[{index}].path", "must be unique")
        if any(path.is_relative_to(Path(other["resolved_path"])) or Path(other["resolved_path"]).is_relative_to(path) for other in other_layers):
            fail(f"layers[{index}].path", "must not contain or be contained by another layer")

    target = data.get("write_target", layers[0]["id"] if len(layers) == 1 and layers[0]["access"] == "read-write" else None)
    target_layer = next((layer for layer in layers if layer["id"] == target), None)
    if target is not None and (not isinstance(target, str) or target_layer is None or target_layer["access"] != "read-write"):
        fail("write_target", "must name a registered read-write layer or be null")
    if target_layer is not None and not target_layer["auto_select"]:
        fail("write_target", "must not name an auto_select: false layer")
    return {"version": CONFIG_VERSION, "config_path": str(config_path), "project_root": str(root),
            "layers": layers, "write_target": target}


def _check_mapping_nodes(node: yaml.Node | None, path: Path) -> None:
    """全階層の重複キーとmerge keyを行番号付きで拒否する。"""

    if isinstance(node, yaml.MappingNode):
        seen = set()
        for key, value in node.value:
            if not isinstance(key, yaml.ScalarNode) or key.tag != "tag:yaml.org,2002:str":
                raise ConfigError(f"{path}: line {key.start_mark.line + 1}: keys must be strings")
            if key.value in seen or key.value == "<<":
                raise ConfigError(f"{path}: line {key.start_mark.line + 1}: duplicate or merge key {key.value}")
            seen.add(key.value)
            _check_mapping_nodes(value, path)
    elif isinstance(node, yaml.SequenceNode):
        for value in node.value:
            _check_mapping_nodes(value, path)


def load_config(project_root: Path, *, allow_missing: bool = False, check_manifest: bool = True, _operation: bool = False) -> dict:
    """明示ルートの設定だけを読み、レイヤーの利用可能性を確認する。"""

    config_path = project_root.resolve() / CONFIG_NAME
    try:
        if not _operation and (project_root.resolve() / ".project-knowledge.lock").exists():
            raise ConfigError("Knowledge operation in progress; resume or recover the recorded operation first")
        if config_path.is_symlink():
            raise ConfigError(f"{config_path}: config must not be a symbolic link")
        config = parse_config(config_path.read_text(encoding="utf-8-sig"), config_path)
        for layer in config["layers"]:
            path = Path(layer["resolved_path"])
            try:
                mode = path.stat().st_mode
            except FileNotFoundError:
                if not layer["optional"] and not allow_missing:
                    raise ConfigError(f"{path}: layer directory is missing; initialize it explicitly")
                layer["available"] = False
                continue
            if not stat.S_ISDIR(mode):
                raise ConfigError(f"{path}: layer must be a directory")
            layer["available"] = True
            if check_manifest:
                manifest = yaml.safe_load((path / "manifest.yml").read_text(encoding="utf-8"))
                if not isinstance(manifest, dict) or manifest.get("format") != "project-knowledge" or manifest.get("format_version") != "1.0":
                    raise ConfigError(f"{path}: unsupported or malformed manifest.yml")
        return config
    except (OSError, UnicodeError, yaml.YAMLError, RuntimeError) as exc:
        raise ConfigError(f"{config_path}: {exc}") from exc


def select_layer(config: dict, layer_id: str | None = None, *, write: bool = False, allow_missing: bool = False) -> dict:
    """読み書き対象を選び、別レイヤーへの暗黙切り替えを防ぐ。"""

    identifier = layer_id if layer_id is not None else config["write_target"] if write else None
    candidates = [item for item in config["layers"] if identifier is None or item["id"] == identifier]
    if (write and identifier is None) or len(candidates) != 1:
        raise ConfigError("no target layer; specify a registered layer ID")
    layer = candidates[0]
    if write and layer["access"] != "read-write":
        raise ConfigError(f"{layer['id']}: layer is read-only")
    if not layer.get("available", True) and not allow_missing:
        raise ConfigError(f"{layer['id']}: layer directory is missing")
    return layer


def registered_path(path: Path, *, policy: bool = False, write: bool = False, layer_id: str | None = None, check_manifest: bool = True, project_root: Path | None = None) -> Path:
    """既存CLIのproject/bundle/Policy引数が登録先と一致するか確認する。"""

    candidate = path.resolve()
    start = candidate.parent if policy else candidate
    if project_root is not None:
        config_path = project_root.resolve() / CONFIG_NAME
    elif (start / CONFIG_NAME).exists():
        config_path = start / CONFIG_NAME
    else:
        config_path = discover_config(start)
    if config_path is None:
        raise ConfigError(f"{path}: project is not registered ({CONFIG_NAME} missing)")
    config = load_config(config_path.parent, check_manifest=check_manifest)
    expected_layers = [
        layer for layer in config["layers"]
        if candidate == (Path(layer["resolved_path"]) / "knowledge-policy.md" if policy else Path(layer["resolved_path"]))
    ]
    if layer_id is not None:
        layer = select_layer(config, layer_id, write=write)
        expected_layers = [layer] if layer in expected_layers else []
    elif write:
        layer = select_layer(config, write=True)
        expected_layers = [layer] if layer in expected_layers else []
    if len(expected_layers) != 1:
        raise ConfigError(f"{path}: path does not match the registered layer")
    return candidate


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path)
    parser.add_argument("--start", type=Path, default=Path.cwd())
    parser.add_argument("--workspace-root", type=Path)
    parser.add_argument("--layer")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    try:
        config_path = args.project_root.resolve() / CONFIG_NAME if args.project_root else discover_config(args.start, args.workspace_root)
        if config_path is None:
            raise ConfigError(f"project is not registered ({CONFIG_NAME} missing)")
        config = load_config(config_path.parent)
        if args.layer is not None or args.write:
            config["selected_layer"] = select_layer(config, args.layer, write=args.write)["id"]
        print(json.dumps(config, ensure_ascii=False, indent=2))
        return 0
    except (ConfigError, OSError, RuntimeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
