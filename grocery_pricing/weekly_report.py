from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from html import escape
from pathlib import Path
from statistics import mean, median
from typing import Any

from .catalog_history import build_catalog_history


@dataclass(frozen=True)
class SnapshotStats:
    snapshot_date: str
    products: int
    categories: int
    average_price: float
    sale_items: int
    sale_rate: float


def _price(value: Any) -> float | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def load_snapshot(path: Path) -> dict[str, dict[str, Any]]:
    products: dict[str, dict[str, Any]] = {}
    with path.open(encoding="utf-8") as snapshot:
        for line_number, line in enumerate(snapshot, 1):
            try:
                item = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(f"{path}:{line_number}: invalid JSON") from error
            upc = str(item.get("upc", "")).strip()
            current_price = _price(item.get("current_price"))
            if upc and current_price is not None:
                item["_current_price"] = current_price
                item["_regular_price"] = _price(item.get("regular_price"))
                products[upc] = item
    if not products:
        raise ValueError(f"{path} contains no usable products")
    return products


def snapshot_stats(path: Path, products: dict[str, dict[str, Any]]) -> SnapshotStats:
    prices = [item["_current_price"] for item in products.values()]
    categories = {
        category
        for item in products.values()
        for category in item.get("categories", [])
        if category
    }
    sale_items = sum(
        1
        for item in products.values()
        if item["_regular_price"] is not None
        and item["_current_price"] < item["_regular_price"]
    )
    return SnapshotStats(
        snapshot_date=path.stem,
        products=len(products),
        categories=len(categories),
        average_price=round(mean(prices), 2),
        sale_items=sale_items,
        sale_rate=round((sale_items / len(products)) * 100, 1),
    )


def compare_snapshots(
    previous: dict[str, dict[str, Any]],
    latest: dict[str, dict[str, Any]],
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    common_upcs = previous.keys() & latest.keys()
    changes: list[dict[str, Any]] = []
    for upc in common_upcs:
        old_price = previous[upc]["_current_price"]
        new_price = latest[upc]["_current_price"]
        difference = round(new_price - old_price, 2)
        if difference:
            changes.append(
                {
                    "upc": upc,
                    "name": latest[upc].get("name", "Unknown product"),
                    "previous_price": old_price,
                    "current_price": new_price,
                    "change": difference,
                    "change_percentage": round((difference / old_price) * 100, 1),
                }
            )

    increases = [change for change in changes if change["change"] > 0]
    decreases = [change for change in changes if change["change"] < 0]
    percentage_changes = [
        change["change_percentage"]
        for change in changes
        if abs(change["change_percentage"]) <= 500
    ]
    comparison = {
        "matched_products": len(common_upcs),
        "coverage_percentage": round(
            (len(common_upcs) / max(len(previous), 1)) * 100, 1
        ),
        "price_changes": len(changes),
        "price_increases": len(increases),
        "price_decreases": len(decreases),
        "unchanged_prices": len(common_upcs) - len(changes),
        "new_products": len(latest.keys() - previous.keys()),
        "removed_products": len(previous.keys() - latest.keys()),
        "median_price_change_percentage": round(median(percentage_changes), 1)
        if percentage_changes
        else 0.0,
    }
    return comparison, decreases, increases


def build_weekly_summary(snapshot_paths: list[Path]) -> dict[str, Any]:
    if len(snapshot_paths) < 2:
        raise ValueError("At least two snapshots are required for a weekly comparison")

    ordered_paths = sorted(snapshot_paths)
    loaded = [(path, load_snapshot(path)) for path in ordered_paths]
    history = [
        asdict(snapshot_stats(path, products)) for path, products in loaded
    ]
    comparisons = []
    latest_decreases: list[dict[str, Any]] = []
    latest_increases: list[dict[str, Any]] = []
    for index in range(1, len(loaded)):
        previous_path, previous = loaded[index - 1]
        latest_path, latest = loaded[index]
        comparison, decreases, increases = compare_snapshots(previous, latest)
        comparisons.append(
            {
                "from_date": previous_path.stem,
                "to_date": latest_path.stem,
                **comparison,
            }
        )
        if index == len(loaded) - 1:
            latest_decreases = decreases
            latest_increases = increases

    previous_path, previous = loaded[-2]
    latest_path, latest = loaded[-1]
    previous_stats = snapshot_stats(previous_path, previous)
    latest_stats = snapshot_stats(latest_path, latest)
    latest_comparison = comparisons[-1]

    return {
        "generated_from": [previous_path.name, latest_path.name],
        "latest": asdict(latest_stats),
        "previous": asdict(previous_stats),
        "comparison": latest_comparison,
        "largest_decreases": sorted(
            latest_decreases,
            key=lambda item: (item["change_percentage"], item["upc"]),
        )[:10],
        "largest_increases": sorted(
            latest_increases,
            key=lambda item: (-item["change_percentage"], item["upc"]),
        )[:10],
        "history": history,
        "comparisons": comparisons,
    }


def _money(value: float) -> str:
    return f"${value:,.2f}"


def _movement_rows(items: list[dict[str, Any]]) -> str:
    if not items:
        return '<tr><td colspan="4">No price changes this week.</td></tr>'
    return "".join(
        "<tr>"
        f"<td>{escape(item['name'])}<small>UPC {escape(item['upc'])}</small></td>"
        f"<td>{_money(item['previous_price'])}</td>"
        f"<td>{_money(item['current_price'])}</td>"
        f"<td class=\"{'down' if item['change'] < 0 else 'up'}\">"
        f"{item['change_percentage']:+.1f}%</td>"
        "</tr>"
        for item in items
    )


def _line_chart(
    rows: list[dict[str, Any]], field: str, label: str, suffix: str = ""
) -> str:
    width, height = 720, 220
    left, top, right, bottom = 54, 24, 18, 42
    values = [float(row[field]) for row in rows]
    low, high = min(values), max(values)
    padding = max((high - low) * 0.15, 0.5)
    low -= padding
    high += padding
    plot_width = width - left - right
    plot_height = height - top - bottom

    def point(index: int, value: float) -> tuple[float, float]:
        x = left + (index / max(len(rows) - 1, 1)) * plot_width
        y = top + ((high - value) / max(high - low, 1)) * plot_height
        return x, y

    points = [point(index, value) for index, value in enumerate(values)]
    polyline = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
    marks = "".join(
        f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4"><title>'
        f"{escape(rows[index]['snapshot_date'])}: {values[index]:,.1f}{escape(suffix)}"
        "</title></circle>"
        f'<text class="value-label" x="{x:.1f}" y="{y - 10:.1f}" text-anchor="middle">'
        f"{_chart_value(field, values[index])}</text>"
        for index, (x, y) in enumerate(points)
    )
    labels = "".join(
        f'<text x="{x:.1f}" y="{height - 14}" text-anchor="middle">'
        f"{escape(rows[index]['snapshot_date'][5:])}</text>"
        for index, (x, _) in enumerate(points)
    )
    return f"""<svg viewBox="0 0 {width} {height}" role="img" aria-label="{escape(label)} over time">
      <line x1="{left}" y1="{top + plot_height}" x2="{width - right}" y2="{top + plot_height}" />
      <polyline points="{polyline}" />
      {marks}{labels}
    </svg>"""


def _chart_value(field: str, value: float) -> str:
    if field == "products":
        return f"{value / 1000:.1f}k"
    if field == "sale_rate":
        return f"{value:.1f}%"
    if field == "average_price":
        return f"${value:.2f}"
    return f"{value:,.1f}"


def render_html(summary: dict[str, Any]) -> str:
    latest = summary["latest"]
    previous = summary["previous"]
    comparison = summary["comparison"]
    history_rows = "".join(
        "<tr>"
        f"<td>{row['snapshot_date']}</td><td>{row['products']:,}</td>"
        f"<td>{row['categories']:,}</td><td>{_money(row['average_price'])}</td>"
        f"<td>{row['sale_rate']:.1f}%</td>"
        "</tr>"
        for row in reversed(summary["history"])
    )
    comparison_rows = "".join(
        "<tr>"
        f"<td>{row['from_date']} → {row['to_date']}</td>"
        f"<td>{row['matched_products']:,}</td>"
        f"<td>{row['coverage_percentage']:.1f}%</td>"
        f"<td class=\"down\">{row['price_decreases']:,}</td>"
        f"<td class=\"up\">{row['price_increases']:,}</td>"
        f"<td>{row['new_products']:,}</td><td>{row['removed_products']:,}</td>"
        "</tr>"
        for row in reversed(summary["comparisons"])
    )
    product_chart = _line_chart(
        summary["history"], "products", "Unique products"
    )
    sale_chart = _line_chart(
        summary["history"], "sale_rate", "Products on sale", "%"
    )
    price_chart = _line_chart(
        summary["history"], "average_price", "Average catalog price", ""
    )
    health = (
        "Healthy"
        if comparison["coverage_percentage"] >= 80
        else "Needs attention"
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="Automated King Kullen grocery price time series and weekly comparisons.">
  <title>Price Time Series | King Kullen Research</title>
  <style>
    :root {{ --ink:#191719; --muted:#706a70; --paper:#faf7f8; --card:#fff;
      --line:#e7dfe3; --accent:#c52875; --down:#087a55; --up:#b53b35; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; background:var(--paper); color:var(--ink);
      font:15px/1.5 ui-sans-serif,system-ui,-apple-system,sans-serif; }}
    header,main,footer {{ width:min(1120px,calc(100% - 32px)); margin:auto; }}
    header {{ padding:54px 0 28px; }}
    a {{ color:var(--accent); }}
    .eyebrow {{ color:var(--accent); font-size:12px; font-weight:750;
      letter-spacing:.1em; text-transform:uppercase; }}
    h1 {{ margin:7px 0 6px; font:500 clamp(34px,7vw,68px)/1.02 Georgia,serif; }}
    .lede {{ color:var(--muted); margin:0; font-size:17px; }}
    .metrics {{ display:grid; grid-template-columns:repeat(4,1fr); gap:12px;
      margin:22px 0 30px; }}
    .metric,.panel {{ background:var(--card); border:1px solid var(--line);
      border-radius:12px; }}
    .metric {{ padding:18px; }}
    .metric span,small {{ display:block; color:var(--muted); font-size:12px; }}
    .metric strong {{ display:block; font-size:26px; margin-top:3px; }}
    .grid {{ display:grid; grid-template-columns:1fr 1fr; gap:16px; }}
    .charts {{ display:grid; grid-template-columns:repeat(3,1fr); gap:16px; }}
    .panel {{ overflow:hidden; margin-bottom:16px; }}
    h2 {{ font-size:17px; margin:0; padding:16px 18px;
      border-bottom:1px solid var(--line); }}
    .scroll {{ overflow-x:auto; }}
    .chart {{ padding:10px; }}
    svg {{ display:block; width:100%; height:auto; }}
    svg line {{ stroke:var(--line); }}
    svg polyline {{ fill:none; stroke:var(--accent); stroke-width:3; }}
    svg circle {{ fill:var(--card); stroke:var(--accent); stroke-width:3; }}
    svg text {{ fill:var(--muted); font-size:11px; }}
    table {{ border-collapse:collapse; width:100%; }}
    th,td {{ border-bottom:1px solid var(--line); padding:12px 16px;
      text-align:left; vertical-align:top; }}
    th {{ color:var(--muted); font-size:12px; }}
    tr:last-child td {{ border-bottom:0; }}
    .down {{ color:var(--down); font-weight:750; }}
    .up {{ color:var(--up); font-weight:750; }}
    footer {{ color:var(--muted); padding:20px 0 48px; }}
    .nav {{ display:flex; gap:16px; flex-wrap:wrap; width:min(1120px,calc(100% - 32px)); margin:auto; padding:14px 0; border-bottom:1px solid var(--line); }}
    @media(max-width:900px) {{ .charts {{ grid-template-columns:1fr; }} }}
    @media(max-width:760px) {{ .metrics,.grid {{ grid-template-columns:1fr 1fr; }} }}
    @media(max-width:520px) {{ .metrics,.grid {{ grid-template-columns:1fr; }} }}
  </style>
</head>
<body>
<nav class="nav" aria-label="Primary"><a href="index.html">Overview</a><a href="weekly-report.html" aria-current="page">Time series</a><a href="https://frankiejvaldez.com/projects/kingkullenresearch/catalog-history/" target="_top">All items</a><a href="data/weekly-summary.json" target="_blank" rel="noopener">Data contract</a><a href="https://github.com/frankstop/KingKullenResearch" target="_blank" rel="noopener noreferrer">Source</a></nav>
<header>
  <div class="eyebrow">Automated longitudinal analysis</div>
  <h1>Price time series</h1>
  <p class="lede">{previous['snapshot_date']} compared with {latest['snapshot_date']}.
    Generated from the checked-in price snapshots, not hand-entered numbers.</p>
</header>
<main>
  <div class="metrics">
    <div class="metric"><span>Products tracked</span><strong>{latest['products']:,}</strong></div>
    <div class="metric"><span>Prices changed</span><strong>{comparison['price_changes']:,}</strong></div>
    <div class="metric"><span>Price decreases</span><strong>{comparison['price_decreases']:,}</strong></div>
    <div class="metric"><span>Pipeline health</span><strong>{health}</strong></div>
  </div>
  <section>
    <div class="eyebrow">Time series</div>
    <h2 style="border:0;padding:4px 0 14px">How the catalog changes over time</h2>
    <div class="charts">
      <div class="panel"><h2>Unique products</h2><div class="chart">{product_chart}</div></div>
      <div class="panel"><h2>Products on sale</h2><div class="chart">{sale_chart}</div></div>
      <div class="panel"><h2>Average price</h2><div class="chart">{price_chart}</div></div>
    </div>
  </section>
  <section class="panel"><h2>Every week-over-week comparison</h2><div class="scroll">
    <table><thead><tr><th>Period</th><th>Matched</th><th>Coverage</th>
      <th>Decreases</th><th>Increases</th><th>Added</th><th>Removed</th></tr></thead>
      <tbody>{comparison_rows}</tbody></table>
  </div></section>
  <div class="eyebrow" style="margin:28px 0 10px">Latest weekly detail</div>
  <div class="grid">
    <section class="panel"><h2>Largest price decreases</h2><div class="scroll">
      <table><thead><tr><th>Product</th><th>Was</th><th>Now</th><th>Change</th></tr></thead>
      <tbody>{_movement_rows(summary['largest_decreases'])}</tbody></table>
    </div></section>
    <section class="panel"><h2>Largest price increases</h2><div class="scroll">
      <table><thead><tr><th>Product</th><th>Was</th><th>Now</th><th>Change</th></tr></thead>
      <tbody>{_movement_rows(summary['largest_increases'])}</tbody></table>
    </div></section>
  </div>
  <section class="panel"><h2>Snapshot history</h2><div class="scroll">
    <table><thead><tr><th>Date</th><th>Products</th><th>Categories</th>
      <th>Average price</th><th>On sale</th></tr></thead><tbody>{history_rows}</tbody></table>
  </div></section>
</main>
<footer><a href="./">Project overview</a> · <a href="catalog-history.html">All item histories</a> · <a href="https://github.com/frankstop/KingKullenResearch" target="_blank" rel="noopener noreferrer">Source and raw snapshots</a></footer>
</body>
</html>
"""


def render_markdown(summary: dict[str, Any]) -> str:
    latest = summary["latest"]
    previous = summary["previous"]
    comparison = summary["comparison"]
    return "\n".join(
        [
            "## Weekly price analysis",
            "",
            f"Compared `{previous['snapshot_date']}` → `{latest['snapshot_date']}`.",
            "",
            f"- **{latest['products']:,}** products tracked",
            f"- **{comparison['price_changes']:,}** matched products changed price",
            f"- **{comparison['price_decreases']:,}** decreases and **{comparison['price_increases']:,}** increases",
            f"- **{comparison['new_products']:,}** new and **{comparison['removed_products']:,}** removed products",
            f"- **{latest['sale_rate']:.1f}%** of products are below regular price",
            "",
        ]
    )


def write_report(
    snapshots_dir: Path,
    html_output: Path,
    json_output: Path,
    markdown_output: Path | None = None,
    minimum_coverage: float = 80.0,
) -> dict[str, Any]:
    summary = build_weekly_summary(list(snapshots_dir.glob("*.jsonl")))
    coverage = summary["comparison"]["coverage_percentage"]
    if coverage < minimum_coverage:
        raise ValueError(
            f"Latest snapshot matched only {coverage:.1f}% of prior products; "
            f"minimum coverage is {minimum_coverage:.1f}%"
        )
    html_output.parent.mkdir(parents=True, exist_ok=True)
    json_output.parent.mkdir(parents=True, exist_ok=True)
    html_output.write_text(render_html(summary), encoding="utf-8")
    json_output.write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    if markdown_output:
        markdown_output.parent.mkdir(parents=True, exist_ok=True)
        markdown_output.write_text(render_markdown(summary), encoding="utf-8")
    build_catalog_history(snapshots_dir, json_output.parent / "catalog-history")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compare the latest two snapshots and publish a weekly report."
    )
    parser.add_argument("--snapshots", type=Path, default=Path("data/snapshots"))
    parser.add_argument("--html", type=Path, default=Path("docs/weekly-report.html"))
    parser.add_argument(
        "--json", type=Path, default=Path("docs/data/weekly-summary.json")
    )
    parser.add_argument("--markdown", type=Path)
    parser.add_argument(
        "--minimum-coverage",
        type=float,
        default=80.0,
        help="Fail publication when the latest snapshot matches less of the prior catalog.",
    )
    args = parser.parse_args()
    summary = write_report(
        args.snapshots,
        args.html,
        args.json,
        args.markdown,
        args.minimum_coverage,
    )
    print(render_markdown(summary), end="")


if __name__ == "__main__":
    main()
