import unittest

from grocery_pricing.modeling import PriceRecord, detect_price_drop_anomalies


class DetectPriceDropAnomaliesTest(unittest.TestCase):
    def test_flags_competitor_price_drop_against_same_day_peer_median(self) -> None:
        records = [
            PriceRecord(day=11, store="North Market", price=3.49),
            PriceRecord(day=11, store="Value Grocer", price=3.39),
            PriceRecord(day=11, store="Budget Basket", price=1.99),
        ]

        anomalies = detect_price_drop_anomalies(records)

        self.assertEqual(len(anomalies), 1)
        self.assertEqual(anomalies[0].store, "Budget Basket")
        self.assertEqual(anomalies[0].price, 1.99)
        self.assertEqual(anomalies[0].peer_median_price, 3.39)
        self.assertEqual(anomalies[0].drop_percentage, 41.3)
        self.assertIn("41.3%", anomalies[0].reason)

    def test_does_not_flag_normal_competitive_spread(self) -> None:
        records = [
            PriceRecord(day=1, store="North Market", price=3.49),
            PriceRecord(day=1, store="Value Grocer", price=3.39),
            PriceRecord(day=1, store="Budget Basket", price=3.29),
        ]

        anomalies = detect_price_drop_anomalies(records)

        self.assertEqual(anomalies, [])


if __name__ == "__main__":
    unittest.main()
