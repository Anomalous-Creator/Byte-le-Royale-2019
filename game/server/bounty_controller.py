import sys
import math

from game.utils.helpers import *
from game.server.accolade_controller import AccoladeController

class BountyController:

    def __init__(self):

        self.debug = False
        self.events = []
        self.stats = []
        self.accolade_controller = AccoladeController.get_instance()

    def print(self, msg):
        if self.debug:
            print('BountyController: ' + str(msg))
            sys.stdout.flush()

    def get_events(self):
        e = self.events
        self.events = []
        return e

    def get_stats(self):
        s = self.stats
        self.stats = []
        return s

    @staticmethod
    def clear_bounty(ship):
        for bounty in ship.bounty_list:
            if bounty["bounty_type"] is not BountyType.became_pirate:
                ship.bounty_list.remove(bounty)

    def handle_actions(self, living_ships, universe, teams, npc_teams):
        for team, data in { **teams, **npc_teams}.items():
            ship = data["ship"]

            if ship.is_alive():
                # Determine new bounty if ship is not a pirate
                if ship.notoriety < LegalStanding.pirate:
                    ship.bounty = 0
                    self.clear_bounty(ship)
                    continue

                # Determine new bounty total
                new_bounty = 0

                # Sum the value of all bounties currently held
                for bounty_instance in ship.bounty_list:
                    if bounty_instance["bounty_type"] is BountyType.scrap_sold:
                        # Scrap sold has its bounty value reduced by 0.2% multiplied by number of ticks since it occurred
                        ratio = 1 - (BOUNTY_DECAY_RATE * bounty_instance["age"])
                        if ratio <= 0:
                            ship.bounty_list.remove(bounty_instance)
                            continue
                        new_bounty += ratio * bounty_instance["value"]

                        bounty_instance["age"] += 1
                    else:
                        new_bounty += bounty_instance["value"]

                # Only performing the ceiling one time to maintain accuracy
                ship.bounty = math.ceil(new_bounty)
                self.print(f"New bounty of {ship.bounty} determined for ship: {ship.id}")

                # Check if the player is trying to pay off their bounty
                if ship.action is PlayerAction.pay_off_bounty:

                    if ship.credits < ship.bounty * BOUNTY_PAYOFF_RATIO:
                        self.print(f"Not enough funds to pay off the bounty, has {ship.credits} needs {ship.bounty * BOUNTY_PAYOFF_RATIO}")
                        continue

                    self.print("Ship has funds to pay off bounty")

                    for station in universe.get(ObjectType.secure_station):
                        ship_in_radius = in_radius(
                            station,
                            ship,
                            lambda s, t: s.accessibility_radius,
                            lambda e: e.position)
                        if ship_in_radius:
                            self.print("Ship in range of secure station")
                            break
                    else:
                        self.print("Ship not in range of a secure station")
                        continue


                    # Reduce credits and bounty
                    ship.credits -= max(math.floor(ship.bounty * BOUNTY_PAYOFF_RATIO), 0)
                    ship.bounty = 0

                    # Remove all necessary bounties
                    self.clear_bounty(ship)

                    # Reduce notoriety
                    ship.notoriety = 4

                    self.events.append({
                        "type": LogEvent.ship_pay_off_bounty,
                        "ship_id": ship.id,
                    })

                    self.stats.append({
                        "ship_id": ship.id,
                        "credits": ship.credits,
                    })

            else:
                self.clear_bounty(ship)
