import json
import os
from typing import Dict, Any

class SettingsManager:
    def __init__(self, settings_file: str = "app_settings.json"):
        # Убедимся, что путь к файлу настроек абсолютный
        if not os.path.isabs(settings_file):
            settings_file = os.path.join(os.getcwd(), settings_file)
        self.settings_file = settings_file
        self.default_settings = {
            "csv_file_path": "data/tasks_metadata.csv",
            "theme": "Светлая",
            "language": "Русский",
            "window_width": 1000,
            "window_height": 700,
            "recent_files": [],
            "auto_refresh": True,
            "max_recent_files": 5,
            "workbook_directory": ""  # Новая настройка для каталога задачника
        }
        self.settings = self.load_settings()
    
    def load_settings(self) -> Dict[str, Any]:
        """Загрузка настроек из файла"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    loaded_settings = json.load(f)
                    # Объединяем с настройками по умолчанию для совместимости
                    settings = self.default_settings.copy()
                    settings.update(loaded_settings)
                    return settings
            else:
                # Если файла нет, создаем с настройками по умолчанию
                self.save_settings(self.default_settings)
                return self.default_settings.copy()
        except Exception as e:
            print(f"Ошибка загрузки настроек: {e}")
            return self.default_settings.copy()
    
    def save_settings(self, settings: Dict[str, Any] = None) -> bool:
        """Сохранение настроек в файл"""
        try:
            if settings is not None:
                self.settings = settings
            
            # Создаем директорию если нужно
            directory = os.path.dirname(self.settings_file)
            if directory and not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
            
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=2)
            print(f"Настройки сохранены в: {self.settings_file}")
            return True
        except Exception as e:
            print(f"Ошибка сохранения настроек: {e}")
            # Попробуем сохранить в текущую директорию как запасной вариант
            return self._save_settings_fallback()
    
    def _save_settings_fallback(self) -> bool:
        """Запасной метод сохранения настроек"""
        try:
            # Пробуем сохранить в текущую директорию с другим именем
            fallback_file = "app_settings_fallback.json"
            with open(fallback_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=2)
            print(f"Настройки сохранены в запасной файл: {fallback_file}")
            self.settings_file = fallback_file
            return True
        except Exception as e:
            print(f"Ошибка сохранения в запасной файл: {e}")
            return False
    
    def get_setting(self, key: str, default=None) -> Any:
        """Получение значения настройки"""
        return self.settings.get(key, default)
    
    def set_setting(self, key: str, value: Any) -> None:
        """Установка значения настройки"""
        self.settings[key] = value
    
    def update_settings(self, **kwargs) -> None:
        """Обновление нескольких настроек"""
        self.settings.update(kwargs)
    
    def add_recent_file(self, file_path: str) -> None:
        """Добавление файла в список недавних"""
        # Нормализуем путь
        file_path = os.path.normpath(file_path)
        
        if file_path in self.settings["recent_files"]:
            self.settings["recent_files"].remove(file_path)
        
        self.settings["recent_files"].insert(0, file_path)
        
        # Ограничиваем количество недавних файлов
        max_files = self.settings.get("max_recent_files", 5)
        self.settings["recent_files"] = self.settings["recent_files"][:max_files]
    
    def get_recent_files(self) -> list:
        """Получение списка недавних файлов"""
        return self.settings.get("recent_files", [])
    
    def reset_to_defaults(self) -> None:
        """Сброс настроек к значениям по умолчанию"""
        self.settings = self.default_settings.copy()
        self.save_settings()