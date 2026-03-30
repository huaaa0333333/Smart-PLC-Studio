# orchestrator_ui.py
import streamlit as st
import pandas as pd
import io
from workflows.orchestrator import run_automated_pipeline

def render(client, collection):
    st.title("🧩 多代理一鍵自動化流水線")
    st.markdown("真正的自動化：只需輸入一次需求，AI 代理人們將依次為您設計 **[硬體架構]** ➡️ **[自動化 SCL 程式碼]** ➡️ **[工業 HMI 佈局]**！")

    user_input = st.text_area(
        "請輸入您的控制需求：", 
        height=120, 
        placeholder="例如：老闆要我做一個帶有啟動停按鈕與馬達的簡單輸送帶系統，預算不多，越簡單越好。"
    )
    pdf_file = st.file_uploader("也可上傳 PDF 題目卷/規格書做為參考 (選填)", type=["pdf"])
    
    if st.button("🚀 啟動無縫資料流生產線", type="primary"):
        if not user_input.strip() and not pdf_file:
            st.warning("請至少輸入需求或上傳 PDF！")
            return
            
        pdf_bytes = pdf_file.getvalue() if pdf_file else None
        
        # 啟動自動化流水線
        pipeline_res = run_automated_pipeline(client, collection, user_input, pdf_bytes=pdf_bytes)
        
        if not pipeline_res:
             st.error("流水線在中途或開頭發生嚴重錯誤。")
             return
             
        # ====================
        # 一次性絕美展示所有成果
        # ====================
        st.success("🎉 全部生成完畢！請查看以下綜合報表：")
        
        # 1. 架構成果
        if "arch" in pipeline_res:
            st.markdown("### 1️⃣ 系統需求與硬體架構 (Architecture)")
            st.info(pipeline_res["arch"].req_analysis)
            st.success(pipeline_res["arch"].hardware_selection)
            st.markdown("#### I/O 點位配置表")
            st.markdown(pipeline_res["arch"].io_allocation)
            
        st.divider()
        
        # 2. SCL 成果
        if "scl" in pipeline_res:
            scl_data = pipeline_res["scl"]
            st.markdown("### 2️⃣ 智慧 SCL 程式碼與導師解說 (Code & Explanation)")
            st.info(f"**🧠 開發思路：**\n{scl_data['res'].thinking}")
            st.success(f"**🎓 導師教學：**\n{scl_data['res'].tutorial}")
            
            st.code(scl_data['clean_scl'], language="pascal")
            
            col1, col2 = st.columns([1, 2])
            with col1:
                st.download_button(
                    label="📥 下載 SCL 外部原始碼 (.scl)", 
                    data=scl_data['clean_scl'].encode('utf-8-sig'), 
                    file_name="Automated_Block.scl", 
                    mime="text/plain"
                )
            
            # 從 CSV 動態產生 Excel
            try:
                st.markdown("#### TIA Portal 全域變數表")
                df = pd.read_csv(io.StringIO(scl_data['res'].csv_tags))
                st.dataframe(df, use_container_width=True, hide_index=True)
                
                excel_buffer = io.BytesIO()
                with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer: 
                    df.to_excel(writer, index=False)
                    
                st.download_button(
                    label="📥 下載可匯入 TIA 的變數表 (.xlsx)", 
                    data=excel_buffer.getvalue(), 
                    file_name="Automated_Tags.xlsx", 
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            except Exception as e:
                st.error("變數表格式解析異常")
                
        st.divider()
        
        # 3. HMI 成果
        if "hmi" in pipeline_res:
            st.markdown("### 3️⃣ HMI 工業介面規劃 (HMI Design)")
            st.markdown("#### UI/UX 變數對應表")
            st.markdown(pipeline_res["hmi"].tag_mapping)
            st.markdown("#### ASCII 線框佈局圖 (Wireframe)")
            st.code(pipeline_res["hmi"].wireframe, language="text")
