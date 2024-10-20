import json
import os
import struct

from helper import (
  CHAR_COUNT_ASM_PATH,
  CHAR_LIST_ASM_PATH,
  CHAR_LIST_PATH,
  CHAR_TABLE_PATH,
  FAST_INDX_ASM_PATH,
  SPECIAL_CHARACTERS,
)


def generate_char_list(
  char_table: dict[str, str],
  char_list_asm_path: str,
  fast_index_asm_path: str,
  char_count_asm_path: str,
) -> str:
  code_set: set[int] = set()
  for char in SPECIAL_CHARACTERS:
    code = int.from_bytes(char.encode("cp932"), "big")
    code_set.add(code)

  for key in char_table.keys():
    code = int.from_bytes(key.encode("cp932"), "big")
    if 0x889F <= code < 0xF000:
      code_set.add(code)

  code_list = sorted(code_set)
  char_list = "".join([struct.pack(">H", code).decode("cp932").rstrip("\0") for code in code_list])

  os.makedirs(os.path.dirname(char_list_asm_path), exist_ok=True)
  with open(char_list_asm_path, "w", -1, "utf8", None, "\n") as writer:
    for i, code in enumerate(code_list):
      writer.write(f".short 0x{code:04x}, 0x{i:04x}\n")
    writer.write(".short 0x00, 0xff\n")

  os.makedirs(os.path.dirname(fast_index_asm_path), exist_ok=True)
  with open(fast_index_asm_path, "w", -1, "utf8", None, "\n") as writer:
    high = 0
    i = 0
    index_list = None
    while i < len(code_list):
      code = code_list[i]
      code_high = code >> 8
      code_low = (code & 0xFF) >> 4
      if code_high != high:
        if index_list:
          writer.write(f".short 0x{high:02x}")
          for _ in index_list:
            writer.write(f", 0x{_:04x}")
          writer.write("\n")
        index_list = [len(code_list)] * 16
        high = code_high

      if index_list[code_low] > i:
        index_list[code_low] = i

      i += 1

  os.makedirs(os.path.dirname(char_count_asm_path), exist_ok=True)
  with open(char_count_asm_path, "w", -1, "utf8", None, "\n") as writer:
    writer.write(f"LDR R0, =0x{len(char_list):X}\nBX LR\n")

  return char_list


if __name__ == "__main__":
  with open(CHAR_TABLE_PATH, "r", -1, "utf8") as reader:
    char_table = json.load(reader)
  char_list = generate_char_list(char_table, CHAR_LIST_ASM_PATH, FAST_INDX_ASM_PATH, CHAR_COUNT_ASM_PATH)
  os.makedirs(os.path.dirname(CHAR_LIST_PATH), exist_ok=True)
  with open(CHAR_LIST_PATH, "w", -1, "utf8") as writer:
    writer.write(char_list)
