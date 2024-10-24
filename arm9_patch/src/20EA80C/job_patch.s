job_patch:
  LDR R0, [R8, #0]
  BL shift_jis_str_len
  MVN R2, #4
  MUL R0, R2, R0
  ADD R2, R0, #0x3D
  CMP R10, #0xA
  B loc_2151194
