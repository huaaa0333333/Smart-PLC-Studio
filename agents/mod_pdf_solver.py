import streamlit as st
import pandas as pd
import io
from core import utils
from google.genai import types
from core import prompts
from services.rag_service import query_knowledge
from services.llm_service import generate_structured_content

def solve_pdf(client, collection, pdf_bytes: bytes, user_supplement: str) -> tuple:
    """純邏輯：根據 PDF 內容與補充要求產出 SCL 程式碼 (回傳 res, clean_scl, raw_text)"""
    retrieved_docs = query_knowledge(collection, user_supplement, n_results=2) if user_supplement else "無補充知識"
    if not retrieved_docs:
        retrieved_docs = "無補充知識"
    
    knowledge_text, _ = utils.load_knowledge_base()
    prompt_text = prompts.get_pdf_solver_prompt(user_supplement, knowledge_text, retrieved_docs)
    
    pdf_part = types.Part.from_bytes(data=pdf_bytes, mime_type='application/pdf')
    system_instruction = "你是一個嚴謹的 PLC 程式碼生成器，嚴格遵守結構化輸出規範。如果資訊量太大，請專注於核心控制邏輯。"
    res, raw_text = generate_structured_content(
        client=client,
        model='gemini-2.5-flash',
        contents=[pdf_part, prompt_text],
        schema=utils.PLCCodeOutput,
        system_instruction=system_instruction,
        temperature=0.1
    )
    
    if res is None:
        return None, "", raw_text
        
    clean_scl = utils.clean_scl_string(res.scl_code)
    return res, clean_scl, raw_text

def render(client, collection):
    st.title("📄 PDF 考題破解器")
    st.markdown("將您的 PLC 考題、流程圖或硬體規格書 PDF 上傳，讓 AI 幫您看懂並直接轉化為標準 SCL 程式碼與變數表。")
    
    # UI 元件：PDF 上傳與補充說明
    uploaded_file = st.file_uploader("上傳 PDF 題目卷/規格書", type=['pdf'])
    user_supplement = st.text_input("補充說明 (選填)：", placeholder="例如：請特別注意 PDF 第三頁的馬達安全互鎖條件...")

    if st.button("🚀 破解並生成", type="primary"):
        if not uploaded_file:
            st.warning("請先上傳 PDF 檔案！")
            return
            
        with st.spinner("👀 正在閱讀 PDF 規格與流程圖，並撰寫對應邏輯中..."):
            try:
                pdf_bytes = uploaded_file.getvalue()
                res, clean_scl, raw_text = solve_pdf(client, collection, pdf_bytes, user_supplement)
                
                # 🌟 新增：防噎安全網
                if res is None:
                    st.error("⚠️ AI 腦容量過載！它看完題目了，但無法將結果塞進標準的 SCL 格式中。")
                    with st.expander("🕵️ 點此查看 AI 到底碎碎念了什麼 (原始輸出)"):
                        st.text(raw_text)
                    return
                
                st.session_state.history_pdf.insert(0, {
                    "filename": uploaded_file.name,
                    "supplement": user_supplement,
                    "code": clean_scl, 
                    "csv": res.csv_tags, 
                    "thinking": res.thinking, 
                    "tutorial": res.tutorial
                })
            except Exception as e:
                st.error(f"❌ 解析或生成失敗：{e}")

    # ==========================================
    # 歷史紀錄與雙重下載區 (維持與 Generator 一致的完美體驗)
    # ==========================================
    st.divider()
    st.markdown("### 🗂️ 破解與生成紀錄")
    
    if not st.session_state.history_pdf:
        st.info("尚無破解紀錄。請在上傳 PDF 後啟動生成！")
    else:
        for idx, record in enumerate(st.session_state.history_pdf):
            task_title = f"破解任務 #{len(st.session_state.history_pdf) - idx} | 檔案：{record['filename']}"
            with st.expander(task_title, expanded=(idx == 0)):
                if record['supplement']:
                    st.caption(f"補充說明：{record['supplement']}")
                    
                st.info(f"**🧠 考題破解思路：**\n{record['thinking']}")
                st.success(f"**🎓 導師教學：**\n{record['tutorial']}")
                
                st.markdown("#### 1️⃣ SCL 邏輯程式碼 (外部原始碼)")
                st.code(record['code'], language="pascal")
                
                col1, col2 = st.columns([1, 2])
                with col1:
                    st.download_button(
                        label="📥 下載 SCL 外部原始碼 (.scl)", 
                        data=record['code'].encode('utf-8-sig'), 
                        file_name=f"PDF_Solved_Block_{idx}.scl", 
                        mime="text/plain", 
                        key=f"pdf_scl_{idx}"
                    )
                with col2:
                    st.caption("💡 下載後請於 TIA Portal 使用 External source files 生成區塊。")
                
                st.divider()
                
                st.markdown("#### 2️⃣ TIA Portal 全域變數表")
                try:
                    df = pd.read_csv(io.StringIO(record['csv']), dtype=str, skipinitialspace=True)
                    df = df.fillna("")
                    st.dataframe(df, use_container_width=True, hide_index=True)
                    
                    excel_buffer = io.BytesIO()
                    with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer: 
                        df.to_excel(writer, index=False)
                    
                    st.download_button(
                        label="📥 下載可匯入 TIA 的變數表 (.xlsx)", 
                        data=excel_buffer.getvalue(), 
                        file_name=f"PDF_Tags_{idx}.xlsx", 
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 
                        key=f"pdf_csv_{idx}"
                    )
                except Exception as e:
                    st.error(f"變數表格式解析異常：{e}")
