# ======================== ReadMe ========================
#此代码是YOLO后处理代码
#以下代码改自https://github.com/rockchip-linux/rknn-toolkit2/tree/master/examples/onnx/yolov5
#需搭配main.py使用
# ======================== ReadMe ========================

import cv2
import numpy as np
import time
import json
import paho.mqtt.client as mqtt  # 新增MQTT库

#OBJ_THRESH, NMS_THRESH, IMG_SIZE = 0.25, 0.45, 640

CARD1 = 0
CARD2 = 0
ID_FLAG = 0
mqtt_client = None


OBJ_THRESH, NMS_THRESH, IMG_SIZE = 0.6, 0.40, 640

# CLASSES = ("person", "bicycle", "car", "motorbike ", "aeroplane ", "bus ", "train", "truck ", "boat", "traffic light",
#            "fire hydrant", "stop sign ", "parking meter", "bench", "bird", "cat", "dog ", "horse ", "sheep", "cow", "elephant",
#            "bear", "zebra ", "giraffe", "backpack", "umbrella", "handbag", "tie", "suitcase", "frisbee", "skis", "snowboard", "sports ball", "kite",
#            "baseball bat", "baseball glove", "skateboard", "surfboard", "tennis racket", "bottle", "wine glass", "cup", "fork", "knife ",
#            "spoon", "bowl", "banana", "apple", "sandwich", "orange", "broccoli", "carrot", "hot dog", "pizza ", "donut", "cake", "chair", "sofa",
#            "pottedplant", "bed", "diningtable", "toilet ", "tvmonitor", "laptop	", "mouse	", "remote ", "keyboard ", "cell phone", "microwave ",
#            "oven ", "toaster", "sink", "refrigerator ", "book", "clock", "vase", "scissors ", "teddy bear ", "hair drier", "toothbrush ")
#识别分类
CLASSES = ("card1", "card2")

def filter_boxes(boxes, box_confidences, box_class_probs):
    """Filter boxes with object threshold.
    """
    box_confidences = box_confidences.reshape(-1)
    candidate, class_num = box_class_probs.shape

    class_max_score = np.max(box_class_probs, axis=-1)
    classes = np.argmax(box_class_probs, axis=-1)

    _class_pos = np.where(class_max_score* box_confidences >= OBJ_THRESH)
    scores = (class_max_score* box_confidences)[_class_pos]

    boxes = boxes[_class_pos]
    classes = classes[_class_pos]

    return boxes, classes, scores

def nms_boxes(boxes, scores):
    """Suppress non-maximal boxes.
    # Returns
        keep: ndarray, index of effective boxes.
    """
    x = boxes[:, 0]
    y = boxes[:, 1]
    w = boxes[:, 2] - boxes[:, 0]
    h = boxes[:, 3] - boxes[:, 1]

    areas = w * h
    order = scores.argsort()[::-1]

    keep = []
    while order.size > 0:
        i = order[0]
        keep.append(i)

        xx1 = np.maximum(x[i], x[order[1:]])
        yy1 = np.maximum(y[i], y[order[1:]])
        xx2 = np.minimum(x[i] + w[i], x[order[1:]] + w[order[1:]])
        yy2 = np.minimum(y[i] + h[i], y[order[1:]] + h[order[1:]])

        w1 = np.maximum(0.0, xx2 - xx1 + 0.00001)
        h1 = np.maximum(0.0, yy2 - yy1 + 0.00001)
        inter = w1 * h1

        ovr = inter / (areas[i] + areas[order[1:]] - inter)
        inds = np.where(ovr <= NMS_THRESH)[0]
        order = order[inds + 1]
    keep = np.array(keep)
    return keep

def dfl(position):
    # Distribution Focal Loss (DFL)
    # x = np.array(position)
    n,c,h,w = position.shape
    p_num = 4
    mc = c//p_num
    y = position.reshape(n,p_num,mc,h,w)
    
    # Vectorized softmax
    e_y = np.exp(y - np.max(y, axis=2, keepdims=True))  # subtract max for numerical stability
    y = e_y / np.sum(e_y, axis=2, keepdims=True)
    
    acc_metrix = np.arange(mc).reshape(1,1,mc,1,1)
    y = (y*acc_metrix).sum(2)
    return y
    

def box_process(position):
    grid_h, grid_w = position.shape[2:4]
    col, row = np.meshgrid(np.arange(0, grid_w), np.arange(0, grid_h))
    col = col.reshape(1, 1, grid_h, grid_w)
    row = row.reshape(1, 1, grid_h, grid_w)
    grid = np.concatenate((col, row), axis=1)
    stride = np.array([IMG_SIZE//grid_h, IMG_SIZE//grid_w]).reshape(1,2,1,1)

    position = dfl(position)
    box_xy  = grid +0.5 -position[:,0:2,:,:]
    box_xy2 = grid +0.5 +position[:,2:4,:,:]
    xyxy = np.concatenate((box_xy*stride, box_xy2*stride), axis=1)

    return xyxy

def yolov8_post_process(input_data):
    boxes, scores, classes_conf = [], [], []
    defualt_branch=3
    pair_per_branch = len(input_data)//defualt_branch
    # Python 忽略 score_sum 输出
    for i in range(defualt_branch):
        boxes.append(box_process(input_data[pair_per_branch*i]))
        classes_conf.append(input_data[pair_per_branch*i+1])
        scores.append(np.ones_like(input_data[pair_per_branch*i+1][:,:1,:,:], dtype=np.float32))

    def sp_flatten(_in):
        ch = _in.shape[1]
        _in = _in.transpose(0,2,3,1)
        return _in.reshape(-1, ch)

    boxes = [sp_flatten(_v) for _v in boxes]
    classes_conf = [sp_flatten(_v) for _v in classes_conf]
    scores = [sp_flatten(_v) for _v in scores]

    boxes = np.concatenate(boxes)
    classes_conf = np.concatenate(classes_conf)
    scores = np.concatenate(scores)

    # filter according to threshold
    boxes, classes, scores = filter_boxes(boxes, scores, classes_conf)

    # nms
    nboxes, nclasses, nscores = [], [], []
    for c in set(classes):
        inds = np.where(classes == c)
        b = boxes[inds]
        c = classes[inds]
        s = scores[inds]
        keep = nms_boxes(b, s)

        if len(keep) != 0:
            nboxes.append(b[keep])
            nclasses.append(c[keep])
            nscores.append(s[keep])

    if not nclasses and not nscores:
        return None, None, None

    boxes = np.concatenate(nboxes)
    classes = np.concatenate(nclasses)
    scores = np.concatenate(nscores)

    return boxes, classes, scores

def draw(image, boxes, scores, classes, ratio, padding):
    for box, score, cl in zip(boxes, scores, classes):
        top, left, right, bottom = box
        
        top = (top - padding[0])/ratio[0]
        left = (left - padding[1])/ratio[1]
        right = (right - padding[0])/ratio[0]
        bottom = (bottom - padding[1])/ratio[1]
        # print('class: {}, score: {}'.format(CLASSES[cl], score))
        # print('box coordinate left,top,right,down: [{}, {}, {}, {}]'.format(top, left, right, bottom))
        top = int(top)
        left = int(left)

        cv2.rectangle(image, (top, left), (int(right), int(bottom)), (255, 0, 0), 2)
        cv2.putText(image, '{0} {1:.2f}'.format(CLASSES[cl], score),
                    (top, left - 6),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6, (0, 0, 255), 2)

def letterbox(im, new_shape=(640, 640), color=(0, 0, 0)):
    shape = im.shape[:2]  # current shape [height, width]
    if isinstance(new_shape, int):
        new_shape = (new_shape, new_shape)

    r = min(new_shape[0] / shape[0], new_shape[1] / shape[1])

    ratio = r, r  # width, height ratios
    new_unpad = int(round(shape[1] * r)), int(round(shape[0] * r))
    dw, dh = new_shape[1] - new_unpad[0], new_shape[0] - \
        new_unpad[1]  # wh padding

    dw /= 2  # divide padding into 2 sides
    dh /= 2

    if shape[::-1] != new_unpad:  # resize
        im = cv2.resize(im, new_unpad, interpolation=cv2.INTER_LINEAR)
    top, bottom = int(round(dh - 0.1)), int(round(dh + 0.1))
    left, right = int(round(dw - 0.1)), int(round(dw + 0.1))
    im = cv2.copyMakeBorder(im, top, bottom, left, right,
                            cv2.BORDER_CONSTANT, value=color)  # add border
    #return im
    return im, ratio, (left, top)

def myFunc(rknn_lite, IMG):
    global ID_FLAG
    IMG2 = cv2.cvtColor(IMG, cv2.COLOR_BGR2RGB)
    # 等比例缩放
    IMG2, ratio, padding = letterbox(IMG2)
    # 强制放缩
    # IMG2 = cv2.resize(IMG, (IMG_SIZE, IMG_SIZE))
    IMG2 = np.expand_dims(IMG2, 0)
    
    outputs = rknn_lite.inference(inputs=[IMG2],data_format=['nhwc'])

    #print("oups1",len(outputs))
    #print("oups2",outputs[0].shape)

    boxes, classes, scores = yolov8_post_process(outputs)


    if boxes is not None:
        draw(IMG, boxes, scores, classes, ratio, padding)

        now = time.time()

        found_cards = { 'card1': False, 'card2': False }

        for cls, score in zip(classes, scores):
            class_name = CLASSES[cls]
            if class_name in found_cards and score >= 0.85:
                found_cards[class_name] = True

        for card_name in found_cards:
            timer = detect_timer[card_name]
            if found_cards[card_name]:
                ID_FLAG=0
                if timer['start_time'] is None: 
                    timer['start_time'] = now
                elif not timer['triggered'] and now - timer['start_time'] >= 1:
                    if card_name == 'card1':
                        ID_FLAG=1
                        data_send()
                    elif card_name == 'card2':
                        ID_FLAG=2
                        data_send()
                    print(f"[INFO] {card_name} Indentified!")
                    timer['triggered'] = True
            else:
                # 未检测到，重置状态
                timer['start_time'] = None
                timer['triggered'] = False
    else:
        for card_name in detect_timer:
            detect_timer[card_name]['start_time'] = None
            detect_timer[card_name]['triggered'] = False

    return IMG


detect_timer = {
    'card1': {
        'start_time': None,
        'triggered': False
    },
    'card2': {
        'start_time': None,
        'triggered': False
    }
}

# ======================== MQTT配置 ========================
MQTT_CONFIG = {
    "broker": "127.0.0.1",      # MQTT代理地址（本地）
    "port": 1883,               # MQTT端口
    "keepalive": 10,            # 心跳间隔
    "topic": "AI/Identify",    # 发布主题
    "client_id": "AI_YOLOV8"   # 客户端ID
}

def MQTT_Init():
    mqtt_client = mqtt.Client(client_id=MQTT_CONFIG["client_id"])
    try:
        mqtt_client.connect(MQTT_CONFIG["broker"], 
                      MQTT_CONFIG["port"], 
                      MQTT_CONFIG["keepalive"])
        print(f"成功连接到MQTT代理: {MQTT_CONFIG['broker']}:{MQTT_CONFIG['port']}")
        mqtt_client.loop_start()
        return mqtt_client
    except Exception as e:
        print(f"MQTT连接失败: {str(e)}")
        return None


# ======================== 身份识别配置 ========================
def FLAG_Progress():
    global CARD1, CARD2
    if ID_FLAG == 1:
        CARD1=1
    elif ID_FLAG == 2:
        CARD2=1

def data_send():
    global CARD1, CARD2, mqtt_client
    FLAG_Progress()
    mqtt_payload = {
        "card1_num":CARD1, "card2_num":CARD2
    }
    try:
        mqtt_client.publish(
            topic=MQTT_CONFIG["topic"],
            payload=json.dumps(mqtt_payload),
            qos=1
        )
        print(f"[MQTT] 数据已发布至 {MQTT_CONFIG['topic']}")
        CARD1=0
        CARD2=0
    except Exception as e:
        print(f"[MQTT错误] 发布失败: {str(e)}")