-- Migration: Add data confirmation field to subsidy_consultations table
-- Date: 2026-01-22
-- Description: Add data_confirmed boolean field to track whether user has confirmed their data before calculation

-- Add data_confirmed column
ALTER TABLE subsidy_consultations
ADD COLUMN IF NOT EXISTS data_confirmed BOOLEAN DEFAULT FALSE;

-- Add comment to explain the field
COMMENT ON COLUMN subsidy_consultations.data_confirmed IS '使用者是否確認資料正確';

-- Set existing records to confirmed (backward compatibility)
UPDATE subsidy_consultations
SET data_confirmed = TRUE
WHERE grant_min IS NOT NULL OR grant_max IS NOT NULL;
