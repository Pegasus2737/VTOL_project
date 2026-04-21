/**
 * @file    sdlog.h
 * @brief   SD Card Logging Module (FATFS based)
 * @details 負責本地 CSV 資料儲存、每日自動開檔與緩衝區同步策略。
 */

#ifndef __SDLOG_H__
#define __SDLOG_H__

#include "telemetry_record.h" // 依賴統一遙測紀錄結構 [cite: 1987]
#include <stdbool.h>
#include <stdint.h>

/**
 * @brief  初始化 SD 卡與 FATFS 檔案系統
 * @return true: 掛載成功; false: 失敗
 */
bool SDLog_Init(void);

/**
 * @brief  根據日期開啟或建立對應的 CSV 檔案 (例如: GPS_20260324.CSV)
 * @param  dt: 指向包含目前日期的結構體指標
 * @return true: 開啟成功; false: 失敗
 */
bool SDLog_OpenDailyFile(const RTC_DateTime_t *dt);

/**
 * @brief  若檔案為新建立(大小為0)，則寫入 CSV 標頭欄位
 * @return true: 寫入成功或不需寫入; false: 磁碟錯誤
 */
bool SDLog_WriteHeaderIfNeeded(void);

/**
 * @brief  將遙測紀錄結構轉換為單行 CSV 字串
 * @param  rec: 原始紀錄資料
 * @param  out: 輸出的字串緩衝區
 * @param  max_len: 緩衝區最大長度
 * @return true: 轉換成功; false: 長度溢出
 */
bool SDLog_FormatCSVLine(const UnifiedTelemetryRecord *rec, char *out, uint16_t max_len);

/**
 * @brief  將單筆紀錄追加(Append)至 SD 卡檔案中
 * @details 內部會根據 N_RECORDS 設定自動觸發 f_sync()
 * @param  rec: 欲記錄的結構體
 * @return true: 寫入成功; false: 寫入失敗
 */
bool SDLog_AppendRecord(const UnifiedTelemetryRecord *rec);

/**
 * @brief  強制將緩衝區資料同步至實體磁碟 (f_sync)
 * @return true: 同步成功; false: 失敗
 */
bool SDLog_Flush(void);

#endif /* __SDLOG_H__ */
