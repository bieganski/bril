from enum import Enum, unique
from typing import Optional, Sequence, Tuple
from dataclasses import dataclass, field
from collections import defaultdict

# XXX
from pprint import pformat, pprint

@unique
class BrilOp(Enum):
    CONST = "const"
    ID = "id"
    PRINT = "print"
    RET = "ret"

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
    loc: int # unique for each line in function.
    type: str
    args: list[str]
    dest: Optional[str]
    value: Optional[int]
    funcs: Optional[list[str]]
    labels: Optional[list[str]]

    def __hash__(self) -> int:
        return self.loc

    def __eq__(self, __o: object) -> bool:
        if not isinstance(__o, Instruction):
            return False
        return self.loc == __o.loc
    
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
        return f"{s}, loc {self.loc}"

    
    @staticmethod
    def from_json(j: dict, loc: int) -> "Instruction":
        return Instruction(
            op=BrilOp(j["op"]),
            loc=loc,
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
    

def parse_code_line(j: dict, loc: int) -> Instruction | Label:
    if "op" not in j:
        return Label(name=j["label"])
    return Instruction.from_json(j, loc=loc)

@dataclass
class BasicBlock:
    code: list[Instruction]
    name: Optional[str]  # only for debug, not supposed to rely on it's value.

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


FunctionName = str


def to_basic_blocks(j: dict) -> dict[FunctionName, Tuple[BasicBlock, list[BasicBlock]]]:
    """
    Returns (entry_block, map[fun -> blocks])
    """
    res = dict()

    for f in j["functions"]:
        fun_name = f["name"]
        instructions = [parse_code_line(ins, loc=i) for i, ins in enumerate(f["instrs"])]
        
        d = defaultdict(list)

        # Assign each instruction to currently active label.
        # Discard unused labels (those with 0 corresponding instructions).
        # 'None' marks default label (start of function).
        # BUG: it will break on two consecutive labels, without instructions in between,
        # if some jump refers to first label.
        cur_label = None
        first_label = -1
        for x in instructions:
            match x:
                case Label(name=name):
                    cur_label = name
                case Instruction() as i:
                    if first_label == -1: # we cannot use 'None' as initial value.
                        first_label = cur_label # type: ignore
                    d[cur_label].append(i)
                case _:
                    raise ValueError("unexpected implementation error")
        
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
