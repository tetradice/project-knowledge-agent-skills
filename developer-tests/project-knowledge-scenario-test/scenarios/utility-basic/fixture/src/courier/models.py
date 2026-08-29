from __future__ import annotations

from dataclasses import dataclass, replace

from .ids import ShipmentId


@dataclass(frozen=True)
class Shipment:
    shipment_id: ShipmentId
    status: str
    cancellation_reason: str | None = None

    def with_cancellation(self, reason: str) -> Shipment:
        """キャンセル済みの新しいshipmentを返す。"""

        return replace(self, status="cancelled", cancellation_reason=reason)

    def to_dict(self) -> dict[str, str | None]:
        """公開response用のdictへ変換する。"""

        return {
            "shipment_id": self.shipment_id.value,
            "status": self.status,
            "cancellation_reason": self.cancellation_reason,
        }
