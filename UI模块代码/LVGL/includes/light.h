#ifndef _LIGHT_UI_H_
#define _LIGHT_UI_H_

#include "lvgl/lvgl.h"

// 外部变量声明（如有其他模块使用这些状态）
extern bool B401_visible;
extern bool B402_visible;
extern bool B403_visible;

// 初始化与回调函数声明
void light_ui_init(void);

void B401_cb(lv_event_t * e);
void B402_cb(lv_event_t * e);
void B403_cb(lv_event_t * e);

#endif // _LIGHT_UI_H_

