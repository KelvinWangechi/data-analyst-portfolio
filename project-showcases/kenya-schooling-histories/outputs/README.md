# Calculated aggregate outputs

- `schooling_estimates.csv`: 23 disclosure-filtered location/sample/age rows. A is out of school without previous attendance; B is out of school with previous attendance; C is in the school system; O=A+B. All estimates and missing shares are percentages. Blank A/B values mean withheld, not zero.
- `location_gaps.csv`: refugee-minus-host total gaps in percentage points. Component gaps are provided only where both source decompositions are public.
- `sensitivity.csv`: overall O percentages under the baseline and two alternative specifications.
- `release_manifest.json`: source hash, release identifier, software versions and hashes of the public tables/figures.
- `estimates_schema.csv`: field contract for the detailed private run; it is not an empirical results file.

`private*` folders contain import audits, detailed estimates, denominators and diagnostics and are excluded from Git. The public export omits age detail for location/sample families with small component cells, preventing recovery by subtraction. See [methodology](../docs/methodology.md).
