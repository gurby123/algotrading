import numpy as np

### <summary>
### Basic template algorithm simply initializes the date range and cash. This is a skeleton
### framework you can use for designing an algorithm.
### </summary>
class BasicTemplateAlgorithm(QCAlgorithm):
    '''Basic template algorithm simply initializes the date range and cash'''

    def Initialize(self):
        '''Initialise the data and resolution required, as well as the cash and start-end dates for your algorithm. All algorithms must initialized.'''
        self.SetStartDate(2005,1,1)  #Set Start Date
        self.SetEndDate(2018,2,1)    #Set End Date
        self.SetCash(100000)           #Set Strategy Cash
        self.SetWarmUp(150) #warm u for 100 days
        self.SetBrokerageModel(BrokerageName.InteractiveBrokersBrokerage) 
        #self.sizing = startCash * 0.02
        # Find more symbols here: http://quantconnect.com/data
        # self.SetBenchmark("NFLX")
        self.AddEquity("SPY", Resolution.Daily)
        self.Debug("numpy test >>> print numpy.pi: " + str(np.pi))
        self.longOnly = False
        
        self.load_symbols()
        for symbol in self.symbols:
            symbol.weight = 0
            symbol.stopprice = None
            symbol.lastSignal = "NA"
            # https://github.com/Quantconnect/Lean/blob/master/Algorithm.Python/MACDTrendAlgorithm.py1
            # 72, 189, 9,  VS  10,100,5  vs 50, 150, 9 --- seems that best are short is 1/2 to 1/4 ratio of the long
            symbol.macd = self.MACD(symbol, 50, 150, 9, MovingAverageType.Simple, Resolution.Daily)

        # trade every day 30 minutes after open
        self.Schedule.On(self.DateRules.EveryDay("SPY"), self.TimeRules.AfterMarketOpen("SPY", 30), Action(self.trade))


    def OnData(self, data):
        pass


    def trade(self):
        for symbol in self.symbols:
            if not symbol.macd.IsReady:
                continue
            
            macd = symbol.macd
            tolerance = 0.0025;
            holdings = self.Portfolio[symbol].Quantity
            signal = macd.Signal.Current.Value
            fast = macd.Fast.Current.Value
            slow = macd.Slow.Current.Value
            current = macd.Current.Value
            numHoldings = len(self.symbols)
            tradeQty = 0.99 / numHoldings
            
            if holdings <= 0 and  fast > slow:  # 0.01%
                symbol.lastSignal = 'LONG'
                #self.Debug("MACD signal long:" + str(symbol) + " signal:" + str(signal) + " slow:" + str(slow) + " fast:" + str(fast))
                self.SetHoldings(symbol, tradeQty)
            elif holdings >= 0 and slow > fast:
                symbol.lastSignal = 'SHORT'
                #self.Debug("MACD signal short: signal: " + str(signal))
                if not self.longOnly:
                    self.SetHoldings(symbol, -1 * tradeQty)
                else:
                    self.Liquidate(symbol)


    def load_symbols(self):
        syl_list = [
            #'SPY' #, 'USO', 'GLD', 'SLV', 'VNQ', 'HYG', 'EWJ'
            #'CAT', 'DE', 'CVX', 'LMT', 'HON', 'GM'
            #'IBB', 'SPY', 'IYR', 'IYF', 'IYH', 'IYM'
            'SPY'
        ]
        self.symbols = []
        for i in syl_list:
            self.symbols.append(self.AddEquity(i, Resolution.Daily, Market.USA, True, 1.0).Symbol)
