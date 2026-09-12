PRAGMA foreign_keys=ON;
CREATE TABLE customers (
 customer_id TEXT PRIMARY KEY,
 schedule TEXT NOT NULL CHECK(schedule IN ('Changing schedule','Regular schedule')),
 tenure TEXT NOT NULL CHECK(tenure IN ('New','Established'))
);
CREATE TABLE invitations (
 invitation_id TEXT PRIMARY KEY,
 customer_id TEXT NOT NULL UNIQUE REFERENCES customers(customer_id),
 responded INTEGER NOT NULL CHECK(responded IN (0,1))
);
CREATE TABLE responses (
 response_id TEXT PRIMARY KEY,
 customer_id TEXT NOT NULL UNIQUE REFERENCES customers(customer_id),
 reason TEXT NOT NULL,
 satisfaction INTEGER NOT NULL CHECK(satisfaction BETWEEN 1 AND 5),
 text TEXT NOT NULL,
 question_version TEXT NOT NULL
);
CREATE TABLE assignments (
 response_id TEXT NOT NULL REFERENCES responses(response_id),
 theme_id TEXT NOT NULL,
 sentiment TEXT NOT NULL CHECK(sentiment IN ('negative','positive','mixed','neutral','unclear')),
 evidence_quote TEXT NOT NULL CHECK(LENGTH(evidence_quote)>0),
 PRIMARY KEY(response_id,theme_id)
);
CREATE TABLE orders (
 order_id TEXT PRIMARY KEY,
 customer_id TEXT NOT NULL REFERENCES customers(customer_id),
 week INTEGER NOT NULL CHECK(week BETWEEN 1 AND 12),
 status TEXT NOT NULL CHECK(status IN ('completed','skipped','late')),
 meals INTEGER NOT NULL CHECK(meals>=0),
 UNIQUE(customer_id,week)
);
