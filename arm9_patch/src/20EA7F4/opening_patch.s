opening_patch:
  LDR R2, [R1, #0x18]
  MVN R0, #5
  MUL R2, R0, R2
  ADD R2, R2, #0x86
  MOV R0, #2
  B draw_text
