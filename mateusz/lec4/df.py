#!/usr/bin/env python3

import json
import sys
from typing import Callable, Any, Tuple

from bril_utils import Instruction, BasicBlock, to_basic_blocks, calculate_dominators
from bril_utils.misc.utils import get_color_logging_object
from bril_utils.algo.df import calculate_reaching_defs

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
    blocks = to_basic_blocks(j)
    entry, blocks = blocks["main"] # XXX
    res = calculate_reaching_defs(
        blocks=blocks,
        entry=entry,
    )
    from pprint import pformat
    raise ValueError(pformat(res))

if __name__ == "__main__":
    text = str(sys.stdin.read())
    # print(text)
    j = json.loads(text)
    main(j)
    json.dump(j, sys.stdout, indent=2)