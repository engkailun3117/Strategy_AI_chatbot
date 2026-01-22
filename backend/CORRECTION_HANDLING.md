# Data Correction & Update Handling

## Overview
The chatbot now fully supports users correcting or modifying their previously entered data during the conversation. No need to restart or go back - just tell the bot what you want to change!

## How It Works

### 1. **Technical Layer (Database)**
The `update_consultation_data()` method:
- Simply overwrites field values when called with new data
- No special logic needed - just updates the database
- Works for any field at any time

### 2. **AI Detection Layer**
The system prompt now includes explicit instructions for handling corrections:
- Recognizes correction keywords: "修改", "更正", "改成", "應該是", "不對", "錯了", "重新"
- Instructs AI to call `update_subsidy_data` function when user wants to modify data
- Processes the correction just like a new answer

### 3. **Correction Tracking**
The handler tracks which fields were corrected:
- `_corrected_fields` list stores fields that had existing values that were changed
- This allows generating appropriate "updated" confirmation messages
- Differentiates between first-time entry and corrections

### 4. **Natural Confirmation Messages**
When data is corrected, the chatbot responds with update-specific confirmations:
- First entry: "收到！經費規模為 500 萬元。"
- Correction: "了解，已將經費更新為 1000 萬元。"

## User Experience

### Example Correction Scenarios

**Scenario 1: Immediate Correction**
```
Bot: 請問您預計所需的經費是多少？
User: 500萬
Bot: 收到！經費規模為 500 萬元。

請問貴公司的投保人數有多少人？
User: 等等，我剛剛說錯了，預算應該是1000萬
Bot: 了解，已將經費更新為 1000 萬元。

請問貴公司的投保人數有多少人？
```

**Scenario 2: Correction Later in Conversation**
```
Bot: 請問貴公司的實收資本額是多少？
User: 我想修改公司人數，應該是50人不是20人
Bot: 好的，已將投保人數更新為 50 人。

請問貴公司的實收資本額是多少？
```

**Scenario 3: Change Project Type**
```
Bot: 請問您的行銷方向是「內銷」還是「外銷」？
User: 不對，我剛剛選錯了，應該是研發不是行銷
Bot: 好的，已更新為「研發」計畫類型。

請問您預計所需的經費是多少？
[Flow continues from where it left off]
```

**Scenario 4: Check Current Data & Correct**
```
User: 我可以看一下目前填了什麼資料嗎？
Bot: 當然可以！以下是您目前提供的資料：

計畫類型: 行銷
預計所需經費: 5,000,000 元 (500 萬)
公司投保人數: 20 人
公司實收資本額: 10,000,000 元 (1000 萬)
...

User: 資本額應該是2000萬
Bot: 收到，已將資本額更新為 2000 萬元。

請問貴公司大約的年度營業額是多少？
```

## Supported Correction Keywords

The AI recognizes these Chinese keywords as indicators of corrections:
- 修改 (modify)
- 更正 (correct)
- 改成 (change to)
- 應該是 (should be)
- 不對 (not correct)
- 錯了 (wrong)
- 重新 (redo)
- 等等 (wait)

## Implementation Details

### Field-Specific Confirmation Messages

When a field is corrected, the system generates appropriate confirmations:

| Field | First Entry | Correction |
|-------|-------------|-----------|
| Project Type | "收到！您選擇的是研發類型的計畫。" | "好的，已更新為「研發」計畫類型。" |
| Budget | "收到！經費規模為 500 萬元。" | "了解，已將經費更新為 1000 萬元。" |
| People | "好的，貴公司有 20 位投保員工。" | "好的，已將投保人數更新為 50 人。" |
| Capital | "收到！資本額 1000 萬元。" | "收到，已將資本額更新為 2000 萬元。" |
| Revenue | "了解，年營業額約 5000 萬元。" | "明白，已將營業額更新為 8000 萬元。" |
| Bonus Items | "很好！有第三方認證會增加申請優勢。" | "好的，已更新您的回答。" |
| Marketing Type | "收到！您選擇的是內銷市場。" | "了解，已將行銷方向更新為「外銷」。" |

### Code Structure

1. **`__init__()`** - Initializes `_corrected_fields = []`
2. **`update_consultation_data()`** - Tracks corrections in `_corrected_fields`
3. **`_get_natural_confirmation()`** - Checks `_corrected_fields` and generates appropriate message
4. **System Prompt** - Instructs AI to recognize and handle corrections

## Benefits

1. **User Friendly**: No need to restart conversation to fix mistakes
2. **Natural Flow**: Corrections are handled seamlessly within the conversation
3. **Transparent**: Users get clear confirmation that their update was processed
4. **Flexible**: Can correct any field at any time
5. **Smart**: AI recognizes various ways users express corrections

## Testing

To test the correction functionality:
1. Start a conversation and answer some questions
2. Say "等等，我剛剛說錯了，預算應該是XXX" at any point
3. Verify the chatbot acknowledges the update
4. Ask "可以看一下目前的資料嗎" to verify the change was saved
5. Continue the conversation - flow should resume normally

## Future Enhancements

Potential improvements:
- Allow bulk corrections: "修改預算和人數"
- Add confirmation prompts for significant changes
- Track correction history for analytics
- Provide "undo last change" functionality
