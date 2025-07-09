from evdev import InputDevice, categorize, ecodes
import paho.mqtt.client as mqtt
import json
import re  

# ======================== MQTT配置 ========================
MQTT_CONFIG = {
    "broker": "127.0.0.1",
    "port": 1883,
    "keepalive": 10,
    "topic": "scanner/qr",
    "client_id": "scanner_client",
}

# ======================== 扫码枪输入设备路径 ========================
DEVICE_PATH = '/dev/input/event7'

# ======================== 初始化 ========================
device = InputDevice(DEVICE_PATH)

client = mqtt.Client(client_id=MQTT_CONFIG["client_id"])
client.connect(MQTT_CONFIG["broker"], MQTT_CONFIG["port"], MQTT_CONFIG["keepalive"])
client.loop_start()

# ======================== 字符对应表 ========================
key_map = {
    ecodes.KEY_0: '0', ecodes.KEY_1: '1', ecodes.KEY_2: '2',
    ecodes.KEY_3: '3', ecodes.KEY_4: '4', ecodes.KEY_5: '5',
    ecodes.KEY_6: '6', ecodes.KEY_7: '7', ecodes.KEY_8: '8',
    ecodes.KEY_9: '9',
    ecodes.KEY_A: 'A', ecodes.KEY_B: 'B', ecodes.KEY_C: 'C',
    ecodes.KEY_D: 'D', ecodes.KEY_E: 'E', ecodes.KEY_F: 'F',
    ecodes.KEY_G: 'G', ecodes.KEY_H: 'H', ecodes.KEY_I: 'I',
    ecodes.KEY_J: 'J', ecodes.KEY_K: 'K', ecodes.KEY_L: 'L',
    ecodes.KEY_M: 'M', ecodes.KEY_N: 'N', ecodes.KEY_O: 'O',
    ecodes.KEY_P: 'P', ecodes.KEY_Q: 'Q', ecodes.KEY_R: 'R',
    ecodes.KEY_S: 'S', ecodes.KEY_T: 'T', ecodes.KEY_U: 'U',
    ecodes.KEY_V: 'V', ecodes.KEY_W: 'W', ecodes.KEY_X: 'X',
    ecodes.KEY_Y: 'Y', ecodes.KEY_Z: 'Z',
    ecodes.KEY_MINUS: '-', ecodes.KEY_EQUAL: '=',
    ecodes.KEY_SLASH: '/', ecodes.KEY_DOT: '.',
    ecodes.KEY_COMMA: ',', ecodes.KEY_SPACE: ' ',
    ecodes.KEY_APOSTROPHE: '"', 
}

buffer = ''
print(f"Scaner Listening：{DEVICE_PATH}")#Debug

for event in device.read_loop():
    if event.type == ecodes.EV_KEY:
        key_event = categorize(event)
        if key_event.keystate == key_event.key_down:
            code = key_event.scancode
            if code == ecodes.KEY_ENTER:
                print(f"Scaning Done {buffer}")#Debug
                #数据处理
                fields = re.findall(r'"(.*?)"|(\d+)', buffer)
                flat_fields = [f[0] if f[0] else f[1] for f in fields]
                if len(flat_fields) == 4:
                    name, model, price_str, date = flat_fields
                    try:
                        price = int(price_str)
                        payload = json.dumps({
                            "name": name,
                            "model": model,
                            "price": price,
                            "date": date
                        })
                        print(f"[发送 JSON] {payload}")#DEBUG
                        client.publish(MQTT_CONFIG["topic"], payload)
                    except ValueError:
                        print("⚠️ price 字段无法转为整数")#DEBUG
                else:
                    print("⚠️ 字段数量不为 4，忽略")#DEBUG

                buffer = ''
            elif code in key_map:
                buffer += key_map[code]