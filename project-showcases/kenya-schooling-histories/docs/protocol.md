# Calculation specification

The [methodology](methodology.md) defines the analytical population and interpretation. This file maps the executed calculation to the outputs.

1. Read the Stata roster without category conversion and preserve extended missing codes in a private import audit. Check household/member key uniqueness.
2. Select recorded ages 6–17 inclusive. Reject invalid ages, nonpositive/nonfinite eligible weights, unknown status codes and unsupported locations.
3. Use released location strata for the reporting sample. Record conflicts with respondent status; default strict mode rejects conflicts unless the validated reporting basis is explicitly `released_location_strata`.
4. Classify A/B/C/U using the released out-of-school indicator and ever-attendance. Flag out-of-school=0 with never-attendance and out-of-school=1 with current attendance. Unresolved diagnostics remain U.
5. Calculate weighted A/B/C shares on the same classified denominator, O=A+B, the direct indicator estimate on its own valid-response denominator, eligible/classified counts and weights, and unresolved-weight bounds.
6. Repeat for 6–11, 12–14 and 15–17. Calculate refugee-minus-host gaps before rounding. Their component gaps sum to the total gap.
7. Recalculate after excluding respondent-status discrepancies and after including explicit permanent-exit/no-return signals. Export private routing counts by the actual released `batch` field.
8. Apply the public disclosure rules in `build_release.py`. Generate three PNG figures directly from the unrounded estimates, labelled to one decimal. Save tables to six decimals and hashes in the release manifest.
9. Independently recompute the main estimates using SQLite conditional weighted sums and verify the public figures’ source tables, arithmetic, disclosure filters and hashes.

`validation.example.json` documents the evidence that a reproducer must review for their own approved release. It does not certify producer construction code. Raw inputs and private outputs are ignored by Git.
