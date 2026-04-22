#ifndef _CONFIG_H
#define _CONFIG_H
#include "stm32f1xx_hal.h"
#include <stdint.h>
#include <stdbool.h>

/* GPS DMA    / queue */
#define GPS_DMA_BUF_SIZE 256
#define GPS_CHUNK_BUF_SIZE 256
#define GPS_ACC_BUF_SIZE 512
#define GPS_SENTENCE_MAX_LEN 128
#define GPS_SENTENCE_QUEUE_SIZE 8

/* Telemetry / CSV */
#define TELEMETRY_PACKET_BUF_SIZE 256
#define CSV_LINE_BUF_SIZE 256
#define LOG_FILENAME_BUF_SIZE 64
#define TELEMETRY_TX_INTERVAL_MS 1000
/* Button & SD Sync */
#define BUTTON_DEBOUNCE_MS 30
#define BUTTON_LONGPRESS_MS 2000
#define SDLOG_FLUSH_EVERY_N_RECORDS 5

/* GPIO mapping (根據 A03/A04 接線定義) */
#define LED_GPIO_Port GPIOB
#define LED_Pin GPIO_PIN_0
#define BTN_GPIO_Port GPIOC
#define BTN_Pin GPIO_PIN_13
#endif
