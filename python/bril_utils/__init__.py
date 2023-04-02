from enum import Enum, unique
from typing import Optional, Sequence
from dataclasses import dataclass, field
from collections import defaultdict
from functools import singledispatch

from bril_utils.tools import fresh

# XXX
from pprint import pformat, pprint

@unique
class BrilOp(Enum):
    CONST = "const"
    ID = "id"
    PRINT = "print"
    RET = "ret"
    NOP = "nop"

    JUMP = "jmp"
    BRANCH = "br"
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

@dataclass
class Label:
    name: str

@dataclass
class Instruction:
    op: BrilOp # the only obligatory field, due to bril specs.
    
    id: int # unique for each instruction in function. not necessarily ordered.
    
    args: list[str] = field(default_factory=list)
    labels: list[str] = field(default_factory=list)
    funcs: list[str] = field(default_factory=list)
    type: Optional[str] = None
    dest: Optional[str] = None
    value: Optional[int] = None

    def __hash__(self) -> int:
        return self.id

    def __eq__(self, __o: object) -> bool:
        if not isinstance(__o, Instruction):
            return False
        return self.id == __o.id
    
    def __repr__(self) -> str:
        match self.op:
            case BrilOp.CONST:
                s = f"{self.dest} = const {self.value}"
            case BrilOp.PRINT:
                s = f"print {self.args}"
            case BrilOp.BRANCH:
                s = f"br {self.args} {self.labels}"
            case BrilOp.JUMP:
                s = f"jmp {self.args} {self.labels}"
            case _:
                s = f"{self.dest} = {self.op} {self.args}"
        return f"{s}, loc {self.id}"

    
    @staticmethod
    def from_json(j: dict, id: int) -> "Instruction":
        return Instruction(
            op=BrilOp(j["op"]),
            id=id,
            args=j.get("args", []),
            type=j.get("type", "int"),
            
            value=j.get("value"),
            dest=j.get("dest"),

            funcs = j.get("funcs"),
            labels = j.get("labels"),
        )
    
    def to_json(self):
        res = {"op": self.op.value, "args": self.args, "type": self.type}

        for x in ["value", "dest", "funcs", "labels"]:
            field = getattr(self, x)
            if field is not None:
                res[x] = field
        
        return res
    
    def filter_out_killed_by_me(self, instructions: list["Instruction"]) -> list["Instruction"]:
        return [x for x in instructions if x.dest is None or (x.dest != self.dest)]
    
    def wrapping_block(self, blocks: Sequence["BasicBlock"]) -> "BasicBlock":
        for b in blocks:
            if self in b.code:
                return b
        raise ValueError(f"Could not find {self} in any basic block from list of {len(blocks)} given!")

class InstructionGenerator:
    @staticmethod
    def _generic_gen_ins(id: int, **kwargs) -> Instruction:
        return Instruction(
            id=id,
            **kwargs,
        )
    
    def nop(id: int) -> Instruction:
        return __class__._generic_gen_ins(id=id, op=BrilOp.NOP)


def parse_code_line(j: dict, id: int) -> Instruction | Label:
    if "op" not in j:
        return Label(name=j["label"])
    return Instruction.from_json(j, id=id)

@dataclass
class BasicBlock:
    code: list[Instruction]
    name: Optional[str] = None # only for debug, not supposed to rely on it's value.

    # it's up to user to keep 'nexts' and 'prevs' consistent.
    nexts: list["BasicBlock"] = field(default_factory=list)
    prevs: list["BasicBlock"] = field(default_factory=list)

    @property
    def last_instr(self) -> Instruction:
        return self.code[-1]

    def __repr__(self) -> str:
        return f"block {self.name}"

    def __hash__(self) -> int:
        return hash(self.code[0])



def flow_ctrl_targets(ins: Instruction) -> list[str]:
    match ins.op:
        case BrilOp.JUMP | BrilOp.BRANCH:
            assert isinstance(ins.labels, list)
            return ins.labels
        case _:
            assert not ins.labels, ins
            return []


def fresh_label(instructions: Sequence[Instruction | Label], prefix=str):
    env = [
        x.name for x in instructions if isinstance(x, Label)
    ]
    return next(fresh(existing=env, prefix=prefix))

def fresh_ins_id(blocks_or_inss: Sequence[BasicBlock] | Sequence[Instruction]) -> int:
    """
    To understand the `yield` advantage over `return` in that case, 
    let's consider following example:
    
    We just parsed the IR source code and to make sure that there are no empty basic blocks,
    we insert NOPs between each two consecutive labels. The code would look like this:

    for ins in instructions:
        if isinstance(ins, Label) and len(cur_block.code) == 0:
            new_id = fresh_ins_id(instructions)
            nop = nop_ins(..., id=new_id)
            cur_block.code.append(nop)
    
    Note that during exeuction of such loop, providing that the 'if' condition was executed at least once,
    the 'instructions' variable cannot be used safely, as it doesn't reflect real instructions in basic blocks.
    So the 'fresh_ins_id(instructions)' expression is not right - we should pass 'instructions + list_of_all_inserted_nops`.

    To avoid such complexity, we use generators here, by doing: `gen = fresh_ins_id(instructions)` before the loop.
    """
    if len(blocks_or_inss) == 0:
        raise ValueError("len(blocks_or_inss) == 0") # CHANGE_ME to just 'yield 0' if such case is expected.
    
    def helper(blocks: Sequence[BasicBlock]):
        mmax = -1
        for b in blocks:
            mmax = max([x.id for x in b.code if isinstance(x, Instruction)])
        while True:
            mmax += 1
            yield mmax
    
    if isinstance(blocks_or_inss[0], Instruction):
        yield from helper([BasicBlock(code=blocks_or_inss)])
    else:
        assert isinstance(blocks_or_inss[0], BasicBlock)
        yield from helper(blocks_or_inss)

FunctionName = str
def to_basic_blocks(j: dict) -> dict[FunctionName, tuple[BasicBlock, list[BasicBlock]]]:
    """
    Returns (entry_block, map[fun -> blocks])
    """
    res = dict()

    
    gen = fresh_ins_id(instructions) # docstring of 'fresh_ins_id' is worth reading!
    
    for f in j["functions"]:
        fun_name = f["name"]
        instructions = [parse_code_line(ins, id=i) for i, ins in enumerate(f["instrs"])]

        if not isinstance(instructions[0], Label):
            # add a dummy label
            entry_label = fresh_label(instructions=instructions, prefix="entry")
            nop_id = next(gen)
            nop = InstructionGenerator.nop(id=nop_id)
            instructions = [Label(name=entry_label), nop] + instructions

        d = defaultdict(list)

        # Assign each instruction to currently active label.
        cur_block = None
        for x in instructions:
            match x:
                case Label(name=name):
                    if cur_block is None:
                        # i'm a first label.
                        cur_label = name
                        continue
                    # some block already exists.
                    # check if block just processed is not empty, or insert a NOP.
                    if not d[cur_label]:
                        nop_id = next(gen)
                        nop = InstructionGenerator.nop(id=nop_id)
                        d[cur_label].append(nop)
                    cur_label = name
                case Instruction() as i:
                    d[cur_label].append(i)
                case _:
                    raise ValueError("unexpected implementation error")

        # delete it, as it no longer reflects reality.
        del instructions
        
        # .nexts fields are not yet initialized
        dd = dict((k, BasicBlock(code=v, name=k)) for k, v in d.items())
        del d
        
        # In order to fix BUG above, we need to insert some NOPs in between,
        # as below code works under assumption that block.code is non-empty.
        for _, block in dd.items():
            jmp_targets = flow_ctrl_targets(block.last_instr)
            block.nexts = [dd[k] for k in jmp_targets]

        # .nexts are fine, in second iteration fill .prevs
        for _, block in dd.items():
            for b in block.nexts:
                b.prevs.append(block)

        res[fun_name] = dd[first_label], [x for x in dd.values()] # type: ignore

    return res

def calculate_dominators(blocks: list[BasicBlock]) -> dict[BasicBlock, set[BasicBlock]]:
    from copy import copy

    prev = None # not 'dict', in order to trigger 'do-while' first iteration.
    cur = dict([(b, set([b])) for b in blocks])

    while prev != cur:
        prev = copy(cur)
        for b in blocks:
            match b.prevs:
                case x, *y: # non-empty list.
                    cur[b] = cur[b].union(cur[x].intersection(*[cur[z] for z in y]))
                case _:
                    pass
    return cur


def uses(var: str, block: BasicBlock) -> Sequence[Instruction]:
    return [ins for ins in block.code if var in ins.args]
