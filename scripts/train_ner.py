import os
import json
import numpy as np
import torch

# Limit threads to prevent high memory usage during CPU training
torch.set_num_threads(4)

from datasets import load_dataset, Dataset, DatasetDict
from transformers import (
    AutoTokenizer,
    AutoModelForTokenClassification,
    TrainingArguments,
    Trainer,
    DataCollatorForTokenClassification,
)
from seqeval.metrics import classification_report, f1_score, precision_score, recall_score

# Configuration
MODEL_NAME = "bert-base-multilingual-cased"
INPUT_DATA = "data/processed/annotated_hf"
OUTPUT_DIR = "models/ner/checkpoint"
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
                # First token of a word
                label_ids.append(LABEL_TO_ID.get(label[word_idx], LABEL_TO_ID["O"]))
            else:
                # Subword token
                label_ids.append(-100) # Only the first subword gets the label
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

    results = {
        "precision": precision_score(true_labels, true_predictions),
        "recall": recall_score(true_labels, true_predictions),
        "f1": f1_score(true_labels, true_predictions),
    }
    
    # Debug: Print first 3 true vs pred if F1 is 0
    if results["f1"] == 0:
        print("\n--- Evaluation Debug (Sample 0) ---")
        print(f"True: {true_labels[0][:20]}")
        print(f"Pred: {true_predictions[0][:20]}")
        
    return results


def train():
    # Load dataset
    print(f"Searching for data in {INPUT_DATA}...")
    
    data_files = []
    if os.path.isdir(INPUT_DATA):
        data_files = [os.path.join(INPUT_DATA, f) for f in os.listdir(INPUT_DATA) if f.endswith(".jsonl")]
    elif os.path.isfile(INPUT_DATA):
        data_files = [INPUT_DATA]
    else:
        # Check if it's a glob pattern or if we should just assume it's a directory
        import glob
        data_files = glob.glob(INPUT_DATA)

    if not data_files:
        print(f"Error: No data files found at {INPUT_DATA}")
        return

    print(f"Loading datasets from: {data_files}")
    dataset_real = load_dataset('json', data_files=data_files, split='train')
    print(f"Real dataset size: {len(dataset_real)}")
    
    # Load synthetic data
    SYNTHETIC_DATA = "data/processed/annotated_hf/synthetic_ueh.jsonl"
    if os.path.exists(SYNTHETIC_DATA) and SYNTHETIC_DATA not in data_files:
        print(f"Loading synthetic data from {SYNTHETIC_DATA}...")
        dataset_syn = load_dataset('json', data_files=SYNTHETIC_DATA, split='train')
        
        from datasets import concatenate_datasets
        dataset = concatenate_datasets([dataset_real, dataset_syn])
        print(f"Combined dataset size: {len(dataset)}")
    else:
        dataset = dataset_real

    # Split dataset
    dataset = dataset.train_test_split(test_size=0.2)
    ds = DatasetDict({
        'train': dataset['train'],
        'validation': dataset['test']
    })

    # We need to explicitly initialize the tokenizer if it requires specific flags
    # RoBERTa requires add_prefix_space=True when using is_split_into_words
    if "roberta" in MODEL_NAME:
        tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, add_prefix_space=True)
    else:
        tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        
    def tokenize_function(examples):
        return tokenize_and_align_labels(examples, tokenizer)
    
    # Preprocess
    print("Preprocessing data...")
    tokenized_ds = ds.map(
        tokenize_function,
        batched=True,
        remove_columns=ds["train"].column_names
    )

    # Load model
    print(f"Loading model {MODEL_NAME}...")
    model = AutoModelForTokenClassification.from_pretrained(
        MODEL_NAME,
        num_labels=len(LABEL_LIST),
        id2label=ID_TO_LABEL,
        label2id=LABEL_TO_ID
    )

    # Training arguments
    training_args = TrainingArguments(
        output_dir=OUTPUT_DIR,
        evaluation_strategy="epoch",
        learning_rate=2e-5,
        per_device_train_batch_size=2,
        gradient_accumulation_steps=4,
        per_device_eval_batch_size=2,
        eval_accumulation_steps=1, # Very important to prevent RAM OOM during evaluation
        num_train_epochs=20,

        weight_decay=0.01,
        save_strategy="epoch",
        save_total_limit=3,
        load_best_model_at_end=True,
        push_to_hub=False,
        report_to="none" # Disable wandb/tensorboard for now
    )

    # Initialize Trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_ds["train"],
        eval_dataset=tokenized_ds["validation"],
        tokenizer=tokenizer,
        data_collator=DataCollatorForTokenClassification(tokenizer),
        compute_metrics=compute_metrics,
    )

    # Train
    print("Starting training...")
    
    # Simple logic to resume from the last stable checkpoint if it exists
    last_checkpoint = None
    if os.path.isdir(OUTPUT_DIR):
        checkpoints = [os.path.join(OUTPUT_DIR, d) for d in os.listdir(OUTPUT_DIR) if d.startswith("checkpoint-")]
        if checkpoints:
            last_checkpoint = max(checkpoints, key=os.path.getmtime)
            print(f"Resuming from checkpoint: {last_checkpoint}")

    trainer.train(resume_from_checkpoint=last_checkpoint)

    
    # Save the model
    print(f"Saving final model to {OUTPUT_DIR}...")
    trainer.save_model(OUTPUT_DIR)
    print("Training complete!")

if __name__ == "__main__":
    os.environ["TORCH_COMPILE"] = "0"
    train()

