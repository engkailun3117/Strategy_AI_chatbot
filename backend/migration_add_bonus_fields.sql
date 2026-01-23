-- Migration: Add individual bonus item fields to subsidy_consultations table
-- Date: 2026-01-22
-- Description: Replace generic bonus_count/bonus_details with specific boolean fields for each bonus item

-- Add new boolean columns for specific bonus items (nullable, no default)
ALTER TABLE subsidy_consultations
ADD COLUMN IF NOT EXISTS has_certification BOOLEAN,
ADD COLUMN IF NOT EXISTS has_gov_award BOOLEAN,
ADD COLUMN IF NOT EXISTS is_mit BOOLEAN,
ADD COLUMN IF NOT EXISTS has_industry_academia BOOLEAN,
ADD COLUMN IF NOT EXISTS has_factory_registration BOOLEAN;

-- Add comment to explain the new fields
COMMENT ON COLUMN subsidy_consultations.has_certification IS '是否產品／服務取得第三方認證';
COMMENT ON COLUMN subsidy_consultations.has_gov_award IS '是否取得政府相關獎項';
COMMENT ON COLUMN subsidy_consultations.is_mit IS '產品是否為 MIT 生產';
COMMENT ON COLUMN subsidy_consultations.has_industry_academia IS '是否有做產學合作';
COMMENT ON COLUMN subsidy_consultations.has_factory_registration IS '是否有工廠登記證';
