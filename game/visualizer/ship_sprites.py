import math

import pygame

from game.visualizer.spritesheet_functions import SpriteSheet
from game.common.enums import *

class ShipSpriteSheet(pygame.sprite.Sprite):
    def __init__(self, sprite_sheet_data, x, y, ship_id, color):
        super().__init__()

        sprite_sheet = SpriteSheet("game/visualizer/assets/simple_ship.png")

        self.image = sprite_sheet.get_image(sprite_sheet_data[0],
                                            sprite_sheet_data[1],
                                            sprite_sheet_data[2],
                                            sprite_sheet_data[3])

        self.image_cache = self.image

        # Colorizing ship
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
        self.ship_id = ship_id
        self.current_vec = None
        self.new_vec = None
        self.move_target = None

        self.first = False


    def update(self, universe, events, intermediate=0):

        ship = self.find_self(universe)
        if ship is None:
            return

        events = self.get_pertinent_events(events)

        if self.first:
            self.first = False
            self.rect.center = ship.position

        if intermediate == 0:
            self.current_vec = pygame.math.Vector2(self.rect.x, self.rect.y)
            self.new_vec = pygame.math.Vector2(ship.position)

            move_event = self.get_event_type(events, LogEvent.ship_move, one=True)
            if move_event:
                self.move_target = move_event["target_pos"]


        if self.move_target != None:
            # update rotation
            angle_to = math.degrees(math.atan2(
                self.rect.x-self.move_target[0],
                self.rect.y-self.move_target[1]))

            self.rotate(angle_to)

        # lerp
        lerp = self.current_vec.lerp(self.new_vec, intermediate)
        self.rect.x, self.rect.y = lerp[0], lerp[1]


    def find_self(self, universe):
        for obj in universe:
            if obj.object_type == ObjectType.ship and obj.id == self.ship_id:
                return obj
        return None

    def get_pertinent_events(self, events):
        my_events = []
        for e in events:
            if "ship_id" in e and e["ship_id"] == self.ship_id:
                my_events.append(e)
        return my_events

    def get_event_type(self, events, event_type, one=False):
        selected = []
        for e in events:
            if e["type"] == event_type:
                if one:
                    return e
                selected.append(e)
        return selected if len(selected) else None


    def rotate(self, angle):
        rot_sprite = pygame.transform.rotozoom(self.image_cache, angle, 0.6)
        self.image = rot_sprite
        self.rect = self.image.get_rect(center=self.rect.center)


class PlayerShipSprite(ShipSpriteSheet):
    def __init__(self, x, y, ship_id):
        ShipSpriteSheet.__init__(self, [
            0, 0,
            32, 32
        ], x, y, ship_id, pygame.Color(255, 255, 255))


class NeutralShipSprite(ShipSpriteSheet):
    def __init__(self, x, y, ship_id):
        ShipSpriteSheet.__init__(self, [
            0, 0,
            32, 32
        ], x, y, ship_id, pygame.Color(0, 255, 0))

class EnemyShipSprite(ShipSpriteSheet):
    def __init__(self, x, y, ship_id):
        ShipSpriteSheet.__init__(self, [
            0, 0,
            32, 32
        ], x, y, ship_id, pygame.Color(0, 0, 255))


