from dataclasses import dataclass
from typing import Tuple
import numpy as np

@dataclass
class Layout:
    shape: Tuple[int, ...]
    stride: Tuple[int, ...]
    raw: str

    def __hash__(self):
        return hash(self.shape) ^ hash(self.stride) ^ hash(self.raw)

class Tensor:
    layout: Layout
    data: np.ndarray

def parse_layout(layout: str):
    return Layout(shape=(0,), stride=(0,), raw=layout)
    