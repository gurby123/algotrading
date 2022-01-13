from unittest import TestCase

from technical_indicators_calculator import set_technical_indicators, Company
from technical_indicators_chart_plotting import TechnicalIndicatorsChartPlotter
import yfinance as yf

class TestTechnicalIndicator(TestCase):

    def test_tech_indicator(self):
        company = Company(’TWTR’)
        config = {}
        company.prices = yf.Ticker(company.symbol).history(period=’1y’)[’Open’][’High’][’Low’][’Close’][’Volume_BTC’]
        set_technical_indicators(config, company)


    df = add_all_ta_features(
        df, open="Open", high="High", low="Low", close="Close", volume="Volume_BTC", fillna=True)
