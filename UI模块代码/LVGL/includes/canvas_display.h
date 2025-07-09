// canvas_display.h

#ifndef CANVAS_DISPLAY_H
#define CANVAS_DISPLAY_H

#include <stdint.h>
#include <pthread.h> 
extern pthread_mutex_t canvas_mutex;
// 启动 canvas 显示功能（在独立线程中调用）
void canvas_init(void);
void* canvas_display_thread(void *arg);

#endif // CANVAS_DISPLAY_H

