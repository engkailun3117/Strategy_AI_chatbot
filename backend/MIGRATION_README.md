# Database Migration: Add Individual Bonus Item Fields

## Overview
This migration adds individual boolean fields for each bonus item to the `subsidy_consultations` table, replacing the generic `bonus_count` and `bonus_details` approach with explicit yes/no questions.

## New Fields
- `has_certification` - 是否產品／服務取得第三方認證
- `has_gov_award` - 是否取得政府相關獎項
- `is_mit` - 產品是否為 MIT 生產
- `has_industry_academia` - 是否有做產學合作
- `has_factory_registration` - 是否有工廠登記證

## How to Run the Migration

### Option 1: Using psql (Recommended)
```bash
psql -U <username> -d <database_name> -f migration_add_bonus_fields.sql
```

### Option 2: Using the Backend Application
If you have a database management script, you can run:
```bash
python -c "from database import engine; engine.execute(open('migration_add_bonus_fields.sql').read())"
```

## Changes Made
1. **Database Model** (`models.py`):
   - Added 5 new Boolean columns to `SubsidyConsultation` model
   - Updated `to_dict()` to include new fields
   - Updated `to_export_format()` to display as "是"/"否"

2. **Chatbot Handler** (`subsidy_chatbot_handler.py`):
   - Updated function declarations to accept boolean bonus fields
   - Modified system prompt to ask about each bonus item individually
   - Updated `get_next_field_question()` to ask 5 separate yes/no questions
   - Updated `update_consultation_data()` to handle boolean responses
   - Added `_update_bonus_count_and_details()` to auto-calculate legacy fields

## User Experience Changes
**Before:**
- Single question: "請問貴公司有哪些加分項目？（例如：專利、認證、技術創新等，最多5項）"
- User had to know and list all items

**After:**
- 5 separate questions:
  1. "請問貴公司的產品／服務是否取得第三方認證？（請回答「是」或「否」）"
  2. "請問貴公司是否取得政府相關獎項？（請回答「是」或「否」）"
  3. "請問貴公司的產品是否為 MIT 生產？（請回答「是」或「否」）"
  4. "請問貴公司是否有做產學合作？（請回答「是」或「否」）"
  5. "請問貴公司是否有工廠登記證？（請回答「是」或「否」）"
- Simple yes/no answers required

## Backward Compatibility
The legacy `bonus_count` and `bonus_details` fields are preserved and automatically calculated from the individual boolean fields, ensuring compatibility with existing reports and exports.

## Testing
After running the migration, test by:
1. Starting a new chat session
2. Answering the bonus questions one by one with "是" or "否"
3. Verifying the data is saved correctly
4. Checking that `bonus_count` is calculated correctly (count of "是" answers)
