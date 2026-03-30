import os
import chromadb

def init_chromadb(db_name="siemens_knowledge"):
    """初始化 ChromaDB 並回傳 collection 及狀態"""
    db_path = "data/chroma_db" if os.path.exists("data/chroma_db") else "../data/chroma_db"
    try:
        db_client = chromadb.PersistentClient(path=db_path)
        collection = db_client.get_collection(name=db_name)
        return collection, True
    except Exception as e:
        print(f"ChromaDB 連線失敗: {e}")
        return None, False

def query_knowledge(collection, query_text, n_results=3, where_filter=None):
    """從 ChromaDB 中查詢相似的文獻"""
    if not collection:
        return ""
        
    try:
        kwargs = {
            "query_texts": [query_text],
            "n_results": n_results
        }
        if where_filter:
            kwargs["where"] = where_filter
            
        results = collection.query(**kwargs)
        if results and "documents" in results and results["documents"][0]:
            return "\n\n---\n\n".join(results["documents"][0])
    except Exception as e:
        print(f"向量庫檢索失敗: {e}")
        
    return ""
