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
    uint32_t gps_checksum_fail_count; // GPS 校驗碼錯誤次數 [cite: 2241]
    uint32_t gps_parse_fail_count;    // NMEA 解析失敗次數 [cite: 2242]
    uint32_t rtc_read_fail_count;     // RTC 讀取異常次數 [cite: 2243]
    uint32_t sd_mount_fail_count;     // SD 卡掛載失敗次數 [cite: 2244]
    uint32_t sd_write_fail_count;     // SD 卡寫入失敗次數 [cite: 2245]
    uint32_t uart_tx_fail_count;      // UART 傳送失敗次數 [cite: 2246]
} SystemErrorCounters_t;

/* 功能函式宣告 */
void ErrorMgr_Init(void);                        // 初始化計數器 [cite: 2248]
void ErrorMgr_IncGPSChecksumFail(void);          // 增加 GPS 校驗錯誤計數 [cite: 2249]
void ErrorMgr_IncGPSParseFail(void);             // 增加 GPS 解析錯誤計數 [cite: 2250]
void ErrorMgr_IncRTCReadFail(void);              // 增加 RTC 讀取錯誤計數 [cite: 2251]
void ErrorMgr_IncSDMountFail(void);              // 增加 SD 掛載錯誤計數 [cite: 2252]
void ErrorMgr_IncSDWriteFail(void);              // 增加 SD 寫入錯誤計數 [cite: 2253]
void ErrorMgr_IncUARTTxFail(void);               // 增加 UART 傳送錯誤計數 [cite: 2254]
SystemErrorCounters_t ErrorMgr_GetCounters(void); // 獲取當前所有計數值 [cite: 2255]

#endif /* __ERROR_MANAGER_H__ */
