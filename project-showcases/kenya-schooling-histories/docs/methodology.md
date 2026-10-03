# Data, definitions and analytical limits

## Provenance

This analysis uses the actual anonymised household-member roster (`hhm.dta`) from K-LSRH Wave 1, **KEN_2022_K-LSRH_v01_M**, covering 2022–2023. It was downloaded through the World Bank’s approved public-use process on 4 October 2026. The release contains 45,011 roster members in 9,304 households; 16,472 members in 5,605 households have recorded ages 6–17. No simulated observations enter the findings. Raw data remain local and are not redistributed.

**Dataset citation:** Precious Zikhali, Nistha Sinha, Utz Pape, Theresa Beltramo and Edward Miguel. *Kenya — Longitudinal Socioeconomic Study of Refugees and Host Communities 2022–2023, Wave 1*. Ref. KEN_2022_K-LSRH_v01_M. [World Bank Microdata Library](https://microdata.worldbank.org/catalog/6409), [DOI](https://doi.org/10.48529/x4g6-9k44). Downloaded 4 October 2026.

## What the outcome measures

The primary outcome is the producer’s released `a4_outofschool` indicator, labelled “out of school system (never attended or no longer in school)”. It is decomposed using `a4a_everattendschool`:

| State | Rule | Interpretation |
|---|---|---|
| A | Out-of-school = 1; ever-attended = 0 | Out of school without previous attendance |
| B | Out-of-school = 1; ever-attended = 1 | Out of school with previous attendance |
| C | Out-of-school = 0; no contradictory schooling diagnostic | Not classified as out of the school system |
| U | Missing required classification or contradictory schooling responses | Unclassified |

C is not daily attendance, learning achievement, or enrolment in an age-appropriate grade. A child may count as in the school system while planning to enrol when school reopens. B is not a measured dropout event or a statement of permanent exit.

Questionnaire p. 32 distinguishes ever-attendance (Q15), current/planned enrolment (Q17: 1 current, 2 planned, 3 neither), current attendance (Q18), reasons for absence (Q19), and holiday return plans (Q20). The released indicator agrees with `ever-attended = 0 OR Q17 = 3` for all but one of the 16,472 age-eligible children. This is an empirical reconciliation, not a claim to possess the producer’s construction code. The contradictory record reports never-attendance but is coded in the school system; it remains U. A separate child with missing ever-attendance has current enrolment and attendance and a valid in-system indicator; that record remains C without imputing its history.

Fifty-nine children are coded in the system but report permanent exit, or holidays with no plan to return. The sensitivity calculation moves these to B. The main estimate continues to use the released indicator; the alternative is not presented as a verified correction to the source data.

## Denominators and weights

For each location/sample/age group, V contains classified A, B and C records. Each component is `100 × sum(household weight for that state) / sum(household weight over V)`. Total exclusion O = A + B. A share *within the out-of-school population* uses A/(A+B) or B/(A+B) and is explicitly identified as such in the narrative.

The household weight is assigned to each eligible roster member, making the estimates child-level proportions. It is not replaced by representative-respondent or selected-child-module weights. Arithmetic uses float64 sums; component identities and group gaps are checked before rounding. Unweighted n is the actual contributing record count, not the estimated population size.

The primary classified denominator has 16,471 children. The one unresolved child is in Turkana hosts and represents 0.0932% of that group’s eligible weight. Assigning it either in or out yields overall bounds of 40.3390%–40.4322%, compared with the classified estimate of 40.3767%. Bounds only address this classification uncertainty.

Ages in years are missing for 585 roster members. Of these, 237 have ages recorded in months from 1 to 12; the remaining 348 lack a usable age-in-years/months value. They are excluded from the fixed-age population without assuming that all are adults. The classification bounds do not cover age-eligibility uncertainty or other measurement error.

## Geography and sample membership

Comparisons use released `strata_actual`: Kakuma and Kalobeyei refugee strata are pooled with their original weights and compared with Turkana hosts; Dadaab, Nairobi and Other Urban are paired separately. The host sample is included once in each comparison. Other Urban covers the release’s Nakuru/Mombasa sample; it is not every other Kenyan city.

The sampling strata and the label attached to the household respondent are not perfectly interchangeable. Six age-eligible records in refugee strata have a host respondent-status label. The released location/sample grouping is retained for the main analysis, consistent with `groups_location_status`. Excluding the six changes the Turkana refugee estimate by 0.0022 percentage points and the Nairobi refugee estimate by 0.0128 points. No person is reassigned to a different sampling frame or given a new weight.

The host sampling areas are defined by proximity to camps or selected urban neighbourhoods. Results are not county-wide or national prevalence. Within-location gaps are unadjusted descriptive differences: age, household characteristics, migration histories and selection can differ across samples.

## Robustness and uncertainty

[The sensitivity table](../outputs/sensitivity.csv) reports the released-indicator baseline, exclusion of status discrepancies, and an alternative including explicit exit/no-return signals. The largest change under the exit alternative is 1.1985 percentage points for Dadaab refugees (59.8774% to 61.0758%). All four overall gap directions remain unchanged.

No confidence intervals or p-values are reported. Hosts were cluster-sampled and refugees drawn from overlapping frames; treating individual children as independent would give an unjustified precision claim. Released reporting strata are not assumed to be survey variance strata. The analysis does not claim that the Dadaab 2.4-point difference, or any other gap, is statistically distinguishable from zero.

Age groups 6–11, 12–14 and 15–17 are fixed age ranges, not grade membership. Differences between them are cross-sectional. The World Bank report’s primary-age definition has curriculum-specific exceptions, so its Figures 21–22 are contextual evidence, not numerical validation targets for these fixed-age estimates.

## Disclosure and interpretation

The public release withholds A and B together wherever either is supported by fewer than five records. Where an age component triggers the rule, all age detail for that location/sample family is withheld to prevent subtraction from totals. The resulting public table contains 23 rows: eight overall groups and 15 age-group rows. Urban host components and Other Urban refugee age details are not published. Individual identifiers, exact event counts, granular routing tables, raw-code frequencies and private run manifests are excluded. The threshold is a conservative project rule, not a claim of formal disclosure certification or a substitute for reviewing the combination of outputs.

The study does not establish the causes of exclusion, estimate programme impact, or describe current service conditions. The targeted child-respondent module selects enrolled children and is not used to estimate exclusion. Reasons reported by selected respondents are not generalized to never-attenders. Suggested first-entry and re-entry responses are implications to investigate, not interventions evaluated here.
