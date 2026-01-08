import os
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

def create_test_images():
    test_dir = Path(__file__).parent / 'test_data'
    test_dir.mkdir(exist_ok=True)
    
    # Создаем изображение с английским текстом
    img1 = Image.new('RGB', (800, 200), color='white')
    d1 = ImageDraw.Draw(img1)
    
    try:
        font = ImageFont.truetype("arial.ttf", 40)
    except:
        font = ImageFont.load_default()
    
    d1.text((50, 50), "Visual Studio Code - Programming", fill='black', font=font)
    d1.text((50, 100), "GitHub Repository: ai-screen-monitor", fill='black', font=font)
    img1.save(test_dir / 'test_image_work.png')
    
    # Создаем изображение с русским текстом
    img2 = Image.new('RGB', (800, 200), color='white')
    d2 = ImageDraw.Draw(img2)
    
    d2.text((50, 50), "ВКонтакте - Социальная сеть", fill='black', font=font)
    d2.text((50, 100), "YouTube - Видео хостинг", fill='black', font=font)
    img2.save(test_dir / 'test_image_social.png')
    
    print(f"Создано 2 тестовых изображения в {test_dir}")

if __name__ == "__main__":
    create_test_images()
