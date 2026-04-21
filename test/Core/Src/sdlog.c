#include "sdlog.h"
#include "config.h"
#include "fatfs.h"
#include <stdio.h>
#include <string.h>

/* 模組靜態變數 */
static FATFS g_fs;                          // FatFs 檔案系統物件 [cite: 2003]
static FIL g_file;                          // 檔案物件 [cite: 2004]
static char g_filename[LOG_FILENAME_BUF_SIZE]; // 儲存當前檔名 [cite: 2005]
static uint8_t g_file_opened = 0;           // 檔案開啟狀態旗標 [cite: 2006]
static uint32_t g_record_counter = 0;       // 記錄筆數計數器，用於觸發 f_sync [cite: 2007]

/* CSV 標頭定義 [cite: 2008, 2009] */
static const char *csv_header =
    "mcu_tick_ms,gps_date,gps_time,rtc_date,rtc_time,gps_valid,fix_quality,"
    "satellites,hdop,latitude_deg,longitude_deg,altitude_m,speed_knots,"
    "speed_kmh,course_deg,rmc_ok,gga_ok\r\n";

/**
 * @brief 初始化 SD 卡並掛載檔案系統
 */
bool SDLog_Init(void) {
    extern UART_HandleTypeDef huart1;
    
    // 嘗試掛載邏輯磁碟機，1 表示立即掛載 [cite: 2012]
    FRESULT res = f_mount(&g_fs, "", 1);
    
    if (res != FR_OK) {
        char diag[96];
        snprintf(diag, sizeof(diag), "[DBG] f_mount() FAIL, code=%d (0x%02X)\r\n", res, res);
        HAL_UART_Transmit(&huart1, (uint8_t *)diag, strlen(diag), 100);
        return false;
    }
    
    return true;
}

/**
 * @brief 根據日期建立或開啟 CSV 檔案
 */
bool SDLog_OpenDailyFile(const RTC_DateTime_t *dt) {
    extern UART_HandleTypeDef huart1;
    if (!dt) return false;

    // 格式化檔名为 8.3 兼容格式，例如: G010101.CSV (G + MDDYY 或 G + MMDD) [cite: 2017, 2018, 2019]
    // 8.3 格式：主名最多 8 个字符，扩展名最多 3 个字符
    // 使用 MMDD 因为 year 在 RTC 中总是 2001+偏移
    snprintf(g_filename, sizeof(g_filename), "GPS%02u%02u.CSV",
             dt->month, dt->day);

    // 以「總是開啟並具備寫入權限」模式打開檔案 [cite: 2020]
    FRESULT res = f_open(&g_file, g_filename, FA_OPEN_ALWAYS | FA_WRITE);
    if (res != FR_OK) {
        char diag[96];
        snprintf(diag, sizeof(diag), "[DBG] f_open(%s) FAIL, code=%d\r\n", g_filename, res);
        HAL_UART_Transmit(&huart1, (uint8_t *)diag, strlen(diag), 100);
        return false;
    }

    // 將檔案指標移至末尾以便續寫 [cite: 2023]
    res = f_lseek(&g_file, f_size(&g_file));
    if (res != FR_OK) {
        char diag[96];
        snprintf(diag, sizeof(diag), "[DBG] f_lseek() FAIL, code=%d\r\n", res);
        HAL_UART_Transmit(&huart1, (uint8_t *)diag, strlen(diag), 100);
        f_close(&g_file);
        return false;
    }

    g_file_opened = 1;
    return true;
}

/**
 * @brief 若檔案為空，則寫入 CSV 標頭
 */
bool SDLog_WriteHeaderIfNeeded(void) {
    if (!g_file_opened) return false;

    if (f_size(&g_file) == 0) {
        UINT bw = 0;
        // 寫入標頭字串 [cite: 2036]
        if (f_write(&g_file, csv_header, strlen(csv_header), &bw) != FR_OK) {
            return false;
        }
        if (bw != strlen(csv_header)) return false;

        // 立即同步，確保標頭寫入物理磁區 [cite: 2039]
        if (f_sync(&g_file) != FR_OK) return false;
    }
    return true;
}

/**
 * @brief 將遙測紀錄轉換為 CSV 字串格式
 */
bool SDLog_FormatCSVLine(const UnifiedTelemetryRecord *rec, char *out, uint16_t max_len) {
    if (!rec || !out) return false;

    int n = snprintf(out, max_len,
        "%lu,%04u%02u%02u,%02u%02u%02u,%04u%02u%02u,%02u%02u%02u,%u,%u,%u,"
        "%.2f,%.6f,%.6f,%.2f,%.2f,%.2f,%.2f,%u,%u\r\n",
        (unsigned long)rec->mcu_tick_ms,
        rec->gps_dt.year, rec->gps_dt.month, rec->gps_dt.day,
        rec->gps_dt.hour, rec->gps_dt.min, rec->gps_dt.sec,
        rec->rtc_dt.year, rec->rtc_dt.month, rec->rtc_dt.day,
        rec->rtc_dt.hour, rec->rtc_dt.min, rec->rtc_dt.sec,
        rec->gps_valid, rec->fix_quality, rec->satellites,
        rec->hdop, rec->latitude_deg, rec->longitude_deg,
        rec->altitude_m, rec->speed_knots, rec->speed_kmh,
        rec->course_deg, rec->rmc_ok, rec->gga_ok);

    return (n > 0 && n < (int)max_len);
}

/**
 * @brief 新增一筆記錄到 SD 卡
 */
bool SDLog_AppendRecord(const UnifiedTelemetryRecord *rec) {
    if (!g_file_opened || !rec) return false;

    char line[CSV_LINE_BUF_SIZE] = {0};
    if (!SDLog_FormatCSVLine(rec, line, sizeof(line))) return false;

    UINT bw = 0;
    FRESULT res;
    // 執行寫入動作 [cite: 2075]
    res = f_write(&g_file, line, strlen(line), &bw);
    if (res != FR_OK) {
        extern UART_HandleTypeDef huart1;
        char diag[64];
        snprintf(diag, sizeof(diag), "[DBG] f_write() FAIL, code=%d\r\n", res);
        HAL_UART_Transmit(&huart1, (uint8_t *)diag, strlen(diag), 100);
        return false;
    }
    if (bw != strlen(line)) return false;

    g_record_counter++;

    // 根據設定頻率定期執行 f_sync，平衡效能與資料安全 [cite: 2077]
    if ((g_record_counter % SDLOG_FLUSH_EVERY_N_RECORDS) == 0) {
        return SDLog_Flush();
    }

    return true;
}

/**
 * @brief 強制同步緩衝區資料到 SD 卡
 */
bool SDLog_Flush(void) {
    if (!g_file_opened) return false;
    FRESULT res = f_sync(&g_file);
    if (res != FR_OK) {
        extern UART_HandleTypeDef huart1;
        char diag[64];
        snprintf(diag, sizeof(diag), "[DBG] f_sync() FAIL, code=%d\r\n", res);
        HAL_UART_Transmit(&huart1, (uint8_t *)diag, strlen(diag), 100);
        return false;
    }
    return true;
}
