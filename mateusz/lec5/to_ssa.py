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

    entry_frontiers = calculate_dominance_frontiers(
        for_who=entry,
        blocks=blocks
    )

    raise ValueError((entry_frontiers))

    # new_blocks = to_ssa(
    #     blocks=blocks,
    #     entry=entry
    # )
    # from pprint import pformat
    # raise ValueError(pformat(new_blocks))



def calculate_dominance_frontiers(for_who: BasicBlock, blocks: list[BasicBlock]) -> list[BasicBlock]:
    from copy import copy
    from functools import reduce
    
    raise NotImplementedError()

if __name__ == "__main__":
    text = str(sys.stdin.read())
    # print(text)
    j = json.loads(text)
    main(j)
    json.dump(j, sys.stdout, indent=2)