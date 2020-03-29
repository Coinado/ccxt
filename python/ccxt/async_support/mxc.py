# -*- coding: utf-8 -*-

# PLEASE DO NOT EDIT THIS FILE, IT IS GENERATED AND WILL BE OVERWRITTEN:
# https://github.com/ccxt/ccxt/blob/master/CONTRIBUTING.md#how-to-contribute-code

from ccxt.async_support.base.exchange import Exchange
import math
from ccxt.base.errors import ExchangeError
from ccxt.base.errors import ArgumentsRequired


class mxc(Exchange):

    def describe(self):
        return self.deep_extend(super(mxc, self).describe(), {
            'id': 'mxc',
            'name': 'MXC',
            'countries': ['CN'],
            'version': 'v1',
            'rateLimit': 1000,
            'has': {
                'CORS': False,
                'createMarketOrder': False,
                'fetchTickers': True,
                'withdraw': False,
                'fetchDeposits': False,
                'fetchWithdrawals': False,
                'fetchTransactions': False,
                'createDepositAddress': False,
                'fetchDepositAddress': False,
                'fetchClosedOrders': False,
                'fetchOHLCV': True,
                'fetchOpenOrders': False,
                'fetchOrderTrades': False,
                'fetchOrders': True,
                'fetchOrder': True,
                'fetchMyTrades': False,
            },
            'timeframes': {
                '1m': '60',
                '5m': '300',
                '15m': '900',
                '30m': '1800',
                '60m': '3600',
                '1h': '3600',
                '2h': '7200',
                '4h': '14400',
                '6h': '21600',
                '12h': '43200',
                '1d': '86400',
                '1w': '604800',
            },
            'urls': {
                'logo': '',
                'api': {
                    'public': 'https://www.mxc.ceo/open/api/v1/data/',
                    'private': 'https://www.mxc.ceo/open/api/v1/private/',
                },
                'www': 'https://mxc.ceo/',
                'doc': 'https://github.com/mxcdevelop/APIDoc',
                'fees': [
                    'https://www.mxc.ceo/info/fee',
                ],
                'referral': '',
            },
            'api': {
                'public': {
                    'get': [
                        'markets',
                        'markets_info',
                        'depth',
                        'history',
                        'ticker',
                        'kline',
                    ],
                },
                'private': {
                    'get': [
                        'account/info',
                        'current/orders',
                        'orders',
                        'order',
                    ],
                    'post': [
                        'order',
                        'order_batch',
                        'order_cancel',
                    ],
                    'delete': [
                        'order',
                    ],
                },
            },
            'fees': {
                'trading': {
                    'tierBased': True,
                    'percentage': True,
                    'maker': 0.002,
                    'taker': 0.002,
                },
            },
            'exceptions': {
            },
            # https://gate.io/api2#errCode
            'errorCodeNames': {
            },
            'options': {
                'limits': {
                    'cost': {
                        'min': {
                            'BTC': 0.0001,
                            'ETH': 0.001,
                            'USDT': 1,
                        },
                    },
                },
            },
        })

    async def fetch_markets(self, params={}):
        response = await self.publicGetMarketsInfo(params)
        markets = self.safe_value(response, 'data')
        if not markets:
            raise ExchangeError(self.id + ' fetchMarkets got an unrecognized response')
        result = []
        keys = list(markets.keys())
        for i in range(0, len(keys)):
            id = keys[i]
            market = markets[id]
            details = market
            # all of their symbols are separated with an underscore
            # but not boe_eth_eth(BOE_ETH/ETH) which has two underscores
            # https://github.com/ccxt/ccxt/issues/4894
            parts = id.split('_')
            numParts = len(parts)
            baseId = parts[0]
            quoteId = parts[1]
            if numParts > 2:
                baseId = parts[0] + '_' + parts[1]
                quoteId = parts[2]
            base = self.safe_currency_code(baseId)
            quote = self.safe_currency_code(quoteId)
            symbol = base + '/' + quote
            precision = {
                'amount': 8,
                'price': details['priceScale'],
            }
            amountLimits = {
                'min': details['minAmount'],
                'max': None,
            }
            priceLimits = {
                'min': math.pow(10, -details['priceScale']),
                'max': None,
            }
            defaultCost = amountLimits['min'] * priceLimits['min']
            minCost = self.safe_float(self.options['limits']['cost']['min'], quote, defaultCost)
            costLimits = {
                'min': minCost,
                'max': None,
            }
            limits = {
                'amount': amountLimits,
                'price': priceLimits,
                'cost': costLimits,
            }
            active = True
            result.append({
                'id': id,
                'symbol': symbol,
                'base': base,
                'quote': quote,
                'baseId': baseId,
                'quoteId': quoteId,
                'info': market,
                'active': active,
                'maker': details['sellFeeRate'],
                'taker': details['buyFeeRate'],
                'precision': precision,
                'limits': limits,
            })
        return result

    async def fetch_balance(self, params={}):
        await self.load_markets()
        request = {
            'api_key': self.apiKey,
            'req_time': self.milliseconds(),
        }
        response = await self.privateGetAccountInfo(self.extend(request, params))
        result = {'info': response}
        currencyIds = list(response.keys())
        for i in range(0, len(currencyIds)):
            currencyId = currencyIds[i]
            code = self.safe_currency_code(currencyId)
            account = self.account()
            account['free'] = self.safe_float(response[currencyId], 'available')
            account['used'] = self.safe_float(response[currencyId], 'frozen')
            result[code] = account
        return self.parse_balance(result)

    async def fetch_order_book(self, symbol, limit=None, params={}):
        await self.load_markets()
        request = {
            'depth': 5,
            'market': self.market_id(symbol),
        }
        response = await self.publicGetDepth(self.extend(request, params))
        orderbook = self.safe_value(response, 'data')
        return self.parse_order_book(orderbook, None, 'bids', 'asks', 'price', 'quantity')

    def parse_ohlcv(self, ohlcv, market=None, timeframe='1m', since=None, limit=None):
        # they return [Timestamp, Volume, Close, High, Low, Open]
        return [
            int(ohlcv[0]),   # t
            float(ohlcv[1]),  # o
            float(ohlcv[2]),  # c
            float(ohlcv[3]),  # h
            float(ohlcv[4]),  # l
            float(ohlcv[5]),  # v
        ]

    async def fetch_ohlcv(self, symbol, timeframe='1m', since=None, limit=None, params={}):
        await self.load_markets()
        market = self.market(symbol)
        now = self.milliseconds()
        periodDurationInSeconds = self.parse_timeframe(timeframe)
        request = {
            'market': self.market_id(symbol),
            'interval': timeframe,
            'startTime': int(now - periodDurationInSeconds / 1000),
        }
        # max limit = 1001
        if limit is not None:
            hours = int((periodDurationInSeconds * limit) / 3600)
            request['range_hour'] = max(0, hours - 1)
        if since is not None:
            request['startTime'] = int(since / 1000)
        response = await self.publicGetKline(self.extend(request, params))
        #        ordering: Ts, O, C, H, L, V
        #     {
        #         "code": 200,
        #         "data": [
        #             ["TS", "o", "c", "h", "l", "v"],
        #         ]
        #     }
        #
        data = self.safe_value(response, 'data', [])
        return self.parse_ohlcvs(data, market, timeframe, since, limit)

    def parse_ticker(self, ticker, market=None):
        timestamp = self.milliseconds()
        symbol = None
        if market:
            symbol = market['symbol']
        last = self.safe_float(ticker, 'last')
        percentage = self.safe_float(ticker, 'percentChange')
        open = self.safe_float(ticker, 'open')
        change = None
        average = None
        if (last is not None) and (percentage is not None):
            change = last - open
            average = self.sum(last, open) / 2
        return {
            'symbol': symbol,
            'timestamp': timestamp,
            'datetime': self.iso8601(timestamp),
            'high': self.safe_float(ticker, 'high'),
            'low': self.safe_float(ticker, 'low'),
            'bid': self.safe_float(ticker, 'buy'),
            'bidVolume': None,
            'ask': self.safe_float(ticker, 'sell'),
            'askVolume': None,
            'vwap': None,
            'open': open,
            'close': last,
            'last': last,
            'previousClose': None,
            'change': change,
            'percentage': percentage,
            'average': average,
            'baseVolume': self.safe_float(ticker, 'volume'),  # gateio has them reversed
            'quoteVolume': None,
            'info': ticker,
        }

    async def fetch_tickers(self, symbols=None, params={}):
        await self.load_markets()
        response = await self.publicGetTicker(params)
        result = {}
        data = self.safe_value(response, 'data', [])
        ids = list(data.keys())
        for i in range(0, len(ids)):
            id = ids[i]
            baseId, quoteId = id.split('_')
            base = baseId.upper()
            quote = quoteId.upper()
            base = self.safe_currency_code(base)
            quote = self.safe_currency_code(quote)
            symbol = base + '/' + quote
            market = None
            if symbol in self.markets:
                market = self.markets[symbol]
            if id in self.markets_by_id:
                market = self.markets_by_id[id]
            result[symbol] = self.parse_ticker(data[id], market)
        return result

    async def fetch_ticker(self, symbol, params={}):
        await self.load_markets()
        market = self.market(symbol)
        ticker = await self.publicGetTicker(self.extend({
            'market': self.market_id(symbol),
        }, params))
        return self.parse_ticker(ticker, market)

    def parse_trade(self, trade, market=None):
        dateStr = self.safe_value(trade, 'tradeTime')
        timestamp = None
        if dateStr is not None:
            timestamp = self.parse_date(dateStr + '  GMT+8')
        # take either of orderid or orderId
        price = self.safe_float(trade, 'tradePrice')
        amount = self.safe_float(trade, 'tradeQuantity')
        type = self.safe_string(trade, 'tradeType')
        cost = None
        if price is not None:
            if amount is not None:
                cost = price * amount
        symbol = None
        if market is not None:
            symbol = market['symbol']
        return {
            'id': None,
            'info': trade,
            'timestamp': timestamp,
            'datetime': self.iso8601(timestamp),
            'symbol': symbol,
            'order': None,
            'type': None,
            'side': type == 'buy' if '1' else 'sell',
            'takerOrMaker': None,
            'price': price,
            'amount': amount,
            'cost': cost,
            'fee': None,
        }

    async def fetch_trades(self, symbol, since=None, limit=None, params={}):
        await self.load_markets()
        market = self.market(symbol)
        request = {
            'market': self.market_id(symbol),
        }
        response = await self.publicGetHistory(self.extend(request, params))
        return self.parse_trades(response['data'], market, since, limit)

    async def fetch_orders(self, symbol=None, since=None, limit=None, params={}):
        request = {
            'api_key': self.apiKey,
            'req_time': self.milliseconds(),
        }
        response = await self.privateGetCurrentOrders(self.extend(request, params))
        return self.parse_orders(response['data'], None, since, limit)

    async def fetch_order(self, id, symbol=None, params={}):
        await self.load_markets()
        request = {
            'trade_no': id,
            'market': self.market_id(symbol),
            'api_key': self.apiKey,
            'req_time': self.milliseconds(),
        }
        response = await self.privateGetOrder(self.extend(request, params))
        return self.parse_order(response['data'])

    def parse_order_side(self, side):
        sides = {
            '1': 'buy',
            '2': 'sell',
        }
        return self.safe_string(sides, side, side)

    def parse_order_status(self, status):
        statuses = {
            '1': 'open',
            '2': 'closed',
            '3': 'open',  # partial closed
            '4': 'canceled',  # partial closed
            '5': 'canceled',  # partial canceled
        }
        return self.safe_string(statuses, status, status)

    def parse_order(self, order, market=None):
        # Different API endpoints returns order info in different format...
        # with different fields filled.
        id = self.safe_string(order, 'id')
        if id is None:
            id = self.safe_string(order, 'data')
        symbol = None
        marketId = self.safe_string(order, 'market')
        if marketId in self.markets_by_id:
            market = self.markets_by_id[marketId]
        if market is not None:
            symbol = market['symbol']
        dateStr = self.safe_string(order, 'createTime')
        # XXX: MXC returns order creation times in GMT+8 timezone with out specifying it
        #  hence appending ' GMT+8' to it so we can get the correct value
        # XXX: Also MXC api does not return actual matched prices and costs/fees
        timestamp = None
        if dateStr is not None:
            timestamp = self.parse_date(dateStr + '  GMT+8')
        status = self.parse_order_status(self.safe_string(order, 'status'))
        side = self.parse_order_side(self.safe_string(order, 'type'))
        price = self.safe_float(order, 'price')
        amount = self.safe_float(order, 'totalQuantity')
        if amount is None:
            amount = self.safe_float(order, 'initialAmount')
        filled = self.safe_float(order, 'tradedQuantity')
        average = None
        remaining = None
        if (filled is not None) and (amount is not None):
            remaining = amount - filled
        return {
            'id': id,
            'datetime': self.iso8601(timestamp),
            'timestamp': timestamp,
            'status': status,
            'symbol': symbol,
            'type': 'limit',
            'side': side,
            'price': price,
            'cost': None,
            'amount': amount,
            'filled': filled,
            'remaining': remaining,
            'average': average,
            'trades': None,
            'fee': {
                'cost': None,
                'currency': None,
                'rate': None,
            },
            'info': order,
        }

    async def create_order(self, symbol, type, side, amount, price=None, params={}):
        if type == 'market':
            raise ExchangeError(self.id + ' allows limit orders only')
        await self.load_markets()
        market = self.market(symbol)
        request = {
            'api_key': self.apiKey,
            'req_time': self.milliseconds(),
            'market': self.market_id(symbol),
            'price': price,
            'quantity': amount,
            'trade_type': '1' if (side == 'buy') else '2',
        }
        response = await self.privatePostOrder(self.extend(request, params))
        return self.parse_order(self.extend({
            'status': 'open',
            'type': side,
            'initialAmount': amount,
        }, response), market)

    async def cancel_order(self, id, symbol=None, params={}):
        if symbol is None:
            raise ArgumentsRequired(self.id + ' cancelOrder requires symbol argument')
        await self.load_markets()
        request = {
            'api_key': self.apiKey,
            'req_time': self.milliseconds(),
            'market': self.market_id(symbol),
            'trade_no': id,
        }
        return await self.privateDeleteOrder(self.extend(request, params))

    def sign(self, path, api='public', method='GET', params={}, headers=None, body=None):
        url = self.urls['api'][api] + self.implode_params(path, params)
        query = self.omit(params, self.extract_params(path))
        if api == 'public':
            if query:
                url += '?' + self.urlencode(query)
        else:
            self.check_required_credentials()
            auth = self.rawencode(self.keysort(query))
            signature = self.hash(self.encode(auth + '&api_secret=' + self.secret), 'md5')
            suffix = 'sign=' + signature
            url += '?' + auth + '&' + suffix
        return {'url': url, 'method': method, 'body': body, 'headers': headers}

    def handle_errors(self, code, reason, url, method, headers, body, response, requestHeaders, requestBody):
        if response is None:
            return
        resultString = self.safe_string(response, 'result', '')
        if resultString != 'false':
            return
        errorCode = self.safe_string(response, 'code')
        message = self.safe_string(response, 'message', body)
        if errorCode is not None:
            feedback = self.safe_string(self.errorCodeNames, errorCode, message)
            self.throw_exactly_matched_exception(self.exceptions['exact'], errorCode, feedback)
