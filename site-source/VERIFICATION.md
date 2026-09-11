# Final planned site update verification

Verified September 10, 2026 before publication:

- Exact-path preview at `/KingKullenResearch/` loads the dashboard and frozen snapshot (21,040 products).
- Discount patterns, Product explorer, and Catalog coverage each render the complete original retirement notice and shared footer.
- Retirement banner stays visible below the navigation during scrolling; tested desktop and mobile layout.
- Old Site resolves to `/KingKullenResearch/old-site/`; archived weekly report renders 18 snapshots; archived catalog searches 21,040 products and opens full per-UPC histories from local shards.
- `scripts/verify_final_site.py` passes: all 85 original files exist; 82 remain byte-identical; three HTML pages have only local-link/canonical adjustments. Local HTML asset and page references resolve. Final HTML/snapshot hashes match their build manifest.
- Existing `test_published_catalog_history.py` passes against the retained data and raw snapshots.
- Desktop 1280px and mobile 390px layouts inspected. No document-level horizontal overflow on the dashboard.
- GitHub Pages remains `main:/docs`; weekly crawl remains manually disabled. Historical raw data and analysis outputs are unchanged.

This is a completed, retired presentation. No further feature work is planned.
