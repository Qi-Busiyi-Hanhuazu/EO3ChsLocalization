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
        raw_bytes = reader.read()

      assert len(raw_bytes) <= 512
      colors = []
      for r, g, b in map(rgb555_to_color, struct.unpack(f"<{len(raw_bytes) // 2}H", raw_bytes)):
        colors.extend([r, g, b])

      if os.path.exists(f"{input_root}/{rel_path}.cmp"):
        image_bytes = ndspy.lz10.decompressFromFile(f"{input_root}/{rel_path}.cmp")
      elif os.path.exists(f"{input_root}/{rel_path}.nbfc"):
        with open(f"{input_root}/{rel_path}.nbfc", "rb") as reader:
          image_bytes = reader.read()
      else:
        print(rel_path, "no compressed file found")
        continue

      width = 256
      while len(image_bytes) % width != 0 or len(image_bytes) // width % 8 != 0:
        width //= 2
      height = len(image_bytes) // width
      image = Image.frombytes("P", (width, height), image_bytes)
      image.putpalette(colors)

      output_path = f"{output_root}/{rel_path}.png"
      os.makedirs(os.path.dirname(output_path), exist_ok=True)
      image.save(output_path)


if __name__ == "__main__":
  export_images(f"{DIR_UNAPCKED_DATA}/{DIR_IMAGES}", "maintenance/images")
