import torch
import json
from pathlib import Path
from transformers import (
    AutoTokenizer, 
    AutoModelForSequenceClassification,
    AutoConfig,
    BertTokenizer,
    BertForSequenceClassification
)
from typing import Dict, Any, Optional
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class TransformerClassificationResult:
    category: str
    confidence: float
    category_id: int
    logits: list

class TransformerClassifier:
    
    def __init__(self, model_path: Optional[str] = None):
        if model_path is None:
            model_path = Path(__file__).parent / "trained_model"
        else:
            model_path = Path(model_path)
        
        self.model_path = model_path

        required_files = ['config.json', 'pytorch_model.bin']
        for file in required_files:
            if not (model_path / file).exists():
                raise FileNotFoundError(f"Не найден файл: {model_path / file}")

        with open(model_path / "config.json", "r", encoding="utf-8") as f:
            self.config = json.load(f)
        
        logger.info(f"Загрузка модели из {model_path}")
        
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(str(model_path))

            if 'model_type' not in self.config:
                self.config['model_type'] = 'bert'
                with open(model_path / "config.json", "w", encoding="utf-8") as f:
                    json.dump(self.config, f, ensure_ascii=False, indent=2)

            config = AutoConfig.from_pretrained(str(model_path))
            self.model = AutoModelForSequenceClassification.from_pretrained(
                str(model_path), 
                config=config
            )
            
        except Exception as e:
            logger.warning(f"Auto загрузка не удалась: {e}")

            try:
                self.tokenizer = BertTokenizer.from_pretrained(
                    str(model_path),
                    local_files_only=True
                )

                config_dict = {
                    "architectures": ["BertForSequenceClassification"],
                    "attention_probs_dropout_prob": 0.1,
                    "hidden_act": "gelu",
                    "hidden_dropout_prob": 0.1,
                    "hidden_size": 312,
                    "initializer_range": 0.02,
                    "intermediate_size": 600,
                    "layer_norm_eps": 1e-12,
                    "max_position_embeddings": 2048,
                    "model_type": "bert",
                    "num_attention_heads": 12,
                    "num_hidden_layers": 3,
                    "pad_token_id": 0,
                    "position_embedding_type": "absolute",
                    "transformers_version": "4.35.0",
                    "type_vocab_size": 2,
                    "use_cache": True,
                    "vocab_size": 83828,
                    "num_labels": self.config.get('num_labels', 4),
                    "id2label": self.config.get('id2label', 
                        {0: "harmful", 1: "neutral", 2: "non_work", 3: "work"}),
                    "label2id": self.config.get('label2id',
                        {"harmful": 0, "neutral": 1, "non_work": 2, "work": 3})
                }

                config_path = model_path / "config.json"
                with open(config_path, "w", encoding="utf-8") as f:
                    json.dump(config_dict, f, ensure_ascii=False, indent=2)
                
                config = AutoConfig.from_pretrained(model_path)
                self.model = BertForSequenceClassification(config)

                state_dict = torch.load(
                    model_path / "pytorch_model.bin",
                    map_location=torch.device('cpu')
                )
                self.model.load_state_dict(state_dict)
                
            except Exception as e2:
                logger.error(f"Загрузка как BERT тоже не удалась: {e2}")
                raise RuntimeError(f"Не удалось загрузить модель: {e2}")

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)
        self.model.eval()
        
        logger.info(f"Модель загружена на {self.device}")

        self.id_to_category = self.config.get("id2label", 
            {0: "harmful", 1: "neutral", 2: "non_work", 3: "work"})
        self.category_to_id = self.config.get("label2id",
            {"harmful": 0, "neutral": 1, "non_work": 2, "work": 3})
    
    def classify(self, text: str) -> TransformerClassificationResult:
        try:
            inputs = self.tokenizer(
                text,
                truncation=True,
                padding=True,
                max_length=128,
                return_tensors="pt"
            )
            
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            with torch.no_grad():
                outputs = self.model(**inputs)
                logits = outputs.logits
                probabilities = torch.softmax(logits, dim=-1)
            
            predicted_id = torch.argmax(probabilities, dim=-1).item()
            confidence = probabilities[0][predicted_id].item()
            category = self.id_to_category.get(str(predicted_id), "neutral")
            
            result = TransformerClassificationResult(
                category=category,
                confidence=confidence,
                category_id=predicted_id,
                logits=logits[0].cpu().tolist()
            )
            
            logger.debug(f"Transformer: {category} (уверенность: {confidence:.3f})")
            return result
            
        except Exception as e:
            logger.error(f"Ошибка классификации: {e}")
            return TransformerClassificationResult(
                category="neutral",
                confidence=0.0,
                category_id=1,
                logits=[0, 0, 0, 0]
            )

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    test_model_path = Path(__file__).parent / "trained_model"
    
    if not test_model_path.exists():
        print("Тестовой модели нет, создаем минимальную...")
        test_model_path.mkdir(exist_ok=True)
        
        config = {
            "model_type": "bert",
            "num_labels": 4,
            "id2label": {0: "harmful", 1: "neutral", 2: "non_work", 3: "work"},
            "label2id": {"harmful": 0, "neutral": 1, "non_work": 2, "work": 3}
        }
        
        with open(test_model_path / "config.json", "w") as f:
            json.dump(config, f)
        
        print("Создана тестовая конфигурация. Обучите модель в Colab!")
    else:
        classifier = TransformerClassifier()
        
        test_texts = [
            "Visual Studio Code Python GitHub",
            "Facebook YouTube Instagram",
            "rutracker crack VPN",
            "File Explorer Desktop Settings"
        ]
        
        for text in test_texts:
            result = classifier.classify(text)
            print(f"{text[:30]}... -> {result.category} "
                  f"(уверенность: {result.confidence:.3f})")
