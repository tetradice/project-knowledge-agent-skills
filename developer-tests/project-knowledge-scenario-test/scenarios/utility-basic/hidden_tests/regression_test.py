from __future__ import annotations

import sys
import unittest
from pathlib import Path


def main() -> int:
    """Fixture作成時の既存API契約を固定したまま回帰確認する。"""

    workspace = Path(sys.argv[1]).resolve()
    sys.path.insert(0, str(workspace / "src"))

    # Task Agentが変更できない初期契約で既存機能を確認
    from courier.api import get_shipment
    from courier.ids import ShipmentId
    from courier.models import Shipment
    from courier.repository import InMemoryShipmentRepository

    class ExistingApiContract(unittest.TestCase):
        def setUp(self) -> None:
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

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(ExistingApiContract)
    return 0 if unittest.TextTestRunner().run(suite).wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
