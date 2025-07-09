#include "lvgl/lvgl.h"
#include "lvgl/demos/lv_demos.h"
#include <unistd.h>
#include <pthread.h>
#include <stdlib.h>
#include <time.h>
#include <stdio.h>
#include <sys/time.h>
#include "ui/ui.h"
#include "mqtt_connect.h" 
#include "mqtt_data.h"
#include <sys/time.h>
#include "canvas_display.h"
#include "weather_chart.h"
#include "fan_animation.h"
#include "light.h"

static lv_timer_t *time_updater; // 时间更新器
extern lv_obj_t *ui_weathershow;

/* 时间更新函数 */
void update_system_time() {
    time_t rawtime;
    struct tm *timeinfo;
    char buffer[9];  // HH:MM:SS\0
    char date_buf[32];  // YYYY-MM-DD
    char week_buf[16];  // 星期X

    time(&rawtime);
    timeinfo = localtime(&rawtime);
    strftime(buffer, sizeof(buffer), "%H:%M:%S", timeinfo);

    /* 格式化日期：YYYY-MM-DD */
    strftime(date_buf, sizeof(date_buf), "%Y年%m月%d日", timeinfo);

    /* 格式化星期*/
    const char *weekdays[] = {"日", "一", "二", "三", "四", "五", "六"};
    snprintf(week_buf, sizeof(week_buf), "星期%s", weekdays[timeinfo->tm_wday]);

    // 安全更新接口
    safe_ui_update(ui_Label_time, buffer);
    safe_ui_update(ui_Label_date, date_buf);
    safe_ui_update(ui_Label_week, week_buf);
    
}

/* MQTT客户端线程启动函数 */
void* mqtt_thread(void* arg) {
    mqtt_client_start();
    return NULL;
}

uint32_t lv_os_get_idle_percent(void) {
    return 100;
}

int main(void)
{
    lv_init();

    // 初始化显示驱动
    /*Linux frame buffer device init*/
    lv_display_t * disp = lv_linux_fbdev_create();
    lv_linux_fbdev_set_file(disp, "/dev/fb0");
    
    // 初始化输入设备
    /* 如添加如下两行，对应前面屏幕适配后的设备节点 /dev/input/event2 */
    lv_indev_t * touch;
    touch = lv_evdev_create(LV_INDEV_TYPE_POINTER,"/dev/input/event1");
    

    ui_init();//初始化ui界面
    ui_manage_system_init();//初始化元件管理系统
    light_ui_init();//初始化灯光控制页面
    
    // 启动 YOLO画面显示线程
    canvas_init();//创建canvas画布
    pthread_t canvas_tid;
    pthread_create(&canvas_tid, NULL, canvas_display_thread, NULL);

    // 启动时间更新器
    time_updater = lv_timer_create(update_system_time, 1000, NULL); // 每秒更新一次
    lv_timer_set_repeat_count(time_updater, -1);  // 无限重复

    // 启动 MQTT 线程
    pthread_t mqtt_tid;
    pthread_create(&mqtt_tid, NULL, mqtt_thread, NULL);  // 启动mqtt线程
    
    //创建天气图表
    create_chart_weather();

    //风扇动画
    start_rotation_with_acceleration();
    

    //安全更新注册
    safe_ui_update_init();  // 启动定时器 + 初始化上下文
    register_safe_label(ui_Label_time);
    register_safe_label(ui_Label_date);
    register_safe_label(ui_Label_week);
    register_safe_label(ui_Label_Distance);
    register_safe_label(ui_Label36);
    register_safe_label(ui_Label31);
    register_safe_label(ui_Label29);
    register_safe_label(ui_Label37);
    register_safe_label(ui_Label40);
    register_safe_label(ui_Label41);
    register_safe_label(ui_Label_voltage);
    register_safe_label(ui_Label_current);
    register_safe_label(ui_Label_power);
    register_safe_label(ui_Label_partinfo);
    register_safe_label(ui_Label_Name);
    register_safe_label(ui_Label_Charact);
    register_safe_label(ui_Label_Number);
    register_safe_label(ui_Label_State);
    register_safe_bar(ui_Slider1);
    register_safe_bar(ui_Slider4);
    register_safe_bar(ui_fan_speed);
    register_safe_chart(ui_Chart_VIP, Voltage);
    register_safe_chart(ui_Chart_VIP, Current);
    register_safe_chart(ui_Chart_VIP, Power);
    register_safe_attr(ui_Icon_WIFI_disconnect);
    register_safe_attr(ui_Icon_WIFI_connect);
    register_safe_attr(ui_Icon_4G);
    register_safe_attr(ui_Lab_B401);
    register_safe_attr(ui_Lab_B402);
    register_safe_attr(ui_Lab_B403);
    register_safe_attr(ui_Lab_B404);
    register_safe_attr(ui_Lab_Cateen);

    /*Handle LVGL tasks*/
    while(1) {
        lv_timer_handler();
        usleep(5000);
    }

    return 0;
}


