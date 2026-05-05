import hashlib
import os
from typing import Optional

def load_prompt(phenomenon: str, task_type: str) -> str:
    """
    Load prompt from external file based on phenomenon and task_type.

    Expected task_types: 'detection', 'replacement', 'detect_then_replace',
    'monolithic_replace', 'pipeline_replace', plus the pipeline sub-steps
    'explain' and 'transform' (loaded individually by the pipeline nodes).

    For task_type='pipeline_replace', this returns the concatenation of the
    three sub-step prompt files separated by marker lines, so the run
    document's `prompt_text` and `prompt_hash` uniquely identify the full
    pipeline prompt set.
    """
    if task_type == "pipeline_replace":
        parts = []
        for label, sub_task in (("DETECT", "detection"), ("EXPLAIN", "explain"), ("TRANSFORM", "transform")):
            parts.append(f"# === {label} ===\n" + load_prompt(phenomenon, sub_task))
        return "\n\n".join(parts)

    if task_type == "detection":
        prefix = "detect"
    elif task_type in ["replacement", "detect_then_replace"]:
        prefix = "replace"
    elif task_type == "monolithic_replace":
        prefix = "monolithic_replace"
    elif task_type == "explain":
        prefix = "explain"
    elif task_type == "transform":
        prefix = "transform"
    else:
        raise ValueError(f"Invalid task_type: {task_type}")

    path = f"prompts/{phenomenon}/{prefix}_{phenomenon}.txt"
    
    # Try multiple base paths for container/local development
    base_paths = [
        os.getcwd(),
        os.getenv("REPO_ROOT", "/app"),
        "/app",
        "/"
    ]
    
    for base in base_paths:
        full_path = os.path.join(base, path)
        if os.path.exists(full_path):
            with open(full_path, "r") as f:
                return f.read().strip()
                
    raise FileNotFoundError(f"Prompt file not found: {path} (searched in {base_paths})")

def compute_prompt_hash(prompt_text: str) -> str:
    """Compute SHA256 hash of prompt text."""
    return hashlib.sha256(prompt_text.encode("utf-8")).hexdigest()
