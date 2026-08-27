from __future__ import annotations

import re
from dataclasses import dataclass

from .errors import InvalidShipmentId


@dataclass(frozen=True)
class ShipmentId:
    value: str

    @classmethod
    def parse(cls, raw: str) -> ShipmentId:
        """外部入力をshipment IDへ変換する。"""

        # 公開IDのprefixと8桁の小文字英数字を検証
        if not re.fullmatch(r"shp_[a-z0-9]{8}", raw):
            raise InvalidShipmentId("shipment_id must match shp_[a-z0-9]{8}")
        return cls(raw)
