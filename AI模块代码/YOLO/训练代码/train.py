# ======================== Readme ========================
#本代码是YOLOv8n训练代码
#因ultralytics库较为完善-->可直接用来训练
# ======================== Readme ========================

from ultralytics import YOLO

model =YOLO('runs/detect/train/weights/best.pt')
model.train(data='ultralytics/datasets/ID_identify/ID.yaml', epochs=200, imgsz=640, device=0, workers=0,augment=True)
