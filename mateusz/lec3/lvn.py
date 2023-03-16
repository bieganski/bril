#!/usr/bin/env python3

import json
import sys

from dead_code_removal import main as DCR

from dataclasses import dataclass

@dataclass
class State:
    pass

def create_lvn_mapping(s: State, j: dict):
    """
    @param 'j' is a subdict, only for a function or basic block (it needs to have 'instrs' as a direct child!)
    """
    for ins in j["instrs"]:
        raise ValueError(ins)

def reassign_code_inplace(s: State, j: dict):
    """
    @param 'j' is a subdict, only for a function or basic block (it needs to have 'instrs' as a direct child!)
    """
    pass

def main(j: dict):
    """
    Computes LVN, modifies code in a way that applies lvn-related optimizations.
    """
    
    for f in j["functions"]:
        s = State()
        jj = f["instrs"]
        create_lvn_mapping(   s=s, j=jj)
        reassign_code_inplace(s=s, j=jj)
    

if __name__ == "__main__":
    text = str(sys.stdin.read())
    # print(text)
    j = json.loads(text)
    main(j)
    json.dump(j, sys.stdout)