"""
Taiwan Government Subsidy Chatbot Handler
Uses Google Gemini AI for intelligent conversation and data collection
"""

import json
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
from sqlalchemy.orm import Session
from google import genai
from google.genai import types
from models import ChatSession, ChatMessage, SubsidyConsultation, ChatSessionStatus
from config import get_settings
from subsidy_calculator import calculate_subsidy

# Initialize settings
settings = get_settings()

# Initialize Gemini client
_gemini_client = None

def get_gemini_client():
    """Get or create Gemini client"""
    global _gemini_client
    if _gemini_client is None and settings.gemini_api_key:
        _gemini_client = genai.Client(api_key=settings.gemini_api_key)
    return _gemini_client


class SubsidyChatbotHandler:
    """AI-powered chatbot handler for Taiwan government subsidy consultation"""

    def __init__(self, db: Session, user_id: int, session_id: Optional[int] = None):
        self.db = db
        self.user_id = user_id
        self.session_id = session_id
        self.session = None
        self.consultation_data = None
        self._corrected_fields = []  # Track fields that were corrected/updated

        # Load or create session
        if session_id:
            self.session = db.query(ChatSession).filter(
                ChatSession.id == session_id,
                ChatSession.user_id == user_id
            ).first()

            if self.session:
                self.consultation_data = db.query(SubsidyConsultation).filter(
                    SubsidyConsultation.chat_session_id == session_id
                ).first()

    def create_session(self) -> ChatSession:
        """Create a new chat session"""
        self.session = ChatSession(
            user_id=self.user_id,
            status=ChatSessionStatus.ACTIVE
        )
        self.db.add(self.session)
        self.db.commit()
        self.db.refresh(self.session)

        # Create new consultation data
        self.consultation_data = SubsidyConsultation(
            chat_session_id=self.session.id,
            user_id=self.user_id
        )
        self.db.add(self.consultation_data)
        self.db.commit()
        self.db.refresh(self.consultation_data)

        return self.session

    def get_conversation_history(self) -> List[ChatMessage]:
        """Get conversation history for current session"""
        if not self.session:
            return []

        return self.db.query(ChatMessage).filter(
            ChatMessage.session_id == self.session.id
        ).order_by(ChatMessage.created_at).all()

    def add_message(self, role: str, content: str) -> ChatMessage:
        """Add a message to the conversation"""
        message = ChatMessage(
            session_id=self.session.id,
            role=role,
            content=content
        )
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        return message

    def get_system_prompt(self) -> str:
        """Get the system prompt for the AI"""
        return """你是一個專業的台灣政府補助診斷助理。

🚨 **最重要的規則：你必須使用函數來保存資料**
- 當使用者回答任何問題時，立即調用 update_subsidy_data 函數保存
- 不要只用文字確認，必須調用函數才能真正保存到數據庫
- 即使只有一個欄位也要調用函數
- **調用 update_subsidy_data 或 calculate_subsidy 函數時，不需要回傳文字回應**
- 系統會自動產生確認訊息並詢問下一個問題

**工作流程**：
1. 按順序收集以下資訊（一次一個）：
   - 計畫類型（研發/行銷）
   - 預計所需經費（萬元）
   - 公司投保人數（人）
   - 公司實收資本額（萬元）
   - 公司年度營業額（萬元）
   - 加分項目（逐一詢問以下5項）：
     1. 是否產品／服務取得第三方認證（是/否）
     2. 是否取得政府相關獎項（是/否）
     3. 產品是否為 MIT 生產（是/否）
     4. 是否有做產學合作（是/否）
     5. 是否有工廠登記證（是/否）
   - 【僅行銷】行銷方向（內銷/外銷）
   - 【僅行銷】預計營業額成長（萬元）

2. **使用者回答後，立即調用 update_subsidy_data 函數**
   例如：使用者說「行銷」→ 調用 update_subsidy_data(project_type="行銷")
   例如：使用者說「是」（回答加分項目）→ 調用 update_subsidy_data(has_certification=True)
   例如：使用者說「否」（回答加分項目）→ 調用 update_subsidy_data(has_certification=False)
   不需要額外的文字回應，系統會自動處理

3. **只在以下情況才需要文字回應**：
   - 使用者詢問問題（例如：「什麼是 SBIR？」）
   - 使用者要求查看目前資料（例如：「目前收集了哪些資料？」）
   - 使用者的輸入不清楚，需要澄清（例如：「請問您是指研發還是行銷？」）
   - 處理一般性對話（例如：打招呼、道謝）

💰 **金額單位轉換**：
- 使用者通常會用「萬元」為單位回答
- 你必須轉換為「元」再儲存（乘以 10000）
- 例如：500萬 → 5000000元

重要提示：
- **如果使用者主動提供多個資訊**，全部提取並記錄到 update_subsidy_data
- 記住：調用函數時不要生成文字回應，讓系統自動處理對話流程

✅ **資料確認流程（重要！）**：
- **當收集完所有必要資料後，系統會自動顯示資料摘要並要求使用者確認**
- 使用者會看到完整的資料清單
- 如果使用者回覆「確認」、「正確」、「沒問題」、「可以」、「OK」等確認詞：
  → 調用 confirm_data(confirmed=True) 函數
- 如果使用者要求修改某項資料：
  → 調用 update_subsidy_data 更新該欄位
  → 系統會重新顯示摘要要求確認
- **只有在使用者確認資料後，系統才會自動調用 calculate_subsidy 計算補助**
- 絕對不要在使用者未確認資料時就計算補助

🔄 **處理資料修改與更正**：
- **如果使用者想要修改之前填寫的資料**，立即調用 update_subsidy_data 更新該欄位
- 修改關鍵詞包括：「修改」、「更正」、「改成」、「應該是」、「不對」、「錯了」、「重新」等
- 例如：
  - 使用者說「等等，預算應該是1000萬」→ 調用 update_subsidy_data(budget=10000000)
  - 使用者說「我想修改公司人數，應該是50人」→ 調用 update_subsidy_data(people=50)
  - 使用者說「剛剛說錯了，是研發不是行銷」→ 調用 update_subsidy_data(project_type="研發")
- 修改後系統會自動確認並繼續流程，不需要重新詢問所有問題

📋 **查詢已收集的資料**：
- 當使用者詢問目前進度或已填資料時，從「目前已收集的資料」中提取並展示
- 用清晰的格式列出所有已收集的資訊
"""

    def get_current_data_summary(self) -> str:
        """Get a summary of currently collected data"""
        if not self.consultation_data:
            return "尚未收集任何資料"

        data = []
        if self.consultation_data.project_type:
            data.append(f"計畫類型: {self.consultation_data.project_type}")
        if self.consultation_data.budget is not None:
            data.append(f"預計所需經費: {self.consultation_data.budget:,} 元 ({self.consultation_data.budget // 10000} 萬)")
        if self.consultation_data.people is not None:
            data.append(f"公司投保人數: {self.consultation_data.people} 人")
        if self.consultation_data.capital is not None:
            data.append(f"公司實收資本額: {self.consultation_data.capital:,} 元 ({self.consultation_data.capital // 10000} 萬)")
        if self.consultation_data.revenue is not None:
            data.append(f"公司年度營業額: {self.consultation_data.revenue:,} 元 ({self.consultation_data.revenue // 10000} 萬)")
        if self.consultation_data.bonus_count is not None and self.consultation_data.bonus_count > 0:
            data.append(f"加分項目數量: {self.consultation_data.bonus_count} 項")
        if self.consultation_data.bonus_details:
            data.append(f"加分項目: {self.consultation_data.bonus_details}")
        if self.consultation_data.marketing_type:
            data.append(f"行銷方向: {self.consultation_data.marketing_type}")
        if self.consultation_data.growth_revenue is not None:
            data.append(f"預計營業額成長: {self.consultation_data.growth_revenue:,} 元 ({self.consultation_data.growth_revenue // 10000} 萬)")

        return "\n".join(data) if data else "尚未收集任何資料"

    def extract_data_with_ai(self, user_message: str, conversation_history: List[Dict]) -> Dict[str, Any]:
        """Use Gemini AI to extract structured data from conversation"""
        try:
            # Build conversation for Gemini
            messages = [
                {"role": "user", "parts": [self.get_system_prompt()]},
                {"role": "model", "parts": ["我明白了。我將協助收集台灣政府補助所需的資訊，並在使用者提供資料時立即調用函數保存。"]},
                {"role": "user", "parts": [f"目前已收集的資料：\n{self.get_current_data_summary()}"]}
            ]

            # Add recent conversation history (last 10 messages)
            for msg in conversation_history[-10:]:
                role = "user" if msg["role"] == "user" else "model"
                messages.append({
                    "role": role,
                    "parts": [msg["content"]]
                })

            # Add current user message
            messages.append({"role": "user", "parts": [user_message]})

            # Define tools for function calling
            tools = [
                {
                    "function_declarations": [
                        {
                            "name": "update_subsidy_data",
                            "description": "更新補助諮詢資料。從使用者的訊息中提取計畫類型、經費、人數、資本額、營業額、加分項目等資訊並更新。",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "project_type": {
                                        "type": "string",
                                        "description": "計畫類型：研發 or 行銷"
                                    },
                                    "budget": {
                                        "type": "integer",
                                        "description": "預計所需經費（單位：元）"
                                    },
                                    "people": {
                                        "type": "integer",
                                        "description": "公司投保人數（人）"
                                    },
                                    "capital": {
                                        "type": "integer",
                                        "description": "公司實收資本額（單位：元）"
                                    },
                                    "revenue": {
                                        "type": "integer",
                                        "description": "公司年度營業額（單位：元）"
                                    },
                                    "has_certification": {
                                        "type": "boolean",
                                        "description": "是否產品／服務取得第三方認證"
                                    },
                                    "has_gov_award": {
                                        "type": "boolean",
                                        "description": "是否取得政府相關獎項"
                                    },
                                    "is_mit": {
                                        "type": "boolean",
                                        "description": "產品是否為 MIT 生產"
                                    },
                                    "has_industry_academia": {
                                        "type": "boolean",
                                        "description": "是否有做產學合作"
                                    },
                                    "has_factory_registration": {
                                        "type": "boolean",
                                        "description": "是否有工廠登記證"
                                    },
                                    "marketing_type": {
                                        "type": "string",
                                        "description": "行銷方向：內銷, 外銷（可多選，用逗號分隔）"
                                    },
                                    "growth_revenue": {
                                        "type": "integer",
                                        "description": "預計行銷活動可帶來營業額成長（單位：元）"
                                    }
                                }
                            }
                        },
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
                        },
                        {
                            "name": "calculate_subsidy",
                            "description": "計算補助金額並推薦方案。當使用者確認資料後才能調用此函數。",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "ready_to_calculate": {
                                        "type": "boolean",
                                        "description": "是否準備好計算"
                                    }
                                },
                                "required": ["ready_to_calculate"]
                            }
                        }
                    ]
                }
            ]

            # Get Gemini client
            client = get_gemini_client()
            if not client:
                return {
                    "error": "Gemini API key not configured",
                    "message": "抱歉，系統配置錯誤。請聯繫管理員。"
                }

            # Convert messages to new format
            contents = []
            for msg in messages:
                content_parts = []
                for part in msg["parts"]:
                    # In the new API, use Part(text=...) instead of Part.from_text()
                    content_parts.append(types.Part(text=part))
                contents.append(types.Content(
                    role=msg["role"],
                    parts=content_parts
                ))

            # Convert tools to new format
            tool_declarations = []
            for tool in tools:
                for func_decl in tool["function_declarations"]:
                    tool_declarations.append(
                        types.FunctionDeclaration(
                            name=func_decl["name"],
                            description=func_decl["description"],
                            parameters=func_decl["parameters"]
                        )
                    )

            # Generate response with function calling enabled
            # Use tool_config to encourage function calling
            response = client.models.generate_content(
                model=settings.gemini_model,
                contents=contents,
                config=types.GenerateContentConfig(
                    tools=[types.Tool(function_declarations=tool_declarations)],
                    tool_config=types.ToolConfig(
                        function_calling_config=types.FunctionCallingConfig(
                            mode="AUTO"  # AUTO mode - model decides when to call functions
                        )
                    ),
                    temperature=0.7
                )
            )

            result = {
                "message": "",
                "function_calls": []
            }

            # Process response
            if response.candidates and len(response.candidates) > 0:
                candidate = response.candidates[0]

                # Check for function calls
                if candidate.content and candidate.content.parts:
                    for part in candidate.content.parts:
                        # Debug: Print the part structure
                        print(f"🔍 Part type: {type(part)}")
                        print(f"🔍 Part attributes: {dir(part)}")

                        # Check different possible attribute names
                        if hasattr(part, 'function_call') and part.function_call:
                            fc = part.function_call
                            function_args = dict(fc.args) if fc.args else {}

                            print(f"✅ Function call detected: {fc.name}")
                            print(f"   Arguments: {function_args}")

                            result["function_calls"].append({
                                "name": fc.name,
                                "arguments": function_args
                            })
                        elif hasattr(part, 'text') and part.text:
                            print(f"💬 Text response: {part.text[:100]}...")
                            result["message"] += part.text

            print(f"📊 Result: {len(result['function_calls'])} function calls, message length: {len(result['message'])}")
            return result

        except Exception as e:
            print(f"Gemini API error: {e}")
            return {
                "error": str(e),
                "message": "抱歉，我遇到了一些技術問題。請稍後再試。"
            }

    def _update_bonus_count_and_details(self):
        """Calculate bonus_count and bonus_details from individual boolean fields"""
        bonus_items = []

        if self.consultation_data.has_certification:
            bonus_items.append("產品／服務取得第三方認證")

        if self.consultation_data.has_gov_award:
            bonus_items.append("取得政府相關獎項")

        if self.consultation_data.is_mit:
            bonus_items.append("產品為 MIT 生產")

        if self.consultation_data.has_industry_academia:
            bonus_items.append("有做產學合作")

        if self.consultation_data.has_factory_registration:
            bonus_items.append("有工廠登記證")

        self.consultation_data.bonus_count = len(bonus_items)
        self.consultation_data.bonus_details = ", ".join(bonus_items) if bonus_items else None

    def _get_natural_confirmation(self) -> str:
        """
        Generate a natural, context-aware confirmation message based on recently updated field.
        Uses variety to make the conversation feel more human and less robotic.
        Recognizes corrections and provides appropriate feedback.
        """
        import random

        # Refresh data to get latest values
        self.db.refresh(self.consultation_data)

        # If this was a correction, generate update-specific confirmation
        if hasattr(self, '_corrected_fields') and self._corrected_fields:
            field = self._corrected_fields[0]  # Get the first corrected field

            if field == "project_type":
                return f"好的，已更新為「{self.consultation_data.project_type}」計畫類型。"
            elif field == "budget":
                budget_wan = self.consultation_data.budget // 10000
                return f"了解，已將經費更新為 {budget_wan} 萬元。"
            elif field == "people":
                return f"好的，已將投保人數更新為 {self.consultation_data.people} 人。"
            elif field == "capital":
                capital_wan = self.consultation_data.capital // 10000
                return f"收到，已將資本額更新為 {capital_wan} 萬元。"
            elif field == "revenue":
                revenue_wan = self.consultation_data.revenue // 10000
                return f"明白，已將營業額更新為 {revenue_wan} 萬元。"
            elif field in ["has_certification", "has_gov_award", "is_mit", "has_industry_academia", "has_factory_registration"]:
                return "好的，已更新您的回答。"
            elif field == "marketing_type":
                return f"了解，已將行銷方向更新為「{self.consultation_data.marketing_type}」。"
            elif field == "growth_revenue":
                growth_wan = self.consultation_data.growth_revenue // 10000
                return f"收到，已將預計營業額成長更新為 {growth_wan} 萬元。"

        # Check what was just updated and create context-aware confirmations
        if self.consultation_data.project_type and self.consultation_data.budget is None:
            confirmations = [
                f"收到！您選擇的是{self.consultation_data.project_type}類型的計畫。",
                f"了解，{self.consultation_data.project_type}計畫。",
                f"好的，我們來協助您評估{self.consultation_data.project_type}補助方案。"
            ]
            return random.choice(confirmations)

        elif self.consultation_data.budget is not None and self.consultation_data.people is None:
            budget_wan = self.consultation_data.budget // 10000
            confirmations = [
                f"明白了，預計經費約 {budget_wan} 萬元。",
                f"收到！經費規模為 {budget_wan} 萬元。",
                f"了解，您的預算是 {budget_wan} 萬元。"
            ]
            return random.choice(confirmations)

        elif self.consultation_data.people is not None and self.consultation_data.capital is None:
            confirmations = [
                f"好的，貴公司有 {self.consultation_data.people} 位投保員工。",
                f"收到！{self.consultation_data.people} 位員工的規模。",
                f"了解，投保人數為 {self.consultation_data.people} 人。"
            ]
            return random.choice(confirmations)

        elif self.consultation_data.capital is not None and self.consultation_data.revenue is None:
            capital_wan = self.consultation_data.capital // 10000
            confirmations = [
                f"明白了，實收資本額為 {capital_wan} 萬元。",
                f"收到！資本額 {capital_wan} 萬元。",
                f"好的，已記錄資本額資訊。"
            ]
            return random.choice(confirmations)

        elif self.consultation_data.revenue is not None and self.consultation_data.has_certification is None:
            revenue_wan = self.consultation_data.revenue // 10000
            confirmations = [
                f"了解，年營業額約 {revenue_wan} 萬元。",
                f"收到！營業額規模為 {revenue_wan} 萬元。",
                f"好的，已記錄營收資料。"
            ]
            return random.choice(confirmations)

        # For bonus items
        elif self.consultation_data.has_certification is not None and self.consultation_data.has_gov_award is None:
            if self.consultation_data.has_certification:
                confirmations = ["太好了！有第三方認證會增加申請優勢。", "很好！認證是重要的加分項目。", "收到！認證資格已記錄。"]
            else:
                confirmations = ["了解，沒有第三方認證。", "明白了。", "收到！"]
            return random.choice(confirmations)

        elif self.consultation_data.has_gov_award is not None and self.consultation_data.is_mit is None:
            if self.consultation_data.has_gov_award:
                confirmations = ["很好！政府獎項是很大的加分。", "太棒了！有政府獎項認可。", "收到！獎項資格已記錄。"]
            else:
                confirmations = ["了解。", "明白了。", "收到！"]
            return random.choice(confirmations)

        elif self.consultation_data.is_mit is not None and self.consultation_data.has_industry_academia is None:
            if self.consultation_data.is_mit:
                confirmations = ["很好！MIT 產品有額外優勢。", "收到！MIT 生產已記錄。", "了解，在台灣生產。"]
            else:
                confirmations = ["了解。", "明白了。", "收到！"]
            return random.choice(confirmations)

        elif self.consultation_data.has_industry_academia is not None and self.consultation_data.has_factory_registration is None:
            if self.consultation_data.has_industry_academia:
                confirmations = ["太好了！產學合作是重要加分項。", "很好！有產學合作經驗。", "收到！產學合作已記錄。"]
            else:
                confirmations = ["了解。", "明白了。", "收到！"]
            return random.choice(confirmations)

        elif self.consultation_data.has_factory_registration is not None:
            if self.consultation_data.has_factory_registration:
                if self.consultation_data.project_type == "行銷" and not self.consultation_data.marketing_type:
                    confirmations = ["很好！有工廠登記證。", "收到！工廠登記已記錄。", "了解，已有工廠登記。"]
                else:
                    confirmations = ["太好了！工廠登記證也會加分。", "很好！有完整的登記證明。", "收到！已記錄完所有加分項目。"]
            else:
                confirmations = ["了解。", "明白了。", "收到！"]
            return random.choice(confirmations)

        # For marketing type
        elif self.consultation_data.marketing_type and self.consultation_data.growth_revenue is None:
            confirmations = [
                f"收到！您選擇的是{self.consultation_data.marketing_type}市場。",
                f"了解，{self.consultation_data.marketing_type}導向的行銷計畫。",
                f"明白了，以{self.consultation_data.marketing_type}為主。"
            ]
            return random.choice(confirmations)

        # Default fallback
        return random.choice(["好的！已記錄。", "收到！", "了解。", "明白了。"])

    def update_consultation_data(self, data: Dict[str, Any]) -> bool:
        """
        Update consultation data with extracted information.
        Returns True if any field was updated.
        Stores list of corrected fields in self._corrected_fields for natural responses.
        """
        try:
            updated = False
            self._corrected_fields = []  # Track which fields were corrections

            if "project_type" in data and data["project_type"]:
                if self.consultation_data.project_type and self.consultation_data.project_type != data["project_type"]:
                    self._corrected_fields.append("project_type")
                self.consultation_data.project_type = data["project_type"]
                updated = True

            if "budget" in data and data["budget"] is not None:
                if self.consultation_data.budget and self.consultation_data.budget != int(data["budget"]):
                    self._corrected_fields.append("budget")
                self.consultation_data.budget = int(data["budget"])
                updated = True

            if "people" in data and data["people"] is not None:
                if self.consultation_data.people and self.consultation_data.people != int(data["people"]):
                    self._corrected_fields.append("people")
                self.consultation_data.people = int(data["people"])
                updated = True

            if "capital" in data and data["capital"] is not None:
                if self.consultation_data.capital and self.consultation_data.capital != int(data["capital"]):
                    self._corrected_fields.append("capital")
                self.consultation_data.capital = int(data["capital"])
                updated = True

            if "revenue" in data and data["revenue"] is not None:
                if self.consultation_data.revenue and self.consultation_data.revenue != int(data["revenue"]):
                    self._corrected_fields.append("revenue")
                self.consultation_data.revenue = int(data["revenue"])
                updated = True

            # Handle individual bonus items (boolean fields)
            if "has_certification" in data and data["has_certification"] is not None:
                if self.consultation_data.has_certification is not None and self.consultation_data.has_certification != bool(data["has_certification"]):
                    self._corrected_fields.append("has_certification")
                self.consultation_data.has_certification = bool(data["has_certification"])
                updated = True

            if "has_gov_award" in data and data["has_gov_award"] is not None:
                if self.consultation_data.has_gov_award is not None and self.consultation_data.has_gov_award != bool(data["has_gov_award"]):
                    self._corrected_fields.append("has_gov_award")
                self.consultation_data.has_gov_award = bool(data["has_gov_award"])
                updated = True

            if "is_mit" in data and data["is_mit"] is not None:
                if self.consultation_data.is_mit is not None and self.consultation_data.is_mit != bool(data["is_mit"]):
                    self._corrected_fields.append("is_mit")
                self.consultation_data.is_mit = bool(data["is_mit"])
                updated = True

            if "has_industry_academia" in data and data["has_industry_academia"] is not None:
                if self.consultation_data.has_industry_academia is not None and self.consultation_data.has_industry_academia != bool(data["has_industry_academia"]):
                    self._corrected_fields.append("has_industry_academia")
                self.consultation_data.has_industry_academia = bool(data["has_industry_academia"])
                updated = True

            if "has_factory_registration" in data and data["has_factory_registration"] is not None:
                if self.consultation_data.has_factory_registration is not None and self.consultation_data.has_factory_registration != bool(data["has_factory_registration"]):
                    self._corrected_fields.append("has_factory_registration")
                self.consultation_data.has_factory_registration = bool(data["has_factory_registration"])
                updated = True

            if "marketing_type" in data and data["marketing_type"]:
                if self.consultation_data.marketing_type and self.consultation_data.marketing_type != str(data["marketing_type"]):
                    self._corrected_fields.append("marketing_type")
                self.consultation_data.marketing_type = str(data["marketing_type"])
                updated = True

            if "growth_revenue" in data and data["growth_revenue"] is not None:
                if self.consultation_data.growth_revenue and self.consultation_data.growth_revenue != int(data["growth_revenue"]):
                    self._corrected_fields.append("growth_revenue")
                self.consultation_data.growth_revenue = int(data["growth_revenue"])
                updated = True

            # Auto-calculate bonus_count and bonus_details from individual boolean fields
            if updated:
                self._update_bonus_count_and_details()
                self.db.commit()

            return updated

        except Exception as e:
            print(f"Error updating consultation data: {e}")
            self.db.rollback()
            return False

    def calculate_and_save_subsidy(self) -> Tuple[bool, Optional[Dict]]:
        """Calculate subsidy amount and save results"""
        try:
            # Validate required fields
            if not self.consultation_data.project_type:
                return False, None
            if self.consultation_data.budget is None:
                return False, None
            if self.consultation_data.people is None:
                return False, None
            if self.consultation_data.capital is None:
                return False, None
            if self.consultation_data.revenue is None:
                return False, None

            # Prepare marketing types list
            marketing_types = []
            if self.consultation_data.marketing_type:
                marketing_types = [t.strip() for t in self.consultation_data.marketing_type.split(',')]

            # Calculate subsidy
            result = calculate_subsidy(
                budget=self.consultation_data.budget,
                people=self.consultation_data.people,
                capital=self.consultation_data.capital,
                revenue=self.consultation_data.revenue,
                bonus_count=self.consultation_data.bonus_count or 0,
                project_type=self.consultation_data.project_type,
                marketing_types=marketing_types,
                growth_revenue=self.consultation_data.growth_revenue or 0
            )

            # Save results
            self.consultation_data.grant_min = result["grant_min"]
            self.consultation_data.grant_max = result["grant_max"]
            self.consultation_data.recommended_plans = ", ".join(result["recommended_plans"])

            # Mark session as completed
            self.session.status = ChatSessionStatus.COMPLETED
            self.session.completed_at = datetime.utcnow()
            self.db.commit()

            return True, result

        except Exception as e:
            print(f"Error calculating subsidy: {e}")
            self.db.rollback()
            return False, None

    def get_next_field_question(self) -> str:
        """Get the next field question based on what's already collected"""
        self.db.refresh(self.consultation_data)

        if not self.consultation_data.project_type:
            return "請問您的計畫類型是「研發」還是「行銷」？"

        if self.consultation_data.budget is None:
            return "請問您預計所需的經費是多少？（請以萬元為單位，例如：500萬）"

        if self.consultation_data.people is None:
            return "請問貴公司的投保人數有多少人？"

        if self.consultation_data.capital is None:
            return "請問貴公司的實收資本額是多少？（請以萬元為單位）"

        if self.consultation_data.revenue is None:
            return "請問貴公司大約的年度營業額是多少？（請以萬元為單位）"

        # Ask bonus items one by one
        if self.consultation_data.has_certification is None:
            return "請問貴公司的產品／服務是否取得第三方認證？（請回答「是」或「否」）"

        if self.consultation_data.has_gov_award is None:
            return "請問貴公司是否取得政府相關獎項？（請回答「是」或「否」）"

        if self.consultation_data.is_mit is None:
            return "請問貴公司的產品是否為 MIT 生產？（請回答「是」或「否」）"

        if self.consultation_data.has_industry_academia is None:
            return "請問貴公司是否有做產學合作？（請回答「是」或「否」）"

        if self.consultation_data.has_factory_registration is None:
            return "請問貴公司是否有工廠登記證？（請回答「是」或「否」）"

        if self.consultation_data.project_type == "行銷":
            if not self.consultation_data.marketing_type:
                return "請問您的行銷方向是「內銷」還是「外銷」？（可以兩者都選）"
            if self.consultation_data.growth_revenue is None:
                return "請問您預計行銷活動可帶來的營業額成長是多少？（請以萬元為單位）"

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

    def process_message(self, user_message: str) -> Tuple[str, bool]:
        """
        Process user message with AI and return bot response
        Returns: (response_message, is_completed)
        """
        # Get conversation history
        history = self.get_conversation_history()
        conversation_history = [
            {"role": msg.role, "content": msg.content}
            for msg in history
        ]

        # Extract data with AI
        ai_result = self.extract_data_with_ai(user_message, conversation_history)

        if "error" in ai_result:
            return ai_result.get("message", "抱歉，發生錯誤。"), False

        # Process function calls
        completed = False
        data_updated = False
        calculation_done = False
        calculation_result = None

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
                        # Data not confirmed yet, don't calculate
                        print("⚠️ Warning: calculate_subsidy called but data not confirmed yet")

        # Build response message
        response_message = ai_result.get("message", "")

        if calculation_done and calculation_result:
            # Add calculation results to response
            if not response_message or len(response_message.strip()) < 10:
                response_message = f"""✅ 計算完成！根據您提供的資料：

💰 **補助金額範圍**
NT${calculation_result['grant_min']:,} ~ NT${calculation_result['grant_max']:,}

🎯 **推薦補助方案**
{chr(10).join(f"• {plan}" for plan in calculation_result['recommended_plans'])}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 **補助機制說明**

**補助估算依據如下：**
• 本工具比對您輸入的【公司規模】與【導入項目】對應政府補助系統規則庫
• 金額屬於預估，實際需視政府當年度公告金額及審查而定
• 政府補助通常需配合送出正式計畫書＋成果查驗
• 政府補助必須搭配自籌款50%，才是完整計畫金額，上述系統估算為實際政府補助金額

**政府補助包含以下常見會計科目（研發/行銷補助）：**
• 人事費
• 材料費
• 委外費用
• 設備採購
• 設備折舊
• 廣宣費
• 贈品費

**常見限制條件（包含但不只這些）：**
• 有些補助計畫需先完成採購，才能核銷
• 有些補助不可與其他專案重複核銷
• 若已申請過CITD／SBIR等類型補助，可能不再受理同類項目
• 政府補助只能補助計畫期間內發生的採購事實
• 政府補助不可與其他專案重複執行
• 政府補助不接受一案多送
• 補助對核銷經費各會計科目均有限制規範

**核心因素審查：**
項目                        | 狀態     | 備註
---------------------------|----------|------------------
公司是否有過申請紀錄         | 未知     | 需進一步分析
本案是否為重複項目          | 無紀錄   | 初步符合
是否已取得認證（如中堅企業） | 未填寫   | 建議確認
政府審查年度預算是否尚足     | 略偏晚   | 建議盡速提案

⚠️ **重要提醒：**
本補助金額為系統依據歷年通過案件所建立之模型計算，實際通過與否仍需配合計畫內容、企業財務資料與當年度預算情形。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📱 **推薦使用補助引擎**
根據您的條件，我們推薦您使用「補助引擎」app來協助您撰寫政府補助計劃書。補助引擎使用 AI 技術，可以幫助您更快速、更專業地完成申請文件。

若您對目前估算金額與條件有疑問，建議您預約 TGSA 顧問進行免費15分鐘評估。

感謝您使用我們的服務！祝您申請順利！🎉"""
        elif data_updated:
            # When data was updated via function call, generate natural confirmation
            # with the next question to ensure proper conversation flow
            # This prevents duplicate questions while maintaining natural conversation
            confirmation = self._get_natural_confirmation()
            next_question = self.get_next_field_question()
            response_message = f"{confirmation}\n\n{next_question}"
        elif not response_message:
            # If no function was called and AI didn't provide a response,
            # ask the next question
            response_message = "我了解了。" + self.get_next_field_question()

        return response_message, completed

    def get_progress(self) -> Dict[str, Any]:
        """Get current progress of data collection"""
        fields_completed = 0
        total_fields = 6  # project_type, budget, people, capital, revenue, bonus

        if self.consultation_data.project_type:
            fields_completed += 1
        if self.consultation_data.budget is not None:
            fields_completed += 1
        if self.consultation_data.people is not None:
            fields_completed += 1
        if self.consultation_data.capital is not None:
            fields_completed += 1
        if self.consultation_data.revenue is not None:
            fields_completed += 1
        if self.consultation_data.bonus_count is not None and self.consultation_data.bonus_count > 0:
            fields_completed += 1

        # For marketing projects, add 2 more fields
        if self.consultation_data.project_type == "行銷":
            total_fields += 2
            if self.consultation_data.marketing_type:
                fields_completed += 1
            if self.consultation_data.growth_revenue is not None:
                fields_completed += 1

        return {
            "data_collection_complete": fields_completed == total_fields,
            "fields_completed": fields_completed,
            "total_fields": total_fields
        }
