# ======================== ReadMe ========================
#此代码是YOLO推理代码
#需搭配func.py后处理函数、rknnpool.py线程池函数、mediamtx使用
#功能要点:1.RTSP推流 2. System V 共享内存 3.YOLO实时推理
# ======================== ReadMe ========================

import cv2
import time
import numpy as np
import sysv_ipc
from rknnpool import initRKNN_NPU_Choice
from func import myFunc  # 替换为你自己的处理函数
import subprocess
from func import MQTT_Init
import func

# ======================== 共享内存参数定义 ========================
WIDTH, HEIGHT = 320, 240  # LVGL canvas 尺寸
SHM_KEY = 1234
SEM_KEY = 5678
SHM_SIZE = WIDTH * HEIGHT * 2  # RGB565: 每像素2字节

# ======================== 共享内存初始化 ========================
try:
    shm = sysv_ipc.SharedMemory(SHM_KEY, sysv_ipc.IPC_CREAT, size=SHM_SIZE)
    shm.write(b'\x00' * SHM_SIZE, 0)
except Exception as e:
    print(f"创建共享内存失败: {e}")
    exit(1)

try:
    sem = sysv_ipc.Semaphore(SEM_KEY, sysv_ipc.IPC_CREAT, initial_value=0)
except Exception as e:
    print(f"创建信号量失败: {e}")
    shm.remove()
    exit(1)

# ======================== 视频输入初始化 ========================
cap = cv2.VideoCapture(21)  # 根据实际摄像头索引修改
cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
cap.set(cv2.CAP_PROP_FPS, 60)

# ======================== 加载YOLO模型 ========================
rknn = initRKNN_NPU_Choice(
    "/home/elf/Desktop/Project/AI/yolo/rknn3588-yolov8/rknnModel/yolov8_nonQAT.rknn", 2)

# ===================== 初始化计数和时间-计算fps =====================
frames = 0
initTime = time.time()
last_time = initTime

# ===================== FFmpeg 推流设置（640x480 原图） =====================
ffmpeg_cmd = [
    'ffmpeg',
    '-f', 'rawvideo',
    '-pix_fmt', 'bgr24',
    '-s', '640x480',
    '-r', '30',
    '-i', '-',
    '-c:v', 'libx264',
    '-preset', 'medium',
    '-tune', 'zerolatency',
    '-f', 'rtsp',
    '-rtsp_transport', 'udp',
    '-pix_fmt', 'yuv420p',
    'rtsp://localhost:8554/mystream'
]
proc = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE)

# ===================== 图像转换函数 =====================
def bgr_to_rgb565(frame):#BGR->RGB565供LVGL的canva使用
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    r = (rgb[:, :, 0] >> 3).astype(np.uint16)
    g = (rgb[:, :, 1] >> 2).astype(np.uint16)
    b = (rgb[:, :, 2] >> 3).astype(np.uint16)
    rgb565 = (r << 11) | (g << 5) | b
    return rgb565

# ===================== MQTT 初始化 =====================
func.mqtt_client = MQTT_Init()

# ===================== 主处理循环 =====================
while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    raw_frame = frame.copy()  # 用于推流的原图

    # YOLO推理
    result_frame = myFunc(rknn, frame)

    # 显示 FPS
    current_time = time.time()
    fps = 1 / (current_time - last_time) if (current_time - last_time) > 0 else 0
    last_time = current_time
    cv2.putText(result_frame, f"FPS: {fps:.2f}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2, cv2.LINE_AA)

    # 适配LVGL的canva大小颜色格式并写入共享内存
    lvgl_frame = cv2.resize(result_frame, (WIDTH, HEIGHT), interpolation=cv2.INTER_LINEAR)
    rgb565 = bgr_to_rgb565(lvgl_frame)
    shm.write(rgb565.tobytes(), 0)
    sem.release()

    # 推流
    try:
        proc.stdin.write(raw_frame.tobytes())
    except Exception as e:
        print(f"写入FFmpeg失败: {e}")
        break

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

    frames += 1

# ===================== 资源清理 =====================
total_time = time.time() - initTime
print(f"总平均帧率: {frames / total_time:.2f} FPS")

cap.release()
cv2.destroyAllWindows()
rknn.release()
shm.detach()
shm.remove()
sem.remove()
proc.stdin.close()
proc.wait()
