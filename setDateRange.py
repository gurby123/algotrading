class BootCampTask(QCAlgorithm):

    def Initialize(self):
        
        #1-2. Set Date Range
        self.SetStartDate(2017, 1, 1)
        self.SetEndDate(2017, 10, 31)
        self.AddEquity("SPY", Resolution.Daily)
        
    def OnData(self, data):
        pass
