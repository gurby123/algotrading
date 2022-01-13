from ta.momentum import RSIIndicator
from ta.trend import MACD

import numpy as np
import pandas
from ta.volatility import BollingerBands

class Company:
    def __init__(self, symbol):
        self.symbol = symbol
        self.technical_indicators = None
        self.prices = None


def generate_buy_sell_signals(condition_buy, condition_sell, dataframe, strategy):
    last_signal = None
    indicators = []
    buy = []
    sell = []
    for i in range(0, len(dataframe)):
        # if buy condition is true and last signal was not Buy
        if condition_buy(i, dataframe) and last_signal != 'Buy':
            last_signal = 'Buy'
            indicators.append(last_signal)
            buy.append(dataframe['Close'].iloc[i])
            sell.append(np.nan)
        # if sell condition is true and last signal was Buy
        elif condition_sell(i, dataframe)  and last_signal == 'Buy':
            last_signal = 'Sell'
            indicators.append(last_signal)
            buy.append(np.nan)
            sell.append(dataframe['Close'].iloc[i])
        else:
            indicators.append(last_signal)
            buy.append(np.nan)
            sell.append(np.nan)

    dataframe[f'{strategy}_Last_Signal'] = np.array(last_signal)
    dataframe[f'{strategy}_Indicator'] = np.array(indicators)
    dataframe[f'{strategy}_Buy'] = np.array(buy)
    dataframe[f'{strategy}_Sell'] = np.array(sell)



def set_technical_indicators(config, company):
    company.technical_indicators = pandas.DataFrame()
    company.technical_indicators['Close'] = company.prices

    get_macd(config, company)
    get_rsi(config, company)
    get_bollinger_bands(config, company)


def get_macd(config, company):
    close_prices = company.prices
    dataframe = company.technical_indicators
    window_slow = 26
    signal = 9
    window_fast = 12
    macd = MACD(company.prices, window_slow, window_fast, signal)
    dataframe['MACD'] = macd.macd()
    dataframe['MACD_Histogram'] = macd.macd_diff()
    dataframe['MACD_Signal'] = macd.macd_signal()

    generate_buy_sell_signals(
        lambda x, dataframe: dataframe['MACD'].values[x] < dataframe['MACD_Signal'].iloc[x],
        lambda x, dataframe: dataframe['MACD'].values[x] > dataframe['MACD_Signal'].iloc[x],
        dataframe,
        'MACD')
    return dataframe


def get_rsi(config, company):
    close_prices = company.prices
    dataframe = company.technical_indicators
    rsi_time_period = 20

    rsi_indicator = RSIIndicator(close_prices, rsi_time_period)
    dataframe['RSI'] = rsi_indicator.rsi()

    low_rsi = 40
    high_rsi = 70

    generate_buy_sell_signals(
        lambda x, dataframe: dataframe['RSI'].values[x] < low_rsi,
        lambda x, dataframe: dataframe['RSI'].values[x] > high_rsi,
    dataframe, 'RSI')

    return dataframe


def get_bollinger_bands(config, company):

    close_prices = company.prices
    dataframe = company.technical_indicators

    window = 20

    indicator_bb = BollingerBands(close=close_prices, window=window, window_dev=2)

    # Add Bollinger Bands features
    dataframe['Bollinger_Bands_Middle'] = indicator_bb.bollinger_mavg()
    dataframe['Bollinger_Bands_Upper'] = indicator_bb.bollinger_hband()
    dataframe['Bollinger_Bands_Lower'] = indicator_bb.bollinger_lband()


    generate_buy_sell_signals(
        lambda x, signal: signal['Close'].values[x] < signal['Bollinger_Bands_Lower'].values[x],
        lambda x, signal: signal['Close'].values[x] > signal['Bollinger_Bands_Upper'].values[x],
        dataframe, 'Bollinger_Bands')

    return dataframe
