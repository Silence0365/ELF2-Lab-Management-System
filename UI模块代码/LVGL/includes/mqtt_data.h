#ifndef MQTT_DATA_H
#define MQTT_DATA_H

#include <MQTTClient.h>
#include <string.h>

// 消息到达后的回调函数声明
int messageArrived(void *context, char *topicName, int topicLen, MQTTClient_message *message);
extern int tof_flag;
extern int card1_flag;
extern int card2_flag;
#endif

