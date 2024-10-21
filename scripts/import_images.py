import os
import struct

import ndspy.lz10
from helper import (
  DIR_IMAGES,
  DIR_IMAGES_REPLACE,
  DIR_REPACK_DATA,
  DIR_UNAPCKED_DATA,
  rgb555_to_color,
)
from PIL import Image


def export_images(input_root: str, image_root: str, output_root: str):
  for root, dirs, files in os.walk(input_root):
    for file_name in files:
      file_name_without_ext, ext = os.path.splitext(file_name)
      if ext not in {".ntfp", ".nbfp"}:
        continue

      full_path = f"{root}/{file_name}"
      rel_path = os.path.relpath(f"{root}/{file_name_without_ext}", input_root)
      image_path = f"{image_root}/{rel_path}.png"
      if not os.path.exists(image_path):
        continue

      with open(full_path, "rb") as reader:
        palette_bytes = reader.read()

      assert len(palette_bytes) <= 512
      colors = []
      for r, g, b in map(rgb555_to_color, struct.unpack(f"<{len(palette_bytes) // 2}H", palette_bytes)):
        colors.extend([r, g, b])

      palette = Image.new("P", (16, 16))
      palette.putpalette(colors)

      image = Image.open(image_path).convert("RGB")
      image_converted: Image.Image = image.quantize(palette=palette, dither=Image.NONE)
      image_bytes = image_converted.tobytes()
      if ext == ".ntfp":
        ndspy.lz10.compressToFile(image_bytes, f"{output_root}/{rel_path}.cmp")


if __name__ == "__main__":
  export_images(f"{DIR_UNAPCKED_DATA}/{DIR_IMAGES}", DIR_IMAGES_REPLACE, f"{DIR_REPACK_DATA}/{DIR_IMAGES}")
