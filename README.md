# A Simple CryptoCompare Client
A class used to gather historical price data from 
[CryptoCompare](https://www.cryptocompare.com/). Code is originally 
taken from my [cryptocurency_backtesting](https://github.com/DylanScotney/cryptocurrency_backtesting) repository that was build as part of my MSc dissertation.

Data from CryptoCompare is sourced from an aggregated feed of over 150 
crypto exchanges giving you reliable and up-to-date traded rates that
are used globally. They have systems in place to remove irregular 
prices, giving you the cleanest (FREE) prices available. 
[Read more](https://www.cryptocompare.com/media/27010937/cccagg_methodology_2018-02-26.pdf).

## **Dependencies**
The class currently uses the following python librarys and any of their 
subsequent dependecies: 
* requests
* json
* datetime
* math
* pandas
* matplotlib

## **Code Overview**
Repo currently only consists of one class ccClient that has limited
functionality. Currently only designed to get historical price data 
of an asset or list of assets. Stores OHLCV data in raw JSON format
and stores close prices w/ corresponding date in CSV format. 

**Note**: Missing data points are extrapolated horizontally. 

**Example Usage:**

*ccClient()*
```
from datetime import datetime
import pandas as pd
from matplotlib import pyplot as plt

# Define parameters
api_key = <my_api_key>
symbols = ['BTC', 'ETH', 'LTC']
ticksize = "day"  # Get daily data. Can be "minute", "hour" or "day"
currency = "USD"  # How assets are valued. Can be "USD" or "BTC"
enddate = datetime(2019, 6, 1)  # Get data up to 01/06/2019
lookback = 400  # Get 400 data points
outfile_raw = "my_raw_data.json"
outfile_df = "my_close_prices.csv"

client = ccClient(api_key, symbols, ticksize, enddate, lookback,
                  currency, outfile_raw, outfile_df)

df = client.get_data()  # Returns pandas Dataframe of close prices

# Plot data
df.plot()
plt.show()
```

## **To Do**
* Write conversion method that will convert data into longer formats 
e.g. 1H ticksize -> 4H ticksize 
* Write methods that incorperate other functionalites of the 
cryptocompare API.
