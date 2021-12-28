class BootCampTask(QCAlgorithm):

    def Initialize(self):
        self.SetCash(100000)
        self.SetStartDate(2017, 5, 1)
        self.SetEndDate(2017, 5, 31)
        
        #1. Request the forex data
        self.AddForex("AUDUSD", Resolution.Hour, Market.Oanda)
        
        #2. Set the brokerage model
        self.SetBrokerageModel(BrokerageName.OandaBrokerage)
        
    def OnData(self, data):
       
        #3. Using "Portfolio.Invested" submit 1 order for 2000 AUDUSD:
        if not self.Portfolio.Invested:
            self.MarketOrder("AUDUSD", 2000)
    
