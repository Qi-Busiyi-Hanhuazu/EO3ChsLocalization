import os
import struct

import ndspy.lz10
from helper import DIR_IMAGES, DIR_UNAPCKED_DATA, rgb555_to_color
from PIL import Image


def export_images(input_root: str, output_root: str):
  for root, dirs, files in os.walk(input_root):
    for file_name in files:
      file_name_without_ext, ext = os.path.splitext(file_name)
      if ext not in {".ntfp", ".nbfp"}:
        continue

      full_path = f"{root}/{file_name}"
      rel_path = os.path.relpath(f"{root}/{file_name_without_ext}", input_root)

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
        if ext == ".nbfp":
          image = Image.new("P", (width, height))
          x, y = 0, 0
          i = 0
          while y < height:
            for y2 in range(8):
              for x2 in range(8):
                image.putpixel((x + x2, y + y2), image_bytes[i])
                i += 1
            x += 8
            if x >= width:
              x = 0
              y += 8
        else:
          image = Image.frombytes("P", (width, height), image_bytes)
        image.putpalette(colors)

        output_path = f"{output_root}/{width}/{rel_path}.png"
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        image.save(output_path)
        if ext == ".nbfp":
          break
        width //= 2


if __name__ == "__main__":
  export_images(f"{DIR_UNAPCKED_DATA}/{DIR_IMAGES}", "maintenance/images")
