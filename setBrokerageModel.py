class BootCampTask(QCAlgorithm):

    def Initialize(self):

        self.SetCash(100000)
        
        #1. Update the date range to May 1st - 31st.
        self.SetStartDate(2017, 5, 1)
        self.SetEndDate(2017, 5, 31)
        
        #1-2. Request hourly EURUSD data and set the market to Oanda
        self.forex = self.AddForex("EURUSD", Resolution.Hour, Market.Oanda)

    def OnData(self, data):
        pass
    
