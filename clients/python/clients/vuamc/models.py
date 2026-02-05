from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class Token:
    text: str
    lemma: str
    pos: str
    is_metaphor: bool = False
    metaphor_type: Optional[str] = None  # e.g., 'met', 'personification'
    function: Optional[str] = None # e.g., 'mrw', 'mflag'

    def __str__(self):
        return self.text

@dataclass
class Sentence:
    id: str
    tokens: List[Token] = field(default_factory=list)

    @property
    def text(self) -> str:
        return " ".join([t.text for t in self.tokens])

    def has_metaphor(self) -> bool:
        return any(t.is_metaphor for t in self.tokens)

@dataclass
class Document:
    id: str
    sentences: List[Sentence] = field(default_factory=list)
