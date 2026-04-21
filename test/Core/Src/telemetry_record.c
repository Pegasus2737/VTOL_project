#include "telemetry_record.h"
#include <string.h> // 提供 memset 使用 [cite: 1587]

/**
 * @brief 重置統一遙測紀錄結構
 */
void TelemetryRecord_Reset(UnifiedTelemetryRecord *rec)
{
    memset(rec, 0, sizeof(*rec));
}

/**
 * @brief 重置 GPS 融合快取
 */
void FusionCache_Reset(GPS_FusionCache_t *cache)
{
    memset(cache, 0, sizeof(*cache));
}

/**
 * @brief 更新快取中的 RMC 資料
 */
void FusionCache_UpdateRMC(GPS_FusionCache_t *cache, const GPS_RMC_t *rmc)
{
    cache->rmc = *rmc;
    cache->rmc_valid = 1;
    cache->rmc_arrival_tick = HAL_GetTick();
}

/**
 * @brief 更新快取中的 GGA 資料
 */
void FusionCache_UpdateGGA(GPS_FusionCache_t *cache, const GPS_GGA_t *gga)
{
    cache->gga = *gga;
    cache->gga_valid = 1;
    cache->gga_arrival_tick = HAL_GetTick();
}

/**
 * @brief 檢查 RMC 與 GGA 是否屬於同一個 UTC 秒數或相鄰秒數 (允許±1秒偏差)
 */
static bool same_utc(const GPS_FusionCache_t *cache)
{
    // 允許秒數相差最多 1 秒 (考慮到 GPS 句子的異步性)
    int rmc_sec = cache->rmc.hour * 3600 + cache->rmc.min * 60 + cache->rmc.sec;
    int gga_sec = cache->gga.hour * 3600 + cache->gga.min * 60 + cache->gga.sec;
    int diff = rmc_sec - gga_sec;
    
    // 正常情況：差異在 ±1 秒內 (允許跨越分界)
    return (diff == 0 || diff == 1 || diff == -1 || 
            diff == 86399 ||  // 23:59:59 vs 00:00:00 (跨午夜)
            diff == -86399);  // 00:00:00 vs 23:59:59
}

/**
 * @brief 嘗試融合快取資料並建構正式紀錄
 * @return true: 融合成功; false: 資料未就緒或不同步
 */
bool Fusion_TryBuildRecord(GPS_FusionCache_t *cache,
                           UnifiedTelemetryRecord *rec,
                           const RTC_DateTime_t *rtc,
                           uint32_t tick_ms)
{
    // 1. 基礎有效性檢查：必須兩者皆有值且時間同步 [cite: 1616, 1617]
    if (!cache->rmc_valid || !cache->gga_valid) return false;
    if (!same_utc(cache)) return false;

    // 2. 定位狀態檢查：RMC 必須為 'A'(Valid)，GGA Fix Quality 必須大於 0 [cite: 1618, 1619]
    if (!cache->rmc.valid) return false;
    if (cache->gga.fix_quality == 0) return false;

    // 3. 開始寫入紀錄 [cite: 1620]
    TelemetryRecord_Reset(rec);
    rec->mcu_tick_ms = tick_ms;

    // 填入 GPS UTC 時間與日期 [cite: 1622]
    rec->gps_dt.year  = cache->rmc.year;
    rec->gps_dt.month = cache->rmc.month;
    rec->gps_dt.day   = cache->rmc.day;
    rec->gps_dt.hour  = cache->rmc.hour;
    rec->gps_dt.min   = cache->rmc.min;
    rec->gps_dt.sec   = cache->rmc.sec;

    // 填入 DS3231 RTC 本地時間 (若提供) [cite: 1625]
    if (rtc) rec->rtc_dt = *rtc;

    // 填入定位品質參數 [cite: 1626, 1628, 1630]
    rec->gps_valid   = cache->rmc.valid;
    rec->fix_quality = cache->gga.fix_quality;
    rec->satellites  = cache->gga.satellites;
    rec->hdop        = cache->gga.hdop;

    // 填入座標與高度資料 [cite: 1631, 1633]
    rec->latitude_deg  = cache->rmc.latitude_deg;
    rec->longitude_deg = cache->rmc.longitude_deg;
    rec->altitude_m    = cache->gga.altitude_m;

    // 填入運動參數 [cite: 1635, 1637, 1639]
    rec->speed_knots   = cache->rmc.speed_knots;
    rec->speed_kmh     = cache->rmc.speed_kmh;
    rec->course_deg    = cache->rmc.course_deg;

    // 4. 設置就緒旗標 [cite: 1640, 1641, 1642]
    rec->rmc_ok = 1;
    rec->gga_ok = 1;
    rec->record_ready = 1;

    return true;
}
