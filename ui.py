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
from core.ui_styles import apply_custom_css
from agents import mod_bug_clinic
from agents import mod_batch

# 套用全站深色科技風 CSS
apply_custom_css()

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
    st.title("⚡ Smart PLC Studio - 智慧指揮中心")
    st.markdown("> 歡迎來到西門子自動化開發輔助核心，整合 Multi-Agent 工作流與 RAG 專業向量知識檢索技術。")
    
    st.divider()
    
    # 使用 st.metric 展現高質感數據狀態
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="🧠 LLM 核心大腦", value="ONLINE", delta="Gemini 2.5 Flash")
    with col2:
        status_val = "READY" if db_connected else "OFFLINE"
        status_delta = "ChromaDB Server" if db_connected else "Check Connection"
        st.metric(label="📚 RAG 向量知識庫", value=status_val, delta=status_delta, delta_color="normal" if db_connected else "inverse")
    with col3:
        _, loaded_modules = utils.load_knowledge_base()
        st.metric(label="📄 基礎手冊模型庫", value=f"{len(loaded_modules)} 卷冊", delta="覆蓋 V17-V19 規範")
    
    st.divider()
    
    st.markdown("### 🚀 核心模組導覽")
    st.info("**🚀 一鍵全自動生產線**：上傳 PDF 規格書 ➡️ 【架構選型】 ➡️ 【SCL 程式開發】 ➡️ 【HMI 規劃】的端到端資料流。")
    st.success("**📝 SCL 智能生成**：輸入口語需求，結合指定版本的知識庫，輸出極淨的 `.scl` 邏輯代碼。")
    st.warning("**🛠️ Bug 診療室**：貼上 TIA Portal 報錯，AI 幫你抓蟲並給出完全修復檔。")
    st.error("**📦 批次題庫引擎**：一鍵產出上百題工業標準測試腳本與 QA (支援 XLSX 匯出)。")

elif page == "🚀 一鍵全自動生產線":
    orchestrator_ui.render(client, collection)

elif page == "🛠️ Bug 診療室":
    mod_bug_clinic.render(client)

elif page == "📦 批次題庫引擎":
    mod_batch.render(client)