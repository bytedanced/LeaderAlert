"""全局常量配置。"""

UDP_PORT = 37465              # UDP 广播端口（收发共用）
BROADCAST_ADDR = "255.255.255.255"  # 广播地址
HEARTBEAT_INTERVAL = 30       # 心跳间隔（秒）
PEER_TIMEOUT = 60             # 超过该时长无心跳则判定离线（秒）

SIM_THRESHOLD = 0.45          # 人脸相似度阈值（余弦相似度，越大越严格）
CONFIRM_WINDOW = 5            # 滑动窗口帧数
CONFIRM_HITS = 3              # 窗口内命中多少帧才确认报警
CAMERA_FPS = 10               # 摄像头检测帧率上限（降低 CPU 占用）
COOLDOWN_SECONDS = 300        # 全局报警冷却时长（秒），默认 5 分钟
DET_SIZE = (320, 320)         # 人脸检测输入尺寸

APP_NAME = "LeaderAlert"      # 应用名（同时用于注册表自启动项名称）
