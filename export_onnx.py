# ============================================================
# ONNX 模型导出脚本
# ------------------------------------------------------------
# 作用：把 .pt 模型转成 .onnx 格式，CPU 推理速度提升 2~5 倍
# 用法：
#   python export_onnx.py              # 默认导出 yolov8n.pt
#   python export_onnx.py --model yolov8s.pt  # 导出其他模型
#   python export_onnx.py --imgsz 480  # 指定分辨率(更小更快)
#
# 导出后用 .onnx 模型运行主程序：
#   python main.py --model yolov8n.onnx --imgsz 480
# ============================================================

import argparse
from ultralytics import YOLO


def main():
    parser = argparse.ArgumentParser(description="导出 ONNX 模型")
    parser.add_argument("--model", type=str, default="yolov8n.pt",
                        help="源模型文件: yolov8n/s/m.pt")
    parser.add_argument("--imgsz", type=int, default=640,
                        help="输入分辨率，480更快，640更准")
    parser.add_argument("--half", action="store_true",
                        help="FP16半精度(文件更小，部分CPU更快)")
    args = parser.parse_args()

    print(f"正在加载 {args.model} ...")
    model = YOLO(args.model)

    print(f"正在导出 ONNX (imgsz={args.imgsz}, half={args.half}) ...")
    # export() 会自动在同目录生成 .onnx 文件
    # 例如 yolov8n.pt -> yolov8n.onnx
    path = model.export(format="onnx", imgsz=args.imgsz, half=args.half)
    print(f"导出完成: {path}")
    print()
    print("现在可以用 ONNX 模型运行了（更快）:")
    print(f"  python main.py --model {path} --imgsz {args.imgsz}")


if __name__ == "__main__":
    main()
