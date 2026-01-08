import os
import sys
import subprocess
import tempfile
import platform
from pathlib import Path
from typing import Optional, Dict, Any
import logging

import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter, ImageDraw, ImageFont
import pytesseract

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OCRProcessor:
    
    def __init__(self, tesseract_path: Optional[str] = None):
        self.os_type = platform.system().lower()
        self.tesseract_path = self._find_tesseract(tesseract_path)
        self.tessdata_path = self._find_tessdata()
        
        pytesseract.pytesseract.tesseract_cmd = self.tesseract_path
        
        logger.info(f"OCRProcessor инициализирован для {self.os_type}")
        logger.info(f"Tesseract путь: {self.tesseract_path}")
        logger.info(f"Tessdata путь: {self.tessdata_path}")
        
        self.preprocessing_config = {
            'resize_factor': 1.5,
            'denoise_strength': 5,
            'contrast_factor': 1.3,
            'sharpness_factor': 1.1,
            'binary_threshold': 160
        }
    
    def _find_tesseract(self, custom_path: Optional[str] = None) -> str:

        if custom_path and Path(custom_path).exists():
            logger.info(f"Используется пользовательский путь к Tesseract: {custom_path}")
            return custom_path
        
        # Определяем возможные пути в зависимости от ОС
        possible_paths = []
        project_root = Path(__file__).parent.parent
        
        if self.os_type == 'windows':
            # Windows
            possible_paths = [
                project_root / 'vendor' / 'tesseract' / 'windows' / 'tesseract.exe',
                project_root / 'vendor' / 'tesseract' / 'windows' / 'bin' / 'tesseract.exe',
                Path("C:/Program Files/Tesseract-OCR/tesseract.exe"),
                Path("C:/Program Files (x86)/Tesseract-OCR/tesseract.exe"),
                Path(os.environ.get('ProgramFiles', '')) / 'Tesseract-OCR/tesseract.exe',
                Path(os.environ.get('ProgramFiles(x86)', '')) / 'Tesseract-OCR/tesseract.exe',
            ]
        elif self.os_type == 'linux':
            # Linux
            possible_paths = [
                project_root / 'vendor' / 'tesseract' / 'linux' / 'tesseract',
                project_root / 'vendor' / 'tesseract' / 'linux' / 'bin' / 'tesseract',
                Path("/usr/bin/tesseract"),
                Path("/usr/local/bin/tesseract"),
            ]
        else:
            # Другие ОС
            possible_paths = [
                Path("/usr/bin/tesseract"),
                Path("/usr/local/bin/tesseract"),
            ]
        
        for path in possible_paths:
            if path.exists():
                logger.info(f"Найден Tesseract: {path}")
                return str(path)
        
        try:
            if self.os_type == 'windows':
                result = subprocess.run(
                    ['where', 'tesseract'],
                    capture_output=True,
                    text=True,
                    shell=True,
                    encoding='utf-8',
                    errors='ignore'
                )
            else:
                result = subprocess.run(
                    ['which', 'tesseract'],
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='ignore'
                )
            
            if result.returncode == 0 and result.stdout.strip():
                tesseract_path = result.stdout.strip().split('\n')[0]
                logger.info(f"Найден Tesseract через which/where: {tesseract_path}")
                return tesseract_path
        except Exception as e:
            logger.warning(f"Ошибка при поиске Tesseract через which/where: {e}")
        
        error_msg = (
            "Tesseract не найден. Установите одним из способов:\n"
            "1. Скачайте Tesseract для Windows: https://github.com/UB-Mannheim/tesseract/wiki\n"
            "2. Установите в vendor/tesseract/windows/\n"
            "3. Или установите системный Tesseract"
        )
        logger.error(error_msg)
        raise EnvironmentError(error_msg)
    
    def _find_tessdata(self) -> Optional[Path]:
        tesseract_dir = Path(self.tesseract_path).parent
        project_root = Path(__file__).parent.parent
        
        possible_paths = []
        
        possible_paths.append(tesseract_dir / 'tessdata')
        possible_paths.append(tesseract_dir.parent / 'tessdata')
        
        if self.os_type == 'windows':
            possible_paths.append(project_root / 'vendor' / 'tesseract' / 'windows' / 'tessdata')
            possible_paths.append(project_root / 'vendor' / 'tesseract' / 'windows' / 'share' / 'tessdata')
        elif self.os_type == 'linux':
            possible_paths.append(project_root / 'vendor' / 'tesseract' / 'linux' / 'tessdata')
            possible_paths.append(project_root / 'vendor' / 'tesseract' / 'linux' / 'share' / 'tessdata')
        
        if self.os_type == 'windows':
            possible_paths.append(Path("C:/Program Files/Tesseract-OCR/tessdata"))
            possible_paths.append(Path("C:/Program Files (x86)/Tesseract-OCR/tessdata"))
        elif self.os_type == 'linux':
            possible_paths.append(Path("/usr/share/tesseract-ocr/tessdata"))
            possible_paths.append(Path("/usr/share/tesseract-ocr/5/tessdata"))
            possible_paths.append(Path("/usr/share/tesseract-ocr/4.00/tessdata"))
        
        for path in possible_paths:
            if path.exists():
                trained_files = list(path.glob('*.traineddata'))
                if trained_files:
                    logger.info(f"Найдена директория tessdata: {path}")
                    logger.info(f"Найдено языковых файлов: {len(trained_files)}")
                    for file in trained_files[:3]:
                        logger.info(f"  - {file.name}")
                    return path
        
        logger.warning("Директория tessdata не найдена или пуста.")
        return None
    
    def _prepare_command(self, image_path: str, lang: str = 'eng', output_path: Optional[str] = None) -> tuple:
        if output_path is None:
            with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as temp_output:
                output_path = temp_output.name
        
        cmd = [
            self.tesseract_path,
            image_path,
            output_path[:-4] if output_path.endswith('.txt') else output_path  # Без .txt
        ]
        
        if lang:
            cmd.extend(['-l', lang])
        
        cmd.extend([
            '--oem', '3',
            '--psm', '3',
            '-c', 'tessedit_create_txt=1'
        ])
        
        if self.tessdata_path:
            tessdata_dir = str(self.tessdata_path)
            cmd.extend(['--tessdata-dir', f'"{tessdata_dir}"'])
        
        return cmd, output_path
    
    def _run_tesseract_safe(self, image_path: str, lang: str = 'eng') -> Dict[str, Any]:
        
        try:
            cmd, output_path = self._prepare_command(image_path, lang)
            
            shell_needed = self.os_type == 'windows'
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore',
                timeout=30,
                shell=shell_needed,
                universal_newlines=True
            )
            
            text = ""
            if os.path.exists(output_path):
                with open(output_path, 'r', encoding='utf-8', errors='ignore') as f:
                    text = f.read()
                
                try:
                    os.unlink(output_path)
                except:
                    pass
            
            success = result.returncode == 0 and bool(text.strip())
            
            if result.stderr:
                error_lines = [line for line in result.stderr.split('\n') 
                             if 'Error' in line or 'Failed' in line or 'Warning' in line]
                if error_lines:
                    logger.warning(f"Tesseract предупреждения: {' '.join(error_lines[:3])}")
            
            return {
                'text': text.strip(),
                'success': success,
                'error': None if success else (result.stderr[:200] if result.stderr else 'Неизвестная ошибка'),
                'raw_stderr': result.stderr
            }
            
        except subprocess.TimeoutExpired:
            logger.error("Остановка при выполнении Tesseract")
            return {'text': '', 'success': False, 'error': 'Таймаут'}
        except Exception as e:
            logger.error(f"Ошибка запуска Tesseract: {e}")
            return {'text': '', 'success': False, 'error': str(e)}
    
    def extract_text(self, image_path: str, lang: str = '') -> Dict[str, Any]:
        try:
            if not Path(image_path).exists():
                return {
                    'success': False,
                    'error': f'Файл не найден: {image_path}',
                    'text': '',
                    'image_path': image_path
                }
            
            if not self.tesseract_path or not Path(self.tesseract_path).exists():
                return {
                    'success': False,
                    'error': 'Tesseract не найден',
                    'text': '',
                    'image_path': image_path
                }
            
            if not self.tessdata_path:
                logger.warning("Локальный tessdata не найден, пробуем системный Tesseract")
                result = self._run_tesseract_without_tessdata_dir(image_path, lang)
            else:
                result = self._run_tesseract_with_explicit_path(image_path, lang)

            if result['success']:
                text = result['text']
                words = [w for w in text.split() if w.strip()]

                confidence = self._estimate_confidence(text)
                
                return {
                    'text': text,
                    'raw_text': text,
                    'confidence': confidence,
                    'orientation': 0,
                    'script': self._detect_script(text),
                    'words_count': len(words),
                    'language': result.get('language', lang or 'eng'),
                    'bounding_boxes': {},
                    'success': True,
                    'image_path': image_path
                }
            else:
                return {
                    'text': '',
                    'raw_text': '',
                    'confidence': 0,
                    'orientation': 0,
                    'script': 'Unknown',
                    'words_count': 0,
                    'language': lang or 'eng',
                    'bounding_boxes': {},
                    'success': False,
                    'error': result['error'],
                    'image_path': image_path
                }
                
        except Exception as e:
            logger.error(f"Ошибка при извлечении текста из {image_path}: {e}")
            return {
                'text': '',
                'raw_text': '',
                'confidence': 0,
                'orientation': 0,
                'script': 'Unknown',
                'words_count': 0,
                'language': lang or 'eng',
                'bounding_boxes': {},
                'success': False,
                'error': str(e),
                'image_path': image_path
            }
    
    def _run_tesseract_with_explicit_path(self, image_path: str, lang: str) -> Dict[str, Any]:
        
        processed_path = self._preprocess_and_save(image_path)
        
        if not processed_path:
            return {'text': '', 'success': False, 'error': 'Ошибка предобработки'}

        test_cases = []
        
        if lang:
            test_cases.append((lang, lang))

        if lang != 'eng+rus':
            test_cases.append(('eng+rus', 'eng+rus'))
        if lang != 'eng':
            test_cases.append(('eng', 'eng'))
        if lang != 'rus':
            test_cases.append(('rus', 'rus'))
        if lang != '':
            test_cases.append(('', 'auto'))
        
        best_result = {'text': '', 'success': False, 'error': ''}
        
        for lang_flag, lang_name in test_cases:
            logger.info(f"Пробуем распознавание с языком: {lang_name}")
            result = self._run_tesseract_subprocess(processed_path, lang_flag)
            
            if result['success'] and result['text'].strip():
                best_result = result
                best_result['language'] = lang_name
                logger.info(f"Успешно распознано с языком {lang_name}: {len(result['text'])} символов")
                break
            else:
                logger.warning(f"Не удалось распознать с языком {lang_name}: {result.get('error')}")
        
        try:
            if processed_path != image_path and os.path.exists(processed_path):
                os.unlink(processed_path)
        except Exception as e:
            logger.warning(f"Не удалось удалить временный файл: {e}")
        
        return best_result

    def _run_tesseract_subprocess(self, image_path: str, lang: str) -> Dict[str, Any]:
        try:
            tessdata_dir = str(self.tessdata_path)
            tesseract_lang = lang if lang else 'eng'
            
            with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as temp_output:
                output_path = temp_output.name
            
            cmd = [
                self.tesseract_path,
                image_path,
                output_path[:-4],
                '-l', tesseract_lang,
                '--tessdata-dir', tessdata_dir,
                '--oem', '3',
                '--psm', '3'
            ]
            
            logger.debug(f"Выполняем команду: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore',
                timeout=30,
                shell=False
            )
            
            text = ""
            if os.path.exists(output_path):
                encodings = ['utf-8', 'cp1251', 'cp866', 'iso-8859-1', 'windows-1252']
                for encoding in encodings:
                    try:
                        with open(output_path, 'r', encoding=encoding, errors='ignore') as f:
                            text = f.read()
                            if text.strip():
                                logger.debug(f"Текст прочитан в кодировке {encoding}")
                                break
                    except Exception as e:
                        logger.debug(f"Ошибка при чтении с кодировкой {encoding}: {e}")
                        continue
            try:
                os.unlink(output_path)
            except:
                pass
            
            success = result.returncode == 0 and bool(text.strip())
            
            if result.stderr:
                error_lines = [line for line in result.stderr.split('\n') 
                             if 'Error' in line or 'Failed' in line]
                if error_lines:
                    logger.warning(f"Tesseract предупреждения: {' '.join(error_lines[:2])}")
            
            return {
                'text': text.strip(),
                'success': success,
                'error': None if success else (result.stderr[:200] if result.stderr else 'Пустой результат')
            }
            
        except subprocess.TimeoutExpired:
            logger.error("Таймаут при выполнении Tesseract")
            return {'text': '', 'success': False, 'error': 'Таймаут'}
        except Exception as e:
            logger.error(f"Ошибка запуска Tesseract: {e}")
            return {'text': '', 'success': False, 'error': str(e)}

    def extract_text(self, image_path: str, lang: str = '') -> Dict[str, Any]:
        try:
            if not Path(image_path).exists():
                return {
                    'success': False,
                    'error': f'Файл не найден: {image_path}',
                    'text': '',
                    'image_path': image_path,
                    'confidence': 0,
                    'words_count': 0,
                    'language': lang or 'eng',
                    'script': 'Unknown'
                }

            if not self.tesseract_path or not Path(self.tesseract_path).exists():
                return {
                    'success': False,
                    'error': 'Tesseract не найден',
                    'text': '',
                    'image_path': image_path,
                    'confidence': 0,
                    'words_count': 0,
                    'language': lang or 'eng',
                    'script': 'Unknown'
                }

            if not self.tessdata_path:
                logger.warning("Локальный tessdata не найден, пробуем системный Tesseract")
                result = self._run_tesseract_without_tessdata_dir(image_path, lang)
            else:
                result = self._run_tesseract_with_explicit_path(image_path, lang)

            if result['success']:
                text = result['text']
                words = [w for w in text.split() if w.strip()]
                
                confidence = self._estimate_confidence(text)
                script = self._detect_script(text)
                detected_lang = result.get('language', lang or 'eng')
                
                logger.info(f"Успешно извлечен текст из {Path(image_path).name}: "
                           f"{len(text)} символов, {len(words)} слов, язык: {detected_lang}")
                
                return {
                    'text': text,
                    'raw_text': text,
                    'confidence': confidence,
                    'orientation': 0,
                    'script': script,
                    'words_count': len(words),
                    'language': detected_lang,
                    'bounding_boxes': {},
                    'success': True,
                    'error': None,
                    'image_path': image_path
                }
            else:
                error_msg = result.get('error', 'Неизвестная ошибка')
                logger.error(f"Ошибка при извлечении текста из {Path(image_path).name}: {error_msg}")
                
                return {
                    'text': '',
                    'raw_text': '',
                    'confidence': 0,
                    'orientation': 0,
                    'script': 'Unknown',
                    'words_count': 0,
                    'language': lang or 'eng',
                    'bounding_boxes': {},
                    'success': False,
                    'error': error_msg,
                    'image_path': image_path
                }
                
        except Exception as e:
            logger.error(f"Критическая ошибка при извлечении текста из {image_path}: {e}")
            import traceback
            traceback.print_exc()
            
            return {
                'text': '',
                'raw_text': '',
                'confidence': 0,
                'orientation': 0,
                'script': 'Unknown',
                'words_count': 0,
                'language': lang or 'eng',
                'bounding_boxes': {},
                'success': False,
                'error': f"Критическая ошибка: {str(e)}",
                'image_path': image_path
            }

    
    def _run_tesseract_without_tessdata_dir(self, image_path: str, lang: str) -> Dict[str, Any]:
        try:
            image = Image.open(image_path)

            config = '--oem 3 --psm 3'

            tesseract_lang = lang if lang else 'eng'
            text = pytesseract.image_to_string(image, lang=tesseract_lang, config=config)
            
            return {
                'text': text.strip(),
                'success': bool(text.strip()),
                'error': None
            }
        except Exception as e:
            logger.error(f"Ошибка при использовании pytesseract: {e}")
            return {'text': '', 'success': False, 'error': str(e)}
    
    def _preprocess_and_save(self, image_path: str) -> str:
        try:
            image = Image.open(image_path)
            
            # Простая предобработка
            if image.mode == 'RGBA':
                background = Image.new('RGB', image.size, (255, 255, 255))
                background.paste(image, mask=image.split()[3])
                image = background
            elif image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Конвертируем в оттенки серого
            image = image.convert('L')
            
            # Улучшаем контраст
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.3)
            
            # Сохраняем во временный файл
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
                temp_path = temp_file.name
                image.save(temp_path, 'PNG', optimize=True)
            
            return temp_path
            
        except Exception as e:
            logger.error(f"Ошибка предобработки: {e}")
            return image_path
    
    def _estimate_confidence(self, text: str) -> float:
        if not text:
            return 0.0
        
        words = [w for w in text.split() if w.strip()]
        word_count = len(words)
        
        # Простая эвристика: больше слов = выше уверенность
        if word_count == 0:
            return 0.0
        elif word_count == 1:
            return 30.0
        elif word_count <= 3:
            return 50.0
        elif word_count <= 10:
            return 70.0
        else:
            return min(90.0, 70.0 + word_count)
    
    def _detect_script(self, text: str) -> str:
        if not text:
            return 'Unknown'
        
        cyrillic_count = sum(1 for c in text if '\u0400' <= c <= '\u04FF')
        latin_count = sum(1 for c in text if c.isalpha() and c.isascii())
        
        if cyrillic_count > latin_count:
            return 'Cyrillic'
        elif latin_count > 0:
            return 'Latin'
        else:
            return 'Unknown'
    
    def extract_text_from_bytes(self, image_bytes: bytes, lang: str = '') -> Dict[str, Any]:
        try:
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
                temp_path = temp_file.name
                temp_file.write(image_bytes)
            
            result = self.extract_text(temp_path, lang)
            
            try:
                os.unlink(temp_path)
            except:
                pass
            
            return result
            
        except Exception as e:
            logger.error(f"Ошибка при обработке байтов изображения: {e}")
            return {
                'text': '', 'success': False, 'error': str(e),
                'confidence': 0, 'words_count': 0
            }
    
    def test_tesseract_installation(self) -> Dict[str, Any]:
        logger.info("Тестирование установки Tesseract...")
        
        result = {
            'os_type': self.os_type,
            'tesseract_path': self.tesseract_path,
            'tessdata_path': str(self.tessdata_path) if self.tessdata_path else None,
            'tesseract_accessible': False,
            'version': 'Неизвестно',
            'error': None,
            'languages_available': []
        }
        
        try:
            cmd = [self.tesseract_path, '--version']
            
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore',
                timeout=5,
                shell=self.os_type == 'windows'
            )
            
            if process.returncode == 0 and process.stdout:
                result['tesseract_accessible'] = True
                version_line = process.stdout.split('\n')[0] if process.stdout else 'Unknown'
                result['version'] = version_line
                logger.info(f"Tesseract доступен: {version_line}")
                
                try:
                    cmd_lang = [self.tesseract_path, '--list-langs']
                    if self.tessdata_path:
                        env = os.environ.copy()
                        env['TESSDATA_PREFIX'] = str(self.tessdata_path.parent)
                        process_lang = subprocess.run(
                            cmd_lang,
                            env=env,
                            capture_output=True,
                            text=True,
                            encoding='utf-8',
                            errors='ignore',
                            timeout=5,
                            shell=self.os_type == 'windows'
                        )
                    else:
                        process_lang = subprocess.run(
                            cmd_lang,
                            capture_output=True,
                            text=True,
                            encoding='utf-8',
                            errors='ignore',
                            timeout=5,
                            shell=self.os_type == 'windows'
                        )
                    
                    if process_lang.returncode == 0 and process_lang.stdout:
                        lines = process_lang.stdout.strip().split('\n')
                        if len(lines) > 1:
                            languages = lines[1:]
                            result['languages_available'] = [lang.strip() for lang in languages if lang.strip()]
                            logger.info(f"Доступные языки: {', '.join(result['languages_available'])}")
                except Exception as e:
                    logger.warning(f"Не удалось получить список языков: {e}")
                    result['languages_available'] = ['eng', 'rus']
            else:
                result['error'] = process.stderr
                logger.error(f"Tesseract недоступен: {process.stderr}")
        
        except Exception as e:
            result['error'] = str(e)
            logger.error(f"Ошибка при тестировании Tesseract: {e}")
            result['languages_available'] = []
        
        return result


    def quick_test(self):
        from PIL import Image, ImageDraw, ImageFont

        img = Image.new('RGB', (400, 150), color='white')
        d = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("arial.ttf", 24)
        except:
            font = ImageFont.load_default()
            
        d.text((20, 30), "Hello World", fill='black', font=font)
        d.text((20, 70), "Test OCR 12345", fill='black', font=font)
            
        test_path = "quick_test.png"
        img.save(test_path)

        result = self._run_tesseract_subprocess(test_path, 'eng')

        if os.path.exists(test_path):
            os.unlink(test_path)

        return result

ocr = OCRProcessor()
result = ocr.quick_test()
print(f"Успех: {result['success']}")
print(f"Текст: {result['text']}")
