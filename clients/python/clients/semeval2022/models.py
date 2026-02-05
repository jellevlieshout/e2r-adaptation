from dataclasses import dataclass
from typing import Optional

@dataclass
class SemEvalSample:
    """
    Represents a sample from the SemEval 2022 Task 2 dataset (CSV format).
    
    Attributes:
        id: Unique identifier for the sample (e.g., 'train_one_shot.en.1.1').
        mwe1: The first multi-word expression (idiom).
        mwe2: The second multi-word expression (usually None or alternative).
        language: Language code (e.g., 'EN', 'PT', 'GL').
        sentence1: The first sentence containing the MWE.
        sentence2: The second sentence containing the MWE (context variants).
        sim: Similarity score or label.
        alternative1: Alternative expression 1.
        alternative2: Alternative expression 2.
    """
    id: str
    mwe1: str
    language: str
    sentence1: str
    sentence2: Optional[str] = None
    mwe2: Optional[str] = None
    sim: Optional[str] = None
    label: Optional[str] = None
    context_previous: Optional[str] = None
    context_next: Optional[str] = None
    setting: Optional[str] = None
    alternative1: Optional[str] = None
    alternative2: Optional[str] = None
