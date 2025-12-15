from PIL import Image

# Пути к входным и выходному файлам
image1_path = "BSUIR.jpg"
image2_path = "key2.jpg"
output_path = "cont.jpg" # Промежуточный результат XOR
final_output_path = "BSUIR_cont.jpg" # Окончательный, неинвертированный результат

# Загрузка и приведение к RGB
img1 = Image.open(image1_path).convert("RGB")
img2 = Image.open(image2_path).convert("RGB")

# Убедимся, что размеры совпадают
if img1.size != img2.size:
    raise ValueError("Размеры изображений не совпадают!")

# Получаем пиксели
pixels1 = img1.load()
pixels2 = img2.load()

# Создаем новое изображение для XOR
result_img_xor = Image.new("RGB", img1.size)
result_pixels_xor = result_img_xor.load()

# XOR по каждому цветовому каналу
for y in range(img1.height):
    for x in range(img1.width):
        r1, g1, b1 = pixels1[x, y]
        r2, g2, b2 = pixels2[x, y]
        result_pixels_xor[x, y] = (
            r1 ^ r2,
            g1 ^ g2,
            b1 ^ b2
        )

# Сохраняем промежуточный результат (опционально, для отладки)
result_img_xor.save(output_path)
print("XOR изображений завершён. Сохранено в", output_path)


# --- Этап 2: Инвертируем, если результат XOR инвертирован ---
# Открываем только что созданное XOR-изображение (cont.bmp)
img_to_fix = Image.open(output_path).convert("RGB")
pixels_to_fix = img_to_fix.load()

final_result_img = Image.new("RGB", img_to_fix.size)
final_result_pixels = final_result_img.load()

for y in range(img_to_fix.height):
    for x in range(img_to_fix.width):
        r, g, b = pixels_to_fix[x, y]
        # Инвертируем каждый канал: 255 - значение
        final_result_pixels[x, y] = (
            255 - r,
            255 - g,
            255 - b
        )

final_result_img.save(final_output_path)
print("Изображение инвертировано обратно до нормальных цветов и сохранено в", final_output_path)