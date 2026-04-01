#!/usr/bin/env python3
"""
watch_model.py — Polls for NER training completion and hot-reloads the service.

Usage:
    python scripts/watch_model.py

It watches for a `config.json` inside the model checkpoint directory.
When found (training complete), it kills the current NER service and restarts it.
"""
import os
import sys
import time
import subprocess
import signal
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s [WATCHER] %(message)s')
logger = logging.getLogger(__name__)

# Paths
ROOT = Path(__file__).parent.parent
MODEL_CHECKPOINT_DIR = ROOT / "models" / "ner" / "checkpoint"
NER_SERVICE_MAIN    = ROOT / "services" / "ner_service" / "main.py"
VENV_PYTHON         = ROOT / "cv_assistant_env" / "bin" / "python"

POLL_INTERVAL_SECS  = 30   # Check every 30 seconds
ner_process: subprocess.Popen | None = None


def is_model_ready(checkpoint_dir: Path) -> bool:
    """Returns True if the best model exists (training wrote config.json to checkpoint root)."""
    # HuggingFace Trainer saves best model config.json in the checkpoint root upon completion
    return (checkpoint_dir / "config.json").exists()


def start_ner_service():
    """Start the NER FastAPI service as a subprocess."""
    global ner_process
    cmd = [str(VENV_PYTHON), str(NER_SERVICE_MAIN)]
    logger.info(f"Starting NER service: {' '.join(cmd)}")
    ner_process = subprocess.Popen(cmd, cwd=str(ROOT))
    logger.info(f"NER service started with PID {ner_process.pid}")


def stop_ner_service():
    """Gracefully stop the running NER service."""
    global ner_process
    if ner_process and ner_process.poll() is None:
        logger.info(f"Stopping NER service PID {ner_process.pid}…")
        ner_process.send_signal(signal.SIGTERM)
        try:
            ner_process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            ner_process.kill()
        logger.info("NER service stopped.")
    ner_process = None


def get_best_checkpoint() -> Path | None:
    """Find the checkpoint sub-dir with the highest step number."""
    if not MODEL_CHECKPOINT_DIR.exists():
        return None
    checkpoints = sorted(
        [d for d in MODEL_CHECKPOINT_DIR.iterdir() if d.is_dir() and d.name.startswith("checkpoint-")],
        key=lambda d: int(d.name.split("-")[-1])
    )
    return checkpoints[-1] if checkpoints else None


def get_latest_f1() -> str:
    """Read the last eval_f1 from trainer_state.json."""
    try:
        import json
        best = get_best_checkpoint()
        if not best:
            return "N/A"
        state_file = best / "trainer_state.json"
        if not state_file.exists():
            return "N/A"
        d = json.loads(state_file.read_text())
        evals = [l for l in d.get("log_history", []) if "eval_f1" in l]
        if evals:
            last = evals[-1]
            return f"F1={last['eval_f1']:.4f} @ epoch {last.get('epoch', '?')}"
    except Exception:
        pass
    return "N/A"


def main():
    logger.info("=" * 60)
    logger.info("NER Model Watcher started.")
    logger.info(f"Watching: {MODEL_CHECKPOINT_DIR}")
    logger.info(f"Waiting for training to complete…")
    logger.info("=" * 60)

    model_was_ready = is_model_ready(MODEL_CHECKPOINT_DIR)
    if model_was_ready:
        logger.info("Model already trained and ready!")
        start_ner_service()
    
    cycle = 0
    while True:
        time.sleep(POLL_INTERVAL_SECS)
        cycle += 1
        
        best_ck = get_best_checkpoint()
        step = int(best_ck.name.split("-")[-1]) if best_ck else 0
        f1_str = get_latest_f1()
        logger.info(f"[{cycle}] Training progress: step={step} | {f1_str}")

        now_ready = is_model_ready(MODEL_CHECKPOINT_DIR)
        if now_ready and not model_was_ready:
            logger.info("🎉 Training COMPLETE! Best model saved. Reloading NER Service…")
            stop_ner_service()
            time.sleep(2)
            start_ner_service()
            model_was_ready = True
            logger.info("✅ NER Service reloaded with the new model.")
            # Run evaluation in background
            eval_cmd = [str(VENV_PYTHON), str(ROOT / "scripts" / "evaluate_model.py")]
            subprocess.Popen(eval_cmd, cwd=str(ROOT))
            logger.info("📊 Started background evaluation on gold standard...")


if __name__ == "__main__":
    main()
