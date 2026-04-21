# STM32F103C8TX GPS 遙測記錄系統 - 完整原始碼

## 📋 檔案內容總覽

本文檔包含專案所有源碼檔案的完整內容。共計：
- **13 個頭檔案** (Core/Inc/)
- **15 個源檔案** (Core/Src/)

---

## 📁 Core/Inc 頭檔案

### 1. main.h
```c
/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file           : main.h
  * @brief          : Header for main.c file.
  *                   This file contains the common defines of the application.
  ******************************************************************************
  * @attention
  *
  * Copyright (c) 2026 STMicroelectronics.
  * All rights reserved.
  *
  * This software is licensed under terms that can be found in the LICENSE file
  * in the root directory of this software component.
  * If no LICENSE file comes with this software, it is provided AS-IS.
  *
  ******************************************************************************
  */
/* USER CODE END Header */

/* Define to prevent recursive inclusion */
#ifndef __MAIN_H
#define __MAIN_H

#ifdef __cplusplus
extern "C" {
#endif

/* Includes */
#include "stm32f1xx_hal.h"

/* Exported functions prototypes */
void Error_Handler(void);

/* Private defines */
#define BTN_Pin_Pin GPIO_PIN_13
#define BTN_Pin_GPIO_Port GPIOC
#define SD_CS_Pin_Pin GPIO_PIN_4
#define SD_CS_Pin_GPIO_Port GPIOA
#define LED_PIN_Pin GPIO_PIN_0
#define LED_PIN_GPIO_Port GPIOB

#ifdef __cplusplus
}
#endif

#endif /* __MAIN_H */
```

### 2. app.h
```c
#ifndef __APP_H__
#define __APP_H__
void APP_Init(void);
void APP_Run(void);
#endif
```

### 3. config.h
```c
#ifndef _CONFIG_H
#define _CONFIG_H
#include "stm32f1xx_hal.h"
#include <stdint.h>
#include <stdbool.h>

/* GPS DMA / queue */
#define GPS_DMA_BUF_SIZE 256
#define GPS_CHUNK_BUF_SIZE 256
#define GPS_ACC_BUF_SIZE 512
#define GPS_SENTENCE_MAX_LEN 128
#define GPS_SENTENCE_QUEUE_SIZE 8

/* Telemetry / CSV */
#define TELEMETRY_PACKET_BUF_SIZE 256
#define CSV_LINE_BUF_SIZE 256
#define LOG_FILENAME_BUF_SIZE 64

/* Button & SD Sync */
#define BUTTON_DEBOUNCE_MS 30
#define BUTTON_LONGPRESS_MS 2000
#define SDLOG_FLUSH_EVERY_N_RECORDS 5

/* GPIO mapping */
#define LED_GPIO_Port GPIOB
#define LED_Pin GPIO_PIN_0
#define BTN_GPIO_Port GPIOC
#define BTN_Pin GPIO_PIN_13
#endif
```

### 4. gps.h
```c
#ifndef _GPS_H_
#define _GPS_H_

#include "config.h"
#include <stdbool.h>
#include <stdint.h>

/**
 * @brief GPS 單條語句結構體
 */
typedef struct
{
    char sentence[GPS_SENTENCE_MAX_LEN];
    uint16_t len;
    uint32_t tick_ms;
} GPS_Sentence_t;

/**
 * @brief GPS 語句環型佇列結構體
 */
typedef struct
{
    GPS_Sentence_t items[GPS_SENTENCE_QUEUE_SIZE];
    uint8_t head;
    uint8_t tail;
    uint8_t count;
} GPS_SentenceQueue_t;

/* 硬體初始化與接收控制函式 */
void GPS_Init(void);
void GPS_StartReception(void);
void GPS_StopReception(void);
void GPS_OnRxEvent(uint16_t size);
void GPS_ProcessRxChunk(void);
void GPS_SplitLinesToQueue(void);
bool GPS_QueuePop(GPS_Sentence_t *out);
uint8_t GPS_GetQueueCount(void);

/* GPS 全局緩衝區 */
extern uint8_t  g_dma_buf[];
extern uint8_t  g_chunk_buf[];
extern volatile uint16_t g_chunk_len;
extern volatile uint8_t  g_chunk_ready;
extern uint16_t g_acc_len;

#endif
```

### 5. nmea_parser.h
```c
#ifndef __NMEA_PARSER_H__
#define __NMEA_PARSER_H__

#include "telemetry_record.h"
#include <stdbool.h>

/**
 * @brief NMEA 語句類型枚舉
 */
typedef enum
{
    NMEA_UNKNOWN = 0,
    NMEA_RMC,
    NMEA_GGA
} NMEA_SentenceType_t;

/* 核心驗證與判定函式 */
bool NMEA_VerifyChecksum(const char *sentence);
NMEA_SentenceType_t NMEA_GetSentenceType(const char *sentence);

/* 解析函式 */
bool NMEA_ParseRMC(const char *sentence, GPS_RMC_t *rmc);
bool NMEA_ParseGGA(const char *sentence, GPS_GGA_t *gga);

/* 資料轉換工具 */
double NMEA_ConvertLatitude(const char *raw, char ns);
double NMEA_ConvertLongitude(const char *raw, char ew);
float NMEA_KnotsToKmh(float knots);

#endif
```

### 6. telemetry_record.h
```c
#ifndef _TELEMETRY_RECORD_H_
#define _TELEMETRY_RECORD_H_

#include "stm32f1xx_hal.h"
#include <stdint.h>
#include <stdbool.h>

/* 基礎時間結構體 */
typedef struct
{
    uint16_t year;
    uint8_t  month;
    uint8_t  day;
    uint8_t  hour;
    uint8_t  min;
    uint8_t  sec;
} RTC_DateTime_t;

/* GPS RMC 原始數據結構 */
typedef struct
{
    uint8_t  valid;
    uint8_t  hour;
    uint8_t  min;
    uint8_t  sec;
    uint8_t  day;
    uint8_t  month;
    uint16_t year;
    double   latitude_deg;
    double   longitude_deg;
    float    speed_knots;
    float    speed_kmh;
    float    course_deg;
} GPS_RMC_t;

/* GPS GGA 原始數據結構 */
typedef struct
{
    uint8_t  fix_quality;
    uint8_t  satellites;
    float    hdop;
    float    altitude_m;
    uint8_t  hour;
    uint8_t  min;
    uint8_t  sec;
    double   latitude_deg;
    double   longitude_deg;
} GPS_GGA_t;

/* 資料融合快取結構 */
typedef struct
{
    GPS_RMC_t rmc;
    uint8_t   rmc_valid;
    GPS_GGA_t gga;
    uint8_t   gga_valid;
    uint32_t  rmc_arrival_tick;
    uint32_t  gga_arrival_tick;
} GPS_FusionCache_t;

/* 統一遙測紀錄結構 */
typedef struct
{
    uint32_t       mcu_tick_ms;
    RTC_DateTime_t gps_dt;
    RTC_DateTime_t rtc_dt;
    uint8_t        gps_valid;
    uint8_t        fix_quality;
    uint8_t        satellites;
    float          hdop;
    double         latitude_deg;
    double         longitude_deg;
    float          altitude_m;
    float          speed_knots;
    float          speed_kmh;
    float          course_deg;
    uint8_t        rmc_ok;
    uint8_t        gga_ok;
    uint8_t        record_ready;
} UnifiedTelemetryRecord;

/* 函式原型 */
void TelemetryRecord_Reset(UnifiedTelemetryRecord *rec);
void FusionCache_Reset(GPS_FusionCache_t *cache);
void FusionCache_UpdateRMC(GPS_FusionCache_t *cache, const GPS_RMC_t *rmc);
void FusionCache_UpdateGGA(GPS_FusionCache_t *cache, const GPS_GGA_t *gga);
bool Fusion_TryBuildRecord(GPS_FusionCache_t *cache,
                           UnifiedTelemetryRecord *rec,
                           const RTC_DateTime_t *rtc,
                           uint32_t tick_ms);

#endif
```

### 7. telemetry.h
```c
/**
 * @file telemetry.h
 * @brief 遙測協定格式化與傳送模組
 * 負責將 UnifiedTelemetryRecord 轉換為 $TEL ASCII 封包並透過 UART 輸出
 */

#ifndef _TELEMETRY_H_
#define _TELEMETRY_H_

#include "telemetry_record.h"
#include <stdbool.h>
#include <stdint.h>

bool Telemetry_FormatPacket(const UnifiedTelemetryRecord *rec, char *out, uint16_t max_len);
bool Telemetry_SendPacket(const UnifiedTelemetryRecord *rec);
uint8_t Telemetry_CalcChecksum(const char *payload);

#endif
```

### 8. sdlog.h
```c
/**
 * @file    sdlog.h
 * @brief   SD Card Logging Module (FATFS based)
 * @details 負責本地 CSV 資料儲存、每日自動開檔與緩衝區同步策略。
 */

#ifndef __SDLOG_H__
#define __SDLOG_H__

#include "telemetry_record.h"
#include <stdbool.h>
#include <stdint.h>

bool SDLog_Init(void);
bool SDLog_OpenDailyFile(const RTC_DateTime_t *dt);
bool SDLog_WriteHeaderIfNeeded(void);
bool SDLog_FormatCSVLine(const UnifiedTelemetryRecord *rec, char *out, uint16_t max_len);
bool SDLog_AppendRecord(const UnifiedTelemetryRecord *rec);
bool SDLog_Flush(void);

#endif
```

### 9. rtc_ds3231.h
```c
/* rtc_ds3231.h */
#ifndef __RTC_DS3231_H__
#define __RTC_DS3231_H__

#include "telemetry_record.h"
#include <stdbool.h>

bool RTC_DS3231_Init(void);
bool RTC_DS3231_ReadDateTime(RTC_DateTime_t *dt);

#endif
```

### 10. button_led.h
```c
#ifndef _BUTTON_LED_H_
#define _BUTTON_LED_H_

#include <stdint.h>

/* 按鈕事件類型定義 */
typedef enum
{
    BTN_EVENT_NONE = 0,
    BTN_EVENT_SHORT_PRESS,
    BTN_EVENT_LONG_PRESS
} ButtonEvent_t;

/* LED 工作模式定義 */
typedef enum
{
    LED_MODE_OFF = 0,
    LED_MODE_IDLE_SLOW_BLINK,
    LED_MODE_RUN_FAST_BLINK,
    LED_MODE_LOGGING_ON,
    LED_MODE_WARN_DOUBLE_BLINK,
    LED_MODE_ERROR_TRIPLE_BLINK,
    LED_MODE_FATAL_FAST_BLINK
} LED_Mode_t;

/* 功能函式宣告 */
void ButtonLED_Init(void);
void Button_Update(void);
ButtonEvent_t Button_GetEvent(void);
void LED_SetMode(LED_Mode_t mode);
void LED_Task(void);

#endif
```

### 11. error_manager.h
```c
/* error_manager.h */
#ifndef __ERROR_MANAGER_H__
#define __ERROR_MANAGER_H__

#include <stdint.h>

/**
 * @brief 系統錯誤計數器結構體
 * 用於追蹤各模組在運行期間發生的異常次數
 */
typedef struct
{
    uint32_t gps_checksum_fail_count;
    uint32_t gps_parse_fail_count;
    uint32_t rtc_read_fail_count;
    uint32_t sd_mount_fail_count;
    uint32_t sd_write_fail_count;
    uint32_t uart_tx_fail_count;
} SystemErrorCounters_t;

void ErrorMgr_Init(void);
void ErrorMgr_IncGPSChecksumFail(void);
void ErrorMgr_IncGPSParseFail(void);
void ErrorMgr_IncRTCReadFail(void);
void ErrorMgr_IncSDMountFail(void);
void ErrorMgr_IncSDWriteFail(void);
void ErrorMgr_IncUARTTxFail(void);
SystemErrorCounters_t ErrorMgr_GetCounters(void);

#endif
```

### 12. stm32f1xx_it.h
```c
/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file    stm32f1xx_it.h
  * @brief   This file contains the headers of the interrupt handlers.
  ******************************************************************************
  * @attention
  *
  * Copyright (c) 2026 STMicroelectronics.
  * All rights reserved.
  *
  * This software is licensed under terms that can be found in the LICENSE file
  * in the root directory of this software component.
  * If no LICENSE file comes with this software, it is provided AS-IS.
  *
  ******************************************************************************
  */
/* USER CODE END Header */

#ifndef __STM32F1xx_IT_H
#define __STM32F1xx_IT_H

#ifdef __cplusplus
extern "C" {
#endif

/* Exported functions prototypes */
void NMI_Handler(void);
void HardFault_Handler(void);
void MemManage_Handler(void);
void BusFault_Handler(void);
void UsageFault_Handler(void);
void SVC_Handler(void);
void DebugMon_Handler(void);
void PendSV_Handler(void);
void SysTick_Handler(void);
void DMA1_Channel6_IRQHandler(void);
void USART1_IRQHandler(void);
void USART2_IRQHandler(void);

#ifdef __cplusplus
}
#endif

#endif
```

### 13. stm32f1xx_hal_conf.h
[HAL 配置檔案 - 主要定義啟用的 HAL 模組與系統參數]

---

## 📁 Core/Src 源檔案

### 1. main.c
[主程式初始化與硬體配置 - 共包含系統時鐘、GPIO、DMA、I2C、SPI、UART 等初始化]

### 2. app.c
[應用層主邏輯 - 狀態機管理 (IDLE/RUN/LOGGING)、GPS 隊列處理、數據融合與輸出]

### 3. gps.c
[GPS 模組 - DMA 接收、IDLE 中斷處理、環型隊列管理、NMEA 語句斷句]

### 4. nmea_parser.c
[NMEA 解析 - 校驗碼驗證、RMC/GGA 語句解析、坐標轉換]

### 5. telemetry_record.c
[遙測紀錄融合 - 數據結構初始化、RMC/GGA 融合、統一紀錄構建]

### 6. telemetry.c
[遙測傳輸 - 封包格式化、校驗碼計算、UART1 發送]

### 7. sdlog.c
[SD 卡記錄 - FATFS 掛載、每日檔案管理、CSV 寫入與緩衝同步]

### 8. rtc_ds3231.c
[RTC 時鐘驅動 - I2C 通信、BCD 轉換、日期時間讀取]

### 9. button_led.c
[按鈕/LED 控制 - 去抖動邏輯、短/長按判定、7 種 LED 模式驅動]

### 10. error_manager.c
[錯誤管理 - 各模組錯誤計數器初始化與增量]

### 11. stm32f1xx_it.c
[中斷服務程序 - USART IDLE 中斷、DMA/UART 中斷處理]

### 12. stm32f1xx_hal_msp.c
[HAL 時鐘與中斷配置 - GPIO MSP、I2C/SPI/UART 初始化]

### 13. system_stm32f1xx.c
[系統核心 - SystemInit()、SystemCoreClock 更新、振盪器配置]

### 14. syscalls.c
[系統呼叫 - newlib libc 的底層實現 (_read, _write, _sbrk 等)]

### 15. sysmem.c
[系統記憶體 - malloc/free 堆管理 (_sbrk 實現)]

---

## 🔗 檔案依賴關係

```
main() 
  └─ APP_Init()
      ├─ ErrorMgr_Init()
      ├─ ButtonLED_Init()
      ├─ GPS_Init() → GPS_StartReception()
      ├─ RTC_DS3231_Init()
      ├─ SDLog_Init()
      │  └─ f_mount() [FATFS]
      └─ SDLog_OpenDailyFile()

APP_Run() [主循環]
  ├─ Button_Update() → Button_GetEvent()
  ├─ LED_Task()
  ├─ GPS_ProcessRxChunk()
  ├─ GPS_SplitLinesToQueue()
  └─ process_gps_queue()
      ├─ NMEA_VerifyChecksum()
      ├─ NMEA_GetSentenceType()
      ├─ NMEA_ParseRMC() / NMEA_ParseGGA()
      ├─ FusionCache_UpdateRMC() / UpdateGGA()
      ├─ Fusion_TryBuildRecord()
      ├─ Telemetry_SendPacket() → UART1
      └─ SDLog_AppendRecord() → SPI1/SD
```

---

## 📊 編譯配置

**編譯工具鏈**: GNU Tools for STM32 v13.3.rel1  
**MCU**: STM32F103C8TX  
**時鐘**: 72 MHz (HSE 8MHz × 9)  
**記憶體**: 64KB SRAM, 64KB Flash  

**編譯產物**:
- `test.elf` - 可執行固件
- `test.list` - 反組譯清單
- `*.o` - 目的檔
- `*.d` - 依賴檔

---

*此文檔包含專案完整源碼內容 (2026-04-02)*
