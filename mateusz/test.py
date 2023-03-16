#!/usr/bin/env python3

import glob
import subprocess
from pathlib import Path

from ikva_utils.misc.utils import get_color_logging_object, get_git_root

logging = get_color_logging_object()

# from logging import CRITICAL
# logging.setLevel(CRITICAL)  # surpress most of output.

blacklist = [
    "divide-by-zero.bril",
    "nonlocal.bril",
]

def main(*args):
    top_dir = Path(__file__).parent.parent
    
    if len(args):
        # handle command-line specified tests..
        for x in args:
            assert x.endswith(".bril"), x
        tests = args
    else:
        # ..or fallback to default tests.
        tests_dir = top_dir / "examples" / "test" / "lvn"
        tests = glob.glob(str(tests_dir / "*.bril"))

    tests = [Path(x) for x in tests]
    
    for x in tests:

        if any([y in str(x) for y in blacklist]):
            logging.warning(f"skip {x}")
            continue

        print(f"{x}..")

        def run_and_parse(cmd: str):
            p = subprocess.Popen(cmd, executable="/bin/bash", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = p.communicate()
            if p.returncode:
                print(stderr.decode("ascii"))
                raise ValueError(f"command '{cmd}' returned {p.returncode}")
            # expected stderr format:
            # total_dyn_inst: 5
            instructions_executed = int(stderr.splitlines()[0].split()[-1])
            ret_value = stdout
            return instructions_executed, ret_value

        ie, ret = run_and_parse(f"set -o pipefail; cat {x} | bril2json | brili -p")
        opt_pass = get_git_root() / "mateusz/lec3/lvn.py"
        y = Path(x).with_suffix(".mtk")
        _ie, _ret = run_and_parse(f"set -o pipefail; cat {x} | bril2json | {opt_pass} | tee wtf | bril2txt | tee {y} | bril2json | brili -p")

        def match_source(gt: Path, mtk: Path) -> bool:
            """
            We cannot just do '==' on .txt representation because of comments and newlines.
            """
            cmd = lambda pth: subprocess.Popen(f"cat {pth} | bril2json", stdout=subprocess.PIPE, shell=True)
            gt_json, _ = cmd(gt).communicate()
            mtk_json, _ = cmd(mtk).communicate()
            return gt_json == mtk_json

        if match_source(gt=x, mtk=y):
            y.unlink()
        else:
            logging.info(f"saving {y} becuase it differs from corresponding .bril")
        
        if _ret != ret:
            raise ValueError(f"output mismatch: gt: {ret} against {_ret}")
        if _ie > ie:
            raise ValueError("too much instructions executed!")
        if _ie < ie:
            logging.critical(f"Executed {_ie} instructions instead of {ie}! nice work bro")

if __name__ == "__main__":
    import sys
    main(*sys.argv[1:])
