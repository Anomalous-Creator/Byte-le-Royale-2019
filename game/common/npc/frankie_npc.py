import random

from game.common.enums import *
from game.common.npc.npc import NPC
from game.utils.helpers import *
from game.client.user_client import UserClient
from game.config import *
import game.utils.filters as F


class FrankieNPC(NPC):

    def __init__(self, ship):
        UserClient.__init__(self)
        self.name = "FrankieNPC"
        self.ship = ship
        self.ship_id = ship.id

        self.action = None
        self.target = None
        self.material = None

        self.type = None
        self.level = None

        self.fields = None
        self.stations = None

        self.previous_position = None
        self.inactive_counter = 0

    def team_name(self):
        return f"FrankieNPC#{random.randint(1,1000)}"

    def take_turn(self, universe):
        # initialize empty variables
        if self.fields is None:
            self.fields = universe.get("asteroid_fields")
        if self.stations is None:
            self.stations = universe.get(ObjectType.station)

        # select new action if not currently in one
        if self.action is None:
            self.action = random.choice(["mine", "mine", "trade", "trade", "trade", "pirate", "module"])
            print(self.action)

        # mining action ------------------------------------------------------------------------------------------------
        if self.action is "mine":
            # if we don't have a field to mine from, pick one
            if self.target is None:
                self.target = random.choice(self.fields)
                self.material = self.target.material_type

            # if we have a field to mine from, go to it and mine until inventory is full
            elif self.target in self.fields:
                self.mine()
                self.move(*self.target.position)

                if sum(self.ship.inventory.values()) >= self.ship.cargo_space:
                    prices = get_best_material_prices(universe)
                    self.target = prices["best_import_prices"][self.material]["station"]

            # if we have a station to sell to, go and sell the materials
            elif self.target in self.stations:
                if self.material in self.ship.inventory:
                    self.sell_material(self.material, self.ship.inventory[self.material])
                self.move(*self.target.position)

                if self.material not in self.ship.inventory or self.ship.inventory[self.material] <= 0:
                    # mining action has been fulfilled
                    self.action = None
                    self.target = None
                    self.material = None

        # trade action -------------------------------------------------------------------------------------------------
        elif self.action is "trade":
            # if we don't have a station to buy from, pick one
            if self.target is None:
                while True:
                    self.target = random.choice(self.stations)
                    if self.target.object_type not in [ObjectType.black_market_station, ObjectType.secure_station]:
                        break
                self.material = self.target.production_material

            # if we have a station to buy from, go to it and purchase some
            elif sum(self.ship.inventory.values()) <= 0:
                self.move(*self.target.position)
                if in_radius(self.ship, self.target, self.target.accessibility_radius, lambda e:e.position):
                    self.buy_material(min(self.ship.cargo_space - sum(self.ship.inventory.values()),
                                          math.floor(self.ship.credits / self.target.sell_price)))

                    # find the station that'll buy it for the most
                    self.target = get_best_material_prices(universe)["best_import_prices"][self.material]["station"]

            # otherwise, sell all materials in the inventory
            elif self.target in self.stations:
                self.move(*self.target.position)
                if in_radius(self.ship, self.target, self.target.accessibility_radius, lambda e:e.position):
                    if self.material in self.ship.inventory:
                        self.sell_material(self.material, self.ship.inventory[self.material])

                if self.material not in self.ship.inventory or self.ship.inventory[self.material] <= 0:
                    # trade action has been fulfilled
                    self.action = None
                    self.target = None
                    self.material = None

        # pirate action ------------------------------------------------------------------------------------------------
        elif self.action is "pirate":
            # if we don't have a target, pick a new sucker
            if self.target is None:
                self.target = random.choice(universe.get("ships"))

            # if we have a target, pursue and kill until dead
            elif self.target.object_type is ObjectType.ship:
                if self.target.current_hull > 0 or self.target.respawn_counter == -1:
                    self.move(*self.target.position)
                    self.attack(self.target)
                else:
                    # target is dead
                    scrap_list = universe.get(ObjectType.illegal_salvage)
                    distance_list = [distance_to(self.ship, x, lambda e:e.position) for x in scrap_list]

                    self.target = scrap_list[distance_list.index(min(distance_list))]

            # once the target has died, go and take their trash
            elif self.target.object_type is ObjectType.illegal_salvage:
                self.move(*self.target.position)
                self.collect_illegal_salvage()

                if self.target.amount <= 10 or sum(self.ship.inventory.values()) >= self.ship.cargo_space:
                    # collected enough
                    market_list = universe.get(ObjectType.black_market_station)
                    distance_list = [distance_to(self.ship, x, lambda e: e.position) for x in market_list]

                    self.target = market_list[distance_list.index(min(distance_list))]

            # once we have scrap, go and sell it at a black market
            elif self.target.object_type is ObjectType.black_market_station:
                self.move(*self.target.position)
                if in_radius(self.ship, self.target, self.target.accessibility_radius, lambda e:e.position):
                    self.sell_salvage()

                    # pirate action has been fulfilled
                    self.action = None
                    self.target = None
                    self.material = None

        # module action ------------------------------------------------------------------------------------------------
        elif self.action is "module":
            # determine if a relevant module can be purchased
            if self.target is None:
                # decide on what module to get
                self.type = None
                if self.ship.module_0 is not ModuleType.empty:
                    self.type = self.ship.module_0
                else:
                    self.type = random.choice([ModuleType.cargo_and_mining, ModuleType.engine_speed,
                                               ModuleType.hull, ModuleType.weapons])

                # decide on upgrade level
                    self.level = None
                if self.ship.module_0_level is not ModuleLevel.illegal:
                    self.level = self.ship.module_0_level + 1
                else:
                    # maximum level reached, cannot buy a module
                    pass

                if self.type is not None or self.level is not None:
                    # check if it is within budget
                    price = get_module_price(get_median_material_price(get_material_sell_prices(universe)), self.level)
                    if self.ship.credits > price:
                        self.target = universe.get(ObjectType.secure_station)[0]
                    else:
                        self.action = None
                else:
                    self.action = None

            # go out and buy the module
            else:
                self.move(*self.target.position)
                if self.ship.module_0 is not self.type and self.ship.module_0_level is not self.level:
                    self.buy_module(self.type, self.level, ShipSlot.zero)
                else:
                    # module action has been fulfilled
                    self.action = None
                    self.target = None

        # override actions----------------------------------------------------------------------------------------------
        # healing
        if self.ship.current_hull / self.ship.max_hull <= 0.25:
            self.move(*universe.get(ObjectType.secure_station)[0].position)
            self.repair(self.ship.max_hull - self.ship.current_hull)

        # inactive tracker
        if self.ship.position == self.previous_position:
            self.inactive_counter += 1
        self.previous_position = self.ship.position

        # if standing still too long or dead, turn off and on again
        if self.inactive_counter >= 75 or self.ship.respawn_counter > 0:
            self.inactive_counter = 0

            self.action = None
            self.target = None
            self.material = None

            self.type = None
            self.level = None

            self.fields = None
            self.stations = None



        return self.action_digest()
