# ============================================================
# 系统显示配置文件
# ------------------------------------------------------------
# 想改 CMD 启动时显示什么文字，直接改这个文件就行，不用动 main.py
# 所有可自定义的内容都在这里，每一项都有注释说明
# ============================================================


# ===== 1. 系统标题（ASCII 艺术字下方的标题） =====
# 改成你想要的名字，比如你的项目名、公司名
SYSTEM_TITLE = "群星云Quntec视觉识别 Vision v2.0"
SYSTEM_SUBTITLE = "Real-Time Object Detection Suite"


# ===== 2. ASCII 艺术字（标题栏的图案） =====
# 你可以换成任何你喜欢的 ASCII 艺术字
# 网上搜 "ASCII art generator" 可以生成你自己的
# 注意：反斜杠 \ 要写成 \\，否则会报错
ASCII_ART = [
    "   ___                    _                 ",
    "  / _ \   _   _   _ __   | |_    ___    ___ ",
    " | | | | | | | | | '_ \  | __|  / _ \  / __|",
    " | |_| | | |_| | | | | | | |_  |  __/ | (__ ",
    "  \__\_\  \__,_| |_| |_|  \__|  \___|  \___|",
                                            
]


# ===== 3. 模型自定义名称 =====
# 当你用不同模型时，显示什么中文名和描述
# 格式: "模型文件名": ("显示名", "描述文字")
# 你可以随便改名字，比如改成你自己起的名字
MODEL_INFO = {
    "yolov8n.pt":  ("Nano",   "极速版 · 适合实时检测 · 参数量~3M"),
    "yolov8s.pt":  ("Small",  "均衡版 · 精度更高 · 参数量~11M"),
    "yolov8m.pt":  ("Medium", "精准版 · 适合高精度场景 · 参数量~26M"),
    "yolov8l.pt":  ("Large",  "高精版 · 更慢更准 · 参数量~44M"),
    "yolov8x.pt":  ("XLarge", "旗舰版 · 最高精度 · 参数量~68M"),
}

# 如果用的模型不在上面列表里，显示这个默认名称
DEFAULT_MODEL_NAME = "Quntec-Yo8.pt"
DEFAULT_MODEL_DESC = "Medium"


# ===== 4. 已启用功能列表 =====
# 启动时显示的功能列表，你可以增删改
# 格式就是普通文字，想加就加一行，想删就删一行
ENABLED_FEATURES = [
    "目标检测   - 识别画面中的物体并标注框+名称+置信度",
    "目标追踪   - 分配唯一ID，物体移动中ID保持不变(ByteTrack)",
    "越线计数   - 画面中央统计线，分上行/下行自动计数",
    "HUD仪表盘  - 实时显示FPS/物体数/类别统计",
    "视频录制   - 按R键录制检测结果为MP4视频",
    "截图保存   - 按S键保存当前画面为JPG图片",
]


# ===== 5. 启动提示文字 =====
# 各阶段显示的提示信息，你可以改成自己的风格
MSG_LOADING_MODEL = "  正在初始化模型，请稍候 ..."
MSG_OPENING_CAMERA = "  [INFO] 正在打开摄像头 #{cam_id} ..."
MSG_OPENING_VIDEO = "  [INFO] 正在打开视频文件: {video_path}"
MSG_SOURCE_READY = "  [OK] 视频源已就绪，开始检测"
MSG_SOURCE_ERROR = "  [ERROR] 无法打开视频源！"
MSG_EXIT_TITLE = "  程序运行结束"
MSG_EXIT_STATS = "  [统计] 越线上行: {up} 次 | 下行: {down} 次"
MSG_EXIT_RECORD_HINT = "  [提示] 录制文件已保存到 recordings/ 文件夹"


# ===== 6. 可识别类别是否显示完整列表 =====
# True  = 启动时列出所有 80 个类别名（默认）
# False = 只显示总数，不列出具体名称（更简洁）
SHOW_CLASS_LIST = True

# 每行显示几个类别（只有 SHOW_CLASS_LIST=True 时有效）
CLASS_LIST_COLUMNS = 6

# 类别列表标题，{count} 会被自动替换成实际数量
CLASS_LIST_TITLE = "  >> 可识别物体类别  (共 {count} 类)"


# ===== 7. 窗口标题栏 =====
# 运行时摄像头窗口的标题
WINDOW_TITLE = "群星云Quntec视觉识别 Vision v2.0 (q:quit r:rec s:shot l:line h:hud)"


# ===== 8. 特别鸣谢 =====
# 启动时显示的鸣谢栏目，你可以自由修改下面所有文字
# 把名字换成你想感谢的人，增删都行

# 是否显示特别鸣谢栏目
SHOW_SPECIAL_THANKS = True

# ---- 鸣谢各部分颜色 ----
# 可选颜色：red / green / yellow / blue / magenta / cyan / white
# 改成你喜欢的颜色组合即可，不用动代码
THANKS_TITLE_COLOR   = "red"     # 标题颜色
THANKS_MESSAGE_COLOR = "blue"   # 寄语颜色
THANKS_NAMES_COLOR   = "magenta"    # 人名颜色
THANKS_DESC_COLOR    = "cyan"     # 贡献描述颜色
THANKS_FOOTER_COLOR  = "magenta"  # 结尾语颜色

# 鸣谢栏目标题
THANKS_TITLE = "  >> 特别鸣谢  Special Thanks"

# 鸣谢寄语（你那段话，可自由编辑）
THANKS_MESSAGE = (
    "  本项目历经高中两年打磨，从最初的构想到最终成型，\n"
    "  离不开以下朋友们的无私帮助与支持。\n"
    "  感谢你们在测试阶段提供的宝贵反馈，\n"
    "  更感谢在开发人员陷入低谷时给予的鼓励与陪伴我们将你们的网名在此写下，感谢你们的付出（顺序不分先后）。"
)

# 鸣谢名单（每行一个人名或一段话，想加就加一行，想删就删一行）
# 格式建议: "名字 - 贡献描述"，会自动分别上色
THANKS_NAMES = [
    "开发鸣谢       - 默    执笔梦星云    北风.   .  ",
    "测试鸣谢        - 秋秋  向右转",
    "全体测试同学 - 耐心试用并提出改进意见",
    "特别鸣谢(网名，排名不分先后)        - Sakura  米哈游全家桶受害者  不吃haozi的苹果派  "
]

# 鸣谢栏结尾语
THANKS_FOOTER = "  非常感谢你们的付出。"
