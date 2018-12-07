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
            print(str(msg))
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
                    new_illgal_salvage = IllegalSalvage()
                    new_illgal_salvage.init(position=random_position, value=material_value)

                    universe.add_object(new_illgal_salvage)
                    self.print('Created new illegal salvage at {} with value {}CR'.format(random_position, material_value))

                    self.events.append({
                        "type": LogEvent.illegal_salvage_spawned,
                        "id": new_illgal_salvage.id,
                        "position": new_illgal_salvage.position
                    })

                # Logging
                self.events.append({
                    "type": LogEvent.cargo_dropped,
                    "ship_id": ship.id,
                    "amount": amount
                })

        # for now we will decay salvage untill garbage collectior is finished.
        for salvage in universe.get(ObjectType.illegal_salvage):
            salvage.turns_till_recycling -= 1

            if salvage.turns_till_recycling <= 0:
                universe.remove_object(salvage)
                del salvage

