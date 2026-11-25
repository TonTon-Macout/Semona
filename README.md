# SEMONA - Serial Monitor
![semona982](https://github.com/user-attachments/assets/ae6de295-30f5-4d18-b2e7-0cc380f2d5d1)


**SEMONA** — это монитор последовательного порта. Программа предоставляет интерфейс для отправки и получения данных, а также множество настроек для комфортной работы, включая поддержку тем оформления, управление цветами, нумерацию строк и многое другое.

Вдохновлена Монитором порта Arduino IDE, но без ардуино, без иде и с некоторыми плюшками

[скачать](https://github.com/TonTon-Macout/Semona/releases/latest/download/Semona.exe) последнюю версию 


![Без имени-8](https://github.com/user-attachments/assets/d219311f-65d3-422c-a73c-01f55ba05d7c)


## Особенности

-  Простое управление портами, скоростью передачи, окончанием строк, можно включить выключить порт, сделать по верх окон итд.
- **Темы оформления**: Встроенные темы — светлая, тёмная и ретро, дуино и океан с возможностью кастомизации всех цветов и цветовых меткок.
  + темы сохраняются в отдельный файл themes.json
  + удобный редактор тем, можно создать свою собственную или отредактировать существующие
- **Цветовые метки**: Поддержка цветового выделения сообщений (Info, Warning, Error, Custom) с использованием специальных символов (`0x01``0x02``0x03``0x04`).
- **Гибкие настройки**:
  - Отображение меток времени.
  - Подсчёт символов.
  - Нумерация строк в окне вывода.
  - Отлючение Семоны
  - и другие
- **незадокументированные фичи**:
  + у меня бывает зависает порт при открытии, и начинает сыпаться мусор
    + лечится включением порта и выключением
    + с ардуино обычно, такого не происходит, а вот на TZT FT232RL - регулярно
    + проблема не программы (в ардуино иде тоже самое)
  + При первом запуске скачанного файла система предупредить о неопознаоном издателе
    + нужно нажать дополнительно -> выполнить в любом случае
  + Я не пробовал но 0xXX должен отправить как текст
## Цветовые метки 
чтобы окрасить строку в определеный цвет нужно 
- включить в настройках цветовые метки
- перед сообщением который нужно отправить вывести метку
  например так 
```CPP
#define SIMBOL_INFO    0x01
#define SIMBOL_WAR     0x02
#define SIMBOL_ERR     0x03
#define SIMBOL_CUSTOM  0x04
Serial.write(SIMBOL_ERR);
Serial.println("ой');
```


> В низу расширенный пример использвания цветных меток и удобного вывода в дебаг совместно с библиотекой Сеттингс Алекса Гайвера 






## Установка
Установка не требуется, просто поместите в нужную папку

## Использование

1. **Выбор порта и настроек**:
   - Выберите COM-порт из выпадающего списка.
   - Установите скорость передачи (baud rate), окончание строки (NL, CR, NL & CR) и другие параметры.
4. **Кастомизация**:
   - Перейдите в меню настроек для изменения темы, размера шрифта, цветов и других параметров.
   - Активируйте режим "Семона" для уникального отображения сообщений.
     - или деактивируйте если ее довольное лицо вас раздражает...
5. **Настройки**:
   - Режим "Семона" включаить Симону.
     - или выключить если ее довольное лицо вас бесит...
   - Цветовые метки, специальные символы в начале строки, по которым программа должна понимать в какой цвет красить строку
     - активировали - программа начнет ожидать такие метки, если вы их не отправляете то ничего и не произойдет
   - Сброс DTR - дергает ногой, чтобы сбросить устройство
     + должно быть физически подключено к ноге reset микроконтроллера
     + во всех ардуино подключено, поэтому при открытии порта ардуино сбрасывается
     + а тут можно отключить
   - Цвета сохраняются сразу, без нажатия кнопки сохранить
 
## Конфигурационные файлы

- `settings.json`: Хранит основные настройки, такие как тема, порт, размер шрифта и т.д.
- `themes.json`: Определяет стили для светлой, тёмной и ретро тем, включая цвета текста и цветовых меток.

## Горячие клавиши

- **Enter**: Отправка команды из поля ввода.
- **ПКМ на окне вывода**: Контекстное меню с опциями копирования, очистки и вызова настроек.


## Разработка

Программа написана на Python с использованием PyQt6 для интерфейса и PySerial для работы с последовательными портами.



![Снимок экрана 2025-04-12 012830](https://github.com/user-attachments/assets/ef79a70f-7708-46dc-87b3-014b1be71f14)

---

расширенный пример использования цветных меток совместо с библиотекой Settings Алекса Гайвера 

- Не забудьте указать логин и вайфай сети 
- Пример запускает веб интерфейс с управлением дебагом 
- Можно переключить вывод с сериал порта в логгер и обратно
- Включить/выключить цветные метки
- переключать уровень дебага
- сообщения уровня кустом выводятся наравне с уровнем еррор
- все зависимости библиотеки сеттингс должны быть  установлены

```cpp 
#include <Arduino.h>
#ifdef ESP8266
#include <ESP8266WiFi.h>
#include <ESP8266mDNS.h>
#else
#include <ESPmDNS.h>
#include <WiFi.h>
#endif

#include <GyverDBFile.h>
#include <LittleFS.h>
#include <SettingsGyver.h>

// ===================== КОНФИГ =====================

#define PROJECT_NAME "Debug Demo"

// Укажи свои данные Wi-Fi
#define WIFI_SSID "ТУТ ИМЯ СЕТИ"
#define WIFI_PASS "Пароль"

#define DEBUG_SPEED 115200
#define MAX_LENGHT_LOG 4000
#define MAX_ATTEMPTS 20

#define DEFAULT_DEBUG Serial

// Выводы UART для ESP32.
// -1 означает стандартные выводы UART.
// Для Serial1 рекомендуется указать GPIO явно.
// Не используй GPIO, занятые другими устройствами.

#define DEBUG_UART1_RX -1
#define DEBUG_UART1_TX -1

#define DEBUG_UART2_RX -1
#define DEBUG_UART2_TX -1

enum SerialSymbol : uint8_t {
    SIMBOL_NONE = 0x00,
    SIMBOL_INFO = 0x01,
    SIMBOL_WAR = 0x02,
    SIMBOL_ERR = 0x03,
    SIMBOL_CUSTOM = 0x04
};

// ===================== БАЗА =====================

GyverDBFile db(&LittleFS, "/settings.db");

DB_KEYS(
    kk,
    wifi_ssid,
    wifi_pass,
    wifi_ssid_reserv,
    wifi_pass_reserv,
    switchWifi,
    ap_mode,
    ssid_ap,
    pass_ap,
    debug_mode,
    debug_lvl,
    color_debug,
    debug_uart);

SettingsGyver sett(PROJECT_NAME, &db);

sets::Logger logger(MAX_LENGHT_LOG);

// Назначенное доменное имя
String hostName;



struct {
    char ssid[25] = WIFI_SSID;
    char password[64] = WIFI_PASS;

    char ssid_reserv[25] = "";
    char password_reserv[64] = "";

    bool switchWifi = false;

    uint8_t ap = 1;
    char ssid_ap[25] = "ESP_Debug";
    char pass_ap[20] = "12345678";

    uint8_t debug = 1;
    uint8_t debug_lvl = 0;
    bool color_debug = true;

    uint8_t debug_uart = 0;

} settings;


class Debug {
   private:
    HardwareSerial* _serial;
    unsigned long _baud;

   public:
    enum DBG_TYPE {
        DBG_NO = 0,
        DBG_SERIAL = 1,
        DBG_LOGGER = 2,
        DBG_LCD = 3
    };

    enum DBG_LVL {
        DBG_LVL_ALL = 0,
        DBG_LVL_INFO = 1,
        DBG_LVL_WARNING = 2,
        DBG_LVL_ERROR = 3
    };

    // Конструктор
    Debug(unsigned long baud, HardwareSerial& serial = DEFAULT_DEBUG)
        : _serial(&serial), _baud(baud) {
    }

    // Запуск выбранного UART
    void begin(uint8_t port = 0) {
#if defined(ESP32)

        switch (port) {
            case 1:
                _serial = &Serial1;
                Serial1.begin(
                    _baud,
                    SERIAL_8N1,
                    DEBUG_UART1_RX,
                    DEBUG_UART1_TX);
                break;

            case 2:
                _serial = &Serial2;
                Serial2.begin(
                    _baud,
                    SERIAL_8N1,
                    DEBUG_UART2_RX,
                    DEBUG_UART2_TX);
                break;

            default:
                _serial = &Serial;
                Serial.begin(_baud);
                break;
        }

#else

        _serial = &Serial;
        Serial.begin(_baud);

#endif
    }

    // Установка другого Serial-порта
    bool setSerial(HardwareSerial& serial, unsigned long baud) {
        _serial = &serial;
        _baud = baud;
        _serial->begin(_baud);
        return true;
    }


    template <typename T>
    void println(const T& msg) {
        if (settings.debug_lvl != DBG_LVL_ALL) return;

        if (settings.debug == DBG_SERIAL) {
            _serial->println(msg);
        } else if (settings.debug == DBG_LOGGER) {
            logger.println(msg);
            sett.reload();
        } else if (settings.debug == DBG_LCD) {
        }
    }

    template <typename T>
    void println(const T& msg, int32_t format) {
        if (settings.debug_lvl != DBG_LVL_ALL) return;

        if (settings.debug == DBG_SERIAL) {
            _serial->println(msg, format);
        } else if (settings.debug == DBG_LOGGER) {
            logger.println(msg, format);
            sett.reload();
        } else if (settings.debug == DBG_LCD) {
        }
    }

    void println(const __FlashStringHelper* msg) {
        if (settings.debug_lvl != DBG_LVL_ALL) return;

        if (settings.debug == DBG_SERIAL) {
            _serial->println(msg);
        } else if (settings.debug == DBG_LOGGER) {
            logger.println(msg);
            sett.reload();
        } else if (settings.debug == DBG_LCD) {
        }
    }

    template <typename T>
    void print(const T& msg) {
        if (settings.debug_lvl != DBG_LVL_ALL) return;

        if (settings.debug == DBG_SERIAL) {
            _serial->print(msg);
        } else if (settings.debug == DBG_LOGGER) {
            logger.print(msg);
        } else if (settings.debug == DBG_LCD) {
        }
    }

    template <typename T>
    void print(const T& msg, int32_t format) {
        if (settings.debug_lvl != DBG_LVL_ALL) return;

        if (settings.debug == DBG_SERIAL) {
            _serial->print(msg, format);
        } else if (settings.debug == DBG_LOGGER) {
            logger.print(msg, format);
        } else if (settings.debug == DBG_LCD) {
        }
    }

    void print(const __FlashStringHelper* msg) {
        if (settings.debug_lvl != DBG_LVL_ALL) return;

        if (settings.debug == DBG_SERIAL) {
            _serial->print(msg);
        } else if (settings.debug == DBG_LOGGER) {
            logger.print(msg);
        } else if (settings.debug == DBG_LCD) {
        }
    }


    void println(const char* text, int32_t value) {
        if (settings.debug_lvl != DBG_LVL_ALL) return;

        char buffer[64];
        snprintf(buffer, sizeof(buffer), "%s%d", text, value);

        if (settings.debug == DBG_SERIAL) {
            _serial->println(buffer);
        } else if (settings.debug == DBG_LOGGER) {
            logger.println(buffer);
            sett.reload();
        }
    }

    template <typename T>
    void println(const char* text, const T& value, int32_t format) {
        if (settings.debug_lvl != DBG_LVL_ALL) return;

        char buffer[64];

        if (format == HEX) {
            snprintf(buffer, sizeof(buffer), "%s%lX", text, (unsigned long)value);
        } else if (format == BIN) {
            char bin[33];
            itoa((unsigned long)value, bin, 2);
            snprintf(buffer, sizeof(buffer), "%s%s", text, bin);
        } else {
            snprintf(buffer, sizeof(buffer), "%s%ld", text, (long)value);
        }

        if (settings.debug == DBG_SERIAL) {
            _serial->println(buffer);
        } else if (settings.debug == DBG_LOGGER) {
            logger.println(buffer);
            sett.reload();
        }
    }

    void println(const __FlashStringHelper* text, int32_t value) {
        if (settings.debug_lvl != DBG_LVL_ALL) return;

        char buffer[64];
        snprintf_P(buffer, sizeof(buffer), PSTR("%S%d"), text, value);

        if (settings.debug == DBG_SERIAL) {
            _serial->println(buffer);
        } else if (settings.debug == DBG_LOGGER) {
            logger.println(buffer);
            sett.reload();
        }
    }

    template <typename T>
    void println(const __FlashStringHelper* text, const T& value, int32_t format) {
        if (settings.debug_lvl != DBG_LVL_ALL) return;

        char buffer[64];

        if (format == HEX) {
            snprintf_P(buffer, sizeof(buffer), PSTR("%S%lX"), text, (unsigned long)value);
        } else if (format == BIN) {
            char bin[33];
            itoa((unsigned long)value, bin, 2);
            snprintf_P(buffer, sizeof(buffer), PSTR("%S%s"), text, bin);
        } else {
            snprintf_P(buffer, sizeof(buffer), PSTR("%S%ld"), text, (long)value);
        }

        if (settings.debug == DBG_SERIAL) {
            _serial->println(buffer);
        } else if (settings.debug == DBG_LOGGER) {
            logger.println(buffer);
            sett.reload();
        }
    }

    void println(const char* text1, const char* text2) {
        if (settings.debug_lvl != DBG_LVL_ALL) return;

        char buffer[64];
        snprintf(buffer, sizeof(buffer), "%s%s", text1, text2);

        if (settings.debug == DBG_SERIAL) {
            _serial->println(buffer);
        } else if (settings.debug == DBG_LOGGER) {
            logger.println(buffer);
            sett.reload();
        }
    }

    void println(const __FlashStringHelper* text1, const __FlashStringHelper* text2) {
        if (settings.debug_lvl != DBG_LVL_ALL) return;

        char buffer[64];
        snprintf_P(buffer, sizeof(buffer), PSTR("%S%S"), text1, text2);

        if (settings.debug == DBG_SERIAL) {
            _serial->println(buffer);
        } else if (settings.debug == DBG_LOGGER) {
            logger.println(buffer);
            sett.reload();
        }
    }

    void println(const char* text1, const char* text2, const char* text3) {
        if (settings.debug_lvl != DBG_LVL_ALL) return;

        char buffer[64];
        snprintf(buffer, sizeof(buffer), "%s%s%s", text1, text2, text3);

        if (settings.debug == DBG_SERIAL) {
            _serial->println(buffer);
        } else if (settings.debug == DBG_LOGGER) {
            logger.println(buffer);
            sett.reload();
        }
    }

    void println(const __FlashStringHelper* text1, const __FlashStringHelper* text2, const __FlashStringHelper* text3) {
        if (settings.debug_lvl != DBG_LVL_ALL) return;

        char buffer[64];
        snprintf_P(buffer, sizeof(buffer), PSTR("%S%S%S"), text1, text2, text3);

        if (settings.debug == DBG_SERIAL) {
            _serial->println(buffer);
        } else if (settings.debug == DBG_LOGGER) {
            logger.println(buffer);
            sett.reload();
        }
    }


    template <typename T>
    void println(SerialSymbol symbol, const T& msg) {
        if (settings.debug_lvl == DBG_LVL_ALL) {
        } else if (settings.debug_lvl == DBG_LVL_INFO) {
            if (symbol < SIMBOL_INFO) return;
        } else if (settings.debug_lvl == DBG_LVL_WARNING) {
            if (symbol < SIMBOL_WAR) return;
        } else if (settings.debug_lvl == DBG_LVL_ERROR) {
            if (symbol < SIMBOL_ERR) return;
        }

        if (settings.debug == DBG_SERIAL) {
            if (settings.color_debug) {
                _serial->write((uint8_t)symbol);
            }
            _serial->println(msg);
        } else if (settings.debug == DBG_LOGGER) {
            if (settings.color_debug) {
                if (symbol == SIMBOL_INFO)
                    logger.print("info:");
                else if (symbol == SIMBOL_WAR)
                    logger.print("warn:");
                else if (symbol == SIMBOL_ERR) {
                    logger.print("err:");
                }
            }

            logger.println(msg);
            sett.reload();
        } else if (settings.debug == DBG_LCD) {
        }
    }

    template <typename T>
    void println(SerialSymbol symbol, const T& msg, int format) {
        if (settings.debug_lvl == DBG_LVL_ALL) {
        } else if (settings.debug_lvl == DBG_LVL_INFO) {
            if (symbol < SIMBOL_INFO) return;
        } else if (settings.debug_lvl == DBG_LVL_WARNING) {
            if (symbol < SIMBOL_WAR) return;
        } else if (settings.debug_lvl == DBG_LVL_ERROR) {
            if (symbol < SIMBOL_ERR) return;
        }

        if (settings.debug == DBG_SERIAL) {
            if (settings.color_debug) {
                _serial->write((uint8_t)symbol);
            }
            _serial->println(msg, format);
        } else if (settings.debug == DBG_LOGGER) {
            if (symbol == SIMBOL_INFO && settings.color_debug)
                logger.print("info:");
            else if (symbol == SIMBOL_WAR && settings.color_debug)
                logger.print("warn:");
            else if (symbol == SIMBOL_ERR && settings.color_debug)
                logger.print("err:");

            logger.println(msg, format);
            sett.reload();
        } else if (settings.debug == DBG_LCD) {
        }
    }

    void println(SerialSymbol symbol, const __FlashStringHelper* msg) {
        if (settings.debug_lvl == DBG_LVL_ALL) {
        } else if (settings.debug_lvl == DBG_LVL_INFO) {
            if (symbol < SIMBOL_INFO) return;
        } else if (settings.debug_lvl == DBG_LVL_WARNING) {
            if (symbol < SIMBOL_WAR) return;
        } else if (settings.debug_lvl == DBG_LVL_ERROR) {
            if (symbol < SIMBOL_ERR) return;
        }

        if (settings.debug == DBG_SERIAL) {
            if (settings.color_debug) {
                _serial->write((uint8_t)symbol);
            }
            _serial->println(msg);
        } else if (settings.debug == DBG_LOGGER) {
            if (symbol == SIMBOL_INFO && settings.color_debug)
                logger.print("info:");
            else if (symbol == SIMBOL_WAR && settings.color_debug)
                logger.print("warn:");
            else if (symbol == SIMBOL_ERR && settings.color_debug)
                logger.print("err:");

            logger.println(msg);
            sett.reload();
        } else if (settings.debug == DBG_LCD) {
        }
    }


    template <typename T1, typename T2>
    void println(SerialSymbol symbol, const T1& msg1, const T2& msg2) {
        if (settings.debug_lvl == DBG_LVL_ALL) {
        } else if (settings.debug_lvl == DBG_LVL_INFO) {
            if (symbol < SIMBOL_INFO) return;
        } else if (settings.debug_lvl == DBG_LVL_WARNING) {
            if (symbol < SIMBOL_WAR) return;
        } else if (settings.debug_lvl == DBG_LVL_ERROR) {
            if (symbol < SIMBOL_ERR) return;
        }

        if (settings.debug == DBG_SERIAL) {
            if (settings.color_debug) {
                _serial->write((uint8_t)symbol);
            }
            _serial->print(msg1);
            _serial->println(msg2);
        } else if (settings.debug == DBG_LOGGER) {
            if (symbol == SIMBOL_INFO && settings.color_debug)
                logger.print("info:");
            else if (symbol == SIMBOL_WAR && settings.color_debug)
                logger.print("warn:");
            else if (symbol == SIMBOL_ERR && settings.color_debug)
                logger.print("err:");

            logger.print(msg1);
            logger.println(msg2);
            sett.reload();
        } else if (settings.debug == DBG_LCD) {
        }
    }

    void println(SerialSymbol symbol, const __FlashStringHelper* msg1, const __FlashStringHelper* msg2) {
        if (settings.debug_lvl == DBG_LVL_ALL) {
        } else if (settings.debug_lvl == DBG_LVL_INFO) {
            if (symbol < SIMBOL_INFO) return;
        } else if (settings.debug_lvl == DBG_LVL_WARNING) {
            if (symbol < SIMBOL_WAR) return;
        } else if (settings.debug_lvl == DBG_LVL_ERROR) {
            if (symbol < SIMBOL_ERR) return;
        }

        if (settings.debug == DBG_SERIAL) {
            if (settings.color_debug) {
                _serial->write((uint8_t)symbol);
            }
            _serial->print(msg1);
            _serial->println(msg2);
        } else if (settings.debug == DBG_LOGGER) {
            if (symbol == SIMBOL_INFO && settings.color_debug)
                logger.print("info:");
            else if (symbol == SIMBOL_WAR && settings.color_debug)
                logger.print("warn:");
            else if (symbol == SIMBOL_ERR && settings.color_debug)
                logger.print("err:");

            logger.print(msg1);
            logger.println(msg2);
            sett.reload();
        } else if (settings.debug == DBG_LCD) {
        }
    }


    template <typename T1, typename T2, typename T3>
    void println(SerialSymbol symbol, const T1& msg1, const T2& msg2, const T3& msg3) {
        if (settings.debug_lvl == DBG_LVL_ALL) {
        } else if (settings.debug_lvl == DBG_LVL_INFO) {
            if (symbol < SIMBOL_INFO) return;
        } else if (settings.debug_lvl == DBG_LVL_WARNING) {
            if (symbol < SIMBOL_WAR) return;
        } else if (settings.debug_lvl == DBG_LVL_ERROR) {
            if (symbol < SIMBOL_ERR) return;
        }

        if (settings.debug == DBG_SERIAL) {
            if (settings.color_debug) {
                _serial->write((uint8_t)symbol);
            }

            _serial->print(msg1);
            _serial->print(msg2);
            _serial->println(msg3);
        } else if (settings.debug == DBG_LOGGER) {
            if (symbol == SIMBOL_INFO && settings.color_debug)
                logger.print("info:");
            else if (symbol == SIMBOL_WAR && settings.color_debug)
                logger.print("warn:");
            else if (symbol == SIMBOL_ERR && settings.color_debug)
                logger.print("err:");

            logger.print(msg1);
            logger.print(msg2);
            logger.println(msg3);
            sett.reload();
        } else if (settings.debug == DBG_LCD) {
        }
    }

    void println(SerialSymbol symbol, const __FlashStringHelper* msg1, const __FlashStringHelper* msg2, const __FlashStringHelper* msg3) {
        if (settings.debug_lvl == DBG_LVL_ALL) {
        } else if (settings.debug_lvl == DBG_LVL_INFO) {
            if (symbol < SIMBOL_INFO) return;
        } else if (settings.debug_lvl == DBG_LVL_WARNING) {
            if (symbol < SIMBOL_WAR) return;
        } else if (settings.debug_lvl == DBG_LVL_ERROR) {
            if (symbol < SIMBOL_ERR) return;
        }

        if (settings.debug == DBG_SERIAL) {
            if (settings.color_debug) {
                _serial->write((uint8_t)symbol);
            }

            _serial->print(msg1);
            _serial->print(msg2);
            _serial->println(msg3);
        } else if (settings.debug == DBG_LOGGER) {
            if (symbol == SIMBOL_INFO && settings.color_debug)
                logger.print("info:");
            else if (symbol == SIMBOL_WAR && settings.color_debug)
                logger.print("warn:");
            else if (symbol == SIMBOL_ERR && settings.color_debug)
                logger.print("err:");

            logger.print(msg1);
            logger.print(msg2);
            logger.println(msg3);
            sett.reload();
        } else if (settings.debug == DBG_LCD) {
        }
    }

    template <typename... Args>
    void printf(const char* format, Args... args) {
        if (settings.debug_lvl != DBG_LVL_ALL) return;

        char buffer[256];
        snprintf(buffer, sizeof(buffer), format, args...);

        if (settings.debug == DBG_SERIAL) {
            _serial->println(buffer);
        } else if (settings.debug == DBG_LOGGER) {
            logger.println(buffer);
            sett.reload();
        } else if (settings.debug == DBG_LCD) {
        }
    }

    template <typename... Args>
    void printf(SerialSymbol symbol, const char* format, Args... args) {
        if (settings.debug_lvl == DBG_LVL_ALL) {
        } else if (symbol == SIMBOL_NONE) {
            return;
        } else if (settings.debug_lvl == DBG_LVL_INFO) {
            if (symbol < SIMBOL_INFO) return;
        } else if (settings.debug_lvl == DBG_LVL_WARNING) {
            if (symbol < SIMBOL_WAR) return;
        } else if (settings.debug_lvl == DBG_LVL_ERROR) {
            if (symbol < SIMBOL_ERR) return;
        }

        char buffer[256];
        snprintf(buffer, sizeof(buffer), format, args...);

        if (settings.debug == DBG_SERIAL) {
            if (settings.color_debug) {
                _serial->write((uint8_t)symbol);
            }
            _serial->println(buffer);
        } else if (settings.debug == DBG_LOGGER) {
            if (settings.color_debug) {
                if (symbol == SIMBOL_INFO)
                    logger.print("info:");
                else if (symbol == SIMBOL_WAR)
                    logger.print("warn:");
                else if (symbol == SIMBOL_ERR)
                    logger.print("err:");
            }

            logger.println(buffer);
            sett.reload();
        }
    }


    template <typename T>
    void operator()(SerialSymbol symbol, const T& msg) {
        println(symbol, msg);
    }

    template <typename T>
    void operator()(SerialSymbol symbol, const T& msg, int32_t format) {
        println(symbol, msg, format);
    }

    void operator()(SerialSymbol symbol, const __FlashStringHelper* msg) {
        println(symbol, msg);
    }

    template <typename T1, typename T2>
    void operator()(SerialSymbol symbol, const T1& msg1, const T2& msg2) {
        println(symbol, msg1, msg2);
    }

    void operator()(SerialSymbol symbol, const __FlashStringHelper* msg1, const __FlashStringHelper* msg2) {
        println(symbol, msg1, msg2);
    }

    template <typename T1, typename T2, typename T3>
    void operator()(SerialSymbol symbol, const T1& msg1, const T2& msg2, const T3& msg3) {
        println(symbol, msg1, msg2, msg3);
    }

    void operator()(SerialSymbol symbol, const __FlashStringHelper* msg1, const __FlashStringHelper* msg2, const __FlashStringHelper* msg3) {
        println(symbol, msg1, msg2, msg3);
    }

    // ==========================================================
    // ОПЕРАТОР ДЛЯ ВЫВОДА БЕЗ СИМВОЛА
    // ==========================================================

    template <typename T>
    void operator()(const T& msg) {
        println(msg);
    }

    template <typename T>
    void operator()(const T& msg, int32_t format) {
        println(msg, format);
    }

    void operator()(const __FlashStringHelper* msg) {
        println(msg);
    }

    void operator()(const char* text, int32_t value) {
        println(text, value);
    }

    template <typename T>
    void operator()(const char* text, const T& value, int32_t format) {
        println(text, value, format);
    }

    void operator()(const __FlashStringHelper* text, int32_t value) {
        println(text, value);
    }

    template <typename T>
    void operator()(const __FlashStringHelper* text, const T& value, int32_t format) {
        println(text, value, format);
    }

    void operator()(const char* text1, const char* text2) {
        println(text1, text2);
    }

    void operator()(const __FlashStringHelper* text1, const __FlashStringHelper* text2) {
        println(text1, text2);
    }

    void operator()(const char* text1, const char* text2, const char* text3) {
        println(text1, text2, text3);
    }

    void operator()(const __FlashStringHelper* text1, const __FlashStringHelper* text2, const __FlashStringHelper* text3) {
        println(text1, text2, text3);
    }
};

// Глобальный объект Debug
Debug DEBUG(DEBUG_SPEED);

// ===================== HEAP =====================

#define HEAP_WARN_FREE (50 * 1024)
#define HEAP_WARN_LARGEST (24 * 1024)
#define HEAP_ERROR_FREE (25 * 1024)
#define HEAP_ERROR_LARGEST (12 * 1024)

void printHeap(const char* preamble) {
    const uint32_t freeHeap = ESP.getFreeHeap();

    uint32_t minHeap = 0;
    uint32_t largest = 0;

#if defined(ARDUINO_ARCH_ESP32)

    minHeap = ESP.getMinFreeHeap();
    largest = ESP.getMaxAllocHeap();

#elif defined(ARDUINO_ARCH_ESP8266)

    largest = ESP.getMaxFreeBlockSize();

#endif

    uint8_t symbol = SIMBOL_INFO;

    if (freeHeap < HEAP_ERROR_FREE || largest < HEAP_ERROR_LARGEST) {
        symbol = SIMBOL_ERR;
    } else if (freeHeap < HEAP_WARN_FREE || largest < HEAP_WARN_LARGEST) {
        symbol = SIMBOL_WAR;
    }

#if defined(ARDUINO_ARCH_ESP32)

    DEBUG.printf(
        (SerialSymbol)symbol,
        "%s | Free: %u KB | Min: %u KB | Largest: %u KB",
        preamble,
        freeHeap / 1024,
        minHeap / 1024,
        largest / 1024);

#elif defined(ARDUINO_ARCH_ESP8266)

    DEBUG.printf(
        (SerialSymbol)symbol,
        "%s | Free: %u KB | Min: N/A | Largest: %u KB",
        preamble,
        freeHeap / 1024,
        largest / 1024);

#endif
}

class WiFiConnector {
   private:
    const int16_t ATTEMPT_DELAY = 500;
    const unsigned long CHECK_INTERVAL = 5 * 60 * 1000;

    unsigned long lastCheckTime = 0;

    bool isAPMode = false;

    int8_t wifiError = -2;
    int8_t wifiReservError = -2;

    bool tryConnect(const char* ssid, const char* password, bool reserv = false) {
        DEBUG(SIMBOL_INFO, "[WIFI] Пытаемся подключиться...");

        reserv ? setReservError(WIFI_ERR_CONNECTION) : setError(WIFI_ERR_CONNECTION);

        WiFi.begin(ssid, password);

        int16_t attempts = 0;

        while (WiFi.status() != WL_CONNECTED && attempts < MAX_ATTEMPTS) {
            delay(ATTEMPT_DELAY);
            attempts++;
        }

        if (WiFi.status() == WL_CONNECTED) {
            DEBUG(SIMBOL_WAR, "[WIFI] Успешно подключились к сети: ", ssid);
            DEBUG(SIMBOL_INFO, "[WIFI] IP устройства: http://", WiFi.localIP().toString());

            sett.reload();

            if (reserv) {
                connectionAttempts = 0;
                setReservError(WIFI_ERR_OK);
                setError(WIFI_ERR_WAIT);
            } else {
                connectionAttempts = 0;
                setError(WIFI_ERR_OK);
                setReservError(WIFI_ERR_WAIT);
            }

            return true;
        }

        DEBUG(SIMBOL_ERR, "[WIFI] Не удалось подключиться к сети: ", ssid);
        DEBUG(SIMBOL_ERR, "[WIFI] Неверный пароль!");

        reserv ? setReservError(WIFI_ERR_PASSSWORD) : setError(WIFI_ERR_PASSSWORD);

        WiFi.disconnect();

        sett.reload();

        return false;
    }

    bool scanForNetwork(const char* ssid, bool reserv = false) {
        DEBUG(SIMBOL_INFO, "[WIFI] Сканируем сети для поиска: ", ssid);

        int16_t n = WiFi.scanNetworks();

        for (int16_t i = 0; i < n; i++) {
            if (strcmp(WiFi.SSID(i).c_str(), ssid) == 0) {
                DEBUG(SIMBOL_INFO, "[WIFI] Сеть найдена");

                return true;
            }
        }

        DEBUG(SIMBOL_ERR, "[WIFI] Сеть ", ssid, " не найдена!");

        reserv ? setReservError(WIFI_ERR_SSID) : setError(WIFI_ERR_SSID);

        return false;
    }

    // Генерация уникального SSID.
    // Порядок сканирования оставлен без изменений.

    String generateUniqueSSID(const char* baseSSID) {
        String newSSID = baseSSID;

        int16_t suffix = 1;

        int16_t n = WiFi.scanNetworks();

        while (true) {
            bool ssidExists = false;

            for (int16_t i = 0; i < n; i++) {
                if (WiFi.SSID(i) == newSSID) {
                    ssidExists = true;
                    break;
                }
            }

            if (!ssidExists) {
                break;
            }

            newSSID = String(baseSSID) + "_" + String(suffix);

            suffix++;
        }

        if (newSSID.length() > 32) {
            newSSID = newSSID.substring(0, 32);

            DEBUG(SIMBOL_ERR, "[WIFI] Имя SSID обрезано до 32 символов: ", newSSID);
        }

        if (newSSID != baseSSID) {
            DEBUG(SIMBOL_ERR, "[WIFI] Конфликт имени точки доступа! Сгенерировано уникальное имя: ", newSSID);
        }

        return newSSID;
    }

    void startAP() {
        DEBUG(SIMBOL_WAR, "[WIFI] Запускаем точку доступа: ", settings.ssid_ap);

        WiFi.mode(WIFI_AP);

        // Сканирование выполняется после перехода в режим AP.
        String uniqueSSID = generateUniqueSSID(settings.ssid_ap);

        if (settings.ap == AP_NO_PASS || settings.ap == ALWAYS_AP_NO_PASS) {
            WiFi.softAP(uniqueSSID.c_str());

            DEBUG(SIMBOL_ERR, "[WIFI] Точка доступа запущена без пароля, ip: ", WiFi.softAPIP().toString().c_str());

        } else {
            WiFi.softAP(uniqueSSID.c_str(), settings.pass_ap, 1, 0, 2);

            DEBUG(SIMBOL_INFO, "[WIFI] Точка доступа запущена с паролем, ip: ", WiFi.softAPIP().toString().c_str());
        }

        isAPMode = true;
    }

   public:
    enum APMode {
        NEVER = 0,
        AP_NO_PASS = 1,
        AP_PASS = 2,
        ALWAYS_AP_NO_PASS = 3,
        ALWAYS_AP_PASS = 4
    };

    enum WiFiErr {
        WIFI_ERR_WAIT = -2,
        WIFI_ERR_CONNECTION = -1,
        WIFI_ERR_OK = 0,
        WIFI_ERR_SSID = 1,
        WIFI_ERR_PASSSWORD = 2,
        WIFI_ERR_AP_ALWAYS = 3
    };

    WiFiConnector() {}

    void begin() {
        setError(WIFI_ERR_CONNECTION);
        setReservError(WIFI_ERR_CONNECTION);

        // Если ALWAYS_AP_*, сразу запускаем точку доступа
        if (settings.ap == ALWAYS_AP_NO_PASS || settings.ap == ALWAYS_AP_PASS) {
            DEBUG(SIMBOL_WAR, "[WIFI] Всегда запускаем в режиме точки доступа");

            startAP();

            if (settings.switchWifi) {
                setReservError(WIFI_ERR_AP_ALWAYS);
                setError(WIFI_ERR_WAIT);
            } else {
                setError(WIFI_ERR_AP_ALWAYS);
                setReservError(WIFI_ERR_WAIT);
            }

            return;
        }

        DEBUG("[WIFI] Устанавливаем режим станции");

        WiFi.mode(WIFI_STA);

        if (settings.switchWifi) {
            // Проверяем резервную сеть
            if (scanForNetwork(settings.ssid_reserv, true) &&
                tryConnect(settings.ssid_reserv, settings.password_reserv, true)) {
                return;
            }

            // Проверяем первую сеть
            if (scanForNetwork(settings.ssid) &&
                tryConnect(settings.ssid, settings.password)) {
                return;
            }

        } else {
            // Проверяем первую сеть
            if (scanForNetwork(settings.ssid) &&
                tryConnect(settings.ssid, settings.password)) {
                return;
            }

            // Проверяем резервную сеть
            if (scanForNetwork(settings.ssid_reserv, true) &&
                tryConnect(settings.ssid_reserv, settings.password_reserv, true)) {
                return;
            }
        }

        // Если не подключились и AP не NEVER, запускаем точку доступа
        if (settings.ap != NEVER) {
            DEBUG(SIMBOL_ERR, "[WIFI] Не удалось подключиться к сетям, запускаем точку доступа");

            startAP();
        } else {
            DEBUG(SIMBOL_ERR, "[WIFI] Подключение не удалось, точка доступа запрещена в настройках (NEVER)");
        }
    }

    int16_t connectionAttempts = 0;


    void setError(int8_t wifi_error) {
        wifiError = wifi_error;
        sett.reload();
    }

    int8_t getError() {
        return wifiError;
    }

    String getErrorStr() {
        switch (getError()) {
            case -2:
                return "---";

            case -1:
                return "подключение...";

            case 0:
                return "подключено";

            case 1:
                return "сеть не найдена";

            case 2:
                return "неверный пароль";

            case 3:
                return "всегда точка доступа";

            default:
                return "критическая ошибка";
        }
    }


    void setReservError(int8_t wifi_error) {
        wifiReservError = wifi_error;
        sett.reload();
    }

    int8_t getReservError() {
        return wifiReservError;
    }

    String getReservErrorStr() {
        switch (getReservError()) {
            case -2:
                return "---";

            case -1:
                return "подключение...";

            case 0:
                return "подключено";

            case 1:
                return "сеть не найдена";

            case 2:
                return "неверный пароль";

            case 3:
                return "всегда точка доступа";

            default:
                return "критическая ошибка";
        }
    }


    void tick() {
        // Проверяем только если в режиме точки доступа и не ALWAYS_AP_*
        if (isAPMode &&
            settings.ap != ALWAYS_AP_NO_PASS &&
            settings.ap != ALWAYS_AP_PASS) {
            unsigned long currentTime = millis();

            if (currentTime - lastCheckTime >= CHECK_INTERVAL) {
                if (connectionAttempts >= MAX_ATTEMPTS) {
                    DEBUG(
                        SIMBOL_ERR,
                        "[WIFI] Закончились попытки подключения (",
                        MAX_ATTEMPTS,
                        "). Для сброса - нажмите кнопку \"подключиться\" ");

                    lastCheckTime = currentTime;

                    return;
                }

                DEBUG(SIMBOL_INFO, "[WIFI] Периодическая проверка доступности сетей");

                if (!settings.switchWifi) {
                    // Проверяем первую сеть
                    if (scanForNetwork(settings.ssid) &&
                        tryConnect(settings.ssid, settings.password)) {
                        isAPMode = false;
                        WiFi.mode(WIFI_STA);

                        return;
                    }

                    // Проверяем резервную сеть
                    if (scanForNetwork(settings.ssid_reserv, true) &&
                        tryConnect(settings.ssid_reserv, settings.password_reserv, true)) {
                        isAPMode = false;
                        WiFi.mode(WIFI_STA);

                        return;
                    }

                } else {
                    // Проверяем резервную сеть
                    if (scanForNetwork(settings.ssid_reserv) &&
                        tryConnect(settings.ssid_reserv, settings.password_reserv)) {
                        isAPMode = false;
                        WiFi.mode(WIFI_STA);

                        return;
                    }

                    // Проверяем первую сеть
                    if (scanForNetwork(settings.ssid, true) &&
                        tryConnect(settings.ssid, settings.password, true)) {
                        isAPMode = false;
                        WiFi.mode(WIFI_STA);

                        return;
                    }
                }

                connectionAttempts++;

                DEBUG(SIMBOL_INFO, "[WIFI] Попытка подключения: ", connectionAttempts);

                lastCheckTime = currentTime;
            }
        }
    }


    bool isConnected() {
        bool connected = WiFi.status() == WL_CONNECTED;

        return connected;
    }

    bool isAccessPoint() {
        if (isAPMode) {
            // DEBUG(SIMBOL_INFO, "[WIFI] Устройство работает в режиме точки доступа");
        }

        return isAPMode;
    }

    bool isInAPMode() {
#if defined(ESP8266)

        WiFiMode_t mode = WiFi.getMode();

        if (mode == WIFI_AP || mode == WIFI_AP_STA) {
            return WiFi.softAPIP() != IPAddress(0, 0, 0, 0);
        }

#else

        wifi_mode_t mode = WiFi.getMode();

        if (mode == WIFI_MODE_AP || mode == WIFI_MODE_APSTA) {
            return WiFi.softAPIP() != IPAddress(0, 0, 0, 0);
        }

#endif

        return false;
    }


    bool findDeviceByMDNS(const char* hostname) {
        if (isAPMode) return false;

        if (WiFi.status() != WL_CONNECTED) {
            DEBUG(SIMBOL_ERR, "[mDNS] Не подключены к Wi-Fi, невозможно выполнить mDNS-запрос");

            return false;
        }

        if (!MDNS.begin("temp-check")) {
            DEBUG(SIMBOL_ERR, "[mDNS] Ошибка инициализации mDNS");

            return false;
        }

        int n = MDNS.queryService(hostname, "local");

        MDNS.end();

        if (n > 0) {
            DEBUG(SIMBOL_ERR, "[mDNS] Конфликт имени mDNS!");

            DEBUG(SIMBOL_ERR, "[mDNS] Устройство с именем ", String(hostname) + ".local уже существует");

            return true;
        } else {
            return false;
        }
    }

    String generateUniqueMDNSName(const char* baseName) {
        hostName = baseName;

        if (isAPMode) return String(baseName);

        String newName = baseName;

        int16_t suffix = 1;

        while (findDeviceByMDNS(newName.c_str())) {
            newName = String(baseName) + "-" + String(suffix);

            suffix++;
        }

        if (newName != baseName) {
            DEBUG(SIMBOL_ERR, "[mDNS] Сгенерировано уникальное имя: ", newName + ".local");

            DEBUG(SIMBOL_ERR, "[mDNS] Назначьте новое имя в настройках имени точки доступа!");
        }

        DEBUG(SIMBOL_INFO, "[mDNS] Устройство доступно по адресу: http://", newName + ".local");

        hostName = newName;

        return newName;
    }

    void startAP(bool pass) {
        DEBUG(SIMBOL_WAR, "[WIFI] Запускаем точку доступа: ", settings.ssid_ap);

        WiFi.mode(WIFI_AP);

        String uniqueSSID = generateUniqueSSID(settings.ssid_ap);

        if (!pass) {
            WiFi.softAP(uniqueSSID.c_str());

            DEBUG(SIMBOL_ERR, "[WIFI] Точка доступа запущена без пароля, ip: ", WiFi.softAPIP().toString().c_str());

        } else {
            WiFi.softAP(uniqueSSID.c_str(), settings.pass_ap, 1, 0, 2);

            DEBUG(SIMBOL_INFO, "[WIFI] Точка доступа запущена с паролем, ip: ", WiFi.softAPIP().toString().c_str());
        }

        isAPMode = true;
    }

} wifi;

void build(sets::Builder& b) {
    static bool expand_wifi = false;

    {
        sets::Group g(b, "WiFi");
        b.Switch("Развернуть", &expand_wifi);
        if (expand_wifi) {
            {
                b.Label("WIFI:", "", sets::Colors::Gray);

                if (wifi.connectionAttempts >= MAX_ATTEMPTS) {
                    b.Label("Осталось попыток подключения", "0", sets::Colors::Red);

                    b.Label("Для сброса нажмите кнопку \"подключиться\"");
                }

                if (b.Input(kk::wifi_ssid, "имя", AnyPtr(settings.ssid, 25))) {
                    b.reload();
                }

                if (b.Pass(kk::wifi_pass, "пароль", AnyPtr(settings.password, sizeof(settings.password)))) {
                    if (strcmp(settings.pass_ap, "appassword") == 0) {
                        if (settings.ap == wifi.AP_NO_PASS) {
                            if (strlen(settings.pass_ap) >= 8) {
                                strncpy(settings.pass_ap, settings.password, sizeof(settings.pass_ap) - 1);

                                settings.pass_ap[sizeof(settings.pass_ap) - 1] = '\0';

                                settings.ap = wifi.AP_PASS;
                            }
                        }
                    }

                    b.reload();
                }

                if (wifi.getError() != -2) {
                    b.Label(
                        "WiFi",
                        wifi.getErrorStr(),
                        wifi.getError() == 0 ? sets::Colors::Green : sets::Colors::Red);
                }

                if (!settings.switchWifi && b.Button("подключиться")) {
                    wifi.connectionAttempts = 0;

                    wifi.begin();
                }
            }

            b.HTML("", "<span class=\"HR\"></span>");

            {
                b.Label("WIFI Резервный:", "", sets::Colors::Gray);

                // Исправлено: переключатель связан с ключом базы
                if (b.Switch(kk::switchWifi, "сначала искать резервный")) {
                    settings.switchWifi = db[kk::switchWifi];

                    b.reload();
                }

                if (b.Input(kk::wifi_ssid_reserv, "имя", AnyPtr(settings.ssid_reserv, 25))) {
                    b.reload();
                }

                if (b.Pass(kk::wifi_pass_reserv, "пароль", AnyPtr(settings.password_reserv, sizeof(settings.password_reserv)))) {
                    b.reload();
                }

                if (wifi.getReservError() != -2) {
                    b.Label(
                        "WiFi",
                        wifi.getReservErrorStr(),
                        wifi.getReservError() == 0 ? sets::Colors::Green : sets::Colors::Red);
                }

                if (settings.switchWifi && b.Button("подключиться")) {
                    wifi.connectionAttempts = 0;

                    wifi.begin();
                }
            }

            b.HTML("", "<span class=\"HR\"></span>");

            {
                b.Label("Точка доступа:", "", sets::Colors::Gray);

                if (b.Select(
                        kk::ap_mode,
                        "Запуск",
                        "НИКОГДА;При отсутствии сетей, без пароля;При отсутствии сетей, с паролем;Всегда, без пароля;Всегда, с паролем;",
                        &settings.ap)) {
                    b.reload();
                }

                if (settings.ap == wifi.ALWAYS_AP_NO_PASS || settings.ap == wifi.ALWAYS_AP_PASS) {
                    b.Label(" ", "Внимание!!!", sets::Colors::Orange);

                    b.Paragraph("", "WiFi всегда будет работать в режиме точки доступа!");
                }

                if (settings.ap == wifi.ALWAYS_AP_NO_PASS || settings.ap == wifi.AP_NO_PASS) {
                    b.Label(" ", "Внимание!!!", sets::Colors::Red);

                    b.Paragraph("", "Кто угодно может подключиться к точке доступа и управлять устройством!");
                }

                if (b.Input(kk::ssid_ap, "WiFi SSID", AnyPtr(settings.ssid_ap, 25))) {
                    b.reload();
                }

                if (strlen(settings.pass_ap) < 8) {
                    b.Label(" ", "Пароль короче 8 символов!!!", sets::Colors::Red);
                }

                if (b.Pass(kk::pass_ap, "пароль", AnyPtr(settings.pass_ap, 20))) {
                    b.reload();
                }
            }
        }
    }

    // ==========================================================
    // DEBUG
    // ==========================================================

    {
        sets::Group g(b, "Debug");

        if (b.Select(kk::debug_mode, "Вывод", "Нет;Serial;Logger")) {
            settings.debug = db[kk::debug_mode];

            DEBUG(SIMBOL_INFO, "Режим Debug изменён");
        }

#if defined(ESP32)

        if (settings.debug == Debug::DBG_SERIAL) {
            if (b.Select(kk::debug_uart, "UART", "Serial0;Serial1;Serial2")) {
                settings.debug_uart = db[kk::debug_uart];

                DEBUG.begin(settings.debug_uart);

                DEBUG(SIMBOL_INFO, "UART Debug изменён");
            }
        }

#endif

        if (b.Select(kk::debug_lvl, "Уровень", "All;Info;Warning;Error")) {
            settings.debug_lvl = db[kk::debug_lvl];

            DEBUG(SIMBOL_INFO, "Уровень Debug изменён");
        }

        if (b.Switch(kk::color_debug, "Цветные метки / префиксы")) {
            settings.color_debug = db[kk::color_debug];
        }

        {
            sets::Buttons bt(b);

            if (b.Button("Текст")) {
                DEBUG("Просто сообщение без меток");
            }

            if (b.Button("NONE")) {
                DEBUG(SIMBOL_NONE, "Сообщение самого низкого приоритета");
            }

            if (b.Button("INFO")) {
                DEBUG(SIMBOL_INFO, "Информационное сообщение");
            }

            if (b.Button("WARN")) {
                DEBUG(SIMBOL_WAR, "Предупреждение");
            }

            if (b.Button("ERROR")) {
                DEBUG(SIMBOL_ERR, "Ошибка!");
            }
            if (b.Button("CUSTOM")) {
                DEBUG(SIMBOL_CUSTOM, "Пользовательское сообщение!");
            }
        }

        if (settings.debug == Debug::DBG_LOGGER) {
            b.Log(logger);

            if (b.Button("Очистить лог")) {
                logger.clear();

                b.reload();
            }
        }
    }
    if (b.Button("Обновить")) {
        b.reload();
    }
}

// ===================== SETUP =====================

void setup() {
    // Первичный запуск Serial для сообщений загрузки
    Serial.begin(DEBUG_SPEED);

    delay(300);

#ifdef ESP32

    if (!LittleFS.begin(true)) {
        Serial.println("LittleFS fail");
    }

#else

    LittleFS.begin();

#endif

    db.begin();

    db.init(kk::wifi_ssid, WIFI_SSID);
    db.init(kk::wifi_pass, WIFI_PASS);

    db.init(kk::wifi_ssid_reserv, "");
    db.init(kk::wifi_pass_reserv, "");

    db.init(kk::switchWifi, false);

    db.init(kk::ap_mode, 1);

    db.init(kk::ssid_ap, "ESP_Debug");
    db.init(kk::pass_ap, "12345678");

    db.init(kk::debug_mode, 1);
    db.init(kk::debug_lvl, 0);
    db.init(kk::color_debug, true);

    db.init(kk::debug_uart, 0);

    strncpy(
        settings.ssid,
        db[kk::wifi_ssid].c_str(),
        sizeof(settings.ssid) - 1);
    settings.ssid[sizeof(settings.ssid) - 1] = '\0';

    strncpy(
        settings.password,
        db[kk::wifi_pass].c_str(),
        sizeof(settings.password) - 1);
    settings.password[sizeof(settings.password) - 1] = '\0';

    strncpy(
        settings.ssid_reserv,
        db[kk::wifi_ssid_reserv].c_str(),
        sizeof(settings.ssid_reserv) - 1);

    settings.ssid_reserv[sizeof(settings.ssid_reserv) - 1] = '\0';
    strncpy(
        settings.password_reserv,
        db[kk::wifi_pass_reserv].c_str(),
        sizeof(settings.password_reserv) - 1);

    settings.password_reserv[sizeof(settings.password_reserv) - 1] = '\0';
    settings.switchWifi = db[kk::switchWifi];
    settings.ap = db[kk::ap_mode];

    strncpy(
        settings.ssid_ap,
        db[kk::ssid_ap].c_str(),
        sizeof(settings.ssid_ap) - 1);

    settings.ssid_ap[sizeof(settings.ssid_ap) - 1] = '\0';

    strncpy(
        settings.pass_ap,
        db[kk::pass_ap].c_str(),
        sizeof(settings.pass_ap) - 1);

    settings.pass_ap[sizeof(settings.pass_ap) - 1] = '\0';
    settings.debug = db[kk::debug_mode];
    settings.debug_lvl = db[kk::debug_lvl];
    settings.color_debug = db[kk::color_debug];
    settings.debug_uart = db[kk::debug_uart];

    DEBUG.begin(settings.debug_uart);
    WiFi.persistent(false);
    WiFi.mode(WIFI_STA);
    delay(200);
    DEBUG(SIMBOL_INFO, "Старт");

    wifi.begin();
    sett.begin();
    sett.onBuild(build);
    DEBUG(SIMBOL_INFO, "Settings OK");

    if (wifi.isConnected()) {
        DEBUG(SIMBOL_INFO, "IP: ", WiFi.localIP().toString());
    } else if (wifi.isAccessPoint()) {
        DEBUG(SIMBOL_INFO, "AP IP: ", WiFi.softAPIP().toString());
    }
}
void loop() {
    sett.tick();
    wifi.tick();
    db.tick();
    static uint32_t tmr;
    if (millis() - tmr > 10000) {
        tmr = millis();
        printHeap("--> ");
    }
}

```

*SEMONA* — это не просто монитор порта, это стиль и ретро-вайб в мире последовательных интерфейсов!
