from clients.semeval2022.client import SemEval2022Client
import sys
from pathlib import Path

# Adjust path based on where this is run (container vs host)
# In container, datasets are likely at /datasets
DATASET_PATH = "/datasets/SemEval2022_Task2"

def verify():
    print(f"Verifying SemEval2022Client with path: {DATASET_PATH}")
    client = SemEval2022Client(DATASET_PATH)
    
    print("\n--- Testing Task A (Train) ---")
    count = 0
    for sample in client.list_samples(task='A', split='train'):
        print(f"Sample: {sample.id} | MWE: {sample.mwe1} | Lang: {sample.language}")
        count += 1
        if count >= 3:
            break
            
    if count == 0:
        print("WARNING: No samples found for Task A Train")
        
    print("\n--- Testing Task B (Dev) ---")
    count = 0
    for sample in client.list_samples(task='B', split='dev'):
        print(f"Sample: {sample.id} | MWE: {sample.mwe1} | Lang: {sample.language}")
        count += 1
        if count >= 3:
            break

    if count == 0:
        print("WARNING: No samples found for Task B Dev")

    print("\n--- Testing Filter by Language (EN) ---")
    count = 0
    for sample in client.list_samples(task='A', language='EN'):
        if sample.language != 'EN':
             print(f"ERROR: Found non-EN sample: {sample.language}")
        count += 1
        if count >= 3:
            break
            
    print("\nVerification Complete")

if __name__ == "__main__":
    try:
        verify()
    except Exception as e:
        print(f"Verification Failed: {e}")
        sys.exit(1)
