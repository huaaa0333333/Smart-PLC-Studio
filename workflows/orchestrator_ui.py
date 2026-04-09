# orchestrator_ui.py
import streamlit as st
import pandas as pd
import io
import re
from workflows.orchestrator import run_automated_pipeline

def render(client, collection):
    st.markdown("### 🧩 無縫資料流生產線")
    st.markdown("真正的自動化設計：只需輸入一次需求，AI 代理人們將依次為您設計 **[硬體架構]** ➡️ **[自動化 SCL 程式碼]** ➡️ **[工業 HMI 佈局]**！")

    # ========= 快捷範本區 (Prompt Templates) =========
    if "pipeline_input_area" not in st.session_state:
        st.session_state.pipeline_input_area = ""

    st.caption("💡 不知道怎麼開始？點擊下方快捷範本自動填入：")
    t_col1, t_col2, t_col3 = st.columns(3)
    if t_col1.button("🟢 簡易輸送帶邏輯", use_container_width=True):
         st.session_state.pipeline_input_area = "設計一個帶有啟動停按鈕與馬達的簡單輸送帶系統。條件：要有綠色運轉燈，還要能按急停按鈕讓整台機器瞬間停下來。預算不高，越簡單越好。"
    if t_col2.button("🌡️ PID 恆溫水槽控制", use_container_width=True):
         st.session_state.pipeline_input_area = "這是一個水循環加熱系統，請幫我設計一個 PID_Compact 溫控邏輯。輸入是 PT100 溫度計，輸出是 PWM 加熱棒控制，並包含上下限警報。"
    if t_col3.button("⚙️ 汽缸順序位移控制", use_container_width=True):
         st.session_state.pipeline_input_area = "幫我寫一個順序控制邏輯 (Sequence Control)。按下啟動後，A汽缸伸出 -> A到位後B汽缸伸出 -> B到位後A退回 -> A退回到位後B退回。需要防呆與時間監控。"

    # ================= 輸入區 =================
    user_input = st.text_area(
        "請描述您的控制需求：", 
        height=140, 
        placeholder="或者您也可以直接在這裡打字，描述你想要達到的成果...",
        key="pipeline_input_area"
    )
    
    # 底部選項與啟動按鈕
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        pdf_file = st.file_uploader("📂 上傳 PDF 題目/規格書 (選填)", type=["pdf"], key="pipeline_pdf_uploader")
    with col2:
        tag_file = st.file_uploader("📊 上傳制式變數/IO表 (CSV/Excel, 選填)", type=["csv", "xlsx", "xls"], key="pipeline_tag_uploader")
    with col3:
        target_version = st.selectbox("🎯 目標 TIA 版本", ["V17", "V18", "V19"], index=0, key="pipeline_target_version")
    
    if st.button("🚀 啟動無縫資料流生產線", type="primary", use_container_width=True):
        if not user_input.strip() and not pdf_file and not tag_file:
            st.warning("請至少輸入需求或上傳檔案！")
        else:
            pdf_bytes = pdf_file.getvalue() if pdf_file else None
            
            tag_table_str = None
            if tag_file:
                try:
                    if tag_file.name.endswith(".csv"):
                        df_tags = pd.read_csv(tag_file)
                    else:
                        df_tags = pd.read_excel(tag_file)
                    tag_table_str = df_tags.to_markdown(index=False)
                except Exception as e:
                    st.error(f"無法讀取變數表檔案: {e}")
            
            # 啟動自動化流水線
            with st.spinner("流水線運作中，請稍候..."):
                pipeline_res = run_automated_pipeline(client, collection, user_input, pdf_bytes=pdf_bytes, tag_table_str=tag_table_str, target_version=target_version)
            
            if not pipeline_res:
                 st.error("❌ 流水線在中途發生嚴重錯誤。")
                 if "pipeline_res" in st.session_state:
                     del st.session_state.pipeline_res
            else:
                 st.session_state.pipeline_res = pipeline_res
                 
    # ==========================================
    # 絕美展示：當 session_state 裡面有結果時就畫出來
    # ==========================================
    if st.session_state.get("pipeline_res"):
        pipeline_res = st.session_state.pipeline_res
        
        st.success("🎉 全部生成完畢！請使用下方頁籤切換查看報告：")
        
        # 建立狀態保留的切換器 (取代會被重置的 st.tabs)
        if "pipeline_active_tab" not in st.session_state:
            st.session_state.pipeline_active_tab = "📋 系統硬體與架構配置"
            
        tab_selection = st.radio(
            "選擇頁籤：",
            ["📋 系統硬體與架構配置", "💻 核心邏輯與 SCL 程式碼", "🖥️ HMI 人機介面佈局"],
            horizontal=True,
            label_visibility="collapsed",
            key="pipeline_active_tab"
        )
        st.divider()
        
        # --------- Tab 1: 架構成果 ---------
        if tab_selection == "📋 系統硬體與架構配置":
            if pipeline_res.get("arch"):
                st.markdown("### 🧠 首席架構師分析報告")
                st.info(pipeline_res["arch"].req_analysis.replace('. ', '。\n\n').replace('。 ', '。\n\n'))
                st.success(pipeline_res["arch"].hardware_selection.replace('. ', '。\n\n').replace('。 ', '。\n\n'))
                
                st.divider()
                st.markdown("#### ⚙️ I/O 點位配置清單")
                # 處理 JSON 把表格換行吃掉的極端狀況
                io_table = re.sub(r"\|\s*\|", "|\n|", pipeline_res["arch"].io_allocation)
                st.markdown(io_table)
            else:
                st.warning("架構分析遺失。")
                
        # --------- Tab 2: SCL 成果 ---------
        elif tab_selection == "💻 核心邏輯與 SCL 程式碼":
            if "scl" in pipeline_res:
                scl_data = pipeline_res["scl"]
                st.markdown("### 🎓 程式導師代碼解析")
                st.info(f"**🧠 邏輯思路解析：**\n{scl_data['res'].thinking}")
                st.success(f"**💡 新手註解與教學：**\n{scl_data['res'].tutorial}")
                
                st.divider()
                st.markdown("#### 💻 可匯入 TIA 的原始程式碼")
                st.code(scl_data['clean_scl'], language="pascal")
                
                # 下載按鈕排版
                dcol1, dcol2 = st.columns([1, 1])
                with dcol1:
                    st.download_button(
                        label="📥 下載 SCL 外部原始碼 (.scl)", 
                        data=scl_data['clean_scl'].encode('utf-8-sig'), 
                        file_name=f"Automated_Block_{target_version}.scl", 
                        mime="text/plain",
                        use_container_width=True,
                        key="dl_scl_btn"
                    )
                with dcol2:
                    try:
                        df = pd.read_csv(io.StringIO(scl_data['res'].csv_tags), dtype=str, skipinitialspace=True, on_bad_lines='skip')
                        if df.empty:
                            df = pd.DataFrame([{"Name": "ParserError", "Comment": "Could not parse AI output correctly."}])
                        else:
                            df = df.fillna("")
                        excel_buffer = io.BytesIO()
                        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer: 
                            df.to_excel(writer, index=False, sheet_name="PLC Tags")
                        
                        st.download_button(
                            label="📥 下載 TIA 變數表匯入檔 (.xlsx)", 
                            data=excel_buffer.getvalue(), 
                            file_name=f"PLC_Tags_{target_version}.xlsx", 
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True,
                            key="dl_tags_btn"
                        )
                    except Exception as e:
                        st.error(f"變數表封裝失敗: {e}")
                
                st.markdown("#### 📊 TIA 全域變數預覽")
                try:
                    st.dataframe(df, use_container_width=True, hide_index=True)
                except:
                    pass
            else:
                st.warning("程式碼生成失敗或遺失。")

        # --------- Tab 3: HMI 成果 ---------
        elif tab_selection == "🖥️ HMI 人機介面佈局":
            if "hmi" in pipeline_res:
                st.markdown("### 🎨 介面規劃師草圖")
                st.markdown("#### UI/UX 與變數對應表")
                st.info(pipeline_res["hmi"].tag_mapping)
                st.divider()
                st.markdown("#### 📐 ASCII 線框佈局圖 (Wireframe)")
                st.code(pipeline_res["hmi"].wireframe, language="text")
            else:
                st.info("本次生成無 HMI 結果。")
