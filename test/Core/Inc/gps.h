#ifndef _GPS_H_
#define _GPS_H_

#include "config.h"
#include <stdbool.h>
#include <stdint.h>

/**
 * @brief GPS 單條語句結構體 [cite: 1792]
 */
typedef struct
{
    char sentence[GPS_SENTENCE_MAX_LEN]; // 儲存 NMEA 字串 [cite: 1794]
    uint16_t len;                        // 字串長度 [cite: 1795]
    uint32_t tick_ms;                    // 接收時的系統時間 [cite: 1796]
} GPS_Sentence_t;

/**
 * @brief GPS 語句環型佇列結構體 [cite: 1798]
 */
typedef struct
{
    GPS_Sentence_t items[GPS_SENTENCE_QUEUE_SIZE]; // 佇列緩衝區 [cite: 1800]
    uint8_t head;                                  // 佇列頭部索引 [cite: 1801]
    uint8_t tail;                                  // 佇列尾部索引 [cite: 1802]
    uint8_t count;                                 // 目前存儲的語句數量 [cite: 1803]
} GPS_SentenceQueue_t;

/* 硬體初始化與接收控制函式 */
void GPS_Init(void);              // 初始化緩衝區與佇列 [cite: 1805]
void GPS_StartReception(void);    // 啟動 DMA 接收與 IDLE 中斷 [cite: 1806]
void GPS_StopReception(void);     // 停止接收 [cite: 1807]

/* 資料處理核心函式 */
void GPS_OnRxEvent(uint16_t size);  // DMA/IDLE 事件回調處理 [cite: 1808]
void GPS_ProcessRxChunk(void);      // 將 DMA 區塊搬移至累加緩衝區 [cite: 1809]
void GPS_SplitLinesToQueue(void);   // 根據換行符斷句並推入佇列 [cite: 1810]
bool GPS_QueuePop(GPS_Sentence_t *out); // 從佇列提取一條待解析語句 [cite: 1811]
uint8_t GPS_GetQueueCount(void);    // 取得隊列中的句子數（用於診斷）

/* GPS 全局緩衝區（用於輪詢模式下的 DMA 數據提取） */
extern uint8_t  g_dma_buf[];           // DMA 直接接收區
extern uint8_t  g_chunk_buf[];         // 單次接收快照區
extern volatile uint16_t g_chunk_len;  // 快照長度
extern volatile uint8_t  g_chunk_ready; // 快照就緒標誌

/* GPS 累積區（用於診斷） */
//extern char     g_acc_buf[];           // 累積區
extern uint16_t g_acc_len;             // 累積區長度

#endif /* _GPS_H_ */
