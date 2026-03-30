# 🏭 Smart PLC Studio - 全能自動化工作站

![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Gemini](https://img.shields.io/badge/Gemini_2.5-8E75B2?style=for-the-badge&logo=googlebard&logoColor=white)
![ChromaDB](https://img.shields.io/badge/ChromaDB-FF6F00?style=for-the-badge)

Smart PLC Studio 是一個基於 LLM (大型語言模型) 與 RAG (檢索增強生成) 技術打造的工業級自動化開發輔助系統。專為西門子 TIA Portal 設計，能將自然語言、PDF 規格書瞬間轉化為高品質的 SCL 程式碼與變數表。

## ✨ 核心模組功能

1. **📝 SCL 智能生成與教學**：輸入自然語言需求，自動產出具備新手教學的 SCL 邏輯區塊，並嚴格遵守 IO 隔離與語法鐵律。
2. **🛠️ Bug 診療室**：貼上編譯報錯或問題程式碼，AI 專家自動診斷漏洞並提供完美修復檔。
3. **⚙️ 進階工藝控制**：專為 PID_Compact、Motion Control 等複雜工藝物件與數學運算打造。
4. **📦 批次題庫引擎**：結合手冊知識庫，一鍵量產數百題工業標準測試腳本與 QA 題庫，支援 Excel 匯出。
5. **📄 PDF 考題破解器**：上傳系統規格書或技能競賽術科 PDF，透過多模態視覺解析，自動梳理流程並生成完整程式碼。

## 🚀 快速啟動 (Quick Start)

### 方法一：使用 Docker Compose 一鍵部署 (推薦)

1. 複製環境變數範本並填寫 API Key：
   ```bash
   cp .env.example .env
   # 編輯 .env 填入 GEMINI_API_KEY
   ```
2. 透過 Docker Compose 啟動服務：
   ```bash
   docker compose up -d --build
   ```
   *(若是未來想關閉服務，可使用 `docker compose down`)*
3. 初始化 Chroma 向量資料庫 (選擇性，若需使用 PDF 破題或題庫等技術文件功能)：
   *(注意：請確保 `data/manuals/` 資料夾內有 PDF 手冊)*
   ```bash
   docker compose exec smart-plc-studio python scripts/build_vector_db.py
   ```
4. 開啟瀏覽器，前往：`http://localhost:8501`

### 方法二：本地端直接執行 (Local Setup)

1. 安裝環境需求套件：
   ```bash
   pip install -r requirements.txt
   ```
2. 初始化 Chroma 向量資料庫：
   ```bash
   python scripts/build_vector_db.py
   ```
3. 啟動 Smart PLC Studio：
   ```bash
   streamlit run ui.py
   ```

## 🧩 多代理工作流 (Multi‑Agent Orchestration)

此功能允許使用者一次執行完整的自動化流水線，串接以下模組：

- 架構設計師
- SCL 產生器
- HMI 設計師
- Bug 診斷室
- 批次題庫引擎
- PDF 破解

在側邊欄選擇 **🧩 多代理工作流**，選擇工作流（例如 *PDF → 完整流程*），上傳 PDF（如需），點擊 **執行工作流**，系統會依序執行每個階段並顯示進度與最終產出。

```mermaid
flowchart LR
    A[上傳 PDF] --> B[架構設計師]
    B --> C[SCL 產生器]
    C --> D[HMI 設計師]
    D --> E[Bug 診斷室]
    E --> F[批次題庫引擎]
    F --> G[PDF 破解]
```

如需更多說明，請參考 `orchestrator_ui.py` 與 `orchestrator.py`。