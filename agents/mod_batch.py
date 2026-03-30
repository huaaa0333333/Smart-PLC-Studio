import streamlit as st
import pandas as pd
import io
from core import utils
from core import prompts
from services.llm_service import generate_structured_content

def generate_batch(client, topic: str, qty: int) -> pd.DataFrame:
    """純邏輯：根據主題與數量批量生成測試腳本/問答 (回傳 DataFrame)"""
    prompt = prompts.get_batch_prompt(topic, qty)
    res, _ = generate_structured_content(
        client=client,
        model='gemini-2.5-flash',
        contents=prompt,
        schema=utils.BatchEngineOutput,
        temperature=0.7
    )
    data = [{"問題/情境": item.question, "解答/邏輯": item.answer} for item in res.items]
    return pd.DataFrame(data)

def render(client):
    st.title("📦 批次題庫與腳本引擎")
    st.markdown("指定知識領域與數量，讓系統自動為您量產技術問答或測試腳本。")
    
    topic = st.text_input("請輸入欲生成的領域或手冊章節：", placeholder="例如：西門子 S7-1200 PID 控制原理，或是馬達控制常見面試題")
    qty = st.slider("生成數量", min_value=1, max_value=20, value=5)
    
    if st.button("🏭 啟動量產", type="primary"):
        if not topic.strip():
            st.warning("請輸入主題！")
            return
            
        with st.spinner(f"正在從大腦萃取知識，全力為您生成 {qty} 筆資料..."):
            try:
                # 呼叫純邏輯函式
                df = generate_batch(client, topic, qty)
                
                # 存入獨立的批次歷史紀錄
                st.session_state.history_batch.insert(0, {
                    "topic": topic, 
                    "qty": qty, 
                    "df": df
                })
            except Exception as e:
                st.error(f"❌ 生成失敗：{e}")

    # ==========================================
    # 歷史紀錄與 Excel 下載區
    # ==========================================
    st.divider()
    st.markdown("### 🗂️ 批次生成紀錄")
    if not st.session_state.history_batch:
        st.info("尚無批次紀錄。")
    else:
        for idx, record in enumerate(st.session_state.history_batch):
            with st.expander(f"批次任務 #{len(st.session_state.history_batch) - idx} | {record['topic']} ({record['qty']} 筆)", expanded=(idx == 0)):
                # 直接在網頁上顯示表格
                st.dataframe(record['df'], use_container_width=True)
                
                # 將 DataFrame 轉換為 Excel 檔案並提供下載
                excel_buffer = io.BytesIO()
                with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer: 
                    record['df'].to_excel(writer, index=False)
                
                st.download_button(
                    label="📥 匯出整包題庫 (Excel)", 
                    data=excel_buffer.getvalue(), 
                    file_name=f"Batch_QA_{idx}.xlsx", 
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 
                    key=f"batch_excel_{idx}"
                )