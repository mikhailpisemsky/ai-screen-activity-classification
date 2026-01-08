import os
import sys
import logging
from pathlib import Path
import json
import time
from typing import Dict, List, Any
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from ocr_processor import OCRProcessor
    from activity_classifier import ActivityClassifier, ActivityCategory
    from hybrid_classifier import HybridActivityClassifier
    from llm.transformer_classifer import TransformerClassifier
except ImportError as e:
    print(f"Ошибка импорта модулей: {e}")
    print("Установите зависимости: pip install -r requirements.txt")
    print("Если используете гибридную модель, убедитесь что обученная модель доступна в llm/trained_model/")
    sys.exit(1)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def test_tesseract_installation():
    print("Тестирование установки Tesseract")
    
    try:
        ocr = OCRProcessor()
        test_result = ocr.test_tesseract_installation()
        
        print(f"ОС: {test_result['os_type']}")
        print(f"Путь к Tesseract: {test_result['tesseract_path']}")
        print(f"Путь к Tessdata: {test_result['tessdata_path']}")
        print(f"Tesseract доступен: {'✓' if test_result['tesseract_accessible'] else '✗'}")
        
        if test_result['tesseract_accessible']:
            print(f"Версия: {test_result.get('version', 'Неизвестно')}")
            if test_result.get('languages_available'):
                print(f"Доступные языки: {', '.join(test_result['languages_available'])}")
            else:
                print("Доступные языки: Не обнаружены")
        
        if test_result.get('error'):
            print(f"Ошибка: {test_result['error']}")
        
        return test_result['tesseract_accessible']
        
    except Exception as e:
        print(f"✗ Ошибка при тестировании Tesseract: {e}")
        return False

def test_text_classification():
    print("Тестирование классификации текста (ключевые слова)")
    
    classifier = ActivityClassifier()
    results = []
    
    test_cases = [
        {
            'name': 'Разработка',
            'text': 'Visual Studio Code Python GitHub',
            'expected': ActivityCategory.WORK
        },
        {
            'name': 'Офисные приложения',
            'text': 'Microsoft Word Excel PowerPoint',
            'expected': ActivityCategory.WORK
        },
        {
            'name': 'Деловая коммуникация',
            'text': 'Slack Jira Outlook email',
            'expected': ActivityCategory.WORK
        },
        {
            'name': 'Социальные сети',
            'text': 'Facebook YouTube Instagram',
            'expected': ActivityCategory.NON_WORK
        },
        {
            'name': 'Игры',
            'text': 'Steam Counter-Strike game',
            'expected': ActivityCategory.NON_WORK
        },
        {
            'name': 'Вредоносные сайты',
            'text': 'rutracker crack VPN',
            'expected': ActivityCategory.HARMFUL
        },
        {
            'name': 'Нейтральная активность',
            'text': 'File Explorer Desktop Settings',
            'expected': ActivityCategory.NEUTRAL
        }
    ]
    
    for test in test_cases:
        print(f"\n{test['name']}:")
        print(f"  Текст: {test['text']}")
        
        try:
            result = classifier.classify(test['text'])
            passed = result.category == test['expected']
            status = "✓" if passed else "✗"
            
            print(f"  Ожидалось: {test['expected'].value}")
            print(f"  Получено: {result.category.value}")
            print(f"  Уверенность: {result.confidence:.1%}")
            print(f"  Статус: {status}")
            
            if result.matched_keywords:
                print(f"  Ключевые слова: {', '.join(result.matched_keywords[:3])}")
            
            results.append({
                'test': test['name'],
                'passed': passed,
                'confidence': result.confidence,
                'category': result.category.value
            })
        except Exception as e:
            print(f"  Ошибка: {e}")
            results.append({
                'test': test['name'],
                'passed': False,
                'error': str(e)
            })

    passed_count = sum(1 for r in results if r['passed'])
    total = len(results)

    print(f"Результат: {passed_count}/{total} пройдено ({passed_count/total:.1%})")
    
    return passed_count == total

def test_transformer_classification():
    print("Тестирование трансформерной классификации")
    
    try:
        transformer_path = Path(__file__).parent / 'llm' / 'trained_model'
        
        if not transformer_path.exists():
            print("⚠ Модель трансформера не найдена. Пропускаем тест.")
            print("  Путь: {}".format(transformer_path))
            return True
        
        classifier = TransformerClassifier()
        results = []
        
        test_cases = [
            {
                'name': 'Разработка',
                'text': 'Visual Studio Code Python GitHub',
                'expected': 'work'
            },
            {
                'name': 'Социальные сети',
                'text': 'Facebook YouTube Instagram',
                'expected': 'non_work'
            },
            {
                'name': 'Вредоносные сайты',
                'text': 'rutracker crack VPN',
                'expected': 'harmful'
            },
            {
                'name': 'Нейтральная активность',
                'text': 'File Explorer Desktop Settings',
                'expected': 'neutral'
            },
            {
                'name': 'Смешанный текст 1',
                'text': 'mail. Desktop google.com Панель управления',
                'expected': 'neutral'
            },
            {
                'name': 'Смешанный текст 2',
                'text': 'piracy bitcoin .torrent',
                'expected': 'harmful'
            },
            {
                'name': 'Смешанный текст 3',
                'text': 'System Monitor новая вкладка browser',
                'expected': 'neutral'
            },
            {
                'name': 'Смешанный текст 4',
                'text': 'corporate, .pptx, merge and issue',
                'expected': 'work'
            }
        ]
        
        for test in test_cases:
            print(f"\n{test['name']}:")
            print(f"  Текст: {test['text'][:50]}...")
            
            try:
                result = classifier.classify(test['text'])
                passed = result.category == test['expected']
                status = "✓" if passed else "✗"
                
                print(f"  Ожидалось: {test['expected']}")
                print(f"  Получено: {result.category}")
                print(f"  Уверенность: {result.confidence:.1%}")
                print(f"  Статус: {status}")
                
                results.append({
                    'test': test['name'],
                    'passed': passed,
                    'confidence': result.confidence,
                    'category': result.category
                })
            except Exception as e:
                print(f"  Ошибка: {e}")
                results.append({
                    'test': test['name'],
                    'passed': False,
                    'error': str(e)
                })

        passed_count = sum(1 for r in results if r['passed'])
        total = len(results)

        print(f"Результат: {passed_count}/{total} пройдено ({passed_count/total:.1%})")
        
        return passed_count / total > 0.5
        
    except Exception as e:
        print(f"✗ Ошибка при тестировании трансформера: {e}")
        return False

def test_hybrid_classification():
    print("Тестирование гибридной классификации")
    
    try:
        classifier = HybridActivityClassifier()
        results = []
        
        test_cases = [
            {
                'name': 'Разработка',
                'text': 'Visual Studio Code Python GitHub',
                'expected': ActivityCategory.WORK
            },
            {
                'name': 'Социальные сети',
                'text': 'Facebook YouTube Instagram',
                'expected': ActivityCategory.NON_WORK
            },
            {
                'name': 'Вредоносные сайты',
                'text': 'rutracker crack VPN',
                'expected': ActivityCategory.HARMFUL
            },
            {
                'name': 'Нейтральная активность',
                'text': 'File Explorer Desktop Settings',
                'expected': ActivityCategory.NEUTRAL
            },
            {
                'name': 'Сложный случай 1',
                'text': 'Открыт Visual Studio Code и параллельно YouTube',
                'expected': ActivityCategory.NON_WORK
            },
            {
                'name': 'Сложный случай 2',
                'text': 'Проверяю почту в Gmail и работаю в Excel',
                'expected': ActivityCategory.WORK
            }
        ]
        
        for test in test_cases:
            print(f"\n{test['name']}:")
            print(f"  Текст: {test['text'][:50]}...")
            
            try:
                result = classifier.classify(test['text'])
                passed = result.category == test['expected']
                status = "✓" if passed else "✗"
                
                print(f"  Ожидалось: {test['expected'].value}")
                print(f"  Получено: {result.category.value}")
                print(f"  Уверенность: {result.confidence:.1%}")
                print(f"  Тип классификации: {getattr(result, 'classifier_type', 'unknown')}")
                print(f"  Статус: {status}")
                
                if hasattr(result, 'transformer_confidence'):
                    print(f"  Уверенность трансформера: {result.transformer_confidence:.1%}")
                if hasattr(result, 'keyword_confidence'):
                    print(f"  Уверенность ключевых слов: {result.keyword_confidence:.1%}")
                
                results.append({
                    'test': test['name'],
                    'passed': passed,
                    'confidence': result.confidence,
                    'category': result.category.value,
                    'classifier_type': getattr(result, 'classifier_type', 'unknown')
                })
            except Exception as e:
                print(f"  Ошибка: {e}")
                results.append({
                    'test': test['name'],
                    'passed': False,
                    'error': str(e)
                })

        passed_count = sum(1 for r in results if r['passed'])
        total = len(results)

        print(f"Результат: {passed_count}/{total} пройдено ({passed_count/total:.1%})")

        classifier_types = {}
        for r in results:
            if r.get('classifier_type'):
                classifier_types[r['classifier_type']] = classifier_types.get(r['classifier_type'], 0) + 1
        
        if classifier_types:
            print("Использованные типы классификации:")
            for ctype, count in classifier_types.items():
                print(f"  {ctype}: {count}")
        
        return passed_count / total > 0.5
        
    except Exception as e:
        print(f"✗ Ошибка при тестировании гибридного классификатора: {e}")
        return False

def test_simple_ocr():
    print("Тестирование ocr_processor")
    
    test_data_dir = Path(__file__).parent / 'test_data'
    test_images = list(test_data_dir.glob('*.png')) + list(test_data_dir.glob('*.jpg'))
    
    if not test_images:
        print("Тестовые изображения не найдены в test_data/")
        print("Создайте простые изображения с английским текстом")
        return False
    
    print(f"Найдено изображений: {len(test_images)}")
    
    try:
        ocr = OCRProcessor()
    except Exception as e:
        print(f"✗ Не удалось инициализировать OCRProcessor: {e}")
        return False
    
    success_count = 0
    
    for image_path in test_images[:2]:
        print(f"\nОбработка: {image_path.name}")
        
        try:
            results = []
            
            # 1. Без указания языка (автоопределение)
            result1 = ocr.extract_text(str(image_path), lang='')
            results.append(('Авто', result1))
            
            # 2. Только английский
            if result1.get('success') and result1.get('text', '').strip():
                result2 = ocr.extract_text(str(image_path), lang='eng')
                results.append(('ENG', result2))
            
            # 3. Только русский
            result3 = ocr.extract_text(str(image_path), lang='rus')
            results.append(('RUS', result3))
            
            # 4. Английский + русский
            result4 = ocr.extract_text(str(image_path), lang='eng+rus')
            results.append(('ENG+RUS', result4))
            
            # Выбираем лучший результат
            best_result = None
            for lang_name, result in results:
                if result.get('success') and result.get('text', '').strip():
                    if not best_result or len(result['text']) > len(best_result['text']):
                        best_result = result
                        best_lang = lang_name
            
            if best_result:
                text = best_result['text']
                confidence = best_result['confidence']
                print(f"  ✓ Успешно ({best_lang}): {len(text)} символов")
                print(f"    Уверенность: {confidence:.1f}%")
                
                if text:
                    preview = text[:100] + "..." if len(text) > 100 else text
                    print(f"    Текст: {preview}")
                    success_count += 1
                else:
                    print(f"  ✗ Текст пустой")
            else:
                print(f"  ✗ Не удалось извлечь текст")
                for lang_name, result in results:
                    status = "✓" if result.get('success') else "✗"
                    text_len = len(result.get('text', ''))
                    print(f"    {lang_name}: {status} ({text_len} символов)")
                
        except Exception as e:
            print(f"  ✗ Ошибка: {e}")
            import traceback
            traceback.print_exc()

    print(f"Результат: {success_count}/{min(2, len(test_images))} успешно")
    
    return success_count > 0

def test_ocr_integration():
    print("Тестирование полного пайплайна OCR + Гибридная классификация")
    
    test_data_dir = Path(__file__).parent / 'test_data'
    test_images = list(test_data_dir.glob('*.png')) + list(test_data_dir.glob('*.jpg'))
    
    if not test_images:
        print("Тестовые изображения не найдены в test_data/")
        return False
    
    try:
        ocr = OCRProcessor()
        classifier = HybridActivityClassifier()
    except Exception as e:
        print(f"✗ Не удалось инициализировать: {e}")
        return False
    
    results = []
    
    for image_path in test_images[:2]:
        print(f"\nОбработка: {image_path.name}")
        
        try:
            ocr_result = ocr.extract_text(str(image_path), lang='eng+rus')
            
            if not ocr_result['success']:
                print(f"  ✗ Ошибка OCR: {ocr_result.get('error', 'Неизвестная ошибка')}")
                results.append({
                    'image': image_path.name,
                    'success': False,
                    'error': 'OCR failed'
                })
                continue
            
            text = ocr_result['text']
            confidence = ocr_result['confidence']
            
            print(f"  ✓ OCR успешен: {len(text)} символов, уверенность: {confidence:.1f}%")

            classification = classifier.classify(text, ocr_confidence=confidence/100.0)
            
            print(f"  Категория: {classification.category.value}")
            print(f"  Уверенность классификации: {classification.confidence:.1%}")
            print(f"  Тип классификации: {getattr(classification, 'classifier_type', 'unknown')}")
            
            if hasattr(classification, 'transformer_confidence'):
                print(f"  Уверенность трансформера: {classification.transformer_confidence:.1%}")
            
            results.append({
                'image': image_path.name,
                'success': True,
                'text_length': len(text),
                'ocr_confidence': confidence,
                'category': classification.category.value,
                'classification_confidence': classification.confidence,
                'classifier_type': getattr(classification, 'classifier_type', 'unknown')
            })
            
        except Exception as e:
            print(f"  ✗ Ошибка: {e}")
            results.append({
                'image': image_path.name,
                'success': False,
                'error': str(e)
            })
    
    success_count = sum(1 for r in results if r['success'])
    total = len(results)
    
    print(f"Результат: {success_count}/{total} успешно обработано")
    
    if success_count > 0:
        print("Категории:")
        for r in results:
            if r['success']:
                print(f"  {r['image']}: {r['category']} ({r['classification_confidence']:.1%})")
    
    return success_count > 0

def test_performance():
    print("Тестирование производительности")
    
    try:
        classifier = ActivityClassifier()
    except Exception as e:
        print(f"✗ Не удалось инициализировать классификатор ключевых слов: {e}")
        return False
    
    test_texts = [
        "Visual Studio Code Python JavaScript",
        "Facebook Instagram YouTube",
        "Microsoft Word Excel PowerPoint",
        "File Explorer Settings Desktop"
    ]
    
    times = []
    for text in test_texts:
        start_time = time.perf_counter()
        for _ in range(100):
            classifier.classify(text)
        end_time = time.perf_counter()
        times.append((end_time - start_time) / 100)
    
    avg_time = sum(times) / len(times)
    
    print("Классификатор ключевых слов:")
    print(f"  Среднее время: {avg_time*1000:.2f} мс")
    print(f"  Максимальная скорость: {1/avg_time:.0f} запросов/сек")
    
    if avg_time < 0.01:
        print("  Производительность: ✓ ОТЛИЧНАЯ")
    elif avg_time < 0.1:
        print("  Производительность: ✓ ХОРОШАЯ")
    else:
        print("  Производительность: ⚠ УДОВЛЕТВОРИТЕЛЬНАЯ")
    
    try:
        hybrid_classifier = HybridActivityClassifier()
        print("\nГибридный классификатор:")
        
        hybrid_times = []
        for text in test_texts[:2]:  # Меньше текстов для гибридного теста
            start_time = time.perf_counter()
            result = hybrid_classifier.classify(text)
            end_time = time.perf_counter()
            hybrid_times.append(end_time - start_time)
            
            print(f"  '{text[:30]}...' -> {result.category.value} ({result.confidence:.1%})")
        
        avg_hybrid_time = sum(hybrid_times) / len(hybrid_times)
        print(f"  Среднее время: {avg_hybrid_time*1000:.2f} мс")
        
    except Exception as e:
        print(f"  ⚠ Гибридный классификатор недоступен: {e}")
    
    return avg_time < 0.1

def save_test_results(results: Dict, filename: str):
    test_results_dir = Path(__file__).parent / 'test_results'
    test_results_dir.mkdir(exist_ok=True)
    
    filepath = test_results_dir / filename
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"Результаты сохранены в: {filepath}")

def main():
    print("Тестирование модели классификации экранной активности")
    
    all_results = {
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'architecture': 'hybrid',
        'tests': {}
    }
    
    tesseract_ok = test_tesseract_installation()
    all_results['tests']['tesseract_installation'] = {
        'passed': tesseract_ok,
        'required': True
    }
    
    if not tesseract_ok:
        print("\n⚠ Tesseract не установлен или недоступен")
        print("Для продолжения тестов без ocr_processor нажмите Enter...")
        input()
    
    classification_ok = test_text_classification()
    all_results['tests']['text_classification'] = {
        'passed': classification_ok,
        'required': True
    }
    
    transformer_ok = test_transformer_classification()
    all_results['tests']['transformer_classification'] = {
        'passed': transformer_ok,
        'required': False
    }
    
    hybrid_ok = test_hybrid_classification()
    all_results['tests']['hybrid_classification'] = {
        'passed': hybrid_ok,
        'required': True
    }
    
    if tesseract_ok:
        ocr_ok = test_simple_ocr()
        all_results['tests']['ocr'] = {
            'passed': ocr_ok,
            'required': False
        }
        
        pipeline_ok = test_ocr_integration()
        all_results['tests']['ocr_integration'] = {
            'passed': pipeline_ok,
            'required': False
        }
    
    performance_ok = test_performance()
    all_results['tests']['performance'] = {
        'passed': performance_ok,
        'required': True
    }
    
    print("Итоговые результаты тестирования")
    
    required_passed = 0
    required_total = 0
    
    for test_name, test_result in all_results['tests'].items():
        status = "✓" if test_result['passed'] else "✗"
        required = "(обязательный)" if test_result['required'] else "(опциональный)"
        
        print(f"{status} {test_name} {required}")
        
        if test_result['required']:
            required_total += 1
            if test_result['passed']:
                required_passed += 1
    
    if required_passed == required_total:
        print("✅ Все обязательные тесты пройдены")
        print("Модель готова к использованию")
        
        optional_passed = sum(1 for t in all_results['tests'].values() 
                            if not t['required'] and t['passed'])
        optional_total = sum(1 for t in all_results['tests'].values() 
                           if not t['required'])
        
        if optional_total > 0:
            print(f"Опциональные тесты: {optional_passed}/{optional_total} пройдено")
    else:
        print(f"⚠ Пройдено обязательных тестов: {required_passed}/{required_total}")
        print("Система может работать с ограниченной функциональностью")
    
    save_test_results(all_results, 'hybrid_test_results.json')
    
    return required_passed == required_total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
