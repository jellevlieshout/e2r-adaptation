"""
Dataset ingestion operations — PLAN.md §5.1.
Converts raw dataset client objects into DatasetExampleData for Couchbase storage.
"""

from typing import Dict, List, Optional, Tuple
import logging

from models.types.shared import DatasetType, PhenomenonType, DetectionResult, Span
from models.entities.dataset_example import DatasetExampleData
from models.operations.spans import normalize_spans

logger = logging.getLogger(__name__)


def parse_vu_sentence(doc_id: str, sentence) -> DatasetExampleData:
    """
    Convert a VUAMCClient Sentence into a DatasetExampleData.

    Builds token_labels from is_metaphor flags, derives character-offset spans
    from token positions, and normalizes spans per PLAN.md §7.

    Args:
        doc_id: The VUAMC document ID (e.g., 'a1e-fragment01')
        sentence: A vuamc.models.Sentence object with .id, .tokens

    Returns:
        DatasetExampleData ready for Couchbase storage
    """
    tokens_text = [t.text for t in sentence.tokens]
    token_labels = [1 if t.is_metaphor else 0 for t in sentence.tokens]

    # Reconstruct text and compute character offsets per token
    # Tokens are joined with spaces to form the sentence text
    text = " ".join(tokens_text)

    # Build character-offset spans from metaphor token positions
    spans: List[Span] = []
    char_pos = 0

    for i, token in enumerate(sentence.tokens):
        token_start = char_pos
        token_end = char_pos + len(token.text)

        if token.is_metaphor:
            spans.append(Span(start=token_start, end=token_end))

        # Move past token + space separator
        char_pos = token_end + 1

    # Normalize spans (sort, merge adjacent/overlapping, clip, remove zero-length)
    spans = normalize_spans(spans, len(text))

    is_figurative = any(label == 1 for label in token_labels)

    example_id = f"{doc_id}_s{sentence.id}"

    return DatasetExampleData(
        dataset=DatasetType.VU_AMSTERDAM,
        phenomenon=PhenomenonType.METAPHOR,
        example_id=example_id,
        text=text,
        tokens=tokens_text,
        gold_detection=DetectionResult(
            is_figurative=is_figurative,
            token_labels=token_labels,
            spans=spans,
        ),
        gold_replacement=None,
        metadata={
            "source_doc": doc_id,
            "sentence_n": sentence.id,
        },
    )


def build_semeval_replacement_map(client) -> Dict[Tuple[str, str], Dict]:
    """
    Build a lookup from SubTask B data for sentence-level replacements.

    Reads SubTask B samples and builds a dict keyed by (mwe_lower, language)
    mapping to sentence replacement info.

    Args:
        client: A SemEval2022Client instance

    Returns:
        Dict mapping (mwe, language) -> {
            "gold_sentence_original": str,
            "gold_sentence_replacement": str,
        }
    """
    replacement_map: Dict[Tuple[str, str], Dict] = {}

    for sample in client.list_samples(task='B'):
        if sample.sentence1 and sample.sentence2:
            # Use similarity score to pick the best match
            # sim=1 means the paraphrase preserves meaning (literal replacement)
            # sim=None or sim != "1" means it doesn't preserve meaning well
            sim = sample.sim
            if sim is not None and str(sim).strip() == "1":
                key = (sample.mwe1.lower().strip(), sample.language.upper())
                # Only store first match per MWE+language (avoid duplicates)
                if key not in replacement_map:
                    replacement_map[key] = {
                        "gold_sentence_original": sample.sentence1,
                        "gold_sentence_replacement": sample.sentence2,
                    }

    logger.info(f"Built SemEval replacement map with {len(replacement_map)} entries")
    return replacement_map


def parse_semeval_sample(
    sample,
    replacement_map: Optional[Dict[Tuple[str, str], Dict]] = None,
) -> Optional[DatasetExampleData]:
    """
    Convert a SemEval2022Client Task A sample into a DatasetExampleData.

    Locates the MWE in the target sentence to compute character-offset spans.
    Optionally enriches with SubTask B sentence replacement data from the map.

    Args:
        sample: A SemEvalSample from Task A (with sentence1=Target, label, mwe1)
        replacement_map: Optional dict from build_semeval_replacement_map()

    Returns:
        DatasetExampleData ready for Couchbase storage, or None if text is empty
    """
    text = (sample.sentence1 or "").strip()
    if not text:
        return None

    mwe = sample.mwe1 or ""
    is_figurative = str(sample.label).strip() == "1"

    # Find MWE span in the target text (case-insensitive search)
    spans: List[Span] = []
    if mwe:
        text_lower = text.lower()
        mwe_lower = mwe.lower()
        pos = text_lower.find(mwe_lower)
        if pos >= 0:
            spans.append(Span(start=pos, end=pos + len(mwe)))
        else:
            # MWE not found verbatim — store without span
            logger.debug(f"MWE '{mwe}' not found in text for sample {sample.id}")

    spans = normalize_spans(spans, len(text))

    # Build metadata
    metadata: Dict = {
        "mwe": mwe,
        "language": sample.language,
    }

    if sample.context_previous:
        metadata["context_previous"] = sample.context_previous
    if sample.context_next:
        metadata["context_next"] = sample.context_next
    if sample.setting:
        metadata["setting"] = sample.setting

    # Enrich with SubTask B sentence replacement if available
    if replacement_map and mwe:
        key = (mwe.lower().strip(), (sample.language or "EN").upper())
        replacement_info = replacement_map.get(key)
        if replacement_info:
            metadata["gold_sentence_original"] = replacement_info["gold_sentence_original"]
            metadata["gold_sentence_replacement"] = replacement_info["gold_sentence_replacement"]

    return DatasetExampleData(
        dataset=DatasetType.SEMEVAL,
        phenomenon=PhenomenonType.IDIOM,
        example_id=sample.id,
        text=text,
        tokens=None,
        gold_detection=DetectionResult(
            is_figurative=is_figurative,
            spans=spans,
        ),
        gold_replacement=None,
        metadata=metadata,
    )
