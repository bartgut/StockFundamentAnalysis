import numpy as np
import pandas as pd
from pylab import mpl, plt
import sqlite3

#Plotting settings
plt.style.use('seaborn-v0_8')
mpl.rcParams['font.family'] = 'serif'

#data
loan = 1490000 #1176597.25 #958828.05
yearly_interest_rate = 0.0628
grace_period = 5
repayment_months = 114 #109

#dates
current_date = np.datetime64('today', 'M')
months = np.arange(current_date, current_date + np.timedelta64(repayment_months, 'M'), dtype='datetime64[M]')

#calculations
paid_principal = np.round(np.full(repayment_months, loan/(repayment_months-grace_period)), decimals=2)
paid_principal[:grace_period] = 0
paid_interest = np.zeros(repayment_months)
remaining_loan = np.zeros(repayment_months + 1)
remaining_loan[0] = loan
for t in range(repayment_months):
    paid_interest[t] = np.round(remaining_loan[t] * yearly_interest_rate/12, decimals=2)
    remaining_loan[t + 1] = np.round(remaining_loan[t] - paid_principal[t])

df = pd.DataFrame({
    "Paid Principal": paid_principal,
    "Paid Interest": paid_interest,
    "Remaining Loan": remaining_loan[:-1],
}).set_index(months)

df['Installment'] = np.round(df['Paid Principal'] + df["Paid Interest"], decimals=2)
df['Paid cumulative interest'] = np.round(df['Paid Interest'].cumsum(), decimals=2)

df[['Installment', 'Paid cumulative interest']].plot(figsize=(11,5), secondary_y='Paid cumulative interest')

plt.show()






