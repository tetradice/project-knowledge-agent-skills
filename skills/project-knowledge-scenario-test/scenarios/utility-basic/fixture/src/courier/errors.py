class CourierError(Exception):
    """APIへ安全に公開できる業務error。"""

    code = "courier_error"


class InvalidShipmentId(CourierError):
    code = "invalid_shipment_id"


class ShipmentNotFound(CourierError):
    code = "shipment_not_found"


class InvalidCancellation(CourierError):
    code = "invalid_cancellation"


class ShipmentNotCancellable(CourierError):
    code = "shipment_not_cancellable"
