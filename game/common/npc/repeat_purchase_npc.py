import random

from game.common.enums import *
from game.common.npc.npc import NPC
from game.config import *
from game.utils.helpers import *

class RepeatPurchaseNPC(NPC):

    def take_turn(self, universe):

        # if at heading, clear heading
        if(self.heading is not None
                and self.heading[0] == self.ship.position[0]
                and self.heading[1] == self.ship.position[1]):
            self.heading = None

        # choose a new heading if we don't have one
        if self.heading is None:
            #self.heading = ( random.randint(0, WORLD_BOUNDS[0]), random.randint(0, WORLD_BOUNDS[1]))
            self.heading = random.choice(list(filter(lambda e:e.object_type != ObjectType.ship, universe))).position

        # move towards heading
        self.move(*self.heading)

        # buy random module if we don't have one and are in range of a station
        if self.ship.module_0 == ModuleType.empty or self.ship.module_1 == ModuleType.empty:
            for thing in universe:

                # Check for all stations in the universe
                if thing.object_type not in [ObjectType.secure_station, ObjectType.black_market_station]:
                    continue


                current_station = thing
                # Check if ship is within range of a / the station
                ship_in_radius = in_radius(
                        current_station,
                        self.ship,
                        lambda s,t:s.accessibility_radius,
                        lambda e:e.position)

                # skip if not in range
                if not ship_in_radius: continue



                # Buy module
                if self.ship.module_0 == ModuleType.empty:
                    self.buy_module(
                                ModuleType.engine_speed,
                                ModuleLevel.one,
                                ShipSlot.zero)
                if self.ship.module_1 == ModuleType.empty:
                    self.buy_module(
                                ModuleType.engine_speed,
                                ModuleLevel.two,
                                ShipSlot.one)
        elif self.ship.module_1 == ModuleType.locked:
            self.unlock_module()


        return self.action_digest()


