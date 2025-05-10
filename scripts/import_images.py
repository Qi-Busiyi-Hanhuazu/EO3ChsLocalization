import logging
import os
import struct

import ndspy.lz10
from helper import (
  DIR_IMAGES,
  DIR_IMAGES_REPLACE,
  DIR_REPACK_DATA,
  DIR_UNAPCKED_DATA,
  color_to_rgb555,
  rgb555_to_color,
)
from PIL import Image


def import_images(input_root: str, image_root: str, output_root: str, replace_palette: bool = False):
  for root, dirs, files in os.walk(input_root):
    for file_name in files:
      file_name_without_ext, ext = os.path.splitext(file_name)
      if ext not in {".ntfp", ".nbfp"}:
        continue

      palette_path = f"{root}/{file_name}"
      relative_path = os.path.relpath(f"{root}/{file_name_without_ext}", input_root)
      image_path = f"{image_root}/{relative_path}.png"
      if not os.path.exists(image_path):
        continue

      with open(palette_path, "rb") as reader:
        palette_bytes = reader.read()

      assert len(palette_bytes) <= 512
      if replace_palette:
        image_converted: Image.Image = Image.open(image_path)
        if image_converted.mode == "P":
          new_colors: list[int] = image_converted.getpalette()
          rgb555_colors: list[int] = []
          for i in range(0, len(new_colors), 3):
            rgb555_colors.append(color_to_rgb555((new_colors[i], new_colors[i + 1], new_colors[i + 2])))
          rgb555_colors.sort(key=lambda x: 0 if (x == 0x7C1F or x == 0x7FE0) else 1)
          if len(rgb555_colors) < len(palette_bytes) // 2:
            rgb555_colors += [0] * (len(palette_bytes) // 2 - len(rgb555_colors))
          palette_bytes = struct.pack(f"<{len(rgb555_colors)}H", *rgb555_colors)
          palette_bytes = palette_bytes[: len(palette_bytes)]
          with open(f"{output_root}/{relative_path}{ext}", "wb") as writer:
            writer.write(palette_bytes)

      colors = []
      for r, g, b in map(rgb555_to_color, struct.unpack(f"<{len(palette_bytes) // 2}H", palette_bytes)):
        colors.extend([r, g, b])

      palette = Image.new("P", (16, 16))
      palette.putpalette(colors)

      image = Image.open(image_path)
      if image.mode in {"P", "RGBA"}:
        image = image.convert("RGB")
      image_converted = image.quantize(palette=palette, dither=Image.Dither.NONE)

      if ext == ".nbfp":
        image_bytes = bytearray()
        x, y = 0, 0
        i = 0
        while y < image_converted.height:
          for y2 in range(8):
            for x2 in range(8):
              byte: int = image_converted.getpixel((x + x2, y + y2))
              image_bytes.append(byte)
              i += 1
          x += 8
          if x >= image_converted.width:
            x = 0
            y += 8
      else:
        image_bytes = image_converted.tobytes()

      if len(palette_bytes) <= 32:
        temp = bytearray()
        for i in range(0, len(image_bytes), 2):
          temp.append(image_bytes[i] | (image_bytes[i + 1] << 4))
        image_bytes = bytes(temp)

      if ext == ".ntfp":
        ndspy.lz10.compressToFile(image_bytes, f"{output_root}/{relative_path}.cmp")
      else:
        with open(f"{output_root}/{relative_path}.nbfc", "wb") as writer:
          writer.write(image_bytes)


if __name__ == "__main__":
  import_images(f"{DIR_UNAPCKED_DATA}/{DIR_IMAGES}", DIR_IMAGES_REPLACE, f"{DIR_REPACK_DATA}/{DIR_IMAGES}")
