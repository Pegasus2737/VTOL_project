#include "nmea_parser.h"
#include <string.h>
#include <stdlib.h>
#include <ctype.h>

#define NMEA_MAX_FIELDS 20
#define LOCAL_PARSE_BUF 160

/* 將十六進位字元轉換為整數 */
static int hex2int(char c)
{
    if (c >= '0' && c <= '9') return c - '0';
    c = (char)toupper((unsigned char)c);
    if (c >= 'A' && c <= 'F') return c - 'A' + 10;
    return -1;
}

/* NMEA Checksum 驗證：計算 $ 與 * 之間所有字元的 XOR 值 [cite: 1673, 1679] */
bool NMEA_VerifyChecksum(const char *sentence)
{
    if (!sentence || sentence[0] != '$') return false;

    const char *star = strchr(sentence, '*');
    if (!star || !star[1] || !star[2]) return false;

    uint8_t cs = 0;
    for (const char *p = sentence + 1; p < star; ++p) {
        cs ^= (uint8_t)(*p);
    }

    int hi = hex2int(star[1]);
    int lo = hex2int(star[2]);
    if (hi < 0 || lo < 0) return false;

    return cs == (uint8_t)((hi << 4) | lo);
}

/* 判斷 NMEA 語句類型 [cite: 1685, 1689] */
NMEA_SentenceType_t NMEA_GetSentenceType(const char *sentence)
{
    if (!sentence || sentence[0] != '$') return NMEA_UNKNOWN;
    if (strstr(sentence, "RMC") == sentence + 3) return NMEA_RMC;
    if (strstr(sentence, "GGA") == sentence + 3) return NMEA_GGA;
    return NMEA_UNKNOWN;
}

/* 解析 UTC 時間字串 (HHMMSS) [cite: 1690] */
static bool parse_utc(const char *raw, uint8_t *h, uint8_t *m, uint8_t *s)
{
    if (!raw || strlen(raw) < 6) return false;
    char b[3] = {0};
    b[0] = raw[0]; b[1] = raw[1]; *h = (uint8_t)atoi(b);
    b[0] = raw[2]; b[1] = raw[3]; *m = (uint8_t)atoi(b);
    b[0] = raw[4]; b[1] = raw[5]; *s = (uint8_t)atoi(b);
    return true;
}

/* 解析日期字串 (DDMMYY) [cite: 1698] */
static bool parse_date(const char *raw, uint8_t *d, uint8_t *m, uint16_t *y)
{
    if (!raw || strlen(raw) < 6) return false;
    char b[3] = {0};
    b[0] = raw[0]; b[1] = raw[1]; *d = (uint8_t)atoi(b);
    b[0] = raw[2]; b[1] = raw[3]; *m = (uint8_t)atoi(b);
    b[0] = raw[4]; b[1] = raw[5]; *y = (uint16_t)(2000 + atoi(b));
    return true;
}

/* 緯度轉換：ddmm.mmmm -> decimal degree [cite: 1706, 1711] */
double NMEA_ConvertLatitude(const char *raw, char ns)
{
    double v = atof(raw);
    int deg = (int)(v / 100.0);
    double minutes = v - deg * 100.0;
    double out = deg + minutes / 60.0;
    if (ns == 'S') out = -out;
    return out;
}

/* 經度轉換：dddmm.mmmm -> decimal degree [cite: 1715, 1720] */
double NMEA_ConvertLongitude(const char *raw, char ew)
{
    double v = atof(raw);
    int deg = (int)(v / 100.0);
    double minutes = v - deg * 100.0;
    double out = deg + minutes / 60.0;
    if (ew == 'W') out = -out;
    return out;
}

/* 速度單位轉換：節 -> km/h [cite: 1724] */
float NMEA_KnotsToKmh(float knots)
{
    return knots * 1.852f;
}

/* 將語句按逗號切分為欄位 [cite: 1728, 1736] */
static int split_fields(char *payload, char *fields[], int maxf)
{
    int c = 0;
    fields[c++] = payload;
    for (char *p = payload; *p && c < maxf; ++p) {
        if (*p == ',') {
            *p = '\0';
            fields[c++] = p + 1;
        } else if (*p == '*') {
            *p = '\0';
            break;
        }
    }
    return c;
}

/* 解析 RMC 語句 (推薦定位資料) [cite: 1747, 1757] */
int NMEA_ParseRMC(const char *sentence, GPS_RMC_t *rmc)
{
    if (!sentence || !rmc) return 1;
    if (!NMEA_VerifyChecksum(sentence)) return 2;

    char buf[LOCAL_PARSE_BUF] = {0};
    strncpy(buf, sentence + 1, sizeof(buf) - 1);

    char *f[NMEA_MAX_FIELDS] = {0};
    int n = split_fields(buf, f, NMEA_MAX_FIELDS);
    if (n < 10) return 3;

    memset(rmc, 0, sizeof(*rmc));
    if (!parse_utc(f[1], &rmc->hour, &rmc->min, &rmc->sec)) return 4;

    rmc->valid = (f[2][0] == 'A') ? 1 : 0;
    if (!f[3][0] || !f[4][0] || !f[5][0] || !f[6][0]) return 5;

    rmc->latitude_deg  = NMEA_ConvertLatitude(f[3], f[4][0]);
    rmc->longitude_deg = NMEA_ConvertLongitude(f[5], f[6][0]);
    rmc->speed_knots = f[7][0] ? (float)atof(f[7]) : 0.0f;
    rmc->speed_kmh   = NMEA_KnotsToKmh(rmc->speed_knots);
    rmc->course_deg  = f[8][0] ? (float)atof(f[8]) : 0.0f;

    if (!parse_date(f[9], &rmc->day, &rmc->month, &rmc->year)) return 6;
    return 0;
}

/* 解析 GGA 語句 (定位品質與高度資料) [cite: 1767, 1782] */
int NMEA_ParseGGA(const char *sentence, GPS_GGA_t *gga)
{
    if (!sentence || !gga) return 1;
    if (!NMEA_VerifyChecksum(sentence)) return 2;

    char buf[LOCAL_PARSE_BUF] = {0};
    strncpy(buf, sentence + 1, sizeof(buf) - 1);

    char *f[NMEA_MAX_FIELDS] = {0};
    int n = split_fields(buf, f, NMEA_MAX_FIELDS);
    if (n < 10) return 3;

    memset(gga, 0, sizeof(*gga));
    if (!parse_utc(f[1], &gga->hour, &gga->min, &gga->sec)) return 4;
    if (!f[2][0] || !f[3][0] || !f[4][0] || !f[5][0]) return 5;

    gga->latitude_deg  = NMEA_ConvertLatitude(f[2], f[3][0]);
    gga->longitude_deg = NMEA_ConvertLongitude(f[4], f[5][0]);
    gga->fix_quality = f[6][0] ? (uint8_t)atoi(f[6]) : 0;
    gga->satellites  = f[7][0] ? (uint8_t)atoi(f[7]) : 0;
    gga->hdop        = f[8][0] ? (float)atof(f[8]) : 0.0f;
    gga->altitude_m  = f[9][0] ? (float)atof(f[9]) : 0.0f;

    return 0;
}
