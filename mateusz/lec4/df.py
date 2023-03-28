#!/usr/bin/env python3

import json
import sys
from typing import Callable, Any, Tuple

from bril_utils import Instruction, BrilOp, BasicBlock, parse_code_line, Label, to_basic_blocks, find_top_block

from bril_utils.misc.utils import get_color_logging_object

import logging as log_module

log_module.basicConfig(level=log_module.DEBUG)

logging = get_color_logging_object()


DF_Val_Type = Any

def forward_df(
    blocks: list[BasicBlock],
    entry: BasicBlock,
    entry_val: DF_Val_Type,
    merge: Callable[[list[DF_Val_Type]], DF_Val_Type],
    transfer: Callable[[BasicBlock, DF_Val_Type], DF_Val_Type],
    init: DF_Val_Type,
) -> dict[BasicBlock, Tuple[list[DF_Val_Type], list[DF_Val_Type]]]:

    # == Sanity check first.

    # Make sure that we can rely on 'block.name' fields in further computations.
    if len(set([x.name for x in blocks])) != len(blocks):
        raise ValueError(f"Found blocks with duplicated names! {blocks}")

    # == Full algorithm implementation below.

    in_val = dict([(b, init) for b in blocks])
    in_val[entry] = entry_val
    out_val = dict([(b, init) for b in blocks])

    remaining = [x for x in blocks]
    
    while len(remaining):
        b = remaining.pop(0)
        logging.debug(f"DF: taking {b}")
        in_val[b] = merge([out_val[x] for x in b.prevs])
        out = transfer(b, in_val[b])
        if out != out_val[b]:
            remaining.extend(b.nexts)
            out_val[b] = out

    return dict(
        [(b, (in_val[b], out_val[b])) for b in blocks]
    )

def main(j: dict):
    """
    Computes LVN, modifies code in a way that applies lvn-related optimizations.
    """
    blocks = to_basic_blocks(j)
    entry = find_top_block(blocks)

    # Calculate reachable definitions for each basic block.

    Reaching_Def_Val_T = list[Instruction]

    def reaching_def_transfer(b: BasicBlock, in_val: Reaching_Def_Val_T) -> Reaching_Def_Val_T:

        in_val = [x for x in in_val]
        assignments = []

        for ins in b.code:
            if not ins.dest:
                continue
            in_val = ins.filter_out_killed_by_me(in_val)
            assignments.append(ins)
        
        return in_val + assignments


    def reaching_def_merge(vals: list[Reaching_Def_Val_T]) -> Reaching_Def_Val_T:
        from functools import reduce
        from operator import __add__
        return reduce(__add__, vals, [])

    mapping = forward_df(
        blocks=blocks,
        entry=entry,
        entry_val=[],
        init=[],
        transfer=reaching_def_transfer,
        merge=reaching_def_merge,
    )

    from pprint import pformat
    raise ValueError(pformat(mapping))
    

if __name__ == "__main__":
    text = str(sys.stdin.read())
    # print(text)
    j = json.loads(text)
    main(j)
    json.dump(j, sys.stdout, indent=2)