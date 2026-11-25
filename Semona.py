VERSION = "1.1"
NAME = "SEMONA"
GITHUB_REPO = "TonTon-Macout/Semona"
BUILD_DATE = "26 ноября 2026"
import sys, serial, serial.tools.list_ports, ctypes, json, os, re, time, traceback, requests
from copy import deepcopy
from ctypes import wintypes
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QTextEdit, QLineEdit, QPushButton, 
                            QComboBox, QCheckBox, QDialog, QFormLayout, QRadioButton,
                            QLabel, QGroupBox, QScrollArea, QMessageBox, QColorDialog,
                            QMenu, QSpinBox, QToolTip, QPlainTextEdit, QGraphicsDropShadowEffect,
                            QListWidget, QFontDialog, QListWidgetItem, QSplashScreen, QInputDialog
                            )
from PyQt6.QtCore import (QTimer, Qt, QThread, pyqtSignal, QMutex, QSize, QByteArray, 
                          QBuffer , QPoint, QRect, QMutexLocker, QEvent)
from PyQt6.QtGui import (QPainter, QImage, QIcon, QColor, QAction, QStandardItemModel, 
                         QStandardItem, QTextCursor, QTextCharFormat, QFont, QFontMetrics, 
                         QFontMetricsF,QPixmap, QGuiApplication, QSyntaxHighlighter)


if getattr(sys, "frozen", False):
    os.chdir(os.path.dirname(os.path.abspath(sys.executable)))

def resource_path(relative_path):
    """Абсолютный путь к ресурсу, встроенному в EXE или лежащему рядом с исходником."""
    base_path = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path).replace("\\", "/")


class ArduinoSyntaxHighlighter(QSyntaxHighlighter):
    """Подсветка синтаксиса Arduino/C++ для окна примера SEMONA."""

    def __init__(self, document):
        super().__init__(document)
        self.formats = {}

        def make_format(color, bold=False, italic=False):
            fmt = QTextCharFormat()
            fmt.setForeground(QColor(color))
            if bold:
                fmt.setFontWeight(QFont.Weight.Bold)
            if italic:
                fmt.setFontItalic(True)
            return fmt

        self.formats['keyword'] = make_format('#569CD6', True)
        self.formats['type'] = make_format('#4EC9B0')
        self.formats['function'] = make_format('#DCDCAA')
        self.formats['string'] = make_format('#CE9178')
        self.formats['comment'] = make_format('#6A9955', italic=True)
        self.formats['number'] = make_format('#B5CEA8')
        self.formats['constant'] = make_format('#4FC1FF')
        self.formats['preprocessor'] = make_format('#C586C0')

        self.rules = [
            (re.compile(r'\b(?:void|bool|boolean|byte|char|unsigned|signed|short|int|long|float|double|String|size_t|uint8_t|uint16_t|uint32_t)\b'), self.formats['type']),
            (re.compile(r'\b(?:if|else|for|while|do|switch|case|break|continue|return|const|static|volatile|struct|class|public|private|protected|new|delete|true|false|nullptr)\b'), self.formats['keyword']),
            (re.compile(r'\b(?:HIGH|LOW|INPUT|OUTPUT|INPUT_PULLUP|LED_BUILTIN|A[0-5])\b'), self.formats['constant']),
            (re.compile(r'\b(?:setup|loop|pinMode|digitalWrite|digitalRead|analogRead|analogWrite|millis|micros|delay|Serial|print|println|write|begin)\b'), self.formats['function']),
            (re.compile(r'\b(?:0[xX][0-9A-Fa-f]+|\d+(?:\.\d+)?(?:[uUlLfF]+)?)\b'), self.formats['number']),
            (re.compile(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\''), self.formats['string']),
            (re.compile(r'^\s*#\s*[A-Za-z_]\w*.*$'), self.formats['preprocessor']),
            (re.compile(r'//[^\n]*'), self.formats['comment']),
        ]

    def highlightBlock(self, text):
        # Продолжаем подсветку многострочных /* ... */ комментариев.
        comment_format = self.formats['comment']
        start = 0
        if self.previousBlockState() == 1:
            end = text.find('*/')
            if end == -1:
                self.setFormat(0, len(text), comment_format)
                self.setCurrentBlockState(1)
                return
            self.setFormat(0, end + 2, comment_format)
            start = end + 2

        self.setCurrentBlockState(0)
        block_start = text.find('/*', start)
        while block_start != -1:
            block_end = text.find('*/', block_start + 2)
            if block_end == -1:
                self.setFormat(block_start, len(text) - block_start, comment_format)
                self.setCurrentBlockState(1)
                break
            self.setFormat(block_start, block_end + 2 - block_start, comment_format)
            block_start = text.find('/*', block_end + 2)

        for pattern, fmt in self.rules:
            for match in pattern.finditer(text):
                # Не перекрашиваем фрагменты уже распознанных /* */ комментариев.
                if text.rfind('/*', 0, match.start()) > text.rfind('*/', 0, match.start()):
                    continue
                self.setFormat(match.start(), match.end() - match.start(), fmt)


def character_image(path):
    """Возвращает изображение текущего персонажа (Семона или Семона-деда)."""
    name = os.path.basename(path)
    try:
        with open("settings.json", "r", encoding="utf-8") as f:
            male = bool(json.load(f).get("character_male", False))
    except Exception:
        male = False
    if male:
        if name == "semona.png":
            return resource_path("icons/semon.png")
        if name == "semona_fun.png":
            return resource_path("icons/semon_fun.png")
    return resource_path(path)



def current_character_is_male():
    try:
        with open("settings.json", "r", encoding="utf-8") as f:
            return bool(json.load(f).get("character_male", False))
    except Exception:
        return False

def current_app_icon():
    return resource_path("icons/iconded.ico" if current_character_is_male() else "icons/icon.ico")

def current_app_logo():
    return resource_path("icons/logoded.png" if current_character_is_male() else "icons/logo.png")

def gendered_character_text(text, male):
    pairs = [
        ("Нашёл", "Нашла"), ("Нашел", "Нашла"),
        ("Смог", "Смогла"), ("Открыл", "Открыла"),
        ("Закрыл", "Закрыла"), ("Обнаружил", "Обнаружила"),
        ("Пытался", "Пыталась"), ("Установил", "Установила"),
        ("Согласился", "Согласилась"), ("Выбрал", "Выбрала"),
        ("Проверил", "Проверила"),
        ("Запустил", "Запустила"), ("Переключил", "Переключила"),
        ("Исправил", "Исправила"), ("Обиделся", "Обиделась"),
    ]
    for masculine, feminine in pairs:
        source, target = (feminine, masculine) if male else (masculine, feminine)
        text = re.sub(re.escape(source), target, text, flags=re.IGNORECASE)
    return text



DEFAULT_THEME = {'light': {'stylesheet': ' QWidget {background-color: #f3f5f7; color: #252a31;} QLineEdit#textsend {border: 1px solid '
                         '#cbd2da; background-color: #ffffff; color: #252a31; selection-background-color: #2878c7;} '
                         'QWidget#textContainer {border: 1px solid #cbd2da;} QTextEdit#outputText {background-color: '
                         '#ffffff; font-size: {font_size}px; color: {text_color}; font-family: Consolas; border:0; '
                         'selection-background-color: #2878c7;} QTextEdit#lineNumbers {background-color: #e9edf2; '
                         'border:0; border-right: 2px solid #cbd2da; font-family: Consolas; font-size: {font_size}px; '
                         'color: #77818d;} QComboBox#Combo {border: 1px solid #cbd2da; color: #252a31; '
                         'background-color: #ffffff; padding: 3px;} QMenu, QTextEdit, QLineEdit, QComboBox, QComboBox '
                         'QAbstractItemView {border: 1px solid #cbd2da; background-color: #ffffff; color: #252a31; '
                         'padding: 3px; selection-background-color: #2878c7; selection-color: #ffffff;} '
                         'QMenu::item:selected {background-color: #2878c7; color: #ffffff;} QLabel#charCountLabel '
                         '{color: #77818d;} QPushButton {background-color: #e7ebef; color: #252a31; border: 1px solid '
                         '#cbd2da; border-radius: 4px; padding: 4px 7px;} QPushButton:hover {background-color: '
                         '#d8e0e8;} QPushButton:pressed {background-color: #2878c7; color: #ffffff;} QGroupBox '
                         '{padding: 4px; border-radius: 5px; margin-top: 10px; border: 1px solid #cbd2da; color: '
                         '#252a31;} QGroupBox::title {margin: -14px 0px 0px 5px; padding: 4px 6px;} QCheckBox, '
                         'QRadioButton {spacing: 7px;} QCheckBox::indicator, QRadioButton::indicator {width: 16px; '
                         'height: 16px; border: 1px solid #77818d; background-color: #ffffff; border-radius: 3px;} '
                         'QCheckBox::indicator:checked, QRadioButton::indicator:checked {background-color: #2878c7; '
                         'border: 1px solid #2878c7;} QCheckBox::indicator:disabled, QRadioButton::indicator:disabled '
                         '{background-color: transparent; border: 1px solid #77818d;}',
           'default_timestamp_color': '#77818d',
           'default_sent_color': '#167d5a',
           'default_text_color': '#252a31',
           'control_chars_colors': {'info_color': '#21864b',
                                    'warning_color': '#b7791f',
                                    'error_color': '#c0392b',
                                    'custom_color': '#2878c7'},
           'theme': 'light',
           'off_color': '#dce3e9'},
 'retro': {'stylesheet': ' QWidget {background-color: #2a3b3f; color: #ffffff;} QLineEdit#textsend { border: 1px solid '
                         '#4a6a7a; background-color: #2a3b3f; color: #a3c1ad; } QWidget#textContainer { border: 1px '
                         'solid #3d6a7a;} QTextEdit#outputText {background-color: #3c4e52; font-size: {font_size}px; '
                         'color: {text_color}; font-family: Consolas; border:0;} QTextEdit#lineNumbers { '
                         'background-color: #273336; border:0; border-right: 3px solid #4a6a7a;  font-family: '
                         'Consolas; font-size: {font_size}px; color: #a3c1ad; } QComboBox#Combo {border: 1px solid '
                         '#3c4e52; color:#a3c1ad; background-color:#2a3b3f; }  QMenu, QTextEdit, QLineEdit, QComboBox, '
                         'QComboBox QAbstractItemView { border: 1px solid #3c4e52; background-color: #2a3b3f; color: '
                         '#a3c1ad; padding 3px; } QMenu::item:selected { background-color: #273336; } '
                         'QLabel#charCountLabel {color: #a3c1ad;}    QPushButton { background-color: #273336; color: '
                         '#adbac7;  border: 1px solid #C0C0C0; border-radius:4px;  padding: 4px 7px; }  QPushButton:hover '
                         '{ background-color: #333a43; } QGroupBox{padding: 4px; border-radius: 5px;margin-top:  10px; '
                         'border: 1px solid #c8c8c8;color: #a3c1ad;} QGroupBox::title{margin:-14px 0px 0px 5px; '
                         'padding: 4px 6px; } QCheckBox, QRadioButton { spacing: 7px; } QCheckBox::indicator, '
                         'QRadioButton::indicator { width: 16px; height: 16px; border: 1px solid palette(mid); '
                         'background-color: #ffffff; border-radius: 3px; } QCheckBox::indicator:checked, '
                         'QRadioButton::indicator:checked { background-color: #3984d6; border: 1px solid #2468b2; } '
                         'QCheckBox::indicator:disabled, QRadioButton::indicator:disabled { background-color: '
                         'transparent; border: 1px solid #888888; }',
           'default_timestamp_color': '#a3c1ad',
           'default_sent_color': '#ff43ec',
           'default_text_color': '#ffd5ab',
           'control_chars_colors': {'info_color': '#72c698',
                                    'warning_color': '#ffb155',
                                    'error_color': '#f35a3b',
                                    'custom_color': '#7996ff'},
           'theme': 'dark',
           'off_color': '#52595a'},
 'dark': {'stylesheet': ' QWidget {background-color: #20242b; color: #e6eaf0;} QLineEdit#textsend {border: 1px solid '
                        '#454e5b; background-color: #292f38; color: #e6eaf0; selection-background-color: #4c91d9;} '
                        'QWidget#textContainer {border: 1px solid #454e5b;} QTextEdit#outputText {background-color: '
                        '#1e232a; font-size: {font_size}px; color: {text_color}; font-family: Consolas; border:0; '
                        'selection-background-color: #4c91d9;} QTextEdit#lineNumbers {background-color: #252b33; '
                        'border:0; border-right: 2px solid #454e5b; font-family: Consolas; font-size: {font_size}px; '
                        'color: #9aa5b1;} QComboBox#Combo {border: 1px solid #454e5b; color: #e6eaf0; '
                        'background-color: #292f38; padding: 3px;} QMenu, QTextEdit, QLineEdit, QComboBox, QComboBox '
                        'QAbstractItemView {border: 1px solid #454e5b; background-color: #292f38; color: #e6eaf0; '
                        'padding: 3px; selection-background-color: #4c91d9; selection-color: #ffffff;} '
                        'QMenu::item:selected {background-color: #4c91d9; color: #ffffff;} QLabel#charCountLabel '
                        '{color: #9aa5b1;} QPushButton {background-color: #343c47; color: #e6eaf0; border: 1px solid '
                        '#454e5b; border-radius: 4px; padding: 4px 7px;} QPushButton:hover {background-color: '
                        '#414c59;} QPushButton:pressed {background-color: #4c91d9; color: #ffffff;} QGroupBox '
                        '{padding: 4px; border-radius: 5px; margin-top: 10px; border: 1px solid #454e5b; color: '
                        '#e6eaf0;} QGroupBox::title {margin: -14px 0px 0px 5px; padding: 4px 6px;} QCheckBox, '
                        'QRadioButton {spacing: 7px;} QCheckBox::indicator, QRadioButton::indicator {width: 16px; '
                        'height: 16px; border: 1px solid #9aa5b1; background-color: #292f38; border-radius: 3px;} '
                        'QCheckBox::indicator:checked, QRadioButton::indicator:checked {background-color: #4c91d9; '
                        'border: 1px solid #4c91d9;} QCheckBox::indicator:disabled, QRadioButton::indicator:disabled '
                        '{background-color: transparent; border: 1px solid #9aa5b1;}',
          'default_timestamp_color': '#9aa5b1',
          'default_sent_color': '#63b3ed',
          'default_text_color': '#e6eaf0',
          'control_chars_colors': {'info_color': '#68c58a',
                                   'warning_color': '#e6b65c',
                                   'error_color': '#f07178',
                                   'custom_color': '#82aaff'},
          'theme': 'dark',
          'off_color': '#3b4653'},
 'duino': {'stylesheet': ' QWidget {background-color: #006468; color: #ffffff;} '
                         'QLineEdit#textsend {border: 1px solid #17a1a5; background-color: #ffffff; color: #202020; '
                         'selection-background-color: #00979d;} QWidget#textContainer {border: 1px solid #17a1a5; '
                         'padding-top: 14px;} QTextEdit#outputText {background-color: #ffffff; font-size: {font_size}px; '
                         'color: {text_color}; font-family: Consolas; border: 0; selection-background-color: #00979d;} '
                         'QTextEdit#lineNumbers {background-color: #17a1a5; border: 0; border-right: 3px solid #00888e; '
                         'font-family: Consolas; font-size: {font_size}px; color: #202020;} QComboBox#Combo '
                         '{border: 1px solid #00888e; color: #ffffff; background-color: #006468; padding: 3px;} '
                         'QMenu, QTextEdit, QLineEdit, QComboBox, QComboBox QAbstractItemView '
                         '{border: 1px solid #c0c0c0; background-color: #e0e0e0; color: #202020; padding: 3px; '
                         'selection-background-color: #00979d; selection-color: #ffffff;} '
                         'QMenu::item:selected {background-color: #00979d; color: #ffffff;} '
                         'QLabel#charCountLabel {color: #e0e0e0;} QPushButton {background-color: #d8d8d8; '
                         'color: #202020; border: 1px solid #c0c0c0; border-radius: 4px; padding: 4px 7px;} '
                         'QPushButton:hover {background-color: #b8d8d6; color: #202020;} '
                         'QPushButton:pressed {background-color: #00979d; color: #ffffff;} '
                         'QGroupBox {padding: 4px; border-radius: 5px; margin-top: 10px; '
                         'border: 1px solid #17a1a5; color: #ffffff;} '
                         'QGroupBox::title {margin: -14px 0px 0px 5px; padding: 4px 6px;} '
                         'QCheckBox, QRadioButton {spacing: 7px;} '
                         'QCheckBox::indicator, QRadioButton::indicator {width: 16px; height: 16px; '
                         'border: 1px solid #00888e; background-color: #ffffff; border-radius: 3px;} '
                         'QCheckBox::indicator:checked, QRadioButton::indicator:checked '
                         '{background-color: #00979d; border: 1px solid #006468;} '
                         'QCheckBox::indicator:disabled, QRadioButton::indicator:disabled '
                         '{background-color: transparent; border: 1px solid #888888;}',
           'default_timestamp_color': '#777777',
           'default_sent_color': '#e87524',
           'default_text_color': '#263238',
           'control_chars_colors': {'info_color': '#387a3c',
                                    'warning_color': '#a65e00',
                                    'error_color': '#c62828',
                                    'custom_color': '#007f86'},
           'theme': 'light',
           'off_color': '#c8d2dc'},
 'ocean': {'stylesheet': ' QWidget {background-color: #172b3a; color: #e8f2f7;} QLineEdit#textsend {border: 1px solid '
                         '#36576a; background-color: #203b4d; color: #e8f2f7; selection-background-color: #26a6a1;} '
                         'QWidget#textContainer {border: 1px solid #36576a;} QTextEdit#outputText {background-color: '
                         '#142735; font-size: {font_size}px; color: {text_color}; font-family: Consolas; border:0; '
                         'selection-background-color: #26a6a1;} QTextEdit#lineNumbers {background-color: #1c3444; '
                         'border:0; border-right: 2px solid #36576a; font-family: Consolas; font-size: {font_size}px; '
                         'color: #91adbd;} QComboBox#Combo {border: 1px solid #36576a; color: #e8f2f7; '
                         'background-color: #203b4d; padding: 3px;} QMenu, QTextEdit, QLineEdit, QComboBox, QComboBox '
                         'QAbstractItemView {border: 1px solid #36576a; background-color: #203b4d; color: #e8f2f7; '
                         'padding: 3px; selection-background-color: #26a6a1; selection-color: #ffffff;} '
                         'QMenu::item:selected {background-color: #26a6a1; color: #ffffff;} QLabel#charCountLabel '
                         '{color: #91adbd;} QPushButton {background-color: #29495d; color: #e8f2f7; border: 1px solid '
                         '#36576a; border-radius: 4px; padding: 4px 7px;} QPushButton:hover {background-color: '
                         '#355f77;} QPushButton:pressed {background-color: #26a6a1; color: #ffffff;} QGroupBox '
                         '{padding: 4px; border-radius: 5px; margin-top: 10px; border: 1px solid #36576a; color: '
                         '#e8f2f7;} QGroupBox::title {margin: -14px 0px 0px 5px; padding: 4px 6px;} QCheckBox, '
                         'QRadioButton {spacing: 7px;} QCheckBox::indicator, QRadioButton::indicator {width: 16px; '
                         'height: 16px; border: 1px solid #91adbd; background-color: #203b4d; border-radius: 3px;} '
                         'QCheckBox::indicator:checked, QRadioButton::indicator:checked {background-color: #26a6a1; '
                         'border: 1px solid #26a6a1;} QCheckBox::indicator:disabled, QRadioButton::indicator:disabled '
                         '{background-color: transparent; border: 1px solid #91adbd;}',
           'default_timestamp_color': '#91adbd',
           'default_sent_color': '#79c0ff',
           'default_text_color': '#e8f2f7',
           'control_chars_colors': {'info_color': '#56c596',
                                    'warning_color': '#f0bd63',
                                    'error_color': '#ff7373',
                                    'custom_color': '#70b7d8'},
           'theme': 'dark',
           'off_color': '#294657'}}


# Отдельные правила нужны, чтобы цвета контекстного меню и раскрытого списка
# редактировались независимо от общего оформления QTextEdit/QComboBox.
_THEME_EXTRA_RULES = {
    "light": "QMenu { background-color: #ffffff; color: #252a31; } QMenu::item:selected { background-color: #2878c7; color: #ffffff; } QComboBox#Combo QAbstractItemView { background-color: #ffffff; color: #252a31; } QComboBox#Combo QAbstractItemView::item:selected { background-color: #2878c7; color: #ffffff; }",
    "retro": "QMenu { background-color: #2a3b3f; color: #a3c1ad; } QMenu::item:selected { background-color: #273336; color: #ffffff; } QComboBox#Combo QAbstractItemView { background-color: #2a3b3f; color: #a3c1ad; } QComboBox#Combo QAbstractItemView::item:selected { background-color: #273336; color: #ffffff; }",
    "dark": "QMenu { background-color: #292f38; color: #e6eaf0; } QMenu::item:selected { background-color: #4c91d9; color: #ffffff; } QComboBox#Combo QAbstractItemView { background-color: #292f38; color: #e6eaf0; } QComboBox#Combo QAbstractItemView::item:selected { background-color: #4c91d9; color: #ffffff; }",
    "duino": "QMenu { background-color: #e0e0e0; color: #202020; } QMenu::item:selected { background-color: #00979d; color: #ffffff; } QComboBox#Combo QAbstractItemView { background-color: #e0e0e0; color: #202020; } QComboBox#Combo QAbstractItemView::item:selected { background-color: #00979d; color: #ffffff; }",
    "ocean": "QMenu { background-color: #203b4d; color: #e8f2f7; } QMenu::item:selected { background-color: #26a6a1; color: #ffffff; } QComboBox#Combo QAbstractItemView { background-color: #203b4d; color: #e8f2f7; } QComboBox#Combo QAbstractItemView::item:selected { background-color: #26a6a1; color: #ffffff; }",
}
for _theme_name, _extra_rules in _THEME_EXTRA_RULES.items():
    if _theme_name in DEFAULT_THEME:
        DEFAULT_THEME[_theme_name]["stylesheet"] += " " + _extra_rules


class SerialMonitor(QMainWindow):

    def __init__(self, splash=None):
        super().__init__()
        
        self.splash = splash  #
        self.on_start = True
        self.update_available = False
        self.latest_version = None
        #self.check_latest_version()
        
        # Инициализация ThemeManager
        self.theme_manager = ThemeManager()
        self.themes = self.theme_manager.themes
        self.current_theme = self.theme_manager.get_current_theme()
        
        self.setWindowTitle(NAME)
        self.setGeometry(100, 100, 800, 700)
        self.center_window()
        
        if not os.path.exists('settings.json'):
            self.save_settings(**self.default_settings())
        
        self.serial_port = serial.Serial()
        self.serial_port.timeout = 0.01
        self.serial_port.write_timeout = 0.5
        self.serial_port.dtr = False  # Отключаем DTR перед открытием порта
        self.serial_port.close()  # закрытие порта
      

        self.reader = None
        self._serial_session_active = False
        self._serial_disconnect_handled = False
        self.message_info = "#213e1e" # зеленый
        self.message_warning = "#f26339" # оранжевый
        self.message_error = "#bb332c" # красный
        self.message_custom = "#2b44bb"  # синий

        
        self.data_buffer = []
        self.buffer_mutex = QMutex()
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.flush_buffer_to_display)
        self.update_timer.start(50)
        
        
        
        
        
        
        
        main_widget = QWidget()
        main_widget.setObjectName("mainContainer")
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        input_panel = QWidget()
        input_panel.setObjectName("inputPanel")
        input_panel.setStyleSheet("""
            QWidget#inputPanel { padding: 0px; margin: 0px; background-color: transparent; }
        """)
        input_layout = QHBoxLayout(input_panel)
        input_layout.setContentsMargins(0, 0, 0, 0)  # Отступы от краев: left, top, right, bottom (уменьшены с 0 до 2 для примера)
        input_layout.setSpacing(0)
        
        self.on_top = QCheckBox()
        self.on_top.setObjectName("on_top")
        self.on_top.setChecked(False)
        self.on_top.setFixedSize(30, 30)
        self.on_top.setIconSize(QSize(18, 18))
        self.on_top.setToolTip('Поверх всех окон')
        self.on_top.stateChanged.connect(self.toggle_on_top)
        icon_path = "icons/top_off.png"
        self.on_top.setIcon(QIcon(resource_path(icon_path)))
        self.on_top.setStyleSheet("""
            QCheckBox#on_top {
                background-color: transparent;
                border: none;
                margin: 0px -10px 0px -2px;
                padding: 0px;
            }
            QCheckBox::indicator#on_top {
                width: 0px;
                height: 0px;
                background: none;
                border: none;
                 margin: 0px;
                padding: 0px;
            }
            QCheckBox::indicator:checked#on_top, QCheckBox::indicator:unchecked#on_top {
                width: 0px;
                height: 0px;
                margin: 0px;
                padding: 0px;
            }
        """)
        input_layout.addWidget(self.on_top)

        self.input_field = QLineEdit()
        self.input_field.setObjectName("textsend")
        self.input_field.setFixedHeight(25)
        self.input_field.setStyleSheet("""
            QLineEdit#textsend {
                padding: 3px;
                border-top-right-radius: 4px;
                border-bottom-right-radius: 4px;
                margin: 0px; 
                margin-right: 4px;
                
            }

        """)
        self.input_field.returnPressed.connect(self.send_command)
        self.send_button = QPushButton()
        self.send_button.setObjectName("sendButton")
        self.send_button.setFixedSize(30, 30)
        self.send_button.setIconSize(QSize(24, 24))
        self.send_button.setIcon(QIcon(resource_path("icons/send.png")))
        self.send_button.setStyleSheet("""
            QPushButton#sendButton {
                background-color: transparent;
                border: none;
                margin-right: 0px;
                padding: 0px;
            }

        """)
        self.send_button.clicked.connect(self.send_command)
        self.send_button.setToolTip('Отправить в порт')
        input_layout.addWidget(self.input_field)
        input_layout.addWidget(self.send_button)
       
        layout.addWidget(input_panel)
        
        self.text_container = QWidget()
        self.text_container.setObjectName("textContainer")
        self.text_container.setStyleSheet("""
            QWidget#textContainer {
                border-top-right-radius: 5px;
                padding-top: 3px; 
                
            }
            QTextEdit#outputText {
                border-top-right-radius: 5px; 
                padding-top: 3px;
                padding-right: 3px;
                padding-bottom: 3px;
            }
            QTextEdit#lineNumbers {
                padding-top: 3px;
                padding-bottom: 3px;
            }
            
        """)
        text_layout = QHBoxLayout(self.text_container)
        text_layout.setContentsMargins(1, 1, 1, 1)
        text_layout.setSpacing(0)

        self.line_numbers = QTextEdit()
        self.line_numbers.setObjectName("lineNumbers")
        self.line_numbers.setReadOnly(True)
        # Линейка не должна растягиваться на свободное место при пустом выводе.
        self.line_numbers.setFixedWidth(34)

        self.line_numbers.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.line_numbers.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.line_numbers.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        
        self.line_numbers.setEnabled(True)  # Виджет активен для синхронизации
        self.line_numbers.setAttribute(Qt.WidgetAttribute.WA_NoMousePropagation, True)  # Блокируем события мыши
        self.line_numbers.viewport().installEventFilter(self)  # Устанавливаем фильтр событий для viewport
        
        text_layout.addWidget(self.line_numbers)

        self.output_text = QTextEdit()
        self.output_text.setObjectName("outputText")

            
        self.output_text.setReadOnly(True)
        self.output_text.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.output_text.customContextMenuRequested.connect(self.show_context_menu)
        text_layout.addWidget(self.output_text)

                # Основной текст управляет линейкой. Обратную синхронизацию делаем
        # только от колеса мыши над линейкой, чтобы добавление новых номеров
        # не вызывало самопроизвольную прокрутку основного текста вниз.
        self._syncing_line_scroll = False
        self.output_text.verticalScrollBar().valueChanged.connect(self.sync_line_number_scroll)
        layout.addWidget(self.text_container)
        
        control_panel = QWidget()
        
        control_panel.setObjectName("controlPanel")
        control_layout = QHBoxLayout(control_panel)
        control_panel.setStyleSheet("""
            QWidget#controlPanel { background-color: transparent; margin: 0px 0px; padding: 0px; }
        """)
        control_layout.setContentsMargins(0, 0, 8, 0)  # Отступы от краев: left, top, right, bottom (уменьшены с 0 до 2 для примера)
        control_layout.setSpacing(1)
        self.stop_button = QPushButton()
        self.stop_button.setObjectName("stopButton")
        self.stop_button.setFixedSize(35, 25)
        self.stop_button.setIconSize(QSize(24, 24))
        self.stop_button.setIcon(QIcon(resource_path("icons/off.png")))
        self.stop_button.setStyleSheet("""
            QPushButton#stopButton {
                background-color: transparent;
                border: none;
                margin: 0px 0px;
                padding: 0px;
                margin-left: 2px;
                text-align: left;                       
            }

        """)
        self.stop_button.clicked.connect(self.toggle_serial)
        self.stop_button.setToolTip('Закрыть/открыть порт')
        control_layout.addWidget(self.stop_button)
        self.combo_style = """
            QComboBox#Combo {
                padding: 3px;
                padding-left: 6px;
                border-radius: 0; 
                min-width: 80px;  
                margin-left:4px;
                border-top-left-radius: 4px; 
                border-bottom-left-radius: 4px; 
                              
            }
            QComboBox#deviceCombo QAbstractItemView{
                
            }

        """   
        self.device_combo = QComboBox()
        self.device_combo.setObjectName("Combo")
        self.device_combo.setStyleSheet(self.combo_style)
        #self.device_combo.currentTextChanged.connect(self.change_device)#apply_device_settings
        self.device_combo.setVisible(False)
        control_layout.addWidget(self.device_combo)
        
        self.port_combo = PortComboBox()
        self.port_combo.setObjectName("Combo")
        self.port_combo.setStyleSheet(self.combo_style)

        self.port_combo.update_ports_callback = self.update_ports  # Устанавливаем callback для обновления портов
        self.update_ports()
        self.port_combo.currentTextChanged.connect(self.change_port)
        control_layout.addWidget(self.port_combo)
        
        self.baud_combo = QComboBox()
        self.baud_combo.setObjectName("Combo")
        self.baud_combo.setStyleSheet(self.combo_style)
        baud_rates = [
            '', '300', '600', '1200', '2400', '4800', '9600', '14400', 
            '19200', '28800', '38400', '57600', '115200', '230400', 
            '460800', '500000', '576000', '921600', '1000000', '1152000', 
            '1500000', '2000000'
        ]
        
        self.baud_combo.addItems(baud_rates)
        self.baud_combo.setCurrentText('')
        self.baud_combo.currentTextChanged.connect(self.change_baudrate)
        control_layout.addWidget(self.baud_combo)
        
        self.line_ending_combo = QComboBox()
        self.line_ending_combo.setObjectName("Combo")
        self.line_ending_combo.setStyleSheet(self.combo_style)
        self.line_ending_combo.addItems(["Нет конца строки", "NL", "CR", "NL & CR"])
        self.line_ending_combo.setCurrentText("NL")
        #self.line_ending_combo.currentTextChanged.connect(self.save_serial_settings)
        self.line_ending_combo.currentTextChanged.connect(self.on_line_ending_changed)
        control_layout.addWidget(self.line_ending_combo)

        self.char_count_label = QLabel("0")
        self.char_count_label.setObjectName("charCountLabel")
        self.char_count_label.setVisible(False)
        control_layout.addWidget(self.char_count_label)
        self.char_count_label.setStyleSheet("""
            QLabel#charCountLabel {
                background-color: transparent;
                border: none;
                margin: 0px 0px 0px 10px;
                padding: 0px;
            }
        """)
        
        self.clear_button = QPushButton()
        self.clear_button.setObjectName("clearButton")
        self.clear_button.setToolTip('Очистить')
        self.clear_button.setFixedSize(25, 25)
        self.clear_button.setIconSize(QSize(20, 20))
        self.clear_button.setIcon(QIcon(resource_path("icons/clear.png")))
        self.clear_button.setStyleSheet("""
            QPushButton#clearButton {
                background-color: transparent;
                border: none;
                margin-right: 0px;
                padding: 0px;
                
            }

        """)
        self.clear_button.clicked.connect(self.clear_output)
        control_layout.addWidget(self.clear_button)

        # Запасная кнопка очистки появляется, если штатная кнопка уходит
        # за правый край монитора. Она находится в панели управления между
        # кнопкой открытия/закрытия порта и выпадающими списками.
        self.edge_clear_button = QPushButton(control_panel)
        self.edge_clear_button.setObjectName("edgeClearButton")
        self.edge_clear_button.setToolTip("Очистить")
        self.edge_clear_button.setFixedSize(25, 25)
        self.edge_clear_button.setIconSize(QSize(20, 20))
        self.edge_clear_button.setIcon(QIcon(resource_path("icons/clear.png")))
        self.edge_clear_button.setStyleSheet("""
            QPushButton#edgeClearButton {
                background-color: transparent;
                border: none;
                margin: 0px;
                padding: 0px;
            }
        """)
        self.edge_clear_button.clicked.connect(self.clear_output)
        control_layout.insertWidget(1, self.edge_clear_button)
        self.edge_clear_button.hide()

        self.timestamp_check = QCheckBox()
        self.timestamp_check.setObjectName("timestampCheck")
        self.timestamp_check.setToolTip('Отметки времени')
        self.timestamp_check.setFixedSize(26, 25)
        self.timestamp_check.setIconSize(QSize(22, 22))
        self.update_timestamp_icon(self.timestamp_check.isChecked())
        self.timestamp_check.stateChanged.connect(self.save_serial_settings)
        self.timestamp_check.stateChanged.connect(lambda state: self.update_timestamp_icon(state == Qt.CheckState.Checked.value))
        self.timestamp_check.setStyleSheet("""
            QCheckBox {
                background-color: transparent;
                border: none;
                margin-right: 0px;
                padding: 0px;
            }
            QCheckBox::indicator {
                width: 0px;
                height: 0px;
                background: none;
                border: none;
            }
            QCheckBox::indicator:checked, QCheckBox::indicator:unchecked {
                width: 0px;
                height: 0px;
            }
        """)
        control_layout.addWidget(self.timestamp_check)
        
        layout.addWidget(control_panel)
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        self.reader = None

        # Очищаем буфер вывода при запуске
        self.themes = self.theme_manager.themes  # Единый источник тем
        ###self.###()
              # Закрываем заставку после инициализации
        if self.splash:
            #QThread.sleep(4)  # Задержка 18 секунд
            QTimer.singleShot(200, self.splash.close)
        self.check_files_and_initialize()

        #self.load_themes()  # Загружаем темы из файла
        self.apply_theme()
        self.load_settings_and_apply()
        

        self.control_chars = {
            '\x00': "#FFFFFF",  # NULL - None - цвет текста
            '\x01': '#00FF00',  # SOH - Info - зеленый
            '\x02': '#FFFF00',  # STX - Warning - желтый
            '\x03': '#FF0000',  # ETX - Error - красный
            '\x04': '#00FFFF'   # EOT - Custom - голубой
        }
        #self.use_control_chars = False

        self.start()



        self.setIcon()
        self.enable_rounded_corners()
        self.last_displayed_line = None

        self.on_start = False


    def eventFilter(self, obj, event):
        # Колесо над линейкой прокручивает основной вывод. Не связываем
        # scrollbar линейки обратно: QTextEdit сам прокручивает курсор к концу
        # при добавлении номеров, что иначе могло бы увести вывод вниз.
        if obj == self.line_numbers.viewport() and event.type() == QEvent.Type.Wheel:
            bar = self.output_text.verticalScrollBar()
            delta = event.angleDelta().y()
            steps = delta // 120
            if steps:
                bar.setValue(bar.value() - steps * bar.singleStep() * 3)
            return True
        return super().eventFilter(obj, event)

    def update_edge_clear_button(self):
        """Показывает запасную кнопку, если штатная ушла за правый край экрана.

        Кнопка является элементом control_layout, поэтому при её появлении
        выпадающие списки автоматически сдвигаются вправо, а не перекрываются.
        """
        if not hasattr(self, "edge_clear_button") or not hasattr(self, "clear_button"):
            return

        try:
            clear_rect = QRect(
                self.clear_button.mapToGlobal(QPoint(0, 0)),
                self.clear_button.size()
            )
            screens = QGuiApplication.screens()
            # Если кнопка полностью видна хотя бы на одном мониторе,
            # запасная кнопка не нужна.
            if any(screen.geometry().contains(clear_rect) for screen in screens):
                self.edge_clear_button.hide()
                return

            center = self.frameGeometry().center()
            screen = QGuiApplication.screenAt(center) or self.screen()
            if screen is None or clear_rect.right() <= screen.geometry().right():
                self.edge_clear_button.hide()
                return

            # Элемент уже вставлен в control_layout на позицию сразу после stop_button.
            self.edge_clear_button.show()
        except Exception:
            self.edge_clear_button.hide()

    def moveEvent(self, event):
        super().moveEvent(event)
        QTimer.singleShot(0, self.update_edge_clear_button)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        QTimer.singleShot(0, self.update_edge_clear_button)

    def enable_rounded_corners(self):
        hwnd = self.winId().__int__()
        DWMWA_WINDOW_CORNER_PREFERENCE = 33  # Константа для настройки углов
        DWMNCRP_ROUND = 2  # Значение для скругленных углов

        # Устанавливаем скругленные углы
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd,
            DWMWA_WINDOW_CORNER_PREFERENCE,
            ctypes.byref(ctypes.c_int(DWMNCRP_ROUND)),
            ctypes.sizeof(ctypes.c_int)
        )
    
    def check_latest_version(self):
        self.update_available = False
        self.latest_version = None
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            response = requests.get(
                f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest",
                headers=headers,
                timeout=2
            )
            response.raise_for_status()
            data = response.json()
            self.latest_version = data["tag_name"].lstrip("v")
            if self.latest_version != VERSION:
                self.update_available = True
                message = f"Доступна новая версия: {self.latest_version}"
            else:
                message =f"Нет обновлений, версия: {VERSION}"
        except requests.exceptions.RequestException as e:
            message =f"Ошибка проверки обновления: {e}"
      
        settings = self.load_settings()
        if settings.get("debug", False):
                self.append_colored_text(f'[debug] {message}', self.message_info, True, False)


    def open_latest_release_page(self):
        import webbrowser
        webbrowser.open(f"https://github.com/{GITHUB_REPO}/releases/latest")   

    def center_window(self):
        # Получаем размеры экрана
        screen_geometry = QGuiApplication.primaryScreen().geometry()
        screen_width = screen_geometry.width()
        screen_height = screen_geometry.height()

        # Получаем размеры окна
        window_width = self.frameGeometry().width()
        window_height = self.frameGeometry().height()

        # Рассчитываем координаты для центрирования
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2

        # Перемещаем окно
        self.move(x, y)

    def get_greeting(self):
        current_hour = datetime.now().hour
        if 5 <= current_hour < 12:
            return "Доброе утро! "
        elif 12 <= current_hour < 18:
            return "Добрый день! "
        elif 18 <= current_hour < 22:
            return "Добрый вечер! "
        else:
            return "Доброй ночи! "




    def start(self):
        settings = self.load_settings()
        dbg = settings.get("debug", False)
        dbg_extra = settings.get("debug_extra", False)
        semona = settings.get("semona", True)
        open_startup = settings.get("open_startup", True)
        message = ""
        greeting = self.get_greeting()  # Приветствие всегда включается при старте






        try:
            # Проверяем, инициализирован ли serial_port
            if not hasattr(self, 'serial_port') or self.serial_port is None:
                self.serial_port = serial.Serial()

            # Определяем режим
            use_devices = settings.get("use_devices", False)






            if use_devices:
                # Режим устройства
                last_device = settings.get("last_device", "")

                if not last_device or not last_device.strip():
                    if semona:     message = f"{greeting}Не нашёл последнее устройство в настройках! "
                    else:          message = f"Последнее устройство не указано"

                    self.append_colored_text(message, self.message_warning, True, True, True)

                    self.stop_serial_read()
                    self.stop_serial_port(mute=True)

                    return

                # Загружаем настройки устройства
                devices = self.load_devices()
                if last_device not in devices:
                    if semona:     message = f"{greeting}Не нашёл устройство '{last_device}' в настройках!"
                    else:          message = f"Устройство '{last_device}' не найдено"

                    self.append_colored_text(message, self.message_error, True, True, True)
                    self.stop_serial_read()
                    self.stop_serial_port(mute=True)

                    return

                device = devices[last_device]
                port = device.get("port", "")
                baudrate = device.get("baudrate", "")
                line_ending = device.get("line_ending", "NL")
                timestamp = device.get("timestamp", False)
                use_control_chars = device.get("use_control_chars", False)

                # Проверка порта
                if not port.strip():
                    if semona:   message = f"{greeting}Для устройства '{last_device}' не указан порт!"
                    else:        message = f"Порт для устройства '{last_device}' не указан"

                    self.append_colored_text(message, self.message_error, True, True, True)
                    self.stop_serial_read()
                    self.stop_serial_port(mute=True)

                    return

                # Проверка скорости
                if not baudrate.strip():
                    if semona:    message = f"{greeting}Для устройства '{last_device}' не указана скорость!"
                    else:         message = f"Скорость для устройства '{last_device}' не указана"

                    self.append_colored_text(message, self.message_error, True, True, True)
                    self.stop_serial_read()
                    self.stop_serial_port(mute=True)

                    return

                # Применяем настройки устройства
                self.device_combo.setCurrentText(last_device)
                #self.port_combo.setCurrentText(port)
                #self.baud_combo.setCurrentText(baudrate)
                self.line_ending_combo.setCurrentText(line_ending)
                self.timestamp_check.setChecked(timestamp)
                self.use_control_chars = use_control_chars
              
                self.update_devices()
                if not open_startup:
                    self.stop_serial_read()
                    self.stop_serial_port(mute=True)

                    if semona:        message = f"{greeting} Порт выключен, нажми включить порт!"
                    else:             message = f" Порт выключен"
                # Открываем порт
                else: self.open_serial_port(port, baudrate)

                # Отладочный вывод настроек устройства
                if dbg:
                    message = f"[debug] start - Применены настройки устройства '{last_device}': порт {port}, скорость {baudrate}"
                    self.append_colored_text(message, self.message_warning, True, False, False)

            else:
                # Режим порта и скорости
                port = settings.get("port", "") or ""  
                baudrate = settings.get("baudrate", "") or ""  

                # Проверка порта 
                if not port.strip(): # если порт в настройках не указан
                    port = self.port_combo.currentText() # проверяем порт в выпадающем списке
                    
                    
                    if not port.strip(): # не указан порт и там то 
                       if semona:   message = f"{greeting}Не нашёл ни одного подходящего порта!"
                       else:        message = f"Нет доступных портов"
                     
                       self.append_colored_text(message, self.message_warning, True, True, True)
                       self.stop_serial_read()
                       self.stop_serial_port(mute=True)
                       return                   
                   
                    else: # порт в выпадающем списке указн
                       #if semona:   message = f"{greeting}Нашла подходящий порт {port}!"
                       #else:        message = f"Выбран порт {port}"
                       pass



                # Проверка скорости
                if not baudrate.strip():
                    if semona:        message = f"{greeting}Выбери скорость!"
                    else:             message = f"Скорость не указана в настройках"

                    self.append_colored_text(message, self.message_warning, True, True, True)
                    self.stop_serial_read()
                    self.stop_serial_port(mute=True)

                    return

                # Применяем настройки порта и скорости
                self.port_combo.setCurrentText(port)
                self.baud_combo.setCurrentText(baudrate)

                # Отладочный вывод настроек
                if dbg:
                    message = f"[debug] start - Применены настройки: порт {port}, скорость {baudrate}"
                    self.append_colored_text(message, self.message_warning, True, False, False)


                if not open_startup:
                    self.stop_serial_read()
                    self.stop_serial_port(mute=True)
                    if semona:        message = f"{greeting} Порт выключен, нажми включить порт!"
                    else:             message = f" Порт выключен"
                # Открываем порт
                else: 
                    pass
                    #self.open_serial_port(port, baudrate, on_start=True)

        except AttributeError as e:
            # Ошибка, если serial_port или другие атрибуты не инициализированы
            if semona:    message = f"{greeting}Не смог корректно инициализировать порт"
            else:         message = f"Порт не инициализирован корректно"
            self.append_colored_text(message, self.message_error, True, True, True)

            if dbg and dbg_extra:
                error_details = f"[debug_extra] start - Ошибка: {type(e).__name__}: {str(e)}\n"
                error_details += "".join(traceback.format_exc())
                self.append_colored_text(error_details, self.message_warning, True, True, True)

            self.stop_serial_read()
            self.stop_serial_port(mute=True)

        except Exception as e:
            # Общий случай для непредвиденных ошибок
            if semona:     message = f"{greeting}Не смог запустить порт, неизвестная ошибка: {str(e)}"
            else:          message = f"Неизвестная ошибка при запуске порта: {str(e)}"
            self.append_colored_text(message, self.message_error, True, True, True)

            if dbg and dbg_extra:
                error_details = f"[debug_extra] start - Ошибка: {type(e).__name__}: {str(e)}\n"
                error_details += "".join(traceback.format_exc())
                self.append_colored_text(error_details, self.message_warning, True, True, True)

            self.stop_serial_read()
            self.stop_serial_port(mute=True)








    def clear_buffer(self):
        # Вызывается при новом открытии порта, до запуска reader.
        self.serial_port.reset_input_buffer()
        self.serial_port.reset_output_buffer()
        self.buffer_mutex.lock()
        try:
            self.data_buffer.clear()
        finally:
            self.buffer_mutex.unlock()

    def stop_serial_port(self, mute=False):
        # Явное закрытие пользователем не является потерей соединения.
        self._serial_session_active = False
        settings = self.load_settings()
        dbg = settings.get("debug", False)# and 
        dbg_extra = settings.get("debug_extra", False)
        semona = settings.get("semona", True)  
        mute_ = settings.get("mute", False)  
        if mute_: mute = True

        message = ""
        greeting = ""
        if not mute:
            if self.on_start:    greeting = self.get_greeting()
            else:                greeting = ""

        try:
            # Проверка инициализации порта
            if not hasattr(self, 'serial_port') or self.serial_port is None:
                if semona:    message = f"{greeting}Порт не инициализирован!"
                else:         message = f"Порт не инициализирован"
               
                if not mute:  self.append_colored_text(message, self.message_error, True, True, True)
                self.stop_serial_read()
                self.switch_on_off_icon()
                return

            # Отладочный вывод доступных портов
            if dbg:
                try:
                    available_ports = [port.device for port in serial.tools.list_ports.comports()]
                    message = f"[debug] stop_serial_port - Доступные порты: {available_ports}"
                    self.append_colored_text(message, self.message_warning, True, False, False)
                except Exception as port_error:
                    message = f"[debug] stop_serial_port - Ошибка при получении портов: {str(port_error)}"
                    self.append_colored_text(message, self.message_warning, True, False, False)

            # Сначала останавливаем поток, который использует serial_port,
            # и только после этого закрываем сам порт.
            self.stop_serial_reader()
            if self.serial_port.is_open:
                self.serial_port.close()
                if semona:          message = f"{greeting}Закрыл порт {self.serial_port.port}"
                else:               message = f"Порт {self.serial_port.port} закрыт"
               
                if not mute: self.append_colored_text(message, self.message_info, True, True)
            else:
                if semona:          message = f"{greeting}Странно, но порт {self.serial_port.port} уже закрыт"
                else:               message = f"Порт {self.serial_port.port} уже закрыт"
                
                if not mute: self.append_colored_text(message, self.message_info, True, True)

            self.set_output_background(False)
            self.switch_on_off_icon()

        except serial.SerialException as e:
            # Определяем причину ошибки и формируем сообщение
            error_message = str(e).lower()
            if "access is denied" in error_message or "permission denied" in error_message:
                if semona:           message = f"{greeting}Не смог закрыть порт {self.serial_port.port}, доступ запрещён"
                else:                message = f"Доступ к порту {self.serial_port.port} запрещён"
            elif "no such file or directory" in error_message or "port not found" in error_message:
                if semona:           message = f"{greeting}Не смог найти порт {self.serial_port.port}"
                else:                message = f"Порт {self.serial_port.port} не существует"
            elif "device or resource busy" in error_message:
                if semona:           message = f"{greeting}Не смог закрыть порт {self.serial_port.port}, он занят другим приложением"
                else:                message = f"Порт {self.serial_port.port} занят другим приложением"
            elif "port is already closed" in error_message:
                if semona:           message = f"{greeting}Пытался закрыть порт {self.serial_port.port}, но он уже закрыт"
                else:                message = f"Порт {self.serial_port.port} уже закрыт"
            elif "parameter is incorrect" in error_message:
                if semona:           message = f"{greeting}Не смог закрыть порт {self.serial_port.port}, параметры неверные"
                else:                message = f"Неверные параметры порта {self.serial_port.port}"
            else:
                if semona:           message = f"{greeting}Не смог закрыть порт {self.serial_port.port}, ошибка: {str(e)}"
                else:                message = f"Ошибка закрытия порта {self.serial_port.port}: {str(e)}"

            if not mute: self.append_colored_text(message, self.message_error, True, True, True)

            # Отладочная информация об ошибке
            if dbg and dbg_extra:
                error_details = f"[debug_extra] stop_serial_port - Ошибка: {type(e).__name__}: {str(e)}\n"
                error_details += "".join(traceback.format_exc())
                
                self.append_colored_text(error_details, self.message_warning, True, True, True)

        except AttributeError as e:
            # Ошибка, если self.serial_port.port не существует
            if semona:               message = f"{greeting}Не смог инициализировать порт корректно"
            else:                    message = f"Порт не инициализирован корректно"
            
            if not mute: self.append_colored_text(message, self.message_error, True, True, True)

            if dbg and dbg_extra:
                error_details = f"[debug_extra] stop_serial_port - Ошибка: {type(e).__name__}: {str(e)}\n"
                error_details += "".join(traceback.format_exc())
                
                if not mute: self.append_colored_text(error_details, self.message_warning, True, True, True)

        except Exception as e:
            # Общий случай для непредвиденных ошибок
            if semona:              message = f"{greeting}Не смог закрыть порт, неизвестная ошибка: {str(e)}"
            else:                   message = f"Неизвестная ошибка при закрытии порта: {str(e)}"
            
            if not mute: self.append_colored_text(message, self.message_error, True, True, True)

            if dbg and dbg_extra:
                error_details = f"[debug_extra]stop_serial_port - Ошибка: {type(e).__name__}: {str(e)}\n"
                error_details += "".join(traceback.format_exc())
                self.append_colored_text(error_details, self.message_warning, True, True, True)

    def open_serial_port(self, port, baud, mute=False):
        ###

        settings = self.load_settings()
        dbg = settings.get("debug", False)#
        dbg_extra = settings.get("debug_extra", False)
        semona = settings.get("semona", True)
        reset = settings.get("reset_device", True)
        use_devices = settings.get("use_devices", False)
        mute_ = settings.get("mute", False)  
        if mute_: mute = True
        open_on_start = settings.get("open_startup", True)
        message = ""

        if self.on_start:   greeting = self.get_greeting()
        else:          
            greeting = ""
            self.clear_output()

        try:
            # Проверка, указан ли порт
            if not port or not port.strip():
                if semona:           message = f"{greeting}Выбери порт!"
                else:                message = f"Порт не указан"
                if not mute: self.append_colored_text(message, self.message_error, True, True, True)
                self.stop_serial_read()
                self.stop_serial_port(mute=True)
                return

            # Проверка, указана ли скорость
            if not baud or not baud.strip():
                if semona:
                    message = f"{greeting}Выбери скорость для порта {port}!"
                else:
                    message = f"Скорость не указана для порта {port}"
                if not mute: self.append_colored_text(message, self.message_error, True, True, True)
                self.stop_serial_read()
                self.stop_serial_port(mute=True)
                return
            # При автоматическом запуске настройка open_startup=False означает,
            # что порт вообще не следует открывать.
            if self.on_start and not open_on_start:
                if semona: message = f"{greeting}Монитор порта выключен!"
                else: message = "Монитор порта выключен"
                if not mute:
                    self.append_colored_text(message, self.message_warning, True, True, True)
                self.stop_serial_read()
                return

            # Проверяем, открыт ли порт с такими же параметрами
            if (self.serial_port.is_open and self.serial_port.port == port and str(self.serial_port.baudrate) == str(baud)):
                if dbg:
                    self.append_colored_text(
                        f"[debug] Порт {port} уже открыт на скорости {baud}",
                        self.message_warning, True, False, False
                    )
                self.start_serial_reader()
                self.switch_on_off_icon()
                return
            # Отладочный вывод доступных портов
            if dbg:
                try:
                    available_ports = [p.device for p in serial.tools.list_ports.comports()]
                    message = f"[debug] open_serial_port - Доступные порты: {available_ports}"
                    if not mute: self.append_colored_text(message, self.message_warning, True, False, False)
                except Exception as port_error:
                    message = f"[debug] open_serial_port - Ошибка при получении портов: {str(port_error)}"
                    if not mute: self.append_colored_text(message, self.message_warning, True, False, False)

            # Инициализация порта, если он еще не создан
            if not hasattr(self, 'serial_port') or self.serial_port is None:
                self.serial_port = serial.Serial()

            # Если выбран другой порт или другая скорость, сначала безопасно
            # останавливаем reader и закрываем старое соединение.
            if self.serial_port.is_open:
                self.stop_serial_reader()
                self.serial_port.close()

            # Попытка открытия порта
            self.serial_port.port = port
            self.serial_port.baudrate = int(baud)
            self.serial_port.timeout = 0.01
            self.serial_port.dtr = False
            self.serial_port.open()
            self._serial_session_active = True
            self._serial_disconnect_handled = False

            # Сброс устройства
            if reset:   self.reset_device()

            # Очистка буферов
            self.clear_buffer()


            # Успешное открытие порта
            if use_devices:
                if not self.on_start:
                    device_name = self.device_combo.currentText() if hasattr(self, 'device_combo') else ""
                else: 
                    last_device = settings.get("last_device", "")
                    device_name = last_device
                   
                    devices = self.load_devices()
                    if device_name not in devices:
                        self.append_colored_text(
                            f"Не нашёл устройство '{device_name}' в настройках.",
                            self.message_error,
                            True,
                            True,
                            True
                        )
                        self.stop_serial_read ()
                        self.stop_serial_port(mute=True)
                        return
                    device = devices[device_name]
                    port = device.get("port", "")
                    baud = device.get("baudrate", "")

               
                if device_name and device_name.strip():
                    if semona:     message = f"{greeting}Открыл устройство {device_name}, порт {port} на скорости {baud}"
                    else:          message = f"Устройство {device_name}, порт {port} открыт на скорости {baud}"
                else:
                    if semona:     message = f"{greeting}Открыл порт {port} на скорости {baud}"
                    else:          message = f"Порт {port} открыт на скорости {baud}"
            else:
                if semona:         message = f"{greeting}Открыл порт {port} на скорости {baud}"
                else:              message = f"Порт {port} открыт на скорости {baud}"

            if not mute: self.append_colored_text(message, self.message_info, True, True)

            self.start_serial_reader()
            self.switch_on_off_icon()


        except serial.SerialException as e:
            # Обработка специфичных ошибок порта
            error_message = str(e).lower()
            if any(phrase in error_message for phrase in ["access is denied", "permission denied", "отказано в доступе", "доступ запрещён", "недостаточно прав"]):
                if semona:     message = f"{greeting}Не смог открыть порт {port}, доступ запрещён"
                else:          message = f"Доступ к порту {port} запрещён"
            elif any(phrase in error_message for phrase in ["no such file or directory", "port not found", "does not exist", "указанное устройство не существует", "нет такого файла или каталога", "порт не найден", "не удается найти указанный файл."]):
                if semona:     message = f"{greeting}Не смог найти порт {port}"
                else:          message = f"Порт {port} не существует"
            elif any(phrase in error_message for phrase in ["device or resource busy", "устройство или ресурс занят", "порт занят"]):
                if semona:     message = f"{greeting}Не смог открыть порт {port}, он занят другим приложением"
                else:          message = f"Порт {port} занят другим приложением"
            elif any(phrase in error_message for phrase in ["cannot configure port", "oserror(22", "недопустимый параметр", "операция не поддерживается"]):
                if semona:     message = f"{greeting}Не смог открыть порт {port}, выбранная скорость {baud} не поддерживается портом"
                else:          message = f"Скорость {baud} не поддерживается портом {port}"
            elif "parameter is incorrect" in error_message:
                if semona:     message = f"{greeting}Не смог открыть порт {port}, параметры неверные"
                else:          message = f"Неверные параметры порта {port}"
            elif any(phrase in error_message for phrase in ["port is already open", "порт уже открыт"]):
                if semona:     message = f"{greeting}Не смог открыть порт {port}, он уже открыт"
                else:          message = f"Порт {port} уже открыт"
            elif any(phrase in error_message for phrase in ["device disconnected", "ioerror", "устройство не готово", "ввод-вывод ошибка"]):
                if semona:     message = f"{greeting}Не смог открыть порт {port}, устройство отключено"
                else:          message = f"Устройство на порту {port} отключено"
            elif any(phrase in error_message for phrase in ["timeout", "время ожидания операции истекло"]):
                if semona:     message = f"{greeting}Не смог открыть порт {port}, таймаут операции"
                else:          message = f"Таймаут при открытии порта {port}"
            else:
                if semona:     message = f"{greeting}Не смог открыть порт {port}, ошибка: {str(e)}"
                else:          message = f"Ошибка открытия порта {port}: {str(e)}"

            if not mute:  self.append_colored_text(message, self.message_error, True, True, True)

            if dbg and dbg_extra:
                error_details = f"[debug_extra] open_serial_port - Ошибка: {type(e).__name__}: {str(e)}\n"
                error_details += "".join(traceback.format_exc())
                self.append_colored_text(error_details, self.message_warning, True, False, False)

            self.stop_serial_read()
            self.switch_on_off_icon()


        except PermissionError as e:
            # Обработка прямых ошибок доступа
            if semona:
                message = f"{greeting}Не смог открыть порт {port}, доступ запрещён"
            else:
                message = f"Доступ к порту {port} запрещён"

            if not mute:
                self.append_colored_text(message, self.message_error, True, True, True)

            if dbg and dbg_extra:
                error_details = f"[debug_extra] open_serial_port - Ошибка: {type(e).__name__}: {str(e)}\n"
                error_details += "".join(traceback.format_exc())
                self.append_colored_text(error_details, self.message_warning, True, False, False)

            self.stop_serial_read()
            self.switch_on_off_icon()

        except ValueError as e:
            # Ошибка преобразования скорости или других параметров
            if semona:
                message = f"{greeting}Не смог открыть порт {port}, неверный формат скорости: {str(e)}"
            else:
                message = f"Неверный формат скорости для порта {port}: {str(e)}"
            if not mute: self.append_colored_text(message, self.message_error, True, True, True)

            if dbg and dbg_extra:
                error_details = f"[debug_extra] open_serial_port - Ошибка: {type(e).__name__}: {str(e)}\n"
                error_details += "".join(traceback.format_exc())
                self.append_colored_text(error_details, self.message_warning, True, True, True)

            self.stop_serial_read()
            self.stop_serial_port(mute=True)
            self.switch_on_off_icon()

        except AttributeError as e:
            # Ошибка, если serial_port не инициализирован корректно
            if semona:
                message = f"{greeting}Не смог корректно инициализировать порт"
            else:
                message = f"Порт не инициализирован корректно"
            if not mute: self.append_colored_text(message, self.message_error, True, True, True)

            if dbg and dbg_extra:
                error_details = f"[debug_extra] open_serial_port - Ошибка: {type(e).__name__}: {str(e)}\n"
                error_details += "".join(traceback.format_exc())
                self.append_colored_text(error_details, self.message_warning, True, True, True)

            self.stop_serial_read()
            self.stop_serial_port(mute=True)
            self.switch_on_off_icon()

        except Exception as e:
            # Общий случай для непредвиденных ошибок
            if semona:
                message = f"{greeting}Не смог открыть порт {port}, неизвестная ошибка: {str(e)}"
            else:
                message = f"Неизвестная ошибка при открытии порта {port}: {str(e)}"
            if not mute: self.append_colored_text(message, self.message_error, True, True, True)

            if dbg and dbg_extra:
                error_details = f"[debug_extra] open_serial_port - Ошибка: {type(e).__name__}: {str(e)}\n"
                error_details += "".join(traceback.format_exc())
                self.append_colored_text(error_details, self.message_warning, True, True, True)

            self.stop_serial_read()
            self.stop_serial_port(mute=True)
            self.switch_on_off_icon()




    def setIcon(self):
        self.setWindowIcon(QIcon(current_app_icon()))
        return


        if current_theme == "retro":
            self.setWindowIcon(QIcon(current_app_icon()))
        else :
            self.setWindowIcon(QIcon(current_app_icon()))


    def showEvent(self, event):
        hwnd = self.winId().__int__()  # Получаем handle окна
        DWMWA_USE_IMMERSIVE_DARK_MODE = 20  # Константа для тёмного режима
        
        # Загружаем текущие настройки
        settings = self.load_settings()
        current_theme = settings.get("theme", "light")  # По умолчанию "light"
        
        theme_name = self.theme_manager.get_current_theme_name()
        active_theme = self.theme_manager.get_theme(theme_name).get("theme", "light")

        print(f"active_theme {active_theme}")
        
        # Определяем, светлая или тёмная тема
        if active_theme == "light":
            value = 0  # Светлый режим для заголовка
        else:  # "dark" или "retro"
            value = 1  # Тёмный режим для заголовка
        
        # Устанавливаем стиль заголовка
        dwmapi = ctypes.WinDLL("dwmapi")
        dwmapi.DwmSetWindowAttribute(hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE, ctypes.byref(ctypes.c_int(value)), ctypes.sizeof(ctypes.c_int))
        
        super().showEvent(event)
        QTimer.singleShot(0, self.update_edge_clear_button)
    


    def load_settings(self):
        try:
            with open('settings.json', 'r', encoding='utf-8') as f:
                settings = json.load(f)
                # Синхронизируем текущую тему с ThemeManager
                self.theme_manager.set_theme(settings.get("theme", "light"))
                return settings
        except Exception as e:
            # Не обращаемся к локальной переменной settings: при ошибке чтения
            # файла она ещё не существует. Не вызываем load_settings повторно.
            if getattr(self, "debug", False):
                try:
                    self.append_colored_text(
                        f'[debug] Ошибка загрузки settings.json: {e}. Используются настройки по умолчанию.',
                        self.message_warning, True, False
                    )
                except Exception:
                    pass
            return self.default_settings()
        
               
    def on_line_ending_changed(self, text):
        # Определяем сообщение в зависимости от выбранного значения
        if text == "NL":
            ending = "на \\n"
        elif text == "CR":
            ending = "на \\r"
        elif text == "NL & CR":
            ending = "на \\r\\n"
        else:
            ending = "ничем"
        self.save_serial_settings()
        # Отправляем сообщение
        if not self.on_start:
            self.append_colored_text(
                f"Теперь отправляемая команда будет завершаться {ending}",
                self.message_info, newline=True, msg=True, err=False
            )


    def check_files_and_initialize(self):
            settings_exists = os.path.exists("settings.json") and os.path.getsize("settings.json") > 0
            themes_exists = os.path.exists("themes.json") and os.path.getsize("themes.json") > 0

            if not settings_exists or not themes_exists:
                dialog = RetroVibeDialog(self)
                dialog.exec()

            

    def create_settings_file(self, retro=False):
        settings = {
            "theme": "retro" if retro else "light",
            "port": None,
            "baudrate": "",
            "timestamp": False,
            "topmost": False,
            "use_devices": False,
            "font_size": 15,
            "semona": True,
            "max_lines": 10000,
            "line_ending": "NL",
            "count_chars": False,
            "show_line_numbers": True,
            "use_control_chars": False,
             "debug": False,
             "debug_extra": False,
             "make_Sem_fun": False,
             "character_male": False,
             "last_device": "",
             "mute": False,
             "open_startup": True,
             "reset_device": True  

        }
        with open("settings.json", "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=4)

    def create_themes_file(self, retro=False):
        themes = DEFAULT_THEME
        with open("themes.json", "w", encoding="utf-8") as f:
            json.dump(themes, f, indent=4)

    def apply_tooltip_style(self, current_theme = 'light'):

        # Получаем цвет фона и текста из темы
        #background_color = self.themes[current_theme].get("default_timestamp_color", "#FFFFFF")
        background_color = self.get_qtextedit_background_color(current_theme)
        #text_color = "#000000"
        text_color = self.message_info

        # Применяем стиль к QToolTip
        QApplication.instance().setStyleSheet(f"""
            QToolTip {{
                background-color: {background_color};
                color: {text_color};
                border: 1px solid {text_color};
                padding: 5px;
                border-radius: 5px;
            }}
        """)



   
    def append_colored_text(self, text, color, newline=True, msg=False, err=False):
        '''
          отправить текст
          - text собстно текст 
          - color цвет #000
          - newline - новая строка
          - msg - слово Семоне
          - err - сердито 
          
        '''
        settings = self.load_settings()
        font_size = settings.get("font_size", 12)
        font_size = font_size / 1.4
        semona = settings.get("semona", True)
        mute = settings.get("mute", False)  

        if msg and semona and not mute:
            text = gendered_character_text(text, bool(settings.get("character_male", False)))
            scrollbar = self.output_text.verticalScrollBar()
            was_at_bottom = scrollbar.value() == scrollbar.maximum()
            cursor = self.output_text.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)

            cloud_width = 50  # Начальная ширина облачка
            cloud_height = 30  # Начальная высота облачка

            screen = QApplication.primaryScreen()
            device_pixel_ratio = screen.devicePixelRatio() or 1.0

            if settings.get("debug", False):
                dpi = screen.logicalDotsPerInch()
                physical_dpi = screen.physicalDotsPerInch()
                self.append_colored_text(
                    f"[debug] Logical DPI: {dpi}, Physical DPI: {physical_dpi}, Device Pixel Ratio: {device_pixel_ratio}",
                    self.message_info, True, False
                )


            # Рассчитываем высоту изображения относительно строк текста
            line_height_px = self.calculate_line_height()#fm.lineSpacing()
            image_height_pixels = line_height_px * 6 #115 / device_pixel_ratio  # Высота изображения 6 строчек 
            #lines_for_image = max(1, int(image_height_pixels / line_height_px))  # Сколько строк занимает изображение
            


            # Настраиваем шрифт (фиксированный размер, независимо от масштаба)
            font = QFont()
            font.setPointSizeF(font_size)  # Фиксированный размер шрифта
            font.setFamily("Consolas")
            fm = QFontMetricsF(font)
            text_rect = fm.boundingRect(text)

            # Фиксированные отступы (независимо от масштаба)
            text_padding = 15   # Отступы для текста по горизонтали
            text_paddingH = 15  # Отступы для текста по вертикали
            extra_margin = 0   # Запас для предотвращения обрезки
            extra_text_width = 20  # Дополнительный запас для ширины текста
            height_multiplier = 1.2  # Коэффициент для увеличения высоты облачка

            # Вычисляем размеры облачка (добавляем запас для текста)
            bubble_width = text_rect.width() + text_padding * 2 + extra_text_width  # Увеличиваем ширину
            bubble_height = (text_rect.height() + text_paddingH * 2) * height_multiplier  # Увеличиваем высоту с коэффициентом

            total_width = bubble_width + 70  # Оставляем как есть
            total_height = image_height_pixels  # bubble_height * 2  # Увеличиваем общую высоту пропорционально

            # Создаем изображение с запасом
            cloud_img = QImage(QSize(int(total_width + extra_margin), int(total_height)), QImage.Format.Format_ARGB32)
            cloud_img.fill(Qt.GlobalColor.transparent)

            # Создаем QPainter
            painter = QPainter(cloud_img)
            try:
                painter.setFont(font)
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)  # Включаем сглаживание
                painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

                # Настраиваем цвета
                current_theme = settings.get("theme", "light")
                background_color = "#f0f0f0"
                if current_theme in self.themes:
                    background_color = self.get_qtextedit_background_color(current_theme)
                    background_color = QColor(background_color).darker(110)
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QColor(background_color))

                # Рисуем прямоугольник, прижимая его к низу QImage
                bubble_y = int(total_height + extra_margin - bubble_height - extra_margin / 2)  # Прижимаем к низу
                bubble_rect = QRect(
                    int(20 + extra_margin / 2),
                    bubble_y,
                    int(bubble_width),
                    int(bubble_height)
                )
                painter.drawRoundedRect(bubble_rect, 10, 10)

                # Рисуем треугольник
                triangle_size = 10 
                painter.setBrush(QColor(background_color))
                painter.drawPolygon([
                    QPoint(int(21 + extra_margin / 2), int(bubble_y + 8)),
                    QPoint(int(21 + extra_margin / 2 - triangle_size), int(bubble_y + triangle_size + 8)),
                    QPoint(int(21 + extra_margin / 2), int(bubble_y + triangle_size * 2 + 8))
                ])

                # Рисуем текст
                painter.setPen(QColor(color))
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                extra_left_padding = 10  # Увеличиваем левый отступ
                painter.drawText(
                    bubble_rect.adjusted(
                        int(text_padding + extra_left_padding),  # Увеличиваем левый отступ
                        int(text_paddingH),
                        -int(text_padding),  # Правый отступ
                        -int(text_paddingH)
                    ),
                    Qt.AlignmentFlag.AlignCenter, 
                    text
                )
            finally:
                painter.end()

                        # Определяем путь к изображению в зависимости от темы

            
            #funSem = settings.get("make_Sem_fun", False)
            #current_theme = settings.get("theme", "light")
          
            #if funSem :
            #    if err:
            #        image_path = character_image("icons/semona.png")
            #    else:
            #        image_path = character_image("icons/semona_fun.png")
            #else:
            #    if err:
            #        image_path = character_image("icons/semona.png")
            #    else:
            #        image_path = character_image("icons/semona_fun.png" if current_theme == "retro" else "icons/semona.png")
            if err:
                image_path = character_image("icons/semona.png")
            else:
                image_path = character_image("icons/semona_fun.png") 

            #print(f"высота изображения: {image_height_pixels}")
            #  
            spacer_h = max(1, int(line_height_px))
            html = f"""
                <table cellspacing="0" cellpadding="0" style="border-collapse:collapse; margin:0; padding:0; display:block; clear:both; ">
                   <tr style="height:{spacer_h}px;">
                        <td colspan="2" style="padding:0; margin:0; line-height:0; "></td>
                   </tr>
                   <tr>
                    <td style="vertical-align:middle; padding:0; margin:0;">
                      <img src="{image_path}"
                           width="{int(image_height_pixels)}"
                           height="{int(image_height_pixels)}"
                           style="display:block; margin:0; padding:0; border:0;">
                    </td>
                    <td style="vertical-align:bottom; padding:0; margin:0;">
                      <img src="data:image/png;base64,{self.qimage_to_base64(cloud_img)}"
                           width="{int((total_width + extra_margin) / device_pixel_ratio)}"
                           height="{int((total_height) / device_pixel_ratio)}"
                           style="display:block; margin:0; padding:0; border:0;">
                    </td>
                  </tr>
                  <tr style="height:{spacer_h}px;">
                    <td colspan="2" style="padding:0; margin:0; line-height:0;"></td>
                  </tr>
                </table>
            """
            
            
       
            
            
            
            
            

            cursor.insertHtml(html)


            

            if newline:
                cursor.insertHtml("\r\n")
                
                self.add_number(image_height_pixels)
                        # Обновление счетчика символов
                self.update_char_count()
                self.sync_line_numbers()




            if was_at_bottom:
                pass
            
            scrollbar.setValue(scrollbar.maximum())
        elif msg and mute:
            if newline:
                self.add_number()
                self.update_char_count()
                self.sync_line_numbers()
            return

        else:

            scrollbar = self.output_text.verticalScrollBar()
            was_at_bottom = scrollbar.value() == scrollbar.maximum()
            cursor = self.output_text.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            format = QTextCharFormat()
            format.setForeground(QColor(color))
            if newline:
                cursor.insertText(text + "\n", format)
            else:
                cursor.insertText(text, format)
            if newline:
                self.add_number()
                self.update_char_count()
                self.sync_line_numbers()
            if was_at_bottom:
                scrollbar.setValue(scrollbar.maximum())


    def calculate_line_height(self):
        """
        Вычисляет реальную высоту строки в окне вывода (QTextEdit outputText) в пикселях.
    
        Учитывает текущий шрифт, межстрочный интервал и отступы виджета.
        Корректирует результат с учётом масштабирования DPI для точности на разных дисплеях.
    
        Returns:
            int: Высота строки в пикселях, включая отступы.
    
        Raises:
            AttributeError: Если output_text не инициализирован или отсутствуют нужные атрибуты.
        """
        try:
            # Получаем текущий шрифт из output_text
            font = self.output_text.font()
            
            # Создаём объект QFontMetrics для измерения свойств шрифта
            font_metrics = QFontMetrics(font)
            
            # Получаем межстрочный интервал (включает высоту шрифта и ведущий интервал)
            line_height = font_metrics.lineSpacing()
            
            # Добавляем отступы виджета (сверху и снизу), если они есть
            #margins = self.output_text.contentsMargins()
            #total_margins = margins.top() + margins.bottom()
            #line_height += total_margins
            
            # Корректируем с учётом DPI (масштабирование дисплея)
            screen = QApplication.primaryScreen()
            device_pixel_ratio = screen.devicePixelRatio() or 1.0
            line_height = int(line_height * device_pixel_ratio)
            
            #print(f"[calculate_line_height] вычесленная высота строки: {line_height}px")
            
            return line_height
        
        except AttributeError as e:
            # Логируем ошибку, если output_text или его атрибуты не инициализированы
            settings = self.load_settings()
            if settings.get("debug", False):
                self.append_colored_text(
                    f"[debug] Ошибка при вычислении высоты строки: {str(e)}",
                    self.message_error,
                    True,
                    False
                )
            return 0  # Возвращаем 0, чтобы приложение не крашнулось

    def add_number(self, height_img=None):
        settings = self.load_settings()
        if not settings.get("show_line_numbers", True):
            return

        cursor = self.line_numbers.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)

        # Следующий номер берём из количества блоков, не перечитывая весь QTextEdit.
        next_number = max(1, self.line_numbers.document().blockCount())

        if height_img is None:
            # Обычная вставка одной строки с номером
            cursor.insertText(f"{next_number}\n")
        else:
            # Высота строки текста (защита от деления на 0)
            line_height = self.calculate_line_height() or 1
            num_lines = max(1, (height_img / line_height)+2)
            print(f"[add_number] высота строки: {line_height}px, строк: {num_lines}, высота картинки: {line_height*(num_lines-2)}px, общая высота {line_height*num_lines}px")
            #cursor.insertText(f"{next_number}\n")
            for _ in range(int(num_lines)):
                cursor.insertText("\r\n")

        self.line_numbers.setTextCursor(cursor)



    def clear_line_numbers(self):
        self.line_numbers.clear()
        # Добавляем первую строку с номером 1, если show_line_numbers включено
        settings = self.load_settings()
        if settings.get("show_line_numbers", True):
            cursor = self.line_numbers.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            #cursor.insertText("1\n")
            self.line_numbers.setTextCursor(cursor)
    
    
    def clear_output(self):
        self.output_text.clear()
        self.clear_line_numbers()
        self.buffer_mutex.lock()
        try:
            self.data_buffer.clear()
        finally:
            self.buffer_mutex.unlock()
        settings = self.load_settings()
        if settings.get("count_chars", False):
            self.char_count_label.setText("0")
            
            
    def sync_line_number_scroll(self, value=None):
        """Синхронизирует линейку с прокруткой основного текста."""
        if self._syncing_line_scroll:
            return
        source = self.output_text.verticalScrollBar()
        target = self.line_numbers.verticalScrollBar()
        self._syncing_line_scroll = True
        try:
            ratio = (source.value() / source.maximum()) if source.maximum() else 0.0
            target.setValue(round(ratio * target.maximum()))
        finally:
            self._syncing_line_scroll = False

    def sync_line_numbers(self):
        settings = self.load_settings()
        show_line_numbers = settings.get("show_line_numbers", True)
        self.line_numbers.setVisible(show_line_numbers)
        self.line_numbers.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)

        if show_line_numbers:
            # Ширина зависит только от количества цифр в последнем номере.
            line_count = max(1, self.output_text.document().blockCount() - 1)
            font_metrics = self.line_numbers.fontMetrics()
            digit_count = len(str(line_count))
            required_width = 18 + digit_count * font_metrics.horizontalAdvance('0')
            self.line_numbers.setFixedWidth(max(34, int(required_width)))

        self.sync_line_number_scroll()




    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    def get_qtextedit_background_color(self, theme_name, themes_file='themes.json'):
        try:
            # Загружаем темы из файла
            with open(themes_file, 'r', encoding='utf-8') as f:
                themes = json.load(f)

            # Проверяем, существует ли выбранная тема
            if theme_name not in themes:
                raise ValueError(f"Тема '{theme_name}' не найдена в файле {themes_file}")

            # Получаем stylesheet текущей темы
            stylesheet = themes[theme_name].get("stylesheet", "")

            # Ищем background-color для QTextEdit
            match = re.search(r"QTextEdit#outputText\s*{\s*background-color:\s*#([0-9a-fA-F]{6});", stylesheet)
            if match:
                return f"#{match.group(1)}"  # Возвращаем найденный цвет
            else:
                print("Цвет background-color для QTextEdit#outputText не найден, используется значение по умолчанию.")
                return "#f0f0f0"  # Значение по умолчанию (белый цвет)

        except Exception as e:
            print(f"Ошибка: {e}")
            return "#f0f0f0"  # Значение по умолчанию (белый цвет)


    def qimage_to_base64(self, qimage):
        """Преобразует QImage в base64 для вставки в HTML."""
        byte_array = QByteArray()
        buffer = QBuffer(byte_array)
        buffer.open(QBuffer.OpenModeFlag.WriteOnly)
        qimage.save(buffer, "PNG")
        return byte_array.toBase64().data().decode()


    @staticmethod
    def default_theme():
        themes = DEFAULT_THEME
        return themes
    
    def load_themes(self):
        """Загружает темы и синхронизирует их с ThemeManager."""
        default_control_colors = {
            "info_color": "#00FF00",
            "warning_color": "#FFFF00",
            "error_color": "#FF0000",
            "custom_color": "#00FFFF",
        }
        try:
            with open("themes.json", "r", encoding="utf-8") as f:
                loaded = json.load(f)
            if not isinstance(loaded, dict):
                raise ValueError("Некорректный формат themes.json")
        except FileNotFoundError:
            loaded = deepcopy(DEFAULT_THEME)
        except Exception as e:
            print(f"Ошибка загрузки тем из themes.json: {e}")
            loaded = deepcopy(DEFAULT_THEME)

        # Подмешиваем отсутствующие поля, не затирая пользовательские настройки.
        for theme_name, default_data in DEFAULT_THEME.items():
            loaded.setdefault(theme_name, deepcopy(default_data))
        for theme_name, theme in loaded.items():
            base = DEFAULT_THEME.get(theme_name, DEFAULT_THEME["light"])
            for key, value in base.items():
                if key == "control_chars_colors":
                    theme.setdefault(key, deepcopy(value))
                else:
                    theme.setdefault(key, deepcopy(value))
            theme.setdefault("control_chars_colors", deepcopy(default_control_colors))
            for key, value in default_control_colors.items():
                theme["control_chars_colors"].setdefault(key, value)

        self.themes = loaded
        if hasattr(self, "theme_manager"):
            self.theme_manager.themes = self.themes
            current = self.theme_manager.current_theme_name
            if current not in self.themes:
                current = "light"
                self.theme_manager.current_theme_name = current
            self.theme_manager.current_theme = self.themes[current]

        settings = self.load_settings()
        if settings.get("theme_palette_version", 0) < 2:
            # Обновляем заводские палитры, сохраняя Retro и пользовательские темы.
            for built_in in ("light", "dark", "duino", "ocean"):
                loaded[built_in] = deepcopy(DEFAULT_THEME[built_in])
            settings["theme_palette_version"] = 2
            try:
                with open("themes.json", "w", encoding="utf-8") as f:
                    json.dump(loaded, f, ensure_ascii=False, indent=4)
                with open("settings.json", "w", encoding="utf-8") as f:
                    json.dump(settings, f, ensure_ascii=False, indent=4)
            except Exception as e:
                print(f"Ошибка обновления стандартных тем: {e}")
            if hasattr(self, "theme_manager"):
                self.theme_manager.themes = self.themes
                self.theme_manager.current_theme = self.themes.get(self.theme_manager.current_theme_name, self.themes["light"])
        current_theme = settings.get("theme", "light")
        if current_theme not in self.themes:
            current_theme = "light"
        colors = self.themes[current_theme]["control_chars_colors"]
        self.message_info = QColor(colors["info_color"])
        self.message_warning = QColor(colors["warning_color"])
        self.message_error = QColor(colors["error_color"])
        self.message_custom = QColor(colors["custom_color"])

        # Создаем файл при первом запуске/восстанавливаем поврежденный.
        if not os.path.exists("themes.json"):
            with open("themes.json", "w", encoding="utf-8") as f:
                json.dump(self.themes, f, ensure_ascii=False, indent=4)

    def update_window_title(self):
        settings = self.load_settings()
        if settings.get("use_devices", False) and self.device_combo.currentText():
            title = f"{self.device_combo.currentData(Qt.ItemDataRole.UserRole)} - {NAME}"
        else:
            title = NAME
        self.setWindowTitle(title)

    def update_char_count(self):
        settings = self.load_settings()
        if settings.get("count_chars", False):
            full_text = self.output_text.toPlainText()
            if not full_text:
                count = 0
            else:
                lines = full_text.split('\n')
                count = 0
                for line in lines:
                    if line.strip():  # Пропускаем пустые строки
                        if self.timestamp_check.isChecked() and len(line) > 12 and line[2] == ':' and line[5] == ':' and line[8] == '.':
                            data = line[12:].strip()  # Убираем "HH:MM:SS.mmm "
                            count += len(data)
                        else:
                            count += len(line.strip())
            self.char_count_label.setText(f"{count}")
            self.char_count_label.setVisible(True)
        else:
            self.char_count_label.setVisible(False)





    def toggle_serial(self, start=False):
        settings = self.load_settings()
        dbg = settings.get("debug", False)
        dbg_extra = settings.get("debug_extra", False)
        semona = settings.get("semona", True)
        message = ""

        try:
            # Проверка состояния порта
            if hasattr(self, 'serial_port') and self.serial_port and self.serial_port.is_open:
                # Порт открыт, нужно закрыть
                self.stop_serial_port()
                return

            # Определяем режим
            use_devices = settings.get("use_devices", False)

            if use_devices:
                # Режим устройства
                device_name = self.device_combo.currentText()

                # Проверка, выбрано ли устройство
                if not device_name or not device_name.strip():
                    if semona:     message = f"Выбери устройство!"
                    else:          message = f"Устройство не выбрано"

                    self.append_colored_text(message, self.message_error, True, True, True)

                    self.stop_serial_read()
                    self.stop_serial_port(mute=True)
                    return

                # Загружаем настройки устройства
                devices = self.load_devices()
                if device_name not in devices:
                    if semona:     message = f"Не нашёл устройство '{device_name}' в настройках!"
                    else:          message = f"Устройство '{device_name}' не найдено"

                    self.append_colored_text(message, self.message_error, True, True, True)
                    self.stop_serial_read()
                    self.stop_serial_port(mute=True)

                    return

                device = devices[device_name]
                port = device.get("port", "")
                baudrate = device.get("baudrate", "")
                line_ending = device.get("line_ending", "NL")
                timestamp = device.get("timestamp", False)
                use_control_chars = device.get("use_control_chars", False)

                # Проверка порта
                if not port.strip():
                    if semona:  message = f"Укажи порт для '{device_name}'!"
                    else:       message = f"Порт для устройства '{device_name}' не указан"

                    self.append_colored_text(message, self.message_error, True, True, True)
                    self.stop_serial_read()
                    self.stop_serial_port(mute=True)


                    return

                # Проверка скорости
                if not baudrate.strip():
                    if semona:   message = f"Укажи скорость для '{device_name}'!"
                    else:        message = f"Скорость для устройства '{device_name}' не указана"

                    self.append_colored_text(message, self.message_error, True, True, True)

                    self.stop_serial_read()
                    self.stop_serial_port(mute=True)

                    return

                # Применяем настройки устройства
                  # может и не стоит хз
                self.port_combo.setCurrentText(port)
                self.baud_combo.setCurrentText(baudrate)
                self.line_ending_combo.setCurrentText(line_ending)

                self.timestamp_check.setChecked(timestamp)
                self.use_control_chars = use_control_chars

                # Сохраняем последнее устройство
                self.save_settings(last_device=device_name)

                # Отладочный вывод настроек устройства
                if dbg:
                    message = f"[debug] toggle_serial - Применены настройки устройства '{device_name}': порт {port}, скорость {baudrate}"
                    self.append_colored_text(message, self.message_warning, True, False, False)

            else:
                # Режим выбора порта и скорости
                port = self.port_combo.currentText()
                baudrate = self.baud_combo.currentText()

                # Проверка порта
                if not port.strip():
                    if semona:  message = f"Выбери Порт!"
                    else:       message = f"Порт не выбран"

                    self.stop_serial_read()
                    self.stop_serial_port(mute=True)

                    self.append_colored_text(message, self.message_error, True, True, True)

                    return

                # Проверка скорости
                if not baudrate.strip():
                    if semona:  message = f"Выбери скорость!"
                    else:       message = f"Скорость не выбрана"

                    self.append_colored_text(message, self.message_error, True, True, True)

                    self.stop_serial_read()
                    self.stop_serial_port(mute=True)

                    return

            # Отладочный вывод доступных портов
            if dbg:
                try:
                    available_ports = [p.device for p in serial.tools.list_ports.comports()]
                    message = f"[debug] toggle_serial - Доступные порты: {available_ports}"
                    self.append_colored_text(message, self.message_warning, True, False, False)
                except Exception as port_error:
                    message = f"[debug] toggle_serial - Ошибка при получении портов: {str(port_error)}"
                    self.append_colored_text(message, self.message_warning, True, False, False)


            # Открываем порт
            self.open_serial_port(port, baudrate)

        except AttributeError as e:
            # Ошибка, если serial_port не инициализирован
            if semona:    message = f"Не смог корректно инициализировать порт"
            else:         message = f"Порт не инициализирован корректно"
            self.append_colored_text(message, self.message_error, True, True, True)

            if dbg and dbg_extra:
                error_details = f"[debug_extra] toggle_serial - Ошибка: {type(e).__name__}: {str(e)}\n"
                error_details += "".join(traceback.format_exc())
                self.append_colored_text(error_details, self.message_warning, True, True, True)

            self.stop_serial_read()
            self.stop_serial_port(mute=True)


        except Exception as e:
            # Общий случай для непредвиденных ошибок
            if semona:
                message = f"Не смог переключить состояние порта, неизвестная ошибка: {str(e)}"
            else:
                message = f"Неизвестная ошибка при переключении порта: {str(e)}"
            self.append_colored_text(message, self.message_error, True, True, True)

            if dbg and dbg_extra:
                error_details = f"[debug_extra] toggle_serial - Ошибка: {type(e).__name__}: {str(e)}\n"
                error_details += "".join(traceback.format_exc())
                self.append_colored_text(error_details, self.message_warning, True, True, True)

            self.stop_serial_read()
            self.stop_serial_port(mute=True)

    def change_port(self, port=None):
        settings = self.load_settings()
        dbg = settings.get("debug", False)
        dbg_extra = settings.get("debug_extra", False)
        semona = settings.get("semona", True)
        open_on_start = settings.get("open_startup", True)
        message = ""
        
        if self.on_start and open_on_start == False:
            if semona:   message = f"Монитор порта выключен!"
            else:        message = f"Монитор порта выключен"
            self.append_colored_text(message, self.message_warning, True, True, True)
            return

        try:
            # Если порт не передан, берем текущий из выпадающего списка
            if port is None:
                port = self.port_combo.currentText()

            # Проверка, выбран ли порт
            if not port or not port.strip():
                if semona:    message = f"Порт не выбран. Укажи порт!"
                else:         message = f"Порт не выбран"

                self.append_colored_text(message, self.message_error, True, True, True)

                self.stop_serial_read()
                self.stop_serial_port(mute=True)

                return

            # Проверка, выбрана ли скорость
            baudrate = self.baud_combo.currentText()
            if not baudrate or not baudrate.strip():
                if semona:    message = f"Выбери Скорость!"
                else:         message = f"Скорость не указана для порта {port}"

                self.append_colored_text(message, self.message_error, True, True, True)

                self.stop_serial_read()
                self.stop_serial_port(mute=True)

                return

            # Отладочный вывод доступных портов
            if dbg:
                try:
                    available_ports = [p.device for p in serial.tools.list_ports.comports()]
                    message = f"[debug] change_port - Доступные порты: {available_ports}"
                    self.append_colored_text(message, self.message_warning, True, False, False)
                except Exception as port_error:
                    message = f"[debug] change_port - Ошибка при получении портов: {str(port_error)}"
                    self.append_colored_text(message, self.message_warning, True, False, False)

            # Если порт открыт, закрываем его
            if hasattr(self, 'serial_port') and self.serial_port and self.serial_port.is_open:
                self.stop_serial_port(mute=True)


            # Открываем новый порт
            self.open_serial_port(port, baudrate)

            # Сохраняем настройки
            self.save_serial_settings()

        except AttributeError as e:
            # Ошибка, если serial_port не инициализирован
            if semona:   message = f"Не смог корректно инициализировать порт"
            else:        message = f"Порт не инициализирован корректно"

            self.append_colored_text(message, self.message_error, True, True, True)

            if dbg and dbg_extra:
                error_details = f"[debug_extra] change_port - Ошибка: {type(e).__name__}: {str(e)}\n"
                error_details += "".join(traceback.format_exc())

                self.append_colored_text(error_details, self.message_warning, True, True, True)

            self.stop_serial_read()
            self.stop_serial_port(mute=True)


        except Exception as e:
            # Общий случай для непредвиденных ошибок
            if semona:    message = f"Не смог сменить порт, неизвестная ошибка: {str(e)}"
            else:         message = f"Неизвестная ошибка при смене порта: {str(e)}"

            self.append_colored_text(message, self.message_error, True, True, True)

            if dbg and dbg_extra:
                error_details = f"[debug_extra] change_port - Ошибка: {type(e).__name__}: {str(e)}\n"
                error_details += "".join(traceback.format_exc())
                self.append_colored_text(error_details, self.message_warning, True, True, True)

            self.stop_serial_read()
            self.stop_serial_port(mute=True)

 
    def change_baudrate(self, baudrate=None):
        settings = self.load_settings()
        dbg = settings.get("debug", False)
        dbg_extra = settings.get("debug_extra", False)
        semona = settings.get("semona", True)
        message = ""


        try:
            # Если скорость не передана, берем текущую из выпадающего списка
            if baudrate is None:
                baudrate = self.baud_combo.currentText()

            # Проверка, выбрана ли скорость
            if not baudrate or not baudrate.strip():
                if semona:   message = f"Выбери скорость!"
                else:        message = f"Скорость не выбрана"


                self.append_colored_text(message, self.message_error, True, True, True)
                self.stop_serial_read()
                self.stop_serial_port(mute=True)

                return

            # Получаем текущий выбранный порт
            port = self.port_combo.currentText()

            # Проверка, выбран ли порт
            if not port or not port.strip():
                if semona:    message = f"Выбери порт!"
                else:         message = f"Порт не выбран"

                self.append_colored_text(message, self.message_error, True, True, True)
                self.stop_serial_read()
                self.stop_serial_port(mute=True)

                return

            # Проверка, доступен ли порт
            try:
                available_ports = [p.device for p in serial.tools.list_ports.comports()]
                if port not in available_ports:
                    if semona:   message = f"Не могу использовать порт {port}, он недоступен!"
                    else:        message = f"Порт {port} недоступен"

                    self.append_colored_text(message, self.message_error, True, True, True)
                    self.stop_serial_read()
                    self.stop_serial_port(mute=True)

                    return
            except Exception as port_error:
                if dbg:
                    message = f"[debug] change_baudrate - Ошибка при получении портов: {str(port_error)}"
                    self.append_colored_text(message, self.message_warning, True, False, False)


            # Если порт открыт, закрываем его
            if hasattr(self, 'serial_port') and self.serial_port and self.serial_port.is_open:
                self.stop_serial_port(mute=True)
                # Открываем порт с новой скоростью
                self.open_serial_port(port, baudrate)
            else:
                if not self.on_start:
                    if semona:   message = f"Установил скорость {baudrate} для порта {port}"
                    else:        message = f"Для порта {port} установлена скорость {baudrate}"
                    self.append_colored_text(message, self.message_info, True, True) 

            
           
            
            # Сохраняем настройки
            self.save_serial_settings()

        except AttributeError as e:
            # Ошибка, если serial_port не инициализирован
            if semona:   message = f"Не смог корректно инициализировать порт"
            else:        message = f"Порт не инициализирован корректно"
            self.append_colored_text(message, self.message_error, True, True, True)

            if dbg and dbg_extra:
                error_details = f"[debug_extra] change_baudrate - Ошибка: {type(e).__name__}: {str(e)}\n"
                error_details += "".join(traceback.format_exc())
                self.append_colored_text(error_details, self.message_warning, True, True, True)

            self.stop_serial_read()
            self.stop_serial_port(mute=True)


        except Exception as e:
            # Общий случай для непредвиденных ошибок
            if semona:   message = f"Не смог сменить скорость, неизвестная ошибка: {str(e)}"
            else:        message = f"Неизвестная ошибка при смене скорости: {str(e)}"
            self.append_colored_text(message, self.message_error, True, True, True)

            if dbg and dbg_extra:
                error_details = f"[debug_extra] change_baudrate - Ошибка: {type(e).__name__}: {str(e)}\n"
                error_details += "".join(traceback.format_exc())
                self.append_colored_text(error_details, self.message_warning, True, True, True)

            self.stop_serial_read()
            self.stop_serial_port(mute=True)

    def change_device(self, device_name=None):
        self.clear_output()

        settings = self.load_settings()
        dbg = settings.get("debug", False)
        dbg_extra = settings.get("debug_extra", False)
        semona = settings.get("semona", True)
        message = ""

        
        try:
            # Если устройство не передано, берем текущее из выпадающего списка
            if device_name is None:
                device_name = self.device_combo.currentText()

            # Проверка, выбрано ли устройство
            if not device_name or not device_name.strip():
                if semona:    message = f"Не могу применить устройство, так как оно не выбрано!"
                else:         message = f"Устройство не выбрано"

                self.append_colored_text(message, self.message_error, True, True, True)
                self.stop_serial_read()
                self.stop_serial_port(mute=True)

                return

            # Загружаем настройки устройства
            devices = self.load_devices()
            if device_name not in devices:
                if semona:       message = f"Не нашёл устройство '{device_name}' в настройках!"
                else:            message = f"Устройство '{device_name}' не найдено"
               
                self.append_colored_text(message, self.message_error, True, True, True)
                self.stop_serial_read()
                self.stop_serial_port(mute=True)
              
                return

            device = devices[device_name]
            port = device.get("port", "")
            baudrate = device.get("baudrate", "")
            line_ending = device.get("line_ending", "NL")
            timestamp = device.get("timestamp", False)
            use_control_chars = device.get("use_control_chars", False)

            # Проверка порта
            if not port.strip():
                if semona:       message = f"Для устройства '{device_name}' не указан порт!"
                else:            message = f"Порт для устройства '{device_name}' не указан"
               
                self.append_colored_text(message, self.message_error, True, True, True)
                self.stop_serial_read()
                self.stop_serial_port(mute=True)
               
                return

            # Проверка скорости
            if not baudrate.strip():
                if semona:       message = f"Для устройства '{device_name}' не указана скорость!"
                else:            message = f"Скорость для устройства '{device_name}' не указана"
                self.append_colored_text(message, self.message_error, True, True, True)
                self.stop_serial_read()
                self.stop_serial_port(mute=True)
                return

            # Отладочный вывод настроек устройства
            if dbg:
                message = f"[debug] change_device - Применены настройки устройства '{device_name}': порт {port}, скорость {baudrate}"
                self.append_colored_text(message, self.message_warning, True, False, False)

            # Применяем настройки устройства
            self.device_combo.setCurrentText(device_name)
            #self.port_combo.setCurrentText(port)
            #self.baud_combo.setCurrentText(baudrate)
            self.line_ending_combo.setCurrentText(line_ending)
            self.timestamp_check.setChecked(timestamp)
            self.use_control_chars = use_control_chars

            # Сохраняем последнее устройство
            self.save_settings(last_device=device_name)

            # Если порт открыт, закрываем его
            if hasattr(self, 'serial_port') and self.serial_port and self.serial_port.is_open:
                self.stop_serial_port(mute=True)

            # Отладочный вывод доступных портов
            if dbg:
                try:
                    available_ports = [p.device for p in serial.tools.list_ports.comports()]
                    message = f"[debug] change_device - Доступные порты: {available_ports}"
                    self.append_colored_text(message, self.message_warning, True, False, False)
                except Exception as port_error:
                    message = f"[debug] change_device - Ошибка при получении портов: {str(port_error)}"
                    self.append_colored_text(message, self.message_warning, True, False, False)


            # Открываем порт
            self.open_serial_port(port, baudrate)

        except AttributeError as e:
            # Ошибка, если serial_port или другие атрибуты не инициализированы
            if semona:
                message = f"Не смог корректно инициализировать порт"
            else:
                message = f"Порт не инициализирован корректно"
            self.append_colored_text(message, self.message_error, True, True, True)

            if dbg and dbg_extra:
                error_details = f"[debug_extra] change_device - Ошибка: {type(e).__name__}: {str(e)}\n"
                error_details += "".join(traceback.format_exc())
                self.append_colored_text(error_details, self.message_warning, True, True, True)

            self.stop_serial_read()
            self.stop_serial_port(mute=True)

        except Exception as e:
            # Общий случай для непредвиденных ошибок
            if semona:
                message = f"Не смог сменить устройство, неизвестная ошибка: {str(e)}"
            else:
                message = f"Неизвестная ошибка при смене устройства: {str(e)}"
            self.append_colored_text(message, self.message_error, True, True, True)

            if dbg and dbg_extra:
                error_details = f"[debug_extra] change_device - Ошибка: {type(e).__name__}: {str(e)}\n"
                error_details += "".join(traceback.format_exc())
                self.append_colored_text(error_details, self.message_warning, True, True, True)

            self.stop_serial_read()
            self.stop_serial_port(mute=True)


    def change_device(self, device_name):
        settings = self.load_settings()
        if settings.get("debug", False):
            self.append_colored_text(
                f'[debug] Вызов change_device: {device_name}',
                self.message_warning, True, False
            )

        if not device_name:
            if settings.get("debug", False):
                self.append_colored_text(
                    '[debug] Имя устройства пустое, пропуск',
                    self.message_warning, True, False
                )
            return

        devices = self.load_devices()
        if device_name not in devices:
            self.append_colored_text(
                f"Устройство '{device_name}' не найдено",
                self.message_error, True, True, True
            )
            return

        device = devices[device_name]
        port = device.get("port", "")
        baudrate = device.get("baudrate", "")
        line_ending = device.get("line_ending", "NL")
        timestamp = device.get("timestamp", False)
        use_control_chars = device.get("use_control_chars", False)

        # Проверяем, изменились ли параметры
        current_port = self.serial_port.port if self.serial_port and hasattr(self.serial_port, 'port') else None
        current_baudrate = str(self.serial_port.baudrate) if self.serial_port and hasattr(self.serial_port, 'baudrate') else None

        if current_port == port and current_baudrate == baudrate and self.serial_port.is_open:
            if settings.get("debug", False):
                self.append_colored_text(
                    f'[debug] Порт {port} уже открыт с baudrate {baudrate}, пропуск',
                    self.message_warning, True, False
                )
            return

        # Применяем настройки
        self.port_combo.setCurrentText(port)
        self.baud_combo.setCurrentText(baudrate)
        self.line_ending_combo.setCurrentText(line_ending)
        self.timestamp_check.setChecked(timestamp)
        self.use_control_chars = use_control_chars

        # Сохраняем last_device
        settings["last_device"] = device_name
        self.save_settings(**settings)

        # Закрываем текущий порт, если он открыт
        if self.serial_port.is_open:
            self.stop_serial_port(mute=True)

        # Открываем порт
        if port and baudrate:
            self.open_serial_port(port, baudrate)
        else:
            self.append_colored_text(
                f"Не указан порт или скорость для устройства '{device_name}'",
                self.message_error, True, True, True
            )


    def update_timestamp_icon(self, checked):
        icon_path = "icons/stamp_on.png" if checked else "icons/stamp_off.png"
        self.timestamp_check.setIcon(QIcon(resource_path(icon_path)))




    def update_ports(self):
        # Получаем текущие настройки
        settings = self.load_settings()
        use_devices = settings.get("use_devices", False)
        saved_port = settings.get("port", None)

        # Очищаем текущий список портов
        self.port_combo.blockSignals(True)
        self.port_combo.clear()

        # Получаем список доступных портов
        ports = [port.device for port in serial.tools.list_ports.comports()]

        # Добавляем пустую строку как первый элемент
        #self.port_combo.addItem("")
        self.port_combo.addItems(ports)

        # Устанавливаем текущий порт
        if use_devices:
            # В режиме устройств порт берется из настроек устройства
            device_name = self.device_combo.currentText()
            if device_name:
                devices = self.load_devices()
                if device_name in devices:
                    device_port = devices[device_name].get("port", "")
                    if device_port in ports:
                        self.port_combo.setCurrentText(device_port)
                    else:
                        self.port_combo.setCurrentText("")
        else:
            # В обычном режиме проверяем настройки порта
            if saved_port is None:
                # Если порт в настройках null, выбираем пустую строку
                self.port_combo.setCurrentText("")
            elif saved_port in ports:
                # Если порт из настроек существует, выбираем его
                self.port_combo.setCurrentText(saved_port)
            else:
                # Если порт из настроек недоступен, выбираем пустую строку
                self.port_combo.setCurrentText("")

        self.port_combo.blockSignals(False)





    def update_devices(self):
        # Очищаем текущий список устройств в выпадающем списке
        self.device_combo.clear()

        # Загружаем список устройств из файла
        devices = self.load_devices()

        # Создаем модель для отображения устройств
        model = QStandardItemModel()
        settings = self.load_settings()
        last_device = settings.get("last_device", "")
        font_size = settings.get("font_size", 15)
        # Проходим по каждому устройству и его настройкам
        for name, sett_device in devices.items():
            # Создаем элемент для имени устройства
            

            item = QStandardItem()
            item.setText(name)  # Устанавливаем текст элемента как имя устройства
            item.setData(name, Qt.ItemDataRole.UserRole)  # Сохраняем имя устройства как пользовательские данные
            font = item.font()
            
            font.setPointSize(font_size)  # Устанавливаем размер шрифта
            item.setFont(font)

            # Создаем дополнительный элемент для отображения деталей устройства (порт и скорость)
            detail_text = f"{sett_device['port']} {sett_device['baudrate']}"  # Формируем текст с портом и скоростью
            detail_item = QStandardItem()
            detail_item.setText(detail_text)  # Устанавливаем текст элемента
            detail_font = detail_item.font()
            detail_font.setPointSize(font_size-5)  # Устанавливаем меньший размер шрифта для деталей
            detail_item.setFont(detail_font)
            detail_item.setForeground(QColor("gray"))  # Устанавливаем серый цвет текста
            detail_item.setFlags(Qt.ItemFlag.NoItemFlags)  # Отключаем возможность выбора элемента

            # Добавляем элементы в модель
            model.appendRow(item)  # Добавляем основной элемент (имя устройства)
            model.appendRow(detail_item)  # Добавляем элемент с деталями устройства
        


            # Добавляем сепаратор
        separator_item = QStandardItem()
        separator_item.setText("──────────")  # Имитация горизонтальной линии
        separator_font = separator_item.font()
        separator_font.setPointSize(10)
        separator_item.setFont(separator_font)
        separator_item.setForeground(QColor("gray"))
        separator_item.setFlags(Qt.ItemFlag.NoItemFlags)  # Не выбираемый
        model.appendRow(separator_item)


        # Добавляем специальный пункт для открытия окна устройств
        add_device_item = QStandardItem()
        add_device_item.setText("Добавить устройство...")
        add_device_item.setData("ADD_DEVICE", Qt.ItemDataRole.UserRole)  # Уникальный идентификатор
        font = add_device_item.font()
        font.setPointSize(font_size-2)
        font.setItalic(True)  # Курсив для отличия

        add_device_item.setFont(font)
        #add_device_item.setForeground(QColor("gray"))  # Синий цвет для выделения
        model.appendRow(add_device_item)

        # Устанавливаем модель в выпадающий список устройств
        self.device_combo.setModel(model)

        # Отключаем сигнал изменения текста, чтобы избежать дублирования
        try:
            self.device_combo.currentTextChanged.disconnect()
        except TypeError:
            pass

        # Подключаем сигнал изменения текста с проверкой выбранного пункта
        def on_device_changed(text):
            selected_item = self.device_combo.model().item(self.device_combo.currentIndex())
            if selected_item and selected_item.data(Qt.ItemDataRole.UserRole) == "ADD_DEVICE":
                self.show_devices()
            else:
                self.change_device(text)

        self.device_combo.currentTextChanged.connect(on_device_changed)


    def update_devices(self, from_combo_change=False):
        # Очищаем текущий список устройств в выпадающем списке
        self.device_combo.clear()

        # Загружаем список устройств из файла
        devices = self.load_devices()

        # Создаем модель для отображения устройств
        model = QStandardItemModel()
        settings = self.load_settings()
        last_device = settings.get("last_device", "")
        font_size = settings.get("font_size", 15)

        # Проходим по каждому устройству и его настройкам
        for name, sett_device in devices.items():
            # Создаем элемент для имени устройства
            item = QStandardItem()
            item.setText(name)
            item.setData(name, Qt.ItemDataRole.UserRole)
            font = item.font()
            font.setPointSize(font_size)
            item.setFont(font)

            # Создаем дополнительный элемент для отображения деталей устройства
            detail_text = f"{sett_device['port']} {sett_device['baudrate']}"
            detail_item = QStandardItem()
            detail_item.setText(detail_text)
            detail_font = detail_item.font()
            detail_font.setPointSize(font_size - 5)
            detail_item.setFont(detail_font)
            detail_item.setForeground(QColor("gray"))
            detail_item.setFlags(Qt.ItemFlag.NoItemFlags)

            # Добавляем элементы в модель
            model.appendRow(item)
            model.appendRow(detail_item)

        # Добавляем сепаратор
        separator_item = QStandardItem()
        separator_item.setText("──────────")
        separator_font = separator_item.font()
        separator_font.setPointSize(10)
        separator_item.setFont(separator_font)
        separator_item.setForeground(QColor("gray"))
        separator_item.setFlags(Qt.ItemFlag.NoItemFlags)
        model.appendRow(separator_item)

        # Добавляем специальный пункт для открытия окна устройств
        add_device_item = QStandardItem()
        add_device_item.setText("Добавить устройство...")
        add_device_item.setData("ADD_DEVICE", Qt.ItemDataRole.UserRole)
        font = add_device_item.font()
        font.setPointSize(font_size - 2)
        font.setItalic(True)
        add_device_item.setFont(font)
        model.appendRow(add_device_item)

        # Устанавливаем модель
        self.device_combo.setModel(model)

        # Выбираем last_device, если не вызвано изменением QComboBox
        if not from_combo_change and last_device in devices:
            for i in range(model.rowCount()):
                item = model.item(i)
                if item and item.data(Qt.ItemDataRole.UserRole) == last_device:
                    self.device_combo.setCurrentIndex(i)
                    if settings.get("debug", False):
                        self.append_colored_text(
                            f'[debug] Выбран last_device: {last_device}',
                            self.message_warning, True, False
                        )
                    break

        # Отключаем старый сигнал
        try:
            self.device_combo.currentTextChanged.disconnect()
        except TypeError:
            pass

        # Подключаем новый сигнал
        def on_device_changed(text):
            selected_item = self.device_combo.model().item(self.device_combo.currentIndex())
            if selected_item and selected_item.data(Qt.ItemDataRole.UserRole) == "ADD_DEVICE":
                self.show_devices()
            else:
                self.change_device(text)

        self.device_combo.currentTextChanged.connect(on_device_changed)
        self.device_combo.blockSignals(False)  # Разблокируем сигналы







    def handle_serial_data(self, data):
        """Принимает пакет из worker-потока. Выполняется в GUI-потоке."""
        if isinstance(data, tuple) and len(data) == 2:
            line, received_at = data
        else:  # совместимость со старыми вызовами/диагностическими сообщениями
            line, received_at = str(data), datetime.now().strftime("%H:%M:%S.%f")[:-3]
        if line is None:
            return
        self.buffer_mutex.lock()
        try:
            self.data_buffer.append((str(line), str(received_at)))
        finally:
            self.buffer_mutex.unlock()

    def set_output_background(self, port_open):
        """Возвращает окну вывода цвет текущей темы в зависимости от состояния порта."""
        settings = self.load_settings()
        theme_name = settings.get("theme", self.theme_manager.get_current_theme_name())
        if theme_name not in self.theme_manager.themes:
            theme_name = "light"
        theme = self.theme_manager.get_theme(theme_name)
        if port_open:
            stylesheet = theme.get("stylesheet", "")
            match = re.search(
                r"QTextEdit#outputText\s*\{[^}]*background-color\s*:\s*(#[0-9a-fA-F]{6}|#[0-9a-fA-F]{3}|[A-Za-z]+)",
                stylesheet,
                re.S,
            )
            color = match.group(1) if match else "#ffffff"
        else:
            color = theme.get("off_color", "#c8d2dc")
        self.output_text.setStyleSheet(f"QTextEdit#outputText {{ background-color: {color}; }}")

    def start_serial_reader(self):
        # Перезапуск reader не должен сбрасывать TX-буфер: там могут находиться
        # ещё не переданные данные. Входной буфер очищается только при открытии порта.
        self.stop_serial_reader()
        if not self.serial_port or not self.serial_port.is_open:
            settings = self.load_settings()
            if settings.get("debug", False):
                self.append_colored_text(
                    "[debug] Не удалось запустить поток чтения: порт не открыт",
                    self.message_error
                )
            self.set_output_background(False)
            return
        try:
            self.buffer_mutex.lock()
            try:
                self.data_buffer.clear()
            finally:
                self.buffer_mutex.unlock()
            self.reader = SerialReader(
                self.serial_port,
                debug=bool(self.load_settings().get("debug", False))
            )
            self.reader.data_received.connect(self.handle_serial_data)
            self.reader.connection_lost.connect(self.handle_serial_connection_lost)
            self.reader.start()
            self.set_output_background(True)
        except Exception as e:
            self.reader = None
            self.set_output_background(False)
            settings = self.load_settings()
            if settings.get("debug", False):
                self.append_colored_text(
                    f"[debug] Ошибка запуска потока чтения: {str(e)}",
                    self.message_error, True
                )

    def handle_serial_connection_lost(self, error_text=""):
        """Обрабатывает неожиданное отключение адаптера в GUI-потоке."""
        if not getattr(self, "_serial_session_active", False):
            return
        if getattr(self, "_serial_disconnect_handled", False):
            return

        self._serial_disconnect_handled = True
        self._serial_session_active = False
        try:
            port_name = self.serial_port.port or "COM-порт"
        except Exception:
            port_name = "COM-порт"

        # Сначала завершаем reader, затем закрываем объект pyserial.
        self.stop_serial_reader()
        try:
            if self.serial_port and self.serial_port.is_open:
                self.serial_port.close()
        except Exception:
            pass

        self.set_output_background(False)
        self.switch_on_off_icon()

        settings = self.load_settings()
        if settings.get("semona", True):
            self.append_colored_text(
                f"Ой, кажется, порт {port_name} закрылся. Возможно, адаптер отключили.",
                self.message_warning, True, True, True
            )
        else:
            self.append_colored_text(
                f"Соединение с портом {port_name} потеряно. Порт закрыт.",
                self.message_warning, True, True, False
            )

        if settings.get("debug", False) and error_text:
            self.append_colored_text(
                f"[debug] Потеря соединения с {port_name}: {error_text}",
                self.message_warning, True, False, False
            )

    def stop_serial_reader(self):
        """Останавливает только QThread, не закрывая COM-порт."""
        reader = getattr(self, "reader", None)
        if reader is not None:
            reader.stop()
            if reader is not QThread.currentThread():
                # Дожидаемся фактического завершения, прежде чем закрывать порт.
                reader.wait()
            self.reader = None

    def stop_serial_read(self):
        """Совместимый метод полной остановки чтения и закрытия COM-порта."""
        self._serial_session_active = False
        self.stop_serial_reader()
        if getattr(self, "serial_port", None) and self.serial_port.is_open:
            try:
                self.serial_port.close()
            except Exception:
                pass
            self.switch_on_off_icon()
        self.set_output_background(False)

    def display_data(self, data):
        # Оставлено для совместимости: основной reader теперь использует очередь.
        self.handle_serial_data(data)

    def flush_buffer_to_display(self):
        """Пакетно вставляет накопленные строки, сохраняя время каждой строки."""
        self.buffer_mutex.lock()
        try:
            data_to_process = self.data_buffer[:]
            self.data_buffer.clear()
        finally:
            self.buffer_mutex.unlock()
        if not data_to_process:
            return

        settings = self.load_settings()
        current_theme = self.theme_manager.get_current_theme_name()
        if current_theme not in self.theme_manager.themes:
            current_theme = "light"
        theme = self.theme_manager.get_theme(current_theme)
        timestamp_enabled = self.timestamp_check.isChecked()
        if settings.get("use_devices", False) and hasattr(self, "use_control_chars"):
            use_control_chars = bool(self.use_control_chars)
        else:
            use_control_chars = bool(settings.get("use_control_chars", False))
        control_colors = theme.get("control_chars_colors", {})
        default_color = self.theme_manager.get_qcolor("default_text_color", current_theme).name()
        timestamp_color = self.theme_manager.get_qcolor("default_timestamp_color", current_theme).name()

        scrollbar = self.output_text.verticalScrollBar()
        was_at_bottom = scrollbar.value() >= scrollbar.maximum() - 1
        cursor = self.output_text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.output_text.setUpdatesEnabled(False)
        line_number_count = 0
        try:
            for line, received_at in data_to_process:
                if line == "":
                    continue
                color = default_color
                display_text = line
                if use_control_chars and display_text and display_text[0] in self.control_chars:
                    marker = display_text[0]
                    color_key = {
                        "\x01": "info_color",
                        "\x02": "warning_color",
                        "\x03": "error_color",
                        "\x04": "custom_color",
                        "\x00": None,
                    }.get(marker)
                    if color_key:
                        color = control_colors.get(color_key, color)
                    display_text = display_text[1:]
                if timestamp_enabled:
                    fmt_time = QTextCharFormat()
                    fmt_time.setForeground(QColor(timestamp_color))
                    cursor.insertText(f"{received_at} ", fmt_time)
                fmt = QTextCharFormat()
                fmt.setForeground(QColor(color))
                cursor.insertText(display_text + "\n", fmt)
                line_number_count += 1

            # Номера строк также добавляем одной вставкой на весь пакет.
            if line_number_count and settings.get("show_line_numbers", True):
                number_cursor = self.line_numbers.textCursor()
                number_cursor.movePosition(QTextCursor.MoveOperation.End)
                first_number = max(1, self.line_numbers.document().blockCount())
                number_cursor.insertText("".join(
                    f"{number}\n" for number in range(first_number, first_number + line_number_count)
                ))
                self.line_numbers.setTextCursor(number_cursor)

            # Ограничиваем объём вывода после вставки всего пакета.
            max_lines = max(1, int(settings.get("max_lines", 10000)))
            document = self.output_text.document()
            if document.blockCount() > max_lines:
                remove_count = document.blockCount() - max_lines
                trim_cursor = QTextCursor(document)
                trim_cursor.movePosition(QTextCursor.MoveOperation.Start)
                trim_cursor.movePosition(
                    QTextCursor.MoveOperation.NextBlock,
                    QTextCursor.MoveMode.KeepAnchor,
                    remove_count
                )
                trim_cursor.removeSelectedText()
                # Линейка пересобирается только при реальном обрезании.
                self.line_numbers.clear()
                if settings.get("show_line_numbers", True):
                    number_cursor = self.line_numbers.textCursor()
                    number_cursor.movePosition(QTextCursor.MoveOperation.End)
                    number_cursor.insertText("".join(
                        f"{number}\n" for number in range(1, document.blockCount())
                    ))
        finally:
            self.output_text.setUpdatesEnabled(True)

        if was_at_bottom:
            scrollbar.setValue(scrollbar.maximum())
        self.update_char_count()
        self.sync_line_numbers()

    def makeSemFun(self, funSem):
        try:
            # Загружаем текущие настройки из файла
            with open("settings.json", "r", encoding="utf-8") as file:
                settings = json.load(file)
    
            # Обновляем значение ключа "make_Sem_fun"
            settings["make_Sem_fun"] = bool(funSem)  # Преобразуем значение в логическое
            
    
            # Сохраняем обновленные настройки обратно в файл
            with open("settings.json", "w", encoding="utf-8") as file:
                json.dump(settings, file, indent=4, ensure_ascii=False)
    
            #print(f"Настройка 'make_Sem_fun' успешно обновлена: {funSem}")
        except Exception as e:
            print(f"Ошибка при обновлении настройки 'make_Sem_fun': {e}")
            pass

    def setCharacterMode(self, male):
        """Переключает образ, название программы и иконку."""
        global NAME
        male = bool(male)
        try:
            settings = self.load_settings()
            settings["character_male"] = male
            with open("settings.json", "w", encoding="utf-8") as file:
                json.dump(settings, file, indent=4, ensure_ascii=False)
            NAME = "SEMÖN" if male else "SEMONA"
            self.setWindowIcon(QIcon(current_app_icon()))
            self.update_window_title()
            if getattr(self, "splash", None) is not None:
                try:
                    self.splash.setPixmap(QPixmap(current_app_logo()))
                except Exception:
                    pass
        except Exception as e:
            try:
                debug_enabled = bool(self.load_settings().get("debug", False))
            except Exception:
                debug_enabled = False
            if debug_enabled:
                self.append_colored_text(f"[debug] Не удалось сохранить режим персонажа: {e}", self.message_warning, True, False, False)




    def send_command(self):
        if not hasattr(self, "empty_message_count"):
            self.empty_message_count = 0  # Счетчик пустых сообщений
        if not hasattr(self, "countdown_value"):
            self.countdown_value = 5  # Значение для обратного отсчета
        settings = self.load_settings()

        if self.serial_port.is_open:
            command = self.input_field.text()
            
            current_theme = settings.get("theme", "light")
            timestamp_color = self.themes[current_theme]["default_timestamp_color"]
            sent_color = self.themes[current_theme]["default_sent_color"]

            # Пасхалка: сначала Семона обижается, затем дед соглашается вернуться.
            if not command.strip():
                self.empty_message_count += 1
                settings = self.load_settings()
                if settings.get("semona", False):
                    male = bool(settings.get("character_male", False))
                    dbg = settings.get("debug", False)
                    if self.empty_message_count > 5:
                        if self.countdown_value > 0:
                            if self.countdown_value == 5:
                                self.append_colored_text("Ну и зачем отправлять пустые сообщения?", self.message_custom, True, True, not male)
                            if self.countdown_value == 1:
                                self.append_colored_text("Стоооой!!!111одионодин", self.message_custom, True, True, not male)
                            command = str(self.countdown_value)
                            self.countdown_value -= 1
                        else:
                            if not male:
                                self.append_colored_text("Всё, я обиделась...", self.message_custom, True, True, True)
                                self.makeSemFun(False)
                                self.setCharacterMode(True)
                                if dbg:
                                    self.append_colored_text("[debug] Вы обидели Семону", self.message_warning, True, False, False)
                            else:
                                # Сначала полностью возвращаем образ Семоны,
                                # чтобы даже финальная реплика уже отображалась от её имени.
                                self.makeSemFun(True)
                                self.setCharacterMode(False)
                                self.append_colored_text("Ладно, уговорили, я возвращаюсь!", self.message_custom, True, True, True)
                                if dbg:
                                    self.append_colored_text("[debug] Семона согласилась вернуться", self.message_warning, True, False, False)
                            self.empty_message_count = 0
                            self.countdown_value = 5
                    else:
                        command = ">"
                command = ">"
            else:
                self.empty_message_count = 0
                self.countdown_value = 5

            # Определяем окончание строки
            if settings.get("use_devices", False) and self.device_combo.currentData(Qt.ItemDataRole.UserRole):
                device_name = self.device_combo.currentData(Qt.ItemDataRole.UserRole)
                line_ending = self.load_devices()[device_name].get("line_ending", "NL")
            else:
                line_ending = self.line_ending_combo.currentText()

            # Добавляем окончание строки
            if line_ending == "NL":
                command += "\n"
            elif line_ending == "CR":
                command += "\r"
            elif line_ending == "NL & CR":
                command += "\r\n"

            try:
                payload = command.encode("utf-8")
                written = self.serial_port.write(payload)
                if written != len(payload):
                    raise serial.SerialTimeoutException(
                        f"Передано {written} из {len(payload)} байт"
                    )
            except (serial.SerialException, OSError) as e:
                self.append_colored_text(
                    f"Не удалось отправить данные: {e}", self.message_error, True, True, True
                )
                self.stop_serial_read()
                return

            # Убираем только добавленный нами терминатор, не трогая пробелы
            # и табуляцию, которые пользователь действительно отправил.
            display_command = command
            if line_ending == "NL":
                display_command = display_command[:-1]
            elif line_ending == "CR":
                display_command = display_command[:-1]
            elif line_ending == "NL & CR":
                display_command = display_command[:-2]
            if self.timestamp_check.isChecked():
                timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                self.append_colored_text(f"{timestamp} ", timestamp_color, newline=False)
                self.append_colored_text(display_command, sent_color)
            else:
                self.append_colored_text(display_command, sent_color)

            self.input_field.clear()

        else: 
            semona = settings.get("semona", True)
            if semona:  message = f"Открой порт!"
            else:       message = f"Порт не открыт"
            
            self.append_colored_text(message, self.message_error, True, True, True)  

    #def clear_output(self):
    #    self.output_text.clear()
    #    self.line_numbers.clear()
    #    self.char_count_label.setText("0")




    def switch_on_off_icon(self):
        if self.serial_port.is_open:
            self.stop_button.setIcon(QIcon(resource_path("icons/on.png")))
        else:
            self.stop_button.setIcon(QIcon(resource_path("icons/off.png")))








    def open_theme_editor(self):
        """Открывает единственный экземпляр немодального редактора тем."""
        editor = getattr(self, "_theme_editor_dialog", None)
        if editor is not None:
            try:
                if editor.isVisible():
                    editor.raise_()
                    editor.activateWindow()
                    return
            except RuntimeError:
                self._theme_editor_dialog = None

        self._theme_editor_dialog = ThemesEditorDialog(self)
        self._theme_editor_dialog.setWindowModality(Qt.WindowModality.NonModal)
        self._theme_editor_dialog.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        self._theme_editor_dialog.destroyed.connect(lambda *_: setattr(self, "_theme_editor_dialog", None))
        self._theme_editor_dialog.show()
        self._theme_editor_dialog.raise_()
        self._theme_editor_dialog.activateWindow()

    def show_settings(self):
        # Редактор тем работает немодально. Не открываем поверх него второе
        # окно настроек: пользователь продолжает работать с главным окном.
        editor = getattr(self, "_theme_editor_dialog", None)
        if editor is not None and editor.isVisible():
            editor.raise_()
            editor.activateWindow()
            return
        dialog = SettingsDialog(self)
        if dialog.exec():
            theme = dialog.get_theme()
            use_devices = dialog.get_use_devices()
            max_lines = dialog.get_max_lines()
            count_chars = dialog.get_count_chars()
            font_size = dialog.get_font_size()
            show_line_numbers = dialog.get_show_line_numbers()
            mute =  dialog.get_mute()
            open_startup = dialog.get_open_startup()
            settings = {
                "theme": theme,
                "use_devices": use_devices,
                "max_lines": max_lines,
                "count_chars": count_chars,
                "font_size": font_size,
                "mute": mute,
                "open_startup": open_startup,
                "show_line_numbers": show_line_numbers
            }
            if not use_devices:
                settings["use_control_chars"] = dialog.control_chars_check.isChecked()
            self.save_settings(**settings)
            self.apply_theme()
            self.device_combo.setVisible(use_devices)
            self.port_combo.setVisible(not use_devices)
            self.baud_combo.setVisible(not use_devices)
            self.line_ending_combo.setVisible(not use_devices)
            if use_devices:
                self.update_devices()
            self.line_numbers.setVisible(show_line_numbers)
            self.sync_line_numbers()

            # Если режим устройств активирован, проверяем наличие устройств.
            # Если devices.json отсутствует, пуст или не содержит ни одного устройства,
            # открываем окно для добавления нового устройства.
            if use_devices:
                devices = self.load_devices()
                if not devices or len(devices) == 0:
                    self.show_devices()

    def show_devices(self):
        dialog = DevicesDialog(self)

        dialog.exec()
        self.update_devices()

    def show_about(self):
        dialog = AboutDialog(self)
        dialog.exec()

    def toggle_on_top(self):
        if self.on_top.isChecked():
            icon_path = "icons/top_on.png"
            self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        else:
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowStaysOnTopHint)
            icon_path = "icons/top_off.png"
        self.on_top.setIcon(QIcon(resource_path(icon_path)))
        self.show()

    def show_context_menu(self, pos):
        menu = QMenu(self)
        if self.update_available:
            update_action = menu.addAction(QIcon(resource_path("icons/update.png")), f"Доступна новая версия ({self.latest_version})")
            update_action.triggered.connect(self.open_latest_release_page)
            menu.addSeparator()


        if self.output_text.textCursor().hasSelection():
            copy_action = QAction("Скопировать", self)
            copy_action.triggered.connect(self.output_text.copy)
            menu.addAction(copy_action)

        select_all_action = QAction("Выделить все", self)
        select_all_action.triggered.connect(self.output_text.selectAll)
        menu.addAction(select_all_action)

        menu.addSeparator()

        clear_action = QAction("Очистить", self)
        clear_action.triggered.connect(self.clear_output)
        menu.addAction(clear_action)

        timestamp_action = QAction("Отметки времени", self)
        timestamp_action.setCheckable(True)
        timestamp_action.setChecked(self.timestamp_check.isChecked())
        timestamp_action.triggered.connect(lambda: self.timestamp_check.setChecked(not self.timestamp_check.isChecked()))
        menu.addAction(timestamp_action)

        menu.addSeparator()

        on_top_action = QAction("Поверх всех окон", self)
        on_top_action.setCheckable(True)
        on_top_action.setChecked(self.on_top.isChecked())
        on_top_action.triggered.connect(lambda: self.on_top.setChecked(not self.on_top.isChecked()))
        menu.addAction(on_top_action)

        menu.addSeparator()
        
        if self.device_combo.isVisible():
            devices_action = QAction("Устройства", self)
            devices_action.triggered.connect(self.show_devices)
            menu.addAction(devices_action)

        
            device_menu = menu.addMenu("Выбрать устройство")
            devices = self.load_devices()
            for device in devices.keys():
                display_text = f"{device} ({devices[device]['port']} | {devices[device]['baudrate']})"
                action = QAction(display_text, self)
                action.triggered.connect(lambda checked, d=device: self.device_combo.setCurrentIndex(self.device_combo.findData(d, Qt.ItemDataRole.UserRole)))
                device_menu.addAction(action)

        menu.addSeparator()
        settings_action = QAction("Настройки", self)
        settings_action.triggered.connect(self.show_settings)
        menu.addAction(settings_action)

        about_action = QAction("О программе", self)
        about_action.triggered.connect(self.show_about)
        menu.addAction(about_action)

        menu.addSeparator()
        reset_action = QAction("Сброс устройства (DTR)", self)
        reset_action.triggered.connect(lambda: self.reset_device(True))
        menu.addAction(reset_action)     


        menu.exec(self.output_text.mapToGlobal(pos))



    def auto_detect_baudrate(self):
        if self.serial_port.is_open:
            self.stop_serial_read ()

        port = self.port_combo.currentText() if not self.device_combo.isVisible() else self.load_devices()[self.device_combo.currentData(Qt.ItemDataRole.UserRole)]['port']
        if not port:
            self.append_colored_text("Не выбран порт для автоопределения", self.message_error, True, True, True)
            return

        # Расширенный список стандартных скоростей
        baud_rates = [
            '', '300', '600', '1200', '2400', '4800', '9600', '14400', 
            '19200', '28800', '38400', '57600', '115200', '230400', 
            '460800', '500000', '576000', '921600', '1000000', '1152000', 
            '1500000', '2000000'
        ]
        self.append_colored_text("Начинаю автоопределение скорости...", self.message_warning, True, True)


        for baud in baud_rates:
            try:
                self.serial_port.port = port
                self.serial_port.baudrate = int(baud)
                self.serial_port.dtr = False
                self.serial_port.open()
                settings = self.load_settings()
                if settings.get("reset_device", True):    self.reset_device()

                self.serial_port.reset_input_buffer()  # Очистка входного буфера
                self.serial_port.reset_output_buffer()  # Очистка выходного буфера
                self.data_buffer.clear()
                self.switch_on_off_icon()
                # Даем небольшую паузу для получения данных
                temp_reader = SerialReader(self.serial_port)
                temp_reader.start()
                temp_reader.msleep(500)  # Ждем 500мс

                if temp_reader.received_bytes:  # Если что-то получили
                    # Завершаем временный reader до запуска основного: два потока
                    # не должны одновременно читать один COM-порт.
                    temp_reader.stop()
                    temp_reader.wait()
                    self.append_colored_text(f"Обнаружила рабочая скорость: {baud}", self.message_info, True, True)
                    self.baud_combo.setCurrentText(baud)
                    self.start_serial_reader()
                    self.save_serial_settings()
                    return

                temp_reader.stop()
                temp_reader.wait()
                self.serial_port.close()
                self.switch_on_off_icon()

            except Exception as e:
                self.output_text.append(f"Проверка {baud} не удалась: {str(e)}")
                if self.serial_port.is_open:
                    self.serial_port.close()
                    self.switch_on_off_icon()


        self.append_colored_text("Не удалось определить скорость автоматически", self.message_error, True, True, True)
        self.stop_serial_read()
        self.stop_serial_port(mute=True)

    

    def default_settings(self):
        return {
            "theme": "light",
            "port": None,
            "baudrate": "",
            "timestamp": False,
            "topmost": False,
            "use_devices": False,
            "font_size": 15,
            "semona": True,
            "max_lines": 10000,
            "line_ending": "NL",
            "count_chars": False,
            "show_line_numbers": True,
            "use_control_chars": True,
             "debug": False,
             "make_Sem_fun": False,
             "character_male": False,
             "last_device": "",
             "mute": False,
             "open_startup": True,
             "reset_device": True  
        }


    def save_settings(self, theme=None, use_devices=None, max_lines=None, count_chars=None, 
                      font_size=None, show_line_numbers=None, port=None, baudrate=None, 
                      timestamp=None, topmost=None, line_ending=None, use_control_chars=None, 
                      semona=None, debug=None, debug_extra=None, make_Sem_fun=None, character_male=None,
                      last_device=None, reset_device=None, open_startup=None, mute=None ):
        # Загружаем текущие настройки только если нужно обновить существующий файл
        try:
            with open('settings.json', 'r') as f:
                settings = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            settings = self.default_settings()  # Если файла нет или он сломан, используем настройки по умолчанию

        # Обновляем только те параметры, которые переданы 
        if theme is not None: settings["theme"] = theme
        if use_devices is not None: settings["use_devices"] = use_devices
        if max_lines is not None: settings["max_lines"] = max_lines
        if count_chars is not None: settings["count_chars"] = count_chars
        if font_size is not None: settings["font_size"] = font_size
        if show_line_numbers is not None: settings["show_line_numbers"] = show_line_numbers
        if port is not None: settings["port"] = port
        if baudrate is not None: settings["baudrate"] = baudrate
        if timestamp is not None: settings["timestamp"] = timestamp
        if topmost is not None: settings["topmost"] = topmost
        if line_ending is not None: settings["line_ending"] = line_ending
        if use_control_chars is not None: settings["use_control_chars"] = use_control_chars
        if semona is not None: settings["semona"] = semona
        if debug is not None: settings["debug"] = debug
        if debug_extra is not None: settings["debug_extra"] = debug_extra
        if make_Sem_fun is not None: settings["make_Sem_fun"] = make_Sem_fun
        if character_male is not None: settings["character_male"] = bool(character_male)
        if last_device is not None: settings["last_device"] = last_device
        if reset_device is not None: settings["reset_device"] = reset_device
        if open_startup is not None: settings["open_startup"] = open_startup
        if mute is not None: settings["mute"] = mute

        with open('settings.json', 'w') as f:
            json.dump(settings, f)
        
    def load_devices(self):
        try:
            with open('devices.json', 'r', encoding='utf-8') as f:
                devices = json.load(f)
            # Проверяем и добавляем недостающие ключи
            for device in devices.values():
                if "use_control_chars" not in device:
                    device["use_control_chars"] = False
            return devices
        except FileNotFoundError:
            settings = self.load_settings()
            if settings.get("debug", False):
                self.append_colored_text(f'[debug] Файл devices.json не найден. SerialMonitor.load_devices', self.message_warning, True, False)
            #print('Файл devices.json не найден. SerialMonitor.load_devices')
            return {}
        except Exception as e:
            settings = self.load_settings()
            if settings.get("debug", False):
                self.append_colored_text(f'[debug] Ошибка загрузки devices.json: {e}. SerialMonitor.load_devices', self.message_warning, True, False)
            #print(f'Ошибка загрузки devices.json: {e}. SerialMonitor.load_devices')
            return {}
        
    def save_devices(self, devices):
        with open('devices.json', 'w', encoding='utf-8') as f:
            json.dump(devices, f, indent=4)

    def save_serial_settings(self):
        settings = self.load_settings()
        if not settings.get("use_devices", False):
            settings["port"] = self.port_combo.currentText() if self.port_combo.count() > 0 else None
            settings["baudrate"] = self.baud_combo.currentText()
            settings["timestamp"] = self.timestamp_check.isChecked()
            settings["line_ending"] = self.line_ending_combo.currentText()
            with open('settings.json', 'w') as f:
                json.dump(settings, f)
    



    def reset_device2(self, reset = False, msg = False):
        settings = self.load_settings()
        dbg = settings.get("debug", False)
        reset_enabled = settings.get("reset_device", True)  # Проверяем настройку сброса
        semona = settings.get("semona", True)
        if reset:
            reset_enabled = True

        if not reset_enabled:
            if dbg:
                self.append_colored_text(
                    "[debug] Сброс устройства отключен в настройках.",
                    self.message_warning,
                    True,
                    False
                )
            return
        
        try:
            if not self.serial_port.is_open:

                if semona:  message = "Увы, но сначала надо открыть порт!"
                else:       message = "Cначала надо открыть порт!"
                if msg:
                    self.append_colored_text(
                        message,
                        self.message_error,
                        True,
                        True,
                        True
                        )
                if dbg:
                    self.append_colored_text(
                                        "[debug] Cначала надо открыть порт!",
                                        self.message_error,
                                        True,
                                        False
                                        )
                return

    
            # Устанавливаем DTR и RTS в False для сброса
            self.serial_port.dtr = False
            self.serial_port.rts = False
            
            if msg:
                if semona:  message = f"Пробуем сбросить устройство! Ну как, получилось?"
                else:       message = f"Попытка сброса устройства"
                self.append_colored_text(message, self.message_info, True, msg, False)
            
            if dbg:
                self.append_colored_text(
                    "[debug] Осуществлена попытка сбросить устройство.",
                    self.message_warning,
                    True,
                    False
                )
    
            # Даем устройству время на сброс
            #time.sleep(0.5) не даем
    
            # Восстанавливаем сигналы DTR и RTS
            self.serial_port.dtr = True
            self.serial_port.rts = True
            if dbg:
                self.append_colored_text(
                    "[debug] Сигналы DTR и RTS восстановлены. Сброс устройства завершен.",
                    self.message_warning,
                    True,
                    False,
                    False
                )
        except Exception as e:
                if msg:
                    self.append_colored_text(
                        "Ошибка при выполнении сброса устройства!",
                        self.message_error,
                        True,
                        True,
                        True
                    )    
                dbg_extra = settings.get("debug_extra", False)
                if dbg and dbg_extra: 
                    self.append_colored_text(
                            f"[debug] Ошибка при выполнении сброса устройства: {str(e)}",
                            self.message_error,
                            True,
                            False,
                            True
                        )   


    def reset_device(self, reset=False):
        settings = self.load_settings()

        dbg = settings.get("debug", False)
        semona = settings.get("semona", True)
        reset_enabled = settings.get("reset_device", True)


        if reset:
            reset_enabled = True

        if not reset_enabled:
            if dbg:
                self.append_colored_text(
                    "[debug] Сброс устройства отключен в настройках.",
                    self.message_warning,
                    True,
                    False
                )
            return

        try:
            # Проверяем, открыт ли порт
            if not self.serial_port.is_open:

                if reset:
                    if semona: message = "Увы, но сначала надо открыть порт!"
                    else:      message = "Сначала надо открыть порт!"

                    self.append_colored_text(
                        message,
                        self.message_error,
                        True,
                        True,
                        True
                    )

                if dbg:
                    self.append_colored_text(
                        "[debug] Сначала надо открыть порт!",
                        self.message_error,
                        True,
                        False
                    )

                return

            # Устанавливаем DTR и RTS в False для сброса
            self.serial_port.dtr = False
            self.serial_port.rts = False

            if reset:
                if semona: message = "Пробуем сбросить устройство! Ну как, получилось?"
                else:      message = "Попытка сброса устройства"

                self.append_colored_text(
                    message,
                    self.message_info,
                    True,
                    True,
                    False
                )

            if dbg:
                self.append_colored_text(
                    "[debug] Осуществлена попытка сбросить устройство.",
                    self.message_warning,
                    True,
                    False
                )

            # Даем устройству время на сброс
            # time.sleep(0.5) не используем, чтобы не блокировать программу

            # Восстанавливаем сигналы DTR и RTS
            self.serial_port.dtr = True
            self.serial_port.rts = True

            if dbg:
                self.append_colored_text(
                    "[debug] Сигналы DTR и RTS восстановлены. Сброс устройства завершен.",
                    self.message_warning,
                    True,
                    False,
                    False
                )

        except Exception as e:
            if reset:
                self.append_colored_text(
                    "Ошибка при выполнении сброса устройства!",
                    self.message_error,
                    True,
                    True,
                    True
                )

            dbg_extra = settings.get("debug_extra", False)

            if dbg and dbg_extra:
                self.append_colored_text(
                    f"[debug] Ошибка при выполнении сброса устройства: {str(e)}",
                    self.message_error,
                    True,
                    False,
                    True
                )


    def load_settings_and_apply(self):
        try:
            settings = self.load_settings()
            self.use_control_chars = settings.get("use_control_chars", False)  # Устанавливаем по умолчанию только если не в режиме устройств
             
            if settings.get("use_devices", False):  # Режим устройств
                self.device_combo.setVisible(True)
                self.port_combo.setVisible(False)
                self.baud_combo.setVisible(False)
                self.line_ending_combo.setVisible(False)
                #self.update_devices()

                # Загружаем последнее устройство из настроек
                last_device = settings.get("last_device", None)
                if last_device:
                    devices = self.load_devices()
                    if last_device in devices:
                        self.device_combo.setCurrentIndex(self.device_combo.findData(last_device, Qt.ItemDataRole.UserRole))
                        
                        #self.change_device(last_device)
                    else:
                        self.append_colored_text(
                            f"Устройство '{last_device}' не нашёл в файле устройств.",
                            self.message_error,
                            True,
                            True,
                            True
                        )
                        
                        self.show_devices()
                else:
                    self.show_devices()

            else:  # Обычный режим
                self.device_combo.setVisible(False)
                self.port_combo.setVisible(True)
                self.baud_combo.setVisible(True)
                self.line_ending_combo.setVisible(True)

                # Проверяем доступные порты
                available_ports = [self.port_combo.itemText(i) for i in range(self.port_combo.count())]
                if settings.get("port") and settings["port"] in available_ports:
                    self.port_combo.setCurrentText(settings["port"])
                elif settings.get("port") is None:
                    self.port_combo.setCurrentText("")  # Пустая строка для port: null

                # Проверяем доступные скорости
                available_baudrates = [self.baud_combo.itemText(i) for i in range(self.baud_combo.count())]
                if settings.get("baudrate") and str(settings["baudrate"]) in available_baudrates:
                    self.baud_combo.setCurrentText(str(settings["baudrate"]))
                elif settings.get("baudrate") is None:
                    self.baud_combo.setCurrentText("")

                # Применяем настройки порта и скорости
                if settings.get("port") and settings.get("baudrate") and settings["port"] in available_ports and str(settings["baudrate"]) in available_baudrates:
                    try:
                        #self.change_port_and_baudrate(settings["port"], settings["baudrate"])

                        self.open_serial_port(settings["port"], settings["baudrate"])
                    except Exception as e:
                        self.append_colored_text(
                            f"Ошибка применения настроек порта '{settings['port']}' и скорости '{settings['baudrate']}': {str(e)}",
                            self.message_error,
                            True,
                            True,
                            True
                        )

                # Применяем окончание строки
                self.line_ending_combo.setCurrentText(settings.get("line_ending", "NL"))

            # Обновляем состояние кнопки "Стоп"
            self.switch_on_off_icon()
            

            # Обновляем счетчик символов и заголовок окна
            self.update_char_count()
            self.update_window_title()

        except Exception as e:
            self.append_colored_text(
                f"Ошибка загрузки и применения настроек: {str(e)}",
                self.message_error,
                True,
                True,
                True
            )

    def apply_device_settings(self, device_name: str, open_port = True):

        if not device_name:
            self.append_colored_text(
                "Устройство не выбрано. Пожалуйста, выбери устройство.",
                self.message_warning,
                True,
                True, 
                True
            )
            self.stop_serial_read ()
            self.stop_serial_port(mute=True)
            return

        devices = self.load_devices()
        if device_name not in devices:
            self.append_colored_text(
                f"Не нашёл устройство '{device_name}' в настройках.",
                self.message_error,
                True,
                True,
                True
            )
            self.stop_serial_read ()
            self.stop_serial_port(mute=True)
            return

        device = devices[device_name]
        port = device.get("port", "")
        baudrate = device.get("baudrate", "")
        line_ending = device.get("line_ending", "NL")
        timestamp = device.get("timestamp", False)
        use_control_chars = device.get("use_control_chars", False)

        if not port.strip():
            self.append_colored_text(
                f"Для устройства '{device_name}' не указан порт. Выбери порт.",
                self.message_error,
                True,
                True,
                True
            )
            self.stop_serial_read ()
            self.stop_serial_port(mute=True)
            return

        try:
            # Применяем настройки
            self.port_combo.setCurrentText(port)
            self.baud_combo.setCurrentText(baudrate)
            self.line_ending_combo.setCurrentText(line_ending)
            self.timestamp_check.setChecked(timestamp)
            self.use_control_chars = use_control_chars

            # Закрываем порт, если открыт
            #if self.serial_port.is_open:
            #    self.stop_serial_read ()

            # Очищаем вывод и открываем порт
            #self.clear_output()
            #self.change_port_and_baudrate(port, baudrate)
            #self.open_serial_port(port, baudrate)
            if open_port: 
                self.open_serial_port(port, baudrate)
                self.start_serial_reader()

            self.save_settings(last_device=device_name)


            settings = self.load_settings()
            if settings.get("debug", False):
                self.append_colored_text(
                    f"[debug] apply_device_settings - Настройки устройства '{device_name}' применены: порт {port}, скорость {baudrate}",
                    self.message_warning,
                    True,
                    False
                )

        except Exception as e:
            self.append_colored_text(
                f"Ошибка применения настроек устройства '{device_name}': {str(e)}",
                self.message_error,
                True,
                True, True
            )
            self.stop_serial_read ()
            self.stop_serial_port(mute=True)





    def apply_theme(self):
        settings = self.load_settings()
        font_size = settings.get("font_size", 16)
        theme_name = settings.get("theme", self.theme_manager.get_current_theme_name())
        if theme_name not in self.theme_manager.themes:
            theme_name = "light"
        self.theme_manager.current_theme_name = theme_name
        self.theme_manager.current_theme = self.theme_manager.themes[theme_name]

        # Получаем стили через ThemeManager
        stylesheet = self.theme_manager.get_stylesheet(theme_name=theme_name, font_size=font_size)
        self.setStyleSheet(stylesheet)
        
        # Обновляем иконки в зависимости от темы
        self.setIcon()
        
        # Обновляем цвета сообщений
        self.message_info = self.theme_manager.get_qcolor("info_color")
        self.message_warning = self.theme_manager.get_qcolor("warning_color")
        self.message_error = self.theme_manager.get_qcolor("error_color")
        self.message_custom = self.theme_manager.get_qcolor("custom_color")
        
        # Обновляем виджеты, если необходимо
        self.update_timestamp_icon(self.timestamp_check.isChecked())
        self.switch_on_off_icon()
        self.set_output_background(bool(self.serial_port and self.serial_port.is_open))
    





    def closeEvent(self, event):

        try:
            # Останавливаем поток чтения
            self.stop_serial_reader()

            # Закрываем serial-порт
            if self.serial_port.is_open:
                self.serial_port.close()
                self.switch_on_off_icon()

            # Останавливаем таймер обновления
            if self.update_timer.isActive():
                self.update_timer.stop()

            # Сохраняем настройки
            self.save_serial_settings()

            event.accept()
        except Exception as e:
            self.append_colored_text(
                f"Ошибка при закрытии приложения: {str(e)}",
                self.message_error,
                True,
                True, True
            )
            event.accept()

class PortComboBox(QComboBox):
    def showPopup(self):
        # Вызываем метод обновления портов перед раскрытием списка
        if hasattr(self, 'update_ports_callback') and callable(self.update_ports_callback):
            self.update_ports_callback()
        super().showPopup()  # Вызываем оригинальный метод для отображения списка

class SerialReader(QThread):
    # Передаём строку и timestamp, зафиксированный в момент её получения.
    data_received = pyqtSignal(object)
    connection_lost = pyqtSignal(str)

    def __init__(self, serial_port: serial.Serial, parent=None, debug=False):
        super().__init__()
        self.serial_port = serial_port
        self.parent = parent  # оставлен для совместимости с прежним вызовом
        self.debug = bool(debug)
        self.running = True
        self.buffer = bytearray()
        self.received_bytes = bytearray()
        self.encoding = "utf-8"
        self.idle_flush_ms = 500
        self.max_packet_size = 4096
        self.stopped_intentionally = False

    def stop(self):
        self.stopped_intentionally = True
        self.running = False

    def _emit_bytes(self, raw_line):
        # Метка времени создаётся worker-потоком при завершении/сбросе строки,
        # а не позднее в GUI при пакетном отображении.
        line = raw_line.decode(self.encoding, errors="replace")
        received_at = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        self.data_received.emit((line, received_at))

    def run(self):
        last_data_time = None
        try:
            while self.running:
                if not self.serial_port or not self.serial_port.is_open:
                    if not self.stopped_intentionally and self.debug:
                        self.data_received.emit(("[debug] Порт не открыт или недоступен.", datetime.now().strftime("%H:%M:%S.%f")[:-3]))
                    break

                waiting = self.serial_port.in_waiting
                if waiting:
                    raw = self.serial_port.read(min(waiting, 8192))
                    if raw:
                        self.buffer.extend(raw)
                        self.received_bytes.extend(raw)
                        last_data_time = time.monotonic()

                # Обрабатываем все полные строки за проход, не ограничиваясь
                # одной строкой на 10 мс. CRLF считается одним разделителем.
                while self.buffer and self.running:
                    cr = self.buffer.find(b"\r")
                    lf = self.buffer.find(b"\n")
                    positions = [pos for pos in (cr, lf) if pos >= 0]
                    if positions:
                        pos = min(positions)
                        raw_line = bytes(self.buffer[:pos])
                        delimiter = self.buffer[pos]
                        del self.buffer[:pos + 1]
                        if delimiter == 13 and self.buffer[:1] == b"\n":
                            del self.buffer[:1]
                        self._emit_bytes(raw_line)
                        continue

                    now = time.monotonic()
                    idle = last_data_time is not None and (now - last_data_time) * 1000 >= self.idle_flush_ms
                    if idle or len(self.buffer) >= self.max_packet_size:
                        chunk_size = len(self.buffer) if idle else self.max_packet_size
                        raw_line = bytes(self.buffer[:chunk_size])
                        del self.buffer[:chunk_size]
                        self._emit_bytes(raw_line)
                        if not self.buffer:
                            last_data_time = None
                        continue
                    break

                self.msleep(2)

        except (serial.SerialException, OSError) as e:
            if self.running and not self.stopped_intentionally:
                # Сигнал будет обработан главным GUI-потоком: там порт
                # корректно закроется, обновится кнопка и появится реплика Семоны.
                self.connection_lost.emit(str(e))
                if self.debug:
                    self.data_received.emit((f"[debug] Ошибка порта: {e}", datetime.now().strftime("%H:%M:%S.%f")[:-3]))
        except Exception as e:
            if self.running and not self.stopped_intentionally:
                if self.debug:
                    self.data_received.emit((f"[debug] Ошибка чтения: {e}", datetime.now().strftime("%H:%M:%S.%f")[:-3]))
        finally:
            self.running = False

class DevicesDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Устройства")
        self.setMinimumSize(400, 500)
        self.parent().setIcon()
       # self.setWindowIcon(QIcon(current_app_icon()))
        self._debug_printed = False  # Флаг для отладочного вывода
        
        self.layout = QVBoxLayout()
        
        self.add_group = QGroupBox("Новое устройство")
        self.add_layout = QFormLayout()
        self.device_name = QLineEdit()
        self.device_port = QComboBox()
        self.device_port.addItems([port.device for port in serial.tools.list_ports.comports()])
        self.device_baud = QComboBox()
        self.device_baud.addItems([
            '300', '600', '1200', '2400', '4800', '9600', '14400', 
            '19200', '28800', '38400', '57600', '115200', '230400', 
            '460800', '500000', '576000', '921600', '1000000', '1152000', 
            '1500000', '2000000'
        ])
        self.device_timestamp = QCheckBox("Отметки времени")
        self.device_control_chars = QCheckBox("Цветовые метки")  # Добавляем галочку
        self.device_line_ending = QComboBox()
        self.device_line_ending.addItems(["Нет конца строки", "NL", "CR", "NL & CR"])
        self.device_line_ending.setCurrentText("NL")
        self.confirm_add_button = QPushButton("Добавить")
        self.confirm_add_button.clicked.connect(self.add_device)
        
        self.add_layout.addRow("Имя:", self.device_name)
        self.add_layout.addRow("Порт:", self.device_port)
        self.add_layout.addRow("Скорость:", self.device_baud)
        self.add_layout.addRow("Окончание строки:", self.device_line_ending)
        self.add_layout.addRow("", self.device_timestamp)
        self.add_layout.addRow("", self.device_control_chars)  # Добавляем в форму
        self.add_layout.addRow(self.confirm_add_button)
        
        self.add_group.setLayout(self.add_layout)
        self.add_group.setVisible(False)
        self.layout.addWidget(self.add_group)
        
        self.devices_scroll = QScrollArea()
        self.devices_widget = QWidget()
        self.devices_layout = QVBoxLayout()
        self.devices_widget.setLayout(self.devices_layout)
        self.devices_scroll.setWidget(self.devices_widget)
        self.devices_scroll.setWidgetResizable(True)
        self.layout.addWidget(self.devices_scroll)

        self.add_button = QPushButton("Добавить устройство")
        self.add_button.clicked.connect(self.show_add_form)
        self.layout.addWidget(self.add_button)
        
        
        
        self.setLayout(self.layout)
        self.apply_theme()
        self.update_devices_list()

    def apply_theme(self):
        settings = self.parent().load_settings()
        #if settings.get("theme") == "dark":
            #self.setStyleSheet(self.parent().dark_theme_stylesheet())
       # else:
            #self.setStyleSheet(self.parent().light_theme_stylesheet())

    def show_add_form(self):
        self.add_group.setVisible(True)
        self.add_button.setVisible(False)


    def update_devices_list(self):
        for i in reversed(range(self.devices_layout.count())):
            self.devices_layout.itemAt(i).widget().setParent(None)

        devices = self.parent().load_devices()
        for name, settings in devices.items():
            device_group = QGroupBox(name)
            device_layout = QFormLayout()

            port_combo = QComboBox()
            port_combo.addItems([port.device for port in serial.tools.list_ports.comports()])
            port_combo.setCurrentText(settings["port"])
            port_combo.currentTextChanged.connect(lambda text, n=name: self.mark_as_changed(n))

            baud_combo = QComboBox()
            baud_combo.addItems([
                '300', '600', '1200', '2400', '4800', '9600', '14400', 
                '19200', '28800', '38400', '57600', '115200', '230400', 
                '460800', '500000', '576000', '921600', '1000000', '1152000', 
                '1500000', '2000000'
            ])
            baud_combo.setCurrentText(settings["baudrate"])
            baud_combo.currentTextChanged.connect(lambda text, n=name: self.mark_as_changed(n))

            line_ending_combo = QComboBox()
            line_ending_combo.addItems(["Нет конца строки", "NL", "CR", "NL & CR"])
            line_ending_combo.setCurrentText(settings.get("line_ending", "NL"))
            line_ending_combo.currentTextChanged.connect(lambda text, n=name: self.mark_as_changed(n))

            timestamp_check = QCheckBox("Отметки времени")
            timestamp_check.setChecked(settings["timestamp"])
            timestamp_check.stateChanged.connect(lambda state, n=name: self.mark_as_changed(n))

            control_chars_check = QCheckBox("Цветовые метки")
            control_chars_check.setChecked(settings.get("use_control_chars", False))
            #print(f"update_devices_list: {name}, use_control_chars: {control_chars_check.isChecked()}")  # Отладочный вывод


           
           
            control_chars_check.stateChanged.connect(lambda state, n=name: self.mark_as_changed(n))

            action_button = QPushButton("Удалить")
            action_button.clicked.connect(lambda _, n=name, btn=action_button: self.remove_device(n, btn))

            device_layout.addRow("Порт:", port_combo)          # 0: метка, 1: порт
            device_layout.addRow("Скорость:", baud_combo)      # 2: метка, 3: скорость
            device_layout.addRow("Окончание строки:", line_ending_combo)  # 4: метка, 5: окончание строки
            device_layout.addRow("", timestamp_check)          # 6: чекбокс отметок времени
            device_layout.addRow("", control_chars_check)      # 8: чекбокс управляющих символов
            device_layout.addRow(action_button)                # 10: кнопка
            device_group.setLayout(device_layout)
            self.devices_layout.addWidget(device_group)

            # Выводим отладочную информацию только один раз
      
        if not self._debug_printed:
            sett = self.parent().load_settings()
            if sett.get("debug", False):
                self.parent().append_colored_text(f'[debug] список устройств:', self.parent().message_warning, True, False)
                for name, device_settings in devices.items():
                    self.parent().append_colored_text(f'-- Устройство: {name}', self.parent().message_warning, True, False)
                    self.parent().append_colored_text(f'   Порт: {device_settings.get("port", "Не указан")}', self.parent().message_warning, True, False)
                    self.parent().append_colored_text(f'   Скорость: {device_settings.get("baudrate", "Не указана")}', self.parent().message_warning, True, False)
                    self.parent().append_colored_text(f'   Отметки времени: {device_settings.get("timestamp", False)}', self.parent().message_warning, True, False)
                    self.parent().append_colored_text(f'   Окончание строки: {device_settings.get("line_ending", "NL")}', self.parent().message_warning, True, False)
                    self.parent().append_colored_text(f'   Цветовые метки: {device_settings.get("use_control_chars", False)}', self.parent().message_warning, True, False)
            self._debug_printed = True


    def mark_as_changed(self, name):
        devices = self.parent().load_devices()
        widget = self.devices_layout.itemAt(list(devices.keys()).index(name)).widget()
        # Получаем кнопку "Удалить" или "Сохранить" (последний элемент в layout)
        button = widget.layout().itemAt(widget.layout().count() - 1).widget()
        if button.text() == "Удалить":
            button.setText("Сохранить")
            button.clicked.disconnect()
            button.clicked.connect(lambda: self.save_device(name))

    def save_device(self, name):
        devices = self.parent().load_devices()
        widget = self.devices_layout.itemAt(list(devices.keys()).index(name)).widget()
        layout = widget.layout()

        # Получаем данные из формы редактирования устройства
        port = layout.itemAt(1).widget().currentText()          # Порт (индекс 1)
        baudrate = layout.itemAt(3).widget().currentText()      # Скорость (индекс 3)
        line_ending = layout.itemAt(5).widget().currentText()   # Окончание строки (индекс 5)
        timestamp = layout.itemAt(6).widget().isChecked()       # Отметки времени (индекс 6)
        use_control_chars = layout.itemAt(7).widget().isChecked()  # Управляющие символы (индекс 7)

        # Полностью обновляем настройки устройства
        devices[name] = {
            "port": port,
            "baudrate": baudrate,
            "line_ending": line_ending,
            "timestamp": timestamp,
            "use_control_chars": use_control_chars
        }

        # Сохраняем изменения в файл
        self.parent().save_devices(devices)

        # Обновляем кнопку
        button = layout.itemAt(layout.count() - 1).widget()
        button.setText("Удалить")
        button.clicked.disconnect()
        button.clicked.connect(lambda _, n=name, btn=button: self.remove_device(n, btn))

        # Обновляем интерфейс
        self.parent().update_devices()  # Обновляем список устройств в основном окне
        self.update_devices_list()      # Обновляем список устройств в диалоге

    def add_device(self):
        devices = self.parent().load_devices()
        name = self.device_name.text()
        if name and name not in devices:
            devices[name] = {
                "port": self.device_port.currentText(),
                "baudrate": self.device_baud.currentText(),
                "timestamp": self.device_timestamp.isChecked(),
                "line_ending": self.device_line_ending.currentText(),
                "use_control_chars": self.device_control_chars.isChecked()
            }
            self.parent().save_devices(devices)
            self.device_name.clear()
            self.add_group.setVisible(False)
            self.add_button.setVisible(True)
            self.update_devices_list()
            self.parent().update_devices()
    

    def remove_device(self, name, button):
        reply = QMessageBox.question(self, 'Подтверждение', f'Удалить устройство "{name}"?',
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                   QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            devices = self.parent().load_devices()
            if name in devices:
                del devices[name]
                self.parent().save_devices(devices)
                self.update_devices_list()
                self.parent().update_devices()



class SettingsDialog(QDialog):

        def __init__(self, parent=None):
            super().__init__(parent)
            self.setWindowTitle("Настройки")
            #self.setMinimumSize(450, 755)
            #self.setBaseSize(500, 755)
            self.setGeometry(0, 0, 500, 755)
            self.center_window()
            self.setWindowIcon(QIcon(current_app_icon()))

            self.layout = QVBoxLayout()

            # Создаем QScrollArea
            scroll_area = QScrollArea()
            scroll_area.setWidgetResizable(True)  # Делаем содержимое масштабируемым

            # Создаем контейнерный виджет для содержимого
            content_widget = QWidget()
            content_layout = QVBoxLayout(content_widget)  # Макет для содержимого

            main_group = QGroupBox("Основные")
            main_layout = QVBoxLayout()  # Создаём общий макет для группы


            self.devices_check = QCheckBox("Режим устройств")
            self.devices_check.setToolTip('Вместо выбора порта - выбор устройства<br>• Добавить новое - контекстное меню -> Устройства')
            self.devices_check.stateChanged.connect(self.toggle_control_chars_visibility)
            
            self.devices_check.setVisible(False)
            
            self.reset_device_check = QCheckBox("Сброс через DTR")
            self.reset_device_check.setToolTip('Сброс устройства при открытии порта')
 
            control_chars_layout = QFormLayout()
            self.control_chars_check = QCheckBox("Активировать цветовые метки")
            self.control_chars_check.setToolTip('Будет искать цветные метки в данных<br>• 0x01 — INFO<br>• 0x02 — WARNING<br>• 0x03 — ERROR<br>• 0x04 — CUSTOM<br>• В режиме устройств метки включаются отдельно для каждого устройства.')
            self.control_chars_help_button = QPushButton("Как использовать цветовые метки?")
            self.control_chars_help_button.setToolTip("Открыть инструкцию и пример скетча для Arduino")
            self.control_chars_help_button.clicked.connect(self.show_control_chars_help)
            self.control_chars_check.toggled.connect(self.update_control_chars_help_visibility)

            self.semona_check = QCheckBox("Семона")
            self.semona_check.setToolTip('Просто Семона')
            self.semona_check.setVisible(False)  # Скрываем

            self.mute_check = QCheckBox("Отключить сообщения")
            self.mute_check.setToolTip('Отключает вывод информационных сообщений в текстовое поле')
            self.mute_check.setVisible(False)  # Скрываем
            
            #замест галочек выпадающий список
            self.message_mode_combo = QComboBox()
            self.message_mode_combo.addItems(["Семона", "Сообщения", "Без сообщений"])
            self.message_mode_combo.setToolTip('Выберите режим отображения сообщений:<br>• Семона - включает Семону<br>• Сообщения - только информационные сообщения<br>• Без сообщений - отключает все сообщения')
            self.message_mode_combo.currentIndexChanged.connect(self.update_message_mode)

            self.open_startup_check = QCheckBox("Открывать порт при старте")
            self.open_startup_check.setToolTip('Будет открывать порт при старте')

            self.debug_check = QCheckBox("Дебаг")
            self.debug_check.setToolTip('Вывод отладочной информации в текстовое поле')
            self.debug_check.stateChanged.connect(self.toogle_debug_extra_visibility)
            
            self.debug_extra_check = QCheckBox("Вывод полной ошибки в дебаг")
            self.debug_extra_check.setToolTip('Вывод сырой отладочной информации')
            
         

            main_layout.addWidget(self.devices_check)  # Добавляем devices_layout в общий макет
           
            main_layout.addWidget(self.message_mode_combo)  #  выпадающий список
            main_layout.addWidget(self.semona_check)# скрыто
            main_layout.addWidget(self.mute_check)  #  скрыто
          
            main_layout.addWidget(self.control_chars_check)
            main_layout.addWidget(self.control_chars_help_button)
            

            main_layout.addWidget(self.reset_device_check)  
            main_layout.addWidget(self.open_startup_check)  
            main_layout.addWidget(self.debug_check)
            main_layout.addWidget(self.debug_extra_check)
            

            # Устанавливаем общий макет для main_group
            main_group.setLayout(main_layout)

            # Добавляем main_group в макет содержимого
            content_layout.addWidget(main_group)

            # Тема
            theme_group = QGroupBox("Тема")
            theme_layout = QFormLayout()
            self.theme_combo = QComboBox()
            
            self.load_themes()
            self.theme_combo.addItems(self.themes.keys())
            
            self.theme_combo.setToolTip('Выбор темы<br>• темы сохраняются в themes.json<br>• файл можно редактировать')
          
            self.edit_themes_button = QPushButton("Редактор")
            self.edit_themes_button.setToolTip("Открыть редактор тем")

            self.edit_themes_button.clicked.connect(self.open_theme_editor)
            
            self.edit_themes_button.setVisible(True)
            
            theme_layout.addRow("", self.theme_combo)
            theme_layout.addRow("", self.edit_themes_button)
            theme_group.setLayout(theme_layout)
            content_layout.addWidget(theme_group)

            # Цвета и шрифт
            colors_group = QGroupBox("Цвета")
            colors_main_layout = QVBoxLayout()  # общий макет для группы

            # Макет для кнопок выбора цветов
            colors_layout = QFormLayout()
            self.timestamp_color_button = QPushButton("Выбрать цвет отметок времени")
            self.timestamp_color_button.clicked.connect(self.choose_timestamp_color)
            colors_layout.addWidget(self.timestamp_color_button)

            self.sent_color_button = QPushButton("Выбрать цвет отправленных данных")
            self.sent_color_button.clicked.connect(self.choose_sent_color)
            colors_layout.addWidget(self.sent_color_button)

            self.text_color_button = QPushButton("Выбрать цвет текста")
            self.text_color_button.clicked.connect(self.choose_text_color)
            colors_layout.addWidget(self.text_color_button)

            self.font_size_label = QLabel("Размер шрифта:")
            self.font_size_input = QSpinBox()
            self.font_size_input.setRange(8, 24)
            self.font_size_input.setValue(10)
            colors_layout.addRow(self.font_size_label, self.font_size_input)

            colors_main_layout.addLayout(colors_layout)  # макет в общий макет

            # Макет для кнопок управляющих символов
            control_chars_layout = QFormLayout()
            self.info_color_button = QPushButton("Цвет Info (0x01)")
            self.info_color_button.clicked.connect(self.choose_info_color)
            control_chars_layout.addWidget(self.info_color_button)

            self.warning_color_button = QPushButton("Цвет Warning (0x02)")
            self.warning_color_button.clicked.connect(self.choose_warning_color)
            control_chars_layout.addWidget(self.warning_color_button)

            self.error_color_button = QPushButton("Цвет Error (0x03)")
            self.error_color_button.clicked.connect(self.choose_error_color)
            control_chars_layout.addWidget(self.error_color_button)

            self.custom_color_button = QPushButton("Цвет Custom (0x04)")
            self.custom_color_button.clicked.connect(self.choose_custom_color)
            control_chars_layout.addWidget(self.custom_color_button)

    #       self.save_to_theme_button2 = QPushButton("Сохранить в тему")
    #       self.save_to_theme_button2.clicked.connect(self.save_colors_to_theme)
    #       control_chars_layout.addWidget(self.save_to_theme_button2)

            colors_main_layout.addLayout(control_chars_layout)  # макет в общий макет





            # Устанавливаем общий макет для группы
            colors_group.setLayout(colors_main_layout)

            # Группу в макет содержимого
            content_layout.addWidget(colors_group)

            # Строки
            lines_group = QGroupBox("Строки")
            lines_layout = QFormLayout()
            self.max_lines_label = QLabel("Максимальное количество строк:")
            self.max_lines_label.setToolTip('Максимальное количество строк в окне вывода, сверх указанного будет обрезать')
            self.max_lines_input = QSpinBox()
            self.max_lines_input.setRange(100, 100000)
            self.max_lines_input.setValue(10000)
            self.count_chars_check = QCheckBox("Считать символы")
            self.count_chars_check.setToolTip('раз два три и т.д.')
            self.show_line_numbers_check = QCheckBox("Нумерация строк")
            self.show_line_numbers_check.setToolTip('Показывать номера строк ')
            lines_layout.addWidget(self.max_lines_label)
            lines_layout.addWidget(self.max_lines_input)
            lines_layout.addWidget(self.count_chars_check)
            lines_layout.addWidget(self.show_line_numbers_check)
            lines_group.setLayout(lines_layout)
            content_layout.addWidget(lines_group)



            # Устанавливаем контейнерный виджет в QScrollArea
            scroll_area.setWidget(content_widget)




            # Добавляем QScrollArea в основной макет окна
            self.layout.addWidget(scroll_area)

            self.save_button = QPushButton("Сохранить")
            self.save_button.setToolTip('Сохранить настройки, цвета сохраняются и без этого')
            self.save_button.clicked.connect(self.accept)
            self.layout.addWidget(self.save_button)
            
            


            self.setLayout(self.layout)
            self.load_settings()
            self.apply_theme()
            self.update_color_buttons()
            self.toggle_control_chars_visibility()
            self.toogle_debug_extra_visibility()


        def update_message_mode(self):
            """Обновляет настройки semona и mute в зависимости от выбранного режима."""
            mode = self.message_mode_combo.currentText()
            if mode == "Семона":
                self.semona_check.setChecked(True)
                self.mute_check.setChecked(False)
            elif mode == "Сообщения":
                self.semona_check.setChecked(False)
                self.mute_check.setChecked(False)
            elif mode == "Без сообщений":
                self.semona_check.setChecked(False)
                self.mute_check.setChecked(True)


        def center_window(self):
            # Получаем размеры экрана
            screen_geometry = QGuiApplication.primaryScreen().geometry()
            screen_width = screen_geometry.width()
            screen_height = screen_geometry.height()

            # Получаем размеры окна
            window_width = self.frameGeometry().width()
            window_height = self.frameGeometry().height()

            # Рассчитываем координаты для центрирования
            x = (screen_width - window_width) // 2
            y = (screen_height - window_height) // 2

            # Перемещаем окно
            self.move(x, y)


        def toggle_control_chars_visibility(self):
            # В режиме устройств глобальная настройка меток скрыта:
            # она включается отдельно в настройках каждого устройства.
            visible = not self.devices_check.isChecked()
            self.control_chars_check.setVisible(visible)
            self.update_control_chars_help_visibility(self.control_chars_check.isChecked())

        def update_control_chars_help_visibility(self, checked=None):
            if not hasattr(self, "control_chars_help_button"):
                return
            if checked is None:
                checked = self.control_chars_check.isChecked()
            self.control_chars_help_button.setVisible(
                bool(checked) and not self.devices_check.isChecked()
            )

        def show_control_chars_help(self):
            code = r"""// SEMONA — пример использования цветовых меток
// Откройте Serial Monitor SEMONA и выберите скорость 115200 бод.
// В настройках SEMONA включите «Активировать цветовые метки».
// Метка отправляется отдельным первым байтом строки через Serial.write().
// Следом отправляется обычный текст сообщения.
// 0x01 — INFO (информация)
// 0x02 — WARNING (предупреждение)
// 0x03 — ERROR (ошибка)
// 0x04 — CUSTOM (пользовательский цвет)

const unsigned long MESSAGE_INTERVAL = 1500;
unsigned long previousMillis = 0;
unsigned long counter = 0;

void setup() {
  Serial.begin(115200);
  delay(500); 

  Serial.write(0x01);
  Serial.println("INFO: Устройство запущено");

  Serial.write(0x02);
  Serial.println("WARNING: Это пример предупреждения");

  Serial.write(0x03);
  Serial.println("ERROR: Это пример сообщения об ошибке");

  Serial.write(0x04);
  Serial.println("CUSTOM: Сообщение пользовательского типа");

  Serial.println("Обычное сообщение без цветовой метки");
}

void loop() {

  unsigned long currentMillis = millis();
  if (currentMillis - previousMillis >= MESSAGE_INTERVAL) {
    previousMillis = currentMillis;
    counter++;

    Serial.write(0x01);
    Serial.print("INFO: Счётчик = ");
    Serial.println(counter);

    if (counter % 5 == 0) {
      Serial.write(0x02);
      Serial.println("WARNING: Прошло пять интервалов");
    }

    if (counter % 10 == 0) {
      Serial.write(0x04);
      Serial.println("CUSTOM: Контрольное сообщение");
    }
  }
}
"""
            dialog = QDialog(self)
            dialog.setWindowTitle("Цветовые метки SEMONA — инструкция")
            dialog.setWindowIcon(QIcon(current_app_icon()))
            dialog.setMinimumSize(680, 650)
            dialog.resize(760, 720)

            layout = QVBoxLayout(dialog)
            explanation = QLabel(
                "Цветовая метка — это специальный управляющий байт, который SEMONA "
                "распознаёт в начале строки и использует для выбора цвета сообщения.\n"
                "Отправляйте метку отдельной командой Serial.write(), а затем текст "
                "через Serial.print() или Serial.println().\n\n"
                "Метки:\n0x00 — Обычный цвет\n0x01 — INFO\n0x02 — WARNING\n0x03 — ERROR\n0x04 — CUSTOM\n"
                "Без метки сообщение отображается обычным цветом. "
                "Цвета меток можно настроить в разделе «Цвета»."
            )
            explanation.setWordWrap(True)
            layout.addWidget(explanation)

            code_label = QLabel("Пример использования:")
            layout.addWidget(code_label)

            code_view = QPlainTextEdit()
            code_view.setReadOnly(True)
            code_view.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
            code_view.setPlainText(code)
            code_font = QFont("Consolas", 10)
            code_font.setStyleHint(QFont.StyleHint.Monospace)
            code_view.setFont(code_font)
            # Для примера всегда используется отдельная тёмная Arduino/C++-подобная тема,
            # независимо от выбранной темы всего приложения.
            code_view.setStyleSheet("""
                QPlainTextEdit {
                    background-color: #1E1E1E;
                    color: #D4D4D4;
                    border: 1px solid #3C3C3C;
                    border-radius: 5px;
                    padding: 9px;
                    selection-background-color: #264F78;
                    selection-color: #FFFFFF;
                }
                QScrollBar:vertical { background: #252526; width: 12px; margin: 0; }
                QScrollBar::handle:vertical { background: #555555; min-height: 24px; border-radius: 5px; }
                QScrollBar::handle:vertical:hover { background: #707070; }
                QScrollBar:horizontal { background: #252526; height: 12px; margin: 0; }
                QScrollBar::handle:horizontal { background: #555555; min-width: 24px; border-radius: 5px; }
                QScrollBar::handle:horizontal:hover { background: #707070; }
            """)
            code_view.highlighter = ArduinoSyntaxHighlighter(code_view.document())
            layout.addWidget(code_view, 1)

            buttons = QHBoxLayout()
            copy_button = QPushButton("Копировать пример")
            copy_button.clicked.connect(
                lambda: (QApplication.clipboard().setText(code),
                         copy_button.setText("Скопировано ✓"))
            )
            close_button = QPushButton("Закрыть")
            close_button.clicked.connect(dialog.accept)
            buttons.addWidget(copy_button)
            buttons.addStretch(1)
            buttons.addWidget(close_button)
            layout.addLayout(buttons)

            dialog.setStyleSheet(self.styleSheet())
            dialog.exec()

        def toogle_debug_extra_visibility(self):
            self.debug_extra_check.setVisible(self.debug_check.isChecked())

        def save_colors_to_theme(self):
            current_theme = self.theme_combo.currentText()
            settings = self.parent().load_settings()

            timestamp_color = self.parent().themes[current_theme]["default_timestamp_color"]
            sent_color = self.parent().themes[current_theme]["default_sent_color"]
            text_color = self.parent().themes[current_theme]["default_text_color"]
            control_colors = self.parent().themes[current_theme]["control_chars_colors"]

                # Добавляем цвета управляющих символов
            info_color = control_colors.get("info_color", "#00FF00")
            warning_color = control_colors.get("warning_color", "#FFFF00")
            error_color = control_colors.get("error_color", "#FF0000")
            custom_color = control_colors.get("custom_color", "#00FFFF")

            try:
                with open('themes.json', 'r', encoding='utf-8') as f:
                    themes = json.load(f)
            except FileNotFoundError:
                themes = self.themes

            if current_theme in themes:
                themes[current_theme]["default_timestamp_color"] = timestamp_color
                themes[current_theme]["default_sent_color"] = sent_color
                themes[current_theme]["default_text_color"] = text_color
                themes[current_theme]["control_chars_colors"] = control_colors
                themes[current_theme]["control_chars_colors"] = {
                    "info_color": info_color,
                    "warning_color": warning_color,
                    "error_color": error_color,
                    "custom_color": custom_color
                }

            with open('themes.json', 'w', encoding='utf-8') as f:
                json.dump(themes, f, indent=4)

            #QMessageBox.information(self, "Успех", f"Цвета сохранены в тему '{current_theme}'")


        def open_theme_editor(self):
            """Закрываем настройки и открываем немодальный редактор тем."""
            main_window = self.parent()
            self.accept()
            if main_window and hasattr(main_window, "open_theme_editor"):
                QTimer.singleShot(0, main_window.open_theme_editor)

        def load_themes(self):
            try:
                with open('themes.json', 'r', encoding='utf-8') as f:
                    self.themes = json.load(f)
            except FileNotFoundError:
                #print("Файл тем не найден. load_themes()")
                settings = self.load_settings()
                if settings.get("debug", False):
                    self.append_colored_text(f'[debug] Файл тем не найден. load_themes()', self.message_warning, True, False)
                
                self.themes = DEFAULT_THEME
                
                with open('themes.json', 'w', encoding='utf-8') as f:
                    json.dump(self.themes, f, indent=4)
            except Exception as e:
                settings = self.load_settings()
                if settings.get("debug", False):
                    self.append_colored_text(f'[debug] Ошибка загрузки тем в SettingsDialog: {e}', self.message_warning, True, False)

                self.themes = self.parent().default_theme()  # Используем дефолтные темы из SerialMonitor
 
 
        def get_max_lines(self):
            return self.max_lines_input.value()
       
        def get_open_startup(self):
            return self.open_startup_check.isChecked()

        def apply_theme(self):
            settings = self.parent().load_settings()
            current_theme = settings.get("theme", "light")
            if current_theme in self.themes:
                stylesheet = self.themes[current_theme]["stylesheet"]
                font_size = settings.get("font_size", 16)
                text_color = settings.get("text_color", self.themes[current_theme]["default_text_color"])
                # Заменяем placeholders в stylesheet
                styled_sheet = (stylesheet.replace("{font_size}", str(font_size))
                                .replace("{text_color}", text_color)
                                .replace("{font_family}", "Consolas"))
                self.setStyleSheet(styled_sheet)
                self.parent().apply_tooltip_style(current_theme)   

        def load_settings(self):
            settings = self.parent().load_settings()  # Загружаем настройки из родителя
            self.theme_combo.setCurrentText(settings.get("theme", "light"))
            self.devices_check.setChecked(settings.get("use_devices", False))
            self.max_lines_input.setValue(settings.get("max_lines", 10000))
            self.count_chars_check.setChecked(settings.get("count_chars", False))
            self.show_line_numbers_check.setChecked(settings.get("show_line_numbers", False))
            self.semona_check.setChecked(settings.get("semona", True))
            self.font_size_input.setValue(settings.get("font_size", 16))
            self.control_chars_check.setChecked(settings.get("use_control_chars", False))
            self.debug_check.setChecked(settings.get("debug", False)) 
            self.debug_extra_check.setChecked(settings.get("debug_extra", False)) 
            self.reset_device_check.setChecked(settings.get("reset_device", True))  
            self.open_startup_check.setChecked(settings.get("open_startup", True))  
            self.mute_check.setChecked(settings.get("mute", False))  
            # Устанавливаем состояние выпадающего списка на основе semona и mute
            if self.semona_check.isChecked():
                self.message_mode_combo.setCurrentText("Семона")
            elif self.mute_check.isChecked():
                self.message_mode_combo.setCurrentText("Без сообщений")
            else:
                self.message_mode_combo.setCurrentText("Сообщения")        
                
            # Если включен режим отладки, выводим сообщение
            if settings.get("debug", False):
                self.parent().append_colored_text( f'[debug] текущие настройки:',  self.parent().message_warning,  True,   False )
                self.parent().append_colored_text( f'-- theme: {self.theme_combo.currentText()}',  self.parent().message_warning,  True,   False )
                self.parent().append_colored_text( f'-- use_devices: {self.devices_check.isChecked()}',  self.parent().message_warning,  True,   False )
                self.parent().append_colored_text( f'-- max_lines: {self.max_lines_input.value()}',  self.parent().message_warning,  True,   False )
                self.parent().append_colored_text( f'-- count_chars: {self.count_chars_check.isChecked()}',  self.parent().message_warning,  True,   False )
                self.parent().append_colored_text( f'-- show_line_numbers: {self.show_line_numbers_check.isChecked()}',  self.parent().message_warning,  True,   False )
                self.parent().append_colored_text( f'-- semona: {self.semona_check.isChecked()}',  self.parent().message_warning,  True,   False )
                self.parent().append_colored_text( f'-- font_size: {self.font_size_input.value()}',  self.parent().message_warning,  True,   False )
                self.parent().append_colored_text( f'-- use_control_chars: {self.control_chars_check.isChecked()}',  self.parent().message_warning,  True,   False )
                self.parent().append_colored_text( f'-- debug: {self.debug_check.isChecked()}',  self.parent().message_warning,  True,   False )
                self.parent().append_colored_text( f'-- debug: {self.debug_extra_check.isChecked()}',  self.parent().message_warning,  True,   False )
                self.parent().append_colored_text( f'-- reset: {self.reset_device_check.isChecked()}',  self.parent().message_warning,  True,   False )
                self.parent().append_colored_text( f'-- open_startup: {self.open_startup_check.isChecked()}',  self.parent().message_warning,  True,   False )
                self.parent().append_colored_text( f'-- mute: {self.mute_check.isChecked()}',  self.parent().message_warning,  True,   False )
            # Обновляем кнопки цветов
            self.update_color_buttons()

        def get_show_line_numbers(self):
            return self.show_line_numbers_check.isChecked()
        
        def get_mute(self):
            return self.mute_check.isChecked()

        def update_color_buttons(self):
            settings = self.parent().load_settings()
            current_theme = settings.get("theme", "light")
            timestamp_color = self.parent().themes[current_theme]["default_timestamp_color"]
            sent_color = self.parent().themes[current_theme]["default_sent_color"]
            text_color = self.parent().themes[current_theme]["default_text_color"]
            control_colors = self.parent().themes[current_theme]["control_chars_colors"]

            self.timestamp_color_button.setStyleSheet(f"background-color: {timestamp_color}; color: white; padding: 5px;")
            self.sent_color_button.setStyleSheet(f"background-color: {sent_color}; color: white; padding: 5px;")
            self.text_color_button.setStyleSheet(f"background-color: {text_color}; color: white; padding: 5px;")
            self.info_color_button.setStyleSheet(f"background-color: {control_colors['info_color']}; color: white; padding: 5px;")
            self.warning_color_button.setStyleSheet(f"background-color: {control_colors['warning_color']}; color: white; padding: 5px;")
            self.error_color_button.setStyleSheet(f"background-color: {control_colors['error_color']}; color: white; padding: 5px;")
            self.custom_color_button.setStyleSheet(f"background-color: {control_colors['custom_color']}; color: white; padding: 5px;")

        def choose_info_color(self):
            settings = self.parent().load_settings()
            dbg = settings.get("debug", False)  # Проверяем, включен ли режим отладки
            current_theme = settings.get("theme", "light")
            control_colors = self.parent().themes[current_theme]["control_chars_colors"]
            current_color = QColor(control_colors.get("info_color", "#00FF00"))

            if dbg:
                self.parent().append_colored_text(
                    f"[debug] Текущая тема: {current_theme}", 
                    self.parent().message_warning, 
                    True, 
                    False
                )
                self.parent().append_colored_text(
                    f"[debug] Текущий цвет Info: {current_color.name()}", 
                    self.parent().message_warning, 
                    True, 
                    False
                )

            color = QColorDialog.getColor(current_color, self, "Выберите цвет для Info")
            if color.isValid():
                control_colors["info_color"] = color.name()
                self.parent().message_info = color
                with open('themes.json', 'w', encoding='utf-8') as f:
                    json.dump(self.parent().themes, f, indent=4)

                if dbg:
                    self.parent().append_colored_text(
                        f"[debug] Новый цвет Info: {color.name()} записан в тему {current_theme}", 
                        self.parent().message_warning, 
                        True, 
                        False
                    )

                self.update_color_buttons()
            

        def choose_warning_color(self):
            settings = self.parent().load_settings()
            dbg = settings.get("debug", False)  # Проверяем, включен ли режим отладки
            current_theme = settings.get("theme", "light")
            control_colors = self.parent().themes[current_theme]["control_chars_colors"]
            current_color = QColor(control_colors.get("warning_color", "#FFFF00"))

            if dbg:
                self.parent().append_colored_text(
                    f"[debug] Текущая тема: {current_theme}",
                    self.parent().message_warning,
                    True,
                    False
                )
                self.parent().append_colored_text(
                    f"[debug] Текущий цвет Warning: {current_color.name()}",
                    self.parent().message_warning,
                    True,
                    False
                )

            color = QColorDialog.getColor(current_color, self, "Выберите цвет для Warning")
            if color.isValid():
                control_colors["warning_color"] = color.name()
                self.parent().message_warning = color
                with open('themes.json', 'w', encoding='utf-8') as f:
                    json.dump(self.parent().themes, f, indent=4)

                if dbg:
                    self.parent().append_colored_text(
                        f"[debug] Новый цвет Warning: {color.name()} записан в тему {current_theme}",
                        self.parent().message_warning,
                        True,
                        False
                    )

                self.update_color_buttons()

        def choose_error_color(self):
            settings = self.parent().load_settings()
            dbg = settings.get("debug", False)  # Проверяем, включен ли режим отладки
            current_theme = settings.get("theme", "light")
            control_colors = self.parent().themes[current_theme]["control_chars_colors"]
            current_color = QColor(control_colors.get("error_color", "#FF0000"))

            if dbg:
                self.parent().append_colored_text(
                    f"[debug] Текущая тема: {current_theme}",
                    self.parent().message_warning,
                    True,
                    False
                )
                self.parent().append_colored_text(
                    f"[debug] Текущий цвет Error: {current_color.name()}",
                    self.parent().message_warning,
                    True,
                    False
                )

            color = QColorDialog.getColor(current_color, self, "Выберите цвет для Error")
            if color.isValid():
                control_colors["error_color"] = color.name()
                self.parent().message_error = color
                with open('themes.json', 'w', encoding='utf-8') as f:
                    json.dump(self.parent().themes, f, indent=4)

                if dbg:
                    self.parent().append_colored_text(
                        f"[debug] Новый цвет Error: {color.name()} записан в тему {current_theme}",
                        self.parent().message_warning,
                        True,
                        False
                    )

                self.update_color_buttons()

        def choose_custom_color(self):
            settings = self.parent().load_settings()
            dbg = settings.get("debug", False)  # Проверяем, включен ли режим отладки
            current_theme = settings.get("theme", "light")
            control_colors = self.parent().themes[current_theme]["control_chars_colors"]
            current_color = QColor(control_colors.get("custom_color", "#00FFFF"))

            if dbg:
                self.parent().append_colored_text(
                    f"[debug] Текущая тема: {current_theme}",
                    self.parent().message_warning,
                    True,
                    False
                )
                self.parent().append_colored_text(
                    f"[debug] Текущий цвет Custom: {current_color.name()}",
                    self.parent().message_warning,
                    True,
                    False
                )

            color = QColorDialog.getColor(current_color, self, "Выберите цвет для Custom")
            if color.isValid():
                control_colors["custom_color"] = color.name()
                self.parent().message_custom = color
                with open('themes.json', 'w', encoding='utf-8') as f:
                    json.dump(self.parent().themes, f, indent=4)

                if dbg:
                    self.parent().append_colored_text(
                        f"[debug] Новый цвет Custom: {color.name()} записан в тему {current_theme}",
                        self.parent().message_warning,
                        True,
                        False
                    )

                self.update_color_buttons()


        def get_count_chars(self):
            return self.count_chars_check.isChecked()

        def get_theme(self):
            return self.theme_combo.currentText()

        def get_use_devices(self):
            return self.devices_check.isChecked()

        def get_font_size(self):
            return self.font_size_input.value()

        def choose_timestamp_color(self):
            settings = self.parent().load_settings()
            current_theme = settings.get("theme", "light")
            current_color = QColor(self.parent().themes[current_theme]["default_timestamp_color"])
            color = QColorDialog.getColor(current_color, self, "Выберите цвет отметок времени")
            if color.isValid():
                self.parent().themes[current_theme]["default_timestamp_color"] = color.name()
                with open('themes.json', 'w', encoding='utf-8') as f:
                    json.dump(self.parent().themes, f, indent=4)
                self.update_color_buttons()

        def choose_sent_color(self):
            settings = self.parent().load_settings()
            current_theme = settings.get("theme", "light")
            current_color = QColor(self.parent().themes[current_theme]["default_sent_color"])
            color = QColorDialog.getColor(current_color, self, "Выберите цвет отправленных данных")
            if color.isValid():
                self.parent().themes[current_theme]["default_sent_color"] = color.name()
                with open('themes.json', 'w', encoding='utf-8') as f:
                    json.dump(self.parent().themes, f, indent=4)
                self.update_color_buttons()

        def choose_text_color(self):
            settings = self.parent().load_settings()
            current_theme = settings.get("theme", "light")
            current_color = QColor(self.parent().themes[current_theme]["default_text_color"])
            color = QColorDialog.getColor(current_color, self, "Выберите цвет текста")
            if color.isValid():
                self.parent().themes[current_theme]["default_text_color"] = color.name()
                with open('themes.json', 'w', encoding='utf-8') as f:
                    json.dump(self.parent().themes, f, indent=4)
                self.update_color_buttons()

        def accept(self):
            self.save_colors_to_theme()
            # Создаём словарь настроек на основе текущих значений элементов интерфейса 
            settings = {
                "theme": self.theme_combo.currentText(),  # Текущая выбранная тема из выпадающего списка
                "use_devices": self.devices_check.isChecked(),  # Включён ли режим использования устройств (чекбокс)
                "max_lines": self.max_lines_input.value(),  # Максимальное количество строк в выводе (значение из числового поля)
                "count_chars": self.count_chars_check.isChecked(),  # Включён ли подсчёт символов (чекбокс)
                "font_size": self.font_size_input.value(),  # Размер шрифта (значение из числового поля)
                "semona": self.semona_check.isChecked(),  # Неясное назначение (возможно, специфичная настройка или опечатка)
                "show_line_numbers": self.show_line_numbers_check.isChecked(),  # Показывать ли номера строк (чекбокс)
                "debug": self.debug_check.isChecked(),  # Включён ли режим отладки (чекбокс)
                "debug_extra": self.debug_extra_check.isChecked(),  # Включён ли режим отладки (чекбокс)
                "mute": self.mute_check.isChecked(),  # Показывать ли номера строк (чекбокс)
                "open_startup": self.open_startup_check.isChecked(),  # Сбросить ли устройство (чекбокс)
                "reset_device": self.reset_device_check.isChecked(),  # Сбросить ли устройство (чекбокс)
            } 
           
            # Если режим устройств не включён
            if not self.devices_check.isChecked():
                settings["use_control_chars"] = self.control_chars_check.isChecked()  # Сохраняем состояние чекбокса управляющих символов в настройки
                self.parent().use_control_chars = self.control_chars_check.isChecked()  # Обновляем атрибут родительского объекта напрямую
            else:
                # Если режим устройств включён, получаем имя текущего устройства из выпадающего списка
                device_name = self.parent().device_combo.currentData(Qt.ItemDataRole.UserRole)
                if device_name:  # Проверяем, выбрано ли устройство (не None)
                    devices = self.parent().load_devices()  # Загружаем словарь всех устройств из родительского объекта
                    if device_name in devices:  # Если выбранное устройство есть в словаре
                        self.parent().use_control_chars = devices[device_name]["use_control_chars"] # Обновляем атрибут родительского объекта
                        #devices[device_name]["use_control_chars"] = self.control_chars_check.isChecked()  # Обновляем настройку управляющих символов для этого устройства
                        #self.parent().save_devices(devices)  # Сохраняем обновлённый словарь устройств
                    #self.parent().use_control_chars = self.control_chars_check.isChecked()  # Обновляем атрибут родительского объекта
                    #self.parent().use_control_chars_changed = True  # Устанавливаем флаг, что значение use_control_chars было изменено

            # Сохраняем все настройки в родительском объекте, распаковывая словарь
            self.parent().save_settings(**settings)
            settings = self.parent().load_settings()  # Загружаем настройки из родителя 
            if settings.get("debug", False):
                self.parent().append_colored_text( f'[debug] применили настройки:',  self.parent().message_warning,  True,   False )
                self.parent().append_colored_text( f'-- theme: {self.theme_combo.currentText()}',  self.parent().message_warning,  True,   False )
                self.parent().append_colored_text( f'-- use_devices: {self.devices_check.isChecked()}',  self.parent().message_warning,  True,   False )
                self.parent().append_colored_text( f'-- max_lines: {self.max_lines_input.value()}',  self.parent().message_warning,  True,   False )
                self.parent().append_colored_text( f'-- count_chars: {self.count_chars_check.isChecked()}',  self.parent().message_warning,  True,   False )
                self.parent().append_colored_text( f'-- show_line_numbers: {self.show_line_numbers_check.isChecked()}',  self.parent().message_warning,  True,   False )
                self.parent().append_colored_text( f'-- semona: {self.semona_check.isChecked()}',  self.parent().message_warning,  True,   False )
                self.parent().append_colored_text( f'-- font_size: {self.font_size_input.value()}',  self.parent().message_warning,  True,   False )
                self.parent().append_colored_text( f'-- use_control_chars: {self.control_chars_check.isChecked()}',  self.parent().message_warning,  True,   False )
                self.parent().append_colored_text( f'-- debug: {self.debug_check.isChecked()}',  self.parent().message_warning,  True,   False )
                self.parent().append_colored_text( f'-- debug: {self.debug_extra_check.isChecked()}',  self.parent().message_warning,  True,   False )
                self.parent().append_colored_text( f'-- reset: {self.reset_device_check.isChecked()}',  self.parent().message_warning,  True,   False )
                self.parent().append_colored_text( f'-- mute: {self.mute_check.isChecked()}',  self.parent().message_warning,  True,   False )
                self.parent().append_colored_text( f'-- open_startup: {self.open_startup_check.isChecked()}',  self.parent().message_warning,  True,   False )
            # Обновляем кнопки цветов
            self.apply_theme()  # Применяем тему 
            
            # Вызываем метод accept() родительского класса (QDialog), чтобы закрыть диалог с подтверждением
            super().accept()





class ThemeManager:
    def __init__(self, themes_file='themes.json', settings_file='settings.json'):
        self.themes_file = themes_file
        self.settings_file = settings_file
        self.themes = self.load_themes()
        self.current_theme_name = self.load_current_theme_name()
        if self.current_theme_name not in self.themes:
            self.current_theme_name = "light"
        self.current_theme = self.themes.get(self.current_theme_name, deepcopy(DEFAULT_THEME["light"]))

    def load_themes(self):
        try:
            if os.path.exists(self.themes_file):
                with open(self.themes_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return deepcopy(DEFAULT_THEME)
        except Exception as e:
            print(f"Ошибка загрузки тем: {e}")
            return deepcopy(DEFAULT_THEME)

    def save_themes(self):
        try:
            with open(self.themes_file, 'w', encoding='utf-8') as f:
                json.dump(self.themes, f, indent=4)
        except Exception as e:
            print(f"Ошибка сохранения тем: {e}")

    def load_current_theme_name(self):
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    return settings.get("theme", "light")
            return "light"
        except Exception as e:
            print(f"Ошибка загрузки настроек: {e}")
            return "light"

    def save_current_theme_name(self, theme_name):
        try:
            settings = {}
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
            settings["theme"] = theme_name
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=4)
            self.current_theme_name = theme_name
            self.current_theme = self.themes.get(theme_name, DEFAULT_THEME["light"])
        except Exception as e:
            print(f"Ошибка сохранения текущей темы: {e}")

    def get_current_theme(self):
        return self.current_theme

    def get_current_theme_name(self):
        return self.current_theme_name

    def get_theme(self, theme_name):
        return self.themes.get(theme_name, DEFAULT_THEME["light"])

    def get_stylesheet(self, theme_name=None, font_size=16, text_color=None, font_family="Consolas"):
        theme = self.themes.get(theme_name, self.current_theme) if theme_name else self.current_theme
        text_color = text_color or theme["default_text_color"]
        stylesheet = theme["stylesheet"]
        return stylesheet.replace("{font_size}", str(font_size)).replace("{text_color}", text_color).replace("{font_family}", font_family)

    def get_color(self, color_key, theme_name=None):
        theme = self.themes.get(theme_name, self.current_theme) if theme_name else self.current_theme
        if color_key in theme:
            return theme[color_key]
        elif color_key in theme["control_chars_colors"]:
            return theme["control_chars_colors"][color_key]
        return None

    def get_qcolor(self, color_key, theme_name=None):
        color = self.get_color(color_key, theme_name)
        return QColor(color) if color else QColor("#000000")

    def set_theme(self, theme_name):
        if theme_name in self.themes:
            self.save_current_theme_name(theme_name)
        else:
            print(f"Тема '{theme_name}' не найдена.")

    def add_theme(self, theme_name, theme_data):
        if theme_name not in self.themes:
            self.themes[theme_name] = deepcopy(theme_data)
            self.save_themes()
            return True
        print(f"Тема '{theme_name}' уже существует.")
        return False

    def delete_theme(self, theme_name):
        if theme_name in ["light", "retro", "dark", "duino", "ocean"]:
            print("Нельзя удалить стандартные темы!")
            return False
        if theme_name in self.themes:
            del self.themes[theme_name]
            self.save_themes()
            if theme_name == self.current_theme_name:
                self.set_theme("light")
            return True
        print(f"Тема '{theme_name}' не найдена.")
        return False

    def update_theme(self, theme_name, theme_data):
        if theme_name in self.themes:
            self.themes[theme_name] = deepcopy(theme_data)
            self.save_themes()
            if theme_name == self.current_theme_name:
                self.current_theme = self.themes[theme_name]
            return True
        print(f"Тема '{theme_name}' не найдена.")
        return False

    def get_all_theme_names(self):
        return list(self.themes.keys())

    def update_stylesheet_property(self, theme_name, selector, property_name, value):
        if theme_name not in self.themes:
            return False
        theme = self.themes[theme_name]
        stylesheet = theme["stylesheet"]
        selectors = self.parse_stylesheet(stylesheet)
        updated = False
        for i, (sel, props) in enumerate(selectors):
            if sel.strip() == selector.strip():
                new_properties = []
                prop_updated = False
                for prop, val in props:
                    if prop == property_name:
                        if property_name in ("border", "border-right"):
                            # Меняем именно цвет, не принимая слова px/solid за цвет.
                            color_pattern = r"#[0-9a-fA-F]{3,8}|rgba?\([^)]*\)|\b(?:black|white|red|green|blue|gray|grey|transparent)\b"
                            if re.search(color_pattern, val, flags=re.I):
                                val = re.sub(color_pattern, value, val, count=1, flags=re.I)
                            else:
                                val = f"1px solid {value}"
                            new_properties.append((prop, val))
                        else:
                            new_properties.append((prop, value))
                        prop_updated = True
                    else:
                        new_properties.append((prop, val))
                if not prop_updated and property_name in ["background-color", "color", "border", "border-right"]:
                    new_properties.append((property_name, f"1px solid {value}") if property_name in ("border", "border-right") else (property_name, value))
                selectors[i] = (sel, new_properties)
                updated = True
        if not updated:
            selectors.append((selector, [(property_name, value)]))
        theme["stylesheet"] = ' '.join([f"{sel} {{{' '.join(f'{p}: {v};' for p, v in props)}}}" for sel, props in selectors])
        self.update_theme(theme_name, theme)
        return True


    def parse_stylesheet(self, stylesheet):
        selectors = []
        seen_selectors = set()  # Для отслеживания уникальных селекторов
        current_selector = ""
        current_properties = []
        brace_level = 0
        buffer = ""
        i = 0
        while i < len(stylesheet):
            char = stylesheet[i]
            buffer += char
            if char == '{':
                brace_level += 1
                if brace_level == 1:
                    current_selector = buffer[:-1].strip()
                    buffer = ""
            elif char == '}' and brace_level > 0:
                brace_level -= 1
                if brace_level == 0:
                    properties = re.findall(r'([\w-]+):\s*([^;]*);', buffer[:-1].strip())
                    if current_selector:
                        if current_selector in seen_selectors:
                            for index, (existing_selector, existing_props) in enumerate(selectors):
                                if existing_selector == current_selector:
                                    for prop, value in properties:
                                        existing_props = [(p, v) for p, v in existing_props if p != prop]
                                        existing_props.append((prop, value))
                                    selectors[index] = (existing_selector, existing_props)
                                    break
                        else:
                            selectors.append((current_selector, properties))
                            seen_selectors.add(current_selector)
                    buffer = ""
                    current_selector = ""
            i += 1
        print(f"Parsed {len(selectors)} selectors: {[sel for sel, _ in selectors]}")
        return selectors

# Класс ThemesEditorDialog
class ThemesEditorDialog(QDialog):
    """Понятный редактор цветов: параметры сгруппированы по элементам интерфейса."""

    COLOR_ITEMS = [
        ("Окно приложения", "QWidget", "background-color", "Основной фон окна и панелей"),
        ("Текст интерфейса", "QWidget", "color", "Надписи, подписи и обычный текст интерфейса"),
        ("Кнопки", "QPushButton", "background-color", "Обычное состояние кнопок"),
        ("Текст кнопок", "QPushButton", "color", "Надписи на кнопках"),
        ("Кнопки при наведении", "QPushButton:hover", "background-color", "Фон кнопки под курсором"),
        ("Поле ввода команды", "QLineEdit#textsend", "background-color", "Фон строки, куда вводится команда"),
        ("Текст поля ввода", "QLineEdit#textsend", "color", "Цвет вводимой команды"),
        ("Окно принятых/отправленных данных", "QTextEdit#outputText", "background-color", "Фон большого окна с текстом порта"),
        ("Номера строк", "QTextEdit#lineNumbers", "background-color", "Фон колонки с номерами строк"),
        ("Текст номеров строк", "QTextEdit#lineNumbers", "color", "Цвет цифр в колонке номеров"),
        ("Выпадающие списки", "QComboBox#Combo", "background-color", "Фон закрытого списка выбора COM-порта и параметров"),
        ("Текст выпадающих списков", "QComboBox#Combo", "color", "Текст выбранного значения"),
        ("Фон раскрытого списка", "QComboBox#Combo QAbstractItemView", "background-color", "Фон открытого списка вариантов"),
        ("Текст раскрытого списка", "QComboBox#Combo QAbstractItemView", "color", "Текст вариантов в открытом списке"),
        ("Выбранный пункт списка", "QComboBox#Combo QAbstractItemView::item:selected", "background-color", "Фон выбранного/подсвеченного варианта"),
        ("Текст выбранного пункта", "QComboBox#Combo QAbstractItemView::item:selected", "color", "Текст выбранного/подсвеченного варианта"),
        ("Фон контекстного меню", "QMenu", "background-color", "Фон меню по правому щелчку"),
        ("Текст контекстного меню", "QMenu", "color", "Текст пунктов контекстного меню"),
        ("Выделенный пункт меню", "QMenu::item:selected", "background-color", "Фон пункта меню под курсором"),
        ("Текст выделенного пункта", "QMenu::item:selected", "color", "Текст пункта меню под курсором"),
        ("Рамка окна данных", "QTextEdit#outputText", "border", "Рамка вокруг окна принятых/отправленных данных"),
        ("Рамка поля ввода", "QLineEdit#textsend", "border", "Рамка строки ввода команды"),
        ("Рамка выпадающих списков", "QComboBox#Combo", "border", "Рамка закрытых выпадающих списков"),
        ("Рамка кнопок", "QPushButton", "border", "Рамка кнопок интерфейса"),
        ("Рамка панели данных", "QWidget#textContainer", "border", "Рамка панели с окном данных и номерами строк"),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Настройка оформления")
        self.resize(760, 760)
        self.setWindowIcon(QIcon(current_app_icon()))
        self.setWindowModality(Qt.WindowModality.NonModal)
        self.theme_manager = parent.theme_manager if parent and hasattr(parent, "theme_manager") else ThemeManager()
        self.themes = self.theme_manager.themes

        root = QVBoxLayout(self)
        top = QHBoxLayout()
        top.addWidget(QLabel("Тема:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(self.theme_manager.get_all_theme_names())

        # При открытии редактора сразу показываем тему, которая сейчас
        # действительно используется главным окном. Настройки приложения
        # являются источником истины, а ThemeManager хранит их актуальное состояние.
        active_theme = self.theme_manager.get_current_theme_name()
        if parent and hasattr(parent, "load_settings"):
            try:
                active_theme = parent.load_settings().get("theme", active_theme)
            except Exception:
                pass
        if active_theme not in self.theme_manager.themes:
            active_theme = "light"
        self.theme_combo.setCurrentText(active_theme)

        self.theme_combo.currentTextChanged.connect(self.load_theme_settings)
        top.addWidget(self.theme_combo, 1)
        self.create_button = QPushButton("Создать копию…")
        self.create_button.clicked.connect(self.create_new_theme)
        top.addWidget(self.create_button)
        root.addLayout(top)

        hint = QLabel(" ")
        hint.setWordWrap(True)
        root.addWidget(hint)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        self.content_layout = QVBoxLayout(content)
        self.color_buttons = []
        self._build_color_group("Окно и основные элементы", self.COLOR_ITEMS[:5])
        self._build_color_group("Ввод и отображение данных", self.COLOR_ITEMS[5:10])
        self._build_color_group("Выпадающие списки", self.COLOR_ITEMS[10:16])
        self._build_color_group("Контекстное меню", self.COLOR_ITEMS[16:20])
        self._build_color_group("Рамки элементов", self.COLOR_ITEMS[20:])
        self._build_message_colors()
        self._build_log_colors()
        self.content_layout.addStretch()
        scroll.setWidget(content)
        root.addWidget(scroll, 1)

        actions = QHBoxLayout()
        self.save_button = QPushButton("Сохранить тему")
        self.save_button.clicked.connect(self.save_theme)
        self.apply_button = QPushButton("Применить тему")
        self.apply_button.clicked.connect(self.apply_theme)
        self.reset_button = QPushButton("Сбросить цвета по умолчанию")
        self.reset_button.setToolTip("Восстановить исходные цвета выбранной стандартной темы")
        self.reset_button.clicked.connect(self.reset_default_theme)
        self.delete_button = QPushButton("Удалить тему")
        self.delete_button.clicked.connect(self.delete_theme)
        actions.addWidget(self.save_button)
        actions.addWidget(self.apply_button)
        actions.addWidget(self.reset_button)
        actions.addStretch()
        actions.addWidget(self.delete_button)
        root.addLayout(actions)
        self.load_theme_settings()

    def _build_color_group(self, title, items):
        group = QGroupBox(title)
        form = QFormLayout(group)
        for label, selector, prop, description in items:
            button = QPushButton(" ")
            button.setFixedSize(74, 30)
            button.setToolTip(description)
            button.clicked.connect(lambda checked=False, s=selector, p=prop, l=label: self.choose_style_color(s, p, l))
            form.addRow(QLabel(label + ":"), button)
            self.color_buttons.append((button, selector, prop))
        self.content_layout.addWidget(group)

    def _build_message_colors(self):
        group = QGroupBox("Цвета сообщений в окне данных")
        form = QFormLayout(group)
        self.message_color_buttons = []
        items = [
            ("Информационное сообщение", "info_color", "Зелёный/информационный тип (0x01)"),
            ("Предупреждение", "warning_color", "Предупреждающий тип (0x02)"),
            ("Ошибка", "error_color", "Сообщение об ошибке (0x03)"),
            ("Пользовательское сообщение", "custom_color", "Пользовательский тип (0x04)"),
        ]
        for label, key, tip in items:
            button = QPushButton(" "); button.setFixedSize(74, 30); button.setToolTip(tip)
            button.clicked.connect(lambda checked=False, k=key, l=label: self.choose_log_color(k, l))
            form.addRow(QLabel(label + ":"), button)
            self.message_color_buttons.append((button, key))
        self.content_layout.addWidget(group)

    def _build_log_colors(self):
        group = QGroupBox("Дополнительные цвета текста")
        form = QFormLayout(group)
        self.extra_color_buttons = []
        for label, key, tip in [
            ("Время получения сообщения", "default_timestamp_color", "Цвет временной отметки перед сообщением"),
            ("Отправленные данные", "default_sent_color", "Цвет текста, отправленного в COM-порт"),
            ("Отключённое состояние", "off_color", "Цвет индикации отключённого/неактивного состояния"),
        ]:
            button = QPushButton(" "); button.setFixedSize(74, 30); button.setToolTip(tip)
            button.clicked.connect(lambda checked=False, k=key, l=label: self.choose_extra_color(k, l))
            form.addRow(QLabel(label + ":"), button)
            self.extra_color_buttons.append((button, key))
        self.content_layout.addWidget(group)

    def _find_property(self, selector, prop):
        theme = self.theme_manager.get_theme(self.theme_combo.currentText())
        parsed = self.theme_manager.parse_stylesheet(theme.get("stylesheet", ""))
        for sel, properties in parsed:
            if sel.strip() == selector:
                for name, value in properties:
                    if name == prop:
                        if prop in ("border", "border-right"):
                            match = re.search(r"#[0-9a-fA-F]{3,8}|rgba?\([^)]*\)|\b(?:black|white|red|green|blue|gray|grey|transparent)\b", value, flags=re.I)
                            return QColor(match.group(0)) if match else QColor("#808080")
                        return QColor(value.strip())

        # Совместимость со старыми themes.json: раньше меню и раскрытый список
        # входили в общие группы селекторов, а отдельные правила ещё не существовали.
        legacy_selector = None
        legacy_prop = prop
        if selector == "QMenu":
            legacy_selector = "QMenu"
        elif selector == "QComboBox#Combo QAbstractItemView":
            legacy_selector = "QComboBox QAbstractItemView"
        elif selector == "QComboBox#Combo QAbstractItemView::item:selected":
            legacy_selector = "QComboBox QAbstractItemView"
            legacy_prop = "selection-background-color" if prop == "background-color" else "selection-color"
        if legacy_selector:
            for sel, properties in parsed:
                if legacy_selector in [part.strip() for part in sel.split(",")]:
                    for name, value in properties:
                        if name == legacy_prop:
                            return QColor(value.strip())
        return QColor("#808080")

    def _paint_button(self, button, color):
        qcolor = QColor(color)
        button.setStyleSheet(f"background-color: {qcolor.name()}; border: 1px solid #777; border-radius: 4px;")
        button.setText(qcolor.name())

    def load_theme_settings(self, *_):
        name = self.theme_combo.currentText()
        if not name:
            return
        theme = self.theme_manager.get_theme(name)
        self.reset_button.setVisible(name in DEFAULT_THEME)
        for button, selector, prop in self.color_buttons:
            self._paint_button(button, self._find_property(selector, prop))
        control = theme.setdefault("control_chars_colors", deepcopy(DEFAULT_THEME["light"]["control_chars_colors"]))
        for button, key in self.message_color_buttons:
            self._paint_button(button, control.get(key, "#808080"))
        for button, key in self.extra_color_buttons:
            self._paint_button(button, theme.get(key, "#808080"))
        self.apply_theme_to_dialog()

    def choose_style_color(self, selector, prop, label):
        current = self._find_property(selector, prop)
        color = QColorDialog.getColor(current, self, "Цвет: " + label)
        if color.isValid():
            self.theme_manager.update_stylesheet_property(self.theme_combo.currentText(), selector, prop, color.name())
            self.load_theme_settings()

    def choose_log_color(self, key, label):
        name = self.theme_combo.currentText()
        theme = self.theme_manager.get_theme(name)
        current = QColor(theme.setdefault("control_chars_colors", {}).get(key, "#808080"))
        color = QColorDialog.getColor(current, self, "Цвет: " + label)
        if color.isValid():
            theme["control_chars_colors"][key] = color.name()
            self.theme_manager.update_theme(name, theme)
            self.load_theme_settings()

    def choose_extra_color(self, key, label):
        name = self.theme_combo.currentText()
        theme = self.theme_manager.get_theme(name)
        color = QColorDialog.getColor(QColor(theme.get(key, "#808080")), self, "Цвет: " + label)
        if color.isValid():
            theme[key] = color.name()
            self.theme_manager.update_theme(name, theme)
            self.load_theme_settings()

    def create_new_theme(self):
        name, ok = QInputDialog.getText(self, "Новая тема", "Название новой темы:")
        name = name.strip()
        if not ok or not name:
            return
        if name in self.theme_manager.themes:
            QMessageBox.warning(self, "Тема существует", "Выберите другое название.")
            return
        base = self.theme_manager.get_theme(self.theme_combo.currentText())
        if self.theme_manager.add_theme(name, base):
            self.theme_combo.addItem(name)
            self.theme_combo.setCurrentText(name)
            self.load_theme_settings()

    def save_theme(self):
        name = self.theme_combo.currentText()
        self.theme_manager.save_themes()
        QMessageBox.information(self, "Сохранено", f"Тема «{name}» сохранена.")

    def apply_theme(self):
        name = self.theme_combo.currentText()
        self.theme_manager.set_theme(name)
        if self.parent() and hasattr(self.parent(), "save_settings"):
            self.parent().save_settings(theme=name)
            self.parent().apply_theme()
        self.apply_theme_to_dialog()

    def reset_default_theme(self):
        name = self.theme_combo.currentText()
        if name not in DEFAULT_THEME:
            return
        answer = QMessageBox.question(
            self,
            "Сброс стандартной темы",
            f"Восстановить исходные цвета темы «{name}»?\n\nВсе изменения этой темы будут заменены заводскими настройками.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if answer != QMessageBox.StandardButton.Yes:
            return

        # Восстанавливаем только выбранную стандартную тему, не затрагивая остальные.
        self.theme_manager.themes[name] = deepcopy(DEFAULT_THEME[name])
        self.theme_manager.save_themes()
        if name == self.theme_manager.get_current_theme_name():
            self.theme_manager.current_theme = self.theme_manager.themes[name]
            if self.parent() and hasattr(self.parent(), "apply_theme"):
                self.parent().apply_theme()
        self.load_theme_settings()
        QMessageBox.information(self, "Сброс выполнен", f"Тема «{name}» восстановлена к исходным цветам.")

    def delete_theme(self):
        name = self.theme_combo.currentText()
        if name in ("light", "retro", "dark", "duino", "ocean"):
            QMessageBox.warning(self, "Нельзя удалить", "Стандартные темы удалить нельзя.")
            return
        answer = QMessageBox.question(self, "Удаление темы", f"Удалить тему «{name}»?")
        if answer == QMessageBox.StandardButton.Yes and self.theme_manager.delete_theme(name):
            self.theme_combo.removeItem(self.theme_combo.currentIndex())
            self.load_theme_settings()

    def apply_theme_to_dialog(self):
        name = self.theme_combo.currentText()
        if not name:
            return
        font_size = 16
        if self.parent() and hasattr(self.parent(), "load_settings"):
            font_size = self.parent().load_settings().get("font_size", 16)
        self.setStyleSheet(self.theme_manager.get_stylesheet(theme_name=name, font_size=font_size, font_family="Consolas"))

class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("О программе")
        self.setMinimumSize(300, 200)
        self.setWindowIcon(QIcon(current_app_icon()))
        # Получаем дату последней модификации файла SMonic.py
        #        file_path = os.path.abspath(__file__)  # Путь к текущему файлу
        #        mod_time = os.path.getmtime(file_path)  # Время последней модификации в секундах




        #BUILD_DATE = datetime.fromtimestamp(mod_time).strftime("%d %B %Y")  # Форматируем дату, например: "08 April 2025"
        
        layout = QVBoxLayout()
        # Определяем путь к изображению в зависимости от темы
        settings = self.parent().load_settings()
        current_theme = settings.get("theme", "light")
        funSem = settings.get("make_Sem_fun", False)
      
        # Определяем путь к изображению и текст
        if funSem:
            image_path = character_image("icons/semona_fun.png")
            retro_text = ""
        else:
            image_path = character_image("icons/semona_fun.png" if current_theme == "retro" else "icons/semona.png")
            retro_text = "" if current_theme == "retro" else f"{NAME} любит Ретро!"

        # Основной текст с изображением и информацией
        main_label = QLabel(f"""
            <div style='text-align: center;'>
                <img src='{image_path}' width='115' height='115'><br><br>
                {NAME} - Serial Monitor<br>
                Версия: {VERSION}<br>
                Автор: Vanila<br>
                Дата сборки: {BUILD_DATE}<br>
                <a href='https://github.com/TonTon-Macout/Semona/'>GitHub</a>
            </div>
        """)
        main_label.setOpenExternalLinks(True)
        main_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(main_label)

        # Отдельный QLabel для текста с tooltip
        if retro_text:
            retro_label = QLabel(f"<div style='text-align: center;'>{retro_text}</div>")
            retro_label.setToolTip("Пустые сообщения в открытый порт сделают Семона снова весёлым")
            retro_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(retro_label)

        # Кнопка "Закрыть"
        close_button = QPushButton("Закрыть")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)
        
        self.setLayout(layout)
        self.apply_theme()

    def apply_theme(self):
        return
        settings = self.parent().load_settings()
       # if settings.get("theme") == "dark":
       #     self.setStyleSheet(self.parent().dark_theme_stylesheet())
       # else:
       #     self.setStyleSheet(self.parent().light_theme_stylesheet())


class RetroVibeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Сложный выбор")
        self.setMinimumSize(300, 150)
        self.setWindowIcon(QIcon(current_app_icon()))

        layout = QVBoxLayout()

        # Лейбл с изображением
        screen = QApplication.primaryScreen()
        device_pixel_ratio = screen.devicePixelRatio() or 1.0
        width  = int(115 / device_pixel_ratio)
        height = int(115 / device_pixel_ratio)
        self.label = QLabel(f"""
            <div style='text-align: center;'>
                <h1>РЕТРО ВАЙБ?</h1>     <br>
                <img src='{character_image('icons/semona_fun.png')}' width='{width}' height='{height}'><br><br>
                {NAME} - Serial Monitor<br>
                Версия: {VERSION}<br><br>
            </div>
        """)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label)

        buttons_layout = QHBoxLayout()

        # Кнопка "ЕСТЕСТВЕННО!"
        self.yes_button = QPushButton("ЕСТЕСТВЕННО!")
        self.yes_button.setStyleSheet("background-color: #4A90E2; color: white; border-radius: 14px; height: 30px; ")
        self.yes_button.clicked.connect(self.create_retro_files)
        self.yes_button.enterEvent = lambda event: self.change_label_image(character_image("icons/semona_fun.png"))
        self.yes_button.leaveEvent = lambda event: self.reset_label_image()
        buttons_layout.addWidget(self.yes_button)

        # Кнопка "НИВКОЕМСЛУЧАЕ!"
        self.no_button = QPushButton("=(")
        self.no_button.setStyleSheet("background-color: #E74C3C; color: white; border-radius: 14px; max-width: 50px; height: 30px;")
        self.no_button.clicked.connect(self.create_default_files)
        self.no_button.enterEvent = lambda event: self.change_label_image(character_image("icons/semona.png"))
        self.no_button.leaveEvent = lambda event: self.reset_label_image()
        buttons_layout.addWidget(self.no_button)

        layout.addLayout(buttons_layout)
      
        self.setLayout(layout)
        
   
    def change_label_image(self, image_path):
        image_path = character_image(image_path)
        screen = QApplication.primaryScreen()
        device_pixel_ratio = screen.devicePixelRatio() or 1.0
        width  = int(115 / device_pixel_ratio)
        height = int(115 / device_pixel_ratio)
        self.label.setText(f"""
            <div style='text-align: center;'>
                <h1>РЕТРО ВАЙБ?</h1>     <br>
                <img src='{image_path}'  width='{width}' height='{height}' ><br><br>
                {NAME} - Serial Monitor<br>
                Версия: {VERSION}<br><br>
            </div>
        """)

    def reset_label_image(self):
        screen = QApplication.primaryScreen()
        device_pixel_ratio = screen.devicePixelRatio() or 1.0
        width  = int(115 / device_pixel_ratio)
        height = int(115 / device_pixel_ratio)
        self.label.setText(f"""
            <div style='text-align: center;'>
                <h1>РЕТРО ВАЙБ?</h1>     <br>
                <img src='{character_image('icons/semona_fun.png')}'  width='{width}' height='{height}'><br><br>
                {NAME} - Serial Monitor<br>
                Версия: {VERSION}<br><br>
            </div>
        """)

    def create_retro_files(self):
        self.parent().create_settings_file(retro=True)
        self.parent().create_themes_file(retro=True)
        self.parent().apply_theme()
        self.accept()

    def create_default_files(self):
        self.parent().create_settings_file(retro=False)
        self.parent().create_themes_file(retro=False)
        self.parent().apply_theme()
        self.accept()



class CustomSplashScreen(QWidget):
    def __init__(self, pixmap, text, parent=None):
        super().__init__(parent)
        self.monitor = None  # Будет установлен позже
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Масштабируем изображение
        screen = QApplication.primaryScreen()
        scale_factor = screen.devicePixelRatio() or 1.0
        
        scaled_pixmap = pixmap.scaled(
            int(180),
            int(162),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        scaled_pixmap.setDevicePixelRatio(scale_factor)

        # Добавляем изображение
        self.label_image = QLabel(self)
        self.label_image.setPixmap(scaled_pixmap)
        self.label_image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label_image)

        # Добавляем текст
        self.label_text = QLabel(text, self)
        self.label_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        font_size = int(24 * scale_factor)
        self.label_text.setStyleSheet(f"""
            color: #ffd7aa;
            font-size: {font_size}px;
            font-family: Consolas;
            font-weight: bold;
            padding: 0px;
            margin-left: -25px;
        """)
        
        # Добавляем эффект тени
        shadow_effect = QGraphicsDropShadowEffect(self)
        shadow_effect.setBlurRadius(20)
        shadow_effect.setColor(QColor(69, 128, 121, 250))
        shadow_effect.setOffset(0, 0)
        self.label_text.setGraphicsEffect(shadow_effect)
        layout.addWidget(self.label_text)

        self.setLayout(layout)
        QTimer.singleShot(0, self.center_on_screen)

    def center_on_screen(self):
        screen = QApplication.primaryScreen().availableGeometry()
        self.adjustSize()
        size = self.size()
        x = (screen.width() - size.width()) // 2 + screen.x()
        y = (screen.height() - size.height()) // 2 + screen.y()
        self.move(x, y)

    def showMessage(self, text):
        self.label_text.setText(text)

    def start_version_check(self, monitor):
        self.monitor = monitor
        self.showMessage(f"{NAME}\nПроверка обновлений...")

        # Запускаем таймер на 5 секунд
        self.timeout_timer = QTimer(self)
        self.timeout_timer.setSingleShot(True)
        self.timeout_timer.timeout.connect(self.finish_version_check)
        self.timeout_timer.start(5000)  # 5000 мс = 5 секунд

        # Выполняем синхронную проверку версии
        self.check_latest_version()

    def check_latest_version(self):
        latest_version = None
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            response = requests.get(
                f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest",
                headers=headers,
                timeout=2
            )
            response.raise_for_status()
            data = response.json()
            latest_version = data["tag_name"].lstrip("v")
            if latest_version != VERSION:
                self.monitor.update_available = True
                self.monitor.latest_version = latest_version
                message = f"Доступна новая версия: {latest_version}"
            else:
                message = f"Нет обновлений, версия: {VERSION}"
        except requests.exceptions.RequestException as e:
            message = f"Ошибка проверки обновления: {e}"

        # Обновляем сообщение на сплэш-скрине
        self.showMessage(f"{NAME}\n{message}")

        # Логируем в debug-режиме
        settings = self.monitor.load_settings()
        if settings.get("debug", False):
            self.monitor.append_colored_text(f'[debug] {message}', self.monitor.message_info, True, False)

        # Останавливаем таймер и завершаем проверку
        if self.timeout_timer.isActive():
            self.timeout_timer.stop()
        self.finish_version_check()

    def finish_version_check(self):
        # Закрываем сплэш-скрин и показываем основное окно
        self.close()
        self.monitor.show()



if __name__ == '__main__':
    if current_character_is_male():
        NAME = "SEMÖN"
    print(f" {NAME} {VERSION}")


    app = QApplication(sys.argv)
    #app.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
 

    # Создаем сплэш-скрин
    splash_pix = QPixmap(current_app_logo())
    
    splash_text = f"{NAME}"
    splash = CustomSplashScreen(splash_pix, splash_text)
    splash.show()
    # Обновляем события, чтобы сплэш-скрин отобразился
    app.processEvents()

    # Создаем основное окно
    window = SerialMonitor(splash=splash)

    # Запускаем проверку версии
    splash.start_version_check(window)

    sys.exit(app.exec())