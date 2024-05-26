import pygame
import cpu

class Display:
    display = [[0 for _ in range(160)] for _ in range(144)]
    background = [[0 for _ in range(256)] for _ in range(256)]
    window = [[0 for _ in range(256)] for _ in range(256)]
    sprites = []
    palette = (
        (185, 237, 186),
        (118, 196, 123),
        (49, 105, 64),
        (10, 38, 16)
    )

    def __init__(self, scaling_fact, memory):
        pygame.init()
        self.scaling_fact = scaling_fact
        self.win = pygame.display.set_mode((160 * scaling_fact, 144 * scaling_fact))
        self.screen = pygame.Surface((160, 144))
        pygame.display.set_caption("SillyGB")
        memory[0xff44] = 0x90

    def visualize_display(self, memory):
        self.load_display(memory)

        y = 0
        for i in range(144):
            x = 0
            for j in range(160):
                pygame.draw.rect(self.screen, self.palette[self.display[i][j]], [x, y, 1, 1])
                x += 1
            y += 1

        self.win.blit(pygame.transform.scale(self.screen, self.win.get_rect().size), (0, 0))
        pygame.display.update()

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
        if (memory[0xff40] & 16) != 0:
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
            tiles = self.get_tiles(memory)
            bg_tiles = []
            if (memory[0xff40] & 8) == 0:
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

    def load_window(self, memory: cpu.Memory):
        tiles = self.get_tiles(memory)
        win_tiles = []
        if (memory[0xff40] & 64) == 0:
            for i in range(0x9800, 0x9c00):
                win_tiles.append(tiles[memory[i]])
        else:
            for i in range(0x9c00, 0xa000):
                win_tiles.append(tiles[memory[i]])

        ti = 0
        for y in range(32):
            for x in range(32):
                display_x = x * 8
                display_y = y * 8

                for y1 in range(8):
                    for x1 in range(8):
                        self.window[display_y + y1][display_x + x1] = win_tiles[ti][y1][x1]
                ti += 1

    def load_sprite(self, memory):
        self.sprite = []
        i = 0xfe00
        while i < 0xfea0:
            ypos = memory[i]
            xpos = memory[i + 1]
            t_index = memory[i + 2]
            attributes = memory[i + 3]

            priority = attributes >> 7
            yflip = (attributes >> 6) & 1
            xflip = (attributes >> 5) & 1
            self.sprites.append((ypos, xpos, t_index, priority, yflip, xflip))
            i += 4

    def reset_background(self):
        self.background = [[0 for _ in range(512)] for _ in range(512)]

    def reset_window(self):
        self.window = [[0 for _ in range(256)] for _ in range(256)]

    def load_display(self, memory: cpu.Memory()):
        self.reset_background()
        if memory[0xff40] & 1 != 0:
            self.load_background(memory)
