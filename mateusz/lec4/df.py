#!/usr/bin/env python3

import json
import sys

from bril_utils import Instruction, BrilOp, BasicBlock, parse_code_line, Label, to_basic_blocks

from typing import Callable, Any, Tuple

DF_Val_Type = Any

def forward_df(
    blocks: list[BasicBlock],
    entry: BasicBlock,
    merge: Callable[[list[DF_Val_Type]], DF_Val_Type],
    transfer: Callable[[BasicBlock, DF_Val_Type], DF_Val_Type],
    init: DF_Val_Type,
) -> dict[str, Tuple[list[DF_Val_Type], list[DF_Val_Type]]]:

    # == Sanity check first.

    # Make sure that we can rely on 'block.name' fields in further computations.
    if len(set([x.name for x in blocks])) != len(blocks):
        raise ValueError(f"Found blocks with duplicated names! {blocks}")

    # == Full algorithm implementation below.

    in_val = dict([(b.name, ...) for b in blocks])
    out_val = dict([(b.name, ...) for b in blocks])

    remaining = blocks
    
    while len(remaining):
        b = remaining.pop(0)
        in_val[b] = merge([out_val[x] for x in b.prevs])
        out = transfer(b, in_val[b])
        if out != out_val[b]:
            remaining.extend(b.nexts)

    return dict(
        [(b, (in_val[b], out_val[b])) for b in blocks]
    )

def main(j: dict):
    """
    Computes LVN, modifies code in a way that applies lvn-related optimizations.
    """
    blocks = to_basic_blocks(j)

    # Calculate reachable definitions for each basic block.

    mapping = forward_df(
        blocks=blocks,
        entry=...,
    )
    

if __name__ == "__main__":
    text = str(sys.stdin.read())
    # print(text)
    j = json.loads(text)
    main(j)
    json.dump(j, sys.stdout, indent=2)