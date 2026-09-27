# Dependency licenses

Actual inventories: `docs/evidence/python-licenses.json` (88 installed distributions at first audit) and `docs/evidence/npm-licenses.json` (pnpm dependency graph). Generated with Python pip-licenses and pnpm licenses list. This is a metadata inventory, not a legal clearance opinion.

Most application dependencies are permissive MIT/BSD/Apache variants. Notable obligations requiring distribution review:

- psycopg and psycopg-binary: LGPL-3.0-only. Preserve license and corresponding source/relinking obligations as applicable; do not strip notices from packaged images.
- certifi: MPL-2.0. Preserve its notice and source obligations for modified covered files.
- ECharts bundle: retain upstream Apache-2.0 notices in the bundled JavaScript.
- @img/sharp-win32-x64: Apache-2.0 AND LGPL-3.0-or-later (native libvips packaging); retain notices and applicable LGPL source/relinking obligations.
- lightningcss and its Windows native package: MPL-2.0; caniuse-lite: CC-BY-4.0 attribution. Included in the actual JavaScript inventory.
- Chromium, geospatial native libraries and fonts have their own transitive licenses. Preserve image/package license files. Windows fonts and downloaded database executables are not redistributed from this repository.

Suggested project license: Apache-2.0 for explicit patent terms and permissive contributions, **pending owner selection**. No LICENSE file was imposed. Publication remains unapproved.
