import unittest

from grocery_pricing.reconciliation import reconcile_scraped_item


class ReconcileScrapedItemTest(unittest.TestCase):
    def test_matches_master_catalog_item_by_exact_upc(self) -> None:
        scraped_item = {"upc": "000123456789", "name": "Organic Gala Apples"}
        master_catalog = [
            {"id": "milk", "upc": "000111222333", "name": "Whole Milk"},
            {"id": "apples", "upc": "000123456789", "name": "Organic Gala Apples"},
        ]

        result = reconcile_scraped_item(scraped_item, master_catalog)

        self.assertEqual(result.match_type, "exact_upc")
        self.assertEqual(result.confidence, 1.0)
        self.assertEqual(result.catalog_item["id"], "apples")

    def test_matches_master_catalog_item_by_normalized_name(self) -> None:
        scraped_item = {"upc": "999999999999", "name": " organic   gala apples "}
        master_catalog = [
            {"id": "apples", "upc": "000123456789", "name": "Organic Gala Apples"},
        ]

        result = reconcile_scraped_item(scraped_item, master_catalog)

        self.assertEqual(result.match_type, "normalized_name")
        self.assertEqual(result.confidence, 0.85)
        self.assertEqual(result.catalog_item["id"], "apples")

    def test_handles_null_upc_by_falling_back_to_name(self) -> None:
        scraped_item = {"upc": None, "name": "Organic Gala Apples"}
        master_catalog = [
            {"id": "apples", "upc": "000123456789", "name": "Organic Gala Apples"},
        ]

        result = reconcile_scraped_item(scraped_item, master_catalog)

        self.assertEqual(result.match_type, "normalized_name")
        self.assertEqual(result.catalog_item["id"], "apples")

    def test_handles_null_name_without_raising(self) -> None:
        scraped_item = {"upc": None, "name": None}
        master_catalog = [
            {"id": "apples", "upc": "000123456789", "name": "Organic Gala Apples"},
        ]

        result = reconcile_scraped_item(scraped_item, master_catalog)

        self.assertEqual(result.match_type, "no_match")
        self.assertIsNone(result.catalog_item)

    def test_returns_zero_confidence_when_no_catalog_item_matches(self) -> None:
        scraped_item = {"upc": "999999999999", "name": "Cinnamon Oat Cereal"}
        master_catalog = [
            {"id": "apples", "upc": "000123456789", "name": "Organic Gala Apples"},
        ]

        result = reconcile_scraped_item(scraped_item, master_catalog)

        self.assertEqual(result.match_type, "no_match")
        self.assertEqual(result.confidence, 0.0)
        self.assertIsNone(result.catalog_item)


if __name__ == "__main__":
    unittest.main()
