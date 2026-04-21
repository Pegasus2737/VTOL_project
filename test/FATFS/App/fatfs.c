/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file   fatfs.c
  * @brief  Code for fatfs applications
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
/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file   fatfs.c
  * @brief  Code for fatfs applications
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
#include "fatfs.h"
#include "rtc_ds3231.h"

uint8_t retUSER;    /* Return value for USER */
char USERPath[4];   /* USER logical drive path */
FATFS USERFatFS;    /* File system object for USER logical drive */
FIL USERFile;       /* File object for USER */

/* USER CODE BEGIN Variables */

/* USER CODE END Variables */

void MX_FATFS_Init(void)
{
  /*## FatFS: Link the USER driver ###########################*/
  retUSER = FATFS_LinkDriver(&USER_Driver, USERPath);

  /* USER CODE BEGIN Init */
  /* additional user code for init */
  /* USER CODE END Init */
}

/**
  * @brief  Gets Time from RTC
  * @param  None
  * @retval Time in DWORD (FatFs format: packed date/time)
  */
DWORD get_fattime(void)
{
  /* USER CODE BEGIN get_fattime */
  RTC_DateTime_t now;
  DWORD fattime;
  
  /* Read current time from DS3231 RTC */
  if (!RTC_DS3231_ReadDateTime(&now)) {
    /* If RTC read fails, return default valid time: 2020-01-01 00:00:00 */
    return ((2020 - 1980) << 25) | (1 << 20) | (1 << 14) | 0;
  }
  
  /* Validate year - RTC might have garbage value (e.g., 4001) before GPS sync */
  /* Valid FAT range is 1980-2107. Before 2000 or after 2107 = invalid, use default */
  if (now.year < 2000 || now.year > 2107) {
    /* Return default: 2020-01-01 00:00:00 */
    return ((2020 - 1980) << 25) | (1 << 20) | (1 << 14) | 0;
  }
  
  /* Validate month and day */
  if (now.month < 1 || now.month > 12 || now.day < 1 || now.day > 31) {
    return ((2020 - 1980) << 25) | (1 << 20) | (1 << 14) | 0;
  }
  
  /* Pack into FatFs format:
     Bit 31-25: Year-1980 (0-127)
     Bit 24-20: Month (1-12)
     Bit 19-14: Day (1-31)
     Bit 13-8: Hour (0-23)
     Bit 7-5: Minute (0-59)
     Bit 4-0: Second/2 (0-29)
  */
  
  fattime = ((now.year - 1980) & 0x7F) << 25;  /* Year */
  fattime |= (now.month & 0x0F) << 20;          /* Month */
  fattime |= (now.day & 0x1F) << 14;            /* Day */
  fattime |= (now.hour & 0x1F) << 8;            /* Hour */
  fattime |= (now.min & 0x3F) << 5;             /* Minute */
  fattime |= (now.sec / 2) & 0x1F;              /* Second/2 */
  
  return fattime;
  /* USER CODE END get_fattime */
}

/* USER CODE BEGIN Application */

/* USER CODE END Application */
