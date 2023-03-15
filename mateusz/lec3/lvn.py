#!/usr/bin/env python3

import json
import sys

from dead_code_removal import main as DCR

def main(j):
    DCR(j)
    

if __name__ == "__main__":
    text = str(sys.stdin.read())
    # print(text)
    j = json.loads(text)
    main(j)
    json.dump(j, sys.stdout)