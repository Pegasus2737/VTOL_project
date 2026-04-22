/**
 * @file app.c
 * @brief 系統主應用邏輯與狀態機實作 [cite: 1393, 2270]
 */

#include "app.h"
#include "gps.h"
#include "nmea_parser.h"
#include "telemetry_record.h"
#include "telemetry.h"
#include "sdlog.h"
#include "rtc_ds3231.h"
#include "button_led.h"
#include "error_manager.h"
#include <stdio.h>
#include <string.h>
/* 系統狀態定義 */
typedef enum {
    SYS_IDLE = 0,    // 待機模式：僅基本監控
    SYS_RUN,         // 運行模式：開始傳送遙測數據至 PC
    SYS_LOGGING      // 記錄模式：同步傳送至 PC 並寫入 SD 卡 [cite: 2280, 2285]
} AppState_t;
extern UART_HandleTypeDef huart2;

/* 靜態全域變數 [cite: 2286, 2289] */
static AppState_t           g_state = SYS_IDLE;
static GPS_FusionCache_t    g_fusion;
static UnifiedTelemetryRecord g_record;
static RTC_DateTime_t       g_rtc;
extern UART_HandleTypeDef huart1;

/* 測試開關：改為 1 啟用虛擬數據測試，改為 0 使用 GPS 實時數據 */
#define USE_TEST_DATA 1

/**
 * @brief 生成虛擬遙測數據用於測試 SD 卡寫入功能
 */
static void APP_GenerateTestData(void) {
    static uint32_t test_counter = 0;
    static uint32_t last_gen_time = 0;
    uint32_t now = HAL_GetTick();
    
    // 依照遙測頻率產生虛擬資料，避免無效高頻更新
    if ((now - last_gen_time) < TELEMETRY_TX_INTERVAL_MS) return;
    last_gen_time = now;
    
    test_counter++;
    
    // 讀取 RTC
    if (!RTC_DS3231_ReadDateTime(&g_rtc)) {
        ErrorMgr_IncRTCReadFail();
    }
    
    // 構造虛擬遙測記錄
    g_record.mcu_tick_ms = now;
    
    // GPS 日期時間 (虛擬：遞增)
    g_record.gps_dt.year = 26;
    g_record.gps_dt.month = 4;
    g_record.gps_dt.day = 20;
    g_record.gps_dt.hour = 12;
    g_record.gps_dt.min = 22 + (test_counter / 600);  // 每 600 筆遞增 1 分鐘
    g_record.gps_dt.sec = (test_counter % 60);
    
    // RTC 日期時間
    g_record.rtc_dt = g_rtc;
    
    // GPS 定位數據 (虛擬)
    g_record.gps_valid = 1;
    g_record.fix_quality = 1;
    g_record.satellites = 8;
    g_record.hdop = 2.5f;
    g_record.latitude_deg = 25.01f + (test_counter * 0.00001f);  // 緩慢遞增
    g_record.longitude_deg = 121.54f + (test_counter * 0.00001f);
    g_record.altitude_m = 25.0f + (float)(test_counter % 50);
    g_record.speed_knots = 1.5f + ((test_counter / 100) % 5);
    g_record.speed_kmh = 2.8f + ((test_counter / 100) % 9);
    g_record.course_deg = (float)((test_counter * 5) % 360);
    g_record.rmc_ok = 1;
    g_record.gga_ok = 1;
    
    g_record.record_ready = 1;
    
    // 輸出進度
    if ((test_counter % 10) == 0) {
        char msg[64];
        snprintf(msg, sizeof(msg), "[TEST] Generated %lu records\r\n", test_counter);
        HAL_UART_Transmit(&huart1, (uint8_t *)msg, strlen(msg), 100);
    }
}
/**
 * @brief 進入新狀態並更新 LED 指示燈模式 [cite: 2290]
 */
static void enter_state(AppState_t s) {
    g_state = s;
    switch (s) {
        case SYS_IDLE:
            LED_SetMode(LED_MODE_IDLE_SLOW_BLINK);
            {
                char msg[64];
                snprintf(msg, sizeof(msg), "[DBG] state -> IDLE\r\n");
                HAL_UART_Transmit(&huart1, (uint8_t *)msg, strlen(msg), 100);
            }
            break;
        case SYS_RUN:
            LED_SetMode(LED_MODE_RUN_FAST_BLINK);
            {
                char msg[64];
                snprintf(msg, sizeof(msg), "[DBG] state -> RUN\r\n");
                HAL_UART_Transmit(&huart1, (uint8_t *)msg, strlen(msg), 100);
            }
            break;
        case SYS_LOGGING:
            LED_SetMode(LED_MODE_LOGGING_ON);
            {
                char msg[64];
                snprintf(msg, sizeof(msg), "[DBG] state -> LOGGING\r\n");
                HAL_UART_Transmit(&huart1, (uint8_t *)msg, strlen(msg), 100);
            }
            break;
    }
}

/**
 * @brief 處理按鈕事件觸發狀態切換 [cite: 2302]
 */
static void handle_button(void) {
    ButtonEvent_t evt = Button_GetEvent();
    if (evt == BTN_EVENT_NONE) return;

    switch (g_state) {
        case SYS_IDLE:
            if (evt == BTN_EVENT_SHORT_PRESS)      enter_state(SYS_RUN);
            else if (evt == BTN_EVENT_LONG_PRESS)  enter_state(SYS_LOGGING);
            break;
        case SYS_RUN:
            if (evt == BTN_EVENT_SHORT_PRESS)      enter_state(SYS_LOGGING);
            else if (evt == BTN_EVENT_LONG_PRESS)  enter_state(SYS_IDLE);
            break;
        case SYS_LOGGING:
            if (evt == BTN_EVENT_SHORT_PRESS)      enter_state(SYS_RUN);
            else if (evt == BTN_EVENT_LONG_PRESS)  enter_state(SYS_IDLE);
            break;
    }
}

/* 調試用：上一次輸出診斷的時間 */
static uint32_t last_gps_diag_time = 0;

// 外部计数器 - 来自中断处理程序
extern volatile uint32_t g_usart2_irq_count;
extern volatile uint32_t g_dma_data_received;

/**
 * @brief 处理 GPS 队列中的数据并进行解析与融合 [cite: 2316]
 */
static void process_gps_queue(void) {
    GPS_Sentence_t s;
    static uint32_t sentence_count = 0;
    static uint32_t rmc_count = 0, gga_count = 0, unknown_count = 0;
    static uint32_t last_stats_time = 0;
    
    while (GPS_QueuePop(&s)) {
        sentence_count++;
        last_gps_diag_time = HAL_GetTick();  // 更新最后 GPS 活动时间
        
        // 1. 验证 Checksum [cite: 2321]
        uint8_t checksum_ok = NMEA_VerifyChecksum(s.sentence);
        
        // 2. 判断 NMEA 语句类型并解析 [cite: 2326]
        NMEA_SentenceType_t type = NMEA_GetSentenceType(s.sentence);
        
        if (!checksum_ok) {
            ErrorMgr_IncGPSChecksumFail();
            continue;
        }
        
        if (type == NMEA_RMC) {
            rmc_count++;
            GPS_RMC_t rmc;
            memset(&rmc, 0, sizeof(rmc));
            int parse_result = NMEA_ParseRMC(s.sentence, &rmc);
            
            if (parse_result == 0) {
                FusionCache_UpdateRMC(&g_fusion, &rmc);
                /*
                // 解析成功，輸出 NMEA
                char nmea_line[256];
                snprintf(nmea_line, sizeof(nmea_line), "[NMEA] %s\r\n", s.sentence);
                HAL_UART_Transmit(&huart1, (uint8_t *)nmea_line, strlen(nmea_line), 100);
                */
            } else if (parse_result != 4) { // 忽略因無信號導致的 UTC 時間解析失敗
                ErrorMgr_IncGPSParseFail();
                /*
                char fail_msg[256];
                snprintf(fail_msg, sizeof(fail_msg), "[DBG] RMC parse fail (code %d): %s\r\n", parse_result, s.sentence);
                HAL_UART_Transmit(&huart1, (uint8_t *)fail_msg, strlen(fail_msg), 100);
                */
            }
        }
        else if (type == NMEA_GGA) {
            gga_count++;
            GPS_GGA_t gga;
            memset(&gga, 0, sizeof(gga));
            int parse_result = NMEA_ParseGGA(s.sentence, &gga);
            
            if (parse_result == 0) {
                FusionCache_UpdateGGA(&g_fusion, &gga);
                /*
                // 解析成功，輸出 NMEA
                char nmea_line[256];
                snprintf(nmea_line, sizeof(nmea_line), "[NMEA] %s\r\n", s.sentence);
                HAL_UART_Transmit(&huart1, (uint8_t *)nmea_line, strlen(nmea_line), 100);
                */
            } else if (parse_result != 4) { // 忽略因無信號導致的 UTC 時間解析失敗
                ErrorMgr_IncGPSParseFail();
                /*
                char fail_msg[256];
                snprintf(fail_msg, sizeof(fail_msg), "[DBG] GGA parse fail (code %d): %s\r\n", parse_result, s.sentence);
                HAL_UART_Transmit(&huart1, (uint8_t *)fail_msg, strlen(fail_msg), 100);
                */
            }
        } else {
            unknown_count++;
        }

        // 3. 读取 RTC 并尝试构建完整遥测记录 [cite: 2344, 2346]
        if (!RTC_DS3231_ReadDateTime(&g_rtc)) {
            ErrorMgr_IncRTCReadFail();
        }

        Fusion_TryBuildRecord(&g_fusion, &g_record, &g_rtc, HAL_GetTick());
    }
    
    // 定期输出统计信息
    uint32_t now = HAL_GetTick();
    if ((now - last_stats_time) >= 3000) {
        last_stats_time = now;
        SystemErrorCounters_t errs = ErrorMgr_GetCounters();
        uint32_t gps_age = HAL_GetTick() - last_gps_diag_time;
        
        /*
        char stats[256];
        snprintf(stats, sizeof(stats),
            "[DBG] mode=%s sentences=%lu records=%lu last_gps=%lums ago rmc=%u gga=%u chk=%lu parse=%lu rtc=%lu uart=%lu sdw=%lu\r\n",
            (g_state == SYS_IDLE ? "IDLE" : (g_state == SYS_RUN ? "RUN" : "LOGGING")),
            sentence_count, g_record.record_ready ? 1 : 0, gps_age,
            g_fusion.rmc_valid, g_fusion.gga_valid, 
            errs.gps_checksum_fail_count, errs.gps_parse_fail_count,
            errs.rtc_read_fail_count, errs.uart_tx_fail_count, errs.sd_write_fail_count);
        HAL_UART_Transmit(&huart1, (uint8_t *)stats, strlen(stats), 100);
        
        char type_count[256];
        snprintf(type_count, sizeof(type_count),
            "[DBG] type_count rmc=%lu gga=%lu unknown=%lu\r\n",
            rmc_count, gga_count, unknown_count);
        HAL_UART_Transmit(&huart1, (uint8_t *)type_count, strlen(type_count), 100);
        */
    }
}
static void output_record(void) {
    static uint32_t last_tx_tick = 0;

    // 如果无法融合则直接返回
    if (!g_record.record_ready) return;

    // 統一遙測/記錄輸出節流：避免高頻重複資料淹沒上位機
    uint32_t now = HAL_GetTick();
    if ((uint32_t)(now - last_tx_tick) < TELEMETRY_TX_INTERVAL_MS) return;
    last_tx_tick = now;

    // 路径 A：USART1 传送至 PC GUI [cite: 2352, 2354]
    if (g_state == SYS_RUN || g_state == SYS_LOGGING) {
        if (!Telemetry_SendPacket(&g_record))
            ErrorMgr_IncUARTTxFail();
    }

    // 路径 B：SPI1 写入 SD 卡 [cite: 2357, 2359]
    if (g_state == SYS_LOGGING) {
        if (!SDLog_AppendRecord(&g_record))
            ErrorMgr_IncSDWriteFail();
    }

    g_record.record_ready = 0; // 重置准备标记 [cite: 2362]
}

/**
 * @brief 應用程式初始化 [cite: 2363]
 */
void APP_Init(void) {
    ErrorMgr_Init();
    ButtonLED_Init();
    GPS_Init();
    FusionCache_Reset(&g_fusion);
    TelemetryRecord_Reset(&g_record);
    RTC_DS3231_Init();

    // 启动消息
    char boot_msg[96];
    snprintf(boot_msg, sizeof(boot_msg), "[BOOT] Hello from STM32F103 (USART1)\r\n");
    HAL_UART_Transmit(&huart1, (uint8_t *)boot_msg, strlen(boot_msg), 100);

    // 诊断：RTC 初始化成功
    RTC_DateTime_t test_rtc;
    if (RTC_DS3231_ReadDateTime(&test_rtc)) {
        char diag[128];
        snprintf(diag, sizeof(diag), "[DBG] RTC init ok: %04u-%02u-%02u %02u:%02u:%02u\r\n",
                 test_rtc.year + 2000, test_rtc.month, test_rtc.day,
                 test_rtc.hour, test_rtc.min, test_rtc.sec);
        HAL_UART_Transmit(&huart1, (uint8_t *)diag, strlen(diag), 100);
    } else {
        char diag[96];
        snprintf(diag, sizeof(diag), "[DBG] RTC init fail\r\n");
        HAL_UART_Transmit(&huart1, (uint8_t *)diag, strlen(diag), 100);
    }

    // SD 卡初始化 [cite: 2372]
    if (SDLog_Init()) {
        char diag[64];
        snprintf(diag, sizeof(diag), "[DBG] SD card mount OK\r\n");
        HAL_UART_Transmit(&huart1, (uint8_t *)diag, strlen(diag), 100);
    } else {
        char diag[64];
        snprintf(diag, sizeof(diag), "[DBG] SD card mount FAIL\r\n");
        HAL_UART_Transmit(&huart1, (uint8_t *)diag, strlen(diag), 100);
        ErrorMgr_IncSDMountFail();
    }

    // 建立当日文件 [cite: 2374, 2377]
    if (RTC_DS3231_ReadDateTime(&g_rtc)) {
        if (SDLog_OpenDailyFile(&g_rtc)) {
            char diag[64];
            snprintf(diag, sizeof(diag), "[DBG] Daily file open OK\r\n");
            HAL_UART_Transmit(&huart1, (uint8_t *)diag, strlen(diag), 100);
            SDLog_WriteHeaderIfNeeded();
        } else {
            char diag[64];
            snprintf(diag, sizeof(diag), "[DBG] Daily file open FAIL\r\n");
            HAL_UART_Transmit(&huart1, (uint8_t *)diag, strlen(diag), 100);
        }
    }

    GPS_StartReception(); // 开始 DMA 接收 [cite: 2379]
    enter_state(SYS_IDLE);
    char init_done[64];
    snprintf(init_done, sizeof(init_done), "[DBG] app init done\r\n");
    HAL_UART_Transmit(&huart1, (uint8_t *)init_done, strlen(init_done), 100);
}

/**
 * @brief 應用程式主循環任務 [cite: 2381]
 */
void APP_Run(void) {
    static uint32_t last_early_diag = 0;
    static uint16_t last_read_pos = 0;  // 追蹤上次讀取位置
    static uint8_t temp_buf[GPS_DMA_BUF_SIZE];  // 臨時緩衝區
    static uint32_t heartbeat_counter = 0;
    
    Button_Update();        // 按鈕掃描 [cite: 2383]
    LED_Task();             // 指示燈任務 [cite: 2384]
    handle_button();        // 處理按鈕事件 [cite: 2385]

    // 定期檢查 DMA 計數器並處理接收到的數據（循環 DMA 模式）
    extern DMA_HandleTypeDef hdma_usart2_rx;
    uint16_t current_dma = __HAL_DMA_GET_COUNTER(&hdma_usart2_rx);
    uint16_t current_write_pos = GPS_DMA_BUF_SIZE - current_dma;  // DMA 寫入位置
    
    if (current_write_pos != last_read_pos) {
        uint16_t data_len = 0;
        
        // 處理循環 DMA 可能的回繞
        if (current_write_pos > last_read_pos) {
            // 簡單情況：未回繞，直接複製
            data_len = current_write_pos - last_read_pos;
            memcpy(temp_buf, g_dma_buf + last_read_pos, data_len);
        } else if (current_write_pos < last_read_pos) {
            // 回繞情況：分兩段複製
            uint16_t len1 = GPS_DMA_BUF_SIZE - last_read_pos;
            uint16_t len2 = current_write_pos;
            memcpy(temp_buf, g_dma_buf + last_read_pos, len1);
            memcpy(temp_buf + len1, g_dma_buf, len2);
            data_len = len1 + len2;
        }
        // 若相等則無新數據
        
        if (data_len > 0 && data_len <= GPS_DMA_BUF_SIZE) {
            memcpy(g_chunk_buf, temp_buf, data_len);
            g_chunk_len = data_len;
            g_chunk_ready = 1;
        }
        
        last_read_pos = current_write_pos;
    }
    
    
    GPS_ProcessRxChunk();   // 處理 DMA 資料區塊 [cite: 2386]
    GPS_SplitLinesToQueue(); // NMEA 斷句 [cite: 2387]

#if USE_TEST_DATA
    // 使用虛擬測試數據
    APP_GenerateTestData();
#else
    // 使用真實 GPS 數據
    process_gps_queue();    // 解析與融合 [cite: 2388]
#endif
    
    output_record();        // 輸出結果 [cite: 2389]
}
