import random

from game.common.enums import *
from game.common.npc.npc import NPC
from game.utils.helpers import *
from game.config import *
import game.utils.filters as F


class AdvancedPirateNPC(NPC):

    target_ship = None
    is_hunting = True
    is_gathering = False
    is_selling = False

    def take_turn(self, universe):
        # if at heading, clear heading
        if(self.heading is not None
                and self.heading[0] == self.ship.position[0]
                and self.heading[1] == self.ship.position[1]):
            self.heading = None

        while AdvancedPirateNPC.target_ship is None or not AdvancedPirateNPC.target_ship.is_alive:
            ships = self.get_ships(universe)
            AdvancedPirateNPC.target_ship = random.choice(ships)

        salvage_list = universe.get(ObjectType.illegal_salvage)
        target_scrap = None
        for scrap in salvage_list:
            scrap_in_radius = in_radius(
                self.ship,
                scrap,
                self.ship.weapon_range,
                lambda e: e.position)
            if scrap_in_radius:
                target_scrap = scrap

        if AdvancedPirateNPC.is_hunting and AdvancedPirateNPC.target_ship.is_alive:
            AdvancedPirateNPC.is_hunting = False
            AdvancedPirateNPC.is_gathering = True
        elif AdvancedPirateNPC.is_gathering and target_scrap is None:
            AdvancedPirateNPC.is_gathering = False
            AdvancedPirateNPC.is_selling = True

        elif AdvancedPirateNPC.is_selling and not (MaterialType.salvage in self.ship.inventory and self.ship.inventory[MaterialType.salvage] >= 50):
            AdvancedPirateNPC.is_selling = False
            AdvancedPirateNPC.is_hunting = True


        if AdvancedPirateNPC.is_gathering:
            self.heading = self.ship.position
            self.collect_illegal_salvage()

        elif AdvancedPirateNPC.is_selling:
            for thing in universe.get(ObjectType.black_market_station):
                if thing.object_type is ObjectType.black_market_station:
                    station = thing

            self.heading = station.position

            self.sell_salvage()
        else:
            AdvancedPirateNPC.is_hunting = True
            self.heading = AdvancedPirateNPC.target_ship.position
            self.attack(AdvancedPirateNPC.target_ship)

        # move towards heading
        self.move(*self.heading)

        if self.ship.module_0 == ModuleType.empty:
            self.buy_module(ModuleType.weapons, 1, 0)

        return self.action_digest()


