"""
DUAL MOMENTUM-IN OUT v2.4 by Vladimir

inspired by Peter Guenther, Tentor Testivis, Dan Whitnable, Thomas Chang and T Smith.
based on Intersection of ROC comparison using OUT_DAY approach by Vladimir
https://www.quantconnect.com/forum/discussion/10246/intersection-of-roc-comparison-using-out-day-approach/p1/comment-28827
"""
import numpy as np
# ----------------------------------------------------------
STOCKS = ['QQQ', 'FDN']; BONDS = ['TLT', 'TLH']; 
VOLA = 126; BASE_RET = 85; RET = 252; EXCL = 21; LEV = 1.00; 
# ----------------------------------------------------------

class DualMomentumInOut(QCAlgorithm):

    def Initialize(self):

        self.SetStartDate(2019, 1, 1)
        # self.SetEndDate(2021, 11, 27)
        self.cap = 100000        
        
        self.STK1 = self.AddEquity('QQQ', Resolution.Hour).Symbol
        self.STK2 = self.AddEquity('FDN', Resolution.Hour).Symbol
        self.BND1 = self.AddEquity('TLT', Resolution.Hour).Symbol
        self.BND2 = self.AddEquity('TLH', Resolution.Hour).Symbol
        self.ASSETS = [self.STK1, self.STK2, self.BND1, self.BND2]

        self.SLV = self.AddEquity('SLV', Resolution.Daily).Symbol  
        self.GLD = self.AddEquity('GLD', Resolution.Daily).Symbol  
        self.XLI = self.AddEquity('XLI', Resolution.Daily).Symbol 
        self.XLU = self.AddEquity('XLU', Resolution.Daily).Symbol
        self.DBB = self.AddEquity('DBB', Resolution.Daily).Symbol  
        self.UUP = self.AddEquity('UUP', Resolution.Daily).Symbol  
        self.MKT = self.AddEquity('SPY', Resolution.Daily).Symbol          

        self.pairs = [self.SLV, self.GLD, self.XLI, self.XLU, self.DBB, self.UUP]
        
        self.bull = 1        
        self.count = 0 
        self.outday = 0        
        self.wt = {}
        self.real_wt = {}
        self.mkt = []
        self.SetWarmUp(timedelta(350))
        
        self.selected_bond = self.BND1
        self.selected_stock = self.STK1

        self.Schedule.On(self.DateRules.EveryDay(), self.TimeRules.AfterMarketOpen('SPY', 100),
            self.calculate_signal)
           
            
        symbols = [self.MKT] + self.pairs
        for symbol in symbols:
            self.consolidator = TradeBarConsolidator(timedelta(days=1))
            self.consolidator.DataConsolidated += self.consolidation_handler
            self.SubscriptionManager.AddConsolidator(symbol, self.consolidator)
        
        self.history = self.History(symbols, VOLA + 1, Resolution.Daily)
        if self.history.empty or 'close' not in self.history.columns:
            return
        self.history = self.history['close'].unstack(level=0).dropna()
        
        
    def consolidation_handler(self, sender, consolidated):
        self.history.loc[consolidated.EndTime, consolidated.Symbol] = consolidated.Close
        self.history = self.history.iloc[-(VOLA + 1):]  
            
   
    def returns(self, symbol, period, excl):
        prices = self.History(symbol, TimeSpan.FromDays(period + excl), Resolution.Daily).close
        return prices[-excl] / prices[0]
        
        
    def calculate_signal(self):
        vola = self.history[[self.MKT]].pct_change().std() * np.sqrt(252)
        wait_days = int(vola * BASE_RET)
        period = int((1.0 - vola) * BASE_RET)        
        r = self.history.pct_change(period).iloc[-1]

        exit = ((r[self.SLV] < r[self.GLD]) and (r[self.XLI] < r[self.XLU]) and  (r[self.DBB] < r[self.UUP]))

        if exit:
            self.bull = False
            self.outday = self.count
        if self.count >= self.outday + wait_days:
            self.bull = True
        self.count += 1


        if self.returns(self.BND1, RET, EXCL) < self.returns(self.BND2, RET, EXCL):
            self.selected_bond = self.BND2
            
        elif self.returns(self.BND1, RET, EXCL) > self.returns(self.BND2, RET, EXCL):
            self.selected_bond = self.BND1
            
        if self.returns(self.STK1, RET, EXCL) < self.returns(self.STK2, RET, EXCL):
            self.selected_stock = self.STK2
            
        elif self.returns(self.STK1, RET, EXCL) > self.returns(self.STK2, RET, EXCL):
            self.selected_stock = self.STK1
            
        if not self.bull:
            for sec in self.ASSETS:    
                self.wt[sec] = 0.99 if sec is self.selected_bond else 0 if sec is self.selected_bond else 0
            self.trade() 

        elif self.bull:
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
            
                    
    def OnEndOfDay(self):                
        mkt_price = self.Securities[self.MKT].Close
        self.mkt.append(mkt_price)
        mkt_perf = self.mkt[-1] / self.mkt[0] * self.cap
        self.Plot('Strategy Equity', 'SPY', mkt_perf)
        
        account_leverage = self.Portfolio.TotalHoldingsValue / self.Portfolio.TotalPortfolioValue
        self.Plot('Holdings', 'leverage', round(account_leverage, 1))
        for sec, weight in self.wt.items(): 
            self.real_wt[sec] = round(self.ActiveSecurities[sec].Holdings.Quantity * self.Securities[sec].Price / self.Portfolio.TotalPortfolioValue,4)
            self.Plot('Holdings', self.Securities[sec].Symbol, round(self.real_wt[sec], 3))
