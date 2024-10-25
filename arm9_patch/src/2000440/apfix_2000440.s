@ AP Fix
@ https://github.com/DS-Homebrew/TWiLightMenu/blob/master/resources/apfix/BJ3J-85D6.ips

LDR R0, =0x02146860
LDR R1, [R0]
LDR R2, =0xE0095D34
CMP R1, R2
MOVEQ R1, #0x72
STREQB R1, [R0, #8]
MOVEQ R1, #0x8E
STREQB R1, [R0, #0xC4]
BX LR
