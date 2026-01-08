import re
import json
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum
import logging
from datetime import datetime
from pathlib import Path

from keyword_lists import KEYWORDS, CATEGORY_MAPPING, SUBCATEGORY_MAPPING

logger = logging.getLogger(__name__)

class ActivityCategory(Enum):
    WORK = "Рабочая активность"
    NON_WORK = "Нерабочая активность"
    HARMFUL = "Вредоносные сайты"
    NEUTRAL = "Нейтральная / Системная активность"
    UNKNOWN = "Неизвестная активность"

@dataclass
class ClassificationResult:
    category: ActivityCategory
    subcategory: str
    confidence: float
    matched_keywords: List[str]
    detected_apps: List[str]
    text_summary: str
    timestamp: datetime
    classifier_type: str = "keyword"
    transformer_confidence: float = 0.0
    keyword_confidence: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'category': self.category.value,
            'subcategory': self.subcategory,
            'confidence': float(self.confidence),
            'matched_keywords': self.matched_keywords,
            'detected_apps': self.detected_apps,
            'text_summary': self.text_summary[:200] if self.text_summary else '',
            'timestamp': self.timestamp.isoformat()
        }

class ActivityClassifier:
    
    def __init__(self, keywords: Optional[Dict] = None):
        self.keywords = keywords or KEYWORDS
        self.compiled_patterns = self._compile_keyword_patterns()
        
        # Веса категорий для расчета уверенности
        self.category_weights = {
            ActivityCategory.WORK: 1.0,
            ActivityCategory.NON_WORK: 1.0,
            ActivityCategory.HARMFUL: 1.2,
            ActivityCategory.NEUTRAL: 0.8,
            ActivityCategory.UNKNOWN: 0.5
        }
        
        # Пороги классификации
        self.thresholds = {
            'min_confidence': 0.2,
            'min_keywords': 1,
            'text_length_factor': 0.05
        }
        
    def _compile_keyword_patterns(self) -> Dict[str, Dict[str, re.Pattern]]:
        patterns = {}
        
        for category, subcategories in self.keywords.items():
            patterns[category] = {}
            for subcategory, keywords in subcategories.items():
                # Создаем паттерн для поиска ключевых слов
                # Используем границы слов для точного соответствия
                keyword_patterns = []
                for keyword in keywords:
                    # Экранируем специальные символы
                    escaped = re.escape(keyword.lower())
                    # Для ключей с точкой в конце ищем как начало слова
                    if keyword.endswith('.'):
                        pattern = fr'\b{escaped}\w*'
                    else:
                        if ' ' in keyword:
                            words = escaped.split()
                            full_phrase_pattern = r'\b' + escaped + r'\b'
                            keyword_patterns.append(full_phrase_pattern)

                            significant_words = [word for word in words if len(word) > 3]
                            for word in significant_words:
                                keyword_patterns.append(r'\b' + word + r'\b')
                        else:
                            pattern = r'\b' + escaped + r'\b'
                            keyword_patterns.append(pattern)
                
                # Объединяем все паттерны через ИЛИ
                unique_patterns = list(set(keyword_patterns))
                combined_pattern = '|'.join(unique_patterns)
                
                patterns[category][subcategory] = re.compile(
                    combined_pattern, 
                    re.IGNORECASE | re.UNICODE
                )
        
        return patterns
    
    def _normalize_text(self, text: str) -> str:
        # Приводим к нижнему регистру
        text = text.lower()
        
        # Заменяем несколько пробелов на один
        text = re.sub(r'\s+', ' ', text)
        
        # Удаляем специальные символы, но сохраняем буквы и цифры
        text = re.sub(r'[^\w\s.,!?;:]', ' ', text)
        
        return text.strip()
    
    def _find_matches(self, text: str) -> Dict[str, Dict[str, List[str]]]:
        normalized_text = self._normalize_text(text)
        matches = {}
        
        for category, subcategories in self.compiled_patterns.items():
            category_matches = {}
            for subcategory, pattern in subcategories.items():
                # Ищем все совпадения
                found = pattern.findall(normalized_text)
                if found:
                    # Убираем дубликаты
                    unique_matches = list(set([m.lower() for m in found]))
                    category_matches[subcategory] = unique_matches
            
            if category_matches:
                matches[category] = category_matches
        
        return matches
    
    def _calculate_confidence(self, matches: Dict[str, Dict[str, List[str]]], 
                            text_length: int) -> Dict[ActivityCategory, float]:
        confidences = {}
        total_matches = 0
        
        # Считаем общее количество совпадений
        for category, subcategories in matches.items():
            for matches_list in subcategories.values():
                total_matches += len(matches_list)
        
        if total_matches == 0:
            # Если нет совпадений, возвращаем минимальную уверенность
            for category in ActivityCategory:
                if category != ActivityCategory.UNKNOWN:
                    confidences[category] = 0.0
            return confidences
        
        # Расчет уверенности для каждой категории
        for category in ActivityCategory:
            if category == ActivityCategory.UNKNOWN:
                continue
                
            category_str = self._category_to_str(category)
            category_matches = 0
            
            if category_str in matches:
                for matches_list in matches[category_str].values():
                    category_matches += len(matches_list)
            
            # Базовая уверенность на основе доли совпадений
            base_confidence = category_matches / total_matches
            
            # Корректировка на длину текста
            length_factor = min(1.0, text_length * self.thresholds['text_length_factor'])
            
            # Применяем вес категории
            weight = self.category_weights.get(category, 1.0)
            
            # Итоговая уверенность
            confidence = base_confidence * weight * length_factor
            confidences[category] = min(1.0, confidence)
        
        return confidences
    
    def _category_to_str(self, category: ActivityCategory) -> str:
        mapping = {
            ActivityCategory.WORK: 'work',
            ActivityCategory.NON_WORK: 'non_work',
            ActivityCategory.HARMFUL: 'harmful',
            ActivityCategory.NEUTRAL: 'neutral'
        }
        return mapping.get(category, 'unknown')
    
    def _str_to_category(self, category_str: str) -> ActivityCategory:
        mapping = {
            'work': ActivityCategory.WORK,
            'non_work': ActivityCategory.NON_WORK,
            'harmful': ActivityCategory.HARMFUL,
            'neutral': ActivityCategory.NEUTRAL
        }
        return mapping.get(category_str, ActivityCategory.UNKNOWN)
    
    def get_category_name(self, category: ActivityCategory) -> str:
        return CATEGORY_MAPPING.get(self._category_to_str(category), "Неизвестная категория")
    
    def get_subcategory_name(self, subcategory: str) -> str:
        return SUBCATEGORY_MAPPING.get(subcategory, subcategory)
    
    def classify(self, text: str, ocr_confidence: float = 1.0) -> ClassificationResult:
        # Если текст пустой или слишком короткий
        if not text or len(text.strip()) < 10:
            return ClassificationResult(
                category=ActivityCategory.UNKNOWN,
                subcategory='Недостаточно текста',
                confidence=0.0,
                matched_keywords=[],
                detected_apps=[],
                text_summary='',
                timestamp=datetime.now()
            )
        
        # Поиск совпадений
        matches = self._find_matches(text)
        
        # Расчет уверенности
        confidences = self._calculate_confidence(matches, len(text))
        
        # Корректировка уверенности на основе качества OCR
        for category in confidences:
            confidences[category] *= ocr_confidence
        
        # Определение категории с максимальной уверенностью
        if confidences:
            best_category = max(confidences.items(), key=lambda x: x[1])
            best_category_enum, best_confidence = best_category
            
            # Проверка порога уверенности
            if best_confidence < self.thresholds['min_confidence']:
                best_category_enum = ActivityCategory.UNKNOWN
                best_confidence = 0.0
        else:
            best_category_enum = ActivityCategory.UNKNOWN
            best_confidence = 0.0
        
        # Определение подкатегории
        subcategory = 'Не определено'
        detected_apps = []
        matched_keywords = []
        
        if best_category_enum != ActivityCategory.UNKNOWN:
            category_str = self._category_to_str(best_category_enum)
            if category_str in matches:
                # Выбираем подкатегорию с наибольшим количеством совпадений
                subcategory_matches = matches[category_str]
                if subcategory_matches:
                    best_subcategory = max(subcategory_matches.items(), 
                                         key=lambda x: len(x[1]))
                    subcategory = best_subcategory[0]
                    
                    # Собираем найденные ключевые слова
                    for subcat, keywords in subcategory_matches.items():
                        matched_keywords.extend(keywords)
                    
                    # Определяем приложения/сайты
                    detected_apps = list(set(matched_keywords))
        
        # Получаем русские названия
        subcategory_name = self.get_subcategory_name(subcategory)
        
        # Создаем краткое содержание текста
        text_summary = text[:500] + ('...' if len(text) > 500 else '')
        
        return ClassificationResult(
            category=best_category_enum,
            subcategory=subcategory_name,
            confidence=best_confidence,
            matched_keywords=matched_keywords[:10],
            detected_apps=detected_apps[:5],
            text_summary=text_summary,
            timestamp=datetime.now()
        )
    
    def classify_image(self, image_path: str, 
                      ocr_processor: 'OCRProcessor') -> ClassificationResult:
        try:
            # Извлекаем текст
            ocr_result = ocr_processor.extract_text(image_path)
            
            if not ocr_result['success']:
                return ClassificationResult(
                    category=ActivityCategory.UNKNOWN,
                    subcategory='Ошибка OCR',
                    confidence=0.0,
                    matched_keywords=[],
                    detected_apps=[],
                    text_summary='',
                    timestamp=datetime.now()
                )
            
            # Классифицируем текст
            confidence = ocr_result['confidence'] / 100.0  # Нормализуем 0-100 в 0-1
            return self.classify(ocr_result['text'], confidence)
            
        except Exception as e:
            logger.error(f"Ошибка при классификации изображения: {e}")
            return ClassificationResult(
                category=ActivityCategory.UNKNOWN,
                subcategory='Ошибка обработки',
                confidence=0.0,
                matched_keywords=[],
                detected_apps=[],
                text_summary='',
                timestamp=datetime.now()
            )
    
    def export_keywords(self, filepath: str) -> None:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.keywords, f, ensure_ascii=False, indent=2)
    
    @classmethod
    def from_json(cls, keywords_file: str) -> 'ActivityClassifier':
        with open(keywords_file, 'r', encoding='utf-8') as f:
            keywords = json.load(f)
        
        return cls(keywords)
