# Taiwan Government Subsidy Chatbot - API Documentation

## 🎯 Overview

This API provides AI-powered chatbot services for Taiwan government subsidy consultation using **Google Gemini AI**.

**Base URL**: `http://localhost:8000` (development)

## 🔐 Authentication

All endpoints (except `/` health check) require JWT authentication.

**Header**: `Authorization: Bearer <JWT_TOKEN>`

The JWT token should be obtained from your main authentication system.

## 📡 API Endpoints

### Health Check

#### `GET /`

Check if the API is running.

**Response:**
```json
{
  "status": "ok",
  "message": "Taiwan Government Subsidy Chatbot API is running",
  "version": "1.0.0",
  "features": ["external_jwt_auth", "gemini_ai_chatbot", "subsidy_calculation", "session_management"]
}
```

---

### Authentication

#### `GET /api/auth/me`

Get current authenticated user information.

**Headers**: `Authorization: Bearer <token>`

**Response:**
```json
{
  "id": 1,
  "external_user_id": "user123",
  "username": "John Doe",
  "role": "user",
  "is_active": true,
  "created_at": "2026-01-21T10:00:00",
  "updated_at": "2026-01-21T10:00:00"
}
```

---

### Subsidy Chatbot

#### `POST /api/subsidy/chat`

Send a message to the subsidy consultation chatbot.

**Request Body:**
```json
{
  "message": "我想申請研發補助",
  "session_id": null  // or existing session ID
}
```

**Response:**
```json
{
  "session_id": 1,
  "message": "您好！我是台灣政府補助診斷助理...",
  "completed": false,
  "progress": {
    "data_collection_complete": false,
    "fields_completed": 0,
    "total_fields": 6
  }
}
```

---

#### `GET /api/subsidy/sessions`

Get all subsidy consultation sessions for the current user.

**Response:**
```json
[
  {
    "id": 1,
    "user_id": 1,
    "status": "active",
    "created_at": "2026-01-21T10:00:00",
    "updated_at": "2026-01-21T10:05:00",
    "completed_at": null
  }
]
```

---

#### `GET /api/subsidy/sessions/latest`

Get the latest active session (to avoid duplicate sessions on page refresh).

**Response:**
```json
{
  "session_id": 1,
  "status": "active",
  "created_at": "2026-01-21T10:00:00"
}
```

Or if no active session:
```json
{
  "session_id": null
}
```

---

#### `POST /api/subsidy/sessions/new`

Create a new subsidy consultation session.

**Response:**
```json
{
  "session_id": 2,
  "message": "您好！我是台灣政府補助診斷助理...",
  "progress": {
    "data_collection_complete": false,
    "fields_completed": 0,
    "total_fields": 6
  }
}
```

---

#### `GET /api/subsidy/sessions/{session_id}/messages`

Get all messages for a specific session.

**Path Parameter**: `session_id` (integer)

**Response:**
```json
[
  {
    "id": 1,
    "role": "assistant",
    "content": "您好！我是台灣政府補助診斷助理...",
    "created_at": "2026-01-21T10:00:00"
  },
  {
    "id": 2,
    "role": "user",
    "content": "我想申請研發補助",
    "created_at": "2026-01-21T10:01:00"
  }
]
```

---

#### `GET /api/subsidy/consultations/{session_id}`

Get the consultation data for a specific session.

**Path Parameter**: `session_id` (integer)

**Response:**
```json
{
  "id": 1,
  "chat_session_id": 1,
  "user_id": 1,
  "source": "補助診斷士",
  "project_type": "研發",
  "budget": 5000000,
  "people": 20,
  "capital": 10000000,
  "revenue": 30000000,
  "growth_revenue": null,
  "bonus_count": 3,
  "bonus_details": "專利, 認證, 技術創新",
  "marketing_type": null,
  "grant_min": 2887500,
  "grant_max": 3850000,
  "recommended_plans": "地方SBIR, CITD, 中央SBIR",
  "timestamp": "2026-01-21T10:00:00",
  "created_at": "2026-01-21T10:00:00",
  "updated_at": "2026-01-21T10:15:00"
}
```

---

#### `GET /api/subsidy/consultations/{session_id}/export`

Export consultation data with Chinese field names.

**Path Parameter**: `session_id` (integer)

**Response:**
```json
{
  "時間戳": "2026-01-21 10:00:00",
  "來源": "補助診斷士",
  "類型選擇": "研發",
  "預計所需經費(元)": 5000000,
  "公司投保人數(人)": 20,
  "公司實收資本額(元)": 10000000,
  "公司大約年度營業額(元)": 30000000,
  "加分項目數量": 3,
  "加分項目詳情": "專利, 認證, 技術創新",
  "行銷方向": null,
  "預計行銷活動可帶來營業額成長(元)": null,
  "補助最低值(元)": 2887500,
  "補助最高值(元)": 3850000,
  "推薦方案名稱": "地方SBIR, CITD, 中央SBIR"
}
```

---

#### `POST /api/subsidy/calculate`

Calculate subsidy amount directly (without chat session).

**Request Body:**
```json
{
  "project_type": "研發",
  "budget": 5000000,
  "people": 20,
  "capital": 10000000,
  "revenue": 30000000,
  "bonus_count": 3,
  "bonus_details": "專利, 認證, 技術創新",
  "marketing_type": null,
  "growth_revenue": null
}
```

**Response:**
```json
{
  "grant_min": 2887500,
  "grant_max": 3850000,
  "recommended_plans": ["地方SBIR", "CITD", "中央SBIR"],
  "breakdown": {
    "grant_employee": 3000000,
    "grant_revenue_bonus": 500000,
    "bonus_amount": 350000,
    "upper_limit": 4500000
  }
}
```

---

## 🤖 Chatbot Conversation Flow

### Research Project (研發) Flow:

1. **Project Type**: "請問您的計畫類型是「研發」還是「行銷」？"
   - User: "研發"

2. **Budget**: "請問您預計所需的經費是多少？（請以萬元為單位）"
   - User: "500萬"

3. **People**: "請問貴公司的投保人數有多少人？"
   - User: "20人"

4. **Capital**: "請問貴公司的實收資本額是多少？（請以萬元為單位）"
   - User: "1000萬"

5. **Revenue**: "請問貴公司大約的年度營業額是多少？（請以萬元為單位）"
   - User: "3000萬"

6. **Bonus Items**: "請問貴公司有哪些加分項目？"
   - User: "專利、認證、技術創新"

7. **Calculate**: System calculates and shows results with recommended plans

### Marketing Project (行銷) Flow:

Same as above, but adds:

8. **Marketing Type**: "請問您的行銷方向是「內銷」還是「外銷」？"
   - User: "外銷"

9. **Growth Revenue**: "請問您預計行銷活動可帶來的營業額成長是多少？"
   - User: "500萬"

---

## 🎯 Recommended Subsidy Programs

### For 研發 (R&D) Projects:
- **地方SBIR**: threshold >= 0
- **CITD**: threshold >= 1,500,000 元
- **中央SBIR**: threshold >= 2,000,000 元

### For 行銷 (Marketing) Projects:
- **開拓海外市場計畫**: When marketing_type includes "外銷"
- **內銷行銷推廣計畫（預留）**: When marketing_type includes "內銷"

**Threshold** = grant_max × 0.8

---

## 💡 Usage Examples

### Example 1: Start a new chat session

```bash
curl -X POST http://localhost:8000/api/subsidy/chat \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "我想申請研發補助",
    "session_id": null
  }'
```

### Example 2: Continue existing session

```bash
curl -X POST http://localhost:8000/api/subsidy/chat \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "500萬",
    "session_id": 1
  }'
```

### Example 3: Direct calculation (no chat)

```bash
curl -X POST http://localhost:8000/api/subsidy/calculate \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "project_type": "研發",
    "budget": 5000000,
    "people": 20,
    "capital": 10000000,
    "revenue": 30000000,
    "bonus_count": 3,
    "bonus_details": "專利, 認證, 技術創新"
  }'
```

---

## 🔧 Error Responses

### 401 Unauthorized
```json
{
  "detail": "Not authenticated"
}
```

### 404 Not Found
```json
{
  "detail": "Chat session not found"
}
```

### 500 Internal Server Error
```json
{
  "detail": "An error occurred while processing your message: ..."
}
```

---

## 📊 Data Collection Fields

| Field | Type | Unit | Required | Description |
|-------|------|------|----------|-------------|
| `project_type` | string | - | ✅ | 研發 or 行銷 |
| `budget` | integer | 元 | ✅ | 預計所需經費 |
| `people` | integer | 人 | ✅ | 公司投保人數 |
| `capital` | integer | 元 | ✅ | 公司實收資本額 |
| `revenue` | integer | 元 | ✅ | 公司大約年度營業額 |
| `bonus_count` | integer | - | Optional | 加分項目數量 (0-5) |
| `bonus_details` | string | - | Optional | 加分項目詳情 |
| `marketing_type` | string | - | 行銷類必填 | 內銷, 外銷 |
| `growth_revenue` | integer | 元 | 行銷類必填 | 預計營業額成長 |

**Note**: Users input amounts in 萬元, but the API stores them in 元 (multiply by 10,000).

---

**Last Updated**: 2026-01-21
**Version**: 1.0.0
**AI Model**: Google Gemini 2.5 Flash
