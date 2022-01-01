import numpy as np

###
# All-Weather Portfolio
# ---------------------------------------------
# Strategy Author: Ray Dalio 
# Source: Tony Robbins / Money, master the game
# ----------------------------------------------
###
class BasicTemplateAlgorithm(QCAlgorithm):
    '''Basic template algorithm simply initializes the date range and cash'''

    def Initialize(self):
        '''Initialise the data and resolution required, as well as the cash and start-end dates for your algorithm. All algorithms must initialized.'''

        self.SetStartDate(2011,1,1)  #Set Start Date
        self.SetEndDate(2019,1,1)    #Set End Date
        self.SetCash(100000)           #Set Strategy Cash
        
        # Dividend Handling
        self.raw_handling = True
        
        # Simulate topping up your account with savings every period 
        self.savings_on = False
        self.savings_amt = 1000
        
        # This is to stop us adding savings on the first rebalance as it is 
        # immediately after starting the algo
        self.first_rebalance = True
        
        
        # This dictionary will be looped through to add equities and setholdings 
        # It can be expanded to hold more ETF's/Equities.
        self.all_weather = {
            "Equity 1":{
                    "Ticker": "VOO", # Vanguard S&P 500 ETF
                    "Weight": 0.15,
                    },
            "Equity 2":{
                    "Ticker": "VEA", # Vanguard FTSE Developed Markets ETF
                    "Weight": 0.15,
                    },        
            
            "Bonds Med-Term":{
                    "Ticker": "IEF", # iShares 7-10 Year Treasury Bond ETF
                    "Weight": 0.15,
                    },
                    
            "Bonds Long-Term":{
                    "Ticker": "TLT", # iShares 20+ Year Treasury Bond ETF
                    "Weight": 0.4,
                    },
            "Commodity 1":{
                    "Ticker": "GLD", # SPDR Gold Trust
                    "Weight": 0.075,
                    },
            "Commodity 2":{
                    "Ticker": "USO", # United States Oil Fund
                    "Weight": 0.075,
                    },
                    
            }
            
        
        # Setup IB Broker simulation
        self.SetBrokerageModel(BrokerageName.InteractiveBrokersBrokerage)
            
        
        # Add The ETF'S!
        # ---------------
        for key, asset in self.all_weather.items():
            self.AddEquity(asset["Ticker"], Resolution.Daily)
            
            # Set Dividend Handling Method
            # ----------------------------
            # https://www.quantconnect.com/forum/discussion/508/update-dividends-splits-and-custom-price-normalization/p1
            if self.raw_handling:
                self.Securities[asset["Ticker"]].SetDataNormalizationMode(DataNormalizationMode.Raw)
            else:
                self.Securities[asset["Ticker"]].SetDataNormalizationMode(DataNormalizationMode.TotalReturn)
        
        
        # We will assume that if we can place an order for the Equity, then the other
        # ETF's should be fine. 
        self.Schedule.On(self.DateRules.MonthStart(self.all_weather["Equity 1"]["Ticker"]),
                            self.TimeRules.AfterMarketOpen(self.all_weather["Equity 1"]["Ticker"]),
                            self.Rebalance)
                            

    def OnData(self, data):
        '''OnData event is the primary entry point for your algorithm. Each new data point will be pumped in here.

        Arguments:
            data: Slice object keyed by symbol containing the stock data
        '''
        # Log any dividends received.
        # ---------------------------
        for kvp in data.Dividends: # update this to Dividends dictionary
            div_ticker = kvp.Key
            div_distribution = kvp.Value.Distribution
            div_total_value = div_distribution * self.Portfolio[div_ticker].Quantity
            self.Log("DIVIDEND >> {0} - ${1} - ${2}".format(div_ticker, div_distribution, div_total_value))
            
            
    def Rebalance(self):
        month = self.Time.month
        
        # Return if we don't want to rebalance this month
        # Add extra months in here to rebalance more often
        # i.e for March insert 3 into the list. 
        if month not in [1,6]: return
    
        self.Log('-------------------->>')
        self.Log("{0} RE-BALANCE >> Total Value {1} | Cash {2}".format(
                                                                    self.Time.strftime('%B').upper(),
                                                                    self.Portfolio.TotalPortfolioValue,
                                                                    self.Portfolio.Cash))
    
    
        if self.savings_on and not self.first_rebalance:
            
            cash_after_savings = self.Portfolio.Cash + self.savings_amt
            self.Log("Top Up Savings >> New Cash Balance {0}".format(
                                                                cash_after_savings))
            self.Portfolio.SetCash(cash_after_savings)
    
        # Rebalance!                                                                
        for key, asset in self.all_weather.items():
            
            holdings = self.Portfolio[asset["Ticker"]].Quantity
            price = self.Portfolio[asset["Ticker"]].Price
            
            self.Log("{0} >> Current Holdings {1} | Current Price {2}".format(
                                                                    self.Portfolio[asset["Ticker"]].Symbol,
                                                                    holdings,
                                                                    price))

            self.SetHoldings(asset["Ticker"], asset["Weight"])
            
        self.Log('-------------------->>')
        
        # Set first rebalance to False so we add the savings next time around
        # (if turned on)
        self.first_rebalance = False
