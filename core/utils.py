import os
import json
import re
import streamlit as st
from pydantic import BaseModel, Field

# ==========================================
# 1. 定義 Pydantic 結構化輸出 (確保 AI 產出格式穩定)
# ==========================================
class PLCCodeOutput(BaseModel):
    thinking: str = Field(description="設計邏輯的思路與變數分析")
    tutorial: str = Field(description="逐行新手教學與註解說明，解釋為什麼這樣寫")
    scl_code: str = Field(description="純粹的西門子 SCL 程式碼 (嚴格遵守 IO 隔離與語法)")
    csv_tags: str = Field(description="包含 Name,Path,Data Type,Logical Address 等欄位的 TIA Portal 官方 CSV 格式字串")

class BugClinicOutput(BaseModel):
    diagnosis: str = Field(description="錯誤原因分析與診斷")
    fixed_scl_code: str = Field(description="修復後的純粹西門子 SCL 程式碼 (不可包含 Markdown)")

class QAItem(BaseModel):
    question: str = Field(description="情境或技術問題")
    answer: str = Field(description="標準解答或對應的控制邏輯思路")

class BatchEngineOutput(BaseModel):
    items: list[QAItem]

# ==========================================
# 2. SCL 語法鐵律 (全系統共用的最高指導原則)
# ==========================================
SCL_RULES = """
【🔥🔥🔥 極度重要的 SCL 語法鐵律 (Violation is unacceptable) 🔥🔥🔥】：
1. 【宣告區塊】：FB 靜態變數必須用 `VAR` 宣告。在宣告區塊內，變數名稱絕對不可以包含 `#` 或 `"`！(例如只能寫 `Run_Latch : Bool;`)
2. 【邏輯區塊】：在 `BEGIN` 之後的程式碼中，呼叫任何「內部變數」都必須加上 `#` (例如 `#Run_Latch`)，呼叫「外部硬體 IO」必須加上雙引號 (例如 `"Start_Button"`)。
3. 【IO 隔離】：對應實體 %I, %Q 的硬體接點，絕對不可以在 SCL 內部宣告，必須直接在邏輯中使用雙引號呼叫，並輸出在 CSV 變數表中。
4. SCL 的賦值符號是 `:=`。多重實例計時器型態為 `TON_TIME` 或 `IEC_TIMER`。
"""

# ==========================================
# 3. 系統工具函式
# ==========================================
def clean_scl_string(raw_scl: str) -> str:
    """正則暴力清道夫：精準切下 SCL 區塊，無視 AI 偷加的 Markdown 或廢話"""
    match = re.search(r'(FUNCTION_BLOCK.*?END_FUNCTION_BLOCK|FUNCTION.*?END_FUNCTION)', raw_scl, re.IGNORECASE | re.DOTALL)
    if match:
        return match.group(1).strip()
    return raw_scl.replace("```scl", "").replace("```pascal", "").replace("```", "").replace("[SCL_CODE]", "").replace("[/SCL_CODE]", "").strip()

@st.cache_data
def load_knowledge_base():
    """載入靜態 JSON 知識庫 (避免每次切換頁面都重新讀取)"""
    base_dir = "data/templates" if os.path.exists("data/templates") else "../data/templates"
    files_to_load = ["scl_qa_test_10.json", "io_mapping_test_10.json", "lib_test_10.json", "tech_test_10.json"]
    combined_knowledge = ""
    loaded_files = []
    
    for file_name in files_to_load:
        file_path = os.path.join(base_dir, file_name)
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    combined_knowledge += f"\n\n--- 來自 {file_name} 的知識 ---\n"
                    combined_knowledge += json.dumps(data, ensure_ascii=False, indent=2)
                    loaded_files.append(file_name)
            except Exception:
                pass
                
    return combined_knowledge, loaded_files