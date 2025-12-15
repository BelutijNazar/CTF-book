import os
from hashlib import sha256
from tkinter import Tk, simpledialog, messagebox

# Настройки
TRUE_IMAGE = "GRSU_cont.jpg"
FAKE_IMAGE = "BSUIR_cont.jpg"
ENCRYPTED_FILE = "encrypted1.dat"               # Шифруется с паролем
FAKE_ENCRYPTED_FILE = "encrypted2.dat"     # Шифруется без пароля
OUTPUT_IMAGE = "GRSU.jpg"
FAKE_OUTPUT_IMAGE = "BSUIR.jpg"

PASSWORD_HASH = sha256(b"22021940").hexdigest()  # Установи свой пароль здесь
NO_PASSWORD_KEY = 0x5A  # Фиксированный ключ для "фейковой" картинки

def xor_with_key(data: bytes, key: bytes) -> bytes:
    key_cycle = (key * (len(data) // len(key) + 1))[:len(data)]
    return bytes([a ^ b for a, b in zip(data, key_cycle)])

def xor_with_byte(data: bytes, byte_key: int) -> bytes:
    return bytes([b ^ byte_key for b in data])

def decrypt_file_with_password(password: str):
    key = sha256(password.encode()).digest()
    with open(ENCRYPTED_FILE, "rb") as f:
        encrypted = f.read()
    return xor_with_key(encrypted, key)

def decrypt_file_no_password():
    with open(FAKE_ENCRYPTED_FILE, "rb") as f:
        encrypted = f.read()
    return xor_with_byte(encrypted, NO_PASSWORD_KEY)

def main():
    Tk().withdraw()
    pwd = simpledialog.askstring("Пароль", "Введите пароль:", show='*')
    if not pwd:
        return

    if sha256(pwd.encode()).hexdigest() == PASSWORD_HASH:
        try:
            data = decrypt_file_with_password(pwd)
            with open(OUTPUT_IMAGE, "wb") as f:
                f.write(data)
            os.startfile(OUTPUT_IMAGE)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось расшифровать изображение: {e}")
    else:
        try:
            data = decrypt_file_no_password()
            with open(FAKE_OUTPUT_IMAGE, "wb") as f:
                f.write(data)
            os.startfile(FAKE_OUTPUT_IMAGE)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось открыть фейловое изображение: {e}")

if __name__ == "__main__":
    main()
