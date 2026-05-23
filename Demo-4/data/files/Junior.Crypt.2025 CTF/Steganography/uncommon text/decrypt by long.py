from docx import Document

# Сопоставление визуально схожих русских и английских букв
visually_similar_letters = {
    'A': ('А', 'A'), 'a': ('а', 'a'),
    'B': ('В', 'B'),
    'C': ('С', 'C'), 'c': ('с', 'c'),
    'E': ('Е', 'E'), 'e': ('е', 'e'),
    'H': ('Н', 'H'),
    'K': ('К', 'K'),
    'M': ('М', 'M'),
    'O': ('О', 'O'), 'o': ('о', 'o'),
    'P': ('Р', 'P'), 'p': ('р', 'p'),
    'T': ('Т', 'T'),
    'X': ('Х', 'X'), 'x': ('х', 'x'),
    'Y': ('У', 'Y'), 'y': ('у', 'y'),
}

# Буква -> бит
char_to_bit = {}
for _, (ru, en) in visually_similar_letters.items():
    char_to_bit[ru] = '0'
    char_to_bit[en] = '1'


def extract_flag_from_docx(docx_path, flag_length_bits):
    doc = Document(docx_path)
    binary_string = ''

    for para in doc.paragraphs:
        for char in para.text:
            if char in char_to_bit:
                binary_string += char_to_bit[char]
                if len(binary_string) >= flag_length_bits:
                    break
        if len(binary_string) >= flag_length_bits:
            break

    if len(binary_string) < flag_length_bits:
        print(f"[!] Недостаточно закодированных символов: нужно {flag_length_bits}, найдено {len(binary_string)}")
        return None

    flag_bits = binary_string[:flag_length_bits]
    flag_bytes = [flag_bits[i:i + 8] for i in range(0, len(flag_bits), 8)]

    try:
        return ''.join(chr(int(b, 2)) for b in flag_bytes)
    except ValueError:
        print("[!] Ошибка при декодировании.")
        return None


# === Пример использования ===
if __name__ == "__main__":
    file_path = input("Введите путь к docx файлу: ").strip()
    flag_length = int(input("Введите длину флага в символах: ").strip()) * 8  # 1 символ = 8 бит
    flag = extract_flag_from_docx(file_path, flag_length)

    if flag:
        print(f"[+] Извлечённый флаг: {flag}")
    else:
        print("[!] Флаг не найден или декодировать не удалось.")
