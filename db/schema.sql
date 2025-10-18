-- Products table
CREATE TABLE products (
  product_code TEXT PRIMARY KEY,
  product_name TEXT,
  product_family TEXT,
  underwriting_class TEXT,
  waiting_period_days INTEGER
);

-- Policies table
CREATE TABLE policies (
  policy_id INTEGER PRIMARY KEY,
  product_code TEXT REFERENCES products(product_code),
  cover_type TEXT CHECK (cover_type IN ('life','health')),
  sum_assured NUMERIC,
  start_date DATE,
  end_date DATE,
  premium_freq TEXT CHECK (premium_freq IN ('M','Q','A')),
  premium_amount NUMERIC,
  channel TEXT
);

-- Members table
CREATE TABLE members (
  member_id INTEGER PRIMARY KEY,
  policy_id INTEGER REFERENCES policies(policy_id),
  gender TEXT CHECK (gender IN ('M','F')),
  birth_date DATE,
  region TEXT,
  smoker_flag BOOLEAN,
  bmi NUMERIC,
  join_date DATE
);

-- Claims table
CREATE TABLE claims (
  claim_id INTEGER PRIMARY KEY,
  member_id INTEGER REFERENCES members(member_id),
  policy_id INTEGER REFERENCES policies(policy_id),
  claim_date DATE,
  notification_date DATE,
  diagnosis_code TEXT,
  claim_type TEXT,
  status TEXT,
  initial_reserve NUMERIC,
  approved_amount NUMERIC,
  paid_amount NUMERIC,
  close_date DATE
);

-- Claim Payments
CREATE TABLE claim_payments (
  payment_id INTEGER PRIMARY KEY,
  claim_id INTEGER REFERENCES claims(claim_id),
  payment_date DATE,
  payment_amount NUMERIC
);

-- Premiums Ledger
CREATE TABLE premiums_ledger (
  policy_id INTEGER REFERENCES policies(policy_id),
  period_month TEXT,  -- 'YYYY-MM'
  earned_premium NUMERIC,
  PRIMARY KEY (policy_id, period_month)
);

-- Calendar
CREATE TABLE calendar (
  dt DATE PRIMARY KEY,
  month INTEGER,
  quarter INTEGER,
  year INTEGER
);
