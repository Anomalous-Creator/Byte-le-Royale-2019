import sys
import random
import math

from game.utils.helpers import *
from game.common.stats import *
from game.common.illegal_salvage import IllegalSalvage

class IllegalSalvageController:

    def __init__(self):

        self.debug = False
        self.events = []
        self.stats = []

    def print(self, msg):
        if self.debug:
            print('IllegalSalvageController: ' + str(msg))
            sys.stdout.flush()

    def get_events(self):
        e = self.events
        self.events = []
        return e

    def get_stats(self):
        s = self.stats
        self.stats = []
        return s

    def handle_actions(self, living_ships, universe, teams, npc_teams):
        for team, data in { **teams, **npc_teams}.items():
            ship = data["ship"]

            # Check for ships that are performing the drop cargo action
            if ship.action is PlayerAction.drop_cargo:
                self.print('dropping illegal salvage...')

                if not ship.is_alive():
                    continue

                material_type = ship.action_param_1
                amount = ship.action_param_2

                if material_type not in ship.inventory:
                    continue

                inventory = ship.inventory[material_type]
                amount_left = max(0, inventory-amount)
                amount_dropped = inventory - amount_left

                ship.inventory[material_type] = amount_left

                # TODO get current value of material
                material_value = 10

                # Create salvage object
                salvage_to_create = math.floor(amount_dropped/100)

                for _ in range(salvage_to_create):
                    random_position = (
                        ship.position[0] + random.randint(-10, 10),
                        ship.position[1] + random.randint(-10, 10)
                    )
                    new_illegal_salvage = IllegalSalvage()
                    new_illegal_salvage.init(position=random_position, value=material_value)

                    universe.append(new_illegal_salvage)
                    self.print('Created new illegal salvage at {} with value {}CR'.format(random_position, material_value))

                    self.events.append({
                        "type": LogEvent.illegal_salvage_spawned,
                        "id": new_illegal_salvage.id,
                        "position": new_illegal_salvage.position
                    })

                # Logging
                self.events.append({
                    "type": LogEvent.cargo_dropped,
                    "ship_id": ship.id,
                    "amount": amount
                })



            # Check for ships performing the salvage action
            elif ship.action is PlayerAction.collect_illegal_salvage:

                if not ship.is_alive():
                    continue

                salvage = None
                for thing in universe:
                    # Check for all scrap in the universe within weapon's range
                    if thing.object_type is ObjectType.illegal_salvage:
                        scrap = thing

                        ship_in_radius = in_radius(
                            scrap,
                            ship,
                            ship.weapon_range,
                            lambda e: e.position)

                        if ship_in_radius:
                            salvage = scrap
                            break
                else:
                    self.print('No illegal salvage found nearby')
                    continue

                # Check if salvage pile is already empty just in case
                if salvage.value == 0:
                    self.print('Found illegal salvage has no value')
                    continue

                # TODO determine balanced pickup rate
                pickup_rate = 10

                pickup_amount = 0
                if salvage.value >= pickup_rate:
                    pickup_amount = pickup_rate
                elif salvage.value < pickup_rate:
                    pickup_amount = salvage.value

                salvage.value -= pickup_amount
                if MaterialType.salvage not in ship.inventory:
                    ship.inventory[MaterialType.salvage] = 0
                ship.inventory[MaterialType.salvage] += pickup_amount

                self.print('Illegal salvage collected')

                # Logging
                self.events.append({
                    "type": LogEvent.illegal_salvage_picked_up,
                    "ship_id": ship.id,
                })

                self.stats.append({
                    "ship_id": ship.id,
                    "material": MaterialType.salvage,
                    "yield": pickup_amount
                })





        # for now we will decay salvage untill garbage collectior is finished.
        for salvage in filter(lambda e:e.object_type == ObjectType.illegal_salvage, universe):
            salvage.turns_till_recycling -= 1

            if salvage.turns_till_recycling <= 0 or salvage.value <= 0:
                universe.remove(salvage)
                del salvage

