import tkinter as tk
import sv_ttk
import json
import os
import platform
import subprocess
import ast
import shutil
import webbrowser
import csv
import re
import ast
import ctypes
import copy
import winreg
from datetime import datetime
from task_manager import TaskManager
from settings_manager import SettingsManager
from deep_translator import GoogleTranslator
from tkinter import ttk, messagebox, filedialog

class CryptographyApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Задачник по кибербезопасности")
        # 1. Инициализация менеджера настроек
        self.settings_manager = SettingsManager()
        # 2. Загрузка размеров окна и их применение
        window_width = self.settings_manager.get_setting("window_width", 1100)
        window_height = self.settings_manager.get_setting("window_height", 750)
        self.root.geometry(f"{window_width}x{window_height}")
        self.root.minsize(1100, 750) 
        # 3. Применение темы при запуске 
        current_theme = self.settings_manager.get_setting("theme", "Системная")
        self.apply_app_theme(current_theme)
        # 4. Увеличение шрифтов 
        style = ttk.Style()
        style.configure(".", font=("Arial", 13)) 
        style.configure("TButton", font=("Arial", 12, "bold"), padding=6)
        style.configure("TLabelframe.Label", font=("Arial", 13, "bold"))
        style.configure("Treeview", font=("Arial", 11), rowheight=28)
        style.configure("Treeview.Heading", font=("Arial", 11, "bold"))
        # 5. Инициализация менеджера задач
        self.current_csv_file = self.settings_manager.get_setting("csv_file_path", "data/tasks_metadata.csv")
        self.task_manager = TaskManager(self.current_csv_file)
        # 6. Инициализация коллекций
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.collections_file = os.path.join(script_dir, "collections.json")
        self.load_collections()
        # Переменные для фильтров
        self.current_category = "Все"
        self.current_level = "Все"
        self.current_search_query = ""
        # Переменные для сортировки
        self.sort_column = "key"
        self.sort_descending = False
        self.selected_tasks = set()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        # 6. Создание интерфейса
        self.create_menu_bar()
        self.create_main_frame()
        # 7. Запускаем фоновый цикл автообновления 
        if hasattr(self, 'auto_refresh_loop'):
            self.auto_refresh_loop()
            
    def apply_treeview_colors(self):
        """Настраивает цвета чередования строк для таблицы в зависимости от темы"""
        if not hasattr(self, 'tasks_tree') or not self.tasks_tree.winfo_exists():
            return

        try:
            actual_theme = sv_ttk.get_theme()
        except:
            actual_theme = "light"

        if actual_theme == "dark":
            even_bg = "#2b2b2b"  
            odd_bg = "#1c1c1c"   
            text_fg = "#ffffff"  
            selected_bg = "#005fb8" 
        else:
            even_bg = "#f2f6fc"  
            odd_bg = "#ffffff"   
            text_fg = "#000000"  
            selected_bg = "#005fb8"

        style = ttk.Style()
        style.map('Treeview', 
                  background=[('selected', selected_bg)], 
                  foreground=[('selected', '#ffffff')])

        self.tasks_tree.tag_configure('evenrow', background=even_bg, foreground=text_fg)
        self.tasks_tree.tag_configure('oddrow', background=odd_bg, foreground=text_fg)
    
    def on_closing(self):
        """Обработчик закрытия приложения"""
        try:
            self.restore_main_database()
            self.settings_manager.set_setting("window_width", self.root.winfo_width())
            self.settings_manager.set_setting("window_height", self.root.winfo_height())
            self.settings_manager.set_setting("csv_file_path", self.current_csv_file)
            success = self.settings_manager.save_settings()
            if not success:
                print("Предупреждение: не удалось сохранить настройки при закрытии")
        except Exception as e:
            print(f"Ошибка при сохранении настроек при закрытии: {e}")

        self.root.destroy()
        
    def create_menu_bar(self):
        """Создание верхнего меню"""
        self.menu_bar = tk.Menu(self.root)
        self.root.config(menu=self.menu_bar)
        
        # Меню "Задачи"
        tasks_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Задачи", menu=tasks_menu)
        tasks_menu.add_command(label="Просмотр задач", command=self.show_option1)
        tasks_menu.add_command(label="Мои коллекции", command=self.show_option2)
        tasks_menu.add_command(label="Выбрать каталог задачника...", command=self.select_workbook_directory)
        
        # Подменю "Недавние файлы"
        self.recent_menu = tk.Menu(tasks_menu, tearoff=0)
        tasks_menu.add_cascade(label="Недавние файлы", menu=self.recent_menu)
        self.update_recent_files_menu()
        
        tasks_menu.add_separator()
        tasks_menu.add_command(label="Загрузить CSV файл...", command=self.load_csv_file)
        tasks_menu.add_command(label="Обновить данные", command=self.refresh_data)
        tasks_menu.add_separator()
        tasks_menu.add_command(label="Выход", command=self.on_closing)
        
        # Меню "Аналитика"
        stats_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Аналитика", menu=stats_menu)
        stats_menu.add_command(label="Статистика", command=self.show_option3)
        
        # Меню "Настройки"
        settings_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Настройки", menu=settings_menu)
        settings_menu.add_command(label="Настройки приложения", command=self.show_option4)
        
        # Меню "Справка"
        help_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Справка", menu=help_menu)
        help_menu.add_command(label="О программе", command=self.show_about)
    
    def select_workbook_directory(self):
        """Выбор каталога задачника"""
        directory = filedialog.askdirectory(
            title="Выберите каталог задачника",
            initialdir="."
        )
        
        if directory:
            try:
                # Сохраняем выбранный каталог в настройках
                self.settings_manager.set_setting("workbook_directory", directory)
                self.settings_manager.save_settings()
                
                messagebox.showinfo(
                    "Успех", 
                    f"Каталог задачника установлен:\n{directory}"
                )
                
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось установить каталог:\n{str(e)}")
    
    def update_recent_files_menu(self):
        """Обновление меню недавних файлов"""
        recent_files = self.settings_manager.get_recent_files()
        self.recent_menu.delete(0, tk.END)
        
        if recent_files:
            for file_path in recent_files:
                if os.path.exists(file_path):
                    filename = os.path.basename(file_path)
                    self.recent_menu.add_command(
                        label=filename,
                        command=lambda path=file_path: self.load_specific_csv_file(path)
                    )
        else:
            self.recent_menu.add_command(label="Нет недавних файлов", state=tk.DISABLED)
    
    def load_specific_csv_file(self, file_path: str):
        """Загрузка конкретного CSV файла из меню недавних"""
        self.restore_main_database()
        try:
            self.current_csv_file = file_path
            self.task_manager = TaskManager(file_path)
            
            # Обновляем настройки
            self.settings_manager.set_setting("csv_file_path", file_path)
            self.settings_manager.add_recent_file(file_path)
            self.settings_manager.save_settings()
            
            # Обновляем интерфейс
            self.update_interface_after_file_load(file_path)
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить файл:\n{str(e)}")
    
    def load_csv_file(self):
        """Загрузка CSV файла через диалог выбора файла"""
        self.restore_main_database()
        file_path = filedialog.askopenfilename(
            title="Выберите CSV файл с задачами",
            filetypes=[
                ("CSV files", "*.csv"),
                ("All files", "*.*")
            ],
            initialdir="."
        )
        
        if file_path:
            try:
                self.current_csv_file = file_path
                self.task_manager = TaskManager(file_path)
                
                # Сохраняем в настройках
                self.settings_manager.set_setting("csv_file_path", file_path)
                self.settings_manager.add_recent_file(file_path)
                self.settings_manager.save_settings()
                
                # Обновляем интерфейс
                self.update_interface_after_file_load(file_path)
                
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось загрузить файл:\n{str(e)}")
    
    def update_interface_after_file_load(self, file_path: str):
        """Обновление интерфейса после загрузки файла (Безопасный маршрут)"""
        filename = os.path.basename(file_path)
        messagebox.showinfo(
            "Успех", 
            f"Файл '{filename}' успешно загружен!\nЗагружено задач: {len(self.task_manager.tasks)}"
        )
        self.update_recent_files_menu()
        self.restore_main_database()
        self.show_option1() 

    def auto_refresh_loop(self):
        """Фоновый цикл: тихо обновляет данные"""
        is_auto = self.settings_manager.get_setting("auto_refresh", True)
        if is_auto:
            try:
                self.task_manager.load_tasks()
                if getattr(self, 'in_collection_view', False):
                    if hasattr(self, 'current_folder_refresh_func'):
                        self.current_folder_refresh_func()
                else:
                    if hasattr(self, 'tasks_tree') and self.tasks_tree.winfo_exists():
                        self.update_filter_comboboxes()
                        self.update_tasks_table()
                        self.update_filter_status()
            except Exception as e:
                pass
                
        self.root.after(30000, self.auto_refresh_loop)

    def refresh_data(self):
        """Обновление данных вручную"""
        try:
            self.task_manager = TaskManager(self.current_csv_file)
            
            if getattr(self, 'in_collection_view', False):
                if hasattr(self, 'current_folder_refresh_func'):
                    self.current_folder_refresh_func()
            else:
                if hasattr(self, 'tasks_tree') and self.tasks_tree.winfo_exists():
                    self.update_filter_comboboxes()
                    self.update_tasks_table()
                    self.update_filter_status()
            
            messagebox.showinfo("Обновлено", f"Данные успешно обновлены!\nЗагружено задач: {len(self.task_manager.tasks)}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось обновить данные:\n{str(e)}")
    
    def create_main_frame(self):
        """Создание главной формы с логотипом"""
        # Основной фрейм
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Настройка веса строк и столбцов для растягивания
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.rowconfigure(1, weight=1)
        
        # Логотип
        self.create_logo_section()
        
        # Стартовая информация
        self.create_welcome_section()
    
    def create_logo_section(self):
        """Создание секции с логотипом"""
        logo_frame = ttk.Frame(self.main_frame)
        logo_frame.grid(row=0, column=0, pady=20, sticky=(tk.W, tk.E))
        logo_frame.columnconfigure(0, weight=1)
        
        # Определяем цвет в зависимости от темы
        current_theme = self.settings_manager.get_setting("theme", "Светлая")
        accent_color = "#58a6ff" if current_theme == "Темная" else "blue"
        
        # Заголовок
        logo_label = ttk.Label(logo_frame, text="ЗАДАЧНИК ПО КИБЕРБЕЗОПАСНОСТИ", 
                              font=("Arial", 32, "bold"), foreground=accent_color)
        logo_label.grid(row=0, column=0, pady=20)
        
        # Подзаголовок
        sub_label = ttk.Label(logo_frame, text="Практикум по решению задач по кибербезопасности", 
                             font=("Arial", 16), foreground="gray")
        sub_label.grid(row=1, column=0, pady=5)
        
        file_info = f"Текущий файл: {os.path.basename(self.current_csv_file)}"
        self.file_label = ttk.Label(logo_frame, text=file_info, 
                                   font=("Arial", 11), foreground="darkgreen", wraplength=700, justify=tk.CENTER)
        self.file_label.grid(row=2, column=0, pady=5)
    
    def create_welcome_section(self):
        """Создание приветственной секции"""
        self.welcome_frame = ttk.Frame(self.main_frame)
        self.welcome_frame.grid(row=1, column=0, pady=50, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.welcome_frame.columnconfigure(0, weight=1)
        
        stats = self.task_manager.get_task_statistics()
        style = ttk.Style()
        style.configure("TLabelframe.Label", font=("Arial", 14, "bold")) 
        style.configure("TButton", font=("Arial", 11))                   
        welcome_text = f"""Добро пожаловать в задачник по кибербезопасности!
        
        Доступно для изучения:
        • {stats['total_tasks']} задач различной сложности
        • {stats['categories_count']} категорий кибербезопасности
        • {stats['tags_count']} различных тегов

        Используйте верхнее меню для навигации по приложению:

        📊 Задачи - просмотр, поиск и загрузка CSV файлов
        📈 Аналитика - статистика и анализ прогресса
        ⚙️ Настройки - конфигурация приложения
        ❓ Справка - информация о программе"""
        
        welcome_label = ttk.Label(self.welcome_frame, text=welcome_text, 
                                  font=("Arial", 14), justify=tk.LEFT, wraplength=800)
        welcome_label.grid(row=0, column=0, pady=(10, 0))
        file_info = f"Текущий файл: {os.path.basename(self.current_csv_file)}"
        file_label = ttk.Label(self.welcome_frame, text=file_info, 
                               font=("Arial", 14), justify=tk.LEFT)
        file_label.grid(row=1, column=0, pady=(15, 20))
        quick_access_frame = ttk.LabelFrame(self.welcome_frame, text="Быстрый доступ", padding="15")
        quick_access_frame.grid(row=2, column=0, pady=20) 
        
        ttk.Button(quick_access_frame, text="📁 Все задачи", width=18,
                  command=self.show_option1).grid(row=0, column=0, padx=10, pady=5)
        ttk.Button(quick_access_frame, text="⭐ Мои коллекции", width=18,
                  command=self.show_option2).grid(row=0, column=1, padx=10, pady=5)
        ttk.Button(quick_access_frame, text="📊 Статистика", width=18,
                  command=self.show_option3).grid(row=0, column=2, padx=10, pady=5)
        ttk.Button(quick_access_frame, text="📂 Загрузить CSV", width=18,
                  command=self.load_csv_file).grid(row=0, column=3, padx=10, pady=5)
    
    def clear_content(self):
        """Очистка текущего контента и сброс геометрии сетки"""
        if hasattr(self, 'selected_tasks'):
            self.selected_tasks.clear()
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        for i in range(10): 
            self.main_frame.rowconfigure(i, weight=0)
            self.main_frame.columnconfigure(i, weight=0)
        self.main_frame.columnconfigure(0, weight=1) 
        if platform.system() == 'Linux':
            self.root.unbind_all("<Button-4>")
            self.root.unbind_all("<Button-5>")
        else:
            self.root.unbind_all("<MouseWheel>")
    
    def show_option1(self):
        """Режим 1: Просмотр задач"""
        self.restore_main_database()
        self.clear_content()
        self.create_task_browser()
    
    def show_option2(self):
        """Режим 2: Мои коллекции"""
        if hasattr(self, 'main_task_manager'):
            self.task_manager = self.main_task_manager
            self.current_csv_file = self.settings_manager.get_setting("csv_file_path")
            del self.main_task_manager
            self.in_collection_view = False
        self.restore_main_database()
        self.clear_content()
        self.create_collections_interface()
    
    def show_option3(self):
        """Режим 3: Статистика"""
        self.restore_main_database()
        self.clear_content()
        self.create_statistics_interface()
    
    def show_option4(self):
        """Режим 4: Настройки"""
        self.restore_main_database()
        self.clear_content()
        self.create_settings_interface()
    
    def show_about(self):
        """Показать информацию о программе"""
        stats = self.task_manager.get_task_statistics()
        about_text = f"""
        Задачник по кибербезопасности
        
        Версия 2.0
        Разработано для практического изучения кибербезопасности
        
        Текущий файл: {os.path.basename(self.current_csv_file)}
        Загружено задач: {stats['total_tasks']}
        
        Функции:
        • Просмотр задач по кибербезопасности
        • Фильтрация по категориям и сложности
        • Поиск по задачам
        • Добавление в коллекции
        • Загрузка CSV файлов
        • Сохранение настроек
        • Статистика и анализ
        
        © 2026 Все права защищены
        """
        messagebox.showinfo("О программе", about_text)
    
    def create_task_browser(self):
        """Интерфейс для просмотра задач"""
        title_frame = ttk.Frame(self.main_frame)
        title_frame.grid(row=0, column=0, pady=10, sticky=(tk.W, tk.E))
        title_frame.columnconfigure(0, weight=1)
        
        ttk.Label(title_frame, text="📁 Просмотр задач", font=("Arial", 16, "bold")).grid(row=0, column=0, sticky=tk.W)
        file_info = f"Файл: {os.path.basename(self.current_csv_file)}"
        ttk.Label(title_frame, text=file_info, font=("Arial", 9), foreground="darkgreen").grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        ttk.Button(title_frame, text="← На главную", command=self.return_to_main_menu).grid(row=0, column=1, rowspan=2, sticky=(tk.E, tk.N, tk.S))
        
        # Управление данными
        control_frame = ttk.LabelFrame(self.main_frame, text="Управление данными", padding=10)
        control_frame.grid(row=1, column=0, pady=(5, 10), sticky=(tk.W, tk.E))
        ttk.Button(control_frame, text="📂 Загрузить другой CSV", command=self.load_csv_file).grid(row=0, column=0, padx=5, pady=2)
        ttk.Button(control_frame, text="🔄 Обновить данные", command=self.refresh_data).grid(row=0, column=1, padx=5, pady=2)
        
        filter_frame = ttk.LabelFrame(self.main_frame, text="Поиск и фильтры", padding=10)
        filter_frame.grid(row=2, column=0, pady=5, sticky=(tk.W, tk.E))
        
        filter_frame.columnconfigure(1, weight=1)
        filter_frame.columnconfigure(3, weight=1)
        filter_frame.columnconfigure(5, weight=1)
        filter_frame.columnconfigure(7, weight=1)

        # СТРОКА 0
        ttk.Label(filter_frame, text="Текст поиска:").grid(row=0, column=0, padx=5, pady=(5, 10), sticky=tk.W)
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(filter_frame, textvariable=self.search_var, font=("Arial", 11))
        search_entry.grid(row=0, column=1, columnspan=6, padx=5, pady=(5, 10), sticky=(tk.W, tk.E))
        
        search_btn = ttk.Button(filter_frame, text="🔍 Найти", command=self.on_filters_changed)
        search_btn.grid(row=0, column=7, padx=5, pady=(5, 10), sticky=tk.E)
        search_entry.bind('<Return>', self.on_filters_changed)

        # СТРОКА 1
        ttk.Label(filter_frame, text="Категория:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.category_var = tk.StringVar(value="Все")
        self.category_combo = ttk.Combobox(filter_frame, textvariable=self.category_var, state="readonly", width=15)
        self.category_combo.grid(row=1, column=1, padx=5, pady=5, sticky=(tk.W, tk.E))
        self.category_combo.bind('<<ComboboxSelected>>', self.on_filters_changed)
        
        ttk.Label(filter_frame, text="Уровень:").grid(row=1, column=2, padx=5, pady=5, sticky=tk.W)
        self.level_var = tk.StringVar(value="Все")
        self.level_combo = ttk.Combobox(filter_frame, textvariable=self.level_var, state="readonly", width=12)
        self.level_combo.grid(row=1, column=3, padx=5, pady=5, sticky=(tk.W, tk.E))
        self.level_combo.bind('<<ComboboxSelected>>', self.on_filters_changed)

        ttk.Label(filter_frame, text="Турнир:").grid(row=1, column=4, padx=5, pady=5, sticky=tk.W)
        self.ctf_var = tk.StringVar(value="Все")
        self.ctf_combo = ttk.Combobox(filter_frame, textvariable=self.ctf_var, state="readonly", width=15)
        self.ctf_combo.grid(row=1, column=5, padx=5, pady=5, sticky=(tk.W, tk.E))
        self.ctf_combo.bind('<<ComboboxSelected>>', self.on_filters_changed)

        ttk.Label(filter_frame, text="Тег:").grid(row=1, column=6, padx=5, pady=5, sticky=tk.W)
        self.tag_var = tk.StringVar(value="Все")
        self.tag_combo = ttk.Combobox(filter_frame, textvariable=self.tag_var, state="readonly", width=12)
        self.tag_combo.grid(row=1, column=7, padx=5, pady=5, sticky=(tk.W, tk.E))
        self.tag_combo.bind('<<ComboboxSelected>>', self.on_filters_changed)
        
        # СТРОКА 2
        self.writeup_var = tk.BooleanVar()
        ttk.Checkbutton(filter_frame, text="Есть writeup", variable=self.writeup_var, command=self.on_filters_changed).grid(row=2, column=0, columnspan=2, padx=5, pady=(5, 5), sticky=tk.W)
        
        self.wsite_var = tk.BooleanVar()
        ttk.Checkbutton(filter_frame, text="Есть сайт", variable=self.wsite_var, command=self.on_filters_changed).grid(row=2, column=2, columnspan=2, padx=5, pady=(5, 5), sticky=tk.W)
        
        self.attachment_var = tk.BooleanVar()
        ttk.Checkbutton(filter_frame, text="Есть вложение", variable=self.attachment_var, command=self.on_filters_changed).grid(row=2, column=4, columnspan=2, padx=5, pady=(5, 5), sticky=tk.W)
        
        ttk.Button(filter_frame, text="Сбросить фильтры", command=self.reset_filters).grid(row=2, column=6, columnspan=2, padx=5, pady=(5, 5), sticky=tk.E)
        
        self.update_filter_comboboxes()
        
        # Статус фильтров
        self.filter_status = ttk.Label(self.main_frame, text="", foreground="blue")
        self.filter_status.grid(row=3, column=0, pady=5, sticky=tk.W)
        
        # Таблица задач
        self.create_tasks_table()
        
        # Обновление статуса
        self.update_filter_status()
    
    def create_tasks_table(self):
        """Создание таблицы для отображения задач"""
        self.in_collection_view = False 
        bulk_frame = ttk.Frame(self.main_frame)
        bulk_frame.grid(row=3, column=0, pady=(10, 0), sticky=(tk.W, tk.E))
        bulk_frame.columnconfigure(1, weight=1)
        
        # Статус слева
        self.filter_status = ttk.Label(bulk_frame, text="", foreground="blue")
        self.filter_status.grid(row=0, column=0, sticky=tk.W)

        # Контейнер для кнопок справа
        btn_frame = ttk.Frame(bulk_frame)
        btn_frame.grid(row=0, column=2, sticky=tk.E)

        ttk.Button(btn_frame, text="⭐ Добавить выбранные в коллекцию", command=self.add_selected_to_collection).pack(side=tk.LEFT, padx=2)

        table_frame = ttk.Frame(self.main_frame)
        table_frame.grid(row=4, column=0, pady=10, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        columns = ("chk", "key", "challenge", "category", "level", "description", "ctf", 
                  "writeup", "wsite", "attachment", "tag1", "tag2", "tag3", "tag4", "tag5")
        self.tasks_tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=20)
        
        self.headers_map = {
            "chk": "☐",  
            "key": "ID",
            "challenge": "Задача",
            "category": "Категория",
            "level": "Уровень",
            "description": "Описание",
            "ctf": "CTF",
            "writeup": "Writeup",
            "wsite": "Сайт",
            "attachment": "Вложение",
            "tag1": "Тег 1", "tag2": "Тег 2", "tag3": "Тег 3", "tag4": "Тег 4", "tag5": "Тег 5"
        }

        sortable_cols = ["key", "challenge", "category", "level", "ctf", "writeup", "wsite", "attachment", "tag1", "tag2", "tag3", "tag4", "tag5"]

        for col_id in columns:
            display_name = self.headers_map.get(col_id, col_id)
            
            # Если это колонка с чекбоксами -> привязываем функцию Выбрать/Сбросить всё
            if col_id == "chk":
                self.tasks_tree.heading(col_id, text=display_name, command=self.toggle_select_all)
            # Если разрешена сортировка
            elif col_id in sortable_cols:
                self.tasks_tree.heading(col_id, text=display_name, command=lambda c=col_id: self.on_header_click(c))
            else:
                self.tasks_tree.heading(col_id, text=display_name)

        self.tasks_tree.column("chk", width=40, minwidth=40, stretch=False, anchor="center")
        self.tasks_tree.column("key", width=50, minwidth=50, stretch=False)
        self.tasks_tree.column("challenge", width=150)
        self.tasks_tree.column("category", width=100)
        self.tasks_tree.column("level", width=70)
        self.tasks_tree.column("description", width=80)
        self.tasks_tree.column("ctf", width=120)
        self.tasks_tree.column("writeup", width=80, anchor="center")
        self.tasks_tree.column("wsite", width=80, anchor="center")
        self.tasks_tree.column("attachment", width=80, anchor="center")
        self.tasks_tree.column("tag1", width=80)
        self.tasks_tree.column("tag2", width=80)
        self.tasks_tree.column("tag3", width=80)
        self.tasks_tree.column("tag4", width=80)
        self.tasks_tree.column("tag5", width=80)
        
        # Скроллбар
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tasks_tree.yview)
        self.tasks_tree.configure(yscrollcommand=scrollbar.set)
        
        # Размещение
        self.tasks_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)
        self.main_frame.rowconfigure(4, weight=1)
        
        self.tasks_tree.bind("<ButtonRelease-1>", self.toggle_checkbox)
        self.tasks_tree.bind("<Double-1>", self.show_task_details)
        self.tasks_tree.bind("<Double-Button-3>", self.edit_cell_on_right_click)
        self.update_header_arrows()
        self.apply_treeview_colors()
        self.update_tasks_table()
    
    def toggle_checkbox(self, event):
        """Переключает галочку ☑/☐ при клике по первой колонке"""
        region = self.tasks_tree.identify("region", event.x, event.y)
        if region != "cell": return
        
        col = self.tasks_tree.identify_column(event.x)
        if col == "#1": # Колонка с чекбоксами всегда первая
            row_id = self.tasks_tree.identify_row(event.y)
            if not row_id: return
            
            values = list(self.tasks_tree.item(row_id, "values"))
            task_id = self._get_real_task_id(str(values[1]))
            
            # Меняем значение
            if values[0] == "☐":
                values[0] = "☑"
                self.selected_tasks.add(task_id)
            else:
                values[0] = "☐"
                self.selected_tasks.discard(task_id)
                
            # Обновляем только одну строку для скорости
            self.tasks_tree.item(row_id, values=values)

    def select_all_tasks(self):
        """Выделяет все задачи, которые сейчас видны в таблице"""
        for row_id in self.tasks_tree.get_children():
            values = list(self.tasks_tree.item(row_id, "values"))
            task_id = str(values[1])
            values[0] = "☑"
            self.selected_tasks.add(task_id)
            self.tasks_tree.item(row_id, values=values)

    def toggle_select_all(self):
        """Переключает выделение всех видимых задач при клике на заголовок 'chk'"""
        visible_items = self.tasks_tree.get_children()
        if not visible_items: return
        
        # Проверяем, все ли сейчас выделены
        all_selected = True
        for row_id in visible_items:
            values = self.tasks_tree.item(row_id, "values")
            if values[0] == "☐":
                all_selected = False
                break
                
        # Если все выделены -> сбрасываем всё
        if all_selected:
            self.deselect_all_tasks()
            self.headers_map["chk"] = "☐" 
        # Если выделены не все (или ни одной) -> выделяем всё
        else:
            self.select_all_tasks()
            self.headers_map["chk"] = "☑" 
            
        # Обновляем заголовок колонки
        self.tasks_tree.heading("chk", text=self.headers_map["chk"])
    
    def deselect_all_tasks(self):
        """Снимает выделение со всех задач в таблице"""
        for row_id in self.tasks_tree.get_children():
            values = list(self.tasks_tree.item(row_id, "values"))
            task_id = str(values[1])
            values[0] = "☐"
            self.selected_tasks.discard(task_id)
            self.tasks_tree.item(row_id, values=values)

    def add_selected_to_collection(self):
        """Вызов окна для массового добавления в коллекцию"""
        if not self.selected_tasks:
            messagebox.showinfo("Инфо", "Сначала выделите задачи галочками (☑).")
            return
        self.open_add_to_collection_dialog(list(self.selected_tasks))
    
    def update_tasks_table(self):
        """Обновление таблицы задач согласно фильтрам и СОРТИРОВКЕ"""
        for item in self.tasks_tree.get_children():
            self.tasks_tree.delete(item)
        
        # 1. Получение отфильтрованных задач 
        search_query = self.search_var.get() if hasattr(self, 'search_var') else ""
        
        filtered_tasks = self.task_manager.get_tasks_by_filters(
            query=search_query,           
            category=self.category_var.get(), 
            level=self.level_var.get(),
            ctf=self.ctf_var.get() if hasattr(self, 'ctf_var') else None,
            tag=self.tag_var.get() if hasattr(self, 'tag_var') else None,
            has_writeup=self.writeup_var.get(),
            has_wsite=self.wsite_var.get(),
            has_attachment=self.attachment_var.get()
        )
        
        # 2. СОРТИРОВКА
        if self.sort_column:
            def sort_key(task):
                value = getattr(task, self.sort_column, "")
                
                # --- Сортировка по ID ---
                if self.sort_column == "key":
                    try: return int(value)
                    except ValueError: return 0
                
                # --- Сортировка по УРОВНЮ СЛОЖНОСТИ ---
                if self.sort_column == "level":
                    val = str(value).lower().strip()
                    if val in ["easy", "легкий"]: return 1
                    if val in ["medium", "средний"]: return 2
                    if val in ["hard", "сложный"]: return 3
                    if val == "insane": return 4
                    return 5  
                
                # --- Сортировка по ЧЕКБОКСАМ (Сайт, Вложение, Writeup) ---
                if self.sort_column in ["writeup", "wsite", "attachment"]:
                    # Проверяем, есть ли реально данные (✅) или нет (❌)
                    has_data = bool(value and value != "[]" and value != "None" and str(value).strip())
                    # 1 - значит данные есть (будут наверху), 0 - данных нет
                    return 1 if has_data else 0

                # --- Стандартная сортировка по алфавиту для остальных полей ---
                if value is None: return ""
                return str(value).lower()
                
            filtered_tasks.sort(key=sort_key, reverse=self.sort_descending)
        
        # 3. Добавление задач в таблицу 
        for i, task in enumerate(filtered_tasks):
            has_wr = "✅" if task.writeup and task.writeup != "[]" and task.writeup != "None" else "❌"
            has_site = "✅" if task.wsite and task.wsite != "[]" and task.wsite != "None" and task.wsite != "" else "❌"
            has_att = "✅" if task.attachment and task.attachment != "[]" and task.attachment != "None" else "❌"
            
            # Определяем, четная это строка или нечетная
            row_tag = 'evenrow' if i % 2 == 0 else 'oddrow'
            chk_val = "☑" if str(task.key) in self.selected_tasks else "☐"
            self.tasks_tree.insert("", tk.END, values=(
                chk_val,
                task.key,
                task.challenge,
                task.category,
                task.level if task.level else "Не указан",
                task.description[:50] + "..." if len(task.description) > 50 else task.description,
                task.ctf,
                has_wr,
                has_site,
                has_att,
                task.tag1 if task.tag1 else "",
                task.tag2 if task.tag2 else "",
                task.tag3 if task.tag3 else "",
                task.tag4 if task.tag4 else "",
                task.tag5 if task.tag5 else ""
            ), tags=(row_tag,))  
    
    def on_filters_changed(self, event=None):
        """Обработчик изменения фильтров"""
        self.update_tasks_table()
        self.update_filter_status()
        
        if event and hasattr(event, 'widget'):
            try:
                event.widget.selection_clear() 
            except:
                pass
        
        self.root.focus_set()
    
    def reset_filters(self):
        """Сброс фильтров и сортировки к значениям по умолчанию"""
        if hasattr(self, 'search_var'): self.search_var.set("")
        self.category_var.set("Все")
        self.level_var.set("Все")
        if hasattr(self, 'ctf_var'): self.ctf_var.set("Все")
        if hasattr(self, 'tag_var'): self.tag_var.set("Все")
            
        self.writeup_var.set(False)
        self.wsite_var.set(False)
        self.attachment_var.set(False)
        self.sort_column = "key"
        self.sort_descending = False
        self.update_header_arrows()
        self.update_tasks_table()
        self.update_filter_status()
        
    def update_filter_comboboxes(self):
        """Пересчитывает списки тегов, категорий и уровней и обновляет выпадающие меню"""
        if not hasattr(self, 'category_combo') or not self.category_combo.winfo_exists():
            return 

        # 1. Обновляем категории 
        categories = ["Все", "Пусто"] + self.task_manager.get_all_categories()
        self.category_combo['values'] = categories
        if self.category_var.get() not in categories:
            self.category_var.set("Все")

        # 2. Обновляем уровни 
        raw_levels = self.task_manager.get_all_levels()
        clean_levels =[l for l in raw_levels if l and l.lower() != "не указан"]
        def get_level_priority(level_name):
            name = level_name.lower().strip()
            if name in["easy", "легкий"]: return 1
            if name in ["medium", "средний"]: return 2
            if name in["hard", "сложный"]: return 3
            if name == "insane": return 4
            return 5
        clean_levels.sort(key=lambda x: (get_level_priority(x), x))
        
        levels = ["Все", "Не указан"] + clean_levels
        self.level_combo['values'] = levels
        if self.level_var.get() not in levels:
            self.level_var.set("Все")

        # 3. Обновляем турниры 
        ctfs = ["Все", "Пусто"] + self.task_manager.get_all_ctfs()
        self.ctf_combo['values'] = ctfs
        if self.ctf_var.get() not in ctfs:
            self.ctf_var.set("Все")

        # 4. Обновляем теги 
        tags =["Все", "Пусто"] + self.task_manager.get_all_tags()
        self.tag_combo['values'] = tags
        if self.tag_var.get() not in tags:
            self.tag_var.set("Все")
    
    def update_filter_status(self):
        """Обновление статусной строки фильтров"""
        # === 1. Получаем текст из строки поиска ===
        search_query = self.search_var.get().strip() if hasattr(self, 'search_var') else ""
        
        category = self.category_var.get()
        level = self.level_var.get()
        ctf = self.ctf_var.get() if hasattr(self, 'ctf_var') else "Все"
        tag = self.tag_var.get() if hasattr(self, 'tag_var') else "Все"
        writeup = self.writeup_var.get()
        wsite = self.wsite_var.get()
        attachment = self.attachment_var.get()
        
        # === 2. Передаем search_query САМЫМ ПЕРВЫМ параметром ===
        filtered_tasks = self.task_manager.get_tasks_by_filters(
            search_query,    
            category, 
            level, 
            ctf,     
            tag,  
            writeup, 
            wsite, 
            attachment
        )
        
        total_tasks = len(self.task_manager.tasks)
        
        status_text = f"📊 Показано задач: {len(filtered_tasks)} из {total_tasks}"
        
        # === 3. Добавляем отображение текста поиска в статус внизу ===
        if search_query: status_text += f" | 🔍 Поиск: '{search_query}'"
        
        if category != "Все": status_text += f" | 🏷️ {category}"
        if level != "Все": status_text += f" | ⚡ {level}"
        if ctf != "Все": status_text += f" | 🏆 {ctf}"
        if tag != "Все": status_text += f" | # {tag}"
        
        if writeup: status_text += " | 📝 Есть writeup"
        if wsite: status_text += " | 🌐 Есть сайт"
        if attachment: status_text += " | 📎 Есть вложение"
        
        current_theme = self.settings_manager.get_setting("theme", "Светлая")
        accent_color = "#58a6ff" if current_theme == "Темная" else "blue"
        
        self.filter_status.config(text=status_text, foreground=accent_color)
    
    
    def perform_search(self):
        """Выполнение поиска задач"""
        query = self.search_var.get().strip()
        category = self.search_category_var.get()
        has_writeup = self.search_writeup_var.get()
        has_wsite = self.search_wsite_var.get()
        has_attachment = self.search_attachment_var.get()
        
        if not query and category == "Все" and not has_writeup and not has_wsite and not has_attachment:
            results = self.task_manager.tasks
        else:
            results = self.task_manager.search_tasks_with_filters(
                query, category, has_writeup, has_wsite, has_attachment
            )
        
        for item in self.search_tree.get_children():
            self.search_tree.delete(item)
        
        for task in results:
            self.search_tree.insert("", tk.END, values=(
                task.key,
                task.challenge,
                task.category,
                task.level if task.level else "Не указан",
                task.description[:60] + "..." if len(task.description) > 60 else task.description,
                task.ctf,
                "✅" if task.writeup and task.writeup != "[]" else "❌",
                "✅" if task.wsite and task.wsite != "[]" else "❌",
                "✅" if task.attachment and task.attachment != "[]" else "❌",
                task.tag1 if task.tag1 else "",
                task.tag2 if task.tag2 else "",
                task.tag3 if task.tag3 else "",
                task.tag4 if task.tag4 else "",
                task.tag5 if task.tag5 else ""
            ))
        
        status_parts = []
        if query:
            status_parts.append(f"текст: '{query}'")
        if category != "Все":
            status_parts.append(f"категория: {category}")
        if has_writeup:
            status_parts.append("есть writeup")
        if has_wsite:
            status_parts.append("есть сайт")
        if has_attachment:
            status_parts.append("есть вложение")
        
        status_text = f"🔍 Найдено задач: {len(results)}"
        if status_parts:
            status_text += f" по критериям: {', '.join(status_parts)}"
        
        current_theme = self.settings_manager.get_setting("theme", "Светлая")
        success_color = "#4ade80" if current_theme == "Темная" else "green"
        fail_color = "#f87171" if current_theme == "Темная" else "red"
        
        self.search_status.config(
            text=status_text,
            foreground=success_color if results else fail_color
        )
    
    def clear_search(self):
        """Очистка результатов поиска"""
        self.search_var.set("")
        self.search_category_var.set("Все")
        self.search_writeup_var.set(False)
        self.search_wsite_var.set(False)
        self.search_attachment_var.set(False)
        for item in self.search_tree.get_children():
            self.search_tree.delete(item)
            
        current_theme = self.settings_manager.get_setting("theme", "Светлая")
        accent_color = "#58a6ff" if current_theme == "Темная" else "blue"
        self.search_status.config(text="Введите поисковый запрос", foreground=accent_color)
    
    def create_statistics_interface(self):
        """Интерфейс статистики (Дашборд с карточками и скроллом)"""
        title_frame = ttk.Frame(self.main_frame)
        title_frame.grid(row=0, column=0, pady=10, sticky=(tk.W, tk.E))
        title_frame.columnconfigure(0, weight=1)
        
        ttk.Label(title_frame, text="📊 Статистика", font=("Arial", 20, "bold")).grid(row=0, column=0, sticky=tk.W)
        ttk.Button(title_frame, text="← На главную", command=self.return_to_main_menu).grid(row=0, column=1, sticky=tk.E)
        
        stats = self.task_manager.get_task_statistics()
        
        # === ДИНАМИЧЕСКИЕ ЦВЕТА И ФИКСАЦИЯ СТИЛЯ ШРИФТА ЗАГОЛОВКОВ ===
        current_theme = self.settings_manager.get_setting("theme", "Светлая")
        is_dark = current_theme == "Темная"
        
        accent_color = "#58a6ff" if is_dark else "blue"
        lbl_color = "#a0a0a0" if is_dark else "gray" 
        
        # Настройка стиля для заголовков LabelFrame, чтобы размер текста и эмодзи был одинаков в обеих темах
        style = ttk.Style()
        style.configure("TLabelframe.Label", font=("Arial", 14, "bold"))
        
        bg_color = self.root.cget('bg')
        canvas = tk.Canvas(self.main_frame, highlightthickness=0, bg=bg_color)
        scrollbar = ttk.Scrollbar(self.main_frame, orient=tk.VERTICAL, command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        
        def configure_canvas(event):
            canvas.itemconfig(canvas_window, width=event.width)
            
        canvas.bind("<Configure>", configure_canvas)
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=1, column=1, sticky=(tk.N, tk.S))
        self.main_frame.rowconfigure(1, weight=1)

        def _on_mousewheel(event):
            if scrollable_frame.winfo_reqheight() <= canvas.winfo_height(): return
            if platform.system() == 'Windows': canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            elif platform.system() == 'Darwin': canvas.yview_scroll(int(-1 * event.delta), "units")
            else:
                if event.num == 4: canvas.yview_scroll(-1, "units")
                elif event.num == 5: canvas.yview_scroll(1, "units")

        if platform.system() == 'Linux':
            self.root.bind_all("<Button-4>", _on_mousewheel)
            self.root.bind_all("<Button-5>", _on_mousewheel)
        else:
            self.root.bind_all("<MouseWheel>", _on_mousewheel)

        # === ФУНКЦИЯ СОЗДАНИЯ КРАСИВОЙ КАРТОЧКИ ===
        def create_stat_card(parent, title, items, icon=""):
            card = ttk.LabelFrame(parent, text=f"{icon} {title}", padding=20)
            card.pack(fill=tk.X, pady=15, padx=20) 
            card.columnconfigure(0, minsize=220) 
            card.columnconfigure(1, minsize=80)  
            card.columnconfigure(2, minsize=220) 
            card.columnconfigure(3, minsize=80)  
            
            row, col = 0, 0
            midpoint = (len(items) + 1) // 2
            
            for key, val in items.items():
                lbl_key = ttk.Label(card, text=f"• {key}:", font=("Arial", 13, "bold"), foreground=lbl_color)
                lbl_key.grid(row=row, column=col*2, sticky=tk.W, pady=6)
                
                lbl_val = ttk.Label(card, text=str(val), font=("Arial", 14, "bold"))
                lbl_val.grid(row=row, column=col*2+1, sticky=tk.W, pady=6)
                
                row += 1
                if len(items) > 10 and row >= midpoint:
                    row = 0; col += 1

        general_items = {
            "Всего задач": stats['total_tasks'],
            "Категорий": stats['categories_count'],
            "Уровней сложности": stats['levels_count'],
            "Тегов": stats['tags_count']
        }
        create_stat_card(scrollable_frame, "Общая статистика", general_items, "📈")
        create_stat_card(scrollable_frame, "Распределение по категориям", stats['categories'], "📁")
        create_stat_card(scrollable_frame, "Распределение по уровням", stats['levels'], "⚡")
        
        if 'tags' in stats and stats['tags']:
            sorted_tags = dict(sorted(stats['tags'].items(), key=lambda x: str(x[0]).lower()))
            create_stat_card(scrollable_frame, "Распределение по тегам", sorted_tags, "🏷️")

        file_info = f"Текущий файл базы данных: {os.path.basename(self.current_csv_file)}"
        ttk.Label(scrollable_frame, text=file_info, font=("Arial", 12, "italic"), 
                  foreground=accent_color, wraplength=700, justify=tk.CENTER).pack(pady=25, anchor=tk.CENTER)
        
    def create_settings_interface(self):
        """Интерфейс настроек (Без выбора языка, увеличенные шрифты)"""
        title_label = ttk.Label(self.main_frame, text="⚙️ Настройки приложения", font=("Arial", 20, "bold"))
        title_label.grid(row=0, column=0, pady=15, sticky=tk.W)
        
        back_btn = ttk.Button(self.main_frame, text="← На главную", command=self.return_to_main_menu)
        back_btn.grid(row=0, column=0, sticky=tk.E)
        
        settings_frame = ttk.LabelFrame(self.main_frame, text="Настройки", padding="25")
        settings_frame.grid(row=1, column=0, pady=15, sticky=(tk.W, tk.E))
        
        current_theme = self.settings_manager.get_setting("theme", "Системная")
        current_auto_refresh = self.settings_manager.get_setting("auto_refresh", True)
        
        path_color = "#58a6ff" if current_theme == "Темная" else "#0000cc"
        
        self.theme_var = tk.StringVar(value=current_theme)
        self.auto_refresh_var = tk.BooleanVar(value=current_auto_refresh)
        
        # --- Настройки интерфейса ---
        ttk.Label(settings_frame, text="Тема интерфейса:", font=("Arial", 14)).grid(row=0, column=0, sticky=tk.W, pady=12)
        theme_combo = ttk.Combobox(settings_frame, textvariable=self.theme_var, 
                                  values=["Светлая", "Темная", "Системная"], state="readonly", width=25, font=("Arial", 13))
        theme_combo.grid(row=0, column=1, padx=15, pady=12, sticky=tk.W)
        theme_combo.bind("<<ComboboxSelected>>", lambda e: [theme_combo.selection_clear(), self.root.focus_set()])
        
        # Вторая строка - Автообновление 
        ttk.Label(settings_frame, text="Автообновление:", font=("Arial", 14)).grid(row=1, column=0, sticky=tk.W, pady=12)
        auto_refresh_check = ttk.Checkbutton(settings_frame, text="Автоматически обновлять данные", 
                                           variable=self.auto_refresh_var)
        auto_refresh_check.grid(row=1, column=1, padx=15, pady=12, sticky=tk.W)
        
        # --- Раздел файлов и каталогов ---
        files_frame = ttk.LabelFrame(settings_frame, text="Файлы и каталоги", padding="20")
        files_frame.grid(row=2, column=0, columnspan=2, pady=20, sticky=(tk.W, tk.E))
        
        ttk.Label(files_frame, text="Текущий файл задач:", font=("Arial", 13, "bold")).grid(row=0, column=0, sticky=tk.W)
        # Добавлено wraplength=450
        ttk.Label(files_frame, text=self.current_csv_file, font=("Arial", 13), foreground=path_color, wraplength=450).grid(row=0, column=1, sticky=tk.W, padx=15)
        
        ttk.Label(files_frame, text="Файл настроек:", font=("Arial", 13, "bold")).grid(row=1, column=0, sticky=tk.W, pady=12)
        ttk.Label(files_frame, text=self.settings_manager.settings_file, font=("Arial", 13), foreground=path_color, wraplength=450).grid(row=1, column=1, sticky=tk.W, padx=15, pady=12)
        
        # --- Кнопки ---
        button_frame = ttk.Frame(settings_frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=30)
        
        save_btn = ttk.Button(button_frame, text="Сохранить настройки", command=self.save_application_settings, width=30)
        save_btn.grid(row=0, column=0, padx=20)
        
        reset_btn = ttk.Button(button_frame, text="Сбросить настройки", command=self.reset_application_settings, width=30)
        reset_btn.grid(row=0, column=1, padx=20)
        
    def save_application_settings(self):
        """Сохранение настроек приложения"""
        try:
            new_theme = self.theme_var.get()
            settings = {
                "theme": new_theme,
                "auto_refresh": self.auto_refresh_var.get(),
                "csv_file_path": self.current_csv_file,
                "window_width": self.root.winfo_width(),
                "window_height": self.root.winfo_height()
            }

            self.settings_manager.update_settings(**settings)
            if self.settings_manager.save_settings():
                self.apply_app_theme(new_theme)
                self.apply_treeview_colors() 
                self.show_option4()
                messagebox.showinfo("Успех", "Настройки успешно сохранены!")
            else:
                messagebox.showwarning("Предупреждение", "Настройки сохранены в запасной файл.")

        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при сохранении настроек:\n{str(e)}")
              
    def reset_application_settings(self):
        """Сброс настроек к значениям по умолчанию"""
        result = messagebox.askyesno(
            "Подтверждение", 
            "Вы уверены, что хотите сбросить все настройки к значениям по умолчанию?"
        )
        
        if result:
            self.settings_manager.reset_to_defaults()
            messagebox.showinfo("Успех", "Настройки сброшены к значениям по умолчанию!")
            self.show_option4()
    
    def return_to_main_menu(self):
        """Возврат к главному меню"""
        if hasattr(self, 'main_task_manager'):
            self.task_manager = self.main_task_manager
            self.current_csv_file = self.settings_manager.get_setting("csv_file_path")
            del self.main_task_manager
            self.in_collection_view = False
        self.restore_main_database()
        self.clear_content()
        self.create_logo_section()
        self.create_welcome_section()
        
    def open_external_file(self, filename_raw, ctf=None, category=None, task_name=None, task_id=None):
        """Открывает файл. Строгий приоритет для d.txt"""
        if not filename_raw or filename_raw in ["[]", "None", ""]: return
        filename = filename_raw
        try:
            if filename.startswith("[") and filename.endswith("]"):
                parsed = ast.literal_eval(filename)
                if isinstance(parsed, list) and len(parsed) > 0: filename = parsed[0]
        except: pass 
        target_folder = self._resolve_task_path(ctf, category, task_name)
        found_path = None
        
        if target_folder:
            # Сценарий A: Запрос на d.txt
            if filename == "d.txt":
                files = os.listdir(target_folder)
                
                # 1. Приоритет: Точно d.txt
                for f in files:
                    if f.lower() == "d.txt":
                        found_path = os.path.join(target_folder, f)
                        break
                
                # 2. Приоритет: Description...
                if not found_path:
                    for f in files:
                        if f.lower().startswith("description") and f.lower().endswith(".txt"):
                            found_path = os.path.join(target_folder, f)
                            break
                            
                # 3. Приоритет: Любой txt 
                if not found_path:
                    for f in files:
                        low = f.lower()
                        if low.endswith(".txt") and "writeup" not in low and "cipher" not in low:
                            found_path = os.path.join(target_folder, f)
                            break
            
            # Сценарий B: Точное совпадение
            elif os.path.exists(os.path.join(target_folder, filename)):
                found_path = os.path.join(target_folder, filename)
            
            # Сценарий C: Поиск БЕЗ учета расширения
            else:
                files = os.listdir(target_folder)
                target_lower = filename.lower()
                
                # 1. Имя.расширение 
                for f in files:
                    if f.lower().startswith(target_lower + "."):
                        found_path = os.path.join(target_folder, f)
                        break
                
                # 2. Просто имя 
                if not found_path:
                    for f in files:
                        name_part, _ = os.path.splitext(f)
                        if name_part.lower() == target_lower:
                            found_path = os.path.join(target_folder, f)
                            break
                
                # 3. Fuzzy
                if not found_path:
                    def simplify(s): return re.sub(r'[\W_]+', '', s.lower())
                    target_simple = simplify(filename)
                    for f in files:
                        if simplify(f).startswith(target_simple):
                            found_path = os.path.join(target_folder, f)
                            break

        # 6. Открытие
        if not found_path:
            msg = f"Не удалось найти файл: '{filename}'"
            if target_folder: msg += f"\nВ папке: '{os.path.basename(target_folder)}'"
            messagebox.showerror("Файл не найден", msg)
            return

        try:
            if platform.system() == 'Darwin': subprocess.call(('open', found_path))
            elif platform.system() == 'Windows': os.startfile(found_path)
            else: subprocess.call(('xdg-open', found_path))
            self.show_floating_navigator(found_path, ctf, category, task_name)
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось открыть файл:\n{e}")
    
    def show_task_details(self, event):
        """Показывает окно с деталями задачи"""
        selected_item = self.tasks_tree.selection()
        if not selected_item: return
        
        item_values = self.tasks_tree.item(selected_item[0])['values']
        visible_id = str(item_values[1]) 
        task_id = self._get_real_task_id(visible_id)
        
        task = next((t for t in self.task_manager.tasks if str(t.key) == str(task_id)), None)
        if not task: return

        if not hasattr(self, 'task_playlists'): self.task_playlists = {}
        self.task_playlists[task.challenge] = []
        current_playlist = self.task_playlists[task.challenge]
        self.current_task_active_files = current_playlist 

        detail_window = tk.Toplevel(self.root)
        detail_window.title(f"Задача: {task.challenge}")
        detail_window.geometry("600x650")
        current_theme = self.settings_manager.get_setting("theme", "Светлая")
        is_dark = current_theme == "Темная"
        
        lbl_color = "#9fb3c8" if is_dark else "#2c3e50"       
        link_color = "#58a6ff" if is_dark else "blue"         
        edit_color = "#a0a0a0" if is_dark else "gray"         
        archive_color = "#e3b341" if is_dark else "brown"    
        alt_color = "#4ade80" if is_dark else "darkgreen"     

        ttk.Label(detail_window, text="📄 Детальная информация о задаче", font=("Arial", 14, "bold")).pack(pady=15)
        content_frame = ttk.Frame(detail_window, padding="20")
        content_frame.pack(fill=tk.BOTH, expand=True)

        def copy_to_clipboard(text):
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            self.root.update()
            messagebox.showinfo("Скопировано", f"Текст скопирован:\n{text}")

        # === ГЛАВНАЯ ФУНКЦИЯ ОТРИСОВКИ ===
        def create_row(parent, label_text, value_text, is_link=False, filename=None, is_web_link=False, is_netcat=False):
            row_frame = ttk.Frame(parent)
            row_frame.pack(fill=tk.X, pady=5)
            lbl = ttk.Label(row_frame, text=label_text, width=22, font=("Arial", 10, "bold"), foreground=lbl_color)
            lbl.pack(side=tk.LEFT, anchor="n")
            
            clean_value = str(value_text).strip()
            try:
                if clean_value.startswith("[") and clean_value.endswith("]"):
                    parsed = ast.literal_eval(clean_value)
                    if isinstance(parsed, list) and len(parsed) > 0: clean_value = str(parsed[0])
            except: pass
            clean_value = clean_value.strip("[]'\" ")

            if is_web_link and clean_value and clean_value != "[]" and clean_value != "":
                val = ttk.Label(row_frame, text=f"{clean_value} (Перейти 🌐)", font=("Arial", 10, "underline"), foreground=link_color, cursor="hand2")
                val.pack(side=tk.LEFT, anchor="n")
                val.bind("<Button-1>", lambda e: webbrowser.open(clean_value))
                copy_lbl = ttk.Label(row_frame, text=" 📋", font=("Arial", 12), cursor="hand2")
                copy_lbl.pack(side=tk.LEFT, anchor="n", padx=5)
                copy_lbl.bind("<Button-1>", lambda e: copy_to_clipboard(clean_value))
            
            elif is_netcat and clean_value and clean_value != "[]" and clean_value != "":
                nc_color = "#ffb86c" if is_dark else "#d35400"
                val = ttk.Label(row_frame, text=clean_value, font=("Consolas", 10, "bold"), foreground=nc_color)
                val.pack(side=tk.LEFT, anchor="n")
                copy_lbl = ttk.Label(row_frame, text=" 📋", font=("Arial", 12), cursor="hand2")
                copy_lbl.pack(side=tk.LEFT, anchor="n", padx=5)
                copy_lbl.bind("<Button-1>", lambda e: copy_to_clipboard(clean_value))

            elif is_link and filename and filename != "[]" and filename != "":
                clean_filename = str(filename).strip()
                try:
                    if clean_filename.startswith("[") and clean_filename.endswith("]"):
                        parsed = ast.literal_eval(clean_filename)
                        if isinstance(parsed, list) and len(parsed) > 0: clean_filename = str(parsed[0])
                except: pass
                clean_filename = clean_filename.strip("[]'\" ")

                display_text = value_text if "index.html" in value_text else clean_value
                val = ttk.Label(row_frame, text=f"{display_text} (Открыть ↗)", font=("Arial", 10, "underline"), foreground=link_color, cursor="hand2")
                val.pack(side=tk.LEFT, anchor="n")
                val.bind("<Button-1>", lambda e: self.open_external_file(clean_filename, ctf=task.ctf, category=task.category, task_name=task.challenge, task_id=task.key))
                edit_lbl = ttk.Label(row_frame, text=" ✏️(Ред.)", font=("Arial", 10), foreground=edit_color, cursor="hand2")
                edit_lbl.pack(side=tk.LEFT, anchor="n", padx=5)
                edit_lbl.bind("<Button-1>", lambda e: self.edit_file_safely(clean_filename, ctf=task.ctf, category=task.category, task_name=task.challenge, task_id=task.key))
                edit_lbl.bind("<Enter>", lambda e: edit_lbl.configure(foreground="red"))
                edit_lbl.bind("<Leave>", lambda e: edit_lbl.configure(foreground=edit_color))
            else:
                display = clean_value if clean_value != "[]" and clean_value != "" else "Отсутствует"
                ttk.Label(row_frame, text=display, font=("Arial", 10), wraplength=380).pack(side=tk.LEFT, anchor="n")

        create_row(content_frame, "ID задачи:", visible_id)
        create_row(content_frame, "Название задачи:", task.challenge)
        create_row(content_frame, "Категория:", task.category)
        create_row(content_frame, "Уровень сложности:", task.level)
        create_row(content_frame, "CTF мероприятие:", task.ctf)
        ttk.Separator(content_frame, orient='horizontal').pack(fill='x', pady=10)

        # === ОПИСАНИЕ ===
        files_info = self.get_task_files_info(task.ctf, task.category, task.challenge)
        
        desc_frame = ttk.Frame(content_frame)
        desc_frame.pack(fill=tk.X, pady=5)
        ttk.Label(desc_frame, text="Описание:", width=22, font=("Arial", 10, "bold"), foreground=lbl_color).pack(side=tk.LEFT, anchor="n")
        
        if not task.description.endswith('.txt'):
             ttk.Label(desc_frame, text=task.description, font=("Arial", 10), wraplength=380).pack(side=tk.LEFT)
        else:
            has_content = False 
            if files_info['zip']:
                self.current_task_active_files.append(files_info['zip'])
                zip_lbl = ttk.Label(desc_frame, text="📦 Архив (Открыть)", font=("Arial", 10, "underline"), foreground=archive_color, cursor="hand2")
                zip_lbl.pack(side=tk.LEFT, padx=(0, 5))
                zip_lbl.bind("<Button-1>", lambda e, f=files_info['zip']: self.open_external_file(f, ctf=task.ctf, category=task.category, task_name=task.challenge))
                has_content = True
            
            if files_info['desc']:
                self.current_task_active_files.append(files_info['desc'])
                if has_content: ttk.Label(desc_frame, text="|", foreground="gray").pack(side=tk.LEFT, padx=5)
                desc_filename = files_info['desc']
                
                lbl = ttk.Label(desc_frame, text="📄 Текст (Открыть)", font=("Arial", 10, "underline"), foreground=link_color, cursor="hand2")
                lbl.pack(side=tk.LEFT, padx=(0, 2))
                lbl.bind("<Button-1>", lambda e, f=desc_filename: self.open_external_file(f, ctf=task.ctf, category=task.category, task_name=task.challenge))
                
                edt = ttk.Label(desc_frame, text="✏️", font=("Arial", 10), foreground=edit_color, cursor="hand2")
                edt.pack(side=tk.LEFT)
                edt.bind("<Button-1>", lambda e, f=desc_filename: self.edit_file_safely(f, ctf=task.ctf, category=task.category, task_name=task.challenge))
                
                trans_container = ttk.Frame(desc_frame)
                trans_container.pack(side=tk.LEFT, padx=10)

                def render_translation_ui():
                    for widget in trans_container.winfo_children(): widget.destroy()
                    target_folder = self._resolve_task_path(task.ctf, task.category, task.challenge)
                    if target_folder:
                        file_path = os.path.join(target_folder, desc_filename)
                        if os.path.exists(file_path):
                            try:
                                with open(file_path, 'r', encoding='utf-8') as f: content = f.read()
                                has_auto = "--- АВТОМАТИЧЕСКИЙ ПЕРЕВОД (RU) ---" in content
                                rus = sum(1 for c in content if 'а' <= c.lower() <= 'я' or c.lower() == 'ё')
                                tot = sum(1 for c in content if c.isalpha())
                                if has_auto or (tot > 0 and (rus / tot) >= 0.2):
                                    ttk.Label(trans_container, text="✅ RU", font=("Arial", 10, "bold"), foreground=alt_color).pack(side=tk.LEFT)
                                else:
                                    trans_btn = ttk.Label(trans_container, text="🌐 (Перевести)", font=("Arial", 10, "bold"), foreground="#2980b9", cursor="hand2")
                                    trans_btn.pack(side=tk.LEFT)
                                    trans_btn.bind("<Button-1>", lambda e, f=desc_filename: self.translate_file_inline(f, ctf=task.ctf, category=task.category, task_name=task.challenge, on_success_callback=render_translation_ui))
                            except: pass 
                render_translation_ui()
                has_content = True

            if not has_content:
                ttk.Label(desc_frame, text="Файлы не найдены", foreground="red").pack(side=tk.LEFT)

        # WRITEUP
        has_wr = task.writeup and task.writeup != "[]" and task.writeup != "None"
        if has_wr:
            clean_wr = str(task.writeup).strip()
            try:
                if clean_wr.startswith("[") and clean_wr.endswith("]"):
                    parsed = ast.literal_eval(clean_wr)
                    if isinstance(parsed, list) and len(parsed) > 0: clean_wr = str(parsed[0])
            except: pass
            clean_wr = clean_wr.strip("[]'\" ")
            self.current_task_active_files.append(clean_wr)
            
        create_row(content_frame, "Наличие writeup:", "Доступен" if has_wr else "Нет", is_link=has_wr, filename=task.writeup)
        
        has_site = task.wsite and task.wsite != "[]" and task.wsite != "None" and task.wsite != ""
        create_row(content_frame, "Сайт:", task.wsite, is_web_link=has_site)
        has_nc = task.nc and task.nc != "[]" and task.nc != "None" and task.nc != ""
        create_row(content_frame, "Netcat:", task.nc, is_netcat=has_nc)
        
        # ВЛОЖЕНИЯ
        raw_att = task.attachment
        att_list =[]
        if raw_att and raw_att != "[]" and raw_att != "None" and raw_att != "":
            try:
                clean_str = raw_att.strip()
                if clean_str.startswith("[") and clean_str.endswith("]"):
                    parsed = ast.literal_eval(clean_str)
                    if isinstance(parsed, list): att_list =[str(x).strip() for x in parsed if x]
                else: att_list = [clean_str]
            except: att_list = [str(raw_att).strip()]

        if not att_list:
            create_row(content_frame, "Файл задания:", "Нет вложений")
        else:
            for i, filename in enumerate(att_list):
                self.current_task_active_files.append(filename)
                lbl = "Файл задания:" if i == 0 else ""
                create_row(content_frame, lbl, filename, is_link=True, filename=filename)

        tags = [t for t in[task.tag1, task.tag2, task.tag3, task.tag4, task.tag5] if t]
        if tags: create_row(content_frame, "Теги:", ", ".join(tags))

        # === КНОПКА: ОТКРЫТЬ ПАПКУ ===
        def open_task_folder():
            target_folder = self._resolve_task_path(task.ctf, task.category, task.challenge)
            if not target_folder or not os.path.exists(target_folder):
                messagebox.showerror("Ошибка", "Оригинальная папка задачи не найдена на диске.")
                return
            try:
                if platform.system() == 'Windows': os.startfile(target_folder)
                elif platform.system() == 'Darwin': subprocess.call(('open', target_folder))
                else: subprocess.call(('xdg-open', target_folder))
            except Exception as e:
                messagebox.showerror("Ошибка", str(e))

        # === БЕЗОПАСНОЕ ЗАКРЫТИЕ ОКНА ===
        def close_task_window():
            if hasattr(self, 'nav_window') and self.nav_window.winfo_exists():
                try: 
                    self.nav_window.event_generate("WM_DELETE_WINDOW")
                except: 
                    self.nav_window.destroy()
            detail_window.destroy()

        detail_window.protocol("WM_DELETE_WINDOW", close_task_window)
        
        btn_frame = ttk.Frame(detail_window)
        btn_frame.pack(pady=(15, 10))
        
        ttk.Button(btn_frame, text="📁 Открыть папку", command=open_task_folder).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="⭐ В коллекцию", command=lambda: self.open_add_to_collection_dialog([str(task.key)])).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Закрыть", command=close_task_window).pack(side=tk.LEFT, padx=5)
        
    def edit_cell_on_right_click(self, event):
        """In-line редактирование метаданных (только разрешенные поля)"""
        region = self.tasks_tree.identify("region", event.x, event.y)
        if region != "cell": return
            
        row_id = self.tasks_tree.identify_row(event.y)
        col_id = self.tasks_tree.identify_column(event.x)
        if not row_id or not col_id: return

        self.tasks_tree.selection_set(row_id)
            
        try:
            col_idx = int(col_id.replace('#', '')) - 1
            columns = self.tasks_tree["columns"]
            actual_col_name = columns[col_idx]
        except: return

        editable_columns =["challenge", "level", "ctf", "tag1", "tag2", "tag3", "tag4", "tag5"]
        
        if actual_col_name not in editable_columns:
            messagebox.showinfo("Инфо", "Это поле нельзя редактировать напрямую.\nФайлы редактируются кликом по ним, а системные данные заблокированы.")
            return

        item_values = self.tasks_tree.item(row_id)['values']
        
        task_key = self._get_real_task_id(str(item_values[1]))
        
        task = next((t for t in self.task_manager.tasks if str(t.key) == task_key), None)
        if not task: return
        
        real_current_value = getattr(task, actual_col_name, "")

        # --- ИНТЕРАКТИВНОЕ ПОЛЕ ВВОДА ---
        bbox = self.tasks_tree.bbox(row_id, col_id)
        if not bbox: return 
        x, y, width, height = bbox

        entry = ttk.Entry(self.tasks_tree, font=("Arial", 10))
        entry.place(x=x, y=y, width=width, height=height)
        
        entry.insert(0, real_current_value)
        entry.select_range(0, tk.END)
        entry.focus_set()

        def save_edit(e=None):
            new_value = entry.get().strip()
            entry.destroy() 
            
            if str(new_value) != str(real_current_value):
                # === ФИЗИЧЕСКОЕ ПЕРЕМЕЩЕНИЕ ПАПКИ ===
                if actual_col_name in ["challenge", "category", "ctf"]:
                    old_path = self._resolve_task_path(task.ctf, task.category, task.challenge)
                    
                    if old_path and os.path.exists(old_path):
                        def safe(s): 
                            v = re.sub(r'[\\/*?:"<>|]', "", str(s)).strip()
                            return v if v else "Unknown"
                        
                        # Определяем корень в зависимости от режима
                        if getattr(self, 'in_collection_view', False):
                            base_files_dir = self.current_csv_file.replace('.csv', '_files')
                        else:
                            script_dir = os.path.dirname(os.path.abspath(__file__))
                            base_files_dir = os.path.join(script_dir, "data", "files")
                        
                        n_ctf = safe(new_value) if actual_col_name == "ctf" else safe(task.ctf)
                        n_cat = safe(new_value) if actual_col_name == "category" else safe(task.category)
                        n_chal = safe(new_value) if actual_col_name == "challenge" else safe(task.challenge)
                        
                        new_path = os.path.join(base_files_dir, n_ctf, n_cat, n_chal)
                        
                        try:
                            os.makedirs(os.path.dirname(new_path), exist_ok=True)
                            os.rename(old_path, new_path)
                        except Exception as ex:
                            messagebox.showerror("Ошибка", f"Не удалось переименовать папку на диске.\nЗакройте файлы задачи и попробуйте снова.\n{ex}")
                            return 

                success = self.task_manager.update_task_field(task_key, actual_col_name, new_value)
                if success:
                    self.update_filter_comboboxes()
                    if getattr(self, 'in_collection_view', False):
                        if hasattr(self, 'current_folder_refresh_func'):
                            self.root.after(10, self.current_folder_refresh_func)
                    else:
                        self.root.after(10, lambda: [self.update_tasks_table(), self.update_filter_status()])
                else:
                    messagebox.showerror("Ошибка", "Не удалось сохранить CSV файл.")

        def cancel_edit(e=None):
            entry.destroy()

        entry.bind("<Return>", save_edit)
        entry.bind("<Escape>", cancel_edit)
        entry.bind("<FocusOut>", save_edit)
        
    def edit_file_safely(self, filename_raw, ctf, category, task_name):
        """Редактирование с бэкапом. Строгий приоритет для d.txt"""
        filename = filename_raw
        try:
            if filename.startswith("[") and filename.endswith("]"):
                parsed = ast.literal_eval(filename)
                if isinstance(parsed, list) and len(parsed) > 0: filename = parsed[0]
        except: pass 
        target_folder = self._resolve_task_path(ctf, category, task_name)
        found_path = None
        
        if target_folder:
            # Сценарий A: d.txt
            if filename == "d.txt":
                files = os.listdir(target_folder)
                
                # 1. Строго d.txt
                for f in files:
                    if f.lower() == "d.txt":
                        found_path = os.path.join(target_folder, f)
                        break
                
                # 2. Description...
                if not found_path:
                    for f in files:
                        if f.lower().startswith("description") and f.lower().endswith(".txt"):
                            found_path = os.path.join(target_folder, f)
                            break
                            
                # 3. Fallback 
                if not found_path:
                    for f in files:
                        low = f.lower()
                        if low.endswith(".txt") and "writeup" not in low and "cipher" not in low:
                            found_path = os.path.join(target_folder, f)
                            break

            elif os.path.exists(os.path.join(target_folder, filename)):
                 found_path = os.path.join(target_folder, filename)
            else:
                files = os.listdir(target_folder)
                target_lower = filename.lower()
                for f in files:
                    if f.lower().startswith(target_lower + "."):
                        found_path = os.path.join(target_folder, f)
                        break
                if not found_path:
                    def simplify(s): return re.sub(r'[\W_]+', '', s.lower())
                    target = simplify(filename)
                    for f in files:
                        if simplify(f).startswith(target):
                            found_path = os.path.join(target_folder, f)
                            break
                    
        if not found_path:
            messagebox.showerror("Ошибка", f"Файл '{filename}' не найден.")
            return

        # БЭКАП И ОТКРЫТИЕ 
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            backup_root = os.path.abspath(os.path.join(script_dir, "..", "backups"))
            safe_ctf = ctf if ctf else "Unknown_CTF"
            safe_cat = category if category else "Unknown_Category"
            safe_task = task_name if task_name else "Unknown_Task"
            specific_backup_dir = os.path.join(backup_root, safe_ctf, safe_cat, safe_task)
            os.makedirs(specific_backup_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            backup_filename = f"{os.path.basename(found_path)}_{timestamp}.bak"
            final_backup_path = os.path.join(specific_backup_dir, backup_filename)
            shutil.copy2(found_path, final_backup_path)
            print(f"Бэкап создан: {final_backup_path}")
        except Exception as e:
            if not messagebox.askyesno("Ошибка бэкапа", f"Не удалось создать бэкап:\n{e}\n\nПродолжить?"): return

        try:
            if platform.system() == 'Darwin': subprocess.call(('open', found_path))
            elif platform.system() == 'Windows': os.startfile(found_path)
            else: subprocess.call(('xdg-open', found_path))
        except Exception as e:
            messagebox.showerror("Ошибка открытия", f"Не удалось запустить редактор:\n{e}")
            
    def translate_file_inline(self, filename, ctf, category, task_name, on_success_callback=None):
        """Переводит текст, сохраняет бэкап и динамически обновляет интерфейс (через callback)."""
        target_folder = self._resolve_task_path(ctf, category, task_name)
        if not target_folder:
            messagebox.showerror("Ошибка", "Папка задачи не найдена.")
            return
            
        file_path = os.path.join(target_folder, filename)
        if not os.path.exists(file_path):
            messagebox.showerror("Ошибка", f"Файл {filename} не найден на диске.")
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось прочитать файл:\n{e}")
            return

        separator = "\n\n" + "="*40 + "\n--- АВТОМАТИЧЕСКИЙ ПЕРЕВОД (RU) ---\n" + "="*40 + "\n\n"
        if separator.strip() in content:
            messagebox.showinfo("Внимание", "Этот файл уже содержит перевод!")
            return

        # Бэкап
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            backup_root = os.path.abspath(os.path.join(script_dir, "..", "backups"))
            safe_ctf = ctf if ctf else "Unknown_CTF"
            safe_cat = category if category else "Unknown_Category"
            safe_task = task_name if task_name else "Unknown_Task"
            
            specific_backup_dir = os.path.join(backup_root, safe_ctf, safe_cat, safe_task)
            os.makedirs(specific_backup_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            backup_filename = f"{filename}_before_translate_{timestamp}.bak"
            
            shutil.copy2(file_path, os.path.join(specific_backup_dir, backup_filename))
        except Exception as e:
            if not messagebox.askyesno("Ошибка бэкапа", f"Не удалось создать бэкап:\n{e}\n\nПеревести без страховки?"):
                return

        # Перевод
        wait_window = tk.Toplevel(self.root)
        wait_window.title("Перевод...")
        wait_window.geometry("300x100")
        ttk.Label(wait_window, text="Выполняется перевод текста...\nПожалуйста, подождите.", justify=tk.CENTER).pack(expand=True)
        wait_window.update()

        try:
            translator = GoogleTranslator(source='auto', target='ru')
            max_chars = 4500
            translated_parts =[]
            
            text_parts = [content[i:i+max_chars] for i in range(0, len(content), max_chars)]
            for part in text_parts:
                translated_parts.append(translator.translate(part))
                
            translated_text = "".join(translated_parts)
            new_content = content + separator + translated_text
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
                
            wait_window.destroy()
            
            if on_success_callback:
                on_success_callback()
                
            messagebox.showinfo("Успех", "Перевод успешно добавлен в файл!")
            
        except ImportError:
            wait_window.destroy()
            messagebox.showerror("Ошибка", "Библиотека deep-translator не установлена.\nНапишите: pip install deep-translator")
        except Exception as e:
            wait_window.destroy()
            messagebox.showerror("Ошибка перевода", f"Убедитесь, что есть подключение к интернету.\nПодробности: {e}")
    
    def get_task_files_info(self, ctf, category, task_name):
        """Сканирует папку задачи. Приоритет: d.txt -> Description -> Любой txt"""
        result = {'zip': None, 'desc': None}
        target_folder = self._resolve_task_path(ctf, category, task_name)
        if not target_folder or not os.path.exists(target_folder): return result
        files = os.listdir(target_folder)
        # 1. ZIP
        archive_extensions = ('.zip', '.tar.gz', '.tgz', '.rar', '.7z', '.tar')
        for f in files:
            if f.lower().endswith(archive_extensions):
                result['zip'] = f
                break
        # 2. ОПИСАНИЕ 
        # А. Ищем строго d.txt
        for f in files:
            if f.lower() == "d.txt":
                result['desc'] = f
                break
        
        # Б. Ищем Description*.txt
        if not result['desc']:
            for f in files:
                if f.lower().startswith('description') and f.lower().endswith('.txt'):
                    result['desc'] = f
                    break
                    
        # В. Если совсем ничего нет - берем любой txt 
            
        return result
    
    def on_header_click(self, col):
        """Обработка клика по заголовку таблицы"""
        if self.sort_column == col:
            self.sort_descending = not self.sort_descending
        else:
            self.sort_column = col
            self.sort_descending = False
        self.update_header_arrows()
        self.update_tasks_table()

    def update_header_arrows(self):
        """Рисует стрелочки ▲/▼ в заголовках"""
        for col_id, display_name in self.headers_map.items():
            if col_id == self.sort_column:
                arrow = " ▼" if self.sort_descending else " ▲"
                self.tasks_tree.heading(col_id, text=display_name + arrow)
            else:
                self.tasks_tree.heading(col_id, text=display_name)
                
    def _resolve_task_path(self, ctf, category, task_name):
        """Строгий поиск папки задачи: Главная БД -> data/files, Коллекции -> _files"""
        
        # 1. ОПРЕДЕЛЯЕМ БАЗОВУЮ ПАПКУ В ЗАВИСИМОСТИ ОТ РЕЖИМА
        if getattr(self, 'in_collection_view', False) and hasattr(self, 'current_csv_file'):
            base_dir = self.current_csv_file.replace('.csv', '_files')
        else:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            path1 = os.path.join(script_dir, "data", "files")
            path2 = os.path.abspath(os.path.join(script_dir, "..", "data", "files"))
            base_dir = path1 if os.path.exists(path1) else path2 if os.path.exists(path2) else path1
            
        if not os.path.exists(base_dir): 
            return None

        # Вспомогательная функция поиска без учета регистра
        def find_dir(parent_path, target_name):
            if not target_name or not os.path.exists(parent_path): return None
            target_clean = str(target_name).strip().lower()
            exact_path = os.path.join(parent_path, str(target_name).strip())
            if os.path.exists(exact_path) and os.path.isdir(exact_path): return exact_path
            try:
                for item in os.listdir(parent_path):
                    item_path = os.path.join(parent_path, item)
                    if os.path.isdir(item_path) and item.strip().lower() == target_clean: return item_path
            except: pass
            return None

        # 2. ИДЕМ СТРОГО ПО ЦЕПОЧКЕ
        ctf_dir = find_dir(base_dir, ctf)
        if not ctf_dir: return None

        cat_dir = None
        if category:
            first_cat = str(category).split(',')[0].strip()
            cat_dir = find_dir(ctf_dir, first_cat)

        search_parent = cat_dir if cat_dir else ctf_dir
        task_dir = find_dir(search_parent, task_name)
        
        if not task_dir:
            try:
                for item in os.listdir(ctf_dir):
                    sub = os.path.join(ctf_dir, item)
                    if os.path.isdir(sub):
                        task_dir = find_dir(sub, task_name)
                        if task_dir: break
            except: pass
            
        return task_dir
    
    def show_floating_navigator(self, current_file_path, ctf, category, task_name):
        """Создает плавающую панель навигации."""
        if hasattr(self, 'nav_window') and self.nav_window.winfo_exists():
            self.nav_window.destroy()

        target_folder = self._resolve_task_path(ctf, category, task_name)
        if not target_folder: return
        playlist = getattr(self, 'task_playlists', {}).get(task_name, [])
        if not playlist:
            return

        all_files =[]
        for fname in playlist:
            if not fname: continue
            
            found_path = None
            if fname == "d.txt":
                files = os.listdir(target_folder)
                for f in files:
                    if f.lower() == "d.txt": found_path = os.path.join(target_folder, f); break
                if not found_path:
                    for f in files:
                        if f.lower().startswith("description") and f.lower().endswith(".txt"): found_path = os.path.join(target_folder, f); break
                if not found_path:
                    for f in files:
                        low = f.lower()
                        if low.endswith(".txt") and "writeup" not in low and "cipher" not in low: found_path = os.path.join(target_folder, f); break
            
            elif os.path.exists(os.path.join(target_folder, fname)):
                found_path = os.path.join(target_folder, fname)
                
            else:
                files = os.listdir(target_folder)
                target_lower = fname.lower()
                for f in files:
                    if f.lower().startswith(target_lower + "."): found_path = os.path.join(target_folder, f); break
                if not found_path:
                    def simplify(s): return re.sub(r'[\W_]+', '', s.lower())
                    target_simple = simplify(fname)
                    for f in files:
                        if simplify(f).startswith(target_simple): found_path = os.path.join(target_folder, f); break
            
            if found_path and found_path not in all_files:
                all_files.append(found_path)

        if len(all_files) <= 1:
            return

        try:
            current_idx =[all_files.index(current_file_path)]
        except ValueError:
            current_idx =[0]

        self.nav_window = tk.Toplevel(self.root)
        self.nav_window.title("Навигатор")
        self.nav_window.geometry("350x90")
        self.nav_window.attributes('-topmost', True) 
        self.nav_window.resizable(False, False)

        screen_width = self.nav_window.winfo_screenwidth()
        x_center = int((screen_width - 350) / 2)
        self.nav_window.geometry(f"+{x_center}+50")

        lbl_info = ttk.Label(self.nav_window, text="Файлы задачи:", font=("Arial", 9), foreground="gray")
        lbl_info.pack(pady=(5, 0))

        lbl_file = ttk.Label(self.nav_window, text="", font=("Arial", 10, "bold"), anchor="center")
        lbl_file.pack(fill=tk.X, pady=2)

        btn_frame = ttk.Frame(self.nav_window)
        btn_frame.pack(fill=tk.X, padx=10, pady=5)

        def open_file_by_idx(idx):
            filepath = all_files[idx]
            filename = os.path.basename(filepath)
            lbl_file.config(text=f"{idx + 1}/{len(all_files)}: {filename}")
            
            opened_existing = False
            if platform.system() == 'Windows':
                try:
                    user32 = ctypes.windll.user32
                    found_hwnd = None
                    def enum_window_callback(hwnd, lParam):
                        nonlocal found_hwnd
                        if user32.IsWindowVisible(hwnd):
                            length = user32.GetWindowTextLengthW(hwnd)
                            if length > 0:
                                buff = ctypes.create_unicode_buffer(length + 1)
                                user32.GetWindowTextW(hwnd, buff, length + 1)
                                title = buff.value.lower()
                                if filename.lower() in title and "задачник" not in title and "навигатор" not in title and "задача:" not in title:
                                    found_hwnd = hwnd
                                    return False
                        return True
                    
                    EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
                    cb = EnumWindowsProc(enum_window_callback)
                    user32.EnumWindows(cb, 0)
                    
                    if found_hwnd:
                        user32.ShowWindow(found_hwnd, 9)
                        user32.SetForegroundWindow(found_hwnd)
                        opened_existing = True
                except: pass

            if not opened_existing:
                try:
                    if platform.system() == 'Darwin': subprocess.call(('open', filepath))
                    elif platform.system() == 'Windows': os.startfile(filepath)
                    else: subprocess.call(('xdg-open', filepath))
                except Exception as e:
                    print(f"Ошибка: {e}")

        def go_prev():
            current_idx[0] = (current_idx[0] - 1) % len(all_files)
            open_file_by_idx(current_idx[0])

        def go_next():
            current_idx[0] = (current_idx[0] + 1) % len(all_files)
            open_file_by_idx(current_idx[0])

        ttk.Button(btn_frame, text="◄ Назад", command=go_prev).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        ttk.Button(btn_frame, text="Далее ►", command=go_next).pack(side=tk.RIGHT, expand=True, fill=tk.X, padx=2)

        lbl_file.config(text=f"{current_idx[0] + 1}/{len(all_files)}: {os.path.basename(current_file_path)}")

        def on_nav_close():
            if platform.system() == 'Windows':
                try:
                    user32 = ctypes.windll.user32
                    WM_CLOSE = 0x0010
                    filenames_to_close =[os.path.basename(f).lower() for f in all_files]
                    
                    def enum_window_callback(hwnd, lParam):
                        if user32.IsWindowVisible(hwnd):
                            length = user32.GetWindowTextLengthW(hwnd)
                            if length > 0:
                                buff = ctypes.create_unicode_buffer(length + 1)
                                user32.GetWindowTextW(hwnd, buff, length + 1)
                                title = buff.value.lower()
                                for fname in filenames_to_close:
                                    if fname in title and "задачник" not in title and "навигатор" not in title and "задача:" not in title:
                                        user32.PostMessageW(hwnd, WM_CLOSE, 0, 0)
                                        break
                        return True
                    EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
                    cb = EnumWindowsProc(enum_window_callback)
                    user32.EnumWindows(cb, 0)
                except Exception as e: print(e)
            self.nav_window.destroy()

        self.nav_window.protocol("WM_DELETE_WINDOW", on_nav_close)
        
    def get_collection_csv_path(self, section, folder_name):
        """Возвращает путь к CSV."""
        safe_sec = re.sub(r'[\\/*?:"<>|]', "", section).strip()
        safe_fld = re.sub(r'[\\/*?:"<>|]', "", folder_name).strip()
        sec_dir = os.path.join(self.collections_dir, safe_sec)
        os.makedirs(sec_dir, exist_ok=True)
        return os.path.join(sec_dir, f"{safe_fld}.csv")

    def load_collections(self):
        """Загрузка структуры коллекций"""
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.collections_dir = os.path.join(script_dir, "data", "collections")
        os.makedirs(self.collections_dir, exist_ok=True)
        self.collections_file = os.path.join(self.collections_dir, "structure.json")
        self.collections = {} 
        try:
            if os.path.exists(self.collections_file):
                with open(self.collections_file, 'r', encoding='utf-8') as f:
                    self.collections.update(json.load(f))
        except: pass
        if not self.collections:
            self.collections = {"Мои задачи": []}

    def save_collections(self):
        with open(self.collections_file, 'w', encoding='utf-8') as f:
            json.dump(self.collections, f, ensure_ascii=False, indent=4)
    
    def create_collections_interface(self):
        """Отрисовка интерфейса 'Мои коллекции' """
        for i in range(20):
            self.main_frame.rowconfigure(i, weight=0)
            self.main_frame.columnconfigure(i, weight=0)
        top_frame = ttk.Frame(self.main_frame)
        top_frame.grid(row=0, column=0, pady=10, sticky=(tk.W, tk.E))
        top_frame.columnconfigure(1, weight=1)
        
        ttk.Label(top_frame, text="⭐ Мои коллекции", font=("Arial", 20, "bold")).grid(row=0, column=0, sticky=tk.W)
        ttk.Button(top_frame, text="➕ Новый раздел", command=self.add_collection_section).grid(row=0, column=1, padx=20, sticky=tk.W)
        ttk.Button(top_frame, text="← На главную", command=self.return_to_main_menu).grid(row=0, column=2, sticky=tk.E)

        is_dark = self.settings_manager.get_setting("theme", "Светлая") == "Темная"
        bg_color = "#1c1c1c" if is_dark else "#fafafa" 
        fg_color = "#58a6ff" if is_dark else "#2c3e50" 
        btn_bg = "#2b2b2b" if is_dark else "#ffffff"   
        btn_fg = "#ffffff" if is_dark else "#000000"

        canvas = tk.Canvas(self.main_frame, highlightthickness=0, bg=bg_color)
        scrollbar = ttk.Scrollbar(self.main_frame, orient=tk.VERTICAL, command=canvas.yview)
        content_frame = tk.Frame(canvas, bg=bg_color)

        canvas_window = canvas.create_window((0, 0), window=content_frame, anchor="nw")
        
        def configure_canvas(event):
            canvas.itemconfig(canvas_window, width=event.width)
            
        def update_scrollregion(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
            
        canvas.bind("<Configure>", configure_canvas)
        content_frame.bind("<Configure>", update_scrollregion)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=1, column=1, sticky=(tk.N, tk.S))
        self.main_frame.rowconfigure(1, weight=1)
        self.main_frame.columnconfigure(0, weight=1)

        canvas.yview_moveto(0)

        def _on_mousewheel(event):
            content_height = content_frame.winfo_reqheight()
            canvas_height = canvas.winfo_height()
            if content_height <= canvas_height: return
                
            if platform.system() == 'Windows': canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            elif platform.system() == 'Darwin': canvas.yview_scroll(int(-1 * event.delta), "units")
            else:
                if event.num == 4: canvas.yview_scroll(-1, "units")
                elif event.num == 5: canvas.yview_scroll(1, "units")

        if platform.system() == 'Linux':
            self.root.bind_all("<Button-4>", _on_mousewheel)
            self.root.bind_all("<Button-5>", _on_mousewheel)
        else:
            self.root.bind_all("<MouseWheel>", _on_mousewheel)

        def build_folder_widget(parent, sec, fname, task_count):
            f_frame = tk.Frame(parent, bg=btn_bg, relief=tk.RIDGE, bd=2, cursor="hand2")
            f_frame.pack(side=tk.LEFT, padx=(0, 20), pady=10) # Увеличены отступы
            
            def on_open(e): self.open_collection_folder(sec, fname)
            
            lbl_name = tk.Label(f_frame, text=f"📁 {fname}", font=("Arial", 14, "bold"), bg=btn_bg, fg=btn_fg)
            lbl_name.pack(pady=(15, 5), padx=25)
            
            lbl_count = tk.Label(f_frame, text=f"({task_count} задач)", font=("Arial", 11), bg=btn_bg, fg=btn_fg)
            lbl_count.pack(pady=0, padx=25)
            
            actions_frame = tk.Frame(f_frame, bg=btn_bg)
            actions_frame.pack(pady=(10, 10))
            
            edit_lbl = tk.Label(actions_frame, text="✏️ Ред.", font=("Arial", 11, "bold"), bg=btn_bg, fg="#a0a0a0")
            edit_lbl.pack(side=tk.LEFT, padx=8)
            del_lbl = tk.Label(actions_frame, text="❌ Удал.", font=("Arial", 11, "bold"), bg=btn_bg, fg="#ff4444")
            del_lbl.pack(side=tk.LEFT, padx=8)
            
            f_frame.bind("<Button-1>", on_open)
            lbl_name.bind("<Button-1>", on_open)
            lbl_count.bind("<Button-1>", on_open)
            
            del_lbl.bind("<Button-1>", lambda e: self.delete_collection_folder(sec, fname))
            edit_lbl.bind("<Button-1>", lambda e: self.rename_collection_folder(sec, fname))

        row_idx = 0
        for section, folders in self.collections.items():
            sec_header = tk.Frame(content_frame, bg=bg_color)
            sec_header.grid(row=row_idx, column=0, pady=(25, 10), sticky=tk.W)
            tk.Label(sec_header, text=section, font=("Arial", 18, "bold"), bg=bg_color, fg=fg_color).pack(side=tk.LEFT)
            sec_actions = tk.Frame(sec_header, bg=bg_color)
            sec_actions.pack(side=tk.LEFT, padx=15)
            edit_sec = tk.Label(sec_actions, text="✏️ переименовать", font=("Arial", 11, "bold"), bg=bg_color, fg="#a0a0a0", cursor="hand2")
            edit_sec.pack(side=tk.LEFT, padx=8)
            edit_sec.bind("<Button-1>", lambda e, s=section: self.rename_collection_section(s))
            del_sec = tk.Label(sec_actions, text="❌ удалить", font=("Arial", 11, "bold"), bg=bg_color, fg="#ff4444", cursor="hand2")
            del_sec.pack(side=tk.LEFT, padx=8)
            del_sec.bind("<Button-1>", lambda e, s=section: self.delete_collection_section(s))
            ttk.Separator(content_frame, orient='horizontal').grid(row=row_idx+1, column=0, sticky=(tk.W, tk.E), pady=(0, 15))

            folders_frame = tk.Frame(content_frame, bg=bg_color)
            folders_frame.grid(row=row_idx+2, column=0, sticky=tk.W, padx=10)
            
            for folder_name in folders:
                csv_path = self.get_collection_csv_path(section, folder_name)
                task_count = 0
                if os.path.exists(csv_path):
                    try:
                        with open(csv_path, 'r', encoding='utf-8') as f:
                            task_count = sum(1 for line in f) - 1 
                    except: pass
                if task_count < 0: task_count = 0
                
                build_folder_widget(folders_frame, section, folder_name, task_count)

            add_fld_btn = tk.Button(
                folders_frame, text="➕\nНовая папка", font=("Arial", 12, "bold"), 
                width=12, height=4, bg=btn_bg, fg=btn_fg, relief=tk.SOLID, bd=1, cursor="hand2",
                command=lambda s=section: self.add_collection_folder(s)
            )
            add_fld_btn.pack(side=tk.LEFT, padx=(0, 20), pady=10)
            
            row_idx += 3

    # === ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ДЛЯ КОЛЛЕКЦИЙ ===
    def add_collection_section(self):
        sec_name = self.ask_string_ru("Новый раздел", "Введите название нового раздела (например, 'Решенное'):")
        if sec_name:
            sec_name = sec_name.strip()
            if sec_name in self.collections:
                messagebox.showwarning("Внимание", "Раздел с таким именем уже существует!")
                return
            self.collections[sec_name] = []
            self.save_collections()
            self.show_option2()

    def rename_collection_section(self, old_name):
        """Переименование раздела (и физической папки на диске)"""
        new_name = self.ask_string_ru("Переименование", f"Новое имя для раздела '{old_name}':")
        if new_name:
            new_name = new_name.strip()
            if not new_name or new_name == old_name: return
            if new_name in self.collections:
                messagebox.showwarning("Внимание", "Раздел с таким именем уже существует!")
                return
            safe_old = re.sub(r'[\\/*?:"<>|]', "", old_name).strip()
            safe_new = re.sub(r'[\\/*?:"<>|]', "", new_name).strip()
            old_dir = os.path.join(self.collections_dir, safe_old)
            new_dir = os.path.join(self.collections_dir, safe_new)
            
            if os.path.exists(old_dir):
                try:
                    os.rename(old_dir, new_dir)
                except Exception as e:
                    messagebox.showerror("Ошибка", f"Не удалось переименовать папку на диске:\n{e}")
                    return
            new_collections = {}
            for key, val in self.collections.items():
                if key == old_name:
                    new_collections[new_name] = val
                else:
                    new_collections[key] = val
            self.collections = new_collections
            self.save_collections()
            self.show_option2()

    def delete_collection_section(self, section):
        """Удаление раздела и физической папки со всеми файлами"""
        if messagebox.askyesno("Удаление", f"Удалить раздел '{section}' и ВСЕ его папки?"):
            safe_sec = re.sub(r'[\\/*?:"<>|]', "", section).strip()
            sec_dir = os.path.join(self.collections_dir, safe_sec)
            if os.path.exists(sec_dir):
                try:
                    shutil.rmtree(sec_dir) 
                except Exception as e:
                    print(f"Ошибка при удалении директории: {e}")  
            del self.collections[section]
            self.save_collections()
            self.show_option2()

    def add_collection_folder(self, section):
        folder_name = self.ask_string_ru("Новая папка", f"Название новой папки в разделе '{section}':")
        if folder_name:
            folder_name = folder_name.strip()
            if folder_name in self.collections[section]:
                messagebox.showwarning("Внимание", "Папка с таким именем уже есть!")
                return
            
            self.collections[section].append(folder_name)
            self.save_collections()
            
            csv_path = self.get_collection_csv_path(section, folder_name)
            headers = ["key", "ctf", "nctf", "data", "category", "ncat0", "ncat1", "challenge", "description", "nc", "wsite", "writeup", "attachment", "level", "tag1", "tag2", "tag3", "tag4", "tag5"]
            with open(csv_path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=headers, quoting=csv.QUOTE_ALL)
                writer.writeheader()
            
            self.show_option2()

    def rename_collection_folder(self, section, old_name):
        new_name = self.ask_string_ru("Переименование", f"Новое имя для папки '{old_name}':")
        if new_name:
            new_name = new_name.strip()
            if not new_name or new_name == old_name: return
            if new_name in self.collections[section]:
                messagebox.showwarning("Внимание", "Папка с таким именем уже есть!")
                return
            
            old_csv = self.get_collection_csv_path(section, old_name)
            new_csv = self.get_collection_csv_path(section, new_name)
            
            if os.path.exists(old_csv):
                try:
                    os.replace(old_csv, new_csv)
                except Exception as e:
                    messagebox.showerror("Ошибка", f"Не удалось переименовать файл на диске:\n{e}")
                    return 
                    
            if old_name in self.collections[section]:
                idx = self.collections[section].index(old_name)
                self.collections[section][idx] = new_name
                self.save_collections()
                
            self.show_option2()

    def delete_collection_folder(self, section, folder_name):
        if messagebox.askyesno("Удаление", f"Удалить папку '{folder_name}' и её задачи?"):
            
            # Безопасное удаление из списка 
            if folder_name in self.collections[section]:
                self.collections[section].remove(folder_name)
                self.save_collections()
            
            # Пытаемся удалить файл, игнорируя ошибки (если файла уже нет)
            csv_path = self.get_collection_csv_path(section, folder_name)
            if os.path.exists(csv_path):
                try:
                    os.remove(csv_path)
                except:
                    pass
                
            self.show_option2()
    
    def remove_selected_from_folder(self, section, folder_name):
        """Удаляет выделенные задачи из CSV и удаляет их клонированные файлы из _files"""
        if not self.selected_tasks:
            messagebox.showinfo("Инфо", "Сначала выделите задачи галочками (☑).")
            return
            
        if messagebox.askyesno("Подтверждение", f"Удалить {len(self.selected_tasks)} задач из папки '{folder_name}'?"):
            
            # 1. Удаляем физические папки клонированных задач
            for task_id in list(self.selected_tasks):
                task = next((t for t in self.task_manager.tasks if str(t.key) == str(task_id)), None)
                if task:
                    # Ищем папку конкретной задачи внутри коллекции (_files)
                    task_path = self._resolve_task_path(task.ctf, task.category, task.challenge)
                    if task_path and os.path.exists(task_path):
                        try:
                            shutil.rmtree(task_path, ignore_errors=True)
                        except Exception as e:
                            print(f"Ошибка удаления папки задачи: {e}")
                            
            # 2. Очищаем CSV
            self.task_manager.tasks = [t for t in self.task_manager.tasks if str(t.key) not in self.selected_tasks]
            self.task_manager.save_tasks_to_csv()
            
            messagebox.showinfo("Успех", "Задачи удалены из папки.")
            self.selected_tasks.clear()
            self.open_collection_folder(section, folder_name) # Перерисовываем
    
    def open_collection_folder(self, section, folder_name):
        """Открывает таблицу с задачами из выбранной папки (с поиском и чекбоксами)"""
        self.clear_content()
        self.selected_tasks.clear() 
        if not hasattr(self, 'headers_map'):
            self.headers_map = {
                "chk": "☐", "key": "ID", "challenge": "Задача", "category": "Категория",
                "level": "Уровень", "description": "Описание", "ctf": "CTF",
                "writeup": "Writeup", "wsite": "Сайт", "attachment": "Вложение",
                "tag1": "Тег 1", "tag2": "Тег 2", "tag3": "Тег 3", "tag4": "Тег 4", "tag5": "Тег 5"
            }
        self.headers_map["chk"] = "☐" 
        
        # === Подменяем базу данных ===
        if not hasattr(self, 'main_task_manager'):
            self.main_task_manager = self.task_manager 
            
        csv_path = self.get_collection_csv_path(section, folder_name)
        if not os.path.exists(csv_path):
            headers = ["key", "ctf", "nctf", "data", "category", "ncat0", "ncat1", "challenge", "description", "nc", "wsite", "writeup", "attachment", "level", "tag1", "tag2", "tag3", "tag4", "tag5"]
            with open(csv_path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=headers, quoting=csv.QUOTE_ALL)
                writer.writeheader()
                
        self.task_manager = TaskManager(csv_path) 
        self.current_csv_file = csv_path
        self.in_collection_view = True
        self.folder_id_map = {}
        
        all_folder_tasks = self.task_manager.tasks
        
        # 1. ЗАГОЛОВОК
        top_frame = ttk.Frame(self.main_frame)
        top_frame.grid(row=0, column=0, pady=10, sticky=(tk.W, tk.E))
        top_frame.columnconfigure(0, weight=1)
        ttk.Label(top_frame, text=f"📂 {section} ➔ {folder_name}", font=("Arial", 16, "bold")).grid(row=0, column=0, sticky=tk.W)
        ttk.Button(top_frame, text="← Назад к папкам", command=self.show_option2).grid(row=0, column=1, sticky=tk.E)

        # === ПАНЕЛЬ ПОИСКА ===
        search_frame = ttk.Frame(self.main_frame)
        search_frame.grid(row=1, column=0, pady=(0, 10), sticky=(tk.W, tk.E))
        ttk.Label(search_frame, text="Поиск по папке:").pack(side=tk.LEFT, padx=5)
        
        folder_search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=folder_search_var, width=40, font=("Arial", 11))
        search_entry.pack(side=tk.LEFT, padx=5)

        # 2. ПАНЕЛЬ МАССОВЫХ ДЕЙСТВИЙ
        bulk_frame = ttk.Frame(self.main_frame)
        bulk_frame.grid(row=2, column=0, pady=(0, 10), sticky=(tk.W, tk.E))
        
        is_dark = self.settings_manager.get_setting("theme") == "Темная"
        accent_color = "#58a6ff" if is_dark else "blue"
        
        status_lbl = ttk.Label(bulk_frame, text="", foreground=accent_color)
        status_lbl.pack(side=tk.LEFT)

        ttk.Button(bulk_frame, text="❌ Удалить из папки", command=lambda: self.remove_selected_from_folder(section, folder_name)).pack(side=tk.RIGHT, padx=5)
        ttk.Button(bulk_frame, text="Сбросить всё", command=self.deselect_all_tasks).pack(side=tk.RIGHT, padx=5)
        ttk.Button(bulk_frame, text="☑ Выбрать всё", command=self.toggle_select_all).pack(side=tk.RIGHT, padx=5)
        
        # 3. ТАБЛИЦА
        table_frame = ttk.Frame(self.main_frame)
        table_frame.grid(row=3, column=0, pady=5, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.main_frame.rowconfigure(3, weight=1)
        
        columns = ("chk", "key", "challenge", "category", "level", "description", "ctf", 
                  "writeup", "wsite", "attachment", "tag1", "tag2", "tag3", "tag4", "tag5")
        self.tasks_tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=20)
        
        sortable_cols = ["key", "challenge", "category", "level", "ctf", "writeup", "wsite", "attachment", "tag1", "tag2", "tag3", "tag4", "tag5"]
        self.sort_descending = False
        self.sort_column = "key"

        def folder_header_click(col, force_update=False):
            if not force_update:
                if self.sort_column == col:
                    self.sort_descending = not self.sort_descending
                else:
                    self.sort_column = col
                    self.sort_descending = False
            populate_folder_table()

        for col_id in columns:
            display_name = self.headers_map.get(col_id, col_id)
            if col_id == "chk":
                self.tasks_tree.heading(col_id, text=display_name, command=self.toggle_select_all)
            elif col_id in sortable_cols:
                self.tasks_tree.heading(col_id, text=display_name, command=lambda c=col_id: folder_header_click(c))
            else:
                self.tasks_tree.heading(col_id, text=display_name)

        self.tasks_tree.column("chk", width=40, minwidth=40, stretch=False, anchor="center")
        self.tasks_tree.column("key", width=50, minwidth=50, stretch=False)
        self.tasks_tree.column("challenge", width=150)
        self.tasks_tree.column("category", width=100)
        self.tasks_tree.column("level", width=70)
        self.tasks_tree.column("description", width=80)
        self.tasks_tree.column("ctf", width=120)
        self.tasks_tree.column("writeup", width=80, anchor="center")
        self.tasks_tree.column("wsite", width=80, anchor="center")
        self.tasks_tree.column("attachment", width=80, anchor="center")
        self.tasks_tree.column("tag1", width=80)
        self.tasks_tree.column("tag2", width=80)
        self.tasks_tree.column("tag3", width=80)
        self.tasks_tree.column("tag4", width=80)
        self.tasks_tree.column("tag5", width=80)

        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tasks_tree.yview)
        self.tasks_tree.configure(yscrollcommand=scrollbar.set)
        self.tasks_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)

        self.apply_treeview_colors()
        self.tasks_tree.bind("<ButtonRelease-1>", self.toggle_checkbox)
        self.tasks_tree.bind("<Double-1>", self.show_task_details)
        self.tasks_tree.bind("<Double-Button-3>", self.edit_cell_on_right_click)

        #4. ЛОГИКА ФИЛЬТРАЦИИ И ЗАПОЛНЕНИЯ (С ЗАЩИТОЙ ОТ КРАШЕЙ) 
        def populate_folder_table(event=None):
            if not hasattr(self, 'tasks_tree') or not self.tasks_tree.winfo_exists():
                return
                
            for item in self.tasks_tree.get_children():
                self.tasks_tree.delete(item)
                
            query = folder_search_var.get().lower().strip()
            
            display_tasks = []
            for t in self.task_manager.tasks:
                if not query:
                    display_tasks.append(t)
                else:
                    if t.challenge and query in str(t.challenge).lower():
                        display_tasks.append(t)
            
            if self.sort_column:
                def sort_key(task):
                    val = getattr(task, self.sort_column, "")
                    if self.sort_column == "key":
                        try: return int(val)
                        except: return 0
                    if self.sort_column == "level":
                        v = str(val).lower().strip()
                        if v in ["easy", "легкий"]: return 1
                        if v in ["medium", "средний"]: return 2
                        if v in ["hard", "сложный"]: return 3
                        if v == "insane": return 4
                        return 5
                    if self.sort_column in ["writeup", "wsite", "attachment"]:
                        has_data = bool(val and val != "[]" and val != "None" and str(val).strip())
                        return 1 if has_data else 0
                    return str(val).lower() if val else ""
                
                display_tasks.sort(key=sort_key, reverse=self.sort_descending)
                
                for c_id in columns:
                    disp = self.headers_map.get(c_id, c_id)
                    if c_id == self.sort_column:
                        arrow = " ▼" if self.sort_descending else " ▲"
                        self.tasks_tree.heading(c_id, text=disp + arrow)
                    else:
                        self.tasks_tree.heading(c_id, text=disp)

            status_text = f"📊 Всего в папке: {len(all_folder_tasks)}"
            if query: status_text += f" | 🔍 Поиск: '{query}' (Найдено: {len(display_tasks)})"
            
            if status_lbl.winfo_exists():
                status_lbl.config(text=status_text)

            self.folder_id_map.clear()
            local_id_counter = 1
            
            for i, task in enumerate(display_tasks):
                has_wr = "✅" if task.writeup and task.writeup != "[]" and task.writeup != "None" else "❌"
                has_site = "✅" if task.wsite and task.wsite != "[]" and task.wsite != "None" and task.wsite != "" else "❌"
                has_att = "✅" if task.attachment and task.attachment != "[]" and task.attachment != "None" else "❌"
                
                row_tag = 'evenrow' if i % 2 == 0 else 'oddrow'
                chk_val = "☑" if str(task.key) in self.selected_tasks else "☐"
                
                local_id = str(local_id_counter)
                self.folder_id_map[local_id] = str(task.key)
                
                self.tasks_tree.insert("", tk.END, values=(
                    chk_val, local_id, task.challenge, task.category, task.level if task.level else "Не указан",
                    task.description[:50] + "..." if len(task.description) > 50 else task.description,
                    task.ctf, has_wr, has_site, has_att,
                    task.tag1, task.tag2, task.tag3, task.tag4, task.tag5
                ), tags=(row_tag,))
                local_id_counter += 1

        self.current_folder_refresh_func = populate_folder_table
        search_entry.bind('<Return>', populate_folder_table)
        ttk.Button(search_frame, text="🔍 Найти", command=populate_folder_table).pack(side=tk.LEFT, padx=5)

        populate_folder_table()
            
    def open_add_to_collection_dialog(self, task_ids):
        """Единое диалоговое окно для добавления задач"""
        if not task_ids:
            messagebox.showinfo("Инфо", "Нет задач для добавления.")
            return
            
        choose_win = tk.Toplevel(self.root)
        choose_win.title("Добавить в коллекцию")
        choose_win.geometry("380x350") 
        choose_win.transient(self.root)
        choose_win.grab_set()
        
        ttk.Label(choose_win, text=f"Добавление задач: {len(task_ids)} шт.", font=("Arial", 11, "bold")).pack(pady=(10, 0))
        ttk.Label(choose_win, text="Кликните по папке для выбора.\nЗажмите Ctrl и кликайте, чтобы выбрать несколько.", wraplength=350, justify=tk.CENTER).pack(pady=5)
        
        frame = ttk.Frame(choose_win)
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)
        
        scrollbar = ttk.Scrollbar(frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        listbox = tk.Listbox(frame, selectmode=tk.EXTENDED, yscrollcommand=scrollbar.set, font=("Arial", 10))
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=listbox.yview)
        
        folder_options = []
        for sec, folders_list in getattr(self, 'collections', {}).items():
            for f_name in folders_list:
                folder_options.append(f"{sec} -> {f_name}")
                
        if not folder_options:
            listbox.insert(tk.END, "Нет созданных папок!")
            listbox.config(state=tk.DISABLED)
            ttk.Button(choose_win, text="ОК", command=choose_win.destroy).pack(pady=10)
            return
            
        for opt in folder_options:
            listbox.insert(tk.END, opt)
            
        def save_choice():
            selected_indices = listbox.curselection()
            if not selected_indices:
                messagebox.showinfo("Инфо", "Выберите хотя бы одну папку!")
                return
                
            source_manager = getattr(self, 'main_task_manager', self.task_manager)
            tasks_to_add = [t for t in source_manager.tasks if str(t.key) in task_ids]
            
            added_count = 0
            duplicate_count = 0
            
            def safe(s): 
                v = re.sub(r'[\\/*?:"<>|]', "", str(s)).strip()
                return v if v else "Unknown"

            for i in selected_indices:
                selection = listbox.get(i)
                sec, f_name = selection.split(" -> ")
                
                # Пути к CSV и к папке с клонированными файлами
                col_csv_path = self.get_collection_csv_path(sec, f_name)
                col_files_dir = col_csv_path.replace('.csv', '_files')
                
                if not os.path.exists(col_csv_path):
                    headers = ["key", "ctf", "nctf", "data", "category", "ncat0", "ncat1", "challenge", "description", "nc", "wsite", "writeup", "attachment", "level", "tag1", "tag2", "tag3", "tag4", "tag5"]
                    with open(col_csv_path, 'w', encoding='utf-8', newline='') as f:
                        writer = csv.DictWriter(f, fieldnames=headers, quoting=csv.QUOTE_ALL)
                        writer.writeheader()

                col_manager = TaskManager(col_csv_path)
                
                # Проверка дубликатов по названию и турниру
                existing_signatures = [f"{t.ctf}_{t.challenge}".lower().strip() for t in col_manager.tasks]
                
                # Генерируем уникальные ID для коллекции (1, 2, 3...)
                existing_keys = [int(t.key) for t in col_manager.tasks if str(t.key).isdigit()]
                next_key = max(existing_keys) + 1 if existing_keys else 1

                for task in tasks_to_add:
                    sig = f"{task.ctf}_{task.challenge}".lower().strip()
                    if sig not in existing_signatures:
                        self.in_collection_view = False
                        orig_path = self._resolve_task_path(task.ctf, task.category, task.challenge)
                        self.in_collection_view = True
                        
                        if orig_path and os.path.exists(orig_path):
                            new_path = os.path.join(col_files_dir, safe(task.ctf), safe(task.category), safe(task.challenge))
                            if not os.path.exists(new_path):
                                os.makedirs(os.path.dirname(new_path), exist_ok=True)
                                shutil.copytree(orig_path, new_path)
                        
                        new_task = copy.deepcopy(task)
                        new_task.key = str(next_key)
                        next_key += 1
                        
                        col_manager.tasks.append(new_task)
                        added_count += 1
                    else:
                        duplicate_count += 1
                
                col_manager.csv_file_path = col_csv_path
                col_manager.save_tasks_to_csv()
            
            msg = ""
            if added_count > 0: msg += f"Успешно скопировано задач (и их файлов): {added_count}.\n"
            if duplicate_count > 0: msg += f"Пропущено дубликатов: {duplicate_count}."
            if msg: messagebox.showinfo("Результат", msg)
            
            if hasattr(self, 'deselect_all_tasks'): self.deselect_all_tasks()
            choose_win.destroy()
            
        btn_frame = ttk.Frame(choose_win)
        btn_frame.pack(fill=tk.X, pady=10)
        ttk.Button(btn_frame, text="✅ Добавить в выбранные папки", command=save_choice).pack()
        
    def _get_real_task_id(self, raw_id):
        """Переводит локальный ID папки (1,2,3) обратно в реальный ID задачи для базы"""
        if getattr(self, 'in_collection_view', False):
            return self.folder_id_map.get(str(raw_id), str(raw_id))
        return str(raw_id)
    
    def ask_string_ru(self, title, prompt):
        """Собственное диалоговое окно ввода с русскими кнопками"""
        dlg = tk.Toplevel(self.root)
        dlg.title(title)
        dlg.geometry("350x150")
        dlg.transient(self.root)
        dlg.grab_set()

        # Центрируем по экрану
        dlg.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - dlg.winfo_width()) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - dlg.winfo_height()) // 2
        dlg.geometry(f"+{x}+{y}")

        ttk.Label(dlg, text=prompt, wraplength=300, justify=tk.CENTER).pack(pady=10)
        entry = ttk.Entry(dlg, width=40, font=("Arial", 10))
        entry.pack(pady=5)
        entry.focus_set()

        result = [None] 

        def on_ok(e=None):
            result[0] = entry.get()
            dlg.destroy()

        def on_cancel(e=None):
            dlg.destroy()

        btn_frame = ttk.Frame(dlg)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="ОК", command=on_ok).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="Отмена", command=on_cancel).pack(side=tk.LEFT, padx=10)

        dlg.bind("<Return>", on_ok)
        dlg.bind("<Escape>", on_cancel)

        self.root.wait_window(dlg) 
        return result[0]
    
    def apply_app_theme(self, theme_setting):
        """Применяет тему, умеет автоматически считывать тему Windows"""
        if theme_setting == "Темная":
            sv_ttk.set_theme("dark")
        elif theme_setting == "Светлая":
            sv_ttk.set_theme("light")
        elif theme_setting == "Системная":
            if platform.system() == "Windows":
                try:
                    registry_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
                    value, _ = winreg.QueryValueEx(registry_key, "AppsUseLightTheme")
                    if value == 0:
                        sv_ttk.set_theme("dark")
                    else:
                        sv_ttk.set_theme("light")
                except Exception:
                    sv_ttk.set_theme("light") 
            else:
                sv_ttk.set_theme("light") 
    
    def restore_main_database(self):
        """Возвращает главную базу данных, если мы находились внутри папки коллекции"""
        if hasattr(self, 'main_task_manager'):
            self.task_manager = self.main_task_manager
            self.current_csv_file = self.settings_manager.get_setting("csv_file_path")
            del self.main_task_manager
            self.in_collection_view = False
            
    def open_and_create_task_folder(self, ctf, category, task_name):
        """Открывает папку задачи в Проводнике. Если её нет - создает новую."""
        # Пытаемся найти существующую
        target_folder = self._resolve_task_path(ctf, category, task_name)
        
        if not target_folder:
            # ПАПКИ НЕТ! Создаем новую физическую структуру
            base_dir = os.path.dirname(os.path.abspath(__file__))
            files_dir = os.path.join(base_dir, "data", "files")
            
            # Очищаем имена от запрещенных символов Windows (<, >, :, ", /, \, |, ?, *)
            safe_ctf = re.sub(r'[\\/*?:"<>|]', "", str(ctf)).strip() if ctf else "Unknown_CTF"
            safe_cat = re.sub(r'[\\/*?:"<>|]', "", str(category)).strip() if category else "Unknown_Category"
            safe_task = re.sub(r'[\\/*?:"<>|]', "", str(task_name)).strip() if task_name else "Unknown_Task"
            
            target_folder = os.path.join(files_dir, safe_ctf, safe_cat, safe_task)
            
            try:
                os.makedirs(target_folder, exist_ok=True)
                messagebox.showinfo("Новая папка", f"Создана новая директория для задачи:\n{target_folder}\n\nТеперь вы можете скопировать туда нужные файлы!")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось создать папку:\n{e}")
                return

        # Открываем папку в системном файловом менеджере
        try:
            if platform.system() == 'Windows': os.startfile(target_folder)
            elif platform.system() == 'Darwin': subprocess.call(('open', target_folder))
            else: subprocess.call(('xdg-open', target_folder))
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось открыть папку:\n{e}")