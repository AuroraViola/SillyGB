import prettyhex

class Registers:
    r = {
        "a": 0,
        "b": 0,
        "c": 0,
        "d": 0,
        "e": 0,
        "h": 0,
        "l": 0,
        "sp": 0
    }
    pc = 0x0

    flagZ = 0
    flagN = 0
    flagH = 0
    flagC = 0

    ime_to_be_setted = 0
    ime = 0

    def __getitem__(self, key) -> int:
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
        else:
            return self.r[key]

    def __setitem__(self, key, value) -> None:
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
        elif key == "f":
            self.flagZ = value >> 7
            self.flagN = (value >> 6) & 1
            self.flagH = (value >> 5) & 1
            self.flagC = (value >> 4) & 1
        else:
            self.r[key] = value

    def debug_compare(self) -> list:
        return [self["af"], self["bc"], self["de"], self["hl"], self["sp"], self.pc]

class Memory:
    rom = [0 for _ in range(2**16)]

    def __getitem__(self, key) -> int:
        if 0x0000 <= key <= 0xffff:
            return self.rom[key]

    def __setitem__(self, key, value) -> None:
        if 0x0000 <= key <= 0xffff:
            self.rom[key] = value

    def reset(self) -> None:
        self.rom = [0 for _ in range(2 ** 16)]
