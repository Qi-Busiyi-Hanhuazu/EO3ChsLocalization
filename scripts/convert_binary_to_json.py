import io
import json
import os

from helper import (
  DIR_TEMP_DECOMPRESSED,
  DIR_TEXT_FILES,
  TRASH_PATTERN,
  BytesConverter,
  TranslationItem,
)

HARDCODED_TEXTS = {
  "arm9.bin": (
    ("剣虎", "催眠フクロウ"),
    ("雷", "ＰＬＡＹＥＲ達の先制攻撃！"),
    ("ウォリアー", "＜－－－防具－－－＞"),
    ("クラス未設定", "プリンス"),
    ("ウォリアー", "プリンス"),
    ("★ＭＡＳＴＥＲ", "外す"),
    ("アイテム", "キ"),
    ("決定", "募集中です・・・"),
    ("戻る", "戻る"),
    ("使う", "捨てる"),
    ("クエスト", "戦乱　その忌むべき名を呼べ"),
    ("読む", "捨てる"),
    ("戻る", "再検索"),
  ),
  "overlay/overlay_0001.bin": (("－－－－－－－－", "ＤＥＦＥＮＣＥ"),),
  "overlay/overlay_0003.bin": (
    ("売却価格", "売却価格"),
    ("アーマンの宿", "－－－－－－"),
    ("冒険者の登録", "外に出る"),
    ("樹海探索を開始する", "街に戻る"),
    ("モンク", "ビーストキング"),
    ("引退", "名前変更"),
    ("ミッションの受領", "アイテム図鑑"),
    ("＜－－食料－－＞", "ビーストキング"),
    ("クエストを受ける", "外に出る"),
    ("宿泊する", "荷物を受け取る"),
    ("航海に出る", "エピック図鑑"),
    ("商品を買う", "アイテム"),
    ("売却価格", "挿話を読む"),
  ),
}


def parse_binary(reader: io.BytesIO, sheet_name: str, bytes_converter: BytesConverter) -> list[TranslationItem]:
  output = []
  raw_bytes = reader.read()
  offset = 0
  for text_from, text_to in HARDCODED_TEXTS[f"{sheet_name}.bin"]:
    if type(text_from) is str:
      bytes_from = bytes_converter.to_bytes(text_from)
      bytes_to = bytes_converter.to_bytes(text_to)
    else:
      bytes_from = text_from
      bytes_to = text_to

    offset = raw_bytes.find(bytes_from, offset)
    if offset == -1:
      raise ValueError(f"String not found: {text_from}")

    while True:
      zero = raw_bytes.find(b"\x00", offset)
      if zero == -1:
        raise ValueError(f"String not terminated: {text_from}")
      text_bytes = raw_bytes[offset:zero]
      if len(text_bytes) == 0:
        offset = zero + 1
        continue

      message = bytes_converter.parse_bytes(text_bytes)
      max_length = len(text_bytes) + (4 - len(text_bytes) % 4) - 1
      item: TranslationItem = {
        "offset": offset,
        "key": f"{sheet_name.replace("/", "__").upper()}_{offset:06x}",
        "original": message,
        "translation": message,
        "max_length": max_length,
      }
      if TRASH_PATTERN.search(message):
        item["trash"] = True
      output.append(item)
      if text_bytes == bytes_to:
        break
      offset = zero + 1

  return output


def convert_binary_to_json(input_root: str, json_root: str, language: str):
  bytes_converter = BytesConverter()
  for key, value in HARDCODED_TEXTS.items():
    output_path = f"{json_root}/{language}/{key}.json"
    sheet_name = key.removesuffix(".bin").replace("\\", "/")
    with open(f"{input_root}/{key}", "rb") as reader:
      parsed = parse_binary(reader, sheet_name, bytes_converter)

    if len(parsed) > 0:
      os.makedirs(os.path.dirname(output_path), exist_ok=True)
      with open(output_path, "w", -1, "utf8", None, "\n") as writer:
        json.dump(parsed, writer, ensure_ascii=False, indent=2)
      continue

    if os.path.exists(output_path):
      os.remove(output_path)


if __name__ == "__main__":
  convert_binary_to_json(DIR_TEMP_DECOMPRESSED, DIR_TEXT_FILES, "ja")
