from PIL import Image

# Пути к XOR-изображению и одному из оригиналов
xor_image_path = "GRSU_cont.jpg"       # Результат XOR двух картинок
known_image_path = "GRSU.jpg"         # Один из оригиналов (image1 или image2)
output_path = "recovered_image.jpg"     # Куда сохранить восстановленное изображение

# Загрузка и приведение к RGB
xor_img = Image.open(xor_image_path).convert("RGB")
known_img = Image.open(known_image_path).convert("RGB")

# Проверка размеров
if xor_img.size != known_img.size:
    raise ValueError("Размеры изображений не совпадают!")

# Получение пикселей
xor_pixels = xor_img.load()
known_pixels = known_img.load()

# Создание нового изображения
recovered_img = Image.new("RGB", xor_img.size)
recovered_pixels = recovered_img.load()

# Обратный XOR: recovered = xor ^ known
for y in range(xor_img.height):
    for x in range(xor_img.width):
        xr, xg, xb = xor_pixels[x, y]
        kr, kg, kb = known_pixels[x, y]
        recovered_pixels[x, y] = (
            xr ^ kr,
            xg ^ kg,
            xb ^ kb
        )

# Сохранение результата
recovered_img.save(output_path)
print("Изображение восстановлено и сохранено как:", output_path)
