PACKER.EXE
File packer for some Nintendo DS Atlus games
Copyright (C) 2012 CUE & Skye
http://romxhack.esforos.com/

Supported games:
- Megami Ibunroku: Devil Survivor (JAPAN)
- Shin Megami Tensei: Devil Survivor (USA)
- Devil Survivor 2 (JAPAN)
- Shin Megami Tensei: Devil Survivor 2 (USA)
- Sekaiju no Meikyuu III: Seikai no Raihousha (JAPAN)
- Etrian Odyssey III: The Drowned City (USA)
- Radiant Historia (JAPAN)
- Radiant Historia (USA)

All games have 3 files with the same name and different extension:
- 'file.ndx' with the file names
- 'file.idx' with the file pointers
- 'file.bin' with the file datas

Usage: PACKER file1 [file2]

- unpack 'file1.bin' into '@file1\\' if no 'file2' is specified
- pack files from '@file1\\' into 'file2.bin'

* you do not have to specify the '.bin' extensions
* 'file1.bin'/'file1.ndx'/'file1.idx' must be present in the same folder



INFO.EXE
Show info from NDX/IDX files
Copyright (C) 2012 CUE

Usage: INFO filename

* filename must be a valid '.ndx'/'.idx' file
