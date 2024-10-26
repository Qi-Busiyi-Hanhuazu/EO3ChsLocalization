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


def parse_tbl_type_2(reader: io.BytesIO, sheet_name: str, bytes_converter: BytesConverter) -> list[TranslationItem]:
  output = []
  index = 0
  while True:
    buffer = reader.read(44)
    if len(buffer) == 0:
      break
    assert len(buffer) == 44
    raw_bytes, text_length = struct.unpack("<40sI", buffer)
    raw_bytes = raw_bytes.rstrip(b"\0")
    assert text_length * 2 == len(raw_bytes)
    message = bytes_converter.parse_bytes(raw_bytes)
    item: TranslationItem = {
      "index": index,
      "key": f"{sheet_name.replace("/", "__").upper()}_{index:04d}",
      "original": message,
      "translation": message,
    }
    if TRASH_PATTERN.search(message):
      item["trash"] = True
    output.append(item)
    index += 1

  return output


def convert_tbl_type_2_to_json(input_root: str, json_root: str, language: str):
  bytes_converter = BytesConverter()
  for root, dirs, files in os.walk(input_root):
    for file_name in files:
      if not file_name.endswith(".tbl"):
        continue
      file_path = os.path.relpath(f"{root}/{file_name}", input_root)
      output_path = f"{json_root}/{language}/{file_path.removesuffix(".tbl")}.tbl_type_2.json"
      sheet_name = file_path.removesuffix(".tbl").replace("\\", "/")
      if not file_name.startswith("debug_"):
        with open(f"{input_root}/{file_path}", "rb") as reader:
          try:
            parsed = parse_tbl_type_2(reader, sheet_name, bytes_converter)
          except (AssertionError, UnicodeDecodeError):
            continue

        if len(parsed) > 0:
          os.makedirs(os.path.dirname(output_path), exist_ok=True)
          with open(output_path, "w", -1, "utf8", None, "\n") as writer:
            json.dump(parsed, writer, ensure_ascii=False, indent=2)
          continue

      if os.path.exists(output_path):
        os.remove(output_path)


if __name__ == "__main__":
  convert_tbl_type_2_to_json(DIR_UNAPCKED_DATA, DIR_TEXT_FILES, "ja")
