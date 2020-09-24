import time
import sys

from exmo_client import call_api
from get_limits_exmo import get_min_quantity, get_price_precision, get_pair_settings


STOCK_TIME_OFFSET = 0


class ScriptError(Exception):
    pass


class ScriptQuitCondition(Exception):
    pass


class TradingEngine:
    def __init__(self, CURRENCY_1, CURRENCY_2, ORDER_LIFE_TIME, STOCK_FEE, AVG_PRICE_PERIOD, CAN_SPEND, PROFIT_MARKUP):
        self.CURRENCY_1 = CURRENCY_1
        self.CURRENCY_2 = CURRENCY_2
        self.CURRENT_PAIR = self.CURRENCY_1 + '_' + self.CURRENCY_2
        self.ORDER_LIFE_TIME = ORDER_LIFE_TIME
        self.STOCK_FEE = STOCK_FEE
        self.AVG_PRICE_PERIOD = AVG_PRICE_PERIOD
        self.CAN_SPEND = CAN_SPEND
        self.PROFIT_MARKUP = PROFIT_MARKUP
        pairs = get_pair_settings(self.CURRENT_PAIR)
        self.CURRENCY_1_MIN_QUANTITY = pairs.min_quantity
        self.CURRENCY_1_MIN_QUANTITY = pairs.price_precision

    def check_balance(self):
        try:
            balances = call_api('user_info')['balances']
            alt_balance = float(balances[self.CURRENCY_1])

            profit = (self.CAN_SPEND*(1+self.STOCK_FEE) +
                           self.CAN_SPEND * self.PROFIT_MARKUP) / (1 - self.STOCK_FEE)

            if float(balances[self.CURRENCY_1]) > 0:
                decision = input("""
                    You have {amount: 0.8f} {curr1} on your balance.
                     Do you really want to sell all this at {rate: 0.8f} and get {wanna_get: 0.8f} {curr2}?
                    Input Yes or No
                """.format(
                    amount=alt_balance,
                    curr1=self.CURRENCY_1,
                    curr2=self.CURRENCY_2,
                    wanna_get=profit,
                    rate=profit/alt_balance
                ))
                if decision.lower() == 'yes':
                    print('Lets sell your currency!')
                if decision in ('No','no'):
                    print(f'Please transfer {self.CURRENCY_1} to another wallet or use in other transactions')
                    sys.exit(0)
                else:
                    raise ScriptError('Input is incorrect!!')
        except Exception as e:
            print(str(e))

    def check_current_sell_orders(self, opened_orders):
        buy_orders = []
        for order in opened_orders:
            if order['type'] == 'buy':
                buy_orders.append(order)
                return buy_orders
            else:
                raise ScriptQuitCondition(self.CURRENT_PAIR,
                    'Please,wait until ALL sell orders are executed')

    def check_current_buy_orders(self, buy_orders):
        for order in buy_orders:
            print(self.CURRENT_PAIR,'Checking the status of a buy order', order['order_id'])
            try:
                order_history = call_api(
                    'order_trades', order_id=order['order_id'])
                raise ScriptQuitCondition(self.CURRENT_PAIR,
                    'Buy  order has already been partially completed; must wait until complete closure')
            except ScriptError as error_massage:
                if 'Error 50304' in str(error_massage):
                    print(self.CURRENT_PAIR,'There are no partially executed orders')
                    time_passed = time.time() + STOCK_TIME_OFFSET*60 * \
                        60 - int(order['created'])
                    if time_passed > self.ORDER_LIFE_TIME * 60:
                        call_api('order_cancel', order_id=order['order_id'])
                        raise ScriptQuitCondition(self.CURRENT_PAIR,
                            f'Cancellation of an unexecuted order for {str(self.CURRENCY_1)} after {str(self.ORDER_LIFE_TIME)} minutes of waiting')
                    else:
                        raise ScriptQuitCondition(self.CURRENT_PAIR,
                            f'{str(time_passed)} second passed, waiting for  order execution')
                else:
                    raise ScriptQuitCondition(str(error_massage))

    def create_sell_order(self, balances):
        will_get = self.CAN_SPEND + self.CAN_SPEND * \
            (self.STOCK_FEE+self.PROFIT_MARKUP)
        print('sell', balances[self.CURRENCY_1], will_get,
              (will_get/float(balances[self.CURRENCY_1])))
        new_order = call_api(
            'order_create',
            pair=self.CURRENT_PAIR,
            quantity=balances[self.CURRENCY_1],
            price="{price:0.{prec}f}".format(
                prec=self.PRICE_PRECISION,
                price=will_get/float(balances[self.CURRENCY_1])),
            type='sell'
        )
        print(new_order)
        print('f {self.CURRENCY_1} Sell order created',
              self.CURRENCY_1, new_order['order_id'])

    def create_buy_order(self, balances):
        if float(balances[self.CURRENCY_2]) >= self.CAN_SPEND:
            last_deals = call_api('trades', pair=self.CURRENT_PAIR)
            prices = []
            for deal in last_deals[self.CURRENT_PAIR]:
                time_passed = time.time() + STOCK_TIME_OFFSET * \
                    60*60 - int(deal['date'])
                if time_passed < self.AVG_PRICE_PERIOD*60:
                    prices.append(float(deal['price']))
            try:
                avg_price = sum(prices)/len(prices)
                my_need_price = avg_price - \
                    avg_price * (self.STOCK_FEE+self.PROFIT_MARKUP)
                my_amount = self.CAN_SPEND/my_need_price

                print('buy', my_amount, my_need_price)
                if my_amount >= self.CURRENCY_1_MIN_QUANTITY:
                    new_order = call_api(
                        'order_create',
                        pair=self.CURRENT_PAIR,
                        quantity=my_amount,
                        price="{price:0.{prec}f}".format(
                        prec=self.PRICE_PRECISION, 
                        price=my_need_price),
                        type='buy'
                    )
                    print('Buy order created', new_order['order_id'])

                else:  # мы можем купить слишком мало на нашу сумму
                    raise ScriptQuitCondition(
                        f'the amount for trades {self.CAN_SPEND} is less than the minimum allowed by the exchange')
            except ZeroDivisionError:
                print('Can not calculate the average price' , prices)
        else:
            raise ScriptQuitCondition(self.CURRENT_PAIR,'Currency amount is less than the minimum quantity')

    def trade(self):

        try:

            buy_orders = []
            opened_orders = []
            try:
                opened_orders = call_api('user_open_orders')[
                    self.CURRENCY_1 + '_' + self.CURRENCY_2]
            except KeyError:
                print('There are no open orders')

            # 1 def get_open_orders_list(self):
            self.check_current_sell_orders(opened_orders)
            if buy_orders:
                self.check_current_buy_orders(buy_orders)
            else:
                balances = call_api('user_info')['balances']
                if float(balances[self.CURRENCY_1]) >= self.CURRENCY_1_MIN_QUANTITY:
                    self.create_sell_order(balances)
                else:
                    self.create_buy_order(balances)
        except ScriptError as error:
            print(error)
        except ScriptQuitCondition as error:
            print(error)
        except Exception as outside_exception:
            print(outside_exception)
