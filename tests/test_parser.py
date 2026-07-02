import unittest
from pathlib import Path

from grocery_pricing.parser import GroceryProductPageParser, parse_product_page


FIXTURE_HTML = """
<html>
  <head>
    <meta name="store" content="North Market">
    <meta name="timestamp" content="2026-05-14T15:30:00-04:00">
  </head>
  <body>
    <h1 data-field="name"> Organic   Gala Apples </h1>
    <p data-field="upc">UPC: 123456789</p>
    <p data-field="current-price">$3.49</p>
    <p data-field="regular-price">Regular price: $3.99</p>
  </body>
</html>
"""


class ParseProductPageTest(unittest.TestCase):
    def test_scrapy_style_parser_parses_checked_in_fixture(self) -> None:
        fixture = Path("fixtures/sample_product.html").read_text(encoding="utf-8")

        item = GroceryProductPageParser().parse(fixture)

        self.assertEqual(
            item.to_json(),
            {
                "upc": "000123456789",
                "name": "Organic Gala Apples",
                "current_price": "3.49",
                "regular_price": "3.99",
                "store": "North Market",
                "department": "UNAVAILABLE",
                "categories": [],
                "timestamp": "2026-05-14T19:30:00Z",
            },
        )

    def test_normalizes_upc_to_twelve_digits(self) -> None:
        item = parse_product_page(FIXTURE_HTML)

        self.assertEqual(item.upc, "000123456789")

    def test_normalizes_product_name_whitespace(self) -> None:
        item = parse_product_page(FIXTURE_HTML)

        self.assertEqual(item.name, "Organic Gala Apples")

    def test_normalizes_current_price(self) -> None:
        item = parse_product_page(FIXTURE_HTML)

        self.assertEqual(item.current_price, "3.49")

    def test_normalizes_regular_price(self) -> None:
        item = parse_product_page(FIXTURE_HTML)

        self.assertEqual(item.regular_price, "3.99")

    def test_normalizes_store_and_timestamp(self) -> None:
        item = parse_product_page(FIXTURE_HTML)

        self.assertEqual(item.store, "North Market")
        self.assertEqual(item.timestamp, "2026-05-14T19:30:00Z")

    def test_requires_all_public_fields(self) -> None:
        with self.assertRaisesRegex(ValueError, "current-price"):
            parse_product_page(FIXTURE_HTML.replace('data-field="current-price"', ""))


if __name__ == "__main__":
    unittest.main()
