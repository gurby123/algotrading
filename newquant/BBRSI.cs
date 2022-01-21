namespace QuantConnect 
{   
    /*
    *   QuantConnect University: Bollinger Bands Example:
    */
    public class BollingerBandsAlgorithm : QCAlgorithm
    {
        string _symbol = "SPY";
        BollingerBands _bb;
        RelativeStrengthIndex _rsi;
        AverageTrueRange _atr;
        ExponentialMovingAverage _ema;
        SimpleMovingAverage _sma;
        MovingAverageConvergenceDivergence _macd;
        
        decimal _price;
        
        //Initialize the data and resolution you require for your strategy:
        public override void Initialize()
        {
            //Initialize
            SetStartDate(2021, 1, 1);         
            SetEndDate(2022, 1, 20); 
            SetCash(25000);
            
            //Add as many securities as you like. All the data will be passed into the event handler:
            AddSecurity(SecurityType.Equity, _symbol, Resolution.Minute);
            
            //Set up Indicators:
            _bb = BB(_symbol, 20, 1, MovingAverageType.Simple, Resolution.Daily);
            _rsi = RSI(_symbol, 14,  MovingAverageType.Simple, Resolution.Daily);
            _atr = ATR(_symbol, 14,  MovingAverageType.Simple, Resolution.Daily);
            _ema = EMA(_symbol, 14, Resolution.Daily);
            _sma = SMA(_symbol, 14, Resolution.Daily);
            _macd = MACD(_symbol, 12, 26, 9, MovingAverageType.Simple, Resolution.Daily);
        }

        public void OnData(TradeBars data) 
        {   
            if (!_bb.IsReady || !_rsi.IsReady) return;
            
            _price = data["SPY"].Close;
            
            if (!Portfolio.HoldStock) 
            { 
                int quantity = (int)Math.Floor(Portfolio.Cash / data[_symbol].Close);
                
                //Order function places trades: enter the string symbol and the quantity you want:
                Order(_symbol,  quantity);
                
                //Debug sends messages to the user console: "Time" is the algorithm time keeper object 
                Debug("Purchased SPY on " + Time.ToShortDateString());
            }
        }
        
        // Fire plotting events once per day:
        public override void OnEndOfDay() {
            if (!_bb.IsReady) return;
            
            Plot("BB", "Price", _price);
            Plot("BB", _bb.UpperBand, _bb.MiddleBand, _bb.LowerBand);
            
            Plot("RSI", _rsi);
            
            Plot("ATR", _atr);
            
            Plot("MACD", "Price", _price);
            Plot("MACD", _macd.Fast, _macd.Slow);
            
            Plot("Averages", _ema, _sma);
        }
    }
}
