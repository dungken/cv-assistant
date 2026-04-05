import os
import json
import argparse
import numpy as np
import torch
from datasets import load_dataset, Dataset, DatasetDict
from transformers import (
    AutoTokenizer,
    AutoModelForTokenClassification,
    TrainingArguments,
    Trainer,
    DataCollatorForTokenClassification,
    EarlyStoppingCallback,
)
from seqeval.metrics import classification_report, f1_score, precision_score, recall_score

# --- Configuration ---
BASE_MODEL = "models/ner/final"
TRAIN_DATA = "data/processed/annotated_hf/jd_train.jsonl"
OUTPUT_DIR = "models/ner/jd_checkpoint"
FINAL_DIR = "models/ner/jd_final"

LABEL_LIST = [
    "O", "B-PER", "I-PER", "B-ORG", "I-ORG", "B-DATE", "I-DATE",
    "B-LOC", "I-LOC", "B-SKILL", "I-SKILL", "B-DEGREE", "I-DEGREE",
    "B-MAJOR", "I-MAJOR", "B-JOB_TITLE", "I-JOB_TITLE", "B-PROJECT",
    "I-PROJECT", "B-CERT", "I-CERT"
]
LABEL_TO_ID = {label: i for i, label in enumerate(LABEL_LIST)}
ID_TO_LABEL = {i: label for i, label in enumerate(LABEL_LIST)}

def tokenize_and_align_labels(examples, tokenizer):
    tokenized_inputs = tokenizer(
        examples["tokens"],
        truncation=True,
        is_split_into_words=True,
        padding="max_length",
        max_length=512
    )

    labels = []
    for i, label in enumerate(examples["ner_tags"]):
        word_ids = tokenized_inputs.word_ids(batch_index=i)
        previous_word_idx = None
        label_ids = []
        for word_idx in word_ids:
            if word_idx is None:
                label_ids.append(-100)
            elif word_idx != previous_word_idx:
                label_ids.append(LABEL_TO_ID.get(label[word_idx], LABEL_TO_ID["O"]))
            else:
                label_ids.append(-100)
            previous_word_idx = word_idx
        labels.append(label_ids)

    tokenized_inputs["labels"] = labels
    return tokenized_inputs

def compute_metrics(p):
    predictions, labels = p
    predictions = np.argmax(predictions, axis=2)

    true_predictions = [
        [ID_TO_LABEL[p] for (p, l) in zip(prediction, label) if l != -100]
        for prediction, label in zip(predictions, labels)
    ]
    true_labels = [
        [ID_TO_LABEL[l] for (p, l) in zip(prediction, label) if l != -100]
        for prediction, label in zip(predictions, labels)
    ]

    return {
        "precision": precision_score(true_labels, true_predictions),
        "recall": recall_score(true_labels, true_predictions),
        "f1": f1_score(true_labels, true_predictions),
    }

def train():
    print(f"Fine-tuning JD model from {BASE_MODEL}")
    
    # Load dataset
    if not os.path.exists(TRAIN_DATA):
        print(f"Error: Training data {TRAIN_DATA} not found. Run label_jds_auto.py first.")
        return

    dataset = load_dataset('json', data_files=TRAIN_DATA, split='train')
    split = dataset.train_test_split(test_size=0.15, seed=42)
    ds = DatasetDict({'train': split['train'], 'validation': split['test']})
    
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
    
    print("Preprocessing data...")
    tokenized_ds = ds.map(
        lambda x: tokenize_and_align_labels(x, tokenizer),
        batched=True,
        remove_columns=ds["train"].column_names
    )

    print(f"Loading base model from {BASE_MODEL}...")
    model = AutoModelForTokenClassification.from_pretrained(
        BASE_MODEL,
        num_labels=len(LABEL_LIST),
        id2label=ID_TO_LABEL,
        label2id=LABEL_TO_ID
    )

    training_args = TrainingArguments(
        output_dir=OUTPUT_DIR,
        eval_strategy="epoch",
        learning_rate=2e-5,
        per_device_train_batch_size=2, # Optimized for 4GB VRAM
        gradient_accumulation_steps=4,
        num_train_epochs=8, # JD fine-tuning needs fewer epochs
        weight_decay=0.01,
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="f1",
        fp16=torch.cuda.is_available(),
        logging_steps=10,
        report_to="none"
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_ds["train"],
        eval_dataset=tokenized_ds["validation"],
        data_collator=DataCollatorForTokenClassification(tokenizer),
        compute_metrics=compute_metrics,
        callbacks=[EarlyStoppingCallback(early_stopping_patience=2)],
    )

    print("Starting fine-tuning...")
    trainer.train()

    print(f"Saving final JD model to {FINAL_DIR}...")
    trainer.save_model(FINAL_DIR)
    tokenizer.save_pretrained(FINAL_DIR)
    print("Done!")

if __name__ == "__main__":
    train()
