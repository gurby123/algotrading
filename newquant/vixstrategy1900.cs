"""
VIX Strategy using hourly RSI 
(which is used as momentum indicator rather than a contrarian)
"""
from clr import AddReference # .NET Common Language Runtime (CLR) <- http://pythonnet.github.io/
AddReference("System")
AddReference("QuantConnect.Algorithm") # to load an assembly use AddReference
AddReference("QuantConnect.Common")

from System import * # CLR namespaces to be treatedas Python packages
from QuantConnect import *
from QuantConnect.Algorithm import *

# from QuantConnect.Python import PythonQuandl # quandl data not CLOSE
# from QuantConnect.Python import PythonData # custom data

import numpy as np; import pandas as pd
from datetime import datetime, timedelta
import decimal
import talib

class VIXbyRSI(QCAlgorithm):
    
    def __init__(self):
        self._period = 6
        self.perc_pos = 1.0 # just need something ~0.3 for enough fun
        
    def Initialize(self):
        self.SetCash(10000)
        self.SetStartDate(2011,5,1) 
        self.SetEndDate(datetime.now().date() - timedelta(1))
        
        self.first_time = True
        self.RSI_previous = None

        self.SetBrokerageModel(BrokerageName.InteractiveBrokersBrokerage, AccountType.Margin)
        
        self.XIV = self.AddEquity("XIV", Resolution.Hour).Symbol
        self.VXX = self.AddEquity("VXX", Resolution.Hour).Symbol
        self.spy = self.AddEquity("SPY", Resolution.Hour).Symbol
        
        self._RSI = self.RSI(self.XIV, self._period, MovingAverageType.Simple, Resolution.Hour)
        self.Plot("Indicators", self._RSI)

        self.Schedule.On(self.DateRules.EveryDay(self.XIV), self.TimeRules.AfterMarketOpen(self.XIV, 1),  Action(self.rebalance))
        self.Schedule.On(self.DateRules.EveryDay(self.XIV), self.TimeRules.AfterMarketOpen(self.XIV, 121),  Action(self.rebalance))       
        self.Schedule.On(self.DateRules.EveryDay(self.XIV), self.TimeRules.AfterMarketOpen(self.XIV, 241),  Action(self.rebalance))       
        self.Schedule.On(self.DateRules.EveryDay(self.XIV), self.TimeRules.AfterMarketOpen(self.XIV, 361),  Action(self.rebalance))
               

    def OnData(self, data):
        # we may insert some stop-losses in here
        pass

    def rebalance(self):    # every two hours

        # wait if still open orders
        if len(self.Transactions.GetOpenOrders())>0: return
        
        # wait for i. indicator warm up 
        if (not self._RSI.IsReady):
            if self.first_time:    # update RSI previous
                self.RSI_previous = self._RSI.Current.Value
                self.first_time = False
            return
        
        # update RSI
        RSI_curr = self._RSI.Current.Value
        self.Log(str(self.Time)+" RSI: "+ str(RSI_curr))
    
        # get current qnties
        XIV_qnty = self.Portfolio[self.XIV].Quantity
        VXX_qnty = self.Portfolio[self.VXX].Quantity
       
        # XIV positions
        if self.RSI_previous > 85 and RSI_curr <= 85: # down and below 85: SELL  
            if XIV_qnty > 0:
                self.Liquidate(self.XIV)
            if VXX_qnty > 0:
                self.Liquidate(self.VXX)
        if self.RSI_previous < 70 and RSI_curr >= 70: # up and above 70: BUY 
            if XIV_qnty == 0:
                self.SetHoldings(self.XIV, self.perc_pos)
            if VXX_qnty > 0:
                self.Liquidate(self.VXX)
       
        # VXX positions
        if self.RSI_previous > 30 and RSI_curr <= 30: # down and below 30: BUY
            if XIV_qnty > 0:
                self.Liquidate(self.XIV)
            if VXX_qnty == 0:
                self.SetHoldings(self.VXX, self.perc_pos)
        if self.RSI_previous < 15 and RSI_curr >= 15: # up and above 15: SELL
            if VXX_qnty > 0:
                self.Liquidate(self.VXX)
            if XIV_qnty == 0:
                self.SetHoldings(self.XIV, self.perc_pos)

        self.RSI_previous = RSI_curr
