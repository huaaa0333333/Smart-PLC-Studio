import os
import json
import re
from dotenv import load_dotenv
from google import genai
from google.genai import types

# 載入底層 PDF 解析引擎
try:
    import fitz 
except ImportError:
    raise ImportError("請先執行指令安裝套件: pip install PyMuPDF")

# 初始化與金鑰設定
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError("找不到 GEMINI_API_KEY，請確認 .env 檔案設定是否正確。")

client = genai.Client(api_key=API_KEY)

SYSTEM_PROMPT = """
你是一位專精於西門子 TIA Portal 與 SCL 語言的資深自動化控制專家。
我會提供一份西門子手冊的部分純文字內容。
請從中萃取出符合「階段一：基礎邏輯（如基礎邏輯閘、計時器、計數器、馬達啟停）」的知識，並轉換為問答 (QA) 格式。

【輸出格式要求】
請務必只輸出合法的 JSON 陣列 (Array)。每個物件需具備以下欄位：
- "id": 唯一識別碼 (例如 SCL_QA_001)
- "category": 題目分類 (例如 基礎邏輯_計時器應用)
- "instruction": 使用者的自然語言指令
- "context": 補充的系統限制或條件 (例如需使用 TON 計時器)
- "response": 標準的 SCL 程式碼與詳細的中文註解
"""

def main():
    pdf_path = "D:/Smart-PLC-Studio/data/manuals/scl_core_knowledge_only.pdf" # 確認這是你 1300 萬字的第 12 章檔案
    output_path = "D:/Smart-PLC-Studio/data/templates/scl_qa_test_10.json"
    
    if not os.path.exists(pdf_path):
        print(f"❌ 找不到 PDF 檔案：{pdf_path}")
        return

    try:
        print(f"開始讀取巨型 PDF ({pdf_path})...")
        doc = fitz.open(pdf_path)
        raw_text = ""
        
        # 為了效能，我們不需要把 1300 萬字全讀完。
        # 假設一頁大約 2000 字，我們只先讀取前 100 頁來做測試
        for page_num in range(min(100, len(doc))): 
            page = doc.load_page(page_num)
            raw_text += page.get_text("text") + "\n"
            
        print(f"✅ 讀取完成！目前暫存區共有 {len(raw_text)} 個字元。")
        doc.close()

        # ---------------------------------------------------------
        # 👑 關鍵防護機制：文字切片 (Chunking)
        # 避開最前面的目錄，抓取中間 10 萬字的精華區段
        # ---------------------------------------------------------
        start_index = 20000  # 跳過前面兩萬字的目錄與前言
        end_index = 120000   # 擷取 10 萬字給 AI 閱讀
        
        # 確保不會超出字串長度
        safe_chunk = raw_text[start_index:min(end_index, len(raw_text))]
        print(f"✂️ 已成功切出 {len(safe_chunk)} 個字元的區塊，準備送出分析！\n")

        print("呼叫 Gemini 進行 10 題 PoC 生成 (請稍候)...")
        
        user_prompt = "請根據以下手冊區塊內容，精萃出「剛好 10 題」最具代表性的基礎邏輯 QA。請將結果包裝在 ```json 和 ``` 標籤之間，並確保 SCL 語法完全符合西門子規範。\n\n" + safe_chunk

        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=user_prompt, 
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.1, 
            )
        )

        # 擷取 JSON
        ai_reply = response.text
        match = re.search(r'```json\n(.*?)\n```', ai_reply, re.DOTALL)
        if match:
            json_str = match.group(1)
        else:
            json_str = ai_reply.replace('```json', '').replace('```', '').strip()

        # 解析與儲存
        result_json = json.loads(json_str)
        qa_data = result_json if isinstance(result_json, list) else result_json.get("qa_list", [])
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(qa_data, f, ensure_ascii=False, indent=4)
            
        print(f"🎉 史詩級勝利！成功生成 {len(qa_data)} 題 QA。")
        print(f"檔案已穩穩地存放在：{output_path}")

    except json.JSONDecodeError as e:
        print(f"❌ JSON 解析失敗。解析錯誤：{e}")
    except Exception as e:
        print(f"❌ 執行過程中發生錯誤：{e}")

if __name__ == "__main__":
    main()
