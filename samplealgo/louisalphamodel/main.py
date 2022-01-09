from Execution.ImmediateExecutionModel import ImmediateExecutionModel
from Portfolio.EqualWeightingPortfolioConstructionModel import InsightWeightingPortfolioConstructionModel
from Risk.MaximumDrawdownPercentPerSecurity import MaximumDrawdownPercentPerSecurity
from AlphaModel import FundamentalFactorAlphaModel


class VerticalTachyonRegulators(QCAlgorithm):

    def Initialize(self):
        self.SetStartDate(2012, 5, 1)
        self.SetEndDate(2020, 5, 1)
        self.SetCash(100000)
        
        # Execution model
        self.SetExecution(ImmediateExecutionModel())
        
        # Portfolio construction model
        self.SetPortfolioConstruction(InsightWeightingPortfolioConstructionModel())
        
        # Risk model
        stopRisk = self.GetParameter("stopRisk")
        if stopRisk is None:
            stopRisk = 0.1
        self.SetRiskManagement(TrailingStopRiskManagementModel(float(stopRisk)))
#        self.SetRiskManagement(MaximumDrawdownPercentPerSecurity(float(stopRisk)))
        
        # Universe selection
        self.num_coarse = 200
        self.num_fine = 20
        self.lastMonth = -1
        self.UniverseSettings.Resolution = Resolution.Daily
        self.AddUniverse(self.CoarseSelectionFunction, self.FineSelectionFunction)
        
        # Set factor weighting        
        quality_weight = 2
        size_weight = 1
        value_weight = 2
        
        # Alpha Model
        self.AddAlpha(FundamentalFactorAlphaModel(self.num_fine, quality_weight, value_weight, size_weight))
        
        self.Schedule.On(self.DateRules.Every(DayOfWeek.Monday), 
                        self.TimeRules.At(10, 30),
                        self.Plotting)


    def Plotting(self):
        self.Plot("Positions", "Num", len([x.Symbol for x in self.Portfolio.Values if self.Portfolio[x.Symbol].Invested]))


    def CoarseSelectionFunction(self, coarse):
        # If not time to rebalance, keep the same universe
        if self.Time.month == self.lastMonth: 
            return Universe.Unchanged
        
        # Else reassign the month variable
        self.lastMonth = self.Time.month
        
        # Select only those with fundamental data and a sufficiently large price
        # Sort by top dollar volume: most liquid to least liquid
        selected = sorted([x for x in coarse if x.HasFundamentalData and x.Price > 5],
            key = lambda x: x.DollarVolume, reverse=True)
        
        return [x.Symbol for x in selected[:self.num_coarse]]


    def FineSelectionFunction(self, fine):
        # Filter the fine data for equities with non-zero/non-null Value,
        filtered_fine = [x.Symbol for x in fine if x.OperationRatios.GrossMargin.Value > 0
                                                and x.OperationRatios.QuickRatio.Value > 0
                                                and x.OperationRatios.DebttoAssets.Value > 0
                                                and x.ValuationRatios.BookValuePerShare > 0
                                                and x.ValuationRatios.CashReturn > 0
                                                and x.ValuationRatios.EarningYield > 0
                                                and x.MarketCap > 0]
        
        return filtered_fine
