import json
import logging
import os
import re
import struct
from typing import TypedDict

DIR_TEXT_FILES = "texts"
DIR_ORIGNAL_FILES = "original_files"
DIR_OUT = "out"
DIR_ARM9_PATCH = "arm9_patch"
DIR_UNAPCKED_DATA = "original_files/data/Data/@Target/Data"
DIR_REPACK_DATA = "temp/pack/@Target/Data"
DIR_TEMP_DECOMPRESSED = "temp/decompressed"
DIR_TEMP_DECOMPRESSED_MODIFIED = "temp/decompressed_mod"
DIR_TEMP_OUT = "temp/out"
DIR_IMAGES_REPLACE = "files/images"

DIR_FONT = "Font"
DIR_IMAGES = "Tex"

ZH_HANS_2_KANJI_PATH = "files/zh_Hans_2_kanji.json"
ORIGINAL_CHAR_LIST_PATH = "files/original_char_list.txt"
CHAR_TABLE_PATH = "out/char_table.json"
CHAR_LIST_PATH = "out/char_list.txt"
CHAR_LIST_ASM_PATH = "arm9_patch/src/20EAD68/char_list.s"
FAST_INDX_ASM_PATH = "arm9_patch/src/20E9D0C/fast_index.s"
CHAR_COUNT_ASM_PATH = "arm9_patch/src/201B204/char_count.s"

SYMBOL_OUT_PATH = "out/symbols.txt"
BANNER_PATH = "original_files/banner.bin"
BANNER_OUT_PATH = "out/banner.bin"
PACK_PATH = "original_files/data/Data/Target.bin"

ARM9_COMPRESSED_SIZE_OFFSET = 0xBB4
ARM9_NEW_STRING_OFFSET = 0x20EA280 - 0x2000000


TRASH_PATTERN = re.compile(
  r"^(?:リザーブ|アザー[０-９]{3}|モンスター[０-９]{3}解説文|[－？]+|ＮＯＮＥ|ＮＯＮＥＤＡＴＡ|)$|[＿]|ダミー|だみー",
  re.DOTALL,
)
CONTROL_PATTERN = re.compile(r"\[[^\[\]]+\]")
KANA_PATTERN = re.compile(r"[\u3040-\u309F\u30A0-\u30FF]+")

CHINESE_TO_JAPANESE = {
  "·": "・",
  "—": "ー",
  " ": "　",
  "+": "＋",
  "-": "－",
  "%": "％",
  "~": "～",
  ".": "．",
  ",": "，",
  "/": "／",
}
SPECIAL_CHARACTERS = "　、。，．・：；？！゛゜´｀¨＾￣＿ヽヾゝゞ〃仝々〆〇ー―‐／＼～∥｜…‥‘’“”（）＋－±×÷＝＜＞≦≧￥＄％＃＆＊＠☆★○●◎◇◆□■△▲▽▼※→←↑↓◯０１２３４５６７８９ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚぁあぃいぅうぇえぉおかがきぎくぐけげこごさざしじすずせぜそぞただちぢっつづてでとどなにぬねのはばぱひびぴふぶぷへべぺほぼぽまみむめもゃやゅゆょよらりるれろゎわゐゑをんァアィイゥウェエォオカガキギクグケゲコゴサザシジスズセゼソゾタダチヂッツヅテデトドナニヌネノハバパヒビピフブプヘベペホボポマミムメモャヤュユョヨラリルレロヮワヰヱヲンヴヵヶⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩ"


class TranslationItem(TypedDict):
  index: int
  key: str
  original: str
  translation: str
  suffix: str
  trash: bool
  untranslated: bool
  offset: int
  max_length: int


def load_translation_dict(path: str) -> dict[str, str]:
  with open(path, "r", -1, "utf8") as reader:
    translation_list: list[TranslationItem] = json.load(reader)

  translations = {}
  for item_dict in translation_list:
    if item_dict.get("trash", False) or item_dict.get("untranslated", False):
      continue
    translations[item_dict["key"]] = item_dict["translation"]

  return translations


def load_translation_items(path: str) -> list[TranslationItem]:
  with open(path, "r", -1, "utf8") as reader:
    translation_list = json.load(reader)

  return translation_list


def get_used_characters(json_root: str) -> set[str]:
  characters = set()
  for root, dirs, files in os.walk(json_root):
    for file_name in files:
      if not file_name.endswith(".json"):
        continue

      translations = load_translation_dict(f"{root}/{file_name}")

      for key, value in translations.items():
        content = CONTROL_PATTERN.sub("", value).replace("\n", "")
        if KANA_PATTERN.search(content):
          continue

        for k, v in CHINESE_TO_JAPANESE.items():
          content = content.replace(k, v)

        for char in content:
          characters.add(char)

  return characters


class CharTable:
  def __init__(self, char_table_path: str):
    self.char_table = {}
    if os.path.exists(char_table_path):
      with open(char_table_path, "r", -1, "utf8") as reader:
        self.char_table: dict[str, str] = json.load(reader)
    else:
      logging.warning("Character table not found.")

    self.char_table_reversed: dict[str, str] = {v: k for k, v in self.char_table.items()}
    self.zh_hans_no_code = set()

  def convert_zh_hans_to_shift_jis(self, text: str) -> str:
    output = []
    i = 0
    while i < len(text):
      char = text[i]
      if char == "[":
        right_index = text.find("]", i)
        output.append(text[i : right_index + 1])
        i = right_index + 1
        continue
      elif char == "\\":
        assert text[i + 1] == "r"
        output.append("\\r")
        i += 2
        continue

      char = CHINESE_TO_JAPANESE.get(char, char)
      if char in "0123456789":
        char = chr(ord(char) - ord("0") + ord("０"))
      elif char in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        char = chr(ord(char) - ord("A") + ord("Ａ"))
      elif char in "abcdefghijklmnopqrstuvwxyz":
        char = chr(ord(char) - ord("a") + ord("ａ"))

      if char in self.char_table_reversed:
        output.append(self.char_table_reversed[char])
      else:
        try:
          char.encode("cp932")
          output.append(char)
        except UnicodeEncodeError:
          if char not in self.zh_hans_no_code:
            logging.warning(f"Char missing: {char}")
            self.zh_hans_no_code.add(char)
          output.append("？")

      i += 1

    return "".join(output)


class BytesConverter:
  def __init__(self) -> None:
    self.unkown_controls = set()

  def parse_bytes(self, raw_bytes: bytes) -> str:
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

      if control_type not in self.unkown_controls:
        logging.warning(f"Unknown control code: {control_type:02X}, {output}")
        self.unkown_controls.add(control_type)
      i += 2

    return output

  def to_bytes(self, text: str) -> bytes:
    i = 0
    output = bytearray()
    while i < len(text):
      char = text[i]
      if char == "[":
        right_index = text.find("]", i)
        control = text[i + 1 : right_index]
        key, *_ = control.split(" ", 1)
        if _:
          value = int(_[0], 16)
        if key == "END":
          output.extend(b"\xff\xff")
        elif key == "COLOR":
          output.extend(struct.pack("<2sH", b"\x80\x04", value))
        elif key == "KEY":
          output.extend(b"\x80\x06")
        elif key == "EVENT":
          output.extend(struct.pack("<2sH", b"\x80\x10", value))
        elif key == "PROGRAM":
          output.extend(struct.pack("<2sH", b"\x80\x11", value))
        elif key == "GUILD":
          output.extend(b"\x80\x40")
        elif key == "NPC":
          output.extend(struct.pack("<2sH", b"\x80\x43", value))
        elif key == "SHIP":
          output.extend(b"\x80\x44")
        else:
          raise ValueError(f"Unknown control: {control}")

        i = right_index + 1
        continue
      elif char == "\\":
        assert text[i + 1] == "r"
        if i < len(text) - 2 and text[i + 2] == "\n":
          output.extend(b"\x80\x01\x80\x02")
          i += 3
          continue
        output.extend(b"\x80\x02")
        i += 2
        continue
      elif char == "\n":
        output.extend(b"\x80\x01")
        i += 1
        continue
      output.extend(char.encode("cp932"))
      i += 1

    return bytes(output)


def color_to_rgb555(c: tuple[int, int, int]) -> int:
  r = c[0] // 8
  g = c[1] // 8
  b = c[2] // 8
  return r | (g << 5) | (b << 10)


def rgb555_to_color(c: int) -> tuple[int, int, int]:
  r = c & 0x1F
  g = (c >> 5) & 0x1F
  b = (c >> 10) & 0x1F
  return (8 * r, 8 * g, 8 * b)
