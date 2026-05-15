from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from statistics import median


@dataclass(frozen=True)
class PriceRecord:
    day: int
    store: str
    price: float


@dataclass(frozen=True)
class PriceDropAnomaly:
    day: int
    store: str
    price: float
    peer_median_price: float
    drop_percentage: float
    reason: str


def detect_price_drop_anomalies(
    records: list[PriceRecord], drop_threshold_percentage: float = 25.0
) -> list[PriceDropAnomaly]:
    records_by_day: dict[int, list[PriceRecord]] = defaultdict(list)
    for record in records:
        records_by_day[record.day].append(record)

    anomalies: list[PriceDropAnomaly] = []
    for day, day_records in sorted(records_by_day.items()):
        peer_median_price = median(record.price for record in day_records)
        for record in day_records:
            drop_percentage = round(
                ((peer_median_price - record.price) / peer_median_price) * 100,
                1,
            )
            if drop_percentage >= drop_threshold_percentage:
                anomalies.append(
                    PriceDropAnomaly(
                        day=day,
                        store=record.store,
                        price=record.price,
                        peer_median_price=peer_median_price,
                        drop_percentage=drop_percentage,
                        reason=(
                            f"{record.store} is {drop_percentage}% below the "
                            f"same-day peer median price of {peer_median_price:.2f}."
                        ),
                    )
                )
    return anomalies
