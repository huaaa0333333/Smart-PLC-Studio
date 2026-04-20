import streamlit as st

def apply_custom_css(theme_name="預設科技黑 (Default)"):
    """
    終極佈景主題引擎 (V3.1)。
    徹底掃除「頑固白色區塊」 (Expander Headers, Sidebar Header)。
    """
    
    LIGHT_THEMES = ["經典極簡白", "回憶之域 (Memories of Realms)"]
    is_light = theme_name in LIGHT_THEMES

    themes = {
        "預設科技黑 (Default)": {
            "bg_app": "#0A191F",
            "bg_sidebar": "#071318",
            "bg_secondary": "#0F242C",
            "text_main": "#DCE3E8",
            "text_muted": "#94A3B8",
            "text_inverse": "#0A191F",
            "accent": "#00E6A8",
            "btn_p_top": "#00E6A8",
            "btn_p_bot": "#00B386",
            "btn_s_bg": "#1A2E35",
            "btn_s_text": "#DCE3E8",
            "border": "rgba(0, 230, 168, 0.2)",
            "shadow": "rgba(0,0,0,0.4)"
        },
        "經典極簡白": {
            "bg_app": "#FFFFFF",
            "bg_sidebar": "#F8F9FA",
            "bg_secondary": "#F0F2F6",
            "text_main": "#1A202C",
            "text_muted": "#4A5568",
            "text_inverse": "#FFFFFF",
            "accent": "#2B6CB0",
            "btn_p_top": "#2D3748",
            "btn_p_bot": "#1A202C",
            "btn_s_bg": "#EDF2F7",
            "btn_s_text": "#1A202C",
            "border": "#E2E8F0",
            "shadow": "rgba(0,0,0,0.05)"
        },
        "質感工業灰": {
            "bg_app": "#2C2E33",
            "bg_sidebar": "#1F2125",
            "bg_secondary": "#33363D",
            "text_main": "#F8FAFC",
            "text_muted": "#A0AEC0",
            "text_inverse": "#1A202C",
            "accent": "#4FD1C5",
            "btn_p_top": "#4FD1C5",
            "btn_p_bot": "#38B2AC",
            "btn_s_bg": "#1A202C",
            "btn_s_text": "#F8FAFC",
            "border": "rgba(255,255,255,0.1)",
            "shadow": "rgba(0,0,0,0.3)"
        },
        "回憶之域 (Memories of Realms)": {
            "bg_app": "#EAF6F5",      # 夢幻水藍底色 (洋裝+背景主調)
            "bg_sidebar": "#D0ECEA",  # 稍深的青藍 (側邊欄層次)
            "bg_secondary": "#B8D8D5",# 中景青灰 (次要背景)
            "text_main": "#0B2C38",   # 極深海藍 (最高對比文字)
            "text_muted": "#2D7A72",  # 深翠青 (次要文字)
            "text_inverse": "#FFFFFF",
            "accent": "#2ABDA8",      # 角色髮色翠青 (最具代表性)
            "btn_p_top": "#3ECFBB",   # 明亮翠青 (主按鈕高光)
            "btn_p_bot": "#2ABDA8",   # 翠青主色 (主按鈕底色)
            "btn_s_bg": "#C5E3E0",    # 淡青灰 (次要按鈕背景)
            "btn_s_text": "#0B2C38",  # 深色文字確保對比
            "border": "#8ECFCA",      # 青色邊框
            "shadow": "rgba(42, 189, 168, 0.18)" # 翠青柔光
        },
        "銀河巡海者 (Galaxy Ranger)": {
            "bg_app": "#0D0D0D",
            "bg_sidebar": "#111111",
            "bg_secondary": "#1A1A1A",
            "text_main": "#F8F9FA",
            "text_muted": "#A2A2A2",
            "text_inverse": "#FFFFFF", 
            "accent": "#C41E3A",
            "btn_p_top": "#C41E3A",
            "btn_p_bot": "#8B0000",
            "btn_s_bg": "#D4AF37",
            "btn_s_text": "#111111", # 鍍金金底配黑字
            "border": "#D4AF37",
            "shadow": "rgba(196, 30, 58, 0.4)"
        }
    }

    t = themes.get(theme_name, themes["預設科技黑 (Default)"])

    css = f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');

        /* 1. 核心底色與語意色彩 (解決淺色爆炸與深色渲染衝突) */
        :root {{
            color-scheme: {"light" if is_light else "dark"} !important;
            --primary-color: {t['accent']} !important;
            --background-color: {t['bg_app']} !important;
            --secondary-background-color: {t['bg_secondary']} !important;
            --text-color: {t['text_main']} !important;
            --font: 'Inter', sans-serif !important;
        }}

        html, body, .stApp, 
        section[data-testid="stSidebar"], 
        div[data-testid="stSidebarContent"],
        div[data-testid="stSidebarNav"],
        div[data-testid="stAppViewContainer"] {{
            background-color: {t['bg_app']} !important;
            color: {t['text_main']} !important;
        }}

        /* 強制覆蓋文字以避免 config.toml 在淺色主題產生「白底白字」 */
        [data-testid="stMarkdownContainer"] p,
        [data-testid="stMarkdownContainer"] h1,
        [data-testid="stMarkdownContainer"] h2,
        [data-testid="stMarkdownContainer"] h3,
        [data-testid="stMarkdownContainer"] h4,
        [data-testid="stMarkdownContainer"] h5,
        [data-testid="stMarkdownContainer"] h6,
        [data-testid="stMarkdownContainer"] li,
        [data-testid="stMetricLabel"] *,
        [data-testid="stText"] *,
        div.stMarkdown {{
            color: {t['text_main']} !important;
        }}

        
        /* 側邊欄專屬底色 */
        section[data-testid="stSidebar"] {{
            background-color: {t['bg_sidebar']} !important;
            border-right: 1px solid {t['border']} !important;
        }}

        /* 2. 【Expander / 摺疊面板修復】 */
        div[data-testid="stExpander"] {{
            background-color: {t['bg_secondary']} !important;
            border: 1px solid {t['border']} !important;
            border-radius: 10px !important;
            overflow: hidden !important;
            color: {t['text_main']} !important;
        }}
        .streamlit-expanderHeader,
        [data-testid="stExpanderDetails"] {{
            background-color: {t['bg_secondary']} !important;
            color: {t['text_main']} !important;
        }}
        .streamlit-expanderHeader p, 
        .streamlit-expanderHeader svg {{
            color: {t['text_main']} !important;
            font-weight: 700 !important;
        }}

        /* 3. 【按鈕修復】 */
        button[data-testid="baseButton-primary"] {{
            background: linear-gradient(135deg, {t['btn_p_top']}, {t['btn_p_bot']}) !important;
            color: {t['text_inverse']} !important;
            border: none !important;
            box-shadow: 0 4px 15px {t['shadow']} !important;
        }}
        
        button[data-testid="baseButton-secondary"],
        div.stButton > button,
        div[data-testid="stDownloadButton"] > button {{
            background-color: {t['btn_s_bg']} !important;
            color: {t['btn_s_text']} !important;
            border: 1px solid {t['border']} !important;
        }}
        
        button[data-testid="baseButton-secondary"]:hover,
        div.stButton > button:hover,
        div[data-testid="stDownloadButton"] > button:hover {{
            border-color: {t['accent']} !important;
            color: {t['accent']} !important;
        }}

        /* 4. 【輸入元件】 文字、Label、Placeholder 全修 */
        
        /* 所有輸入框的 Label */
        .stTextInput label, 
        .stTextArea label,
        .stSelectbox label,
        .stFileUploader label,
        [data-testid="stWidgetLabel"] p,
        [data-testid="stWidgetLabel"] {{
            color: {t['text_main']} !important;
            font-weight: 600 !important;
        }}
        
        /* 文字輸入框 & TextArea 的值與佔位符 */
        .stTextInput input,
        .stTextArea textarea {{
            background-color: {t['bg_app']} !important;
            color: {t['text_main']} !important;
            border: 1px solid {t['border']} !important;
        }}
        .stTextInput input::placeholder,
        .stTextArea textarea::placeholder {{
            color: {t['text_muted']} !important;
            opacity: 0.8 !important;
        }}
        
        /* 下拉選單 */
        div[data-baseweb="select"] > div,
        div[data-baseweb="select"] span {{
            background-color: {t['bg_app']} !important;
            color: {t['text_main']} !important;
            border-color: {t['border']} !important;
        }}
        
        /* 檔案上傳區塊 */
        [data-testid="stFileUploadDropzone"],
        [data-testid="stFileUploaderDropzone"] {{
            background-color: {t['bg_secondary']} !important;
            border: 2px dashed {t['border']} !important;
        }}
        [data-testid="stFileUploadDropzone"] p,
        [data-testid="stFileUploadDropzone"] small,
        [data-testid="stFileUploaderDropzone"] p,
        [data-testid="stFileUploaderDropzone"] small {{
            color: {t['text_muted']} !important;
        }}

        /* 5. 側邊欄文字控制 (全量) */
        [data-testid="stSidebar"] * {{
            color: {t['text_main']} !important;
        }}
        
        /* 側邊欄 Expander 圓角修正 (防止內容溢出圓角) */
        [data-testid="stSidebar"] div[data-testid="stExpander"] {{
            border-radius: 10px !important;
            overflow: hidden !important;
        }}
        [data-testid="stSidebar"] div[data-testid="stExpander"] > details {{
            border-radius: 10px !important;
            overflow: hidden !important;
        }}
        
        /* Radio button 選項區塊不蓋過圓角 */
        [data-testid="stSidebar"] [data-testid="stRadio"] {{
            background-color: transparent !important;
        }}

        /* 基本 HTML Table 渲染樣式 (供 df.to_html 轉換使用) */
        table {{
            width: 100% !important;
            border-collapse: collapse !important;
            margin-bottom: 1rem !important;
        }}
        table, th, td {{
            color: {t['text_main']} !important;
            border: 1px solid {t['border']} !important;
            padding: 8px 12px !important;
        }}
        thead tr th {{
            background-color: {t['btn_s_bg']} !important;
            color: {t['text_main']} !important;
            font-weight: 600 !important;
            text-align: left !important;
        }}
        tbody tr td {{
            background-color: {t['bg_secondary']} !important;
            color: {t['text_main']} !important;
        }}

        /* 隱藏原生組件與多餘背景 */
        header[data-testid="stHeader"] {{
            background: transparent !important;
        }}
        [data-testid="stAppViewContainer"] > header {{
            background-color: transparent !important;
            border-bottom: none !important;
        }}
        
        /* 程式碼 & ASCII Art 等寬字型修正 */
        pre, code, .stCodeBlock {{
            font-family: 'Courier New', Consolas, 'Lucida Console', 'DejaVu Sans Mono', monospace !important;
            font-size: 13px !important;
            line-height: 1.5 !important;
            letter-spacing: 0 !important;
            word-spacing: 0 !important;
        }}
        pre, code {{
            white-space: pre !important;
        }}
        div[data-testid="stCodeBlock"] {{
            width: 100% !important;
            max-width: 100% !important;
            overflow-x: auto !important;
        }}
        pre {{
            overflow-x: auto !important;
            background-color: #1A202C !important;
            color: #48BB78 !important;
            border-radius: 6px !important;
            padding: 1rem !important;
            max-width: 100% !important;
        }}
        </style>
    """
    st.markdown(css, unsafe_allow_html=True)

    # 亮色主題需要額外強制蓋過 config.toml 的深色基底
    if is_light:
        light_bg  = t['bg_app']
        light_sec = t['bg_secondary']
        light_txt = t['text_main']
        light_bdr = t['border']
        light_muted = t['text_muted']
        
        extra_css = f"""
        <style>
        /* =====================================================
           亮色主題補強覆蓋 (針對 Streamlit 特有元件的深色殘酷寫死修復)
        ===================================================== */

        /* 所有可能的背景容器 */
        .main, .block-container, 
        div[data-testid="stVerticalBlock"],
        div[data-testid="stHorizontalBlock"],
        div.stBlock, div.element-container {{
            background-color: {light_bg} !important;
        }}

        /* Checkbox & Radio 按鈕與文字修復 */
        [data-testid="stCheckbox"] label,
        [data-testid="stRadio"] label {{
            color: {light_txt} !important;
        }}
        [data-testid="stCheckbox"] div[data-checked="false"],
        [data-testid="stRadio"] div[data-checked="false"] {{
            background-color: {light_bg} !important;
            border-color: {light_bdr} !important;
        }}

        /* Table/Dataframes 樣式覆蓋 */
        table {{
            width: 100% !important;
            border-collapse: collapse !important;
        }}
        table, th, td {{
            color: {light_txt} !important;
            border: 1px solid {light_bdr} !important;
            padding: 8px 12px !important;
        }}
        thead tr th {{
            background-color: {light_sec} !important;
            color: {light_txt} !important;
            font-weight: 600 !important;
        }}
        tbody tr td {{
            background-color: {light_bg} !important;
            color: {light_txt} !important;
        }}

        /* 程式碼區塊淺色覆蓋 (避免在淺色主題出現全黑方塊) */
        pre, code, .stCodeBlock, div[data-testid="stCodeBlock"] {{
            background-color: {light_sec} !important;
            color: #0F5A3E !important; 
        }}

        /* 分頁元件 Tabs 修復 */
        button[data-baseweb="tab"] {{
            color: {light_muted} !important;
            background-color: transparent !important;
        }}
        button[data-baseweb="tab"][aria-selected="true"] {{
            color: {t['accent']} !important;
        }}
        button[data-baseweb="tab"][aria-selected="true"] span {{
            color: {t['accent']} !important;
        }}
        div[data-baseweb="tab-highlight"] {{
            background-color: {t['accent']} !important;
        }}
        
        /* Metric 容器 */
        [data-testid="stMetric"],
        [data-testid="stMetricValue"],
        [data-testid="stMetricDelta"],
        div[data-testid="metric-container"] {{
            background-color: transparent !important;
            color: {light_txt} !important;
        }}
        [data-testid="stMetricValue"] {{
            color: {t['accent']} !important;
        }}
        
        /* Expander 所有子元素 (保留圓角) */
        details {{
            background-color: {light_sec} !important;
            color: {light_txt} !important;
            border-radius: 10px !important;
            overflow: hidden;
        }}
        details > summary {{
            background-color: {light_sec} !important;
            color: {light_txt} !important;
            border-radius: 10px !important;
            padding: 0.75rem 1rem !important;
        }}
        details[open] > summary {{
            border-radius: 10px 10px 0 0 !important;
        }}
        details > div {{
            background-color: {light_sec} !important;
            color: {light_txt} !important;
        }}
        
        /* 輸入框深色殘留清除 */
        .stTextInput input,
        .stTextArea textarea,
        div[data-baseweb="input"],
        div[data-baseweb="textarea"] {{
            background-color: {light_bg} !important;
            color: {light_txt} !important;
            border: 1px solid {light_bdr} !important;
        }}
        
        /* 檔案上傳黑色殘留 */
        section[data-testid="stFileUploadDropzone"] > div,
        [data-testid="stFileUploaderDropzone"] > div,
        div[data-testid="stFileUploader"] > section {{
            background-color: {light_sec} !important;
            border: 2px dashed {light_bdr} !important;
        }}
        [data-testid*="FileUpload"] span, 
        [data-testid*="FileUpload"] p, 
        [data-testid*="FileUpload"] small {{
            color: {light_muted} !important;
        }}
        
        /* Selectbox 選項列表 */
        ul[data-baseweb="menu"],
        li[data-baseweb="menu-item"],
        div[data-baseweb="popover"] div {{
            background-color: {light_bg} !important;
            color: {light_txt} !important;
        }}
        </style>
        """
        st.markdown(extra_css, unsafe_allow_html=True)

