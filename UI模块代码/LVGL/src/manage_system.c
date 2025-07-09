#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <pthread.h>
#include "lvgl/lvgl.h"
#include "lvgl/examples/lv_examples.h"
#include "lvgl/demos/lv_demos.h"
#include "ui/ui.h"

//动画定时器
static void hide_obj_cb(lv_timer_t * timer) {
    lv_obj_t * obj = (lv_obj_t *)lv_timer_get_user_data(timer);
    lv_obj_add_flag(obj, LV_OBJ_FLAG_HIDDEN);
    lv_timer_del(timer);  
}

static void scan_obj_cb(lv_timer_t * timer) {
    lv_obj_t * obj = (lv_obj_t *)lv_timer_get_user_data(timer);
    lv_obj_add_flag(obj, LV_OBJ_FLAG_HIDDEN);
    lv_timer_del(timer);  
}

static void scan_exit_obj_cb(lv_timer_t * timer) {
    lv_obj_t * obj = (lv_obj_t *)lv_timer_get_user_data(timer);
    lv_obj_add_flag(obj, LV_OBJ_FLAG_HIDDEN);
    lv_timer_del(timer);  
}

//密码设置
static const char * correct_password = "0365";  // 正确密码

//元件数量最大值
#define MAX_COMPONENTS 100

//元件数量结构体
typedef struct {
    char name[32];      // 名称
    char model[32];     // 型号
    int quantity;       // 数量
    char date[20];      // 时间字符串，如 "2025-05-23"
} ComponentInfo;

//变量定义
static ComponentInfo component_list[MAX_COMPONENTS];
static int component_count = 0;
static lv_obj_t *component_table = NULL;
static int dropdown_quantity = 0;
static int current_selected_row = -1;  

//声明
void ui_Scaning_disappear(lv_event_t * e);
void ui_Scaning_appear(lv_event_t * e);
void ui_login (lv_event_t * e);
void init_component_table(lv_obj_t *parent);
void add_component(const char *name, const char *model, int quantity);
void component_table_event_cb(lv_event_t * e);
void dropdown_event_cb(lv_event_t * e);
void ui_output_appear();
void ui_output_disappear(lv_event_t * e);
void add_component_from_label(lv_obj_t *label);
void ui_out_callback_cb(lv_event_t * e);
void ui_Scaning_exit (lv_event_t * e);
void ui_output_disappear_exit(lv_event_t * e);

//初始化
void ui_manage_system_init()
{
    lv_obj_add_event_cb(ui_scan_confirm,ui_Scaning_disappear , LV_EVENT_ALL, NULL);
    lv_obj_add_event_cb(ui_scan_exit,ui_Scaning_exit , LV_EVENT_ALL, NULL);
    lv_obj_add_event_cb(ui_add_button,ui_Scaning_appear , LV_EVENT_ALL, NULL);
    lv_obj_add_event_cb(ui_Keyboard,ui_login , LV_EVENT_ALL, NULL);
    init_component_table(ui_chart); 
    lv_obj_add_event_cb(component_table, component_table_event_cb, LV_EVENT_VALUE_CHANGED, NULL);
    lv_obj_add_event_cb(ui_num__select, dropdown_event_cb, LV_EVENT_VALUE_CHANGED, NULL);
    lv_obj_add_event_cb(ui_export_confirm, ui_output_disappear, LV_EVENT_ALL, NULL);
    lv_obj_add_event_cb(ui_export_exit, ui_output_disappear_exit, LV_EVENT_ALL, NULL);
    lv_obj_add_event_cb(ui_Panel9, ui_out_callback_cb, LV_EVENT_ALL, NULL);
    add_component("STM32", "STM32F103C8T6", 100);
}

//扫描动画--消失
void ui_Scaning_disappear(lv_event_t * e) {
    lv_event_code_t code = lv_event_get_code(e);
    if(code == LV_EVENT_CLICKED) {
        //添加数据
        add_component_from_label(ui_Label_partinfo);

        // 执行淡出动画
        disappear_Animation(ui_Import_, 0);

        // 创建一个 500ms 后的定时器用于隐藏
        lv_timer_t * timer = lv_timer_create(scan_obj_cb, 500, ui_Import_);
        lv_timer_set_repeat_count(timer, 1); // 执行一次后自动销毁
    }
}
//扫描动画--出现
void ui_Scaning_appear (lv_event_t * e) {
    lv_event_code_t code = lv_event_get_code(e);
    if(code == LV_EVENT_CLICKED) {
        // 执行淡入动画
        lv_obj_set_style_opa(ui_Import_, LV_OPA_TRANSP, LV_PART_MAIN);
        lv_obj_clear_flag(ui_Import_, LV_OBJ_FLAG_HIDDEN);
        appear_Animation(ui_Import_, 0);
    }
}
//扫描动画--消失
void ui_Scaning_exit (lv_event_t * e) {
    lv_event_code_t code = lv_event_get_code(e);
    if(code == LV_EVENT_CLICKED) {
        //添加数据
        //add_component_from_label(ui_Label_partinfo);

        // 执行淡出动画
        disappear_Animation(ui_Import_, 0);

        // 创建一个 500ms 后的定时器用于隐藏
        lv_timer_t * timer = lv_timer_create(scan_exit_obj_cb, 500, ui_Import_);
        lv_timer_set_repeat_count(timer, 1); // 执行一次后自动销毁
    }
}

//元件页面登录
void ui_login (lv_event_t * e)
{
    lv_event_code_t code = lv_event_get_code(e);
    if(code == LV_EVENT_READY) {
        const char * input = lv_textarea_get_text(ui_Password);
        if(strcmp(input, correct_password) == 0) {
            _ui_flag_modify(ui_Passworf_Tip, LV_OBJ_FLAG_HIDDEN, _UI_MODIFY_FLAG_ADD);
            _ui_flag_modify(ui_Copoments_Lib, LV_OBJ_FLAG_HIDDEN, _UI_MODIFY_FLAG_REMOVE);

        } else {
            _ui_flag_modify(ui_Passworf_Tip, LV_OBJ_FLAG_HIDDEN, _UI_MODIFY_FLAG_REMOVE);
            lv_textarea_set_text(ui_Password, "");
        }
    }
}
//元件动画退出
void ui_out_callback_cb(lv_event_t * e)
{
    lv_event_code_t code = lv_event_get_code(e);
    if(code == LV_EVENT_CLICKED) {
        lv_textarea_set_text(ui_Password, "");
        _ui_flag_modify(ui_Passworf_Tip, LV_OBJ_FLAG_HIDDEN, _UI_MODIFY_FLAG_ADD);
        _ui_flag_modify(ui_Copoments_Lib, LV_OBJ_FLAG_HIDDEN, _UI_MODIFY_FLAG_ADD);
    }
}


//表格初始化
void init_component_table(lv_obj_t *parent)
{
    component_table = lv_table_create(parent);
    lv_obj_set_size(component_table, 530, 289);  // 视UI界面调整尺寸
    lv_obj_align(component_table, LV_ALIGN_CENTER, 0, 0);
    lv_obj_add_flag(component_table, LV_OBJ_FLAG_SCROLLABLE);

    lv_table_set_col_cnt(component_table, 3);
    lv_table_set_row_cnt(component_table, 1);  // 先添加标题行

    lv_table_set_cell_value(component_table, 0, 0, "名称");
    lv_table_set_cell_value(component_table, 0, 1, "型号");
    lv_table_set_cell_value(component_table, 0, 2, "数量");
    lv_table_set_col_width(component_table, 0, 150);  // name 列宽
    lv_table_set_col_width(component_table, 1, 250);  // model 列宽
    lv_table_set_col_width(component_table, 2, 100);  // quantity 列宽

    // 设置字体样式
    static lv_style_t table_style;
    lv_style_init(&table_style);
    lv_style_set_text_font(&table_style, &ui_font_Font12); 
    lv_obj_set_style_pad_all(component_table, 4, 0);         // 单元格内边距
    lv_obj_set_style_text_line_space(component_table, 6, 0); // 行间距

    static lv_style_t style_content;
    lv_style_init(&style_content);
    lv_style_set_text_align(&style_content, LV_TEXT_ALIGN_CENTER);  
    lv_style_set_border_width(&table_style, 0); //取消边
    lv_obj_add_style(component_table, &style_content, LV_PART_ITEMS);  // 应用于内容区域
    // 应用到表格所有单元格
    lv_obj_add_style(component_table, &table_style, 0);
}

//元件信息添加
void add_component(const char *name, const char *model, int quantity) {
    for (int i = 0; i < component_count; i++) {
        if (strcmp(component_list[i].name, name) == 0 &&
            strcmp(component_list[i].model, model) == 0) {
            // 合并数量
            component_list[i].quantity += quantity;

            char qty_str[16];
            snprintf(qty_str, sizeof(qty_str), "%d", component_list[i].quantity);
            lv_table_set_cell_value(component_table, i + 1, 2, qty_str);

            printf("[INFO] 合并元件: %s %s，新增数量=%d，总数量=%d\n",
                   name, model, quantity, component_list[i].quantity);
            return;
        }
    }

    // 添加新元件
    if (component_count < MAX_COMPONENTS) {
        strncpy(component_list[component_count].name, name, sizeof(component_list[component_count].name) - 1);
        component_list[component_count].name[sizeof(component_list[component_count].name) - 1] = '\0';

        strncpy(component_list[component_count].model, model, sizeof(component_list[component_count].model) - 1);
        component_list[component_count].model[sizeof(component_list[component_count].model) - 1] = '\0';

        component_list[component_count].quantity = quantity;

        lv_table_set_cell_value(component_table, component_count + 1, 0, component_list[component_count].name);
        lv_table_set_cell_value(component_table, component_count + 1, 1, component_list[component_count].model);

        char qty_str[16];
        snprintf(qty_str, sizeof(qty_str), "%d", quantity);
        lv_table_set_cell_value(component_table, component_count + 1, 2, qty_str);

        printf("[INFO] 添加新元件: %s %s 数量=%d\n", name, model, quantity);

        component_count++;
    }
}

//取出框回调
void component_table_event_cb(lv_event_t * e) {
    lv_obj_t * table = lv_event_get_target(e);

    uint32_t row, col;
    lv_table_get_selected_cell(table, &row, &col);
        if(row == 0) return; // 忽略标题行

        int idx = row - 1;
        if(idx >= 0 && idx < component_count) {
            current_selected_row = row;
            // 读取数据
            const char * name = component_list[idx].name;
            const char * model = component_list[idx].model;

            // 填充到文本框
            lv_label_set_text(ui_Export_Name2, name);
            lv_label_set_text(ui_Export_Type2, model);
            ui_output_appear();

        }
    
}

//数量选择框回调
void dropdown_event_cb(lv_event_t * e)
{
    lv_event_code_t code = lv_event_get_code(e);
    if(code == LV_EVENT_VALUE_CHANGED) {
        lv_obj_t * dd = lv_event_get_target(e);

        char sel_buf[32]; // 定义缓冲区
        lv_dropdown_get_selected_str(dd, sel_buf, sizeof(sel_buf)); // 把选中字符串拷贝到sel_buf

        int quantity = atoi(sel_buf);

        char quantity_str[16];
        snprintf(quantity_str, sizeof(quantity_str), "%d", quantity); // 把数字转换成字符串
        dropdown_quantity = atoi(sel_buf);  // 存入全局变量
        //lv_textarea_set_text(ui_TextArea1, quantity_str); // 传入字符串指针
    }
}

//输出选择框选择后回调
void ui_output_disappear(lv_event_t * e) {
    lv_event_code_t code = lv_event_get_code(e);
    if(code == LV_EVENT_CLICKED) {

        if(current_selected_row > 0 && current_selected_row <= component_count) {
            int idx = current_selected_row - 1;

            int used_qty = dropdown_quantity;
            if(used_qty > component_list[idx].quantity) {
                used_qty = component_list[idx].quantity;  // 防止负数
            }

            component_list[idx].quantity -= used_qty;  //更新剩余数

            char quantity_str[16];
            snprintf(quantity_str, sizeof(quantity_str), "%d", component_list[idx].quantity);  //显示剩余数
            lv_table_set_cell_value(component_table, current_selected_row, 2, quantity_str);
        }

        disappear_Animation(ui_Export, 0);
        lv_timer_t * timer = lv_timer_create(hide_obj_cb, 500, ui_Export);
        lv_timer_set_repeat_count(timer, 1);
    }
}

//取出动画--消失
void ui_output_disappear_exit(lv_event_t * e) {
    lv_event_code_t code = lv_event_get_code(e);
    if(code == LV_EVENT_CLICKED) {
        disappear_Animation(ui_Export, 0);
        lv_timer_t * timer = lv_timer_create(hide_obj_cb, 500, ui_Export);
        lv_timer_set_repeat_count(timer, 1);
    }
}

//取出动画--出现
void ui_output_appear() 
{
        // 执行淡入动画
        lv_obj_set_style_opa(ui_Export, LV_OPA_TRANSP, LV_PART_MAIN);
        lv_obj_clear_flag(ui_Export, LV_OBJ_FLAG_HIDDEN);
        appear_Animation(ui_Export, 0);
}

static void trim_quote_and_space(char *str) {
    // 去前面空格和引号
    while(*str == ' ' || *str == '"') {
        memmove(str, str + 1, strlen(str));
    }
    // 去尾部空格和引号
    size_t len = strlen(str);
    while(len > 0 && (str[len - 1] == ' ' || str[len - 1] == '"')) {
        str[len - 1] = '\0';
        len--;
    }
}

//添加元件数据处理
void add_component_from_label(lv_obj_t *label) {
    const char *text = lv_label_get_text(label);
    if (text == NULL) return;

    char buf[128];
    strncpy(buf, text, sizeof(buf) - 1);
    buf[sizeof(buf) - 1] = '\0';

    // 分割解析: "name", "model", quantity
    char *token = strtok(buf, ",");
    if (token == NULL) return;
    trim_quote_and_space(token);
    char *name = token;

    token = strtok(NULL, ",");
    if (token == NULL) return;
    trim_quote_and_space(token);
    char *model = token;

    token = strtok(NULL, ",");
    if (token == NULL) return;
    trim_quote_and_space(token);
    int quantity = atoi(token);

    printf("Name: %s\n", name);
    printf("Model: %s\n", model);
    printf("Quantity: %d\n", quantity);

    // 调用添加函数
    add_component(name, model, quantity);
}
