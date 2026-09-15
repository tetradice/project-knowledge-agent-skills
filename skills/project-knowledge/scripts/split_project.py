# /// script
# requires-python = ">=3.11"
# dependencies = ["PyYAML>=6.0,<7"]
# ///
"""一つの既存レイヤーから新規レイヤーへの分割候補を準備・適用・復旧する。"""

import argparse
import sys
from pathlib import Path

from layer_workflow import apply_split, prepare_split, recover
from project_config import ConfigError


def main() -> int:
    """段階を明示した分割操作だけを実行する。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_root", type=Path)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--plan", type=Path, help="固定配置表から候補を準備")
    action.add_argument("--apply", action="store_true", help="検査済み候補を切替")
    action.add_argument("--recover", action="store_true", help="中断した切替を復旧")
    args = parser.parse_args()
    try:
        root = args.project_root.resolve()
        if args.plan:
            prepare_split(root, args.plan)
        elif args.apply:
            apply_split(root)
        else:
            recover(root)
        return 0
    except (ConfigError, OSError, ValueError) as exc:
        print(f"Cannot split project-knowledge: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
