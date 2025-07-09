#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <pthread.h>
#include "lvgl/lvgl.h"
#include "ui/ui.h"

// ========== 安全隐藏回调 ==========
static void animation_obj_cb(lv_timer_t * timer) {
    lv_obj_t * obj = (lv_obj_t *)lv_timer_get_user_data(timer);
    if (obj && lv_obj_is_valid(obj)) {
        lv_obj_add_flag(obj, LV_OBJ_FLAG_HIDDEN);
    }
    lv_timer_del(timer);
}

// ========== Charging 动画异步函数 ==========
static void charging_anim_safe(void *param)
{
    disappear_Animation(ui_uncharge, 0);

    lv_obj_set_style_opa(ui_charing, LV_OPA_TRANSP, LV_PART_MAIN);
    lv_obj_set_style_opa(ui_lighting, LV_OPA_TRANSP, LV_PART_MAIN);
    lv_obj_clear_flag(ui_charing, LV_OBJ_FLAG_HIDDEN);
    lv_obj_clear_flag(ui_lighting, LV_OBJ_FLAG_HIDDEN);

    appear_Animation(ui_charing, 0);
    appear_Animation(ui_lighting, 0);

    lv_timer_t * timer0 = lv_timer_create(animation_obj_cb, 500, ui_uncharge);
    lv_timer_set_repeat_count(timer0, 1);
}

void ui_Charging() {
    lv_async_call(charging_anim_safe, NULL);  // 异步调度动画，安全
}

// ========== UnCharging 动画异步函数 ==========
static void uncharging_anim_safe(void *param)
{
    disappear_Animation(ui_charing, 0);
    disappear_Animation(ui_lighting, 0);

    lv_obj_set_style_opa(ui_uncharge, LV_OPA_TRANSP, LV_PART_MAIN);
    lv_obj_clear_flag(ui_uncharge, LV_OBJ_FLAG_HIDDEN);
    appear_Animation(ui_uncharge, 0);

    lv_timer_t * timer1 = lv_timer_create(animation_obj_cb, 500, ui_charing);
    lv_timer_t * timer2 = lv_timer_create(animation_obj_cb, 500, ui_lighting);
    lv_timer_set_repeat_count(timer1, 1);
    lv_timer_set_repeat_count(timer2, 1);
}

void ui_UnCharging() {
    lv_async_call(uncharging_anim_safe, NULL);  // 异步调度动画
}

// ========== 电量图标位置更新 ==========
static void soc_safe_update(void *param)
{
    int battery_percentage = *(int *)param;

    int x_position = -35 + (1 + 35) * battery_percentage / 100;
    lv_obj_set_x(ui_charing, x_position);
    lv_obj_set_x(ui_uncharge, x_position);

    free(param);  // 释放传入的堆变量
}

void bettery_soc(int battery_percentage)
{
    int *arg = malloc(sizeof(int));
    if (arg) {
        *arg = battery_percentage;
        lv_async_call(soc_safe_update, arg);  // 异步位置更新
    }
}

