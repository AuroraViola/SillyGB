import pygame
import cpu
import cartridge
import ppu
import prettyhex


def reset():
    cpu.memory.rom = [0 for _ in range(2**15)]
    cpu.memory.vram = [0 for _ in range(2**13)]
    cpu.memory.xram = [0 for _ in range(2**13)]
    cpu.memory.wram = [0 for _ in range(2**13)]
    cpu.memory.oam = [0 for _ in range(160)]
    cpu.memory.io_registers = [0 for _ in range(2**7)]
    cpu.memory.hram = [0 for _ in range((2**7)-1)]
    cpu.memory.interrupt = 0

    cpu.registers.r = {
        "a": 0x01,
        "b": 0,
        "c": 0x13,
        "d": 0,
        "e": 0xd8,
        "h": 0x01,
        "l": 0x4d,
        "sp": 0xfffe
    }
    cpu.registers.pc = 0x0100

    cpu.registers.flagZ = 1
    cpu.registers.flagN = 0
    cpu.registers.flagH = 1
    cpu.registers.flagC = 1

    cpu.registers.ime = 0

def run_test(cartridge: cartridge.Cartridge, test_name, test_num, instructions_num):
    cartridge.load_rom(cpu.memory)

    print("\n\033[1mExecuting Test " + str(test_num) + " - " + test_name + "\033[0m")
    for i in range(instructions_num):
        cpu.execute()

def test_registers(expected_registers):
    if cpu.registers.debug_compare() == expected_registers:
        return "Registers: \033[92mOK\033[0m"
    else:
        error = "Registers: \033[91mError\033[0m"
        error += "\nExpected:      " + str(list(map(prettyhex.prettyhex, expected_registers)))
        error += "\nGot:           " + str(list(map(prettyhex.prettyhex, cpu.registers.debug_compare())))
        return error

def test_ram(address, expected_result):
    result = []
    for i in range(address, address + 16):
        result.append(cpu.memory[i])

    if result == expected_result:
        return "Memory: \033[92mOK\033[0m"
    else:
        error = "Memory: \033[91mError\033[0m"
        error += "\nExpected: " + str(expected_result)
        error += "\nGot:      " + str(result)
        return error

if __name__ == "__main__":
    # Test 1
    c = cartridge.Cartridge("tests/hello-world.gb")
    run_test(c, "Hello World", 1, 20000)

    expected_registers = [0xe480, 0x0000, 0x0833, 0x9a40, 0xfffe, 0x0190, 0]
    print(test_registers(expected_registers))

    expected_ram = [0xff, 0x01, 0xfc, 0x03, 0xfd, 0x03, 0xfc, 0x03, 0xf9, 0x07, 0xf0, 0x0f, 0xc1, 0x3f, 0x82, 0xff]
    print(test_ram(0x9400, expected_ram))

    reset()

    # Test 2
    c = cartridge.Cartridge("tests/CounterTest.gb")
    run_test(c, "Saving in different numbers in memory", 2, 100)

    expected_registers = [0x0080, 0x0a0a, 0x00d8, 0xc00a, 0xfffe, 0x0160, 0]
    print(test_registers(expected_registers))

    expected_ram = [0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
    print(test_ram(0xc000, expected_ram))

    reset()

    # Test 3
    c = cartridge.Cartridge("tests/CallsTests.gb")
    run_test(c, "Calls and returns", 3, 100)

    expected_registers = [0xaab0, 0xcafe, 0xfeed, 0xdead, 0xfffe, 0x0162, 0]
    print(test_registers(expected_registers))

    expected_ram = [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x55, 0x01, 0x00, 0x00]
    print(test_ram(0xfff0, expected_ram))

    reset()

    # Test 4
    c = cartridge.Cartridge("tests/PopPushTest.gb")
    run_test(c, "Pop and push", 4, 100)

    expected_registers = [0xaab0, 0xbbcc, 0xddee, 0x8899, 0xfffe, 0x016e, 0]
    print(test_registers(expected_registers))

    expected_ram = [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x99, 0x88, 0xee, 0xdd, 0xcc, 0xbb, 0xb0, 0xaa, 0x00, 0x00]
    print(test_ram(0xfff0, expected_ram))

    reset()

    # Test 5
    c = cartridge.Cartridge("tests/LDhl.gb")
    run_test(c, "Load in hl and accessing memory", 5, 100)

    expected_registers = [0x69b0, 0x0013, 0x00d8, 0xc000, 0xfffe, 0x0156, 0]
    print(test_registers(expected_registers))

    expected_ram = [0x69, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
    print(test_ram(0xc000, expected_ram))

    reset()

    # Test 6
    c = cartridge.Cartridge("tests/LDPUSH.gb")
    run_test(c, "LD SP, HL and push", 6, 100)

    expected_registers = [0x7f60, 0x0013, 0x00d8, 0xcfff, 0xcffb, 0x015e, 0]
    print(test_registers(expected_registers))

    expected_ram = [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x60, 0x46, 0x20, 0x50, 0x00]
    print(test_ram(0xcff0, expected_ram))

    reset()

    # Test 7
    c = cartridge.Cartridge("tests/JRTest.gb")
    run_test(c, "Relative jumps", 7, 100)

    expected_registers = [0x32b0, 0x3213, 0x32d8, 0x014d, 0xfffe, 0x015c, 0]
    print(test_registers(expected_registers))

    reset()

    # Test 8
    c = cartridge.Cartridge("tests/AddCarryTest.gb")
    run_test(c, "ADC carry", 8, 100)

    expected_registers = [0x0600, 0x0013, 0x00d8, 0x014d, 0xfffe, 0x0156, 0]
    print(test_registers(expected_registers))

    reset()

    # Test 9
    c = cartridge.Cartridge("tests/POPAF.gb")
    run_test(c, "POP AF", 9, 20)

    expected_registers = [0x00c0, 0x1200, 0x1200, 0x5757, 0xfffe, 0x016a, 0]
    print(test_registers(expected_registers))

    expected_ram = [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x12, 0x00, 0x00]
    print(test_ram(0xfff0, expected_ram))

    reset()
