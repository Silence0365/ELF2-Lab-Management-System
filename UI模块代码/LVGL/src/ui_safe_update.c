#include "ui_safe_update.h"
#include "lvgl/lvgl.h"
#include "ui/ui.h"
#include <stdlib.h>
#include <string.h>

#define MAX_LABELS 32
#define MAX_BARS 8
#define MAX_CHARTS 8
#define MAX_STATE_OBJS 16
#define MAX_ATTR_OBJS 32

// ================== Label ==================
typedef struct {
    lv_obj_t *label;
    char *pending_text;
    bool update_required;
} label_update_ctx_t;

static label_update_ctx_t label_ctxs[MAX_LABELS];

static void update_labels(void) {
    for (int i = 0; i < MAX_LABELS; i++) {
        if (label_ctxs[i].label && label_ctxs[i].update_required && label_ctxs[i].pending_text) {
            if (lv_obj_is_valid(label_ctxs[i].label)) {
                lv_label_set_text(label_ctxs[i].label, label_ctxs[i].pending_text);
            }
            free(label_ctxs[i].pending_text);
            label_ctxs[i].pending_text = NULL;
            label_ctxs[i].update_required = false;
        }
    }
}

void safe_ui_update(lv_obj_t *label, const char *text) {
    for (int i = 0; i < MAX_LABELS; i++) {
        if (label_ctxs[i].label == label) {
            if (label_ctxs[i].pending_text) free(label_ctxs[i].pending_text);
            label_ctxs[i].pending_text = strdup(text);
            label_ctxs[i].update_required = true;
            return;
        }
    }
}

// ================== Bar ==================
typedef struct {
    lv_obj_t *bar;
    int32_t value;
    bool update_required;
} bar_update_ctx_t;

static bar_update_ctx_t bar_ctxs[MAX_BARS];

static void update_bars(void) {
    for (int i = 0; i < MAX_BARS; i++) {
        if (bar_ctxs[i].bar && bar_ctxs[i].update_required) {
            if (lv_obj_is_valid(bar_ctxs[i].bar)) {
                lv_bar_set_value(bar_ctxs[i].bar, bar_ctxs[i].value, LV_ANIM_ON);
            }
            bar_ctxs[i].update_required = false;
        }
    }
}

void safe_ui_bar_update(lv_obj_t *bar, int32_t value) {
    for (int i = 0; i < MAX_BARS; i++) {
        if (bar_ctxs[i].bar == bar) {
            bar_ctxs[i].value = value;
            bar_ctxs[i].update_required = true;
            return;
        }
    }
}

// ================== Chart ==================
typedef struct {
    lv_obj_t *chart;
    lv_chart_series_t *series;
    lv_coord_t value;
    bool update_required;
} chart_update_ctx_t;

static chart_update_ctx_t chart_ctxs[MAX_CHARTS];

static void update_charts(void) {
    for (int i = 0; i < MAX_CHARTS; i++) {
        if (chart_ctxs[i].chart && chart_ctxs[i].update_required && chart_ctxs[i].series) {
            if (lv_obj_is_valid(chart_ctxs[i].chart)) {
                lv_chart_set_next_value(chart_ctxs[i].chart, chart_ctxs[i].series, chart_ctxs[i].value);
                lv_chart_refresh(chart_ctxs[i].chart);
            }
            chart_ctxs[i].update_required = false;
        }
    }
}

void safe_chart_add_point(lv_obj_t *chart, lv_chart_series_t *series, lv_coord_t value) {
    for (int i = 0; i < MAX_CHARTS; i++) {
        if (chart_ctxs[i].chart == chart && chart_ctxs[i].series == series) {
            chart_ctxs[i].value = value;
            chart_ctxs[i].update_required = true;
            return;
        }
    }
}

// ==================  对象安全更新 ==================
typedef struct {
    lv_obj_t *obj; 
    void (*update_fn)(lv_obj_t *, void *); 
    void *state_data;       
    bool update_required;
} ui_state_ctx_t;

static ui_state_ctx_t state_ctxs[MAX_STATE_OBJS];

void register_safe_state(lv_obj_t *obj, void (*update_fn)(lv_obj_t *, void *)) {
    for (int i = 0; i < MAX_STATE_OBJS; i++) {
        if (state_ctxs[i].obj == NULL) {
            state_ctxs[i].obj = obj;
            state_ctxs[i].update_fn = update_fn;
            state_ctxs[i].state_data = NULL;
            return;
        }
    }
}

void safe_ui_state_update(lv_obj_t *obj, void *new_state, size_t state_size) {
    for (int i = 0; i < MAX_STATE_OBJS; i++) {
        if (state_ctxs[i].obj == obj) {
            // 如果已有状态，比较新旧是否一致
            if (state_ctxs[i].state_data) {
                if (memcmp(state_ctxs[i].state_data, new_state, state_size) == 0) {
                    // 内容一致，不需要更新
                    return;
                }
                free(state_ctxs[i].state_data);  // 旧的不一致，释放
            }

            // 替换为新状态
            state_ctxs[i].state_data = malloc(state_size);
            if (!state_ctxs[i].state_data) return;
            memcpy(state_ctxs[i].state_data, new_state, state_size);
            state_ctxs[i].update_required = true;
            return;
        }
    }
}


static void update_ui_states(void) {
    for (int i = 0; i < MAX_STATE_OBJS; i++) {
        if (state_ctxs[i].obj && state_ctxs[i].update_required && state_ctxs[i].update_fn && state_ctxs[i].state_data) {
            if (lv_obj_is_valid(state_ctxs[i].obj)) {
                state_ctxs[i].update_fn(state_ctxs[i].obj, state_ctxs[i].state_data);
            }
            free(state_ctxs[i].state_data);
            state_ctxs[i].state_data = NULL;
            state_ctxs[i].update_required = false;
        }
    }
}
// ==================透明度安全更新 ==================
typedef struct {
    lv_obj_t *obj;
    lv_opa_t pending_opa;
    bool opa_update_required;

    bool pending_visible;
    bool visible_update_required;
} ui_attr_ctx_t;


static ui_attr_ctx_t attr_ctxs[MAX_ATTR_OBJS];

void register_safe_attr(lv_obj_t *obj) {
    for (int i = 0; i < MAX_ATTR_OBJS; i++) {
        if (attr_ctxs[i].obj == NULL) {
            attr_ctxs[i].obj = obj;
            return;
        }
    }
}

void safe_ui_set_opa(lv_obj_t *obj, lv_opa_t opa) {
    for (int i = 0; i < MAX_ATTR_OBJS; i++) {
        if (attr_ctxs[i].obj == obj) {
            if (attr_ctxs[i].opa_update_required && attr_ctxs[i].pending_opa == opa)
                return;  // 避免重复
            attr_ctxs[i].pending_opa = opa;
            attr_ctxs[i].opa_update_required = true;
            return;
        }
    }
}

void safe_ui_set_visible(lv_obj_t *obj, bool visible) {
    for (int i = 0; i < MAX_ATTR_OBJS; i++) {
        if (attr_ctxs[i].obj == obj) {
            if (attr_ctxs[i].visible_update_required && attr_ctxs[i].pending_visible == visible)
                return;
            attr_ctxs[i].pending_visible = visible;
            attr_ctxs[i].visible_update_required = true;
            return;
        }
    }
}

static void update_ui_attrs(void) {
    for (int i = 0; i < MAX_ATTR_OBJS; i++) {
        if (!attr_ctxs[i].obj || !lv_obj_is_valid(attr_ctxs[i].obj)) continue;

        if (attr_ctxs[i].opa_update_required) {
            lv_obj_set_style_opa(attr_ctxs[i].obj, attr_ctxs[i].pending_opa, LV_PART_MAIN);
            attr_ctxs[i].opa_update_required = false;
        }

        if (attr_ctxs[i].visible_update_required) {
            if (attr_ctxs[i].pending_visible)
                lv_obj_clear_flag(attr_ctxs[i].obj, LV_OBJ_FLAG_HIDDEN);
            else
                lv_obj_add_flag(attr_ctxs[i].obj, LV_OBJ_FLAG_HIDDEN);
            attr_ctxs[i].visible_update_required = false;
        }
    }
}

// ================== 注册接口 ==================
void register_safe_label(lv_obj_t *label) {
    for (int i = 0; i < MAX_LABELS; i++) {
        if (label_ctxs[i].label == NULL) {
            label_ctxs[i].label = label;
            return;
        }
    }
}

void register_safe_bar(lv_obj_t *bar) {
    for (int i = 0; i < MAX_BARS; i++) {
        if (bar_ctxs[i].bar == NULL) {
            bar_ctxs[i].bar = bar;
            return;
        }
    }
}

void register_safe_chart(lv_obj_t *chart, lv_chart_series_t *series) {
    for (int i = 0; i < MAX_CHARTS; i++) {
        if (chart_ctxs[i].chart == NULL) {
            chart_ctxs[i].chart = chart;
            chart_ctxs[i].series = series;
            return;
        }
    }
}

// ================== 定时器回调 ==================
static void ui_update_timer_cb(lv_timer_t *timer) {
    (void)timer;
    update_labels();
    update_bars();
    update_charts();
    update_ui_states();
    update_ui_attrs();
}	

// ================== 初始化 ==================
void safe_ui_update_init(void) {
    memset(label_ctxs, 0, sizeof(label_ctxs));
    memset(bar_ctxs, 0, sizeof(bar_ctxs));
    memset(chart_ctxs, 0, sizeof(chart_ctxs));
    memset(state_ctxs, 0, sizeof(state_ctxs));
    lv_timer_create(ui_update_timer_cb, 50, NULL);  // 每50ms刷新一次 UI
} 
