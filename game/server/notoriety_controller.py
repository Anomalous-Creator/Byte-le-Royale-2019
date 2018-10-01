import sys
import math

from game.common.enums import *
from game.common.stats import *
from game.common.name_helpers import *
from game.common.asteroid_field import AsteroidField
from game.common.ship import Ship

class NotorietyController:

    __instance = None

    def __init__(self):

        if NotorietyController.__instance != None:
            print("NotorietyController is a singleton and has already been instanciated. Use NotorietyController.get_instance() to get instance of class")
        else:
            NotorietyController.__instance = self

        self.debug = True
        self.events = []
        self.stats = []


    @staticmethod
    def get_instance():
        if NotorietyController.__instance == None:
            NotorietyController()
        return NotorietyController.__instance

    def print(self, msg):
        if self.debug:
            print(str(msg))
            sys.stdout.flush()

    def attribute_notoriety(self, ship, change_reason):
        change = 0

        # evil deeds
        if change_reason is NotorietyChangeReason.destroy_civilian:
            ship.notoriety += GameStats.destroy_civilian
        elif change_reason is NotorietyChangeReason.destroy_bounty_hunter:
            ship.notoriety += GameStats.destroy_bounty_hunter
        elif change_reason is NotorietyChangeReason.destroy_police:
            ship.notoriety += GameStats.destroy_police
        elif change_reason is NotorietyChangeReason.destroy_enforcer:
            ship.notoriety += GameStats.destroy_enforcer
        elif change_reason is NotorietyChangeReason.carrying_illegal_module:
            ship.notoriety += GameStats.carrying_illegal_module

        # good deeds
        elif change_reason is NotorietyChangeReason.destroy_pirate:
            ship.notoriety += GameStats.destroy_pirate

        # a remote possibility that you will be ably to pay off your own bounty
        #elif change_reason is NotorietyChangeReason.pay_off_bounty:
        #    ship.notoriety += GameStats.pay_off_bounty



    def update_standing(self, universe):
        for obj in universe:
            if obj.object_type is not ObjectType.ship: continue

            ship = obj
            if ship.notoriety >= LegalStanding.pirate:
                ship.legal_standing = LegalStanding.pirate
            elif LegalStanding.bounty_hunter <= ship.notoriety:
                ship.legal_standing = LegalStanding.bounty_hunter
            else:
                ship.legal_standing = LegalStanding.citizen
