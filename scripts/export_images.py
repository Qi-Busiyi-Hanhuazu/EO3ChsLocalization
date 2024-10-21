import os
import struct

import ndspy.lz10
from helper import DIR_IMAGES, DIR_UNAPCKED_DATA, rgb555_to_color
from PIL import Image


def export_images(input_root: str, output_root: str):
  for root, dirs, files in os.walk(input_root):
    for file_name in files:
      if not file_name.endswith(".ntfp") and not file_name.endswith(".nbfp"):
        continue

      full_path = f"{root}/{file_name}"
      rel_path = os.path.relpath(f"{root}/{os.path.splitext(file_name)[0]}", input_root)

      with open(full_path, "rb") as reader:
        palette_bytes = reader.read()

      assert len(palette_bytes) <= 512
      colors = []
      for r, g, b in map(rgb555_to_color, struct.unpack(f"<{len(palette_bytes) // 2}H", palette_bytes)):
        colors.extend([r, g, b])

      if os.path.exists(f"{input_root}/{rel_path}.cmp"):
        image_bytes = ndspy.lz10.decompressFromFile(f"{input_root}/{rel_path}.cmp")
      elif os.path.exists(f"{input_root}/{rel_path}.nbfc"):
        with open(f"{input_root}/{rel_path}.nbfc", "rb") as reader:
          image_bytes = reader.read()
      else:
        print(rel_path, "no compressed file found")
        continue

      if len(palette_bytes) <= 32:
        temp = bytearray()
        for byte in image_bytes:
          temp.extend([byte & 0xF, byte >> 4])
        image_bytes = bytes(temp)

      width = 256
      while len(image_bytes) % width != 0 or len(image_bytes) // width % 8 != 0:
        width //= 2

      while width >= 8:
        height = len(image_bytes) // width
        image = Image.frombytes("P", (width, height), image_bytes)
        image.putpalette(colors)

        output_path = f"{output_root}/{width}/{rel_path}.png"
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        image.save(output_path)
        width //= 2


if __name__ == "__main__":
  export_images(f"{DIR_UNAPCKED_DATA}/{DIR_IMAGES}", "maintenance/images")
