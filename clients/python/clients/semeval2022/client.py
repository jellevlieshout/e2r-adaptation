import csv
from pathlib import Path
from typing import Iterator, Optional, List
import logging

from .models import SemEvalSample

class SemEval2022Client:
    def __init__(self, dataset_path: str):
        self.dataset_path = Path(dataset_path)
        if not self.dataset_path.exists():
            raise FileNotFoundError(f"Dataset path not found: {self.dataset_path}")

    def _resolve_files(self, task: Optional[str] = None, split: Optional[str] = None) -> Iterator[Path]:
        """
        Resolves CSV files based on task and split filters.
        """
        # Define paths to check. This is a bit of a heuristic given the folder structure.
        # Structure:
        # /datasets/SemEval2022_Task2/
        #   SubTaskA/
        #     Data/ (train/dev/eval)
        #     TestData/ (test)
        #   SubTaskB/
        #     TrainData/
        #     EvaluationData/ (dev/eval)
        #     TestData/ (test)

        paths_to_check = []

        if task:
            if task.upper() == 'A':
                paths_to_check.append(self.dataset_path / "SubTaskA")
            elif task.upper() == 'B':
                paths_to_check.append(self.dataset_path / "SubTaskB")
        else:
            paths_to_check.append(self.dataset_path / "SubTaskA")
            paths_to_check.append(self.dataset_path / "SubTaskB")
        
        for task_dir in paths_to_check:
            if not task_dir.exists():
                continue

            # Walk through all subdirectories to find CSVs
            # We need to map 'split' to filenames or folder locations
            
            # Simple recursive search for CSVs, then filter by filename
            for path in task_dir.rglob("*.csv"):
                filename = path.name.lower()
                
                # Filter by split if requested
                if split:
                    if split.lower() == 'train':
                        # train_data.csv, train_one_shot.csv, train_zero_shot.csv
                        if 'train' not in filename:
                            continue
                    elif split.lower() == 'dev':
                        # dev.csv, dev_gold.csv
                         if 'dev' not in filename:
                             continue
                    elif split.lower() == 'test':
                         # test.csv
                         if 'test' not in filename:
                             continue
                    # What if 'eval' is requested?
                
                # Skip submission format files
                if 'submission_format' in filename:
                    continue

                if 'gold' in filename:
                    continue

                yield path

    def list_samples(self, task: Optional[str] = None, split: Optional[str] = None, language: Optional[str] = None) -> Iterator[SemEvalSample]:
        """
        Iterates over samples in the dataset, optionally filtered by task, split, and language.
        """
        for csv_path in self._resolve_files(task, split):
            try:
                with open(csv_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    fieldnames = reader.fieldnames or []
                    
                    is_task_a = 'DataID' in fieldnames
                    
                    for row in reader:
                        # Filter by language if requested
                        row_lang = row.get('Language')
                        if language and row_lang and row_lang.upper() != language.upper():
                            continue
                            
                        if is_task_a:
                            # Task A: DataID,Language,MWE,Setting,Previous,Target,Next,Label
                            yield SemEvalSample(
                                id=row.get('DataID', ''),
                                mwe1=row.get('MWE', ''),
                                language=row.get('Language', ''),
                                sentence1=row.get('Target', ''),
                                sentence2=None, # Task A doesn't have a second sentence
                                label=row.get('Label'),
                                setting=row.get('Setting'),
                                context_previous=row.get('Previous'),
                                context_next=row.get('Next')
                            )
                        else:
                            # Task B: ID,MWE1,MWE2,Language,sentence_1,sentence_2,sim,alternative_1,alternative_2
                            # Handling variations: sentence_1 vs sentence1
                            s1 = row.get('sentence_1') or row.get('sentence1') or ''
                            s2 = row.get('sentence_2') or row.get('sentence2')
                            
                            yield SemEvalSample(
                                id=row.get('ID', ''),
                                mwe1=row.get('MWE1', ''),
                                mwe2=row.get('MWE2'),
                                language=row.get('Language', ''),
                                sentence1=s1,
                                sentence2=s2,
                                sim=row.get('sim'),
                                alternative1=row.get('alternative_1'),
                                alternative2=row.get('alternative_2')
                            )
            except Exception as e:
                logging.error(f"Error reading file {csv_path}: {e}")
                continue
