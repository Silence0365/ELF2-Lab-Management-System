#include "mqtt_connect.h"
#include "mqtt_data.h"
#include <MQTTClient.h>
#include <unistd.h>
#include <pthread.h>  // 添加 pthread 支持

//MQTT配置
#define MQTT_ADDRESS  "tcp://localhost:1883"
#define MQTT_CLIENTID "lvgl_display"
#define RECIEVE_MQTT_TOPIC    "sensors/data"
#define SEND_MQTT_TOPIC    "control/LVGL"

static MQTTClient client;
static void* mqtt_thread(void* arg) {  
    
    MQTTClient_connectOptions conn_opts = MQTTClient_connectOptions_initializer;

    MQTTClient_create(&client, MQTT_ADDRESS, MQTT_CLIENTID,
                      MQTTCLIENT_PERSISTENCE_NONE, NULL);
    
    MQTTClient_setCallbacks(client, NULL, NULL, messageArrived, NULL);

    conn_opts.keepAliveInterval = 10;
    conn_opts.cleansession = 1;

    while (MQTTClient_connect(client, &conn_opts) != MQTTCLIENT_SUCCESS) {
        printf("[MQTT] 重连中...\n");
        sleep(5);
    }

    printf("[MQTT] 连接成功，订阅中...\n");
    MQTTClient_subscribe(client, RECIEVE_MQTT_TOPIC, 1);//receive
    MQTTClient_subscribe(client, SEND_MQTT_TOPIC, 1);//send
    MQTTClient_subscribe(client, "AI/Identify", 1);//AI_Identify
    MQTTClient_subscribe(client, "scanner/qr", 1);//scanner/qr
    MQTTClient_subscribe(client, "ack/LVGL", 1);//ack/LVGL
    MQTTClient_subscribe(client, "network/status" , 1);//network/status"
    while (1) {
        MQTTClient_yield();
        usleep(10000);
    }

    return NULL;
}

//发送信息函数_SEND_MQTT_TOPIC
int mqtt_publish_control_ack(const char* payload) {
    if (client == NULL) {
        printf("[MQTT] 客户端未初始化\n");
        return -1;
    }

    MQTTClient_message pubmsg = MQTTClient_message_initializer;
    MQTTClient_deliveryToken token;

    pubmsg.payload = (void*)payload;
    pubmsg.payloadlen = (int)strlen(payload);
    pubmsg.qos = 1;
    pubmsg.retained = 0;

    int rc = MQTTClient_publishMessage(client, SEND_MQTT_TOPIC, &pubmsg, &token);
    if (rc != MQTTCLIENT_SUCCESS) {
        printf("[MQTT] 发布失败，错误码：%d\n", rc);
        return rc;
    }

    // 不等待消息完成，直接返回，异步发布
    printf("[MQTT] 消息异步发送，token=%d\n", token);
    return MQTTCLIENT_SUCCESS;
} 


// 添加这个函数
void mqtt_client_start() {
    pthread_t tid;
    pthread_create(&tid, NULL, mqtt_thread, NULL);
}

