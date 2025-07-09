#include "lvgl/lvgl.h"
#include "ui/ui.h"
#include "mqtt_connect.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// 状态变量定义
static int32_t cur_angle = 0;
static int32_t cur_speed = 0;
static int32_t target_speed = 0;
int32_t val = 0;
static bool click_locked = false;

static lv_timer_t *rotate_timer = NULL;
static lv_timer_t *auto_close_timer = NULL;

#define MAX_ACCEL 1
#define THROTTLE_INTERVAL_MS 50  // 发送间隔时间--防止发送过快
static uint32_t last_send_ms = 0;

// MQTT结构体
typedef struct {
    char msg[64];
} mqtt_async_ctx_t;

// MQTT 发布函数--异步
static void safe_mqtt_publish(void *param) {
    mqtt_async_ctx_t *ctx = (mqtt_async_ctx_t *)param;
    mqtt_publish_control_ack(ctx->msg);
    free(ctx);
}

// 定时器回调--控制加减速 + 更新角度
static void rotate_timer_cb(lv_timer_t *timer) {
    lv_obj_t *img = (lv_obj_t *)lv_timer_get_user_data(timer);

    if (cur_speed < target_speed) cur_speed += MAX_ACCEL;
    else if (cur_speed > target_speed) cur_speed -= MAX_ACCEL;

    cur_angle += cur_speed;
    cur_angle %= 3600;
    lv_img_set_angle(img, cur_angle);
}

// 动画恢复定时器
static void resume_timer_cb(lv_timer_t *timer) {
    if (rotate_timer) lv_timer_resume(rotate_timer);
    lv_timer_del(timer);
}

// 转速调节slider收回动画
static void auto_close_timer_cb(lv_timer_t *timer) {
    fanbardisappear_Animation(ui_fan_speed, 0);
    click_locked = false;

    if (val == 0) {
        if (rotate_timer) lv_timer_pause(rotate_timer);
        rotateback_Animation(ui_fan, 0);
        lv_timer_create(resume_timer_cb, 1000, NULL);
    }

    lv_timer_del(timer);
    auto_close_timer = NULL;
}

// 滑动条滑动事件
void ui_event_animation_fan(lv_event_t *e) {
    if (lv_event_get_code(e) == LV_EVENT_VALUE_CHANGED) {
        val = lv_slider_get_value(lv_event_get_target(e));
        target_speed = val * 2;

        uint32_t now = lv_tick_get();
        if (now - last_send_ms >= THROTTLE_INTERVAL_MS || last_send_ms == 0) {
            last_send_ms = now;

            mqtt_async_ctx_t *ctx = malloc(sizeof(mqtt_async_ctx_t));
            if (ctx) {
                snprintf(ctx->msg, sizeof(ctx->msg), "{\"speed\":%d}", val);
                lv_async_call(safe_mqtt_publish, ctx);
            }
        }

        if (auto_close_timer) {
            lv_timer_reset(auto_close_timer);
        } else {
            auto_close_timer = lv_timer_create(auto_close_timer_cb, 5000, NULL);
        }
    }
}

// 控制条点击事件：显示控制条并播放动画
void ui_appear_speed_control_bar(lv_event_t *e) {
    if (lv_event_get_code(e) == LV_EVENT_CLICKED) {
        if (click_locked) return;
        click_locked = true;

        if (val == 0) {
            if (rotate_timer) lv_timer_pause(rotate_timer);
            rotate_Animation(ui_fan, 0);
            fanbar_Animation(ui_fan_speed, 0);
            lv_timer_create(resume_timer_cb, 1000, NULL);
        } else {
            fanbar_Animation(ui_fan_speed, 0);
        }

        if (auto_close_timer) {
            lv_timer_reset(auto_close_timer);
        } else {
            auto_close_timer = lv_timer_create(auto_close_timer_cb, 5000, NULL);
        }
    }
}

// 初始化
void start_rotation_with_acceleration() {
    lv_obj_add_event_cb(ui_fan, ui_appear_speed_control_bar, LV_EVENT_ALL, NULL);
    lv_obj_add_event_cb(ui_fan_speed, ui_event_animation_fan, LV_EVENT_VALUE_CHANGED, NULL);
    lv_img_set_pivot(ui_fan, 40 / 2, 40 / 2);

    if (!rotate_timer) {
        rotate_timer = lv_timer_create(rotate_timer_cb, 16, ui_fan);
    }
} 
