from __future__ import annotations

from .errors import ShipmentNotFound
from .ids import ShipmentId
from .models import Shipment
from .repository import ShipmentRepository


class ShipmentService:
    def __init__(self, repository: ShipmentRepository) -> None:
        self._repository = repository

    def get(self, shipment_id: ShipmentId) -> Shipment:
        """shipmentを取得し、未登録ならdomain errorへ変換する。"""

        # Repository経由でshipmentを取得
        shipment = self._repository.find(shipment_id)
        if shipment is None:
            raise ShipmentNotFound(f"shipment not found: {shipment_id.value}")
        return shipment
