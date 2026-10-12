"""数据目录与模型路径解析。

- --data-dir 参数可覆盖数据目录（用于同机多实例测试）
- 打包后数据写到 exe 同级 data/，保证 onefile 模式下数据可持久化
- 模型路径优先取打包内置（_MEIPASS），其次项目 assets/，最后默认下载目录
"""
import os
import sys

# 由 setup() 初始化
DATA_DIR = None


def project_root() -> str:
    """项目根目录（storage 包的上一级）。打包态此值无意义，仅开发态使用。"""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def setup(data_dir_override=None) -> None:
    """初始化数据目录并创建子目录。"""
    global DATA_DIR
    if data_dir_override:
        DATA_DIR = os.path.abspath(data_dir_override)
    elif getattr(sys, "frozen", False):
        DATA_DIR = os.path.join(os.path.dirname(sys.executable), "data")
    else:
        DATA_DIR = os.path.join(project_root(), "data")
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(snapshots_dir(), exist_ok=True)
    os.makedirs(leader_photos_dir(), exist_ok=True)


def db_path() -> str:
    return os.path.join(DATA_DIR, "leader_alert.db")


def snapshots_dir() -> str:
    return os.path.join(DATA_DIR, "snapshots")


def leader_photos_dir() -> str:
    return os.path.join(DATA_DIR, "leader_photos")


def model_root() -> str:
    """返回 insightface 的 root 目录：其下 models/buffalo_s/ 应包含模型文件。"""
    # 1. 打包内置（PyInstaller --add-data "assets/models;models"）
    if getattr(sys, "frozen", False):
        base = getattr(sys, "_MEIPASS", None)
        if base and os.path.isdir(os.path.join(base, "models", "buffalo_s")):
            return base
    # 2. 开发态项目 assets/（build.bat 会把模型拷贝到此处）
    dev_assets = os.path.join(project_root(), "assets")
    if os.path.isdir(os.path.join(dev_assets, "models", "buffalo_s")):
        return dev_assets
    # 3. 兜底：insightface 默认下载目录（首次会联网自动下载）
    return os.path.expanduser("~/.insightface")
