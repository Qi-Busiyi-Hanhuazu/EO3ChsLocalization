/*----------------------------------------------------------------------------*/
/*-- info.c                                                                 --*/
/*-- Show info from NDX/IDX files                                           --*/
/*-- Copyright (C) 2012 CUE                                                 --*/
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
void Title(void);
void Usage(void);
void Tree(char *ndx, int offset, char *path);
void Index(char *idx);

/*----------------------------------------------------------------------------*/
int main(int argc, char **argv) {
  unsigned char *buffer;
  unsigned int   length;

  Title();

  if (argc != 2) Usage();

  if (Extension(argv[1], ".ndx")) {
    length = FileSize(argv[1]);
    if (length < KILO_1) EXIT("File too short\n");
    if (length > MEGA_1) EXIT("File too big\n");
    buffer = FileLoad(argv[1]);
    if (buffer[1] || buffer[3]) EXIT("File is not a valid NDX file\n");
    Tree(buffer, 0, "");
    free(buffer);
  } else if (Extension(argv[1], ".idx")) {
    length = FileSize(argv[1]);
    if (length < KILO_1) EXIT("File too short\n");
    if (length > MEGA_1) EXIT("File too big\n");
    buffer = FileLoad(argv[1]);
    if (*(long long *)(buffer) != 0x800) EXIT("File is not a valid IDX file\n");
    Index(buffer);
    free(buffer);
  } else {
    EXIT("Unsupported extension\n");
  }

  printf("\nDone\n");

  exit(EXIT_SUCCESS);
}

/*----------------------------------------------------------------------------*/
void Title(void) {
  printf(
    "\n"
    "INFO - Copyright (C) 2012 CUE\n"
    "Show info from NDX/IDX files\n"
    "\n"
  );
}

/*----------------------------------------------------------------------------*/
void Usage(void) {
  EXIT(
    "Usage: INFO filename\n"
    "\n"
    "* 'filename' must be a valid '.ndx'/'.idx' file\n"
  );
}

/*----------------------------------------------------------------------------*/
void Tree(char *ndx, int offset, char *path) {
  unsigned char name[256];
  unsigned int  total, length, nchars, isFile, position, hash;
  unsigned int  i;

  total = *(unsigned short *)(ndx + offset); offset += 2;
  while (total--) {
    length = sprintf(name, "%s/", path);
    nchars = *(unsigned short *)(ndx + offset); offset += 2;
    isFile = 0;
    while (nchars--) {
      if (ndx[offset] == '.') isFile = 1;
      name[length++] = ndx[offset++];
    }
    name[length] = 0;

    if (!isFile) {
      printf("--------");
    } else {
      for (hash = 0, i = 1; i < length; i++) {
        hash = 37 * hash + name[i];
        if ((name[i] >= 'A') && (name[i] <= 'Z')) hash += 0x20;
      }
      printf("hash=%03X", hash & 0x7FF);
    }
    printf(" %s\n", name + 1);

    position = *(int *)(ndx + offset); offset += 4;
    if (position) Tree(ndx, position, name);
  }
}

/*----------------------------------------------------------------------------*/
void Index(char *idx) {
  long long    data48;
  unsigned int extend, number, index0, offset, length, hash, pos, max;
  unsigned int i;

  for (hash = 0; hash < 0x0800; hash++) {
    index0 = hash * 6 + 8;
    data48 = *(long long *)(idx + index0) & 0x0000FFFFFFFFFFFFULL;

    length = data48 >> 26;
    offset = (data48 & 0x03FFFFFE) >> 1;
    extend = data48 & 1;

    printf("hash=%03X  idx0=[%08X", hash, index0);
    for (i = 0; i < 6; i++) printf(":%02X", (unsigned char)idx[index0 + i]);
    printf("]");

    if (!data48) {
      printf("  idx1=--------  files=--  [--------:--------]");
    } else if (!extend) {
      printf("  idx1=--------  files=01  [%08X:%08X]", offset, length);
    } else {
      pos = offset;
      max = idx[pos++];
      printf("  idx1=%08X  files=%02X  ", pos, max);

      for (number = 0; number < max; number++) {
        offset = *(unsigned int *)(idx + pos); pos += 4;
        if (number) { length = *(unsigned int *)(idx + pos); pos += 4; }
        printf("[%08X:%08X", offset << 2, length);

        while (idx[pos]) {
          printf(":%02X", (unsigned char)idx[pos++]);
          printf(":%02X", (unsigned char)idx[pos++]);
        }
        printf(":%02X]", (unsigned char)idx[pos++]);
      }
    }
    printf("\n");
  }
}

/*----------------------------------------------------------------------------*/
/*--  EOF                                           Copyright (C) 2012 CUE  --*/
/*----------------------------------------------------------------------------*/
