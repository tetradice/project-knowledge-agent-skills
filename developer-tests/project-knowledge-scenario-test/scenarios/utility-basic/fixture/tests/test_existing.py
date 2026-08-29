from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from courier.api import get_shipment
from courier.ids import ShipmentId
from courier.models import Shipment
from courier.repository import InMemoryShipmentRepository


class ExistingApiTest(unittest.TestCase):
    def setUp(self) -> None:
        # 各testを独立したRepositoryで実行
        self.repository = InMemoryShipmentRepository([
            Shipment(ShipmentId.parse("shp_abcd1234"), "pending")
        ])

    def test_gets_existing_shipment(self) -> None:
        response = get_shipment(self.repository, "shp_abcd1234")

        self.assertEqual(200, response["status"])
        self.assertEqual("pending", response["data"]["status"])

    def test_maps_invalid_id_to_api_error(self) -> None:
        response = get_shipment(self.repository, "wrong")

        self.assertEqual(400, response["status"])
        self.assertEqual("invalid_shipment_id", response["error"]["code"])


if __name__ == "__main__":
    unittest.main()
