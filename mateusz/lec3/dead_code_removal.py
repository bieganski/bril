#!/usr/bin/env python3

import json
import sys

def main(j):
    print(j)

if __name__ == "__main__":
    j = json.load(sys.stdin)
    main(j)