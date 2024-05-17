import pygame
import main
import ppu
import prettyhex


def reset():
    main.memory.rom = [0 for _ in range(2**15)]
    main.memory.vram = [0 for _ in range(2**13)]
    main.memory.xram = [0 for _ in range(2**13)]
    main.memory.wram = [0 for _ in range(2**13)]
    main.memory.oam = [0 for _ in range(160)]
    main.memory.io_registers = [0 for _ in range(2**7)]
    main.memory.hram = [0 for _ in range((2**7)-1)]
    main.memory.interrupt = 0

    main.registers.r = {
        "a": 0x01,
        "b": 0,
        "c": 0x13,
        "d": 0,
        "e": 0xd8,
        "h": 0x01,
        "l": 0x4d,
        "sp": 0xfffe
    }
    main.registers.pc = 0x0100

    main.registers.flag_zero = 1
    main.registers.flag_subtraction = 0
    main.registers.flag_half_carry = 1
    main.registers.flag_carry = 1

    main.registers.ime = 0

def run_test(rom, test_name, test_num, instructions_num):
    main.load_rom(rom)

    print("\n\033[1mExecuting Test " + str(test_num) + " - " + test_name + "\033[0m")
    for i in range(instructions_num):
        main.execute(main.fetch())
        main.memory[0xff44] += 1
        main.memory[0xff44] &= 255
        main.memory[0xff0f] &= 0b11111110

def test_registers(expected_registers):
    if main.registers.debug_compare() == expected_registers:
        return "Registers: \033[92mOK\033[0m"
    else:
        error = "Registers: \033[91mError\033[0m"
        error += "\nExpected:      " + str(list(map(prettyhex.prettyhex, expected_registers)))
        error += "\nGot:           " + str(list(map(prettyhex.prettyhex, main.registers.debug_compare())))
        return error

def test_ram(address, expected_result):
    result = []
    for i in range(address, address + 16):
        result.append(main.memory[i])

    if result == expected_result:
        return "Memory: \033[92mOK\033[0m"
    else:
        error = "Memory: \033[91mError\033[0m"
        error += "\nExpected: " + str(expected_result)
        error += "\nGot:      " + str(result)
        return error

if __name__ == "__main__":
    # Test 1
    rom = "tests/hello-world.gb"
    run_test(rom, "Hello World", 1, 13000)

    expected_registers = [0xe480, 0x0000, 0x0833, 0x9a40, 0xfffe, 0x0190, 0]
    print(test_registers(expected_registers))

    expected_ram = [0xff, 0x01, 0xfc, 0x03, 0xfd, 0x03, 0xfc, 0x03, 0xf9, 0x07, 0xf0, 0x0f, 0xc1, 0x3f, 0x82, 0xff]
    print(test_ram(0x9400, expected_ram))

    reset()

    # Test 2
    rom = "tests/CounterTest.gb"
    run_test(rom, "Saving in different numbers in memory", 2, 100)

    expected_registers = [0x0080, 0x0a0a, 0x00d8, 0xc00a, 0xfffe, 0x0160, 0]
    print(test_registers(expected_registers))

    expected_ram = [0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
    print(test_ram(0xc000, expected_ram))

    reset()

    # Test 3
    rom = "tests/CallsTests.gb"
    run_test(rom, "Calls and returns", 3, 100)

    expected_registers = [0xaab0, 0xcafe, 0xfeed, 0xdead, 0xfffe, 0x0162, 0]
    print(test_registers(expected_registers))

    expected_ram = [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x55, 0x01, 0x00, 0x00]
    print(test_ram(0xfff0, expected_ram))

    reset()

    # Test 4
    rom = "tests/PopPushTest.gb"
    run_test(rom, "Pop and push", 4, 100)

    expected_registers = [0xaab0, 0xbbcc, 0xddee, 0x8899, 0xfffe, 0x016e, 0]
    print(test_registers(expected_registers))

    expected_ram = [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x99, 0x88, 0xee, 0xdd, 0xcc, 0xbb, 0xb0, 0xaa, 0x00, 0x00]
    print(test_ram(0xfff0, expected_ram))

    reset()

    # Test 5
    rom = "tests/LDhl.gb"
    run_test(rom, "Load in hl and accessing memory", 5, 100)

    expected_registers = [0x69b0, 0x0013, 0x00d8, 0xc000, 0xfffe, 0x0156, 0]
    print(test_registers(expected_registers))

    expected_ram = [0x69, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
    print(test_ram(0xc000, expected_ram))

    reset()

    # Test 6
    rom = "tests/LDPUSH.gb"
    run_test(rom, "LD SP, HL and push", 6, 100)

    expected_registers = [0x7f60, 0x0013, 0x00d8, 0xcfff, 0xcffb, 0x015e, 0]
    print(test_registers(expected_registers))

    expected_ram = [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x60, 0x46, 0x20, 0x50, 0x00]
    print(test_ram(0xcff0, expected_ram))

    reset()

    # Test 7
    rom = "tests/JRTest.gb"
    run_test(rom, "Relative jumps", 7, 100)

    expected_registers = [0x32b0, 0x3213, 0x32d8, 0x014d, 0xfffe, 0x015c, 0]
    print(test_registers(expected_registers))

    reset()

    # Test 8
    rom = "tests/AddCarryTest.gb"
    run_test(rom, "ADC carry", 8, 100)

    expected_registers = [0x0600, 0x0013, 0x00d8, 0x014d, 0xfffe, 0x0156, 0]
    print(test_registers(expected_registers))

    reset()

    # Test 9
    rom = "tests/POPAF.gb"
    run_test(rom, "POP AF", 9, 200)

    expected_registers = [0x00c0, 0x1200, 0x1200, 0x5757, 0xfffe, 0x016a, 0]
    print(test_registers(expected_registers))

    reset()
