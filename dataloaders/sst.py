# https://github.com/munikarmanish/bert-sentiment/blob/master/bert_sentiment/data.py
"""This module defines a configurable SSTDataset class."""

import pytreebank
import torch
from pytorch_transformers import BertTokenizer
from torch.utils.data import Dataset

tokenizer = BertTokenizer.from_pretrained("bert-large-uncased")

sst = pytreebank.load_sst()

def rpad(array, n=70):
    """Right padding."""
    current_len = len(array)
    if current_len > n:
        return array[: n - 1]
    extra = n - current_len
    return array + ([0] * extra)


def get_binary_label(label):
    """Convert fine-grained label to binary label."""
    if label < 2:
        return 0
    if label > 2:
        return 1
    raise ValueError("Invalid label")


class SSTDataset(Dataset):
    """Configurable SST Dataset.
    
    Things we can configure:
        - split (train / val / test)
        - root / all nodes
        - binary / fine-grained
    """

    def __init__(self, split="train", root=True, binary=True):
        """Initializes the dataset with given configuration.

        Args:
            split: str
                Dataset split, one of [train, val, test]
            root: bool
                If true, only use root nodes. Else, use all nodes.
            binary: bool
                If true, use binary labels. Else, use fine-grained.
        """
        logger.info(f"Loading SST {split} set")
        self.sst = sst[split]

        logger.info("Tokenizing")
        if root and binary:
            self.data = [
                (
                    rpad(
                        tokenizer.encode("[CLS] " + tree.to_lines()[0] + " [SEP]"), n=66
                    ),
                    get_binary_label(tree.label),
                )
                for tree in self.sst
                if tree.label != 2
            ]
        elif root and not binary:
            self.data = [
                (
                    rpad(
                        tokenizer.encode("[CLS] " + tree.to_lines()[0] + " [SEP]"), n=66
                    ),
                    tree.label,
                )
                for tree in self.sst
            ]
        elif not root and not binary:
            self.data = [
                (rpad(tokenizer.encode("[CLS] " + line + " [SEP]"), n=66), label)
                for tree in self.sst
                for label, line in tree.to_labeled_lines()
            ]
        else:
            self.data = [
                (
                    rpad(tokenizer.encode("[CLS] " + line + " [SEP]"), n=66),
                    get_binary_label(label),
                )
                for tree in self.sst
                for label, line in tree.to_labeled_lines()
                if label != 2
            ]

    def __len__(self):
        return len(self.data)

    def __getitem__(self, index):
        X, y = self.data[index]
        X = torch.tensor(X)
        return X, y

def load_sst():

    train_ds = SSTDataset(split="train", root=True, binary=True)
    val_ds = SSTDataset(split="dev", root=True, binary=True)
    test_ds = SSTDataset(split="test", root=True, binary=True)

    train_dl = torch.utils.data.DataLoader(
        train_ds, batch_size=32, shuffle=True, num_workers=4
    )
    val_dl = torch.utils.data.DataLoader(
        val_ds, batch_size=32, shuffle=False, num_workers=4
    )
    test_dl = torch.utils.data.DataLoader(
        test_ds, batch_size=32, shuffle=False, num_workers=4
    )

    return train_dl, val_dl, test_dl