#ifndef UI_SAFE_UPDATE_H
#define UI_SAFE_UPDATE_H

#include "lvgl/lvgl.h"

// ================== 初始化 ==================
void safe_ui_update_init(void);  // 启动后台刷新定时器

// ================== 文本标签更新 ==================
void register_safe_label(lv_obj_t *label);
void safe_ui_update(lv_obj_t *label, const char *text);

// ================== 进度条更新 ==================
void register_safe_bar(lv_obj_t *bar);
void safe_ui_bar_update(lv_obj_t *bar, int32_t value);

// ================== 图表更新 ==================
void register_safe_chart(lv_obj_t *chart, lv_chart_series_t *series);
void safe_chart_add_point(lv_obj_t *chart, lv_chart_series_t *series, lv_coord_t value);

// ================== 状态结构更新 ==================
void register_safe_state(lv_obj_t *obj, void (*update_fn)(lv_obj_t *, void *));
void safe_ui_state_update(lv_obj_t *obj, void *new_state, size_t state_size);

// ================== 属性通用更新 ==================
void register_safe_attr(lv_obj_t *obj);
void safe_ui_set_opa(lv_obj_t *obj, lv_opa_t opa);
void safe_ui_set_visible(lv_obj_t *obj, bool visible);

#endif  // UI_SAFE_UPDATE_H

