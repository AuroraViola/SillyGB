import cpu

class Cartridge:
    romtype = 0
    romsize = 0
    is_switched_rom = False
    rom = []
    bank = 1
    banks_num = 0

    def __init__(self, romfile):
        self.romfile = romfile
        with open(self.romfile, 'rb') as f:
            f.seek(0x147, 1)
            self.romtype = int.from_bytes(f.read(1))
            self.banks_num = 2 * (1 << int.from_bytes(f.read(1)))
            self.romsize = (2**14) * self.banks_num

        with open(self.romfile, 'rb') as f:
            for i in range(self.romsize):
                bytes = f.read(1)
                self.rom.append(int.from_bytes(bytes))

    def load_rom(self):
        for i in range(0x8000):
            cpu.memory.mem[i] = self.rom[i]

    def load_rom_old(self):
        with open(self.romfile, 'rb') as f:
            for i in range(2**15):
                bytes = f.read(1)
                cpu.memory.mem[i] = (int.from_bytes(bytes))

    def switch_bank(self):
        self.is_switched_rom = False
        if self.bank == 0:
            self.bank = 1
        for i in range(0x4000):
            cpu.memory.mem[i + 0x4000] = self.rom[i + 0x4000 * self.bank]

game = None