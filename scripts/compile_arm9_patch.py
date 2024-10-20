import os
import re
import shutil
import subprocess

from helper import (
  ARM9_DECOMPRESSED_PATH,
  ARM9_MODIFIED_PATH,
  DIR_ARM9_PATCH,
  SYMBOL_OUT_PATH,
)

SYMBOL_PATTERN = re.compile(r"^(?P<address>[0-9a-f]{8}) \w\s+.text\s+\d{8} (?P<name>.+)$")


def compile_arm9_patch(
  root: str,
  arm9_path: str,
  arm9_output_path: str,
  symbol_output_path: str,
):
  if os.path.exists(f"{root}/build"):
    shutil.rmtree(f"{root}/build")
  for file_name in os.listdir(root):
    if file_name.startswith("repl_"):
      os.remove(f"{root}/{file_name}")

  with open(arm9_path, "rb") as reader:
    arm9 = reader.read()

  symbols = []
  for folder in os.listdir(f"{root}/src"):
    if not os.path.isdir(f"{root}/src/{folder}"):
      continue

    address = int(folder, 16)
    p = subprocess.run(
      [
        "make",
        f"TARGET=repl_{address:07X}",
        f"SOURCES=src/{folder}",
        f"CODEADDR=0x{address:07X}",
      ],
      cwd=root,
    )
    if p.returncode != 0:
      raise Exception(f"Failed to compile {folder}")

    with open(f"{root}/repl_{address:07X}.bin", "rb") as reader:
      patch = reader.read()

    arm9 = arm9[: address - 0x2000000] + patch + arm9[address - 0x2000000 + len(patch) :]

    with open(f"{root}/repl_{address:07X}.sym", "r", -1, "utf8") as reader:
      symbols_text = reader.read()

    for result in SYMBOL_PATTERN.finditer(symbols_text):
      symbols.append(result.group("name"), int(result.group("address"), 16))

  with open(arm9_output_path, "wb") as writer:
    writer.write(arm9)

  with open(symbol_output_path, "w", -1, "utf8", None, "\n") as writer:
    for name, address in symbols:
      writer.write(f"{name} = 0x{address:08X};\n")


if __name__ == "__main__":
  compile_arm9_patch(DIR_ARM9_PATCH, ARM9_DECOMPRESSED_PATH, ARM9_MODIFIED_PATH, SYMBOL_OUT_PATH)
