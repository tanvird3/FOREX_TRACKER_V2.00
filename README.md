# Currency pair tracker (updates every minute)
This app pulls data from Alpha Vantage Foreign Currency Intraday Trading API and does basic technical analysis. It also updates the charts on a per minute basis. 

### Parameters For the Indicators (coder's assumptions, you are advised to use your own prudence)

#### Bollinger Band: 2 Standard Deviation
#### MACD: n_slow=26, n_fast=12, n_sign=9
#### RSI: n_period=60, Resistance and Support are put at 55 and 45 respectively

### Known Issues:

1. Due to the free API callback limit of Alpha Vantage, even if items are changed from the dropdown menus, the charts may not get updated before the 1 minute designated time. A premium subscription can be bought to have a better experience.

2. Data pulled from Alpha Vantage are only upto 4 decimal places, thus the charts might not be as precise as they should be. 