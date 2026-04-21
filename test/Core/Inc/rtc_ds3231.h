/* rtc_ds3231.h */
#ifndef __RTC_DS3231_H__
#define __RTC_DS3231_H__

#include "telemetry_record.h" // 引用 RTC_DateTime_t 結構定義
#include <stdbool.h>

/**
 * @brief 初始化 DS3231 RTC 模組
 * @return true: 初始化成功; false: 失敗 [cite: 2092]
 */
bool RTC_DS3231_Init(void);

/**
 * @brief 從 DS3231 讀取當前日期與時間
 * @param dt 指向儲存時間資料的結構體指標 [cite: 2093]
 * @return true: 讀取成功; false: 傳輸失敗 [cite: 2108]
 */
bool RTC_DS3231_ReadDateTime(RTC_DateTime_t *dt);

#endif /* __RTC_DS3231_H__ */
