import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import platform
import subprocess
import ast
import shutil
import webbrowser
from datetime import datetime
from task_manager import TaskManager
from settings_manager import SettingsManager

class TaskDetailWindow:
    """Модальное окно для отображения деталей задачи"""
    
    def __init__(self, parent, task_data, columns):
        self.parent = parent
        self.task_data = task_data
        self.columns = columns
        
        # Создание модального окна
        self.window = tk.Toplevel(parent)
        self.window.title("Детали задачи")
        self.window.geometry("600x600")
        self.window.resizable(True, True)
        self.window.transient(parent)
        self.window.grab_set()
        
        # Центрирование окна
        self.window.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - self.window.winfo_width()) // 2
        y = parent.winfo_y() + (parent.winfo_height() - self.window.winfo_height()) // 2
        self.window.geometry(f"+{x}+{y}")
        
        self.create_widgets()
    
    def create_widgets(self):
        """Создание виджетов окна"""
        # Основной фрейм с прокруткой
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Полоса прокрутки
        canvas = tk.Canvas(main_frame)
        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Заголовок
        title_label = ttk.Label(scrollable_frame, text="📋 Детальная информация о задаче", 
                               font=("Arial", 14, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20), sticky=tk.W)
        
        # Отображение данных задачи
        row = 1
        for i, (column, value) in enumerate(zip(self.columns, self.task_data)):
            column_name = self.get_column_display_name(column)
            
            # Метка названия поля
            name_label = ttk.Label(scrollable_frame, text=f"{column_name}:", 
                                  font=("Arial", 10, "bold"), foreground="darkblue")
            name_label.grid(row=row, column=0, padx=(0, 10), pady=5, sticky=tk.W)
            
            # Значение поля
            value_text = str(value) if value is not None else "Не указано"
            value_label = ttk.Label(scrollable_frame, text=value_text, 
                                   font=("Arial", 10), wraplength=400, justify=tk.LEFT)
            value_label.grid(row=row, column=1, padx=(0, 20), pady=5, sticky=tk.W)
            
            row += 1
        
        # Кнопка закрытия
        button_frame = ttk.Frame(scrollable_frame)
        button_frame.grid(row=row, column=0, columnspan=2, pady=20)
        
        close_btn = ttk.Button(button_frame, text="Закрыть", 
                              command=self.window.destroy, width=20)
        close_btn.pack()
        
        # Размещение canvas и scrollbar
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Настройка веса для растягивания
        scrollable_frame.columnconfigure(1, weight=1)
    
    def get_column_display_name(self, column):
        """Получение отображаемого имени колонки"""
        display_names = {
            "key": "ID задачи",
            "challenge": "Название задачи",
            "category": "Категория",
            "level": "Уровень сложности",
            "description": "Описание",
            "ctf": "CTF мероприятие",
            "writeup": "Наличие writeup",
            "wsite": "Наличие сайта",
            "attachment": "Наличие вложения",
            "tag1": "Тег 1",
            "tag2": "Тег 2",
            "tag3": "Тег 3",
            "tag4": "Тег 4",
            "tag5": "Тег 5",
            "nctf": "Название CTF",
            "data": "Дата",
            "ncat0": "Категория 0",
            "ncat1": "Категория 1",
            "nc": "Дополнительная информация"
        }
        return display_names.get(column, column)

class CryptographyApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Задачник по кибербезопасности")
        
        # Инициализация менеджера настроек
        self.settings_manager = SettingsManager()
        
        # Загрузка настроек окна
        window_width = self.settings_manager.get_setting("window_width", 1000)
        window_height = self.settings_manager.get_setting("window_height", 700)
        self.root.geometry(f"{window_width}x{window_height}")
        
        self.sort_column = "key"
        self.sort_descending = False
        
        # Инициализация менеджера задач
        self.current_csv_file = self.settings_manager.get_setting("csv_file_path", "data/tasks_metadata.csv")
        self.task_manager = TaskManager(self.current_csv_file)
        
        # Переменные для хранения текущих фильтров
        self.current_category = "Все"
        self.current_level = "Все"
        self.current_search_query = ""
        
        # Привязка обработчика закрытия окна
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Создание интерфейса
        self.create_menu_bar()
        self.create_main_frame()
    
    def on_closing(self):
        """Обработчик закрытия приложения"""
        try:
            # Сохраняем размер окна
            self.settings_manager.set_setting("window_width", self.root.winfo_width())
            self.settings_manager.set_setting("window_height", self.root.winfo_height())

            # Сохраняем текущий CSV файл
            self.settings_manager.set_setting("csv_file_path", self.current_csv_file)

            # Сохраняем настройки
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
        tasks_menu.add_command(label="Поиск задач", command=self.show_option2)
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
        """Обновление интерфейса после загрузки файла"""
        filename = os.path.basename(file_path)
        messagebox.showinfo(
            "Успех", 
            f"Файл '{filename}' успешно загружен!\n"
            f"Загружено задач: {len(self.task_manager.tasks)}"
        )
        
        # Обновляем меню недавних файлов
        self.update_recent_files_menu()
        
        # Обновляем интерфейс если находимся в режиме просмотра задач
        if hasattr(self, 'tasks_tree') and self.tasks_tree.winfo_exists():
            self.update_tasks_table()
            self.update_filter_status()
        
        # Обновляем главную страницу если она активна
        self.return_to_main_menu()
    
    def refresh_data(self):
        """Обновление данных из текущего CSV файла"""
        try:
            self.task_manager = TaskManager(self.current_csv_file)
            
            # Обновляем интерфейс если находимся в режиме просмотра задач
            if hasattr(self, 'tasks_tree') and self.tasks_tree.winfo_exists():
                self.update_tasks_table()
                self.update_filter_status()
            
            messagebox.showinfo(
                "Обновлено", 
                f"Данные обновлены!\nЗагружено задач: {len(self.task_manager.tasks)}"
            )
            
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
        
        # Заголовок
        logo_label = ttk.Label(logo_frame, text="ЗАДАЧНИК ПО КИБЕРБЕЗОПАСНОСТИ", 
                              font=("Arial", 24, "bold"), foreground="darkblue")
        logo_label.grid(row=0, column=0, pady=20)
        
        # Подзаголовок
        sub_label = ttk.Label(logo_frame, text="Практикум по решению задач по кибербезопасности", 
                             font=("Arial", 12), foreground="gray")
        sub_label.grid(row=1, column=0, pady=5)
        
        # Информация о текущем файле
        file_info = f"Текущий файл: {os.path.basename(self.current_csv_file)}"
        self.file_label = ttk.Label(logo_frame, text=file_info, 
                                   font=("Arial", 9), foreground="darkgreen")
        self.file_label.grid(row=2, column=0, pady=5)
    
    def create_welcome_section(self):
        """Создание приветственной секции"""
        welcome_frame = ttk.Frame(self.main_frame)
        welcome_frame.grid(row=1, column=0, pady=50, sticky=(tk.W, tk.E, tk.N, tk.S))
        welcome_frame.columnconfigure(0, weight=1)
        
        # Статистика
        stats = self.task_manager.get_task_statistics()
        
        welcome_text = f"""
        Добро пожаловать в задачник по кибербезопасности!
        
        Доступно для изучения:
        • {stats['total_tasks']} задач различной сложности
        • {stats['categories_count']} категорий кибербезопасности
        • {stats['tags_count']} различных тегов
        
        Текущий файл: {os.path.basename(self.current_csv_file)}
        
        Используйте верхнее меню для навигации по приложению:
        
        📊 Задачи - просмотр, поиск и загрузка CSV файлов
        📈 Аналитика - статистика и анализ прогресса
        ⚙️ Настройки - конфигурация приложения
        ❓ Справка - информация о программе
        """
        
        welcome_label = ttk.Label(welcome_frame, text=welcome_text, 
                                 font=("Arial", 11), justify=tk.LEFT)
        welcome_label.grid(row=0, column=0, pady=20)
        
        # Быстрый доступ
        quick_access_frame = ttk.LabelFrame(welcome_frame, text="Быстрый доступ", padding="10")
        quick_access_frame.grid(row=1, column=0, pady=20, sticky=(tk.W, tk.E))
        
        ttk.Button(quick_access_frame, text="📁 Все задачи", 
                  command=self.show_option1).grid(row=0, column=0, padx=5)
        ttk.Button(quick_access_frame, text="🔍 Поиск", 
                  command=self.show_option2).grid(row=0, column=1, padx=5)
        ttk.Button(quick_access_frame, text="📊 Статистика", 
                  command=self.show_option3).grid(row=0, column=2, padx=5)
        ttk.Button(quick_access_frame, text="📂 Загрузить CSV", 
                  command=self.load_csv_file).grid(row=0, column=3, padx=5)
    
    def clear_content(self):
        """Очистка текущего контента (сохраняем только основной фрейм)"""
        for widget in self.main_frame.winfo_children():
            widget.destroy()
    
    def show_option1(self):
        """Режим 1: Просмотр задач"""
        self.clear_content()
        self.create_task_browser()
    
    def show_option2(self):
        """Режим 2: Поиск задач"""
        self.clear_content()
        self.create_search_interface()
    
    def show_option3(self):
        """Режим 3: Статистика"""
        self.clear_content()
        self.create_statistics_interface()
    
    def show_option4(self):
        """Режим 4: Настройки"""
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
        • Загрузка CSV файлов
        • Сохранение настроек
        • Статистика и анализ
        
        © 2025 Все права защищены
        """
        messagebox.showinfo("О программе", about_text)
    
    def create_task_browser(self):
        """Интерфейс для просмотра задач"""
        # Заголовок
        title_frame = ttk.Frame(self.main_frame)
        title_frame.grid(row=0, column=0, pady=10, sticky=(tk.W, tk.E))
        title_frame.columnconfigure(0, weight=1)
        
        title_label = ttk.Label(title_frame, text="📁 Просмотр задач", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, sticky=tk.W)
        
        # Информация о файле
        file_info = f"Файл: {os.path.basename(self.current_csv_file)}"
        file_label = ttk.Label(title_frame, text=file_info, 
                              font=("Arial", 9), foreground="darkgreen")
        file_label.grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        
        # Кнопка возврата
        back_btn = ttk.Button(title_frame, text="← На главную", 
                             command=self.return_to_main_menu)
        back_btn.grid(row=0, column=1, rowspan=2, sticky=(tk.E, tk.N, tk.S))
        
        # Фрейм управления (увеличенная высота)
        control_frame = ttk.LabelFrame(self.main_frame, text="Управление данными", padding="20")
        control_frame.grid(row=1, column=0, pady=10, sticky=(tk.W, tk.E))
        
        # Кнопки управления файлами
        ttk.Button(control_frame, text="📂 Загрузить другой CSV", 
                  command=self.load_csv_file).grid(row=0, column=0, padx=5)
        ttk.Button(control_frame, text="🔄 Обновить данные", 
                  command=self.refresh_data).grid(row=0, column=1, padx=5)
        
        # Фрейм для фильтров
        filter_frame = ttk.LabelFrame(self.main_frame, text="Фильтры", padding="10")
        filter_frame.grid(row=2, column=0, pady=10, sticky=(tk.W, tk.E))
        
        # Первая строка фильтров
        # 1. Категория
        ttk.Label(filter_frame, text="Категория:").grid(row=0, column=0, padx=5, sticky=tk.W)
        self.category_var = tk.StringVar(value="Все")
        categories = ["Все"] + self.task_manager.get_all_categories()
        category_combo = ttk.Combobox(filter_frame, textvariable=self.category_var, 
                                     values=categories, state="readonly", width=20)
        category_combo.grid(row=0, column=1, padx=5)
        category_combo.bind('<<ComboboxSelected>>', self.on_filters_changed)
        
        # 2. Уровень
        ttk.Label(filter_frame, text="Уровень:").grid(row=0, column=2, padx=5, sticky=tk.W)
        self.level_var = tk.StringVar(value="Все")
        raw_levels = self.task_manager.get_all_levels()
        clean_levels = [l for l in raw_levels if l and l.lower() != "не указан"]
        def get_level_priority(level_name):
            name = level_name.lower().strip()
            if name == "easy" or name == "легкий": return 1
            if name == "medium" or name == "средний": return 2
            if name == "hard" or name == "сложный": return 3
            if name == "insane": return 4
            return 5 
        clean_levels.sort(key=lambda x: (get_level_priority(x), x))
        levels = ["Все", "Не указан"] + clean_levels
        level_combo = ttk.Combobox(filter_frame, textvariable=self.level_var, 
                                  values=levels, state="readonly", width=15)
        level_combo.grid(row=0, column=3, padx=5)
        level_combo.bind('<<ComboboxSelected>>', self.on_filters_changed)

        # 3. Турнир (CTF) 
        ttk.Label(filter_frame, text="Турнир:").grid(row=0, column=4, padx=5, sticky=tk.W)
        self.ctf_var = tk.StringVar(value="Все") 
        ctfs = ["Все"] + self.task_manager.get_all_ctfs()
        ctf_combo = ttk.Combobox(filter_frame, textvariable=self.ctf_var, 
                                values=ctfs, state="readonly", width=20)
        ctf_combo.grid(row=0, column=5, padx=5)
        ctf_combo.bind('<<ComboboxSelected>>', self.on_filters_changed)
        
        # 4. ТЕГИ 
        ttk.Label(filter_frame, text="Тег:").grid(row=0, column=6, padx=5, sticky=tk.W)
        self.tag_var = tk.StringVar(value="Все")
        tags = ["Все"] + self.task_manager.get_all_tags()
        tag_combo = ttk.Combobox(filter_frame, textvariable=self.tag_var, 
                                values=tags, state="readonly", width=15)
        tag_combo.grid(row=0, column=7, padx=5)
        tag_combo.bind('<<ComboboxSelected>>', self.on_filters_changed)
        # Вторая строка фильтров - чекбоксы
        self.writeup_var = tk.BooleanVar()
        writeup_check = ttk.Checkbutton(filter_frame, text="Есть writeup", 
                                       variable=self.writeup_var,
                                       command=self.on_filters_changed)
        writeup_check.grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        
        self.wsite_var = tk.BooleanVar()
        wsite_check = ttk.Checkbutton(filter_frame, text="Есть сайт", 
                                     variable=self.wsite_var,
                                     command=self.on_filters_changed)
        wsite_check.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        
        self.attachment_var = tk.BooleanVar()
        attachment_check = ttk.Checkbutton(filter_frame, text="Есть вложение", 
                                          variable=self.attachment_var,
                                          command=self.on_filters_changed)
        attachment_check.grid(row=1, column=2, padx=5, pady=5, sticky=tk.W)
        
        # Кнопка сброса фильтров
        reset_btn = ttk.Button(filter_frame, text="Сбросить фильтры",
                              command=self.reset_filters)
        reset_btn.grid(row=1, column=3, padx=10, pady=5)
        
        # Статус фильтров
        self.filter_status = ttk.Label(self.main_frame, text="", foreground="blue")
        self.filter_status.grid(row=3, column=0, pady=5, sticky=tk.W)
        
        # Таблица задач
        self.create_tasks_table()
        
        # Обновление статуса
        self.update_filter_status()
    
    def create_tasks_table(self):
        """Создание таблицы для отображения задач (с сортировкой)"""
        # Фрейм для таблицы
        table_frame = ttk.Frame(self.main_frame)
        table_frame.grid(row=4, column=0, pady=10, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Колонки
        columns = ("key", "challenge", "category", "level", "description", "ctf", 
                  "writeup", "wsite", "attachment", "tag1", "tag2", "tag3", "tag4", "tag5")
        self.tasks_tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=20)
        
        self.headers_map = {
            "key": "ID",
            "challenge": "Задача",
            "category": "Категория",
            "level": "Уровень",
            "description": "Описание",
            "ctf": "CTF",
            "writeup": "Writeup",
            "wsite": "Сайт",
            "attachment": "Вложение",
            "tag1": "Тег 1",
            "tag2": "Тег 2",
            "tag3": "Тег 3",
            "tag4": "Тег 4",
            "tag5": "Тег 5"
        }

        # Колонки, по которым разрешена сортировка (как ты просил)
        sortable_cols = ["key", "challenge", "category", "ctf", "tag1", "tag2", "tag3", "tag4", "tag5"]

        for col_id in columns:
            display_name = self.headers_map.get(col_id, col_id)
            
            # Если колонка в списке сортируемых - добавляем команду клика
            if col_id in sortable_cols:
                self.tasks_tree.heading(col_id, text=display_name, 
                                      command=lambda c=col_id: self.on_header_click(c))
            else:
                # Если сортировать нельзя (например, Вложение), просто текст
                self.tasks_tree.heading(col_id, text=display_name)

        self.tasks_tree.column("key", width=50)
        self.tasks_tree.column("challenge", width=150)
        self.tasks_tree.column("category", width=100)
        self.tasks_tree.column("level", width=70)
        self.tasks_tree.column("description", width=80)
        self.tasks_tree.column("ctf", width=120)
        self.tasks_tree.column("writeup", width=80)
        self.tasks_tree.column("wsite", width=80)
        self.tasks_tree.column("attachment", width=80)
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
        
        # Привязка двойного клика (из предыдущих шагов)
        self.tasks_tree.bind("<Double-1>", self.show_task_details)
        
        # Первичное обновление заголовков (показать стрелку по умолчанию)
        self.update_header_arrows()
        
        # Заполнение данными
        self.update_tasks_table()
    
    def on_task_double_click(self, event):
        """Обработчик двойного клика по задаче в таблице просмотра"""
        item = self.tasks_tree.selection()[0] if self.tasks_tree.selection() else None
        if item:
            task_data = self.tasks_tree.item(item, "values")
            columns = ("key", "challenge", "category", "level", "description", "ctf", 
                      "writeup", "wsite", "attachment", "tag1", "tag2", "tag3", "tag4", "tag5")
            TaskDetailWindow(self.root, task_data, columns)
    
    def update_tasks_table(self):
        """Обновление таблицы задач согласно фильтрам и СОРТИРОВКЕ"""
        for item in self.tasks_tree.get_children():
            self.tasks_tree.delete(item)
        
        # 1. Получение отфильтрованных задач (ДОБАВИЛ tag)
        filtered_tasks = self.task_manager.get_tasks_by_filters(
            self.category_var.get(), 
            self.level_var.get(),
            self.ctf_var.get() if hasattr(self, 'ctf_var') else None,
            self.tag_var.get() if hasattr(self, 'tag_var') else None,  # <--- ВОТ ТУТ
            self.writeup_var.get(),
            self.wsite_var.get(),
            self.attachment_var.get()
        )
        
        # 2. СОРТИРОВКА
        if self.sort_column:
            def sort_key(task):
                value = getattr(task, self.sort_column, "")
                if self.sort_column == "key":
                    try: return int(value)
                    except ValueError: return 0
                if value is None: return ""
                return str(value).lower()
            filtered_tasks.sort(key=sort_key, reverse=self.sort_descending)
        
        # 3. Заполнение
        for task in filtered_tasks:
            has_wr = "✅" if task.writeup and task.writeup != "[]" and task.writeup != "None" else "❌"
            has_site = "✅" if task.wsite and task.wsite != "[]" and task.wsite != "None" and task.wsite != "" else "❌"
            has_att = "✅" if task.attachment and task.attachment != "[]" and task.attachment != "None" else "❌"
            
            self.tasks_tree.insert("", tk.END, values=(
                task.key, task.challenge, task.category,
                task.level if task.level else "Не указан",
                task.description[:50] + "..." if len(task.description) > 50 else task.description,
                task.ctf, has_wr, has_site, has_att,
                task.tag1, task.tag2, task.tag3, task.tag4, task.tag5
            ))
    
    def on_filters_changed(self, event=None):
        """Обработчик изменения фильтров"""
        self.update_tasks_table()
        self.update_filter_status()
    
    def reset_filters(self):
        """Сброс фильтров и сортировки к значениям по умолчанию"""
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
    
    def update_filter_status(self):
        """Обновление статусной строки фильтров (ИСПРАВЛЕНО)"""
        category = self.category_var.get()
        level = self.level_var.get()
        
        ctf = self.ctf_var.get() if hasattr(self, 'ctf_var') else "Все"
        tag = self.tag_var.get() if hasattr(self, 'tag_var') else "Все"
        
        writeup = self.writeup_var.get()
        wsite = self.wsite_var.get()
        attachment = self.attachment_var.get()
        
        filtered_tasks = self.task_manager.get_tasks_by_filters(
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
        
        if category != "Все": status_text += f" | 🏷️ {category}"
        if level != "Все": status_text += f" | ⚡ {level}"
        if ctf != "Все": status_text += f" | 🏆 {ctf}"
        if tag != "Все": status_text += f" | # {tag}"
        
        if writeup: status_text += " | 📝 Есть writeup"
        if wsite: status_text += " | 🌐 Есть сайт"
        if attachment: status_text += " | 📎 Есть вложение"
        
        self.filter_status.config(text=status_text)
    
    def create_search_interface(self):
        """Интерфейс для поиска задач"""
        # Заголовок
        title_label = ttk.Label(self.main_frame, text="🔍 Поиск задач", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, pady=10, sticky=tk.W)
        
        # Кнопка возврата
        back_btn = ttk.Button(self.main_frame, text="← На главную", 
                             command=self.return_to_main_menu)
        back_btn.grid(row=0, column=0, sticky=tk.E)
        
        # Поле поиска
        search_frame = ttk.LabelFrame(self.main_frame, text="Поиск", padding="10")
        search_frame.grid(row=1, column=0, pady=10, sticky=(tk.W, tk.E))
        
        # Строка 1: Текстовый поиск
        ttk.Label(search_frame, text="Текст поиска:").grid(row=0, column=0, padx=5, sticky=tk.W)
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=40, font=("Arial", 10))
        search_entry.grid(row=0, column=1, padx=5, sticky=tk.W)
        search_entry.bind('<Return>', lambda e: self.perform_search())
        
        # Строка 2: Категория и чекбоксы
        ttk.Label(search_frame, text="Категория:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.search_category_var = tk.StringVar(value="Все")
        search_categories = ["Все"] + self.task_manager.get_all_categories()
        search_category_combo = ttk.Combobox(search_frame, textvariable=self.search_category_var, 
                                           values=search_categories, state="readonly", width=25)
        search_category_combo.set("Все")
        search_category_combo.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        
        # Чекбоксы для поиска
        self.search_writeup_var = tk.BooleanVar()
        search_writeup_check = ttk.Checkbutton(search_frame, text="Есть writeup", 
                                             variable=self.search_writeup_var)
        search_writeup_check.grid(row=1, column=2, padx=10, pady=5, sticky=tk.W)
        
        self.search_wsite_var = tk.BooleanVar()
        search_wsite_check = ttk.Checkbutton(search_frame, text="Есть сайт", 
                                           variable=self.search_wsite_var)
        search_wsite_check.grid(row=1, column=3, padx=10, pady=5, sticky=tk.W)
        
        self.search_attachment_var = tk.BooleanVar()
        search_attachment_check = ttk.Checkbutton(search_frame, text="Есть вложение", 
                                                variable=self.search_attachment_var)
        search_attachment_check.grid(row=1, column=4, padx=10, pady=5, sticky=tk.W)
        
        # Строка 3: Кнопки управления
        search_btn = ttk.Button(search_frame, text="Найти",
                              command=self.perform_search)
        search_btn.grid(row=2, column=0, padx=5, pady=5)
        
        clear_btn = ttk.Button(search_frame, text="Очистить",
                             command=self.clear_search)
        clear_btn.grid(row=2, column=1, padx=5, pady=5)
        
        # Статус поиска
        self.search_status = ttk.Label(self.main_frame, text="Введите поисковый запрос", 
                                      foreground="blue")
        self.search_status.grid(row=2, column=0, pady=5, sticky=tk.W)
        
        # Таблица результатов поиска с дополнительными колонками
        self.create_search_results_table()
    
    def create_search_results_table(self):
        """Создание таблицы для результатов поиска"""
        table_frame = ttk.Frame(self.main_frame)
        table_frame.grid(row=3, column=0, pady=10, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Создание Treeview с дополнительными колонками
        columns = ("key", "challenge", "category", "level", "description", "ctf", 
                  "writeup", "wsite", "attachment", "tag1", "tag2", "tag3", "tag4", "tag5")
        self.search_tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=20)
        
        # Заголовки колонок
        self.search_tree.heading("key", text="ID")
        self.search_tree.heading("challenge", text="Задача")
        self.search_tree.heading("category", text="Категория")
        self.search_tree.heading("level", text="Уровень")
        self.search_tree.heading("description", text="Описание")
        self.search_tree.heading("ctf", text="CTF")
        self.search_tree.heading("writeup", text="Writeup")
        self.search_tree.heading("wsite", text="Сайт")
        self.search_tree.heading("attachment", text="Вложение")
        self.search_tree.heading("tag1", text="Тег 1")
        self.search_tree.heading("tag2", text="Тег 2")
        self.search_tree.heading("tag3", text="Тег 3")
        self.search_tree.heading("tag4", text="Тег 4")
        self.search_tree.heading("tag5", text="Тег 5")
        
        # Настройка ширины колонок
        self.search_tree.column("key", width=50)
        self.search_tree.column("challenge", width=150)
        self.search_tree.column("category", width=100)
        self.search_tree.column("level", width=70)
        self.search_tree.column("description", width=80)
        self.search_tree.column("ctf", width=120)
        self.search_tree.column("writeup", width=70)
        self.search_tree.column("wsite", width=70)
        self.search_tree.column("attachment", width=70)
        self.search_tree.column("tag1", width=80)
        self.search_tree.column("tag2", width=80)
        self.search_tree.column("tag3", width=80)
        self.search_tree.column("tag4", width=80)
        self.search_tree.column("tag5", width=80)
        
        # Привязка двойного клика
        self.search_tree.bind("<Double-1>", self.on_search_result_double_click)
        
        # Полоса прокрутки
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.search_tree.yview)
        self.search_tree.configure(yscrollcommand=scrollbar.set)
        
        # Размещение элементов
        self.search_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Настройка растягивания
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)
        self.main_frame.rowconfigure(3, weight=1)
    
    def on_search_result_double_click(self, event):
        """Обработчик двойного клика по результату поиска"""
        item = self.search_tree.selection()[0] if self.search_tree.selection() else None
        if item:
            task_data = self.search_tree.item(item, "values")
            columns = ("key", "challenge", "category", "level", "description", "ctf", 
                      "writeup", "wsite", "attachment", "tag1", "tag2", "tag3", "tag4", "tag5")
            TaskDetailWindow(self.root, task_data, columns)
    
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
        
        self.search_status.config(
            text=status_text,
            foreground="green" if results else "red"
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
        self.search_status.config(text="Введите поисковый запрос", foreground="blue")
    
    def create_statistics_interface(self):
        """Интерфейс статистики"""
        title_label = ttk.Label(self.main_frame, text="📊 Статистика", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, pady=10, sticky=tk.W)
        
        back_btn = ttk.Button(self.main_frame, text="← На главную", 
                             command=self.return_to_main_menu)
        back_btn.grid(row=0, column=0, sticky=tk.E)
        
        stats_frame = ttk.Frame(self.main_frame)
        stats_frame.grid(row=1, column=0, pady=10, sticky=(tk.W, tk.E, tk.N, tk.S))
        stats = self.task_manager.get_task_statistics()
        
        category_stats = "\n".join([f"• {cat}: {count} задач" 
                                  for cat, count in stats['categories'].items()])
        
        level_stats = "\n".join([f"• {level}: {count} задач" 
                               for level, count in stats['levels'].items()]) if stats['levels'] else "• Уровни не указаны"
        
        stats_text = f"""
        📈 Общая статистика:
        
        📁 Всего задач: {stats['total_tasks']}
        🏷️ Категорий: {stats['categories_count']}
        ⚡ Уровней сложности: {stats['levels_count']}
        🏷️ Тегов: {stats['tags_count']}
        
        📊 Распределение по категориям:
        {category_stats}
        
        📈 Распределение по уровням:
        {level_stats}
        
        📄 Текущий файл: {os.path.basename(self.current_csv_file)}
        """
        
        stats_label = ttk.Label(stats_frame, text=stats_text, justify=tk.LEFT, font=("Arial", 10))
        stats_label.grid(row=0, column=0, sticky=tk.W)
        self.main_frame.rowconfigure(1, weight=1)
        stats_frame.columnconfigure(0, weight=1)
        stats_frame.rowconfigure(0, weight=1)
    
    def create_settings_interface(self):
        """Интерфейс настроек"""
        title_label = ttk.Label(self.main_frame, text="⚙️ Настройки приложения", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, pady=10, sticky=tk.W)
        
        back_btn = ttk.Button(self.main_frame, text="← На главную", 
                             command=self.return_to_main_menu)
        back_btn.grid(row=0, column=0, sticky=tk.E)
        
        settings_frame = ttk.LabelFrame(self.main_frame, text="Настройки", padding="20")
        settings_frame.grid(row=1, column=0, pady=10, sticky=(tk.W, tk.E))
        
        current_theme = self.settings_manager.get_setting("theme", "Светлая")
        current_language = self.settings_manager.get_setting("language", "Русский")
        current_auto_refresh = self.settings_manager.get_setting("auto_refresh", True)
        current_workbook_dir = self.settings_manager.get_setting("workbook_directory", "Не установлен")
        
        self.theme_var = tk.StringVar(value=current_theme)
        self.language_var = tk.StringVar(value=current_language)
        self.auto_refresh_var = tk.BooleanVar(value=current_auto_refresh)
        
        ttk.Label(settings_frame, text="Тема интерфейса:", font=("Arial", 10)).grid(row=0, column=0, sticky=tk.W, pady=5)
        theme_combo = ttk.Combobox(settings_frame, textvariable=self.theme_var, 
                                  values=["Светлая", "Темная", "Системная"], state="readonly", width=25)
        theme_combo.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        
        ttk.Label(settings_frame, text="Язык интерфейса:", font=("Arial", 10)).grid(row=1, column=0, sticky=tk.W, pady=5)
        language_combo = ttk.Combobox(settings_frame, textvariable=self.language_var, 
                                     values=["Русский", "English"], state="readonly", width=25)
        language_combo.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        
        ttk.Label(settings_frame, text="Автообновление:", font=("Arial", 10)).grid(row=2, column=0, sticky=tk.W, pady=5)
        auto_refresh_check = ttk.Checkbutton(settings_frame, text="Автоматически обновлять данные", 
                                           variable=self.auto_refresh_var)
        auto_refresh_check.grid(row=2, column=1, padx=5, pady=5, sticky=tk.W)
        
        files_frame = ttk.LabelFrame(settings_frame, text="Файлы и каталоги", padding="10")
        files_frame.grid(row=3, column=0, columnspan=2, pady=10, sticky=(tk.W, tk.E))
        
        ttk.Label(files_frame, text="Текущий файл задач:", font=("Arial", 9)).grid(row=0, column=0, sticky=tk.W)
        ttk.Label(files_frame, text=self.current_csv_file, font=("Arial", 9), foreground="blue").grid(row=0, column=1, sticky=tk.W, padx=5)
        
        ttk.Label(files_frame, text="Каталог задачника:", font=("Arial", 9)).grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Label(files_frame, text=current_workbook_dir, font=("Arial", 9), foreground="blue").grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(files_frame, text="Файл настроек:", font=("Arial", 9)).grid(row=2, column=0, sticky=tk.W, pady=5)
        ttk.Label(files_frame, text=self.settings_manager.settings_file, font=("Arial", 9), foreground="blue").grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)
        
        button_frame = ttk.Frame(settings_frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=20)
        
        save_btn = ttk.Button(button_frame, text="Сохранить настройки", 
                             command=self.save_application_settings, width=20)
        save_btn.grid(row=0, column=0, padx=10)
        
        reset_btn = ttk.Button(button_frame, text="Сбросить настройки", 
                              command=self.reset_application_settings, width=20)
        reset_btn.grid(row=0, column=1, padx=10)
        
        info_text = f"""
        Текущие настройки сохраняются в файл: {self.settings_manager.settings_file}
        Настройки автоматически загружаются при запуске приложения.
        """
        info_label = ttk.Label(settings_frame, text=info_text, font=("Arial", 8), 
                              foreground="gray", justify=tk.LEFT)
        info_label.grid(row=5, column=0, columnspan=2, pady=10, sticky=tk.W)
    
    def save_application_settings(self):
        """Сохранение настроек приложения"""
        try:
            settings = {
                "theme": self.theme_var.get(),
                "language": self.language_var.get(),
                "auto_refresh": self.auto_refresh_var.get(),
                "csv_file_path": self.current_csv_file,
                "window_width": self.root.winfo_width(),
                "window_height": self.root.winfo_height()
            }

            self.settings_manager.update_settings(**settings)
            if self.settings_manager.save_settings():
                messagebox.showinfo("Успех", "Настройки успешно сохранены!")
            else:
                messagebox.showwarning("Предупреждение", 
                                     "Настройки сохранены в запасной файл. Проверьте права доступа.")

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
        self.clear_content()
        self.create_logo_section()
        self.create_welcome_section()
        
    def open_external_file(self, filename_raw, ctf=None, category=None, task_name=None):
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
                    import re
                    def simplify(s): return re.sub(r'[\W_]+', '', s.lower())
                    target_simple = simplify(filename)
                    for f in files:
                        if simplify(f).startswith(target_simple):
                            found_path = os.path.join(target_folder, f)
                            break

        if not found_path:
            msg = f"Не удалось найти файл: '{filename}'"
            if target_folder: msg += f"\nВ папке: {target_folder}"
            messagebox.showerror("Файл не найден", msg)
            return

        try:
            if platform.system() == 'Darwin': subprocess.call(('open', found_path))
            elif platform.system() == 'Windows': os.startfile(found_path)
            else: subprocess.call(('xdg-open', found_path))
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось открыть файл:\n{e}")

    def show_task_details(self, event):
        """Показывает окно с деталями задачи"""
        selected_item = self.tasks_tree.selection()
        if not selected_item: return
        
        item_values = self.tasks_tree.item(selected_item[0])['values']
        task_id = item_values[0] 
        
        task = next((t for t in self.task_manager.tasks if str(t.key) == str(task_id)), None)
        if not task: return

        detail_window = tk.Toplevel(self.root)
        detail_window.title(f"Задача: {task.challenge}")
        detail_window.geometry("600x650")
        
        ttk.Label(detail_window, text="📄 Детальная информация о задаче", 
                 font=("Arial", 14, "bold")).pack(pady=15)

        content_frame = ttk.Frame(detail_window, padding="20")
        content_frame.pack(fill=tk.BOTH, expand=True)

        def copy_to_clipboard(text):
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            self.root.update()
            messagebox.showinfo("Скопировано", f"Ссылка скопирована:\n{text}")

        # === ГЛАВНАЯ ФУНКЦИЯ ОТРИСОВКИ ===
        def create_row(parent, label_text, value_text, is_link=False, filename=None, is_web_link=False, is_netcat=False):
            row_frame = ttk.Frame(parent)
            row_frame.pack(fill=tk.X, pady=5)
            
            lbl = ttk.Label(row_frame, text=label_text, width=22, font=("Arial", 10, "bold"), foreground="#2c3e50")
            lbl.pack(side=tk.LEFT, anchor="n")
            
            clean_value = str(value_text).strip()
            try:
                if clean_value.startswith("[") and clean_value.endswith("]"):
                    import ast
                    parsed = ast.literal_eval(clean_value)
                    if isinstance(parsed, list) and len(parsed) > 0: clean_value = str(parsed[0])
            except: pass
            clean_value = clean_value.strip("[]'\" ")

            # --- 1. WEB LINK (Удаленный сайт) ---
            if is_web_link and clean_value and clean_value != "[]" and clean_value != "":
                val = ttk.Label(row_frame, text=f"{clean_value} (Перейти 🌐)", 
                               font=("Arial", 10, "underline"), foreground="blue", cursor="hand2")
                val.pack(side=tk.LEFT, anchor="n")
                val.bind("<Button-1>", lambda e: webbrowser.open(clean_value))
                
                copy_lbl = ttk.Label(row_frame, text=" 📋", font=("Arial", 12), cursor="hand2")
                copy_lbl.pack(side=tk.LEFT, anchor="n", padx=5)
                copy_lbl.bind("<Button-1>", lambda e: copy_to_clipboard(clean_value))
                copy_lbl.bind("<Enter>", lambda e: copy_lbl.configure(foreground="gray"))
                copy_lbl.bind("<Leave>", lambda e: copy_lbl.configure(foreground="black"))

            # --- 2. NETCAT ---
            elif is_netcat and clean_value and clean_value != "[]" and clean_value != "":
                val = ttk.Label(row_frame, text=clean_value, font=("Consolas", 10, "bold"), foreground="#d35400")
                val.pack(side=tk.LEFT, anchor="n")
                copy_lbl = ttk.Label(row_frame, text=" 📋", font=("Arial", 12), cursor="hand2")
                copy_lbl.pack(side=tk.LEFT, anchor="n", padx=5)
                copy_lbl.bind("<Button-1>", lambda e: copy_to_clipboard(clean_value))

            # --- 3. ФАЙЛ / ЛОКАЛЬНЫЙ САЙТ (Ссылка + Редактирование) ---
            elif is_link and filename and filename != "[]" and filename != "":
                clean_filename = str(filename).strip()
                try:
                    if clean_filename.startswith("[") and clean_filename.endswith("]"):
                        import ast
                        parsed = ast.literal_eval(clean_filename)
                        if isinstance(parsed, list) and len(parsed) > 0: clean_filename = str(parsed[0])
                except: pass
                clean_filename = clean_filename.strip("[]'\" ")

                display_text = value_text if "index.html" in value_text else clean_value

                val = ttk.Label(row_frame, text=f"{display_text} (Открыть ↗)", 
                               font=("Arial", 10, "underline"), foreground="blue", cursor="hand2")
                val.pack(side=tk.LEFT, anchor="n")
                
                val.bind("<Button-1>", lambda e: self.open_external_file(
                    clean_filename, ctf=task.ctf, category=task.category, task_name=task.challenge))
                
                # Кнопка редактирования
                edit_lbl = ttk.Label(row_frame, text=" ✏️(Ред.)", font=("Arial", 10), foreground="gray", cursor="hand2")
                edit_lbl.pack(side=tk.LEFT, anchor="n", padx=5)
                edit_lbl.bind("<Button-1>", lambda e: self.edit_file_safely(
                    clean_filename, ctf=task.ctf, category=task.category, task_name=task.challenge))
                edit_lbl.bind("<Enter>", lambda e: edit_lbl.configure(foreground="red"))
                edit_lbl.bind("<Leave>", lambda e: edit_lbl.configure(foreground="gray"))

            # --- 4. ПРОСТО ТЕКСТ ---
            else:
                display = clean_value if clean_value != "[]" and clean_value != "" else "Отсутствует"
                ttk.Label(row_frame, text=display, font=("Arial", 10), wraplength=380).pack(side=tk.LEFT, anchor="n")

        # --- ЗАПОЛНЕНИЕ ПОЛЕЙ ---
        create_row(content_frame, "ID задачи:", str(task.key))
        create_row(content_frame, "Название задачи:", task.challenge)
        create_row(content_frame, "Категория:", task.category)
        create_row(content_frame, "Уровень сложности:", task.level)
        create_row(content_frame, "CTF мероприятие:", task.ctf)
        ttk.Separator(content_frame, orient='horizontal').pack(fill='x', pady=10)

        # ОПИСАНИЕ (ZIP + TEXT)
        files_info = self.get_task_files_info(task.ctf, task.category, task.challenge)
        desc_frame = ttk.Frame(content_frame)
        desc_frame.pack(fill=tk.X, pady=5)
        ttk.Label(desc_frame, text="Описание:", width=22, font=("Arial", 10, "bold"), foreground="#2c3e50").pack(side=tk.LEFT, anchor="n")
        
        if not task.description.endswith('.txt'):
             ttk.Label(desc_frame, text=task.description, font=("Arial", 10), wraplength=380).pack(side=tk.LEFT)
        else:
            has_content = False 
            if files_info['zip']:
                lbl = ttk.Label(desc_frame, text="📦 Архив (Открыть)", font=("Arial", 10, "underline"), foreground="brown", cursor="hand2")
                lbl.pack(side=tk.LEFT, padx=(0, 5))
                lbl.bind("<Button-1>", lambda e, f=files_info['zip']: self.open_external_file(f, ctf=task.ctf, category=task.category, task_name=task.challenge))
                has_content = True
            
            if files_info['desc']:
                if has_content: ttk.Label(desc_frame, text="|", foreground="gray").pack(side=tk.LEFT, padx=5)
                lbl = ttk.Label(desc_frame, text="📄 Текст задания (Открыть)", font=("Arial", 10, "underline"), foreground="blue", cursor="hand2")
                lbl.pack(side=tk.LEFT, padx=(0, 2))
                lbl.bind("<Button-1>", lambda e, f=files_info['desc']: self.open_external_file(f, ctf=task.ctf, category=task.category, task_name=task.challenge))
                
                edt = ttk.Label(desc_frame, text="✏️", font=("Arial", 10), foreground="gray", cursor="hand2")
                edt.pack(side=tk.LEFT)
                edt.bind("<Button-1>", lambda e, f=files_info['desc']: self.edit_file_safely(f, ctf=task.ctf, category=task.category, task_name=task.challenge))
                edt.bind("<Enter>", lambda e: edt.configure(foreground="red"))
                edt.bind("<Leave>", lambda e: edt.configure(foreground="gray"))
                has_content = True

            if not has_content: ttk.Label(desc_frame, text="Файлы не найдены", foreground="red").pack(side=tk.LEFT)

        # WRITEUP
        has_wr = task.writeup and task.writeup != "[]" and task.writeup != "None"
        create_row(content_frame, "Наличие writeup:", "Доступен" if has_wr else "Нет", is_link=has_wr, filename=task.writeup)
        
        # === САЙТ ===
        raw_site = task.wsite
        clean_site = ""
        
        # 1. Очистка строки из CSV
        if raw_site and raw_site != "[]" and raw_site != "None" and raw_site != "":
            clean_site = str(raw_site).strip()
            try:
                if clean_site.startswith("[") and clean_site.endswith("]"):
                    import ast
                    parsed = ast.literal_eval(clean_site)
                    if isinstance(parsed, list) and len(parsed) > 0: clean_site = str(parsed[0])
            except: pass
            clean_site = clean_site.strip("[]'\" ")

        # 2. Функция для открытия папки в проводнике
        def open_folder(path):
            try:
                if platform.system() == 'Windows': os.startfile(path)
                elif platform.system() == 'Darwin': subprocess.call(('open', path))
                else: subprocess.call(('xdg-open', path))
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось открыть папку:\n{e}")

        # 3. Логика выбора
        if not clean_site:
            create_row(content_frame, "Сайт:", "Отсутствует")
        
        # ВАРИАНТ А: Ссылка в интернет (http/https)
        elif clean_site.lower().startswith("http"):
            create_row(content_frame, "Сайт:", clean_site, is_web_link=True)
            
        # ВАРИАНТ Б: Локальная папка (wsite)
        else:
            task_folder = self._resolve_task_path(task.ctf, task.category, task.challenge)
            found_folder_path = None
            folder_name_to_show = clean_site

            if task_folder and os.path.exists(task_folder):
                # 1. Пробуем найти папку с точным именем из CSV
                exact_path = os.path.join(task_folder, clean_site)
                if os.path.isdir(exact_path):
                    found_folder_path = exact_path
                
                # 2. Если не нашли, ищем любую папку, в названии которой есть "wsite"
                if not found_folder_path and "wsite" in clean_site.lower():
                    try:
                        for item in os.listdir(task_folder):
                            full_path = os.path.join(task_folder, item)
                            if os.path.isdir(full_path) and "wsite" in item.lower():
                                found_folder_path = full_path
                                folder_name_to_show = item 
                                break
                    except: pass

            # Отрисовка результата
            site_frame = ttk.Frame(content_frame)
            site_frame.pack(fill=tk.X, pady=5)
            ttk.Label(site_frame, text="Сайт:", width=22, font=("Arial", 10, "bold"), foreground="#2c3e50").pack(side=tk.LEFT)

            if found_folder_path:
                link = ttk.Label(site_frame, text=f"📂 {folder_name_to_show} (Открыть папку)", 
                               font=("Arial", 10, "underline"), foreground="brown", cursor="hand2")
                link.pack(side=tk.LEFT)
                link.bind("<Button-1>", lambda e: open_folder(found_folder_path))
            else:
                err = ttk.Label(site_frame, text=f"Папка '{clean_site}' не найдена", 
                              font=("Arial", 10), foreground="red")
                err.pack(side=tk.LEFT)

        # NETCAT
        has_nc = task.nc and task.nc != "[]" and task.nc != "None" and task.nc != ""
        create_row(content_frame, "Netcat:", task.nc, is_netcat=has_nc)
        
        # ВЛОЖЕНИЯ
        raw_att = task.attachment
        att_list = []
        if raw_att and raw_att != "[]" and raw_att != "None" and raw_att != "":
            try:
                clean_str = raw_att.strip()
                if clean_str.startswith("[") and clean_str.endswith("]"):
                    import ast
                    parsed = ast.literal_eval(clean_str)
                    if isinstance(parsed, list): att_list = [str(x).strip() for x in parsed if x]
                else: att_list = [clean_str]
            except: att_list = [str(raw_att).strip()]

        if not att_list:
            create_row(content_frame, "Файл задания:", "Нет вложений")
        else:
            for i, filename in enumerate(att_list):
                lbl = "Файл задания:" if i == 0 else ""
                create_row(content_frame, lbl, filename, is_link=True, filename=filename)

        tags = [t for t in [task.tag1, task.tag2, task.tag3, task.tag4, task.tag5] if t]
        if tags: create_row(content_frame, "Теги:", ", ".join(tags))
        ttk.Button(detail_window, text="Закрыть", command=detail_window.destroy).pack(pady=10)
        
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
                    import re
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
        """
        Ищет путь к папке задачи.
        """
        # 1. Базовый путь
        base_dir = os.path.dirname(os.path.abspath(__file__))
        roots = [
            os.path.join(base_dir, "data", "files"),
            os.path.abspath(os.path.join(base_dir, "..", "data", "files"))
        ]
        current_path = next((r for r in roots if os.path.exists(r)), None)
        
        if not current_path: return None 

        def find_folder_insensitive(base, target_name):
            if not os.path.exists(base): return None
            try:
                if os.path.exists(os.path.join(base, target_name)):
                    return os.path.join(base, target_name)
                
                target_lower = target_name.lower().strip()
                for item in os.listdir(base):
                    if os.path.isdir(os.path.join(base, item)):
                        if item.lower().strip() == target_lower:
                            return os.path.join(base, item)
            except: pass
            return None

        # 2. Ищем папку Турнира (CTF)
        if ctf:
            current_path = find_folder_insensitive(current_path, ctf)
            if not current_path: return None 

        # 3. Ищем папку Задачи (СКАНИРУЕМ ВСЕ КАТЕГОРИИ)
        if task_name:
            direct_task = find_folder_insensitive(current_path, task_name)
            if direct_task:
                return direct_task
            
            try:
                subfolders = [f.path for f in os.scandir(current_path) if f.is_dir()]
                
                for cat_folder in subfolders:
                    found_task = find_folder_insensitive(cat_folder, task_name)
                    if found_task:
                        return found_task
            except:
                pass
            
        return None