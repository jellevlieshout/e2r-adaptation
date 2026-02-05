import xml.etree.ElementTree as ET
from typing import Iterator, Optional
from pathlib import Path
from .models import Document, Sentence, Token

class VUAMCClient:
    NAMESPACES = {
        'tei': 'http://www.tei-c.org/ns/1.0',
        'vici': 'http://www.tei-c.org/ns/VICI'
    }

    def __init__(self, xml_path: str):
        self.xml_path = Path(xml_path)
        if not self.xml_path.exists():
            raise FileNotFoundError(f"File not found: {self.xml_path}")

    def documents(self) -> Iterator[Document]:
        """
        Iterates over documents in the VUAMC XML file. 
        Using iterparse to avoid loading the whole tree if possible, 
        but given the structure (nested text in group), we might need to be careful.
        However, since the file is ~16MB, standard parse is acceptable and safer for structure.
        """
        tree = ET.parse(self.xml_path)
        root = tree.getroot()
        
        # The structure is TEI -> text -> group -> text
        # We want to iterate over the inner texts
        
        # Find the group element
        group = root.find('.//tei:group', self.NAMESPACES)
        if group is None:
            # Fallback if there is no group (maybe single text)
            texts = root.findall('tei:text', self.NAMESPACES)
        else:
            texts = group.findall('tei:text', self.NAMESPACES)

        for text_elem in texts:
            doc_id = text_elem.get(f"{{http://www.w3.org/XML/1998/namespace}}id")
            if not doc_id:
                doc_id = "unknown"
            
            sentences = []
            body = text_elem.find('tei:body', self.NAMESPACES)
            if body:
                # Find all sentences 's' in the body
                # Note: 's' can be nested in 'p', 'div1', etc.
                # using .//tei:s to find all descendants
                for s_elem in body.findall('.//tei:s', self.NAMESPACES):
                    s_id = s_elem.get('n')
                    if not s_id:
                        s_id = "unknown"
                    
                    tokens = []
                    # Iterate over children to maintain order of words and punctuation
                    # We look for 'w' (word) and 'c' (punctuation)
                    # Note: XML elements are ordered, so iterating over children is correct.
                    # However, .findall() only does direct children or recursive by tag. 
                    # We need to iterate over all children and check tag.
                    
                    for child in s_elem:
                        tag_name = child.tag.replace(f"{{{self.NAMESPACES['tei']}}}", "")
                        
                        if tag_name == 'w':
                            # Check for seg[@function='mrw'] inside w
                            # The structure seen is <w><seg>text</seg></w>
                            # So the text of the word is actually inside the seg if it is present?
                            # Let's check the file content again.
                            # <w ...><seg ...>reveals</seg></w> -> text is in seg.text
                            # <w ...>Roland </w> -> text is in w.text
                            
                            is_metaphor = False
                            metaphor_type = None
                            function = None
                            
                            seg = child.find('tei:seg', self.NAMESPACES)
                            if seg is not None:
                                # It has a segment, check if it is mrw or mFlag
                                seg_function = seg.get('function')
                                if seg_function in ('mrw', 'mFlag'):
                                    is_metaphor = True
                                    metaphor_type = seg.get('type')
                                    function = seg_function
                                    # Map 'subtype' to 'status' as per observation of XML structure
                                    # The text mentions 'status' code but XML uses 'subtype' for WIDLII, PP
                                    status = seg.get('subtype')
                                    if status:
                                        # Clean up status if needed, but it seems to be just the code
                                        pass
                                
                                token_text = seg.text or ""
                                if seg.tail:
                                    token_text += seg.tail
                            else:
                                token_text = child.text or ""
                            
                            # Append tail of w if any (usually space, but that's handled by joining usually)
                            # In this corpus, spaces seem to be included in text: "Latest "
                            
                            token_text = token_text.strip()
                            
                            tokens.append(Token(
                                text=token_text,
                                lemma=child.get('lemma', '').strip(),
                                pos=child.get('type', ''),
                                is_metaphor=is_metaphor,
                                metaphor_type=metaphor_type,
                                function=function,
                                status=status if is_metaphor else None
                            ))
                            
                        elif tag_name == 'c':
                            tokens.append(Token(
                                text=(child.text or "").strip(),
                                lemma=(child.text or "").strip(),
                                pos='PUNCT'
                            ))
                            
                    sentences.append(Sentence(id=s_id, tokens=tokens))
            
            yield Document(id=doc_id, sentences=sentences)
