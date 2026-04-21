#ifndef _BUTTON_LED_H_
#define _BUTTON_LED_H_

#include <stdint.h>

/* 按鈕事件類型定義 */
typedef enum
{
    BTN_EVENT_NONE = 0,             // 無事件 [cite: 2133]
    BTN_EVENT_SHORT_PRESS,          // 短按事件 [cite: 2134]
    BTN_EVENT_LONG_PRESS            // 長按事件 [cite: 2135]
} ButtonEvent_t;

/* LED 工作模式定義 */
typedef enum
{
    LED_MODE_OFF = 0,               // 熄滅 [cite: 2139]
    LED_MODE_IDLE_SLOW_BLINK,       // 待機模式：慢閃 [cite: 2140]
    LED_MODE_RUN_FAST_BLINK,        // 運行模式：快閃 [cite: 2141]
    LED_MODE_LOGGING_ON,            // 紀錄中：常亮 [cite: 2142]
    LED_MODE_WARN_DOUBLE_BLINK,     // 警告：連閃兩下 [cite: 2143]
    LED_MODE_ERROR_TRIPLE_BLINK,    // 錯誤：連閃三下 [cite: 2144]
    LED_MODE_FATAL_FAST_BLINK       // 致命錯誤：極快閃爍 [cite: 2145]
} LED_Mode_t;

/* 功能函式宣告 */
void ButtonLED_Init(void);          // 模組初始化 [cite: 2147]
void Button_Update(void);           // 按鈕掃描（放置於主循環） [cite: 2148]
ButtonEvent_t Button_GetEvent(void); // 獲取並清除按鈕事件 [cite: 2149]
void LED_SetMode(LED_Mode_t mode);   // 設定 LED 模式 [cite: 2150]
void LED_Task(void);                // LED 閃爍處理（放置於主循環） [cite: 2151]

#endif
