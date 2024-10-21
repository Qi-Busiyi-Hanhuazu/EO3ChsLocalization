import json
import os
import struct

from helper import (
  CHAR_TABLE_PATH,
  DIR_REPACK_DATA,
  DIR_TEXT_FILES,
  BytesConverter,
  CharTable,
  TranslationItem,
  load_translation_dict,
)


def to_tbl(data: dict[int, TranslationItem], bytes_converter: BytesConverter) -> bytes:
  output = bytearray()
  item_count = max(data.keys()) + 1
  output.extend(struct.pack("<H", item_count))

  data_bytes = bytearray()
  ends = []

  for i in range(item_count):
    if i not in data:
      data_bytes.append(0)
      ends.append(len(data_bytes))
      continue

    text = data[i]["translation"]
    text_bytes = bytes_converter.to_bytes(text)
    data_bytes.extend(text_bytes)
    data_bytes.append(0)
    ends.append(len(data_bytes))

  for i in range(item_count):
    output.extend(struct.pack("<H", ends[i]))

  return bytes(output + data_bytes)


def convert_json_to_tbl(json_root: str, language: str, output_root: str, char_table: CharTable):
  bytes_converter = BytesConverter()
  for root, dirs, files in os.walk(f"{json_root}/ja"):
    for file_name in files:
      if not file_name.endswith(".tbl.json"):
        continue
      file_path = os.path.relpath(f"{root}/{file_name}", f"{json_root}/ja")
      sheet_name = file_path.removesuffix(".tbl.json").replace("\\", "/")
      original_json_path = f"{json_root}/ja/{file_path}"
      translation_json_path = f"{json_root}/{language}/{file_path}"
      if not os.path.exists(original_json_path) or not os.path.exists(translation_json_path):
        continue

      with open(original_json_path, "r", -1, "utf-8") as reader:
        data_dict: dict[int, TranslationItem] = {i["index"]: i for i in json.load(reader)}

      translations = load_translation_dict(translation_json_path)

      for key, value in data_dict.items():
        if value["key"] in translations:
          value["translation"] = char_table.convert_zh_hans_to_shift_jis(translations[value["key"]])

      new_bytes = to_tbl(data_dict, bytes_converter)

      output_path = f"{output_root}/{sheet_name}.tbl"
      os.makedirs(os.path.dirname(output_path), exist_ok=True)
      with open(output_path, "wb") as writer:
        writer.write(new_bytes)


if __name__ == "__main__":
  char_table = CharTable(CHAR_TABLE_PATH)
  convert_json_to_tbl(DIR_TEXT_FILES, "zh_Hans", DIR_REPACK_DATA, char_table)
