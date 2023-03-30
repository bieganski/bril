#!/usr/bin/env python3

import json
import sys
from typing import Any

from bril_utils.misc.utils import get_color_logging_object
from bril_utils import BasicBlock, to_basic_blocks, find_top_block, calculate_dominators


import logging as log_module

log_module.basicConfig(level=log_module.DEBUG)

logging = get_color_logging_object()


DF_Val_Type = Any

def to_ssa(
    blocks: list[BasicBlock],
    entry: BasicBlock,
) -> list[BasicBlock]:
    raise NotImplementedError()

def main(j: dict):
    """
    Computes LVN, modifies code in a way that applies lvn-related optimizations.
    """
    blocks = to_basic_blocks(j)
    entry = find_top_block(blocks)

    frontiers = calculate_dominance_frontiers(
        blocks=blocks
    )
    raise ValueError(frontiers[entry])

    # new_blocks = to_ssa(
    #     blocks=blocks,
    #     entry=entry
    # )
    # from pprint import pformat
    # raise ValueError(pformat(new_blocks))



def calculate_dominance_frontiers(blocks: list[BasicBlock]) -> dict[BasicBlock, set[BasicBlock]]:

    dominators : dict[BasicBlock, set(BasicBlock)] = calculate_dominators(blocks)

    from collections import defaultdict

    frontiers = defaultdict(set)

    for b, ds in dominators.items():
        for n in b.nexts:
            for d in ds:
                if d not in dominators[n]:
                    frontiers[d].add(n)
    
    return frontiers
            
    

if __name__ == "__main__":
    text = str(sys.stdin.read())
    # print(text)
    j = json.loads(text)
    main(j)
    json.dump(j, sys.stdout, indent=2)