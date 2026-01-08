import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any
import logging
from typing import Dict, Any, Optional

sys.path.insert(0, str(Path(__file__).parent / 'llm'))

from activity_classifier import ActivityClassifier, ActivityCategory, ClassificationResult
from llm.transformer_classifer import TransformerClassifier, TransformerClassificationResult

logger = logging.getLogger(__name__)

class HybridActivityClassifier:
    
    def __init__(self, transformer_model_path: Optional[str] = None):
        self.keyword_classifier = ActivityClassifier()
        self.transformer_classifier = TransformerClassifier(transformer_model_path)
        
        self.weights = {
            'keyword': 0.5,
            'transformer': 0.5
        }
        
        self.thresholds = {
            'min_confidence': 0.2,
            'transformer_fallback': 0.4
        }
        
        self.category_mapping = {
            'work': ActivityCategory.WORK,
            'non_work': ActivityCategory.NON_WORK,
            'harmful': ActivityCategory.HARMFUL,
            'neutral': ActivityCategory.NEUTRAL
        }
        
        logger.info("HybridActivityClassifier инициализирован")
    
    def classify(self, text: str, ocr_confidence: float = 1.0) -> ClassificationResult:
        
        # 1. Классификация по ключевым словам
        keyword_result = self.keyword_classifier.classify(text, ocr_confidence)
        
        # 2. Классификация через трансформер
        transformer_result = None
        if len(text.split()) >= 3:
            try:
                transformer_result = self.transformer_classifier.classify(text)
            except Exception as e:
                logger.warning(f"Классификация через LLM не удалась: {e}")
                transformer_result = None
        
        # 3. Слияние результатов
        if transformer_result is None:
            # Используем только ключевые слова
            final_result = keyword_result
            final_result.classifier_type = "keyword_only"
            final_result.transformer_confidence = 0.0
        else:
            # Совмещаем результаты
            final_result = self._merge_results(keyword_result, transformer_result)
        
        return final_result
    
    def _merge_results(self, keyword_result: ClassificationResult, 
                      transformer_result: TransformerClassificationResult) -> ClassificationResult:
        
        transformer_category = self.category_mapping.get(
            transformer_result.category, ActivityCategory.UNKNOWN)
        
        if keyword_result.category == transformer_category:
            combined_confidence = (
                keyword_result.confidence * self.weights['keyword'] +
                transformer_result.confidence * self.weights['transformer']
            )
            
            result = ClassificationResult(
                category=keyword_result.category,
                subcategory=keyword_result.subcategory,
                confidence=combined_confidence,
                matched_keywords=keyword_result.matched_keywords,
                detected_apps=keyword_result.detected_apps,
                text_summary=keyword_result.text_summary,
                timestamp=datetime.now(),
                classifier_type="hybrid_agreement",
                transformer_confidence=transformer_result.confidence,
                keyword_confidence=keyword_result.confidence
            )
        
        else:
            keyword_weighted = keyword_result.confidence * self.weights['keyword']
            transformer_weighted = transformer_result.confidence * self.weights['transformer']
            
            if keyword_weighted >= transformer_weighted:
                selected_category = keyword_result.category
                selected_subcategory = keyword_result.subcategory
                selected_confidence = keyword_result.confidence
                classifier_type = "keyword_selected"
            else:
                selected_category = transformer_category
                selected_subcategory = self._get_subcategory_for_transformer(transformer_result)
                selected_confidence = transformer_result.confidence
                classifier_type = "transformer_selected"
            
            result = ClassificationResult(
                category=selected_category,
                subcategory=selected_subcategory,
                confidence=selected_confidence,
                matched_keywords=keyword_result.matched_keywords if classifier_type == "keyword_selected" else [],
                detected_apps=keyword_result.detected_apps if classifier_type == "keyword_selected" else [],
                text_summary=keyword_result.text_summary,
                timestamp=datetime.now(),
                classifier_type=classifier_type,
                transformer_confidence=transformer_result.confidence,
                keyword_confidence=keyword_result.confidence
            )
        
        return result
    
    def _get_subcategory_for_transformer(self, transformer_result: TransformerClassificationResult) -> str:
        if transformer_result.category == 'work':
            return 'LLM: Рабочая активность'
        elif transformer_result.category == 'non_work':
            return 'LLM: Нерабочая активность'
        elif transformer_result.category == 'harmful':
            return 'LLM: Вредоносная активность'
        else:
            return 'LLM: Нейтральная активность'
    
    def classify_image(self, image_path: str, ocr_processor) -> ClassificationResult:
        ocr_result = ocr_processor.extract_text(image_path)
        
        if not ocr_result['success']:
            return ClassificationResult(
                category=ActivityCategory.UNKNOWN,
                subcategory='Ошибка OCR',
                confidence=0.0,
                matched_keywords=[],
                detected_apps=[],
                text_summary='',
                timestamp=datetime.now(),
                classifier_type="error"
            )
        
        confidence = ocr_result['confidence'] / 100.0
        return self.classify(ocr_result['text'], confidence)

if __name__ == "__main__":
    from ocr_processor import OCRProcessor
    
    ocr = OCRProcessor()
    classifier = HybridActivityClassifier()
    
    test_image = Path(__file__).parent / "test_data" / "test_image_work.png"
    
    if test_image.exists():
        result = classifier.classify_image(str(test_image), ocr)
        
        print(f"Категория: {result.category.value}")
        print(f"Подкатегория: {result.subcategory}")
        print(f"Уверенность: {result.confidence:.2%}")
        print(f"Тип классификатора: {result.classifier_type}")
        
        if hasattr(result, 'transformer_confidence'):
            print(f"Уверенность трансформера: {result.transformer_confidence:.2%}")
        if hasattr(result, 'keyword_confidence'):
            print(f"Уверенность ключевых слов: {result.keyword_confidence:.2%}")
