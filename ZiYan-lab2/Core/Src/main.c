/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file           : main.c
  * @brief          : Main program body
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
/* Includes ------------------------------------------------------------------*/
#include "main.h"
#include "i2c.h"
#include "tim.h"
#include "usart.h"
#include "gpio.h"

#include <stdio.h>
#include <string.h>
#include <stdbool.h>
#include <math.h>

// ===== OLED library =====
#include "ssd1306.h"
#include "ssd1306_fonts.h"

// =========================
// Pin definition
// =========================
#define DHT11_PORT       GPIOA
#define DHT11_PIN        GPIO_PIN_1

#define BTN_PORT         GPIOB
#define BTN_PIN          GPIO_PIN_12

#define RED_LED_PORT     GPIOB
#define RED_LED_PIN      GPIO_PIN_0

#define GREEN_LED_PORT   GPIOB
#define GREEN_LED_PIN    GPIO_PIN_1

// =========================
// Global variables
// =========================
bool oledEnabled = false;   // false: OFF, true: ON

GPIO_PinState lastButtonState = GPIO_PIN_SET;
GPIO_PinState currentButtonState = GPIO_PIN_SET;

uint32_t lastDebounceTime = 0;
const uint32_t debounceDelay = 50;

uint32_t lastSampleTime = 0;
const uint32_t sampleInterval = 2000;   // 2 seconds

float temperature = 0.0f;
float humidity = 0.0f;

// =========================
// Function prototypes
// =========================
void SystemClock_Config(void);

void delay_us(uint16_t us);

void DHT11_SetPinOutput(void);
void DHT11_SetPinInput(void);
int DHT11_Start(void);           // 改成 int
int DHT11_CheckResponse(void);   // 改成 int
int DHT11_ReadByte(void);        // 改成 int
int DHT11_ReadData(float *temp, float *humi); // 改成 int

void updateLEDs(void);
void updateOLED(float t, float h);
void sendSerialData(float t, float h);
void handleButton(void);

// =========================
// Microsecond delay using TIM2
// =========================
void delay_us(uint16_t us)
{
  __HAL_TIM_SET_COUNTER(&htim2, 0);
  while (__HAL_TIM_GET_COUNTER(&htim2) < us);
}

// =========================
// DHT11 pin mode switching
// =========================
void DHT11_SetPinOutput(void)
{
  GPIO_InitTypeDef GPIO_InitStruct = {0};
  GPIO_InitStruct.Pin = DHT11_PIN;
  GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
  HAL_GPIO_Init(DHT11_PORT, &GPIO_InitStruct);
}

void DHT11_SetPinInput(void)
{
  GPIO_InitTypeDef GPIO_InitStruct = {0};
  GPIO_InitStruct.Pin = DHT11_PIN;
  GPIO_InitStruct.Mode = GPIO_MODE_INPUT;
  GPIO_InitStruct.Pull = GPIO_PULLUP;
  HAL_GPIO_Init(DHT11_PORT, &GPIO_InitStruct);
}

// =========================
// DHT11 start signal
// =========================
int DHT11_Start(void)
{
  DHT11_SetPinOutput();
  HAL_GPIO_WritePin(DHT11_PORT, DHT11_PIN, GPIO_PIN_RESET);
  HAL_Delay(18);  // 至少 18ms
  HAL_GPIO_WritePin(DHT11_PORT, DHT11_PIN, GPIO_PIN_SET);
  delay_us(30);
  DHT11_SetPinInput();

  return DHT11_CheckResponse();
}

// =========================
// Check DHT11 response
// =========================
int DHT11_CheckResponse(void)
{
  uint32_t timeout = 0;

  // 1. 等待 DHT11 把電壓拉低 (通常需要等 20~40 微秒)
  while (HAL_GPIO_ReadPin(DHT11_PORT, DHT11_PIN) == GPIO_PIN_SET)
  {
     delay_us(1);
     if (++timeout > 200) return -1; // 錯誤 -1：等了 200 微秒都沒拉低 (沒反應)
  }

  // 2. 等待 DHT11 把電壓拉高 (通常會維持低電位 80 微秒)
  timeout = 0;
  while (HAL_GPIO_ReadPin(DHT11_PORT, DHT11_PIN) == GPIO_PIN_RESET)
  {
     delay_us(1);
     if (++timeout > 250) return -2; // 錯誤 -2：一直卡在低電位彈不回來
  }

  // 3. 再次等待 DHT11 把電壓拉低 (準備開始傳送資料)
  timeout = 0;
  while (HAL_GPIO_ReadPin(DHT11_PORT, DHT11_PIN) == GPIO_PIN_SET)
  {
     delay_us(1);
     if (++timeout > 250) return -3; // 錯誤 -3：卡在高電位，無法開始傳資料
  }

  return 1; // 完美握手成功！
}
// =========================
// Read one byte from DHT11
// =========================
int DHT11_ReadByte(void)
{
  uint8_t i, byte = 0;
  uint32_t timeout;

  for (i = 0; i < 8; i++)
  {
    timeout = 0;
    while (HAL_GPIO_ReadPin(DHT11_PORT, DHT11_PIN) == GPIO_PIN_RESET)
    {
       delay_us(1);
       if (++timeout > 100) return -4; // 錯誤 -4：等不到位元開始
    }

    delay_us(40);

    if (HAL_GPIO_ReadPin(DHT11_PORT, DHT11_PIN) == GPIO_PIN_SET)
    {
      byte |= (1 << (7 - i));
    }

    timeout = 0;
    while (HAL_GPIO_ReadPin(DHT11_PORT, DHT11_PIN) == GPIO_PIN_SET)
    {
       delay_us(1);
       if (++timeout > 100) return -5; // 錯誤 -5：等不到位元結束
    }
  }
  return byte;
}

// =========================
// Read DHT11 data
// Returns 1 if success
// =========================
int DHT11_ReadData(float *temp, float *humi)
{
  int status = DHT11_Start();
  if (status < 0) return status;

  int Rh_byte1 = DHT11_ReadByte();
  if (Rh_byte1 < 0) return Rh_byte1;

  int Rh_byte2 = DHT11_ReadByte();
  if (Rh_byte2 < 0) return Rh_byte2;

  int Temp_byte1 = DHT11_ReadByte();
  if (Temp_byte1 < 0) return Temp_byte1;

  int Temp_byte2 = DHT11_ReadByte();
  if (Temp_byte2 < 0) return Temp_byte2;

  int SUM = DHT11_ReadByte();
  if (SUM < 0) return SUM;

  if ((uint8_t)(Rh_byte1 + Rh_byte2 + Temp_byte1 + Temp_byte2) == (uint8_t)SUM)
  {
    *humi = (float)Rh_byte1;
    *temp = (float)Temp_byte1;
    return 1;
  }

  return -6; // 錯誤 -6：總和檢查碼錯誤 (雜訊干擾)
}

// =========================
// Update LEDs
// =========================
void updateLEDs(void)
{
  if (oledEnabled)
  {
    HAL_GPIO_WritePin(GREEN_LED_PORT, GREEN_LED_PIN, GPIO_PIN_SET);
    HAL_GPIO_WritePin(RED_LED_PORT, RED_LED_PIN, GPIO_PIN_RESET);
  }
  else
  {
    HAL_GPIO_WritePin(GREEN_LED_PORT, GREEN_LED_PIN, GPIO_PIN_RESET);
    HAL_GPIO_WritePin(RED_LED_PORT, RED_LED_PIN, GPIO_PIN_SET);
  }
}

// =========================
// Update OLED
// =========================
void updateOLED(float t, float h)
{
  char line1[32];
  char line2[32];

  ssd1306_Fill(Black);

  if (oledEnabled)
  {
    ssd1306_SetCursor(0, 0);
    ssd1306_WriteString("DHT11 Monitor", Font_7x10, White);

    snprintf(line1, sizeof(line1), "Temp: %.1f C", t);
    snprintf(line2, sizeof(line2), "Humi: %.1f %%", h);

    ssd1306_SetCursor(0, 20);
    ssd1306_WriteString(line1, Font_7x10, White);

    ssd1306_SetCursor(0, 40);
    ssd1306_WriteString(line2, Font_7x10, White);
  }
  else
  {
    ssd1306_SetCursor(0, 20);
    ssd1306_WriteString("OLED STOP", Font_7x10, White);

    ssd1306_SetCursor(0, 40);
    ssd1306_WriteString("Press button...", Font_7x10, White);
  }

  ssd1306_UpdateScreen();
}

// =========================
// Send UART data
// CSV format:
// DATA,temp,humidity,oledState
// =========================
void sendSerialData(float t, float h)
{
  char msg[64];
  int len = snprintf(msg, sizeof(msg), "DATA,%.1f,%.1f,%d\r\n", t, h, oledEnabled ? 1 : 0);
  HAL_UART_Transmit(&huart1, (uint8_t *)msg, len, 100);
}

// =========================
// Handle button toggle
// =========================
void handleButton(void)
{
  GPIO_PinState reading = HAL_GPIO_ReadPin(BTN_PORT, BTN_PIN);

  if (reading != lastButtonState)
  {
    lastDebounceTime = HAL_GetTick();
  }

  if ((HAL_GetTick() - lastDebounceTime) > debounceDelay)
  {
    if (reading != currentButtonState)
    {
      currentButtonState = reading;

      // button pressed (active LOW)
      if (currentButtonState == GPIO_PIN_RESET)
      {
        oledEnabled = !oledEnabled;
        updateLEDs();
        updateOLED(temperature, humidity);
      }
    }
  }

  lastButtonState = reading;
}

/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */

/* USER CODE END Includes */

/* Private typedef -----------------------------------------------------------*/
/* USER CODE BEGIN PTD */

/* USER CODE END PTD */

/* Private define ------------------------------------------------------------*/
/* USER CODE BEGIN PD */
#define DHT11_PORT       GPIOA
#define DHT11_PIN        GPIO_PIN_1

#define BTN_PORT         GPIOB
#define BTN_PIN          GPIO_PIN_12

#define RED_LED_PORT     GPIOB
#define RED_LED_PIN      GPIO_PIN_0

#define GREEN_LED_PORT   GPIOB
#define GREEN_LED_PIN    GPIO_PIN_1
/* USER CODE END PD */

/* Private macro -------------------------------------------------------------*/
/* USER CODE BEGIN PM */

/* USER CODE END PM */

/* Private variables ---------------------------------------------------------*/

/* USER CODE BEGIN PV */

/* USER CODE END PV */

/* Private function prototypes -----------------------------------------------*/
void SystemClock_Config(void);
/* USER CODE BEGIN PFP */

/* USER CODE END PFP */

/* Private user code ---------------------------------------------------------*/
/* USER CODE BEGIN 0 */

/* USER CODE END 0 */

/**
  * @brief  The application entry point.
  * @retval int
  */
int main(void)
{

  /* USER CODE BEGIN 1 */

  /* USER CODE END 1 */

  /* MCU Configuration--------------------------------------------------------*/

  /* Reset of all peripherals, Initializes the Flash interface and the Systick. */
	/* Reset of all peripherals, Initializes the Flash interface and the Systick. */
	  HAL_Init();

	  /* Configure the system clock */
	  SystemClock_Config();

	  /* Initialize all configured peripherals */
	  MX_GPIO_Init();
	  MX_I2C1_Init();
	  MX_TIM2_Init();
	  MX_USART1_UART_Init();

	  /* USER CODE BEGIN 2 */
	  // 💡 1. 確保所有東西都 Init 完之後，再啟動計時器！
	  HAL_TIM_Base_Start(&htim2);

	  // 💡 2. 螢幕與 LED 初始化
	  ssd1306_Init();
	  HAL_GPIO_WritePin(RED_LED_PORT, RED_LED_PIN, GPIO_PIN_SET);
	  HAL_GPIO_WritePin(GREEN_LED_PORT, GREEN_LED_PIN, GPIO_PIN_RESET);
	  updateLEDs();
	  updateOLED(temperature, humidity);
  /* USER CODE BEGIN 2 */
  const char *boot_msg = "\r\n[BOOT] Hello from STM32F103 (USART1)\r\n";
  HAL_UART_Transmit(&huart1, (uint8_t*)boot_msg, strlen(boot_msg), 100);
  /* USER CODE END 2 */

  /* Infinite loop */
  /* USER CODE BEGIN WHILE */
  while (1)
    {
      handleButton();

      if (HAL_GetTick() - lastSampleTime >= sampleInterval)
      {
        lastSampleTime = HAL_GetTick();

        float t, h;
        char debug_msg[128]; // 加大字串長度以容納詳細訊息

        int status = DHT11_ReadData(&t, &h);

        if (status == 1)
        {
          // === 成功讀取 ===
          temperature = t;
          humidity = h;
          sendSerialData(temperature, humidity);
          updateOLED(temperature, humidity);
        }
        else
        {
          // === 讀取失敗：印出詳細死因 ===
          switch(status) {
            case -1: snprintf(debug_msg, sizeof(debug_msg), "DEBUG: [ERR -1] No Response (Stuck HIGH). Check PA1 connection or add 10k Pull-up resistor.\r\n"); break;
            case -2: snprintf(debug_msg, sizeof(debug_msg), "DEBUG: [ERR -2] Stuck LOW. PA1 might be shorted to GND.\r\n"); break;
            case -3: snprintf(debug_msg, sizeof(debug_msg), "DEBUG: [ERR -3] Timeout wait for LOW. Sensor glitch or TIM2 issue.\r\n"); break;
            case -4: snprintf(debug_msg, sizeof(debug_msg), "DEBUG: [ERR -4] Timeout wait for bit start. TIM2 too slow?\r\n"); break;
            case -5: snprintf(debug_msg, sizeof(debug_msg), "DEBUG: [ERR -5] Timeout wait for bit end. TIM2 too slow?\r\n"); break;
            case -6: snprintf(debug_msg, sizeof(debug_msg), "DEBUG: [ERR -6] Checksum Error. Data corrupted or TIM2 not strictly 1us.\r\n"); break;
            default: snprintf(debug_msg, sizeof(debug_msg), "DEBUG: Unknown Error %d\r\n", status); break;
          }

          HAL_UART_Transmit(&huart1, (uint8_t *)debug_msg, strlen(debug_msg), HAL_MAX_DELAY);
        }
      }
    }
  /* USER CODE END 3 */
}

/**
  * @brief System Clock Configuration
  * @retval None
  */
void SystemClock_Config(void)
{
  RCC_OscInitTypeDef RCC_OscInitStruct = {0};
  RCC_ClkInitTypeDef RCC_ClkInitStruct = {0};

  /** Initializes the RCC Oscillators according to the specified parameters
  * in the RCC_OscInitTypeDef structure.
  */
  RCC_OscInitStruct.OscillatorType = RCC_OSCILLATORTYPE_HSI;
  RCC_OscInitStruct.HSIState = RCC_HSI_ON;
  RCC_OscInitStruct.HSICalibrationValue = RCC_HSICALIBRATION_DEFAULT;
  RCC_OscInitStruct.PLL.PLLState = RCC_PLL_NONE;
  if (HAL_RCC_OscConfig(&RCC_OscInitStruct) != HAL_OK)
  {
    Error_Handler();
  }

  /** Initializes the CPU, AHB and APB buses clocks
  */
  RCC_ClkInitStruct.ClockType = RCC_CLOCKTYPE_HCLK|RCC_CLOCKTYPE_SYSCLK
                              |RCC_CLOCKTYPE_PCLK1|RCC_CLOCKTYPE_PCLK2;
  RCC_ClkInitStruct.SYSCLKSource = RCC_SYSCLKSOURCE_HSI;
  RCC_ClkInitStruct.AHBCLKDivider = RCC_SYSCLK_DIV1;
  RCC_ClkInitStruct.APB1CLKDivider = RCC_HCLK_DIV1;
  RCC_ClkInitStruct.APB2CLKDivider = RCC_HCLK_DIV1;

  if (HAL_RCC_ClockConfig(&RCC_ClkInitStruct, FLASH_LATENCY_0) != HAL_OK)
  {
    Error_Handler();
  }
}

/* USER CODE BEGIN 4 */

/* USER CODE END 4 */

/**
  * @brief  This function is executed in case of error occurrence.
  * @retval None
  */
void Error_Handler(void)
{
  /* USER CODE BEGIN Error_Handler_Debug */
  /* User can add his own implementation to report the HAL error return state */
  __disable_irq();
  while (1)
  {
  }
  /* USER CODE END Error_Handler_Debug */
}

#ifdef  USE_FULL_ASSERT
/**
  * @brief  Reports the name of the source file and the source line number
  *         where the assert_param error has occurred.
  * @param  file: pointer to the source file name
  * @param  line: assert_param error line source number
  * @retval None
  */
void assert_failed(uint8_t *file, uint32_t line)
{
  /* USER CODE BEGIN 6 */
  /* User can add his own implementation to report the file name and line number,
     ex: printf("Wrong parameters value: file %s on line %d\r\n", file, line) */
  /* USER CODE END 6 */
}
#endif /* USE_FULL_ASSERT */
