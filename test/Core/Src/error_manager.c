#include "error_manager.h"
#include <string.h>

/* 全域錯誤計數器變數 */
static SystemErrorCounters_t g_err;

/**
 * @brief 初始化錯誤計數器，將所有數值清零
 */
void ErrorMgr_Init(void) {
    memset(&g_err, 0, sizeof(g_err));
}

/**
 * @brief GPS Checksum 校驗失敗計數增加
 */
void ErrorMgr_IncGPSChecksumFail(void) {
    g_err.gps_checksum_fail_count++;
}

/**
 * @brief GPS NMEA 語句解析失敗計數增加
 */
void ErrorMgr_IncGPSParseFail(void) {
    g_err.gps_parse_fail_count++;
}

/**
 * @brief RTC (DS3231) 讀取失敗計數增加
 */
void ErrorMgr_IncRTCReadFail(void) {
    g_err.rtc_read_fail_count++;
}

/**
 * @brief SD 卡掛載 (f_mount) 失敗計數增加
 */
void ErrorMgr_IncSDMountFail(void) {
    g_err.sd_mount_fail_count++;
}

/**
 * @brief SD 卡寫入或同步 (f_write/f_sync) 失敗計數增加
 */
void ErrorMgr_IncSDWriteFail(void) {
    g_err.sd_write_fail_count++;
}

/**
 * @brief UART (PC 遙測) 傳送失敗計數增加
 */
void ErrorMgr_IncUARTTxFail(void) {
    g_err.uart_tx_fail_count++;
}

/**
 * @brief 獲取當前所有的錯誤統計數據
 * @return SystemErrorCounters_t 結構體副本
 */
SystemErrorCounters_t ErrorMgr_GetCounters(void) {
    return g_err;
}
