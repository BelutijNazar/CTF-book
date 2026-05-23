import csv
import os
from dataclasses import dataclass
from typing import List, Dict, Optional, Any
@dataclass
class Task:
    key: str
    ctf: str
    nctf: str
    data: str
    category: str
    ncat0: str
    ncat1: str
    challenge: str
    description: str
    nc: str
    wsite: str
    writeup: str
    attachment: str
    level: str
    tag1: str
    tag2: str
    tag3: str
    tag4: str
    tag5: str
class TaskManager:
    # 1. СЛОВАРЬ 
    NCAT_PARSER = {
        'crypto':1, 'cryptography':1, 
        'misc':2, 
        'pwn':3, 'box pwn':3, 'binary exploitation':3,
        'rev':4, 'reverse':4, 'reversing':4, 'reverse engineering':4, 'reverse engineer':4,
        'web':5, 'web exploitation':5,
        'forensics':6, 'forensic':6,
        'hardware':7, 
        'intro':8, 'sanity': 8, 'sanity check': 8,
        'osint':9,
        'blockchain':10,
        'programming':11, 'ppc':11,
        'digital assets':12,
        'gambling':13,
        'checkin':14,
        'steganography': 15, 'stegano': 15, 'stego': 15
    }
    # 2. ОТОБРАЖЕНИЕ В ФИЛЬТРЕ 
    ID_TO_DISPLAY = {
        1: "Cryptography",
        2: "Misc",
        3: "Pwn / Binary",
        4: "Reverse Engineering",
        5: "Web Exploitation",
        6: "Forensics",
        7: "Hardware",
        8: "Intro / Sanity",
        9: "OSINT",
        10: "Blockchain",
        11: "Programming / PPC",
        12: "Digital Assets",
        13: "Gambling",
        14: "Checkin",
        15: "Steganography" 
    }
    def __init__(self, csv_file_path: str):
        self.csv_file_path = csv_file_path
        self.tasks: List[Task] = []
        self.load_tasks()
    def load_tasks(self):
        """Загрузка задач из CSV файла"""
        if not os.path.exists(self.csv_file_path):
            print(f"Файл {self.csv_file_path} не найден")
            return []    
        try:
            with open(self.csv_file_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                self.tasks = []
                for row in reader:
                    task = Task(
                        key=row.get('key', ''),
                        ctf=row.get('ctf', ''),
                        nctf=row.get('nctf', ''),
                        data=row.get('data', ''),
                        category=row.get('category', ''),
                        ncat0=row.get('ncat0', '0'),
                        ncat1=row.get('ncat1', '0'),
                        challenge=row.get('challenge', ''),
                        description=row.get('description', ''),
                        nc=row.get('nc', ''),
                        wsite=row.get('wsite', ''),
                        writeup=row.get('writeup', ''),
                        attachment=row.get('attachment', ''),
                        level=row.get('level', ''),
                        tag1=row.get('tag1', ''),
                        tag2=row.get('tag2', ''),
                        tag3=row.get('tag3', ''),
                        tag4=row.get('tag4', ''),
                        tag5=row.get('tag5', '')
                    )
                    self.tasks.append(task)
            return True
        except Exception as e:
            print(f"Ошибка загрузки задач: {e}")
            self.tasks = []
            return False          
    def get_all_categories(self) -> List[str]:
        """Смотрит на цифры в ncat0 и ncat1 и переводит их в слова."""
        used_ids = set()
        for task in self.tasks:
            if task.ncat0 and task.ncat0 != '0': 
                try: used_ids.add(int(task.ncat0))
                except: pass
            if task.ncat1 and task.ncat1 != '0': 
                try: used_ids.add(int(task.ncat1))
                except: pass
        categories = []
        for cat_id in used_ids:
            if cat_id in self.ID_TO_DISPLAY:
                categories.append(self.ID_TO_DISPLAY[cat_id])
            else:
                categories.append(f"Category {cat_id}")
                
        return sorted(categories)

    def get_all_levels(self) -> List[str]:
        levels = set(task.level for task in self.tasks if task.level)
        return sorted(list(levels))
        
    def get_all_ctfs(self) -> List[str]:
        ctfs = set(task.ctf for task in self.tasks if task.ctf)
        return sorted(list(ctfs))

    def get_all_tags(self) -> List[str]:
        tags = set()
        for task in self.tasks:
            for tag in [task.tag1, task.tag2, task.tag3, task.tag4, task.tag5]:
                if tag: tags.add(tag)
        return sorted(list(tags))

    def get_tasks_by_filters(self, query: str = "", category: str = None, level: str = None, 
                           ctf: str = None, tag: str = None,
                           has_writeup: bool = False, has_wsite: bool = False, 
                           has_attachment: bool = False) -> List[Task]:
        """Универсальная фильтрация: Текстовый поиск + Фильтры + Чекбоксы"""
        filtered_tasks = self.tasks
        
        # 0. ТЕКСТОВЫЙ ПОИСК 
        if query:
            query = query.lower().strip()
            filtered_tasks = [t for t in filtered_tasks if t.challenge and query in str(t.challenge).lower()]

        # 1. ФИЛЬТР ПО КАТЕГОРИИ
        if category and category != "Все":
            if category == "Пусто":
                filtered_tasks = [t for t in filtered_tasks if (not t.ncat0 or t.ncat0 == '0') and (not t.ncat1 or t.ncat1 == '0')]
            else:
                target_id = None
                for cat_id, name in self.ID_TO_DISPLAY.items():
                    if name == category:
                        target_id = str(cat_id)
                        break
                if target_id:
                    filtered_tasks = [t for t in filtered_tasks if str(t.ncat0) == target_id or str(t.ncat1) == target_id]

        # 2. Уровень
        if level and level != "Все":
            if level == "Не указан":
                filtered_tasks = [t for t in filtered_tasks if not t.level or t.level.strip() == "" or t.level.lower() == "не указан"]
            else:
                filtered_tasks = [t for t in filtered_tasks if t.level and t.level.lower() == level.lower()]

        # 3. Турнир
        if ctf and ctf != "Все":
            if ctf == "Пусто":
                filtered_tasks = [t for t in filtered_tasks if not t.ctf or not t.ctf.strip()]
            else:
                filtered_tasks = [t for t in filtered_tasks if t.ctf == ctf]
            
        # 4. Тег
        if tag and tag != "Все":
            if tag == "Пусто":
                filtered_tasks = [t for t in filtered_tasks if not any([t.tag1, t.tag2, t.tag3, t.tag4, t.tag5])]
            else:
                filtered_tasks = [t for t in filtered_tasks if tag in [t.tag1, t.tag2, t.tag3, t.tag4, t.tag5]]
        
        # 5. Чекбоксы
        if has_writeup: filtered_tasks = [t for t in filtered_tasks if t.writeup and t.writeup != "[]" and t.writeup != "None" and t.writeup.strip()]
        if has_wsite: filtered_tasks = [t for t in filtered_tasks if t.wsite and t.wsite != "[]" and t.wsite != "None" and t.wsite.strip()]
        if has_attachment: filtered_tasks = [t for t in filtered_tasks if t.attachment and t.attachment != "[]" and t.attachment != "None" and t.attachment.strip()]
        
        return filtered_tasks

    def get_task_statistics(self) -> Dict[str, Any]:
        stats = {
            'total_tasks': len(self.tasks),
            'categories_count': len(self.get_all_categories()),
            'levels_count': len(self.get_all_levels()),
            'tags_count': len(self.get_all_tags()),
            'categories': {},
            'levels': {},
            'tags': {}
        }
        for name in self.get_all_categories():
            stats['categories'][name] = len(self.get_tasks_by_filters(category=name))
        for level in self.get_all_levels():
            stats['levels'][level] = len(self.get_tasks_by_filters(level=level))
        for tag in self.get_all_tags():
            stats['tags'][tag] = len(self.get_tasks_by_filters(tag=tag))
        return stats
    
    def save_tasks_to_csv(self) -> bool:
        """Сохраняет текущий список задач обратно в CSV файл (с безопасными кавычками)"""
        if not self.csv_file_path or not os.path.exists(self.csv_file_path):
            print("Ошибка: Файл CSV не найден для сохранения.")
            return False
        
        try:
            headers =[
                "key", "ctf", "nctf", "data", "category", "ncat0", "ncat1",
                "challenge", "description", "nc", "wsite", "writeup", "attachment",
                "level", "tag1", "tag2", "tag3", "tag4", "tag5"
            ]
            
            with open(self.csv_file_path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=headers, quoting=csv.QUOTE_ALL)
                writer.writeheader()
                
                for task in self.tasks:
                    row = {
                        "key": task.key, "ctf": task.ctf, "nctf": task.nctf,
                        "data": task.data, "category": task.category, 
                        "ncat0": task.ncat0, "ncat1": task.ncat1,
                        "challenge": task.challenge, "description": task.description,
                        "nc": task.nc, "wsite": task.wsite, "writeup": task.writeup,
                        "attachment": task.attachment, "level": task.level,
                        "tag1": task.tag1, "tag2": task.tag2, "tag3": task.tag3,
                        "tag4": task.tag4, "tag5": task.tag5
                    }
                    writer.writerow(row)
            return True
        except Exception as e:
            print(f"Ошибка при сохранении CSV: {e}")
            return False

    def update_task_field(self, task_key: str, field_name: str, new_value: str) -> bool:
        """Обновляет конкретное поле у задачи и сразу сохраняет изменения в файл"""
        for task in self.tasks:
            if str(task.key) == str(task_key):
                if hasattr(task, field_name):
                    setattr(task, field_name, str(new_value))
                    return self.save_tasks_to_csv()
        return False