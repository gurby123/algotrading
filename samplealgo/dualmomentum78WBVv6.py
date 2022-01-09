"""
DUAL MOMENTUM-IN OUT v2 by Vladimir
https://www.quantconnect.com/forum/discussion/9597/the-in-amp-out-strategy-continued-from-quantopian/p3/comment-28146

inspired by Peter Guenther, Tentor Testivis, Dan Whitnable, Thomas Chang and T Smith.

"""
import numpy as np

class DualMomentumInOut(QCAlgorithm):

    def Initialize(self):
        self.Debug(self.Time.strftime("%m/%d/%Y %A %H:%M:%S")  + " Initializing DualMomentumInOut")
        self.msg = ""
        self.SetStartDate(2019, 1, 1)
        self.SetEndDate(2021, 12, 1)
        self.cap = 10000        
        self.SetCash(10000)
        self.STK1 = self.AddEquity('QQQ', Resolution.Minute).Symbol
        self.STK2 = self.AddEquity('FDN', Resolution.Minute).Symbol
        self.BND1 = self.AddEquity('TLT', Resolution.Minute).Symbol
        self.BND2 = self.AddEquity('TLH', Resolution.Minute).Symbol
        self.ASSETS = [self.STK1, self.STK2, self.BND1, self.BND2]

        self.MKT = self.AddEquity('SPY', Resolution.Daily).Symbol  
        self.XLI = self.AddEquity('XLI', Resolution.Daily).Symbol 
        self.XLU = self.AddEquity('XLU', Resolution.Daily).Symbol 
        self.SLV = self.AddEquity('SLV', Resolution.Daily).Symbol 
        self.GLD = self.AddEquity('GLD', Resolution.Daily).Symbol 
        self.FXA = self.AddEquity('FXA', Resolution.Daily).Symbol
        self.FXF = self.AddEquity('FXF', Resolution.Daily).Symbol
        self.DBB = self.AddEquity('DBB', Resolution.Daily).Symbol
        self.UUP = self.AddEquity('UUP', Resolution.Daily).Symbol          
        self.IGE = self.AddEquity('IGE', Resolution.Daily).Symbol
        self.SHY = self.AddEquity('SHY', Resolution.Daily).Symbol        

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
        #self.SetWarmUp(timedelta(126))
        self.SetWarmUp(timedelta(90))

        self.Schedule.On(self.DateRules.EveryDay(), self.TimeRules.AfterMarketOpen('SPY', 100),
            self.calculate_signal)

        self.Schedule.On(self.DateRules.EveryDay(), self.TimeRules.AfterMarketOpen('SPY', 120),
            self.trade_out)
            
        self.Schedule.On(self.DateRules.WeekStart(), self.TimeRules.AfterMarketOpen('SPY', 100),
            self.trade_in)    
            
        self.Schedule.On(self.DateRules.EveryDay(), self.TimeRules.BeforeMarketClose('SPY', 0), 
            self.record_vars)   
            
        #self.Schedule.On(self.DateRules.EveryDay(), self.TimeRules.Every(TimeSpan.FromMinutes(10)),
        #    self.trade_in) 
        #self.Schedule.On(self.DateRules.EveryDay(), self.TimeRules.Every(TimeSpan.FromMinutes(5)),
        #    self.calculate_signal)
        #self.Schedule.On(self.DateRules.EveryDay(), self.TimeRules.Every(TimeSpan.FromMinutes(7)),
        #    self.trade_out)
            
        symbols = self.SIGNALS + [self.MKT] + self.FORPAIRS
        for symbol in symbols:
            self.consolidator = TradeBarConsolidator(timedelta(days = 1))
            self.consolidator.DataConsolidated += self.consolidation_handler
            self.SubscriptionManager.AddConsolidator(symbol, self.consolidator)
            
        self.lookback = 252 # 1 year trading days
        self.history = self.History(symbols, self.lookback, Resolution.Daily)
        #self.Debug(self.Time.strftime("%m/%d/%Y %A %H:%M:%S")  + " self.history =")
       
        # indicees: symbols, time  columns: OHLCV
        
        if self.history.empty or 'close' not in self.history.columns:
            return
        
        self.history = self.history['close'].unstack(level=0).dropna()
        #self.Debug(self.history)
        # 
        #
        #  timestamp 1: 
        #  timestamp 2: 
        #
        #
        
        self.update_history_shift() 
        
        ''' 
            Everyday:
                1.  11:10 AM: Calculate Signals 
                2.  11:30 AM: Trade_Out
            WeekEnd (Last trading day of week - Friday if no holiday):
                1. 11:30 AM: Trade In
            
            Recording DATA EveryDay before market close
        
        '''
        
    def EndOfDay(self):
        # check if account drawdown exceeds some predetermined limit
        
        # if self.drawdown_reached:
        #     self.Liquidate() # liquidate everything
        #     self.Quit()  # kill the algorithm
        self.Debug(self.Time.strftime("%m/%d/%Y %A %H:%M:%S")  + " EndOfDay called")
        pass
        
    def consolidation_handler(self, sender, consolidated):
        self.history.loc[consolidated.EndTime, consolidated.Symbol] = consolidated.Close
        self.history = self.history.iloc[-self.lookback:]
        self.update_history_shift()
        
        
    def update_history_shift(self):
        #self.Debug("update_history_shift called")
        #self.Debug("---self.history.shift(self.SHIFT)---")
        #elf.Debug(self.history.shift(self.SHIFT))
        #self.Debug("+++self.history.shift(self.SHIFT).rolling(self.MEAN)+++")
        #self.Debug(self.history.shift(self.SHIFT).rolling(self.MEAN))
        #self.Debug("***self.history.shift(self.SHIFT).rolling(self.MEAN).mean()***")
        #self.Debug(self.history.shift(self.SHIFT).rolling(self.MEAN).mean())
    
    
        #
        # The history sift goes back 55 business days (i.e ignoring from today going back 55)
        # The rolling self mean takes the average of the last 10 rows of closing prices
        #
        self.history_shift_mean = self.history.shift(self.SHIFT).rolling(self.MEAN).mean()    
            
   
    def returns(self, symbol, period, excl):
        # history call of daily close data of length (period + excl)
        prices = self.History(symbol, TimeSpan.FromDays(period + excl), Resolution.Daily).close
        
        # symbol = SPY , period = 10,  excl = 3
        # 13 days of close data for SPY
        # returns of last 3 days over history call period
        #  = last 3 days of closes / close 13 days ago
        
        # returns the last excl days of returns as compared to the beginning of the period
        #
        return prices[-excl] / prices[0]
        
        
    def calculate_signal(self):
        self.Debug(self.Time.strftime("%m/%d/%Y %A %H:%M:%S")  + "  calculate_signal called")
        self.add_msg("calculate_signal called")

        '''
            Finds 55-day return for all securities
            
            Calculates extreme negative returns (1th percentile)
            
            If there are currently extreme returns, sets bull flag to False
            Starts counter 
            
            Also selects bond and stock we will be trading based on recent returns
        
        '''
        # self.history
        #elf.Debug("----- self.history -----")
        #self.Debug(self.history)
        
        #self.Debug("+++++ self.history_shift_mean +++++")
        #self.Debug(self.history_shift_mean)
        
        #
        # momentum for all securities todays closing prices / 55 days ago rolling 10 days average subtrace
        #
        mom = (self.history / self.history_shift_mean - 1)
        #self.Debug(self.Time.strftime("%m/%d/%Y %A %H:%M:%S")  + "   mom = (self.history / self.history_shift_mean - 1)")
        #self.Debug(mom)
        # 
        # 
        # 
        #  
        
        # MOMENTUM Values/Return over past 55 days
        # Today's return / 11 Period SMA 55 days ago
        
        mom[self.UUP] = mom[self.UUP] * (-1)
        mom['S_G'] = mom[self.SLV] - mom[self.GLD]
        mom['I_U'] = mom[self.XLI] - mom[self.XLU]
        mom['A_F'] = mom[self.FXA] - mom[self.FXF]   
        
        pctl = np.nanpercentile(mom, 1, axis=0)
        
        # calculating value of 1th percentile of return
        # this over all history call
        
        # it's a dataframe that you can a pass symbol and it will return true
        # if the previous 55-day return is an extreme negative
        
        # you can pass it a symbol extreme[self.MKT], and it returns a boolean
        # you can also pass it multiple symbols extreme[]
        extreme = mom.iloc[-1] < pctl
        
        # looking at most recent data, last day, is it extreme compared to
        # historical 1th percentile of worst returns?
        
        wait_days_value_1 = 0.50 * self.wait_days
        wait_days_value_2 = self.INI_WAIT_DAYS * max(1,
                     np.where((mom[self.GLD].iloc[-1]>0) & (mom[self.SLV].iloc[-1]<0) & (mom[self.SLV].iloc[-2]>0), self.INI_WAIT_DAYS, 1),
                     np.where((mom[self.XLU].iloc[-1]>0) & (mom[self.XLI].iloc[-1]<0) & (mom[self.XLI].iloc[-2]>0), self.INI_WAIT_DAYS, 1),
                     np.where((mom[self.FXF].iloc[-1]>0) & (mom[self.FXA].iloc[-1]<0) & (mom[self.FXA].iloc[-2]>0), self.INI_WAIT_DAYS, 1)
                     )
        
        self.wait_days = int(max(wait_days_value_1, wait_days_value_2))
        
        # we want our wait days to be no more than 60 days
        adjwaitdays = min(60, self.wait_days)
        # self.Debug('{}'.format(self.wait_days))
        
        
        # returns true if ANY security has an extreme negative 55 day return
        if (extreme[self.SIGNALS + self.PAIR_LIST]).any():
            self.bull = False
            self.outday = self.count
        
        # if there is an extreme, we wait a maximum of 60 days
        # at the end of our wait period, we are again bullish
        
        # reset each time we have a new extreme.
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
        
        self.add_msg("Are we in a bull market ? " + str(self.bull) + "\n")

        for signal, status in extreme.items():
            self.add_key_value_msg(signal, str(status))
        self.send_message("calculate_signal called ")

                    
    def trade_out(self):
        #self.Debug(self.Time.strftime("%m/%d/%Y %A %H:%M:%S")  + " trade_out called")
        self.add_msg("trade_out called")

        # if bull is false
        if not self.bull:
            self.add_msg("Yes we are in a Bear Market!  Need to Trade Out")

            # STK 1, STK 2, BND 1, BND 2
            data = "Portfolio\n"
            data += "Symbol Weight\n"

            for sec in self.ASSETS: 
                # Just bonds
                # set selected BOND to full weight and everything else to 0
                self.wt[sec] = 0.99 if sec is self.selected_bond else 0 
                self.add_key_value_msg(str(sec), str(self.wt[sec]))
                
            self.trade()
        else:
            self.add_msg("Skipping trade out.  We are in a Bull market.")
        self.send_message("called trade_out")
            
    def trade_in(self):
        #self.Debug(self.Time.strftime("%m/%d/%Y %A %H:%M:%S")  + " trade_in called")
        self.add_msg("trade_in called")
        self.add_msg("")

        # if bull is true
        if self.bull: 
            self.add_msg("Yes we are in a Bull Market!  Trade in")

             # STK 1, STK 2, BND 1, BND 2
            self.add_key_value_msg("Symbol", "Weight")

            for sec in self.ASSETS:
                # just stock
                # set selected STOCK to full weight and everything else to 0
                self.wt[sec] = 0.99 if sec is self.selected_stock else 0
                self.add_key_value_msg(str(sec), str(self.wt[sec]))
            self.trade()
        else:
            self.add_msg("Skipping trade in.  We are in a bear market.")

        self.send_message("called trade_in")

                    
    def trade(self):
        #self.Debug(self.Time.strftime("%m/%d/%Y %A %H:%M:%S")  + " trade called")

        for sec, weight in self.wt.items():
            
            # liquidate all 0 weight sec
            if weight == 0 and self.Portfolio[sec].IsLong:
                self.Liquidate(sec)
            
            # MAY BE REDUNDANT
            # if weight is 0 and we're long
            cond1 = weight == 0 and self.Portfolio[sec].IsLong
            
            # if weight is positive and not invested 
            cond2 = weight > 0 and not self.Portfolio[sec].Invested
            
            # if condition is true, we will submit an order
            if cond1 or cond2:
                self.Debug("  SetHoldings Sec:"+str(sec)+" Weight:"+str(weight))
                #self.Debug(sec)
                self.SetHoldings(sec, weight)
            
                    
    def record_vars(self):    
        #self.Debug(self.Time.strftime("%m/%d/%Y %A %H:%M:%S")  + " record_vars called")
        #data = "record_vars called\n\n"

        hist = self.History([self.MKT], 2, Resolution.Daily)['close'].unstack(level= 0).dropna() 
        # self.Debug(hist)
        self.spy.append(hist[self.MKT].iloc[-1])
        spy_perf = self.spy[-1] / self.spy[0] * self.cap
        self.Plot("Strategy Equity", "SPY", spy_perf)
        
        account_leverage = self.Portfolio.TotalHoldingsValue / self.Portfolio.TotalPortfolioValue
        #data = "Total Portfolio Value:"+str(self.Portfolio.TotalPortfolioValue)+"\n"
        #data = "Total Holdings Value:"+str(self.Portfolio.TotalHoldingsValue)+"\n"
        self.add_key_value_msg("Total Portfolio Value:", str(self.Portfolio.TotalPortfolioValue))
        self.add_key_value_msg("Total Holdings Value:", str(self.Portfolio.TotalHoldingsValue))
        self.Plot('Holdings', 'leverage', round(account_leverage, 1))
        for sec, weight in self.wt.items(): 
            self.real_wt[sec] = round(self.ActiveSecurities[sec].Holdings.Quantity * self.Securities[sec].Price / self.Portfolio.TotalPortfolioValue,4)
            self.Plot('Holdings', self.Securities[sec].Symbol, round(self.real_wt[sec], 3))
        self.send_message("called record_vars")
        
    def add_msg(self, msg):
        self.msg += "<tr><td colspan=\"2\">" + msg + "</td></tr>"
    
    def add_key_value_msg(self, key, value):
        self.msg += "<tr><td>" + key + "</td><td>" + value + "</td></tr>"
        
    def send_message(self, subject):
        body = "<html><body><table>" + self.msg + "</table></body></html>"
        self.Notify.Email("wberger@leadoutcome.com", subject, body);
        self.msg=""
