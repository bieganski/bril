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

        # Remove assigned symbols that we know about that are globally unused.
        rms = []
        for i, ins in enumerate(f["instrs"]):
            dest = ins.get("dest")
            if dest and dest not in used:
                rms.append(i)
        
        for idx in rms:
            f["instrs"].pop(idx)


if __name__ == "__main__":
    text = str(sys.stdin.read())
    # print(text)
    j = json.loads(text)
    main(j)
    json.dump(j, sys.stdout)