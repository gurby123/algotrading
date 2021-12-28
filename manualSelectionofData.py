class BootCampTask(QCAlgorithm):

    def Initialize(self):
        self.SetStartDate(2017, 6, 1)
        self.SetEndDate(2017, 6, 15)
        
        # Manually Select Data
        self.spy = self.AddEquity("SPY", Resolution.Minute)
        self.iwm = self.AddEquity("IWM", Resolution.Minute)
        
    def OnData(self, data):
        pass
