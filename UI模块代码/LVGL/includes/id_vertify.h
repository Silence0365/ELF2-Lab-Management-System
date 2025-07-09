#ifndef ID_VERIFY_H
#define ID_VERIFY_H

#include <stdlib.h>
#include "lvgl.h"   // 引入 LVGL 以支持 lv_timer_t 类型

#ifdef __cplusplus
extern "C" {
#endif

// 初始化动画系统（如需要提前启动可在主程序调用）
void TOF_Vertifying(void);
void ID_Vertifying(void);
// 动画定时器任务函数（一般无需主动调用）
void yolo_animation_task(lv_timer_t * t);

#ifdef __cplusplus
} // extern "C"
#endif

#endif // ID_VERIFY_H

