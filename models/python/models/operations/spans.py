"""
Span normalization — PLAN.md §7.
Must be applied before storage and before evaluation.
"""

from typing import List
from models.types.shared import Span


def normalize_spans(spans: List[Span], text_length: int) -> List[Span]:
    """
    Normalize a list of spans per PLAN.md §7:
    1. Sort spans by start position
    2. Merge overlapping spans
    3. Clip to boundaries [0, text_length]
    4. Remove zero-length spans

    Args:
        spans: List of Span objects to normalize
        text_length: Length of the text (used for clipping)

    Returns:
        Normalized list of Span objects
    """
    if not spans:
        return []

    # 1. Sort by start position
    sorted_spans = sorted(spans, key=lambda s: (s.start, s.end))

    # 3. Clip to boundaries first (before merging, so merge sees clipped values)
    clipped = []
    for s in sorted_spans:
        start = max(0, s.start)
        end = min(text_length, s.end)
        # 4. Remove zero-length spans
        if start < end:
            clipped.append(Span(start=start, end=end))

    if not clipped:
        return []

    # 2. Merge overlapping spans
    merged = [clipped[0]]
    for span in clipped[1:]:
        last = merged[-1]
        if span.start <= last.end:
            # Overlapping or adjacent — merge
            merged[-1] = Span(start=last.start, end=max(last.end, span.end))
        else:
            merged.append(span)

    return merged
