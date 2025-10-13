-- Monthly claims (count + paid)
CREATE VIEW IF NOT EXISTS vw_claims_monthly AS
SELECT
  substr(claim_date,1,7) AS month,
  claim_type,
  COUNT(*) AS claim_count,
  SUM(paid_amount) AS paid_sum
FROM claims
GROUP BY month, claim_type;

-- Monthly loss ratio (paid / earned)
CREATE VIEW IF NOT EXISTS vw_loss_ratio_monthly AS
WITH paid AS (
  SELECT substr(claim_date,1,7) AS month, SUM(paid_amount) AS paid
  FROM claims
  GROUP BY month
),
prem AS (
  SELECT period_month AS month, SUM(earned_premium) AS earned
  FROM premiums_ledger
  GROUP BY month
)
SELECT
  prem.month,
  earned,
  COALESCE(paid.paid,0) AS paid,
  CASE WHEN earned > 0 THEN ROUND(paid.paid / earned, 4) ELSE NULL END AS loss_ratio
FROM prem
LEFT JOIN paid ON paid.month = prem.month
ORDER BY prem.month;

-- Member risk features (simple)
CREATE VIEW IF NOT EXISTS vw_member_risk AS
SELECT
  m.member_id,
  m.gender,
  m.region,
  m.smoker_flag,
  m.bmi,
  CAST(strftime('%Y','2025-09-30') AS INTEGER) - CAST(strftime('%Y', m.birth_date) AS INTEGER) AS age,
  COUNT(c.claim_id) AS past_claims
FROM members m
LEFT JOIN claims c ON c.member_id = m.member_id
GROUP BY m.member_id;

-- Top-level KPIs
CREATE VIEW IF NOT EXISTS vw_paid_kpis AS
SELECT
  SUM(pl.earned_premium) AS earned,
  SUM(cp.payment_amount) AS paid,
  CASE WHEN SUM(pl.earned_premium) = 0 THEN 0
       ELSE ROUND(SUM(cp.payment_amount) * 1.0 / SUM(pl.earned_premium), 4)
  END AS loss_ratio
FROM premiums_ledger pl
LEFT JOIN policies p ON p.policy_id = pl.policy_id
LEFT JOIN claims cl ON cl.policy_id = p.policy_id
LEFT JOIN claim_payments cp ON cp.claim_id = cl.claim_id;

-- Monthly claims by type (for tab 2)
CREATE VIEW IF NOT EXISTS vw_monthly_claims_by_type AS
SELECT
  substr(claim_date,1,7) AS month,
  claim_type,
  COUNT(*) AS num_claims
FROM claims
GROUP BY month, claim_type
ORDER BY month, claim_type;

-- Portfolio View: Members + Policies + Products
DROP VIEW IF EXISTS vw_member_portfolio;

CREATE VIEW vw_member_portfolio AS
SELECT
  m.member_id,
  m.gender,
  m.region,
  m.smoker_flag,
  m.bmi,
  m.policy_id,
  p.product_code,
  pr.product_family
FROM members m
JOIN policies p ON m.policy_id = p.policy_id
JOIN products pr ON p.product_code = pr.product_code;


-- Portfolio Filters
DROP VIEW IF EXISTS vw_claims_enriched;

CREATE VIEW vw_claims_enriched AS
SELECT
  c.claim_id,
  c.claim_date,
  c.claim_type,
  c.paid_amount,
  c.approved_amount,
  m.gender,
  m.region,
  m.smoker_flag,
  p.product_code,
  pr.product_family
FROM claims c
JOIN members m ON c.member_id = m.member_id
JOIN policies p ON m.policy_id = p.policy_id
JOIN products pr ON p.product_code = pr.product_code;





