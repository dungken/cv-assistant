import torch
print("Torch version:", torch.__version__)
from transformers import pipeline
print("Transformers imported")
try:
    nlp = pipeline("ner", model="./models/ner/final", tokenizer="./models/ner/final", aggregation_strategy="simple")
    print("Model loaded successfully")
    res = nlp("Trần Đình Hoan is a Software Engineer at Google.")
    print("Inference result:", res)
except Exception as e:
    print("Error during model loading/inference:", e)
