import pygame
import ppu
import prettyhex

class Registers:
    r = {
        "a": 0x01, # 01
        "b": 0,
        "c": 0x13, # 13
        "d": 0,
        "e": 0xd8, # d8
        "h": 0x01, # 01
        "l": 0x4d, # 4d
        "sp": 0xfffe
    }
    pc = 0x0100

    flag_zero = 1
    flag_subtraction = 0
    flag_half_carry = 1
    flag_carry = 1

    ime_to_be_setted = 0
    ime = 0

    def __getitem__(self, key):
        if key == "f":
            return (self.flag_zero << 7) + (self.flag_subtraction << 6) + (self.flag_half_carry << 5) + (self.flag_carry << 4)
        elif key == "af":
            return (self.r["a"] << 8) + self["f"]
        elif key == "bc":
            return (self.r["b"] << 8) + self.r["c"]
        elif key == "de":
            return (self.r["d"] << 8) + self.r["e"]
        elif key == "hl":
            return (self.r["h"] << 8) + self.r["l"]
        elif key == "[hl]":
            return memory[self["hl"]]
        else:
            return self.r[key]

    def __setitem__(self, key, value):
        if key == "af":
            self.r["a"] = value >> 8
            self["f"] = value & 0b0000000011111111
        elif key == "bc":
            self.r["b"] = value >> 8
            self.r["c"] = value & 0b0000000011111111
        elif key == "de":
            self.r["d"] = value >> 8
            self.r["e"] = value & 0b0000000011111111
        elif key == "hl":
            self.r["h"] = value >> 8
            self.r["l"] = value & 0b0000000011111111
        elif key == "[hl]":
            memory[self["hl"]] = value
        elif key == "f":
            self.flag_zero = value >> 7
            self.flag_subtraction = (value >> 6) & 1
            self.flag_half_carry = (value >> 5) & 1
            self.flag_carry = (value >> 4) & 1
        else:
            self.r[key] = value

    def __repr__(self):
        rstring = "AF  = $" + prettyhex.prettyhex2(self["a"]) + prettyhex.prettyhex2(self["f"])
        rstring += "\nBC  = $" + prettyhex.prettyhex2(self["b"]) + prettyhex.prettyhex2(self["c"])
        rstring += "\nDE  = $" + prettyhex.prettyhex2(self["d"]) + prettyhex.prettyhex2(self["e"])
        rstring += "\nHL  = $" + prettyhex.prettyhex2(self["h"]) + prettyhex.prettyhex2(self["l"])
        rstring += "\nSP  = $" + prettyhex.prettyhex(self["sp"])
        rstring += "\nPC  = $" + prettyhex.prettyhex(self.pc)
        if self.ime == 1:
            rstring += "\nIME = Enabled\n"
        else:
            rstring += "\nIME = Disabled\n"
        return rstring

    def debug_compare(self):
        return [self["af"], self["bc"], self["de"], self["hl"], self["sp"], self.pc, self.ime]

class Memory:
    rom = [0 for _ in range(2**15)]
    vram = [0 for _ in range(2**13)]
    xram = [0 for _ in range(2**13)]
    wram = [0 for _ in range(2**13)]
    oam = [0 for _ in range(160)]
    io_registers = [0 for _ in range(2**7)]
    hram = [0 for _ in range((2**7)-1)]
    interrupt = 0

    def __getitem__(self, key):
        # ROM
        if 0x0000 <= key <= 0x7fff:
            return self.rom[key]
        # VRAM
        elif 0x8000 <= key <= 0x9fff:
            return self.vram[key - 0x8000]
        # External RAM
        elif 0xa000 <= key <= 0xbfff:
            return self.xram[key - 0xa000]
        # Working RAM
        elif 0xc000 <= key <= 0xdfff:
            return self.wram[key - 0xc000]
        # Echo RAM
        elif 0xe000 <= key <= 0xfdff:
            return self.wram[key - 0xe000]
        # Object Attribution Memory
        elif 0xfe00 <= key <= 0xfe9f:
            return self.oam[key - 0xfe00]
        # Not usable
        elif 0xfea0 <= key <= 0xfeff:
            return 255
        # I/O Registers
        elif 0xff00 <= key <= 0xff7f:
            return self.io_registers[key - 0xff00]
        # High RAM
        elif 0xff80 <= key <= 0xfffe:
            return self.hram[key - 0xff80]
        # Interrupt
        elif key == 0xffff:
            return self.interrupt

    def __setitem__(self, key, value):
        # ROM
        if 0x0000 <= key <= 0x7fff:
            #self.rom[key] = value
            pass
        # VRAM
        elif 0x8000 <= key <= 0x9fff:
            self.vram[key - 0x8000] = value
        # External RAM
        elif 0xa000 <= key <= 0xbfff:
            self.xram[key - 0xa000] = value
        # Working RAM
        elif 0xc000 <= key <= 0xdfff:
            self.wram[key - 0xc000] = value
        # Echo RAM
        elif 0xe000 <= key <= 0xfdff:
            self.wram[key - 0xe000] = value
        # Object Attribution Memory
        elif 0xfe00 <= key <= 0xfe9f:
            self.oam[key - 0xfe00] = value
        # Not usable
        elif 0xfea0 <= key <= 0xfeff:
            pass
        # I/O Registers
        elif 0xff00 <= key <= 0xff7f:
            self.io_registers[key - 0xff00] = value
        # High RAM
        elif 0xff80 <= key <= 0xfffe:
            self.hram[key - 0xff80] = value
        # Interrupt
        elif key == 0xffff:
            self.interrupt = value

def load_rom(filename):
    with open(filename, 'rb') as f:
        for i in range(2**15):
            instruction = f.read(1)
            if instruction == b'':
                break
            memory.rom[i] = (int.from_bytes(instruction))

def createSquare(x, y, color):
    pygame.draw.rect(pygamedisplay, color, [x, y, size_mul, size_mul])
def visualizeGrid(display):
    y = -memory[0xff42] * size_mul
    for row in display:
        x = -memory[0xff43] *size_mul
        for item in row:
            if item == 0:
                createSquare(x, y, (198, 222, 140))
            elif item == 1:
                createSquare(x, y, (132, 165, 99))
            elif item == 2:
                createSquare(x, y, (57, 97, 57))
            else:
                createSquare(x, y, (8, 24, 16))

            x += size_mul
        y += size_mul

    y = (-memory[0xff42] + 256)* size_mul
    for row in display:
        x = -memory[0xff43] *size_mul
        for item in row:
            if item == 0:
                createSquare(x, y, (198, 222, 140))
            elif item == 1:
                createSquare(x, y, (132, 165, 99))
            elif item == 2:
                createSquare(x, y, (57, 97, 57))
            else:
                createSquare(x, y, (8, 24, 16))

            x += size_mul
        y += size_mul
    pygame.display.update()


def is_carry(val1, val2, bits):
    carry_size = (2 ** bits) - 1
    if registers.flag_subtraction == 1:
        if ((val1 & carry_size) - (val2 & carry_size)) < 0:
            return 1
        return 0
    else:
        if ((val1 & carry_size) + (val2 & carry_size)) > carry_size:
            return 1
        return 0

def fetch():
    opcode = memory[registers.pc]
    a1 = memory[(registers.pc + 1)]
    a2 = memory[(registers.pc + 2)]
    return opcode, a1, a2

def execute(instruction):
    decoded_instruction = []
    rst_vec = [0x00, 0x08, 0x10, 0x18, 0x20, 0x28, 0x30, 0x38]

    opcode = instruction[0]
    imm8 = instruction[1]
    imm16 = instruction[2]*256 + instruction[1]

    condition = cond[(opcode & 0b00011000) >> 3]

    dest_source_r16mem = r16mem[(opcode & 0b00110000) >> 4]

    operand_r8 = r8[opcode & 0b00000111]
    operand_r16 = r16[(opcode & 0b00110000) >> 4]
    operand_stk_r8 = r8[(opcode & 0b00111000) >> 3]
    operand_stk_r16 = r16stk[(opcode & 0b00110000) >> 4]

    b3 = (opcode & 0b00111000) >> 3
    tgt3 = rst_vec[(opcode & 0b00111000) >> 3]

    # block 0
    if 0x00 <= opcode <= 0X3f:
        # NOP
        if opcode == 0x00:
            decoded_instruction = ["NOP"]
            registers.pc += 1
        # LD r16, imm16
        elif opcode in [0x01, 0x11, 0x21, 0x31]:
            decoded_instruction = ["LD", operand_r16, hex(imm16)]
            registers.pc += 3
            registers[operand_r16] = imm16
        # LD [r16mem], a
        elif opcode in [0x02, 0x12, 0x22, 0x32]:
            decoded_instruction = ["LD", ("[" + dest_source_r16mem + "]"), "a"]
            registers.pc += 1
            if dest_source_r16mem == "hl+":
                registers["[hl]"] = registers["a"]
                registers["hl"] += 1
                registers["hl"] &= 65535
            elif dest_source_r16mem == "hl-":
                registers["[hl]"] = registers["a"]
                registers["hl"] -= 1
                registers["hl"] &= 65535
            else:
                memory[registers[dest_source_r16mem]] = registers["a"]
        # LD a, [r16mem]
        elif opcode in [0x0a, 0x1a, 0x2a, 0x3a]:
            decoded_instruction = ["LD", "a", ("[" + dest_source_r16mem+ "]")]
            registers.pc += 1
            if dest_source_r16mem == "hl+":
                registers["a"] = registers["[hl]"]
                registers["hl"] += 1
                registers["hl"] &= 65535
            elif dest_source_r16mem == "hl-":
                registers["a"] = registers["[hl]"]
                registers["hl"] -= 1
                registers["hl"] &= 65535
            else:
                registers["a"] = memory[registers[dest_source_r16mem]]
        # LD [imm16], sp
        elif opcode == 0x08:
            decoded_instruction = ["LD", ("[" + str(hex(imm16)) + "]")]
            registers.pc += 3
            memory[imm16] = registers["sp"] & 255
            memory[imm16 + 1] = registers["sp"] >> 8
        # INC r16
        elif opcode in [0x03, 0x13, 0x23, 0x33]:
            decoded_instruction = ["INC", operand_r16]
            registers.pc += 1
            registers[operand_r16] += 1
            registers[operand_r16] &= 65535
        # DEC r16
        elif opcode in [0x0b, 0x1b, 0x2b, 0x3b]:
            decoded_instruction = ["DEC", operand_r16]
            registers.pc += 1
            registers[operand_r16] -= 1
            registers[operand_r16] &= 65535
        # ADD hl, r16
        elif opcode in [0x09, 0x19, 0x29, 0x39]:
            registers.pc += 1
            registers.flag_subtraction = 0
            registers.flag_carry = is_carry(registers["hl"], registers[operand_r16], 16)
            registers.flag_half_carry = is_carry(registers["hl"], registers[operand_r16], 12)
            registers["hl"] += registers[operand_r16]
            registers["hl"] &= 65535
        # INC r8
        elif opcode in [0x04, 0x14, 0x24, 0x34, 0x0c, 0x1c, 0x2c, 0x3c]:
            decoded_instruction = ["INC", operand_stk_r8]
            registers.pc += 1
            registers.flag_subtraction = 0
            registers.flag_half_carry = is_carry(registers[operand_stk_r8], 1, 4)
            registers[operand_stk_r8] += 1
            registers[operand_stk_r8] &= 255
            if registers[operand_stk_r8] == 0:
                registers.flag_zero = 1
            else:
                registers.flag_zero = 0
        # DEC r8
        elif opcode in [0x05, 0x15, 0x25, 0x35, 0x0d, 0x1d, 0x2d, 0x3d]:
            decoded_instruction = ["DEC", operand_stk_r8]
            registers.pc += 1
            registers.flag_subtraction = 1
            registers.flag_half_carry = is_carry(registers[operand_stk_r8], 1, 4)
            registers[operand_stk_r8] -= 1
            registers[operand_stk_r8] &= 255
            if registers[operand_stk_r8] == 0:
                registers.flag_zero = 1
            else:
                registers.flag_zero = 0
        # LD r8, imm8
        elif opcode in [0x06, 0x16, 0x26, 0x36, 0x0e, 0x1e, 0x2e, 0x3e]:
            decoded_instruction = ["LD", operand_stk_r8, hex(imm8)]
            registers.pc += 2
            registers[operand_stk_r8] = imm8
        # RLCA
        elif opcode == 0x07:
            decoded_instruction = ["RLCA"]
            registers.pc += 1
            registers.flag_half_carry = 0
            registers.flag_zero = 0
            registers.flag_subtraction = 0
            registers.flag_carry = (registers[operand_r8] & 128) >> 7
            registers["a"] = (registers["a"] << 1) | registers.flag_carry
        # RRCA
        elif opcode == 0x0f:
            decoded_instruction = ["RRCA"]
            registers.pc += 1
            registers.flag_half_carry = 0
            registers.flag_zero = 0
            registers.flag_subtraction = 0
            registers.flag_carry = registers[operand_r8] & 1
            registers["a"] = (registers["a"] >> 1) | (registers.flag_carry << 7)
        # RLA
        elif opcode == 0x17:
            decoded_instruction = ["RLA"]
            registers.pc += 1
            registers.flag_half_carry = 0
            registers.flag_zero = 0
            registers.flag_subtraction = 0
            registers["a"] = (registers["a"] << 1) | registers.flag_carry
            registers.flag_carry = (registers["a"] >> 8)
            registers["a"] &= 255
        # RRA
        elif opcode == 0x1f:
            decoded_instruction = ["RRA"]
            registers.pc += 1
            registers.flag_half_carry = 0
            registers.flag_zero = 0
            registers.flag_subtraction = 0
            pflag = registers.flag_carry
            registers.flag_carry = registers["a"] & 1
            registers["a"] = (registers["a"] >> 1) | (pflag << 7)
        # DAA TODO
        elif opcode == 0x27:
            decoded_instruction = ["DAA"]
            registers.pc += 1
            print("meow")
            registers.flag_half_carry = 0
            if registers["a"] == 0:
                registers.flag_zero = 1
            else:
                registers.flag_zero = 0
        # CPL
        elif opcode == 0x2f:
            decoded_instruction = ["CPL"]
            registers.pc += 1
            registers["a"] = (~registers["a"]) & 255
        # SCF
        elif opcode == 0x37:
            decoded_instruction = ["SCF"]
            registers.pc += 1
            registers.flag_carry = 1
            registers.flag_subtraction = 0
            registers.flag_half_carry = 0
        # CCF
        elif opcode == 0x3f:
            decoded_instruction = ["CCF"]
            registers.pc += 1
            if registers.flag_carry == 1:
                registers.flag_carry = 0
            else:
                registers.flag_carry = 1
            registers.flag_subtraction = 0
            registers.flag_half_carry = 0
        # JR imm8
        elif opcode == 0x18:
            registers.pc += 2
            if imm8 > 127:
                imm8 -= 256
            decoded_instruction = ["JR", imm8]
            registers.pc += imm8
        # JR cond, imm8
        elif opcode in [0x20, 0x30, 0x28, 0x38]:
            registers.pc += 2
            if imm8 > 127:
                imm8 -= 256
            decoded_instruction = ["JR", imm8]
            if registers.flag_zero == 0 and condition == "nz":
                registers.pc += imm8
            elif registers.flag_zero == 1 and condition == "z":
                registers.pc += imm8
            elif registers.flag_carry == 0 and condition == "nc":
                registers.pc += imm8
            elif registers.flag_carry == 1 and condition == "c":
                registers.pc += imm8
        # STOP
        elif opcode == 0x10:
            decoded_instruction = ["STOP"]
            registers.pc += 2

    # block 1
    elif 0x40 <= opcode <= 0X7f:
        registers.pc += 1
        # HALT
        if opcode == 0x76:
            decoded_instruction = ["HALT"]
        # LD r8, r8
        else:
            decoded_instruction = ["LD", operand_stk_r8, operand_r8]
            registers[operand_stk_r8] = registers[operand_r8]


    # block 2
    elif 0x80 <= opcode <= 0Xbf:
        registers.pc += 1
        # ADD a, r8
        if 0x80 <= opcode <= 0X87:
            decoded_instruction = ["ADD", "a", operand_r8]
            registers.flag_subtraction = 0
            registers.flag_carry = is_carry(registers["a"], registers[operand_r8], 8)
            registers.flag_half_carry = is_carry(registers["a"], registers[operand_r8], 4)
            registers["a"] += registers[operand_r8]

            registers["a"] &= 255
            if registers["a"] == 0:
                registers.flag_zero = 1
            else:
                registers.flag_zero = 0
        # ADC a, r8
        elif 0x88 <= opcode <= 0X8f:
            decoded_instruction = ["ADC", "a", operand_r8]
            prevflag = registers.flag_carry
            registers.flag_subtraction = 0
            registers.flag_carry = is_carry(registers["a"], registers[operand_r8] + prevflag, 8)
            registers.flag_half_carry = is_carry(registers["a"], registers[operand_r8] + prevflag, 4)
            registers["a"] += registers[operand_r8]

            registers["a"] &= 255
            registers["a"] += prevflag
            if registers["a"] == 0:
                registers.flag_zero = 1
            else:
                registers.flag_zero = 0
        # SUB a, r8
        elif 0x90 <= opcode <= 0X97:
            decoded_instruction = ["SUB", "a", operand_r8]
            registers.flag_subtraction = 1
            registers.flag_carry = is_carry(registers["a"], registers[operand_r8], 8)
            registers.flag_half_carry = is_carry(registers["a"], registers[operand_r8], 4)
            registers["a"] -= registers[operand_r8]

            registers["a"] &= 255
            if registers["a"] == 0:
                registers.flag_zero = 1
            else:
                registers.flag_zero = 0
        # SBC a, r8
        elif 0x98 <= opcode <= 0X9f:
            decoded_instruction = ["SBC", "a", operand_r8]
            registers.flag_subtraction = 1
            if operand_r8 != "a":
                registers.flag_carry = is_carry(registers["a"], (registers[operand_r8] + registers.flag_carry), 8)
            registers.flag_half_carry = is_carry(registers["a"], registers[operand_r8], 4)
            registers["a"] -= registers[operand_r8]

            registers["a"] &= 255
            if registers["a"] == 0:
                registers.flag_zero = 1
            else:
                registers.flag_zero = 0
        # AND a, r8
        elif 0xa0 <= opcode <= 0Xa7:
            decoded_instruction = ["AND", "a", operand_r8]
            registers.flag_subtraction = 0
            registers.flag_half_carry = 1
            registers.flag_carry = 0

            registers["a"] = registers["a"] & registers[operand_r8]
            if registers["a"] == 0:
                registers.flag_zero = 1
            else:
                registers.flag_zero = 0
        # XOR a, r8
        elif 0xa8 <= opcode <= 0Xaf:
            decoded_instruction = ["XOR", "a", operand_r8]
            registers.flag_subtraction = 0
            registers.flag_half_carry = 0
            registers.flag_carry = 0

            registers["a"] = registers["a"] ^ registers[operand_r8]
            if registers["a"] == 0:
                registers.flag_zero = 1
            else:
                registers.flag_zero = 0
        # OR a, r8
        elif 0xb0 <= opcode <= 0Xb7:
            decoded_instruction = ["OR", "a", operand_r8]
            registers.flag_subtraction = 0
            registers.flag_half_carry = 0
            registers.flag_carry = 0

            registers["a"] = registers["a"] | registers[operand_r8]
            if registers["a"] == 0:
                registers.flag_zero = 1
            else:
                registers.flag_zero = 0
        # CP a, r8
        elif 0xb8 <= opcode <= 0Xbf:
            decoded_instruction = ["CP", "a", operand_r8]
            registers.flag_subtraction = 1
            registers.flag_carry = is_carry(registers["a"], imm8, 8)
            registers.flag_half_carry = is_carry(registers["a"], imm8, 4)
            if registers["a"] - registers[operand_r8] == 0:
                registers.flag_zero = 1
            else:
                registers.flag_zero = 0

    # block 3
    elif 0xc0 <= opcode <= 0Xff:
        # ADD a, imm8
        if opcode == 0xc6:
            decoded_instruction = ["ADD", "a", imm8]
            registers.pc += 2
            registers.flag_subtraction = 0
            registers.flag_carry = is_carry(registers["a"], imm8, 8)
            registers.flag_half_carry = is_carry(registers["a"], imm8, 4)

            registers["a"] += imm8
            registers["a"] &= 255
            if registers["a"] == 0:
                registers.flag_zero = 1
            else:
                registers.flag_zero = 0
        # ADC a, imm8
        elif opcode == 0xce:
            decoded_instruction = ["ADC", "a", imm8]
            registers.pc += 2
            prevflag = registers.flag_carry
            registers.flag_subtraction = 0
            registers.flag_carry = is_carry(registers["a"], imm8, 8)
            registers.flag_half_carry = is_carry(registers["a"], imm8, 4)

            registers["a"] += imm8
            registers["a"] &= 255
            registers["a"] += prevflag
            if registers["a"] == 0:
                registers.flag_zero = 1
            else:
                registers.flag_zero = 0
        # SUB a, imm8
        elif opcode == 0xd6:
            decoded_instruction = ["SUB", "a", imm8]
            registers.pc += 2
            registers.flag_subtraction = 1
            registers.flag_carry = is_carry(registers["a"], imm8, 8)
            registers.flag_half_carry = is_carry(registers["a"], imm8, 4)

            registers["a"] -= imm8
            registers["a"] &= 255
            if registers["a"] == 0:
                registers.flag_zero = 1
            else:
                registers.flag_zero = 0
        # SBC a, imm8
        elif opcode == 0xde:
            decoded_instruction = ["SBC", "a", imm8]
            registers.pc += 2
            registers.flag_subtraction = 1

            registers.flag_carry = is_carry(registers["a"], (imm8 + registers.flag_carry), 8)
            registers.flag_half_carry = is_carry(registers["a"], imm8, 4)

            registers["a"] -= imm8
            registers["a"] &= 255
            if registers["a"] == 0:
                registers.flag_zero = 1
            else:
                registers.flag_zero = 0
        # AND a, imm8
        elif opcode == 0xe6:
            decoded_instruction = ["AND", "a", imm8]
            registers.pc += 2
            registers.flag_subtraction = 0
            registers.flag_half_carry = 1
            registers.flag_carry = 0

            registers["a"] &= imm8
            if registers["a"] == 0:
                registers.flag_zero = 1
            else:
                registers.flag_zero = 0
        # XOR a, imm8
        elif opcode == 0xee:
            decoded_instruction = ["XOR", "a", imm8]
            registers.pc += 2
            registers.flag_subtraction = 0
            registers.flag_half_carry = 0
            registers.flag_carry = 0

            registers["a"] ^= imm8
            if registers["a"] == 0:
                registers.flag_zero = 1
            else:
                registers.flag_zero = 0
        # OR a, imm8
        elif opcode == 0xf6:
            decoded_instruction = ["OR", "a", imm8]
            registers.pc += 2
            registers.flag_subtraction = 0
            registers.flag_half_carry = 0
            registers.flag_carry = 0

            registers["a"] |= imm8
            if registers["a"] == 0:
                registers.flag_zero = 1
            else:
                registers.flag_zero = 0
        # CP a, imm8
        elif opcode == 0xfe:
            decoded_instruction = ["CP", "a", imm8]
            registers.pc += 2
            registers.flag_subtraction = 1
            registers.flag_carry = is_carry(registers["a"], imm8, 8)
            registers.flag_half_carry = is_carry(registers["a"], imm8, 4)
            if registers["a"] - imm8 == 0:
                registers.flag_zero = 1
            else:
                registers.flag_zero = 0

        # RET cond
        elif opcode in [0xc0, 0xd0, 0xc8, 0xd8]:
            decoded_instruction = ["RET", condition]
            registers.pc += 1
            flag = False
            if registers.flag_zero == 0 and condition == "nz":
                flag = True
            elif registers.flag_zero == 1 and condition == "z":
                flag = True
            elif registers.flag_carry == 0 and condition == "nc":
                flag = True
            elif registers.flag_carry == 1 and condition == "c":
                flag = True
            if flag:
                registers.pc = memory[registers["sp"]]
                registers["sp"] += 1
                registers["sp"] &= 65535
                registers.pc += (memory[registers["sp"]] << 8)
                registers["sp"] += 1
                registers["sp"] &= 65535
        # RET
        elif opcode == 0xc9:
            decoded_instruction = ["RET"]
            registers.pc += 1
            registers.pc = memory[registers["sp"]]
            registers["sp"] += 1
            registers["sp"] &= 65535
            registers.pc += (memory[registers["sp"]] << 8)
            registers["sp"] += 1
            registers["sp"] &= 65535
        # RETI
        elif opcode == 0xd9:
            decoded_instruction = ["RETI"]
            registers.pc += 1
            registers.ime_to_be_setted = 1
            registers.pc = memory[registers["sp"]]
            registers["sp"] += 1
            registers["sp"] &= 65535
            registers.pc += (memory[registers["sp"]] << 8)
            registers["sp"] += 1
            registers["sp"] &= 65535
        # JP cond, imm16
        elif opcode in [0xc2, 0xd2, 0xca, 0xda]:
            decoded_instruction = ["JP", condition, hex(imm16)]
            registers.pc += 3
            if registers.flag_zero == 0 and condition == "nz":
                registers.pc = imm16
            elif registers.flag_zero == 1 and condition == "z":
                registers.pc = imm16
            elif registers.flag_carry == 0 and condition == "nc":
                registers.pc = imm16
            elif registers.flag_carry == 1 and condition == "c":
                registers.pc = imm16
        # JP imm16
        elif opcode == 0xc3:
            decoded_instruction = ["JP", hex(imm16)]
            registers.pc = imm16
        # JP hl
        elif opcode == 0xe9:
            decoded_instruction = ["JP", "hl"]
            registers.pc = registers["hl"]
        # CALL cond, imm16
        elif opcode in [0xc4, 0xd4, 0xcc, 0xdc]:
            decoded_instruction = ["CALL", condition, hex(imm16)]
            registers.pc += 3
            flag = False
            if registers.flag_zero == 0 and condition == "nz":
                flag = True
            elif registers.flag_zero == 1 and condition == "z":
                flag = True
            elif registers.flag_carry == 0 and condition == "nc":
                flag = True
            elif registers.flag_carry == 1 and condition == "c":
                flag = True
            if flag:
                registers["sp"] -= 1
                registers["sp"] &= 65535
                memory[registers["sp"]] = registers.pc >> 8
                registers["sp"] -= 1
                registers["sp"] &= 65535
                memory[registers["sp"]] = registers.pc & 255
                registers.pc = imm16
        # CALL imm16
        elif opcode == 0xcd:
            decoded_instruction = ["CALL", hex(imm16)]
            registers.pc += 3
            registers["sp"] -= 1
            registers["sp"] &= 65535
            memory[registers["sp"]] = registers.pc >> 8
            registers["sp"] -= 1
            registers["sp"] &= 65535
            memory[registers["sp"]] = registers.pc & 255
            registers.pc = imm16
        # RST tgt3
        elif opcode in [0xc7, 0xd7, 0xe7, 0xf7, 0xcf, 0xdf, 0xef, 0xff]:
            decoded_instruction = ["RST", hex(tgt3)]
            registers.pc += 1
            registers["sp"] -= 1
            registers["sp"] &= 65535
            memory[registers["sp"]] = registers.pc >> 8
            registers["sp"] -= 1
            registers["sp"] &= 65535
            memory[registers["sp"]] = registers.pc & 255
            registers.pc = tgt3
        # POP r16stk (load from stack)
        elif opcode in [0xc1, 0xd1, 0xe1, 0xf1]:
            decoded_instruction = ["POP", operand_stk_r16]
            registers.pc += 1
            registers[operand_stk_r16] = memory[registers["sp"]]
            registers["sp"] += 1
            registers["sp"] &= 65535
            registers[operand_stk_r16] += (memory[registers["sp"]] << 8)
            registers["sp"] += 1
            registers["sp"] &= 65535
        # PUSH r16stk (save on stack)
        elif opcode in [0xc5, 0xd5, 0xe5, 0xf5]:
            decoded_instruction = ["PUSH", operand_stk_r16]
            registers.pc += 1
            registers["sp"] -= 1
            registers["sp"] &= 65535
            memory[registers["sp"]] = registers[operand_stk_r16] >> 8
            registers["sp"] -= 1
            registers["sp"] &= 65535
            memory[registers["sp"]] = registers[operand_stk_r16] & 255
        # PREFIX
        elif opcode == 0xcb:
            registers.pc += 2
            # RLC r8
            if 0x00 <= instruction[1] <= 0x07:
                decoded_instruction = ["RLC", operand_r8]
                registers.flag_half_carry = 0
                registers.flag_subtraction = 0
                registers.flag_carry = (registers[operand_r8] & 128) >> 7
                registers[operand_r8] = (registers[operand_r8] << 1) | registers.flag_carry
                if registers[operand_r8] == 0:
                    registers.flag_zero = 1
                else:
                    registers.flag_zero = 0
            # RRC r8
            elif 0x08 <= instruction[1] <= 0x0f:
                decoded_instruction = ["RRC", operand_r8]
                registers.flag_half_carry = 0
                registers.flag_subtraction = 0
                registers.flag_carry = registers[operand_r8] & 1
                registers[operand_r8] = (registers[operand_r8] >> 1) | (registers.flag_carry << 7)
                if registers[operand_r8] == 0:
                    registers.flag_zero = 1
                else:
                    registers.flag_zero = 0
            # RL r8
            elif 0x10 <= instruction[1] <= 0x17:
                decoded_instruction = ["RL", operand_r8]
                registers.flag_half_carry = 0
                registers.flag_subtraction = 0
                registers[operand_r8] = (registers[operand_r8] << 1) | registers.flag_carry
                registers.flag_carry = (registers[operand_r8] >> 8)
                registers[operand_r8] &= 255
                if registers[operand_r8] == 0:
                    registers.flag_zero = 1
                else:
                    registers.flag_zero = 0
            # RR r8
            elif 0x18 <= instruction[1] <= 0x1f:
                decoded_instruction = ["RR", operand_r8]
                registers.flag_half_carry = 0
                registers.flag_subtraction = 0
                pflag = registers.flag_carry
                registers.flag_carry = registers[operand_r8] & 1
                registers[operand_r8] = (registers[operand_r8] >> 1) | (pflag << 7)
                if registers[operand_r8] == 0:
                    registers.flag_zero = 1
                else:
                    registers.flag_zero = 0
            # SLA r8
            elif 0x20 <= instruction[1] <= 0x27:
                decoded_instruction = ["SLA", operand_r8]
                registers.flag_half_carry = 0
                registers.flag_subtraction = 0
                registers[operand_r8] = (registers[operand_r8] << 1)
                registers.flag_carry = (registers[operand_r8] >> 8)
                registers[operand_r8] &= 255
                if registers[operand_r8] == 0:
                    registers.flag_zero = 1
                else:
                    registers.flag_zero = 0
            # SRA r8
            elif 0x28 <= instruction[1] <= 0x2f:
                decoded_instruction = ["SRA", operand_r8]
                registers.flag_half_carry = 0
                registers.flag_subtraction = 0
                registers.flag_carry = registers[operand_r8] & 1
                registers[operand_r8] = (registers[operand_r8] >> 1)
                registers[operand_r8] |= (registers[operand_r8] & 128) << 1
                if registers[operand_r8] == 0:
                    registers.flag_zero = 1
                else:
                    registers.flag_zero = 0
            # SWAP r8
            elif 0x30 <= instruction[1] <= 0x37:
                decoded_instruction = ["SWAP", operand_r8]
                registers.flag_carry = 0
                registers.flag_half_carry = 0
                registers.flag_subtraction = 0
                temp = (registers[operand_r8] & 15) << 4
                temp += registers[operand_r8] >> 4
                registers[operand_r8] = temp
                if registers[operand_r8] == 0:
                    registers.flag_zero = 1
                else:
                    registers.flag_zero = 0
            # SRL r8
            elif 0x38 <= instruction[1] <= 0x3f:
                decoded_instruction = ["SRL", operand_r8]
                registers.flag_half_carry = 0
                registers.flag_subtraction = 0
                registers.flag_carry = registers[operand_r8] & 1
                registers[operand_r8] = (registers[operand_r8] >> 1)
                if registers[operand_r8] == 0:
                    registers.flag_zero = 1
                else:
                    registers.flag_zero = 0
            # BIT b3, r8
            elif 0x40 <= instruction[1] <= 0x7f:
                decoded_instruction = ["BIT", b3, operand_r8]
                registers.flag_half_carry = 1
                registers.flag_subtraction = 0
                iszero = (registers[operand_r8] >> b3) & 1
                if iszero == 0:
                    registers.flag_zero = 1
                else:
                    registers.flag_zero = 0
            # RES, b3, r8
            elif 0x80 <= instruction[1] <= 0xcf:
                decoded_instruction = ["RES", b3, operand_r8]
                registers[operand_r8] &= (255 - (2**b3))
            # SET b3, r8
            elif 0xd0 <= instruction[1] <= 0xff:
                decoded_instruction = ["SET", b3, operand_r8]
                registers[operand_r8] |= (1 << b3)
        # ADD sp, imm8
        elif opcode == 0xe8:
            decoded_instruction = ["ADD", "SP", hex(imm8)]
            registers.pc += 2
            if imm8 > 127:
                imm8 -= 256
            registers.flag_carry = is_carry(registers["sp"], imm8, 8)
            registers.flag_half_carry = is_carry(registers["sp"], imm8, 4)
            registers.flag_zero = 0
            registers.flag_subtraction = 0
            registers["sp"] += imm8
            registers["sp"] &= 65535
        # LD hl, sp + imm8
        elif opcode == 0xf8:
            decoded_instruction = ["LD", "hl", ("sp + " + str(imm8))]
            registers.pc += 2
            if imm8 > 127:
                imm8 -= 256
            registers.flag_carry = is_carry(registers["sp"], imm8, 8)
            registers.flag_half_carry = is_carry(registers["sp"], imm8, 4)
            registers.flag_zero = 0
            registers.flag_subtraction = 0
            registers["hl"] = registers["sp"] + imm8
            registers["hl"] &= 65535
        # LD sp, hl
        elif opcode == 0xf9:
            decoded_instruction = ["LD", "sp", "hl"]
            registers.pc += 1
            registers["sp"] = registers["hl"]
        # DI
        elif opcode == 0xf3:
            decoded_instruction = ["DI"]
            registers.pc += 1
            registers.ime = 0
        # EI
        elif opcode == 0xfb:
            decoded_instruction = ["EI"]
            registers.pc += 1
            registers.ime_to_be_setted = 1
        # LDH [imm8], a
        elif opcode == 0xe0:
            decoded_instruction = ["LDH", ("[" + str(imm8) + "]"), "a"]
            registers.pc += 2
            memory[0xff00 + imm8] = registers["a"]
        # LDH a, [imm8]
        elif opcode == 0xf0:
            decoded_instruction = ["LDH", "a", ("[" + str(imm8) + "]")]
            registers.pc += 2
            registers["a"] = memory[0xff00 + imm8]
        # LDH [c], a
        elif opcode == 0xe2:
            decoded_instruction = ["LDH", "a", "[c]"]
            registers.pc += 1
            memory[0xff00 + registers["c"]] = registers["a"]
        # LDH a, [c]
        elif opcode == 0xf2:
            decoded_instruction = ["LDH", "[c]", "a"]
            registers.pc += 1
            registers["a"] = memory[0xff00 + registers["c"]]
        # LD [imm16], a
        elif opcode == 0xea:
            decoded_instruction = ["LD", ("[" + str(imm16) + "]"), "a"]
            registers.pc += 3
            memory[imm16] = registers["a"]
        # LD a, [imm16]
        elif opcode == 0xfa:
            decoded_instruction = ["LD", "a", ("[" + str(imm16) + "]")]
            registers.pc += 3
            registers["a"] = memory[imm16]
        else:
            decoded_instruction = ["NOT AN INSTRUCTION"]


        if opcode not in [0xfb, 0xd9]:
            if registers.ime_to_be_setted == 1:
                registers.ime_to_be_setted = 0
                registers.ime = 1

    return decoded_instruction


registers = Registers()
r8 = ["b", "c", "d", "e", "h", "l", "[hl]", "a"]
r16 = ["bc", "de", "hl", "sp"]
r16stk = ["bc", "de", "hl", "af"]
r16mem = ["bc", "de", "hl+", "hl-"]
cond = ["nz", "z", "nc", "c"]

size_mul = 3
memory = Memory()

if __name__ == "__main__":
    pygame.init()
    #pygamedisplay = pygame.display.set_mode((256 * size_mul, 256 * size_mul))
    pygamedisplay = pygame.display.set_mode((160 * size_mul, 144 * size_mul))
    pygame.display.set_caption("SillyGB")

    rom = "testsPrivate/05-op rp.gb"
    rom = "testsPrivate/10-bit ops.gb"
    rom = "testsPrivate/08-misc instrs.gb"
    rom = "testsPrivate/11-op a,(hl).gb"
    rom = "testsPrivate/bgbtest.gb"
    rom = "tests/hello-world.gb"
    rom = "testsPrivate/03-op sp,hl.gb"
    rom = "testsPrivate/09-op r,r.gb"
    rom = "testsPrivate/07-jr,jp,call,ret,rst.gb"
    rom = "testsPrivate/02-interrupts.gb"
    rom = "testsPrivate/Tetris.gb"
    rom = "testsPrivate/04-op r,imm.gb"
    rom = "testsPrivate/06-ld r,r.gb"
    rom = "testsPrivate/01-special.gb"
    load_rom(rom)

    display = []
    for i in range(256):
        row = [0 for _ in range(256)]
        display.append(row)

    breakpoint = 0xc884
    found = False

    # Execution
    tick = 1
    done = False
    #for i in range(59999):
    while not done:

        if registers.pc == breakpoint:
            found = True

        execute(fetch())
        if found:
            print(registers)

        #input("\n-->")

        #vblank
        memory[0xff44] += 1
        memory[0xff44] &= 255

        eventlist = pygame.event.get()
        for ev in eventlist:
            if ev.type == pygame.QUIT:
                done = True

        if tick % 60000 == 0:
            memory[0xff0f] &= 0b11111110
            tiles = ppu.get_tiles(memory)
            display = ppu.load_background(display, memory, tiles)
            visualizeGrid(display)
            pygame.display.flip()
        tick += 1

    pygame.quit()