import streamlit as st

def apply_custom_css():
    """注入客製化高質感 (Dark Pine/Teal) 的 CSS"""
    st.markdown("""
        <style>
        /* 導入現代字型 */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

        /* 1. Global Base */
        html, body, [class*="css"]  {
            font-family: 'Inter', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            background-color: #0A191F !important;
        }
        
        /* 2. Sidebar Glassmorphism */
        [data-testid="stSidebar"] {
            background-color: rgba(15, 36, 44, 0.85);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border-right: 1px solid rgba(0, 230, 168, 0.15);
        }

        /* 3. Primary Button 質感薄荷綠 */
        button[data-testid="baseButton-primary"] {
            background: linear-gradient(135deg, #00E6A8 0%, #00B386 100%);
            border: none;
            color: #0A191F !important;  /* 深色字體更能於亮色背景中顯現 */
            font-weight: 700;
            border-radius: 8px;
            padding: 0.5rem 1.5rem;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(0, 230, 168, 0.2);
        }
        button[data-testid="baseButton-primary"]:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(0, 230, 168, 0.4);
            background: linear-gradient(135deg, #1AFFB9 0%, #00CCA0 100%);
        }

        /* 4. Secondary/Default Button 邊框發光 */
        button[data-testid="baseButton-secondary"] {
            border: 1px solid rgba(255, 255, 255, 0.2);
            background-color: transparent;
            font-weight: 500;
            border-radius: 8px;
            color: #DCE3E8;
            transition: all 0.3s ease;
        }
        button[data-testid="baseButton-secondary"]:hover {
            border-color: #00E6A8;
            color: #00E6A8;
            box-shadow: 0 0 10px rgba(0, 230, 168, 0.15);
            transform: translateY(-1px);
        }

        /* 5. Inputs & Text Areas (聚焦時邊框發光) */
        .stTextArea textarea, .stTextInput input {
            background-color: #0F242C;
            border-radius: 8px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            color: #DCE3E8;
            transition: all 0.3s ease;
        }
        .stTextArea textarea:focus, .stTextInput input:focus {
            border-color: #00E6A8;
            box-shadow: 0 0 0 1px #00E6A8, 0 0 10px rgba(0,230,168,0.1) !important;
        }
        
        /* 6. Metrics 卡片數據風格化 (首頁用) */
        [data-testid="stMetricValue"] {
            font-size: 2.5rem;
            font-weight: 700;
            background: -webkit-linear-gradient(45deg, #00E6A8, #00B386);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            filter: drop-shadow(0px 2px 4px rgba(0,230,168,0.15));
        }

        /* 7. Markdown Blockquotes (引言區塊質感化) */
        blockquote {
            border-left: 4px solid #00E6A8;
            background-color: rgba(0, 230, 168, 0.05);
            padding: 1rem;
            border-radius: 0 8px 8px 0;
            margin-left: 0;
            color: #A0B2BC;
        }

        /* 8. Expander 扁平化微陰影 */
        .streamlit-expanderHeader {
            background-color: #0F242C;
            border-radius: 8px;
            font-weight: 600;
            color: #E2E8F0;
        }
        
        /* 9. 分隔線優化 */
        hr {
            border-color: rgba(255, 255, 255, 0.08) !important;
        }

        /* 10. 隱藏 Streamlit 原生累贅元件 (但保留側邊欄展開按鈕) */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {background: transparent !important;}
        [data-testid="stHeader"] {background: transparent !important;}
        .stDeployButton {display:none;}
        [data-testid="stHeaderActionElements"] {display: none;} /* 只隱藏右上角的選單列 */
        </style>
    """, unsafe_allow_html=True)
