# Taiwan Government Subsidy Chatbot - API Guide

Complete reference for the Taiwan Government Subsidy Chatbot API, including endpoints, calculation logic, and important implementation notes.

---

## Table of Contents

1. [API Endpoints](#api-endpoints)
2. [Subsidy Calculation Logic](#subsidy-calculation-logic)
3. [Database Schema](#database-schema)
4. [Important Features](#important-features)
5. [Database Migrations](#database-migrations)
6. [Testing](#testing)

---

## API Endpoints

### Authentication

All endpoints require JWT authentication via Bearer token in the Authorization header:
```
Authorization: Bearer <jwt_token>
```

### Base URL
```
http://localhost:8000
```

---

### 1. Chat Endpoints

#### **POST /api/subsidy/chat**
Send a message to the subsidy consultation chatbot.

**Request Body:**
```json
{
  "message": "研發",
  "session_id": 5  // optional, null for first message
}
```

**Response:**
```json
{
  "session_id": 5,
  "message": "收到！您選擇的是研發類型的計畫。\n\n請問您預計所需的經費是多少？",
  "completed": false,
  "progress": {
    "fields_completed": 1,
    "total_fields": 6
  }
}
```

**Behavior:**
- Creates new session if `session_id` is null
- Processes user message and updates consultation data
- Returns bot response with natural confirmation messages
- Auto-shows data summary and asks for confirmation when all fields complete
- Only calculates after user confirms data

---

### 2. Session Management Endpoints

#### **GET /api/subsidy/sessions/latest**
Get the latest active session for the current user.

**Response:**
```json
{
  "session_id": 5,
  "status": "ACTIVE",
  "created_at": "2026-01-22T10:30:00"
}
```

Or if no active session:
```json
{
  "session_id": null
}
```

**Use Case:** Check for existing session on page load to avoid creating duplicates.

---

#### **POST /api/subsidy/sessions/new**
Create a new consultation session with optional memory preservation.

**Query Parameters:**
- `previous_session_id` (optional): ID of previous session to copy data from

**Examples:**
```bash
# Fresh start
POST /api/subsidy/sessions/new

# With memory preservation
POST /api/subsidy/sessions/new?previous_session_id=5
```

**Response:**
```json
{
  "session_id": 6,
  "message": "您好！我是新手戰略指引的 AI 助理...",
  "progress": {
    "fields_completed": 0,
    "total_fields": 6
  }
}
```

**Memory Preservation:** When `previous_session_id` is provided, copies all consultation data (project_type, budget, people, capital, revenue, bonus items, marketing data) from the previous session to the new one.

---

#### **GET /api/subsidy/sessions**
Get all sessions for the current user.

**Response:**
```json
[
  {
    "id": 5,
    "user_id": 1,
    "status": "COMPLETED",
    "created_at": "2026-01-22T10:00:00",
    "updated_at": "2026-01-22T10:30:00",
    "completed_at": "2026-01-22T10:30:00"
  }
]
```

---

#### **GET /api/subsidy/sessions/{session_id}/messages**
Get all chat messages for a specific session.

**Response:**
```json
[
  {
    "id": 1,
    "session_id": 5,
    "role": "assistant",
    "content": "您好！我是台灣政府補助診斷助理...",
    "created_at": "2026-01-22T10:00:00"
  },
  {
    "id": 2,
    "session_id": 5,
    "role": "user",
    "content": "研發",
    "created_at": "2026-01-22T10:00:30"
  }
]
```

**Use Case:** Load chat history when returning to an existing session.

---

### 3. Consultation Data Endpoints

#### **GET /api/subsidy/consultations/{session_id}**
Get consultation data for a specific session.

**Response:**
```json
{
  "id": 3,
  "chat_session_id": 5,
  "user_id": 1,
  "source": "補助診斷士",
  "project_type": "研發",
  "data_confirmed": true,
  "budget": 5000000,
  "people": 20,
  "capital": 10000000,
  "revenue": 50000000,
  "has_certification": true,
  "has_gov_award": false,
  "is_mit": true,
  "has_industry_academia": true,
  "has_factory_registration": false,
  "bonus_count": 3,
  "bonus_details": "產品／服務取得第三方認證, 產品為 MIT 生產, 有做產學合作",
  "marketing_type": null,
  "growth_revenue": null,
  "grant_min": 1500000,
  "grant_max": 3000000,
  "recommended_plans": "地方SBIR, CITD, 中央SBIR",
  "timestamp": "2026-01-22T10:30:00",
  "created_at": "2026-01-22T10:00:00",
  "updated_at": "2026-01-22T10:30:00"
}
```

---

#### **GET /api/subsidy/consultations/{session_id}/export**
Export consultation data to CSV/Excel format.

**Query Parameters:**
- `format`: `csv` or `excel` (default: `csv`)

**Response:** File download with Chinese field names

**CSV Fields:**
- 時間戳
- 來源
- 類型選擇
- 預計所需經費(元)
- 公司投保人數(人)
- 公司實收資本額(元)
- 公司大約年度營業額(元)
- 產品／服務取得第三方認證
- 取得政府相關獎項
- 產品為 MIT 生產
- 有做產學合作
- 有工廠登記證
- 加分項目數量
- 加分項目詳情
- 行銷方向
- 預計行銷活動可帶來營業額成長(元)
- 補助最低值(元)
- 補助最高值(元)
- 推薦方案名稱

---

## Subsidy Calculation Logic

### Overview
The calculation engine determines subsidy ranges and recommends suitable government programs based on company data.

### Input Parameters

| Parameter | Type | Description | Unit |
|-----------|------|-------------|------|
| `budget` | integer | Project budget | 元 (TWD) |
| `people` | integer | Company employees | 人 |
| `capital` | integer | Registered capital | 元 (TWD) |
| `revenue` | integer | Annual revenue | 元 (TWD) |
| `bonus_count` | integer | Number of bonus items (0-5) | 項 |
| `project_type` | string | "研發" or "行銷" | - |
| `marketing_types` | list | ["內銷", "外銷"] or empty | - |

### Calculation Formula

#### Base Grant Calculation
```python
base_percentage = 0.5  # 50% of budget
grant_base = budget * base_percentage
```

#### Grant Range with Bonus Multiplier
```python
bonus_factor = 1.0 + (bonus_count * 0.05)  # Each bonus adds 5%

grant_min = grant_base * 0.6
grant_max = grant_base * bonus_factor
```

**Example:**
- Budget: 5,000,000 元
- Bonus Count: 3
- Base: 5,000,000 × 0.5 = 2,500,000 元
- Bonus Factor: 1.0 + (3 × 0.05) = 1.15
- Min: 2,500,000 × 0.6 = 1,500,000 元
- Max: 2,500,000 × 1.15 = 2,875,000 元

### Program Recommendations

#### 研發 (R&D) Programs

**1. 地方SBIR (Local SBIR)**
- Max Grant: 1,000,000 元
- Conditions: Any company size

**2. CITD (Collaborative Innovation Technology Development)**
- Max Grant: 10,000,000 元
- Conditions:
  - Capital ≥ 50,000,000 元 OR
  - Revenue ≥ 100,000,000 元 OR
  - Employees ≥ 50 人

**3. 中央SBIR (Central SBIR)**
- Max Grant: 3,500,000 元
- Conditions: Any company size

#### 行銷 (Marketing) Programs

**1. 開拓海外市場計畫 (International Market Development)**
- Conditions: "外銷" in marketing_types
- Max Grant: Based on budget

**2. 內銷推廣計畫 (Domestic Market Promotion)**
- Conditions: "內銷" in marketing_types
- Max Grant: Based on budget

### Recommendation Logic

Programs are recommended if:
1. Company meets eligibility criteria
2. Grant max ≤ Program max grant
3. Program type matches project type

---

## Database Schema

### Key Tables

#### **subsidy_consultations**

Stores all consultation data and calculation results.

```sql
CREATE TABLE subsidy_consultations (
    id SERIAL PRIMARY KEY,
    chat_session_id INTEGER REFERENCES chat_sessions(id),
    user_id INTEGER REFERENCES users(id),

    -- Basic Info
    source VARCHAR(100) DEFAULT '補助診斷士',
    project_type VARCHAR(50),              -- 研發 or 行銷
    data_confirmed BOOLEAN DEFAULT FALSE,  -- User confirmed data

    -- Financial Data (stored in 元/TWD)
    budget BIGINT,                         -- 預計所需經費
    people INTEGER,                        -- 公司投保人數
    capital BIGINT,                        -- 公司實收資本額
    revenue BIGINT,                        -- 公司年度營業額
    growth_revenue BIGINT,                 -- 預計營業額成長

    -- Bonus Items (Individual flags)
    has_certification BOOLEAN,             -- 第三方認證
    has_gov_award BOOLEAN,                 -- 政府獎項
    is_mit BOOLEAN,                        -- MIT生產
    has_industry_academia BOOLEAN,         -- 產學合作
    has_factory_registration BOOLEAN,      -- 工廠登記證

    -- Legacy bonus fields (auto-calculated)
    bonus_count INTEGER DEFAULT 0,
    bonus_details TEXT,

    -- Marketing data
    marketing_type TEXT,                   -- 內銷, 外銷

    -- Calculation Results
    grant_min BIGINT,                      -- 補助最低值
    grant_max BIGINT,                      -- 補助最高值
    recommended_plans TEXT,                -- Comma-separated

    -- Timestamps
    timestamp TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

#### **chat_sessions**

```sql
CREATE TABLE chat_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    status VARCHAR(20) DEFAULT 'ACTIVE',  -- ACTIVE, COMPLETED, ABANDONED
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);
```

#### **chat_messages**

```sql
CREATE TABLE chat_messages (
    id SERIAL PRIMARY KEY,
    session_id INTEGER REFERENCES chat_sessions(id),
    role VARCHAR(20) NOT NULL,            -- 'user' or 'assistant'
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## Important Features

### 1. **Intelligent Session Management**

- **Auto-load existing sessions**: On page load, automatically detects and loads the latest active session
- **First-time user detection**: Identifies new users and shows welcome message
- **Chat history restoration**: Loads all previous messages when returning to a session
- **Memory preservation**: Option to copy consultation data when creating new sessions

### 2. **Natural Conversation Flow**

- **Context-aware confirmations**: Different messages for first entry vs corrections
  - First: "收到！經費規模為 500 萬元。"
  - Correction: "了解，已將經費更新為 1000 萬元。"
- **Varied responses**: 3 variations per field to avoid robotic repetition
- **Encouraging feedback**: Positive reinforcement for bonus items

### 3. **Data Correction & Updates**

- **Anytime corrections**: Users can modify any field at any time during conversation
- **Correction detection**: Recognizes keywords: 修改, 更正, 改成, 應該是, 不對, 錯了
- **Automatic re-prompting**: Shows updated summary after corrections

### 4. **Mandatory Confirmation Before Calculation**

- **Data summary display**: Shows complete data review before calculating
- **User confirmation required**: Must explicitly confirm with "確認", "正確", "OK", etc.
- **Correction opportunity**: Can make changes during confirmation phase
- **Prevents premature calculation**: Especially important for sessions with preserved data

### 5. **Explicit Bonus Item Questions**

Instead of asking users to "list bonus items", the chatbot asks 5 explicit yes/no questions:
1. 是否產品／服務取得第三方認證？
2. 是否取得政府相關獎項？
3. 產品是否為 MIT 生產？
4. 是否有做產學合作？
5. 是否有工廠登記證？

### 6. **Comprehensive Results Display**

Final calculation includes:
- Grant amount range (min ~ max)
- Recommended subsidy programs
- **補助機制說明** section with:
  - Estimation methodology
  - Eligible expense categories
  - Common restrictions
  - Core factor review table
  - TGSA consultation recommendation

---

## Database Migrations

### Required Migrations

Run these SQL scripts in order before deploying:

#### 1. **Add Bonus Item Fields**
```bash
psql -U username -d database_name -f backend/migration_add_bonus_fields.sql
```

Adds individual boolean fields for each bonus item.

#### 2. **Add Confirmation Field**
```bash
psql -U username -d database_name -f backend/migration_add_confirmation_field.sql
```

Adds `data_confirmed` field to track user confirmation status.

### Migration Scripts

Both scripts include:
- Column additions with proper types
- Comments for documentation
- Backward compatibility handling
- Safe `IF NOT EXISTS` checks

---

## Testing

### Test Chatbot Interface

Open `test-chatbot.html` in a browser to test the chatbot.

**Features:**
- Session detection and loading
- Chat history display
- Memory preservation option
- Real-time progress tracking

### Test Cases

#### **1. Normal Flow**
1. Open test-chatbot.html
2. Answer all questions
3. See data summary with confirmation prompt
4. Reply "確認"
5. Verify calculation results displayed

#### **2. Data Correction**
1. Complete questionnaire
2. See summary
3. Say: "預算改成1000萬"
4. Verify updated summary shown
5. Confirm and verify calculation

#### **3. Session Preservation**
1. Complete questionnaire and get results
2. Click "🆕 New Session"
3. Click "確定" to preserve data
4. Verify: Summary shown immediately (not calculation)
5. Can modify or confirm
6. After confirmation, see new calculation

#### **4. First-Time User**
1. Clear all sessions or use new JWT token
2. Open test-chatbot.html
3. Verify: "歡迎！這是您第一次使用補助診斷助理。"
4. Verify: New session created automatically

#### **5. Returning User**
1. Have existing active session with messages
2. Open test-chatbot.html
3. Verify: "已載入您的上次對話 (Session #X)"
4. Verify: All previous messages loaded
5. Verify: Progress indicator correct

---

## Important Notes

### Unit Conversions

Users typically input in **萬元 (10,000 TWD)**, but the system stores in **元 (TWD)**:

```python
# User says "500萬"
budget_wan = 500
budget_yuan = budget_wan * 10000  # 5,000,000 元
```

The AI automatically handles this conversion via the system prompt.

### Function Calling

The chatbot uses Gemini AI with function calling:

**Functions:**
1. `update_subsidy_data` - Saves user input to database
2. `confirm_data` - Records user confirmation
3. `calculate_subsidy` - Triggers subsidy calculation (only after confirmation)

**Tool Config:**
```python
tool_config=types.ToolConfig(
    function_calling_config=types.FunctionCallingConfig(
        mode="AUTO"  # AI decides when to call functions
    )
)
```

### Workflow States

The conversation has 3 states:

1. **Data Collection**: Asking questions, collecting inputs
2. **Confirmation**: All data collected, showing summary, waiting for confirmation
3. **Calculation**: Data confirmed, calculation performed, results displayed

The `data_confirmed` field tracks transition from state 2 → 3.

### Session Status

- **ACTIVE**: Currently in progress
- **COMPLETED**: Calculation done, results shown
- **ABANDONED**: User left without completing

### Bonus Count Calculation

The `bonus_count` field is **auto-calculated** from the 5 boolean fields:

```python
bonus_count = sum([
    has_certification,
    has_gov_award,
    is_mit,
    has_industry_academia,
    has_factory_registration
])
```

### Memory Preservation Behavior

When creating new session with `previous_session_id`:
- ✅ Copies: All consultation data fields
- ✅ Copies: Bonus items, financial data, project type
- ❌ Does NOT copy: Chat messages (fresh conversation)
- ❌ Does NOT copy: Calculation results (requires new confirmation)
- ❌ Does NOT copy: `data_confirmed` flag (requires re-confirmation)

This ensures users can review and modify preserved data before calculating again.

---

## Error Handling

### Common Errors

**Missing JWT Token:**
```json
{
  "detail": "Not authenticated"
}
```

**Session Not Found:**
```json
{
  "detail": "Chat session not found"
}
```

**Invalid Session Access:**
```json
{
  "detail": "Chat session not found"  // User trying to access another user's session
}
```

### Validation

The system validates:
- All required fields present before calculation
- User owns the session they're accessing
- JWT token is valid and not expired
- Consultation data exists for session

---

## API Response Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 401 | Unauthorized (missing or invalid JWT) |
| 404 | Not Found (session or data doesn't exist) |
| 500 | Internal Server Error |

---

## Quick Start

1. **Start Backend:**
```bash
cd backend
uvicorn main:app --reload
```

2. **Run Migrations:**
```bash
psql -U username -d dbname -f migration_add_bonus_fields.sql
psql -U username -d dbname -f migration_add_confirmation_field.sql
```

3. **Open Test Interface:**
```bash
open test-chatbot.html
```

4. **Test the Flow:**
- Answer questions
- See data summary
- Confirm
- View results

---

## Support

For questions or issues:
- Check the calculation logic section for subsidy calculations
- Review the API endpoints for integration details
- See the test cases for expected behavior
- Refer to important notes for implementation details

---

**Last Updated:** 2026-01-22
**Version:** 1.0.0
**API Base URL:** http://localhost:8000
