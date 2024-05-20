import cpu


class Cartridge:
    def __init__(self, romfile):
        self.romfile = romfile

    def load_rom(self, memory: cpu.Memory):
        with open(self.romfile, 'rb') as f:
            for i in range(2**14):
                instruction = f.read(1)
                if instruction == b'':
                    break
                memory.rom_b0[i] = (int.from_bytes(instruction))
            for i in range(2**14):
                instruction = f.read(1)
                if instruction == b'':
                    break
                memory.rom_bn[i] = (int.from_bytes(instruction))

    def switch_bank(self, memory: cpu.Memory, bank: int):
        pass