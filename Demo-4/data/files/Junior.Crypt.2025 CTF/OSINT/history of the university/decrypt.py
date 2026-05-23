# prepare_fake_encrypted.py
FAKE_IMAGE = "BSUIR_cont.jpg"
FAKE_ENCRYPTED_FILE = "encrypted2.dat"
KEY_BYTE = 0x5A

with open(FAKE_IMAGE, "rb") as f:
    data = f.read()

encrypted = bytes([b ^ KEY_BYTE for b in data])

with open(FAKE_ENCRYPTED_FILE, "wb") as f:
    f.write(encrypted)

print("Фейловое изображение зашифровано без пароля.")


