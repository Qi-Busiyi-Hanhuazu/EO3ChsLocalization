import io
import os
import struct

from helper import DIR_UNAPCKED_DATA, PACK_PATH


class TocEntry:
  name: str
  number: int
  index0: int
  index1: int
  length: int
  offset: int

  def __init__(self, name, number, index0, index1, length, offset):
    self.name = name
    self.number = number
    self.index0 = index0
    self.index1 = index1
    self.length = length
    self.offset = offset


def unpack_files(file_path: str, output_path: str):
  file_without_extension = os.path.splitext(file_path)[0]
  idx_path = f"{file_without_extension}.idx"
  ndx_path = f"{file_without_extension}.ndx"
  bin_path = f"{file_without_extension}.bin"

  idx_reader = open(idx_path, "rb")
  ndx_reader = open(ndx_path, "rb")
  bin_reader = open(bin_path, "rb")

  tree(ndx_reader, idx_reader, bin_reader, 0, "", output_path)


def tree(
  ndx_reader: io.BytesIO,
  idx_reader: io.BytesIO,
  bin_reader: io.BytesIO,
  offset: int,
  path: str,
  output_path: str,
):
  ndx_reader.seek(offset)
  (total,) = struct.unpack("<H", ndx_reader.read(2))
  for i in range(total):
    (char_length,) = struct.unpack("<H", ndx_reader.read(2))
    is_file = False
    (file_name,) = struct.unpack(f"<{char_length}s", ndx_reader.read(char_length))
    file_name: bytes
    new_path = f"{path}/{file_name.decode("utf-8")}".removeprefix("/")

    (offset,) = struct.unpack("<I", ndx_reader.read(4))
    is_file = offset == 0
    if is_file:
      entry = get_data(idx_reader, new_path)
      os.makedirs(f"{output_path}/{os.path.dirname(new_path)}", exist_ok=True)
      with open(f"{output_path}/{new_path}", "wb") as file:
        bin_reader.seek(entry.offset)
        file.write(bin_reader.read(entry.length))

    else:
      position = ndx_reader.tell()
      tree(ndx_reader, idx_reader, bin_reader, offset, new_path, output_path)
      ndx_reader.seek(position)


def get_data(idx_reader: io.BytesIO, path: str):
  number, index0, index1, length, offset = 0, 0, 0, 0, 0
  lower_name = path.lower()

  hash = get_hash(lower_name)
  index0 = (hash & 0x07FF) * 6 + 8
  idx_reader.seek(index0)
  (_,) = struct.unpack("<Q", idx_reader.read(8))
  data48: int = _ & 0xFFFFFFFFFFFF
  length = data48 >> 26
  offset = (data48 & 0x03FFFFFE) >> 1
  extend = data48 & 1
  if extend > 0:
    idx_reader.seek(offset)
    (max,) = struct.unpack("<B", idx_reader.read(1))
    for number in range(max):
      index1 = idx_reader.tell()
      (offset,) = struct.unpack("<I", idx_reader.read(4))
      if number > 0:
        (length,) = struct.unpack("<I", idx_reader.read(4))
      ch, n = struct.unpack("<2B", idx_reader.read(2))
      if n < len(lower_name) and lower_name[n] == chr(ch):
        ch, n = struct.unpack("<2B", idx_reader.read(2))
        if ch == 0:
          break
        if n < len(lower_name) and lower_name[n] == chr(ch):
          break
        idx_reader.read(1)
      else:
        (_,) = struct.unpack("<B", idx_reader.read(1))
        if _ > 0:
          idx_reader.read(2)
  number += 1

  return TocEntry(path, number, index0, index1, length, offset << 2)


def get_hash(path: str) -> int:
  hash = 0
  for i in range(len(path)):
    hash = (hash * 0x25 + ord(path[i])) & 0xFFFFFFFF
  return hash


if __name__ == "__main__":
  unpack_files(PACK_PATH, DIR_UNAPCKED_DATA)
