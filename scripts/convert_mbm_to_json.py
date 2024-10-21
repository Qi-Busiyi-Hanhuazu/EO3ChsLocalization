import io
import json
import os
import struct

from helper import (
  DIR_TEXT_FILES,
  DIR_UNAPCKED_DATA,
  TRASH_PATTERN,
  BytesConverter,
  TranslationItem,
)


def parse_mbm(reader: io.BytesIO, sheet_name: str, bytes_converter: BytesConverter) -> list[TranslationItem]:
  output = []
  zero_1, magic, unk1, file_size, item_count, header_size, zero_2, zero_3 = struct.unpack("<I4s6I", reader.read(32))
  if zero_1 != 0 or magic != b"MSG2" or unk1 != 0x10000 or header_size != 0x20:
    return []

  i = 0
  while True:
    index, length, offset, zero = struct.unpack("<4I", reader.read(16))
    if index == 0 and length == 0 and offset == 0 and zero == 0:
      i += 1
      continue
    if zero != 0:
      break
    if index != i:
      return []
    pos = reader.tell()
    reader.seek(offset)
    raw_bytes = reader.read(length)
    message = bytes_converter.parse_bytes(raw_bytes)
    suffix = ""
    while True:
      for _ in {"\n", "[END]"}:
        if message.endswith(_):
          message = message.removesuffix(_)
          suffix = _ + suffix
          break
      else:
        break

    item: TranslationItem = {
      "index": index,
      "key": f"{sheet_name.replace("/", "__").upper()}_{index:04d}",
      "original": message,
      "translation": message,
      "suffix": suffix,
    }
    if TRASH_PATTERN.search(message):
      item["trash"] = True
    output.append(item)
    reader.seek(pos)
    i += 1

  return output


def convert_mbm_to_json(input_root: str, json_root: str, language: str):
  bytes_converter = BytesConverter()
  for root, dirs, files in os.walk(input_root):
    for file_name in files:
      if not file_name.endswith(".mbm"):
        continue
      file_path = os.path.relpath(f"{root}/{file_name}", input_root)
      output_path = f"{json_root}/{language}/{file_path}.json"
      sheet_name = file_path.removesuffix(".mbm").replace("\\", "/")
      if not file_name.startswith("debug_"):
        with open(f"{input_root}/{file_path}", "rb") as reader:
          parsed = parse_mbm(reader, sheet_name, bytes_converter)

        if len(parsed) > 0:
          os.makedirs(os.path.dirname(output_path), exist_ok=True)
          with open(output_path, "w", -1, "utf8", None, "\n") as writer:
            json.dump(parsed, writer, ensure_ascii=False, indent=2)
          continue

      if os.path.exists(output_path):
        os.remove(output_path)


if __name__ == "__main__":
  convert_mbm_to_json(DIR_UNAPCKED_DATA, DIR_TEXT_FILES, "ja")
