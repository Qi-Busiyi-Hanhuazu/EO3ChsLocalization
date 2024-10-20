/*----------------------------------------------------------------------------*/
/*-- common.inc                                                             --*/
/*-- Common processes                                                       --*/
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
#ifndef _COMMON_INC_
#define _COMMON_INC_

/*----------------------------------------------------------------------------*/
#include <stdio.h>
#include <stdlib.h>

/*----------------------------------------------------------------------------*/
#define BYTE_0   0x00000000
#define KILO_0   0x00000000
#define MEGA_0   0x00000000
#define GIGA_0   0x00000000

#define BYTE_1   0x00000001
#define BYTE_2   0x00000002
#define BYTE_4   0x00000004
#define BYTE_8   0x00000008
#define BYTE_16  0x00000010
#define BYTE_32  0x00000020
#define BYTE_64  0x00000040
#define BYTE_128 0x00000080
#define BYTE_256 0x00000100
#define BYTE_512 0x00000200
#define KILO_1   0x00000400
#define KILO_2   0x00000800
#define KILO_4   0x00001000
#define KILO_8   0x00002000
#define KILO_16  0x00004000
#define KILO_32  0x00008000
#define KILO_64  0x00010000
#define KILO_128 0x00020000
#define KILO_256 0x00040000
#define KILO_512 0x00080000
#define MEGA_1   0x00100000
#define MEGA_2   0x00200000
#define MEGA_4   0x00400000
#define MEGA_8   0x00800000
#define MEGA_16  0x01000000
#define MEGA_32  0x02000000
#define MEGA_64  0x04000000
#define MEGA_128 0x08000000
#define MEGA_256 0x10000000
#define MEGA_512 0x20000000
#define GIGA_1   0x40000000
#define GIGA_2   0x80000000

#define MIN_FILESIZE MEGA_0
#define MAX_FILESIZE MEGA_256

/*----------------------------------------------------------------------------*/
#define EXIT(text) { printf(text); exit(EXIT_FAILURE); }

/*----------------------------------------------------------------------------*/
int   FileSize(char *filename);
void *FileLoad(char *filename);
void  FileSave(char *filename, void *buffer, int length);
void  Folder(char *path);
void *Memory(int length, int size);
void *NewMemory(void *buffer, int length, int size);
int   Extension(char *fn, char *fe);
int   StrLen(char *data);
void *MemCopy(void *target, void *source, int length);

/*----------------------------------------------------------------------------*/
int FileSize(char *filename) {
  FILE *fp;
  int   fs;

  if ((fp = fopen(filename, "rb")) == NULL) EXIT("File open error\n");
  fs = filelength(fileno(fp));
  if (fclose(fp) == EOF) EXIT("File close error\n");

  return(fs);
}

/*----------------------------------------------------------------------------*/
void *FileLoad(char *filename) {
  FILE *fp;
  int   fs;
  char *fb;

  if ((fp = fopen(filename, "rb")) == NULL) EXIT("File open error\n");
  fs = filelength(fileno(fp));
  if (fs < MIN_FILESIZE) EXIT("File too short\n");
  if (fs > MAX_FILESIZE) EXIT("File too big\n");
  fb = Memory(fs, sizeof(char));
  if (fread(fb, 1, fs, fp) != fs) EXIT("File read error\n");
  if (fclose(fp) == EOF) EXIT("File close error\n");

  return(fb);
}

/*----------------------------------------------------------------------------*/
void FileSave(char *filename, void *buffer, int length) {
  FILE *fp;

  Folder(filename);

  if ((fp = fopen(filename, "wb")) == NULL) EXIT("File create error\n");
  if (fwrite(buffer, 1, length, fp) != length) EXIT("File write error\n");
  if (fclose(fp) == EOF) EXIT("File close error\n");
}

/*----------------------------------------------------------------------------*/
void Folder(char *path) {
  int i;

  for (i = 0; path[i]; i++) {
    if ((path[i] == '/') || (path[i] == '\\')) {
      path[i] = 0;
      if (mkdir(path) > 0) EXIT("Create folder error\n");
      path[i] = '/';
    }
  }
}

/*----------------------------------------------------------------------------*/
void *Memory(int length, int size) {
  char *fb;

  fb = (char *)calloc(length, size);
  if (fb == NULL) EXIT("Memory error\n");

  return(fb);
}

/*----------------------------------------------------------------------------*/
void *NewMemory(void *buffer, int length, int size) {
  char *fb;

  fb = (char *)realloc(buffer, length * size);
  if (fb == NULL) EXIT("Memory error\n");

  return(fb);
}

/*----------------------------------------------------------------------------*/
int Extension(char *fn, char *fe) {
  int ln, le;

  ln = StrLen(fn);
  le = StrLen(fe);

  if (!le || (ln < le)) return(0);

  while (le) if ((fe[--le] & 0xDF) != (fn[--ln] & 0xDF)) return(0);

  return(1);
}

/*----------------------------------------------------------------------------*/
int StrLen(char *data) {
  int i;

  for (i = 0; *data++; i++);

  return(i);
}

/*----------------------------------------------------------------------------*/
void *MemCopy(void *target, void *source, int length) {
  int *src, *tgt;
  int num;

  src = (int *)source;
  tgt = (int *)target;
  num = length >> 2;
  while (num--) *tgt++ = *src++;

  source = (char *)src;
  target = (char *)tgt;
  num = length & 0x3;
  while (num--) *(char *)target++ = *(char *)source++;

  return(target);
}

/*----------------------------------------------------------------------------*/
#endif

/*----------------------------------------------------------------------------*/
/*--  EOF                                           Copyright (C) 2012 CUE  --*/
/*----------------------------------------------------------------------------*/
