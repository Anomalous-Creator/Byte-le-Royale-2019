import math
from itertools import groupby
from game.utils.filters import in_radius as pred_in_radius
from game.utils.filters import AND, EQ, NOT
import types

from game.config import *
from game.common.enums import *
from game.utils.material_price_finder import *


def get_ships(universe, callback=None):

    if callback is not None:
        return [obj
                for obj in universe.get("ships")
                if obj.is_alive()
                and callback(obj)]

    return [obj
            for obj in universe.get("ships")
            if obj.is_alive()]


def ships_in_attack_range(universe, ship):
    def is_visible_wrapper(t):
        return in_radius(ship, t, ship.weapon_range, lambda e: e.position, verify_instance=True)
    return get_ships(universe, is_visible_wrapper)


def get_stations(universe):
    return [ obj for obj in universe if obj.object_type == ObjectType.station ]


def get_asteroid_fields(universe):
    return [obj
            for obj in universe
            if obj.object_type in [
                ObjectType.cuprite_field,
                ObjectType.goethite_field,
                ObjectType.gold_field]]


def distance_to(source, target, accessor, target_accessor=None):
    """
    Params:
    - source: the source object that you wish to start from
    - target: the target you wish to determine the distance to
    - accessor: an accessor method used to get the position of the source. if target_accessor == None, this will be applied to the target.
    - target_accessor: an accessor method used to get the position of the target. Default: None.
    """

    source_pos = accessor(source)
    if target_accessor:
        target_pos = target_accessor(target)
    else:
        target_pos = accessor(target)

    return (
        (source_pos[0] - target_pos[0])**2 +
        (source_pos[1] - target_pos[1])**2
    )**(1/2)


def in_radius(source, target, radius, accessor, target_accessor=None, verify_instance=True):
    """
    Params:
    - source: the source object that you want to search a radius around
    - target: the target object you wish to see if it lies in a radius around the source
    - radius: either an integer, float or accessor function that takes the source and the target and returns an integer or float.
    - accessor: an accessor method used to get the position of the source. If target_accessor == None, this will also be applied to the target.
    - target_accessor: an accessor method used to get the position of the target. Default: None.
    - verify_instance: Verify that source and target do not have the same id.
    """
    source_pos = accessor(source)
    if target_accessor:
        target_pos = target_accessor(target)
    else:
        target_pos = accessor(target)

    result = (source_pos[0] - target_pos[0])**2 + (source_pos[1] - target_pos[1])**2

    if isinstance(radius, types.FunctionType):
        radius = radius(source, target)

    in_range = result < radius**2

    if verify_instance:
        return in_range and source.id != target.id
    else:
        return in_range


def convert_material_to_scrap(universe, material, amount):
    """
    Params:
    :param universe: the universe
    :param material: MaterialType enum of material to convert
    :param amount: number amount of the material given
    :return: integer amount of how many scrap should be created
    """
    value = get_material_price(universe, material)
    return math.ceil(amount * value * 0.25)


def in_secure_zone(source, accessor):
    """
    Params:
    - The object you wish to check if it's position == within the save zone

    """

    center_of_world = (
        WORLD_BOUNDS[0]/2.0,
        WORLD_BOUNDS[1]/2.0
    )

    return in_radius(source, center_of_world, SECURE_ZONE_RADIUS, accessor, target_accessor=lambda e: e)


def get_material_name(material_type):
    material_type = int(material_type)
    if material_type == MaterialType.circuitry:
        return "Circuitry"
    elif material_type == MaterialType.computers:
        return "Computers"
    elif material_type == MaterialType.copper:
        return "Copper"
    elif material_type == MaterialType.cuprite:
        return "Cuprite"
    elif material_type == MaterialType.drones:
        return "Drones"
    elif material_type == MaterialType.goethite:
        return "Goethite"
    elif material_type == MaterialType.gold:
        return "Gold"
    elif material_type == MaterialType.iron:
        return "Iron"
    elif material_type == MaterialType.machinery:
        return "Machinery"
    elif material_type == MaterialType.pylons:
        return "Pylons"
    elif material_type == MaterialType.steel:
        return "Steel"
    elif material_type == MaterialType.weaponry:
        return "Weaponry"
    elif material_type == MaterialType.wire:
        return "Wire"
    return "N/A"

def separate_universe(flat_universe):

    universe = {}

    for key, group in groupby(flat_universe, lambda e: e.object_type):
        if key not in universe:
            universe[key] = []
        universe[key].extend(list(group))

    return universe


def get_mateiral_prices(universe):
    price_list = {}
    all_prices = {}
    for station in universe.get(ObjectType.station):
        if station.primary_import is not None:
            if station.primary_import not in all_prices:
                all_prices[station.primary_import] = []
            all_prices[station.primary_import].append(station.primary_buy_price)

        if station.secondary_import is not None:
            if station.secondary_import not in all_prices:
                all_prices[station.secondary_import] = []
            all_prices[station.secondary_import].append(station.secondary_buy_price)

    for material, prices in all_prices.items():
        if material not in price_list:
            price_list[material] = 0
        price_list[material] = max(prices)

    return price_list


