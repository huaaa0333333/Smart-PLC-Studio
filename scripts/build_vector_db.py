import os
import chromadb
try:
    import fitz  # PyMuPDF
except ImportError:
    raise ImportError("請先執行 pip install PyMuPDF")

# ==========================================
# 1. 路徑與多版本手冊設定 (🌟 升級為陣列，方便未來擴充)
# ==========================================
DB_PATH = "D:/Smart-PLC-Studio/data/chroma_db"

# 將你要匯入的手冊與對應的「版本標籤」寫在這裡
MANUALS_TO_INGEST = [
    {
        "path": "D:/Smart-PLC-Studio/data/manuals/siemens_V19/V19_10.pdf",
        "version": "V19"
    },
    {
        "path": "D:/Smart-PLC-Studio/data/manuals/siemens_V19/V19_11.pdf",
        "version": "V19"
    },    
    {
        "path": "D:/Smart-PLC-Studio/data/manuals/siemens_V19/V19_12.pdf",
        "version": "V19"
    },
        {
        "path": "D:/Smart-PLC-Studio/data/manuals/siemens_V19/V19_15.pdf",
        "version": "V19"
    },
    # 💡 未來如果有 V18 的手冊，只要把檔案放好，解開下面這幾行即可：
    # {
    #     "path": "D:/Smart-PLC-Studio/data/manuals/STEP_7_WinCC_V18_enUS_en-US.pdf",
    #     "version": "V18"
    # }
]

# 切片參數 (Chunking)
CHUNK_SIZE = 1000  
OVERLAP = 200      

def chunk_text(text, chunk_size, overlap):
    """將超長文本切碎為具有重疊區間的小區塊"""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks

def main():
    print("🏭 Smart PLC Studio - 支援多版本的向量知識庫建置系統啟動\n")

    # ==========================================
    # 2. 初始化 ChromaDB (🌟 砍掉舊的，建立全新乾淨的資料庫)
    # ==========================================
    print(f"🧠 正在連接本地向量資料庫 (儲存於 {DB_PATH}) ...")
    client = chromadb.PersistentClient(path=DB_PATH)
    
    # 因為我們更改了 Metadata 結構，最安全的方法是清空重建
    try:
        client.delete_collection("siemens_knowledge")
        print("🗑️ 已清除舊版無標籤的知識庫資料。")
    except Exception:
        pass
        
    collection = client.create_collection(name="siemens_knowledge")

    # ==========================================
    # 3. 批次處理所有手冊
    # ==========================================
    for manual in MANUALS_TO_INGEST:
        pdf_path = manual["path"]
        version_tag = manual["version"]
        file_name = os.path.basename(pdf_path)

        if not os.path.exists(pdf_path):
            print(f"❌ 找不到 PDF 檔案：{pdf_path}，已略過。")
            continue

        print(f"\n📄 [處理中] 正在讀取 {version_tag} 手冊: {file_name} ...")
        
        doc = fitz.open(pdf_path)
        full_text = ""
        for i in range(len(doc)):
            full_text += doc[i].get_text("text") + "\n"
        doc.close()
        
        print(f"✂️  正在進行語意切片 (Chunking)...")
        chunks = chunk_text(full_text, CHUNK_SIZE, OVERLAP)
        
        # 準備寫入資料的格式
        documents = chunks
        ids = [f"tech_func_{version_tag}_chunk_{i}" for i in range(len(chunks))]
        
        # 🌟 核心魔法：把版本標籤 (version) 塞進 metadata 裡面！
        metadatas = [
            {
                "source": file_name, 
                "page_approx": i,
                "version": version_tag  # 👈 未來檢索就是靠這個過濾！
            } for i in range(len(chunks))
        ]
        
        print(f"💾 開始將 {len(chunks)} 筆知識轉化為神經向量並寫入資料庫...")
        collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        print(f"✅ {version_tag} 手冊建置完成！")

    print(f"\n🎉 恭喜！多版本向量資料庫建置完成！實體儲存於：{os.path.abspath(DB_PATH)}")

if __name__ == "__main__":
    main()