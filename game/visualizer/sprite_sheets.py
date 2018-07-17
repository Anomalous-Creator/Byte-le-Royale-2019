import random, math

import pygame
import game.utils.ptext

from game.visualizer.spritesheet_functions import SpriteSheet
from game.common.enums import *


#class MonsterSprite(pygame.sprite.Sprite):
#    def __init__(self, sprite_sheet_path, frames, x, y, h, w, animation_speed):
#        super().__init__()
#
#        self.frames = frames
#        self.index = 0
#        self.tick_counter = 0
#        self.animation_speed = animation_speed
#
#        self.h = h
#        self.w = w
#
#        self.sprite_sheet = SpriteSheet(sprite_sheet_path)
#
#        self.image = self.sprite_sheet.get_image(
#                                                self.frames[self.index][0],
#                                                self.frames[self.index][1],
#                                                self.h,
#                                                self.w
#                                                )
#
#        self.image = pygame.transform.scale(self.image, (self.h*2, self.w*2))
#
#        self.rect = self.image.get_rect()
#        self.rect.x = x
#        self.rect.y = y
#
#    def update(self):
#        self.tick_counter += 1
#        if self.tick_counter % self.animation_speed is 0:
#            if self.index < len(self.frames)-1:
#                self.index += 1
#            else:
#                self.index = 0
#        self.image = self.sprite_sheet.get_image(
#                                                self.frames[self.index][0],
#                                                self.frames[self.index][1],
#                                                self.h,
#                                                self.w
#                                                )
#
#        self.image = pygame.transform.scale(self.image, (self.h*2, self.w*2))
#
#class BeholderSprite(MonsterSprite):
#    def __init__(self, x, y):
#        MonsterSprite.__init__(self, "game/visualizer/assets/beholder.png", [
#            [0, 0],
#            [136, 0],
#            [0, 136],
#            [136, 136]
#        ], x, y, 136, 136, 3)


# TODO Use this as a base to create colored ships
class MagicAttackAnimation(pygame.sprite.Sprite):
    def __init__(self, x, y, color):
        super().__init__()
        self.frames = [
            [  0,   0], [128,   0], [256,   0], [384,   0],
            [  0, 128], [128, 128], [256, 128], [384, 128],
            [  0, 256], [128, 256], [256, 256], [384, 256],
            [  0, 384]
        ]

        self.index = 0
        self.tick_counter = 0
        self.animation_speed = 1

        self.h = 128
        self.w = 128


        self.sprite_sheet = SpriteSheet("game/visualizer/assets/explosion_animation.png")

        self.image = self.sprite_sheet.get_image(
            self.frames[self.index][0],
            self.frames[self.index][1],
            self.h,
            self.w
        )

        self.color = pygame.Color(
            color.r,
            color.g,
            color.b,
            255
        )

        d = 60
        self.color_2 = pygame.Color(
            self.color.r if self.color.r-d < 0 else self.color.r-d,
            self.color.g if self.color.g-d < 0 else self.color.g-d,
            self.color.b if self.color.b-d < 0 else self.color.b-d,
            255
        )

        d = 100
        self.color_3 = pygame.Color(
            self.color.r if self.color.r-d < 0 else self.color.r-d,
            self.color.g if self.color.g-d < 0 else self.color.g-d,
            self.color.b if self.color.b-d < 0 else self.color.b-d,
            255
        )

        pa = pygame.PixelArray(self.image)
        pa.replace(pygame.Color("#ffffff"), self.color)
        pa.replace(pygame.Color("#a5a5a5"), self.color_2)
        pa.replace(pygame.Color("#3c3c3c"), self.color_3)
        del pa


        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

    def update(self, group):
        self.tick_counter += 1
        if self.tick_counter % self.animation_speed is 0:
            if self.index < len(self.frames)-1:
                self.index += 1
            else:
                del self.image
                group.remove(self)

        self.image = self.sprite_sheet.get_image(
            self.frames[self.index][0],
            self.frames[self.index][1],
            self.h,
            self.w
        )
        pa = pygame.PixelArray(self.image)
        pa.replace(pygame.Color("#ffffff"), self.color)
        pa.replace(pygame.Color("#a5a5a5"), self.color_2)
        pa.replace(pygame.Color("#3c3c3c"), self.color_3)
        del pa




#class SpecialAbilityAnimation(pygame.sprite.Sprite):
#    def __init__(self, sprite_sheet_path, frames, x, y, h, w, animation_speed, scale=1, repeat=1):
#        super().__init__()
#
#        self.frames = frames
#        self.index = 0
#        self.tick_counter = 0
#        self.animation_speed = animation_speed
#
#        self.h = h
#        self.w = w
#
#        self.scale = scale
#
#        self.repeat = repeat
#
#        self.sprite_sheet = SpriteSheet(sprite_sheet_path)
#
#        self.image = self.sprite_sheet.get_image(
#            self.frames[self.index][0],
#            self.frames[self.index][1],
#            self.h,
#            self.w
#        )
#
#        self.image = pygame.transform.scale(self.image, (self.h*self.scale, self.w*self.scale))
#
#        self.rect = self.image.get_rect()
#        self.rect.x = x
#        self.rect.y = y
#
#    def update(self, obj):
#
#        self.tick_counter += 1
#        if self.tick_counter % self.animation_speed is 0:
#            if self.index < len(self.frames)-1:
#                self.index += 1
#            else:
#                self.index = 0
#                self.repeat -= 1
#
#        if self.repeat <= 0:
#            obj.remove(self)
#
#        self.image = self.sprite_sheet.get_image(
#            self.frames[self.index][0],
#            self.frames[self.index][1],
#            self.h,
#            self.w
#        )
#
#        self.image = pygame.transform.scale(self.image, (self.h*self.scale, self.w*self.scale))
#
#class ResupplyAnimation(SpecialAbilityAnimation):
#    def __init__(self, x, y):
#        super().__init__(
#            "game/visualizer/assets/resupply_animation.png",
#            [
#                [0,   0], [32,   0], [64,   0],
#                [0,  32], [32,  32], [64,  32],
#                [0,  64], [32,  64], [64,  64],
#
#            ],
#            x, y,
#            32, 32,
#            2, scale=2)

