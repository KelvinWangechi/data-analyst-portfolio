# Cleaning Enquiry to Job Profit

A cleaning owner sees $9,500 in completed jobs. Two jobs still have
missing costs. How much profit can the owner confidently report, and who needs
to follow up?

[Open the interactive case](https://kelvinwangechi.github.io/data-analyst-portfolio/project-showcases/cleaning-enquiry-job-profit/)

The Salesforce core connects validated enquiries, customer contacts and estimator
tasks to human quote approval, customer acceptance, jobs and verified owner reports.
Unique enquiry and accepted-quote keys prevent duplicate handoffs and jobs.

The public enquiry form writes to the Salesforce through a
restricted HTTPS service on the owner's VPS. The existing record-triggered
`Cleaning_Enquiry_Handoff` Flow matches or creates a Contact and creates the
estimator Task. The service reads those records back and checks the Task's
enquiry and contact links before confirming the receipt. Approval and customer
acceptance stay inside Salesforce; the public API exposes no job or approval writes.

Your browser stores a private receipt key and submission UUID, not your form
details. The receipt can be refreshed after an owner action in Salesforce.
Replay submits the same source reference and reuses the enquiry and handoff.
Submissions are retained in Salesforce for verification.

The reporting section is a saved, reconciled historical snapshot. Date filters,
missing-cost what-if exercises and owner briefings run locally. New live enquiries
are outside its labelled historical cohort and do not alter those figures.

## Reporting cohort

- 25 enquiry scenarios: 23 validated CRM enquiries and two rejected intake events.
- 15 won, six lost, two open: close rate 15 / (15 + 6) = 71.43%.
- Enquiry dates: 5–7 October 2026; completed job dates: 6–11 October 2026.
- 15 jobs: 12 completed and three scheduled. Completed revenue: USD 9,500.
- Ten verified jobs: USD 8,000 revenue, 100 person-hours and USD 4,800 direct costs.
- Weighted direct margin: 40%, before overhead and tax. Revenue/person-hour: USD 80.
- JOB-011 lacks other direct cost; JOB-012 lacks material cost. Unknown costs
  remain absent from verified profit metrics.

## Actual integration example

Authenticated Salesforce REST queries through MCP extracted the CRM,
job and rejected-event records. Captured responses were transformed into SQLite,
where verification status, direct costs and direct profit were independently
compared with the Salesforce formulas before producing the reporting snapshot.

`metrics.sql` contains the reporting model used in that reconciliation.
`verified-reporting.json` is the sanitized output, extracted on 11 October 2026
at 18:58:09 UTC. It contains no Salesforce record IDs or customer contacts.
Job-level direct costs and loaded hourly rates were added from the same captured
REST response to support the browser what-if calculation.

This is a Salesforce integration example, not Workiz. Reporting extraction was
on demand; scheduled reporting sync and outbound Slack delivery are not configured.
Quote approval is performed inside Salesforce.

## Live intake integration

`integration/app.py` and `integration/test_intake.py` show the actual adapter
and its automated checks. Credentials are held only in a private VPS file and
are never included in GitHub Pages or the receipt. Input fields are allowlisted;
submission limits and a honeypot reduce casual abuse. This public demo is limited
to five new enquiries per IP per hour and fifty per day across all viewers.

The server stores keyed hashes for receipt possession, payload replay checks and
IP limits, plus source references and timestamps. Customer details live in
Salesforce. Keep the private receipt key in the original browser; it cannot be
recovered from the public reference alone.

Two real HTTPS submissions with the same UUID were read back successfully on
19 October 2026: one enquiry, one estimator task, quote Pending, no job. Thirteen
automated adapter tests cover concurrent replay, lost responses, invalid input,
private receipts, task relationship checks and submission limits.

## Run locally

From this directory, run `python -m http.server 8000` and open
`http://localhost:8000/`. Serve the directory over HTTP so the JSON fetch works.
The production intake service allows the GitHub Pages origin; local previews
can inspect reporting and layout but cannot submit to that service.

Enquiry names use `enq-YYYY-MM-DD-NNN`, with a daily counter in
`America/Los_Angeles` time. The counter survives service restarts; replay retains
the original name. A separate unique source ID prevents duplicate handoffs.
