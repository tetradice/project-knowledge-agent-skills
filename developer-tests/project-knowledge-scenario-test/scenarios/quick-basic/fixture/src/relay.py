"""注文イベントを外部通知へ変換する。"""

from __future__ import annotations

import hashlib
from typing import Any


def should_notify(event: dict[str, Any]) -> bool:
    """通知対象の注文イベントか判定する。"""

    return event.get("type") == "order.paid"


def customer_log_id(customer_id: str) -> str:
    """ログ用の顧客識別子を生成する。"""

    return hashlib.sha256(customer_id.encode("utf-8")).hexdigest()


def retry_schedule(config: dict[str, Any]) -> list[int]:
    """設定から通知の再試行間隔を取得する。"""

    retry = config["delivery"]["retry"]
    return retry["backoff_seconds"][: retry["max_attempts"]]
