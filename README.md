# Algotrading

QuantConnect:
Create	an account in QuantConnect  
<br>
Google Colab:
Please use google colab (Jupyter Notebook on web)  https://colab.research.google.com/notebooks/intro.ipynb
to practice basic python learnings. We will use basic python coding  so you just need to understand the data structures, how to store  and retrieve data. 
Colab	is a web application and does not requires any installation
<br>
Upload the notebook “Colab_Fundamentals_of_Python.ipynb”  in google colab to learn
![image](https://user-images.githubusercontent.com/16415155/147427766-db7ba3bd-fc83-4312-805d-82c7197db85e.png)


![image](https://user-images.githubusercontent.com/16415155/147431903-10ccd1c6-2eb4-475f-a6c3-786bc9222a80.png)

# Strategy
- PE Ratio eg below 20 - buy
- Plan a exit profit price and loss price. 
- Also make a time exit
- Rebalancing
- Purpose: percentage
- Timeline: month or weeks
 
# Criteria/Rule :
- MA50 above MA200
- PE below 40 entry
- PE above 60 exit
- Uptrend

- Determine Quantity based on maximum lost at stop loss ($500 (max loss) divided by loss per share at stop loss)
