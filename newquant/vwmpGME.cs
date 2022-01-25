namespace QuantConnect 
{   
	public class VWAPAlgorithm : QCAlgorithm
    {
    	private VolumeWeightedAveragePriceIndicator _vwap;
        public override void Initialize() 
        {
			SetStartDate(2021, 1, 1);         
            AddSecurity(SecurityType.Equity, "GME", Resolution.Daily);
            _vwap = VWAP("GME", 20);
        }

        public void OnData(TradeBars data) 
        {   
        	if (!Portfolio.HoldStock) SetHoldings("GME", 1m);
            Plot("GME", "Price", data["GME"].Price);
        	Plot("GME", "VWAP", _vwap);
        }
    }
}
