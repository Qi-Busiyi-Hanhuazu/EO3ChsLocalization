/*----------------------------------------------------------------------------*/
/*-- packer.c                                                               --*/
/*-- File packer for some Nintendo DS Atlus games                           --*/
/*-- Copyright (C) 2012 CUE & Skye                                          --*/
/*--                                                                        --*/
/*-- This program is free software: you can redistribute it and/or modify   --*/
/*-- it under the terms of the GNU General Public License as published by   --*/
/*-- the Free Software Foundation, either version 3 of the License, or      --*/
/*-- (at your option) any later version.                                    --*/
/*--                                                                        --*/
/*-- This program is distributed in the hope that it will be useful,        --*/
/*-- but WITHOUT ANY WARRANTY; without even the implied warranty of         --*/
/*-- MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the           --*/
/*-- GNU General Public License for more details.                           --*/
/*--                                                                        --*/
/*-- You should have received a copy of the GNU General Public License      --*/
/*-- along with this program. If not, see <http://www.gnu.org/licenses/>.   --*/
/*----------------------------------------------------------------------------*/

/*----------------------------------------------------------------------------*/
#include "common.inc"

/*----------------------------------------------------------------------------*/
typedef struct {
  unsigned char name[256];
  unsigned int  number;
  unsigned int  index0;
  unsigned int  index1;
  unsigned int  length;
  unsigned int  offset;
} toc_table;
toc_table    *table;
unsigned int  tablesize, tablecount;

/*----------------------------------------------------------------------------*/
void Title(void);
void Usage(void);
void Pack(char *source, char *target);
void Tree(char *ndx, char *idx, int offset, char *path);
void GetData(char *idx, int isFile, char *filename);

/*----------------------------------------------------------------------------*/
int main(int argc, char **argv) {
  Title();

  if ((argc < 2) || (argc > 3)) Usage();

  Pack(argv[1], argc == 2 ? NULL : argv[2]);

  printf("\nDone\n");

  exit(EXIT_SUCCESS);
}

/*----------------------------------------------------------------------------*/
void Title(void) {
  printf(
    "\n"
    "PACKER - Copyright (C) 2012 CUE & Skye\n"
    "File packer for some Nintendo DS Atlus games\n"
    "\n"
  );
}

/*----------------------------------------------------------------------------*/
void Usage(void) {
  EXIT(
    "Supported games:\n"
    "- Megami Ibunroku: Devil Survivor (JAPAN)\n"
    "- Shin Megami Tensei: Devil Survivor (USA)\n"
    "- Devil Survivor 2 (JAPAN)\n"
    "- Shin Megami Tensei: Devil Survivor 2 (USA)\n"
    "- Sekaiju no Meikyuu III: Seikai no Raihousha (JAPAN)\n"
    "- Etrian Odyssey III: The Drowned City (USA)\n"
    "- Radiant Historia (JAPAN)\n"
    "- Radiant Historia (USA)\n"
    "\n"
    "Usage: PACKER file1 [file2]\n"
    "\n"
    "- unpack 'file1.bin' into '@file1\\' if no 'file2' is specified\n"
    "- pack files from '@file1\\' into 'file2.bin'\n"
    "\n"
    "* you do not have to specify the '.bin' extensions\n"
    "* 'file1.bin'/'file1.ndx'/'file1.idx' must be present in the same folder\n"
  );
}

/*----------------------------------------------------------------------------*/
void Pack(char *source, char *target) {
  unsigned char  ndx_name[256], idx_name[256], bin_name[256], new_name[256];
  unsigned char *ndx_buffer, *idx_buffer, *bin_buffer, *new_buffer;
  unsigned int   ndx_length, idx_length, bin_length, new_length, max_length;
  unsigned char  path[256];
  long long      data64;
  unsigned int   i, j, l;

  printf("- reading the original NDX file\n");
  sprintf(ndx_name, "%s.ndx", source);
  ndx_length = FileSize(ndx_name);
  ndx_buffer = FileLoad(ndx_name);

  printf("- reading the original IDX file\n");
  sprintf(idx_name, "%s.idx", source);
  idx_length = FileSize(idx_name);
  idx_buffer = FileLoad(idx_name);

  if (target == NULL) {
    printf("- reading the original BIN file\n");
    sprintf(bin_name, "%s.bin", source);
    bin_length = FileSize(bin_name);
    bin_buffer = FileLoad(bin_name);
  }

  printf("- generating the table of contents\n");
  tablecount = 0;
  tablesize = KILO_32;
  table = Memory(tablesize, sizeof(toc_table));

  l = sprintf(path, "%s", source);
  for (j = 0, i = l; i--; ) {
    if ((path[i] == '\\') || (path[i] == '/') || (path[i] == ':')) {
      j = i + 1;
      break;
    }
  }
  for (i = l; i > j; i--) path[i] = path[i-1];
  path[i] = '@';
  path[l+1] = 0;

  Tree(ndx_buffer, idx_buffer, 0, path);

  if (target == NULL) {
    for (i = 0; i < tablecount; i++) {
      printf("- unpacking \"%s\"\n", table[i].name);

      if (!table[i].number) {
        Folder(table[i].name);
      } else {
        FileSave(table[i].name, bin_buffer + table[i].offset, table[i].length);
      }
    }
  } else {
    max_length = MEGA_32;
    bin_length = 0;
    bin_buffer = Memory(max_length, sizeof(char));

    for (i = 0; i < tablecount; i++) {
      printf("- packing \"%s\"\n", table[i].name);

      if (!table[i].number) continue;

      new_length = FileSize(table[i].name);

      if (!table[i].index1) {
        if (new_length > 0x003FFFFF) EXIT("File size too big\n");
        if (bin_length > 0x07FFFFFF) EXIT("Offset too big\n");

        data64 = *(long long *)(idx_buffer + table[i].index0);
        data64 &= 0xFFFF000000000000ULL;
        data64 |= (long long)new_length << 26;
        data64 |= (long long)bin_length >> 1;
        *(long long *)(idx_buffer + table[i].index0) = data64;
      } else {
        *(unsigned int *)(idx_buffer + table[i].index1) = bin_length >> 2;
        if (table[i].number == 1) {
          if (new_length > 0x003FFFFF) EXIT("File size too big\n");

          data64 = *(long long *)(idx_buffer + table[i].index0);
          data64 &= 0xFFFF000003FFFFFFULL;
          data64 |= (long long)new_length << 26;
          *(long long *)(idx_buffer + table[i].index0) = data64;
        } else {
          *(unsigned int *)(idx_buffer + table[i].index1 + 4) = new_length;
        }
      }

      while (((bin_length + new_length + 3) & -4) > max_length) {
        max_length += MEGA_32;
        bin_buffer = NewMemory(bin_buffer, max_length, sizeof(char));
      }

      new_buffer = FileLoad(table[i].name);
      MemCopy(bin_buffer + bin_length, new_buffer, new_length);
      free(new_buffer);

      bin_length = (bin_length + new_length + 3) & -4;
    }

    printf("- writing the new BIN file\n");
    sprintf(bin_name, "%s.bin", target);
    FileSave(bin_name, bin_buffer, bin_length);

    printf("- writing the new IDX file\n");
    sprintf(idx_name, "%s.idx", target);
    FileSave(idx_name, idx_buffer, idx_length);

    printf("- writing the new NDX file\n");
    sprintf(ndx_name, "%s.ndx", target);
    FileSave(ndx_name, ndx_buffer, ndx_length);
  }

  free(bin_buffer);
  free(idx_buffer);
  free(ndx_buffer);
}

/*----------------------------------------------------------------------------*/
void Tree(char *ndx, char *idx, int offset, char *path) {
  unsigned char name[256];
  unsigned int  total, length, nchars, isFile, position;

  total = *(short *)(ndx + offset); offset += 2;
  while (total--) {
    length = sprintf(name, "%s/", path);
    nchars = *(unsigned short *)(ndx + offset); offset += 2;
    isFile = 0;
    while (nchars--) {
      if (ndx[offset] == '.') isFile = 1;
      name[length++] = ndx[offset++];
    }
    name[length] = 0;

    GetData(idx, isFile, name);

    position = *(unsigned int *)(ndx + offset); offset += 4;
    if (position) Tree(ndx, idx, position, name);
  }
}

/*----------------------------------------------------------------------------*/
void GetData(char *idx, int isFile, char *filename) {
  unsigned char newname[256], *name;
  unsigned int  extend, number, index0, index1, offset, length;
  long long     data48;
  unsigned int  len, hash, pos, max, ch, n;
  unsigned int  i;

  number = index0 = index1 = length = offset = 0;

  if (isFile) {
    len = sprintf(newname, "%s", filename);
    name = newname;
    while (*name++ != '/') len--;
    len--;
    for (hash = 0, i = 0; i < len; i++) {
      if ((name[i] >= 'A') && (name[i] <= 'Z')) name[i] += 'a' - 'A';
      hash = 37 * hash + name[i];
    }

    index0 = (hash & 0x07FF) * 6 + 8;
    data48 = *(long long *)(idx + index0) & 0x0000FFFFFFFFFFFFULL;
    if (!data48 && tablecount) {
      for (i = 0; i <= tablecount; i++) {
        if (table[i].index1) EXIT("File hash not indexed\n");
      }
    }

    length = data48 >> 26;
    offset = (data48 & 0x03FFFFFE) >> 1;
    extend = data48 & 1;

    if (extend) {
      pos = offset;
      max = idx[pos++];

      for (number = 0; number < max; number++) {
        index1 = pos;
        offset = *(unsigned int *)(idx + pos); pos += 4;
        if (number) { length = *(unsigned int *)(idx + pos); pos += 4; }
        ch = idx[pos++];
        n = idx[pos++];
        if ((n < len) && (name[n] == ch)) {
          if (!idx[pos]) break;
          ch = idx[pos++];
          n = idx[pos++];
          if ((n < len) && (name[n] == ch)) break;
          pos++;
        } else {
          if (idx[pos++]) pos += 2;
        }
      }
      if (number == max) EXIT("File is not in the index\n")
    }
    number++;
  }

  if (tablecount == tablesize) {
    tablesize += KILO_32;
    table = NewMemory(table, tablesize, sizeof(toc_table));
  }

  if (!number) sprintf(table[tablecount].name, "%s/", filename);
  else         sprintf(table[tablecount].name, "%s",  filename);
  table[tablecount].number = number;
  table[tablecount].index0 = index0;
  table[tablecount].index1 = index1;
  table[tablecount].length = length;
  table[tablecount].offset = offset << 2;

  tablecount++;
}

/*----------------------------------------------------------------------------*/
/*--  EOF                                     Copyright (C) 2012 CUE & Skye --*/
/*----------------------------------------------------------------------------*/
