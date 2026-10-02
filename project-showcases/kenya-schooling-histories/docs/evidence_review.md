# Evidence review and reading matrix

Accessed 3 October 2026 (Africa/Nairobi). Official questionnaire and report PDFs were retrieved; only the sections named below were reviewed. No microdata were downloaded.

| Source | Population and period | Definition and weighting | Passage reviewed | Overlap or limit |
|---|---|---|---|---|
| K-LSRH catalog, Wave 1 | Refugee and host samples, 2022–2023 | Household roster; household weight `weight` | Identification, Sampling, Weighting, Data Access | Supports design; not national child prevalence |
| Roster variable pages | Household members | Ever attendance and supplied out-of-school indicator coded 0/1; nine actual-location strata | V30, V62 and V12 labels | Web frequencies are unweighted cases, not project results |
| Survey instrument | Roster members and routed child items | Q15 ever attendance; Q17 enrolment/plans; Q18–20 attendance/reasons/plans | Printed pp. 32 and 35–36 | Verifies distinction between absence and exit; does not establish supplied indicator construction |
| World Bank 2024 report | Wave 1; primary-age population | Fig. 21 age definition includes curriculum-specific exceptions; Fig. 22 denominator is non-enrolled primary-age children | Printed pp. 23–25, Figures 21–24 | Existing schooling-history analysis; proposed fixed-age/common-denominator extension needs microdata |
| Two-round report lead | Not verified | Not verified | Landing page only, no usable report text | Read before claiming novelty or using later-wave findings |
| Shirika Plan lead | Later policy context | Not verified | UNHCR page returned rate limit | No policy provisions or implementation findings asserted |

The original report states that its reason data come from a small non-representative out-of-school sample and do not explain low enrolment among never-attenders (p. 25). Reasons should not be generalized to category A. The questionnaire itself must still be reconciled with released missing codes and actual eligibility.

## Source links
- Catalog and citation: https://microdata.worldbank.org/index.php/catalog/6409
- Access: https://microdata.worldbank.org/catalog/6409/get-microdata
- Questionnaire: https://microdata.worldbank.org/catalog/6409/download/180509
- Report: https://microdata.worldbank.org/catalog/6409/download/180510
- Ever attended: https://microdata.worldbank.org/catalog/6409/variable/F1/V30?name=a4a_everattendschool
- Out-of-school: https://microdata.worldbank.org/catalog/6409/variable/F1/V62?name=a4_outofschool
- Geography: https://microdata.worldbank.org/catalog/6409/variable/F1/V12?name=strata_actual
- Follow-up reading lead: https://documents.worldbank.org/en/publication/documents-reports/documentdetail/099021726065512383

## Claim ledger
| Claim | Evidence | Status |
|---|---|---|
| Use the member roster and household weight | Catalog file descriptions and Weighting | Documentation verified; release not inspected |
| Absence and exit differ in questionnaire routing | Instrument p. 32 | Verified |
| Earlier analysis already distinguishes never-attendance | Report p. 24, Fig. 22 | Verified |
| New refugee-host component gap | `estimates.csv` and `gaps.csv` from approved run | Not calculated |
| Age differences | Approved age-group estimates | Not calculated |
| Causes or effectiveness of policy | Requires separate identification evidence | Not identified by this protocol |
