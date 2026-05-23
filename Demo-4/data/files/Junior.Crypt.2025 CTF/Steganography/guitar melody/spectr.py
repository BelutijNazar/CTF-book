import numpy as np
import scipy.io.wavfile as wav
from PIL import Image
import scipy.signal as signal

# Загружаем аудио
rate, data = wav.read("Departure.wav")
if data.ndim > 1:
    data = data[:, 0]  # используем только один канал если стерео

# Загружаем и обрабатываем изображение
img = Image.open("secret1.bmp").convert("L")  # Ч/Б
max_height = 400  # максимально допустимая высота спектра (Гц зависит от частоты дискретизации)
duration_sec = len(data) / rate
img_width = int(duration_sec * 100)  # 100 столбцов в секунду (примерно)

# Масштабируем изображение
img = img.resize((img_width, max_height))
img_np = np.array(img)
img_np = 255 - img_np  # инвертируем цвета: белый фон, чёрные линии = энергия

# Параметры STFT
nperseg = 1024
hop = 512
frequencies, times, Zxx = signal.stft(data, rate, nperseg=nperseg, noverlap=nperseg - hop)

# Встраиваем изображение в высокие частоты спектра
spec = np.copy(Zxx)
img_resized = img_np / 255.0

img_rows = img_resized.shape[0]
img_cols = min(img_resized.shape[1], spec.shape[1])
spec[-img_rows:, :img_cols] += img_resized[:, :img_cols] * np.max(np.abs(Zxx)) * 0.5

# Обратное преобразование
_, modified_data = signal.istft(spec, rate, nperseg=nperseg, noverlap=nperseg - hop)
modified_data = np.real(modified_data).astype(np.int16)

# Сохраняем результат
wav.write("Depart.wav", rate, modified_data)
