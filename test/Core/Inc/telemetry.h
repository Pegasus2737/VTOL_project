/**
 * @file telemetry.h
 * @brief 遙測協定格式化與傳送模組
 * 負責將 UnifiedTelemetryRecord 轉換為 $TEL ASCII 封包並透過 UART 輸出
 */

#ifndef _TELEMETRY_H_
#define _TELEMETRY_H_

#include "telemetry_record.h" // 依賴統一紀錄結構 [cite: 1927]
#include <stdbool.h>
#include <stdint.h>

/**
 * @brief 將遙測紀錄格式化為 $TEL 封包字串 [cite: 1930]
 * @param rec 指向要轉換的統一紀錄結構 [cite: 1930]
 * @param out 輸出緩衝區 [cite: 1930]
 * @param max_len 緩衝區最大長度 [cite: 1931]
 * @return true 格式化成功 / false 失敗
 */
bool Telemetry_FormatPacket(const UnifiedTelemetryRecord *rec, char *out, uint16_t max_len);

/**
 * @brief 格式化並直接透過 USART1 傳送遙測封包 [cite: 1932]
 * @param rec 指向要傳送的紀錄結構 [cite: 1932]
 * @return true 傳送完成 / false 傳送失敗
 */
bool Telemetry_SendPacket(const UnifiedTelemetryRecord *rec);

/**
 * @brief 計算遙測封包的 Checksum (NMEA 風格 XOR) [cite: 1933]
 * @param payload 封包內容 (不含 $ 與 *) [cite: 1933]
 * @return uint8_t 計算出的校驗值 [cite: 1933]
 */
uint8_t Telemetry_CalcChecksum(const char *payload);

#endif /* _TELEMETRY_H_ */
