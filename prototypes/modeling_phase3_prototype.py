"""PROTOTYPE: Phase 3 modeling comparison.

Question: should the first production modeling slice be competitor price-drop
anomaly detection or staple-good forecasting?

Run:
    python3 prototypes/modeling_phase3_prototype.py
"""

from __future__ import annotations

import json
import random
from dataclasses import asdict, dataclass
from statistics import mean, median


@dataclass(frozen=True)
class PricePoint:
    day: int
    store: str
    price: float


def build_synthetic_competitor_prices() -> list[PricePoint]:
    prices: list[PricePoint] = []
    for day in range(1, 15):
        prices.append(PricePoint(day=day, store="North Market", price=3.49))
        prices.append(PricePoint(day=day, store="Value Grocer", price=3.39))
        drop_price = 3.29
        if day in {11, 12}:
            drop_price = 1.99
        prices.append(PricePoint(day=day, store="Budget Basket", price=drop_price))
    return prices


def build_synthetic_staple_prices() -> list[PricePoint]:
    prices: list[PricePoint] = []
    for day in range(1, 22):
        trend = 0.015 * day
        weekly_bump = 0.08 if day % 7 in {5, 6} else 0.0
        prices.append(
            PricePoint(
                day=day,
                store="North Market",
                price=round(4.25 + trend + weekly_bump, 2),
            )
        )
    return prices


def isolation_forest_style_scores(points: list[PricePoint]) -> list[dict[str, object]]:
    random.seed(7)
    prices = [point.price for point in points]
    low = min(prices)
    high = max(prices)
    scores: list[dict[str, object]] = []

    for point in points:
        isolation_hits = 0
        for _ in range(64):
            threshold = random.uniform(low, high)
            if point.price < threshold:
                isolation_hits += 1
        score = isolation_hits / 64
        scores.append(
            {
                "point": asdict(point),
                "anomaly_score": round(score, 3),
                "flagged": score >= 0.9,
            }
        )
    return scores


def arima_style_forecast(points: list[PricePoint]) -> dict[str, object]:
    prices = [point.price for point in points]
    differences = [
        round(current - previous, 2)
        for previous, current in zip(prices, prices[1:])
    ]
    recent_drift = mean(differences[-7:])
    next_price = round(prices[-1] + recent_drift, 2)
    errors = []

    for index in range(8, len(prices)):
        drift = mean(differences[index - 7 : index])
        predicted = round(prices[index - 1] + drift, 2)
        errors.append(round(abs(predicted - prices[index]), 2))

    return {
        "input_points": [asdict(point) for point in points],
        "differences": differences,
        "next_day_forecast": next_price,
        "mean_absolute_error": round(mean(errors), 3),
        "last_observed_price": prices[-1],
    }


def summarize_anomaly_path(points: list[PricePoint]) -> dict[str, object]:
    scored = isolation_forest_style_scores(points)
    flagged = [row for row in scored if row["flagged"]]
    return {
        "input_points": [asdict(point) for point in points],
        "median_price": median(point.price for point in points),
        "scored_points": scored,
        "flagged_points": flagged,
        "signal": "Clear abnormal competitor price drops on days 11 and 12.",
    }


def main() -> None:
    anomaly_state = summarize_anomaly_path(build_synthetic_competitor_prices())
    forecast_state = arima_style_forecast(build_synthetic_staple_prices())
    recommendation = {
        "recommended_first_production_slice": "competitor_price_drop_anomaly_detection",
        "reason": (
            "The anomaly path produces an inspectable analyst signal from a short "
            "history, while forecasting needs more historical seasonality before it "
            "can be trusted for staple goods."
        ),
    }
    print(
        json.dumps(
            {
                "anomaly_detection_path": anomaly_state,
                "arima_style_forecasting_path": forecast_state,
                "recommendation": recommendation,
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
