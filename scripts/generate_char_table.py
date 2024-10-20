import json
import os
import struct

from helper import (
  CHAR_TABLE_PATH,
  DIR_TEXT_FILES,
  ZH_HANS_2_KANJI_PATH,
  get_used_characters,
)


def generate_cp932(used_kanjis: set[str]):
  for high in range(0x88, 0xA0):
    for low in range(0x40, 0xFD):
      if low == 0x7F:
        continue
      code = (high << 8) | low
      try:
        char = struct.pack(">H", code).decode("cp932")
        if char in used_kanjis:
          continue
      except UnicodeDecodeError:
        continue
      yield char


def generate_char_table(json_root: str) -> dict[str, str]:
  char_table: dict[str, str] = {}
  shift_jis_characters = set()
  with open(ZH_HANS_2_KANJI_PATH, "r", -1, "utf8") as reader:
    _: dict[str, str] = json.load(reader)
  zh_Hans_2_kanji = {k: v for k, v in _.items() if v.encode("cp932")[0] < 0xA0}

  characters = get_used_characters(json_root)
  generator = generate_cp932(set(zh_Hans_2_kanji.values()))

  def insert_char(char: str):
    shift_jis_char = next(generator)
    while shift_jis_char in shift_jis_characters:
      shift_jis_char = next(generator)
    char_table[shift_jis_char] = char
    shift_jis_characters.add(shift_jis_char)

  for char in sorted(characters):
    if not 0x4E00 <= ord(char) <= 0x9FFF:
      try:
        char.encode("cp932")
        char_table[char] = char
        continue
      except UnicodeEncodeError:
        pass

    try:
      if char.encode("cp932")[0] < 0xA0:
        if char in shift_jis_characters:
          insert_char(char_table[char])
        char_table[char] = char
        shift_jis_characters.add(char)
        continue
    except UnicodeEncodeError:
      pass

    if char in zh_Hans_2_kanji and zh_Hans_2_kanji[char] not in shift_jis_characters:
      char_table[zh_Hans_2_kanji[char]] = char
      shift_jis_characters.add(zh_Hans_2_kanji[char])
      continue

    insert_char(char)

  char_table = {k: v for k, v in sorted(char_table.items(), key=lambda x: x[0].encode("cp932").rjust(2, b"\0"))}
  return char_table


if __name__ == "__main__":
  char_table = generate_char_table(f"{DIR_TEXT_FILES}/zh_Hans")
  os.makedirs(os.path.dirname(CHAR_TABLE_PATH), exist_ok=True)
  with open(CHAR_TABLE_PATH, "w", -1, "utf8") as writer:
    json.dump(char_table, writer, ensure_ascii=False, indent=2)
