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

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

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
MINECRAFT_VERSION_INFO = {
    "1.21.4": "Дата выхода: 3 декабря 2024\n\nОсновные изменения:\n• Добавлены новые варианты испытаний в Trial Chambers\n• Улучшена производительность в биомах с густыми лесами\n• Исправлены ошибки с загрузкой чанков",
    "1.21.3": "Дата выхода: 22 октября 2024\n\nОсновные изменения:\n• Добавлена поддержка новых блоков в командных блоках\n• Улучшена работа редстоуна",
    "1.21.2": "Дата выхода: 10 сентября 2024\n\nОсновные изменения:\n• Оптимизирована генерация структур\n• Улучшена работа с памятью",
    "1.21.1": "Дата выхода: 20 августа 2024\n\nОсновные изменения:\n• Небольшие исправления после крупного обновления 1.21",
    "1.21": "Дата выхода: 13 июня 2024\n\nОсновные изменения (Tricky Trials):\n• Добавлены новые структуры: Trial Chambers\n• Новые мобы: Breeze, Bogged\n• Новые блоки и предметы",
    "1.20.4": "Дата выхода: 7 декабря 2023\n\nИсправления ошибок и улучшения стабильности",
    "1.20.2": "Дата выхода: 21 сентября 2023\n\nОсновные изменения:\n• Добавлены новые функции для командных блоков\n• Улучшена система крафта",
    "1.20.1": "Дата выхода: 12 июля 2023\n\nНебольшие исправления после выхода 1.20",
    "1.20": "Дата выхода: 7 июня 2023\n\nОсновные изменения (Trails & Tales):\n• Археологические раскопки\n• Новые мобы: верблюд, светящаяся каракатица\n• Новые блоки: бамбук, вишнёвая роща",
    "1.19.4": "Дата выхода: 14 марта 2023\n\nИсправления ошибок и улучшения",
    "1.19.3": "Дата выхода: 7 декабря 2022\n\nОсновные изменения:\n• Добавлены новые команды\n• Улучшена система мобов",
    "1.19.2": "Дата выхода: 5 августа 2022\n\nИсправления ошибок",
    "1.19.1": "Дата выхода: 27 июля 2022\n\nНебольшие исправления",
    "1.19": "Дата выхода: 7 июня 2022\n\nОсновные изменения (The Wild):\n• Новый биом: тёмные глубины\n• Новый моб: хранитель\n• Новые блоки: сколк",
    "1.18.2": "Дата выхода: 28 февраля 2022\n\nИсправления ошибок",
    "1.18.1": "Дата выхода: 10 декабря 2021\n\nНебольшие исправления",
    "1.18": "Дата выхода: 30 ноября 2021\n\nОсновные изменения (Caves & Cliffs: Part II):\n• Полностью переработана генерация пещер и гор\n• Новые мобы: козёл, аксолотль",
    "1.17.1": "Дата выхода: 6 июля 2021\n\nИсправления ошибок",
    "1.17": "Дата выхода: 8 июня 2021\n\nОсновные изменения (Caves & Cliffs: Part I):\n• Новые блоки: аметист, медь\n• Новые мобы: аксолотль, светящийся кальмар",
    "1.16.5": "Дата выхода: 15 января 2021\n\nИсправления ошибок",
    "1.16.4": "Дата выхода: 3 ноября 2020\n\nНебольшие исправления",
    "1.16.3": "Дата выхода: 10 сентября 2020\n\nИсправления ошибок",
    "1.16.2": "Дата выхода: 11 августа 2020\n\nОсновные изменения:\n• Добавлен новый материал: незерит",
    "1.16.1": "Дата выхода: 24 июня 2020\n\nИсправления ошибок",
    "1.16": "Дата выхода: 23 июня 2020\n\nОсновные изменения (Nether Update):\n• Полностью переработан Нижний мир\n• Новые биомы, мобы, блоки"
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

class FriendManager:
    """Управление друзьями (локально)"""
    def __init__(self, friends_file, profile_manager):
        self.friends_file = friends_file
        self.profile_manager = profile_manager
        self.friends = []
        self.load()

    def load(self):
        if os.path.exists(self.friends_file):
            try:
                with open(self.friends_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.friends = data.get("friends", [])
            except:
                self.friends = []
        else:
            self.friends = []

    def save(self):
        with open(self.friends_file, "w", encoding="utf-8") as f:
            json.dump({"friends": self.friends}, f, indent=4)

    def add_friend(self, username):
        if username not in self.profile_manager.get_profile_names():
            return False, "Профиль с таким именем не найден"
        if username in self.friends:
            return False, "Этот пользователь уже в друзьях"
        self.friends.append(username)
        self.save()
        return True, "Друг добавлен"

    def remove_friend(self, username):
        if username in self.friends:
            self.friends.remove(username)
            self.save()
            return True, "Друг удалён"
        return False, "Не найден в списке друзей"

    def get_friend_status(self, username, current_profile):
        profile = self.profile_manager.get_profile(username)
        if not profile:
            return "неизвестно"
        if username == current_profile:
            return "🟢 В сети"
        last_seen = profile.get("last_seen", 0)
        if last_seen:
            dt = datetime.fromtimestamp(last_seen)
            now = datetime.now()
            delta = now - dt
            if delta.days == 0:
                if delta.seconds < 3600:
                    return f"🔵 Был(а) {delta.seconds // 60} мин назад"
                else:
                    return f"🔵 Был(а) {delta.seconds // 3600} ч назад"
            elif delta.days == 1:
                return "🔵 Был(а) вчера"
            else:
                return f"🔵 Был(а) {delta.days} дн назад"
        return "⚪ Ещё не играл(а)"

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
        self.title("Minecraft Launcher")
        self.geometry("1000x650")
        self.resizable(True, True)
        self.minsize(1000, 650)

        # Текущая версия лаунчера
        self.launcher_version = "1.1.0"

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
        self.friend_manager = FriendManager(os.path.join(self.minecraft_directory, FRIENDS_FILE), self.profile_manager)

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

        # Создание интерфейса
        self.create_widgets()

        # Загрузка списка версий после старта цикла
        self.after(10, self.load_all_versions)
        self.update_installed_versions()
        self.apply_profile("Default")
        self.update_stats_display()

        # Проверка обновлений
        self.after(100, self.check_for_updates)

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
        # Вкладки
        self.tabview = ctk.CTkTabview(self, width=980, height=600)
        self.tabview.pack(pady=10, padx=10, fill="both", expand=True)

        self.tab_play = self.tabview.add("Игра")
        self.create_play_tab()

        self.tab_friends = self.tabview.add("Друзья")
        self.create_friends_tab()

        self.tab_versions = self.tabview.add("Версии и лоадеры")
        self.create_versions_tab()

        self.tab_settings = self.tabview.add("Настройки")
        self.create_settings_tab()

        self.tab_mods = self.tabview.add("Моды")
        self.create_mods_tab()

        self.tab_resourcepacks = self.tabview.add("Ресурспаки")
        self.create_resourcepacks_tab()

        self.tab_stats = self.tabview.add("Статистика")
        self.create_stats_tab()

        self.tab_news = self.tabview.add("Новости")
        self.create_news_tab()

    def create_play_tab(self):
        top_frame = ctk.CTkFrame(self.tab_play)
        top_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(top_frame, text="Профиль:").pack(side="left", padx=5)
        self.profile_combo = ctk.CTkComboBox(top_frame, values=self.profile_manager.get_profile_names(),
                                             command=self.on_profile_selected, width=200)
        self.profile_combo.pack(side="left", padx=5)
        self.profile_combo.set("Default")

        self.save_profile_btn = ctk.CTkButton(top_frame, text="Сохранить", command=self.save_current_profile, width=80)
        self.save_profile_btn.pack(side="left", padx=5)
        self.save_as_btn = ctk.CTkButton(top_frame, text="Сохранить как...", command=self.save_profile_as, width=100)
        self.save_as_btn.pack(side="left", padx=5)
        self.delete_profile_btn = ctk.CTkButton(top_frame, text="Удалить", command=self.delete_profile, width=80,
                                                fg_color="red", hover_color="darkred")
        self.delete_profile_btn.pack(side="left", padx=5)

        main_frame = ctk.CTkFrame(self.tab_play)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        left_panel = ctk.CTkFrame(main_frame, width=300)
        left_panel.pack(side="left", fill="y", padx=5, pady=5)

        ctk.CTkLabel(left_panel, text="Запуск игры", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=10)

        ctk.CTkLabel(left_panel, text="Никнейм:").pack(anchor="w", padx=10)
        self.username_entry = ctk.CTkEntry(left_panel, width=250)
        self.username_entry.pack(pady=5, padx=10)

        ctk.CTkLabel(left_panel, text="Версия (установленные):").pack(anchor="w", padx=10)
        self.version_combo = ctk.CTkComboBox(left_panel, values=["Обновление..."], width=250,
                                             command=self.on_version_selected)
        self.version_combo.pack(pady=5, padx=10)
        self.version_combo.bind("<MouseWheel>", self.on_version_scroll)

        self.show_all_btn = ctk.CTkButton(left_panel, text="Показать все версии", command=self.toggle_all_versions,
                                          width=120)
        self.show_all_btn.pack(pady=5)

        self.progress_label = ctk.CTkLabel(left_panel, text="")
        self.progress_label.pack(pady=10)
        self.progress_bar = ctk.CTkProgressBar(left_panel, width=250)
        self.progress_bar.pack(pady=5)
        self.progress_bar.set(0)

        self.launch_btn = ctk.CTkButton(left_panel, text="Играть", command=self.launch_game,
                                        width=200, height=40, font=ctk.CTkFont(size=16))
        self.launch_btn.pack(pady=20)

        right_panel = ctk.CTkFrame(main_frame)
        right_panel.pack(side="right", fill="both", expand=True, padx=5, pady=5)

        ctk.CTkLabel(right_panel, text="Информация о версии", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        self.version_info_text = ctk.CTkTextbox(right_panel, height=150, wrap="word")
        self.version_info_text.pack(fill="x", padx=10, pady=5)
        self.version_info_text.insert("0.0", "Выберите версию для просмотра информации")
        self.version_info_text.configure(state="disabled")

        ctk.CTkLabel(right_panel, text="Установленные моды", font=ctk.CTkFont(size=14)).pack(pady=5)
        self.mods_listbox = ctk.CTkScrollableFrame(right_panel, fg_color="#1a1a2a", corner_radius=10)
        self.mods_listbox.pack(fill="both", expand=True, padx=10, pady=5)
        self.update_mods_list()

    def create_friends_tab(self):
        frame = ctk.CTkFrame(self.tab_friends)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        top_panel = ctk.CTkFrame(frame)
        top_panel.pack(fill="x", pady=5)

        self.friend_entry = ctk.CTkEntry(top_panel, placeholder_text="Никнейм друга...", width=200)
        self.friend_entry.pack(side="left", padx=5)

        self.add_friend_btn = ctk.CTkButton(top_panel, text="Добавить друга", command=self.add_friend, width=120)
        self.add_friend_btn.pack(side="left", padx=5)

        self.friend_listbox = ctk.CTkScrollableFrame(frame, label_text="Список друзей")
        self.friend_listbox.pack(fill="both", expand=True, pady=10)

        self.friend_status_label = ctk.CTkLabel(frame, text="")
        self.friend_status_label.pack()

        self.update_friends_list()

    def update_friends_list(self):
        for widget in self.friend_listbox.winfo_children():
            widget.destroy()

        if not self.friend_manager.friends:
            lbl = ctk.CTkLabel(self.friend_listbox, text="У вас пока нет друзей. Добавьте кого-нибудь!")
            lbl.pack(pady=20)
            return

        for username in self.friend_manager.friends:
            status = self.friend_manager.get_friend_status(username, self.current_profile)
            self.create_friend_card(username, status)

    def create_friend_card(self, username, status):
        card = ctk.CTkFrame(self.friend_listbox, corner_radius=10, fg_color="#2a2a3a")
        card.pack(fill="x", padx=10, pady=5)

        avatar = ctk.CTkLabel(card, text="👤", font=ctk.CTkFont(size=24), width=40)
        avatar.pack(side="left", padx=10, pady=10)

        info_frame = ctk.CTkFrame(card, fg_color="transparent")
        info_frame.pack(side="left", fill="both", expand=True, padx=5)

        name_label = ctk.CTkLabel(info_frame, text=username, font=ctk.CTkFont(size=14, weight="bold"))
        name_label.pack(anchor="w")

        status_label = ctk.CTkLabel(info_frame, text=status, font=ctk.CTkFont(size=12))
        status_label.pack(anchor="w")

        switch_btn = ctk.CTkButton(card, text="Переключиться", width=100,
                                   command=lambda u=username: self.switch_to_friend(u))
        switch_btn.pack(side="right", padx=10, pady=10)

        remove_btn = ctk.CTkButton(card, text="✖", width=30, height=30, corner_radius=5,
                                   fg_color="#b53a3a", hover_color="#c54a4a",
                                   command=lambda u=username: self.remove_friend(u))
        remove_btn.pack(side="right", padx=5, pady=10)

    def add_friend(self):
        username = self.friend_entry.get().strip()
        if not username:
            messagebox.showwarning("Предупреждение", "Введите никнейм")
            return
        success, msg = self.friend_manager.add_friend(username)
        if success:
            self.friend_entry.delete(0, "end")
            self.update_friends_list()
            messagebox.showinfo("Успех", msg)
        else:
            messagebox.showerror("Ошибка", msg)

    def remove_friend(self, username):
        if messagebox.askyesno("Подтверждение", f"Удалить {username} из друзей?"):
            self.friend_manager.remove_friend(username)
            self.update_friends_list()

    def switch_to_friend(self, username):
        self.apply_profile(username)

    def create_versions_tab(self):
        frame = ctk.CTkFrame(self.tab_versions)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        left_frame = ctk.CTkFrame(frame, width=200)
        left_frame.pack(side="left", fill="y", padx=5, pady=5)
        ctk.CTkLabel(left_frame, text="Все доступные версии", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=5)
        self.all_versions_listbox = ctk.CTkScrollableFrame(left_frame, width=180, height=300)
        self.all_versions_listbox.pack(pady=5)

        right_frame = ctk.CTkFrame(frame)
        right_frame.pack(side="right", fill="both", expand=True, padx=5, pady=5)
        ctk.CTkLabel(right_frame, text="Установка мод-лоадеров", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)

        loader_version_frame = ctk.CTkFrame(right_frame)
        loader_version_frame.pack(pady=5)
        ctk.CTkLabel(loader_version_frame, text="Версия Minecraft:").pack(side="left", padx=5)
        self.loader_version_combo = ctk.CTkComboBox(loader_version_frame, values=self.all_versions, width=150)
        self.loader_version_combo.pack(side="left", padx=5)

        btn_frame = ctk.CTkFrame(right_frame)
        btn_frame.pack(pady=10)
        self.forge_btn = ctk.CTkButton(btn_frame, text="Forge", command=lambda: self.install_loader("forge"))
        self.forge_btn.grid(row=0, column=0, padx=5, pady=5)
        self.fabric_btn = ctk.CTkButton(btn_frame, text="Fabric", command=lambda: self.install_loader("fabric"))
        self.fabric_btn.grid(row=0, column=1, padx=5, pady=5)
        self.quilt_btn = ctk.CTkButton(btn_frame, text="Quilt", command=lambda: self.install_loader("quilt"))
        self.quilt_btn.grid(row=0, column=2, padx=5, pady=5)
        self.optifine_btn = ctk.CTkButton(btn_frame, text="OptiFine", command=lambda: self.install_loader("optifine"))
        self.optifine_btn.grid(row=0, column=3, padx=5, pady=5)

        self.loader_status = ctk.CTkLabel(right_frame, text="")
        self.loader_status.pack(pady=10)

        ctk.CTkButton(right_frame, text="Обновить список версий", command=lambda: self.load_all_versions(force_refresh=True)).pack(pady=10)

    def create_settings_tab(self):
        frame = ctk.CTkFrame(self.tab_settings)
        frame.pack(fill="both", expand=True, padx=20, pady=20)

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

        default_mem_frame = ctk.CTkFrame(frame)
        default_mem_frame.pack(pady=5)
        ctk.CTkLabel(default_mem_frame, text="Память (МБ):").pack(side="left", padx=5)
        self.default_memory_var = ctk.StringVar(value=str(self.config.get("default_memory", 2048)))
        ctk.CTkEntry(default_mem_frame, textvariable=self.default_memory_var, width=100).pack(side="left", padx=5)

        default_java_frame = ctk.CTkFrame(frame)
        default_java_frame.pack(pady=5, fill="x")
        ctk.CTkLabel(default_java_frame, text="Путь к Java:").pack(anchor="w")
        self.default_java_entry = ctk.CTkEntry(default_java_frame, width=400)
        self.default_java_entry.pack(fill="x", pady=5)
        self.default_java_entry.insert(0, self.config.get("default_java", ""))

        default_jvm_frame = ctk.CTkFrame(frame)
        default_jvm_frame.pack(pady=5, fill="x")
        ctk.CTkLabel(default_jvm_frame, text="Доп. JVM аргументы:").pack(anchor="w")
        self.default_jvm_entry = ctk.CTkEntry(default_jvm_frame, width=400)
        self.default_jvm_entry.pack(fill="x", pady=5)
        self.default_jvm_entry.insert(0, self.config.get("default_jvm_args", ""))

        ctk.CTkButton(frame, text="💾 Сохранить глобальные настройки", command=self.save_global_settings).pack(pady=20)

    def create_mods_tab(self):
        frame = ctk.CTkFrame(self.tab_mods)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        top_panel = ctk.CTkFrame(frame)
        top_panel.pack(fill="x", pady=5)

        ctk.CTkLabel(top_panel, text="Версия:").pack(side="left", padx=5)
        self.mod_version_combo = ctk.CTkComboBox(top_panel, values=["Загрузка..."], width=120,
                                                 command=self.on_mod_version_change)
        self.mod_version_combo.pack(side="left", padx=5)

        self.mod_search_entry = ctk.CTkEntry(top_panel, placeholder_text="Название мода...", width=250)
        self.mod_search_entry.pack(side="left", padx=5)
        self.mod_search_btn = ctk.CTkButton(top_panel, text="Искать", command=self.search_mods, width=80)
        self.mod_search_btn.pack(side="left", padx=5)

        ctk.CTkLabel(top_panel, text="Сортировать по:").pack(side="left", padx=10)
        self.mod_sort_combo = ctk.CTkComboBox(top_panel, values=["Популярности", "Дате обновления"], width=150)
        self.mod_sort_combo.pack(side="left", padx=5)
        self.mod_sort_combo.set("Популярности")

        self.top_mods_btn = ctk.CTkButton(top_panel, text="Топ модов", command=self.fetch_top_mods, width=100)
        self.top_mods_btn.pack(side="left", padx=10)

        self.delete_selected_btn = ctk.CTkButton(top_panel, text="🗑️ Удалить выбранные", command=self.delete_selected_mods,
                                                 fg_color="#b53a3a", hover_color="#c54a4a", width=150)
        self.delete_selected_btn.pack(side="left", padx=10)

        self.mod_results_frame = ctk.CTkScrollableFrame(frame, label_text="Результаты поиска")
        self.mod_results_frame.pack(fill="both", expand=True, pady=10)

        bottom_panel = ctk.CTkFrame(frame)
        bottom_panel.pack(fill="x", pady=5)
        self.mod_prev_page_btn = ctk.CTkButton(bottom_panel, text="◀ Предыдущая", command=self.mod_prev_page, state="disabled", width=120)
        self.mod_prev_page_btn.pack(side="left", padx=10)
        self.mod_page_label = ctk.CTkLabel(bottom_panel, text="Страница 1")
        self.mod_page_label.pack(side="left", padx=10)
        self.mod_next_page_btn = ctk.CTkButton(bottom_panel, text="Следующая ▶", command=self.mod_next_page, state="disabled", width=120)
        self.mod_next_page_btn.pack(side="left", padx=10)

        self.mod_status_label = ctk.CTkLabel(frame, text="")
        self.mod_status_label.pack()

    def create_resourcepacks_tab(self):
        frame = ctk.CTkFrame(self.tab_resourcepacks)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        top_panel = ctk.CTkFrame(frame)
        top_panel.pack(fill="x", pady=5)
        self.add_rp_btn = ctk.CTkButton(top_panel, text="📂 Загрузить ресурспак с компьютера", command=self.add_resourcepack_from_file, width=250)
        self.add_rp_btn.pack(side="left", padx=10)

        ctk.CTkFrame(frame, height=2, fg_color="#3a3a4a").pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(frame, text="Установленные ресурспаки", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=10, pady=5)

        self.installed_rp_frame = ctk.CTkScrollableFrame(frame, height=150, fg_color="#1a1a2a", corner_radius=10)
        self.installed_rp_frame.pack(fill="x", padx=10, pady=5)
        self.update_resourcepacks_list()

        ctk.CTkFrame(frame, height=2, fg_color="#3a3a4a").pack(fill="x", padx=10, pady=5)

        search_frame = ctk.CTkFrame(frame)
        search_frame.pack(fill="x", pady=5)

        ctk.CTkLabel(search_frame, text="Поиск новых ресурспаков", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=10, pady=5)

        search_panel = ctk.CTkFrame(search_frame)
        search_panel.pack(fill="x", pady=5)

        ctk.CTkLabel(search_panel, text="Версия:").pack(side="left", padx=5)
        self.rp_version_combo = ctk.CTkComboBox(search_panel, values=["Загрузка..."], width=120,
                                                command=self.on_rp_version_change)
        self.rp_version_combo.pack(side="left", padx=5)

        self.rp_search_entry = ctk.CTkEntry(search_panel, placeholder_text="Название ресурспака...", width=250)
        self.rp_search_entry.pack(side="left", padx=5)
        self.rp_search_btn = ctk.CTkButton(search_panel, text="Искать", command=self.search_resourcepacks, width=80)
        self.rp_search_btn.pack(side="left", padx=5)

        ctk.CTkLabel(search_panel, text="Сортировать по:").pack(side="left", padx=10)
        self.rp_sort_combo = ctk.CTkComboBox(search_panel, values=["Популярности", "Дате обновления"], width=150)
        self.rp_sort_combo.pack(side="left", padx=5)
        self.rp_sort_combo.set("Популярности")

        self.top_rp_btn = ctk.CTkButton(search_panel, text="Топ ресурспаков", command=self.fetch_top_resourcepacks, width=120)
        self.top_rp_btn.pack(side="left", padx=10)

        self.rp_results_frame = ctk.CTkScrollableFrame(frame, label_text="Результаты поиска")
        self.rp_results_frame.pack(fill="both", expand=True, padx=10, pady=5)

        rp_bottom_panel = ctk.CTkFrame(frame)
        rp_bottom_panel.pack(fill="x", pady=5)
        self.rp_prev_page_btn = ctk.CTkButton(rp_bottom_panel, text="◀ Предыдущая", command=self.rp_prev_page, state="disabled", width=120)
        self.rp_prev_page_btn.pack(side="left", padx=10)
        self.rp_page_label = ctk.CTkLabel(rp_bottom_panel, text="Страница 1")
        self.rp_page_label.pack(side="left", padx=10)
        self.rp_next_page_btn = ctk.CTkButton(rp_bottom_panel, text="Следующая ▶", command=self.rp_next_page, state="disabled", width=120)
        self.rp_next_page_btn.pack(side="left", padx=10)

        self.rp_status_label = ctk.CTkLabel(frame, text="")
        self.rp_status_label.pack()

    def create_stats_tab(self):
        frame = ctk.CTkFrame(self.tab_stats)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(frame, text="Статистика игрового времени", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=20)

        stats_frame = ctk.CTkFrame(frame, fg_color="#2a2a3a", corner_radius=10)
        stats_frame.pack(pady=10, padx=20, fill="both", expand=True)

        self.stats_label_7d = ctk.CTkLabel(stats_frame, text="За 7 дней: загрузка...", font=ctk.CTkFont(size=16), anchor="w")
        self.stats_label_7d.pack(pady=10, padx=20, fill="x")

        self.stats_label_30d = ctk.CTkLabel(stats_frame, text="За 30 дней: загрузка...", font=ctk.CTkFont(size=16), anchor="w")
        self.stats_label_30d.pack(pady=10, padx=20, fill="x")

        self.stats_label_total = ctk.CTkLabel(stats_frame, text="За всё время: загрузка...", font=ctk.CTkFont(size=16), anchor="w")
        self.stats_label_total.pack(pady=10, padx=20, fill="x")

        ctk.CTkButton(frame, text="Сбросить статистику", command=self.reset_stats, fg_color="red", hover_color="darkred").pack(pady=20)

    def update_stats_display(self):
        total_7d = self.stats_manager.get_total_time(7)
        total_30d = self.stats_manager.get_total_time(30)
        total_all = self.stats_manager.get_total_time()

        self.stats_label_7d.configure(text=f"За 7 дней: {self.stats_manager.format_time(total_7d)}")
        self.stats_label_30d.configure(text=f"За 30 дней: {self.stats_manager.format_time(total_30d)}")
        self.stats_label_total.configure(text=f"За всё время: {self.stats_manager.format_time(total_all)}")

    def reset_stats(self):
        if messagebox.askyesno("Подтверждение", "Вы уверены, что хотите сбросить всю статистику?"):
            self.stats_manager.clear()
            self.update_stats_display()
            messagebox.showinfo("Готово", "Статистика сброшена")

    def create_news_tab(self):
        frame = ctk.CTkFrame(self.tab_news)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        mc_news_frame = ctk.CTkFrame(frame)
        mc_news_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(mc_news_frame, text="Последние версии Minecraft", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=10, pady=5)

        self.versions_scroll = ctk.CTkScrollableFrame(mc_news_frame, height=150)
        self.versions_scroll.pack(fill="x", padx=10, pady=5)
        self.version_buttons = []

        self.mc_version_info = ctk.CTkTextbox(mc_news_frame, height=150, wrap="word")
        self.mc_version_info.pack(fill="x", padx=10, pady=5)
        self.mc_version_info.insert("0.0", "Выберите версию для просмотра информации")
        self.mc_version_info.configure(state="disabled")

        launcher_news_frame = ctk.CTkFrame(frame)
        launcher_news_frame.pack(fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(launcher_news_frame, text="История обновлений лаунчера", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=10, pady=5)
        self.launcher_news_text = ctk.CTkTextbox(launcher_news_frame, wrap="word")
        self.launcher_news_text.pack(fill="both", expand=True, padx=10, pady=5)
        self.update_launcher_news()

    def update_launcher_news(self):
        self.launcher_news_text.delete("0.0", "end")
        content = ""
        for ver in LAUNCHER_VERSIONS:
            content += f"Версия {ver['version']} ({ver['date']}):\n"
            for change in ver['changes']:
                content += f"  {change}\n"
            content += "\n"
        self.launcher_news_text.insert("0.0", content)
        self.launcher_news_text.configure(state="disabled")

    def update_mc_news(self):
        for btn in self.version_buttons:
            btn.destroy()
        self.version_buttons.clear()

        if self.all_versions and self.all_versions[0] != "Загрузка...":
            for ver in self.all_versions:
                btn = ctk.CTkButton(self.versions_scroll, text=ver,
                                    command=lambda v=ver: self.show_mc_version_info(v),
                                    anchor="w", fg_color="transparent", hover_color="#3a6ea5")
                btn.pack(fill="x", pady=1)
                self.version_buttons.append(btn)
            if self.all_versions:
                self.show_mc_version_info(self.all_versions[0])
        else:
            lbl = ctk.CTkLabel(self.versions_scroll, text="Загрузка версий...")
            lbl.pack()
            self.version_buttons.append(lbl)

    def show_mc_version_info(self, version):
        self.mc_version_info.configure(state="normal")
        self.mc_version_info.delete("0.0", "end")
        info = MINECRAFT_VERSION_INFO.get(version, "Описание отсутствует для этой версии.")
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
        self.update_friends_list()

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
            if self.current_profile in self.friend_manager.friends:
                self.friend_manager.remove_friend(self.current_profile)
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
                release_versions = [v["id"] for v in data["versions"] if v["type"] == "release"]
                def version_key(v):
                    parts = v.split('.')
                    key = []
                    for p in parts:
                        try:
                            key.append(int(p))
                        except ValueError:
                            key.append(999)
                    return key
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
        self.loader_version_combo.configure(values=self.all_versions)
        if self.all_versions:
            self.loader_version_combo.set(self.all_versions[0])

        for widget in self.all_versions_listbox.winfo_children():
            widget.destroy()
        for ver in self.all_versions:
            btn = ctk.CTkButton(self.all_versions_listbox, text=ver, command=lambda v=ver: self.select_version(v),
                                fg_color="transparent", anchor="w")
            btn.pack(fill="x", pady=1)

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

            subprocess.run(command)

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

    def search_mods(self):
        query = self.mod_search_entry.get().strip()
        if not query:
            messagebox.showwarning("Поиск", "Введите название мода")
            return
        self.current_mod_query = query
        self.current_mod_sort = self.mod_sort_combo.get()
        self.current_mod_offset = 0
        self.load_mods_page()

    def fetch_top_mods(self):
        self.current_mod_query = ""
        self.current_mod_sort = self.mod_sort_combo.get()
        self.current_mod_offset = 0
        self.load_mods_page()

    def load_mods_page(self):
        for widget in self.mod_results_frame.winfo_children():
            widget.destroy()
        self.mod_status_label.configure(text="Загрузка...")
        self.mod_prev_page_btn.configure(state="disabled")
        self.mod_next_page_btn.configure(state="disabled")
        Thread(target=self._fetch_mods_page, args=(self.current_mod_query, self.current_mod_sort, self.current_mod_offset, self.current_mod_version)).start()

    def _fetch_mods_page(self, query, sort_by, offset, game_version):
        try:
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

    def save_global_settings(self):
        self.config["default_memory"] = int(self.default_memory_var.get())
        self.config["default_java"] = self.default_java_entry.get()
        self.config["default_jvm_args"] = self.default_jvm_entry.get()
        self.save_config()
        messagebox.showinfo("Настройки", "Глобальные настройки сохранены")

    def clear_cache(self):
        if messagebox.askyesno("Очистка кеша", "Это удалит все установленные версии и библиотеки. Продолжить?"):
            try:
                shutil.rmtree(os.path.join(self.minecraft_directory, "versions"))
                shutil.rmtree(os.path.join(self.minecraft_directory, "libraries"))
                os.makedirs(os.path.join(self.minecraft_directory, "versions"), exist_ok=True)
                os.makedirs(os.path.join(self.minecraft_directory, "libraries"), exist_ok=True)
                self.update_installed_versions()
                messagebox.showinfo("Готово", "Кеш очищен")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось очистить кеш: {e}")

if __name__ == "__main__":
    app = MinecraftLauncher()
    app.mainloop()