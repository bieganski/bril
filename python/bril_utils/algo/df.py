#!/usr/bin/env python3

from typing import Callable, Any

from bril_utils import Instruction, BasicBlock
from bril_utils.misc.utils import get_color_logging_object

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
) -> dict[BasicBlock, tuple[list[DF_Val_Type], list[DF_Val_Type]]]:

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

Reaching_Def_Val_T = set[Instruction]

def calculate_reaching_defs(
    blocks: list[BasicBlock],
    entry: BasicBlock,
) -> dict[BasicBlock, tuple[Reaching_Def_Val_T, Reaching_Def_Val_T]]:
    # Calculate reachable definitions for each basic block.

    def reaching_def_transfer(b: BasicBlock, in_val: Reaching_Def_Val_T) -> Reaching_Def_Val_T:
        in_val_copy = [x for x in in_val]
        assignments = set()

        for ins in b.code:
            if not ins.dest:
                continue
            in_val_copy = ins.filter_out_killed_by_me(in_val_copy)
            assignments.add(ins)
        
        return set(in_val_copy).union(assignments)


    def reaching_def_merge(vals: list[Reaching_Def_Val_T]) -> Reaching_Def_Val_T:
        if not vals:
            return set()
        s, *ss = vals
        return s.union(*ss)

    mapping = forward_df(
        blocks=blocks,
        entry=entry,
        entry_val=set(),
        init=set(),
        transfer=reaching_def_transfer,
        merge=reaching_def_merge,
    )

    return mapping


T_master, T_slave = Any, Any
def set_to_dict_lmao(s: set[T_master], f: Callable[[T_master], T_slave]) -> dict[T_slave, set[T_master]]:
    """
    should be called group_by or something.
    """
    from collections import defaultdict
    d = defaultdict(list)
    for v in s:
        d[f(v)].append(v)
    return dict([(k, set(v)) for k, v in d.items()])

_Type = dict[str, set[Instruction]]

def calculate_reaching_defs_dict(
    blocks: list[BasicBlock],
    entry: BasicBlock,
)-> dict[BasicBlock, tuple[_Type, _Type]]:
    reaching_defs = calculate_reaching_defs(
        blocks=blocks,
        entry=entry,
    )
    res = dict()

    f = lambda ins: ins.dest
    for k, (v1, v2) in reaching_defs.items():
        
        res[k] = tuple([
            set_to_dict_lmao(x, f) for x in (v1, v2)
        ])
    return res