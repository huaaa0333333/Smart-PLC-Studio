import streamlit as st
import pandas as pd
import io
import re
from core import utils
from core import prompts
from services.rag_service import query_knowledge
from services.llm_service import generate_markdown_stream

class SclParseResult:
    def __init__(self, thinking, tutorial, scl_code, csv_tags):
        self.thinking = thinking
        self.tutorial = tutorial
        self.scl_code = scl_code
        self.csv_tags = csv_tags

def parse_scl_markdown(text: str) -> SclParseResult:
    thinking = ""
    tutorial = ""
    scl_code = ""
    csv_tags = ""

    # 使用正則表達式根據 "### " 來切分段落
    sections = re.split(r'\n(?=### )', '\n' + text)

    for sec in sections:
        sec = sec.strip()
        if not sec:
            continue
            
        lines = sec.split('\n', 1)
        header = lines[0]
        content = lines[1].strip() if len(lines) > 1 else ""
        
        if "思路" in header:
            thinking = content
        elif "教學" in header or "導師" in header:
            tutorial = content
        elif "SCL" in header or "程式碼" in header:
            scl_code = content
            # 濾掉 Markdown code block 標記
            m = re.search(r'```.*?\n(.*?)\n```', content, re.DOTALL)
            if m: 
                scl_code = m.group(1).strip()
        elif "CSV" in header or "變數" in header:
            csv_tags = content
            m = re.search(r'```.*?\n(.*?)\n```', content, re.DOTALL)
            if m: 
                csv_tags = m.group(1).strip()

    # 極端防呆：如果 SCL 為空，從整個文字裡硬抓非 CSV 的 Code block
    if not scl_code:
        blocks = re.findall(r'```[a-zA-Z-]*\n(.*?)\n```', text, re.DOTALL)
        for b in blocks:
            if "Name,Path,Data Type" not in b:
                scl_code = b.strip()
                break
                
    if not csv_tags:
        blocks = re.findall(r'```[a-zA-Z-]*\n(.*?)\n```', text, re.DOTALL)
        for b in blocks:
            if "Name,Path,Data Type" in b:
                csv_tags = b.strip()
                break

    return SclParseResult(thinking, tutorial, scl_code, csv_tags)

def generate_scl(client, collection, user_input: str, target_version: str = "V17", is_advanced: bool = False, stream: bool = False):
    """純邏輯：根據使用者需求與版本從 RAG 提取知識並生成 SCL 程式碼"""
    retrieved_docs = query_knowledge(collection, user_input, n_results=3, where_filter={"version": target_version})
    if not retrieved_docs:
        retrieved_docs = f"查無 {target_version} 相關的向量文獻"
    
    knowledge_text, _ = utils.load_knowledge_base()
    prompt = prompts.get_generator_prompt(target_version, is_advanced, user_input, knowledge_text, retrieved_docs)
    
    system_instruction = f"你是西門子 TIA Portal {target_version} 的高級專家，請嚴格遵守 Markdown 格式輸出。"
    generator = generate_markdown_stream(
        client=client,
        model='gemini-1.5-pro',
        contents=prompt,
        system_instruction=system_instruction,
        temperature=0.1
    )
    
    if stream:
        return generator
    else:
        full_text = "".join([chunk for chunk in generator])
        res = parse_scl_markdown(full_text)
        clean_scl = utils.clean_scl_string(res.scl_code)
        return res, clean_scl

def render(client, collection, is_advanced=False):
    # 根據是否為進階模式，動態切換標題與提示字眼
    title = "⚙️ 進階工藝控制 (PID/Motion)" if is_advanced else "📝 SCL 智能生成與教學"
    st.title(title)
    
    # 🌟 新增：多版本切換選擇器
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
            
        with st.spinner(f"大腦正在檢索 {target_version} 專屬知識庫，撰寫 SCL 中..."):
            try:
                st.markdown("---")
                generator = generate_scl(client, collection, user_input, target_version, is_advanced, stream=True)
                
                # Streamlit 無縫渲染串流效果！
                full_text = st.write_stream(generator)
                
                # 解析 Markdown 字串以抽取出下載所需組件
                res = parse_scl_markdown(full_text)
                clean_scl = utils.clean_scl_string(res.scl_code)
                
                # 存入歷史紀錄 (🌟 紀錄中多存一個 version)
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
    
    if not st.session_state.history_gen:
        st.info("尚無生成紀錄。請在上方輸入需求開始生成！")
    else:
        for idx, record in enumerate(st.session_state.history_gen):
            # 🌟 歷史標題會顯示是哪個版本產出的
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
                    df = pd.read_csv(io.StringIO(record['csv']))
                    st.dataframe(df, use_container_width=True, hide_index=True)
                    
                    excel_buffer = io.BytesIO()
                    with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer: 
                        df.to_excel(writer, index=False)
                    
                    st.download_button(
                        label="📥 下載可匯入 TIA 的變數表 (.xlsx)", 
                        data=excel_buffer.getvalue(), 
                        file_name=f"Tags_{ver_tag}_{idx}.xlsx", 
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 
                        key=f"csv_{idx}_{is_advanced}"
                    )
                except Exception as e:
                    st.error(f"變數表格式解析異常：{e}")
