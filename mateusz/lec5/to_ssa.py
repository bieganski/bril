#!/usr/bin/env python3

import json
import sys
from typing import Any, Sequence
from collections import defaultdict

from bril_utils.misc.utils import get_color_logging_object
from bril_utils import BasicBlock, Instruction, to_basic_blocks, calculate_dominators, uses


import logging as log_module

log_module.basicConfig(level=log_module.DEBUG)

logging = get_color_logging_object()


DF_Val_Type = Any


def _flatten(lst):
    from functools import reduce
    from operator import __add__
    return reduce(__add__, lst, [])


def calculate_defs(blocks: Sequence[BasicBlock]) -> dict[str, Sequence[BasicBlock]]:
    res = defaultdict(set)
    for b in blocks:
        for ins in b.code:
            if ins.dest is not None:
                res[ins.dest].add(b)
    return dict(res) # type: ignore

def to_ssa(
    blocks: list[BasicBlock],
    entry: BasicBlock,
) -> list[BasicBlock]:
    frontiers = calculate_dominance_frontiers(blocks)
    # left, = [x for x in blocks if x.name == "left"]
    # raise ValueError(frontiers[left])
    defs = calculate_defs(blocks)
    
    for name, def_blocks in defs.items():
        for db in def_blocks:
            for f in frontiers[db]:
                pass
    
    return [] # XXX mypy


def main(j: dict):
    _blocks = to_basic_blocks(j)
    entry, blocks = _blocks["main"]

    new_blocks = to_ssa(
        blocks=blocks,
        entry=entry,
    )
    from pprint import pformat
    raise ValueError(pformat(new_blocks))



def calculate_dominance_frontiers(blocks: list[BasicBlock]) -> dict[BasicBlock, set[BasicBlock]]:

    dominators : dict[BasicBlock, set[BasicBlock]] = calculate_dominators(blocks)

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