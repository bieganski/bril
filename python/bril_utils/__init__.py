from enum import Enum, unique
from typing import Optional
from dataclasses import dataclass

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
    
@dataclass
class BasicBlock:
    code: list[Instruction]
