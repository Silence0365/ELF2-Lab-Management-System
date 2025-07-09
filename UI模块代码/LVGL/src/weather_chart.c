#include "ui/ui.h"  

//后复用为电池状态监测曲线图
extern lv_obj_t * ui_Chart_VIP;
lv_chart_series_t *Voltage;
lv_chart_series_t *Current;
lv_chart_series_t *Power;

void create_chart_weather(void) {
    Voltage = lv_chart_add_series(ui_Chart_VIP, lv_color_hex(0x2b5ecd), LV_CHART_AXIS_PRIMARY_Y);
    Current = lv_chart_add_series(ui_Chart_VIP, lv_color_hex(0x58d441), LV_CHART_AXIS_SECONDARY_Y);
    Power = lv_chart_add_series(ui_Chart_VIP, lv_color_hex(0xa84490), LV_CHART_AXIS_SECONDARY_Y);
}
