import os
import re
import csv
import requests
from datetime import datetime
#                          ГЛОБАЛЬНЫЕ НАСТРОЙКИ ТУРНИРА
PLATFORM_TYPE = "rctf"  # "ctfd" или "rctf"
CTF_URL = "https://ctf.tjctf.org"  # Ссылка на турнир
API_TOKEN = ""  # Для архивного TJCTF оставляем пустым
# Настройки для твоего CSV и папок
TOURNAMENT_NAME = "TJCTF 2024"  
GITHUB_REPOSITORY = "TJCSC/tjctf-2024"  
REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}
CSV_HEADERS = [
    "key", "ctf", "nctf", "data", "category", "ncat0", "ncat1",
    "challenge", "description", "nc", "wsite", "writeup", "attachment",
    "level", "tag1", "tag2", "tag3", "tag4", "tag5"
]
CATEGORY_MAP = {
    'crypto': '1', 'cryptography': '1', 
    'misc': '2', 
    'pwn': '3', 'box pwn': '3', 'binary exploitation': '3',
    'rev': '4', 'reverse': '4', 'reversing': '4', 'reverse engineering': '4', 'reverse engineer': '4',
    'web': '5', 'web exploitation': '5',
    'forensics': '6', 'forensic': '6',
    'hardware': '7', 
    'intro': '8', 'sanity': '8', 'sanity check': '8',
    'osint': '9',
    'blockchain': '10',
    'programming': '11', 'ppc': '11',
    'digital assets': '12',
    'gambling': '13',
    'checkin': '14',
    'steganography': '15', 'stegano': '15', 'stego': '15'
}
def clean_name(name):
    return re.sub(r'[\\/*?:"<>|]', "", str(name)).strip()
def get_next_key(file_path):
    """Определяет сквозной ID (key) на основе последней строки рабочего CSV"""
    if not os.path.exists(file_path):
        return 1
    try:
        with open(file_path, mode="r", encoding="utf-8") as f:
            reader = csv.reader(f)
            rows = list(reader)
            if len(rows) <= 1:
                return 1
            return int(rows[-1][0]) + 1
    except Exception:
        return 1
def download_file(url, save_path, auth_headers=None):
    try:
        headers = {**REQUEST_HEADERS, **(auth_headers or {})}
        res = requests.get(url, headers=headers, stream=True, timeout=10)
        if res.status_code == 200:
            with open(save_path, 'wb') as f:
                for chunk in res.iter_content(chunk_size=8192):
                    f.write(chunk)
            return True
    except Exception:
        pass
    return False
def extract_links_from_text(text):
    """Парсинг внешних линков из описания задачи"""
    raw_links = re.findall(r'(https?://[^\s`\"\'\>\<\,\;\*]+)', text)
    cleaned_links = []
    for link in raw_links:
        if link.endswith(')'):
            link = link[:-1]
        exclude = ['ctftime.org', 'twitter.com', 'discord.gg', 'rules', 'scoreboard']
        if not any(k in link.lower() for k in exclude):
            cleaned_links.append(link)
    return list(set(cleaned_links))
def download_from_github_fallback(category, task_name, target_folder):
    if not GITHUB_REPOSITORY:
        return
    git_cat = category.lower().strip()
    git_task = task_name.lower().strip().replace(" ", "-")
    github_api_url = f"https://api.github.com/repos/{GITHUB_REPOSITORY}/contents"
    possible_paths = [f"{git_cat}/{git_task}", f"challenges/{git_cat}/{git_task}", f"{git_cat}/{task_name.strip()}"]
    for path in possible_paths:
        res = requests.get(f"{github_api_url}/{path}", headers=REQUEST_HEADERS)
        if res.status_code == 200:
            files_data = res.json()
            for item in files_data:
                if item["type"] == "file":
                    f_name = item["name"]
                    if f_name.lower() in ['readme.md', 'solution.md', 'writeup.md']:
                        continue
                    save_p = os.path.join(target_folder, clean_name(f_name))
                    download_file(item["download_url"], save_p)
            break
def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, "data")
    tournament_dir = os.path.join(data_dir, "files", clean_name(TOURNAMENT_NAME))
    csv_file_path = os.path.join(data_dir, "tasks_metadata.csv")
    os.makedirs(data_dir, exist_ok=True)
    write_header = not os.path.exists(csv_file_path)
    current_key = get_next_key(csv_file_path) 
    headers = {"Authorization": f"Bearer {API_TOKEN}"} if API_TOKEN else {}
    print(f"[*] Подключение к API {CTF_URL}...")
    res = requests.get(f"{CTF_URL}/api/v1/challs", headers={**REQUEST_HEADERS, **headers})
    if res.status_code != 200:
        print(f"[!] Ошибка доступа к API. Код: {res.status_code}")
        return
    challenges = res.json().get("data", [])
    print(f"[+] Найдено задач: {len(challenges)}. Начинаем генерацию по твоему рабочему стандарту...")
    parsed_rows = []
    current_date = datetime.now().strftime("%Y-%m-%d")
    for task_info in challenges:
        task_name = task_info.get("name", "Unnamed_Task")
        category = task_info.get("category", "Misc")
        description = task_info.get("description", "")
        platform_files = task_info.get("files", [])
        task_folder = os.path.join(tournament_dir, clean_name(category), clean_name(task_name))
        os.makedirs(task_folder, exist_ok=True)
        print(f"\n[*] Обработка задачи: {category} -> {task_name}")
        txt_desc_name = "d.txt"
        with open(os.path.join(task_folder, txt_desc_name), "w", encoding="utf-8") as f:
            f.write(description)
        files_failed = False
        for file_obj in platform_files:
            file_url = file_obj.get("url")
            file_name = file_obj.get("name", "file")
            if file_url.startswith("/"):
                file_url = f"{CTF_URL}{file_url}"
            save_p = os.path.join(task_folder, clean_name(file_name))
            if not download_file(file_url, save_p, auth_headers=headers):
                files_failed = True
        external_urls = extract_links_from_text(description)
        for url in external_urls:
            file_name = url.split('/')[-1].split('?')[0]
            if file_name and '.' in file_name and len(file_name) < 60:
                save_p = os.path.join(task_folder, clean_name(file_name))
                download_file(url, save_p)
        if files_failed or len(platform_files) == 0:
            download_from_github_fallback(category, task_name, task_folder)
        actual_files = []
        if os.path.exists(task_folder):
            for file_in_dir in os.listdir(task_folder):
                if file_in_dir != "d.txt" and os.path.isfile(os.path.join(task_folder, file_in_dir)):
                    actual_files.append(file_in_dir)
        if actual_files:
            attachment_str = "[" + ", ".join(f"'{f}'" for f in actual_files) + "]"
            print(f"    [+] Найденные файлы занесены в attachment: {attachment_str}")
        else:
            attachment_str = "[]"
        clean_cat_key = category.lower().strip()
        ncat0_val = CATEGORY_MAP.get(clean_cat_key, "2")
        csv_row = {
            "key": str(current_key),
            "ctf": TOURNAMENT_NAME,
            "nctf": "1",  
            "data": current_date,
            "category": category,
            "ncat0": ncat0_val,
            "ncat1": "0",
            "challenge": task_name,
            "description": "d.txt",
            "nc": "",
            "wsite": "[]",
            "writeup": "[]",
            "attachment": attachment_str, 
            "level": "",  
            "tag1": category,   
            "tag2": "",         
            "tag3": "",
            "tag4": "",
            "tag5": ""
        }     
        parsed_rows.append(csv_row)
        current_key += 1
    try:
        mode = "w" if write_header else "a"
        with open(csv_file_path, mode=mode, encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(
                f, 
                fieldnames=CSV_HEADERS, 
                quoting=csv.QUOTE_ALL, 
                lineterminator='\r\n'
            )
            if write_header:
                writer.writeheader()
            writer.writerows(parsed_rows)
        print(f"\n==================================================")
        print(f"✅ База данных успешно обновлена по твоему шаблону!")
        print(f"Файл: {csv_file_path}")
        print(f"Всего обработано новых тасков: {len(parsed_rows)}")
        print(f"==================================================")
    except Exception as e:
        print(f"❌ Ошибка записи базы данных в CSV: {e}")
if __name__ == "__main__":
    main()