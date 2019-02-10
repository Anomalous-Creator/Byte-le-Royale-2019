# Trading

Trading is the most common way to make money. By buying and selling resources for profit, you will make a name for yourself and be a master of your trade.

## How to Trade

Trading is accomplished by entering the range of a station and using the `buy material` or `sell material` action.

## Buying

When you buy items, you specify the amount of the station's production you want to buy.
Then, the following conditions are checked:
* buying more than the station possesses - will buy available amount
* buying more than you can afford - will buy as much as you can afford
* buying more than your ship can hold - will buy as much as you can hold
* if 2 or more players both try to buy a combined total more than store has in stock,
  each player will purchase (total amount / `n`) rounded up, where `n` is the number of players buying.


## Selling

When you sell items, you specify the item you wish to sell in the first parameter, and the amount in the second one.
Then, the following conditions are checked:
* selling more than the station can hold - will sell available amount
* selling more than you possess - will sell what you have in cargo
* if 2 or more players both try to sell a combined total more than store has in stock,
  each player will sell (total amount / `n`) rounded up, where `n` is the number of players selling.


## Related Items

[Mining](asteroid_fields_and_mining.html)