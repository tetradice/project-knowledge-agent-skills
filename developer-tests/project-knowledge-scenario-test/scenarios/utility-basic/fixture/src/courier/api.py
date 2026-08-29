from __future__ import annotations

from typing import Any

from .errors import CourierError
from .ids import ShipmentId
from .repository import ShipmentRepository
from .service import ShipmentService


def get_shipment(repository: ShipmentRepository, raw_shipment_id: str) -> dict[str, Any]:
    """shipment取得APIのresponseを返す。"""

    try:
        # API境界で入力をdomain IDへ変換してServiceを呼び出す
        shipment_id = ShipmentId.parse(raw_shipment_id)
        shipment = ShipmentService(repository).get(shipment_id)
        return {"status": 200, "data": shipment.to_dict()}
    except CourierError as error:
        # domain errorを公開可能なresponseへ変換
        return {"status": 400, "error": {"code": error.code, "message": str(error)}}
