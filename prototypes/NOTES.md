# Prototype Notes

## Phase 3 Modeling Comparison

Question: should the first production modeling slice be competitor price-drop
anomaly detection or staple-good forecasting?

Verdict: promote competitor price-drop anomaly detection first.

Why: the anomaly path produced a clear, inspectable analyst signal from a short
synthetic history. The ARIMA-style forecast was stable on synthetic staple-good
data, but it needs more real history and seasonality before it should influence
pricing decisions.

Production slice promoted: `detect_price_drop_anomalies(records)`.

## Phase 4 Analysis View

Question: what should a glass-box pricing analyst view show for one UPC across
stores?

Verdict: start with a dependency-free HTML prototype before adding Streamlit or
Dash. The repo does not currently carry UI dependencies, and the valuable part
of this phase is the information architecture: price spread over time, current
store comparison, anomaly flags, visible decision rule, and source rows.

Prototype command: `python3 -m grocery_pricing.analysis_view`
