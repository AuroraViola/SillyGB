import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame
import ppu
import cpu
import cartridge
import joypad


def createSquare(x, y, color):
    pygame.draw.rect(pygamedisplay, color, [x, y, size_mul, size_mul])
def visualizeGrid(display):
    y = 0
    for row in display:
        x = 0
        for item in row:
            if item == 0:
                createSquare(x, y, (185, 237, 186))
            elif item == 1:
                createSquare(x, y, (118, 196, 123))
            elif item == 2:
                createSquare(x, y, (49, 105, 64))
            else:
                createSquare(x, y, (10, 38, 16))

            x += size_mul
        y += size_mul

    pygame.display.update()


size_mul = 3

if __name__ == "__main__":
    # Initialize display
    pygame.init()
    pygamedisplay = pygame.display.set_mode((160 * size_mul, 144 * size_mul))
    pygame.display.set_caption("SillyGB")
    display = ppu.Display()
    cpu.memory[0xff44] = 0x90

    # Load cartridge to memory
    cartridge = cartridge.Cartridge("Roms/Private/SillyTest.gb")
    cartridge.load_rom(cpu.memory)

    # Initialize joypad
    p1 = joypad.Joypad()
    cpu.memory[0xff00] = 0xff

    tick = 1
    done = False
    while not done:
        eventlist = pygame.event.get()
        for ev in eventlist:
            if ev.type == pygame.QUIT:
                done = True
            if ev.type == pygame.KEYDOWN:
                cpu.memory[0xff0f] |= 16
                for button in p1.buttonskeys:
                    if ev.key == p1.buttonskeys[button]:
                        cpu.memory[0xff0f] |= 16
                        p1.buttons[button] = 1
            if ev.type == pygame.KEYUP:
                for button in p1.buttonskeys:
                    if ev.key == p1.buttonskeys[button]:
                        p1.buttons[button] = 0

        prev_btn = cpu.memory[0xff00]
        cpu.memory[0xff00] = p1.encode_buttons(cpu.memory[0xff00])

        cpu.execute()

        if tick % 18240 == 0:
            display.load_background(cpu.memory)
            visualizeGrid(display.background)
        tick += 1

    pygame.quit()