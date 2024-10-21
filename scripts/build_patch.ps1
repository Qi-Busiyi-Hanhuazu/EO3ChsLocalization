$packer = "bin\NDS_Atlus_Packer\packer.exe"

# Clean output folder
if (Test-Path -Path "out\" -PathType "Container") {
  Remove-Item -Recurse -Force "out\"
}
if (Test-Path -Path "temp\" -PathType "Container") {
  Remove-Item -Recurse -Force "temp\"
}

# Unpack/extract original files
if (-Not (Test-Path -Path "original_files\data\Data\@Target\Data\Font\Font8x8.cmp" -PathType "Leaf")) {
  if (Test-Path -Path "original_files\data\Data\@Target\" -PathType "Container") {
    Remove-Item -Recurse -Force "original_files\data\Data\@Target\"
  }
  & $packer "original_files\data\Data\Target" | Out-Null
}
New-Item -ItemType "Directory" -Path "temp\pack\"
Copy-Item -Path "original_files\data\Data\*" -Destination "temp\pack\" -Recurse
& $packer "temp\pack\Target" | Out-Null

python scripts\decompress_arm9.py

python scripts\generate_char_table.py
python scripts\generate_char_list.py
python scripts\create_font.py

python scripts\convert_json_to_mbm.py
python scripts\convert_json_to_tbl.py

& $packer "temp\pack\Target" "out\data\Data\Target" | Out-Null

python scripts\compile_arm9_patch.py
python scripts\recompress_arm9.py

python scripts\edit_banner.py

Compress-Archive -Path "out/data/", "out/arm9.bin", "out/banner.bin" -Destination "patch-ds.zip" -Force
Move-Item -Path "patch-ds.zip" -Destination "out/patch-ds.xzp" -Force
