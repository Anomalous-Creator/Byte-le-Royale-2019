import json
import os

from game.common.enums import *
from game.common.ship import Ship
from game.common.police_ship import PoliceShip
from game.common.station import *
from game.common.illegal_salvage import *
from game.common.asteroid_field_types import load_asteroid_field

class GameLogParser:
    def __init__(self, log_dir):

        if not os.path.exists(log_dir):
            raise Exception("Invalid log directory: {}".format(log_dir))

        self.log_dir = log_dir
        self.stats = []

        # parse manifest
        with open("{}/manifest.json".format(log_dir), "r") as f:
            manifest = json.load(f)
            self.max_ticks = manifest["ticks"] - 1

        self.turns = []


        self.tick = 1

        self.load_turns()

    def load_turns(self):
        for tick in range(1,self.max_ticks):
            with open("{0}/{1:05d}.json".format(self.log_dir, tick), "r") as f:
                turn = json.load(f)

            events = self._parse_turn(turn)
            self.turns.append(events)

    def get_turn(self):
        if self.tick < self.max_ticks-1:
            turn = self.turns[self.tick]
            self.tick += 1
            return turn
        else:
            return None, None

    def check_finished(self):
        return self.tick > self.max_ticks


    def _parse_turn(self, turn):

        events = turn["turn_result"]["events"]
        universe = self.deserialize_universe(turn["turn_result"]["universe"])

        for event in events:
            # mark that the event hasn't been handled
            event["handled"] = False

            if event["type"] == LogEvent.ship_attack:
                event["attacker"] = self.get_ship(event["attacker"], universe)
                event["target"] = self.get_ship(event["target"], universe)

            elif event["type"] == LogEvent.police_spawned:
                event["ship"] = self.get_ship(event["ship_id"], universe)

            elif event["type"] == LogEvent.enforcer_spawned:
                event["ship"] = self.get_ship(event["ship_id"], universe)

        self.stats.append(turn["turn_result"]["stats"])

        return universe, events

    def get_stats(self, turns=0):
        if turns <= 0 or turns > self.tick:
            return self.stats[0:self.tick]
        else:
            return self.stats[(self.tick-turns):self.tick]

    def deserialize_universe(self, data):
        objs = []

        for serialized_obj in data:
            obj_type = serialized_obj["object_type"]
            if obj_type == ObjectType.ship:
                obj = Ship()
                obj.from_dict(serialized_obj, security_level=SecurityLevel.engine)
                objs.append(obj)

            elif obj_type == ObjectType.police:
                obj = PoliceShip()
                obj.from_dict(serialized_obj, security_level=SecurityLevel.engine)
                objs.append(obj)

            elif obj_type == ObjectType.enforcer:
                obj = PoliceShip()
                obj.from_dict(serialized_obj, security_level=SecurityLevel.engine)
                objs.append(obj)

            elif obj_type == ObjectType.station:
                obj = Station()
                obj.from_dict(serialized_obj, security_level=SecurityLevel.engine)
                objs.append(obj)

            elif obj_type == ObjectType.black_market_station:
                obj = BlackMarketStation()
                obj.from_dict(serialized_obj, security_level=SecurityLevel.engine)
                objs.append(obj)

            elif obj_type == ObjectType.secure_station:
                obj = SecureStation()
                obj.from_dict(serialized_obj, security_level=SecurityLevel.engine)
                objs.append(obj)

            elif obj_type in [ObjectType.cuprite_field]:
                obj = load_asteroid_field(obj_type, serialized_obj, security_level=SecurityLevel.engine)
                objs.append(obj)

            elif obj_type in [ObjectType.gold_field]:
                obj = load_asteroid_field(obj_type, serialized_obj, security_level=SecurityLevel.engine)
                objs.append(obj)

            elif obj_type in [ObjectType.goethite_field]:
                obj = load_asteroid_field(obj_type, serialized_obj, security_level=SecurityLevel.engine)
                objs.append(obj)

            elif obj_type == ObjectType.illegal_salvage:
                obj = IllegalSalvage()
                obj.from_dict(serialized_obj, security_level=SecurityLevel.engine)
                objs.append(obj)

        return objs

    def get_ship(self, ship_id, universe):
        for obj in universe:
            if obj.object_type in [ObjectType.ship, ObjectType.police, ObjectType.enforcer] and obj.id == ship_id:
                return obj

        raise Exception(f"Could not find ship {ship_id}")


