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
1. 【宣告區塊】：FB 靜態變數必須用 `VAR` 宣告。所有在邏輯中用到的暫存變數 (包含 FOR 迴圈的 index 如 `#i`) 必須在 `VAR_TEMP` 中宣告！變數名稱宣告不可含 `#` 或 `"` (例如寫 `Run_Latch : Bool;` 或 `i : Int;`)。
2. 【邏輯區塊】：在 `BEGIN` 之後呼叫「內部變數」必加 `#` (如 `#Run_Latch`)，呼叫「實體 IO」必加雙引號 (如 `"Start_Button"`)。
3. 【IO 隔離】：對應實體 %I, %Q 的接點不可在 SCL 內部宣告，必須直接以雙引號呼叫，並產出在 CSV 變數表中。
4. 【工藝物件與計時器】：多重實例計時器請宣告為 `TON_TIME` 或 `IEC_TIMER`。計數器請宣告為 `CTU_INT` 或 `IEC_COUNTER`，絕對不可唯讀使用 `CTU`。
5. 【嚴禁自我引用與直接重置】：呼叫 Timer/Counter 時，【絕對不可以】將自身的 `.Q` 或輸出參數直接寫在自己的輸入引數中 (例如 `IN := NOT #MyTimer.Q` 會導致未知的行為或報錯！)。若要做閃爍器或重置，必須用額外的 BOOL 暫存旗標，或是將兩顆 Timer 交替。
6. 【陣列宣告】：宣告陣列時必須遵守標準格式，例如 `MyArray : Array[0..9] of Bool;`。
7. 【數學運算子限制】：SCL 中的除法必須使用 `/`，【絕對不可使用 `DIV`】(這會被判定為未知指令)。例如商數運算請寫 `#A := #B / 10;`，取餘數再用 `MOD`。
8. 【全域變數表限制】：CSV 變數表純粹用於全域接點 (%I, %Q) 與全域記憶體 (%M)。**絕對嚴禁**將任何計時器 (TON_TIME)、計數器 (CTU_INT) 或功能塊背景資料區 (DB) 匯出到 CSV 變數表中！這些純屬區域實例，必須完全定義在 SCL 的 `VAR` 靜態區塊內！
9. 【計時器強制參數與單一呼叫】：呼叫 IEC 計時器時，【必須】明確寫出 `PT` 引數，且**同一個計時器實例在整個 FB 中【絕對只能呼叫一次】！** 請將計時器的呼叫寫在程式碼最末端，並用邏輯運算式控制 `IN` 與 `PT`。嚴禁在 IF 或 CASE 的不同分支內「多次呼叫同一個計時器」並多次傳入 `PT`，這會導致 TIA Portal 編譯器報錯『參數 PT 已使用』！
10. 【狀態機與 CONSTANT 宣告】：若要在 `CASE` 迴圈使用具名標籤 (例如 `CASE #State OF #STATE_IDLE:`)，這些標籤名稱【必須宣告於 `VAR CONSTANT` 區塊內】，絕對不可宣告於普通 `VAR` 內，否則編譯器會報錯『CASE 表達式中的資料類型無效』！建議您可以直接使用數字 `0:`, `1:` 配合註解來當分支，最不容易出錯！
11. 【嚴禁 Pascal 十六進制語法】：SCL 的十六進制必須寫成 `16#00`。請【絕對不要】使用類似 `$00` 或 `$01` 的語法，TIA Portal 編譯器會將其判定為無效字元 (設定值"$00"無效)！"""

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