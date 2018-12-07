from game.common.enums import *

price_list = {}


def update_prices(universe):
    all_prices = {}
    for thing in universe:
        if thing.object_type is not ObjectType.station:
            continue
        station = thing

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


def get_material_price(universe, material):
    """
    Get the current highest available market price for the given material
    :param universe: the universe
    :param material: MaterialType material to get the price of
    :return: number value of the material
    """
    #TODO prevent multiple updates in one turn
    update_prices(universe)

    if material not in price_list:
        return None
    return price_list[material]
