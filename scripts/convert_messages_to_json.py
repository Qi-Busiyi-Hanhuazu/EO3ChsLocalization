import io
import json
import os
import struct

from helper import DIR_TEXT_FILES, DIR_UNPACKED_DATA, TRASH_PATTERN, TranslationItem

unkown_controls = set()


def parse_bytes(raw_bytes: bytes) -> str:
  output = ""
  i = 0
  while i < len(raw_bytes):
    byte = raw_bytes[i]
    if 0x00 <= byte < 0x20:
      output += f"[{byte:02X}]"
      i += 1
      continue
    elif 0x20 <= byte < 0x80:
      output += chr(byte)
      i += 1
      continue
    elif 0x80 < byte < 0xF0:
      output += raw_bytes[i : i + 2].decode("cp932")
      i += 2
      continue
    elif byte == 0xFF:
      if i == len(raw_bytes) - 1 or (i == len(raw_bytes) - 2 and raw_bytes[-1] == 0xFF):
        output += "[END]"
        break
      output += "[FF]"
      i += 1
      continue
    assert byte == 0x80
    control_type = raw_bytes[i + 1]
    if control_type == 0x01:
      if i <= len(raw_bytes) - 4 and raw_bytes[i + 2 : i + 4] == b"\x80\x02":
        output += "\\r\n"
        i += 4
      else:
        output += "\n"
        i += 2
      continue
    elif control_type == 0x02:
      output += "\\r"
      i += 2
      continue
    elif control_type == 0x04:
      (color,) = struct.unpack("<H", raw_bytes[i + 2 : i + 4])
      output += f"[COLOR {color:04X}]"
      i += 4
      continue
    elif control_type == 0x06:
      output += "[KEY]"
      i += 2
      continue
    elif control_type == 0x10:
      (value,) = struct.unpack("<H", raw_bytes[i + 2 : i + 4])
      output += f"[EVENT {value:04X}]"
      i += 4
      continue
    elif control_type == 0x11:
      (value,) = struct.unpack("<H", raw_bytes[i + 2 : i + 4])
      output += f"[PROGRAM {value:04X}]"
      i += 4
      continue
    elif control_type == 0x40:
      output += "[GUILD]"
      i += 2
      continue
    elif control_type == 0x43:
      (color,) = struct.unpack("<H", raw_bytes[i + 2 : i + 4])
      output += f"[NPC {color:04X}]"
      i += 4
      continue
    elif control_type == 0x44:
      output += "[SHIP]"
      i += 2
      continue

    if control_type not in unkown_controls:
      print(f"Unknown control code: {control_type:02X}, {output}")
      unkown_controls.add(control_type)
    i += 2

  return output


def parse_mbm(reader: io.BytesIO, sheet_name: str) -> list[TranslationItem]:
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
    message = parse_bytes(raw_bytes)
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


def convert_messages_to_json(input_root: str, json_root: str, language: str):
  os.makedirs(f"{json_root}/{language}", exist_ok=True)
  for root, dirs, files in os.walk(input_root):
    for file_name in files:
      file_path = os.path.relpath(f"{root}/{file_name}", input_root)
      output_path = f"{json_root}/{language}/{file_path}.json"
      sheet_name = file_path.removesuffix(".mbm").replace("\\", "/")
      if not file_name.startswith("debug_") and file_path.endswith(".mbm"):
        with open(f"{input_root}/{file_path}", "rb") as reader:
          parsed = parse_mbm(reader, sheet_name)

        if len(parsed) > 0:
          os.makedirs(os.path.dirname(output_path), exist_ok=True)
          with open(output_path, "w", -1, "utf8", None, "\n") as writer:
            json.dump(parsed, writer, ensure_ascii=False, indent=2)
          continue

      if os.path.exists(output_path):
        os.remove(output_path)


if __name__ == "__main__":
  convert_messages_to_json(DIR_UNPACKED_DATA, DIR_TEXT_FILES, "ja")
