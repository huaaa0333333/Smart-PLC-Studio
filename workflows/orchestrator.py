# orchestrator.py
"""Core orchestrator for Multi‑Agent Automated Pipeline.
It takes a single user input (and optional PDF) and chains the execution of:
1. Architecture Designer
2. SCL Generator
3. HMI Designer
No Streamlit UI logic is blocking the background execution.
"""
from agents import mod_architecture_designer, mod_generator, mod_hmi_designer, mod_pdf_solver
import streamlit as st

def run_automated_pipeline(client, collection, user_input: str, pdf_bytes: bytes = None, target_version: str = "V17"):
    """Execute the end-to-end automated pipeline."""
    pipeline_state = {}
    
    # Optional Step 0: PDF Parsing
    pipeline_input = user_input
    if pdf_bytes:
        try:
            with st.status("📄 正在解析 PDF 規格...", expanded=True) as status:
                st.write("👀 讀取圖表與文字...")
                pdf_res, _, _ = mod_pdf_solver.solve_pdf(client, collection, pdf_bytes, user_input)
                if pdf_res:
                    pipeline_input += f"\n【PDF 擷取要求】：\n{pdf_res.thinking}"
                status.update(label="✅ PDF 解析完成！", state="complete", expanded=False)
        except Exception as e:
            st.warning(f"PDF 解析出現異常，將退回僅使用文字需求: {e}")

    # Step 1: Architecture Design
    try:
        with st.status("🧠 (1/3) 正在設計硬體架構與 I/O 配置...", expanded=True) as status:
            st.write("🔍 分析需求與安全機制...")
            st.write("⚙️ 評估 PLC 型號與節點...")
            arch_res = mod_architecture_designer.generate_architecture(client, pipeline_input)
            pipeline_state["arch"] = arch_res
            status.update(label="✅ 架構規劃完成！", state="complete", expanded=False)
    except Exception as e:
        st.error(f"❌ 架構規劃失敗，流水線中斷: {e}")
        return pipeline_state

    # Step 2: SCL Generation
    try:
        with st.status("📝 (2/3) 正在撰寫嚴謹的 SCL 程式碼...", expanded=True) as status:
            st.write(f"🧠 檢索 {target_version} 專屬手冊知識...")
            st.write("✍️ 依循硬體 I/O 表產生變數對應與控制邏輯...")
            
            # 結合 Step 1 產生的 I/O 表作為背景限制
            formatted_input = f"原始需求：{pipeline_input}\n【必須嚴格遵守以下系統設計好的硬體 I/O 配置表】\n{arch_res.io_allocation}"
            
            scl_res, clean_scl = mod_generator.generate_scl(client, collection, formatted_input, target_version=target_version, is_advanced=False)
            pipeline_state["scl"] = {"res": scl_res, "clean_scl": clean_scl}
            status.update(label="✅ SCL 邏輯撰寫完成！", state="complete", expanded=False)
    except Exception as e:
        st.error(f"❌ 程式碼生成失敗，流水線中斷: {e}")
        return pipeline_state

    # Step 3: HMI Design
    try:
        with st.status("🖥️ (3/3) 正在佈局 HMI 人機介面...", expanded=True) as status:
            st.write("🎨 導入工業防呆與色彩規範...")
            st.write("📐 測量並繪製 ASCII 線框圖...")
            
            hmi_res = mod_hmi_designer.generate_hmi(client, formatted_input)
            pipeline_state["hmi"] = hmi_res
            status.update(label="✅ HMI 人機介面規劃完成！", state="complete", expanded=False)
    except Exception as e:
        st.warning(f"⚠️ HMI 規劃失敗 (非致命錯誤，將略過): {e}")

    return pipeline_state
