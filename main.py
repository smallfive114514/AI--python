# ============================================================
# 智能视觉识别系统 v2.0
# ------------------------------------------------------------
# 功能：
#   1. 目标检测 —— 实时识别 80 类常见物体
#   2. 目标追踪 —— 每个物体分配唯一ID，移动中ID不变
#   3. 越线计数 —— 画面中央统计线，物体穿过自动计数
#   4. 高级UI   —— 半透明框、HUD仪表盘、类别统计面板
#   5. 视频录制 —— 按 r 开始/停止录制，保存为 mp4
#   6. 视频输入 —— 支持读取本地视频文件
#
# 所有显示文字可在 config.py 中自定义，不用动这个文件
#
# 按键操作：
#   q 退出 | r 录制 | s 截图 | l 显示/隐藏计数线 | h 显示/隐藏HUD
# ============================================================


# ===== 第 1 部分：导入库 =====
import cv2          # OpenCV：画面读取、绘图、显示、录制
import numpy as np  # 数值计算，用于半透明叠加
from ultralytics import YOLO  # YOLOv8 目标检测+追踪模型
import time         # 计算帧率 FPS
import os           # 文件/文件夹操作
import argparse     # 命令行参数解析
from collections import Counter  # 统计各类别数量

# 导入显示配置 —— 所有可自定义的显示文字都在 config.py 里
# 想改启动画面文字、鸣谢名单，去改 config.py 即可
import config as cfg


# ===== 第 2 部分：配色方案 =====
PALETTE = [
    (255, 165, 0), (0, 255, 127), (0, 165, 255), (255, 0, 128),
    (128, 0, 255), (0, 255, 255), (255, 255, 0), (180, 105, 255),
    (50, 205, 50), (255, 20, 147),
]

def get_color(cls_id):
    return PALETTE[cls_id % len(PALETTE)]


# ===== 第 3 部分：绘图工具函数 =====

def draw_box(frame, x1, y1, x2, y2, color, alpha=0.35):
    """画半透明填充 + 实线边框的检测框"""
    overlay = frame.copy()
    cv2.rectangle(overlay, (x1, y1), (x2, y2), color, -1)
    cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)
    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)


def draw_label(frame, text, x, y, color, font_scale=0.55, thickness=2):
    """画带背景色的标签文字"""
    (tw, th), _ = cv2.getTextSize(
        text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)
    cv2.rectangle(frame, (x, y - th - 6), (x + tw + 6, y), color, -1)
    cv2.putText(frame, text, (x + 3, y - 5),
                cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0, 0, 0), thickness)


def draw_hud(frame, fps, n_objects, cross_up, cross_down, rec,
             class_counts, show_hud):
    """画顶部HUD仪表盘：FPS、检测数、越线数、录制状态、类别统计"""
    if not show_hud:
        return
    h, w = frame.shape[:2]
    # 半透明黑色背景条(顶部)
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (w, 90), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.5, frame, 0.5, 0, frame)

    # 第 1 行：FPS + 检测物体数 + 越线计数 + 录制状态
    rec_text = "  [REC]" if rec else ""
    line1 = (f"FPS:{fps:5.1f}  |  Objects:{n_objects:3d}  |  "
             f"Line UP:{cross_up}  DOWN:{cross_down}{rec_text}")
    cv2.putText(frame, line1, (10, 28), cv2.FONT_HERSHEY_SIMPLEX,
                0.6, (0, 255, 0) if not rec else (0, 0, 255), 2)

    # 第 2 行：类别统计(前5个最多的类别)
    top = class_counts.most_common(5)
    if top:
        parts = [f"{name}:{cnt}" for name, cnt in top]
        line2 = "  ".join(parts)
        cv2.putText(frame, line2, (10, 62), cv2.FONT_HERSHEY_SIMPLEX,
                    0.5, (200, 200, 255), 1)


def draw_count_line(frame, line_y, cross_up, cross_down, show_line):
    """画越线计数统计线"""
    if not show_line:
        return
    h, w = frame.shape[:2]
    overlay = frame.copy()
    cv2.line(overlay, (0, line_y), (w, line_y), (0, 255, 255), 2)
    cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)
    cv2.putText(frame, f"UP {cross_up}", (10, line_y - 8),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
    cv2.putText(frame, f"DOWN {cross_down}", (w - 130, line_y - 8),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)


# ===== 第 4 部分：越线计数器 =====
class LineCounter:
    """越线计数器：记录每个追踪ID位置，跨线时计数"""
    def __init__(self, line_ratio=0.5):
        self.line_ratio = line_ratio
        self.line_y = None
        self.history = {}
        self.cross_up = 0
        self.cross_down = 0

    def set_line(self, frame_height):
        self.line_y = int(frame_height * self.line_ratio)

    def update(self, track_id, cx, cy):
        if self.line_y is None:
            return
        if track_id in self.history:
            prev_y = self.history[track_id][1]
            if prev_y < self.line_y <= cy:
                self.cross_down += 1
            elif prev_y > self.line_y >= cy:
                self.cross_up += 1
        self.history[track_id] = (cx, cy)


# ===== 第 5 部分：视频录制器 =====
class VideoRecorder:
    """封装视频录制，按 r 键切换"""
    def __init__(self, save_dir="recordings"):
        self.save_dir = save_dir
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        self.writer = None
        self.recording = False

    def start(self, frame_size, fps=20.0):
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        path = os.path.join(self.save_dir, f"record_{int(time.time())}.mp4")
        self.writer = cv2.VideoWriter(path, fourcc, fps, frame_size)
        self.recording = True
        print(f"[录制开始] {path}")
        return path

    def write(self, frame):
        if self.recording and self.writer is not None:
            self.writer.write(frame)

    def stop(self):
        if self.recording:
            self.writer.release()
            self.recording = False
            print("[录制结束]")

    def toggle(self, frame_size, fps):
        if self.recording:
            self.stop()
        else:
            self.start(frame_size, fps)


# ===== 第 6 部分：启动界面打印工具 =====
# 所有显示文字都从 config.py 读取，改文字去 config.py 即可

def get_model_display_name(model_file):
    """根据模型文件名返回 (显示名, 描述)，从 config.py 查找"""
    base = os.path.basename(model_file).lower()
    for key, (name, desc) in cfg.MODEL_INFO.items():
        if key in base:
            return name, desc
    return model_file, cfg.DEFAULT_MODEL_DESC


def print_banner():
    """打印 ASCII 艺术标题栏，文字来自 config.py"""
    bar = "=" * 60
    print()
    print(bar)
    for line in cfg.ASCII_ART:
        print(line)
    print()
    print("     " + cfg.SYSTEM_TITLE)
    print("     " + cfg.SYSTEM_SUBTITLE)
    print(bar)


def print_config(args, model):
    """打印详细配置面板，文字来自 config.py"""
    bar = "-" * 60
    print(bar)
    print("  >> 系统配置")
    print(bar)

    # 模型信息
    display_name, model_desc = get_model_display_name(args.model)
    print(f"  [模型]   {display_name}")
    print(f"  [描述]   {model_desc}")
    print(f"  [文件]   {args.model}")

    # 检测参数
    source = f"视频文件 {args.video}" if args.video else f"摄像头 #{args.camera}"
    print(f"  [输入源] {source}")
    print(f"  [置信度] {args.conf:.0%}  (低于此值的检测结果会被忽略)")

    # 可识别类别列表（可开关）
    if cfg.SHOW_CLASS_LIST:
        print(bar)
        title = cfg.CLASS_LIST_TITLE.replace("{count}", str(len(model.names)))
        print(title)
        print(bar)
        names = list(model.names.values())
        cols = cfg.CLASS_LIST_COLUMNS
        for i in range(0, len(names), cols):
            row = names[i:i + cols]
            line = "  " + "  ".join(f"{n:<12}" for n in row)
            print(line)
    else:
        print(bar)
        print(f"  >> 可识别物体类别  (共 {len(model.names)} 类)")
        print(bar)

    # 功能特性列表（从 config 读取）
    print(bar)
    print("  >> 已启用功能")
    print(bar)
    for feat in cfg.ENABLED_FEATURES:
        print(f"  [✓] {feat}")
    print(bar)


def print_keymap():
    """打印按键操作速查表"""
    bar = "-" * 60
    print("  >> 按键操作速查")
    print(bar)
    print("  [基础操作]")
    print("    q  退出程序        r  开始/停止录制     s  保存截图")
    print("  [显示控制]")
    print("    l  显示/隐藏计数线  h  显示/隐藏HUD面板")
    print(bar)
    print()


def print_special_thanks():
    """打印特别鸣谢栏目，文字来自 config.py"""
    if not cfg.SHOW_SPECIAL_THANKS:
        return
    bar = "=" * 60
    print(bar)
    print(cfg.THANKS_TITLE)
    print(bar)
    print(cfg.THANKS_MESSAGE)
    print(bar)
    for name in cfg.THANKS_NAMES:
        print(f"  ★  {name}")
    print(bar)
    print(cfg.THANKS_FOOTER)
    print(bar)
    print()


# ===== 第 7 部分：主程序入口 =====
def main():
    # ---------- 7.1 解析命令行参数 ----------
    parser = argparse.ArgumentParser(description="智能视觉识别系统 v2.0")
    parser.add_argument("--camera", type=int, default=0,
                        help="摄像头编号，默认0")
    parser.add_argument("--video", type=str, default=None,
                        help="视频文件路径，填写后用视频代替摄像头")
    parser.add_argument("--model", type=str, default="yolov8n.pt",
                        help="模型文件: yolov8n/s/m/l/x.pt")
    parser.add_argument("--conf", type=float, default=0.5,
                        help="置信度阈值，默认0.5")
    args = parser.parse_args()

    # ---------- 7.2 打印启动界面 ----------
    print_banner()

    # ---------- 7.3 加载模型 ----------
    print(cfg.MSG_LOADING_MODEL)
    model = YOLO(args.model)

    print_config(args, model)
    print_keymap()
    print_special_thanks()

    # ---------- 7.4 打开视频源 ----------
    if args.video is not None:
        print(cfg.MSG_OPENING_VIDEO.format(video_path=args.video))
        cap = cv2.VideoCapture(args.video)
    else:
        print(cfg.MSG_OPENING_CAMERA.format(cam_id=args.camera))
        cap = cv2.VideoCapture(args.camera)

    if not cap.isOpened():
        print(cfg.MSG_SOURCE_ERROR)
        print("    - 摄像头：检查是否被占用、编号是否正确")
        print("    - 视频文件：检查路径是否正确")
        exit(1)
    print(cfg.MSG_SOURCE_READY + "\n")

    # ---------- 7.5 初始化各组件 ----------
    counter = LineCounter(line_ratio=0.5)
    recorder = VideoRecorder(save_dir="recordings")
    screenshot_dir = "screenshots"
    if not os.path.exists(screenshot_dir):
        os.makedirs(screenshot_dir)

    show_line = True
    show_hud = True
    prev_time = 0

    # ---------- 7.6 主循环 ----------
    while True:
        ret, frame = cap.read()
        if not ret:
            print("视频源已结束或读取失败")
            break

        h, w = frame.shape[:2]
        counter.set_line(h)

        # ===== 7.6.1 目标追踪 =====
        # model.track() 给每个物体分配持久ID，移动中ID不变
        # persist=True 跨帧保持追踪状态
        # tracker="bytetrack.yaml" 用ByteTrack追踪算法(轻量快速)
        results = model.track(frame, persist=True, tracker="bytetrack.yaml",
                              conf=args.conf, verbose=False)

        class_counts = Counter()

        # ===== 7.6.2 绘制每个检测/追踪结果 =====
        if results[0].boxes is not None:
            for box in results[0].boxes:
                cls_id = int(box.cls[0])
                class_name = model.names[cls_id]
                class_counts[class_name] += 1
                confidence = float(box.conf[0])
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                color = get_color(cls_id)

                # 画半透明检测框
                draw_box(frame, x1, y1, x2, y2, color, alpha=0.35)

                # 获取追踪ID
                track_id = int(box.id[0]) if box.id is not None else None
                id_str = f"#{track_id}" if track_id is not None else "?"
                label = f"{class_name} {confidence:.0%} {id_str}"
                draw_label(frame, label, x1, y1, color)

                # 越线计数：用物体中心点判断
                cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
                if track_id is not None:
                    counter.update(track_id, cx, cy)
                cv2.circle(frame, (cx, cy), 3, color, -1)

        # ===== 7.6.3 画计数线 =====
        draw_count_line(frame, counter.line_y, counter.cross_up,
                        counter.cross_down, show_line)

        # ===== 7.6.4 FPS + HUD =====
        curr_time = time.time()
        fps = 1 / (curr_time - prev_time) if (curr_time - prev_time) > 0 else 0
        prev_time = curr_time

        n_objects = len(results[0].boxes) if results[0].boxes is not None else 0
        draw_hud(frame, fps, n_objects, counter.cross_up, counter.cross_down,
                 recorder.recording, class_counts, show_hud)

        # ===== 7.6.5 录制 + 显示 =====
        recorder.write(frame)
        cv2.imshow(cfg.WINDOW_TITLE, frame)

        # ===== 7.6.6 按键处理 =====
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('r'):
            recorder.toggle((w, h), 20.0)
        elif key == ord('s'):
            path = os.path.join(screenshot_dir, f"shot_{int(time.time())}.jpg")
            cv2.imwrite(path, frame)
            print(f"截图已保存: {path}")
        elif key == ord('l'):
            show_line = not show_line
        elif key == ord('h'):
            show_hud = not show_hud

    # ---------- 7.7 收尾 ----------
    recorder.stop()
    cap.release()
    cv2.destroyAllWindows()
    print()
    print("=" * 60)
    print(cfg.MSG_EXIT_TITLE)
    print("=" * 60)
    print(cfg.MSG_EXIT_STATS.format(up=counter.cross_up, down=counter.cross_down))
    if recorder.recording:
        print(cfg.MSG_EXIT_RECORD_HINT)
    print("=" * 60)


if __name__ == "__main__":
    main()
