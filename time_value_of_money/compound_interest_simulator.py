import numpy as np
import pandas as pd
from pylab import mpl, plt

#Plotting settings
plt.style.use('seaborn-v0_8')
mpl.rcParams['font.family'] = 'serif'

# data
monthly_investment = 800
bond_interest_rate = 0.065
years = 18
months_number = 12 * years

# calculations
current_date = np.datetime64('today', 'M')
months = np.arange(0, months_number, 1)
months_dates = np.arange(current_date, current_date + np.timedelta64(months_number, 'M'), dtype='datetime64[M]')

invested_cash = np.arange(0, 12*years*monthly_investment, monthly_investment)
growth_factor = (1+bond_interest_rate)**(1/12)

roi_yearly = monthly_investment*((1-growth_factor**months)/(1-growth_factor))


months_with_roi = np.zeros(len(roi_yearly),
                           dtype=[('date', 'datetime64[M]'), ('Invested cash', 'float64'), ('ROI', 'float64')])
months_with_roi['date'] = months_dates
months_with_roi['Invested cash'] = invested_cash
months_with_roi['ROI'] = roi_yearly

df = pd.DataFrame(months_with_roi).set_index('date')

print(invested_cash[-5:])
print(roi_yearly[-5:])

#Plotting
df.plot(figsize=(8,5))
plt.title(f"Investing {monthly_investment} PLN each month in a bond with interest rate of {bond_interest_rate}")
plt.show()