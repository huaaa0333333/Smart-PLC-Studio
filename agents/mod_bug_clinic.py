import streamlit as st
from core import utils
from core import prompts
from services.llm_service import generate_structured_content

def generate_bug_fix(client, bug_input: str) -> tuple:
    """純邏輯：根據錯誤資訊生成修復後的程式碼與診斷說明"""
    prompt = prompts.get_bug_clinic_prompt()
    res, _ = generate_structured_content(
        client=client,
        model='gemini-2.5-flash',
        contents=bug_input,
        schema=utils.BugClinicOutput,
        system_instruction=prompt,
        temperature=0.1
    )
    clean_scl = utils.clean_scl_string(res.fixed_scl_code)
    return res, clean_scl

def render(client):
    st.title("🛠️ Bug 診療室")
    st.markdown("貼上 TIA Portal 的報錯訊息 (Error Log) 或有問題的 SCL 程式碼，讓 AI 幫你抓蟲！")
    
    bug_input = st.text_area("請貼上錯誤程式碼或報錯訊息：", height=200, placeholder="例如：我的跑馬燈不會動，或是 TIA 報錯說找不到 # 號...")
    
    if st.button("🩺 開始診斷", type="primary"):
        if not bug_input.strip():
            st.warning("請輸入錯誤資訊！")
            return
        
        with st.spinner("掃描語法漏洞中..."):
            try:
                # 呼叫純邏輯函式
                res, clean_scl = generate_bug_fix(client, bug_input)
                
                # 存入獨立的 Bug 歷史紀錄
                st.session_state.history_bug.insert(0, {
                    "diagnosis": res.diagnosis, 
                    "code": clean_scl
                })
            except Exception as e:
                st.error(f"❌ 診斷失敗：{e}")

    # ==========================================
    # 歷史紀錄與下載區
    # ==========================================
    st.divider()
    st.markdown("### 🗂️ 診斷與修復紀錄")
    if not st.session_state.history_bug:
        st.info("尚無診斷紀錄。")
    else:
        for idx, record in enumerate(st.session_state.history_bug):
            with st.expander(f"診斷報告 #{len(st.session_state.history_bug) - idx}", expanded=(idx == 0)):
                st.error(f"**🩺 診斷結果：**\n{record['diagnosis']}")
                st.code(record['code'], language="pascal")
                st.download_button(
                    label="📥 下載修復後的 SCL (.scl)", 
                    data=record['code'].encode('utf-8-sig'), 
                    file_name=f"Fixed_Block_{idx}.scl", 
                    mime="text/plain", 
                    key=f"bug_scl_{idx}"
                )