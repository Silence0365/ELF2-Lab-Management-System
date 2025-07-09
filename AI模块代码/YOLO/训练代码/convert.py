# ======================== Readme ========================
#本代码是YOLOv8n转化代码
#pt-->支持RK的onnx
# ======================== Readme ========================

from ultralytics import YOLO

# 加载YOLOv8模型
model = YOLO("runs/detect/train6/weights/best.pt")

# 将模型导出为RKNN格式
success = model.export(format="rknn", device=0)
