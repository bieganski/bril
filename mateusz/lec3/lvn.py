#!/usr/bin/env python3

import json
import sys
from typing import Optional
from dataclasses import dataclass, field

from dead_code_removal import main as DCR

@dataclass
class Record:
    canonical: str
    hash: tuple
    idx: int


class Numbering(dict):
    def __init__(self):
        super(self)
        self.fresh_idx = 0

    def _fresh(self):
        ret = self.fresh_idx
        self.fresh_idx += 1
        return ret

@dataclass
class State:
    records: dict[str, Record] = field(default_factory=dict)

def lvn_inplace(block: list):
    s = State()
    new_instructions = []
    for ins in block:
        if ins.get("dest") is None:
            # do nothing (eg. for 'print').
            new_instructions.append(ins)
            continue
        
        

def local_ssa_inplace(block: list):
    """
    Note that without control flow operations the SSA reduction is trival - 
    - one only needs to rename assignment destinations of alredy seen variables. 
    """
    
    def fresh():
        fresh_idx = 0
        while True:
            res = fresh_idx
            fresh_idx += 1
            yield f"renamed{res}"

    seen = set()
    env = dict()
    fresh_gen = fresh()
    for ins in block:
        args = ins.get("args", [])

        # update env with new variables first.
        ins["args"] = [env.get(x, x) for x in args]

        # optionally rename.
        dst = ins.get("dest")
        if dst is None:
            continue
        if dst in seen:
            # do rename.
            new_var = next(fresh_gen)
            ins["dest"] = new_var
            env[dst] = new_var
        
        seen.add(dst)



def main(j: dict):
    """
    Computes LVN, modifies code in a way that applies lvn-related optimizations.
    """
    
    for f in j["functions"]:
        instructions = f["instrs"]
        local_ssa_inplace(block=instructions)
        lvn_inplace(block=instructions)
    

if __name__ == "__main__":
    text = str(sys.stdin.read())
    # print(text)
    j = json.loads(text)
    main(j)
    json.dump(j, sys.stdout)