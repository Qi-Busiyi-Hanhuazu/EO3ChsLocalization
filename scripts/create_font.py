import json
import struct

import ndspy.lz10
from helper import (
  CHAR_LIST_PATH,
  CHAR_TABLE_PATH,
  DIR_FONT,
  DIR_REPACK_DATA,
  DIR_UNAPCKED_DATA,
  ORIGINAL_CHAR_LIST_PATH,
)
from PIL import Image, ImageDraw, ImageFont

FONT_CONFIG: list[dict] = [
  {
    "font": "files/fonts/Zfull-GB.ttf",
    "size": 8,
    "width": 8,
    "x": 0,
    "y": 6,
  },
  {
    "font": "files/fonts/Zfull-GB.ttf",
    "size": 10,
    "width": 16,
    "x": 0,
    "y": 8,
  },
  {
    "font": "C:/Windows/Fonts/simsun.ttc",
    "size": 12,
    "width": 16,
    "x": 0,
    "y": 10,
  },
]


def create_font(char_table: dict[str, str], original_char_list: str, char_list: str, input_path: str, output_path: str):
  for config in FONT_CONFIG:
    size: int = config["size"]
    width: int = config["width"]
    draw_x: int = config["x"]
    draw_y: int = config["y"]
    font = ImageFont.truetype(config["font"], size)

    with open(f"{input_path}/Font{size}x{size}.cmp", "rb") as reader:
      raw_bytes = ndspy.lz10.decompress(reader.read())

    new_bytes = bytearray()
    for i, char in enumerate(char_list):
      if 0x889F <= struct.unpack(">H", char.encode("cp932").rjust(2, b"\0"))[0] < 0xF000:
        image = Image.new("L", (width, size), 0)
        draw = ImageDraw.Draw(image)
        draw.text((draw_x, draw_y), char_table[char], 0xFF, font, "ls")

        x, y = 0, 0
        while y < size:
          byte = 0
          for _ in range(8):
            bit = image.getpixel((x, y))
            byte = (bit != 0) << _ | byte
            x += 1
            if x == width:
              x = 0
              y += 1
              if y == size:
                break

          new_bytes.append(byte)

      else:
        original_index = original_char_list.index(char)
        original_bytes = raw_bytes[original_index * width * size // 8 : (original_index + 1) * width * size // 8]
        new_bytes.extend(original_bytes)

    compressed = ndspy.lz10.compress(new_bytes)
    with open(f"{output_path}/Font{size}x{size}.cmp", "wb") as writer:
      writer.write(compressed)


if __name__ == "__main__":
  with open(CHAR_TABLE_PATH, "r", -1, "utf8") as reader:
    char_table = json.load(reader)
  with open(ORIGINAL_CHAR_LIST_PATH, "r", -1, "utf8") as reader:
    original_char_list = reader.read()
  with open(CHAR_LIST_PATH, "r", -1, "utf8") as reader:
    char_list = reader.read()

  create_font(
    char_table, original_char_list, char_list, f"{DIR_UNAPCKED_DATA}/{DIR_FONT}", f"{DIR_REPACK_DATA}/{DIR_FONT}"
  )
