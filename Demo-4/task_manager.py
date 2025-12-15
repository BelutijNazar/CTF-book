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
    # 1. СЛОВАРЬ (Для справки и возможного расширения функционала)
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

    # 2. ОТОБРАЖЕНИЕ В ФИЛЬТРЕ (ID -> Красивое имя)
    # Если в CSV стоит число, программа берет название отсюда
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
        """
        Собирает список категорий для выпадающего меню.
        Смотрит на цифры в ncat0 и ncat1 и переводит их в слова.
        """
        used_ids = set()
        for task in self.tasks:
            if task.ncat0 and task.ncat0 != '0': 
                try: used_ids.add(int(task.ncat0))
                except: pass
            if task.ncat1 and task.ncat1 != '0': 
                try: used_ids.add(int(task.ncat1))
                except: pass
        
        # Переводим ID (1, 9, 15) в Названия (Crypto, OSINT, Steganography)
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

    def get_tasks_by_filters(self, category: str = None, level: str = None, 
                           ctf: str = None, tag: str = None,
                           has_writeup: bool = False, has_wsite: bool = False, 
                           has_attachment: bool = False) -> List[Task]:
        """Фильтрация задач"""
        filtered_tasks = self.tasks
        
        # 1. ФИЛЬТР ПО КАТЕГОРИИ (По двум полям ncat0 и ncat1)
        if category and category != "Все":
            target_id = None
            for cat_id, name in self.ID_TO_DISPLAY.items():
                if name == category:
                    target_id = str(cat_id)
                    break
            
            if target_id:
                filtered_tasks = [
                    task for task in filtered_tasks 
                    if str(task.ncat0) == target_id or str(task.ncat1) == target_id
                ]

        # 2. Уровень
        if level and level != "Все":
            if level == "Не указан":
                filtered_tasks = [task for task in filtered_tasks if not task.level or task.level.strip() == "" or task.level.lower() == "не указан"]
            else:
                filtered_tasks = [task for task in filtered_tasks if task.level and task.level.lower() == level.lower()]

        # 3. Турнир
        if ctf and ctf != "Все":
            filtered_tasks = [task for task in filtered_tasks if task.ctf == ctf]
            
        # 4. Тег
        if tag and tag != "Все":
            filtered_tasks = [task for task in filtered_tasks 
                            if tag in [task.tag1, task.tag2, task.tag3, task.tag4, task.tag5]]
        
        # 5. Чекбоксы
        if has_writeup:
            filtered_tasks = [t for t in filtered_tasks if t.writeup and t.writeup != "[]" and t.writeup != "None" and t.writeup.strip()]
        if has_wsite:
            filtered_tasks = [t for t in filtered_tasks if t.wsite and t.wsite != "[]" and t.wsite != "None" and t.wsite.strip()]
        if has_attachment:
            filtered_tasks = [t for t in filtered_tasks if t.attachment and t.attachment != "[]" and t.attachment != "None" and t.attachment.strip()]
        
        return filtered_tasks

    def search_tasks_with_filters(self, query: str = "", category: str = "Все", 
                                  has_writeup: bool = False, has_wsite: bool = False, 
                                  has_attachment: bool = False) -> List[Task]:
        base_filtered = self.get_tasks_by_filters(category=category, has_writeup=has_writeup, 
                                                has_wsite=has_wsite, has_attachment=has_attachment)
        if not query: return base_filtered
        query = query.lower()
        results = []
        for task in base_filtered:
            fields = [task.challenge, task.description, task.category, task.ctf, task.tag1, task.tag2, task.tag3, task.tag4, task.tag5]
            if any(field and query in field.lower() for field in fields):
                results.append(task)
        return results

    def get_task_statistics(self) -> Dict[str, Any]:
        stats = {
            'total_tasks': len(self.tasks),
            'categories_count': len(self.get_all_categories()),
            'levels_count': len(self.get_all_levels()),
            'tags_count': len(self.get_all_tags()),
            'categories': {},
            'levels': {}
        }
        for name in self.get_all_categories():
            stats['categories'][name] = len(self.get_tasks_by_filters(category=name))
        for level in self.get_all_levels():
            stats['levels'][level] = len(self.get_tasks_by_filters(level=level))
        return stats