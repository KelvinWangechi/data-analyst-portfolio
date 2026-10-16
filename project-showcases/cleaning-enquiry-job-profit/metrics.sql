-- SQLite starter model. All currency fields are integer USD cents.
-- One enquiry and at most one job per business scenario.
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS enquiries (
  enquiry_id TEXT PRIMARY KEY,
  customer_name TEXT NOT NULL,
  email TEXT,
  property_address TEXT,
  service TEXT NOT NULL,
  received_date TEXT NOT NULL,
  validation_status TEXT NOT NULL CHECK(validation_status IN ('Valid','Invalid')),
  outcome TEXT NOT NULL CHECK(outcome IN ('Won','Lost','Open','Invalid')),
  quote_cents INTEGER,
  quote_status TEXT NOT NULL,
  approved_by TEXT,
  customer_accepted INTEGER NOT NULL CHECK(customer_accepted IN (0,1)),
  notes TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS jobs (
  job_id TEXT PRIMARY KEY,
  enquiry_id TEXT NOT NULL UNIQUE REFERENCES enquiries(enquiry_id),
  status TEXT NOT NULL CHECK(status IN ('Completed','Scheduled')),
  completed_date TEXT,
  revenue_cents INTEGER,
  person_hours REAL,
  loaded_hourly_cost_cents INTEGER,
  materials_cents INTEGER,
  other_direct_cents INTEGER,
  time_verified INTEGER NOT NULL CHECK(time_verified IN (0,1)),
  costs_confirmed INTEGER NOT NULL CHECK(costs_confirmed IN (0,1)),
  exception_owner TEXT,
  notes TEXT NOT NULL,
  CHECK(person_hours IS NULL OR person_hours >= 0),
  CHECK(revenue_cents IS NULL OR revenue_cents >= 0),
  CHECK(materials_cents IS NULL OR materials_cents >= 0),
  CHECK(other_direct_cents IS NULL OR other_direct_cents >= 0)
);
CREATE TRIGGER IF NOT EXISTS approved_job_insert
BEFORE INSERT ON jobs
WHEN NOT EXISTS (
  SELECT 1 FROM enquiries e WHERE e.enquiry_id = NEW.enquiry_id
  AND e.validation_status = 'Valid' AND e.outcome = 'Won'
  AND e.quote_status = 'Approved' AND COALESCE(e.approved_by,'') <> ''
  AND e.customer_accepted = 1
)
BEGIN SELECT RAISE(ABORT,'Job requires valid enquiry, human quote approval and customer acceptance'); END;
CREATE TRIGGER IF NOT EXISTS approved_job_update
BEFORE UPDATE ON jobs
WHEN NOT EXISTS (
  SELECT 1 FROM enquiries e WHERE e.enquiry_id = NEW.enquiry_id
  AND e.validation_status = 'Valid' AND e.outcome = 'Won'
  AND e.quote_status = 'Approved' AND COALESCE(e.approved_by,'') <> ''
  AND e.customer_accepted = 1
)
BEGIN SELECT RAISE(ABORT,'Job requires valid enquiry, human quote approval and customer acceptance'); END;
CREATE TABLE IF NOT EXISTS processed_events (
  source TEXT NOT NULL,
  event_id TEXT NOT NULL,
  entity_id TEXT NOT NULL,
  result TEXT NOT NULL,
  PRIMARY KEY(source,event_id)
);
DROP VIEW IF EXISTS job_review;
CREATE VIEW job_review AS
SELECT j.*,
  CASE WHEN status = 'Completed'
    AND completed_date IS NOT NULL AND revenue_cents IS NOT NULL AND revenue_cents > 0
    AND person_hours IS NOT NULL AND person_hours > 0 AND time_verified = 1
    AND loaded_hourly_cost_cents IS NOT NULL AND loaded_hourly_cost_cents >= 0
    AND materials_cents IS NOT NULL AND other_direct_cents IS NOT NULL
    AND costs_confirmed = 1 THEN 1 ELSE 0 END AS verified,
  CASE WHEN person_hours IS NOT NULL AND loaded_hourly_cost_cents IS NOT NULL
    THEN ROUND(person_hours * loaded_hourly_cost_cents) END AS labor_cents,
  CASE WHEN status <> 'Completed' THEN 'Awaiting completion'
    WHEN completed_date IS NULL THEN 'Missing completion date'
    WHEN revenue_cents IS NULL OR revenue_cents <= 0 THEN 'Missing or zero revenue'
    WHEN person_hours IS NULL OR person_hours <= 0 OR time_verified = 0 THEN 'Time not verified'
    WHEN loaded_hourly_cost_cents IS NULL THEN 'Missing loaded labor rate'
    WHEN materials_cents IS NULL THEN 'Missing material cost'
    WHEN other_direct_cents IS NULL THEN 'Missing other direct cost'
    WHEN costs_confirmed = 0 THEN 'Costs awaiting confirmation'
    ELSE 'Verified' END AS review_status
FROM jobs j;
DROP VIEW IF EXISTS verified_jobs;
CREATE VIEW verified_jobs AS
SELECT *, labor_cents + materials_cents + other_direct_cents AS direct_cost_cents,
  revenue_cents - labor_cents - materials_cents - other_direct_cents AS direct_profit_cents,
  1.0 * (revenue_cents - labor_cents - materials_cents - other_direct_cents) / revenue_cents AS direct_margin
FROM job_review WHERE verified = 1;
DROP VIEW IF EXISTS exceptions;
CREATE VIEW exceptions AS
SELECT job_id, enquiry_id, revenue_cents, exception_owner, review_status
FROM job_review WHERE status = 'Completed' AND verified = 0;
DROP VIEW IF EXISTS cohort_kpis;
CREATE VIEW cohort_kpis AS
WITH pipeline AS (
  -- Fixed enquiry cohort, outcomes as of 11 October 2026.
  SELECT COUNT(*) AS enquiries, SUM(outcome='Won') AS won, SUM(outcome='Lost') AS lost
  FROM enquiries WHERE received_date >= '2026-10-05' AND received_date < '2026-10-12'
), completed AS (
  SELECT COUNT(*) AS completed_jobs, SUM(revenue_cents) AS completed_revenue_cents
  FROM jobs WHERE status='Completed' AND completed_date >= '2026-10-05' AND completed_date < '2026-10-12'
), verified AS (
  SELECT COUNT(*) AS verified_jobs, SUM(revenue_cents) AS verified_revenue_cents,
    SUM(person_hours) AS verified_person_hours, SUM(direct_cost_cents) AS verified_direct_cost_cents,
    SUM(direct_profit_cents) AS verified_direct_profit_cents
  FROM verified_jobs WHERE completed_date >= '2026-10-05' AND completed_date < '2026-10-12'
)
SELECT p.*, c.*, v.*,
  1.0 * won / NULLIF(won + lost,0) AS close_rate,
  1.0 * verified_jobs / NULLIF(completed_jobs,0) AS cost_coverage,
  1.0 * verified_revenue_cents / 100 / NULLIF(verified_person_hours,0) AS revenue_per_person_hour,
  1.0 * verified_direct_profit_cents / NULLIF(verified_revenue_cents,0) AS direct_margin
FROM pipeline p CROSS JOIN completed c CROSS JOIN verified v;
DROP VIEW IF EXISTS daily_job_kpis;
CREATE VIEW daily_job_kpis AS
SELECT completed_date, COUNT(*) AS completed_jobs, SUM(revenue_cents) AS completed_revenue_cents,
  SUM(verified) AS verified_jobs,
  SUM(CASE WHEN verified=1 THEN revenue_cents ELSE 0 END) AS verified_revenue_cents,
  SUM(CASE WHEN verified=1 THEN person_hours ELSE 0 END) AS verified_person_hours,
  SUM(CASE WHEN verified=1 THEN labor_cents + materials_cents + other_direct_cents ELSE 0 END) AS verified_direct_cost_cents,
  1.0 * SUM(CASE WHEN verified=1 THEN revenue_cents ELSE 0 END) / 100 /
    NULLIF(SUM(CASE WHEN verified=1 THEN person_hours ELSE 0 END),0) AS revenue_per_person_hour,
  1.0 * SUM(CASE WHEN verified=1 THEN revenue_cents - labor_cents - materials_cents - other_direct_cents ELSE 0 END) /
    NULLIF(SUM(CASE WHEN verified=1 THEN revenue_cents ELSE 0 END),0) AS direct_margin
FROM job_review WHERE status='Completed' GROUP BY completed_date;
