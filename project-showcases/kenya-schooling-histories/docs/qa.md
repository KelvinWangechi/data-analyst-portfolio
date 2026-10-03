# Verification and release checks

The empirical run uses `hhm.dta` identified by the SHA-256 in [the release manifest](../outputs/release_manifest.json).

## Executed checks

- **13 unit tests passed:** weighted common denominators and bounds, all-unclassified handling, age selection, invalid weights and duplicate keys, sample-status validation, explicit stratum-based reporting, planned enrolment, contradictory responses, float64 accumulation, and complementary/age-family suppression.
- **Independent SQL verification passed for all 32 private location/sample/age groups.** SQLite conditional weighted sums agree with Python A/B/C percentages within 1e-10 percentage points; eligible and classified counts agree exactly.
- **Public release verification passed:** 23 public rows match their source estimates to the six-decimal export tolerance; component totals and gap identities reconcile; the README’s eight-row table matches the public CSV; the input and all three table/three figure hashes match the manifest.
- **Questionnaire/release reconciliation:** the released indicator and the never-attended-or-no-enrolment rule differ for one age-eligible record, retained as unclassified. Routing cross-tabs were inspected across all five released interview batches.
- **Sensitivity checks completed:** six respondent-status disagreements and 59 additional reported exit/no-return signals were evaluated separately from the baseline. The direction of all four overall refugee–host gaps is unchanged.
- **Disclosure review:** public outputs omit raw data, identifiers, private counts/weights and granular diagnostics; both A/B components are withheld for small overall cells, and all age detail is withheld for affected location/sample families. Component gaps cannot recover withheld urban-host components.
- **Figure review:** the three rendered PNGs were checked for legibility, axes, labels, denominators, captions and clipping. Each chart is generated from the calculated estimates rather than manually entered bar lengths.

## Re-run checks

```sh
python -m unittest discover -s tests -v
python scripts/verify_release.py --data raw/release/hhm.dta --private outputs/private_run01
```

Unit tests use artificial fixtures solely to test code. The published findings use the actual roster. Remaining analytical limits are substantive: survey design variance is not estimated; age eligibility is unresolved for some roster members; released definitions and self-report may contain measurement error; and the comparisons are descriptive. See [methodology](methodology.md).
