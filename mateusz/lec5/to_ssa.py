#!/usr/bin/env python3

import json
import sys
from typing import Any, Sequence, Optional
from collections import defaultdict

from bril_utils.misc.utils import get_color_logging_object
from bril_utils import Instruction, BasicBlock, to_basic_blocks, calculate_dominators, uses
from bril_utils.algo.df import calculate_reaching_defs_dict


import logging as log_module

log_module.basicConfig(level=log_module.DEBUG)

logging = get_color_logging_object()


from pprint import pformat # XXX


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

    new_blocks = [x for x in blocks] # copy.

    from functools import reduce
    from operator import __add__

    defs = calculate_defs(blocks)
    vars = reduce(__add__, defs.keys())

    frontiers = calculate_dominance_frontiers(blocks=blocks)

    for v in vars:
        for b in defs[v]:
            # 'v' was assigned in a block 'b'.
            # for each dominance frontier of 'b' we should seek for 'v' as well?
            for b_df in frontiers[b]:
                pass

    return new_blocks


def main(j: dict):
    _blocks = to_basic_blocks(j)
    entry, blocks = _blocks["main"]

    new_blocks = to_ssa(
        blocks=blocks,
        entry=entry,
    )
    raise ValueError(pformat(new_blocks))



def calculate_dominance_frontiers(blocks: list[BasicBlock]) -> dict[BasicBlock, set[BasicBlock]]:

    dominators : dict[BasicBlock, set[BasicBlock]] = calculate_dominators(blocks)

    from collections import defaultdict
    frontiers = defaultdict(set)

    for node in blocks:
        for p in node.prevs:
            if p not in dominators[node]:
                # node is not dominated by some of it's direct ancestor 'p'.
                # so it must be a frontier for all of 'p's dominators.
                for x in dominators[p]:
                    if x not in dominators[node]:
                        logging.info(f"{p} does not dominate {node} and {x} dominates {p} __AND__ {x} does not dominate {node}, so {node} is a frontier of {x}")
                        frontiers[x].add(node)

    return dict(frontiers)
            
    

if __name__ == "__main__":
    text = str(sys.stdin.read())
    # print(text)
    j = json.loads(text)
    main(j)
    json.dump(j, sys.stdout, indent=2)