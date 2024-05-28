import pygame
import numpy
import cpu

class Display:
    display = numpy.zeros((144, 160), dtype=numpy.uint8, order='C')
    background = numpy.zeros((256, 256), dtype=numpy.uint8)
    window = numpy.zeros((256, 256), dtype=numpy.uint8)
    palette = numpy.array([[185, 237, 186], [118, 196, 123], [49, 105, 64], [10, 38, 16]])
    bg_palette = [0, 1, 2, 3]

    def __init__(self, scaling_fact, memory):
        pygame.init()
        self.scaling_fact = scaling_fact
        self.win = pygame.display.set_mode((160 * scaling_fact, 144 * scaling_fact))
        self.screen = pygame.Surface((160, 144))
        pygame.display.set_caption("SillyGB")
        memory[0xff44] = 0x90

    def visualize_display(self):
        self.load_display()
        self.screen = pygame.surfarray.make_surface(self.palette[numpy.transpose(self.display)])
        self.win.blit(pygame.transform.scale(self.screen, self.win.get_rect().size), (0, 0))
        pygame.display.update()

    def decode_tile(self, addr: int):
        tile = cpu.memory[addr:addr+16]
        decoded_tile = [[0 for _ in range(8)] for _ in range(8)]

        for y in range(8):
            byte1 = tile[y * 2]
            byte2 = tile[y * 2 + 1]

            for x in range(8):
                bit1 = (byte1 >> (7 - x)) & 1
                bit2 = (byte2 >> (7 - x)) & 1
                decoded_tile[y][x] = (bit2 << 1) | bit1

        return decoded_tile

    def get_tiles(self):
        tiles = []
        if (cpu.memory[0xff40] & 16) != 0:
            i = 0x8000
            while i < 0x8800:
                tiles.append(self.decode_tile(i))
                i += 0x0010
        else:
            i = 0x9000
            while i < 0x9800:
                tiles.append(self.decode_tile(i))
                i += 0x0010
        i = 0x8800
        while i < 0x9000:
            tiles.append(self.decode_tile(i))
            i += 0x0010

        return tiles

    def load_background(self):
        tiles = self.get_tiles()
        if (cpu.memory[0xff40] & 8) == 0:
            bg_tiles = cpu.memory[0x9800:0x9c00]
        else:
            bg_tiles = cpu.memory[0x9c00:0xa000]

        ti = 0
        for y in range(32):
            display_y = y << 3
            for x in range(32):
                display_x = x << 3
                tile = tiles[bg_tiles[y * 32 + x]]
                for y1 in range(8):
                    for x1 in range(8):
                        self.background[display_y + y1, display_x + x1] = self.bg_palette[tile[y1][x1]]
                ti += 1

    def load_window(self):
        tiles = self.get_tiles()
        if (cpu.memory[0xff40] & 64) == 0:
            wn_tiles = cpu.memory[0x9800:0x9c00]
        else:
            wn_tiles = cpu.memory[0x9c00:0xa000]

        ti = 0
        for y in range(32):
            display_y = y << 3
            for x in range(32):
                display_x = x << 3
                tile = tiles[wn_tiles[y * 32 + x]]
                for y1 in range(8):
                    for x1 in range(8):
                        self.window[display_y + y1, display_x + x1] = tile[y1][x1]
                ti += 1

    def load_sprites(self):
        oam = cpu.memory[0xfe00:0xfea0]
        return [oam[i:i + 4] for i in range(0, 160, 4)]

    def load_display(self):
        scy = cpu.memory[0xff42]
        scx = cpu.memory[0xff43]
        wy = cpu.memory[0xff4a]
        wx = cpu.memory[0xff4b]
        self.background.fill(0)
        if cpu.memory[0xff40] & 1 != 0:
            bg_pal = cpu.memory[0xff47]
            self.bg_palette = [(bg_pal & 3), ((bg_pal & 12) >> 2), ((bg_pal & 48) >> 4), (bg_pal >> 6)]
            self.load_background()

        # Load on display
        if cpu.memory[0xff40] & 128 != 0:
            for y in range(144):
                bgy = (y + scy) & 255
                for x in range(160):
                    self.display[y, x] = self.background[bgy, (x + scx) & 255]
            if cpu.memory[0xff40] & 2 != 0:
                for sprites in self.load_sprites():
                    sprite_tile = numpy.array(self.decode_tile(0x8000 | (sprites[2] << 4)))
                    # y flip
                    if (sprites[3] >> 6) & 1 != 0:
                        sprite_tile = numpy.flipud(sprite_tile)
                    # x flip
                    if (sprites[3] >> 5) & 1 != 0:
                        sprite_tile = numpy.fliplr(sprite_tile)

                    if 16 <= sprites[0] <= 159 and 8 <= sprites[1] <= 159:
                        for y in range(8):
                            for x in range(8):
                                if sprite_tile[y][x] != 0:
                                    self.display[sprites[0] + y - 16, sprites[1] + x - 8] = sprite_tile[y][x]


