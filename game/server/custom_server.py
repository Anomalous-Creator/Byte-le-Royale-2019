import json
import random
from math import sqrt

from game.server.server_control import ServerControl
from game.common.enums import *
from game.common.npc.test import *
from game.common.npc.test.advanced_pirate_npc import *
from game.common.ship import Ship
from game.utils.generate_game import load
from game.utils.helpers import *

from game.common.npc.frankie_npc import FrankieNPC
from game.common.npc.crankie_npc import CrankieNPC

from game.server.station_controller import StationController
from game.server.mining_controller import MiningController
from game.server.notoriety_controller import NotorietyController
from game.server.combat_controller import CombatController
from game.server.death_controller import DeathController
from game.server.police_controller import PoliceController
from game.server.module_controller import ModuleController
from game.server.buy_sell_controller import BuySellController
from game.server.illegal_salvage_controller import IllegalSalvageController
from game.server.repair_controller import RepairController
from game.common.universe_manager import UniverseManager
from game.server.bounty_controller import BountyController
import game.utils.filters as filters
from game.config import *
from game.utils.projection import *


class CustomServer(ServerControl):

    def __init__(
            self,
            verbose=False,
            wait_on_client=False,
            connection_wait_timer=3,
            wait_timer=None,
            max_game_tick=1000):
        super().__init__(
                wait_on_client,
                connection_wait_timer,
                wait_timer,
                max_game_tick,
                verbose)

        self.verbose = verbose

        self.started = False
        self.turn_log = None

        self.teams = {} #client id to team data
        self.npc_teams = {}

        self.universe = UniverseManager(load())


        # Set up controllers
        self.station_controller = StationController(self.universe.get(ObjectType.station))
        self.station_controller.init(self.universe.get(ObjectType.station))

        self.mining_controller = MiningController()
        self.notoriety_controller = NotorietyController.get_instance()
        self.combat_controller = CombatController()
        self.death_controller = DeathController()
        self.police_controller = PoliceController()
        self.module_controller = ModuleController()
        self.buy_sell_controller = BuySellController()
        self.illegal_salvage_controller = IllegalSalvageController()
        self.repair_controller = RepairController()
        self.bounty_controller = BountyController()

        # prep police
        self.police_controller.setup_police(self.universe)

        self.claim_npcs()

    def pre_turn(self):
        self.print("#"*70)
        self.print("SERVER PRE TURN")

        # reset turn result
        self.turn_log = {
            "events":[],
            "stats": {}
        }

        if not self.started:
            # first turn, ask for client config, e.g. team name
            return # purposefully short circuit to get to send data

        # update police state
        self.police_controller.assess_universe(self.universe)

    def send_turn_data(self):
        # send turn data to clients
        self.print("SERVER SEND DATA")
        payload = {}

        serialized_universe = self.serialize_universe(security_level=SecurityLevel.player_owned)

        for i in self._client_ids:
            #print(f"Pinging {i}")
            #payload[i] = { "message_type": MessageType.ping}

            if not self.started:
                # request team registration info
                payload[i] = {
                        "message_type":  MessageType.team_name
                }

            else:
                # send game specific data in payload
                payload[i] = {
                    "message_type": MessageType.take_turn,
                    "ship": self.teams[i]["ship"].to_dict(security_level=SecurityLevel.player_owned),
                    "universe": self.serialize_visible_objects(SecurityLevel.other_player, i)
                }

        # actually send the data to the client
        self.send({
            "type": "server_turn_prompt",
            "payload": payload
        })

    def post_turn(self):
        self.print("SERVER POST TURN")

        self.deserialize_turn_data()

        if self.started:
            # reset team actions to prevent accidental repeat actions
            for k in self.teams.keys():
                self.teams[k]["action"] = PlayerAction.none
                self.teams[k]["action_param_1"] = None
                self.teams[k]["action_param_2"] = None
                self.teams[k]["action_param_3"] = None

                self.teams[k]["move_action"] = None

        # handle response if we got one
        for data in self.turn_data:
            client_id = data["client_id"]

            if "message_type" not in data:
                return # bad turn
            else:
                message_type = data["message_type"]

            if not self.started:
                if message_type == MessageType.team_name:
                   self.print("Register team name")

                   team_name = data["team_name"]
                   team_color = data["team_color"]

                   ship = Ship()
                   ship.init(team_name, team_color, position=percent_world(0.5, 0.5))

                   self.universe.add_object(ship)

                   self.teams[client_id] = {
                       "team_name": team_name,
                       "ship": ship
                   }

            else:

                if message_type == MessageType.take_turn:
                    if "action_type" in data:
                        # get action
                        self.teams[client_id]["action"] = data["action_type"]
                        setattr(self.teams[client_id]["ship"], "action", data["action_type"])

                        # get action params
                        for i in range(1, 4):
                            param = f"action_param_{i}"
                            if param in data:
                                self.teams[client_id][param] = data[param]
                                setattr(self.teams[client_id]["ship"], param, data[param])


                    if "move_action" in data:
                        self.teams[client_id]["move_action"] = data["move_action"]

        # queue npc actions
        if self.started:
            # reset team actions to prevent accidental repeat actions
            for k in self.npc_teams.keys():
                self.npc_teams[k]["ship"].action = PlayerAction.none
                self.npc_teams[k]["ship"].action_param_1 = None
                self.npc_teams[k]["ship"].action_param_2 = None
                self.npc_teams[k]["ship"].action_param_3 = None

                self.npc_teams[k]["ship"].move_action = None

            for npc in self.npc_teams.keys():
                result = self.npc_teams[npc]["controller"].reset_actions()
                result = self.npc_teams[npc]["controller"].take_turn(self.universe)

                self.npc_teams[npc]["ship"].action = result["action_type"]
                self.npc_teams[npc]["ship"].action_param_1 = result["action_param_1"]
                self.npc_teams[npc]["ship"].action_param_2 = result["action_param_2"]
                self.npc_teams[npc]["ship"].action_param_3 = result["action_param_3"]

                self.npc_teams[npc]["ship"].move_action = result["move_action"]


            for police in self.universe.get("police"):
                police.move_action = None
                police.action = None
                police.action_param_1 = None
                police.action_param_2 = None
                police.action_param_3 = None

                actions = self.police_controller.take_turn(police, self.universe)

                police.move_action = actions["move_action"]
                police.action = actions["action"]
                police.action_param_1 = actions["action_param_1"]
                police.action_param_2 = actions["action_param_2"]
                police.action_param_3 = actions["action_param_3"]


            self.process_actions()

            self.process_move_actions()


        # update station market / update BGS
        self.station_controller.tick(self.universe.get(ObjectType.station))

        self.turn_log["stats"]["market"] = self.station_controller.get_stats()
        self.turn_log["stats"]["mining"] = self.mining_controller.get_stats()
        self.turn_log["stats"]["buying/selling"] = self.buy_sell_controller.get_stats()


        # set to started
        self.started = True

        self.turn_data = []
        self.turn_log["universe"] = self.serialize_universe(security_level=SecurityLevel.engine)
        #self.accolade_controller.update_ships(self.teams)

    def log(self):
        # saves the turn log to this turn's log file.
        # This is what the visualizer reads
        return {
            "turn_result": self.turn_log
        }

    def deserialize_turn_data(self):
        # Deserialize a message from a client

        # if we have recieved a message, then turn data will not be none
        for idx, data in enumerate(self.turn_data):
            if data["message_type"] != MessageType.demo:
                # Deserialize message data, i.e. load ship data
                pass

    def check_end(self):
        # Detect if we have reached a stopping state
        # set self._quit to true to safely shutdown at end of turn
        #self._quit = True
        pass

    def print(self, msg):
        # Handles toggling print messages via verbose
        if self.verbose:
            print(msg)

    def game_over(self):
        accolades = dict()
        accolades["Most Mined"] = self.accolade_controller.most_ore_mined()[0]
        accolades["Most Bounties Claimed"] = self.accolade_controller.most_bounties_claimed()[0]
        accolades["Most Salvage Redeemed"] = self.accolade_controller.most_salvage_redeemed()[0]
        accolades["Most Credits Earned"] = self.accolade_controller.most_credits_earned()[0]
        accolades["Most Fuel Efficient"] = self.accolade_controller.most_efficient()[0]
        accolades["Most Upgraded"] = self.accolade_controller.most_upgrades()[0]
        accolades["Most Ruthless"] = self.accolade_controller.most_innocents_killed()[0]
        accolades["Most Notorious"] = self.accolade_controller.most_notorious()["name"]
        toJSON = {"leaderboard": self.accolade_controller.final_scores(self.universe), "accolades": accolades}
        with open("results.json", "w") as f:
            json.dump(toJSON, f)
        return toJSON

    def claim_npcs(self):
        self.npcs = []

        npc_options = {
                CrankieNPC: 0.425,
                FrankieNPC: 0.425,
                TestMinerNPC: 0.0,
                TestTraderNPC: 0.01,
                CombatNPC: 0.0,
                AdvancedPirateNPC: 0.14,
        }

        for idx, ship in enumerate(self.universe.get(ObjectType.ship)):
            npc_type = random.choices(
                    list(npc_options.keys()),
                    weights=list(npc_options.values()),
                    k=1)[0]

            new_npc_controller = npc_type(ship)
            ship.team_name = new_npc_controller.team_name()

            self.npc_teams[ship.id] = {
                "controller": new_npc_controller,
                "ship": ship
            }


    def process_actions(self):

        # check if ships still alive
        living_ships = self.universe.get_filtered(ObjectType.ship, filter=filters.alive())

        teams = { **self.teams, **{ship.team_name: {"ship": ship} for ship in self.universe.get("police") }}

        # apply the results of any actions a player took if player still alive
        self.bounty_controller.handle_actions(living_ships, self.universe, teams, self.npc_teams)
        self.mining_controller.handle_actions(living_ships, self.universe, teams, self.npc_teams)
        self.combat_controller.handle_actions(living_ships, self.universe, teams, self.npc_teams)
        self.module_controller.handle_actions(living_ships, self.universe, teams, self.npc_teams)
        self.buy_sell_controller.handle_actions(living_ships, self.universe, teams, self.npc_teams)
        self.illegal_salvage_controller.handle_actions(living_ships, self.universe, teams, self.npc_teams)
        self.repair_controller.handle_actions(living_ships, self.universe, teams, self.npc_teams, self.combat_controller.get_combat_counts())

        dead_ships = self.universe.get_filtered(ObjectType.ship, filter=filters.NOT(filters.alive()))
        self.death_controller.handle_actions(dead_ships, self.universe)

        self.notoriety_controller.update_standing_universe(self.universe.get(ObjectType.ship))

        # log events
        self.turn_log["events"].extend( self.mining_controller.get_events() )

        self.turn_log["events"].extend(self.buy_sell_controller.get_events())

        self.turn_log["events"].extend( self.combat_controller.get_events() )

        self.turn_log["events"].extend( self.death_controller.get_events() )

        self.turn_log["events"].extend( self.police_controller.get_events() )

        self.turn_log["events"].extend( self.notoriety_controller.get_events() )

        self.turn_log["events"].extend( self.module_controller.get_events() )

        self.turn_log["events"].extend( self.illegal_salvage_controller.get_events() )

        self.turn_log["events"].extend( self.bounty_controller.get_events() )

        self.turn_log["events"].extend( self.repair_controller.get_events() )

    def process_move_actions(self):

        for team, data in { **self.teams, **self.npc_teams}.items():
            ship = data["ship"]

            if ship.is_alive():
                if "move_action" in data:
                    ship.move_action = data["move_action"]
                self.move_ship(ship)

        for ship in self.universe.get("police"):
            self.move_ship(ship)

    def move_ship(self, ship):

        if ship.move_action is not None:

            target_x_difference  = ship.move_action[0] - ship.position[0]
            target_y_difference  = ship.move_action[1] - ship.position[1]

            x_direction = -1 if target_x_difference < 0 else 1
            x_magnitude = abs(target_x_difference)

            y_direction = -1 if target_y_difference < 0 else 1
            y_magnitude = abs(target_y_difference)

            x_move = min(ship.engine_speed, x_magnitude)
            y_move = min(ship.engine_speed, y_magnitude)

            self.accolade_controller.ship_moved(ship, sqrt(x_move**2 + y_move**2) )

            ship.position = (
                x_direction*x_move + ship.position[0],
                y_direction*y_move + ship.position[1]
            )

            self.turn_log["events"].append({
                "type": LogEvent.ship_move,
                "ship_id": ship.id,
                "pos": ship.position,
                "target_pos": ship.move_action
            })

    def serialize_universe(self, security_level):
        serialized_universe = []

        for obj in self.universe.dump():
            serialized_obj = obj.to_dict(security_level=security_level)
            serialized_universe.append(serialized_obj)
        return serialized_universe

    def serialize_visible_objects(self, security_level, ship_id):
        serialized_visible_universe = []
        own_ship = self.teams[ship_id]["ship"]

        for obj in self.universe.dump():
            if obj.object_type is ObjectType.ship:
                if obj.id == own_ship.id or not in_radius(own_ship, obj, own_ship.sensor_range, lambda e:e.position):
                    continue
            serialized_obj = obj.to_dict(security_level=security_level)
            serialized_visible_universe.append(serialized_obj)
        return serialized_visible_universe



