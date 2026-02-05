# VU Amsterdam Metaphor Corpus (VUAMC)

This directory contains the VU Amsterdam Metaphor Corpus, a dataset annotated for linguistic metaphor. The corpus is a subset of the BNC Baby (British National Corpus), covering four registers: academic, news, fiction, and conversation.

## Files

- `VUAMC.xml`: The main corpus file containing the TEI P5 XML data with metaphor annotations.
- `header2541.xml`: Metadata header for the Oxford Text Archive deposit.
- `VUAMC.odd`, `VUAMC.rnc`, `VUAMC.rng`: Schema definition files (TEI ODD, RELAX NG).

## Data Structure

The data is in TEI P5 XML format.
- **Documents**: `<text>` elements within the `<group>`.
- **Sentences**: `<s>` elements.
- **Tokens**: `<w>` (words) and `<c>` (punctuation).
- **Metaphors**: Annotated using the `<seg>` element with `function="mrw"` (Metaphor Related Word).
  - Example: `<seg function="mrw" type="met">reveals</seg>`

## Reference

- Paper: [VU Amsterdam Metaphor Corpus](https://research.vu.nl/ws/portalfiles/portal/311531885/VU_Amsterdam_Metaphor_Corpus.pdf)
- Original Authors: Gerard J. Steen, Aletta G. Dorst, J. Berenike Herrmann, Anna A. Kaal, Tina Krennmayr.
