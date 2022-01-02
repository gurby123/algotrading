import numpy as np
from sklearn.ensemble import GradientBoostingRegressor

# Adapted from https://www.quantopian.com/posts/simple-machine-learning-example-mk-ii

class SimpleML(QCAlgorithm):
  
    def Initialize(self):
  
        self.SetStartDate(2018,1,1)
        self.SetEndDate(2018,9,1)
        self.SetCash(100000)
        self.AddEquity('AMZN', Resolution.Daily)
        
        self.model = GradientBoostingRegressor()
        
        self.lookback = 30
        self.history_range = 200
        
        self.X = []
        self.y = []
        
        self.Schedule.On(self.DateRules.WeekStart(), self.TimeRules.BeforeMarketClose('AMZN', 10), Action(self.create_model))
        self.Schedule.On(self.DateRules.EveryDay(), self.TimeRules.AfterMarketOpen('AMZN', 1), Action(self.trade))

    def OnData(self, data):

        pass
            
    def create_model(self):
        
        recent_prices = self.History(['AMZN'], self.history_range)['close'].values
        price_changes = np.diff(recent_prices).tolist()
        
        for i in range(self.history_range-self.lookback-1):
            self.X.append(price_changes[i:i+self.lookback])
            self.y.append(price_changes[i+self.lookback])
            
        self.model.fit(self.X, self.y)
    
    def trade(self):
        
        if len(self.y) > self.lookback:
            
            recent_prices = self.History(['AMZN'], self.lookback+1)['close'].values
            price_changes = np.diff(recent_prices)
            
            prediction = self.model.predict(price_changes.reshape(1, -1))
            
            if prediction > 0:
                self.SetHoldings('AMZN', 1.0)
            else:
                self.SetHoldings('AMZN', 0)
