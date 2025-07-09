#ifndef UI_BUTTON5_HANDLER_H
#define UI_BUTTON5_HANDLER_H

#include "lvgl/lvgl.h"

// 初始化 Button5 的事件回调绑定
void ui_Button5_init(void);

// Button5 的事件处理函数（淡出 + 隐藏）
void ui_manage_system_init();

void ui_login (lv_event_t * e);

void ui_Button3_appear(lv_event_t * e);
// 用于在动画结束后隐藏对象的定时器回调
//（如果不希望外部调用，也可以将其改为 static 放在 .c 内）
void hide_obj_cb(lv_timer_t * timer);

#endif // UI_BUTTON5_HANDLER_H

