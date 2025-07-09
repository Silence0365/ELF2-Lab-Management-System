#include "canvas_display.h"
#include "lvgl/lvgl.h"
#include <unistd.h>
#include <sys/shm.h>
#include <sys/sem.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <time.h>
#include <pthread.h>
#include "ui/ui.h"

//#define WIDTH 640
//#define HEIGHT 480
#define WIDTH  320
#define HEIGHT 240
#define SHM_KEY 1234
#define SEM_KEY 5678
#define SHM_SIZE (WIDTH * HEIGHT * 2)

lv_obj_t *canvas;
lv_color_t *canvas_buf;
pthread_mutex_t canvas_mutex;


//回调函数
static void canvas_invalidate_cb(void *user_data) {
    LV_UNUSED(user_data);
    if (canvas) {
        lv_obj_invalidate(canvas);
    }
}


static void canvas_refresh_cb(lv_timer_t *timer) {
    LV_UNUSED(timer);
    if (canvas) lv_obj_invalidate(canvas);
}

// 画布初始化
void canvas_init(void) {
    pthread_mutex_init(&canvas_mutex, NULL);
    pthread_mutex_lock(&canvas_mutex);
    canvas_buf = malloc(WIDTH * HEIGHT * sizeof(lv_color_t));
    pthread_mutex_unlock(&canvas_mutex);

    if (!canvas_buf) {
        perror("malloc canvas_buf");
        exit(1);
    }

    canvas = lv_canvas_create(ui_Screen_Catch); 
    lv_canvas_set_buffer(canvas, canvas_buf, WIDTH, HEIGHT, LV_COLOR_FORMAT_RGB565);
    lv_obj_set_size(canvas, WIDTH, HEIGHT);
    lv_obj_set_style_border_color(canvas, lv_color_hex(0xFF0000), 0);
    lv_obj_set_style_border_width(canvas, 2, 0);
    lv_obj_set_style_radius(canvas, 20, 0); 
    lv_obj_set_style_clip_corner(canvas, true, 0);
    lv_obj_center(canvas);  
    lv_timer_create(canvas_refresh_cb, 13, NULL);
}

// 显示线程--多线程
void *canvas_display_thread(void *arg) {
    int shmid = shmget(SHM_KEY, SHM_SIZE, 0666);
    if (shmid < 0) {
        perror("shmget failed");
        return NULL;
    }

    void *shmaddr = shmat(shmid, NULL, 0);
    if (shmaddr == (void *) -1) {
        perror("shmat failed");
        return NULL;
    }

    int semid = semget(SEM_KEY, 1, 0666);
    if (semid < 0) {
        perror("semget failed");
        return NULL;
    }

    struct sembuf sem_op = { .sem_num = 0, .sem_op = -1, .sem_flg = 0 };
    time_t last = time(NULL);
    int frames = 0;

    while (1) {
        if (semop(semid, &sem_op, 1) == -1) {
            perror("semop failed");
            break;
        }

        if (!canvas_buf || !canvas || shmaddr == (void *) -1) {
            fprintf(stderr, "[canvas] null pointer detected\n");
            break;
        }

        pthread_mutex_lock(&canvas_mutex);
        memcpy(canvas_buf, shmaddr, SHM_SIZE);
        pthread_mutex_unlock(&canvas_mutex);
        usleep(5000); 

        frames++;
        if (time(NULL) != last) {
            printf("[canvas] FPS: %d\n", frames);
            frames = 0;
            last = time(NULL);
        }
    }

    shmdt(shmaddr);
    return NULL;
}

