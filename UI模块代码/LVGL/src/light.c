#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <pthread.h>
#include "lvgl/lvgl.h"
#include "lvgl/examples/lv_examples.h"
#include "lvgl/demos/lv_demos.h"
#include "ui/ui.h"

static bool B401_visible = false;
static bool B402_visible = false;
static bool B403_visible = false;
static bool B404_visible = false;
static bool B405_visible = false;

void light_ui_init(void);
void B401_cb(lv_event_t * e);
void B402_cb(lv_event_t * e);
void B403_cb(lv_event_t * e);
void B404_cb(lv_event_t * e);
void B405_cb(lv_event_t * e);


void light_ui_init(void)
{
    lv_obj_add_event_cb(ui_Lab_B401, B401_cb, LV_EVENT_CLICKED, NULL);
    lv_obj_add_event_cb(ui_Lab_B402, B402_cb, LV_EVENT_CLICKED, NULL);
    lv_obj_add_event_cb(ui_Lab_B403, B403_cb, LV_EVENT_CLICKED, NULL);
    lv_obj_add_event_cb(ui_Lab_B404, B404_cb, LV_EVENT_CLICKED, NULL);
    lv_obj_add_event_cb(ui_Lab_Cateen, B405_cb, LV_EVENT_CLICKED, NULL);
    //默认透明度0-关灯
    lv_obj_set_style_opa(ui_Lab_B401, LV_OPA_TRANSP, LV_PART_MAIN);
    lv_obj_set_style_opa(ui_Lab_B402, LV_OPA_TRANSP, LV_PART_MAIN);
    lv_obj_set_style_opa(ui_Lab_B403, LV_OPA_TRANSP, LV_PART_MAIN);
    lv_obj_set_style_opa(ui_Lab_B404, LV_OPA_TRANSP, LV_PART_MAIN);
    lv_obj_set_style_opa(ui_Lab_Cateen, LV_OPA_TRANSP, LV_PART_MAIN);
}

void B401_cb(lv_event_t * e) {
    lv_event_code_t code = lv_event_get_code(e);
    if(code == LV_EVENT_CLICKED) {
        if(B401_visible)
        {
	    lv_obj_set_style_opa(ui_Lab_B401, LV_OPA_TRANSP, LV_PART_MAIN);
	    char buf[128];
	    snprintf(buf, sizeof(buf), "{\"B401_Light\":\"OFF\"}");
	    mqtt_publish_control_ack(buf);
	    B401_visible=false;
        }
        else
        {
            lv_obj_set_style_opa(ui_Lab_B401, LV_OPA_COVER, LV_PART_MAIN);
    	    char buf[128];
	    snprintf(buf, sizeof(buf), "{\"B401_Light\":\"ON\"}");
	    mqtt_publish_control_ack(buf);
            B401_visible=true;
        }
    }
}

void B402_cb(lv_event_t * e) {
    lv_event_code_t code = lv_event_get_code(e);
    if(code == LV_EVENT_CLICKED) {
        if(B402_visible)
        {
            lv_obj_set_style_opa(ui_Lab_B402, LV_OPA_TRANSP, LV_PART_MAIN);
    	    char buf[128];
	    snprintf(buf, sizeof(buf), "{\"B402_Light\":\"OFF\"}");
	    mqtt_publish_control_ack(buf);
            B402_visible=false;
        }
        else
        {
            lv_obj_set_style_opa(ui_Lab_B402, LV_OPA_COVER, LV_PART_MAIN);
    	    char buf[128];
	    snprintf(buf, sizeof(buf), "{\"B402_Light\":\"ON\"}");
	    mqtt_publish_control_ack(buf);
            B402_visible=true;
        }
    }
}

void B403_cb(lv_event_t * e) {
    lv_event_code_t code = lv_event_get_code(e);
    if(code == LV_EVENT_CLICKED) {
        if(B403_visible)
        {
            lv_obj_set_style_opa(ui_Lab_B403, LV_OPA_TRANSP, LV_PART_MAIN);
    	    char buf[128];
	    snprintf(buf, sizeof(buf), "{\"B403_Light\":\"OFF\"}");
	    mqtt_publish_control_ack(buf);
            B403_visible=false;
        }
        else
        {
            lv_obj_set_style_opa(ui_Lab_B403, LV_OPA_COVER, LV_PART_MAIN);
    	    char buf[128];
	    snprintf(buf, sizeof(buf), "{\"B403_Light\":\"ON\"}");
	    mqtt_publish_control_ack(buf);
            B403_visible=true;
        }
    }
}

void B404_cb(lv_event_t * e) {
    lv_event_code_t code = lv_event_get_code(e);
    if(code == LV_EVENT_CLICKED) {
        if(B404_visible)
        {
            lv_obj_set_style_opa(ui_Lab_B404, LV_OPA_TRANSP, LV_PART_MAIN);
    	    char buf[128];
	    snprintf(buf, sizeof(buf), "{\"B404_Light\":\"OFF\"}");
	    mqtt_publish_control_ack(buf);
            B404_visible=false;
        }
        else
        {
            lv_obj_set_style_opa(ui_Lab_B404, LV_OPA_COVER, LV_PART_MAIN);
    	    char buf[128];
	    snprintf(buf, sizeof(buf), "{\"B404_Light\":\"ON\"}");
	    mqtt_publish_control_ack(buf);
            B404_visible=true;
        }
    }
}

void B405_cb(lv_event_t * e) {
    lv_event_code_t code = lv_event_get_code(e);
    if(code == LV_EVENT_CLICKED) {
        if(B405_visible)
        {
            lv_obj_set_style_opa(ui_Lab_Cateen, LV_OPA_TRANSP, LV_PART_MAIN);
    	    char buf[128];
	    snprintf(buf, sizeof(buf), "{\"B405_Light\":\"OFF\"}");
	    mqtt_publish_control_ack(buf);
            B405_visible=false;
        }
        else
        {
            lv_obj_set_style_opa(ui_Lab_Cateen, LV_OPA_COVER, LV_PART_MAIN);
    	    char buf[128];
	    snprintf(buf, sizeof(buf), "{\"B405_Light\":\"ON\"}");
	    mqtt_publish_control_ack(buf);
            B405_visible=true;
        }
    }
}
