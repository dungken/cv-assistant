import sys
import os
from transformers import pipeline

def test_ner(text):
    # Đường dẫn tới model đã giải nén
    model_path = os.path.join(os.path.dirname(__file__), "..", "models", "ner", "checkpoint")
    
    print(f"Loading model from: {model_path}")
    
    try:
        # Khởi tạo pipeline NER
        # aggregation_strategy="simple" giúp gộp các token B- và I- lại thành 1 thực thể nguyên vẹn
        ner_pipeline = pipeline(
            "ner", 
            model=model_path, 
            tokenizer=model_path,
            aggregation_strategy="simple"
        )
        
        results = ner_pipeline(text)
        
        print("\n" + "="*50)
        print(f"TEXT: {text}")
        print("="*50)
        print(f"{'Entity':<30} | {'Type':<12} | {'Score':<6}")
        print("-" * 55)
        
        for entity in results:
            print(f"{entity['word']:<30} | {entity['entity_group']:<12} | {entity['score']:.4f}")
        
        if not results:
            print("No entities found.")
        print("="*50 + "\n")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        input_text = " ".join(sys.argv[1:])
    else:
        # Văn bản mẫu để test nhanh
        input_text = "Nguyễn Văn A là Kỹ sư phần mềm tại công ty Google với 5 năm kinh nghiệm lập trình Python."
    
    test_ner(input_text)
