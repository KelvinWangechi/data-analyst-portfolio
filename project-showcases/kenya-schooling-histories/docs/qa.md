# Quality and missing evidence

## Executed
- Read the attached research specification.
- Verified primary catalog, core variable labels, geography and login requirement.
- Retrieved original questionnaire and report; reviewed the education passages recorded in evidence_review.md.
- Ran six unit tests on artificial records: classification, weighted common denominators/bounds, all-unknown groups, age eligibility, bad weights/duplicate IDs, and inconsistent sample mappings. All passed.
- Code implements private aggregate outputs and fail-closed validation gates.

## Not executed
No household microdata import or empirical estimation. No real cross-tabs, source-release validation, sampling-design variance estimation, disclosure clearance or chart production. Tests are not validation against survey data.

## Required before findings
1. Download the approved `hhm.dta` roster through the official catalog and review actual access terms.
2. Inspect release labels, sample-status codes and extended missings. Verify supplied out-of-school construction with producer material.
3. Check questionnaire routing and contradictions; resolve interview-batch diagnostics and document any revised classification.
4. Validate household weights; obtain variance design information or retain the point-estimate-only limitation.
5. Execute the pipeline; reconcile denominators and additive gaps; inspect small cells and disclosure by subtraction.
6. Review the two-round report and original policy materials before expanding literature/policy claims.
7. Approve results, generate charts, replace CALC markers, and independently review the manuscript.

## Assistance record
AI assistance: source retrieval, evidence notes, code, tests and separate Word practice draft. No claim that the owner independently authored or executed the statistical analysis. Human review and applicant authorship remain separate tasks.
