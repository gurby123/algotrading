class WellDressedSkyBlueSardine(QCAlgorithm):

    def Initialize(self):
        self.SetStartDate(2019, 1, 1)
        self.SetEndDate(2021, 1, 1)
        self.SetCash(100000)
        self.rebalanceTime = datetime.min
        self.activeStocks = set()

        self.AddUniverse(self.CoarseFilter, self.FineFilter)
        self.UniverseSettings.Resolution = Resolution.Hour
        
        self.portfolioTargets = []

    def CoarseFilter(self, coarse):
        # Rebalancing monthly
        if self.Time <= self.rebalanceTime:
            return self.Universe.Unchanged
        self.rebalanceTime = self.Time + timedelta(30)
        
        sortedByDollarVolume = sorted(coarse, key=lambda x: x.DollarVolume, reverse=True)
        return [x.Symbol for x in sortedByDollarVolume if x.Price > 10
                                                and x.HasFundamentalData][:200]

    def FineFilter(self, fine):
        sortedByPE = sorted(fine, key=lambda x: x.MarketCap)
        return [x.Symbol for x in sortedByPE if x.MarketCap > 0][:10]

    def OnSecuritiesChanged(self, changes):
        # close positions in removed securities
        for x in changes.RemovedSecurities:
            self.Liquidate(x.Symbol)
            self.activeStocks.remove(x.Symbol)
        
        # can't open positions here since data might not be added correctly yet
        for x in changes.AddedSecurities:
            self.activeStocks.add(x.Symbol)   

        # adjust targets if universe has changed
        self.portfolioTargets = [PortfolioTarget(symbol, 1/len(self.activeStocks)) 
                            for symbol in self.activeStocks]

    def OnData(self, data):

        if self.portfolioTargets == []:
            return
        
        for symbol in self.activeStocks:
            if symbol not in data:
                return
        
        self.SetHoldings(self.portfolioTargets)
        
        self.portfolioTargets = []
