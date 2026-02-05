from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class Token:
    """
    Represents a token in the VU Amsterdam Metaphor Corpus.
    
    Attributes:
        text: The actual text of the token.
        lemma: The lemma of the token.
        pos: Part of speech tag.
        is_metaphor: 
            Indicates if the token is related to a cross-domain mapping (MIPVU protocol).
            This includes indirect, direct, and implicit metaphors.
            Example: 'valuable' in "to do valuable work" is metaphorical because it contrasts with the basic meaning "worth a lot of money".
        metaphor_type: 
            The type of metaphor.
            - 'met': Indirect metaphor (e.g., "valuable work").
            - 'lit': Direct metaphor / Simile (e.g., "he's like a ferret").
            - 'impl': Implicit metaphor (e.g., "to embark on such a step... realizing it" where 'it' refers to something metaphorical).
        function: 
            The function/tag type in the XML.
            - 'mrw': Metaphor related word (general code for candidates expressing cross-domain mapping).
            - 'mflag': Metaphor flag (signals comparison, e.g., 'like', 'as if', 'in the role of').
        status:
            Additional status codes for ambiguity or special cases.
            - 'WIDLII': "When In Doubt, Leave It In". Used for ambiguous cases where both metaphorical and non-metaphorical interpretations are possible.
                        Example: "driven up the bumpy Forest Drive" (could be physical elevation or abstract 'up').
            - 'PP': Possible Personification. Example: "A party can't even decide its name" ('decide' is human activity, 'party' is abstract).
            - 'UNCERTAIN': Used when annotators were unsure (mostly internal use).
    """
    text: str
    lemma: str
    pos: str
    is_metaphor: bool = False
    metaphor_type: Optional[str] = None  # e.g., 'met', 'lit', 'impl'
    function: Optional[str] = None # e.g., 'mrw', 'mflag'
    status: Optional[str] = None # e.g., 'WIDLII', 'PP', 'UNCERTAIN'

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
