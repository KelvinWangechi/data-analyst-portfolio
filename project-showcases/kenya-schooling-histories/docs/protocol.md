# Analysis protocol

Protocol version 0.1.0, prepared 3 October 2026. Prospective specification; no survey results available.

## Source and population
Use KEN_2022_K-LSRH_v01_M, Wave 1, 2022–2023, household-member file hhm.dta. Age 6–17 inclusive is a chosen analytical population. Keep household and member identifiers to test uniqueness. Do not use the selectively sampled child-respondent module. The target is the survey's supported refugee and nearby host populations, not all Kenyan children.

## Classification
| State | Operational rule | Meaning |
|---|---|---|
| A | out-of-school = 1 and ever-attended = 0 | Out of school with no previous attendance |
| B | out-of-school = 1 and ever-attended = 1 | Out of school after previous attendance |
| C | out-of-school = 0 with no unresolved diagnostic | Not classified as out of school |
| U | Missing/invalid core state or unresolved diagnostic | Unclassified |

The code flags out-of-school=0 with ever-attended=0 and out-of-school=1 with current-attendance=1. These provisional diagnostic rules are not assertions of error. Keep them in U until questionnaire/release review resolves them. Core fields use documented 0/1 labels; status codes must be supplied after checking actual labels. The questionnaire on page 32 separately asks about plans, current attendance, holidays and transitions. Do not interpret every absence as exit.

## Geography
| Location comparison | Refugee strata | Host strata |
|---|---|---|
| Turkana related | 1 and 2 pooled using weights | 3 |
| Dadaab related | 4 | 5 |
| Nairobi | 6 | 7 |
| Other Urban | 8 | 9 |

Use strata_actual for reporting, not as an assumed variance stratum. No host record is duplicated in pooling. Preserve Other Urban as released.

## Estimands and audit
For V = classified A/B/C children in each reporting group, pA = sum(weight × I[A])/sum(weight), over V; similarly for B and C. Overall out-of-school on this denominator is pA+pB. Refugee-minus-host gap O equals component gap A plus component gap B before rounding.

Report eligible, classified and unresolved n; eligible and classified weight; weighted U share over all eligible children E. Also show the direct out-of-school estimate over valid out-of-school responses and its separate denominator. If W is eligible weight, U unresolved weight, and WA observed A weight, bounds are WA/W to (WA+U)/W. These are missing-classification bounds, not confidence intervals and not bounds on measurement error.

Retain raw Stata missing objects on import; numeric conversion is only for analysis. Extended codes .a/.b/.c/.d/.e/.z must be recorded separately in local raw-code counts. Never interpret -77 Other as a missing value. Audit age missingness before selecting children. Eligible records with invalid weights or unresolvable geography stop execution.

## Extension and interpretation
Preselect age bands 6–11, 12–14 and 15–17. These are not claims about grade membership. Inspect cross-tabs of core and routing fields against the actual interview batch field once verified; never manufacture a batch field. Additional gender analysis is optional and not implemented in this first protocol. No exploratory search for a dramatic subgroup.

## Release gates
Complete validation.json using evidence. Review privacy and small cells, including disclosure by subtraction, before releasing aggregates. Match any benchmark's age definition, enrolment definition, weight and denominator before comparison. Generate Figure 1 (A/B/C composition) and Figure 2 (A and B by age) only after approved estimates exist. No illustrative bars stand in for real results. Full design variables remain unresolved; initial code produces point estimates only.
