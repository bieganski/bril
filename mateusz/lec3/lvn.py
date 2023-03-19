#!/usr/bin/env python3

import json
import sys
from typing import Optional
from dataclasses import dataclass, field
from enum import Enum, unique
from copy import deepcopy

from dead_code_removal import main as DCR

@dataclass
class Record:
    canonical: str
    hash: tuple

@dataclass
class State:
    records: list[Record] = field(default_factory=list)
    mapping : dict[str, Record] = field(default_factory=dict)

@unique
class BrilOp(Enum):
    CONST = "const"
    JUMP = "jmp"
    ID = "id"
    PRINT = "print"
    CALL = "call"

    ADD = "add"
    MUL = "mul"
    SUB = "sub"
    DIV = "div"
    GT = "gt"
    LT = "lt"
    GE = "ge"
    LE = "le"
    NE = "ne"
    EQ = "eq"
    OR = "or"
    AND = "and"
    NOT = "not"

COMMUTE_OPS = {
    BrilOp.ADD,
    BrilOp.MUL,
}

FOLDABLE_OPS = {
    BrilOp.ADD:     lambda a, b: a + b,
    BrilOp.MUL:     lambda a, b: a * b,
    BrilOp.SUB:     lambda a, b: a - b,
    BrilOp.DIV:     lambda a, b: a // b,
    BrilOp.GT:      lambda a, b: a > b,
    BrilOp.LT:      lambda a, b: a < b,
    BrilOp.GE:      lambda a, b: a >= b,
    BrilOp.LE:      lambda a, b: a <= b,
    BrilOp.NE:      lambda a, b: a != b,
    BrilOp.EQ:      lambda a, b: a == b,
    BrilOp.OR:      lambda a, b: a or b,
    BrilOp.AND:     lambda a, b: a and b,
    BrilOp.NOT:     lambda a: not a
}

@dataclass
class Instruction:
    op: BrilOp # the only obligatory field, due to bril specs.
    type: str
    args: list[str]
    dest: Optional[str]
    value: Optional[int]
    funcs: Optional[list[str]]
    

    @staticmethod
    def from_json(j: dict) -> "Instruction":
        return Instruction(
            op=BrilOp(j["op"]),
            args=j.get("args", []),
            type=j.get("type", "int"),
            
            value=j.get("value"),
            dest=j.get("dest"),

            funcs = j.get("funcs")
        )
    
    def to_json(self):
        res = {"op": self.op.value, "args": self.args, "type": self.type}

        for x in ["value", "dest", "funcs"]:
            field = getattr(self, x)
            if field is not None:
                res[x] = field
        
        return res

def ins_encode_decode_id(block: list):
    for i, x in enumerate(block):
        block[i] = Instruction.from_json(x).to_json()
    
def lvn_inplace_block(block: list, initial_state: State):
    """
    Note that initial state is not necessariliy empty, because
    we need to have some mappings for e.g. function arguments.
    """
    new_instructions: list[Instruction] = []

    mapping = initial_state.mapping
    rs      = initial_state.records

    for ins in block:
        ins = Instruction.from_json(ins)
        
        if ins.dest is None:
            # do nothing (eg. for 'print').
            new_instructions.append(ins)
            continue
        
        # First try to fold compile-time known expressions.
        if ins.op in FOLDABLE_OPS:
            arg_const_vals : list[int] = []
            for x in ins.args:
                rr = mapping[x]
                if rr.hash[0] != BrilOp.CONST:
                    break
                arg_const_vals.append(rr.hash[1])
            else:
                # 'break' was never called, so all arguments are const.

                # note that we only overwrite 'ins', and then follow the usual path.
                ins = Instruction(
                    op=BrilOp.CONST,
                    type=ins.type,
                    args=[],
                    dest=ins.dest,
                    funcs=None,
                    # calculate the compile-time-known value below.
                    value=FOLDABLE_OPS[ins.op](*arg_const_vals),
                )
        # Copy propagation.
        if ins.op == BrilOp.ID:
            assert len(ins.args) == 1
            x, = ins.args
            if mapping[x].hash[0] == BrilOp.CONST:
                ins = Instruction(
                    op=BrilOp.CONST,
                    type=ins.type,
                    value=mapping[x].hash[1], # fetch value
                    args=[],
                    funcs=None,
                    dest=ins.dest,
                )

        # Calculate the hash.
        if ins.op == BrilOp.CONST:
            hash = tuple([ins.op, ins.value])
        else:
            # each 'arg' is a variable name, already defined.
            aargs = [rs.index(mapping[x]) for x in ins.args]
            if ins.op in COMMUTE_OPS:
                aargs.sort()
            hash = tuple([ins.op, *aargs])
        
        # Update mapping, based on if the hash already was computed. 
        matches = [x for x in rs if x.hash == hash]
        if len(matches):
            # my value expression was already calculated at some point..
            r, = matches  # make sure there is only one match.
            mapping[ins.dest] = r
        else:
            # i was never calculated before.
            r = Record(
                canonical=ins.dest,
                hash=hash,
            )
            rs.append(r)
            mapping[ins.dest] = r
        
        # Calculate instruction to replace old one.
        new_args = [mapping[a].canonical for a in ins.args]
        new_ins = deepcopy(ins)
        new_ins.args = new_args
        
        new_instructions.append(new_ins)

    def dump_crap():
        from tabulate import tabulate
        print(f"=================mapping: \n{mapping}")
        print(f"records: \n{tabulate([x.__dict__ for x in rs])}")
    
    # dump_crap()


    # huh, we must do in-place with current abstraction right?
    for i, (_, new) in enumerate(zip(block, new_instructions)):
        block[i] = new.to_json()


def lvn_inplace(function: dict):
    
    rs: list[Record ]= []
    m: dict[str, Record] = dict()
    
    for x in function.get("args", []):
        name = x["name"]
        r = Record(
            canonical=name,
            hash=f"unique_hash_{x}",
        )
        rs.append(r)
        m[name] = r
    state = State(records=rs, mapping=m)
    lvn_inplace_block(initial_state=state, block=function["instrs"])


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
        # ins_encode_decode_id(instructions)
        local_ssa_inplace(block=instructions)
        lvn_inplace(function=f)
    for _ in range(5):
        DCR(j)
    

if __name__ == "__main__":
    text = str(sys.stdin.read())
    # print(text)
    j = json.loads(text)
    main(j)
    json.dump(j, sys.stdout, indent=2)