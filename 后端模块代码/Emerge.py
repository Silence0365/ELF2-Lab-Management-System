import time
import json
import paho.mqtt.client as mqtt
import subprocess
import threading

# ======================== 参数配置 ========================
ACC_THRESHOLD = 1
GYRO_THRESHOLD = 20
TEMP_THRESHOLD = 40

MQTT_CONFIG = {
    "broker": "127.0.0.1",
    "port": 1883,
    "keepalive": 10,
    "topic": "sensors/data",
    "client_id": "earthquake_detector"
}

ENABLE_MQTT = True
MQTT_TOPIC = "earthquake/alert"

ALERT_AUDIO = "/home/elf/Desktop/Project/automatic/earthquake.wav"

# ======================== 地震语音播报 ========================
#仿照例程使用amixer
def play_alert_sound(repeat=5):
    for i in range(repeat):

        try:
            subprocess.run(["amixer", "-c", "rockchipnau8822", "sset", "PCM", "255"], check=True)
            subprocess.run(["amixer", "-c", "rockchipnau8822", "sset", "Speaker", "on"], check=True)
            subprocess.run(["amixer", "-c", "rockchipnau8822", "sset", "Speaker", "100"], check=True)
            cmd = f'gst-play-1.0 "{ALERT_AUDIO}" --audiosink="alsasink device=plughw:1,0"'
            subprocess.run(cmd, shell=True, check=True)
        except subprocess.CalledProcessError as e:
            print(f"播放失败（命令错误）: {e}")
        except Exception as e:
            print(f"播放失败: {e}")

# ======================== 地震检测函数 ========================
def is_earthquake(data):
    for axis in data['accel']:
        if abs(axis) > ACC_THRESHOLD:
            return True
    for axis in data['gyro']:
        if abs(axis) > GYRO_THRESHOLD:
            return True
    return False

def trigger_alarm(data):
    with open("quake_log.txt", "a") as f:
        f.write(json.dumps(data) + "\n")
    if ENABLE_MQTT:
        mqtt_client.publish(MQTT_TOPIC, "earthquake", qos=1)
    threading.Thread(target=play_alert_sound, kwargs={"repeat": 5}, daemon=True).start()

# ======================== 火灾检测函数 ========================
def is_fireworks(data):
    if aht > TEMP_THRESHOLD:
        with open("fire_log.txt", "a") as f:
            f.write(json.dumps(data) + "\n")
    if ENABLE_MQTT:
        mqtt_client.publish(MQTT_TOPIC, "earthquake", qos=1)

# ======================== MQTT读取数据 ========================
def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode('utf-8'))
        aht = payload.get("aht20", {})
        bmp = payload.get("bmp280", {})
        print(f"AHT20 - 温度: {aht.get('temperature')}°C, 湿度: {aht.get('humidity')}%")
        print(f"BMP280 - 温度: {bmp.get('temperature')}°C, 气压: {bmp.get('pressure')} hPa")
        # MPU6050：数据读取
        mpu = payload.get("mpu6050", {})
        if not mpu: return
        accel = mpu.get("accel", {})
        gyro = mpu.get("gyro", {})

        data = {
            "accel": [accel.get('x', 0), accel.get('y', 0), accel.get('z', 0)],
            "gyro": [gyro.get('x', 0), gyro.get('y', 0), gyro.get('z', 0)],
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        #条件判断
        if is_earthquake(data):
            trigger_alarm(data)

    except Exception as e:
        print(f"[解析错误] {e}")
        
# ======================== MQTT初始化 ========================
def init_mqtt():
    client = mqtt.Client(client_id=MQTT_CONFIG["client_id"])
    client.on_message = on_message
    try:
        client.connect(MQTT_CONFIG["broker"], MQTT_CONFIG["port"], MQTT_CONFIG["keepalive"])
        client.subscribe(MQTT_CONFIG["topic"], qos=1)
        client.loop_start()
        return client
    except Exception as e:
        print(f"MQTT error: {str(e)}")
        return None

# ======================== 主程序 ========================
def main():
    global mqtt_client
    mqtt_client = init_mqtt()
    if not mqtt_client:
        print("初始化失败")
        return
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("quit")
        mqtt_client.loop_stop()

if __name__ == "__main__":
    main()
