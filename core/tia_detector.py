# core/tia_detector.py
"""
TIA Portal 自動偵測模組 (TIA Auto-Detector)

功能：
  1. 掃描 Windows 登錄檔 (Registry) 找出已安裝的 TIA Portal 版本
     (支援 V15 ~ V20)
  2. 回傳所有已安裝版本的清單，並自動選出最新版
  3. 解析對應版本的 Siemens.Engineering.dll 路徑，供 TIA Openness 使用
  4. 全平台安全：在 Linux/Mac 環境（如 Docker）中跳過掃描並回傳空清單

Registry 掃描路徑（兩種可能，視安裝類型而異）：
  HKEY_LOCAL_MACHINE\\SOFTWARE\\Siemens\\Automation\\Totally Integrated Automation Portal\\<版本>
  HKEY_LOCAL_MACHINE\\SOFTWARE\\WOW6432Node\\Siemens\\Automation\\...
"""

import sys
import os
import logging
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)

# ==========================================
#  TIA Portal 版本對照表
#  Key: 登錄檔中的版本號字串 (VersionString)
#  Value: 使用者友善的版本標籤
# ==========================================
_VERSION_LABEL_MAP = {
    "15.0": "V15",
    "15.1": "V15.1",
    "16.0": "V16",
    "17.0": "V17",
    "18.0": "V18",
    "19.0": "V19",
    "20.0": "V20",
}

# 各版本的 Openness DLL 相對路徑（相對於 TIA Portal 安裝目錄）
_OPENNESS_DLL_RELATIVE_PATHS = [
    r"PublicAPI\{ver}\Siemens.Engineering.dll",
    r"bin\Siemens.Engineering.dll",
]

# 登錄檔根路徑（同時掃描 64-bit 與 32-bit 路徑）
_REGISTRY_BASE_PATHS = [
    r"SOFTWARE\Siemens\Automation\Totally Integrated Automation Portal",
    r"SOFTWARE\WOW6432Node\Siemens\Automation\Totally Integrated Automation Portal",
]


# ==========================================
#  資料類別
# ==========================================
@dataclass
class TIAInstallInfo:
    """代表一個已安裝的 TIA Portal 版本。"""
    version_label: str          # 例：'V17'
    version_number: float       # 例：17.0
    install_path: str           # 安裝根目錄
    openness_dll_path: str = "" # Siemens.Engineering.dll 完整路徑（空字串代表找不到）

    @property
    def has_openness(self) -> bool:
        return bool(self.openness_dll_path) and os.path.exists(self.openness_dll_path)

    def __str__(self) -> str:
        status = "✅ Openness 就緒" if self.has_openness else "⚠️ 未偵測到 Openness DLL"
        return f"{self.version_label} — {self.install_path} [{status}]"


# ==========================================
#  核心掃描邏輯
# ==========================================
def _resolve_openness_dll(install_path: str, ver_label: str) -> str:
    """
    嘗試在安裝路徑下找到 Siemens.Engineering.dll。
    回傳完整路徑，找不到則回傳空字串。
    """
    for rel_template in _OPENNESS_DLL_RELATIVE_PATHS:
        rel = rel_template.replace("{ver}", ver_label)
        full_path = os.path.join(install_path, rel)
        if os.path.exists(full_path):
            return full_path
    return ""


def scan_installed_versions() -> list[TIAInstallInfo]:
    """
    掃描 Windows 登錄檔，回傳所有已安裝的 TIA Portal 版本清單。
    在非 Windows 平台（例如 Linux Docker）會安全地回傳空清單。
    """
    if sys.platform != "win32":
        logger.info("[TIADetector] 非 Windows 平台，跳過 Registry 掃描。")
        return []

    try:
        import winreg
    except ImportError:
        logger.warning("[TIADetector] winreg 模組不可用。")
        return []

    found: list[TIAInstallInfo] = []

    for base_path in _REGISTRY_BASE_PATHS:
        try:
            root_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, base_path)
        except FileNotFoundError:
            continue  # 此路徑不存在，跳過

        try:
            idx = 0
            while True:
                try:
                    subkey_name = winreg.EnumKey(root_key, idx)
                    idx += 1
                except OSError:
                    break  # 枚舉結束

                try:
                    subkey = winreg.OpenKey(root_key, subkey_name)
                    # 讀取安裝目錄值（常見鍵名：InstallDir / InstallationDirectory）
                    install_path = None
                    for val_name in ("InstallDir", "InstallationDirectory", "Path"):
                        try:
                            install_path, _ = winreg.QueryValueEx(subkey, val_name)
                            break
                        except FileNotFoundError:
                            continue

                    if not install_path or not os.path.isdir(install_path):
                        winreg.CloseKey(subkey)
                        continue

                    # 判斷版本號
                    ver_number = None
                    ver_label = None
                    for raw_ver, label in _VERSION_LABEL_MAP.items():
                        if raw_ver in subkey_name or label.lower() in subkey_name.lower():
                            ver_number = float(raw_ver)
                            ver_label = label
                            break

                    if ver_number is None:
                        # 嘗試從 subkey_name 直接解析數字
                        try:
                            ver_number = float(subkey_name)
                            ver_label = f"V{int(ver_number)}"
                        except ValueError:
                            winreg.CloseKey(subkey)
                            continue

                    winreg.CloseKey(subkey)

                    dll_path = _resolve_openness_dll(install_path, ver_label)
                    info = TIAInstallInfo(
                        version_label=ver_label,
                        version_number=ver_number,
                        install_path=install_path,
                        openness_dll_path=dll_path,
                    )
                    # 避免重複（同版本可能在兩個 Registry 路徑都出現）
                    if not any(x.version_label == ver_label for x in found):
                        found.append(info)
                        logger.info(f"[TIADetector] 偵測到 {info}")

                except Exception as e:
                    logger.debug(f"[TIADetector] 讀取子鍵 {subkey_name} 時發生例外: {e}")

        finally:
            winreg.CloseKey(root_key)

    # 依版本號由新到舊排序
    found.sort(key=lambda x: x.version_number, reverse=True)
    return found


def get_latest_version() -> Optional[TIAInstallInfo]:
    """
    回傳最新已安裝的 TIA Portal 版本。
    未找到任何版本時回傳 None。
    """
    versions = scan_installed_versions()
    return versions[0] if versions else None


def get_version_label_list() -> list[str]:
    """
    回傳已安裝版本的標籤清單，例如 ['V19', 'V18', 'V17']。
    若未安裝則回傳 ['V17']（預設備援值）。
    """
    labels = [v.version_label for v in scan_installed_versions()]
    return labels if labels else ["V17"]
