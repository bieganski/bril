import atexit
import hashlib
import logging
import os
import shutil
import signal
import subprocess
from pathlib import Path
from typing import List, Optional, Tuple

_log = None


def get_color_logging_object():
    global _log
    if _log is not None:
        return _log

    import logging

    LOG_LEVEL = logging.DEBUG
    LOGFORMAT = (
        "  %(log_color)s%(levelname)-8s%(reset)s | %(log_color)s%(message)s%(reset)s"
    )
    from colorlog import ColoredFormatter

    logging.root.setLevel(LOG_LEVEL)
    formatter = ColoredFormatter(LOGFORMAT)
    stream = logging.StreamHandler()
    stream.setLevel(LOG_LEVEL)
    stream.setFormatter(formatter)
    log = logging.getLogger("pythonConfig")
    log.setLevel(LOG_LEVEL)
    log.addHandler(stream)

    _log = log

    return _log


def get_git_root():
    return Path(
        subprocess.Popen(
            ["git", "rev-parse", "--show-toplevel"], stdout=subprocess.PIPE
        )
        .communicate()[0]
        .rstrip()
        .decode("utf-8")
    )


class Color:
    yellow = "\x1b[33m"
    green = "\x1b[32m"
    red = "\x1b[21m"
    bold_red = "\x1b[31;1m"
    bold = "\033[1m"
    uline = "\033[4m"
    reset = "\x1b[0m"


def ask_yes_no(question: str):
    bc = Color
    while True:
        answer = input(f"{bc.yellow}>> WARN: {question} [y/n]: {bc.reset}").lower()
        if answer == "y":
            return True
        elif answer == "n":
            return False
        else:
            print(
                f"{bc.yellow}>> WARN: Only valid inputs are 'y' or 'n', try again...{bc.reset}"
            )


def hash(s: str, max_chars=6) -> str:
    hash_object = hashlib.sha1(bytes(s, "utf-8"))
    return hash_object.hexdigest()[:max_chars]


def run_shell(
    command: str, timeout=None, raise_on_timeout: bool = True, passwd=None, **kwargs
) -> Tuple[str, str]:
    """
    Runs a bash command in 'shell=True' mode
    Raises on non-zero exit status.
    All kwargs are passed to subprocess.Popen (e.g. stdout, stderr).

    Returns stdout and stderr bytes.
    """
    logging.info(f"Running shell command: {command}")

    def cmd_is_sudo(cmd: str):
        return cmd.split()[:2] == ["sudo", "-S"]

    if cmd_is_sudo(command):
        sudo_kwargs = {
            "stdin": subprocess.PIPE,
            "stdout": subprocess.PIPE,
            "stderr": subprocess.PIPE,
        }
        kwargs.update(sudo_kwargs)

    p = subprocess.Popen(
        command, shell=True, preexec_fn=os.setsid, executable="/bin/bash", **kwargs
    )
    logging.info(f"Process {p.pid} created..")

    def kill_fn(pid):
        # https://jorgenmodin.net/index_html/Link---unix---Killing-a-subprocess-including-its-children-from-python---Stack-Overflow
        try:
            os.killpg(os.getpgid(pid), signal.SIGTERM)
        except Exception as e:
            pass

    # as we create deamon process above, we need to kill it also when our top-level script exits.
    atexit.register(kill_fn, p.pid)

    if cmd_is_sudo(command) and passwd is None:
        passwd = input("> provide Password: ")

    communicate_kwargs = {"timeout": timeout}

    if cmd_is_sudo(command):
        communicate_kwargs.update({"input": bytes(f"{passwd}\n", "utf-8")})

    try:
        stdout, stderr = p.communicate(**communicate_kwargs)
    except subprocess.TimeoutExpired:
        logging.info(f"Process {p.pid} timeout {timeout}s expired, killing..")
        kill_fn(p.pid)
        if raise_on_timeout:
            raise ValueError(
                f"Timeout {timeout} seconds expired! For command {command}"
            )
        return None, None
    return_code = p.returncode
    if return_code:
        print(p)
        # don't throw error on 0 or None (None is returned after timeout expired)
        raise RuntimeError(f"Command '{command}' returned code {return_code}, aborting")
    return stdout, stderr


def run_shell_capture_output(*args, **kwargs) -> Tuple[str, str]:
    return run_shell(
        *args,
        **kwargs,
        encoding="utf-8",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

