"""
StartupAppLauncher made by TheKliko
Source: https://github.com/TheKliko/StartupAppLauncher
License: MIT
"""


import json
import logging
import os
from pathlib import Path
import platform
import shlex
import subprocess
import sys
from threading import Thread
import time
from tkinter import messagebox
from typing import Literal, NamedTuple, Optional


APP_NAME: str = "StartupAppLauncher"
CONFIG_DIR: Path = Path.home().resolve() / ".config" / "StartupAppLauncher"
CONFIG_FILE: Path = CONFIG_DIR / "config.json"
DEFAULT_CONFIG: dict = {
    "$schema": "https://raw.githubusercontent.com/TheKliko/StartupAppLauncher/refs/heads/main/config/schema.json",
    "active": True,
    "run": []
}
LOG_FILE: Path = CONFIG_DIR / "latest.log"


#region LaunchItem
class LaunchItem(NamedTuple):
    active: bool
    payload: str
    method: Literal["os.system", "os.startfile", "subprocess.Popen"]
    wait: int
    cwd: Path
    args: list[str]
# endregion


# region Config
class Config:
    active: bool
    cwd: Path
    run: list[LaunchItem]

    def __init__(self, config: dict):
        self.active = config["active"]
        if not isinstance(self.active, bool):
            if self.active in {1, "1", "true", "True"}:
                self.active = True
            elif self.active in {0, "0", "false", "False"}:
                self.active = False
            else:
                raise TypeError(f"invalid 'active' value: '{self.active}'")

        self.cwd = config.get("cwd")  # type: ignore
        if self.cwd is None:
            self.cwd = Path.home().resolve()
        elif not isinstance(self.cwd, str):
            raise TypeError(f"invalid 'cwd' value: '{self.cwd}'")
        else:
            self.cwd = Path(self.cwd).resolve()

        self.run = []
        for i, item in enumerate(config["run"]):
            active: bool = item["active"]
            payload: str = item["payload"]
            method: Literal["os.system", "os.startfile", "subprocess.Popen"] = item["method"]
            wait: Optional[int] = item.get("wait")
            cwd: Optional[Path] = item.get("cwd")
            args: Optional[list[str]] = item.get("args")

            if not isinstance(active, bool):
                if active in {1, "1", "true", "True"}:
                    active = True
                elif active in {0, "0", "false", "False"}:
                    active = False
                else:
                    raise TypeError(f"invalid 'active' value on index {i}: '{active}'")

            if not isinstance(payload, str):
                raise TypeError(f"invalid 'payload' value on index {i}: '{payload}'")

            if not isinstance(method, str):
                raise TypeError(f"invalid 'method' value on index {i}: '{method}'")
            elif method not in {"os.system", "os.startfile", "subprocess.Popen"}:
                raise ValueError(f"invalid 'method' value on index {i}: '{method}'")

            if wait is None:
                wait = 0
            elif not isinstance(wait, int):
                try: wait = int(wait)
                except ValueError:
                    raise TypeError(f"invalid 'wait' value on index {i}: '{wait}'")
            if wait < 0:
                raise ValueError(f"invalid 'wait' value on index {i}: '{wait}' (value must be a positive integer!)")

            if cwd is None:
                cwd = cwd = self.cwd
            elif not isinstance(cwd, str):
                raise TypeError(f"invalid 'cwd' value on index {i}: '{cwd}'")
            else:
                cwd = Path(cwd).resolve()
            
            if args is None:
                args = []
            elif not isinstance(args, list):
                raise TypeError(f"invalid 'args' value on index {i}: '{args}'")
            elif not all(isinstance(arg, str) for arg in args):
                raise ValueError(f"invalid 'args' value on index {i}: '{args}'")

            self.run.append(LaunchItem(active, payload, method, wait, cwd, args))
# endregion


# region AsyncLauncher
class AsyncLauncher:
    @classmethod
    def system(cls, index: int, item: LaunchItem) -> None:
        def worker():
            payload = item.payload
            if payload.startswith("shell:"):
                payload = payload.removeprefix("shell:")
            if item.args:
                payload = " ".join(shlex.quote(arg) for arg in [payload]+item.args)

            if item.wait > 0:
                time.sleep(item.wait / 1000)
            try:
                os.system(payload)
            except Exception as e:
                logging.error(f"Error while launching app with index {index}! {type(e).__name__}: {e}")
                logging.debug(str(item))
        Thread(target=worker).start()


    @classmethod
    def startfile(cls, index: int, item: LaunchItem) -> None:
        def worker():
            payload = item.payload
            if payload.startswith("shell:"):
                payload = payload.removeprefix("shell:")
            if item.wait > 0:
                time.sleep(item.wait / 1000)
            try:
                os.startfile(payload, arguments=" ".join(item.args), cwd=item.cwd)
            except Exception as e:
                logging.error(f"Error while launching app with index {index}! {type(e).__name__}: {e}")
                logging.debug(str(item))
        Thread(target=worker).start()


    @classmethod
    def Popen(cls, index: int, item: LaunchItem) -> None:
        def worker():
            shell = False
            command = [item.payload]+item.args
            if item.payload.startswith("shell:"):
                shell = True
                command[0] = item.payload.removeprefix("shell:")
                command = " ".join(shlex.quote(arg) for arg in command)
            if item.wait > 0:
                time.sleep(item.wait / 1000)
            try:
                subprocess.Popen(command, cwd=item.cwd, shell=shell, close_fds=True)
            except Exception as e:
                logging.error(f"Error while launching app with index {index}! {type(e).__name__}: {e}")
                logging.debug(str(item))
        Thread(target=worker).start()
# endregion


# region main()
def main() -> None:
    # Setup logging & log debug info
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        filename=LOG_FILE,
        format="%(asctime)s.%(msecs)03d [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
        level=logging.DEBUG,
        encoding="utf-8"
    )

    if not getattr(sys, "frozen", False):
        logging.warning("You are running the source code directly! Please run the build script to prevent any issues.")
    logging.debug(f"Platform: {platform.system()} {platform.release()}")
    logging.debug(f"Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")


    # Check & load config
    if not CONFIG_FILE.exists():
        logging.error("Config file not found!")
        logging.info("Writing default config...")
        with open(CONFIG_FILE, "w") as file:
            json.dump(DEFAULT_CONFIG, file, indent=4)
        messagebox.showwarning(title=APP_NAME, message=f"WARNING: Config file not found!\nA default config file has been created:\n{CONFIG_DIR}")
        os.system(f'explorer "{CONFIG_DIR}"')
        sys.exit(0)

    with open(CONFIG_FILE, "r") as file:
        config_dict: dict = json.load(file)

    try:
        config: Config = Config(config_dict)
    except (ValueError, TypeError, KeyError) as e:
        logging.error(f"Bad config! {type(e).__name__}: {e}")
        messagebox.showerror(title=APP_NAME, message=f"ERROR: Bad config!\n{type(e).__name__}: {e}")
        sys.exit(1)

    if not config.active:
        logging.warning("Global override: active=false")
        sys.exit(0)


    # Launch apps & commands
    for i, item in enumerate(config.run):
        if not item.active:
            logging.debug(f"Inactive item at index {i}!")

        method: Literal["os.system", "os.startfile", "subprocess.Popen"] = item.method
        match method:
            case "os.system":
                AsyncLauncher.system(i, item)
            case "os.startfile":
                AsyncLauncher.startfile(i, item)
            case "subprocess.Popen":
                AsyncLauncher.Popen(i, item)
# endregion


if __name__ == "__main__":
    main()