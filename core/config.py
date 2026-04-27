"""
core/config.py

Smart PLC Studio 集中設定載入器。

優先順序（由高到低）：
  1. 環境變數 / .env 檔案（用於 API 金鑰等敏感資料）
  2. config.toml（使用者可編輯的行為設定）
  3. 內建預設值（最終備援）

對外公開的全域常數：
  DEFAULT_MODEL          — 預設 AI 模型 ID
  AGENT_MODEL(name)      — 取得特定代理人的模型 ID
  TIA_VERSION            — 自動或手動偵測到的 TIA 版本標籤 (例如 'V17')
  TIA_OPENNESS_DLL       — Siemens.Engineering.dll 完整路徑（空字串代表未找到）
  TIA_INSTALL_PATH       — TIA Portal 安裝目錄
  SAFETY_SCORE_THRESHOLD — 安全稽核閾值
  CODE_REVIEW_THRESHOLD  — 代碼審查警告閾值
  MAX_SCL_RETRIES        — SCL 最大自動重試次數
"""

import os
import sys
import logging

logger = logging.getLogger(__name__)

# ============================================================
#  Step 1：載入 .env（敏感金鑰）
# ============================================================
try:
    from dotenv import load_dotenv
    load_dotenv(override=False)   # 不覆寫已存在的環境變數
except ImportError:
    pass


# ============================================================
#  Step 2：載入 config.toml
# ============================================================
def _load_toml() -> dict:
    """讀取專案根目錄的 config.toml，若不存在則回傳空字典。"""
    # 找到專案根目錄（此檔案的上層目錄）
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    toml_path = os.path.join(root, "config.toml")

    if not os.path.exists(toml_path):
        logger.info("[Config] 找不到 config.toml，使用內建預設值。")
        return {}

    # Python 3.11+ 內建 tomllib；舊版嘗試 tomli 套件
    try:
        if sys.version_info >= (3, 11):
            import tomllib
            with open(toml_path, "rb") as f:
                return tomllib.load(f)
        else:
            import tomli  # pip install tomli
            with open(toml_path, "rb") as f:
                return tomli.load(f)
    except ImportError:
        logger.warning("[Config] 找不到 tomllib/tomli，無法解析 config.toml。請升級至 Python 3.11+，或執行 pip install tomli。")
        return {}
    except Exception as e:
        logger.error(f"[Config] 解析 config.toml 時發生錯誤: {e}")
        return {}


_cfg = _load_toml()


# ============================================================
#  Step 3：AI 模型設定
# ============================================================
_DEFAULT_MODEL_FALLBACK = "gemini-2.5-flash"

DEFAULT_MODEL: str = (
    _cfg.get("ai", {}).get("default_model")
    or os.getenv("DEFAULT_MODEL")
    or _DEFAULT_MODEL_FALLBACK
)

_AGENT_MODEL_OVERRIDES: dict = _cfg.get("ai", {}).get("agent_models", {})


def AGENT_MODEL(agent_name: str) -> str:
    """
    取得特定代理人的模型 ID。
    若 config.toml [ai.agent_models] 中有覆寫設定則使用之，
    否則回退到 DEFAULT_MODEL。
    """
    return _AGENT_MODEL_OVERRIDES.get(agent_name, DEFAULT_MODEL) or DEFAULT_MODEL


# ============================================================
#  Step 4：TIA Portal 自動偵測
# ============================================================
_tia_cfg = _cfg.get("tia", {})
_auto_detect: bool = _tia_cfg.get("auto_detect", True)
_default_version: str = _tia_cfg.get("default_version", "V17")
_dll_override: str = _tia_cfg.get("openness_dll_override", "")
_exe_override: str = _tia_cfg.get("tia_exe_override", "")

# 初始化為預設值
TIA_VERSION: str = _default_version
TIA_OPENNESS_DLL: str = _dll_override
TIA_INSTALL_PATH: str = ""
TIA_ALL_VERSIONS: list = []        # 所有偵測到的版本清單

if _auto_detect and sys.platform == "win32":
    try:
        from core.tia_detector import scan_installed_versions, get_latest_version
        _detected = scan_installed_versions()
        TIA_ALL_VERSIONS = [v.version_label for v in _detected]

        if _detected:
            _latest = _detected[0]   # 已排序，第一個為最新版
            TIA_VERSION = _latest.version_label
            TIA_INSTALL_PATH = _latest.install_path

            # DLL 路徑：優先使用 config.toml 的覆寫值
            if not TIA_OPENNESS_DLL:
                TIA_OPENNESS_DLL = _latest.openness_dll_path

            logger.info(
                f"[Config] TIA Portal 自動偵測完成：{TIA_VERSION} "
                f"(安裝路徑: {TIA_INSTALL_PATH})"
            )
            if TIA_OPENNESS_DLL:
                logger.info(f"[Config] Openness DLL: {TIA_OPENNESS_DLL}")
            else:
                logger.warning("[Config] 未偵測到 Siemens.Engineering.dll，TIA Openness 功能可能無法使用。")
        else:
            logger.warning(f"[Config] 未偵測到任何 TIA Portal 安裝，使用備援版本: {TIA_VERSION}")

    except Exception as e:
        logger.warning(f"[Config] TIA Portal 自動偵測失敗，使用備援版本: {e}")

elif not _auto_detect:
    logger.info(f"[Config] TIA Portal 自動偵測已停用，使用手動版本: {TIA_VERSION}")

# 若有手動指定 DLL，覆蓋偵測結果
if _dll_override:
    TIA_OPENNESS_DLL = _dll_override

if _exe_override:
    TIA_EXE_PATH = _exe_override
else:
    TIA_EXE_PATH = os.path.join(TIA_INSTALL_PATH, "bin", "TIA.exe") if TIA_INSTALL_PATH else ""


# ============================================================
#  Step 5：生產線行為設定
# ============================================================
_pipeline_cfg = _cfg.get("pipeline", {})

SAFETY_SCORE_THRESHOLD: int = int(_pipeline_cfg.get("safety_score_threshold", 60))
CODE_REVIEW_THRESHOLD: int = int(_pipeline_cfg.get("code_review_threshold", 70))
MAX_SCL_RETRIES: int = int(_pipeline_cfg.get("max_scl_retries", 2))


# ============================================================
#  Step 6：UI 設定
# ============================================================
_ui_cfg = _cfg.get("ui", {})

DEFAULT_PROJECT_PATH: str = _ui_cfg.get("default_project_path", "")
DEFAULT_PLC_NAME: str = _ui_cfg.get("default_plc_name", "PLC_1")


# ============================================================
#  診斷輸出（在 DEBUG 等級可見）
# ============================================================
logger.debug(
    f"[Config] 載入完成 | 模型: {DEFAULT_MODEL} | "
    f"TIA: {TIA_VERSION} | "
    f"安全閾值: {SAFETY_SCORE_THRESHOLD} | "
    f"代碼審查閾值: {CODE_REVIEW_THRESHOLD}"
)
