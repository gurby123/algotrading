class BootCampTask(QCAlgorithm):

    def Initialize(self):
        
        self.AddEquity("SPY", Resolution.Daily)
        
        # 1. Set Starting Cash 
        self.SetCash(25000)
        
    def OnData(self, data):
        pass
