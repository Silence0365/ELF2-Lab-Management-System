#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
import json
import threading
import paho.mqtt.client as mqtt  # 导入MQTT库

# ======================== MQTT配置文件========================

#订阅IP
MQTT_BROKER = "localhost" 

#订阅端口
MQTT_PORT = 1883

#订阅主题
MQTT_TOPICS = [
    ("HA/B401/light/state",0),
    ("HA/B402/light/state",0),
    ("HA/B403/light/state",0),
    ("HA/B404/light/state",0),
    ("HA/B405/light/state",0),
    ("HA/Door/state", 0),
    ("HA/B401/light/set", 0),
    ("HA/B402/light/set", 0),
    ("HA/B403/light/set", 0),
    ("HA/B404/light/set", 0),
    ("HA/B405/light/set", 0),
    ("HA/Door/set", 0),
    ("control/HA",0),
    ("control/LVGL",0),
    ("ack/LVGL",0),
    ("HA/Fan/speed/set",0),
    ("HA/Fan/speed/state",0),
    ("AI/Identify",0),
    ("earthquake/alert",0)
]

#发送JSON信息构造函数
def build_state_payload(light_id: str, state: str) -> str:
    payload_dict = {light_id: state}
    return json.dumps(payload_dict)


# 连接成功回调
def on_connect(client, userdata, flags, rc):
    print("✅ Connected with result code", rc)
    for topic, qos in MQTT_TOPICS:
        client.subscribe(topic, qos)
        print(f"📡 Subscribed to topic: {topic}")

# ========================FLAG ==========================
B401_Light_State = "OFF"
B402_Light_State = "OFF"
B403_Light_State = "OFF"
B404_Light_State = "OFF"
B405_Light_State = "OFF"
Door_State      = "OFF"

# ======================== 红蓝灯交替闪烁 ========================
def blink_leds(times=10):
    try:
        for _ in range(times):
            control_gpio(pin=99, mode="out", value=1, action="enable")   # 红灯亮
            control_gpio(pin=102, mode="out", value=0, action="enable")  # 蓝灯灭
            time.sleep(1)
            control_gpio(pin=99, mode="out", value=0, action="enable")   # 红灯灭
            control_gpio(pin=102, mode="out", value=1, action="enable")  # 蓝灯亮
            time.sleep(1)
        # 结束后关闭灯（可选）
        control_gpio(pin=99, mode="out", value=0, action="enable")
        control_gpio(pin=102, mode="out", value=0, action="enable")
    except Exception as e:
        print(f"LED闪烁线程异常: {e}")

# ======================== 信息接收处理 ========================
def on_message(client, userdata, msg):
    global B401_Light_State,B402_Light_State,B403_Light_State,B404_Light_State,B405_Light_State,Door_State#全局变量声明

    # ======================== HA控制 ========================
    if msg.topic == "HA/B401/light/set":
        if msg.payload.decode() == "ON":
            #print("B401 Light turned ON")
            control_gpio(pin=104, mode="out", value=0, action="enable")
            B401_Light_State = "ON"
            client.publish("HA/B401/light/state", "ON", qos=1, retain=True)
        else:
            control_gpio(pin=104, mode="out", value=1, action="enable")
            B401_Light_State = "OFF"
            client.publish("HA/B401/light/state", "OFF", qos=1, retain=True)
            #print("B401 Light turned OFF")
        send_single_ack(client, "B401_Light", B401_Light_State)

    if msg.topic == "HA/B402/light/set":
        if msg.payload.decode() == "ON":
            control_gpio(pin=105, mode="out", value=0, action="enable")
            B402_Light_State = "ON"
            #print("B402 Light turned ON")
            client.publish("HA/B402/light/state", "ON", qos=1, retain=True)
        else:
            control_gpio(pin=105, mode="out", value=1, action="enable")
            B402_Light_State = "OFF"
            client.publish("HA/B402/light/state", "OFF", qos=1, retain=True)
            #print("B402 Light turned OFF")
        send_single_ack(client, "B402_Light", B402_Light_State)

    if msg.topic == "HA/B403/light/set":
        if msg.payload.decode() == "ON":
            control_gpio(pin=107, mode="out", value=0, action="enable")
            B403_Light_State = "ON"
            #print("B403 Light turned ON")
            client.publish("HA/B403/light/state", "ON", qos=1, retain=True)
        else:
            control_gpio(pin=107, mode="out", value=1, action="enable")
            B403_Light_State = "OFF"
            client.publish("HA/B403/light/state", "OFF", qos=1, retain=True)
            #print("B403 Light turned OFF")
        send_single_ack(client, "B403_Light", B403_Light_State)

    if msg.topic == "HA/B404/light/set":
        if msg.payload.decode() == "ON":
            control_gpio(pin=108, mode="out", value=0, action="enable")
            B404_Light_State = "ON"
            #print("B404 Light turned ON")
            client.publish("HA/B404/light/state", "ON", qos=1, retain=True)
        else:
            control_gpio(pin=108, mode="out", value=1, action="enable")
            B404_Light_State = "OFF"
            client.publish("HA/B404/light/state", "OFF", qos=1, retain=True)
            #print("B404 Light turned OFF")
        send_single_ack(client, "B404_Light", B404_Light_State)

    if msg.topic == "HA/B405/light/set":
        if msg.payload.decode() == "ON":
            control_gpio(pin=98, mode="out", value=0, action="enable")
            B405_Light_State = "ON"
            #print("B405 Light turned ON")
            client.publish("HA/B405/light/state", "ON", qos=1, retain=True)
        else:
            control_gpio(pin=98, mode="out", value=1, action="enable")
            B405_Light_State = "OFF"
            client.publish("HA/B405/light/state", "OFF", qos=1, retain=True)
            #print("B405 Light turned OFF")
        send_single_ack(client, "B405_Light", B405_Light_State)

    if msg.topic == "HA/Door/set":
        if msg.payload.decode() == "ON":
            set_pwm_duty_cycle(chip=0, channel=0, period_ns=20000000, speed_percent=94.75)
            control_gpio(pin=98, mode="out", value=0, action="enable")
            Door_State = "ON"
            B405_Light_State = "ON"
            #print(" Door turned ON")
            client.publish("HA/Relay/state", "ON", qos=1, retain=True)
            client.publish("HA/B405/light/state", "ON", qos=1, retain=True)
        else:
            set_pwm_duty_cycle(chip=0, channel=0, period_ns=20000000, speed_percent=97.5)
            control_gpio(pin=98, mode="out", value=1, action="enable")
            Door_State = "OFF"
            B405_Light_State = "OFF"
            client.publish("HA/Door/state", "OFF", qos=1, retain=True)
            client.publish("HA/B405/light/state", "OFF", qos=1, retain=True)
            #print(" Door turned OFF")
        send_single_ack(client, "B405_Light", B405_Light_State)
        #LVGL_ACK(client)  
    if msg.topic == "HA/Fan/speed/set":
        payload = msg.payload.decode()  # JSON解码
        try:
            speed = int(payload)
            if 0 <= speed <= 100:
                #print(f"设置风扇速度为 {speed}%")
                set_pwm_duty_cycle(chip=1, channel=0, period_ns=40000, speed_percent=100 - speed)
                client.publish("HA/Fan/speed/state", str(speed), qos=1, retain=True)
            else:
                print("Fan Pwm Set is out of range")
        except ValueError:
            print("type error!")

        send_single_ack(client, "Fan", speed)

    # ======================== 身份认证 ========================
    if msg.topic == "AI/Identify":
        payload = msg.payload.decode()  # JSON解码
        data = json.loads(payload) 
        card1 = data.get('card1_num')
        card2 = data.get('card2_num')
        card =card1+card2
        if card != 0:
            set_pwm_duty_cycle(chip=0, channel=0, period_ns=20000000, speed_percent=95)
            control_gpio(pin=98, mode="out", value=0, action="enable")
            client.publish("HA/Door/state", "ON", qos=1, retain=True)
            client.publish("HA/B405/light/state", "ON", qos=1, retain=True)
            send_single_ack(client, "B405_Light", B405_Light_State)

            time.sleep(5) 

            set_pwm_duty_cycle(chip=0, channel=0, period_ns=20000000, speed_percent=97.5)    
            control_gpio(pin=98, mode="out", value=1, action="enable")
            client.publish("HA/Door/state", "OFF", qos=1, retain=True)
            client.publish("HA/B405/light/state", "OFF", qos=1, retain=True)
            send_single_ack(client, "B405_Light", B405_Light_State)

    # ======================== LVGL控制 =============================
    if msg.topic == "control/LVGL":
        skip_ack = False
        try:
            payload_json = json.loads(msg.payload.decode())

            for key, state in payload_json.items():
                if key == "B401_Light":
                    control_gpio(pin=104, mode="out", value=0 if state == "ON" else 1, action="enable")
                    client.publish("HA/B401/light/state", state, qos=1, retain=True)
                    B401_Light_State = state

                elif key == "B402_Light":
                    control_gpio(pin=105, mode="out", value=0 if state == "ON" else 1, action="enable")
                    client.publish("HA/B402/light/state", state, qos=1, retain=True)
                    B402_Light_State = state

                elif key == "B403_Light":
                    control_gpio(pin=107, mode="out", value=0 if state == "ON" else 1, action="enable")
                    client.publish("HA/B403/light/state", state, qos=1, retain=True)
                    B403_Light_State = state

                elif key == "B404_Light":
                    control_gpio(pin=108, mode="out", value=0 if state == "ON" else 1, action="enable")
                    client.publish("HA/B404/light/state", state, qos=1, retain=True)
                    B404_Light_State = state

                elif key == "B405_Light":
                    control_gpio(pin=98, mode="out", value=0 if state == "ON" else 1, action="enable")
                    client.publish("HA/B405/light/state", state, qos=1, retain=True)
                    B405_Light_State = state

                elif key == "speed":
                    set_pwm_duty_cycle(chip=1, channel=0, period_ns=40000, speed_percent=100-int(state))
                    client.publish("HA/Fan/speed/state", state, qos=1, retain=True)
                    skip_ack = True

        except json.JSONDecodeError:
            print("JSON Error")
        except Exception as e:
            print(f"处理 control/LVGL 时出错: {e}")

# ======================== 异常情况控制 =============================
    if msg.topic == "earthquake/alert":
            skip_ack = False
            try:
                payload_str = msg.payload.decode().strip()
                if payload_str == "earthquake":
                    set_pwm_duty_cycle(chip=0, channel=0, period_ns=20000000, speed_percent=94.75)#Door_open
                    send_single_ack(client, "emergy", "True")#LVGL
                    print("earthquake_test")
                    blink_thread = threading.Thread(target=blink_leds, daemon=True)
                    blink_thread.start()
            except json.JSONDecodeError:
                print("❌ JSON 解析失败")
            except Exception as e:
                print(f"❌ 处理 control/LVGL 时出错: {e}")



# ======================== LVGL 回调函数 ========================
def send_single_ack(client, key: str, value: str):
    payload = json.dumps({key: value})
    client.publish("ack/LVGL", payload, qos=1, retain=True)


# ======================== GPIO 控制函数 ========================
def control_gpio(pin: int, mode: str = "out", value: int = None, action: str = "enable"):
    gpio_path = f"/sys/class/gpio/gpio{pin}"

    if action == "enable":
        if not os.path.exists(gpio_path):
            with open("/sys/class/gpio/export", 'w') as f:
                f.write(str(pin))
            time.sleep(0.1)

        with open(f"{gpio_path}/direction", 'w') as f:
            f.write(mode)

        if mode == "out" and value is not None:
            if isinstance(value, str):
                value = 1 if value.lower() == "high" else 0
            with open(f"{gpio_path}/value", 'w') as f:
                f.write(str(value))

        if mode == "in":
            with open(f"{gpio_path}/value", 'r') as f:
                read_val = f.read().strip()
            print(f"[GPIO] 读取 GPIO{pin} 输入电平: {read_val}")
            state = "NO" if read_val == "1" else "YES"
            client.publish("bettery/status", json.dumps({"Charging": state}), qos=1, retain=True)


    elif action == "disable":
        if os.path.exists(gpio_path):
            with open("/sys/class/gpio/unexport", 'w') as f:
                f.write(str(pin))
# ======================== GPIO读取状态函数 ========================
def read_gpio_input(pin: int):
    gpio_path = f"/sys/class/gpio/gpio{pin}/value"
    try:
        with open(gpio_path, 'r') as f:
            read_val = f.read().strip()
        print(f"[GPIO] 读取 GPIO{pin} 输入电平: {read_val}")
        state = "NO" if read_val == "1" else "YES"
        client.publish("bettery/status", json.dumps({"Charging": state}), qos=1, retain=True)
    except FileNotFoundError:
        print(f"[GPIO] GPIO{pin} 未初始化，无法读取")
# ======================== PWM 控制函数 ========================

def control_pwm(chip: int, channel: int, period_ns: int = 40000, duty_ns: int = 10000, enable: bool = True):
    """
    控制 PWM 输出
    :param chip: PWM 控制器编号，如 pwmchip0 => 传 0
    :param channel: PWM 通道编号，如 pwm0 => 传 0
    :param period_ns: 周期，单位 ns
    :param duty_ns: 占空比，单位 ns
    :param enable: 是否输出 PWM
    """
    pwmchip_path = f"/sys/class/pwm/pwmchip{chip}"
    pwm_path = f"{pwmchip_path}/pwm{channel}"

    if not os.path.exists(pwm_path):
        with open(f"{pwmchip_path}/export", 'w') as f:
            f.write(str(channel))
        time.sleep(0.1)

    with open(f"{pwm_path}/period", 'w') as f:
        f.write(str(period_ns))

    with open(f"{pwm_path}/duty_cycle", 'w') as f:
        f.write(str(duty_ns))

    with open(f"{pwm_path}/enable", 'w') as f:
        f.write('1' if enable else '0')

# ======================== ADC 读取函数 ========================

def read_adc_voltage(channel: int, vref: float = 1.8) -> float:
    """
    读取 ADC 电压值
    :param channel: ADC 通道号（如 6）
    :param vref: 参考电压（默认 1.8V）
    :return: 电压值 (float)
    """
    adc_path = f"/sys/bus/iio/devices/iio:device0/in_voltage{channel}_raw"
    try:
        with open(adc_path, 'r') as f:
            raw = int(f.read().strip())
        voltage = (raw / 4096.0) * vref
        print(f"[ADC] 通道{channel} = {raw}，电压 ≈ {voltage:.3f} V")
        return voltage
    except FileNotFoundError:
        print(f"[ADC] 通道 {channel} 不存在")
        return -1

# ======================== PWM占空比设置函数 ========================
def set_pwm_duty_cycle(chip: int, channel: int, period_ns: int, speed_percent: int):
    """
    设置指定 PWM 通道的占空比（支持不同频率）
    :param chip: PWM 控制器编号，如 pwmchip0 => 传 0
    :param channel: PWM 通道编号，如 pwm0 => 传 0
    :param period_ns: 周期，单位 ns
    :param speed_percent: 占空比百分比（0~100）
    """
    speed_percent = max(0, min(100, speed_percent))  # 限制范围
    duty_ns = int(period_ns * speed_percent / 100)
    print(f"[PWM] duty_ns = {duty_ns}")

    # 统一用 control_pwm 执行初始化与设置
    try:
        control_pwm(chip=chip, channel=channel, period_ns=period_ns, duty_ns=duty_ns, enable=True)
        print(f"[PWM] pwmchip{chip}/pwm{channel} 频率={1e9/period_ns:.2f}Hz，占空比={speed_percent}%")
    except Exception as e:
        print(f"[PWM] 设置失败: {e}")

# ======================== 示例调用 ========================

if __name__ == "__main__":
    client = mqtt.Client(client_id="UI_Cb")
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_start()
    control_gpio(pin=103, mode="in")
    control_gpio(pin=101, mode="in")
    while True:
        #read_gpio_input(pin=103)
        time.sleep(1)

    # print("=== GPIO / PWM / ADC 控制函数版 示例 ===")

    # # GPIO 输出高电平
    # control_gpio(pin=104, mode="out", value=0, action="enable")
    # time.sleep(1)
    # control_gpio(pin=105, mode="out", value=0, action="enable")
    # time.sleep(1)
    # control_gpio(pin=107, mode="out", value=0, action="enable")
    # time.sleep(1)
    # control_gpio(pin=108, mode="out", value=0, action="enable")
    # time.sleep(1)
    # control_gpio(pin=98, mode="out", value=1, action="enable")
    # #control_gpio(pin=107, mode="out", value=0)

    # GPIO 输入读取


    # # 关闭 GPIO
    # control_gpio(pin=107, action="disable")

    # # PWM 输出
    # control_pwm(chip=0, channel=0, period_ns=1000000, duty_ns=300000, enable=True)
    # time.sleep(2)
    # control_pwm(chip=0, channel=0, enable=False)

    # # ADC 读取（通道6）
    # read_adc_voltage(channel=6)



