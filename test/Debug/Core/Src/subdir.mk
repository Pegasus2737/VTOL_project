################################################################################
# Automatically-generated file. Do not edit!
# Toolchain: GNU Tools for STM32 (13.3.rel1)
################################################################################

# Add inputs and outputs from these tool invocations to the build variables 
C_SRCS += \
../Core/Src/app.c \
../Core/Src/button_led.c \
../Core/Src/error_manager.c \
../Core/Src/gps.c \
../Core/Src/main.c \
../Core/Src/nmea_parser.c \
../Core/Src/rtc_ds3231.c \
../Core/Src/sdlog.c \
../Core/Src/stm32f1xx_hal_msp.c \
../Core/Src/stm32f1xx_it.c \
../Core/Src/syscalls.c \
../Core/Src/sysmem.c \
../Core/Src/system_stm32f1xx.c \
../Core/Src/telemetry.c \
../Core/Src/telemetry_record.c 

OBJS += \
./Core/Src/app.o \
./Core/Src/button_led.o \
./Core/Src/error_manager.o \
./Core/Src/gps.o \
./Core/Src/main.o \
./Core/Src/nmea_parser.o \
./Core/Src/rtc_ds3231.o \
./Core/Src/sdlog.o \
./Core/Src/stm32f1xx_hal_msp.o \
./Core/Src/stm32f1xx_it.o \
./Core/Src/syscalls.o \
./Core/Src/sysmem.o \
./Core/Src/system_stm32f1xx.o \
./Core/Src/telemetry.o \
./Core/Src/telemetry_record.o 

C_DEPS += \
./Core/Src/app.d \
./Core/Src/button_led.d \
./Core/Src/error_manager.d \
./Core/Src/gps.d \
./Core/Src/main.d \
./Core/Src/nmea_parser.d \
./Core/Src/rtc_ds3231.d \
./Core/Src/sdlog.d \
./Core/Src/stm32f1xx_hal_msp.d \
./Core/Src/stm32f1xx_it.d \
./Core/Src/syscalls.d \
./Core/Src/sysmem.d \
./Core/Src/system_stm32f1xx.d \
./Core/Src/telemetry.d \
./Core/Src/telemetry_record.d 


# Each subdirectory must supply rules for building sources it contributes
Core/Src/%.o Core/Src/%.su Core/Src/%.cyclo: ../Core/Src/%.c Core/Src/subdir.mk
	arm-none-eabi-gcc "$<" -mcpu=cortex-m3 -std=gnu11 -g3 -DDEBUG -DUSE_HAL_DRIVER -DSTM32F103xB -c -I../Core/Inc -I../Drivers/STM32F1xx_HAL_Driver/Inc/Legacy -I../Drivers/STM32F1xx_HAL_Driver/Inc -I../Drivers/CMSIS/Device/ST/STM32F1xx/Include -I../Drivers/CMSIS/Include -I../FATFS/Target -I../FATFS/App -I../Middlewares/Third_Party/FatFs/src -O0 -ffunction-sections -fdata-sections -Wall -fstack-usage -fcyclomatic-complexity -MMD -MP -MF"$(@:%.o=%.d)" -MT"$@" --specs=nano.specs -mfloat-abi=soft -mthumb -o "$@"

clean: clean-Core-2f-Src

clean-Core-2f-Src:
	-$(RM) ./Core/Src/app.cyclo ./Core/Src/app.d ./Core/Src/app.o ./Core/Src/app.su ./Core/Src/button_led.cyclo ./Core/Src/button_led.d ./Core/Src/button_led.o ./Core/Src/button_led.su ./Core/Src/error_manager.cyclo ./Core/Src/error_manager.d ./Core/Src/error_manager.o ./Core/Src/error_manager.su ./Core/Src/gps.cyclo ./Core/Src/gps.d ./Core/Src/gps.o ./Core/Src/gps.su ./Core/Src/main.cyclo ./Core/Src/main.d ./Core/Src/main.o ./Core/Src/main.su ./Core/Src/nmea_parser.cyclo ./Core/Src/nmea_parser.d ./Core/Src/nmea_parser.o ./Core/Src/nmea_parser.su ./Core/Src/rtc_ds3231.cyclo ./Core/Src/rtc_ds3231.d ./Core/Src/rtc_ds3231.o ./Core/Src/rtc_ds3231.su ./Core/Src/sdlog.cyclo ./Core/Src/sdlog.d ./Core/Src/sdlog.o ./Core/Src/sdlog.su ./Core/Src/stm32f1xx_hal_msp.cyclo ./Core/Src/stm32f1xx_hal_msp.d ./Core/Src/stm32f1xx_hal_msp.o ./Core/Src/stm32f1xx_hal_msp.su ./Core/Src/stm32f1xx_it.cyclo ./Core/Src/stm32f1xx_it.d ./Core/Src/stm32f1xx_it.o ./Core/Src/stm32f1xx_it.su ./Core/Src/syscalls.cyclo ./Core/Src/syscalls.d ./Core/Src/syscalls.o ./Core/Src/syscalls.su ./Core/Src/sysmem.cyclo ./Core/Src/sysmem.d ./Core/Src/sysmem.o ./Core/Src/sysmem.su ./Core/Src/system_stm32f1xx.cyclo ./Core/Src/system_stm32f1xx.d ./Core/Src/system_stm32f1xx.o ./Core/Src/system_stm32f1xx.su ./Core/Src/telemetry.cyclo ./Core/Src/telemetry.d ./Core/Src/telemetry.o ./Core/Src/telemetry.su ./Core/Src/telemetry_record.cyclo ./Core/Src/telemetry_record.d ./Core/Src/telemetry_record.o ./Core/Src/telemetry_record.su

.PHONY: clean-Core-2f-Src

