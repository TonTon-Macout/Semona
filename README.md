# SEMONA - Serial Monitor
![semona982](https://github.com/user-attachments/assets/ae6de295-30f5-4d18-b2e7-0cc380f2d5d1)


**SEMONA** — это удобный монитор последовательного порта, предназначенный для взаимодействия с устройствами через COM-порты. Программа предоставляет гибкий интерфейс для отправки и получения данных, а также множество настроек для комфортной работы, включая поддержку тем оформления, управление цветами, нумерацию строк и многое другое.

Вдохновлена Монитором порта Arduino IDE, но без ардуино, без иде и с некоторыми плюшками

[ссылка](https://github.com/TonTon-Macout/Semona/releases/latest/download/Semona.zip) на последнюю версию (zip архив с иконками)

## Особенности

-  Простое управление портами, скоростью передачи, окончанием строк, можно включить выключить порт, сделать по верх окон итд.
- **Режим устройств**: Порт скорость и всякое такое сохраяняется под именем и в дальнейшем выбираем по имени.
- **Темы оформления**: Три встроенные темы — светлая, тёмная и ретро, с возможностью кастомизации цветов текста, меток времени и цветовых меткок.
- **Цветовые метки**: Поддержка цветового выделения сообщений (Info, Warning, Error, Custom) с использованием специальных символов (`0x01``0x02``0x03``0x04`).
- **Гибкие настройки**:
  - Отображение меток времени.
  - Подсчёт символов.
  - Нумерация строк в окне вывода.
  - Отлючение Семоны
  - и другие
- **незадокументированные фичи**:
  + у меня бывает зависает порт при открытии, и начинает сыпаться мусор, это и в ардуино иде происходит, но так как тудой сюдой портом дергать там сложнее, то и реже
    + лечится включением порта и выключением  
  + возможны небаги но фичи всякие, обнаружите - пишите
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

## Скриншоты

![Без имени-8](https://github.com/user-attachments/assets/d219311f-65d3-422c-a73c-01f55ba05d7c)





## Установка
Установка не требуется, просто распакуйте и поместите в нужную папку

## Использование

1. **Выбор порта и настроек**:
   - Выберите COM-порт из выпадающего списка.
   - Установите скорость передачи (baud rate), окончание строки (NL, CR, NL & CR) и другие параметры.
2. **Подключение**:
   - Нажмите кнопку включения (иконка "on/off") для открытия порта.
   - Отправляйте команды через поле ввода и наблюдайте за данными в окне вывода.
3. **Устройства**:
   - Включите режим устройств в настройках, чтобы сохранить конфигурации для разных устройств.
   - Добавляйте, редактируйте или удаляйте устройства в соответствующем диалоге.
4. **Кастомизация**:
   - Перейдите в меню настроек для изменения темы, размера шрифта, цветов и других параметров.
   - Активируйте режим "Семона" для уникального отображения сообщений.
     - или деактивируйте если ее довольное лицо вас раздражает...

## Конфигурационные файлы

- `settings.json`: Хранит основные настройки, такие как тема, порт, размер шрифта и т.д.
- `themes.json`: Определяет стили для светлой, тёмной и ретро тем, включая цвета текста и цветовых меток.
- `devices.json`: Сохраняет конфигурации устройств (порт, скорость, окончания строк и т.д.).

## Горячие клавиши

- **Enter**: Отправка команды из поля ввода.
- **ПКМ на окне вывода**: Контекстное меню с опциями копирования, очистки и вызова настроек.


## Разработка

Программа написана на Python с использованием PyQt6 для интерфейса и PySerial для работы с последовательными портами.



![Снимок экрана 2025-04-12 012830](https://github.com/user-attachments/assets/ef79a70f-7708-46dc-87b3-014b1be71f14)

---

Если вы нашли баг или хотите предложить улучшение, создайте issue или pull request! 😊

*SEMONA* — это не просто монитор порта, это стиль и ретро-вайб в мире последовательных интерфейсов!
