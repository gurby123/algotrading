from datetime import timedelta

class FundamentalFactorAlphaModel(AlphaModel):
    
    
    def __init__(self, num_fine, quality_weight, value_weight, size_weight):
        
        # Initialize the various variables/helpers we'll need
        self.lastMonth = -1
        self.longs = []
        self.num_fine = num_fine
        self.period = timedelta(31)
        
        # normalize quality, value, size weights
        weights = [quality_weight, value_weight, size_weight]
        weights = [float(i)/sum(weights) for i in weights]
        
        self.quality_weight = weights[0]
        self.value_weight = weights[1]
        self.size_weight = weights[2]



    def Update(self, algorithm, data):
        '''Updates this alpha model with the latest data from the algorithm.
        This is called each time the algorithm receives data for subscribed securities
        Args:
            algorithm: The algorithm instance
            data: The newa available
        Returns:
            New insights'''
        
        # Return no insights if it's not time to rebalance
        if algorithm.Time.month == self.lastMonth: 
            return []
        self.lastMonth = algorithm.Time.month
        
        # List of insights
        # Insights of the form: Insight(symbol, timedelta, type, direction, magnitude, confidence, sourceModel, weight)
        insights = []
        
        # Close old positions if they aren't in longs
        for security in algorithm.Portfolio.Values:
            if security.Invested and security.Symbol not in self.longs:
                insights.append(Insight(security.Symbol, self.period, InsightType.Price, 
                                            InsightDirection.Flat, None, None, None, None))
        
        length = len(self.longs)
        
        for i in range(length):
            insights.append(Insight(self.longs[i], self.period, InsightType.Price, 
                                    InsightDirection.Up, None, (length - i)**2, None, (length - i)**2 ))
        
        return insights



    def OnSecuritiesChanged(self, algorithm, changes):
        '''Event fired each time the we add/remove securities from the data feed
        Args:
            algorithm: The algorithm instance that experienced the change in securities
            changes: The security additions and removals from the algorithm'''

        # Get the added securities
        added = [x for x in changes.AddedSecurities]
        
        # Assign quality, value, size score to each stock
        quality_scores = self.Scores(added, [(lambda x: x.Fundamentals.OperationRatios.GrossMargin.Value, True, 2), 
                                            (lambda x: x.Fundamentals.OperationRatios.QuickRatio.Value, True, 1), 
                                            (lambda x: x.Fundamentals.OperationRatios.DebttoAssets.Value, False, 2)])
        
        value_scores = self.Scores(added, [(lambda x: x.Fundamentals.ValuationRatios.BookValuePerShare, True, 0.5),
                                            (lambda x: x.Fundamentals.ValuationRatios.CashReturn, True, 0.25),
                                            (lambda x: x.Fundamentals.ValuationRatios.EarningYield, True, 0.25)])
        
        size_scores = self.Scores(added, [(lambda x: x.Fundamentals.MarketCap, False, 1)])
        
        scores = {}
        # Assign a combined score to each stock 
        for symbol,value in quality_scores.items():
            quality_rank = value
            value_rank = value_scores[symbol]
            size_rank = size_scores[symbol]
            scores[symbol] = quality_rank*self.quality_weight + value_rank*self.value_weight + size_rank*self.size_weight
        
        # Sort the securities by their scores
        sorted_stock = sorted(scores.items(), key=lambda tup : tup[1], reverse=False)
        sorted_symbol = [tup[0] for tup in sorted_stock][:self.num_fine]
        
        # Sort the top stocks into the long_list
        self.longs = [security.Symbol for security in sorted_symbol]
        
        # Log longs symbols and their score
        algorithm.Log(", ".join([str(x.Symbol.Value) + ": " + str(scores[x]) for x in sorted_symbol]))


    def Scores(self, added, fundamentals):
        '''Assigns scores to each stock in added
        Args: 
            added: list of sceurities 
            fundamentals: list of 3-tuples (lambda function, bool, float)
        Returns:
            Dictionary with score for each security'''
        
        length = len(fundamentals)
        
        if length == 0:
            return {}
        
        # Initialize helper variables
        scores = {}
        sortedBy = []
        rank = [0 for _ in fundamentals]
        
        # Normalize weights
        weights = [tup[2] for tup in fundamentals]
        weights = [float(i)/sum(weights) for i in weights]
        
        # Create sorted list for each fundamental factor passed
        for tup in fundamentals:
            sortedBy.append(sorted(added, key=tup[0], reverse=tup[1]))
        
        # Create and save score for each symbol
        for index,symbol in enumerate(sortedBy[0]):
            
            # Save symbol's rank for each fundamental factor
            rank[0] = index
            for j in range(1, length):
                rank[j] = sortedBy[j].index(symbol)
            
            # Save symbol's total score
            score = 0
            for i in range(length):
                score += rank[i] * weights[i]
            scores[symbol] = score
            
        return scores
