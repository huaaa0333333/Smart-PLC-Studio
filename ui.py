import os
import streamlit  as st
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
# 4. 主程式路由 (側邊欄摺疊收納導航)
# ==========================================
# 初始化頁面狀態（避免下載或其他重跑時跳回）
if "page" not in st.session_state:
    st.session_state.page = "⚡ 一鍵自動化生產線 (Home)"

with st.sidebar:
    st.title("🏭 工作站導航")
    
    with st.expander("🚀 主核心引擎", expanded=True):
        page = st.radio(
            "前往模式：",
            ["⚡ 一鍵自動化生產線 (Home)", "🛠️ Bug 診療室"],
            label_visibility="collapsed",
            key="page_radio"
        )
        # 同步到 session_state
        st.session_state.page = page
        
    with st.expander("⚙️ 系統設定與快取", expanded=False):
        if st.button("🗑️ 清除所有快取紀錄", use_container_width=True):
            st.session_state.history_arch = []
            st.session_state.history_gen = []
            st.session_state.history_hmi = []
            st.session_state.history_bug = []
            st.session_state.history_batch = []
            st.session_state.history_pdf = []
            if "pipeline_res" in st.session_state:
                del st.session_state.pipeline_res
            st.rerun()

# ==========================================
# 5. 畫面渲染分發
# ==========================================
if st.session_state.page == "⚡ 一鍵自動化生產線 (Home)":
    # (這是一個統合 Dashboard 與流水線的終極首頁)
    st.title("⚡ Smart PLC Studio - 聯邦智能核心")
    
    # 判斷是否隱藏儀表板 (如果已有結果，則收納起來節省空間防止跳動感)
    has_results = "pipeline_res" in st.session_state
    
    with st.expander("📊 系統狀態儀表板", expanded=not has_results):
        st.markdown("> 歡迎來到西門子自動化開發輔助核心，整合 Multi-Agent 工作流與 RAG 專業知識檢索技術。")
        col1, col2 = st.columns(2)
        with col1:
            st.metric(label="🧠 LLM 核心大腦", value="ONLINE", delta="Gemini 2.5 Flash")
        with col2:
            status_val = "READY" if db_connected else "OFFLINE"
            status_delta = "ChromaDB Server" if db_connected else "Check Connection"
            st.metric(label="📚 RAG 向量知識庫", value=status_val, delta=status_delta, delta_color="normal" if db_connected else "inverse")
    
    st.divider()

    # 進入真正的流水線 UI
    orchestrator_ui.render(client, collection)

elif page == "🛠️ Bug 診療室":
    mod_bug_clinic.render(client)
