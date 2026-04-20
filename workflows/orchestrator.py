# orchestrator.py
"""Core orchestrator for Multi-Agent Automated Pipeline.

Supports both full-auto mode and step-by-step human-in-the-loop mode.

Step functions:
  - prepare_pipeline_input: Pre-process input (parse PDF, append tags)
  - run_step_architecture:  Step 1 — Hardware architecture design
  - run_step_scl:           Step 2 — SCL code generation
  - run_step_hmi:           Step 3 — HMI interface design
  - run_automated_pipeline: Full-auto mode (runs all steps without pausing)
"""
from agents import (
    mod_architecture_designer, mod_generator, mod_hmi_designer, 
    mod_pdf_solver, mod_code_reviewer, mod_safety_auditor
)
import streamlit as st

# ... (prepare_pipeline_input and run_step_panel_engineering remain unchanged)

# ==========================================
#  Step 2.5: 工安稽核員 (Safety Audit)
# ==========================================
def run_step_safety_audit(client, scl_code: str, csv_tags: str):
    """Step 2.5 — Safety Audit. Returns SafetyAuditOutput."""
    with st.status("🛡️ 正在進行工業安全性稽核 (Safety Audit)...", expanded=True) as status:
        st.write("🔍 檢測設備互鎖邏輯...")
        st.write("⚠️ 驗證急停與失效安全機制...")
        safety_res = mod_safety_auditor.audit_safety(client, scl_code, csv_tags)
        
        if safety_res.safety_score < 60:
            status.update(label=f"❌ 偵測到安全風險 (評分: {safety_res.safety_score})", state="error", expanded=True)
        else:
            status.update(label="✅ 安全稽核通過！", state="complete", expanded=False)
    return safety_res

# ==========================================
#  Step 2: SCL 程式碼生成 (含自動工安修復)
# ==========================================
def run_step_scl(client, collection, pipeline_input: str, arch_res,
                 target_version: str = "V17", feedback: str = ""):
    """Step 2 — SCL Code Generation. Returns (scl_res, clean_scl, review_result, safety_result)."""
    
    current_feedback = feedback
    max_retries = 2
    retry_count = 0
    
    while retry_count <= max_retries:
        formatted_input = (
            f"原始需求：{pipeline_input}\n"
            f"【必須嚴格遵守以下系統設計好的硬體 I/O 配置表】\n{arch_res.io_allocation}"
        )
        if current_feedback:
            formatted_input += f"\n\n【⚠️ 修正建議/意見 — 請務必遵守】：\n{current_feedback}"

        with st.status(f"📝 正在撰寫嚴謹的 SCL 程式碼 (嘗試 {retry_count + 1})...", expanded=True) as status:
            st.write(f"🧠 檢索 {target_version} 專屬手冊知識...")
            scl_res, clean_scl = mod_generator.generate_scl(
                client, collection, formatted_input,
                target_version=target_version, is_advanced=False
            )
            
            # 1. 基礎代碼審查
            review_result = mod_code_reviewer.review_generated_code(
                client, clean_scl,
                scl_res.csv_tags if hasattr(scl_res, 'csv_tags') else ""
            )
            
            # 2. 工安稽核 (新的步驟)
            safety_result = run_step_safety_audit(client, clean_scl, scl_res.csv_tags)
            
            # 如果安全分數過低且還有重試機會，則自動觸發重試
            if safety_result.safety_score < 60 and retry_count < max_retries:
                retry_count += 1
                st.warning(f"🛡️ 工安稽核未通過 (得分: {safety_result.safety_score})。正在根據建議自動修正並重新生成...")
                current_feedback = f"【工安稽核失敗，請針對以下風險進行修正】：\n{safety_result.recommendations}"
                status.update(label="🔄 偵測到安全隱患，正在重新生成...", state="running")
                continue
            
            status.update(label="✅ SCL 邏輯撰寫與安全稽核完成！", state="complete", expanded=False)
            if review_result.get("score", 0) < 70:
                st.warning(f"⚠️ 代碼品質審查得分較低 ({review_result['score']}): {review_result['feedback']}")
            
            return scl_res, clean_scl, review_result, safety_result


# ==========================================
#  Step 3: HMI 介面設計
# ==========================================
def run_step_hmi(client, pipeline_input: str, arch_res, feedback: str = ""):
    """Step 3 — HMI Design. Returns HMIOutput."""
    formatted_input = (
        f"原始需求：{pipeline_input}\n"
        f"【必須嚴格遵守以下系統設計好的硬體 I/O 配置表】\n{arch_res.io_allocation}"
    )
    if feedback:
        formatted_input += f"\n\n【⚠️ 人類工程師審核修改意見 — 請務必遵守】：\n{feedback}"

    with st.status("🖥️ 正在佈局 HMI 人機介面...", expanded=True) as status:
        st.write("🎨 導入工業防呆與色彩規範...")
        st.write("📐 測量並繪製 ASCII 線框圖...")
        hmi_res = mod_hmi_designer.generate_hmi(client, formatted_input)
        status.update(label="✅ HMI 人機介面規劃完成！", state="complete", expanded=False)
    return hmi_res


# ==========================================
#  全自動模式 (向下相容 + 一鍵完成)
# ==========================================
def run_automated_pipeline(client, collection, user_input: str,
                           pdf_bytes: bytes = None, tag_table_str: str = None,
                           target_version: str = "V17"):
    """Execute the end-to-end automated pipeline (full-auto, no human review)."""
    pipeline_state = {}

    # Step 0: Prepare input
    pipeline_input = prepare_pipeline_input(client, collection, user_input, pdf_bytes, tag_table_str)
    
    # Step 0.5: Panel Engineering
    try:
        panel_res = run_step_panel_engineering(client, pipeline_input)
        pipeline_state["panel"] = panel_res
    except Exception as e:
        st.error(f"❌ 控制箱工程規劃失敗，流水線中斷: {e}")
        return pipeline_state

    # Step 1: Architecture
    try:
        arch_res = run_step_architecture(client, pipeline_input)
        pipeline_state["arch"] = arch_res
    except Exception as e:
        st.error(f"❌ 架構規劃失敗，流水線中斷: {e}")
        return pipeline_state

    # Step 2: SCL
    try:
        scl_res, clean_scl, review_result, safety_result = run_step_scl(
            client, collection, pipeline_input, arch_res, target_version
        )
        pipeline_state["code_review"] = review_result
        pipeline_state["safety_audit"] = safety_result
        pipeline_state["scl"] = {"res": scl_res, "clean_scl": clean_scl}
    except Exception as e:
        st.error(f"❌ 程式碼生成失敗，流水線中斷: {e}")
        return pipeline_state

    # Step 3: HMI
    try:
        hmi_res = run_step_hmi(client, pipeline_input, arch_res)
        pipeline_state["hmi"] = hmi_res
    except Exception as e:
        st.warning(f"⚠️ HMI 規劃失敗 (非致命錯誤，將略過): {e}")

    return pipeline_state

# ==========================================
#  Step 5: 🧨 混沌壓力測試 (Chaos Test)
# ==========================================
def run_step_chaos_testing(client, scl_code: str, csv_tags: str):
    """Step 5 — Chaos Testing. Returns a list of log strings."""
    from agents import mod_chaos_tester
    from services.chaos_runner import ChaosEngine
    
    with st.status("🧨 正在策劃與執行混沌壓力測試 (Chaos Test)...", expanded=True) as status:
        st.write("🧠 解析弱點並生成攻擊劇本...")
        plan = mod_chaos_tester.generate_chaos_plan(client, scl_code, csv_tags)
        
        st.write("🔌 嘗試連接 PLCSIM Advanced 啟動實體攻擊...")
        engine = ChaosEngine(ip='192.168.0.1')
        report_logs = engine.run_chaos_test(plan, csv_tags)
        
        # Check if the report contains disaster alerts
        has_disaster = any("🚨" in log for log in report_logs)
        if has_disaster:
            status.update(label="❌ 壓力測試未通過：偵測到系統崩潰或損壞危險！", state="error", expanded=True)
        else:
            status.update(label="✅ 壓力測試通過！系統具備高強度的抗干擾能力。", state="complete", expanded=False)
            
    return plan, report_logs

# ==========================================
#  Step 6: 📘 系統技術維護手冊編纂 (Tech Writer)
# ==========================================
def run_step_tech_writer(client, pipeline_res: dict):
    """Step 6 — Technical Writer. Returns TechManualOutput."""
    from agents import mod_tech_writer
    
    with st.status("📘 技術寫手正在聚合資料編纂手冊...", expanded=True) as status:
        st.write("🔍 收集 BOM、I/O 表與 SCL 原始碼...")
        
        # 聚合資料
        bom_data = "無 BOM 資訊"
        if "panel" in pipeline_res:
            bom_data = pipeline_res["panel"].bom_items
        elif "arch" in pipeline_res:
            bom_data = pipeline_res["arch"].hardware_selection
            
        io_tags = "無 I/O 變數"
        scl_code = "無程式碼"
        if "scl" in pipeline_res:
            io_tags = pipeline_res["scl"]["res"].csv_tags if hasattr(pipeline_res["scl"]["res"], 'csv_tags') else pipeline_res["scl"]["res"].get("csv_tags", "None")
            scl_code = pipeline_res["scl"]["clean_scl"]
            
        safety_chaos_log = "無安全性日誌"
        if "chaos" in pipeline_res:
            safety_chaos_log = "\n".join(pipeline_res["chaos"]["logs"])
        if "safety_audit" in pipeline_res:
            safety_chaos_log += "\n【工安建議】\n" + pipeline_res["safety_audit"].recommendations

        st.write("✍️ 進行邏輯翻譯與繪製流程圖...")
        manual_res = mod_tech_writer.generate_tech_manual(
            client, bom_data, io_tags, scl_code, safety_chaos_log
        )
        status.update(label="✅ ISO/IEC 系統技術維護手冊編纂完成！", state="complete", expanded=False)
        
    return manual_res
