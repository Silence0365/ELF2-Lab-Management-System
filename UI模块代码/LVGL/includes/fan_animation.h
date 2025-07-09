#ifndef FAN_ANIMATION_H
#define FAN_ANIMATION_H

#include "lvgl/lvgl.h"

extern int32_t val = 0;

// 启动图像旋转（带加减速过渡）
void start_rotation_with_acceleration();

// 滑动条事件回调函数，SquareLine Studio 中 Slider2 应绑定这个函数
void ui_event_animation_fan(lv_event_t *e);

#endif // FAN_ANIMATION_H

