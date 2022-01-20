from QuantConnect.Data.UniverseSelection import *
import pandas as pd
import numpy as np

class EnhancedShortTermMeanReversionAlgorithm(QCAlgorithm):

    def Initialize(self):

        self.SetStartDate(2005, 1, 1)  #Set Start Date
        self.SetEndDate(2018, 1, 27)  #Set Start Date       
        self.SetCash(50000)            #Set Strategy Cash

        
        self.UniverseSettings.Resolution = Resolution.Daily
        self.AddUniverse(self.CoarseSelectionFunction, self.FineSelectionFunction)
        self.AddEquity("SPY", Resolution.Minute) 
        # rebalance the universe selection once a month
        self.rebalence_flag = 0
        # make sure to run the universe selection at the start of the algorithm even it's not the manth start
        self.first_month_trade_flag = 1
        self.trade_flag = 0  
        # Number of quantiles for sorting returns for mean reversion
        self.nq = 5
        # Number of quantiles for sorting volatility over five-day mean reversion period
        self.nq_vol = 3
        # the symbol list after the coarse and fine universe selection
        self.universe = None
        
        self.Schedule.On(self.DateRules.MonthStart("SPY"), self.TimeRules.At(0, 0), Action(self.monthly_rebalance))
        self.Schedule.On(self.DateRules.EveryDay("SPY"), self.TimeRules.BeforeMarketClose("SPY", 303), Action(self.get_prices))
        self.Schedule.On(self.DateRules.EveryDay("SPY"), self.TimeRules.BeforeMarketClose("SPY", 302), Action(self.daily_rebalance))
        self.Schedule.On(self.DateRules.EveryDay("SPY"), self.TimeRules.BeforeMarketClose("SPY", 301), Action(self.short))
        self.Schedule.On(self.DateRules.EveryDay("SPY"), self.TimeRules.BeforeMarketClose("SPY", 300), Action(self.long))
    
    def monthly_rebalance(self):
        # rebalance the universe every month
        self.rebalence_flag = 1
 
    def CoarseSelectionFunction(self, coarse):
        
        if self.rebalence_flag or self.first_month_trade_flag:
            # drop stocks which have no fundamental data or have too low prices
            selected = [x for x in coarse if (x.HasFundamentalData) and (float(x.Price) > 5)]
            # rank the stocks by dollar volume and choose the top 50
            filtered = sorted(selected, key=lambda x: x.DollarVolume, reverse=True) 

            return [ x.Symbol for x in filtered[:50]]
        else:
            return self.universe

    def FineSelectionFunction(self, fine):

        if self.rebalence_flag or self.first_month_trade_flag:
            # filter the stocks which have positive EV To EBITDA
            filtered_fine = [x for x in fine if x.ValuationRatios.EVToEBITDA > 0]
            self.universe = [x.Symbol for x in filtered_fine]
            
            self.rebalence_flag = 0
            self.first_month_trade_flag = 0
            self.trade_flag = 1
            
        return self.universe
        

    def OnData(self, data):
        pass
    
    def short(self):
        if self.universe is None: return
        SPY_Velocity = 0
        self.long_leverage = 0
        self.short_leverage = 0
        # request the history of benchmark
        pri = self.History(["SPY"], 200, Resolution.Daily)
        pos_one = (pri.loc["SPY"]['close'][-1])
        pos_six = (pri.loc["SPY"]['close'][-75:].mean())
        # calculate velocity of the benchmark 
        velocity_stop = (pos_one - pos_six)/100.0
        SPY_Velocity = velocity_stop
        if SPY_Velocity > 0.0:
            self.long_leverage = 1.8
            self.short_leverage = -0.0
        else:
            self.long_leverage = 1.1
            self.short_leverage = -0.7
        for symbol in self.shorts:
            if len(self.shorts) + self.existing_shorts == 0: return
            self.AddEquity(symbol, Resolution.Minute)
            self.SetHoldings(symbol, self.short_leverage/(len(self.shorts) + self.existing_shorts))                                
 
    def long(self):
        if self.universe is None: return
        for symbol in self.longs:
            if len(self.longs) + self.existing_longs == 0: return
            self.AddEquity(symbol, Resolution.Minute)
            self.SetHoldings(symbol, self.long_leverage/(len(self.longs) + self.existing_longs))                                
       
    def get_prices(self):
        if self.universe is None: return
        # Get the last 6 days of prices for every stock in our universe
        prices = {}
        hist = self.History(self.universe, 6, Resolution.Daily)
        for i in self.universe:
            if str(i) in hist.index.levels[0]:
                prices[i.Value] = hist.loc[str(i)]['close']
        df_prices = pd.DataFrame(prices, columns = prices.keys()) 
        # calculate the daily log return
        daily_rets = np.log(df_prices/df_prices.shift(1))
        # calculate the latest return but skip the most recent price
        rets = (df_prices.iloc[-2] - df_prices.iloc[0]) / df_prices.iloc[0]
        # standard deviation of the daily return
        stdevs = daily_rets.std(axis = 0)
        self.ret_qt = pd.qcut(rets, 5, labels=False) + 1
        self.stdev_qt = pd.qcut(stdevs, 3, labels=False) + 1
        self.longs = list((self.ret_qt[self.ret_qt == 1].index) & (self.stdev_qt[self.stdev_qt < 3].index))
        self.shorts = list((self.ret_qt[self.ret_qt == self.nq].index) & (self.stdev_qt[self.stdev_qt < 3].index))

 
    def daily_rebalance(self):
        # rebalance the position in portfolio every day           
        if self.universe is None: return
        self.existing_longs = 0
        self.existing_shorts = 0
       
        for symbol in self.Portfolio.Keys:
            if (symbol.Value != 'SPY') and (symbol.Value in self.ret_qt.index):
                current_quantile = self.ret_qt.loc[symbol.Value]
                if self.Portfolio[symbol].Quantity > 0:
                    if (current_quantile == 1) and (symbol not in self.longs):
                        self.existing_longs += 1
                    elif  (current_quantile > 1) and (symbol not in self.shorts): 
                        self.SetHoldings(symbol, 0)
                elif self.Portfolio[symbol].Quantity < 0:
                    if (current_quantile == self.nq) and (symbol not in self.shorts):
                        self.existing_shorts += 1
                    elif (current_quantile < self.nq) and (symbol not in self.longs): 
                        self.SetHoldings(symbol, 0)
