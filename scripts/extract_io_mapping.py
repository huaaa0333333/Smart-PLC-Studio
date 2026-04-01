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
你現在是一位精通西門子 TIA Portal 硬體組態與 PLC Tags 配置的資深自動化工程師。
我會提供一份西門子手冊（第 11 章：設備與網路編輯）的純文字內容。
請從中萃取出關於變數宣告、絕對位址 (如 %I0.0, %Q0.0, %M0.0) 以及資料型態的標準規範。

【輸出格式要求】
請務必只輸出合法的 JSON 陣列 (Array)。每個物件需具備以下欄位：
- "id": 唯一識別碼 (例如 IO_MAP_001)
- "concept": 硬體或變數概念 (例如 數位輸入位址規則、標籤命名規範)
- "address_format": 西門子標準位址寫法 (例如 %I[Byte].[Bit] 或 %MW10)
- "data_type": 建議的資料型別 (例如 Bool, Int, Word)
- "description": 詳細的中文規範說明與 SCL 中的使用注意事項
"""

def main():
    # 📝 請確認這裡的檔名是你剛裁切好的第 11 章檔案
    pdf_path = "D:/Smart-PLC-Studio/data/manuals/chapter_11_io_mapping.pdf" 
    output_path = "D:/Smart-PLC-Studio/data/io_mapping/io_mapping_test_10.json"
    
    if not os.path.exists(pdf_path):
        print(f"❌ 找不到 PDF 檔案：{pdf_path}")
        return

    try:
        print(f"開始讀取第 11 章專屬手冊 ({pdf_path})...")
        doc = fitz.open(pdf_path)
        raw_text = ""
        
        # 讀取全部頁面 (因為已經是裁切過的單一章節)
        for page_num in range(len(doc)): 
            page = doc.load_page(page_num)
            raw_text += page.get_text("text") + "\n"
            
        print(f"✅ 讀取完成！共擷取出 {len(raw_text)} 個字元。")
        doc.close()

        # 👑 防呆切片機制：雖然已經裁切過，但如果字數還是超過 30 萬字，我們就只取前 10 萬字做 PoC，保護 API 配額
        safe_chunk = raw_text
        if len(raw_text) > 300000:
            print("⚠️ 檔案字數較多，為了安全起見，僅擷取前 10 萬字進行測試...")
            safe_chunk = raw_text[:100000]

        print("呼叫 Gemini 進行 10 題 IO 規範生成 (請稍候)...")
        
        user_prompt = "請根據以下手冊內容，精萃出「剛好 10 筆」最具代表性的 IO 變數與位址命名規範。請將結果包裝在 ```json 和 ``` 標籤之間，並確保格式正確。\n\n" + safe_chunk

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
            
        print(f"🎉 擴充成功！成功生成 {len(qa_data)} 筆 IO 規範資料。")
        print(f"檔案已儲存至：{output_path}")

    except json.JSONDecodeError as e:
        print(f"❌ JSON 解析失敗。解析錯誤：{e}")
    except Exception as e:
        print(f"❌ 執行過程中發生錯誤：{e}")

if __name__ == "__main__":
    main()
