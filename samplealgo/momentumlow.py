"""
SEL(stock selection part)
Based on the 'Momentum Strategy with Market Cap and EV/EBITDA' strategy introduced by Jing Wu, 6 Feb 2018
adapted and recoded by Jack Simonson, Goldie Yalamanchi, Vladimir, and Peter Guenther
https://www.quantconnect.com/forum/discussion/3377/momentum-strategy-with-market-cap-and-ev-ebitda/p1
https://www.quantconnect.com/forum/discussion/9678/quality-companies-in-an-uptrend/p1
https://www.quantconnect.com/forum/discussion/9632/amazing-returns-superior-stock-selection-strategy-superior-in-amp-out-strategy/p1

I/O(in & out part)
Based on the 'In & Out' strategy introduced by Peter Guenther, 4 Oct 2020
expanded/inspired by Tentor Testivis, Dan Whitnable (Quantopian), Vladimir, Thomas Chang, 
Mateusz Pulka, Derek Melchin (QuantConnect), Nathan Swenson, Goldie Yalamanchi, and Sudip Sil
https://www.quantopian.com/posts/new-strategy-in-and-out
https://www.quantconnect.com/forum/discussion/9597/the-in-amp-out-strategy-continued-from-quantopian/p1
code version: In_out_flex_v5_disambiguate_v2
"""

from QuantConnect.Data.UniverseSelection import *
import math
import numpy as np
import pandas as pd
import scipy as sp

class EarningsFactor_InOut(QCAlgorithm):

    def Initialize(self):

        self.SetStartDate(2019, 1, 1)  #Set Start Date
        #self.SetEndDate(2021, 12, 31)  #Set End Date
        self.cap = 100000
        self.SetCash(self.cap)
        
        res = Resolution.Minute
        
        # Holdings
        ### 'Out' holdings and weights
        self.BND1 = self.AddEquity('TLT', res).Symbol #TLT; TMF for 3xlev
        self.HLD_OUT = {self.BND1: 1}
        ### 'In' holdings and weights (static stock selection strategy)
        ##### These are determined flexibly via sorting on fundamentals
        
        ##### In & Out parameters #####
        # Feed-in constants
        self.INI_WAIT_DAYS = 15  # out for 3 trading weeks
        
        # Market and list of signals based on ETFs
        self.MRKT = self.AddEquity('SPY', res).Symbol  # market
        self.PRDC = self.AddEquity('XLI', res).Symbol  # production (industrials)
        self.METL = self.AddEquity('DBB', res).Symbol  # input prices (metals)
        self.NRES = self.AddEquity('IGE', res).Symbol  # input prices (natural res)
        self.DEBT = self.AddEquity('SHY', res).Symbol  # cost of debt (bond yield)
        self.USDX = self.AddEquity('UUP', res).Symbol  # safe haven (USD)
        self.GOLD = self.AddEquity('GLD', res).Symbol  # gold
        self.SLVA = self.AddEquity('SLV', res).Symbol  # vs silver
        self.INFL = self.AddEquity('RINF', res).Symbol  # disambiguate GPLD/SLVA pair via inflaction expectations
        self.UTIL = self.AddEquity('XLU', res).Symbol  # utilities
        self.INDU = self.PRDC  # vs industrials
        self.SHCU = self.AddEquity('FXF', res).Symbol  # safe haven currency (CHF)
        self.RICU = self.AddEquity('FXA', res).Symbol  # vs risk currency (AUD)

        self.FORPAIRS = [self.GOLD, self.SLVA, self.UTIL, self.SHCU, self.RICU]
        self.SIGNALS = [self.PRDC, self.METL, self.NRES, self.DEBT, self.USDX, self.INFL]
        self.pairlist = ['G_S', 'U_I', 'C_A']

        # Initialize variables
        ## 'In'/'out' indicator
        self.be_in = 999 #initially, set to an arbitrary value different from 1 (in) and 0 (out)
        self.be_in_prior = 999
        ## Day count variables
        self.dcount = 0  # count of total days since start
        self.outday = 0  # dcount when self.be_in=0
        ## Flexi wait days
        self.WDadjvar = self.INI_WAIT_DAYS
        
        # set a warm-up period to initialize the indicator
        self.SetWarmUp(timedelta(350))
        
        ##### Momentum & fundamentals strategy parameters #####
        #self.UniverseSettings.Resolution = Resolution.Daily
        self.UniverseSettings.Resolution = Resolution.Minute
        self.AddUniverse(self.UniverseCoarseFilter, self.UniverseFundamentalsFilter)
        self.num_screener = 100
        self.num_stocks = 10
        self.formation_days = 70
        self.lowmom = False
        self.data = {}
        
        # rebalance the universe selection once a month
        self.rebalance_flag = 0
        # make sure to run the universe selection at the start of the algorithm even if it's not the month start
        self.flip_flag = 0
        self.first_month_trade_flag = 1
        self.trade_flag = 0 
        self.symbols = None
        self.month = -1
        self.reb_count = 0
        
        self.Schedule.On(
            self.DateRules.EveryDay(),
            self.TimeRules.AfterMarketOpen('SPY', 120),
            self.rebalance_when_out_of_the_market
        )
        
        self.Schedule.On(
            self.DateRules.EveryDay(), 
            self.TimeRules.BeforeMarketClose('SPY', 0), 
            self.record_vars
        )  
        
        # Setup daily consolidation
        symbols = self.SIGNALS + [self.MRKT] + self.FORPAIRS
        for symbol in symbols:
            self.consolidator = TradeBarConsolidator(timedelta(days=1))
            self.consolidator.DataConsolidated += self.consolidation_handler
            self.SubscriptionManager.AddConsolidator(symbol, self.consolidator)
        
        # Warm up history
        self.lookback = 252
        self.history = self.History(symbols, self.lookback, Resolution.Daily)
        if self.history.empty or 'close' not in self.history.columns:
            return
        self.history = self.history['close'].unstack(level=0).dropna()
        self.update_history_shift()
        
        # Benchmark = record SPY
        self.spy = []

 
    def UniverseCoarseFilter(self, coarse):
        #self.Debug(str(self.Time) + "UniverseCoarseFilter: be_in:" + str(self.be_in) + " flip_flag:" + str(self.flip_flag))
        #if (self.rebalance_flag or self.first_month_trade_flag) and (self.be_in or self.flip_flag):
        if self.month == self.Time.month:
            return Universe.Unchanged
            
        self.month = self.Time.month
            # drop stocks which have no fundamental data or have too low prices
        selected = [x for x in coarse if (x.HasFundamentalData) and (float(x.Price) > 5)]
            # rank the stocks by dollar volume 
        filtered = sorted(selected, key=lambda x: x.DollarVolume, reverse=True)
        return [x.Symbol for x in filtered[:200]]
        #else:
        #    return self.symbols


    def UniverseFundamentalsFilter(self, fundamental):
        #self.Debug(str(self.Time) + "UniverseFundamentalsFilter: be_in:" + str(self.be_in) + " flip_flag:" + str(self.flip_flag))
        #if (self.rebalance_flag or self.first_month_trade_flag) and (self.be_in or self.flip_flag):
            #hist = self.History([i.Symbol for i in fundamental], 1, Resolution.Daily)
        try:
            filtered_fundamental = [x for x in fundamental if (x.ValuationRatios.EVToEBITDA > 0) 
                                                    and (x.EarningReports.BasicAverageShares.ThreeMonths > 0) 
                                                    and float(x.EarningReports.BasicAverageShares.ThreeMonths) * x.Price > 2e9]
                                                    #and float(x.EarningReports.BasicAverageShares.ThreeMonths) * hist.loc[str(x.Symbol)]['close'][0] > 2e9]
                                                    #and x.EarningReports.BasicAverageShares.ThreeMonths * (x.EarningReports.BasicEPS.TwelveMonths*x.ValuationRatios.PERatio) > 2e9]
        except:
            filtered_fundamental = [x for x in fundamental if (x.ValuationRatios.EVToEBITDA > 0) 
                                                and (x.EarningReports.BasicAverageShares.ThreeMonths > 0)] 

        top = sorted(filtered_fundamental, key = lambda x: x.ValuationRatios.EVToEBITDA, reverse=True)[:self.num_screener]
        self.symbols = [x.Symbol for x in top]
        self.rebalance_flag = 0
        self.first_month_trade_flag = 0
        self.trade_flag = 1
        return self.symbols
        #else:
        #    return self.symbols
    
    def OnSecuritiesChanged(self, changes):
        
        for security in changes.RemovedSecurities:
            if security.Symbol in self.data:
                del self.data[security.Symbol]
        
        addedSymbols = []
        for security in changes.AddedSecurities:
            addedSymbols.append(security.Symbol)
            if security.Symbol not in self.data:
                self.data[security.Symbol] = SymbolData(security.Symbol, self.formation_days)
   
        if len(addedSymbols) > 0:
            history = self.History(addedSymbols, 1 + self.formation_days, Resolution.Daily).loc[addedSymbols]
            for symbol in addedSymbols:
                try:
                    self.data[symbol].Warmup(history.loc[symbol])
                except:
                    self.Debug(str(symbol))
                    continue
                self.RegisterIndicator(symbol, self.data[symbol].Roc, Resolution.Daily, Field.Close)
    
    def consolidation_handler(self, sender, consolidated):
        self.history.loc[consolidated.EndTime, consolidated.Symbol] = consolidated.Close
        self.history = self.history.iloc[-self.lookback:]
        self.update_history_shift()
        
    def update_history_shift(self):
        self.history_shift = self.history.rolling(11, center=True).mean().shift(60)

    def rebalance_when_out_of_the_market(self):
        if self.be_in == 999:
            self.flip_flag = 1
            self.rebalance()
            self.flip_flag = 0
        
        # Returns sample to detect extreme observations
        returns_sample = (self.history / self.history_shift - 1)
        # Reverse code USDX: sort largest changes to bottom
        returns_sample[self.USDX] = returns_sample[self.USDX] * (-1)
        # For pairs, take returns differential, reverse coded
        returns_sample['G_S'] = -(returns_sample[self.GOLD] - returns_sample[self.SLVA])
        returns_sample['U_I'] = -(returns_sample[self.UTIL] - returns_sample[self.INDU])
        returns_sample['C_A'] = -(returns_sample[self.SHCU] - returns_sample[self.RICU])    

        # Extreme observations; statist. significance = 1%
        pctl_b = np.nanpercentile(returns_sample, 1, axis=0)
        extreme_b = returns_sample.iloc[-1] < pctl_b
        
        # Re-assess/disambiguate double-edged signals
        median = np.nanmedian(returns_sample, axis=0)
        abovemedian = returns_sample.iloc[-1] > median
        ### Interest rate expectations (cost of debt) may increase because the economic outlook improves (showing in rising input prices) = actually not a negative signal
        extreme_b.loc[[self.DEBT]] = np.where((extreme_b.loc[[self.DEBT]].any()) & (abovemedian[[self.METL, self.NRES]].any()), False, extreme_b.loc[[self.DEBT]])
        ### GOLD/SLVA differential may increase due to inflation expectations which actually suggest an economic improvement = actually not a negative signal
        try:
            extreme_b.loc['G_S'] = np.where((extreme_b.loc[['G_S']].any()) & (abovemedian.loc[[self.INFL]].any()), False, extreme_b.loc['G_S'])
        except:
            pass

        # Determine waitdays empirically via safe haven excess returns, 50% decay
        self.WDadjvar = int(
            max(0.50 * self.WDadjvar,
                self.INI_WAIT_DAYS * max(1,
                                         np.where((returns_sample[self.GOLD].iloc[-1]>0) & (returns_sample[self.SLVA].iloc[-1]<0) & (returns_sample[self.SLVA].iloc[-2]>0), self.INI_WAIT_DAYS, 1),
                                         np.where((returns_sample[self.UTIL].iloc[-1]>0) & (returns_sample[self.INDU].iloc[-1]<0) & (returns_sample[self.INDU].iloc[-2]>0), self.INI_WAIT_DAYS, 1),
                                         np.where((returns_sample[self.SHCU].iloc[-1]>0) & (returns_sample[self.RICU].iloc[-1]<0) & (returns_sample[self.RICU].iloc[-2]>0), self.INI_WAIT_DAYS, 1)
                                         ))
        )
        adjwaitdays = min(60, self.WDadjvar)

        # Determine whether 'in' or 'out' of the market
        if (extreme_b[self.SIGNALS + self.pairlist]).any():
            self.be_in = False
            self.outday = self.dcount
            self.trade({**dict.fromkeys(self.Portfolio.Keys, 0), **self.HLD_OUT})
        if self.dcount >= self.outday + adjwaitdays:
            self.be_in = True
        self.dcount += 1
        
        # Only re-shuffle stock allocation when switching from out to in, not in-between
        if not self.be_in_prior and self.be_in:
            self.flip_flag = 1
            self.rebalance()
            self.reb_count = self.dcount
            self.flip_flag = 0
        
        if self.be_in and self.reb_count > 0 and (self.dcount - self.reb_count) == 20:
            self.rebalance()
            self.reb_count = self.dcount
            
        self.Plot("In Out", "in_market", int(self.be_in))
        self.Plot("In Out", "num_out_signals", extreme_b[self.SIGNALS + self.pairlist].sum())
        self.Plot("Wait Days", "waitdays", adjwaitdays)
        
        self.be_in_prior = self.be_in


    def rebalance(self):
        self.rebalance_flag = 1
        #self.Debug(str(self.Time) + "rebalance: be_in:" + str(self.be_in) + " flip_flag:" + str(self.flip_flag))
            
        if self.symbols is None: return
        chosen_df = self.calc_return(self.symbols)
        chosen_df = chosen_df.iloc[:self.num_stocks]
        
        #for symbol in chosen_df.index:
        #    self.AddEquity(symbol)
        
        weight = 0.99/len(chosen_df)
        self.trade({**dict.fromkeys(chosen_df.index.tolist(), weight), **dict.fromkeys(list(dict.fromkeys(set(self.Portfolio.Keys) - set(chosen_df.index))), 0), **dict.fromkeys(self.HLD_OUT, 0)})
        
        
    def calc_return(self, stocks):
        #hist = self.History(stocks, self.formation_days, Resolution.Daily)
        #current = self.History(stocks, 1, Resolution.Minute)
        
        #self.price = {}
        ret = {}
     
        #for symbol in stocks:
        #    if str(symbol) in hist.index.levels[0] and str(symbol) in current.index.levels[0]:
        #        self.price[symbol.Value] = list(hist.loc[str(symbol)]['close'])
        #        self.price[symbol.Value].append(current.loc[str(symbol)]['close'][0])
        #for symbol in self.price.keys():
        for symbol in stocks:
            try:
            #ret[symbol] = (self.price[symbol][-1] - self.price[symbol][0]) / self.price[symbol][0]
                ret[symbol] = self.data[symbol].Roc.Current.Value
            except:
                self.Debug(str(symbol))
                continue
            
        df_ret = pd.DataFrame.from_dict(ret, orient='index')
        df_ret.columns = ['return']
        sort_return = df_ret.sort_values(by = ['return'], ascending = self.lowmom)
        
        return sort_return
       
        
    def trade(self, weight_by_sec):
        buys = []
        for sec, weight in weight_by_sec.items():
            # Check that we have data in the algorithm to process a trade
            if not self.CurrentSlice.ContainsKey(sec) or self.CurrentSlice[sec] is None:
                continue
            
            cond1 = weight == 0 and self.Portfolio[sec].IsLong
            cond2 = weight > 0 and not self.Portfolio[sec].Invested
            if cond1 or cond2:
                quantity = self.CalculateOrderQuantity(sec, weight)
                if quantity > 0:
                    buys.append((sec, quantity))
                elif quantity < 0:
                    self.Order(sec, quantity)
        for sec, quantity in buys:
            self.Order(sec, quantity)               
 
        
    def record_vars(self): 
        self.spy.append(self.history[self.MRKT].iloc[-1])
        spy_perf = self.spy[-1] / self.spy[0] * self.cap
        self.Plot('Strategy Equity', 'SPY', spy_perf)
        
        account_leverage = self.Portfolio.TotalHoldingsValue / self.Portfolio.TotalPortfolioValue
        self.Plot('Holdings', 'leverage', round(account_leverage, 2))
    
class SymbolData(object):
    def __init__(self, symbol, roc):
        self.Symbol = symbol
        self.Roc = RateOfChange(roc)
   
    def Warmup(self, history):
        for index, row in history.iterrows():
            self.Roc.Update(index, row['close'])
