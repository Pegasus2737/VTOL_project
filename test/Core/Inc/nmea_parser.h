#ifndef __NMEA_PARSER_H__
#define __NMEA_PARSER_H__

#include "telemetry_record.h"
#include <stdbool.h>

/* --- 解析函数返回值定义 --- */
#define NMEA_PARSE_OK          0  // 成功
#define NMEA_ERR_INVALID_PARAM 1  // 无效参数
#define NMEA_ERR_CHECKSUM      2  // Checksum 验证失败
#define NMEA_ERR_FIELD_COUNT   3  // 字段数不足
#define NMEA_ERR_UTC_PARSE     4  // UTC 时间解析失败
#define NMEA_ERR_EMPTY_FIELDS  5  // 必要字段为空
#define NMEA_ERR_DATE_PARSE    6  // 日期解析失败（RMC）
#define NMEA_ERR_GGA_QUALITY   6  // GGA 质量不足

/**
 * @brief NMEA 語句類型枚舉
 */
typedef enum
{
    NMEA_UNKNOWN = 0,   // 未知類型 [cite: 1652]
    NMEA_RMC,           // 推薦最小定位資訊 (Recommended Minimum Specific GNSS Data) [cite: 1653]
    NMEA_GGA            // GPS 定位資料 (Global Positioning System Fix Data) [cite: 1654]
} NMEA_SentenceType_t;

/* --- 核心驗證與判定函式 --- */

/**
 * @brief 驗證 NMEA 語句的 Checksum [cite: 1656]
 * @param sentence 原始 NMEA 字串
 * @return true 驗證通過 / false 驗證失敗
 */
bool NMEA_VerifyChecksum(const char *sentence);

/**
 * @brief 判定 NMEA 語句的類型 (RMC 或 GGA) [cite: 1656]
 * @param sentence 原始 NMEA 字串
 * @return NMEA_SentenceType_t 語句類型
 */
NMEA_SentenceType_t NMEA_GetSentenceType(const char *sentence);

/* --- 解析函式 --- */

/**
 * @brief 解析 RMC 語句並填入結構體 [cite: 1657]
 * @return 0 成功, 非 0 表示错误代码
 */
int NMEA_ParseRMC(const char *sentence, GPS_RMC_t *rmc);

/**
 * @brief 解析 GGA 語句並填入結構體 [cite: 1657]
 * @return 0 成功, 非 0 表示错误代码
 */
int NMEA_ParseGGA(const char *sentence, GPS_GGA_t *gga);

/* --- 資料轉換工具 --- */

/**
 * @brief 將 NMEA 緯度格式 (ddmm.mmmm) 轉換為十進位度數 [cite: 1657]
 * @param raw 原始字串
 * @param ns  南北緯標示 ('N' 或 'S')
 */
double NMEA_ConvertLatitude(const char *raw, char ns);

/**
 * @brief 將 NMEA 經度格式 (dddmm.mmmm) 轉換為十進位度數 [cite: 1658]
 * @param raw 原始字串
 * @param ew  東西經標示 ('E' 或 'W')
 */
double NMEA_ConvertLongitude(const char *raw, char ew);

/**
 * @brief 將速度單位從 節 (Knots) 轉換為 公里/小時 (km/h) [cite: 1658]
 */
float NMEA_KnotsToKmh(float knots);

#endif /* __NMEA_PARSER_H__ */
