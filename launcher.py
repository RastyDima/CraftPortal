import customtkinter as ctk
import minecraft_launcher_lib
import subprocess
import os
import json
import requests
import traceback
import shutil
import time
import tempfile
import urllib.request
import sys
from threading import Thread, Semaphore
from tkinter import messagebox, filedialog
from PIL import Image
from io import BytesIO
from datetime import datetime

# Firebase Admin SDK
try:
    import firebase_admin
    from firebase_admin import credentials, db as firebase_db, auth as firebase_auth
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False
    print("firebase-admin не установлен. Установите: pip install firebase-admin")

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Цвета Velox
CP_BLUE       = "#1e6fbb"
CP_BLUE_HOVER = "#2980d4"
CP_BLUE_DARK  = "#144f8a"
CP_ACCENT     = "#00b4fc"
CP_BG_CARD    = "#1a2233"
CP_BG_PANEL   = "#151c2b"

# Firebase конфигурация
FIREBASE_SERVICE_ACCOUNT = "minecraftlauncher-9189c-firebase-adminsdk-fbsvc-bcb1e87988.json"
FIREBASE_DATABASE_URL = "https://minecraftlauncher-9189c-default-rtdb.firebaseio.com"

CONFIG_FILE = "launcher_config.json"
PROFILES_FILE = "profiles.json"
FRIENDS_FILE = "friends.json"
STATS_FILE = "stats.json"
VERSION_CACHE_FILE = "version_cache.json"
CACHE_MAX_AGE = 24 * 3600  # 24 часа

# URL для проверки обновлений (замените на свой)
UPDATE_URL = "https://raw.githubusercontent.com/username/launcher/main/version.json"

# История версий лаунчера
LAUNCHER_VERSIONS = [
    {
        "version": "1.4.0",
        "date": "2026-03-08",
        "changes": [
            "💬 Чат с друзьями через Firebase Realtime Database",
            "🗨️ Пузырьки сообщений в стиле мессенджера",
            "🔄 Автообновление сообщений каждые 5 секунд",
            "📬 Кнопка чата прямо на карточке друга"
        ]
    },
    {
        "version": "1.3.0",
        "date": "2026-03-08",
        "changes": [
            "🎨 Официальное название: Velox",
            "💙 Новая синяя цветовая схема интерфейса",
            "🏷️ Шапка с логотипом Velox и статусом аккаунта",
            "▶️ Крупная стильная кнопка ИГРАТЬ",
            "🃏 Карточный дизайн панелей",
            "✨ Улучшены отступы, размеры и иконки вкладок"
        ]
    },
    {
        "version": "1.2.1",
        "date": "2026-03-08",
        "changes": [
            "💾 Автосохранение аккаунта Firebase между сессиями",
            "🔄 Автоматический вход при запуске лаунчера",
            "🚪 Выход из аккаунта очищает сохранённые данные"
        ]
    },
    {
        "version": "1.2.0",
        "date": "2026-03-07",
        "changes": [
            "🔥 Система друзей переведена на Firebase",
            "🔐 Регистрация и вход по email/пароль через Firebase Auth",
            "🟢 Реальный статус онлайн через Firebase Realtime Database",
            "📨 Отправка и принятие заявок в друзья",
            "🔔 Обновление списка друзей в реальном времени"
        ]
    },
    {
        "version": "1.1.0",
        "date": "2026-03-05",
        "changes": [
            "🚀 Добавлено автоматическое обновление",
            "⚡ Оптимизация загрузки иконок",
            "🐛 Мелкие исправления"
        ]
    },
    {
        "version": "1.0.1",
        "date": "2026-03-05",
        "changes": [
            "⚡ Кэширование списка версий Minecraft (загрузка раз в сутки)",
            "⚙️ Оптимизация обновлений интерфейса (after_idle)",
            "📦 Ограничение одновременных загрузок иконок",
            "🐛 Мелкие исправления и улучшения стабильности"
        ]
    },
    {
        "version": "1.0.0",
        "date": "2026-03-05",
        "changes": [
            "👥 Добавлена система друзей",
            "🟢 Видно, кто сейчас в сети",
            "🕒 Отображается время последнего визита",
            "🎨 Небольшие улучшения интерфейса"
        ]
    },
    {
        "version": "0.9.9_2",
        "date": "2026-03-04",
        "changes": [
            "📁 Кнопки открытия папок в настройках",
            "🎨 Переключение тем оформления (светлая/тёмная/системная)",
            "✅ Множественное удаление модов (чекбоксы)",
            "🔄 Включение/выключение модов (переименование .jar.disabled)",
            "⚙️ Мелкие исправления и оптимизация"
        ]
    },
    {
        "version": "0.9.9",
        "date": "2026-03-04",
        "changes": [
            "📊 Добавлена вкладка 'Статистика'",
            "⏱️ Отслеживается время игры за 7 дней, 30 дней и всё время"
        ]
    },
    {
        "version": "0.9.8",
        "date": "2026-03-04",
        "changes": [
            "➕ В результатах поиска модов и ресурспаков отображаются поддерживаемые версии Minecraft",
            "📋 Список версий показывается под описанием"
        ]
    },
    {
        "version": "0.9.7",
        "date": "2026-03-04",
        "changes": [
            "➕ Добавлен фильтр по версии игры для поиска модов и ресурспаков",
            "📋 Выбор версии при установке сохранён",
            "🐛 Исправлена совместимость поиска для версии 1.12.2"
        ]
    },
    {
        "version": "0.9.6",
        "date": "2026-03-04",
        "changes": [
            "🎨 Добавлена вкладка 'Ресурспаки'",
            "📦 Поиск и установка ресурспаков с Modrinth",
            "🔄 Включение/выключение ресурспаков (переименование .disabled)",
            "📂 Загрузка ресурспаков с компьютера"
        ]
    },
    {
        "version": "0.9.5",
        "date": "2026-03-04",
        "changes": [
            "📦 Улучшен дизайн списка установленных модов",
            "🖼️ Карточки с иконками и кнопкой удаления"
        ]
    },
    {
        "version": "0.9.4",
        "date": "2026-03-04",
        "changes": [
            "📜 Добавлена подробная информация о версиях Minecraft",
            "📋 Теперь для каждой версии показана дата выхода и список изменений"
        ]
    },
    {
        "version": "0.9.3",
        "date": "2026-03-04",
        "changes": [
            "➕ Добавлена информация о версиях Minecraft во вкладку 'Новости'",
            "📋 Теперь можно посмотреть краткие изменения для каждой версии",
            "🔄 Исправлена сортировка версий (новые сверху)",
            "📜 Добавлен прокручиваемый список всех версий"
        ]
    },
    {
        "version": "0.9.2",
        "date": "2026-03-04",
        "changes": [
            "➕ Добавлена вкладка 'Новости'",
            "🔄 Отображение последних версий Minecraft",
            "📜 История обновлений лаунчера"
        ]
    },
    {
        "version": "0.9.1",
        "date": "2026-03-03",
        "changes": [
            "🐛 Исправлена ошибка загрузки версий",
            "✨ Улучшена стабильность"
        ]
    },
    {
        "version": "0.9.0",
        "date": "2026-03-01",
        "changes": [
            "🚀 Первый релиз лаунчера",
            "📦 Установка Forge/Fabric/Quilt",
            "🔍 Поиск модов с Modrinth",
            "👤 Профили пользователей"
        ]
    }
]

# Краткая информация о версиях Minecraft
def _mc(date, name="", changes=()):
    """Вспомогательная функция для краткого описания версии"""
    lines = [f"Дата выхода: {date}"]
    if name:
        lines.append(f"Название: {name}")
    if changes:
        lines.append("\nИзменения:")
        for c in changes:
            lines.append(f"• {c}")
    return "\n".join(lines)

MINECRAFT_VERSION_INFO = {
    # ── 1.21.x ──
    "1.21.4": _mc("3 декабря 2024",    "",               ("Новые варианты испытаний в Trial Chambers", "Улучшена производительность в лесных биомах", "Исправления ошибок")),
    "1.21.3": _mc("22 октября 2024",   "",               ("Поддержка новых блоков в командных блоках", "Улучшена работа редстоуна")),
    "1.21.2": _mc("10 сентября 2024",  "",               ("Оптимизирована генерация структур", "Улучшена работа с памятью")),
    "1.21.1": _mc("20 августа 2024",   "",               ("Небольшие исправления после 1.21",)),
    "1.21":   _mc("13 июня 2024",      "Tricky Trials",  ("Trial Chambers — новые структуры", "Новые мобы: Breeze, Bogged", "Медный блок гонга, новые предметы")),
    # ── 1.20.x ──
    "1.20.6": _mc("29 апреля 2024",    "",               ("Исправления безопасности и ошибок",)),
    "1.20.5": _mc("23 апреля 2024",    "",               ("Оптимизация производительности",)),
    "1.20.4": _mc("7 декабря 2023",    "",               ("Исправления стабильности",)),
    "1.20.3": _mc("5 декабря 2023",    "",               ("Оптимизация рендеринга", "Исправления ошибок")),
    "1.20.2": _mc("21 сентября 2023",  "",               ("Новые функции командных блоков", "Улучшена система крафта")),
    "1.20.1": _mc("12 июля 2023",      "",               ("Небольшие исправления после 1.20",)),
    "1.20":   _mc("7 июня 2023",       "Trails & Tales", ("Археология — раскопки и черепки", "Новые мобы: верблюд, броненосец", "Вишнёвая роща, бамбуковые блоки", "Снаряжение для персонажа")),
    # ── 1.19.x ──
    "1.19.4": _mc("14 марта 2023",     "",               ("Исправления ошибок и улучшения",)),
    "1.19.3": _mc("7 декабря 2022",    "",               ("Новые команды", "Улучшена система мобов")),
    "1.19.2": _mc("5 августа 2022",    "",               ("Исправления ошибок",)),
    "1.19.1": _mc("27 июля 2022",      "",               ("Небольшие исправления",)),
    "1.19":   _mc("7 июня 2022",       "The Wild",       ("Тёмные глубины — новый биом", "Хранитель — самый страшный моб", "Мангровые болота, блоки сколка", "Лягушки и головастики")),
    # ── 1.18.x ──
    "1.18.2": _mc("28 февраля 2022",   "",               ("Исправления ошибок",)),
    "1.18.1": _mc("10 декабря 2021",   "",               ("Небольшие исправления",)),
    "1.18":   _mc("30 ноября 2021",    "Caves & Cliffs II", ("Переработана генерация пещер и гор", "Новые биомы пещер: капельниковые, лавовые", "Горные биомы: заснеженные склоны, пики")),
    # ── 1.17.x ──
    "1.17.1": _mc("6 июля 2021",       "",               ("Исправления ошибок",)),
    "1.17":   _mc("8 июня 2021",       "Caves & Cliffs I", ("Аксолотли, светящиеся кальмары", "Козлы", "Блоки меди и аметиста", "Подзорная труба")),
    # ── 1.16.x ──
    "1.16.5": _mc("15 января 2021",    "",               ("Исправления ошибок",)),
    "1.16.4": _mc("3 ноября 2020",     "",               ("Небольшие исправления",)),
    "1.16.3": _mc("10 сентября 2020",  "",               ("Исправления ошибок",)),
    "1.16.2": _mc("11 августа 2020",   "",               ("Пиглины-бруты", "Незерит — новый материал")),
    "1.16.1": _mc("24 июня 2020",      "",               ("Исправления ошибок",)),
    "1.16":   _mc("23 июня 2020",      "Nether Update",  ("Переработан Нижний мир", "Новые биомы: малиновый лес, базальтовые дельты", "Пиглины, хоглины, страйдеры", "Незерит")),
    # ── 1.15.x ──
    "1.15.2": _mc("21 января 2020",    "",               ("Исправления ошибок",)),
    "1.15.1": _mc("17 декабря 2019",   "",               ("Небольшие исправления",)),
    "1.15":   _mc("10 декабря 2019",   "Buzzy Bees",     ("Пчёлы и ульи", "Мёд и соты", "Новые блоки улья")),
    # ── 1.14.x ──
    "1.14.4": _mc("19 июля 2019",      "",               ("Исправления ошибок",)),
    "1.14.3": _mc("24 июня 2019",      "",               ("Исправления производительности",)),
    "1.14.2": _mc("13 июня 2019",      "",               ("Исправления ошибок",)),
    "1.14.1": _mc("13 мая 2019",       "",               ("Небольшие исправления",)),
    "1.14":   _mc("23 апреля 2019",    "Village & Pillage", ("Переработаны деревни и жители", "Разбойники, мародёры", "Новые блоки: леса, строительные плиты", "Кузнец, каменщик, картограф")),
    # ── 1.13.x ──
    "1.13.2": _mc("22 октября 2018",   "",               ("Исправления ошибок",)),
    "1.13.1": _mc("22 августа 2018",   "",               ("Исправления ошибок",)),
    "1.13":   _mc("18 июля 2018",      "Update Aquatic", ("Полностью переработан океан", "Дельфины, черепахи, рыбы", "Трезубец и новые зелья", "Затонувшие корабли, подводные руины")),
    # ── 1.12.x ──
    "1.12.2": _mc("18 сентября 2017",  "",               ("Исправления ошибок",)),
    "1.12.1": _mc("28 августа 2017",   "",               ("Небольшие исправления",)),
    "1.12":   _mc("7 июня 2017",       "World of Color", ("12 цветов бетона и глазури", "Попугаи", "Рецептная книга", "Достижения заменены на прогресс")),
    # ── 1.11.x ──
    "1.11.2": _mc("21 декабря 2016",   "",               ("Исправления ошибок",)),
    "1.11.1": _mc("20 декабря 2016",   "",               ("Небольшие исправления",)),
    "1.11":   _mc("14 ноября 2016",    "Exploration Update", ("Картографы и карты сокровищ", "Иллюзионисты, VEX", "Шалкеровые ящики, наблюдатели")),
    # ── 1.10.x ──
    "1.10.2": _mc("26 июня 2016",      "",               ("Исправления ошибок",)),
    "1.10.1": _mc("22 июня 2016",      "",               ("Небольшие исправления",)),
    "1.10":   _mc("26 июня 2016",      "Frostburn Update", ("Белые медведи, магмовые кубы в нижнем мире", "Окаменелости, авто-прыжок", "Новые блоки незера")),
    # ── 1.9.x ──
    "1.9.4":  _mc("10 мая 2016",       "",               ("Исправления ошибок",)),
    "1.9.2":  _mc("30 марта 2016",     "",               ("Небольшие исправления",)),
    "1.9":    _mc("29 февраля 2016",   "Combat Update",  ("Система двух рук", "Перезарядка оружия", "Крылья — элитры", "Города конца, драконьи врата")),
    # ── 1.8.x ──
    "1.8.9":  _mc("9 декабря 2015",    "",               ("Исправления ошибок",)),
    "1.8.8":  _mc("28 июля 2015",      "",               ("Исправления безопасности",)),
    "1.8":    _mc("2 сентября 2014",   "Bountiful Update", ("Кролики, стражи, скакуны", "Морские биомы", "Баннеры, двери из разного дерева", "Спектральные стрелы")),
    # ── 1.7.x ──
    "1.7.10": _mc("26 июня 2014",      "",               ("Исправления ошибок",)),
    "1.7.9":  _mc("9 апреля 2014",     "",               ("Исправления безопасности",)),
    "1.7.2":  _mc("25 октября 2013",   "The Update that Changed the World", ("18 новых биомов", "Новые цветы и деревья", "Рыбалка улучшена", "Аналитика биомов")),
    # ── 1.6.x ──
    "1.6.4":  _mc("19 сентября 2013",  "",               ("Исправления ошибок",)),
    "1.6.2":  _mc("8 июля 2013",       "",               ("Небольшие исправления",)),
    "1.6.1":  _mc("1 июля 2013",       "Horse Update",   ("Лошади, мулы, ослы", "Поводок", "Угольный блок", "Ресурспаки заменили текстурпаки")),
    # ── 1.5.x ──
    "1.5.2":  _mc("25 апреля 2013",    "",               ("Исправления ошибок",)),
    "1.5.1":  _mc("21 марта 2013",     "",               ("Небольшие исправления",)),
    "1.5":    _mc("13 марта 2013",     "Redstone Update", ("Блок редстоуна", "Компаратор", "Воронка, дроппер", "Нетерпящий блок, пружинная плита")),
    # ── 1.4.x ──
    "1.4.7":  _mc("9 января 2013",     "",               ("Исправления ошибок",)),
    "1.4.6":  _mc("20 декабря 2012",   "",               ("Небольшие исправления",)),
    "1.4.2":  _mc("25 октября 2012",   "Pretty Scary Update", ("Нежить: зомби-деревня, скелеты-иссушители", "Маяки", "Морковь, картофель, тыквенный пирог", "Голова моба как блок")),
    # ── 1.3.x ──
    "1.3.2":  _mc("16 августа 2012",   "",               ("Исправления ошибок",)),
    "1.3.1":  _mc("1 августа 2012",    "",               ("Объединены однопользовательский и многопользовательский код", "Торговля с жителями", "Храмы в пустыне и джунглях", "Книга и перо")),
    # ── 1.2.x ──
    "1.2.5":  _mc("4 апреля 2012",     "",               ("Исправления ошибок",)),
    "1.2.4":  _mc("22 марта 2012",     "",               ("Небольшие исправления",)),
    "1.2.1":  _mc("1 марта 2012",      "",               ("Джунглевый биом", "Оцелоты и кошки", "Железные големы", "Новые деревянные блоки")),
    # ── 1.1 ──
    "1.1":    _mc("12 января 2012",    "",               ("Новые языки", "Зачарования в книгах", "Спаун мобов в биомах")),
    # ── 1.0.0 ──
    "1.0.0":  _mc("18 ноября 2011",    "Полный релиз",   ("Первый официальный релиз", "Иссушитель и иссушение", "Зачарования и варка зелий", "Конец — финальный биом с эндер-драконом")),
}

class Updater:
    """Проверка и установка обновлений"""
    def __init__(self, current_version, update_url):
        self.current_version = current_version
        self.update_url = update_url
        self.update_info = None

    def check_for_updates(self):
        try:
            with urllib.request.urlopen(self.update_url, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
                # Сравниваем версии (простейшее строковое сравнение, можно улучшить)
                if data["version"] > self.current_version:
                    self.update_info = data
                    return True
        except Exception as e:
            print(f"Ошибка проверки обновлений: {e}")
        return False

    def download_update(self, dest_path):
        try:
            urllib.request.urlretrieve(self.update_info["download_url"], dest_path)
            return True
        except Exception as e:
            print(f"Ошибка загрузки: {e}")
            return False

    def apply_update(self, new_exe_path):
        # Создаём batch-скрипт для замены и перезапуска
        script = f'''@echo off
timeout /t 1 /nobreak >nul
del /f /q "{sys.argv[0]}"
copy /y "{new_exe_path}" "{sys.argv[0]}"
start "" "{sys.argv[0]}"
del /f /q "{new_exe_path}"
'''
        script_path = os.path.join(os.path.dirname(sys.argv[0]), "update.bat")
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(script)
        subprocess.Popen([script_path], shell=True)
        sys.exit(0)

class StatsManager:
    """Управление статистикой игрового времени"""
    def __init__(self, stats_file):
        self.stats_file = stats_file
        self.data = self.load()

    def load(self):
        if os.path.exists(self.stats_file):
            try:
                with open(self.stats_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                return {"sessions": []}
        return {"sessions": []}

    def save(self):
        with open(self.stats_file, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=4)

    def add_session(self, start_time, end_time):
        duration = int(end_time - start_time)
        self.data["sessions"].append({
            "start": start_time,
            "end": end_time,
            "duration": duration
        })
        self.save()

    def get_total_time(self, days=None):
        now = time.time()
        total = 0
        for session in self.data["sessions"]:
            if days is not None:
                if session["start"] < now - days * 24 * 3600:
                    continue
            total += session["duration"]
        return total

    def format_time(self, seconds):
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        if hours > 0:
            return f"{hours} ч {minutes} мин"
        else:
            return f"{minutes} мин"

    def clear(self):
        self.data["sessions"] = []
        self.save()

class FirebaseManager:
    """Управление Firebase Auth и Realtime Database"""

    def __init__(self):
        self.app = None
        self.current_uid = None
        self.current_username = None
        self.current_email = None
        self.api_key = "AIzaSyBzozXlLemvqCFaoJJ_aK_D2Eh9OKI54r8"
        self._online_listener = None
        self._initialized = False
        # НЕ вызываем _init_firebase здесь — вызывается в фоновом потоке из лаунчера

    def _init_firebase(self):
        if not FIREBASE_AVAILABLE:
            return
        try:
            sa_path = FIREBASE_SERVICE_ACCOUNT
            if not os.path.exists(sa_path):
                sa_path = os.path.join(os.path.dirname(sys.argv[0]), FIREBASE_SERVICE_ACCOUNT)
            if not os.path.exists(sa_path):
                print(f"Service account файл не найден: {FIREBASE_SERVICE_ACCOUNT}")
                return
            if not firebase_admin._apps:
                cred = credentials.Certificate(sa_path)
                firebase_admin.initialize_app(cred, {"databaseURL": FIREBASE_DATABASE_URL})
            self._initialized = True
            print("Firebase инициализирован успешно")
        except Exception as e:
            print(f"Ошибка инициализации Firebase: {e}")

    @property
    def is_logged_in(self):
        return self.current_uid is not None

    # ---------- Auth через REST API ----------
    def register(self, email, password, username):
        """Регистрация нового пользователя"""
        try:
            # Создаём пользователя через Firebase Auth REST API
            url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={self.api_key}"
            resp = requests.post(url, json={"email": email, "password": password, "returnSecureToken": True}, timeout=10)
            data = resp.json()
            if "error" in data:
                return False, data["error"].get("message", "Ошибка регистрации")

            uid = data["localId"]
            id_token = data["idToken"]

            # Проверяем уникальность никнейма
            existing = firebase_db.reference(f"users").order_by_child("username").equal_to(username).get()
            if existing:
                # Удаляем только что созданный аккаунт
                try:
                    firebase_auth.delete_user(uid)
                except:
                    pass
                return False, "Этот никнейм уже занят"

            # Сохраняем профиль в Realtime DB
            firebase_db.reference(f"users/{uid}").set({
                "username": username,
                "email": email,
                "online": False,
                "last_seen": 0,
                "created_at": time.time()
            })

            self.current_uid = uid
            self.current_username = username
            self.current_email = email
            self._set_online(True)
            return True, "Регистрация успешна"
        except Exception as e:
            return False, str(e)

    def login(self, email, password):
        """Вход по email/пароль"""
        try:
            url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={self.api_key}"
            resp = requests.post(url, json={"email": email, "password": password, "returnSecureToken": True}, timeout=10)
            data = resp.json()
            if "error" in data:
                msg = data["error"].get("message", "Ошибка входа")
                if msg == "INVALID_PASSWORD":
                    msg = "Неверный пароль"
                elif msg == "EMAIL_NOT_FOUND":
                    msg = "Email не найден"
                elif "TOO_MANY_ATTEMPTS" in msg:
                    msg = "Слишком много попыток, попробуйте позже"
                return False, msg

            uid = data["localId"]
            # Получаем данные профиля
            user_data = firebase_db.reference(f"users/{uid}").get()
            if not user_data:
                return False, "Профиль не найден в базе данных"

            self.current_uid = uid
            self.current_username = user_data.get("username", email)
            self.current_email = email
            self._set_online(True)
            return True, "Вход выполнен"
        except Exception as e:
            return False, str(e)

    def logout(self):
        if self.current_uid:
            self._set_online(False)
        self.current_uid = None
        self.current_username = None
        self.current_email = None

    def _set_online(self, status: bool):
        if not self._initialized or not self.current_uid:
            return
        try:
            firebase_db.reference(f"users/{self.current_uid}").update({
                "online": status,
                "last_seen": time.time()
            })
        except Exception as e:
            print(f"Ошибка обновления статуса онлайн: {e}")

    def keep_online(self):
        """Периодически обновляет статус онлайн (вызывать каждые 30 сек)"""
        if self.is_logged_in:
            self._set_online(True)

    # ---------- Поиск пользователей ----------
    def find_user_by_username(self, username):
        """Поиск пользователя по никнейму, возвращает (uid, data) или None"""
        try:
            result = firebase_db.reference("users").order_by_child("username").equal_to(username).get()
            if result:
                uid = list(result.keys())[0]
                return uid, result[uid]
            return None
        except Exception as e:
            print(f"Ошибка поиска пользователя: {e}")
            return None

    # ---------- Заявки в друзья ----------
    def send_friend_request(self, to_username):
        """Отправить заявку в друзья"""
        if not self.is_logged_in:
            return False, "Вы не авторизованы"
        if to_username == self.current_username:
            return False, "Нельзя добавить себя в друзья"

        found = self.find_user_by_username(to_username)
        if not found:
            return False, f"Пользователь '{to_username}' не найден"
        to_uid, _ = found

        # Проверяем, уже ли друзья
        existing = firebase_db.reference(f"friends/{self.current_uid}/{to_uid}").get()
        if existing and existing.get("status") == "accepted":
            return False, "Этот пользователь уже у вас в друзьях"

        # Проверяем, не отправлена ли уже заявка
        pending = firebase_db.reference(f"friend_requests/{to_uid}/{self.current_uid}").get()
        if pending:
            return False, "Заявка уже отправлена"

        # Создаём заявку
        firebase_db.reference(f"friend_requests/{to_uid}/{self.current_uid}").set({
            "from_username": self.current_username,
            "timestamp": time.time(),
            "status": "pending"
        })
        return True, f"Заявка отправлена пользователю {to_username}"

    def get_incoming_requests(self):
        """Получить входящие заявки в друзья"""
        if not self.is_logged_in:
            return {}
        try:
            reqs = firebase_db.reference(f"friend_requests/{self.current_uid}").get()
            return reqs or {}
        except:
            return {}

    def accept_friend_request(self, from_uid):
        """Принять заявку в друзья"""
        try:
            req_data = firebase_db.reference(f"friend_requests/{self.current_uid}/{from_uid}").get()
            if not req_data:
                return False, "Заявка не найдена"

            from_username = req_data.get("from_username", "")
            now = time.time()

            # Добавляем в друзья с обеих сторон
            firebase_db.reference(f"friends/{self.current_uid}/{from_uid}").set({
                "username": from_username,
                "status": "accepted",
                "since": now
            })
            firebase_db.reference(f"friends/{from_uid}/{self.current_uid}").set({
                "username": self.current_username,
                "status": "accepted",
                "since": now
            })

            # Удаляем заявку
            firebase_db.reference(f"friend_requests/{self.current_uid}/{from_uid}").delete()
            return True, f"Вы теперь друзья с {from_username}"
        except Exception as e:
            return False, str(e)

    def decline_friend_request(self, from_uid):
        """Отклонить заявку"""
        try:
            firebase_db.reference(f"friend_requests/{self.current_uid}/{from_uid}").delete()
            return True, "Заявка отклонена"
        except Exception as e:
            return False, str(e)

    def remove_friend(self, friend_uid):
        """Удалить из друзей"""
        try:
            firebase_db.reference(f"friends/{self.current_uid}/{friend_uid}").delete()
            firebase_db.reference(f"friends/{friend_uid}/{self.current_uid}").delete()
            return True, "Друг удалён"
        except Exception as e:
            return False, str(e)

    def get_friends(self):
        """Получить список друзей с их данными"""
        if not self.is_logged_in:
            return {}
        try:
            friends = firebase_db.reference(f"friends/{self.current_uid}").get()
            if not friends:
                return {}
            # Получаем актуальный статус для каждого друга
            result = {}
            for uid, fdata in friends.items():
                user_data = firebase_db.reference(f"users/{uid}").get()
                if user_data:
                    result[uid] = {
                        "username": fdata.get("username", ""),
                        "online": user_data.get("online", False),
                        "last_seen": user_data.get("last_seen", 0),
                        "since": fdata.get("since", 0),
                        "status": user_data.get("status", "online"),
                    }
            return result
        except Exception as e:
            print(f"Ошибка получения друзей: {e}")
            return {}

    def format_last_seen(self, last_seen, online):
        if online:
            return "🟢 В сети"
        if not last_seen:
            return "⚪ Никогда не заходил(а)"
        dt = datetime.fromtimestamp(last_seen)
        now = datetime.now()
        delta = now - dt
        if delta.days == 0:
            if delta.seconds < 60:
                return "🔵 Только что был(а)"
            elif delta.seconds < 3600:
                return f"🔵 Был(а) {delta.seconds // 60} мин назад"
            else:
                return f"🔵 Был(а) {delta.seconds // 3600} ч назад"
        elif delta.days == 1:
            return "⚫ Был(а) вчера"
        else:
            return f"⚫ Был(а) {delta.days} дн назад"

    # ---------- Чат ----------
    def get_chat_id(self, uid1, uid2):
        """Стабильный ID чата между двумя пользователями"""
        return "_".join(sorted([uid1, uid2]))

    def send_message(self, to_uid, text):
        """Отправить сообщение"""
        if not self.is_logged_in or not text.strip():
            return False
        try:
            chat_id = self.get_chat_id(self.current_uid, to_uid)
            firebase_db.reference(f"chats/{chat_id}").push({
                "from_uid": self.current_uid,
                "from_username": self.current_username,
                "text": text.strip(),
                "timestamp": time.time()
            })
            return True
        except Exception as e:
            print(f"Ошибка отправки сообщения: {e}")
            return False

    def get_messages(self, friend_uid, limit=50):
        """Получить последние сообщения"""
        if not self.is_logged_in:
            return []
        try:
            chat_id = self.get_chat_id(self.current_uid, friend_uid)
            result = firebase_db.reference(f"chats/{chat_id}").order_by_child("timestamp").limit_to_last(limit).get()
            if not result:
                return []
            msgs = sorted(result.values(), key=lambda m: m.get("timestamp", 0))
            return msgs
        except Exception as e:
            print(f"Ошибка получения сообщений: {e}")
            return []

    # ---------- Статусы ----------
    STATUSES = {
        "🟢 Онлайн":        "online",
        "🎮 Играю":         "playing",
        "💤 Не беспокоить": "dnd",
        "👻 Невидимка":     "invisible",
    }

    def set_user_status(self, status_key):
        if not self.is_logged_in or not self._initialized:
            return
        try:
            firebase_db.reference(f"users/{self.current_uid}").update({
                "status": status_key,
                "online": status_key != "invisible"
            })
        except Exception as e:
            print(f"Ошибка статуса: {e}")

    def get_friend_statuses(self):
        """Возвращает {uid: {username, online, status}} для всех друзей"""
        if not self.is_logged_in or not self._initialized:
            return {}
        try:
            friends = firebase_db.reference(f"friends/{self.current_uid}").get() or {}
            result = {}
            for uid in friends:
                data = firebase_db.reference(f"users/{uid}").get()
                if data:
                    result[uid] = {
                        "username": data.get("username", ""),
                        "online":   data.get("online", False),
                        "status":   data.get("status", "online"),
                    }
            return result
        except Exception as e:
            print(f"Ошибка получения статусов друзей: {e}")
            return {}


class ProfileManager:
    def __init__(self):
        self.profiles = {}
        self.load()

    def load(self):
        if os.path.exists(PROFILES_FILE):
            try:
                with open(PROFILES_FILE, "r", encoding="utf-8") as f:
                    self.profiles = json.load(f)
            except:
                self.profiles = {}
        else:
            self.profiles = {
                "Default": {
                    "username": "Steve",
                    "version": "",
                    "memory": 2048,
                    "java_path": "",
                    "jvm_args": "",
                    "loader": None,
                    "last_seen": 0
                }
            }

    def save(self):
        with open(PROFILES_FILE, "w", encoding="utf-8") as f:
            json.dump(self.profiles, f, indent=4)

    def get_profile_names(self):
        return list(self.profiles.keys())

    def get_profile(self, name):
        return self.profiles.get(name, {})

    def add_profile(self, name, data):
        self.profiles[name] = data
        self.save()

    def delete_profile(self, name):
        if name in self.profiles and name != "Default":
            del self.profiles[name]
            self.save()
            return True
        return False

    def update_profile(self, name, data):
        if name in self.profiles:
            self.profiles[name].update(data)
            self.save()
            return True
        return False

    def update_last_seen(self, name):
        if name in self.profiles:
            self.profiles[name]["last_seen"] = time.time()
            self.save()

class VersionCache:
    """Кэш для списка версий Minecraft"""
    def __init__(self, cache_file):
        self.cache_file = cache_file
        self.data = self.load()

    def load(self):
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                pass
        return {"timestamp": 0, "versions": []}

    def save(self, versions):
        self.data = {
            "timestamp": time.time(),
            "versions": versions
        }
        with open(self.cache_file, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=4)

    def is_valid(self):
        return time.time() - self.data["timestamp"] < CACHE_MAX_AGE

    def get_versions(self):
        return self.data["versions"] if self.is_valid() else None

class MinecraftLauncher(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Velox")
        self.geometry("1100x700")
        self.resizable(True, True)
        self.minsize(1000, 650)
        self.configure(fg_color=CP_BG_PANEL)

        # Иконка окна
        try:
            icon_path = os.path.join(os.path.dirname(sys.argv[0]), "velox.ico")
            if not os.path.exists(icon_path):
                icon_path = "velox.ico"
            if os.path.exists(icon_path):
                self.iconbitmap(icon_path)
        except Exception as e:
            print(f"Иконка не загружена: {e}")

        # Текущая версия лаунчера
        self.launcher_version = "1.4.0"

        # Директории
        self.minecraft_directory = os.path.join(os.path.expanduser("~"), "my_minecraft_launcher")
        os.makedirs(self.minecraft_directory, exist_ok=True)
        self.mods_directory = os.path.join(self.minecraft_directory, "mods")
        os.makedirs(self.mods_directory, exist_ok=True)
        self.resourcepacks_directory = os.path.join(self.minecraft_directory, "resourcepacks")
        os.makedirs(self.resourcepacks_directory, exist_ok=True)

        # Кэш версий
        self.version_cache = VersionCache(os.path.join(self.minecraft_directory, VERSION_CACHE_FILE))

        # Загрузка конфигурации и профилей
        self.config = self.load_config()
        self.profile_manager = ProfileManager()
        self.firebase = FirebaseManager()
        # Firebase инициализируется в фоне — не блокирует UI
        Thread(target=self.firebase._init_firebase, daemon=True).start()

        # Статистика
        self.stats_manager = StatsManager(os.path.join(self.minecraft_directory, STATS_FILE))

        # Список всех версий
        self.all_versions = ["Загрузка..."]
        self.installed_versions = []

        # Кэш для иконок
        self.icon_cache = {}
        self.icon_semaphore = Semaphore(5)  # ограничение одновременных загрузок иконок

        # Пагинация модов
        self.current_mod_query = ""
        self.current_mod_sort = "Популярности"
        self.current_mod_version = ""
        self.current_mod_offset = 0
        self.total_mod_hits = 0
        self.mod_limit = 20

        # Пагинация ресурспаков
        self.current_rp_query = ""
        self.current_rp_sort = "Популярности"
        self.current_rp_version = ""
        self.current_rp_offset = 0
        self.total_rp_hits = 0
        self.rp_limit = 20

        # Время запуска игры
        self.game_start_time = None

        self.protocol("WM_DELETE_WINDOW", self._on_closing)

        # Сначала показываем пустое окно, потом строим UI
        self.after(100, self._build_ui)

    def _build_ui(self):
        """Строим интерфейс после того как окно отрисовалось"""
        self.create_widgets()
        self.update_idletasks()
        self.after(200, self._deferred_startup)

    def _deferred_startup(self):
        """Запускается после отрисовки UI"""
        self.update_installed_versions()
        self.apply_profile("Default")
        self.update_stats_display()
        self.after(200, self.load_all_versions)
        self.after(500, self.check_for_updates)

        self._pending_password = ""
        saved_email = self.config.get("saved_email", "")
        saved_password = self.config.get("saved_password", "")
        if saved_email and saved_password:
            # Ждём 3 сек чтобы Firebase успел инициализироваться в фоне
            self.after(3000, lambda: self._auto_login(saved_email, saved_password))

    def _on_closing(self):
        """При закрытии — ставим офлайн статус"""
        try:
            self.firebase._set_online(False)
        except:
            pass
        self.destroy()

    def _auto_login(self, email, password):
        """Автовход при запуске"""
        self._pending_password = password
        def do():
            ok, msg = self.firebase.login(email, password)
            if ok:
                self.after_idle(lambda: self._build_auth_panel())
                self.after_idle(lambda: self._update_friends_ui_state())
                self.after_idle(lambda: self.header_status.configure(
                    text=f"🟢  {self.firebase.current_username}", text_color=CP_ACCENT))
                self.after_idle(lambda: self._schedule_online_ping())
            else:
                self.config.pop("saved_email", None)
                self.config.pop("saved_password", None)
                self.save_config()
        Thread(target=do).start()

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def save_config(self):
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=4)

    def create_widgets(self):
        # ── Шапка Velox ──
        header = ctk.CTkFrame(self, fg_color=CP_BG_CARD, corner_radius=0, height=56)
        header.pack(fill="x", padx=0, pady=0)
        header.pack_propagate(False)

        logo_frame = ctk.CTkFrame(header, fg_color="transparent")
        logo_frame.pack(side="left", padx=18, pady=8)

        # Логотип из файла
        try:
            logo_path = os.path.join(os.path.dirname(sys.argv[0]), "velox_logo.png")
            if not os.path.exists(logo_path):
                logo_path = "velox_logo.png"
            if os.path.exists(logo_path):
                pil_logo = Image.open(logo_path).resize((40, 40), Image.LANCZOS)
                ctk_logo = ctk.CTkImage(light_image=pil_logo, dark_image=pil_logo, size=(40, 40))
                ctk.CTkLabel(logo_frame, image=ctk_logo, text="").pack(side="left", padx=(0, 8))
            else:
                ctk.CTkLabel(logo_frame, text="⬡", font=ctk.CTkFont(size=28), text_color=CP_ACCENT).pack(side="left", padx=(0, 6))
        except Exception:
            ctk.CTkLabel(logo_frame, text="⬡", font=ctk.CTkFont(size=28), text_color=CP_ACCENT).pack(side="left", padx=(0, 6))

        title_frame = ctk.CTkFrame(logo_frame, fg_color="transparent")
        title_frame.pack(side="left")
        ctk.CTkLabel(title_frame, text="Velox",
                     font=ctk.CTkFont(size=20, weight="bold"), text_color="white").pack(anchor="w")
        ctk.CTkLabel(title_frame, text=f"v{self.launcher_version}",
                     font=ctk.CTkFont(size=10), text_color="#5a7aaa").pack(anchor="w")

        # Правая часть шапки — статус Firebase
        self.header_status = ctk.CTkLabel(header, text="",
                                          font=ctk.CTkFont(size=12), text_color="#5a7aaa")
        self.header_status.pack(side="right", padx=18)

        # ── Вкладки ──
        self.tabview = ctk.CTkTabview(self, fg_color=CP_BG_PANEL)
        self.tabview.pack(pady=(6, 10), padx=12, fill="both", expand=True)

        self.tab_play = self.tabview.add("🎮  Игра")
        self.tab_friends = self.tabview.add("👥  Друзья")
        self.tab_versions = self.tabview.add("📦  Версии")
        self.tab_mods = self.tabview.add("🔧  Контент")
        self.tab_stats = self.tabview.add("📊  Статистика")
        self.tab_news = self.tabview.add("📰  Новости")
        self.tab_settings = self.tabview.add("⚙️  Настройки")

        # Строим только главную вкладку сразу
        self.create_play_tab()

        # Остальные строим поочерёдно с паузой чтобы не блокировать UI
        self.after(100,  self.create_friends_tab)
        self.after(200, self.create_versions_tab)
        self.after(300, self.create_content_tab)
        self.after(400, self.create_stats_tab)
        self.after(500, self.create_news_tab)
        self.after(600, self.create_settings_tab)

    def create_play_tab(self):
        # ── Панель профиля (карточка сверху) ──
        profile_card = ctk.CTkFrame(self.tab_play, fg_color=CP_BG_CARD, corner_radius=12)
        profile_card.pack(fill="x", padx=12, pady=(10, 6))

        ctk.CTkLabel(profile_card, text="Профиль:", font=ctk.CTkFont(size=12),
                     text_color="#5a7aaa").pack(side="left", padx=(14, 4), pady=10)
        self.profile_combo = ctk.CTkComboBox(profile_card, values=self.profile_manager.get_profile_names(),
                                             width=180,
                                             fg_color=CP_BG_PANEL, border_color=CP_BLUE)
        self.profile_combo.pack(side="left", padx=4, pady=10)
        self.profile_combo.set("Default")
        self.profile_combo.configure(command=self.on_profile_selected)

        self.save_profile_btn = ctk.CTkButton(profile_card, text="💾 Сохранить",
                                              command=self.save_current_profile, width=110,
                                              fg_color=CP_BLUE, hover_color=CP_BLUE_HOVER, corner_radius=8)
        self.save_profile_btn.pack(side="left", padx=4)
        self.save_as_btn = ctk.CTkButton(profile_card, text="📋 Копировать",
                                         command=self.save_profile_as, width=110,
                                         fg_color=CP_BG_PANEL, hover_color=CP_BLUE_DARK,
                                         border_width=1, border_color=CP_BLUE, corner_radius=8)
        self.save_as_btn.pack(side="left", padx=4)
        self.delete_profile_btn = ctk.CTkButton(profile_card, text="🗑️ Удалить",
                                                command=self.delete_profile, width=90,
                                                fg_color="#7a1e1e", hover_color="#a02020", corner_radius=8)
        self.delete_profile_btn.pack(side="left", padx=4)

        # ── Основная область ──
        main_frame = ctk.CTkFrame(self.tab_play, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=12, pady=6)
        main_frame.columnconfigure(0, weight=0)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(0, weight=1)

        # ── Левая панель запуска ──
        left_panel = ctk.CTkFrame(main_frame, fg_color=CP_BG_CARD, corner_radius=14, width=300)
        left_panel.grid(row=0, column=0, sticky="ns", padx=(0, 8), pady=0)
        left_panel.pack_propagate(False)

        # Заголовок
        ctk.CTkLabel(left_panel, text="⬡  Velox",
                     font=ctk.CTkFont(size=17, weight="bold"),
                     text_color=CP_ACCENT).pack(pady=(22, 4))
        ctk.CTkLabel(left_panel, text="Запуск Minecraft",
                     font=ctk.CTkFont(size=11), text_color="#5a7aaa").pack(pady=(0, 16))

        ctk.CTkFrame(left_panel, height=1, fg_color=CP_BLUE_DARK).pack(fill="x", padx=16, pady=0)

        # Поля
        fields = ctk.CTkFrame(left_panel, fg_color="transparent")
        fields.pack(fill="x", padx=16, pady=12)

        ctk.CTkLabel(fields, text="Никнейм", font=ctk.CTkFont(size=12, weight="bold"),
                     text_color="#8aaed4").pack(anchor="w", pady=(0, 3))
        self.username_entry = ctk.CTkEntry(fields, width=260, height=36,
                                           fg_color=CP_BG_PANEL, border_color=CP_BLUE,
                                           corner_radius=8, font=ctk.CTkFont(size=13))
        self.username_entry.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(fields, text="Версия", font=ctk.CTkFont(size=12, weight="bold"),
                     text_color="#8aaed4").pack(anchor="w", pady=(0, 3))
        self.version_combo = ctk.CTkComboBox(fields, values=["Обновление..."], width=260, height=36,
                                             fg_color=CP_BG_PANEL, border_color=CP_BLUE,
                                             corner_radius=8)
        self.version_combo.pack(fill="x", pady=(0, 6))
        self.version_combo.configure(command=self.on_version_selected)
        self.version_combo.bind("<MouseWheel>", self.on_version_scroll)

        self.show_all_btn = ctk.CTkButton(fields, text="Показать все версии",
                                          command=self.toggle_all_versions,
                                          fg_color="transparent", hover_color=CP_BLUE_DARK,
                                          border_width=1, border_color="#3a5a8a",
                                          height=28, corner_radius=6,
                                          font=ctk.CTkFont(size=11))
        self.show_all_btn.pack(fill="x", pady=(0, 12))

        # Прогресс
        self.progress_label = ctk.CTkLabel(left_panel, text="",
                                           font=ctk.CTkFont(size=11), text_color="#5a7aaa")
        self.progress_label.pack(pady=(0, 4))
        self.progress_bar = ctk.CTkProgressBar(left_panel, width=260, height=6,
                                               progress_color=CP_ACCENT, fg_color=CP_BG_PANEL,
                                               corner_radius=4)
        self.progress_bar.pack(padx=16, pady=(0, 16))
        self.progress_bar.set(0)

        # Большая кнопка ИГРАТЬ
        self.launch_btn = ctk.CTkButton(
            left_panel,
            text="▶   ИГРАТЬ",
            command=self.launch_game,
            width=260, height=52,
            font=ctk.CTkFont(size=18, weight="bold"),
            fg_color=CP_BLUE,
            hover_color=CP_BLUE_HOVER,
            corner_radius=12,
            text_color="white"
        )
        self.launch_btn.pack(padx=16, pady=(0, 22))

        # ── Правая панель ──
        right_panel = ctk.CTkFrame(main_frame, fg_color=CP_BG_CARD, corner_radius=14)
        right_panel.grid(row=0, column=1, sticky="nsew", pady=0)

        ctk.CTkLabel(right_panel, text="Информация о версии",
                     font=ctk.CTkFont(size=14, weight="bold"), text_color="#8aaed4").pack(anchor="w", padx=14, pady=(14, 6))
        self.version_info_text = ctk.CTkTextbox(right_panel, height=140, wrap="word",
                                                fg_color=CP_BG_PANEL, corner_radius=8,
                                                font=ctk.CTkFont(size=12))
        self.version_info_text.pack(fill="x", padx=14, pady=(0, 10))
        self.version_info_text.insert("0.0", "Выберите версию для просмотра информации")
        self.version_info_text.configure(state="disabled")

        ctk.CTkFrame(right_panel, height=1, fg_color=CP_BLUE_DARK).pack(fill="x", padx=14, pady=0)

        ctk.CTkLabel(right_panel, text="Установленные моды",
                     font=ctk.CTkFont(size=13, weight="bold"), text_color="#8aaed4").pack(anchor="w", padx=14, pady=(10, 6))
        self.mods_listbox = ctk.CTkScrollableFrame(right_panel, fg_color=CP_BG_PANEL, corner_radius=8)
        self.mods_listbox.pack(fill="both", expand=True, padx=14, pady=(0, 14))
        self.update_mods_list()

    def create_friends_tab(self):
        frame = ctk.CTkFrame(self.tab_friends)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        # --- Панель авторизации ---
        self.auth_frame = ctk.CTkFrame(frame, fg_color=CP_BG_CARD, corner_radius=12)
        self.auth_frame.pack(fill="x", padx=10, pady=5)
        self._build_auth_panel()

        # --- Основной контент (скрыт до входа) ---
        self.friends_main_frame = ctk.CTkFrame(frame)
        self.friends_main_frame.pack(fill="both", expand=True, padx=10, pady=5)
        self._build_friends_main()

        self._update_friends_ui_state()

    def _build_auth_panel(self):
        if not hasattr(self, "auth_frame"):
            return
        for w in self.auth_frame.winfo_children():
            w.destroy()

        if self.firebase.is_logged_in:
            # Показываем инфо об аккаунте
            info_row = ctk.CTkFrame(self.auth_frame, fg_color="transparent")
            info_row.pack(fill="x", padx=10, pady=8)
            ctk.CTkLabel(info_row, text=f"🟢 Вы вошли как: ", font=ctk.CTkFont(size=13)).pack(side="left")
            ctk.CTkLabel(info_row, text=self.firebase.current_username,
                         font=ctk.CTkFont(size=13, weight="bold"), text_color="#4fc3f7").pack(side="left")
            ctk.CTkButton(info_row, text="Выйти", width=80, fg_color="#b53a3a", hover_color="#c54a4a",
                          command=self._logout).pack(side="right", padx=5)

            # Статус
            status_row = ctk.CTkFrame(self.auth_frame, fg_color="transparent")
            status_row.pack(fill="x", padx=10, pady=(0, 8))
            ctk.CTkLabel(status_row, text="Статус:", font=ctk.CTkFont(size=12),
                         text_color="#5a7aaa").pack(side="left", padx=(0, 10))
            cur = getattr(self, "_current_status", "🟢 Онлайн")
            seg = ctk.CTkSegmentedButton(
                status_row,
                values=["🟢 Онлайн", "🎮 Играю", "💤 Не беспокоить", "👻 Невидимка"],
                command=self._on_status_change,
                font=ctk.CTkFont(size=11), height=28)
            seg.set(cur)
            seg.pack(side="left", fill="x", expand=True)
        else:
            # Форма входа/регистрации
            self.auth_mode = getattr(self, "auth_mode", "login")

            top_row = ctk.CTkFrame(self.auth_frame, fg_color="transparent")
            top_row.pack(fill="x", padx=10, pady=(8, 2))
            title = "Вход в аккаунт" if self.auth_mode == "login" else "Регистрация"
            ctk.CTkLabel(top_row, text=title, font=ctk.CTkFont(size=14, weight="bold")).pack(side="left")
            switch_text = "→ Регистрация" if self.auth_mode == "login" else "→ Войти"
            ctk.CTkButton(top_row, text=switch_text, width=120, fg_color="transparent",
                          hover_color="#2a2a4a", border_width=1,
                          command=self._toggle_auth_mode).pack(side="right")

            fields_row = ctk.CTkFrame(self.auth_frame, fg_color="transparent")
            fields_row.pack(fill="x", padx=10, pady=5)

            if self.auth_mode == "register":
                self.auth_username_entry = ctk.CTkEntry(fields_row, placeholder_text="Никнейм", width=140)
                self.auth_username_entry.pack(side="left", padx=4)

            self.auth_email_entry = ctk.CTkEntry(fields_row, placeholder_text="Email", width=180)
            self.auth_email_entry.pack(side="left", padx=4)

            self.auth_password_entry = ctk.CTkEntry(fields_row, placeholder_text="Пароль", show="*", width=140)
            self.auth_password_entry.pack(side="left", padx=4)

            btn_text = "Войти" if self.auth_mode == "login" else "Зарегистрироваться"
            ctk.CTkButton(fields_row, text=btn_text, width=140,
                          command=self._do_auth).pack(side="left", padx=8)

            self.auth_status_label = ctk.CTkLabel(self.auth_frame, text="", font=ctk.CTkFont(size=11))
            self.auth_status_label.pack(pady=(0, 5))

    def _toggle_auth_mode(self):
        self.auth_mode = "register" if getattr(self, "auth_mode", "login") == "login" else "login"
        self._build_auth_panel()

    def _do_auth(self):
        email = self.auth_email_entry.get().strip()
        password = self.auth_password_entry.get().strip()
        if not email or not password:
            self.auth_status_label.configure(text="⚠️ Заполните все поля", text_color="orange")
            return

        self.auth_status_label.configure(text="⏳ Подождите...", text_color="gray")
        self.update()

        if self.auth_mode == "login":
            self._pending_password = password
            def do():
                ok, msg = self.firebase.login(email, password)
                self.after_idle(lambda: self._on_auth_result(ok, msg))
            Thread(target=do).start()
        else:
            username = self.auth_username_entry.get().strip()
            if not username:
                self.auth_status_label.configure(text="⚠️ Введите никнейм", text_color="orange")
                return
            self._pending_password = password
            def do():
                ok, msg = self.firebase.register(email, password, username)
                self.after_idle(lambda: self._on_auth_result(ok, msg))
            Thread(target=do).start()

    def _on_auth_result(self, ok, msg):
        if ok:
            # Сохраняем credentials для автовхода
            self.config["saved_email"] = self.firebase.current_email
            self.config["saved_password"] = self._pending_password
            self.save_config()
            self._build_auth_panel()
            self._update_friends_ui_state()
            self.refresh_friends_list()
            self._schedule_online_ping()
            # Обновляем шапку
            self.header_status.configure(
                text=f"🟢  {self.firebase.current_username}", text_color=CP_ACCENT)
        else:
            self.auth_status_label.configure(text=f"❌ {msg}", text_color="#ff6b6b")

    def _logout(self):
        self.firebase.logout()
        self.config.pop("saved_email", None)
        self.config.pop("saved_password", None)
        self.save_config()
        self.header_status.configure(text="", text_color="#5a7aaa")
        self._build_auth_panel()
        self._update_friends_ui_state()

    def _on_status_change(self, value):
        self._current_status = value
        icon = value.split()[0]
        self.header_status.configure(text=f"{icon}  {self.firebase.current_username}")
        status_key = self.firebase.STATUSES.get(value, "online")
        Thread(target=lambda: self.firebase.set_user_status(status_key), daemon=True).start()

    def _schedule_online_ping(self):
        """Обновляем статус онлайн каждые 30 секунд + проверяем друзей"""
        if self.firebase.is_logged_in:
            self.firebase.keep_online()
            self._check_friends_online()
            self.after(30000, self._schedule_online_ping)

    def _check_friends_online(self):
        """Проверяем кто появился онлайн — показываем уведомление"""
        def do():
            statuses = self.firebase.get_friend_statuses()
            prev = getattr(self, "_prev_friend_statuses", {})
            for uid, data in statuses.items():
                was = prev.get(uid, {}).get("online", False)
                now = data.get("online", False)
                if now and not was and data.get("status", "online") != "invisible":
                    name = data.get("username", "Друг")
                    self.after_idle(lambda n=name: self._show_friend_notification(n))
            self._prev_friend_statuses = statuses
        Thread(target=do, daemon=True).start()

    def _show_friend_notification(self, username):
        """Всплывающее уведомление — друг онлайн"""
        try:
            notif = ctk.CTkToplevel(self)
            notif.overrideredirect(True)
            notif.attributes("-topmost", True)
            notif.configure(fg_color=CP_BG_CARD)
            sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
            w, h = 280, 72
            notif.geometry(f"{w}x{h}+{sw-w-20}+{sh-h-60}")

            inner = ctk.CTkFrame(notif, fg_color=CP_BG_CARD, corner_radius=12,
                                  border_width=1, border_color=CP_BLUE)
            inner.pack(fill="both", expand=True, padx=2, pady=2)

            ctk.CTkLabel(inner, text="🟢", font=ctk.CTkFont(size=22)).pack(side="left", padx=(12,6), pady=10)
            txt = ctk.CTkFrame(inner, fg_color="transparent")
            txt.pack(side="left", fill="both", expand=True)
            ctk.CTkLabel(txt, text=username, font=ctk.CTkFont(size=13, weight="bold"),
                         text_color=CP_ACCENT).pack(anchor="w")
            ctk.CTkLabel(txt, text="теперь онлайн", font=ctk.CTkFont(size=11),
                         text_color="#5a7aaa").pack(anchor="w")
            ctk.CTkButton(inner, text="✕", width=24, height=24, corner_radius=6,
                          fg_color="transparent", hover_color=CP_BG_PANEL,
                          command=notif.destroy).pack(side="right", padx=8)

            notif.after(4000, lambda: notif.destroy() if notif.winfo_exists() else None)
        except Exception as e:
            print(f"Ошибка уведомления: {e}")

    def _build_friends_main(self):
        if not hasattr(self, "friends_main_frame"):
            return
        for w in self.friends_main_frame.winfo_children():
            w.destroy()

        if not self.firebase.is_logged_in:
            ctk.CTkLabel(self.friends_main_frame,
                         text="🔒 Войдите в аккаунт, чтобы видеть друзей",
                         font=ctk.CTkFont(size=14), text_color="gray").pack(expand=True)
            return

        # Tabs: Друзья / Заявки
        tabs = ctk.CTkTabview(self.friends_main_frame)
        tabs.pack(fill="both", expand=True)
        self._friends_tab = tabs.add("👥 Друзья")
        self._requests_tab = tabs.add("📨 Заявки")

        # --- Вкладка Друзья ---
        add_row = ctk.CTkFrame(self._friends_tab)
        add_row.pack(fill="x", pady=5)
        self.friend_search_entry = ctk.CTkEntry(add_row, placeholder_text="Никнейм пользователя...", width=220)
        self.friend_search_entry.pack(side="left", padx=5)
        ctk.CTkButton(add_row, text="➕ Добавить в друзья", command=self._send_friend_request, width=160).pack(side="left", padx=5)
        ctk.CTkButton(add_row, text="🔄", width=40, command=self.refresh_friends_list).pack(side="left", padx=2)

        self.friends_list_frame = ctk.CTkScrollableFrame(self._friends_tab, label_text="")
        self.friends_list_frame.pack(fill="both", expand=True, pady=5)

        self.friends_status_label = ctk.CTkLabel(self._friends_tab, text="")
        self.friends_status_label.pack()

        # --- Вкладка Заявки ---
        ctk.CTkButton(self._requests_tab, text="🔄 Обновить", command=self.refresh_requests, width=120).pack(anchor="e", padx=10, pady=5)
        self.requests_list_frame = ctk.CTkScrollableFrame(self._requests_tab, label_text="")
        self.requests_list_frame.pack(fill="both", expand=True, pady=5)
        self.requests_status_label = ctk.CTkLabel(self._requests_tab, text="")
        self.requests_status_label.pack()

        # Загружаем данные
        self.refresh_friends_list()
        self.refresh_requests()

    def _update_friends_ui_state(self):
        self._build_friends_main()

    def _send_friend_request(self):
        username = self.friend_search_entry.get().strip()
        if not username:
            return
        self.friends_status_label.configure(text="⏳ Отправка...", text_color="gray")
        def do():
            ok, msg = self.firebase.send_friend_request(username)
            color = "#4fc3f7" if ok else "#ff6b6b"
            icon = "✅" if ok else "❌"
            self.after_idle(lambda: self.friends_status_label.configure(text=f"{icon} {msg}", text_color=color))
        Thread(target=do).start()

    def refresh_friends_list(self):
        if not self.firebase.is_logged_in:
            return
        if not hasattr(self, "friends_list_frame"):
            return
        for w in self.friends_list_frame.winfo_children():
            w.destroy()
        ctk.CTkLabel(self.friends_list_frame, text="⏳ Загрузка...", text_color="gray").pack(pady=20)

        def do():
            friends = self.firebase.get_friends()
            self.after_idle(lambda: self._display_friends(friends))
        Thread(target=do).start()

    def _display_friends(self, friends):
        for w in self.friends_list_frame.winfo_children():
            w.destroy()

        if not friends:
            ctk.CTkLabel(self.friends_list_frame,
                         text="У вас пока нет друзей.\nДобавьте кого-нибудь!",
                         font=ctk.CTkFont(size=13), text_color="gray").pack(expand=True, pady=30)
            return

        ctk.CTkLabel(self.friends_list_frame,
                     text=f"Друзей: {len(friends)}",
                     font=ctk.CTkFont(size=12), text_color="gray").pack(anchor="w", padx=10, pady=2)

        # Сортируем: онлайн первые
        sorted_friends = sorted(friends.items(), key=lambda x: (not x[1].get("online", False), x[1].get("username", "")))

        for uid, fdata in sorted_friends:
            self._create_friend_card_firebase(uid, fdata)

    def _create_friend_card_firebase(self, uid, fdata):
        username = fdata.get("username", "???")
        online = fdata.get("online", False)
        last_seen = fdata.get("last_seen", 0)
        friend_status = fdata.get("status", "online")

        # Определяем текст и цвет статуса
        STATUS_DISPLAY = {
            "online":    ("🟢 В сети",          "#00e676"),
            "playing":   ("🎮 Играет",          CP_ACCENT),
            "dnd":       ("💤 Не беспокоить",   "#ff9800"),
            "invisible": ("⚪ Не в сети",        "#555"),
        }
        if online:
            status_text, dot_color = STATUS_DISPLAY.get(friend_status, ("🟢 В сети", "#00e676"))
        else:
            status_text = self.firebase.format_last_seen(last_seen, False)
            dot_color = "#555"

        card = ctk.CTkFrame(self.friends_list_frame, corner_radius=10, fg_color=CP_BG_CARD)
        card.pack(fill="x", padx=10, pady=4)

        # Аватар с индикатором статуса
        avatar_frame = ctk.CTkFrame(card, fg_color="transparent", width=50)
        avatar_frame.pack(side="left", padx=10, pady=10)
        avatar_frame.pack_propagate(False)
        ctk.CTkLabel(avatar_frame, text="👤", font=ctk.CTkFont(size=26)).pack()
        ctk.CTkLabel(avatar_frame, text="●", font=ctk.CTkFont(size=10), text_color=dot_color).pack()

        info_frame = ctk.CTkFrame(card, fg_color="transparent")
        info_frame.pack(side="left", fill="both", expand=True, padx=5)
        ctk.CTkLabel(info_frame, text=username, font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w")
        ctk.CTkLabel(info_frame, text=status_text, font=ctk.CTkFont(size=11), text_color=dot_color).pack(anchor="w")

        ctk.CTkButton(card, text="💬", width=36, height=36, corner_radius=8,
                      fg_color=CP_BLUE_DARK, hover_color=CP_BLUE,
                      command=lambda u=uid, n=username: self._open_chat(u, n)).pack(side="right", padx=4)

        ctk.CTkButton(card, text="✖", width=32, height=32, corner_radius=6,
                      fg_color="#b53a3a", hover_color="#c54a4a",
                      command=lambda u=uid, n=username: self._remove_friend(u, n)).pack(side="right", padx=10)

    def _remove_friend(self, uid, username):
        if messagebox.askyesno("Подтверждение", f"Удалить {username} из друзей?"):
            def do():
                ok, msg = self.firebase.remove_friend(uid)
                self.after_idle(self.refresh_friends_list)
            Thread(target=do).start()

    def refresh_requests(self):
        if not self.firebase.is_logged_in:
            return
        if not hasattr(self, "requests_list_frame"):
            return
        for w in self.requests_list_frame.winfo_children():
            w.destroy()
        ctk.CTkLabel(self.requests_list_frame, text="⏳ Загрузка...", text_color="gray").pack(pady=20)

        def do():
            reqs = self.firebase.get_incoming_requests()
            self.after_idle(lambda: self._display_requests(reqs))
        Thread(target=do).start()

    def _display_requests(self, reqs):
        for w in self.requests_list_frame.winfo_children():
            w.destroy()

        if not reqs:
            ctk.CTkLabel(self.requests_list_frame, text="📭 Входящих заявок нет",
                         font=ctk.CTkFont(size=13), text_color="gray").pack(expand=True, pady=30)
            return

        ctk.CTkLabel(self.requests_list_frame, text=f"Входящие заявки: {len(reqs)}",
                     font=ctk.CTkFont(size=12), text_color="gray").pack(anchor="w", padx=10, pady=2)

        for from_uid, req_data in reqs.items():
            self._create_request_card(from_uid, req_data)

    def _create_request_card(self, from_uid, req_data):
        username = req_data.get("from_username", "???")
        ts = req_data.get("timestamp", 0)
        dt_str = datetime.fromtimestamp(ts).strftime("%d.%m %H:%M") if ts else ""

        card = ctk.CTkFrame(self.requests_list_frame, corner_radius=10, fg_color=CP_BG_CARD)
        card.pack(fill="x", padx=10, pady=4)

        ctk.CTkLabel(card, text="👤", font=ctk.CTkFont(size=24), width=40).pack(side="left", padx=10, pady=10)

        info = ctk.CTkFrame(card, fg_color="transparent")
        info.pack(side="left", fill="both", expand=True, padx=5)
        ctk.CTkLabel(info, text=username, font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w")
        ctk.CTkLabel(info, text=f"Заявка от {dt_str}", font=ctk.CTkFont(size=11), text_color="gray").pack(anchor="w")

        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.pack(side="right", padx=10, pady=10)

        ctk.CTkButton(btn_frame, text="✅ Принять", width=90, fg_color="#2e7d32", hover_color="#388e3c",
                      command=lambda u=from_uid: self._accept_request(u)).pack(pady=2)
        ctk.CTkButton(btn_frame, text="❌ Отклонить", width=90, fg_color="#b53a3a", hover_color="#c54a4a",
                      command=lambda u=from_uid: self._decline_request(u)).pack(pady=2)

    def _accept_request(self, from_uid):
        def do():
            ok, msg = self.firebase.accept_friend_request(from_uid)
            self.after_idle(self.refresh_requests)
            self.after_idle(self.refresh_friends_list)
            self.after_idle(lambda: self.requests_status_label.configure(
                text=f"{'✅' if ok else '❌'} {msg}",
                text_color="#4fc3f7" if ok else "#ff6b6b"))
        Thread(target=do).start()

    def _decline_request(self, from_uid):
        def do():
            ok, msg = self.firebase.decline_friend_request(from_uid)
            self.after_idle(self.refresh_requests)
        Thread(target=do).start()

    def _open_chat(self, friend_uid, friend_username):
        """Открыть окно чата с другом"""
        # Проверяем, не открыто ли уже окно чата с этим другом
        win_key = f"chat_{friend_uid}"
        if hasattr(self, "_chat_windows") and win_key in self._chat_windows:
            try:
                self._chat_windows[win_key].lift()
                self._chat_windows[win_key].focus()
                return
            except:
                pass
        if not hasattr(self, "_chat_windows"):
            self._chat_windows = {}
        win = ChatWindow(self, self.firebase, friend_uid, friend_username)
        self._chat_windows[win_key] = win
        win.protocol("WM_DELETE_WINDOW", lambda: self._close_chat(win_key, win))

    def _close_chat(self, key, win):
        if hasattr(self, "_chat_windows"):
            self._chat_windows.pop(key, None)
        win.destroy()

    def update_friends_list(self):
        """Совместимость со старым кодом"""
        if self.firebase.is_logged_in:
            self.refresh_friends_list()

    def create_versions_tab(self):
        outer = ctk.CTkFrame(self.tab_versions, fg_color="transparent")
        outer.pack(fill="both", expand=True, padx=12, pady=10)

        # ── Левая панель: список версий ──
        left = ctk.CTkFrame(outer, fg_color="transparent", width=230)
        left.pack(side="left", fill="y", padx=(0, 8))
        left.pack_propagate(False)

        lhdr = ctk.CTkFrame(left, fg_color=CP_BG_CARD, corner_radius=12)
        lhdr.pack(fill="x", pady=(0, 6))
        ctk.CTkLabel(lhdr, text="📦  Все версии",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(side="left", padx=14, pady=10)
        ctk.CTkButton(lhdr, text="🔄", width=32, height=28, corner_radius=8,
                      fg_color=CP_BG_PANEL, hover_color=CP_BLUE_DARK,
                      command=lambda: self.load_all_versions(force_refresh=True)).pack(side="right", padx=8)

        self.all_versions_listbox = ctk.CTkScrollableFrame(left, fg_color=CP_BG_CARD,
                                                            corner_radius=12)
        self.all_versions_listbox.pack(fill="both", expand=True)

        # ── Правая панель ──
        right = ctk.CTkFrame(outer, fg_color="transparent")
        right.pack(side="right", fill="both", expand=True)

        # Выбранная версия
        sel_card = ctk.CTkFrame(right, fg_color=CP_BG_CARD, corner_radius=12)
        sel_card.pack(fill="x", pady=(0, 8))

        sel_inner = ctk.CTkFrame(sel_card, fg_color="transparent")
        sel_inner.pack(fill="x", padx=16, pady=12)

        ctk.CTkLabel(sel_inner, text="Выбрана:", text_color="#5a7aaa",
                     font=ctk.CTkFont(size=12)).pack(side="left")
        self.loader_version_combo = ctk.CTkComboBox(sel_inner, values=self.all_versions,
                                                     width=160, fg_color=CP_BG_PANEL,
                                                     border_color=CP_BLUE, corner_radius=8)
        self.loader_version_combo.pack(side="left", padx=10)

        ctk.CTkButton(sel_inner, text="⬇️  Скачать ванилу",
                      command=lambda: self.install_loader("vanilla"),
                      fg_color=CP_BLUE, hover_color=CP_BLUE_HOVER,
                      corner_radius=8, width=150).pack(side="left", padx=6)

        # ── Лоадеры ──
        loaders_hdr = ctk.CTkFrame(right, fg_color="transparent")
        loaders_hdr.pack(fill="x", pady=(0, 6))
        ctk.CTkLabel(loaders_hdr, text="⚙️  Установка мод-лоадеров",
                     font=ctk.CTkFont(size=14, weight="bold"), text_color="#8aaed4").pack(side="left")

        loaders_grid = ctk.CTkFrame(right, fg_color="transparent")
        loaders_grid.pack(fill="x", pady=(0, 8))
        loaders_grid.columnconfigure((0, 1, 2, 3), weight=1)

        def make_loader_card(col, icon, name, color, desc, cmd):
            card = ctk.CTkFrame(loaders_grid, fg_color=CP_BG_CARD, corner_radius=14)
            card.grid(row=0, column=col, padx=5, sticky="ew")
            ctk.CTkLabel(card, text=icon, font=ctk.CTkFont(size=28)).pack(pady=(14, 2))
            ctk.CTkLabel(card, text=name, font=ctk.CTkFont(size=13, weight="bold"),
                         text_color=color).pack()
            ctk.CTkLabel(card, text=desc, font=ctk.CTkFont(size=10),
                         text_color="#5a7aaa", wraplength=120).pack(pady=(2, 8), padx=8)
            btn = ctk.CTkButton(card, text="Установить", command=cmd,
                                fg_color=color, hover_color=color,
                                corner_radius=8, height=30, font=ctk.CTkFont(size=12))
            btn.pack(fill="x", padx=10, pady=(0, 14))
            return btn

        self.forge_btn   = make_loader_card(0, "🔨", "Forge",    "#e87b1e", "Классический\nмод-лоадер",   lambda: self.install_loader("forge"))
        self.fabric_btn  = make_loader_card(1, "🧵", "Fabric",   "#c4d645", "Быстрый\nлёгкий лоадер",    lambda: self.install_loader("fabric"))
        self.quilt_btn   = make_loader_card(2, "🪡", "Quilt",    "#9b59b6", "Форк Fabric\nс доп. API",    lambda: self.install_loader("quilt"))
        self.optifine_btn= make_loader_card(3, "✨", "OptiFine", "#3aafdc", "Оптимизация\nи шейдеры",     lambda: self.install_loader("optifine"))

        # ── Статус + установленные ──
        self.loader_status = ctk.CTkLabel(right, text="",
                                           font=ctk.CTkFont(size=12), text_color=CP_ACCENT)
        self.loader_status.pack(pady=4)

        inst_hdr = ctk.CTkFrame(right, fg_color="transparent")
        inst_hdr.pack(fill="x", pady=(6, 4))
        ctk.CTkLabel(inst_hdr, text="✅  Установленные версии",
                     font=ctk.CTkFont(size=13, weight="bold"), text_color="#8aaed4").pack(side="left")

        self.installed_versions_frame = ctk.CTkScrollableFrame(right, fg_color=CP_BG_CARD,
                                                                corner_radius=12, height=130)
        self.installed_versions_frame.pack(fill="x")
        self._refresh_installed_cards()

    def _refresh_installed_cards(self):
        if not hasattr(self, "installed_versions_frame"):
            return
        for w in self.installed_versions_frame.winfo_children():
            w.destroy()
        versions_dir = os.path.join(self.minecraft_directory, "versions")
        installed = []
        if os.path.exists(versions_dir):
            installed = [d for d in os.listdir(versions_dir)
                         if os.path.isdir(os.path.join(versions_dir, d))]
        if not installed:
            ctk.CTkLabel(self.installed_versions_frame,
                         text="Нет установленных версий. Скачайте версию выше.",
                         text_color="#5a7aaa", font=ctk.CTkFont(size=12)).pack(pady=16)
            return
        for v in installed:
            row = ctk.CTkFrame(self.installed_versions_frame, fg_color=CP_BG_PANEL, corner_radius=8)
            row.pack(fill="x", padx=6, pady=3)
            ctk.CTkLabel(row, text="✅", font=ctk.CTkFont(size=13), width=28).pack(side="left", padx=(8,2), pady=6)
            ctk.CTkLabel(row, text=v, font=ctk.CTkFont(size=12), text_color="white").pack(side="left")
            ctk.CTkButton(row, text="▶ Играть", width=80, height=26, corner_radius=6,
                          fg_color=CP_BLUE, hover_color=CP_BLUE_HOVER,
                          command=lambda ver=v: self._quick_launch(ver)).pack(side="right", padx=8, pady=5)

    def create_settings_tab(self):
        frame = ctk.CTkScrollableFrame(self.tab_settings)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(frame, text="Глобальные настройки", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=10)

        dir_frame = ctk.CTkFrame(frame)
        dir_frame.pack(pady=5, fill="x")
        ctk.CTkLabel(dir_frame, text="Директория игры:").pack(anchor="w")
        self.game_dir_entry = ctk.CTkEntry(dir_frame, width=400)
        self.game_dir_entry.pack(fill="x", pady=5)
        self.game_dir_entry.insert(0, self.minecraft_directory)
        self.game_dir_entry.configure(state="disabled")

        folders_frame = ctk.CTkFrame(frame)
        folders_frame.pack(pady=10, fill="x")
        ctk.CTkLabel(folders_frame, text="Быстрый доступ:").pack(anchor="w", padx=5)
        btn_frame = ctk.CTkFrame(folders_frame, fg_color="transparent")
        btn_frame.pack(fill="x", pady=5)

        ctk.CTkButton(btn_frame, text="📁 Папка игры", command=lambda: os.startfile(self.minecraft_directory),
                      width=120).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="📁 Папка модов", command=lambda: os.startfile(self.mods_directory),
                      width=120).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="📁 Папка ресурспаков", command=lambda: os.startfile(self.resourcepacks_directory),
                      width=150).pack(side="left", padx=5)

        ctk.CTkButton(frame, text="🧹 Очистить кеш лаунчера", command=self.clear_cache, fg_color="orange").pack(pady=10)

        theme_frame = ctk.CTkFrame(frame)
        theme_frame.pack(pady=10, fill="x")
        ctk.CTkLabel(theme_frame, text="Тема оформления:").pack(anchor="w", padx=5)
        self.theme_var = ctk.StringVar(value=self.config.get("theme", "dark"))
        theme_combo = ctk.CTkComboBox(theme_frame, values=["dark", "light", "system"],
                                      variable=self.theme_var, command=self.change_theme, width=150)
        theme_combo.pack(anchor="w", padx=5, pady=5)

        ctk.CTkLabel(frame, text="Настройки Java по умолчанию", font=ctk.CTkFont(size=14)).pack(pady=10)

        # ── Ползунок ОЗУ ──
        mem_card = ctk.CTkFrame(frame, fg_color=CP_BG_CARD, corner_radius=12)
        mem_card.pack(fill="x", pady=6)

        mem_header = ctk.CTkFrame(mem_card, fg_color="transparent")
        mem_header.pack(fill="x", padx=16, pady=(12, 4))
        ctk.CTkLabel(mem_header, text="🖥️  Оперативная память (ОЗУ)",
                     font=ctk.CTkFont(size=13, weight="bold"), text_color="#8aaed4").pack(side="left")
        self.mem_value_label = ctk.CTkLabel(mem_header,
                                             text=f"{self.config.get('default_memory', 2048)} МБ",
                                             font=ctk.CTkFont(size=14, weight="bold"),
                                             text_color=CP_ACCENT)
        self.mem_value_label.pack(side="right")

        # Ползунок от 512 до 16384 МБ
        self.default_memory_var = ctk.StringVar(value=str(self.config.get("default_memory", 2048)))
        self.mem_slider = ctk.CTkSlider(mem_card, from_=512, to=16384,
                                         number_of_steps=31,  # шаг 512 МБ
                                         command=self._on_mem_slider,
                                         progress_color=CP_ACCENT,
                                         button_color=CP_BLUE,
                                         button_hover_color=CP_BLUE_HOVER)
        self.mem_slider.pack(fill="x", padx=16, pady=(0, 6))
        self.mem_slider.set(int(self.config.get("default_memory", 2048)))

        # Подписи минимум / максимум
        marks_row = ctk.CTkFrame(mem_card, fg_color="transparent")
        marks_row.pack(fill="x", padx=16, pady=(0, 6))
        ctk.CTkLabel(marks_row, text="512 МБ", font=ctk.CTkFont(size=10),
                     text_color="#5a7aaa").pack(side="left")
        ctk.CTkLabel(marks_row, text="4096", font=ctk.CTkFont(size=10),
                     text_color="#5a7aaa").pack(side="left", expand=True)
        ctk.CTkLabel(marks_row, text="8192", font=ctk.CTkFont(size=10),
                     text_color="#5a7aaa").pack(side="left", expand=True)
        ctk.CTkLabel(marks_row, text="16384 МБ", font=ctk.CTkFont(size=10),
                     text_color="#5a7aaa").pack(side="right")

        # Рекомендации
        try:
            import psutil
            total_ram = psutil.virtual_memory().total // (1024 * 1024)
            recommended = min(max(total_ram // 2, 2048), 8192)
            rec_text = f"💡 Рекомендуется: {recommended} МБ  (доступно {total_ram} МБ)"
        except:
            rec_text = "💡 Рекомендуется: 2048–4096 МБ для большинства систем"
        ctk.CTkLabel(mem_card, text=rec_text, font=ctk.CTkFont(size=11),
                     text_color="#5a7aaa").pack(anchor="w", padx=16, pady=(0, 12))

        default_java_frame = ctk.CTkFrame(frame)
        default_java_frame.pack(pady=5, fill="x")
        ctk.CTkLabel(default_java_frame, text="Путь к Java:").pack(anchor="w")
        self.default_java_entry = ctk.CTkEntry(default_java_frame, width=400)
        self.default_java_entry.pack(fill="x", pady=5)
        self.default_java_entry.insert(0, self.config.get("default_java", ""))

        default_jvm_frame = ctk.CTkFrame(frame)
        default_jvm_frame.pack(pady=5, fill="x")
        ctk.CTkLabel(default_jvm_frame, text="Доп. JVM аргументы:").pack(anchor="w")
        self.default_jvm_entry = ctk.CTkTextbox(default_jvm_frame, height=60, wrap="word",
                                                fg_color=CP_BG_PANEL, corner_radius=8)
        self.default_jvm_entry.pack(fill="x", pady=5)
        self.default_jvm_entry.insert("0.0", self.config.get("default_jvm_args", ""))

        ctk.CTkButton(frame, text="💾 Сохранить глобальные настройки", command=self.save_global_settings).pack(pady=20)

    def create_content_tab(self):
        outer = ctk.CTkFrame(self.tab_mods, fg_color="transparent")
        outer.pack(fill="both", expand=True, padx=10, pady=8)

        # ── Переключатель ──
        switcher_card = ctk.CTkFrame(outer, fg_color=CP_BG_CARD, corner_radius=12)
        switcher_card.pack(fill="x", pady=(0, 8))

        sw_inner = ctk.CTkFrame(switcher_card, fg_color="transparent")
        sw_inner.pack(fill="x", padx=14, pady=10)

        self.content_switcher = ctk.CTkSegmentedButton(
            sw_inner,
            values=["🔧  Моды", "🎨  Ресурспаки"],
            command=self._switch_content_panel,
            font=ctk.CTkFont(size=13, weight="bold"), height=36)
        self.content_switcher.pack(side="left")
        self.content_switcher.set("🔧  Моды")

        # Счётчик результатов
        self._content_count_label = ctk.CTkLabel(sw_inner, text="",
            font=ctk.CTkFont(size=11), text_color=CP_ACCENT,
            fg_color=CP_BG_PANEL, corner_radius=8)
        self._content_count_label.pack(side="right", ipadx=10, ipady=3)

        # ── Панели ──
        self.mods_panel = ctk.CTkFrame(outer, fg_color="transparent")
        self.mods_panel.pack(fill="both", expand=True)
        self._build_mods_panel(self.mods_panel)

        self.rp_panel = ctk.CTkFrame(outer, fg_color="transparent")
        self._build_rp_panel(self.rp_panel)

    def _switch_content_panel(self, value):
        if value == "🔧  Моды":
            self.rp_panel.pack_forget()
            self.mods_panel.pack(fill="both", expand=True)
        else:
            self.mods_panel.pack_forget()
            self.rp_panel.pack(fill="both", expand=True)

    def _build_mods_panel(self, parent):
        # ── Поиск и фильтры ──
        search_card = ctk.CTkFrame(parent, fg_color=CP_BG_CARD, corner_radius=12)
        search_card.pack(fill="x", pady=(0, 6))

        # Строка 1: версия + поиск
        row1 = ctk.CTkFrame(search_card, fg_color="transparent")
        row1.pack(fill="x", padx=12, pady=(10, 4))

        ctk.CTkLabel(row1, text="Версия:", text_color="#5a7aaa",
                     font=ctk.CTkFont(size=12)).pack(side="left", padx=(0, 4))
        self.mod_version_combo = ctk.CTkComboBox(row1, values=["Загрузка..."], width=110,
                                                  fg_color=CP_BG_PANEL, border_color=CP_BLUE,
                                                  corner_radius=8)
        self.mod_version_combo.pack(side="left", padx=(0, 10))
        self.mod_version_combo.configure(command=self.on_mod_version_change)

        self.mod_search_entry = ctk.CTkEntry(row1, placeholder_text="🔍  Поиск мода...",
                                              fg_color=CP_BG_PANEL, border_color=CP_BLUE,
                                              corner_radius=8)
        self.mod_search_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.mod_search_entry.bind("<Return>", lambda e: self.search_mods())

        self.mod_search_btn = ctk.CTkButton(row1, text="Найти", command=self.search_mods,
                                             width=80, fg_color=CP_BLUE, hover_color=CP_BLUE_HOVER,
                                             corner_radius=8)
        self.mod_search_btn.pack(side="left", padx=(0, 6))

        self.top_mods_btn = ctk.CTkButton(row1, text="⭐ Топ", command=self.fetch_top_mods,
                                           width=70, fg_color=CP_BG_PANEL, hover_color=CP_BLUE_DARK,
                                           border_width=1, border_color=CP_BLUE, corner_radius=8)
        self.top_mods_btn.pack(side="left", padx=(0, 4))

        self.delete_selected_btn = ctk.CTkButton(row1, text="🗑️", width=36,
                                                  command=self.delete_selected_mods,
                                                  fg_color="#7a1e1e", hover_color="#a02020",
                                                  corner_radius=8)
        self.delete_selected_btn.pack(side="left")

        # Строка 2: жанры (теги)
        tags_row = ctk.CTkFrame(search_card, fg_color="transparent")
        tags_row.pack(fill="x", padx=12, pady=(0, 10))

        ctk.CTkLabel(tags_row, text="Жанр:", text_color="#5a7aaa",
                     font=ctk.CTkFont(size=12)).pack(side="left", padx=(0, 8))

        GENRES = [
            ("Все", ""),
            ("⚡ Оптимизация", "optimization"),
            ("⚔️ Приключения", "adventure"),
            ("🌍 Генерация", "world-generation"),
            ("⚙️ Технологии", "technology"),
            ("🔮 Магия", "magic"),
            ("🏠 Строительство", "decoration"),
            ("🐾 Мобы", "mobs"),
            ("🎒 Инвентарь", "utility"),
            ("🍖 Еда", "food"),
            ("🗺️ Миникарта", "map"),
            ("📦 Библиотека", "library"),
        ]

        self._genre_buttons = {}
        self._active_genre = ""
        genre_scroll = ctk.CTkScrollableFrame(tags_row, orientation="horizontal",
                                               fg_color="transparent", height=36)
        genre_scroll.pack(side="left", fill="x", expand=True)

        for label, slug in GENRES:
            is_active = (slug == "")
            btn = ctk.CTkButton(genre_scroll, text=label,
                                width=0, height=28, corner_radius=14,
                                fg_color=CP_BLUE if is_active else CP_BG_PANEL,
                                hover_color=CP_BLUE_HOVER,
                                border_width=1, border_color=CP_BLUE,
                                font=ctk.CTkFont(size=11),
                                command=lambda s=slug, l=label: self._select_genre(s))
            btn.pack(side="left", padx=3, pady=2)
            self._genre_buttons[slug] = btn

        # Сортировка (маленькая, справа)
        sort_frame = ctk.CTkFrame(search_card, fg_color="transparent")
        sort_frame.pack(fill="x", padx=12, pady=(0, 8))
        ctk.CTkLabel(sort_frame, text="Сортировка:", text_color="#5a7aaa",
                     font=ctk.CTkFont(size=11)).pack(side="left", padx=(0, 4))
        self.mod_sort_combo = ctk.CTkComboBox(sort_frame, values=["Популярности", "Дате обновления"],
                                               width=160, fg_color=CP_BG_PANEL, border_color=CP_BLUE,
                                               corner_radius=8, font=ctk.CTkFont(size=11))
        self.mod_sort_combo.pack(side="left")
        self.mod_sort_combo.set("Популярности")
        # убрали старый mod_category_combo — заменён тегами
        self.mod_category_combo = self.mod_sort_combo  # алиас чтобы не падало

        # ── Результаты ──
        self.mod_results_frame = ctk.CTkScrollableFrame(parent, fg_color=CP_BG_PANEL,
                                                         corner_radius=10)
        self.mod_results_frame.pack(fill="both", expand=True, pady=4)

        # ── Пагинация ──
        bottom = ctk.CTkFrame(parent, fg_color=CP_BG_CARD, corner_radius=8)
        bottom.pack(fill="x", pady=(4, 0))
        self.mod_prev_page_btn = ctk.CTkButton(bottom, text="◀", command=self.mod_prev_page,
                                                state="disabled", width=60, corner_radius=8,
                                                fg_color=CP_BG_PANEL, border_width=1, border_color=CP_BLUE)
        self.mod_prev_page_btn.pack(side="left", padx=10, pady=8)
        self.mod_page_label = ctk.CTkLabel(bottom, text="", text_color="#5a7aaa",
                                            font=ctk.CTkFont(size=11))
        self.mod_page_label.pack(side="left", padx=6)
        self.mod_next_page_btn = ctk.CTkButton(bottom, text="▶", command=self.mod_next_page,
                                                state="disabled", width=60, corner_radius=8,
                                                fg_color=CP_BG_PANEL, border_width=1, border_color=CP_BLUE)
        self.mod_next_page_btn.pack(side="left", padx=4)
        self.mod_status_label = ctk.CTkLabel(bottom, text="", text_color="#5a7aaa",
                                              font=ctk.CTkFont(size=11))
        self.mod_status_label.pack(side="right", padx=14)

    def _select_genre(self, slug):
        """Переключение активного жанра"""
        self._active_genre = slug
        for s, btn in self._genre_buttons.items():
            btn.configure(fg_color=CP_BLUE if s == slug else CP_BG_PANEL)
        # Сохраняем в current_mod_category и перезапускаем поиск
        MOD_CATEGORIES = {
            "": None, "optimization": "optimization", "adventure": "adventure",
            "world-generation": "world-generation", "technology": "technology",
            "magic": "magic", "decoration": "decoration", "mobs": "mobs",
            "utility": "utility", "food": "food", "map": "map", "library": "library",
        }
        self.current_mod_category = slug
        self.current_mod_offset = 0
        self.load_mods_page()

    def _build_rp_panel(self, parent):
        # ── Установленные ресурспаки ──
        inst_card = ctk.CTkFrame(parent, fg_color=CP_BG_CARD, corner_radius=12)
        inst_card.pack(fill="x", pady=(0, 8))

        inst_hdr = ctk.CTkFrame(inst_card, fg_color="transparent")
        inst_hdr.pack(fill="x", padx=14, pady=(10, 6))
        ctk.CTkLabel(inst_hdr, text="📁  Установленные ресурспаки",
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color="#8aaed4").pack(side="left")
        ctk.CTkButton(inst_hdr, text="📂 Загрузить с ПК",
                      command=self.add_resourcepack_from_file,
                      width=150, fg_color=CP_BLUE, hover_color=CP_BLUE_HOVER,
                      corner_radius=8).pack(side="right")

        self.installed_rp_frame = ctk.CTkScrollableFrame(inst_card, height=110,
                                                          fg_color=CP_BG_PANEL, corner_radius=8)
        self.installed_rp_frame.pack(fill="x", padx=12, pady=(0, 12))
        self.update_resourcepacks_list()

        # ── Поиск ресурспаков ──
        search_card = ctk.CTkFrame(parent, fg_color=CP_BG_CARD, corner_radius=12)
        search_card.pack(fill="x", pady=(0, 6))

        row1 = ctk.CTkFrame(search_card, fg_color="transparent")
        row1.pack(fill="x", padx=12, pady=(10, 4))

        ctk.CTkLabel(row1, text="Версия:", text_color="#5a7aaa",
                     font=ctk.CTkFont(size=12)).pack(side="left", padx=(0, 4))
        self.rp_version_combo = ctk.CTkComboBox(row1, values=["Загрузка..."], width=110,
                                                  fg_color=CP_BG_PANEL, border_color=CP_BLUE,
                                                  corner_radius=8)
        self.rp_version_combo.pack(side="left", padx=(0, 10))
        self.rp_version_combo.configure(command=self.on_rp_version_change)

        self.rp_search_entry = ctk.CTkEntry(row1, placeholder_text="🔍  Поиск ресурспака...",
                                             fg_color=CP_BG_PANEL, border_color=CP_BLUE,
                                             corner_radius=8)
        self.rp_search_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.rp_search_entry.bind("<Return>", lambda e: self.search_resourcepacks())

        self.rp_search_btn = ctk.CTkButton(row1, text="Найти",
                                            command=self.search_resourcepacks,
                                            width=80, fg_color=CP_BLUE, hover_color=CP_BLUE_HOVER,
                                            corner_radius=8)
        self.rp_search_btn.pack(side="left", padx=(0, 6))

        self.top_rp_btn = ctk.CTkButton(row1, text="⭐ Топ",
                                         command=self.fetch_top_resourcepacks,
                                         width=70, fg_color=CP_BG_PANEL, hover_color=CP_BLUE_DARK,
                                         border_width=1, border_color=CP_BLUE, corner_radius=8)
        self.top_rp_btn.pack(side="left")

        row2 = ctk.CTkFrame(search_card, fg_color="transparent")
        row2.pack(fill="x", padx=12, pady=(0, 10))
        ctk.CTkLabel(row2, text="Сортировка:", text_color="#5a7aaa",
                     font=ctk.CTkFont(size=11)).pack(side="left", padx=(0, 4))
        self.rp_sort_combo = ctk.CTkComboBox(row2, values=["Популярности", "Дате обновления"],
                                              width=160, fg_color=CP_BG_PANEL, border_color=CP_BLUE,
                                              corner_radius=8, font=ctk.CTkFont(size=11))
        self.rp_sort_combo.pack(side="left")
        self.rp_sort_combo.set("Популярности")

        # ── Результаты ──
        self.rp_results_frame = ctk.CTkScrollableFrame(parent, fg_color=CP_BG_PANEL,
                                                        corner_radius=10)
        self.rp_results_frame.pack(fill="both", expand=True, pady=4)

        # ── Пагинация ──
        bottom = ctk.CTkFrame(parent, fg_color=CP_BG_CARD, corner_radius=8)
        bottom.pack(fill="x", pady=(4, 0))
        self.rp_prev_page_btn = ctk.CTkButton(bottom, text="◀", command=self.rp_prev_page,
                                               state="disabled", width=60, corner_radius=8,
                                               fg_color=CP_BG_PANEL, border_width=1, border_color=CP_BLUE)
        self.rp_prev_page_btn.pack(side="left", padx=10, pady=8)
        self.rp_page_label = ctk.CTkLabel(bottom, text="", text_color="#5a7aaa",
                                           font=ctk.CTkFont(size=11))
        self.rp_page_label.pack(side="left", padx=6)
        self.rp_next_page_btn = ctk.CTkButton(bottom, text="▶", command=self.rp_next_page,
                                               state="disabled", width=60, corner_radius=8,
                                               fg_color=CP_BG_PANEL, border_width=1, border_color=CP_BLUE)
        self.rp_next_page_btn.pack(side="left", padx=4)
        self.rp_status_label = ctk.CTkLabel(bottom, text="", text_color="#5a7aaa",
                                             font=ctk.CTkFont(size=11))
        self.rp_status_label.pack(side="right", padx=14)

    def create_mods_tab(self):
        pass  # заменено на create_content_tab

    def create_resourcepacks_tab(self):
        pass  # заменено на create_content_tab

    def create_stats_tab(self):
        frame = ctk.CTkScrollableFrame(self.tab_stats, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=12, pady=10)

        # ── Заголовок ──
        header = ctk.CTkFrame(frame, fg_color=CP_BG_CARD, corner_radius=12)
        header.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(header, text="📊  Статистика игрового времени",
                     font=ctk.CTkFont(size=18, weight="bold"), text_color="white").pack(side="left", padx=18, pady=14)
        ctk.CTkButton(header, text="🗑️ Сбросить", command=self.reset_stats,
                      fg_color="#7a1e1e", hover_color="#a02020",
                      width=110, corner_radius=8).pack(side="right", padx=14, pady=10)

        # ── Три карточки ──
        cards_row = ctk.CTkFrame(frame, fg_color="transparent")
        cards_row.pack(fill="x", pady=(0, 12))
        cards_row.columnconfigure(0, weight=1)
        cards_row.columnconfigure(1, weight=1)
        cards_row.columnconfigure(2, weight=1)

        def make_stat_card(parent, col, icon, label, attr_name, color):
            card = ctk.CTkFrame(parent, fg_color=CP_BG_CARD, corner_radius=14)
            card.grid(row=0, column=col, padx=6, sticky="ew")

            ctk.CTkLabel(card, text=icon, font=ctk.CTkFont(size=32)).pack(pady=(18, 4))
            ctk.CTkLabel(card, text=label, font=ctk.CTkFont(size=12),
                         text_color="#5a7aaa").pack()
            lbl = ctk.CTkLabel(card, text="—", font=ctk.CTkFont(size=22, weight="bold"),
                               text_color=color)
            lbl.pack(pady=(6, 4))
            bar = ctk.CTkProgressBar(card, height=6, corner_radius=4,
                                     progress_color=color, fg_color=CP_BG_PANEL)
            bar.pack(fill="x", padx=18, pady=(0, 18))
            bar.set(0)
            setattr(self, attr_name, lbl)
            setattr(self, attr_name + "_bar", bar)

        make_stat_card(cards_row, 0, "📅", "За 7 дней",   "stats_label_7d",    CP_ACCENT)
        make_stat_card(cards_row, 1, "🗓️", "За 30 дней",  "stats_label_30d",   "#7c4dff")
        make_stat_card(cards_row, 2, "🏆", "За всё время","stats_label_total",  "#ff9800")

        # ── Последние сессии ──
        sessions_card = ctk.CTkFrame(frame, fg_color=CP_BG_CARD, corner_radius=14)
        sessions_card.pack(fill="both", expand=True)

        ctk.CTkLabel(sessions_card, text="🕒  Последние сессии",
                     font=ctk.CTkFont(size=14, weight="bold"), text_color="#8aaed4").pack(
            anchor="w", padx=18, pady=(14, 6))
        ctk.CTkFrame(sessions_card, height=1, fg_color=CP_BLUE_DARK).pack(fill="x", padx=18)

        self.sessions_frame = ctk.CTkScrollableFrame(sessions_card, fg_color="transparent", height=220)
        self.sessions_frame.pack(fill="both", expand=True, padx=6, pady=6)

        # Заполняем данными сразу после построения
        self.after_idle(self.update_stats_display)

    def update_stats_display(self):
        if not hasattr(self, "stats_label_7d"):
            return
        total_7d   = self.stats_manager.get_total_time(7)
        total_30d  = self.stats_manager.get_total_time(30)
        total_all  = self.stats_manager.get_total_time()

        self.stats_label_7d.configure(text=self.stats_manager.format_time(total_7d))
        self.stats_label_30d.configure(text=self.stats_manager.format_time(total_30d))
        self.stats_label_total.configure(text=self.stats_manager.format_time(total_all))

        # Прогресс-бары относительно всего времени
        if total_all > 0:
            self.stats_label_7d_bar.set(min(total_7d / total_all, 1.0))
            self.stats_label_30d_bar.set(min(total_30d / total_all, 1.0))
            self.stats_label_total_bar.set(1.0)
        else:
            self.stats_label_7d_bar.set(0)
            self.stats_label_30d_bar.set(0)
            self.stats_label_total_bar.set(0)

        # Последние сессии
        if hasattr(self, "sessions_frame"):
            for w in self.sessions_frame.winfo_children():
                w.destroy()
            sessions = self.stats_manager.data.get("sessions", [])
            if not sessions:
                ctk.CTkLabel(self.sessions_frame, text="Сессий пока нет. Запустите игру!",
                             text_color="#5a7aaa", font=ctk.CTkFont(size=13)).pack(pady=20)
            else:
                for s in reversed(sessions[-15:]):
                    self._make_session_row(s)

    def _make_session_row(self, session):
        row = ctk.CTkFrame(self.sessions_frame, fg_color=CP_BG_PANEL, corner_radius=8)
        row.pack(fill="x", padx=6, pady=3)

        start_dt = datetime.fromtimestamp(session.get("start", 0))
        date_str = start_dt.strftime("%d.%m.%Y  %H:%M")
        dur = self.stats_manager.format_time(session.get("duration", 0))

        ctk.CTkLabel(row, text="🎮", font=ctk.CTkFont(size=16), width=32).pack(side="left", padx=(10, 4), pady=8)
        ctk.CTkLabel(row, text=date_str, font=ctk.CTkFont(size=12),
                     text_color="#8aaed4").pack(side="left", padx=4)
        ctk.CTkLabel(row, text=f"⏱ {dur}", font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=CP_ACCENT).pack(side="right", padx=14)

    def reset_stats(self):
        if messagebox.askyesno("Подтверждение", "Вы уверены, что хотите сбросить всю статистику?"):
            self.stats_manager.clear()
            self.update_stats_display()
            messagebox.showinfo("Готово", "Статистика сброшена")

    def create_news_tab(self):
        outer = ctk.CTkFrame(self.tab_news, fg_color="transparent")
        outer.pack(fill="both", expand=True, padx=12, pady=10)

        # ── Левая панель: версии Minecraft ──
        left = ctk.CTkFrame(outer, fg_color="transparent")
        left.pack(side="left", fill="both", expand=True, padx=(0, 6))

        # Заголовок
        lhdr = ctk.CTkFrame(left, fg_color=CP_BG_CARD, corner_radius=12)
        lhdr.pack(fill="x", pady=(0, 6))
        ctk.CTkLabel(lhdr, text="⛏️  Версии Minecraft",
                     font=ctk.CTkFont(size=15, weight="bold")).pack(side="left", padx=16, pady=12)
        self._news_mc_badge = ctk.CTkLabel(lhdr, text="",
                                            font=ctk.CTkFont(size=11), text_color=CP_ACCENT,
                                            fg_color=CP_BG_PANEL, corner_radius=8)
        self._news_mc_badge.pack(side="right", padx=12, pady=10, ipadx=8, ipady=3)

        # Список версий
        self.versions_scroll = ctk.CTkScrollableFrame(left, fg_color=CP_BG_CARD,
                                                       corner_radius=12, height=260)
        self.versions_scroll.pack(fill="x", pady=(0, 6))
        self.version_buttons = []

        # Карточка с описанием
        info_card = ctk.CTkFrame(left, fg_color=CP_BG_CARD, corner_radius=12)
        info_card.pack(fill="both", expand=True)

        info_hdr = ctk.CTkFrame(info_card, fg_color="transparent")
        info_hdr.pack(fill="x", padx=14, pady=(10, 4))
        self._selected_ver_label = ctk.CTkLabel(info_hdr, text="Выберите версию",
                                                 font=ctk.CTkFont(size=13, weight="bold"),
                                                 text_color=CP_ACCENT)
        self._selected_ver_label.pack(side="left")

        ctk.CTkFrame(info_card, height=1, fg_color=CP_BLUE_DARK).pack(fill="x", padx=14)

        self.mc_version_info = ctk.CTkTextbox(info_card, wrap="word",
                                               fg_color="transparent",
                                               font=ctk.CTkFont(size=12),
                                               text_color="#c8d8f0")
        self.mc_version_info.pack(fill="both", expand=True, padx=14, pady=10)
        self.mc_version_info.insert("0.0", "👈  Выберите версию слева чтобы увидеть изменения")
        self.mc_version_info.configure(state="disabled")

        # ── Правая панель: история лаунчера ──
        right = ctk.CTkFrame(outer, fg_color="transparent", width=340)
        right.pack(side="right", fill="both", padx=(6, 0))
        right.pack_propagate(False)

        rhdr = ctk.CTkFrame(right, fg_color=CP_BG_CARD, corner_radius=12)
        rhdr.pack(fill="x", pady=(0, 6))
        ctk.CTkLabel(rhdr, text="🚀  История лаунчера",
                     font=ctk.CTkFont(size=15, weight="bold")).pack(side="left", padx=16, pady=12)
        ctk.CTkLabel(rhdr, text=f"v{self.launcher_version}",
                     font=ctk.CTkFont(size=11), text_color=CP_ACCENT,
                     fg_color=CP_BG_PANEL, corner_radius=8).pack(side="right", padx=12, pady=10, ipadx=8, ipady=3)

        self._launcher_history_frame = ctk.CTkScrollableFrame(right, fg_color="transparent",
                                                               corner_radius=0)
        self._launcher_history_frame.pack(fill="both", expand=True)
        self._build_launcher_history()

    def _build_launcher_history(self):
        for ver in LAUNCHER_VERSIONS:
            card = ctk.CTkFrame(self._launcher_history_frame, fg_color=CP_BG_CARD, corner_radius=12)
            card.pack(fill="x", pady=4)

            # Шапка карточки
            hdr = ctk.CTkFrame(card, fg_color="transparent")
            hdr.pack(fill="x", padx=14, pady=(10, 6))

            ctk.CTkLabel(hdr, text=f"v{ver['version']}",
                         font=ctk.CTkFont(size=14, weight="bold"),
                         text_color=CP_ACCENT).pack(side="left")
            ctk.CTkLabel(hdr, text=ver['date'],
                         font=ctk.CTkFont(size=11), text_color="#5a7aaa").pack(side="right")

            ctk.CTkFrame(card, height=1, fg_color=CP_BLUE_DARK).pack(fill="x", padx=14)

            # Список изменений
            for change in ver['changes']:
                row = ctk.CTkFrame(card, fg_color="transparent")
                row.pack(fill="x", padx=14, pady=1)
                ctk.CTkLabel(row, text="•", text_color=CP_ACCENT,
                             font=ctk.CTkFont(size=12), width=14).pack(side="left")
                ctk.CTkLabel(row, text=change, font=ctk.CTkFont(size=11),
                             text_color="#c8d8f0", wraplength=260, justify="left",
                             anchor="w").pack(side="left", fill="x", expand=True)

            ctk.CTkFrame(card, height=6, fg_color="transparent").pack()

    def update_launcher_news(self):
        pass  # теперь строится в _build_launcher_history

    def update_mc_news(self):
        if not hasattr(self, "version_buttons"):
            return
            try: btn.destroy()
            except: pass
        self.version_buttons.clear()

        if self.all_versions and self.all_versions[0] != "Загрузка...":
            # Обновляем счётчик
            self._news_mc_badge.configure(text=f"{len(self.all_versions)} версий")

            # Цвета для типов версий
            for ver in self.all_versions:
                try:
                    parts = ver.split(".")
                    color = CP_ACCENT if len(parts) >= 2 and int(parts[1]) >= 20 else "#5a7aaa"
                except (ValueError, IndexError):
                    color = "#5a7aaa"

                row = ctk.CTkFrame(self.versions_scroll, fg_color="transparent")
                row.pack(fill="x", pady=1)

                dot = ctk.CTkLabel(row, text="●", text_color=color,
                                   font=ctk.CTkFont(size=10), width=18)
                dot.pack(side="left", padx=(8, 2))

                btn = ctk.CTkButton(row, text=ver, anchor="w",
                                    fg_color="transparent",
                                    hover_color=CP_BG_CARD,
                                    text_color="white",
                                    font=ctk.CTkFont(size=12),
                                    command=lambda v=ver: self.show_mc_version_info(v))
                btn.pack(side="left", fill="x", expand=True)
                self.version_buttons.append(row)

            if self.all_versions:
                self.show_mc_version_info(self.all_versions[0])
        else:
            lbl = ctk.CTkLabel(self.versions_scroll, text="⏳ Загрузка версий...",
                               text_color="#5a7aaa")
            lbl.pack(pady=20)
            self.version_buttons.append(lbl)

    def show_mc_version_info(self, version):
        self._selected_ver_label.configure(text=f"⛏️  Minecraft {version}")
        self.mc_version_info.configure(state="normal")
        self.mc_version_info.delete("0.0", "end")
        info = MINECRAFT_VERSION_INFO.get(version, "📋  Описание для этой версии пока не добавлено.")
        self.mc_version_info.insert("0.0", info)
        self.mc_version_info.configure(state="disabled")

    # ---------- Логика профилей ----------
    def on_profile_selected(self, choice):
        self.apply_profile(choice)

    def apply_profile(self, profile_name):
        profile = self.profile_manager.get_profile(profile_name)
        if not profile:
            return
        self.current_profile = profile_name
        self.username_entry.delete(0, "end")
        self.username_entry.insert(0, profile.get("username", "Steve"))
        self.profile_version = profile.get("version", "")
        self.profile_combo.set(profile_name)
        if self.firebase.is_logged_in:
            self.refresh_friends_list()

    def save_current_profile(self):
        data = {
            "username": self.username_entry.get(),
            "version": self.version_combo.get() if self.version_combo.get() not in ["Нет установленных", "Обновление..."] else "",
            "memory": int(self.config.get("default_memory", 2048)),
            "java_path": self.config.get("default_java", ""),
            "jvm_args": self.config.get("default_jvm_args", ""),
            "loader": None
        }
        self.profile_manager.update_profile(self.current_profile, data)
        messagebox.showinfo("Профиль", f"Профиль '{self.current_profile}' сохранён")

    def save_profile_as(self):
        dialog = ctk.CTkInputDialog(text="Введите имя нового профиля:", title="Сохранить как")
        new_name = dialog.get_input()
        if new_name and new_name.strip():
            new_name = new_name.strip()
            if new_name in self.profile_manager.get_profile_names():
                messagebox.showerror("Ошибка", "Профиль с таким именем уже существует")
                return
            data = {
                "username": self.username_entry.get(),
                "version": self.version_combo.get() if self.version_combo.get() not in ["Нет установленных", "Обновление..."] else "",
                "memory": int(self.config.get("default_memory", 2048)),
                "java_path": self.config.get("default_java", ""),
                "jvm_args": self.config.get("default_jvm_args", ""),
                "loader": None,
                "last_seen": 0
            }
            self.profile_manager.add_profile(new_name, data)
            self.profile_combo.configure(values=self.profile_manager.get_profile_names())
            self.profile_combo.set(new_name)
            self.current_profile = new_name
            self.username_entry.delete(0, "end")
            self.username_entry.insert(0, new_name)
            self.update_friends_list()
            messagebox.showinfo("Профиль", f"Профиль '{new_name}' создан")

    def delete_profile(self):
        if self.current_profile == "Default":
            messagebox.showerror("Ошибка", "Нельзя удалить профиль Default")
            return
        if messagebox.askyesno("Подтверждение", f"Удалить профиль '{self.current_profile}'?"):
            self.profile_manager.delete_profile(self.current_profile)
            self.profile_combo.configure(values=self.profile_manager.get_profile_names())
            self.profile_combo.set("Default")
            self.apply_profile("Default")
            self.update_friends_list()

    # ---------- Управление версиями с кэшированием ----------
    def load_all_versions(self, force_refresh=False):
        def fetch():
            try:
                if not force_refresh:
                    cached = self.version_cache.get_versions()
                    if cached:
                        self.all_versions = cached
                        self.after_idle(self.update_all_versions_ui)
                        self.after_idle(self.update_mc_news)
                        self.after_idle(self.update_version_selectors)
                        return

                response = requests.get(
                    "https://launchermeta.mojang.com/mc/game/version_manifest_v2.json",
                    timeout=30
                )
                response.raise_for_status()
                data = response.json()

                def version_key(v):
                    parts = v.split('.')
                    key = []
                    for p in parts:
                        try: key.append(int(p))
                        except ValueError: key.append(999)
                    return key

                release_versions = [v["id"] for v in data["versions"] if v["type"] == "release"]
                self.all_versions = sorted(release_versions, key=version_key, reverse=True)
                self.version_cache.save(self.all_versions)
            except Exception as e:
                print(f"Ошибка загрузки версий: {e}")
                self.all_versions = ["1.21.4", "1.21.3", "1.21.1", "1.20.4"]
            finally:
                self.after_idle(self.update_all_versions_ui)
                self.after_idle(self.update_mc_news)
                self.after_idle(self.update_version_selectors)
        Thread(target=fetch).start()

    def update_version_selectors(self):
        if not hasattr(self, "mod_version_combo") or not hasattr(self, "rp_version_combo"):
            return
        versions = self.all_versions if self.all_versions and self.all_versions[0] != "Загрузка..." else ["Загрузка..."]
        self.mod_version_combo.configure(values=versions)
        self.rp_version_combo.configure(values=versions)
        if versions and versions[0] != "Загрузка...":
            default_version = versions[0]
            self.mod_version_combo.set(default_version)
            self.rp_version_combo.set(default_version)
            self.current_mod_version = default_version
            self.current_rp_version = default_version

    def update_all_versions_ui(self):
        if not hasattr(self, "loader_version_combo"):
            return
        self.loader_version_combo.configure(values=self.all_versions)
        if self.all_versions:
            self.loader_version_combo.set(self.all_versions[0])

        for widget in self.all_versions_listbox.winfo_children():
            widget.destroy()

        for ver in self.all_versions:
            row = ctk.CTkFrame(self.all_versions_listbox, fg_color="transparent")
            row.pack(fill="x", pady=1)
            ctk.CTkLabel(row, text="●", text_color=CP_ACCENT,
                         font=ctk.CTkFont(size=9), width=16).pack(side="left", padx=(8, 2))
            btn = ctk.CTkButton(row, text=ver, anchor="w",
                                fg_color="transparent", hover_color=CP_BG_CARD,
                                text_color="white", font=ctk.CTkFont(size=12), height=28,
                                command=lambda v=ver: self.select_version(v))
            btn.pack(side="left", fill="x", expand=True)

    def _quick_launch(self, version):
        """Быстрый запуск из вкладки версий"""
        self.version_combo.set(version)
        self.tabview.set("🎮  Игра")
        self.launch_game()

    def select_version(self, version):
        self.loader_version_combo.set(version)

    def update_installed_versions(self):
        versions_dir = os.path.join(self.minecraft_directory, "versions")
        installed = []
        if os.path.exists(versions_dir):
            installed = [d for d in os.listdir(versions_dir) if os.path.isdir(os.path.join(versions_dir, d))]
        self.installed_versions = installed
        if installed:
            self.version_combo.configure(values=installed)
            if hasattr(self, 'profile_version') and self.profile_version in installed:
                self.version_combo.set(self.profile_version)
            else:
                self.version_combo.set(installed[0])
        else:
            self.version_combo.configure(values=["Нет установленных"])
            self.version_combo.set("Нет установленных")

    def toggle_all_versions(self):
        if self.show_all_btn.cget("text") == "Показать все версии":
            self.version_combo.configure(values=self.all_versions)
            self.show_all_btn.configure(text="Показать установленные")
        else:
            self.update_installed_versions()
            self.show_all_btn.configure(text="Показать все версии")

    def on_version_selected(self, choice):
        self.version_info_text.configure(state="normal")
        self.version_info_text.delete("0.0", "end")
        if choice and choice not in ["Нет установленных", "Обновление..."]:
            json_path = os.path.join(self.minecraft_directory, "versions", choice, f"{choice}.json")
            if os.path.exists(json_path):
                try:
                    with open(json_path, "r") as f:
                        data = json.load(f)
                    info = f"ID: {data.get('id', 'unknown')}\nТип: {data.get('type', 'unknown')}\nВерсия assets: {data.get('assets', 'unknown')}\nMain class: {data.get('mainClass', 'unknown')}"
                    self.version_info_text.insert("0.0", info)
                except:
                    self.version_info_text.insert("0.0", "Не удалось прочитать информацию")
            else:
                self.version_info_text.insert("0.0", "Информация отсутствует")
        self.version_info_text.configure(state="disabled")

    def on_version_scroll(self, event):
        values = self.version_combo.cget("values")
        if not values or values[0] in ["Нет установленных", "Обновление..."]:
            return
        current = self.version_combo.get()
        try:
            idx = values.index(current)
        except ValueError:
            idx = 0
        if event.delta > 0:
            idx = (idx - 1) % len(values)
        else:
            idx = (idx + 1) % len(values)
        self.version_combo.set(values[idx])

    # ---------- Установка мод-лоадеров ----------
    def install_loader(self, loader_type):
        version = self.loader_version_combo.get()
        if not version or version in ["Загрузка..."]:
            messagebox.showerror("Ошибка", "Выберите версию Minecraft")
            return

        self.loader_status.configure(text=f"Установка {loader_type} для {version}...")
        self.forge_btn.configure(state="disabled")
        self.fabric_btn.configure(state="disabled")
        self.quilt_btn.configure(state="disabled")
        self.optifine_btn.configure(state="disabled")
        Thread(target=self._install_loader_thread, args=(loader_type, version)).start()

    def _install_loader_thread(self, loader_type, version):
        try:
            if loader_type == "forge":
                try:
                    self.after_idle(lambda: self.loader_status.configure(text=f"Forge: получение списка версий для {version}..."))
                except RuntimeError:
                    return
                forge_versions = minecraft_launcher_lib.forge.list_forge_versions()
                matching = [fv for fv in forge_versions if fv.startswith(version)]
                if not matching:
                    try:
                        self.after_idle(lambda: self.loader_status.configure(text=f"Forge не найден для {version}"))
                    except RuntimeError:
                        pass
                    return
                latest_forge = matching[-1]
                try:
                    self.after_idle(lambda: self.loader_status.configure(text=f"Установка {latest_forge}..."))
                except RuntimeError:
                    return

                callback_dict = {
                    "setStatus": lambda status: self.after_idle(lambda: self.loader_status.configure(text=f"Forge: {status}")),
                    "setProgress": lambda *args: None
                }
                minecraft_launcher_lib.forge.install_forge_version(latest_forge, self.minecraft_directory, callback=callback_dict)
                try:
                    self.after_idle(lambda: self.loader_status.configure(text="Forge установлен!"))
                except RuntimeError:
                    pass

            elif loader_type == "fabric":
                try:
                    self.after_idle(lambda: self.loader_status.configure(text="Fabric: установка..."))
                except RuntimeError:
                    return
                callback_dict = {
                    "setStatus": lambda status: self.after_idle(lambda: self.loader_status.configure(text=f"Fabric: {status}")),
                    "setProgress": lambda *args: None
                }
                minecraft_launcher_lib.fabric.install_fabric(version, self.minecraft_directory, callback=callback_dict)
                try:
                    self.after_idle(lambda: self.loader_status.configure(text="Fabric установлен!"))
                except RuntimeError:
                    pass

            elif loader_type == "quilt":
                try:
                    self.after_idle(lambda: self.loader_status.configure(text="Quilt: используется Fabric (совместимость)..."))
                except RuntimeError:
                    return
                callback_dict = {
                    "setStatus": lambda status: self.after_idle(lambda: self.loader_status.configure(text=f"Quilt (Fabric): {status}")),
                    "setProgress": lambda *args: None
                }
                minecraft_launcher_lib.fabric.install_fabric(version, self.minecraft_directory, callback=callback_dict)
                try:
                    self.after_idle(lambda: self.loader_status.configure(text="Quilt-совместимый Fabric установлен!"))
                except RuntimeError:
                    pass

            elif loader_type == "optifine":
                try:
                    self.after_idle(lambda: self.loader_status.configure(text="OptiFine: функция в разработке"))
                except RuntimeError:
                    pass
                return

            try:
                self.after_idle(self.update_installed_versions)
            except RuntimeError:
                pass

        except Exception as e:
            try:
                self.after_idle(lambda: self.loader_status.configure(text=f"Ошибка: {str(e)}"))
            except RuntimeError:
                pass
            traceback.print_exc()
        finally:
            try:
                self.after_idle(lambda: self.forge_btn.configure(state="normal"))
                self.after_idle(lambda: self.fabric_btn.configure(state="normal"))
                self.after_idle(lambda: self.quilt_btn.configure(state="normal"))
                self.after_idle(lambda: self.optifine_btn.configure(state="normal"))
            except RuntimeError:
                pass

    # ---------- Запуск игры ----------
    def launch_game(self):
        username = self.username_entry.get().strip()
        if not username:
            messagebox.showerror("Ошибка", "Введите никнейм")
            return
        version = self.version_combo.get()
        if version in ["Нет установленных", "Обновление...", ""]:
            messagebox.showerror("Ошибка", "Выберите версию")
            return

        self.launch_btn.configure(state="disabled", text="Запуск...")
        self.progress_bar.set(0)
        self.game_start_time = time.time()
        Thread(target=self._launch_thread, args=(username, version)).start()

    def _launch_thread(self, username, version):
        try:
            self.after_idle(lambda: self.set_status(f"Подготовка {version}..."))
            callback_dict = {
                "setStatus": lambda s: self.after_idle(lambda: self.set_status(s)),
                "setProgress": lambda *args: self.after_idle(lambda: self._on_set_progress(*args))
            }
            minecraft_launcher_lib.install.install_minecraft_version(version, self.minecraft_directory, callback=callback_dict)
            self.after_idle(lambda: self.set_status("Запуск игры..."))
            self.after_idle(lambda: self.set_progress(90))

            memory = int(self.config.get("default_memory", 2048))
            jvm_args = [f"-Xmx{memory}M", "-XX:+UnlockExperimentalVMOptions", "-XX:+UseG1GC"]
            if self.config.get("default_jvm_args"):
                jvm_args.extend(self.config["default_jvm_args"].split())
            options = {
                "username": username,
                "uuid": "",
                "token": "",
                "jvmArguments": jvm_args,
                "gameDirectory": self.minecraft_directory,
                "launcherName": "My Launcher"
            }
            if self.config.get("default_java"):
                options["executablePath"] = self.config["default_java"]
            command = minecraft_launcher_lib.command.get_minecraft_command(version, self.minecraft_directory, options)

            # Запускаем без консоли
            si = subprocess.STARTUPINFO()
            si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            si.wShowWindow = subprocess.SW_HIDE
            subprocess.run(command, startupinfo=si,
                           creationflags=subprocess.CREATE_NO_WINDOW)

            if self.game_start_time is not None:
                end_time = time.time()
                self.stats_manager.add_session(self.game_start_time, end_time)
                self.profile_manager.update_last_seen(self.current_profile)
                self.game_start_time = None
                self.after_idle(self.update_stats_display)
                self.after_idle(self.update_friends_list)

            self.after_idle(lambda: self.set_status("Игра закрыта"))
            self.after_idle(lambda: self.set_progress(0))
        except Exception as e:
            self.after_idle(lambda: self.set_status(f"Ошибка: {str(e)}"))
            traceback.print_exc()
        finally:
            self.after_idle(lambda: self.launch_btn.configure(state="normal", text="Играть"))

    def set_status(self, text):
        self.progress_label.configure(text=text)

    def set_progress(self, value, max_value=100):
        self.progress_bar.set(value / max_value)

    def _on_set_progress(self, *args):
        if len(args) == 1:
            if isinstance(args[0], dict):
                data = args[0]
                if "progress" in data and "max" in data:
                    self.set_progress(data["progress"], data["max"])
                elif "progress" in data:
                    self.set_progress(data["progress"], 100)
            else:
                self.set_progress(args[0] * 100, 100)
        elif len(args) == 2:
            self.set_progress(args[0], args[1])

    # ---------- Моды ----------
    def on_mod_version_change(self, choice):
        self.current_mod_version = choice

    # Маппинг русских категорий → Modrinth slug
    MOD_CATEGORIES = {
        "Все категории":      None,
        "⚡ Оптимизация":     "optimization",
        "🗺️ Приключения":     "adventure",
        "🌍 Генерация мира":  "worldgen",
        "⚔️ Оружие и броня":  "equipment",
        "🏠 Строительство":   "decoration",
        "🔮 Магия":           "magic",
        "⚙️ Технологии":      "technology",
        "🎒 Инвентарь":       "storage",
        "🐾 Мобы":            "mobs",
        "🍖 Еда":             "food",
        "🗿 Декор":           "decoration",
        "🔧 Утилиты":         "utility",
        "🧭 Миникарта":       "map-and-information",
        "🌐 Мультиплеер":     "social",
        "📦 Библиотека":      "library",
    }

    def search_mods(self):
        query = self.mod_search_entry.get().strip()
        self.current_mod_query = query
        self.current_mod_sort = self.mod_sort_combo.get()
        self.current_mod_category = getattr(self, "_active_genre", "")
        self.current_mod_offset = 0
        self.load_mods_page()

    def fetch_top_mods(self):
        self.current_mod_query = ""
        self.current_mod_sort = self.mod_sort_combo.get()
        self.current_mod_category = getattr(self, "_active_genre", "")
        self.current_mod_offset = 0
        self.load_mods_page()

    def load_mods_page(self):
        for widget in self.mod_results_frame.winfo_children():
            widget.destroy()
        self.mod_status_label.configure(text="Загрузка...")
        self.mod_prev_page_btn.configure(state="disabled")
        self.mod_next_page_btn.configure(state="disabled")
        category = getattr(self, "current_mod_category", "Все категории")
        Thread(target=self._fetch_mods_page, args=(
            self.current_mod_query, self.current_mod_sort,
            self.current_mod_offset, self.current_mod_version, category
        )).start()

    def _fetch_mods_page(self, query, sort_by, offset, game_version, category=""):
        try:
            # category теперь сразу slug (или "" = все)
            if category:
                facets = json.dumps([["project_type:mod"], [f"categories:{category}"]])
            else:
                facets = json.dumps([["project_type:mod"]])
            index = "downloads" if sort_by == "Популярности" else "updated"
            params = {"limit": self.mod_limit, "offset": offset, "facets": facets, "index": index}
            if query:
                params["query"] = query
            if game_version and game_version not in ["Загрузка..."]:
                params["versions"] = json.dumps([game_version])
            headers = {"User-Agent": "MyLauncher/1.0"}
            response = requests.get("https://api.modrinth.com/v2/search", params=params, headers=headers, timeout=15)
            response.raise_for_status()
            data = response.json()
            hits = data.get("hits", [])
            self.total_mod_hits = data.get("total_hits", 0)
            self.after_idle(lambda: self.display_mod_results(hits, offset))
        except Exception as e:
            self.after_idle(lambda: self.mod_status_label.configure(text=f"Ошибка: {str(e)}"))
            traceback.print_exc()

    def display_mod_results(self, hits, offset):
        if not hits:
            self.mod_status_label.configure(text="Ничего не найдено")
            return
        self.mod_status_label.configure(text=f"Найдено {self.total_mod_hits} модов")
        for mod in hits:
            mod_frame = ctk.CTkFrame(self.mod_results_frame)
            mod_frame.pack(fill="x", pady=5, padx=5)
            icon_label = ctk.CTkLabel(mod_frame, text="", width=40, height=40)
            icon_label.pack(side="left", padx=5, pady=5)
            info_frame = ctk.CTkFrame(mod_frame, fg_color="transparent")
            info_frame.pack(side="left", fill="both", expand=True, padx=5)

            title = mod.get("title", "Без названия")
            description = mod.get("description", "")[:100] + "..." if mod.get("description") else ""
            author = mod.get("author", "Неизвестный автор")
            versions = mod.get("versions", [])
            versions_str = ", ".join(versions[:5])
            if len(versions) > 5:
                versions_str += " и др."

            ctk.CTkLabel(info_frame, text=title, font=ctk.CTkFont(weight="bold", size=14)).pack(anchor="w")
            ctk.CTkLabel(info_frame, text=f"Автор: {author}", font=ctk.CTkFont(size=11)).pack(anchor="w")
            ctk.CTkLabel(info_frame, text=description, font=ctk.CTkFont(size=11), wraplength=400).pack(anchor="w")
            ctk.CTkLabel(info_frame, text=f"Версии: {versions_str}", font=ctk.CTkFont(size=10, slant="italic")).pack(anchor="w")

            mod_id = mod.get("project_id")
            filter_version = self.current_mod_version
            if filter_version and filter_version not in ["Загрузка..."]:
                btn = ctk.CTkButton(mod_frame, text="Установить",
                                    command=lambda mid=mod_id, v=filter_version: self.install_mod(mid, v))
                btn.pack(side="right", padx=10, pady=10)
            icon_url = mod.get("icon_url")
            if icon_url:
                Thread(target=self.load_mod_icon, args=(icon_url, mod_id, icon_label, "mod")).start()
            else:
                icon_label.configure(text="🖼️")
        current_page = offset // self.mod_limit + 1
        total_pages = (self.total_mod_hits + self.mod_limit - 1) // self.mod_limit
        self.mod_page_label.configure(text=f"Страница {current_page} из {total_pages}")
        self.mod_prev_page_btn.configure(state="normal" if offset > 0 else "disabled")
        self.mod_next_page_btn.configure(state="normal" if offset + self.mod_limit < self.total_mod_hits else "disabled")

    def mod_prev_page(self):
        if self.current_mod_offset >= self.mod_limit:
            self.current_mod_offset -= self.mod_limit
            self.load_mods_page()

    def mod_next_page(self):
        if self.current_mod_offset + self.mod_limit < self.total_mod_hits:
            self.current_mod_offset += self.mod_limit
            self.load_mods_page()

    def install_mod(self, project_id, game_version):
        Thread(target=self._fetch_mod_versions, args=(project_id, game_version)).start()

    def _fetch_mod_versions(self, project_id, game_version):
        try:
            self.after_idle(lambda: self.mod_status_label.configure(text="Получение версий..."))
            params = {"game_versions": json.dumps([game_version])}
            headers = {"User-Agent": "MyLauncher/1.0"}
            response = requests.get(f"https://api.modrinth.com/v2/project/{project_id}/version",
                                    params=params, headers=headers, timeout=15)
            response.raise_for_status()
            versions = response.json()
            if not versions:
                self.after_idle(lambda: messagebox.showerror("Ошибка", "Нет совместимых версий мода для этой версии игры"))
                return
            self.after_idle(lambda: self.show_mod_version_selector(project_id, versions))
        except Exception as e:
            self.after_idle(lambda: messagebox.showerror("Ошибка", f"Не удалось получить версии: {str(e)}"))

    def show_mod_version_selector(self, project_id, versions):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Выбор версии мода")
        dialog.geometry("400x300")
        dialog.transient(self)
        dialog.grab_set()

        ctk.CTkLabel(dialog, text="Доступные версии мода:", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=10)

        scroll = ctk.CTkScrollableFrame(dialog, height=200)
        scroll.pack(fill="both", expand=True, padx=10, pady=5)

        for ver in versions:
            ver_name = ver.get("name", "Неизвестно")
            ver_number = ver.get("version_number", "?")
            btn = ctk.CTkButton(scroll, text=f"{ver_name} ({ver_number})",
                                command=lambda v=ver: self._download_mod_version(project_id, v, dialog))
            btn.pack(fill="x", pady=2)

        ctk.CTkButton(dialog, text="Отмена", command=dialog.destroy).pack(pady=10)

    def _download_mod_version(self, project_id, version_data, dialog):
        dialog.destroy()
        files = version_data.get("files", [])
        if not files:
            messagebox.showerror("Ошибка", "У этой версии нет файлов для скачивания")
            return
        file_info = files[0]
        url = file_info["url"]
        filename = file_info["filename"]
        self.mod_status_label.configure(text=f"Скачивание {filename}...")
        Thread(target=self._download_mod_file, args=(url, filename)).start()

    def _download_mod_file(self, url, filename):
        try:
            headers = {"User-Agent": "MyLauncher/1.0"}
            r = requests.get(url, stream=True, headers=headers, timeout=30)
            r.raise_for_status()
            path = os.path.join(self.mods_directory, filename)
            with open(path, "wb") as f:
                for chunk in r.iter_content(8192):
                    f.write(chunk)
            self.after_idle(lambda: self.mod_status_label.configure(text=f"✅ Мод {filename} установлен"))
            self.after_idle(self.update_mods_list)
        except Exception as e:
            self.after_idle(lambda: self.mod_status_label.configure(text=f"❌ Ошибка: {str(e)}"))

    # ---------- Установленные моды (с чекбоксами и включением) ----------
    def update_mods_list(self):
        for widget in self.mods_listbox.winfo_children():
            widget.destroy()

        self.mod_checkboxes = []

        if os.path.exists(self.mods_directory):
            all_files = os.listdir(self.mods_directory)
            mod_entries = []
            for f in all_files:
                if f.endswith(".jar"):
                    mod_entries.append((f, True))
                elif f.endswith(".jar.disabled"):
                    original = f[:-9]
                    mod_entries.append((original, False))

            mods_dict = {}
            for name, active in mod_entries:
                if name in mods_dict:
                    if active:
                        mods_dict[name] = True
                else:
                    mods_dict[name] = active

            if mods_dict:
                header = ctk.CTkLabel(self.mods_listbox, text=f"📦 Установлено модов: {len(mods_dict)}",
                                      font=ctk.CTkFont(size=14, weight="bold"))
                header.pack(anchor="w", padx=10, pady=5)

                for mod_name, active in sorted(mods_dict.items()):
                    self.create_mod_card(mod_name, active)
            else:
                no_mods = ctk.CTkLabel(self.mods_listbox, text="✨ Моды не установлены", font=ctk.CTkFont(size=14))
                no_mods.pack(expand=True, pady=50)
        else:
            no_mods = ctk.CTkLabel(self.mods_listbox, text="✨ Моды не установлены", font=ctk.CTkFont(size=14))
            no_mods.pack(expand=True, pady=50)

    def create_mod_card(self, mod_name, active):
        card = ctk.CTkFrame(self.mods_listbox, corner_radius=10, fg_color="#2a2a3a")
        card.pack(fill="x", padx=10, pady=5)

        var = ctk.BooleanVar(value=False)
        chk = ctk.CTkCheckBox(card, text="", variable=var, width=20)
        chk.pack(side="left", padx=5)
        self.mod_checkboxes.append((var, mod_name))

        icon_label = ctk.CTkLabel(card, text="📦", font=ctk.CTkFont(size=24), width=40)
        icon_label.pack(side="left", padx=5, pady=10)

        name_label = ctk.CTkLabel(card, text=mod_name, font=ctk.CTkFont(size=14, weight="bold"))
        name_label.pack(side="left", padx=5, pady=10, fill="x", expand=True)

        enabled_var = ctk.BooleanVar(value=active)
        enabled_check = ctk.CTkCheckBox(card, text="Включён", variable=enabled_var,
                                        command=lambda n=mod_name, v=enabled_var: self.toggle_mod(n, v))
        enabled_check.pack(side="right", padx=5)

        delete_btn = ctk.CTkButton(card, text="🗑️", width=30, height=30, corner_radius=5,
                                   fg_color="#b53a3a", hover_color="#c54a4a",
                                   command=lambda n=mod_name: self.delete_single_mod(n))
        delete_btn.pack(side="right", padx=10, pady=10)

    def toggle_mod(self, mod_name, var):
        active = var.get()
        base_path = os.path.join(self.mods_directory, mod_name)
        if active:
            disabled_path = base_path + ".disabled"
            if os.path.exists(disabled_path):
                os.rename(disabled_path, base_path)
        else:
            if os.path.exists(base_path):
                os.rename(base_path, base_path + ".disabled")
        self.update_mods_list()

    def delete_single_mod(self, mod_name):
        if messagebox.askyesno("Подтверждение", f"Удалить мод {mod_name}?"):
            try:
                base_path = os.path.join(self.mods_directory, mod_name)
                disabled_path = base_path + ".disabled"
                if os.path.exists(base_path):
                    os.remove(base_path)
                if os.path.exists(disabled_path):
                    os.remove(disabled_path)
                self.update_mods_list()
                messagebox.showinfo("Готово", "✅ Мод удалён")
            except Exception as e:
                messagebox.showerror("Ошибка", f"❌ Не удалось удалить мод: {e}")

    def delete_selected_mods(self):
        selected = [name for var, name in self.mod_checkboxes if var.get()]
        if not selected:
            messagebox.showwarning("Удаление", "Не выбрано ни одного мода")
            return
        if messagebox.askyesno("Подтверждение", f"Удалить выбранные моды ({len(selected)} шт.)?"):
            for mod_name in selected:
                try:
                    base_path = os.path.join(self.mods_directory, mod_name)
                    disabled_path = base_path + ".disabled"
                    if os.path.exists(base_path):
                        os.remove(base_path)
                    if os.path.exists(disabled_path):
                        os.remove(disabled_path)
                except Exception as e:
                    print(f"Ошибка при удалении {mod_name}: {e}")
            self.update_mods_list()
            messagebox.showinfo("Готово", "✅ Выбранные моды удалены")

    # ---------- Ресурспаки ----------
    def on_rp_version_change(self, choice):
        self.current_rp_version = choice

    def search_resourcepacks(self):
        query = self.rp_search_entry.get().strip()
        if not query:
            messagebox.showwarning("Поиск", "Введите название ресурспака")
            return
        self.current_rp_query = query
        self.current_rp_sort = self.rp_sort_combo.get()
        self.current_rp_offset = 0
        self.load_resourcepacks_page()

    def fetch_top_resourcepacks(self):
        self.current_rp_query = ""
        self.current_rp_sort = self.rp_sort_combo.get()
        self.current_rp_offset = 0
        self.load_resourcepacks_page()

    def load_resourcepacks_page(self):
        for widget in self.rp_results_frame.winfo_children():
            widget.destroy()
        self.rp_status_label.configure(text="Загрузка...")
        self.rp_prev_page_btn.configure(state="disabled")
        self.rp_next_page_btn.configure(state="disabled")
        Thread(target=self._fetch_resourcepacks_page, args=(self.current_rp_query, self.current_rp_sort, self.current_rp_offset, self.current_rp_version)).start()

    def _fetch_resourcepacks_page(self, query, sort_by, offset, game_version):
        try:
            facets = json.dumps([["project_type:resourcepack"]])
            index = "downloads" if sort_by == "Популярности" else "updated"
            params = {"limit": self.rp_limit, "offset": offset, "facets": facets, "index": index}
            if query:
                params["query"] = query
            if game_version and game_version not in ["Загрузка..."]:
                params["versions"] = json.dumps([game_version])
            headers = {"User-Agent": "MyLauncher/1.0"}
            response = requests.get("https://api.modrinth.com/v2/search", params=params, headers=headers, timeout=15)
            response.raise_for_status()
            data = response.json()
            hits = data.get("hits", [])
            self.total_rp_hits = data.get("total_hits", 0)
            self.after_idle(lambda: self.display_resourcepack_results(hits, offset))
        except Exception as e:
            self.after_idle(lambda: self.rp_status_label.configure(text=f"Ошибка: {str(e)}"))
            traceback.print_exc()

    def display_resourcepack_results(self, hits, offset):
        if not hits:
            self.rp_status_label.configure(text="Ничего не найдено")
            return
        self.rp_status_label.configure(text=f"Найдено {self.total_rp_hits} ресурспаков")
        for rp in hits:
            rp_frame = ctk.CTkFrame(self.rp_results_frame)
            rp_frame.pack(fill="x", pady=5, padx=5)
            icon_label = ctk.CTkLabel(rp_frame, text="", width=40, height=40)
            icon_label.pack(side="left", padx=5, pady=5)
            info_frame = ctk.CTkFrame(rp_frame, fg_color="transparent")
            info_frame.pack(side="left", fill="both", expand=True, padx=5)

            title = rp.get("title", "Без названия")
            description = rp.get("description", "")[:100] + "..." if rp.get("description") else ""
            author = rp.get("author", "Неизвестный автор")
            versions = rp.get("versions", [])
            versions_str = ", ".join(versions[:5])
            if len(versions) > 5:
                versions_str += " и др."

            ctk.CTkLabel(info_frame, text=title, font=ctk.CTkFont(weight="bold", size=14)).pack(anchor="w")
            ctk.CTkLabel(info_frame, text=f"Автор: {author}", font=ctk.CTkFont(size=11)).pack(anchor="w")
            ctk.CTkLabel(info_frame, text=description, font=ctk.CTkFont(size=11), wraplength=400).pack(anchor="w")
            ctk.CTkLabel(info_frame, text=f"Версии: {versions_str}", font=ctk.CTkFont(size=10, slant="italic")).pack(anchor="w")

            project_id = rp.get("project_id")
            filter_version = self.current_rp_version
            if filter_version and filter_version not in ["Загрузка..."]:
                btn = ctk.CTkButton(rp_frame, text="📥 Установить",
                                    command=lambda pid=project_id, v=filter_version: self.install_resourcepack(pid, v))
                btn.pack(side="right", padx=10, pady=10)
            icon_url = rp.get("icon_url")
            if icon_url:
                Thread(target=self.load_mod_icon, args=(icon_url, project_id, icon_label, "rp")).start()
            else:
                icon_label.configure(text="🖼️")
        current_page = offset // self.rp_limit + 1
        total_pages = (self.total_rp_hits + self.rp_limit - 1) // self.rp_limit
        self.rp_page_label.configure(text=f"Страница {current_page} из {total_pages}")
        self.rp_prev_page_btn.configure(state="normal" if offset > 0 else "disabled")
        self.rp_next_page_btn.configure(state="normal" if offset + self.rp_limit < self.total_rp_hits else "disabled")

    def rp_prev_page(self):
        if self.current_rp_offset >= self.rp_limit:
            self.current_rp_offset -= self.rp_limit
            self.load_resourcepacks_page()

    def rp_next_page(self):
        if self.current_rp_offset + self.rp_limit < self.total_rp_hits:
            self.current_rp_offset += self.rp_limit
            self.load_resourcepacks_page()

    def install_resourcepack(self, project_id, game_version):
        Thread(target=self._fetch_resourcepack_versions, args=(project_id, game_version)).start()

    def _fetch_resourcepack_versions(self, project_id, game_version):
        try:
            self.after_idle(lambda: self.rp_status_label.configure(text="Получение версий..."))
            headers = {"User-Agent": "MyLauncher/1.0"}
            response = requests.get(f"https://api.modrinth.com/v2/project/{project_id}/version", headers=headers, timeout=15)
            response.raise_for_status()
            versions = response.json()
            if not versions:
                self.after_idle(lambda: messagebox.showerror("Ошибка", "Нет доступных версий ресурспака"))
                return
            self.after_idle(lambda: self.show_resourcepack_version_selector(project_id, versions))
        except Exception as e:
            self.after_idle(lambda: messagebox.showerror("Ошибка", f"Не удалось получить версии: {str(e)}"))

    def show_resourcepack_version_selector(self, project_id, versions):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Выбор версии ресурспака")
        dialog.geometry("400x300")
        dialog.transient(self)
        dialog.grab_set()

        ctk.CTkLabel(dialog, text="Доступные версии ресурспака:", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=10)

        scroll = ctk.CTkScrollableFrame(dialog, height=200)
        scroll.pack(fill="both", expand=True, padx=10, pady=5)

        for ver in versions:
            ver_name = ver.get("name", "Неизвестно")
            ver_number = ver.get("version_number", "?")
            btn = ctk.CTkButton(scroll, text=f"{ver_name} ({ver_number})",
                                command=lambda v=ver: self._download_resourcepack_version(project_id, v, dialog))
            btn.pack(fill="x", pady=2)

        ctk.CTkButton(dialog, text="Отмена", command=dialog.destroy).pack(pady=10)

    def _download_resourcepack_version(self, project_id, version_data, dialog):
        dialog.destroy()
        files = version_data.get("files", [])
        if not files:
            messagebox.showerror("Ошибка", "У этой версии нет файлов для скачивания")
            return
        file_info = files[0]
        url = file_info["url"]
        filename = file_info["filename"]
        self.rp_status_label.configure(text=f"Скачивание {filename}...")
        Thread(target=self._download_resourcepack_file, args=(url, filename)).start()

    def _download_resourcepack_file(self, url, filename):
        try:
            headers = {"User-Agent": "MyLauncher/1.0"}
            r = requests.get(url, stream=True, headers=headers, timeout=30)
            r.raise_for_status()
            path = os.path.join(self.resourcepacks_directory, filename)
            with open(path, "wb") as f:
                for chunk in r.iter_content(8192):
                    f.write(chunk)
            self.after_idle(lambda: self.rp_status_label.configure(text=f"✅ Ресурспак {filename} установлен"))
            self.after_idle(self.update_resourcepacks_list)
        except Exception as e:
            self.after_idle(lambda: self.rp_status_label.configure(text=f"❌ Ошибка: {str(e)}"))

    def update_resourcepacks_list(self):
        for widget in self.installed_rp_frame.winfo_children():
            widget.destroy()

        if not os.path.exists(self.resourcepacks_directory):
            os.makedirs(self.resourcepacks_directory)

        all_files = os.listdir(self.resourcepacks_directory)
        pack_files = []
        for f in all_files:
            if f.endswith(('.zip', '.jar')):
                pack_files.append((f, True))
            elif f.endswith('.zip.disabled') or f.endswith('.jar.disabled'):
                original = f[:-9]
                pack_files.append((original, False))

        packs_dict = {}
        for name, active in pack_files:
            base = name
            if base in packs_dict:
                if active:
                    packs_dict[base] = True
            else:
                packs_dict[base] = active

        if not packs_dict:
            no_packs = ctk.CTkLabel(self.installed_rp_frame, text="✨ Ресурспаки не установлены", font=ctk.CTkFont(size=14))
            no_packs.pack(expand=True, pady=20)
            return

        header = ctk.CTkLabel(self.installed_rp_frame, text=f"📦 Установлено ресурспаков: {len(packs_dict)}",
                               font=ctk.CTkFont(size=14, weight="bold"))
        header.pack(anchor="w", padx=10, pady=5)

        for pack_name, active in sorted(packs_dict.items()):
            self.create_resourcepack_card(pack_name, active)

    def create_resourcepack_card(self, pack_name, active):
        card = ctk.CTkFrame(self.installed_rp_frame, corner_radius=10, fg_color="#2a2a3a")
        card.pack(fill="x", padx=10, pady=5)

        icon_label = ctk.CTkLabel(card, text="🎨", font=ctk.CTkFont(size=24), width=40)
        icon_label.pack(side="left", padx=10, pady=10)

        name_label = ctk.CTkLabel(card, text=pack_name, font=ctk.CTkFont(size=14, weight="bold"))
        name_label.pack(side="left", padx=5, pady=10, fill="x", expand=True)

        var = ctk.BooleanVar(value=active)
        check = ctk.CTkCheckBox(card, text="", variable=var, width=20,
                                 command=lambda n=pack_name, v=var: self.toggle_resourcepack(n, v))
        check.pack(side="right", padx=5)

        delete_btn = ctk.CTkButton(card, text="🗑️", width=30, height=30, corner_radius=5,
                                   fg_color="#b53a3a", hover_color="#c54a4a",
                                   command=lambda n=pack_name: self.delete_resourcepack(n))
        delete_btn.pack(side="right", padx=10, pady=10)

    def toggle_resourcepack(self, pack_name, var):
        active = var.get()
        base_path = os.path.join(self.resourcepacks_directory, pack_name)
        if active:
            disabled_path = base_path + ".disabled"
            if os.path.exists(disabled_path):
                os.rename(disabled_path, base_path)
        else:
            if os.path.exists(base_path):
                os.rename(base_path, base_path + ".disabled")
        self.update_resourcepacks_list()

    def delete_resourcepack(self, pack_name):
        if messagebox.askyesno("Подтверждение", f"Удалить ресурспак {pack_name}?"):
            try:
                base_path = os.path.join(self.resourcepacks_directory, pack_name)
                disabled_path = base_path + ".disabled"
                if os.path.exists(base_path):
                    os.remove(base_path)
                if os.path.exists(disabled_path):
                    os.remove(disabled_path)
                self.update_resourcepacks_list()
                messagebox.showinfo("Готово", "✅ Ресурспак удалён")
            except Exception as e:
                messagebox.showerror("Ошибка", f"❌ Не удалось удалить ресурспак: {e}")

    def add_resourcepack_from_file(self):
        file_path = filedialog.askopenfilename(
            title="Выберите ресурспак",
            filetypes=[("Resource pack files", "*.zip *.jar"), ("All files", "*.*")]
        )
        if file_path:
            try:
                dest = os.path.join(self.resourcepacks_directory, os.path.basename(file_path))
                if os.path.exists(dest):
                    if not messagebox.askyesno("Подтверждение", f"Файл {os.path.basename(file_path)} уже существует. Перезаписать?"):
                        return
                shutil.copy2(file_path, dest)
                self.update_resourcepacks_list()
                messagebox.showinfo("Готово", f"✅ Ресурспак {os.path.basename(file_path)} установлен")
            except Exception as e:
                messagebox.showerror("Ошибка", f"❌ Не удалось скопировать файл: {e}")

    # ---------- Общая загрузка иконок с ограничением ----------
    def load_mod_icon(self, url, item_id, label_widget, item_type):
        cache_key = f"{item_type}_{item_id}"
        if cache_key in self.icon_cache:
            self.after_idle(lambda: label_widget.configure(image=self.icon_cache[cache_key], text=""))
            return

        def _load():
            with self.icon_semaphore:
                try:
                    response = requests.get(url, timeout=10)
                    response.raise_for_status()
                    img_data = response.content
                    pil_image = Image.open(BytesIO(img_data))
                    pil_image = pil_image.resize((32, 32), Image.Resampling.LANCZOS)
                    ctk_image = ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=(32, 32))
                    self.icon_cache[cache_key] = ctk_image
                    self.after_idle(lambda: label_widget.configure(image=ctk_image, text=""))
                except Exception as e:
                    print(f"Ошибка загрузки иконки для {item_id}: {e}")
                    self.after_idle(lambda: label_widget.configure(text="🖼️"))

        Thread(target=_load).start()

    # ---------- Автоматическое обновление ----------
    def check_for_updates(self):
        def _check():
            updater = Updater(self.launcher_version, UPDATE_URL)
            if updater.check_for_updates():
                self.after(0, lambda: self.prompt_update(updater))
        Thread(target=_check).start()

    def prompt_update(self, updater):
        version = updater.update_info["version"]
        changes = "\n".join(updater.update_info["changes"])
        if messagebox.askyesno("Обновление", f"Доступна новая версия {version}\n\nИзменения:\n{changes}\n\nОбновить сейчас?"):
            self.download_and_update(updater)

    def download_and_update(self, updater):
        # Скачиваем во временную папку
        temp_dir = tempfile.gettempdir()
        new_exe = os.path.join(temp_dir, "launcher_new.exe")
        self.status_label = ctk.CTkLabel(self.tab_settings, text="Скачивание обновления...")
        self.status_label.pack()
        if updater.download_update(new_exe):
            updater.apply_update(new_exe)
        else:
            messagebox.showerror("Ошибка", "Не удалось скачать обновление")

    # ---------- Глобальные настройки ----------
    def change_theme(self, choice):
        ctk.set_appearance_mode(choice)
        self.config["theme"] = choice
        self.save_config()

    def _on_mem_slider(self, value):
        # Округляем до ближайших 512 МБ
        mb = round(value / 512) * 512
        mb = max(512, min(16384, mb))
        self.default_memory_var.set(str(mb))
        self.mem_value_label.configure(text=f"{mb} МБ")

    def save_global_settings(self):
        self.config["default_memory"] = int(self.default_memory_var.get())
        self.config["default_java"] = self.default_java_entry.get()
        self.config["default_jvm_args"] = self.default_jvm_entry.get("0.0", "end").strip()
        self.save_config()
        messagebox.showinfo("Настройки", "Глобальные настройки сохранены")

    def clear_cache(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Очистка кэша")
        dialog.geometry("440x400")
        dialog.resizable(False, False)
        dialog.configure(fg_color=CP_BG_PANEL)
        dialog.transient(self)
        dialog.after(100, dialog.grab_set)  # grab после отрисовки

        ctk.CTkLabel(dialog, text="🧹  Очистка кэша",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(18, 4))
        ctk.CTkLabel(dialog, text="Выберите что удалить:",
                     font=ctk.CTkFont(size=12), text_color="#5a7aaa").pack(pady=(0, 12))

        var_ver_cache  = ctk.BooleanVar(value=True)
        var_icon_cache = ctk.BooleanVar(value=True)
        var_versions   = ctk.BooleanVar(value=False)
        var_libraries  = ctk.BooleanVar(value=False)
        var_assets     = ctk.BooleanVar(value=False)
        var_mods       = ctk.BooleanVar(value=False)

        opts = ctk.CTkFrame(dialog, fg_color=CP_BG_CARD, corner_radius=12)
        opts.pack(fill="x", padx=20, pady=4)

        def make_row(parent, var, title, desc, color="white"):
            row = ctk.CTkFrame(parent, fg_color="transparent")
            row.pack(fill="x", padx=14, pady=5)
            ctk.CTkCheckBox(row, variable=var, text="", width=24).pack(side="left")
            txt = ctk.CTkFrame(row, fg_color="transparent")
            txt.pack(side="left", padx=6)
            ctk.CTkLabel(txt, text=title, font=ctk.CTkFont(size=12, weight="bold"),
                         text_color=color, anchor="w").pack(anchor="w")
            ctk.CTkLabel(txt, text=desc, font=ctk.CTkFont(size=10),
                         text_color="#5a7aaa", anchor="w").pack(anchor="w")

        make_row(opts, var_ver_cache,  "Кэш списка версий",      "version_cache.json — обновит список версий MC",   CP_ACCENT)
        make_row(opts, var_icon_cache, "Кэш иконок модов",       "Очистит иконки модов из памяти")
        make_row(opts, var_versions,   "Установленные версии MC", "⚠️ Удалит все скачанные версии игры",             "#ff9800")
        make_row(opts, var_libraries,  "Библиотеки MC",           "⚠️ Скачаются заново при следующем запуске",       "#ff9800")
        make_row(opts, var_assets,     "Ресурсы MC (assets)",     "⚠️ Удалит звуки и текстуры ванили",               "#ff9800")
        make_row(opts, var_mods,       "Папка модов",             "⚠️ Удалит все моды из папки mods",                "#ff6b6b")

        status_lbl = ctk.CTkLabel(dialog, text="", font=ctk.CTkFont(size=11))
        status_lbl.pack(pady=6)

        def do_clear():
            cleared = []
            errors = []

            if var_ver_cache.get():
                try:
                    cache_path = os.path.join(self.minecraft_directory, VERSION_CACHE_FILE)
                    if os.path.exists(cache_path):
                        os.remove(cache_path)
                    self.version_cache.data = {"timestamp": 0, "versions": []}
                    cleared.append("кэш версий")
                except Exception as e:
                    errors.append(f"кэш версий: {e}")

            if var_icon_cache.get():
                self.icon_cache.clear()
                cleared.append("кэш иконок")

            for var, path, name in [
                (var_versions,  os.path.join(self.minecraft_directory, "versions"),  "версии"),
                (var_libraries, os.path.join(self.minecraft_directory, "libraries"), "библиотеки"),
                (var_assets,    os.path.join(self.minecraft_directory, "assets"),    "ресурсы"),
                (var_mods,      self.mods_directory,                                  "моды"),
            ]:
                if var.get():
                    try:
                        if os.path.exists(path):
                            shutil.rmtree(path)
                        os.makedirs(path, exist_ok=True)
                        cleared.append(name)
                    except Exception as e:
                        errors.append(f"{name}: {e}")

            if not cleared and not errors:
                status_lbl.configure(text="⚠️ Ничего не выбрано", text_color="orange")
                return

            self.update_installed_versions()
            if var_ver_cache.get():
                self.after(500, lambda: self.load_all_versions(force_refresh=True))

            if errors:
                status_lbl.configure(text=f"❌ {'; '.join(errors)}", text_color="#ff6b6b")
            else:
                status_lbl.configure(text=f"✅ Очищено: {', '.join(cleared)}", text_color=CP_ACCENT)

        btn_row = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_row.pack(pady=8)
        ctk.CTkButton(btn_row, text="🧹 Очистить", command=do_clear,
                      fg_color="#e67e22", hover_color="#d35400",
                      corner_radius=8, width=130).pack(side="left", padx=8)
        ctk.CTkButton(btn_row, text="Закрыть", command=dialog.destroy,
                      fg_color=CP_BG_CARD, hover_color=CP_BLUE_DARK,
                      corner_radius=8, width=100).pack(side="left", padx=8)


class ChatWindow(ctk.CTkToplevel):
    """Окно чата с другом"""
    def __init__(self, parent, firebase, friend_uid, friend_username):
        super().__init__(parent)
        self.firebase = firebase
        self.friend_uid = friend_uid
        self.friend_username = friend_username
        self._polling = True

        self.title(f"💬 Чат с {friend_username}")
        self.geometry("420x560")
        self.minsize(360, 440)
        self.configure(fg_color=CP_BG_PANEL)
        self.resizable(True, True)

        self._build_ui()
        self._load_messages()
        self._start_polling()

    def _build_ui(self):
        # Шапка
        header = ctk.CTkFrame(self, fg_color=CP_BG_CARD, corner_radius=0, height=48)
        header.pack(fill="x")
        header.pack_propagate(False)

        ctk.CTkLabel(header, text="👤", font=ctk.CTkFont(size=22)).pack(side="left", padx=12, pady=8)
        info = ctk.CTkFrame(header, fg_color="transparent")
        info.pack(side="left", pady=8)
        ctk.CTkLabel(info, text=self.friend_username,
                     font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w")
        self.status_lbl = ctk.CTkLabel(info, text="",
                                        font=ctk.CTkFont(size=10), text_color="#5a7aaa")
        self.status_lbl.pack(anchor="w")

        # Область сообщений
        self.msg_frame = ctk.CTkScrollableFrame(self, fg_color=CP_BG_PANEL, corner_radius=0)
        self.msg_frame.pack(fill="both", expand=True, padx=0, pady=0)

        # Поле ввода
        input_bar = ctk.CTkFrame(self, fg_color=CP_BG_CARD, corner_radius=0, height=56)
        input_bar.pack(fill="x", side="bottom")
        input_bar.pack_propagate(False)

        self.msg_entry = ctk.CTkEntry(input_bar, placeholder_text="Написать сообщение...",
                                       fg_color=CP_BG_PANEL, border_color=CP_BLUE,
                                       corner_radius=10, height=36,
                                       font=ctk.CTkFont(size=13))
        self.msg_entry.pack(side="left", fill="x", expand=True, padx=(10, 6), pady=10)
        self.msg_entry.bind("<Return>", lambda e: self._send())

        ctk.CTkButton(input_bar, text="➤", width=42, height=36,
                      fg_color=CP_BLUE, hover_color=CP_BLUE_HOVER, corner_radius=10,
                      font=ctk.CTkFont(size=16),
                      command=self._send).pack(side="right", padx=(0, 10), pady=10)

    def _load_messages(self):
        def do():
            msgs = self.firebase.get_messages(self.friend_uid)
            self.after_idle(lambda: self._display_messages(msgs))
        Thread(target=do).start()

    def _display_messages(self, msgs):
        for w in self.msg_frame.winfo_children():
            w.destroy()

        if not msgs:
            ctk.CTkLabel(self.msg_frame, text="Начните общение! 👋",
                         text_color="#5a7aaa", font=ctk.CTkFont(size=13)).pack(expand=True, pady=40)
            return

        for msg in msgs:
            self._add_bubble(msg)

        # Прокрутка вниз
        self.after(100, lambda: self.msg_frame._parent_canvas.yview_moveto(1.0))

    def _add_bubble(self, msg):
        is_mine = msg.get("from_uid") == self.firebase.current_uid
        ts = msg.get("timestamp", 0)
        time_str = datetime.fromtimestamp(ts).strftime("%H:%M") if ts else ""

        outer = ctk.CTkFrame(self.msg_frame, fg_color="transparent")
        outer.pack(fill="x", padx=10, pady=2)

        bubble_color = CP_BLUE if is_mine else CP_BG_CARD
        anchor = "e" if is_mine else "w"
        padx = (60, 6) if is_mine else (6, 60)

        bubble = ctk.CTkFrame(outer, fg_color=bubble_color, corner_radius=14)
        bubble.pack(anchor=anchor, padx=padx)

        ctk.CTkLabel(bubble, text=msg.get("text", ""),
                     font=ctk.CTkFont(size=13), wraplength=240,
                     justify="left").pack(padx=12, pady=(6, 2), anchor="w")
        ctk.CTkLabel(bubble, text=time_str,
                     font=ctk.CTkFont(size=9), text_color="#8aaed4").pack(padx=12, pady=(0, 5), anchor="e")

    def _send(self):
        text = self.msg_entry.get().strip()
        if not text:
            return
        self.msg_entry.delete(0, "end")

        def do():
            ok = self.firebase.send_message(self.friend_uid, text)
            if ok:
                self.after_idle(self._load_messages)
        Thread(target=do).start()

    def _start_polling(self):
        """Опрашиваем новые сообщения каждые 5 секунд"""
        if not self._polling:
            return
        self._load_messages()
        self.after(5000, self._start_polling)

    def destroy(self):
        self._polling = False
        super().destroy()


if __name__ == "__main__":
    app = MinecraftLauncher()
    app.mainloop()
