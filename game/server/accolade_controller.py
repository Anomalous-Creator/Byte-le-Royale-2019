import sys
import math
from game.common.enums import *

class AccoladeController:

    __instance = None

    def __init__(self):

        if AccoladeController.__instance != None:
            print("AccoladeController is a singleton and has already been instanciated. Use AccoladeController.get_instance() to get instance of class")
        else:
            AccoladeController.__instance = self

        self.debug = False
        self.events = []
        self.stats = []
        self.ore = dict()
        self.bounties = dict()
        self.scrap = dict()
        self.salvage = dict()
        self.credits = dict() #credits earned NOT salvage
        self.allCredits = dict() # includes salvage
        self.moved = dict()
        self.upgrades = dict()
        self.kInnocent = dict() #killed an innocent
        self.notorious = {"name": "", "notoriety": 4}


    @staticmethod
    def get_instance():
        if AccoladeController.__instance == None:
            AccoladeController()
        return AccoladeController.__instance

    def get_events(self):
        e = self.events
        self.events = []
        return e

    def get_stats(self):
        s = self.stats
        self.stats = []
        return s

    def print(self, msg):
        if self.debug:
            print("Accolade Controller:" + str(msg))
            sys.stdout.flush()

    # Ore Mined
    def ore_mined(self, ship, oreAdd):
        if ship in self.ore:
            self.ore[ship] += oreAdd
        else:
            self.ore[ship] = oreAdd

    def most_ore_mined(self):
        most = -1
        ship = ""
        for x in self.ore:
            if self.ore[x] > most:
                most = self.ore[x]
                ship = x.team_name
        return [ship, most]

    # Bounties claimed
    def bounty_claim(self, ship):
        if ship in self.bounties:
            self.bounties[ship] += 1
        else:
            self.bounties[ship] = 1
            
    def most_bounties_claimed(self):
        most = -1
        ship = ""
        for x in self.bounties:
            if self.bounties[x] > most:
                most = self.bounties[x]
                ship = x.team_name

        return [ship, most]

    # How much salvage redeemed
    def redeem_salvage(self, ship, salvageAdd):
        if ship in self.salvage:
            self.salvage[ship] += salvageAdd
        else:
            self.salvage[ship] = salvageAdd

    def most_salvage_redeemed(self):
        most = -1
        ship = ""
        for x in self.salvage:
            if self.salvage[x] > most:
                most = self.salvage[x]
                ship = x.team_name

        return [ship, most]

    # credits not from salvage
    def credits_earned(self, ship, creditAdd):
        if ship in self.credits:
            self.credits[ship] += creditAdd
        else:
            self.credits[ship] = creditAdd

    def most_credits_earned(self):
        most = -1
        ship = ""
        for x in self.credits:
            if self.credits[x] > most:
                most = self.credits[x]
                ship = x.team_name

        return [ship, most]

    # all credits
    def all_credits_earned(self, ship, creditAdd):
        if ship in self.allCredits:
            self.allCredits[ship] += creditAdd
        else:
            self.allCredits[ship] = creditAdd

    # Fuel Efficient
    def ship_moved(self, ship, distance):
        if ship in self.moved:
            self.moved[ship] += distance
        else:
            self.moved[ship] = distance

    def most_efficient(self):
        max_efficient = -1
        ship_efficient = ""
        for x in self.moved:
            if x in self.allCredits:
                efficiency = self.allCredits[x] / self.moved[x]
                if efficiency > max_efficient:
                    ship_efficient = x.team_name
                    max_efficient = efficiency

        return [ship_efficient, max_efficient]

    # Ship Upgrades
    def ship_upgraded(self, ship, cost):
        if ship in self.upgrades:
            self.upgrades[ship] += cost
        else:
            self.upgrades[ship] = cost

    def most_upgrades(self):
        most = -1
        ship = ""
        for x in self.upgrades:
            if self.upgrades[x] > most:
                ship = x.team_name
                most = self.upgrades[x]
        return [ship, most]

    # Most Innocents Killed (innocent is dealt no damage back)
    def kill_innocent(self, ship):
        if ship in self.kInnocent:
            self.kInnocent[ship] += 1
        else:
            self.kInnocent[ship] = 1

    def most_innocents_killed(self):
        most = -1
        shipName = ""
        for ship in self.kInnocent:
            if self.kInnocent[ship] > most:
                shipName = ship.team_name
                most = self.kInnocent[ship]
        return [shipName, most]

    # The Most Pirate-y Pirate (for the moment, most notoriety)
    def have_notoriety(self, ship):
        if ship.notoriety > self.notorious["notoriety"]:
            self.notorious = {"name": ship.team_name, "notoriety": ship.notoriety}

    def most_notorious(self):
        return self.notorious

    def final_scores(self, universe):
        toSort = dict()
        for ship in universe.get(ObjectType.ship):
            toSort[ship.team_name] = ship.credits
        toSort = sorted(toSort.items(), key=lambda item: (item[1], item[0]), reverse=True)
        toReturn = list()
        i = 1
        for k, v in toSort:
            toReturn.append({"team_name": k, "credits": v})
            i += 1
        return toReturn
