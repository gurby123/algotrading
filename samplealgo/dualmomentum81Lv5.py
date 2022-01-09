# Intersection of ROC comparison using OUT_DAY approach by Vladimirhttps://www.quantconnect.com/terminal/#backtest-floating-panel
import numpy as np
# ------------------------------------------------------------------------------
STOCKS = ['QQQ']; BONDS = ['TLT', 'TLH']; VOLA = 126; BASE_RET = 85; LEV = 1.50; 
PAIRS = ['SLV', 'GLD', 'XLI', 'XLU', 'DBB', 'UUP']
# ------------------------------------------------------------------------------
class InOut(QCAlgorithm):

    def Initialize(self):        
        self.SetStartDate(2019, 1, 1)  
        # self.SetEndDate(2021, 12, 17)        
        self.cap = 100000
        self.SetCash(self.cap) 
        self.SetBrokerageModel(BrokerageName.InteractiveBrokersBrokerage, AccountType.Margin)
        #self.Portfolio.MarginCallModel = MarginCallModel.Null

        self.STOCKS = [self.AddEquity(ticker, Resolution.Minute).Symbol for ticker in STOCKS] 
        self.BONDS = [self.AddEquity(ticker, Resolution.Minute).Symbol for ticker in BONDS]  
        #self.Securities["QQQ"].SetLeverage(2.0)
        #self.Securities["TLT"].SetLeverage(2.0)
        #self.Securities["TLH"].SetLeverage(2.0)
        self.Securities["QQQ"].MarginModel =  PatternDayTradingMarginModel()
        self.Securities["TLT"].MarginModel =  PatternDayTradingMarginModel()
        self.Securities["TLH"].MarginModel =  PatternDayTradingMarginModel()

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
        #self.SetWarmUp(timedelta(350))
        
        self.Schedule.On(self.DateRules.EveryDay(), self.TimeRules.AfterMarketOpen('SPY', 120),
            self.rebalance)        

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
        
    def rebalance(self):
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
        
        if not self.bull:
            for sec in self.STOCKS: self.wt[sec] = 0.0
            for sec in self.BONDS:  self.wt[sec] = LEV/len(self.BONDS)
            self.trade() 

        elif self.bull:
            for sec in self.STOCKS: self.wt[sec] = LEV/len(self.STOCKS)
            for sec in self.BONDS:  self.wt[sec] = 0.0
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
        self.Plot('Holdings', 'leverage', round(account_leverage, 2))
