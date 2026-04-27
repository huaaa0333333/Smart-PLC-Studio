import streamlit as st
import pandas as pd
import io
import re
from pydantic import BaseModel, Field
from core import utils
from core import prompts
from core.config import DEFAULT_MODEL
from services.rag_service import query_knowledge
from services.llm_service import generate_structured_content

class SclParseResult(BaseModel):
    thinking: str = Field(description="開發思路：闡述您的設計邏輯思路與變數分析")
    tutorial: str = Field(description="導師教學：提供逐行新手教學與註解說明")
    scl_code: str = Field(description="純西門子 SCL 程式碼：嚴格遵守 IO 隔離與語法，不加任何 Markdown 或註解以外的多餘文字")
    csv_tags: str = Field(description="""CSV 變數表內容字串。請務必包含首列標題:
Name,Path,Data Type,Logical Address,Comment,Hmi Visible,Hmi Accessible,Hmi Writeable,Typeobject ID,Version ID
接下來逐行填寫實際變數。""")

def generate_scl(client, collection, user_input: str, target_version: str = "V17", is_advanced: bool = False):
    """純邏輯：根據使用者需求與版本從 RAG 提取知識並強制生成結構化 JSON 內的 SCL 程式碼"""
    retrieved_docs = query_knowledge(collection, user_input, n_results=3, where_filter={"version": target_version})
    if not retrieved_docs:
        retrieved_docs = f"查無 {target_version} 相關的向量文獻"
    
    knowledge_text, _ = utils.load_knowledge_base()
    prompt = prompts.get_generator_prompt(target_version, is_advanced, user_input, knowledge_text, retrieved_docs)
    
    system_instruction = f"你是西門子 TIA Portal {target_version} 的高級專家，請務必按照規定的結構化輸出。"
    res, raw_text = generate_structured_content(
        client=client,
        model=DEFAULT_MODEL,
        contents=prompt,
        schema=SclParseResult,
        system_instruction=system_instruction,
        temperature=0.1
    )
    
    if not res:
        raise ValueError(f"SCL 生成失敗，無法解析為標準 JSON 輸出格式！原始模型輸出:\n{raw_text}")
        
    clean_scl = utils.clean_scl_string(res.scl_code)
    return res, clean_scl

def render(client, collection, is_advanced=False):
    # 根據是否為進階模式，動態切換標題與提示字眼
    title = "⚙️ 進階工藝控制 (PID/Motion)" if is_advanced else "📝 SCL 智能生成與教學"
    st.title(title)
    
    target_version = st.selectbox(
        "請選擇目標 TIA Portal 版本：", 
        ["V17", "V18", "V19"], 
        index=0
    )
    st.caption(f"💡 目前 AI 與 RAG 檢索將嚴格鎖定於 **{target_version}** 的語法與原廠手冊。")
    
    placeholder = "例如：請幫我寫一個包含 PID_Compact 的溫度控制功能塊..." if is_advanced else "例如：請寫一個馬達啟動邏輯，並包含新手教學註解。"
    user_input = st.text_area("請描述您的控制需求：", height=120, placeholder=placeholder)

    if st.button("🚀 執行生成", type="primary"):
        if not user_input.strip():
            st.warning("請先輸入您的控制需求！")
            return
            
        with st.spinner(f"大腦正在檢索 {target_version} 專屬知識庫，強制結構化生成功率極高，請稍候 (約 5~15 秒)..."):
            try:
                st.markdown("---")
                # 結構化輸出不再串流，改為一次等待完畢
                res, clean_scl = generate_scl(client, collection, user_input, target_version, is_advanced)
                
                # 手動渲染結果到畫面上
                st.info(f"**🧠 開發思路解析：**\n{res.thinking}")
                st.success(f"**💡 新手註解與教學：**\n{res.tutorial}")
                st.code(clean_scl, language="pascal")
                
                # 存入歷史紀錄
                st.session_state.history_gen.insert(0, {
                    "version": target_version,
                    "prompt": user_input, 
                    "code": clean_scl, 
                    "csv": res.csv_tags, 
                    "thinking": res.thinking, 
                    "tutorial": res.tutorial
                })
            except Exception as e:
                st.error(f"❌ 生成失敗：{e}")

    # ==========================================
    # 歷史紀錄與雙重下載區
    # ==========================================
    st.divider()
    st.markdown("### 🗂️ 歷史生成紀錄")
    
    if "history_gen" not in st.session_state:
        st.session_state.history_gen = []
        
    if not st.session_state.history_gen:
        st.info("尚無生成紀錄。請在上方輸入需求開始生成！")
    else:
        for idx, record in enumerate(st.session_state.history_gen):
            ver_tag = record.get('version', '通用版')
            task_title = f"任務 #{len(st.session_state.history_gen) - idx} [{ver_tag}] | {record['prompt'][:25]}..."
            
            with st.expander(task_title, expanded=(idx == 0)):
                st.info(f"**🧠 開發思路：**\n{record['thinking']}")
                st.success(f"**🎓 導師教學：**\n{record['tutorial']}")
                
                st.markdown("#### 1️⃣ SCL 邏輯程式碼 (外部原始碼)")
                st.code(record['code'], language="pascal")
                
                col1, col2 = st.columns([1, 2])
                with col1:
                    st.download_button(
                        label=f"📥 下載 {ver_tag} SCL 原始碼 (.scl)", 
                        data=record['code'].encode('utf-8-sig'), 
                        file_name=f"GenBlock_{ver_tag}_{idx}.scl", 
                        mime="text/plain", 
                        key=f"scl_{idx}_{is_advanced}"
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
                        df.to_excel(writer, index=False, sheet_name="PLC Tags")
                    
                    st.download_button(
                        label="📥 下載可匯入 TIA 的變數表 (.xlsx)", 
                        data=excel_buffer.getvalue(), 
                        file_name=f"PLC_Tags_{ver_tag}_{idx}.xlsx", 
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 
                        key=f"csv_{idx}_{is_advanced}"
                    )
                except Exception as e:
                    st.warning(f"變數表格式解析異常。模型輸出：\n{record['csv']}")