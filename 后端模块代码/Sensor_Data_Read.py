#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import serial                                   #串口库
import time
import binascii
import smbus2                                   #IIC总线
import bme280                                   #BMP280库
from adafruit_extended_bus import ExtendedI2C
import adafruit_ahtx0                           #AHT20库
import warnings
import json
import paho.mqtt.client as mqtt
import threading

# ======================== MQTT配置 ========================
MQTT_CONFIG = {
    "broker": "127.0.0.1",      # MQTT代理地址（本地）
    "port": 1883,               # MQTT端口
    "keepalive": 10,            # 心跳间隔
    "topic": "sensors/data",    # 发布主题
    "client_id": "sensor_pub"   # 客户端ID
}

# 抑制I2C频率警告
warnings.filterwarnings("ignore", category=RuntimeWarning, module="adafruit_blinka")

# ======================== 模块配置 ========================
# 串口配置
TOF_UART_PORT = '/dev/ttyS3'  # UART3
TOF_BAUDRATE = 115200

# I2C总线分配
I2C_BUS_7 = 7        # MPU6050|SGP30使用I2C-7
I2C_BUS_BH1750 = 6   # BH1750使用I2C-6 
I2C_BUS_ENV = 8      # AHT20+BMP280使用I2C-8

# 传感器地址
AHT20_ADDR = 0x38
BMP280_ADDR = 0x77
BH1750_ADDR = 0x23
MPU6050_ADDR = 0x68 
INA219_ADDR = 0x40
SGP30_ADDR = 0x58

# ======================== 传感器指令/寄存器  ========================
# BH1750指令
BH1750_POWER_ON = 0x01
BH1750_CONTINUOUS_HIGH_RES_MODE = 0x10

# MPU6050指令
MPU6050_RA_ACCEL_XOUT_H = 0x3B
MPU6050_RA_PWR_MGMT_1 = 0x6B
MPU6050_RA_GYRO_CONFIG = 0x1B
MPU6050_RA_ACCEL_CONFIG = 0x1C

# INA219指令
SHUNT_OHMS                = 0.01
MAX_CURRENT               = 3.0
BATTERY_CAPACITY_MAH      = 9000    #电池容量
CHARGE_VOLTAGE            = 25.2    #充电电压
CHARGE_CURRENT            = 1       #充电电流
REG_SHUNT_VOLTAGE         = 0x01
REG_BUS_VOLTAGE           = 0x02
remaining_mah = BATTERY_CAPACITY_MAH
last_time = time.time()
is_charging = True

# SGP30
SGP30_CMD_IAQ_INIT            = [0x20, 0x03]
SGP30_CMD_MEASURE_AIR_QUALITY = [0x20, 0x08]

# ======================== 数据处理辅助函数  ========================
def to_signed(value):
    """将16位无符号值转换为有符号补码"""
    return value if value < 0x8000 else value - 0x10000

def crc8(data):
    """SGP30使用的CRC-8校验函数（多项式0x31, 初始值0xFF）"""
    crc_func = crcmod.predefined.mkPredefinedCrcFun('crc-8')
    return crc_func(bytes(data))

def read_signed_16bit(bus, reg):
    raw = bus.read_word_data(INA219_ADDR, reg)
    val = ((raw & 0xFF) << 8) | (raw >> 8)
    return val - 0x10000 if val > 0x7FFF else val

def read_unsigned_16bit(bus, reg):
    raw = bus.read_word_data(INA219_ADDR, reg)
    return ((raw & 0xFF) << 8) | (raw >> 8)

def crc8(data):
    crc = 0xFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if (crc & 0x80):
                crc = ((crc << 1) ^ 0x31) & 0xFF
            else:
                crc = (crc << 1) & 0xFF
    return crc

# ======================== 总线设备初始化  ========================
def init_buses():
    buses = {}
    try:
        buses['mpu6050'] = smbus2.SMBus(I2C_BUS_7)
        print(f"I2C-{I2C_BUS_7}(MPU6050)初始化成功")
    except Exception as e:
        print(f"I2C-{I2C_BUS_7}初始化失败: {e}")
        buses['mpu6050'] = None

    try:
        buses['bh1750'] = smbus2.SMBus(I2C_BUS_BH1750)
        print(f"I2C-{I2C_BUS_BH1750}(BH1750)初始化成功")
    except Exception as e:
        print(f"I2C-{I2C_BUS_BH1750}初始化失败: {e}")
        buses['bh1750'] = None

    try:
        buses['env'] = smbus2.SMBus(I2C_BUS_ENV)
        print(f"I2C-{I2C_BUS_ENV}(AHT20+BMP280)初始化成功")
    except Exception as e:
        print(f"I2C-{I2C_BUS_ENV}初始化失败: {e}")
        buses['env'] = None

    try:
        buses['tof'] = serial.Serial(TOF_UART_PORT, TOF_BAUDRATE, timeout=1)
        print(f"UART{TOF_UART_PORT}(TOF)初始化成功")
    except Exception as e:
        print(f"TOF串口初始化失败: {e}")
        buses['tof'] = None

    # AHT20需要ExtendedI2C
    try:
        buses['aht20_i2c'] = ExtendedI2C(I2C_BUS_ENV)
        buses['aht20'] = adafruit_ahtx0.AHTx0(buses['aht20_i2c'], address=AHT20_ADDR)
        print("AHT20初始化成功")
    except Exception as e:
        print(f"AHT20初始化失败: {e}")
        buses['aht20'] = None

    try:
        buses['ina219'] = smbus2.SMBus(I2C_BUS_7)
        print(f"I2C-{I2C_BUS_7}(INA219)初始化成功")
    except Exception as e:
        print(f"I2C-{I2C_BUS_7}初始化失败: {e}")
        buses['ina219'] = None

    try:
        buses['sgp30'] = smbus2.SMBus(I2C_BUS_7)
        buses['sgp30'].write_i2c_block_data(SGP30_ADDR, SGP30_CMD_IAQ_INIT[0], [SGP30_CMD_IAQ_INIT[1]])
        time.sleep(0.01)
        print(f"I2C-{I2C_BUS_7}(SGP30)初始化成功")
    except Exception as e:
        print(f"I2C-{I2C_BUS_7}初始化失败（SGP30）: {e}")
        buses['sgp30'] = None

    return buses

# ======================== 传感器数据读取函数 ========================
#TOF距离传感器
def read_tof(ser):
    if not ser or not ser.in_waiting:
        return None
    try:
        raw_data = ser.read(ser.in_waiting)
        hex_data = binascii.hexlify(raw_data).decode('ascii')
        if len(hex_data) >= 10:
            return int(hex_data[6:10], 16)
    except Exception as e:
        print(f"[TOF错误] {e}")
    return None

#BMP280大气压传感器
def read_bmp280(bus):
    if not bus:
        return None
    try:
        calibration_params = bme280.load_calibration_params(bus, BMP280_ADDR)
        data = bme280.sample(bus, BMP280_ADDR, calibration_params)
        return {'temperature': data.temperature, 'pressure': data.pressure}
    except Exception as e:
        print(f"[BMP280错误] {e}")
    return None

#AHT20温湿度传感器
def read_aht20(sensor):
    if not sensor:
        return None
    try:
        return {
            'temperature': sensor.temperature,
            'humidity': sensor.relative_humidity
        }
    except Exception as e:
        print(f"[AHT20错误] {e}")
    return None

#BH1750光照传感器
def read_bh1750(bus):
    if not bus:
        return None
    try:
        bus.write_byte(BH1750_ADDR, BH1750_POWER_ON)
        bus.write_byte(BH1750_ADDR, BH1750_CONTINUOUS_HIGH_RES_MODE)
        time.sleep(0.12)
        data = bus.read_i2c_block_data(BH1750_ADDR, 0x00, 2)
        return ((data[0] << 8) | data[1]) / 1.2
    except Exception as e:
        print(f"[BH1750错误] {e}")
    return None

#MPU6050传感器
def read_mpu6050(bus):
    if not bus:
        return None
    try:
        # 初始化MPU6050
        bus.write_byte_data(MPU6050_ADDR, MPU6050_RA_PWR_MGMT_1, 0x00)  # 唤醒设备
        time.sleep(0.1)  # 等待初始化完成
        bus.write_byte_data(MPU6050_ADDR, MPU6050_RA_GYRO_CONFIG, 0x08)  # ±500°/s
        bus.write_byte_data(MPU6050_ADDR, MPU6050_RA_ACCEL_CONFIG, 0x10)  # ±8g

        # 读取传感器数据
        data = bus.read_i2c_block_data(MPU6050_ADDR, MPU6050_RA_ACCEL_XOUT_H, 14)
        print(f"[MPU6050] 原始数据: {[hex(b) for b in data]}")  # 调试输出

        # 解析数据
        accel_x = to_signed((data[0] << 8) | data[1]) / 4096.0
        accel_y = to_signed((data[2] << 8) | data[3]) / 4096.0
        accel_z = to_signed((data[4] << 8) | data[5]) / 4096.0
        temp = to_signed((data[6] << 8) | data[7]) / 340.0 + 36.53
        gyro_x = to_signed((data[8] << 8) | data[9]) / 65.5
        gyro_y = to_signed((data[10] << 8) | data[11]) / 65.5
        gyro_z = to_signed((data[12] << 8) | data[13]) / 65.5
        print(f"[MPU6050] 解析温度: {temp:.2f}°C")

        return {
            'accel_x': accel_x,
            'accel_y': accel_y,
            'accel_z': accel_z,
            'temp': temp,
            'gyro_x': gyro_x,
            'gyro_y': gyro_y,
            'gyro_z': gyro_z
        }
    except Exception as e:
        print(f"[MPU6050错误] {e}")
    return None

#INA219传感器
def read_ina219(bus, elapsed_sec, remaining_mah):
    if not bus:
        return None
    try:
        shunt_raw = read_signed_16bit(bus, REG_SHUNT_VOLTAGE)
        bus_raw   = read_unsigned_16bit(bus, REG_BUS_VOLTAGE)

        shunt_voltage_mv = shunt_raw * 0.01
        bus_voltage_v    = ((bus_raw >> 3) * 0.004)
        current_ma       = shunt_voltage_mv / SHUNT_OHMS
        current_a        =current_ma/1000
        power_w         = current_a * bus_voltage_v
        #电量估测算法
        if is_charging:
            net_current_ma = (CHARGE_CURRENT * 1000) - current_ma  # 单位统一为 mA|充电电流=充电-放电
            delta_mah = net_current_ma * (elapsed_sec / 3600.0)
            remaining_mah += delta_mah
        else:
            delta_mah = current_ma * (elapsed_sec / 3600.0)
            remaining_mah -= delta_mah

        # 限制范围
        remaining_mah = max(0, min(BATTERY_CAPACITY_MAH, remaining_mah))
        soc_percent = remaining_mah / BATTERY_CAPACITY_MAH * 100

        return {
            'voltage': bus_voltage_v,
            'current': current_a,
            'power': power_w,
            'shunt_mv': shunt_voltage_mv,
            'remaining_mah': remaining_mah,
            'soc': soc_percent,
            'charging': is_charging 
        }, remaining_mah

    except Exception as e:
        print(f"[INA219错误] {e}")
        return None, remaining_mah

#SGP30传感器
def read_sgp30(bus):
    if not bus:
        return None
    try:
        # 发送测量指令
        bus.write_i2c_block_data(SGP30_ADDR, SGP30_CMD_MEASURE_AIR_QUALITY[0], [SGP30_CMD_MEASURE_AIR_QUALITY[1]])
        time.sleep(0.05)

        # 读取数据：eCO2 (2B+CRC), TVOC (2B+CRC)
        data = bus.read_i2c_block_data(SGP30_ADDR, 0x00, 6)

        if (crc8(data[0:2]) != data[2]) or (crc8(data[3:5]) != data[5]):
            print("[SGP30] CRC校验失败")
            return None

        eCO2 = (data[0] << 8) | data[1]
        TVOC = (data[3] << 8) | data[4]

        return {
            'eCO2': eCO2,
            'TVOC': TVOC
        }

    except Exception as e:
        print(f"[SGP30错误] {e}")
        return None
        
#========================上次记录电量读取函数==================
def fetch_retained_values():
    result = {'remaining_mah': None, 'soc': None}
    event = {'received': False}

    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            client.subscribe(MQTT_CONFIG['topic'], qos=1)
        else:
            print(f"[错误] Retained 客户端连接失败，返回码: {rc}")

    def on_message(client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode('utf-8'))
            if 'ina219' in payload:
                result['remaining_mah'] = payload['ina219'].get('remaining_mah')
                result['soc'] = payload['ina219'].get('soc')
                event['received'] = True
        except Exception as e:
            print(f"[错误] Retained 解析失败: {e}")

    client = mqtt.Client(client_id="fetch_retained")
    client.on_connect = on_connect
    client.on_message = on_message

    try:
        client.connect(MQTT_CONFIG['broker'], MQTT_CONFIG['port'], 5)
        client.loop_start()
        timeout = time.time() + 3  # ⏱️ 等待最多 3 秒
        while not event['received'] and time.time() < timeout:
            time.sleep(0.1)
        client.loop_stop()
        client.disconnect()
        if not event['received']:
            print("记录值丢失，重置容量9000mah")
    except Exception as e:
        print(f"[错误] 获取剩余电量消息失败: {e}")

    return result

#========================充电状态读取函数==================
def on_message_charge_states(client, userdata, msg):
    global is_charging

    if msg.topic == "bettery/status":
        try:
            payload = json.loads(msg.payload.decode())
            if "Charging" in payload:
                is_charging = (payload["Charging"].upper() == "YES")#布尔表达式
                #print(f"⚡ MQTT 充电状态更新：is_charging = {is_charging}")
        except Exception as e:
            print(f"❌ 解析 bettery/status 失败: {e}")

# MQTT初始化函数
def init_mqtt():
    client = mqtt.Client(client_id=MQTT_CONFIG["client_id"])
    client.on_message = on_message_charge_states#绑定回调
    try:
        client.connect(MQTT_CONFIG["broker"], 
                      MQTT_CONFIG["port"], 
                      MQTT_CONFIG["keepalive"])
        print(f"成功连接到MQTT代理: {MQTT_CONFIG['broker']}:{MQTT_CONFIG['port']}")
        client.subscribe("bettery/status", qos=1)#订阅主题
        client.loop_start()
        return client
    except Exception as e:
        print(f"MQTT连接失败: {str(e)}")
        return None
 
#========================主程序==================
def main():
    # 初始化传感器总线
    buses = init_buses()
    #读取记录的SOC和mah
    global remaining_mah, last_time
    retained = fetch_retained_values()
    if retained:
        remaining_mah = retained['remaining_mah'] if retained['remaining_mah'] is not None else BATTERY_CAPACITY_MAH
    # 初始化MQTT客户端
    mqtt_client = init_mqtt()
    if not mqtt_client:
        print("错误：无法初始化MQTT客户端，程序终止")
        return
    #数据读取
    try:
        while True:
            #print("\n" + "="*50)#DEBUG
            #print(f"{time.strftime('%Y-%m-%d %H:%M:%S')} Data")#DEBUG
            #print("="*50)#DEBUG

            # INA219剩余SOC电量估算
            now = time.time()
            elapsed_sec = now - last_time
            last_time = now

            # 读取所有传感器数据
            data = {
                'tof': read_tof(buses['tof']),
                'bmp280': read_bmp280(buses['env']),
                'aht20': read_aht20(buses['aht20']),
                'bh1750': read_bh1750(buses['bh1750']),
                'mpu6050': read_mpu6050(buses['mpu6050']),
                'ina219': None,  # 先设为 None，后续读取后更新-->上电需等待10s后才出数据
                'sgp30': read_sgp30(buses['sgp30'])
            }

            # 剩余电量读取
            if buses.get('ina219'):
                data['ina219'], remaining_mah = read_ina219(buses['ina219'], elapsed_sec, remaining_mah)
 
            # 构建JSON数据包
            mqtt_payload = {
                "timestamp": time.time(),
                "tof": data['tof'],
                "bmp280": {
                    "temperature": data['bmp280']['temperature'] if data['bmp280'] else None,
                    "pressure": data['bmp280']['pressure'] if data['bmp280'] else None
                },
                "aht20": {
                    "temperature": data['aht20']['temperature'] if data['aht20'] else None,
                    "humidity": data['aht20']['humidity'] if data['aht20'] else None
                },
                "bh1750": data['bh1750'] if data['bh1750'] is not None else None,
                "mpu6050": {
                    "accel": {
                        "x": data['mpu6050']['accel_x'] if data['mpu6050'] else None,
                        "y": data['mpu6050']['accel_y'] if data['mpu6050'] else None,
                        "z": data['mpu6050']['accel_z'] if data['mpu6050'] else None
                    },
                    "gyro": {
                        "x": data['mpu6050']['gyro_x'] if data['mpu6050'] else None,
                        "y": data['mpu6050']['gyro_y'] if data['mpu6050'] else None,
                        "z": data['mpu6050']['gyro_z'] if data['mpu6050'] else None
                    },
                    "temp": data['mpu6050']['temp'] if data['mpu6050'] else None
                },
                "ina219": {
                    "voltage":        data['ina219']['voltage']        if data['ina219'] else None,
                    "current":        data['ina219']['current']        if data['ina219'] else None,
                    "power":          data['ina219']['power']          if data['ina219'] else None,
                    "shunt_mv":       data['ina219']['shunt_mv']       if data['ina219'] else None,
                    "remaining_mah":  data['ina219']['remaining_mah']  if data['ina219'] else None,
                    "soc":            data['ina219']['soc']            if data['ina219'] else None,
                    "charging":       data['ina219']['charging']       if data['ina219'] else None
                },
                "sgp30": {
                    "eCO2": data['sgp30']['eCO2'] if data['sgp30'] else None,
                    "TVOC": data['sgp30']['TVOC'] if data['sgp30'] else None
                }
                
            }
 
            # 发布到MQTT（QoS 1确保至少送达一次）
            try:
                mqtt_client.publish(
                    topic=MQTT_CONFIG["topic"],
                    payload=json.dumps(mqtt_payload),
                    qos=1,
                    retain=True
                )
                print(f"[MQTT] 数据已发布至 {MQTT_CONFIG['topic']}")
            except Exception as e:
                print(f"[MQTT错误] 发布失败: {str(e)}")
 
            # 控制台输出数据-->Debug
            if data['tof']: print(f"[TOF] 距离: {data['tof']}mm")
            
            if data['bmp280']:
                print(f"[BMP280] 温度: {data['bmp280']['temperature']:.1f}°C | " +
                      f"气压: {data['bmp280']['pressure']:.1f}hPa")
            
            if data['aht20']:
                print(f"[AHT20] 温度: {data['aht20']['temperature']:.1f}°C | " +
                      f"湿度: {data['aht20']['humidity']:.1f}%")
            
            if data['bh1750'] is not None:
                print(f"[BH1750] 光照: {data['bh1750']:.2f}lx")
            
            if data['mpu6050']:
                m = data['mpu6050']
                print("[MPU6050]")
                print(f"  加速度: X={m['accel_x']:.2f}g Y={m['accel_y']:.2f}g Z={m['accel_z']:.2f}g")
                print(f"  陀螺仪: X={m['gyro_x']:.2f}°/s Y={m['gyro_y']:.2f}°/s Z={m['gyro_z']:.2f}°/s")
                print(f"  温度: {m['temp']:.2f}°C")
                
            if data['ina219']:
                i = data['ina219']
                print("[INA219]")
                print(f"  电压: {i['voltage']:.2f} V | 电流: {i['current']:.1f} A | 功率: {i['power']:.1f} W")
                print(f"  分流压降: {i['shunt_mv']:.2f} mV")
                print(f"  电量: {i['remaining_mah']:.2f} mAh ≈ {i['soc']:.1f}%")
                print(f"  充电器: {'已接入' if i['charging'] else '未接入'}")

            if data['sgp30']:
                print(f"[SGP30] eCO2: {data['sgp30']['eCO2']} ppm | TVOC: {data['sgp30']['TVOC']} ppb")

            time.sleep(1)  # MQTT发布频率-->不建议太快，会引起LVGL段错误
 
    except KeyboardInterrupt:
    	#mqtt_client.loop_stop()
        print("\n正在停止采集...")
    finally:
        # 清理资源
        if mqtt_client.is_connected():
            mqtt_client.disconnect()
        for name, bus in buses.items():
            if hasattr(bus, 'close') and callable(bus.close):
                bus.close()
        print("释放总线")
 
if __name__ == "__main__":
    main()
