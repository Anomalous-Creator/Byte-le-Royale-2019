import random

from game.common.enums import *
from game.common.npc.npc import NPC
from game.config import *
from game.utils.helpers import *
import game.utils.filters as filters

class ModuleNPC(NPC):

    def take_turn(self, universe):

        # if at heading, clear heading
        if(self.heading is not None
                and self.heading[0] == self.ship.position[0]
                and self.heading[1] == self.ship.position[1]):
            self.heading = None

        # choose a new heading if we don't have one
        if self.heading is None:
            #self.heading = ( random.randint(0, WORLD_BOUNDS[0]), random.randint(0, WORLD_BOUNDS[1]))
            self.heading = random.choice(list(universe.get(ObjectType.ship))).position

        # move towards heading
        self.move(*self.heading)

        # buy random module if we don't have one and are in range of a station
        if self.ship.module_0 == ModuleType.empty:
            stations = universe.get(ObjectType.secure_station) + universe.get(ObjectType.black_market_station)
            for current_station in stations:

                # Check if ship is within range of a / the station
                ship_in_radius = in_radius(
                        current_station,
                        self.ship,
                        lambda s,t:s.accessibility_radius,
                        lambda e:e.position)

                # skip if not in range
                if not ship_in_radius:
                    continue

                # Buy module
                self.buy_module(
                            ModuleType.engine_speed,
                            random.choice([ModuleLevel.one, ModuleLevel.two, ModuleLevel.three, ModuleLevel.illegal]),
                            ShipSlot.zero)


        return self.action_digest()


