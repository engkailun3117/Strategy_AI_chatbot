# Data Confirmation Flow Before Final Calculation

## Overview
Added a mandatory confirmation step that displays all collected data for user review before calculating the subsidy recommendation. This addresses two key UX issues:

1. **Prevents immediate calculation with preserved data**: When starting a new session with preserved data, the AI now shows a summary and asks for confirmation instead of immediately calculating
2. **Allows final review**: Users can review all their inputs and make corrections before seeing the final results

## Problem Statement

### Issue 1: Immediate Calculation with Preserved Data
**Scenario:**
1. User completes questionnaire and gets recommendation
2. User clicks "🆕 New Session" and chooses "保留資料"
3. New session has all data pre-filled
4. AI immediately calculates and shows results without asking anything

**Problem:** No opportunity to review or modify data in the new session

### Issue 2: No Confirmation Before Calculation
**Scenario:**
1. User answers all questions one by one
2. After last question, AI immediately calculates results

**Problem:** No chance to review all inputs or correct mistakes before final calculation

## Solution Implemented

### 1. Added Data Confirmation Field

**Database Schema:**
```sql
ALTER TABLE subsidy_consultations
ADD COLUMN data_confirmed BOOLEAN DEFAULT FALSE;
```

This tracks whether the user has confirmed their data is correct.

### 2. Updated Workflow

**New Flow:**
1. User answers all questions (or starts session with preserved data)
2. ✅ **NEW**: System shows complete data summary
3. ✅ **NEW**: Asks user to confirm: "請確認以上資料是否正確？"
4. User can either:
   - Confirm → AI calls `confirm_data()` → Auto-calculates → Shows results
   - Request correction → AI calls `update_subsidy_data()` → Shows updated summary again
5. Only after confirmation does calculation happen

### 3. Summary Display Format

When all fields are complete but not yet confirmed, the system shows:

```
太好了！我已經收集完所有資料。

請確認以下資訊是否正確：

計畫類型: 研發
預計所需經費: 5,000,000 元 (500 萬)
公司投保人數: 20 人
公司實收資本額: 10,000,000 元 (1000 萬)
公司年度營業額: 50,000,000 元 (5000 萬)
產品／服務取得第三方認證: 是
取得政府相關獎項: 否
產品為 MIT 生產: 是
有做產學合作: 是
有工廠登記證: 否
加分項目數量: 3 項
加分項目: 產品／服務取得第三方認證, 產品為 MIT 生產, 有做產學合作

如果以上資料都正確，請回覆「確認」或「正確」，我將為您計算補助方案。
如果需要修改任何資料，請直接告訴我要修改的項目。
```

## Implementation Details

### Backend Changes

#### 1. **New Function Declaration: `confirm_data`**

Added to Gemini function declarations:
```python
{
    "name": "confirm_data",
    "description": "使用者確認所有資料正確無誤。當使用者回覆「確認」、「正確」、「沒問題」、「可以」等確認詞時調用此函數。",
    "parameters": {
        "type": "object",
        "properties": {
            "confirmed": {
                "type": "boolean",
                "description": "使用者是否確認資料正確"
            }
        },
        "required": ["confirmed"]
    }
}
```

#### 2. **Updated `get_next_field_question()`**

```python
def get_next_field_question(self) -> str:
    # ... existing field checks ...

    # All required fields collected - show summary and ask for confirmation
    if not self.consultation_data.data_confirmed:
        summary = self.get_current_data_summary()
        return f"""太好了！我已經收集完所有資料。

請確認以下資訊是否正確：

{summary}

如果以上資料都正確，請回覆「確認」或「正確」，我將為您計算補助方案。
如果需要修改任何資料，請直接告訴我要修改的項目。"""

    # Data confirmed, ready to calculate
    return "資料收集完成！讓我為您計算適合的補助方案..."
```

#### 3. **Updated `process_message()` Function Call Handling**

```python
if "function_calls" in ai_result:
    for call in ai_result["function_calls"]:
        if call["name"] == "update_subsidy_data":
            if self.update_consultation_data(call["arguments"]):
                data_updated = True

        elif call["name"] == "confirm_data":
            # User confirmed the data is correct
            if call["arguments"].get("confirmed", False):
                self.consultation_data.data_confirmed = True
                self.db.commit()
                # Automatically trigger calculation after confirmation
                success, calc_result = self.calculate_and_save_subsidy()
                if success:
                    calculation_done = True
                    calculation_result = calc_result
                    completed = True

        elif call["name"] == "calculate_subsidy":
            # Only calculate if data has been confirmed
            if self.consultation_data.data_confirmed:
                success, calc_result = self.calculate_and_save_subsidy()
                if success:
                    calculation_done = True
                    calculation_result = calc_result
                    completed = True
            else:
                print("⚠️ Warning: calculate_subsidy called but data not confirmed yet")
```

#### 4. **Updated System Prompt**

Added section explaining the confirmation flow:
```
✅ **資料確認流程（重要！）**：
- 當收集完所有必要資料後，系統會自動顯示資料摘要並要求使用者確認
- 使用者會看到完整的資料清單
- 如果使用者回覆「確認」、「正確」、「沒問題」、「可以」、「OK」等確認詞：
  → 調用 confirm_data(confirmed=True) 函數
- 如果使用者要求修改某項資料：
  → 調用 update_subsidy_data 更新該欄位
  → 系統會重新顯示摘要要求確認
- 只有在使用者確認資料後，系統才會自動調用 calculate_subsidy 計算補助
- 絕對不要在使用者未確認資料時就計算補助
```

### Model Changes

**File:** `backend/models.py`

Added field to `SubsidyConsultation` model:
```python
data_confirmed = Column(Boolean, default=False, nullable=True)  # 使用者是否確認資料正確
```

Updated `to_dict()` to include `data_confirmed`.

### Migration Script

**File:** `backend/migration_add_confirmation_field.sql`

```sql
-- Add data_confirmed column
ALTER TABLE subsidy_consultations
ADD COLUMN IF NOT EXISTS data_confirmed BOOLEAN DEFAULT FALSE;

-- Set existing records to confirmed (backward compatibility)
UPDATE subsidy_consultations
SET data_confirmed = TRUE
WHERE grant_min IS NOT NULL OR grant_max IS NOT NULL;
```

## User Experience Examples

### Example 1: Normal Flow

```
User: "研發"
Bot: "收到！您選擇的是研發類型的計畫。請問您預計所需的經費是多少？"

User: "500萬"
Bot: "明白了，預計經費約 500 萬元。請問貴公司的投保人數有多少人？"

... [answers all questions] ...

User: "是" (last bonus question)
Bot: "很好！有完整的登記證明。

太好了！我已經收集完所有資料。

請確認以下資訊是否正確：

計畫類型: 研發
預計所需經費: 5,000,000 元 (500 萬)
公司投保人數: 20 人
...

如果以上資料都正確，請回覆「確認」或「正確」，我將為您計算補助方案。
如果需要修改任何資料，請直接告訴我要修改的項目。"

User: "確認"
Bot: [Shows full calculation results with subsidy recommendations]
```

### Example 2: Correction During Confirmation

```
... [summary shown] ...

User: "等等，預算應該是1000萬不是500萬"
Bot: "了解，已將經費更新為 1000 萬元。

請確認以下資訊是否正確：

計畫類型: 研發
預計所需經費: 10,000,000 元 (1000 萬)
公司投保人數: 20 人
...

如果以上資料都正確，請回覆「確認」或「正確」，我將為您計算補助方案。"

User: "正確"
Bot: [Shows calculation results]
```

### Example 3: New Session with Preserved Data

```
[User clicks "🆕 New Session" and chooses "保留資料"]

Bot: "已開始新對話並保留先前資料 (Session #5 → #6)

太好了！我已經收集完所有資料。

請確認以下資訊是否正確：

計畫類型: 行銷
預計所需經費: 5,000,000 元 (500 萬)
...

如果以上資料都正確，請回覆「確認」或「正確」，我將為您計算補助方案。
如果需要修改任何資料，請直接告訴我要修改的項目。"

User: "預算改成800萬，人數改成30人"
Bot: "了解，已將經費更新為 800 萬元。
     好的，已將投保人數更新為 30 人。

     請確認以下資訊是否正確：

     計畫類型: 行銷
     預計所需經費: 8,000,000 元 (800 萬)
     公司投保人數: 30 人
     ...

     如果以上資料都正確，請回覆「確認」或「正確」，我將為您計算補助方案。"

User: "OK"
Bot: [Shows calculation results]
```

## Confirmation Keywords

The AI recognizes these keywords as confirmation:
- 確認
- 正確
- 沒問題
- 可以
- OK
- 好
- 是的

## Benefits

1. **Transparency**: Users see exactly what data will be used for calculation
2. **Accuracy**: Opportunity to catch and fix errors before final results
3. **Trust**: Shows the system values user input and allows verification
4. **Better UX with Preserved Data**: Users can review and modify preserved data before calculating
5. **Prevents Errors**: Reduces chance of incorrect recommendations due to data entry mistakes

## Testing

### Test Case 1: Normal Flow with Confirmation
1. Answer all questions
2. Should see: Data summary with confirmation prompt
3. Reply: "確認"
4. Should see: Calculation results immediately

### Test Case 2: Correction During Confirmation
1. Complete all questions and see summary
2. Reply: "預算改成1000萬"
3. Should see: Updated summary with new budget
4. Reply: "確認"
5. Should see: Calculation results

### Test Case 3: New Session with Preserved Data
1. Complete questionnaire in session #1
2. Start new session with preserved data
3. Should see: Summary of preserved data immediately
4. Can modify or confirm
5. After confirmation, see calculation results

### Test Case 4: Multiple Corrections
1. See summary
2. Make correction #1
3. See updated summary
4. Make correction #2
5. See updated summary again
6. Confirm
7. See calculation results

## Migration Instructions

1. Run the SQL migration:
```bash
psql -U username -d database_name -f migration_add_confirmation_field.sql
```

2. Restart the backend server

3. Test the confirmation flow

## Files Modified

- `backend/models.py` - Added `data_confirmed` field
- `backend/subsidy_chatbot_handler.py` - Added confirmation logic
- `backend/migration_add_confirmation_field.sql` - Database migration
- `CONFIRMATION_FLOW.md` - This documentation

## Future Enhancements

- Allow editing specific fields inline during confirmation
- Show diff/changes when data is updated during confirmation
- Add "Preview Calculation" button before confirmation
- Support bulk edits during confirmation phase
- Add confirmation step timeout (auto-confirm after X minutes)
