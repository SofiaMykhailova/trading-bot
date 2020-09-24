import asyncio
import time
from trading_engine import TradingEngine


''' You can trade many currency pairs at the same time.  Now bot works with two pairs : pair1 and pair2,
         but you can create as many pair as you need.
  
    Enter your details for each currency pair in the order shown in the example:

    CURRENCY_1 -  crypto currency(for example 'BTC')
    CURRENCY_2 - fiat currency(for example 'USD')
    ORDER_LIFE_TIME- how long to wait for a buy order to close
    STOCK_FEE - exchange commission(depends on your trading volume)
    CAN_SPEND - amount of money for buy orders
    PROFIT_MARKUP-  the profit you want to get(in example 0.001(0.1% of every deal))

    example:
    "pair1 = TradingEngine(CURRENCY_1='BTC', CURRENCY_2='USD', ORDER_LIFE_TIME=30,
                      STOCK_FEE=0.0036, AVG_PRICE_PERIOD=5, CAN_SPEND=100, PROFIT_MARKUP=0.001)"

    Good luck!
'''


# change None to your settings

pair1 = TradingEngine(CURRENCY_1=None, CURRENCY_2=None, ORDER_LIFE_TIME=None,
                      STOCK_FEE=None, CAN_SPEND=None, PROFIT_MARKUP=None)
pair2 = TradingEngine(CURRENCY_1=None, CURRENCY_2=None, ORDER_LIFE_TIME=None,
                      STOCK_FEE=None, CAN_SPEND=None, PROFIT_MARKUP=None)


pairs = (pair1, pair2)
for pair in pairs:
    pair.check_balance()
    print('finish checking')

Trades = []
async def trade(pair):
    while True:
        await asyncio.sleep(5)
        pair.trade()

for pair in pairs:
    task = trade(pair)
    Trades.append(task)


loop = asyncio.get_event_loop()
tasks = [loop.create_task(trade) for trade in Trades]
loop.run_until_complete(asyncio.wait(tasks))
