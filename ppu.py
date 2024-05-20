import cpu

class Display:
    background = [[0 for _ in range(256)] for _ in range(256)]
    window = [[0 for _ in range(256)] for _ in range(256)]

    def decode_tile(self, memory: cpu.Memory, addr: int):
        tile = []
        for i in range(addr, addr+16):
            tile.append(memory[i])
        tp = 0
        decoded_tile = []

        for j in range(8):
            row = [0 for _ in range(8)]
            for i in range(8):
                row[i] += (tile[tp] & 2**(8-i-1)) >> 8-i-1
            tp += 1
            for i in range(8):
                row[i] += ((tile[tp] & 2**(8-i-1)) >> 8-i-1) * 2
            tp += 1
            decoded_tile.append(row)

        return decoded_tile


    def get_tiles(self, memory: cpu.Memory):
        tiles = []
        if ((memory[0xff40] & 16) >> 4) == 1:
            i = 0x8000
            while i < 0x8800:
                tiles.append(self.decode_tile(memory, i))
                i += 0x0010
        else:
            i = 0x9000
            while i < 0x9800:
                tiles.append(self.decode_tile(memory, i))
                i += 0x0010
        i = 0x8800
        while i < 0x9000:
            tiles.append(self.decode_tile(memory, i))
            i += 0x0010

        return tiles

    def load_background(self, memory: cpu.Memory):
        self.reset_background()
        tiles = self.get_tiles(memory)
        bg_tiles = []
        if ((memory[0xff40] & 8) >> 3) == 0:
            for i in range(0x9800, 0x9c00):
                bg_tiles.append(tiles[memory[i]])
        else:
            for i in range(0x9c00, 0xa000):
                bg_tiles.append(tiles[memory[i]])

        ti = 0
        for y in range(32):
            for x in range(32):
                display_x = x * 8
                display_y = y * 8

                for y1 in range(8):
                    for x1 in range(8):
                        self.background[display_y + y1][display_x + x1] = bg_tiles[ti][y1][x1]
                ti += 1

    def reset_background(self):
        self.background = [[0 for _ in range(256)] for _ in range(256)]

    def reset_window(self):
        self.window = [[0 for _ in range(256)] for _ in range(256)]
