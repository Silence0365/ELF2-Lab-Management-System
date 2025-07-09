#ifndef CHARGER_UI_H
#define CHARGER_UI_H

#include "lvgl/lvgl.h"

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @brief 初始化充电模块相关事件回调绑定
 * 应在 UI 构建完成后调用，用于绑定 Bottom1 / Bottom2 的事件处理函数
 */
void charger_init(void);

/**
 * @brief 点击 ui_Bottom1 时触发：执行充电 UI 切换逻辑
 *
 * @param e LVGL 事件指针
 */
void ui_Charging();

/**
 * @brief 点击 ui_Bottom2 时触发：执行取消充电 UI 切换逻辑
 *
 * @param e LVGL 事件指针
 */
void ui_UnCharging();

/**
 * @brief 动画结束后自动隐藏对象的定时器回调
 *
 * @param timer LVGL 定时器对象，user_data 应为 lv_obj_t*
 */
void animation_obj_cb(lv_timer_t * timer);

void bettery_soc(int battery_percentage);

#ifdef __cplusplus
} /* extern "C" */
#endif

#endif // CHARGER_UI_H

