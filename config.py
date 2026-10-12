"""全局常量配置。"""

UDP_PORT = 37465              # UDP 广播端口默认值（收发共用，可在设置中修改）
BROADCAST_ADDR = "255.255.255.255"  # 广播地址默认值（可在设置中配置多个，逗号分隔）
HEARTBEAT_INTERVAL = 1       # 心跳间隔默认值（秒，可在设置中修改）
PEER_TIMEOUT = 60             # 离线判定默认值（秒，可在设置中修改）

SIM_THRESHOLD = 0.45          # 人脸相似度阈值（余弦相似度，越大越严格）
CONFIRM_WINDOW = 5            # 滑动窗口帧数
CONFIRM_HITS = 3              # 窗口内命中多少帧才确认报警
CAMERA_FPS = 10               # 摄像头检测帧率上限（降低 CPU 占用）
COOLDOWN_SECONDS = 300        # 全局报警冷却时长（秒），默认 5 分钟
DET_SIZE = (320, 320)         # 人脸检测输入尺寸

APP_NAME = "LeaderAlert"      # 应用名（同时用于注册表自启动项名称）
APP_VERSION = "0.1.0"         # 版本号（与 pyproject.toml 保持一致）
