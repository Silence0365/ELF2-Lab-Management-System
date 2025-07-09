from flask import Flask, request, jsonify
import paho.mqtt.client as mqtt
import threading
import json
from flask_cors import CORS
import subprocess
from threading import Thread
import os

app = Flask(__name__)
CORS(app)  # 允许所有来源跨域请求
# 设备和传感器状态缓存（初始化）
devices = {
    "B401": {"name": "B401灯光", "state": "off"},
    "B402": {"name": "B402灯光", "state": "off"},
    "B403": {"name": "B403灯光", "state": "off"},
    "B404": {"name": "B404灯光", "state": "off"},
    "B405": {"name": "B405灯光", "state": "off"},
    "Door": {"name": "Door", "state": "off"},  
    "Fan": {"name": "Fan", "speed": 0},
}

sensors = {
    "temperature": "--",
    "humidity": "--",
    "pressure": "--",
    "light": "--",
    "tof": "--",
    "voltage": "--",
    "current": "--",
    "power": "--",
    "energy_wh": "--",
    "soc": "--"
}

# MQTT 配置
MQTT_BROKER = "127.0.0.1"
MQTT_PORT = 1883  # ws端口9001是WebSocket，paho用TCP1883连接正常
MQTT_TOPICS = [f"HA/{key}/light/state" for key in devices.keys() if key != "Fan"] + [
    "HA/Fan/speed/state",
    "sensors/data",
    "HA/Door/state",
    "HA/Door/set"
]


mqtt_client = mqtt.Client()

def on_connect(client, userdata, flags, rc):
    print("MQTT connected with result code", rc)
    # 订阅主题
    for topic in MQTT_TOPICS:
        client.subscribe(topic, qos=1)
        print("Subscribed to", topic)

def on_message(client, userdata, msg):
    topic = msg.topic
    payload = msg.payload.decode()
    print(f"MQTT message received on {topic}: {payload}")

    # 设备状态更新
    import re
    dev_match = re.match(r"HA/(B40[1-5]|Relay)/light/state", topic)
    if dev_match:
        dev_key = dev_match.group(1)
        if dev_key in devices:
            devices[dev_key]["state"] = payload.lower()
        return

    # 风扇速度状态更新
    if topic == "HA/Fan/speed/state":
        speed = int(payload)
        if 0 <= speed <= 100:
            devices["Fan"]["speed"] = speed
        return

    # 传感器数据更新
    if topic == "sensors/data":
        try:
            data = json.loads(payload)
            # aht20 温湿度
            if "aht20" in data:
                if "temperature" in data["aht20"] and data["aht20"]["temperature"] is not None:
                    sensors["temperature"] = round(data["aht20"]["temperature"], 2)
                if "humidity" in data["aht20"] and data["aht20"]["humidity"] is not None:
                    sensors["humidity"] = round(data["aht20"]["humidity"], 2)
            # bmp280 气压
            if "bmp280" in data:
                if "pressure" in data["bmp280"] and data["bmp280"]["pressure"] is not None:
                    sensors["pressure"] = round(data["bmp280"]["pressure"], 2)
            # bh1750 光照
            if "bh1750" in data and data["bh1750"] is not None:
                sensors["light"] = round(data["bh1750"], 2)
            # tof 距离
            if "tof" in data and data["tof"] is not None:
                sensors["tof"] = round(data["tof"], 2)
            # ina219 电池相关
            if "ina219" in data:
                ina = data["ina219"]
                if ina.get("voltage") is not None:
                    sensors["voltage"] = round(ina.get("voltage"), 2)
                if ina.get("current") is not None:
                    sensors["current"] = round(ina.get("current"), 2)
                if ina.get("power") is not None:
                    sensors["power"] = round(ina.get("power"), 2)
                if "remaining_mah" in ina and ina.get("remaining_mah") is not None and ina.get("voltage") is not None:
                    sensors["energy_wh"] = round(ina["remaining_mah"] * ina["voltage"] / 1000, 2)
                if ina.get("soc") is not None:
                    sensors["soc"] = round(ina.get("soc"), 2)
            # sgp30 空气质量（eCO2 和 TVOC）
            if "sgp30" in data:
                if "eCO2" in data["sgp30"] and data["sgp30"]["eCO2"] is not None:
                    sensors["co2"] = round(data["sgp30"]["eCO2"], 2)
                if "TVOC" in data["sgp30"] and data["sgp30"]["TVOC"] is not None:
                    sensors["tvoc"] = round(data["sgp30"]["TVOC"], 2)
        except Exception as e:
            print("Failed to parse sensor data:", e)


# 启动 MQTT 连接与循环
def mqtt_thread():
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
    mqtt_client.loop_forever()

threading.Thread(target=mqtt_thread, daemon=True).start()
def run_http_server():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    subprocess.run(["python3", "-m", "http.server", "8000", "--directory", current_dir])
# --- Flask HTTP 接口 ---

# 获取当前设备和传感器状态
@app.route('/api/status', methods=['GET'])
def api_status():
    device_states = {}
    for k, v in devices.items():
        if k == "Fan":
            device_states[k] = v.get("speed", 0)
        else:
            device_states[k] = v.get("state", "off")
    return jsonify({
        "devices": device_states,
        "sensors": sensors
    })


# 设备控制接口，前端调用此接口发送控制命令
@app.route('/api/control', methods=['POST'])
def api_control():
    data = request.json
    device = data.get("device")
    command = data.get("command")

    if device not in devices:
        return jsonify({"error": "未知设备"}), 400

    if device == "Fan":
        # 允许数字命令（字符串形式的数字也转int）
        try:
            speed = int(command)
            if not (0 <= speed <= 100):
                raise ValueError
        except:
            return jsonify({"error": "无效风扇速度命令，应为0~100的数字"}), 400
        
        devices["Fan"]["speed"] = speed
        # 发布MQTT消息，假设风扇控制主题和格式为HA/Fan/speed/set，消息内容为速度数字
        mqtt_client.publish("HA/Fan/speed/set", str(speed), qos=1, retain=True)
        print("1")
        return jsonify({"status": "success", "device": device, "command": speed})

    else:
        # 其他设备继续处理ON/OFF命令
        if command not in ("ON", "OFF"):
            return jsonify({"error": "无效命令"}), 400
        devices[device]["state"] = command.lower()
        if device == "Door":
            topic = "HA/Door/set"
        else:
            topic = f"HA/{device}/light/set"
        mqtt_client.publish(topic, command, qos=1, retain=True)
        return jsonify({"status": "success", "device": device, "command": command})

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    # 只允许 user 登录
    if username == "user" and password == "user":
        return jsonify({"success": True, "message": "登录成功"})
    else:
        return jsonify({"success": False, "message": "用户名或密码错误"})
    

if __name__ == "__main__":
    Thread(target=run_http_server, daemon=True).start()
    app.run(host="0.0.0.0", port=5001)

