import sys
import math

from game.common.enums import *
from game.common.name_helpers import *
from game.common.asteroid_field import AsteroidField
from game.common.ship import Ship
from game.common.stats import GameStats
from game.utils.helpers import *

class RepairController:

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

            # passive heal for ships near station
            ship_near_a_station = False
            for stations in universe.get("all_stations"):

                #  determine if ship should start repairing
                ship_in_radius = in_radius(
                    stations,
                    ship,
                    lambda s, t: s.accessibility_radius,
                    lambda e: e.position)
                if ship_in_radius:
                    ship_near_a_station = True
                    if ship.passive_repair_counter <= 0:
                        # countdown to next heal
                        ship.passive_repair_counter -= 0

                    elif ship.current_hull != ship.max_hull:
                        ship.passive_repair_counter = GameStats.passive_repair_counter

                        # commence heal
                        if ship.max_hull - ship.current_hull < GameStats.passive_repair_amount:
                            ship.current_hull = ship.max_hull
                        else:
                            ship.current_hull += GameStats.passive_repair_amount

            if not ship_near_a_station:
                ship.passive_repair_counter = GameStats.passive_repair_counter

            # Check for ships that are performing the repair action
            #if ship.action is PlayerAction.repair:

            #    payment = ship.action_param_2

                #  cannot afford repair
            #    if ship.credits < payment:
            #        return

            #    hull_to_repair = payment
            #    ship.current_hull