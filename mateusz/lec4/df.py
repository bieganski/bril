#!/usr/bin/env python3

import json
import sys

from bril_utils import Instruction, BrilOp, BasicBlock, parse_code_line, Label, to_basic_blocks



def main(j: dict):
    """
    Computes LVN, modifies code in a way that applies lvn-related optimizations.
    """
    blocks = to_basic_blocks(j)

    from pprint import pformat
    raise ValueError(pformat(blocks))
    # for _ in range(5):
    #     DCR(j)
    

if __name__ == "__main__":
    text = str(sys.stdin.read())
    # print(text)
    j = json.loads(text)
    main(j)
    json.dump(j, sys.stdout, indent=2)