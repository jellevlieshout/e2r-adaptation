import hashlib
import os
from typing import Optional

def load_prompt(phenomenon: str, task_type: str) -> str:
    """
    Load prompt from external file based on phenomenon and task_type.
    
    Expected task_types: 'detection', 'replacement', 'detect_then_replace'
    """
    if task_type == "detection":
        prefix = "detect"
    elif task_type in ["replacement", "detect_then_replace"]:
        prefix = "replace"
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
