import pygame

class Joypad():
    buttons = {
        "up": 0,
        "down": 0,
        "left": 0,
        "right": 0,
        "a": 0,
        "b": 0,
        "start": 0,
        "select": 0,
    }

    buttonskeys = {
        "up": pygame.K_w,
        "down": pygame.K_s,
        "left": pygame.K_a,
        "right": pygame.K_d,
        "a": pygame.K_l,
        "b": pygame.K_k,
        "start": pygame.K_RETURN,
        "select": pygame.K_BACKSPACE
    }

    def encode_buttons(self, joypad_register: int) -> int:
        buttons_enc = self.buttons["a"]
        buttons_enc |= (self.buttons["b"] << 1)
        buttons_enc |= (self.buttons["select"] << 2)
        buttons_enc |= (self.buttons["start"] << 3)

        dpad_enc = self.buttons["right"]
        dpad_enc |= (self.buttons["left"] << 1)
        dpad_enc |= (self.buttons["up"] << 2)
        dpad_enc |= (self.buttons["down"] << 3)

        # Buttons and D-pad are selected
        if joypad_register & 0b00110000 == 0:
            joypad_register &= 0xf0
            buttons_enc |= dpad_enc
            joypad_register |= ((~buttons_enc) & 15)
        # Buttons are selected
        elif joypad_register & 0b00110000 == 16:
            joypad_register &= 0xf0
            joypad_register |= ((~buttons_enc) & 15)
        # D-pad is selected
        elif joypad_register & 0b00110000 == 32:
            joypad_register &= 0xf0
            joypad_register |= ((~dpad_enc) & 15)
        # Nothing is selected
        elif joypad_register & 0b00110000 == 48:
            joypad_register &= 0xf0
            joypad_register |= 0xf

        return joypad_register


