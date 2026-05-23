import wave

def encrypt_message_in_audio(audio_file_path, message, output_file_path):
    """
    Шифрует сообщение в аудиофайл с использованием стеганографии LSB (без соли, пароля и разделителя).

    Args:
        audio_file_path (str): Путь к аудиофайлу (.wav).
        message (str): Сообщение для шифрования.
        output_file_path (str): Путь для сохранения аудиофайла с зашифрованным сообщением.
    """

    # 1. Подготовка сообщения:
    # - Кодируем сообщение в байты.
    byte_message = message.encode('utf-8')

    # 2. Чтение аудиофайла:
    try:
        audio_file = wave.open(audio_file_path, mode='rb')
        params = audio_file.getparams()
        n_channels, samp_width, frame_rate, n_frames, comp_type, comp_name = params
        frames = audio_file.readframes(n_frames)
        audio_file.close()
    except wave.Error as e:
        raise ValueError(f"Ошибка при чтении аудиофайла: {e}")

    # 3. Проверка размера сообщения:
    # - Рассчитываем максимальный размер сообщения, которое можно вместить в аудиофайл.
    # - Проверяем, не превышает ли размер сообщения этот предел.
    max_bytes_to_hide = n_frames * n_channels * samp_width // 8
    if len(byte_message) > max_bytes_to_hide:
        raise ValueError(f"Сообщение слишком длинное для этого аудиофайла. Максимальный размер: {max_bytes_to_hide} байт.")

    # 4. Шифрование сообщения в аудиоданные:
    # - Преобразуем аудиоданные в список байтов.
    # - Заменяем наименее значащие биты (LSB) аудиоданных битами сообщения.
    modified_frames = bytearray(frames)
    for i, byte in enumerate(byte_message):
        for j in range(8):  # Проходим по битам каждого байта сообщения
            # Получаем i-й байт аудиоданных и j-й бит байта сообщения
            index = i * 8 + j
            if index < len(modified_frames):
                # Заменяем LSB аудиоданных битом сообщения
                modified_frames[index] = (modified_frames[index] & ~1) | ((byte >> (7 - j)) & 1)
            else:
                break  # Прекращаем, если достигли конца аудиоданных

    # 5. Запись измененных аудиоданных в новый файл:
    # - Записываем измененные аудиоданные в новый аудиофайл.
    try:
        new_audio_file = wave.open(output_file_path, 'wb')
        new_audio_file.setparams(params)
        new_audio_file.writeframes(bytes(modified_frames))
        new_audio_file.close()
    except wave.Error as e:
        raise ValueError(f"Ошибка при записи аудиофайла: {e}")

audio_file = 'Departure.wav'  # Замените на путь к вашему аудиофайлу
message = '     M     e     t     r    o     2     0     3    3     '
encrypted_audio_file = 'change.wav'

try:
    encrypt_message_in_audio(audio_file, message, encrypted_audio_file)
    print(f"Сообщение зашифровано в {encrypted_audio_file}")

except ValueError as e:
    print(f"Ошибка: {e}")