# Final public interface

This is the final planned site update for the retired King Kullen Research project. No feature development, data collection, support, or scheduled refresh has resumed.

- GitHub Pages continues to publish `main:/docs` at `https://frankiejvaldez.com/KingKullenResearch/`.
- `docs/index.html` is the accepted Data dashboard, compiled with Data plugin 1.0.2, with only the requested retirement header and shared footer added.
- `docs/data-app-build.json` binds the published HTML to its complete frozen, content-addressed snapshot. No server-side API is required for exploration.
- `dashboard/` retains the authored React, CSS, and calculation code. All analytics and chart identities are unchanged from the accepted dashboard.
- `docs/old-site/` preserves the former 85-file frontend. `legacy-manifest.json` records its original hashes. Only the three archived HTML pages have intentional navigation/canonical-link corrections to keep the archive local. Their retirement notices, reports, data, assets, and history shards remain intact.
- Previous root report, history, and data paths remain available for existing links. The shared **Old Site** footer points to the local archive.
- The weekly crawl workflow remains manually disabled. Do not run the historical crawler/report publishing commands against this final interface.

For an actual defect correction, prepare a Data app with the same runtime version and the published snapshot, restore these authored files and `theme.css`, and build using the Data plugin's documented `data-app.mjs build --separate-data` command. Preserve the snapshot's artifact ID and reviewed data. Run `python3 scripts/package_final_site.py /path/to/dashboard-project`, then the tests. Packaging verifies build hashes, strips only the machine-local task marker, adds the public canonical metadata, and copies the frozen snapshot. It does not change hosting configuration, publish, or refresh data.
