class BootCampTask(QCAlgorithm):

    def Initialize(self):

        self.SetCash(100000)
        self.SetStartDate(2017, 5, 1)
        self.SetEndDate(2017, 5, 31)
        self.AddForex("EURUSD", Resolution.Hour, Market.Oanda)
        self.SetBrokerageModel(BrokerageName.OandaBrokerage)
        self.eurusdAskClosePrice = 0

    def OnData(self, data):
        # 1. Debug the close of ask price of the "EURUSD" hourly bar at 05/01/2017 10am
        # Check the self.Time property then
        if self.Time.day == 1 and self.Time.hour == 10:
            # Save the value and print the close of ask price
            self.eurusdAskClosePrice = data["EURUSD"].Ask.Close
            self.Debug(str(self.eurusdAskClosePrice))
    
