#ifndef MQTT_H
#define MQTT_H

#include <pthread.h>

// 启动 MQTT 客户端线程
void mqtt_client_start();  // 添加这个声明

int mqtt_publish_control_ack(const char* payload);

#endif

