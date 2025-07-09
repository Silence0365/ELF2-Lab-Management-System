#ifndef WEATHER_CHART_H
#define WEATHER_CHART_H

#include "ui/ui.h"  


// 全局可访问的 series 指针

extern lv_chart_series_t *Voltage;
extern lv_chart_series_t *Current;
extern lv_chart_series_t *Power;
extern lv_obj_t * ui_Chart1;
// 初始化曲线（需在 ui_Chart1 创建后调用）
void create_chart_weather(void);

#endif // WEATHER_CHART_H

