import os
import json
import re
from dotenv import load_dotenv
from google import genai
from google.genai import types
from core.config import DEFAULT_MODEL

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

# ==========================================
# ⚙️ 萃取目標設定區 (在這裡切換你要跑哪一份)
# ==========================================
# 請輸入 "LIBRARY" 或 "TECH"
TARGET_MODULE = "TECH" 

# 定義不同模組的路徑與專屬 Prompt
CONFIG = {
    "LIBRARY": {
        "pdf_path": "D:/Smart-PLC-Studio/data/manuals/10-Using libraries.pdf",
        "output_path": "D:/Smart-PLC-Studio/data/templates/lib_test_10.json",
        "prompt": """
            你是一位專精於西門子 TIA Portal 架構與版本控管的資深工程師。
            請從以下手冊內容中，萃取出「剛好 10 筆」關於 Libraries (函式庫) 的核心知識。
            請務必輸出 JSON 陣列，每個物件包含：
            "id" (如 LIB_QA_001), "concept" (核心概念), "best_practice" (最佳實踐/操作步驟), "scl_impact" (對 SCL 開發的影響或注意事項)。
        """
    },
    "TECH": {
        "pdf_path": "D:/Smart-PLC-Studio/data/manuals/15-Using technology functions.pdf",
        "output_path": "D:/Smart-PLC-Studio/data/templates/tech_test_10.json",
        "prompt": """
            你是一位專精於西門子 TIA Portal 運動控制與 PID 工藝的資深工程師。
            請從以下手冊內容中，萃取出「剛好 10 筆」關於 Technology Functions 的核心知識。
            請務必輸出 JSON 陣列，每個物件包含：
            "id" (如 TECH_QA_001), "to_type" (工藝物件類型), "instruction" (控制指令), "key_parameters" (關鍵參數說明), "scl_example" (SCL 呼叫範例)。
        """
    }
}

def main():
    current_config = CONFIG[TARGET_MODULE]
    pdf_path = current_config["pdf_path"]
    output_path = current_config["output_path"]
    
    if not os.path.exists(pdf_path):
        print(f"❌ 找不到 PDF 檔案：{pdf_path}")
        return

    try:
        print(f"開始讀取進階手冊 [{TARGET_MODULE}] ({pdf_path})...")
        doc = fitz.open(pdf_path)
        raw_text = ""
        
        # 讀取前 100 頁即可，避免記憶體爆炸
        for page_num in range(min(100, len(doc))): 
            page = doc.load_page(page_num)
            raw_text += page.get_text("text") + "\n"
            
        doc.close()

        # 👑 防護機制：字串切片 (避開目錄，取精華 10 萬字)
        start_index = 10000 
        end_index = 110000   
        safe_chunk = raw_text[start_index:min(end_index, len(raw_text))]
        
        print(f"✂️ 已切出 {len(safe_chunk)} 個字元，準備送出分析！\n")
        print("呼叫 Gemini 進行生成 (請稍候)...")
        
        user_prompt = current_config["prompt"] + "\n\n請將結果包裝在 ```json 和 ``` 標籤之間。\n\n" + safe_chunk

        response = client.models.generate_content(
            model=DEFAULT_MODEL,
            contents=user_prompt, 
            config=types.GenerateContentConfig(
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
            
        print(f"🎉 萃取成功！成功生成 {len(qa_data)} 筆進階資料。")
        print(f"檔案已儲存至：{output_path}")

    except json.JSONDecodeError as e:
        print(f"❌ JSON 解析失敗。解析錯誤：{e}")
    except Exception as e:
        print(f"❌ 執行過程中發生錯誤：{e}")

if __name__ == "__main__":
    main()
