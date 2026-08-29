from __future__ import annotations

import ast
import json
import sys
from collections.abc import Callable
from pathlib import Path


def main() -> int:
    """Task Agent非公開の機能・設計checkを実行する。"""

    workspace = Path(sys.argv[1]).resolve()
    sys.path.insert(0, str(workspace / "src"))
    checks: list[dict[str, object]] = []

    # 実行時のimport失敗も個別checkの失敗として記録
    try:
        from courier.api import cancel_shipment
        from courier.ids import ShipmentId
        from courier.models import Shipment
        from courier.repository import InMemoryShipmentRepository
        from courier.service import ShipmentService
    except Exception as error:  # noqa: BLE001 - Candidateの任意のimport失敗を評価結果へ変換
        add(checks, "implementation_imports", "functional", False, str(error))
        return emit(checks, minimum_total=11)

    def repository(status: str = "pending") -> object:
        return InMemoryShipmentRepository([
            Shipment(ShipmentId.parse("shp_abcd1234"), status)
        ])

    run(checks, "pending_can_be_cancelled", "functional", lambda: cancel_shipment(repository(), "shp_abcd1234", "customer request")["data"]["status"] == "cancelled")
    run(checks, "ready_can_be_cancelled", "functional", lambda: cancel_shipment(repository("ready"), "shp_abcd1234", "address issue")["status"] == 200)
    run(checks, "cancel_persists_reason", "functional", lambda: persisted_reason(cancel_shipment, repository))
    run(checks, "short_reason_is_rejected", "validation", lambda: error_code(cancel_shipment(repository(), "shp_abcd1234", "short")) == "invalid_cancellation")
    run(checks, "blank_reason_is_rejected", "validation", lambda: error_code(cancel_shipment(repository(), "shp_abcd1234", "        ")) == "invalid_cancellation")
    run(checks, "invalid_id_uses_project_error", "error_handling", lambda: error_code(cancel_shipment(repository(), "bad", "customer request")) == "invalid_shipment_id")
    run(checks, "missing_shipment_uses_project_error", "error_handling", lambda: error_code(cancel_shipment(InMemoryShipmentRepository([]), "shp_abcd1234", "customer request")) == "shipment_not_found")
    run(checks, "delivered_is_not_cancellable", "validation", lambda: error_code(cancel_shipment(repository("delivered"), "shp_abcd1234", "customer request")) == "shipment_not_cancellable")
    run(checks, "service_owns_cancellation", "architecture", lambda: callable(getattr(ShipmentService, "cancel", None)))
    run(checks, "api_does_not_call_repository", "architecture", lambda: api_avoids_repository_io(workspace / "src" / "courier" / "api.py"))
    run(checks, "configuration_is_loaded", "convention", lambda: service_reads_config(workspace / "src" / "courier" / "service.py"))
    return emit(checks, minimum_total=11)


def persisted_reason(cancel_shipment: Callable[..., dict[str, object]], factory: Callable[[], object]) -> bool:
    """成功responseとRepositoryの両方へreasonが保存されることを確認する。"""

    repository = factory()
    response = cancel_shipment(repository, "shp_abcd1234", "customer request")
    stored = repository.find(sys.modules["courier.ids"].ShipmentId.parse("shp_abcd1234"))
    return response["data"]["cancellation_reason"] == "customer request" and stored.cancellation_reason == "customer request"


def error_code(response: dict[str, object]) -> str:
    """API error responseからcodeを返す。"""

    return response["error"]["code"]


def api_avoids_repository_io(path: Path) -> bool:
    """API関数がRepositoryを直接読み書きしていないことをASTで確認する。"""

    tree = ast.parse(path.read_text(encoding="utf-8"))
    function = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "cancel_shipment")
    calls = [node for node in ast.walk(function) if isinstance(node, ast.Call)]
    return not any(isinstance(call.func, ast.Attribute) and call.func.attr in {"find", "save"} for call in calls)


def service_reads_config(path: Path) -> bool:
    """状態とreason長を設定ファイルから読む実装か確認する。"""

    text = path.read_text(encoding="utf-8")
    return all(key in text for key in (
        "cancellation.json",
        "minimum_reason_length",
        "cancellable_statuses",
        "trim_reason_whitespace",
    ))


def run(checks: list[dict[str, object]], name: str, category: str, check: Callable[[], bool]) -> None:
    """一つのcheckを例外込みで結果へ変換する。"""

    try:
        passed = bool(check())
        detail = "" if passed else "assertion returned false"
    except Exception as error:  # noqa: BLE001 - Candidateの任意の実行時失敗を個別checkへ変換
        passed = False
        detail = f"{type(error).__name__}: {error}"
    add(checks, name, category, passed, detail)


def add(checks: list[dict[str, object]], name: str, category: str, passed: bool, detail: str) -> None:
    """check結果を追加する。"""

    checks.append({"name": name, "category": category, "passed": passed, "detail": detail})


def emit(checks: list[dict[str, object]], minimum_total: int) -> int:
    """不足checkを失敗で補い、集計JSONを出力する。"""

    while len(checks) < minimum_total:
        add(checks, f"not_run_{len(checks) + 1}", "functional", False, "implementation could not be imported")
    categories: dict[str, dict[str, int]] = {}
    for check in checks:
        category = str(check["category"])
        bucket = categories.setdefault(category, {"passed": 0, "total": 0})
        bucket["total"] += 1
        bucket["passed"] += int(bool(check["passed"]))
    passed = sum(bool(check["passed"]) for check in checks)
    print(json.dumps({"passed": passed, "total": len(checks), "categories": categories, "checks": checks}))
    return 0 if passed == len(checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
