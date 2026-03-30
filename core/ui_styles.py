import streamlit as st

def apply_custom_css():
    """注入客製化高質感 (Dark Cyber-Industrial) 的 CSS"""
    st.markdown("""
        <style>
        /* 導入現代字型 */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

        /* 1. Global Base */
        html, body, [class*="css"]  {
            font-family: 'Inter', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
        }
        
        /* 2. Sidebar Glassmorphism */
        [data-testid="stSidebar"] {
            background-color: rgba(30, 35, 47, 0.7);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border-right: 1px solid rgba(0, 255, 204, 0.15);
        }

        /* 3. Primary Button 炫光霓虹效果 */
        button[data-testid="baseButton-primary"] {
            background: linear-gradient(135deg, #00C6FF 0%, #0072FF 100%);
            border: none;
            color: white !important;
            font-weight: 600;
            border-radius: 8px;
            padding: 0.5rem 1.5rem;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(0, 198, 255, 0.3);
        }
        button[data-testid="baseButton-primary"]:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 25px rgba(0, 198, 255, 0.5);
            background: linear-gradient(135deg, #00d2ff 0%, #0084ff 100%);
        }

        /* 4. Secondary/Default Button 邊框發光 */
        button[data-testid="baseButton-secondary"] {
            border: 1px solid rgba(255, 255, 255, 0.2);
            background-color: transparent;
            font-weight: 500;
            border-radius: 8px;
            transition: all 0.3s ease;
        }
        button[data-testid="baseButton-secondary"]:hover {
            border-color: #00FFCC;
            color: #00FFCC;
            box-shadow: 0 0 12px rgba(0, 255, 204, 0.2);
            transform: translateY(-1px);
        }

        /* 5. Inputs & Text Areas (聚焦時霓虹光暈) */
        .stTextArea textarea, .stTextInput input {
            background-color: #161A25;
            border-radius: 8px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            color: #E2E8F0;
            transition: all 0.3s ease;
        }
        .stTextArea textarea:focus, .stTextInput input:focus {
            border-color: #00FFCC;
            box-shadow: 0 0 0 1px #00FFCC, 0 0 10px rgba(0,255,204,0.2) !important;
        }
        
        /* 6. Metrics 卡片數據風格化 (首頁用) */
        [data-testid="stMetricValue"] {
            font-size: 2.5rem;
            font-weight: 700;
            background: -webkit-linear-gradient(45deg, #00FFCC, #0072FF);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            filter: drop-shadow(0px 2px 4px rgba(0,255,204,0.2));
        }

        /* 7. Markdown Blockquotes (引言區塊質感化) */
        blockquote {
            border-left: 4px solid #00FFCC;
            background-color: rgba(0, 255, 204, 0.05);
            padding: 1rem;
            border-radius: 0 8px 8px 0;
            margin-left: 0;
        }

        /* 8. Expander 扁平化微陰影 */
        .streamlit-expanderHeader {
            background-color: #1A1E29;
            border-radius: 8px;
            font-weight: 600;
        }
        
        /* 9. 分隔線優化 */
        hr {
            border-color: rgba(255, 255, 255, 0.1) !important;
        }
        </style>
    """, unsafe_allow_html=True)
