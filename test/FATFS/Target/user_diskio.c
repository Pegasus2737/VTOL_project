/* USER CODE BEGIN Header */
/**
 ******************************************************************************
  * @file    user_diskio.c
  * @brief   This file includes a diskio driver skeleton to be completed by the user.
  ******************************************************************************
  * @attention
  *
  * Copyright (c) 2026 STMicroelectronics.
  * All rights reserved.
  *
  * This software is licensed under terms that can be found in the LICENSE file
  * in the root directory of this software component.
  * If no LICENSE file comes with this software, it is provided AS-IS.
  *
  ******************************************************************************
  */
 /* USER CODE END Header */

#ifdef USE_OBSOLETE_USER_CODE_SECTION_0
/*
 * Warning: the user section 0 is no more in use (starting from CubeMx version 4.16.0)
 * To be suppressed in the future.
 * Kept to ensure backward compatibility with previous CubeMx versions when
 * migrating projects.
 * User code previously added there should be copied in the new user sections before
 * the section contents can be deleted.
 */
/* USER CODE BEGIN 0 */
/* USER CODE END 0 */
#endif

/* USER CODE BEGIN DECL */

/* Includes ------------------------------------------------------------------*/
#include <string.h>
#include <stdio.h>
#include "ff_gen_drv.h"
#include "main.h"

/* Private typedef -----------------------------------------------------------*/
/* Private define ------------------------------------------------------------*/
#define SD_CMD0    0       /* GO_IDLE_STATE */
#define SD_CMD8    8       /* SEND_IF_COND */
#define SD_CMD55   55      /* APP_CMD */
#define SD_ACMD41  41      /* SD_SEND_OP_COND (after CMD55) */
#define SD_CMD17   17      /* READ_SINGLE_BLOCK */
#define SD_CMD24   24      /* WRITE_SINGLE_BLOCK */
#define SD_INIT_TIMEOUT  100
#define SECTOR_SIZE      512
#define DATA_START_BLOCK 0xFE
#define DATA_RESP_OK     0x05

/* Private variables ---------------------------------------------------------*/
/* Disk status */
static volatile DSTATUS Stat = STA_NOINIT;

/* Card type: 0=unknown, 1=SDSC, 2=SDHC/SDXC */
static uint8_t CardType = 0;

/* External variables from CubeMX */
extern SPI_HandleTypeDef hspi1;
extern UART_HandleTypeDef huart1;

/* NOTE: For best SD card performance, ensure PA6 (MISO) has a 10kΩ pull-up to 3.3V
   This can be added externally or configured in CubeMX GPIO settings
   If not configured, SD read will fail with all 0x00 bytes */

/* Diagnostic output helper */
static void SD_DebugPrint(const char *msg)
{
  HAL_UART_Transmit(&huart1, (uint8_t *)msg, strlen(msg), 1000);
}

/**
  * @brief  Adjust SPI speed and mode
  * @param  fast: 1 for high speed (read/write), 0 for low speed (init)
  */
static void SD_SetSpeed(uint8_t fast)
{
  if (fast) {
    /* Slower speed: 72MHz / 32 = 2.25MHz (more stable for SD card) */
    hspi1.Init.BaudRatePrescaler = SPI_BAUDRATEPRESCALER_32;
  } else {
    /* Ultra-low speed for init: 72MHz / 256 = 281kHz (absolute minimum) */
    /* This gives weak pull-up maximum time to charge parasitic capacitance */
    hspi1.Init.BaudRatePrescaler = SPI_BAUDRATEPRESCALER_256;
  }
  
  /* Use SPI Mode 3 (CPOL=1, CPHA=1) for better signal sampling with weak pull-up */
  /* This delays data sampling to the second clock edge, allowing MISO signal to rise */
  hspi1.Init.CLKPolarity = SPI_POLARITY_HIGH;    /* CPOL=1 */
  hspi1.Init.CLKPhase = SPI_PHASE_2EDGE;         /* CPHA=1 */
  
  HAL_SPI_Init(&hspi1);
}

/* USER CODE END DECL */


/* Private functions ---------------------------------------------------------*/

/**
  * @brief  SD card SPI write byte
  * @param  byte: byte to write
  */
static void SD_SPI_WriteByte(uint8_t byte)
{
  HAL_SPI_Transmit(&hspi1, &byte, 1, 1000);
}

/**
  * @brief  SD card SPI read byte
  * @retval byte read
  */
static uint8_t SD_SPI_ReadByte(void)
{
  uint8_t byte = 0xFF;
  HAL_SPI_TransmitReceive(&hspi1, &byte, &byte, 1, 1000);
  return byte;
}

/**
  * @brief  SD card CS control
  * @param  level: 0 = select, 1 = deselect
  */
static void SD_CS_Control(uint8_t level)
{
  if (level)
    HAL_GPIO_WritePin(SD_CS_Pin_GPIO_Port, SD_CS_Pin_Pin, GPIO_PIN_SET);
  else
    HAL_GPIO_WritePin(SD_CS_Pin_GPIO_Port, SD_CS_Pin_Pin, GPIO_PIN_RESET);
}

/**
  * @brief  Wait for SD card response
  * @param  timeout: max attempts
  * @retval response byte or 0xFF if timeout
  */
static uint8_t SD_WaitResponse(uint16_t timeout)
{
  uint8_t res;
  for (; timeout; timeout--) {
    res = SD_SPI_ReadByte();
    if (res != 0xFF) return res;
    for(uint8_t i = 0; i < 10; i++);  /* Small delay */
  }
  return 0xFF;
}

/**
  * @brief  Send command without changing CS (for use within read/write sequences)
  * @param  cmd: command index
  * @param  arg: command argument
  * @retval response R1 byte
  */
static uint8_t SD_SendCmd_NoCS(uint8_t cmd, uint32_t arg)
{
  uint8_t crc;
  
  /* Different CRCs for different commands */
  if (cmd == 0) {
    crc = 0x95;    /* CMD0 */
  } else if (cmd == 8) {
    crc = 0x87;    /* CMD8 */
  } else {
    crc = 0xFF;    /* Others - CRC checking disabled in SPI mode */
  }
  
  /* Send command byte: 01CCCCCC */
  SD_SPI_WriteByte(0x40 | cmd);
  
  /* Send 4-byte argument */
  SD_SPI_WriteByte((uint8_t)(arg >> 24));
  SD_SPI_WriteByte((uint8_t)(arg >> 16));
  SD_SPI_WriteByte((uint8_t)(arg >> 8));
  SD_SPI_WriteByte((uint8_t)arg);
  
  /* Send CRC */
  SD_SPI_WriteByte(crc);
  
  /* Wait for response - no CS changes */
  return SD_WaitResponse(100);
}

/**
  * @brief  Send command to SD card (with CS control)
  * @param  cmd: command index
  * @param  arg: command argument
  * @retval response R1 byte
  */
static uint8_t SD_SendCmd(uint8_t cmd, uint32_t arg)
{
  uint8_t res;
  SD_CS_Control(0);
  res = SD_SendCmd_NoCS(cmd, arg);
  SD_CS_Control(1);
  SD_SPI_WriteByte(0xFF);
  return res;
}

/**
  * @brief  Pre-charge MISO line to overcome weak pull-up limitation
  * @detail Temporarily configure PA6 as push-pull output to charge parasitic capacitance
  */
static void SD_MISO_PreCharge(void)
{
  GPIO_InitTypeDef GPIO_InitStruct = {0};
  
  /* Temporarily switch PA6 to push-pull OUTPUT */
  GPIO_InitStruct.Pin = GPIO_PIN_6;
  GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_HIGH;
  HAL_GPIO_Init(GPIOA, &GPIO_InitStruct);
  
  /* Force PA6 high for 1ms to charge the line */
  HAL_GPIO_WritePin(GPIOA, GPIO_PIN_6, GPIO_PIN_SET);
  for (volatile uint32_t i = 0; i < 3000; i++);
  
  /* Switch PA6 back to INPUT with pull-up */
  GPIO_InitStruct.Pin = GPIO_PIN_6;
  GPIO_InitStruct.Mode = GPIO_MODE_INPUT;
  GPIO_InitStruct.Pull = GPIO_PULLUP;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_HIGH;
  HAL_GPIO_Init(GPIOA, &GPIO_InitStruct);
  
  SD_DebugPrint("[DBG] SD init: MISO pre-charge done\r\n");
}

/**
  * @brief  Initialize SD card with modern SD protocol, fallback to CMD1
  * @retval 1 if success, 0 if failed
  */
static uint8_t SD_CardInit(void)
{
  uint8_t res;
  uint16_t i;
  char diag[80];
  
  /* Enable GPIO clock FIRST */
  __HAL_RCC_GPIOA_CLK_ENABLE();
  
  /* Pre-charge MISO line BEFORE any GPIO reconfig to shake loose the old card */
  SD_MISO_PreCharge();
  
  /* Force PA6 (MISO) reconfiguration with MAXIMUM pull-up strength */
  GPIO_InitTypeDef GPIO_InitStruct = {0};
  
  /* PA5 (SCK): Alternate Function Push-Pull, HIGH speed */
  GPIO_InitStruct.Pin = GPIO_PIN_5;
  GPIO_InitStruct.Mode = GPIO_MODE_AF_PP;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_HIGH;
  HAL_GPIO_Init(GPIOA, &GPIO_InitStruct);
  
  /* PA6 (MISO): Input with pull-up */
  GPIO_InitStruct.Pin = GPIO_PIN_6;
  GPIO_InitStruct.Mode = GPIO_MODE_INPUT;
  GPIO_InitStruct.Pull = GPIO_PULLUP;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_HIGH;
  HAL_GPIO_Init(GPIOA, &GPIO_InitStruct);
  
  /* PA7 (MOSI): Alternate Function Push-Pull */
  GPIO_InitStruct.Pin = GPIO_PIN_7;
  GPIO_InitStruct.Mode = GPIO_MODE_AF_PP;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_HIGH;
  HAL_GPIO_Init(GPIOA, &GPIO_InitStruct);
  
  SD_DebugPrint("[DBG] SD init: SPI pins reconfigured with MAXIMUM pull-up\r\n");
  
  /* Start with ULTRA-LOW speed for initialization */
  SD_SetSpeed(0);
  SD_DebugPrint("[DBG] SD init: SPI speed set to LOW (281kHz - minimum)\\r\\n");
  
  /* SPI diagnostic: Try to read a byte when nothing is being sent */
  /* Normal SPI MISO should be pulled high (0xFF) when idle */
  uint8_t test_byte = SD_SPI_ReadByte();
  if (test_byte != 0xFF) {
    char diag[40];
    snprintf(diag, sizeof(diag), "[W] MISO idle=0x%02X (low)\r\n", test_byte);
    SD_DebugPrint(diag);
  }
  
  /* Deselect card */
  SD_CS_Control(1);
  
  /* Send 560 dummy clocks for initialization */
  for (i = 0; i < 70; i++)  /* 70 * 8 = 560 clocks */
    SD_SPI_WriteByte(0xFF);
  
  /* Send CMD0 - GO_IDLE_STATE */
  for (i = 0; i < 10; i++) {
    res = SD_SendCmd(SD_CMD0, 0);
    if (res == 0x01 || res == 0x00) break;
  }
  
  /* Send CMD8 (SEND_IF_COND) - 0x000001AA checks for SD v2 support */
  /* Response: R7 (5 bytes) but we only care about first byte (R1) */
  res = SD_SendCmd(8, 0x000001AA);
  
  if (res == 0x00 || res == 0x01) {
    /* Read 4 bytes of response data (not critical for our usage) */
    for (i = 0; i < 4; i++) {
      SD_SPI_ReadByte();
    }
    /* Mark as SD v2 capable - type will be determined later via OCR */
    CardType = 0;  /* Will be set after ACMD41 via CMD58 */
  } else {
    /* CMD8 failed = SD v1 (SDSC) */
    CardType = 1;
  }
  
  for (i = 0; i < 300; i++) {
    /* Send CMD55 first (APP COMMAND) */
    res = SD_SendCmd(55, 0);
    if (res > 1) continue;
    
    /* Now send ACMD41 (SEND_OP_COND) with HCS=1 (high capacity support) */
    res = SD_SendCmd(41, 0x40000000);
    
    if (res == 0x00) {
      SD_DebugPrint("[DBG] SD init: SUCCESS - card ready!\r\n");
      
      /* Read OCR (Operation Conditions Register) via CMD58 to determine card type */
      /* OCR bit 30 (CCS) = 0:SDSC (byte addressing), 1:SDHC/SDXC (block addressing) */
      res = SD_SendCmd(58, 0);
      if (res == 0x00 || res == 0x01) {
        /* Read OCR value (4 bytes) */
        uint8_t ocr_bytes[4];
        for (i = 0; i < 4; i++) {
          ocr_bytes[i] = SD_SPI_ReadByte();
        }
        /* OCR diagnostic removed to save FLASH */
        
        /* Check CCS bit (bit 30 = byte 0, bit 6) */
        /* OCR format: [OCR_MSB ... OCR_LSB] from SPI */
        uint8_t ccs_bit = (ocr_bytes[0] >> 6) & 0x01;
        if (ccs_bit) {
          CardType = 2;  /* SDHC/SDXC - block addressing */
        } else {
          CardType = 1;  /* SDSC - byte addressing */
        }
      } else {
        /* CMD58 failed, default to SDSC to be safe */
        CardType = 1;
      }
      
      /* Set block size to 512 bytes (CMD16) */
      res = SD_SendCmd(16, 512);
      
      /* Verify card status with CMD13 */
      res = SD_SendCmd(13, 0);
      
      SD_CS_Control(1);
      SD_SPI_WriteByte(0xFF);
      return 1;
    }
  }
  
  /* Initialization timeout - removed message to save FLASH */
  SD_CS_Control(1);
  return 0;
}

/* Forward declarations */
DSTATUS USER_initialize (BYTE pdrv);
DSTATUS USER_status (BYTE pdrv);
DRESULT USER_read (BYTE pdrv, BYTE *buff, DWORD sector, UINT count);
#if _USE_WRITE == 1
  DRESULT USER_write (BYTE pdrv, const BYTE *buff, DWORD sector, UINT count);
#endif /* _USE_WRITE == 1 */
#if _USE_IOCTL == 1
  DRESULT USER_ioctl (BYTE pdrv, BYTE cmd, void *buff);
#endif /* _USE_IOCTL == 1 */

Diskio_drvTypeDef  USER_Driver =
{
  USER_initialize,
  USER_status,
  USER_read,
#if  _USE_WRITE
  USER_write,
#endif  /* _USE_WRITE == 1 */
#if  _USE_IOCTL == 1
  USER_ioctl,
#endif /* _USE_IOCTL == 1 */
};

/* Private functions ---------------------------------------------------------*/

/**
  * @brief  Initializes a Drive
  * @param  pdrv: Physical drive number (0..)
  * @retval DSTATUS: Operation status
  */
DSTATUS USER_initialize (
	BYTE pdrv           /* Physical drive nmuber to identify the drive */
)
{
  /* USER CODE BEGIN INIT */
  char diag[80];
  if (pdrv == 0) {
    if (SD_CardInit()) {
      Stat = 0;  /* Card ready */
      SD_DebugPrint("[DBG] USER_initialize: SD_CardInit SUCCESS, Stat=0\r\n");
    } else {
      Stat = STA_NOINIT;  /* Init failed */
      SD_DebugPrint("[DBG] USER_initialize: SD_CardInit FAILED, Stat=STA_NOINIT\r\n");
    }
  }
  snprintf(diag, sizeof(diag), "[DBG] USER_initialize: returning Stat=0x%02X\r\n", Stat);
  SD_DebugPrint(diag);
  return Stat;
  /* USER CODE END INIT */
}

/**
  * @brief  Gets Disk Status
  * @param  pdrv: Physical drive number (0..)
  * @retval DSTATUS: Operation status
  */
DSTATUS USER_status (
	BYTE pdrv       /* Physical drive number to identify the drive */
)
{
  /* USER CODE BEGIN STATUS */
  if (pdrv == 0) {
    return Stat;  /* Return current status */
  }
  return STA_NOINIT;
  /* USER CODE END STATUS */
}

/**
  * @brief  Reads Sector(s)
  * @param  pdrv: Physical drive number (0..)
  * @param  *buff: Data buffer to store read data
  * @param  sector: Sector address (LBA)
  * @param  count: Number of sectors to read (1..128)
  * @retval DRESULT: Operation result
  */
DRESULT USER_read (
	BYTE pdrv,      /* Physical drive nmuber to identify the drive */
	BYTE *buff,     /* Data buffer to store read data */
	DWORD sector,   /* Sector address in LBA */
	UINT count      /* Number of sectors to read */
)
{
  /* USER CODE BEGIN READ */
  uint8_t res, i;
  uint16_t j;
  uint32_t retry;
  uint8_t token;
  char diag[80];
  static uint8_t read_count = 0;
  
  if (pdrv == 0) {
    /* Log first few reads */
    if (read_count < 3) {
      snprintf(diag, sizeof(diag), "[DBG] USER_read: sector=%lu count=%u\r\n", sector, count);
      SD_DebugPrint(diag);
    }
    read_count++;
    
    /* Keep CS low for entire read sequence */
    SD_CS_Control(0);
    
    for (i = 0; i < count; i++) {
      /* Calculate sector address based on card type */
      uint32_t addr = sector + i;
      uint8_t addr_retry = 0;
      
      /* SDSC cards use BYTE addressing (multiply by 512) */
      /* SDHC/SDXC cards use BLOCK addressing (no multiply needed) */
      if (CardType == 1) {  /* SDSC */
        addr = addr << 9;   /* addr = addr * 512 */
        if (read_count < 4) {
          snprintf(diag, sizeof(diag), "[DBG] SDSC addr conversion: sector=%lu -> 0x%lX\r\n", 
                   sector + i, addr);
          SD_DebugPrint(diag);
        }
      }
      
      /* Send CMD17 - READ_SINGLE_BLOCK, keeping CS low */
      /* If address error (0x20) occurs, auto-detect and retry with opposite addressing mode */
      for (addr_retry = 0; addr_retry < 2; addr_retry++) {
        res = SD_SendCmd_NoCS(SD_CMD17, addr);
        
        if (res == 0x00) {
          /* Command accepted, proceed to data phase */
          break;
        } else if (res == 0x20 && addr_retry == 0) {
          /* Address Error - toggle addressing mode and retry */
          if (read_count < 4) {
            snprintf(diag, sizeof(diag), "[DBG] USER_read: Address Error (0x20), toggling addressing mode\r\n");
            SD_DebugPrint(diag);
          }
          if (CardType == 1) {
            /* Was trying byte addressing, switch to block addressing */
            addr = sector + i;
          } else {
            /* Was trying block addressing, switch to byte addressing */
            addr = (sector + i) << 9;
          }
          /* Continue loop to retry with new address */
        } else {
          /* Other error or retry exhausted */
          snprintf(diag, sizeof(diag), "[DBG] USER_read: CMD17 FAIL res=0x%02X\r\n", res);
          SD_DebugPrint(diag);
          SD_CS_Control(1);
          return RES_ERROR;
        }
      }
      
      if (res != 0x00) {
        snprintf(diag, sizeof(diag), "[DBG] USER_read: CMD17 FAIL after retry, res=0x%02X\r\n", res);
        SD_DebugPrint(diag);
        SD_CS_Control(1);
        return RES_ERROR;
      }
      
      /* After CMD17, wait for data start block token (0xFE) */
      /* Read bytes until we find 0xFE token or timeout */
      token = 0xFF;
      retry = 100000;
      uint8_t first_byte = 0xFF;
      
      while (retry-- && token == 0xFF) {
        token = SD_SPI_ReadByte();
        
        if (first_byte == 0xFF && token != 0xFF) {
          first_byte = token;
          if (read_count < 4) {
            snprintf(diag, sizeof(diag), "[DBG] USER_read: First byte after CMD17: 0x%02X (retry left=%lu)\r\n", 
                     token, retry);
            SD_DebugPrint(diag);
          }
        }
      }
      
      if (token != DATA_START_BLOCK) {
        if (read_count == 1) {
          if (first_byte == 0xFF) {
            SD_DebugPrint("[DBG] FAIL: card not responding\r\n");
          } else if (first_byte == 0x00) {
            SD_DebugPrint("[DBG] FAIL: add MISO pull-up resistor\r\n");
          }
        }
        
        /* Keep low speed - do NOT switch back to high */
        SD_CS_Control(1);
        return RES_ERROR;
      }
      
      if (read_count < 4) {
        SD_DebugPrint("[DBG] USER_read: token OK! Data phase...");
        /* STAY at LOW speed - do NOT switch to high speed */
      }
      
      /* Token SUCCESS - read real sector data */
      if (read_count == 1) {
        SD_DebugPrint("[DBG] USER_read: First 32 bytes of sector:\r\n");
      }
      
      /* Read sector data */
      for (j = 0; j < SECTOR_SIZE; j++) {
        uint8_t byte = SD_SPI_ReadByte();
        buff[(i * SECTOR_SIZE) + j] = byte;
        
        /* Hex dump first read's first 32 bytes */
        if (read_count == 1 && j < 32) {
          char hexbyte[4];
          snprintf(hexbyte, sizeof(hexbyte), "%02X ", byte);
          SD_DebugPrint(hexbyte);
          if ((j + 1) % 16 == 0) SD_DebugPrint("\r\n");
        }
      }
      
      if (read_count == 1) {
        SD_DebugPrint("\r\n");
      }
      
      /* Read CRC (2 bytes) */
      SD_SPI_ReadByte();
      SD_SPI_ReadByte();
    }
    
    /* Send dummy bytes and deselect */
    for (j = 0; j < 8; j++)
      SD_SPI_WriteByte(0xFF);
    SD_CS_Control(1);
    SD_SPI_WriteByte(0xFF);
    
    return RES_OK;
  }
  
  return RES_ERROR;
  /* USER CODE END READ */
}

/**
  * @brief  Writes Sector(s)
  * @param  pdrv: Physical drive number (0..)
  * @param  *buff: Data to be written
  * @param  sector: Sector address (LBA)
  * @param  count: Number of sectors to write (1..128)
  * @retval DRESULT: Operation result
  */
#if _USE_WRITE == 1
DRESULT USER_write (
	BYTE pdrv,          /* Physical drive nmuber to identify the drive */
	const BYTE *buff,   /* Data to be written */
	DWORD sector,       /* Sector address in LBA */
	UINT count          /* Number of sectors to write */
)
{
  /* USER CODE BEGIN WRITE */
  uint8_t res, i;
  uint16_t j, retry;
  uint8_t dataResp;
  
  if (pdrv == 0) {
    SD_CS_Control(0);
    
    for (i = 0; i < count; i++) {
      /* Calculate sector address based on card type (same as read) */
      uint32_t addr = sector + i;
      uint8_t addr_retry = 0;
      
      /* SDSC cards use BYTE addressing (multiply by 512) */
      /* SDHC/SDXC cards use BLOCK addressing (no multiply needed) */
      if (CardType == 1) {  /* SDSC */
        addr = addr << 9;   /* addr = addr * 512 */
      }
      
      /* Send CMD24 - WRITE_SINGLE_BLOCK, keeping CS low */
      /* Auto-detect addressing mode like in read */
      for (addr_retry = 0; addr_retry < 2; addr_retry++) {
        res = SD_SendCmd_NoCS(SD_CMD24, addr);
        
        if (res == 0x00) {
          /* Command accepted, proceed to data phase */
          break;
        } else if (res == 0x20 && addr_retry == 0) {
          /* Address Error - toggle addressing mode and retry */
          if (CardType == 1) {
            /* Was trying byte addressing, switch to block addressing */
            addr = sector + i;
          } else {
            /* Was trying block addressing, switch to byte addressing */
            addr = (sector + i) << 9;
          }
          /* Continue loop to retry with new address */
        } else {
          /* Other error or retry exhausted */
          SD_CS_Control(1);
          return RES_ERROR;
        }
      }
      
      if (res != 0x00) {
        SD_CS_Control(1);
        return RES_ERROR;
      }
      
      /* Wait before sending data (at least 1 byte delay) */
      SD_SPI_WriteByte(0xFF);
      
      /* Send data start token */
      SD_SPI_WriteByte(DATA_START_BLOCK);
      
      /* Write sector data */
      for (j = 0; j < SECTOR_SIZE; j++) {
        SD_SPI_WriteByte(buff[(i * SECTOR_SIZE) + j]);
      }
      
      /* Write CRC (2 bytes) - not critical but required */
      SD_SPI_WriteByte(0xFF);
      SD_SPI_WriteByte(0xFF);
      
      /* Get data response token (should be 0x05 = accepted) */
      dataResp = SD_SPI_ReadByte();
      
      if ((dataResp & 0x1F) != DATA_RESP_OK) {
        SD_CS_Control(1);
        return RES_ERROR;
      }
      
      /* CRITICAL: Wait while card is busy writing to flash */
      /* With weak pull-up, MISO rise time is very slow */
      /* Use much larger timeout and send dummy clocks */
      retry = 500000;  /* 10x longer timeout for weak pull-up */
      while (retry--) {
        uint8_t miso = SD_SPI_ReadByte();
        if (miso == 0xFF) break;  /* Card released MISO, write complete */
      }
      
      /* Send extra dummy clocks (32 clocks = 4 bytes) to clear card state machine */
      for (j = 0; j < 4; j++) {
        SD_SPI_WriteByte(0xFF);
      }
    }
    
    /* Deselect card and send final clocks */
    SD_CS_Control(1);
    for (j = 0; j < 8; j++) {
      SD_SPI_WriteByte(0xFF);
    }
    
    return RES_OK;
  }
  
  return RES_ERROR;
  /* USER CODE END WRITE */
}
#endif /* _USE_WRITE == 1 */

/**
  * @brief  I/O control operation
  * @param  pdrv: Physical drive number (0..)
  * @param  cmd: Control code
  * @param  *buff: Buffer to send/receive control data
  * @retval DRESULT: Operation result
  */
#if _USE_IOCTL == 1
DRESULT USER_ioctl (
	BYTE pdrv,      /* Physical drive nmuber (0..) */
	BYTE cmd,       /* Control code */
	void *buff      /* Buffer to send/receive control data */
)
{
  /* USER CODE BEGIN IOCTL */
  DRESULT res = RES_ERROR;
  
  if (pdrv == 0) {
    switch (cmd) {
      case CTRL_SYNC:           /* Make sure that no pending write process */
        res = RES_OK;
        break;
      case GET_SECTOR_COUNT:    /* Get number of sectors on the disk */
        *(DWORD *)buff = 0x10000;  /* 64MB assumed */
        res = RES_OK;
        break;
      case GET_SECTOR_SIZE:     /* Get R/W sector size */
        *(WORD *)buff = SECTOR_SIZE;
        res = RES_OK;
        break;
      case GET_BLOCK_SIZE:      /* Get erase block size */
        *(DWORD *)buff = 1;
        res = RES_OK;
        break;
    }
  }
  
  return res;
  /* USER CODE END IOCTL */
}
#endif /* _USE_IOCTL == 1 */

