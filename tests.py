import os
import cpu
import json
import prettyhex
import debugcpu


def set_reg_values(registers, a: int, b: int, c: int, d: int, e: int, f: int, h: int, l: int, pc: int, sp: int) -> None:
    registers['a'] = a
    registers['b'] = b
    registers['c'] = c
    registers['d'] = d
    registers['e'] = e
    registers['f'] = f
    registers['h'] = h
    registers['l'] = l
    registers.pc = pc
    registers['sp'] = sp


def set_ram_values(memory, ram_values : list) -> None:
    memory.reset()
    for values in ram_values:
        memory[values[0]] = values[1]


if __name__ == "__main__":
    expected_reg = debugcpu.Registers()
    expected_ram = debugcpu.Memory()

    tests_dir = 'GameboyCPUTests/v2/'
    tests_files = os.listdir(tests_dir)
    tests_files.remove("README.md")

    passed = 0
    for test_file in tests_files:
        json_file = tests_dir + test_file
        with open(json_file, 'r') as f:
            failed_reg = 0
            failed_ram = 0

            tests = json.load(f)
            for test in tests:
                name = [int(x, 16) for x in test["name"].split(" ")]

                ini = test["initial"]
                set_reg_values(cpu.registers, ini["a"], ini["b"], ini["c"], ini["d"], ini["e"], ini["f"], ini["h"], ini["l"], ini["pc"]-1, ini["sp"])
                set_ram_values(cpu.memory, ini["ram"])

                fin = test["final"]
                set_reg_values(expected_reg, fin["a"], fin["b"], fin["c"], fin["d"], fin["e"], fin["f"], fin["h"], fin["l"], fin["pc"]-1, fin["sp"])
                set_ram_values(expected_ram, fin["ram"])

                cpu.execute_instruction()

                if cpu.registers.debug_compare() != expected_reg.debug_compare():
                    failed_reg += 1

                if cpu.memory.rom != expected_ram.rom:
                    failed_ram += 1

            if failed_reg == 0 and failed_ram == 0:
                passed += 1
                print("opcode " + prettyhex.prettyhex2(name[0]) + ": \033[92mPASSED\033[0m")
            else:
                print("opcode " + prettyhex.prettyhex2(name[0]) + ": \033[91mFAILED\033[0m")

    print("Tests passed: " + str(passed) + "/" + str(len(tests_files)))
