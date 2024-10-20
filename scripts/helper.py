import json
import logging
import os
import re
from typing import TypedDict

DIR_TEXT_FILES = "texts"
DIR_UNAPCKED_ROOT = "unpacked"
DIR_UNPACKED_DATA = "unpacked/Data"
DIR_UNPACKED_DATA_OUTPUT = "temp/pack/Data"

CHAR_TABLE_PATH = "out/char_table.json"
ARM9_PATH = "original_files/arm9.bin"
ARM9_DECOMPRESSED_PATH = "src/arm9.bin"
ARM9_MODIFIED_PATH = "temp/nitro/arm9.bin"
ARM9_OUT_PATH = "out/arm9.bin"
BANNER_PATH = "original_files/banner.bin"
BANNER_OUT_PATH = "out/banner.bin"
PACK_PATH = "original_files/Target.bin"
ZH_HANS_2_KANJI_PATH = "files/zh_Hans_2_kanji.json"


TRASH_PATTERN = re.compile(
  r"[＿]|リザーブ|アザー[０-９]{3}|モンスター[０-９]{3}解説文|ダミー",
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
}


class TranslationItem(TypedDict):
  index: int
  key: str
  original: str
  translation: str
  suffix: str
  trash: bool
  untranslated: bool


char_table_reversed: dict[str, str] = {}
zh_hans_no_code = set()


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
