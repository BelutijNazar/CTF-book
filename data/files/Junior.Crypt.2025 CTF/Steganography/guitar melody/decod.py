import wave
def extract_message_from_audio(audio_file_path, message_length):
    """
    Извлекает зашифрованное сообщение из аудиофайла, используя стеганографию LSB.

    Args:
        audio_file_path (str): Путь к аудиофайлу (.wav).
        message_length (int): Длина сообщения в символах.  **Важно: Вы должны знать длину сообщения!**

    Returns:
        str: Извлеченное сообщение.
    """

    # 1. Чтение аудиофайла:
    try:
        audio_file = wave.open(audio_file_path, mode='rb')
        params = audio_file.getparams()
        n_channels, samp_width, frame_rate, n_frames, comp_type, comp_name = params
        frames = audio_file.readframes(n_frames)
        audio_file.close()
    except wave.Error as e:
        raise ValueError(f"Ошибка при чтении аудиофайла: {e}")

    # 2. Извлечение битов сообщения из аудиоданных:
    # - Извлекаем LSB из каждого байта аудиоданных.
    # - Собираем биты в байты сообщения.
    binary_message = ""
    for byte in frames:
        binary_message += str(byte & 1)

    # 3. Преобразование битов в байты:
    # - Преобразуем битовую строку в байтовую строку.
    byte_message = bytearray()
    for i in range(0, len(binary_message), 8):
        byte = binary_message[i:i+8]
        if len(byte) == 8:
            byte_message.append(int(byte, 2))

    # 4. Извлечение сообщения заданной длины:
    # - Извлекаем первые `message_length` байт из байтового сообщения.
    try:
        message = byte_message[:message_length].decode('utf-8')
        return message

    except UnicodeDecodeError:
        return None  # Ошибка декодирования

message = ''
encrypted_audio_file = 'change.wav'

try:
    message_length = len(message)  # Длина сообщения в символах
    extracted_message = extract_message_from_audio(encrypted_audio_file, message_length)
    if extracted_message:
        print(f"Извлеченное сообщение: {extracted_message}")
    else:
        print("Сообщение не найдено или ошибка декодирования.")

except ValueError as e:
    print(f"Ошибка: {e}")