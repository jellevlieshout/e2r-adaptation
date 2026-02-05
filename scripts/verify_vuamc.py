import sys
from pathlib import Path

# Add clients/python to sys.path
repo_root = Path(__file__).parent.parent
sys.path.append(str(repo_root / "clients" / "python"))

from clients.vuamc import VUAMCClient

def main():
    xml_path = repo_root / "datasets" / "vu-amsterdam-metaphor-corpus" / "VUAMC.xml"
    print(f"Loading VUAMC from {xml_path}")
    
    client = VUAMCClient(str(xml_path))
    
    metaphor_count = 0
    doc_count = 0
    
    try:
        for doc in client.documents():
            doc_count += 1
            print(f"Document ID: {doc.id}")
            print(f"Sentences: {len(doc.sentences)}")
            
            for sentence in doc.sentences[:3]:  # Print first 3 sentences
                print(f"  Sentence {sentence.id}: {sentence.text}")
                if sentence.has_metaphor():
                    for token in sentence.tokens:
                        if token.is_metaphor:
                            print(f"    [METAPHOR] '{token.text}' (type: {token.metaphor_type})")
                            metaphor_count += 1
            
            if doc_count >= 5:
                break
                
        print(f"\nVerification finished. Processed {doc_count} documents.")
        print(f"Found {metaphor_count} metaphors in sampled sentences.")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
