#include "mqtt_data.h"
#include "ui/ui.h"              // UI 对象声明
#include "ui/ui.h" 
#include "ui_safe_update.h"     // 异步 UI 更新接口
#include <MQTTClient.h>
#include <cJSON.h>
#include <stdio.h>
#include <string.h>
#include "weather_chart.h"
#include "id_vertify.h"
#include "bettery.h"

int tof_flag = 0;
int card1_flag = 0;
int card2_flag = 0;
extern val;

// 回调函数：当接收到 MQTT 消息时被调用
int messageArrived(void *context, char *topicName, int topicLen, MQTTClient_message *message) 
{
    char *payload = (char *)malloc(message->payloadlen + 1);
    if (!payload) {
        printf("[MQTT] 内存分配失败!\n");
        goto cleanup;
    }
    memcpy(payload, message->payload, message->payloadlen);
    payload[message->payloadlen] = '\0';  // 添加结尾符

    printf("[MQTT] 收到消息: %s\n", payload);

    cJSON *root = cJSON_Parse(payload);
    if (!root) 
    {
        printf("[MQTT] JSON 解析失败!\n");
        free(payload);
        goto cleanup;
    }
    //topic:"AI/Identify"
    if (strcmp(topicName, "AI/Identify") == 0) 
    {
        cJSON *card1_num = cJSON_GetObjectItem(root, "card1_num");
        cJSON *card2_num = cJSON_GetObjectItem(root, "card2_num");
        if (card1_num && cJSON_IsNumber(card1_num) && card2_num && cJSON_IsNumber(card2_num)) 
        {
            card1_flag = card1_num->valueint;  // ✅ 存入全局变量
            card2_flag = card2_num->valueint;
            char buf1[64], buf2[64];
            snprintf(buf1, sizeof(buf1), "%d", card1_num->valueint);
            snprintf(buf2, sizeof(buf2), "%d", card2_num->valueint);
            ID_Vertifying();
            

            //safe_ui_update(ui_Label12, buf1);  // 更新 label12
            //safe_ui_update(ui_Label13, buf2);  // 更新 label13
        }
    }
    //topic:"sensors/data"
    else if (strcmp(topicName, "sensors/data") == 0) 
    {
        // TOF
        cJSON *tof = cJSON_GetObjectItem(root, "tof");
        if (tof && cJSON_IsNumber(tof)) 
        {
            char buf[64];
            snprintf(buf, sizeof(buf), "%d mm", tof->valueint);
            safe_ui_update(ui_Label_Distance, buf);
            tof_flag = tof->valueint;
            TOF_Vertifying();
        }

        // bmp280.temperature&pressure
        cJSON *bmp280 = cJSON_GetObjectItem(root, "bmp280");
        if (bmp280) 
        {
            // ① 温度
            cJSON *temp = cJSON_GetObjectItem(bmp280, "temperature");
            if (temp && cJSON_IsNumber(temp)) 
            {
                char buf[64];
                snprintf(buf, sizeof(buf), "%.2f ℃", temp->valuedouble);
                //safe_ui_update(ui_Label11, buf);
            }

            // ② 大气压
            cJSON *pressure = cJSON_GetObjectItem(bmp280, "pressure");
            if (pressure && cJSON_IsNumber(pressure)) 
            {
                char buf[64];
                snprintf(buf, sizeof(buf), "%.0f hPa", pressure->valuedouble);
                safe_ui_update(ui_Label36, buf);
            }
        }
        // aht20.humidity
        cJSON *aht20 = cJSON_GetObjectItem(root, "aht20");
        if (aht20) 
        {
            // 温度
            cJSON *temp = cJSON_GetObjectItem(aht20, "temperature");
            if (temp && cJSON_IsNumber(temp)) 
            {
                char buf[64];
                snprintf(buf, sizeof(buf), "%.0f ℃", temp->valuedouble);
                safe_ui_update(ui_Label31, buf); 
                
            }

            // 湿度
            cJSON *humi = cJSON_GetObjectItem(aht20, "humidity");
            if (humi && cJSON_IsNumber(humi)) 
            {
                char buf[64];
                snprintf(buf, sizeof(buf), "%.0f %%", humi->valuedouble);
                safe_ui_update(ui_Label29, buf);
                //safe_chart_add_point(ui_Chart1, humi_series, (lv_coord_t)(humi->valuedouble));
            }
        }

        // bh1750
        cJSON *illum = cJSON_GetObjectItem(root, "bh1750");
        if (illum && cJSON_IsNumber(illum)) 
        {
            char buf[64];
            snprintf(buf, sizeof(buf), "%.0f lx", illum->valuedouble);
            safe_ui_update(ui_Label37, buf);
        }

        // mpu6050
        cJSON *mpu = cJSON_GetObjectItem(root, "mpu6050");
        if (mpu) 
        {
            // mpu6050.temp
            cJSON *temp = cJSON_GetObjectItem(mpu, "temp");
            if (temp && cJSON_IsNumber(temp)) 
            {
                char buf[64];
                snprintf(buf, sizeof(buf), "MPU温度: %.2f ℃", temp->valuedouble);
                //safe_ui_update(ui_Label7, buf);
            }

            // mpu6050.accel
            cJSON *accel = cJSON_GetObjectItem(mpu, "accel");
            if (accel) 
            {
                cJSON *x = cJSON_GetObjectItem(accel, "x");
                cJSON *y = cJSON_GetObjectItem(accel, "y");
                cJSON *z = cJSON_GetObjectItem(accel, "z");
                if (x && y && z && cJSON_IsNumber(x) && cJSON_IsNumber(y) && cJSON_IsNumber(z)) 
                {
                    char buf[128];
                    snprintf(buf, sizeof(buf), "加速度 x:%.2f y:%.2f z:%.2f", x->valuedouble, y->valuedouble, z->valuedouble);
                    //safe_ui_update(ui_Label15, buf);
                }
            }

            // mpu6050.gyro
            cJSON *gyro = cJSON_GetObjectItem(mpu, "gyro");
            if (gyro) 
            {
                cJSON *x = cJSON_GetObjectItem(gyro, "x");
                cJSON *y = cJSON_GetObjectItem(gyro, "y");
                cJSON *z = cJSON_GetObjectItem(gyro, "z");
                if (x && y && z && cJSON_IsNumber(x) && cJSON_IsNumber(y) && cJSON_IsNumber(z)) 
                {
                    char buf[128];
                    snprintf(buf, sizeof(buf), "陀螺仪 x:%.2f y:%.2f z:%.2f", x->valuedouble, y->valuedouble, z->valuedouble);
                    //safe_ui_update(ui_Label16, buf);
                }
            }
        }
    
        // ina219
        cJSON *ina219 = cJSON_GetObjectItem(root, "ina219");
        if (ina219) 
        { 
            // 电压
            cJSON *voltage = cJSON_GetObjectItem(ina219, "voltage");
            if (voltage && cJSON_IsNumber(voltage)) 
            {
                char buf[64];
                snprintf(buf, sizeof(buf), "%.2f V", voltage->valuedouble);
                safe_ui_update(ui_Label_voltage, buf);

                lv_coord_t voltage_chart = (lv_coord_t)(voltage->valuedouble * 10);
                safe_chart_add_point(ui_Chart_VIP, Voltage, voltage_chart);
            }

            // 电流
            cJSON *current = cJSON_GetObjectItem(ina219, "current");
            if (current && cJSON_IsNumber(current)) 
            {
                char buf[64];
                snprintf(buf, sizeof(buf), "%.2f A", current->valuedouble);
                safe_ui_update(ui_Label_current, buf);
                lv_coord_t current_chart = (lv_coord_t)(current->valuedouble * 100);
                safe_chart_add_point(ui_Chart_VIP, Current, current_chart);
            }

            // 功率
            cJSON *power = cJSON_GetObjectItem(ina219, "power");
            if (power && cJSON_IsNumber(power)) 
            {
                char buf[64];
                snprintf(buf, sizeof(buf), "%.2f W", power->valuedouble);
                safe_ui_update(ui_Label_power, buf);
                lv_coord_t power_chart = (lv_coord_t)(power->valuedouble * 10);
                safe_chart_add_point(ui_Chart_VIP, Power, power_chart);
            }

            // SOC
            cJSON *soc = cJSON_GetObjectItem(ina219, "soc");
            if (soc && cJSON_IsNumber(soc)) 
            {
                char buf[64];
                snprintf(buf, sizeof(buf), "电池状态: %.2f %%", soc->valuedouble);
                int battery_percentage = (int)(soc->valuedouble + 0.5);  // 四舍五入
                bettery_soc(battery_percentage);
                //safe_ui_update(ui_Label_SOC, buf);
            }

            // charge_status
            static bool last_charging_state = -1;
            cJSON *charging = cJSON_GetObjectItem(ina219, "charging");
            if (charging && cJSON_IsBool(charging)) 
            {
                bool is_charging = cJSON_IsTrue(charging);

                // 只有状态变化时才触发对应函数
                if (is_charging != last_charging_state) 
                {
                    last_charging_state = is_charging;  // 更新状态缓存

                    if (is_charging) {
                        ui_Charging();
                    } else {
                        ui_UnCharging();
                    }
                }
            }

        }

        // SGP30 空气质量
        cJSON *sgp30 = cJSON_GetObjectItem(root, "sgp30");
        if (sgp30) 
        { 
            // eCO2
            cJSON *eco2 = cJSON_GetObjectItem(sgp30, "eCO2");
            if (eco2 && cJSON_IsNumber(eco2)) 
            {
                char buf[64];
                snprintf(buf, sizeof(buf), "%.0f ppm", eco2->valuedouble);
                safe_ui_update(ui_Label40, buf);
                safe_ui_bar_update(ui_Slider1, (int32_t)(eco2->valuedouble));
            }

            // TVOC
            cJSON *tvoc = cJSON_GetObjectItem(sgp30, "TVOC");
            if (tvoc && cJSON_IsNumber(tvoc)) 
            {
                char buf[64];
                snprintf(buf, sizeof(buf), "%.0f ppb", tvoc->valuedouble);
                safe_ui_update(ui_Label41, buf);
                safe_ui_bar_update(ui_Slider4, (int32_t)(tvoc->valuedouble));
            }
        }
    }
    
    //topic:"scanner/qr"
    else if (strcmp(topicName, "scanner/qr") == 0) 
    {
        cJSON *root = cJSON_Parse(payload);
        if (!root) 
        {
            printf(" JSON 解析失败\n");
            return;
        }

        cJSON *name  = cJSON_GetObjectItem(root, "name");
        cJSON *model = cJSON_GetObjectItem(root, "model");
        cJSON *price = cJSON_GetObjectItem(root, "price");

        if (cJSON_IsString(name) && cJSON_IsString(model) && cJSON_IsNumber(price)) 
        {
            // 格式化为你要求的字符串格式（去掉date字段）
            char result[256];
            snprintf(result, sizeof(result),
                    "\"%s\", \"%s\", %d",  // 不再使用date
                    name->valuestring,
                    model->valuestring,
                    price->valueint);

            // 更新 ui_Label1（线程安全封装）
            safe_ui_update(ui_Label_partinfo, result);
        }
    }

    else if (strcmp(topicName, "ack/LVGL") == 0) 
    {
        const char* light_keys[] = {
            "B401_Light", "B402_Light", "B403_Light", "B404_Light", "B405_Light", "Relay"
        };

        for (int i = 0; i < 6; i++) 
        {
            cJSON *item = cJSON_GetObjectItem(root, light_keys[i]);
            if (item && cJSON_IsString(item)) 
            {
                int is_on = strcmp(item->valuestring, "ON") == 0;
                lv_opa_t opa = is_on ? LV_OPA_COVER : LV_OPA_TRANSP;

                if (strcmp(light_keys[i], "B401_Light") == 0) 
                {
                    safe_ui_set_opa(ui_Lab_B401, opa);
                    printf("%s B401 灯\n", is_on ? "打开" : "关闭");
                } 
                else if (strcmp(light_keys[i], "B402_Light") == 0) 
                {
                    safe_ui_set_opa(ui_Lab_B402, opa);
                    printf("%s B402 灯\n", is_on ? "打开" : "关闭");
                } 
                else if (strcmp(light_keys[i], "B403_Light") == 0) 
                {
                    safe_ui_set_opa(ui_Lab_B403, opa);
                    printf("%s B403 灯\n", is_on ? "打开" : "关闭");
                } 
                else if (strcmp(light_keys[i], "B404_Light") == 0) 
                {
                    safe_ui_set_opa(ui_Lab_B404, opa);
                    printf("%s B404 灯\n", is_on ? "打开" : "关闭");
                } 
                else if (strcmp(light_keys[i], "B405_Light") == 0) 
                {
                    safe_ui_set_opa(ui_Lab_Cateen, opa);
                    printf("%s B405 灯\n", is_on ? "打开" : "关闭");
                } 
                else if (strcmp(light_keys[i], "Relay") == 0) 
                {
                    printf("%s 继电器\n", is_on ? "打开" : "关闭");
                    // 无需透明度操作
                }
            }
        }
        cJSON *speed_item = cJSON_GetObjectItem(root, "Fan");
        if (speed_item && cJSON_IsNumber(speed_item)) 
        {
    		int received_speed = speed_item->valueint;
    		val = received_speed;               // 同步 UI 滑动条值
    		safe_ui_bar_update(ui_fan_speed, val);  // ✅ 安全更新滑动条（带动画）
    		//printf("同步风扇速度：%d\n", received_speed);
    	}
    }



    // 处理主题 network/status
    else if (strcmp(topicName, "network/status") == 0) 
    {
        cJSON *wifi = cJSON_GetObjectItem(root, "WIFI");
        cJSON *lte  = cJSON_GetObjectItem(root, "4G");

        // 处理 WIFI 状态
        if (wifi && cJSON_IsString(wifi)) {
            if (strcmp(wifi->valuestring, "OK") == 0) {
                // ✅ WIFI 正常
                printf("WIFI 状态: OK\n");
                safe_ui_set_visible(ui_Icon_WIFI_connect, true);
                safe_ui_set_visible(ui_Icon_WIFI_disconnect, false);
            } else {
                // ❌ WIFI 异常
                printf("WIFI 状态: FAIL\n");
                safe_ui_set_visible(ui_Icon_WIFI_connect, false);
                safe_ui_set_visible(ui_Icon_WIFI_disconnect, true);
            }
        }

        // 处理 4G 状态
        if (lte && cJSON_IsString(lte)) {
            if (strcmp(lte->valuestring, "OK") == 0) {
                // ✅ 4G 正常
                printf("4G 状态: OK\n");
                safe_ui_set_visible(ui_Icon_4G, true);
            } else {
                // ❌ 4G 异常
                printf("4G 状态: FAIL\n");
                safe_ui_set_visible(ui_Icon_4G, false);
            }
        }
    }




        cJSON_Delete(root);
 




    // Bar 进度条映射（比例转换举例）

    cleanup:
        //cJSON_Delete(root);
        MQTTClient_freeMessage(&message);
        MQTTClient_free(topicName);
        return 1;
}



