import os
import streamlit as st
from dotenv import load_dotenv
from google import genai
from services.rag_service import init_chromadb
from workflows import orchestrator_ui

# ==========================================
# 1. 頁面基本設定 (必須在所有程式碼的最前面)
# ==========================================
st.set_page_config(page_title="Smart PLC Studio - 全能工作站", page_icon="🏭", layout="wide")

# ==========================================
# 2. 引入自訂模組
# ==========================================
from core import utils
from agents import mod_bug_clinic
from agents import mod_batch

# ==========================================
# 3. 系統資源初始化 (Gemini 引擎 & 向量大腦)
# ==========================================
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    st.error("❌ 找不到 GEMINI_API_KEY，請確認 .env 檔案設定是否正確。")
    st.stop()

# 建立 Gemini 客戶端
client = genai.Client(api_key=API_KEY)

# 建立 ChromaDB 連線
collection, db_connected = init_chromadb("siemens_knowledge")

# 初始化各模組的獨立歷史紀錄
if "history_arch" not in st.session_state: st.session_state.history_arch = []
if "history_gen" not in st.session_state: st.session_state.history_gen = []
if "history_hmi" not in st.session_state: st.session_state.history_hmi = []
if "history_bug" not in st.session_state: st.session_state.history_bug = []
if "history_batch" not in st.session_state: st.session_state.history_batch = []
if "history_pdf" not in st.session_state: st.session_state.history_pdf = []

# ==========================================
# 4. 主程式路由 (側邊欄導航)
# ==========================================
with st.sidebar:
    st.title("🏭 導航選單")
    page = st.radio("前往工作室：", [
        "🏠 首頁主控台",
        "🚀 一鍵全自動生產線",
        "🛠️ Bug 診療室",
        "📦 批次題庫引擎"
    ])
    st.divider()
    if st.button("🗑️ 清除當前頁面紀錄", use_container_width=True):
        if "PLC 架構設計師" in page: st.session_state.history_arch = []
        elif "SCL 智能生成" in page or "進階工藝" in page: st.session_state.history_gen = []
        elif "HMI 介面規劃師" in page: st.session_state.history_hmi = []
        elif "Bug 診療室" in page: st.session_state.history_bug = []
        elif "批次題庫" in page: st.session_state.history_batch = []
        elif "PDF 考題破解器" in page: st.session_state.history_pdf = []
        st.rerun()

# ==========================================
# 5. 畫面渲染分發
# ==========================================
if page == "🏠 首頁主控台":
    st.title("🏭 Smart PLC Studio - 首頁主控台")
    st.markdown("歡迎來到西門子自動化全能工作站！這是一個結合多智慧代理人 (Multi-Agent) 協作的工業級開發平台。")
    
    col1, col2 = st.columns(2)
    with col1:
        st.info("🟢 **核心引擎狀態**：Gemini API 連線正常")
        st.success("🟢 **知識庫連線**：ChromaDB 已就緒" if db_connected else "🔴 **知識庫連線**：ChromaDB 未連線")
    with col2:
        _, loaded_modules = utils.load_knowledge_base()
        st.markdown("#### 📚 已掛載的靜態手冊模型")
        for mod in loaded_modules:
            st.markdown(f"- `{mod}`")
    
    st.divider()
    st.markdown("### 🚀 系統功能導覽\n"
                "* **🚀 一鍵全自動生產線**：上傳規格書或輸入需求，AI 將自動為您完成【架構選型】 ➡️ 【SCL 程式開發】 ➡️ 【HMI 介面規劃】的端到端資料流。\n"
                "* **🛠️ Bug 診療室**：貼上報錯，AI 幫你抓蟲並給出修復檔。\n"
                "* **📦 批次題庫引擎**：結合手冊知識庫，一鍵產出大量測試腳本與 QA (支援 Excel 匯出)。")

elif page == "🚀 一鍵全自動生產線":
    orchestrator_ui.render(client, collection)

elif page == "🛠️ Bug 診療室":
    mod_bug_clinic.render(client)

elif page == "📦 批次題庫引擎":
    mod_batch.render(client)