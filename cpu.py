import debugcpu
import prettyhex

class Registers:
    r = {
        "a": 0x01,
        "b": 0,
        "c": 0x13,
        "d": 0,
        "e": 0xd8,
        "h": 0x01,
        "l": 0x4d,
        "sp": 0xfffe
    }
    pc = 0x0100

    flagZ = 1
    flagN = 0
    flagH = 1
    flagC = 1

    ime_to_be_setted = 0
    ime = 0

    def __getitem__(self, key):
        if key == "f":
            return (self.flagZ << 7) + (self.flagN << 6) + (self.flagH << 5) + (self.flagC << 4)
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
            self["f"] = value & 255
        elif key == "bc":
            self.r["b"] = value >> 8
            self.r["c"] = value & 255
        elif key == "de":
            self.r["d"] = value >> 8
            self.r["e"] = value & 255
        elif key == "hl":
            self.r["h"] = value >> 8
            self.r["l"] = value & 255
        elif key == "[hl]":
            memory[self["hl"]] = value
        elif key == "f":
            self.flagZ = value >> 7
            self.flagN = (value >> 6) & 1
            self.flagH = (value >> 5) & 1
            self.flagC = (value >> 4) & 1
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
        return [self["af"], self["bc"], self["de"], self["hl"], self["sp"], self.pc]

class Memory:
    mem = [0 for _ in range(2**16)]

    def __init__(self):
        for i in range(0xfea0, 0xff00):
            self.mem[i] = 255

    def __getitem__(self, key):
        return self.mem[key]

    def __setitem__(self, key, value):
        if (0x0000 <= key <= 0x7fff) or (0xfea0 <= key <= 0xfeff):
            pass
        elif 0xe000 <= key <= 0xfdff:
            self.mem[key] = value
            self.mem[key - 0x2000] = value
        elif 0xc000 <= key <= 0xddff:
            self.mem[key] = value
            self.mem[key + 0x2000] = value
        else:
            self.mem[key] = value

class Tick:
    t_states = 0
    scan_line_tick = 188
    tima_counter = 0
    divider_register = 0

    def add_tick(self, n):
        self.t_states += n

        self.scan_line_tick += n
        if self.scan_line_tick >= 456:
            self.scan_line_tick -= 456
            memory[0xff44] += 1
            if memory[0xff44] == 144:
                memory[0xff0f] |= 1
            if memory[0xff44] >= 153:
                self.scan_line_tick -= 456
                memory[0xff44] = 0

        if memory[0xff07] & 1 == 1:
            self.tima_counter += n
            if self.tima_counter > clock_select[memory[0xff07] & 3]:
                self.tima_counter = 0
                memory[0xff05] += 1
                if memory[0xff05] == 256:
                    memory[0xff05] = memory[0xff06]
                    memory[0xff0f] |= 4

        self.divider_register += n
        if self.divider_register >= 16384:
            self.divider_register -= 16384
            memory[0xff04] += 1
            memory[0xff04] &= 255

registers = Registers()

# Set this variable to True for running the tests
debug = False
if debug:
    memory = debugcpu.Memory()
else:
    memory = Memory()

clock = Tick()

r8 = ["b", "c", "d", "e", "h", "l", "[hl]", "a"]
r16 = ["bc", "de", "hl", "sp"]
r16stk = ["bc", "de", "hl", "af"]
r16mem = ["bc", "de", "hl+", "hl-"]
cond = ["nz", "z", "nc", "c"]
rst_vec = [0x00, 0x08, 0x10, 0x18, 0x20, 0x28, 0x30, 0x38]

clock_select = [1024, 16, 64, 256]

opcode = 0
imm8 = 0
imm16 = 0
condition = ""
dest_source_r16mem = ""
operand_r8 = ""
operand_r16 = ""
operand_stk_r8 = ""
operand_stk_r16 = ""
b3 = 0
tgt3 = 0


def is_carry(val1, val2, bits, subtraction):
    carry_size = (2 ** bits) - 1
    if subtraction:
        if ((val1 & carry_size) - (val2 & carry_size)) < 0:
            return 1
        return 0
    else:
        return ((val1 & carry_size) + (val2 & carry_size)) >> (bits)


def execute():
    if registers.ime == 1:
        run_interrupt()
    ticks = execute_instruction()
    post_execution(ticks)

def nop():
    registers.pc += 1
    return 4
def ld_r16_imm16():
    registers.pc += 3
    registers[operand_r16] = imm16
    return 12

def ld_r16mem_a():
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
    return 8


def ld_a_r16mem():
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
    return 8

def ld_imm16_sp():
    registers.pc += 3
    memory[imm16] = registers["sp"] & 255
    memory[imm16 + 1] = registers["sp"] >> 8
    return 20

def inc_r16():
    registers.pc += 1
    registers[operand_r16] += 1
    registers[operand_r16] &= 65535
    return 8

def dec_r16():
    registers.pc += 1
    registers[operand_r16] -= 1
    registers[operand_r16] &= 65535
    return 8

def add_hl_r16():
    registers.pc += 1
    registers.flagN = 0
    registers.flagH = is_carry(registers["hl"], registers[operand_r16], 12, 0)
    registers.flagC = is_carry(registers["hl"], registers[operand_r16], 16, 0)
    registers["hl"] += registers[operand_r16]
    registers["hl"] &= 65535
    return 8

def inc_r8():
    registers.pc += 1
    registers.flagH = is_carry(registers[operand_stk_r8], 1, 4, 0)
    registers[operand_stk_r8] += 1
    registers[operand_stk_r8] &= 255
    registers.flagN = 0
    registers.flagZ = 0 if registers[operand_stk_r8] != 0 else 1
    return 4 if operand_stk_r8 != "[hl]" else 12

def dec_r8():
    registers.pc += 1
    registers.flagH = is_carry(registers[operand_stk_r8], 1, 4, 1)
    registers[operand_stk_r8] -= 1
    registers[operand_stk_r8] &= 255
    registers.flagN = 1
    registers.flagZ = 0 if registers[operand_stk_r8] != 0 else 1
    return 4 if operand_stk_r8 != "[hl]" else 12

def ld_r8_imm8():
    registers.pc += 2
    registers[operand_stk_r8] = imm8
    return 8 if registers[operand_stk_r8] != "[hl]" else 12

def rlca():
    registers.pc += 1
    registers.flagC = (registers["a"] & 128) >> 7
    registers["a"] = (registers["a"] << 1) | registers.flagC
    registers["a"] &= 255
    registers.flagN = 0
    registers.flagH = 0
    registers.flagZ = 0
    return 4

def rrca():
    registers.pc += 1
    registers.flagC = registers["a"] & 1
    registers["a"] = (registers["a"] >> 1) | (registers.flagC << 7)
    registers.flagN = 0
    registers.flagH = 0
    registers.flagZ = 0
    return 4

def rla():
    registers.pc += 1
    registers["a"] = (registers["a"] << 1) | registers.flagC
    registers.flagC = (registers["a"] >> 8)
    registers["a"] &= 255
    registers.flagN = 0
    registers.flagH = 0
    registers.flagZ = 0
    return 4

def rra():
    registers.pc += 1
    prevC = registers.flagC
    registers.flagC = registers["a"] & 1
    registers["a"] = registers["a"] >> 1
    registers["a"] |= (prevC << 7)
    registers.flagN = 0
    registers.flagH = 0
    registers.flagZ = 0
    return 4

def daa():
    registers.pc += 1

    temp = registers["a"]
    corr = 0
    corr |= 0x06 if (registers.flagH != 0) else 0x00
    corr |= 0x60 if (registers.flagC != 0) else 0x00

    if registers.flagN == 1:
        temp -= corr
    else:
        corr |= 0x06 if (temp & 0x0f) > 0x09 else 0x00
        corr |= 0x60 if temp > 0x99 else 0x00
        temp += corr

    if (corr & 0x60) != 0:
        registers.flagC = 1

    registers.flagH = 0

    temp &= 255

    registers["a"] = temp
    registers.flagZ = 0 if registers["a"] != 0 else 1
    return 4
def cpl():
    registers.pc += 1
    registers["a"] = (~registers["a"]) & 255
    registers.flagN = 1
    registers.flagH = 1
    return 4
def scf():
    registers.pc += 1
    registers.flagN = 0
    registers.flagH = 0
    registers.flagC = 1
    return 4

def ccf():
    registers.pc += 1
    registers.flagN = 0
    registers.flagH = 0
    registers.flagC = 0 if registers.flagC == 1 else 1
    return 4
def jr():
    global imm8
    registers.pc += 2
    if imm8 >= 128:
        imm8 -= 256
    registers.pc += imm8
    return 12
def jr_cond():
    global imm8
    registers.pc += 2
    if imm8 >= 128:
        imm8 -= 256
    flag = False
    if registers.flagC == 1 and condition == "c":
        flag = True
    elif registers.flagC == 0 and condition == "nc":
        flag = True
    elif registers.flagZ == 1 and condition == "z":
        flag = True
    elif registers.flagZ == 0 and condition == "nz":
        flag = True
    if flag:
        registers.pc += imm8
        return 12
    else:
        return 8

def stop(): # TODO
    registers.pc += 2
    return 4
def halt():  # TODO
    registers.pc += 1
    return 4
def ld_r8_r8():
    registers.pc += 1
    registers[operand_stk_r8] = registers[operand_r8]
    return 4 if operand_r8 != "[hl]" and operand_stk_r8 != "[hl]" else 8
def add_a_r8():
    registers.pc += 1
    registers.flagH = is_carry(registers["a"], registers[operand_r8], 4, 0)
    registers.flagC = is_carry(registers["a"], registers[operand_r8], 8, 0)
    registers["a"] += registers[operand_r8]
    registers["a"] &= 255
    registers.flagN = 0
    registers.flagZ = 0 if registers["a"] != 0 else 1
    return 4 if operand_r8 != "[hl]" else 8
def adc_a_r8():
    registers.pc += 1
    prevC = registers.flagC
    registers.flagH = int((((registers["a"] & 15) + (registers[operand_r8] & 15) + registers.flagC) > 15))
    registers.flagC = int((registers["a"] + registers[operand_r8] + prevC) > 255)
    registers["a"] += registers[operand_r8] + prevC
    registers["a"] &= 255
    registers.flagN = 0
    registers.flagZ = 0 if registers["a"] != 0 else 1
    return 4 if operand_r8 != "[hl]" else 8
def sub_a_r8():
    registers.pc += 1
    registers.flagH = is_carry(registers["a"], registers[operand_r8], 4, 1)
    registers.flagC = is_carry(registers["a"], registers[operand_r8], 8, 1)
    registers["a"] -= registers[operand_r8]
    registers["a"] &= 255
    registers.flagN = 1
    registers.flagZ = 0 if registers["a"] != 0 else 1
    return 4 if operand_r8 != "[hl]" else 8
def sbc_a_r8():
    registers.pc += 1
    prevC = registers.flagC
    registers.flagH = int((((registers["a"] & 15) - (registers[operand_r8] & 15) - registers.flagC) < 0))
    registers.flagC = int((registers["a"] - registers[operand_r8] - prevC) < 0)
    registers["a"] -= (registers[operand_r8] + prevC)
    registers["a"] &= 255
    registers.flagN = 1
    registers.flagZ = 0 if registers["a"] != 0 else 1
    return 4 if operand_r8 != "[hl]" else 8
def and_a_r8():
    registers.pc += 1
    registers["a"] &= registers[operand_r8]
    registers["a"] & 255
    registers.flagZ = 0 if registers["a"] != 0 else 1
    registers.flagN = 0
    registers.flagH = 1
    registers.flagC = 0
    return 4 if operand_r8 != "[hl]" else 8
def xor_a_r8():
    registers.pc += 1
    registers["a"] ^= registers[operand_r8]
    registers["a"] & 255
    registers.flagZ = 0 if registers["a"] != 0 else 1
    registers.flagN = 0
    registers.flagH = 0
    registers.flagC = 0
    return 4 if operand_r8 != "[hl]" else 8
def or_a_r8():
    registers.pc += 1
    registers["a"] |= registers[operand_r8]
    registers["a"] & 255
    registers.flagZ = 0 if registers["a"] != 0 else 1
    registers.flagN = 0
    registers.flagH = 0
    registers.flagC = 0
    return 4 if operand_r8 != "[hl]" else 8
def cp_a_r8():
    registers.pc += 1
    temp = registers["a"] - registers[operand_r8]
    temp &= 255
    registers.flagZ = 0 if temp != 0 else 1
    registers.flagN = 1
    registers.flagH = is_carry(registers["a"], registers[operand_r8], 4, 1)
    registers.flagC = is_carry(registers["a"], registers[operand_r8], 8, 1)
    return 4 if operand_r8 != "[hl]" else 8
def add_a_imm8():
    registers.pc += 2
    registers.flagH = is_carry(registers["a"], imm8, 4, 0)
    registers.flagC = is_carry(registers["a"], imm8, 8, 0)
    registers["a"] += imm8
    registers["a"] &= 255
    registers.flagN = 0
    registers.flagZ = 0 if registers["a"] != 0 else 1
    return 8
def adc_a_imm8():
    registers.pc += 2
    prevC = registers.flagC
    registers.flagH = int((((registers["a"] & 15) + (imm8 & 15) + registers.flagC) > 15))
    registers.flagC = int((registers["a"] + imm8 + prevC) > 255)
    registers["a"] += (imm8 + prevC)
    registers["a"] &= 255
    registers.flagN = 0
    registers.flagZ = 0 if registers["a"] != 0 else 1
    return 8
def sub_a_imm8():
    registers.pc += 2
    registers.flagH = is_carry(registers["a"], imm8, 4, 1)
    registers.flagC = is_carry(registers["a"], imm8, 8, 1)
    registers["a"] -= imm8
    registers["a"] &= 255
    registers.flagN = 1
    registers.flagZ = 0 if registers["a"] != 0 else 1
    return 8
def sbc_a_imm8():
    registers.pc += 2
    prevC = registers.flagC
    registers.flagH = int((((registers["a"] & 15) - (imm8 & 15) - registers.flagC) < 0))
    registers.flagC = int((registers["a"] - imm8 - prevC) < 0)
    registers["a"] -= imm8 + prevC
    registers["a"] &= 255
    registers.flagN = 1
    registers.flagZ = 0 if registers["a"] != 0 else 1
    return 8
def and_a_imm8():
    registers.pc += 2
    registers["a"] &= imm8
    registers["a"] & 255
    registers.flagZ = 0 if registers["a"] != 0 else 1
    registers.flagN = 0
    registers.flagH = 1
    registers.flagC = 0
    return 8
def xor_a_imm8():
    registers.pc += 2
    registers["a"] ^= imm8
    registers["a"] & 255
    registers.flagZ = 0 if registers["a"] != 0 else 1
    registers.flagN = 0
    registers.flagH = 0
    registers.flagC = 0
    return 8
def or_a_imm8():
    registers.pc += 2
    registers["a"] |= imm8
    registers["a"] & 255
    registers.flagZ = 0 if registers["a"] != 0 else 1
    registers.flagN = 0
    registers.flagH = 0
    registers.flagC = 0
    return 8
def cp_a_imm8():
    registers.pc += 2
    temp = registers["a"] - imm8
    temp &= 255
    registers.flagZ = 0 if temp != 0 else 1
    registers.flagN = 1
    registers.flagH = is_carry(registers["a"], imm8, 4, 1)
    registers.flagC = is_carry(registers["a"], imm8, 8, 1)
    return 8
def ret_cond():
    registers.pc += 1
    flag = False
    if registers.flagC == 1 and condition == "c":
        flag = True
    elif registers.flagC == 0 and condition == "nc":
        flag = True
    elif registers.flagZ == 1 and condition == "z":
        flag = True
    elif registers.flagZ == 0 and condition == "nz":
        flag = True
    if flag:
        registers.pc = memory[registers["sp"]] & 255
        registers["sp"] += 1
        registers["sp"] &= 65535
        registers.pc += memory[registers["sp"]] << 8
        registers["sp"] += 1
        registers["sp"] &= 65535
        return 20
    else:
        return 16
def ret():
    registers.pc = memory[registers["sp"]] & 255
    registers["sp"] += 1
    registers["sp"] &= 65535
    registers.pc += memory[registers["sp"]] << 8
    registers["sp"] += 1
    registers["sp"] &= 65535
    return 16
def reti():
    registers.pc = memory[registers["sp"]] & 255
    registers["sp"] += 1
    registers["sp"] &= 65535
    registers.pc += memory[registers["sp"]] << 8
    registers["sp"] += 1
    registers["sp"] &= 65535
    registers.ime = 1
    return 16
def jp_cond():
    registers.pc += 3
    flag = False
    if registers.flagC == 1 and condition == "c":
        flag = True
    elif registers.flagC == 0 and condition == "nc":
        flag = True
    elif registers.flagZ == 1 and condition == "z":
        flag = True
    elif registers.flagZ == 0 and condition == "nz":
        flag = True
    if flag:
        registers.pc = imm16
        return 16
    else:
        return 12
def jp():
    registers.pc = imm16
    return 16
def jp_hl():
    registers.pc = registers["hl"]
    return 4
def call_cond():
    registers.pc += 3
    flag = False
    if registers.flagC == 1 and condition == "c":
        flag = True
    elif registers.flagC == 0 and condition == "nc":
        flag = True
    elif registers.flagZ == 1 and condition == "z":
        flag = True
    elif registers.flagZ == 0 and condition == "nz":
        flag = True
    if flag:
        registers["sp"] -= 1
        registers["sp"] &= 65535
        memory[registers["sp"]] = registers.pc >> 8
        registers["sp"] -= 1
        registers["sp"] &= 65535
        memory[registers["sp"]] = registers.pc & 255
        registers.pc = imm16
        return 24
    else:
        return 12
def call():
    registers.pc += 3
    registers["sp"] -= 1
    registers["sp"] &= 65535
    memory[registers["sp"]] = registers.pc >> 8
    registers["sp"] -= 1
    registers["sp"] &= 65535
    memory[registers["sp"]] = registers.pc & 255
    registers.pc = imm16
    return 24
def rst():
    registers.pc += 1
    registers["sp"] -= 1
    registers["sp"] &= 65535
    memory[registers["sp"]] = registers.pc >> 8
    registers["sp"] -= 1
    registers["sp"] &= 65535
    memory[registers["sp"]] = registers.pc & 255
    registers.pc = tgt3
    return 16
def pop():
    registers.pc += 1
    registers[operand_stk_r16] = memory[registers["sp"]] & 255
    registers["sp"] += 1
    registers["sp"] &= 65535
    registers[operand_stk_r16] += memory[registers["sp"]] << 8
    registers["sp"] += 1
    registers["sp"] &= 65535
    return 12
def push():
    registers.pc += 1
    registers["sp"] -= 1
    registers["sp"] &= 65535
    memory[registers["sp"]] = registers[operand_stk_r16] >> 8
    registers["sp"] -= 1
    registers["sp"] &= 65535
    memory[registers["sp"]] = registers[operand_stk_r16] & 255
    return 16
def prefix():
    global b3
    b3 = (imm8 & 0b00111000) >> 3
    return jump_table_cb[imm8]()
def add_sp_imm8():
    global imm8
    registers.pc += 2
    if imm8 > 127:
        imm8 -= 256

    registers.flagZ = 0
    registers.flagN = 0
    registers.flagH = is_carry(registers["sp"], imm8, 4, 0)
    registers.flagC = is_carry(registers["sp"], imm8, 8, 0)

    registers["sp"] += imm8
    registers["sp"] &= 65535
    return 16
def add_hl_sp_imm8():
    global imm8
    registers.pc += 2
    if imm8 > 127:
        imm8 -= 256

    registers.flagZ = 0
    registers.flagN = 0
    registers.flagH = is_carry(registers["sp"], imm8, 4, 0)
    registers.flagC = is_carry(registers["sp"], imm8, 8, 0)

    registers["hl"] = registers["sp"] + imm8
    registers["hl"] &= 65535
    return 12
def ld_sp_hl():
    registers.pc += 1
    registers["sp"] = registers["hl"]
    return 8
def di():
    registers.pc += 1
    registers.ime = 0
    return 4
def ei():
    registers.pc += 1
    if registers.ime == 0:
        registers.ime_to_be_setted += 1
    return 4
def ldh_imm8_a():
    registers.pc += 2
    memory[0xff00 + imm8] = registers["a"]
    return 12
def ldh_a_imm8():
    registers.pc += 2
    registers["a"] = memory[0xff00 + imm8]
    return 12
def ldh_c_a():
    registers.pc += 1
    memory[0xff00 + registers["c"]] = registers["a"]
    return 8
def ldh_a_c():
    registers.pc += 1
    registers["a"] = memory[0xff00 + registers["c"]]
    return 8
def ld_imm16_a():
    registers.pc += 3
    memory[imm16] = registers["a"]
    return 16
def ld_a_imm16():
    registers.pc += 3
    registers["a"] = memory[imm16]
    return 16
def invalid():
    pass


def rlc_r8():
    registers.pc += 2
    registers.flagC = (registers[operand_r8] & 128) >> 7
    registers[operand_r8] = (registers[operand_r8] << 1) | registers.flagC
    registers[operand_r8] &= 255
    registers.flagN = 0
    registers.flagH = 0
    registers.flagZ = 0 if registers[operand_r8] != 0 else 1
    return 8 if operand_r8 != "[hl]" else 16
def rrc_r8():
    registers.pc += 2
    registers.flagC = registers[operand_r8] & 1
    registers[operand_r8] = (registers[operand_r8] >> 1) | (registers.flagC << 7)
    registers.flagN = 0
    registers.flagH = 0
    registers.flagZ = 0 if registers[operand_r8] != 0 else 1
    return 8 if operand_r8 != "[hl]" else 16
def rl_r8():
    registers.pc += 2
    registers[operand_r8] = (registers[operand_r8] << 1) | registers.flagC
    registers.flagC = (registers[operand_r8] >> 8)
    registers[operand_r8] &= 255
    registers.flagN = 0
    registers.flagH = 0
    registers.flagZ = 0 if registers[operand_r8] != 0 else 1
    return 8 if operand_r8 != "[hl]" else 16
def rr_r8():
    registers.pc += 2
    prevC = registers.flagC
    registers.flagC = registers[operand_r8] & 1
    registers[operand_r8] = registers[operand_r8] >> 1
    registers[operand_r8] += (prevC << 7)
    registers.flagN = 0
    registers.flagH = 0
    registers.flagZ = 0 if registers[operand_r8] != 0 else 1
    return 8 if operand_r8 != "[hl]" else 16
def sla_r8():
    registers.pc += 2
    registers[operand_r8] = (registers[operand_r8] << 1)
    registers.flagC = (registers[operand_r8] >> 8)
    registers[operand_r8] &= 255
    registers.flagN = 0
    registers.flagH = 0
    registers.flagZ = 0 if registers[operand_r8] != 0 else 1
    return 8 if operand_r8 != "[hl]" else 16
def sra_r8():
    registers.pc += 2
    registers.flagC = registers[operand_r8] & 1
    registers[operand_r8] = (registers[operand_r8] >> 1)
    registers[operand_r8] |= (registers[operand_r8] & 64) << 1
    registers.flagN = 0
    registers.flagH = 0
    registers.flagZ = 0 if registers[operand_r8] != 0 else 1
    return 8 if operand_r8 != "[hl]" else 16
def swap_r8():
    registers.pc += 2
    low = registers[operand_r8] & 15
    registers[operand_r8] = registers[operand_r8] >> 4
    registers[operand_r8] += low << 4
    registers.flagN = 0
    registers.flagH = 0
    registers.flagC = 0
    registers.flagZ = 0 if registers[operand_r8] != 0 else 1
    return 8 if operand_r8 != "[hl]" else 16
def srl_r8():
    registers.pc += 2
    registers.flagN = 0
    registers.flagH = 0
    registers.flagC = registers[operand_r8] & 1
    registers[operand_r8] = (registers[operand_r8] >> 1) & 127
    registers.flagZ = 0 if registers[operand_r8] != 0 else 1
    return 8 if operand_r8 != "[hl]" else 16
def bit():
    registers.pc += 2
    iszero = (registers[operand_r8] >> b3) & 1
    registers.flagZ = 1 if iszero == 0 else 0
    registers.flagN = 0
    registers.flagH = 1
    return 8 if operand_r8 != "[hl]" else 12
def res():
    registers.pc += 2
    registers[operand_r8] &= (255 - (2 ** b3))
    return 8 if operand_r8 != "[hl]" else 16
def set():
    registers.pc += 2
    registers[operand_r8] |= (1 << b3)
    return 8 if operand_r8 != "[hl]" else 16

def generate_table():
    jumpt = [invalid for _ in range(256)]

    for opcode in range(256):
        if opcode == 0x00:
            jumpt[opcode] = nop
        elif opcode in [0x01, 0x11, 0x21, 0x31]:
            jumpt[opcode] = ld_r16_imm16
        elif opcode in [0x02, 0x12, 0x22, 0x32]:
            jumpt[opcode] = ld_r16mem_a
        elif opcode in [0x0a, 0x1a, 0x2a, 0x3a]:
            jumpt[opcode] = ld_a_r16mem
        elif opcode == 0x08:
            jumpt[opcode] = ld_imm16_sp
        elif opcode in [0x03, 0x13, 0x23, 0x33]:
            jumpt[opcode] = inc_r16
        elif opcode in [0x0b, 0x1b, 0x2b, 0x3b]:
            jumpt[opcode] = dec_r16
        elif opcode in [0x09, 0x19, 0x29, 0x39]:
            jumpt[opcode] = add_hl_r16
        elif opcode in [0x04, 0x14, 0x24, 0x34, 0x0c, 0x1c, 0x2c, 0x3c]:
            jumpt[opcode] = inc_r8
        elif opcode in [0x05, 0x15, 0x25, 0x35, 0x0d, 0x1d, 0x2d, 0x3d]:
            jumpt[opcode] = dec_r8
        elif opcode in [0x06, 0x16, 0x26, 0x36, 0x0e, 0x1e, 0x2e, 0x3e]:
            jumpt[opcode] = ld_r8_imm8
        elif opcode == 0x07:
            jumpt[opcode] = rlca
        elif opcode == 0x0f:
            jumpt[opcode] = rrca
        elif opcode == 0x17:
            jumpt[opcode] = rla
        elif opcode == 0x1f:
            jumpt[opcode] = rra
        elif opcode == 0x27:
            jumpt[opcode] = daa
        elif opcode == 0x2f:
            jumpt[opcode] = cpl
        elif opcode == 0x37:
            jumpt[opcode] = scf
        elif opcode == 0x3f:
            jumpt[opcode] = ccf
        elif opcode == 0x18:
            jumpt[opcode] = jr
        elif opcode in [0x20, 0x30, 0x28, 0x38]:
            jumpt[opcode] = jr_cond
        elif opcode == 0x10:
            jumpt[opcode] = stop
        elif opcode == 0x76:
            jumpt[opcode] = halt
        elif 0x40 <= opcode <= 0x7f and opcode != 0x76:
            jumpt[opcode] = ld_r8_r8
        elif 0x80 <= opcode <= 0x87:
            jumpt[opcode] = add_a_r8
        elif 0x88 <= opcode <= 0x8f:
            jumpt[opcode] = adc_a_r8
        elif 0x90 <= opcode <= 0x97:
            jumpt[opcode] = sub_a_r8
        elif 0x98 <= opcode <= 0x9f:
            jumpt[opcode] = sbc_a_r8
        elif 0xa0 <= opcode <= 0xa7:
            jumpt[opcode] = and_a_r8
        elif 0xa8 <= opcode <= 0xaf:
            jumpt[opcode] = xor_a_r8
        elif 0xb0 <= opcode <= 0xb7:
            jumpt[opcode] = or_a_r8
        elif 0xb8 <= opcode <= 0Xbf:
            jumpt[opcode] = cp_a_r8
        elif opcode == 0xc6:
            jumpt[opcode] = add_a_imm8
        elif opcode == 0xce:
            jumpt[opcode] = adc_a_imm8
        elif opcode == 0xd6:
            jumpt[opcode] = sub_a_imm8
        elif opcode == 0xde:
            jumpt[opcode] = sbc_a_imm8
        elif opcode == 0xe6:
            jumpt[opcode] = and_a_imm8
        elif opcode == 0xee:
            jumpt[opcode] = xor_a_imm8
        elif opcode == 0xf6:
            jumpt[opcode] = or_a_imm8
        elif opcode == 0xfe:
            jumpt[opcode] = cp_a_imm8
        elif opcode in [0xc0, 0xd0, 0xc8, 0xd8]:
            jumpt[opcode] = ret_cond
        elif opcode == 0xc9:
            jumpt[opcode] = ret
        elif opcode == 0xd9:
            jumpt[opcode] = reti
        elif opcode in [0xc2, 0xd2, 0xca, 0xda]:
            jumpt[opcode] = jp_cond
        elif opcode == 0xc3:
            jumpt[opcode] = jp
        elif opcode == 0xe9:
            jumpt[opcode] = jp_hl
        elif opcode in [0xc4, 0xd4, 0xcc, 0xdc]:
            jumpt[opcode] = call_cond
        elif opcode == 0xcd:
            jumpt[opcode] = call
        elif opcode in [0xc7, 0xd7, 0xe7, 0xf7, 0xcf, 0xdf, 0xef, 0xff]:
            jumpt[opcode] = rst
        elif opcode in [0xc1, 0xd1, 0xe1, 0xf1]:
            jumpt[opcode] = pop
        elif opcode in [0xc5, 0xd5, 0xe5, 0xf5]:
            jumpt[opcode] = push
        elif opcode == 0xcb:
            jumpt[opcode] = prefix
        elif opcode == 0xe8:
            jumpt[opcode] = add_sp_imm8
        elif opcode == 0xf8:
            jumpt[opcode] = add_hl_sp_imm8
        elif opcode == 0xf9:
            jumpt[opcode] = ld_sp_hl
        elif opcode == 0xf3:
            jumpt[opcode] = di
        elif opcode == 0xfb:
            jumpt[opcode] = ei
        elif opcode == 0xe0:
            jumpt[opcode] = ldh_imm8_a
        elif opcode == 0xf0:
            jumpt[opcode] = ldh_a_imm8
        elif opcode == 0xe2:
            jumpt[opcode] = ldh_c_a
        elif opcode == 0xf2:
            jumpt[opcode] = ldh_a_c
        elif opcode == 0xea:
            jumpt[opcode] = ld_imm16_a
        elif opcode == 0xfa:
            jumpt[opcode] = ld_a_imm16
    return jumpt

def generate_table_cb():
    jumpt = [invalid for _ in range(256)]

    for opcode in range(256):
        if opcode <= 0x07:
            jumpt[opcode] = rlc_r8
        elif opcode <= 0x0f:
            jumpt[opcode] = rrc_r8
        elif opcode <= 0x17:
            jumpt[opcode] = rl_r8
        elif opcode <= 0x1f:
            jumpt[opcode] = rr_r8
        elif opcode <= 0x27:
            jumpt[opcode] = sla_r8
        elif opcode <= 0x2f:
            jumpt[opcode] = sra_r8
        elif opcode <= 0x37:
            jumpt[opcode] = swap_r8
        elif opcode <= 0x3f:
            jumpt[opcode] = srl_r8
        elif opcode <= 0x7f:
            jumpt[opcode] = bit
        elif opcode <= 0xbf:
            jumpt[opcode] = res
        elif opcode <= 0xff:
            jumpt[opcode] = set
    return jumpt



def execute_instruction():
    global imm8, imm16, condition, dest_source_r16mem, operand_r16, operand_r8, operand_stk_r16, operand_stk_r8, b3, tgt3
    opcode = memory[registers.pc]
    imm8 = memory[registers.pc+1]
    imm16 = memory[registers.pc+2]*256 + memory[registers.pc+1]

    condition = cond[(opcode & 0b00011000) >> 3]

    dest_source_r16mem = r16mem[(opcode & 0b00110000) >> 4]

    if opcode != 0xcb:
        operand_r8 = r8[opcode & 0b00000111]
    else:
        operand_r8 = r8[imm8 & 0b00000111]
    operand_r16 = r16[(opcode & 0b00110000) >> 4]
    operand_stk_r8 = r8[(opcode & 0b00111000) >> 3]
    operand_stk_r16 = r16stk[(opcode & 0b00110000) >> 4]


    tgt3 = rst_vec[(opcode & 0b00111000) >> 3]

    return jump_table[opcode]()


def run_interrupt():
    if (memory[0xffff] & memory[0xff0f]) != 0:
        # vblank interrupt
        if (memory[0xffff] & 1) == 1 and (memory[0xff0f] & 1) == 1:
            memory[0xff0f] &= 0b11111110
            registers.ime = 0
            vblank_interrupt()
            clock.add_tick(20)
        # LCD interrupt
        elif (memory[0xffff] & 0b10) == 2 and (memory[0xff0f] & 0b10) == 2:
            memory[0xff0f] &= 0b11111101
            registers.ime = 0
            lcd_interrupt()
            clock.add_tick(20)
        # Timer interrupt
        elif (memory[0xffff] & 0b100) == 4 and (memory[0xff0f] & 0b100) == 4:
            memory[0xff0f] &= 0b11111011
            registers.ime = 0
            timer_interrupt()
            clock.add_tick(20)
        # Serial interrupt
        elif (memory[0xffff] & 0b1000) == 8 and (memory[0xff0f] & 0b1000) == 8:
            memory[0xff0f] &= 0b11110111
            registers.ime = 0
            serial_interrupt()
            clock.add_tick(20)
        # Joypad interrupt
        elif (memory[0xffff] & 0b10000) == 16 and (memory[0xff0f] & 0b10000) == 16:
            memory[0xff0f] &= 0b11101111
            registers.ime = 0
            joypad_interrupt()
            clock.add_tick(20)

def vblank_interrupt():
    registers["sp"] -= 1
    registers["sp"] &= 65535
    memory[registers["sp"]] = registers.pc >> 8
    registers["sp"] -= 1
    registers["sp"] &= 65535
    memory[registers["sp"]] = registers.pc & 255
    registers.pc = 0x40

def lcd_interrupt():
    print("lcd interrupt")
    registers["sp"] -= 1
    registers["sp"] &= 65535
    memory[registers["sp"]] = registers.pc >> 8
    registers["sp"] -= 1
    registers["sp"] &= 65535
    memory[registers["sp"]] = registers.pc & 255
    registers.pc = 0x48

def timer_interrupt():
    print("timer interrupt")
    registers["sp"] -= 1
    registers["sp"] &= 65535
    memory[registers["sp"]] = registers.pc >> 8
    registers["sp"] -= 1
    registers["sp"] &= 65535
    memory[registers["sp"]] = registers.pc & 255
    registers.pc = 0x50

def serial_interrupt():
    print("serial interrupt")
    registers["sp"] -= 1
    registers["sp"] &= 65535
    memory[registers["sp"]] = registers.pc >> 8
    registers["sp"] -= 1
    registers["sp"] &= 65535
    memory[registers["sp"]] = registers.pc & 255
    registers.pc = 0x58

def joypad_interrupt():
    print("joypad interrupt")
    registers["sp"] -= 1
    registers["sp"] &= 65535
    memory[registers["sp"]] = registers.pc >> 8
    registers["sp"] -= 1
    registers["sp"] &= 65535
    memory[registers["sp"]] = registers.pc & 255
    registers.pc = 0x60

def post_execution(ticks : int):
    clock.add_tick(ticks)
    if registers.ime_to_be_setted == 1:
        registers.ime_to_be_setted = 2
    elif registers.ime_to_be_setted == 2:
        registers.ime_to_be_setted = 0
        registers.ime = 1


jump_table = generate_table()
jump_table_cb = generate_table_cb()
