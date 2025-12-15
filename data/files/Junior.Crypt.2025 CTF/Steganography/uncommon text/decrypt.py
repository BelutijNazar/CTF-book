from docx import Document

# Русско-английские пары визуально одинаковых букв
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

char_to_bit = {}
for _, (ru, en) in visually_similar_letters.items():
    char_to_bit[ru] = '0'
    char_to_bit[en] = '1'


def decode_until_terminator(docx_path, terminator='}'):
    doc = Document(docx_path)
    binary_data = ''

    for para in doc.paragraphs:
        for char in para.text:
            if char in char_to_bit:
                binary_data += char_to_bit[char]

    flag = ''
    for i in range(0, len(binary_data), 8):
        byte = binary_data[i:i + 8]
        if len(byte) < 8:
            break
        char = chr(int(byte, 2))
        flag += char
        if char == terminator:  # конец флага
            break

    if terminator in flag:
        return flag
    else:
        print("[!] Конец флага (терминатор) не найден.")
        return None


# === Пример использования ===
if __name__ == "__main__":
    file_path = input("Введите путь к docx файлу: ").strip()
    flag = decode_until_terminator(file_path, terminator='}')

    if flag:
        print(f"[+] Извлечённый флаг: {flag}")
    else:
        print("[!] Флаг не найден или некорректно извлечён.")
