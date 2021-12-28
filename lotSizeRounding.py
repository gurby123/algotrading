class BootCampTask(QCAlgorithm):
 
    def Initialize(self):

        self.SetCash(100000)
        self.SetStartDate(2017, 5, 1)
        self.SetEndDate(2017, 5, 31)
        self.AddForex("EURUSD", Resolution.Hour, Market.Oanda)
        self.SetBrokerageModel(BrokerageName.OandaBrokerage)
        
        #1. Save lot size to "self.lotSize"
        self.lotSize = float(self.Securities["EURUSD"].SymbolProperties.LotSize)
        
        #2. Print the lot size:
        self.Debug("The lot size is " + str(self.lotSize))
        
        #3. Round the order to the log size, save result to "self.roundedOrderSize"
        self.orderQuantity = 20180.12
        self.roundedOrderSize = round(self.orderQuantity/self.lotSize) * self.lotSize
        self.Debug("The order size is " + str(self.roundedOrderSize))
        
    def OnData(self, data):
        pass
    
