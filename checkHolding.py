class BootCampTask(QCAlgorithm):

    def Initialize(self):
        self.SetStartDate(2017, 6, 1)
        self.SetEndDate(2017, 6, 2)
        
        #1. Update the AddEquity command to request IBM data
        self.ibm = self.AddEquity("IBM", Resolution.Daily)
        
    def OnData(self, data):
        
        #2. Display the Quantity of IBM Shares You Own
        self.Debug("Number of IBM Shares: " + str(self.Portfolio["IBM"].Quantity))
        
