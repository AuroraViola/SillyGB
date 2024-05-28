import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame
import ppu
import cpu
import cartridge
import joypad


scaling_fact = 4

if __name__ == "__main__":
    # Initialize display
    screen = ppu.Display(4)

    # Load cartridge to memory
    cartridge.game = cartridge.Cartridge("Roms/SillyTest.gb")
    print("Rom type", cartridge.game.romtype)
    print("Rom size", cartridge.game.romsize)
    print("Number of banks", cartridge.game.banks_num)
    cartridge.game.load_rom()

    # Initialize joypad
    p1 = joypad.Joypad()
    cpu.memory[0xff00] = 0xff

    tick = 1
    done = False
    while not done:
        cpu.memory[0xff00] = p1.encode_buttons(cpu.memory[0xff00])
        cpu.execute()

        if tick % 18240 == 0:
            screen.visualize_display()
            eventlist = pygame.event.get()
            for ev in eventlist:
                if ev.type == pygame.QUIT:
                    done = True
                if ev.type == pygame.KEYDOWN:
                    for button in p1.buttonskeys:
                        if ev.key == p1.buttonskeys[button]:
                            cpu.memory[0xff0f] |= 16
                            p1.buttons[button] = 1
                if ev.type == pygame.KEYUP:
                    for button in p1.buttonskeys:
                        if ev.key == p1.buttonskeys[button]:
                            p1.buttons[button] = 0

        tick += 1

    pygame.quit()