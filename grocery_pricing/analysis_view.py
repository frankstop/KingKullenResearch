from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from html import escape
from pathlib import Path
from typing import Iterable, List

from grocery_pricing.modeling import PriceDropAnomaly, PriceRecord, detect_price_drop_anomalies


@dataclass(frozen=True)
class SourcePriceRow:
    upc: str
    product_name: str
    day: int
    timestamp: str
    store: str
    current_price: float
    regular_price: float
    source: str


@dataclass(frozen=True)
class AnalysisViewModel:
    upc: str
    product_name: str
    rows: List[SourcePriceRow]
    anomalies: List[PriceDropAnomaly]
    latest_run_completed_at: str = ""


def build_sample_analysis() -> AnalysisViewModel:
    rows = [
        SourcePriceRow("000123456789", "Organic Gala Apples", 10, "2026-05-10T09:00:00Z", "North Market", 3.49, 3.99, "fixture:north-market"),
        SourcePriceRow("000123456789", "Organic Gala Apples", 10, "2026-05-10T09:04:00Z", "Value Grocer", 3.39, 3.69, "fixture:value-grocer"),
        SourcePriceRow("000123456789", "Organic Gala Apples", 10, "2026-05-10T09:08:00Z", "Budget Basket", 3.29, 3.59, "fixture:budget-basket"),
        SourcePriceRow("000123456789", "Organic Gala Apples", 11, "2026-05-11T09:00:00Z", "North Market", 3.49, 3.99, "fixture:north-market"),
        SourcePriceRow("000123456789", "Organic Gala Apples", 11, "2026-05-11T09:04:00Z", "Value Grocer", 3.39, 3.69, "fixture:value-grocer"),
        SourcePriceRow("000123456789", "Organic Gala Apples", 11, "2026-05-11T09:08:00Z", "Budget Basket", 1.99, 3.59, "fixture:budget-basket"),
        SourcePriceRow("000123456789", "Organic Gala Apples", 12, "2026-05-12T09:00:00Z", "North Market", 3.49, 3.99, "fixture:north-market"),
        SourcePriceRow("000123456789", "Organic Gala Apples", 12, "2026-05-12T09:04:00Z", "Value Grocer", 3.39, 3.69, "fixture:value-grocer"),
        SourcePriceRow("000123456789", "Organic Gala Apples", 12, "2026-05-12T09:08:00Z", "Budget Basket", 1.99, 3.59, "fixture:budget-basket"),
        SourcePriceRow("000123456789", "Organic Gala Apples", 13, "2026-05-13T09:00:00Z", "North Market", 3.49, 3.99, "fixture:north-market"),
        SourcePriceRow("000123456789", "Organic Gala Apples", 13, "2026-05-13T09:04:00Z", "Value Grocer", 3.39, 3.69, "fixture:value-grocer"),
        SourcePriceRow("000123456789", "Organic Gala Apples", 13, "2026-05-13T09:08:00Z", "Budget Basket", 3.29, 3.59, "fixture:budget-basket"),
    ]
    records = [
        PriceRecord(day=row.day, store=row.store, price=row.current_price)
        for row in rows
    ]
    return AnalysisViewModel(
        upc="000123456789",
        product_name="Organic Gala Apples",
        rows=rows,
        anomalies=detect_price_drop_anomalies(records),
    )


def build_analysis_from_latest_run(latest_run_path: Path) -> AnalysisViewModel:
    latest_run = json.loads(latest_run_path.read_text(encoding="utf-8"))
    parsed_item = latest_run["parsed_item"]
    sample = build_sample_analysis()
    rows = [
        SourcePriceRow(
            upc=parsed_item["upc"],
            product_name=parsed_item["name"],
            day=row.day,
            timestamp=row.timestamp,
            store=row.store,
            current_price=row.current_price,
            regular_price=row.regular_price,
            source=row.source,
        )
        for row in sample.rows
    ]
    return AnalysisViewModel(
        upc=parsed_item["upc"],
        product_name=parsed_item["name"],
        rows=rows,
        anomalies=sample.anomalies,
        latest_run_completed_at=latest_run["completed_at"],
    )


def render_analysis_view_html(analysis: AnalysisViewModel) -> str:
    spread_svg = render_spread_svg(analysis.rows)
    comparison_rows = render_store_comparison(analysis.rows)
    anomaly_rows = render_anomaly_rows(analysis.anomalies)
    source_rows = render_source_rows(analysis.rows, analysis.anomalies)

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Analysis View | UPC {escape(analysis.upc)}</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: oklch(97% 0.006 170);
      --surface: oklch(99% 0.004 170);
      --panel: oklch(94% 0.009 178);
      --line: oklch(84% 0.018 178);
      --text: oklch(22% 0.018 178);
      --muted: oklch(45% 0.026 178);
      --accent: oklch(49% 0.12 178);
      --accent-ink: oklch(98% 0.006 178);
      --warning: oklch(61% 0.145 35);
      --warning-bg: oklch(94% 0.038 55);
      --success: oklch(50% 0.11 145);
      --font: -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: var(--bg);
      color: var(--text);
      font-family: var(--font);
      font-size: 14px;
      letter-spacing: 0;
    }}
    header {{
      border-bottom: 1px solid var(--line);
      background: var(--surface);
      padding: 18px 24px 14px;
    }}
    .eyebrow {{
      color: var(--muted);
      font-size: 12px;
      font-weight: 700;
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }}
    h1 {{
      margin: 4px 0 0;
      font-size: 24px;
      line-height: 1.2;
      font-weight: 760;
    }}
    .summary {{
      display: grid;
      grid-template-columns: repeat(4, minmax(160px, 1fr));
      gap: 1px;
      background: var(--line);
      border-bottom: 1px solid var(--line);
    }}
    .metric {{
      background: var(--surface);
      padding: 14px 18px;
      min-height: 78px;
    }}
    .metric span {{
      color: var(--muted);
      display: block;
      font-size: 12px;
      margin-bottom: 5px;
    }}
    .metric strong {{
      font-size: 18px;
      font-weight: 720;
    }}
    main {{
      display: grid;
      grid-template-columns: minmax(0, 1.4fr) minmax(320px, 0.6fr);
      gap: 18px;
      padding: 18px 24px 28px;
    }}
    section {{
      border: 1px solid var(--line);
      background: var(--surface);
      border-radius: 8px;
      overflow: hidden;
    }}
    section h2 {{
      margin: 0;
      padding: 12px 14px;
      border-bottom: 1px solid var(--line);
      font-size: 15px;
      font-weight: 720;
    }}
    .chart-wrap {{ padding: 14px; }}
    svg {{ width: 100%; height: auto; display: block; }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-variant-numeric: tabular-nums;
    }}
    th, td {{
      padding: 10px 12px;
      border-bottom: 1px solid var(--line);
      text-align: left;
      vertical-align: top;
    }}
    th {{
      color: var(--muted);
      font-size: 12px;
      font-weight: 680;
      background: var(--panel);
    }}
    tr:last-child td {{ border-bottom: 0; }}
    .stack {{ display: grid; gap: 18px; }}
    .flag {{
      display: inline-flex;
      align-items: center;
      border-radius: 999px;
      padding: 3px 8px;
      background: var(--warning-bg);
      color: var(--warning);
      font-size: 12px;
      font-weight: 720;
      white-space: nowrap;
    }}
    .ok {{
      color: var(--success);
      font-weight: 720;
    }}
    .decision {{
      padding: 12px 14px 14px;
      border-top: 1px solid var(--line);
      background: var(--panel);
      color: var(--muted);
      line-height: 1.45;
    }}
    .decision strong {{ color: var(--text); }}
    @media (max-width: 880px) {{
      .summary, main {{ grid-template-columns: 1fr; }}
      main, header {{ padding-left: 14px; padding-right: 14px; }}
      .source-table {{ overflow-x: auto; }}
      table {{ min-width: 680px; }}
    }}
  </style>
</head>
<body>
  <header>
    <div class="eyebrow">Analysis View</div>
    <h1>{escape(analysis.product_name)} · UPC {escape(analysis.upc)}</h1>
  </header>
  <div class="summary">
    <div class="metric"><span>Stores</span><strong>{len(stores(analysis.rows))}</strong></div>
    <div class="metric"><span>Observed days</span><strong>{len(days(analysis.rows))}</strong></div>
    <div class="metric"><span>Lowest current price</span><strong>${min(row.current_price for row in analysis.rows):.2f}</strong></div>
    <div class="metric"><span>{latest_run_label(analysis)}</span><strong>{latest_run_value(analysis)}</strong></div>
  </div>
  <main>
    <div class="stack">
      <section>
        <h2>Price spread over time</h2>
        <div class="chart-wrap">{spread_svg}</div>
        <div class="decision"><strong>Decision rule:</strong> compare each store price to the same-day peer median, then flag drops at or above 25.0%.</div>
      </section>
      <section>
        <h2>Source rows</h2>
        <div class="source-table">{source_rows}</div>
      </section>
    </div>
    <div class="stack">
      <section>
        <h2>Store comparison</h2>
        {comparison_rows}
      </section>
      <section>
        <h2>Anomaly flags</h2>
        {anomaly_rows}
      </section>
    </div>
  </main>
</body>
</html>
"""


def render_spread_svg(rows: List[SourcePriceRow]) -> str:
    width = 760
    height = 270
    pad_left = 52
    pad_top = 22
    plot_width = width - 82
    plot_height = height - 64
    min_price = min(row.current_price for row in rows) - 0.10
    max_price = max(row.current_price for row in rows) + 0.10
    ordered_days = days(rows)
    palette = {
        "North Market": "oklch(49% 0.12 178)",
        "Value Grocer": "oklch(56% 0.13 260)",
        "Budget Basket": "oklch(61% 0.145 35)",
    }

    def x_for(day: int) -> float:
        index = ordered_days.index(day)
        return pad_left + (index / max(len(ordered_days) - 1, 1)) * plot_width

    def y_for(price: float) -> float:
        ratio = (price - min_price) / (max_price - min_price)
        return pad_top + plot_height - (ratio * plot_height)

    lines = []
    points = []
    for store in stores(rows):
        store_rows = sorted([row for row in rows if row.store == store], key=lambda row: row.day)
        coords = [(x_for(row.day), y_for(row.current_price)) for row in store_rows]
        path = " ".join(f"{x:.1f},{y:.1f}" for x, y in coords)
        color = palette.get(store, "oklch(40% 0.05 170)")
        lines.append(f'<polyline points="{path}" fill="none" stroke="{color}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" />')
        for row, (x, y) in zip(store_rows, coords):
            points.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4.2" fill="{color}"><title>{escape(store)} day {row.day}: ${row.current_price:.2f}</title></circle>')

    x_labels = [
        f'<text x="{x_for(day):.1f}" y="{height - 18}" text-anchor="middle">Day {day}</text>'
        for day in ordered_days
    ]
    legend = [
        f'<g transform="translate({pad_left + index * 145}, 8)"><circle cx="0" cy="0" r="4" fill="{palette.get(store, "oklch(40% 0.05 170)")}" /><text x="10" y="4">{escape(store)}</text></g>'
        for index, store in enumerate(stores(rows))
    ]
    return f"""<svg viewBox="0 0 {width} {height}" role="img" aria-label="Price spread over time by store">
  <rect x="0" y="0" width="{width}" height="{height}" rx="8" fill="oklch(98% 0.004 170)" />
  <line x1="{pad_left}" y1="{pad_top + plot_height}" x2="{pad_left + plot_width}" y2="{pad_top + plot_height}" stroke="oklch(84% 0.018 178)" />
  <line x1="{pad_left}" y1="{pad_top}" x2="{pad_left}" y2="{pad_top + plot_height}" stroke="oklch(84% 0.018 178)" />
  <text x="8" y="{y_for(max_price - 0.10):.1f}" fill="oklch(45% 0.026 178)">${max_price - 0.10:.2f}</text>
  <text x="8" y="{y_for(min_price + 0.10):.1f}" fill="oklch(45% 0.026 178)">${min_price + 0.10:.2f}</text>
  {"".join(legend)}
  {"".join(lines)}
  {"".join(points)}
  {"".join(x_labels)}
</svg>"""


def render_store_comparison(rows: List[SourcePriceRow]) -> str:
    latest_day = max(row.day for row in rows)
    latest_rows = [row for row in rows if row.day == latest_day]
    body = "".join(
        f"<tr><td>{escape(row.store)}</td><td>${row.current_price:.2f}</td><td>${row.regular_price:.2f}</td><td>{latest_day}</td></tr>"
        for row in sorted(latest_rows, key=lambda row: row.current_price)
    )
    return f"<table><thead><tr><th>Store</th><th>Current</th><th>Regular</th><th>Day</th></tr></thead><tbody>{body}</tbody></table>"


def render_anomaly_rows(anomalies: List[PriceDropAnomaly]) -> str:
    if not anomalies:
        return '<div class="decision"><span class="ok">No anomaly flags</span></div>'
    body = "".join(
        f"<tr><td>Day {anomaly.day}</td><td>{escape(anomaly.store)}</td><td>${anomaly.price:.2f}</td><td><span class=\"flag\">{anomaly.drop_percentage:.1f}% below median</span></td></tr>"
        for anomaly in anomalies
    )
    explanation = escape(anomalies[0].reason)
    return f"<table><thead><tr><th>Day</th><th>Store</th><th>Price</th><th>Signal</th></tr></thead><tbody>{body}</tbody></table><div class=\"decision\"><strong>Why flagged:</strong> {explanation}</div>"


def render_source_rows(rows: List[SourcePriceRow], anomalies: List[PriceDropAnomaly]) -> str:
    flagged_keys = {(anomaly.day, anomaly.store) for anomaly in anomalies}
    rendered_rows = []
    for row in sorted(rows, key=lambda row: (row.day, row.store)):
        status = (
            '<span class="flag">Flagged</span>'
            if (row.day, row.store) in flagged_keys
            else '<span class="ok">Normal</span>'
        )
        rendered_rows.append(
            "<tr>"
            f"<td>{row.timestamp}</td>"
            f"<td>{escape(row.store)}</td>"
            f"<td>${row.current_price:.2f}</td>"
            f"<td>${row.regular_price:.2f}</td>"
            f"<td>{status}</td>"
            f"<td>{escape(row.source)}</td>"
            "</tr>"
        )
    body = "".join(rendered_rows)
    return f"<table><thead><tr><th>Timestamp</th><th>Store</th><th>Current</th><th>Regular</th><th>Decision</th><th>Source</th></tr></thead><tbody>{body}</tbody></table>"


def stores(rows: Iterable[SourcePriceRow]) -> List[str]:
    return sorted({row.store for row in rows})


def days(rows: Iterable[SourcePriceRow]) -> List[int]:
    return sorted({row.day for row in rows})


def latest_run_label(analysis: AnalysisViewModel) -> str:
    if analysis.latest_run_completed_at:
        return "Latest successful run"
    return "Anomaly flags"


def latest_run_value(analysis: AnalysisViewModel) -> str:
    if analysis.latest_run_completed_at:
        return escape(analysis.latest_run_completed_at)
    return str(len(analysis.anomalies))


def main() -> None:
    parser = argparse.ArgumentParser(description="Render the Phase 4 Analysis View prototype.")
    parser.add_argument(
        "output",
        nargs="?",
        default="artifacts/analysis_view.html",
        help="HTML output path",
    )
    parser.add_argument(
        "--latest-run",
        type=Path,
        default=Path("artifacts/latest_successful_run.json"),
        help="Latest successful run JSON to read when present",
    )
    args = parser.parse_args()

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if args.latest_run.exists():
        analysis = build_analysis_from_latest_run(args.latest_run)
    else:
        analysis = build_sample_analysis()
    output_path.write_text(render_analysis_view_html(analysis), encoding="utf-8")
    print(str(output_path))


if __name__ == "__main__":
    main()
