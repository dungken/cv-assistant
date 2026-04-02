"""
Task 1.4: Evaluate NER model on test samples.
Computes Precision, Recall, F1 per entity type and overall.
Outputs detailed classification report and error analysis.
"""

import os
import json
import argparse
import numpy as np
from pathlib import Path
from collections import Counter, defaultdict

import torch
from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline
from seqeval.metrics import classification_report, f1_score, precision_score, recall_score
from datasets import load_dataset

# ─── Configuration ───────────────────────────────────────────────────────────

MODEL_DIR = "models/ner/final"
TEST_DATA = "data/processed/annotated_hf/synthetic_it_test.jsonl"
LABEL_LIST = [
    "O", "B-PER", "I-PER", "B-ORG", "I-ORG", "B-DATE", "I-DATE",
    "B-LOC", "I-LOC", "B-SKILL", "I-SKILL", "B-DEGREE", "I-DEGREE",
    "B-MAJOR", "I-MAJOR", "B-JOB_TITLE", "I-JOB_TITLE", "B-PROJECT",
    "I-PROJECT", "B-CERT", "I-CERT"
]
ID_TO_LABEL = {i: label for i, label in enumerate(LABEL_LIST)}
LABEL_TO_ID = {label: i for i, label in enumerate(LABEL_LIST)}


def load_test_data(test_file: str, max_samples: int = 0) -> list[dict]:
    """Load test data from JSONL file."""
    data = []
    with open(test_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))
    if max_samples > 0:
        data = data[:max_samples]
    return data


def evaluate_with_model(model_dir: str, test_data: list[dict]) -> dict:
    """Evaluate NER model on test data using HuggingFace pipeline."""
    print(f"Loading model from {model_dir}...")
    tokenizer = AutoTokenizer.from_pretrained(model_dir)
    model = AutoModelForTokenClassification.from_pretrained(model_dir)

    # Use pipeline for inference
    ner_pipeline = pipeline(
        "ner",
        model=model,
        tokenizer=tokenizer,
        aggregation_strategy="simple",
        device=0 if torch.cuda.is_available() else -1,
    )

    true_labels_all = []
    pred_labels_all = []
    errors = []

    for i, sample in enumerate(test_data):
        tokens = sample["tokens"]
        true_tags = sample["ner_tags"]
        text = " ".join(tokens)

        # Get predictions
        try:
            predictions = ner_pipeline(text)
        except Exception as e:
            print(f"  [ERROR] Sample {i}: {e}")
            continue

        # Map pipeline predictions back to token-level BIO tags
        pred_tags = ["O"] * len(tokens)
        char_offsets = []
        offset = 0
        for token in tokens:
            char_offsets.append((offset, offset + len(token)))
            offset += len(token) + 1  # +1 for space

        for pred in predictions:
            pred_start = pred["start"]
            pred_end = pred["end"]
            label = pred["entity_group"]

            first_token = True
            for j, (tok_start, tok_end) in enumerate(char_offsets):
                if tok_start < pred_end and tok_end > pred_start:
                    if first_token:
                        pred_tags[j] = f"B-{label}"
                        first_token = False
                    else:
                        pred_tags[j] = f"I-{label}"

        # Validate tags are in label list
        pred_tags = [t if t in LABEL_LIST else "O" for t in pred_tags]
        true_tags = [t if t in LABEL_LIST else "O" for t in true_tags]

        true_labels_all.append(true_tags)
        pred_labels_all.append(pred_tags)

        # Collect errors for analysis
        for j, (true_t, pred_t) in enumerate(zip(true_tags, pred_tags)):
            if true_t != pred_t and (true_t != "O" or pred_t != "O"):
                errors.append({
                    "sample_id": sample.get("id", i),
                    "token": tokens[j],
                    "true": true_t,
                    "pred": pred_t,
                    "context": " ".join(tokens[max(0, j-3):j+4])
                })

        if (i + 1) % 50 == 0:
            print(f"  Evaluated {i + 1}/{len(test_data)} samples")

    return {
        "true_labels": true_labels_all,
        "pred_labels": pred_labels_all,
        "errors": errors,
    }


def evaluate_rule_based(test_data: list[dict]) -> dict:
    """Evaluate using rule-based annotator (as baseline)."""
    from auto_label_cvs import CVAnnotator, build_skill_lookup

    print("Loading skills dictionary for rule-based baseline...")
    skills = build_skill_lookup()
    annotator = CVAnnotator(skills)

    true_labels_all = []
    pred_labels_all = []

    for i, sample in enumerate(test_data):
        tokens = sample["tokens"]
        true_tags = sample["ner_tags"]
        text = " ".join(tokens)

        # Get rule-based predictions
        result = annotator.annotate(text)
        pred_tags = result["ner_tags"]

        # Align lengths (in case tokenization differs slightly)
        min_len = min(len(true_tags), len(pred_tags))
        true_labels_all.append(true_tags[:min_len])
        pred_labels_all.append(pred_tags[:min_len])

    return {
        "true_labels": true_labels_all,
        "pred_labels": pred_labels_all,
        "errors": [],
    }


def print_results(results: dict, title: str, output_file: str = None):
    """Print and optionally save evaluation results."""
    true_labels = results["true_labels"]
    pred_labels = results["pred_labels"]

    report = classification_report(true_labels, pred_labels, digits=4)
    overall_f1 = f1_score(true_labels, pred_labels)
    overall_p = precision_score(true_labels, pred_labels)
    overall_r = recall_score(true_labels, pred_labels)

    output = []
    output.append("=" * 70)
    output.append(f"  {title}")
    output.append("=" * 70)
    output.append(f"\nOverall Metrics:")
    output.append(f"  Precision: {overall_p:.4f}")
    output.append(f"  Recall:    {overall_r:.4f}")
    output.append(f"  F1-Score:  {overall_f1:.4f}")
    output.append(f"\nDetailed Classification Report:")
    output.append(report)

    # Entity-level statistics
    output.append("\nEntity Distribution in Test Set:")
    entity_counts = Counter()
    for tags in true_labels:
        for tag in tags:
            if tag.startswith("B-"):
                entity_counts[tag[2:]] += 1

    for entity, count in sorted(entity_counts.items(), key=lambda x: -x[1]):
        output.append(f"  {entity:15s}: {count:5d} entities")

    # Error analysis
    if results.get("errors"):
        output.append(f"\nTop Error Patterns (showing first 20):")
        error_types = Counter()
        for err in results["errors"]:
            key = f"{err['true']} -> {err['pred']}"
            error_types[key] += 1

        for pattern, count in error_types.most_common(20):
            output.append(f"  {pattern:30s}: {count:5d} times")

        output.append(f"\nExample Errors:")
        for err in results["errors"][:10]:
            output.append(
                f"  Token: '{err['token']}' | True: {err['true']} | "
                f"Pred: {err['pred']} | Context: ...{err['context']}..."
            )

    text = "\n".join(output)
    print(text)

    if output_file:
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w") as f:
            f.write(text)
        print(f"\nReport saved to {output_file}")

    return {
        "precision": overall_p,
        "recall": overall_r,
        "f1": overall_f1,
    }


def main():
    parser = argparse.ArgumentParser(description="Evaluate NER model on test samples")
    parser.add_argument("--model-dir", type=str, default=MODEL_DIR, help="Trained model directory")
    parser.add_argument("--test-data", type=str, default=TEST_DATA, help="Test data JSONL file")
    parser.add_argument("--max-samples", type=int, default=100, help="Max samples to evaluate (0=all)")
    parser.add_argument("--output", type=str, default="reports/ner_evaluation.txt", help="Output report file")
    parser.add_argument("--baseline", action="store_true", help="Also run rule-based baseline evaluation")
    args = parser.parse_args()

    if not os.path.exists(args.test_data):
        print(f"ERROR: Test data not found at {args.test_data}")
        print("Run auto_label_cvs.py first to generate test data.")
        return

    # Load test data
    print(f"Loading test data from {args.test_data}...")
    test_data = load_test_data(args.test_data, args.max_samples)
    print(f"  Loaded {len(test_data)} test samples")

    results_summary = {}

    # Evaluate model if it exists
    if os.path.exists(args.model_dir):
        print(f"\n--- Evaluating NER Model ---")
        model_results = evaluate_with_model(args.model_dir, test_data)
        metrics = print_results(model_results, "NER Model Evaluation", args.output)
        results_summary["model"] = metrics
    else:
        print(f"\nWARNING: Model not found at {args.model_dir}")
        print("Train a model first with train_ner.py")

    # Baseline evaluation
    if args.baseline:
        print(f"\n--- Evaluating Rule-Based Baseline ---")
        try:
            baseline_results = evaluate_rule_based(test_data)
            baseline_output = args.output.replace(".txt", "_baseline.txt") if args.output else None
            metrics = print_results(baseline_results, "Rule-Based Baseline Evaluation", baseline_output)
            results_summary["baseline"] = metrics
        except ImportError:
            print("  Skipping baseline (auto_label_cvs.py not importable from this location)")

    # Comparison summary
    if len(results_summary) > 1:
        print(f"\n{'='*50}")
        print(f"  Model Comparison Summary")
        print(f"{'='*50}")
        for name, metrics in results_summary.items():
            print(f"  {name:15s}: P={metrics['precision']:.4f}  R={metrics['recall']:.4f}  F1={metrics['f1']:.4f}")


if __name__ == "__main__":
    main()
