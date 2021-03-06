"""
DUAL MOMENTUM-IN OUT v2 by Vladimir
https://www.quantconnect.com/forum/discussion/9597/the-in-amp-out-strategy-continued-from-quantopian/p3/comment-28146

inspired by Peter Guenther, Tentor Testivis, Dan Whitnable, Thomas Chang and T Smith.

"""
import numpy as np

class DualMomentumInOut(QCAlgorithm):

    def Initialize(self):

        self.SetStartDate(2019, 1, 1)
        # self.SetEndDate(2020, 11, 27)
        self.cap = 100000        
        
        self.STK1 = self.AddEquity('QQQ', Resolution.Hour).Symbol
        self.STK2 = self.AddEquity('FDN', Resolution.Hour).Symbol
        self.BND1 = self.AddEquity('TLT', Resolution.Hour).Symbol
        self.BND2 = self.AddEquity('TLH', Resolution.Hour).Symbol
        self.ASSETS = [self.STK1, self.STK2, self.BND1, self.BND2]

        self.MKT = self.AddEquity('SPY', Resolution.Hour).Symbol  
        self.XLI = self.AddEquity('XLI', Resolution.Hour).Symbol 
        self.XLU = self.AddEquity('XLU', Resolution.Hour).Symbol 
        self.SLV = self.AddEquity('SLV', Resolution.Hour).Symbol 
        self.GLD = self.AddEquity('GLD', Resolution.Hour).Symbol 
        self.FXA = self.AddEquity('FXA', Resolution.Hour).Symbol
        self.FXF = self.AddEquity('FXF', Resolution.Hour).Symbol
        self.DBB = self.AddEquity('DBB', Resolution.Hour).Symbol
        self.UUP = self.AddEquity('UUP', Resolution.Hour).Symbol          
        self.IGE = self.AddEquity('IGE', Resolution.Hour).Symbol
        self.SHY = self.AddEquity('SHY', Resolution.Hour).Symbol        

        self.FORPAIRS = [self.XLI, self.XLU, self.SLV, self.GLD, self.FXA, self.FXF]
        self.SIGNALS  = [self.XLI, self.DBB, self.IGE, self.SHY, self.UUP]
        self.PAIR_LIST = ['S_G', 'I_U', 'A_F']
        
        self.INI_WAIT_DAYS = 15
        self.SHIFT = 55
        self.MEAN = 11
        self.RET = 126
        self.EXCL = 5
        self.leveragePercentage = 101
        self.selected_bond = self.BND1
        self.selected_stock = self.STK1
        self.init = 0
        
        self.bull = 1 
        self.count = 0 
        self.outday = 0
        self.in_stock = 0
        self.spy = []
        self.wait_days = self.INI_WAIT_DAYS
        self.wt = {}
        self.real_wt = {}
        self.SetWarmUp(timedelta(126))

        self.Schedule.On(self.DateRules.EveryDay(), self.TimeRules.AfterMarketOpen('SPY', 100),
            self.calculate_signal)

        self.Schedule.On(self.DateRules.EveryDay(), self.TimeRules.Every(TimeSpan.FromMinutes(15)),
            self.trade_out)
            
        self.Schedule.On(self.DateRules.WeekEnd(), self.TimeRules.AfterMarketOpen('SPY', 120),
            self.trade_in)    
            
        self.Schedule.On(self.DateRules.EveryDay(), self.TimeRules.BeforeMarketClose('SPY', 0), 
            self.record_vars)            
            
        symbols = self.SIGNALS + [self.MKT] + self.FORPAIRS
        for symbol in symbols:
            self.consolidator = TradeBarConsolidator(timedelta(days = 1))
            self.consolidator.DataConsolidated += self.consolidation_handler
            self.SubscriptionManager.AddConsolidator(symbol, self.consolidator)
            
        self.lookback = 252
        self.history = self.History(symbols, self.lookback, Resolution.Daily)
        if self.history.empty or 'close' not in self.history.columns:
            return
        self.history = self.history['close'].unstack(level=0).dropna()
        self.update_history_shift() 
        
        
    def consolidation_handler(self, sender, consolidated):
        self.history.loc[consolidated.EndTime, consolidated.Symbol] = consolidated.Close
        self.history = self.history.iloc[-self.lookback:]
        self.update_history_shift()
        
        
    def update_history_shift(self):
        self.history_shift_mean = self.history.shift(self.SHIFT).rolling(self.MEAN).mean()    
            
   
    def returns(self, symbol, period, excl):
        prices = self.History(symbol, TimeSpan.FromDays(period + excl), Resolution.Daily).close
        return prices[-excl] / prices[0]
        
        
    def calculate_signal(self):
        mom = (self.history / self.history_shift_mean - 1)

        mom[self.UUP] = mom[self.UUP] * (-1)
        mom['S_G'] = mom[self.SLV] - mom[self.GLD]
        mom['I_U'] = mom[self.XLI] - mom[self.XLU]
        mom['A_F'] = mom[self.FXA] - mom[self.FXF]   

        pctl = np.nanpercentile(mom, 1, axis=0)
        extreme = mom.iloc[-1] < pctl

        self.wait_days = int(
            max(0.50 * self.wait_days,
                self.INI_WAIT_DAYS * max(1,
                     np.where((mom[self.GLD].iloc[-1]>0) & (mom[self.SLV].iloc[-1]<0) & (mom[self.SLV].iloc[-2]>0), self.INI_WAIT_DAYS, 1),
                     np.where((mom[self.XLU].iloc[-1]>0) & (mom[self.XLI].iloc[-1]<0) & (mom[self.XLI].iloc[-2]>0), self.INI_WAIT_DAYS, 1),
                     np.where((mom[self.FXF].iloc[-1]>0) & (mom[self.FXA].iloc[-1]<0) & (mom[self.FXA].iloc[-2]>0), self.INI_WAIT_DAYS, 1)
                     )))
                     
        adjwaitdays = min(60, self.wait_days)

        # self.Debug('{}'.format(self.wait_days))

        if (extreme[self.SIGNALS + self.PAIR_LIST]).any():
            self.bull = False
            self.outday = self.count
            
        if self.count >= self.outday + adjwaitdays:
            self.bull = True
            
        self.count += 1

        self.Plot("In Out", "in_market", int(self.bull))
        self.Plot("In Out", "num_out_signals", extreme[self.SIGNALS + self.PAIR_LIST].sum())
        self.Plot("Wait Days", "waitdays", adjwaitdays)

        if self.returns(self.BND1, self.RET, self.EXCL) < self.returns(self.BND2, self.RET, self.EXCL):
            self.selected_bond = self.BND2
            
        elif self.returns(self.BND1, self.RET, self.EXCL) > self.returns(self.BND2, self.RET, self.EXCL):
            self.selected_bond = self.BND1
            
        if self.returns(self.STK1, self.RET, self.EXCL) < self.returns(self.STK2, self.RET, self.EXCL):
            self.selected_stock = self.STK2
            
        elif self.returns(self.STK1, self.RET, self.EXCL) > self.returns(self.STK2, self.RET, self.EXCL):
            self.selected_stock = self.STK1
            
                    
    def trade_out(self):
        
        if not self.bull:
            for sec in self.ASSETS:    
                self.wt[sec] = 0.99 if sec is self.selected_bond else 0 if sec is self.selected_bond else 0
            self.trade() 
            
            
    def trade_in(self):
        
        if self.bull:    
            for sec in self.ASSETS:
                self.wt[sec] = 0.99 if sec is self.selected_stock else 0
            self.trade()            

                    
    def trade(self):

        for sec, weight in self.wt.items():
            if weight == 0 and self.Portfolio[sec].IsLong:
                self.Liquidate(sec)
                
            cond1 = weight == 0 and self.Portfolio[sec].IsLong
            cond2 = weight > 0 and not self.Portfolio[sec].Invested
            if cond1 or cond2:
                self.SetHoldings(sec, weight)
            
                    
    def record_vars(self):                
                
        hist = self.History([self.MKT], 2, Resolution.Daily)['close'].unstack(level= 0).dropna() 
        self.spy.append(hist[self.MKT].iloc[-1])
        spy_perf = self.spy[-1] / self.spy[0] * self.cap
        self.Plot("Strategy Equity", "SPY", spy_perf)
        
        account_leverage = self.Portfolio.TotalHoldingsValue / self.Portfolio.TotalPortfolioValue
        self.Plot('Holdings', 'leverage', round(account_leverage, 1))
        for sec, weight in self.wt.items(): 
            self.real_wt[sec] = round(self.ActiveSecurities[sec].Holdings.Quantity * self.Securities[sec].Price / self.Portfolio.TotalPortfolioValue,4)
            self.Plot('Holdings', self.Securities[sec].Symbol, round(self.real_wt[sec], 3))
