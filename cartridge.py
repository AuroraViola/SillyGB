import cpu


class Cartridge:
    banks = []

    def __init__(self, romfile):
        self.romfile = romfile

    def load_rom(self, memory: cpu.Memory):
        with open(self.romfile, 'rb') as f:
            for i in range(2**15):
                instruction = f.read(1)
                memory.rom[i] = (int.from_bytes(instruction))

    def switch_bank(self, memory: cpu.Memory, n_bank: int):
        memory.bank = self.banks[n_bank]
