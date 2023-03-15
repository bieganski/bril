#!/usr/bin/env python3

import json
import sys

def main(j):
    for f in j["functions"]:

        # Find all globally used symbols.
        used = []
        for ins in f["instrs"]:
            args = ins.get("args") or []
            used.extend(args)

        # Keep only those symbols, that we know about that are globally used somewhere.
        new_instructions = []
        for ins in f["instrs"]:
            dest = ins.get("dest")
            if dest and dest not in used:
                pass
            else:
                new_instructions.append(ins)
        
        f["instrs"] = new_instructions


if __name__ == "__main__":
    text = str(sys.stdin.read())
    # print(text)
    j = json.loads(text)
    main(j)
    json.dump(j, sys.stdout)