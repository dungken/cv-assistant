-- Tuần 16 — extend jd_raw with parsed signal columns.
-- Idempotent: safe to run multiple times against an existing DB.

ALTER TABLE jd_raw ADD COLUMN IF NOT EXISTS min_exp INTEGER;
ALTER TABLE jd_raw ADD COLUMN IF NOT EXISTS max_exp INTEGER;
ALTER TABLE jd_raw ADD COLUMN IF NOT EXISTS seniority VARCHAR(16);
ALTER TABLE jd_raw ADD COLUMN IF NOT EXISTS skills_required JSONB DEFAULT '[]'::jsonb;
ALTER TABLE jd_raw ADD COLUMN IF NOT EXISTS skills_preferred JSONB DEFAULT '[]'::jsonb;
ALTER TABLE jd_raw ADD COLUMN IF NOT EXISTS degree_required VARCHAR(64);
ALTER TABLE jd_raw ADD COLUMN IF NOT EXISTS work_mode VARCHAR(16);
ALTER TABLE jd_raw ADD COLUMN IF NOT EXISTS description_summary TEXT;
ALTER TABLE jd_raw ADD COLUMN IF NOT EXISTS parsed_at TIMESTAMP;
ALTER TABLE jd_raw ADD COLUMN IF NOT EXISTS parse_version VARCHAR(16);

CREATE INDEX IF NOT EXISTS idx_jd_seniority ON jd_raw (seniority);
CREATE INDEX IF NOT EXISTS idx_jd_parsed ON jd_raw (parsed_at);

-- Tuần 16 — extend skill_user_cv with personal-preference columns
ALTER TABLE skill_user_cv ADD COLUMN IF NOT EXISTS years_experience DOUBLE PRECISION;
ALTER TABLE skill_user_cv ADD COLUMN IF NOT EXISTS preferred_location VARCHAR(128);
ALTER TABLE skill_user_cv ADD COLUMN IF NOT EXISTS preferred_work_modes JSONB DEFAULT '[]'::jsonb;
