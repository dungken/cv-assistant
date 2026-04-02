import os
import json
import argparse
import numpy as np
import torch

# Limit threads to prevent high memory usage during CPU training
torch.set_num_threads(4)

from datasets import load_dataset, Dataset, DatasetDict, concatenate_datasets
from transformers import (
    AutoTokenizer,
    AutoModelForTokenClassification,
    TrainingArguments,
    Trainer,
    DataCollatorForTokenClassification,
    EarlyStoppingCallback,
)
from seqeval.metrics import classification_report, f1_score, precision_score, recall_score

# Configuration
SUPPORTED_MODELS = {
    "mbert": "bert-base-multilingual-cased",
    "phobert": "vinai/phobert-base-v2",
    "xlm-roberta": "xlm-roberta-base",
}
DEFAULT_MODEL = "mbert"
INPUT_DATA = "data/processed/annotated_hf"
SYNTHETIC_DATA = "data/processed/annotated_hf/synthetic_it.jsonl"
OUTPUT_DIR = "models/ner/checkpoint"
FINAL_DIR = "models/ner/final"
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


def load_all_data(input_dir: str, synthetic_file: str) -> Dataset:
    """Load and merge all training data: annotated + synthetic IT CVs."""
    all_datasets = []

    # Load annotated data from input directory
    if os.path.isdir(input_dir):
        # Only load files that contain labels - avoid the main aggregate if splits exist
        files_in_dir = os.listdir(input_dir)
        has_splits = any("_train" in f or "_test" in f for f in files_in_dir)
        
        if has_splits:
            data_files = [
                os.path.join(input_dir, f) for f in files_in_dir
                if f.endswith(".jsonl") and ("_train" in f or "_test" in f)
            ]
        else:
            data_files = [
                os.path.join(input_dir, f) for f in files_in_dir
                if f.endswith(".jsonl")
            ]
        
        if data_files:
            print(f"Loading data from: {data_files}")
            ds = load_dataset('json', data_files=data_files, split='train')
            all_datasets.append(ds)
            print(f"  Samples: {len(ds)}")

    # Load synthetic IT data (from auto_label_cvs.py output)
    if os.path.exists(synthetic_file):
        # Avoid loading synthetic_file if it's already in data_files (same path)
        synth_abs = os.path.abspath(synthetic_file)
        data_files_abs = [os.path.abspath(f) for f in data_files]
        
        if synth_abs not in data_files_abs:
            ds_syn = load_dataset('json', data_files=synthetic_file, split='train')
            all_datasets.append(ds_syn)
            print(f"  Added synthetic file: {synthetic_file} ({len(ds_syn)} samples)")
        else:
            print(f"  Skipping {synthetic_file} - already loaded from input_dir.")

    if not all_datasets:
        raise ValueError(f"No training data found in {input_dir} or {synthetic_file}")

    if len(all_datasets) > 1:
        combined = concatenate_datasets(all_datasets)
    else:
        combined = all_datasets[0]

    print(f"  Total combined samples: {len(combined)}")
    return combined


def train(args):
    # Resolve model name
    model_name = SUPPORTED_MODELS.get(args.model, args.model)
    output_dir = args.output_dir or OUTPUT_DIR
    final_dir = args.final_dir or FINAL_DIR

    print(f"Model: {model_name}")
    print(f"Checkpoint dir: {output_dir}")
    print(f"Final model dir: {final_dir}")

    # Load dataset
    print(f"\nLoading training data...")
    dataset = load_all_data(args.input_data or INPUT_DATA, args.synthetic_data or SYNTHETIC_DATA)

    # Split dataset
    split = dataset.train_test_split(test_size=0.2, seed=42)
    ds = DatasetDict({
        'train': split['train'],
        'validation': split['test']
    })
    print(f"  Train: {len(ds['train'])}, Validation: {len(ds['validation'])}")

    # Initialize tokenizer (RoBERTa/PhoBERT need add_prefix_space)
    is_roberta = any(k in model_name.lower() for k in ["roberta", "phobert"])
    if is_roberta:
        tokenizer = AutoTokenizer.from_pretrained(model_name, add_prefix_space=True)
    else:
        tokenizer = AutoTokenizer.from_pretrained(model_name)

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
    print(f"Loading model {model_name}...")
    model = AutoModelForTokenClassification.from_pretrained(
        model_name,
        num_labels=len(LABEL_LIST),
        id2label=ID_TO_LABEL,
        label2id=LABEL_TO_ID
    )

    # Training arguments
    training_args = TrainingArguments(
        output_dir=output_dir,
        eval_strategy="epoch",
        learning_rate=args.lr,
        per_device_train_batch_size=args.batch_size,
        gradient_accumulation_steps=args.grad_accum,
        per_device_eval_batch_size=args.batch_size,
        eval_accumulation_steps=1,
        num_train_epochs=args.epochs,
        weight_decay=0.01,
        warmup_steps=int(0.1 * (len(tokenized_ds["train"]) // args.batch_size) * args.epochs),
        save_strategy="epoch",
        save_total_limit=3,
        load_best_model_at_end=True,
        metric_for_best_model="f1",
        greater_is_better=True,
        push_to_hub=False,
        report_to="none",
        logging_steps=50,
        fp16=torch.cuda.is_available(),
    )

    # Initialize Trainer with early stopping
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_ds["train"],
        eval_dataset=tokenized_ds["validation"],
        data_collator=DataCollatorForTokenClassification(tokenizer),
        compute_metrics=compute_metrics,
        callbacks=[EarlyStoppingCallback(early_stopping_patience=3)],
    )

    # Train (resume from checkpoint if available)
    print("Starting training...")
    last_checkpoint = None
    if os.path.isdir(output_dir):
        checkpoints = [
            os.path.join(output_dir, d) for d in os.listdir(output_dir)
            if d.startswith("checkpoint-")
        ]
        if checkpoints:
            last_checkpoint = max(checkpoints, key=os.path.getmtime)
            print(f"Resuming from checkpoint: {last_checkpoint}")

    trainer.train(resume_from_checkpoint=last_checkpoint)

    # Save final model
    os.makedirs(final_dir, exist_ok=True)
    print(f"\nSaving final model to {final_dir}...")
    trainer.save_model(final_dir)
    tokenizer.save_pretrained(final_dir)

    # Run final evaluation and print detailed report
    print("\n" + "=" * 60)
    print("Final Evaluation Report")
    print("=" * 60)
    eval_results = trainer.evaluate()
    for key, value in eval_results.items():
        print(f"  {key}: {value:.4f}")

    print(f"\nTraining complete! Model saved to {final_dir}")

if __name__ == "__main__":
    os.environ["TORCH_COMPILE"] = "0"

    parser = argparse.ArgumentParser(description="Train NER model for IT CVs")
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL,
                        choices=list(SUPPORTED_MODELS.keys()),
                        help=f"Model to use: {list(SUPPORTED_MODELS.keys())}")
    parser.add_argument("--input-data", type=str, default=None, help="Input data directory")
    parser.add_argument("--synthetic-data", type=str, default=None, help="Synthetic IT data JSONL file")
    parser.add_argument("--output-dir", type=str, default=None, help="Checkpoint output directory")
    parser.add_argument("--final-dir", type=str, default=None, help="Final model output directory")
    parser.add_argument("--epochs", type=int, default=20, help="Number of training epochs")
    parser.add_argument("--batch-size", type=int, default=2, help="Per-device batch size")
    parser.add_argument("--grad-accum", type=int, default=4, help="Gradient accumulation steps")
    parser.add_argument("--lr", type=float, default=2e-5, help="Learning rate")

    args = parser.parse_args()
    train(args)

