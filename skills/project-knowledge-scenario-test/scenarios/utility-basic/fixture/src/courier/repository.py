from __future__ import annotations

from typing import Protocol

from .ids import ShipmentId
from .models import Shipment


class ShipmentRepository(Protocol):
    def find(self, shipment_id: ShipmentId) -> Shipment | None:
        """IDに一致するshipmentを返す。"""

    def save(self, shipment: Shipment) -> None:
        """shipmentを保存する。"""


class InMemoryShipmentRepository:
    def __init__(self, shipments: list[Shipment]) -> None:
        # domain IDをkeyにしてfixture用データを保持
        self._shipments = {shipment.shipment_id: shipment for shipment in shipments}

    def find(self, shipment_id: ShipmentId) -> Shipment | None:
        """IDに一致するshipmentを返す。"""

        return self._shipments.get(shipment_id)

    def save(self, shipment: Shipment) -> None:
        """shipmentを保存する。"""

        self._shipments[shipment.shipment_id] = shipment
