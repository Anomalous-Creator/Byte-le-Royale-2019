import sys, math, random, time
import zipfile

import pygame
from pygame.locals import *

from game.visualizer.game_log_parser import GameLogParser
from game.visualizer.ship_sprites import *
from game.visualizer.station_sprites import *
from game.visualizer.illegal_salvage_sprite import IllegalSalvageSprite
from game.visualizer.asteroid_field_sprites import get_asteroid_field_sprite
from game.common.enums import *
from game.visualizer.ship_sprites import ShipSpriteSheet
from game.config import *
from game.visualizer.stats_display import *
import game.utils.stat_utils as stat_utils
import game.utils.click_utils as click_utils
import game.utils.helpers as helpers

pause = False
log_parser = None
global_surf = None
fpsClock = None
universe = None
events = None
focus_team_color = None
team_name = None

debug = False

# Create Sprite groups
ship_group = pygame.sprite.RenderUpdates()
station_group = pygame.sprite.Group()
asteroid_field_group = pygame.sprite.Group()
illegal_salvage_group = pygame.sprite.Group()

_VIS_INTERMEDIATE_FRAMES = VIS_INTERMEDIATE_FRAMES
_FPS = FPS

def log(msg):
    if debug:
        print(str(msg))


def start(verbose, log_path, gamma, dont_wait, fullscreen, focus_team_name=None):
    global fpsClock
    global log_parser
    global universe
    global events
    global team_name
    team_name = focus_team_name

    log_parser = GameLogParser(log_path)
    universe, events = log_parser.get_turn()
    ShipSpriteSheet.set_focus_team(focus_team_name)
    # if focus_team_name is not None: print(focus_team_name)
    # else: print("None")

    # initialize pygame
    pygame.init()
    fpsClock = pygame.time.Clock()

    # get global surface object and set window caption
    global global_surf
    if fullscreen:
        global_surf = pygame.display.set_mode(DISPLAY_SIZE, pygame.FULLSCREEN)
    else:
        global_surf = pygame.display.set_mode(DISPLAY_SIZE)
    pygame.display.set_caption('Byte-le Royale')

    # set gamma (i.e. sort of like brightness)
    pygame.display.set_gamma(gamma)

    for obj in universe:
        if obj.object_type == ObjectType.ship:
            if obj.team_name == focus_team_name:  # is the team name the focus team?
                ship_sprite = PlayerShipSprite(*obj.position, obj.id)
                ship_group.add(ship_sprite)
            else:
                ship_sprite = NeutralShipSprite(*obj.position, obj.id)
                ship_group.add(ship_sprite)

        elif obj.object_type == ObjectType.police:
            ship_sprite = PoliceShipSprite(*obj.position, obj.id)
            ship_group.add(ship_sprite)

        elif obj.object_type == ObjectType.enforcer:
            ship_sprite = EnforcerShipSprite(*obj.position, obj.id)
            ship_group.add(ship_sprite)

        elif obj.object_type == ObjectType.enforcer:
            ship_sprite = EnforcerShipSprite(*obj.position, obj.id)
            ship_group.add(ship_sprite)

        elif obj.object_type == ObjectType.station:
            station_sprite = NeutralStationSprite(*obj.position, obj.id)
            station_group.add(station_sprite)

        elif obj.object_type == ObjectType.black_market_station:
            station_sprite = BlackMarketStationSprite(*obj.position, obj.id)
            station_group.add(station_sprite)

        elif obj.object_type == ObjectType.secure_station:
            station_sprite = SecureStationSprite(*obj.position, obj.id)
            station_group.add(station_sprite)

        elif obj.object_type in [ObjectType.goethite_field, ObjectType.cuprite_field, ObjectType.gold_field]:
            asteroid_field_sprite = get_asteroid_field_sprite(obj.object_type, *obj.position)
            asteroid_field_group.add(asteroid_field_sprite)

        elif obj.object_type is ObjectType.illegal_salvage:
            illegal_salvage_sprite = IllegalSalvageSprite(*obj.position, obj.id)
            illegal_salvage_group.add(illegal_salvage_sprite)




    # prepare for game loop
    first_loop = True
    turn_wait_counter = 1

    while True:

        # Has the user paused the game?
        # if so don't try to update the screen
        if not pause:

            if log_parser.check_finished():
                # print("Finished log playback")
                if focus_team_name is not None:
                    stats_ship = None
                    for item in universe:
                        if item.object_type == ObjectType.ship and item.team_name == focus_team_name:
                            stats_ship = item
                            break
                    show_ship_stats_display(stats_ship, global_surf, fpsClock, dont_wait)
                    show_end_screen(focus_team_name, dont_wait)
                else:
                    show_end_screen(focus_team_name, dont_wait)

            # should we get the next turn event list
            # or should we wait for some animation to
            # finish
            if turn_wait_counter == 0:
                universe, events = log_parser.get_turn()

                if universe == None and events == None:
                    # game is over, go to end screen
                    # print("Finished playback!")

                    pygame.quit()
                    sys.exit()
            else:
                turn_wait_counter -= 1


            # read through the events and handle
            for event in events:
                if not event["handled"]:
                    pass
                    #if event["type"] == LogEvent.demo:
                    #    # there should be data stored
                    #    # on the event object pertaining to
                    #    # the type of event
                    #    print(event)

                    #    # Marks that we have handled this event
                    #    # prevents us from attempting to handle this event again
                    #    event["handled"] = True

                    if event["type"] is LogEvent.police_spawned:
                        new_ship = PoliceShipSprite(*event["ship"].position, event["ship"].id)
                        ship_group.add(new_ship)
                    if event["type"] is LogEvent.enforcer_spawned:
                        new_ship = EnforcerShipSprite(*event["ship"].position, event["ship"].id)
                        ship_group.add(new_ship)
                    elif event["type"] is LogEvent.police_removed:
                        for ship_sprite in ship_group.sprites():
                            if ship_sprite.ship_id == event["ship_id"]:
                                ship_group.remove(ship_sprite)
                    elif event["type"] is LogEvent.despawn_enforcer:
                        for ship_sprite in ship_group.sprites():
                            if ship_sprite.ship_id == event["ship_id"]:
                                ship_group.remove(ship_sprite)
                    if event["type"] is LogEvent.illegal_salvage_spawned:
                        new_illegal_salvage = IllegalSalvageSprite(*event["position"], event["id"])
                        illegal_salvage_group.add(new_illegal_salvage)



            #####
            # Rendering Stuff
            #####

            # render team name
            if first_loop:
                first_loop = False
                # render things here that should only be
                # rendered when we start and then are just redrawn
                # after this


            # intermediate loop
            # -- allows for pretty lerping of ship movement
            if _VIS_INTERMEDIATE_FRAMES <= 0:
                update_groups(-1)
                draw_screen()

                draw_lasers(ship_group, events)

                handle_events()

                # update the display
                pygame.display.update()
                fpsClock.tick(_FPS)
            else:
                for i in range(0,_VIS_INTERMEDIATE_FRAMES):
                    if _VIS_INTERMEDIATE_FRAMES >= 0:
                        intermediate = i/float(_VIS_INTERMEDIATE_FRAMES)
                    else:
                        intermediate = -1

                    update_groups(intermediate)

                    draw_screen()

                    draw_lasers(ship_group, events)

                    handle_events()

                    # update the display
                    pygame.display.update()
                    fpsClock.tick(FPS)
        else:
            handle_events()


def show_end_screen(focus_team_name, dont_wait):
    global fpsClock
    global log_parser
    global universe
    global events
    global global_surf

    wait_timer = 0

    while True:  # Leaderboard
        # Show leaderboard before exit
        # print("Reached the end of the match", flush=True)
        global_surf.fill(pygame.Color(0, 0, 0))

        # Set up variables used in display
        titleFont = pygame.font.SysFont(pygame.font.get_default_font(), 32)
        font = pygame.font.SysFont(pygame.font.get_default_font(), 16)
        currentHeight = 10
        gap = 20
        left_allign_leaderboard = 50
        left_allign_accolades = 720
        screenCenter = pygame.display.get_surface().get_size()[0] / 2

        if not dont_wait:
            renderText = titleFont.render("Final results", True, (0, 155, 0))  # Title
            global_surf.blit(renderText, [screenCenter - renderText.get_rect().width / 2, currentHeight])
            currentHeight += gap*2
            if focus_team_name is not None:
                renderText = font.render("Press escape to exit, press S to show stats screen again", True, (0, 155, 0))
            else:
                renderText = font.render("Press escape to exit", True, (0, 155, 0))
            global_surf.blit(renderText, [screenCenter - renderText.get_rect().width / 2, currentHeight])
            currentHeight += gap*2

        # Show team leaderboard
        for idx, team_data in enumerate(log_parser.results["leaderboard"]):
            team = team_data["team_name"]
            credits = team_data["credits"]
            if team == focus_team_name:
                text = " -> {0:>2}) {1:<7} Team {2}".format(idx + 1, int(credits), team[:20])
                renderText = font.render(text, True, (0, 255, 0))
                global_surf.blit(renderText, [left_allign_leaderboard - 40, currentHeight])
            else:
                text = "{0:>2}) {1:<7} Team {2}".format(idx+1, int(credits), team[:20])
                renderText = font.render(text, True, (0, 155, 0))
                global_surf.blit(renderText, [left_allign_leaderboard, currentHeight])
            currentHeight += gap

        currentHeight = 90
        # Show accolades
        for accolade, team in log_parser.results["accolades"].items():
            if team == focus_team_name:
                text = " -> {0:<25}: Team {1}".format(accolade, team[:20])
                renderText = font.render(text, True, (0, 255, 0))
                global_surf.blit(renderText, [left_allign_accolades, currentHeight])
            else:
                text = "{0:<25}: Team {1}".format(accolade, team[:20])
                renderText = font.render(text, True, (0, 155, 0))
                global_surf.blit(renderText, [left_allign_accolades, currentHeight])
            currentHeight += gap


        # Handle Events
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()

            if event.type == KEYUP:
                if event.key == K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                if event.key == K_s and focus_team_name is not None:
                    stats_ship = None
                    for item in universe:
                        if item.object_type == ObjectType.ship and item.team_name == focus_team_name:
                            stats_ship = item
                            break
                    show_ship_stats_display(stats_ship, global_surf, fpsClock)


        pygame.display.update()
        fpsClock.tick(_FPS)

        if dont_wait:
            # don't wait on anything requiring user input
            wait_timer += fpsClock.get_time()
            if wait_timer > 5000:
                sys.exit(0)



def update_groups(intermediate):

    # call update on groups
    ship_group.update(universe, events, intermediate)

    illegal_salvage_group.update(universe, illegal_salvage_group)

def draw_lasers(ship_group, events):
    attacks = get_events_of_type(LogEvent.ship_attack, events)

    for attack in attacks:
        if not attack["attacker"].is_alive():
            attacker = world_to_display(*attack["attacker_position"])
        else:
            attacker = next(filter(lambda e: e.ship_id == attack["attacker"].id, ship_group), None).rect.center

        if not attack["target"].is_alive():
            target = world_to_display(*attack["target_position"])
        else:
            target = next(filter(lambda e: e.ship_id == attack["target"].id, ship_group), None).rect.center

        pygame.draw.circle(global_surf, pygame.Color(155, 0, 0), attacker, 2)
        pygame.draw.aaline(global_surf, pygame.Color(255, 0, 0), attacker, target)

        spread = 8

        for _ in range(random.randint(2,4)):
            global_surf.fill(

                random.choice([
                    pygame.Color(155, 0, 0),
                    pygame.Color(255, 0, 0),
                    pygame.Color(255, 238, 0),
                    pygame.Color(255, 191, 0),
                    pygame.Color(255, 132, 0),

                ]), (
                random.randint(-spread,spread)+target[0],
                random.randint(-spread,spread)+target[1],
                2, 2,))



def draw_screen():

    # clear screen, fill with black
    global_surf.fill(pygame.Color(0,0,0))

    # draw groups to screen
    station_group.draw(global_surf)
    asteroid_field_group.draw(global_surf)
    illegal_salvage_group.draw(global_surf)
    ship_group.draw(global_surf)

    # If the version is old, draw text to warn of playback errors
    if log_parser.outdated_manifest:
        font = pygame.font.SysFont(pygame.font.get_default_font(), 24, True)
        text = f"The visualizer is a higher version number ({str(log_parser.v_cur)}) than the game being simulated ({str(log_parser.v_man)}). Playback Errors may occur."
        renderText = font.render(text, True, (255, 50, 50))
        global_surf.blit(renderText, (150, 10))

    # This is the turn counter
    font = pygame.font.SysFont(pygame.font.get_default_font(),24,True)
    text = ("Turn " + str(log_parser.tick - 1).rjust(6, "0"))
    renderText = font.render(text, True, (0, 155, 0))
    global_surf.blit(renderText, (10, 695))


def handle_events():
    for event in pygame.event.get():

        # if the application has been exited by the user
        if event.type == QUIT:
            pygame.quit()
            sys.exit()

        # handle key up events
        elif event.type == KEYUP:
            if event.key == K_p:
                # if p is pressed, toggle pause
                global pause
                pause = not pause
            if event.key == K_f:
                # if f is pressed, toggle fullscreen
                # No guarentee it works for windows.
                pygame.display.toggle_fullscreen()
            if event.key == K_ESCAPE:
                pygame.quit()
                sys.exit()
            if event.key == K_t:
                n = 3000
                show_station_stats_display("Stats Demo", {
                    "a": [math.sin(i/100)+1 for i in range(n)],
                    "b": [math.cos(i/100)+1 for i in range(n)],
                    "c": [math.cos(i/100 + math.pi)+1 for i in range(n)],
                    "d": [math.sin(i/100 + math.pi)+1 for i in range(n)],
                    "e": [math.pow(i/1000, 1/2)+1 for i in range(n)],
                    "f": [math.pow(1/2, i/100)+1 for i in range(n)],
                    "g": [(i/n)*2 for i in range(n)],
                    "h": [(1-(i/n))*2 for i in range(n)],
                }, global_surf, fpsClock)

            if event.key == K_s and team_name != None:
                ship = None
                for o in universe:
                    if o.object_type == ObjectType.ship and o.team_name == team_name:
                        ship = o
                        break

                if ship is not None:
                    show_ship_stats_display(ship, global_surf, fpsClock)

            if event.key == K_1 :
                stats = log_parser.get_stats()
                compiled = stat_utils.format_stats(stats, stat_utils.StatsTypes.primary_material_buy_by_station)

                show_station_stats_display("Primary Material Buy Price by Station", compiled, global_surf, fpsClock)

            if event.key == K_2:
                stats = log_parser.get_stats()
                compiled = stat_utils.format_stats(stats, stat_utils.StatsTypes.secondary_material_buy_by_station)

                show_station_stats_display("Secondary Material Buy Price by Station", compiled, global_surf, fpsClock)

            if event.key == K_3:
                stats = log_parser.get_stats()
                compiled = stat_utils.format_stats(stats, stat_utils.StatsTypes.material_sell_by_station)

                show_station_stats_display("Material Sell Price by Station",  compiled, global_surf, fpsClock)

            if event.key == K_4:
                stats = log_parser.get_stats()
                compiled = stat_utils.format_stats(stats, stat_utils.StatsTypes.material_buy_vs_sell)

                material_stats_selection_screen(compiled, global_surf, fpsClock)

            if event.key == K_5:
                stats = log_parser.get_stats()
                compiled = stat_utils.format_stats(stats, stat_utils.StatsTypes.material_production_vs_consumption)

                material_stats_selection_screen_2(compiled, global_surf, fpsClock)

            if event.key == K_o and pygame.key.get_mods() & pygame.KMOD_SHIFT:
                global debug
                debug = not debug

                if debug:
                    log("Logging Enabled")

            global _VIS_INTERMEDIATE_FRAMES
            global _FPS
            if event.key == K_UP and pygame.key.get_mods() & pygame.KMOD_SHIFT:
                _FPS = LOW_FPS
                _VIS_INTERMEDIATE_FRAMES = -1

            if event.key == K_DOWN and pygame.key.get_mods() & pygame.KMOD_SHIFT:
                _FPS = FPS
                _VIS_INTERMEDIATE_FRAMES = VIS_INTERMEDIATE_FRAMES

        elif event.type == MOUSEBUTTONUP:
            pos = event.pos

            ship = click_utils.get_ship_near_pos(pos, universe, first=True)
            station = click_utils.get_static_obj_near_pos(pos, first=True, obj_type=ObjectType.station)

            if ship is not None:
                show_ship_stats_display(ship, global_surf, fpsClock)

            elif station is not None:
                station_name = station["name"]

                stats = log_parser.get_stats()
                compiled = stat_utils.format_stats(stats, stat_utils.StatsTypes.station_stats)

                show_station_stats_display(f"{station_name} Statistics", compiled[station_name], global_surf, fpsClock)



def get_events_of_type(event_type, events):
    return [ event for event in events if event["type"] == event_type ]
