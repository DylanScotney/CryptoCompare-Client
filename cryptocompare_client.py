import requests
import json
from datetime import datetime, timedelta
import math
import pandas as pd
from matplotlib import pyplot as plt

class ccClient():
    """
    Concrete implementation of a data loading strategy used in
    dataLoader class. designed to pull crypto exchange OHLCV data
    from https://www.cryptocompare.com.

    Initialisation:
    - api_key:              (str) cryptocompare api key
    - symbols:              (list, str) ticker symbols for coins to be
                            considered e.g. ["BTC", "LTC", "ETH", ...]
    - ticksize:             (str) ticksize of data considered.
                            cryptocompare currently only accepts: "day",
                            "hour", or "minute"
    - end_date:             (datetime) object of the most latest
                            date of desired data
    - lookback:             (int) number of ticks of data to request
    - currency:             (str) The currency in which to price the 
                            assets. Accepts "BTC" or "USD"
    - outfile_raw:          (json) json file storing OHLCV data
    - outfile_df:           (csv) csv file that stores close prices in a
                            pandas DataFrame

    Members:
    - self._key:            (str) api_key (see initialisation)
    - self._symbols:        (list, str) symbols (see initialisation)
    - self._ticksize:       (str) ticksize (see initialisation)
    - self._end_date:       (datetime) end_date (see initialisation)
    - self._start_date:     (datetime) start date of data
    - self._timedelta:      (datetime) time different between
                            self._end_date and self._start_date
    - self._lookback:       (int) lookback (see initialisation)
    - self._outfile_raw:    (str) outfile_raw (see initialisation)
    - self._outfile_df:     (str) outfile df (see initialisation)
    - self._limit:          (int) Cryptocompare has a limit of pulling 
                            2000 datapoints at any one time

    To Do:
    - Write conversion function that will convert data into longer 
    formats e.g. 1H ticksize -> 4H ticksize 
    - Write methods that incorperate other functionalites of 
    the cryptocompare API.

    """

    def __init__(self, api_key, symbols, ticksize, end_date,
                 lookback, currency, outfile_raw, outfile_df):

        self._typeCheckArgs(api_key, symbols, ticksize, end_date,
                            lookback, currency, outfile_raw, outfile_df)
        
        # private memebers as to be instiated on construction only
        self._key = api_key
        self._symbols = symbols
        self._ticksize = ticksize
        self._end_date = end_date
        self._lookback = lookback
        self._currency = currency
        self._outfile_raw = outfile_raw
        self._outfile_df = outfile_df

        # Free CryptoCompare API has max 2000 datapoints per pull
        self._limit = 2000

        # Compute startdate from end date
        self._timedelta = self._setTimeDelta()
        self._start_date = self._end_date + self._timedelta

    def _setTimeDelta(self):
        """
        Sets the member self._timedelta on construction.

        self._timedelta is the difference between the start date and end
        date in datetime format. 
        """
        if self._ticksize == "minute":
            return timedelta(minutes=-self._lookback)
        elif self._ticksize == "hour":
            return timedelta(hours=-self._lookback)
        elif self._ticksize == "day":
            return timedelta(days=-self._lookback)
        else:
            raise ValueError(("Ticksize not recognised."
                             + "Use: 'day', 'hour' or 'minute'"))


    def _typeCheckArgs(self, api_key, symbols, ticksize, end_date,
                       lookback, currency, outfile_raw, outfile_df):
        """
        Checks the type for input args on construction. 
        """

        if not isinstance(api_key, str):
            raise ValueError("api_key must be str type")
        
        if not all(isinstance(symbol, str) for symbol in symbols):
            raise ValueError("Symbols must be list of string types")

        if ticksize not in ("hour", "minute", "day"):
            raise ValueError(("Ticksize not compatible."
                              + "Use: 'day', 'hour', 'minute'"))

        if not isinstance(end_date, datetime):
            raise ValueError("end_date must be a datetime object")

        if not ((isinstance(lookback, int)) and (lookback >= 1)):
            raise ValueError("lookback must be a positive int")
        
        if currency not in ("BTC", "USD"):
            raise ValueError("Currency not supported. Use: 'BTC' or 'USD")
        
        if not isinstance(outfile_raw, str):
            raise ValueError("outfile_raw variable must be a str")

        if not isinstance(outfile_df, str):
            raise ValueError("outfile_df variable must be a str")
        
        if not outfile_raw.lower().endswith(('.json')):
            raise ValueError("outfile_raw must be a JSON file")
        
        if not outfile_df.lower().endswith(('.csv')):
            raise ValueError("outfile_df must be a csv file")

    def _construct_url(self, symbol, limit, timestamp='none'):
        """
        Constructs URL compatible with cryptocompare API software to
        pull desired data. 

        Inputs:
        - symbol:           (str) Desired ticker symbol, e.g. "BTC"
        - limit:            (int) Number of ticks to request
        - timestamp:        (int) Timestamp of the latest date of dataset
        """

        if timestamp == 'none':
            url = ("https://min-api.cryptocompare.com/data/histo{}?fsym={}&tsym={}&limit={}&api_key={}".format(self._ticksize, symbol, self._currency, limit, self._key))
        else:
            url = ("https://min-api.cryptocompare.com/data/histo{}?fsym={}&tsym={}&limit={}&toTs={}&api_key={}".format(self._ticksize, symbol, self._currency, limit, timestamp, self._key))

        return url

    def _pull_data(self, symbol, limit, timestamp='none'):
        """
        Used to request and store data in JSON files from cryptocompare.
        Default call will return close prices of asset
        '''

        Inputs:
        - symbol:           (str) ticker symbol of desired coin
        - limit:            (int) number of ticks to request
        - timestamp:        (int) lastest timestamp of dataseries

        Output:
        - content:          (list, floats) list of close prices for
                            given data
        '''
        """

        address = self._construct_url(symbol, limit, timestamp)
        response = requests.get(address)
        content = response.json()

        if(content["Response"] == "Error"):
            raise RuntimeError(content["Message"])

        return content

    def get_data(self, plot=False):
        """
        Gets all available data for each asset in self.symbols
        from self._start_date to self._end_date. Stores data in outfiles

        Stores raw data in JSON format in self._outfile_raw and close 
        price dataframe in self._outfile_df.

        Output:
        - df:                   (pandas dataframe) of format:
                                df = {
                                      'index' : [<list of dattimes>]
                                      'asset1': [<list of close prices>]
                                      ...
                                     }
        
        Notes:
        - due to cryptocompares 2000 datapoint limit, calls greater than
        2000 data points will do it in several stages. E.g. for 5000
        data points will use 3 calls getting 2000, 2000 and 1000 points.
        - Gaps in data are extrapolated horizontally. 
        """

        # initialise dataframe
        # ---------------------------------------------------------------------
        if self._ticksize == "hour":
            freq = '1H'
        elif self._ticksize == "day":
            freq = '1D'
        elif self._ticksize == 'minute':
            freq = '1T'

        times = pd.date_range(start=self._start_date,
                              end=self._end_date, freq=freq)
        df = pd.DataFrame({'date': times})
        df = df.set_index('date')
        # ---------------------------------------------------------------------

        # Declare some params for extraction
        # ---------------------------------------------------------------------
        # Enddate timestamp (ms after 01/01/1970)
        enddate_stamp = (self._end_date - datetime(1970, 1, 1)).total_seconds()

        # Number of pulls needed to get self._lookback datapoints
        calls_needed = math.ceil(self._lookback/self._limit)
        final_call_limit = self._lookback % self._limit

        data_dict = {}
        # ---------------------------------------------------------------------

        # Get data for all assets
        for symbol in self._symbols:
            df[symbol] = 0.0  # initialise asset row in df

            # Extract data from api
            # -----------------------------------------------------------------
            data = []

            for i in range(1, calls_needed+1):
                if (i == calls_needed) and (final_call_limit > 0):
                    limit = final_call_limit
                else:
                    limit = self._limit

                # Request limit hours of data up to enddate_stamp
                content = self._pull_data(symbol, limit, enddate_stamp)

                # update timestamp for next request
                enddate_stamp = content["TimeFrom"]

                # store extracted data
                data.extend(content['Data'])
            # -----------------------------------------------------------------

            close_times = ([datetime.fromtimestamp(item['time'])
                           for item in data])
            if(self._ticksize == "day"):
                close_times = [time.date() for time in close_times]
            close_prices = [item["close"] for item in data]

            # Store data in dataframe
            # -----------------------------------------------------------------
            for i in range(df.shape[0]):
                date = df.index[i]
                if self._ticksize == "day":
                    date = date.date()
                try:
                    index = close_times.index(date)
                    df[symbol][i] = close_prices[index]
                except ValueError:
                    # if no data at date, assume the previous date's data
                    if i > 0:
                        df[symbol][i] = df[symbol][i-1]
            # -----------------------------------------------------------------

            data_dict[symbol] = data

            # redeclare end_stamp to pull next symbol data
            enddate_stamp = ((self._end_date - datetime(1970, 1, 1))
                             .total_seconds())        

        # save raw data and dataframe
        with open(self._outfile_raw, 'w') as json_file:
            json.dump(data_dict, json_file, indent=4)

        df.to_csv(self._outfile_df)

        if plot:
            df.plot()
            plt.show()

        return df
