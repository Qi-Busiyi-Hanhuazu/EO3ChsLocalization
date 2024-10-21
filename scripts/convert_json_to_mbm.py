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


def to_mbm(data: dict[int, TranslationItem], bytes_converter: BytesConverter) -> bytes:
  output = bytearray()
  item_count = max(data.keys()) + 1
  output.extend(struct.pack("<I4s6I", 0, b"MSG2", 0x10000, 0, item_count, 0x20, 0, 0))

  header_length = 0x20 + 0x10 * item_count
  data_bytes = bytearray()

  for i in range(item_count):
    if i not in data:
      output.extend(struct.pack("<4I", 0, 0, 0, 0))
      continue

    offset = header_length + len(data_bytes)
    text = data[i]["translation"] + data[i].get("suffix", "")
    text_bytes = bytes_converter.to_bytes(text)
    data_bytes.extend(text_bytes)
    output.extend(struct.pack("<4I", i, len(text_bytes), offset, 0))

  return bytes(output + data_bytes)


def convert_json_to_mbm(json_root: str, language: str, output_root: str, char_table: CharTable):
  bytes_converter = BytesConverter()
  for root, dirs, files in os.walk(f"{json_root}/ja"):
    for file_name in files:
      if not file_name.endswith(".mbm.json"):
        continue
      file_path = os.path.relpath(f"{root}/{file_name}", f"{json_root}/ja")
      sheet_name = file_path.removesuffix(".mbm.json").replace("\\", "/")
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

      new_bytes = to_mbm(data_dict, bytes_converter)

      output_path = f"{output_root}/{sheet_name}.mbm"
      os.makedirs(os.path.dirname(output_path), exist_ok=True)
      with open(output_path, "wb") as writer:
        writer.write(new_bytes)


if __name__ == "__main__":
  char_table = CharTable(CHAR_TABLE_PATH)
  convert_json_to_mbm(DIR_TEXT_FILES, "zh_Hans", DIR_REPACK_DATA, char_table)
