import subprocess
import time
import json
import paho.mqtt.client as mqtt

# ======================== 网卡参数配置 ========================
WIFI_IFACE = "wlP4p65s0"
LTE_IFACE  = "enxf04bb3b9ebe5"
TARGET_IP  = "8.8.8.8"  #网络连通测试IP

# ======================== MQTT配置 ========================
MQTT_BROKER = "localhost"
MQTT_PORT   = 1883
MQTT_TOPIC  = "network/status"

# ======================== MQTT初始化 ========================
client = mqtt.Client()
client.connect(MQTT_BROKER, MQTT_PORT, 60)

# ======================== Ping函数 ========================
def ping_through_interface(interface, target="8.8.8.8", count=1, timeout=1):
    try:
        result = subprocess.run(
            ["ping", "-I", interface, "-c", str(count), "-W", str(timeout), target],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return result.returncode == 0
    except Exception as e:
        print(f"网卡 {interface} Ping 失败: {e}")
        return False

# ======================== 主循环 ========================
print("Start Check")
while True:
    wifi_connected = ping_through_interface(WIFI_IFACE, TARGET_IP)
    lte_connected  = ping_through_interface(LTE_IFACE, TARGET_IP)

    wifi_status = "OK" if wifi_connected else "FAIL"
    lte_status  = "OK" if lte_connected else "FAIL"

    status = {
        "WIFI": wifi_status,
        "4G":   lte_status
    }
    # 控制台输出
    print(f"[{time.strftime('%H:%M:%S')}] WIFI: {wifi_status} | 4G: {lte_status}")#DEBUG
    try:
        client.publish(MQTT_TOPIC, json.dumps(status))
    except Exception as e:
        print(f"[MQTT] 发布失败: {e}")

    time.sleep(3)#3S检测一次
