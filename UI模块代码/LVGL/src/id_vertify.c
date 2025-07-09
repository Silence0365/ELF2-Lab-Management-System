#include "mqtt_data.h"
#include "ui/ui.h"
#include "lvgl.h"
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
static lv_timer_t *yolo_timer = NULL;  // 控制动画的定时器
static bool tof_pending = false;
static void return_to_main_page_cb(lv_timer_t *timer);

// ==================== 动画安全封装 ====================

// 封装 yolo 动画为安全异步回调
static void yolo_safe_call(void *param)
{
    YoloPoint3_Animation(ui_Pointyolo3, 0);
    YoloPoint2_Animation(ui_Pointyolo2, 0);
    YoloPonit1_Animation(ui_Pointyolo1, 0);
    YoloPoint0_Animation(ui_Pointyolo0, 0);
}


// 每2000ms执行一次动画（安全调用）
static void yolo_animation_task(lv_timer_t * t)
{
    lv_async_call(yolo_safe_call, NULL);  // 异步调用动画
}

// 封装页面切换为安全异步回调
static void page_appear_safe_call(void *param)
{
        _ui_flag_modify(ui_Lab_Control, LV_OBJ_FLAG_HIDDEN, _UI_MODIFY_FLAG_ADD);
        _ui_flag_modify(ui_Weather_Cup, LV_OBJ_FLAG_HIDDEN, _UI_MODIFY_FLAG_ADD);
        _ui_flag_modify(ui_Power_Detection, LV_OBJ_FLAG_HIDDEN, _UI_MODIFY_FLAG_ADD);
        _ui_flag_modify(ui_Password_Confirm, LV_OBJ_FLAG_HIDDEN, _UI_MODIFY_FLAG_ADD);
        _ui_flag_modify(ui_System_Info, LV_OBJ_FLAG_HIDDEN, _UI_MODIFY_FLAG_ADD);
        _ui_flag_modify(ui_Copoments_Lib, LV_OBJ_FLAG_HIDDEN, _UI_MODIFY_FLAG_ADD);
        _ui_flag_modify(ui_Yolo_Identify, LV_OBJ_FLAG_HIDDEN, _UI_MODIFY_FLAG_REMOVE);
        _ui_state_modify(ui_Panel6, LV_STATE_CHECKED, _UI_MODIFY_STATE_ADD);
        _ui_state_modify(ui_Panel7, LV_STATE_CHECKED, _UI_MODIFY_STATE_REMOVE);
        _ui_state_modify(ui_Panel8, LV_STATE_CHECKED, _UI_MODIFY_STATE_REMOVE);
        _ui_state_modify(ui_Panel13, LV_STATE_CHECKED, _UI_MODIFY_STATE_REMOVE);
        _ui_state_modify(ui_Panel15, LV_STATE_CHECKED, _UI_MODIFY_STATE_REMOVE);
        _ui_state_modify(ui_Panel17, LV_STATE_CHECKED, _UI_MODIFY_STATE_REMOVE);
        lv_timer_create(return_to_main_page_cb, 300000, NULL); 
}

static void page_disappear_safe_call(void *param)
{
        _ui_flag_modify(ui_Weather_Cup, LV_OBJ_FLAG_HIDDEN, _UI_MODIFY_FLAG_REMOVE);
        _ui_flag_modify(ui_Lab_Control, LV_OBJ_FLAG_HIDDEN, _UI_MODIFY_FLAG_ADD);
        _ui_flag_modify(ui_Power_Detection, LV_OBJ_FLAG_HIDDEN, _UI_MODIFY_FLAG_ADD);
        _ui_flag_modify(ui_Password_Confirm, LV_OBJ_FLAG_HIDDEN, _UI_MODIFY_FLAG_ADD);
        _ui_flag_modify(ui_System_Info, LV_OBJ_FLAG_HIDDEN, _UI_MODIFY_FLAG_ADD);
        _ui_flag_modify(ui_Yolo_Identify, LV_OBJ_FLAG_HIDDEN, _UI_MODIFY_FLAG_ADD);
        _ui_flag_modify(ui_Copoments_Lib, LV_OBJ_FLAG_HIDDEN, _UI_MODIFY_FLAG_ADD);
        _ui_state_modify(ui_Panel8, LV_STATE_CHECKED, _UI_MODIFY_STATE_ADD);
        _ui_state_modify(ui_Panel6, LV_STATE_CHECKED, _UI_MODIFY_STATE_REMOVE);
        _ui_state_modify(ui_Panel7, LV_STATE_CHECKED, _UI_MODIFY_STATE_REMOVE);
        _ui_state_modify(ui_Panel13, LV_STATE_CHECKED, _UI_MODIFY_STATE_REMOVE);
        _ui_state_modify(ui_Panel15, LV_STATE_CHECKED, _UI_MODIFY_STATE_REMOVE);
        _ui_state_modify(ui_Panel17, LV_STATE_CHECKED, _UI_MODIFY_STATE_REMOVE);
}
static void return_to_main_page_cb(lv_timer_t *timer)
{
    lv_async_call(page_disappear_safe_call, NULL);//安全回调
    lv_timer_del(timer);  // 执行一次后删除
}
//消抖
static void tof_delayed_check_cb(lv_timer_t *t)
{
    if (tof_flag > 200 && tof_flag <= 2000) {
        lv_async_call(page_appear_safe_call, NULL);
        if (yolo_timer == NULL) {
            yolo_timer = lv_timer_create(yolo_animation_task, 2000, NULL);
        }
    }
    tof_pending = false; // 清除状态
    lv_timer_del(t);
}

// ==================== 验证逻辑 ====================
// 核心验证函数，动态启停定时器
void TOF_Vertifying()
{
    if (tof_flag > 200 && tof_flag <= 2000 && !tof_pending)
    {
        tof_pending = true; // 标记已在等待中
        lv_timer_create(tof_delayed_check_cb, 1000, NULL); // 1 秒后再次检查
    }

    // 防抖
    if (tof_flag <= 200 || tof_flag > 2000) {
        if (yolo_timer) {
            lv_timer_del(yolo_timer);
            yolo_timer = NULL;
        }
    }
}

// 封装 ID 动画为安全异步回调
static void id_safe_call(void *param)
{
    DynamicIsland_Animation(ui_Dynamic_Island, 0);
    coinlocked_Animation(ui_Icon_locked, 0);
    coinunlocked_Animation(ui_Icon_unlocked, 0);
}

void ID_Vertifying()
{
    if (card1_flag ==1)
    {
        if (yolo_timer != NULL)
        {
            lv_timer_del(yolo_timer);
            yolo_timer = NULL;
        }
        lv_async_call(id_safe_call, NULL);  // 异步调用 UI 动画
        safe_ui_update(ui_Label_Name, "按附件阿克洛夫");
        safe_ui_update(ui_Label_Charact, "学生");
        safe_ui_update(ui_Label_Number, "2212270127");
        safe_ui_update(ui_Label_State, "正常");
	lv_timer_create(return_to_main_page_cb, 10000, NULL); 
	card1_flag=0;
	printf("CARD1识别\n");
    }
    if (card2_flag ==1)
    {
    	if (yolo_timer != NULL)
        {
            lv_timer_del(yolo_timer);
            yolo_timer = NULL;
        }
        lv_async_call(id_safe_call, NULL);  // 异步调用 UI 动画
        safe_ui_update(ui_Label_Name, "河源木桃香");
        safe_ui_update(ui_Label_Charact, "教师");
        safe_ui_update(ui_Label_Number, "2212270122");
        safe_ui_update(ui_Label_State, "正常");
	lv_timer_create(return_to_main_page_cb, 10000, NULL); 
	card2_flag=0;
	printf("CARD2识别\n");
    }
}

