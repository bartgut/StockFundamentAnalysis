import numpy as np
import pandas as pd
from pylab import mpl, plt

#Plotting settings
plt.style.use('seaborn-v0_8')
mpl.rcParams['font.family'] = 'serif'

#Loan class
class AmortizedLoan(object):
    def __init__(self, loan, interest_rate, years_number):
        self.loan = loan
        self.interest_rate = interest_rate
        self.years_number = years_number
        self.pa_param = (1 - (1 + self.interest_rate) ** (-self.years_number)) / self.interest_rate

    def calculate(self):
        current_date = np.datetime64('today', 'Y')
        years = np.arange(0, self.years_number, 1)
        years_date = np.arange(current_date, current_date + np.timedelta64(self.years_number, 'Y'), dtype='datetime64[Y]')
        annual_payment = self.loan / self.pa_param
        paid_interest = np.zeros(self.years_number)
        paid_principal = np.zeros(self.years_number)
        remaining_loan = np.zeros(self.years_number + 1)
        remaining_loan[0] = self.loan

        for t in range(self.years_number):
            paid_interest[t] = remaining_loan[t] * self.interest_rate
            paid_principal[t] = annual_payment - paid_interest[t]
            remaining_loan[t + 1] = remaining_loan[t] - paid_principal[t]

        loan_data = np.zeros(len(years),
                             dtype=[('Date', 'datetime64[Y]'),
                                    ('Payment', 'float64'),
                                    ('Interest', 'float64'),
                                    ('Principal', 'float64')])
        loan_data['Date'] = years_date
        loan_data['Payment'] = annual_payment
        loan_data['Interest'] = paid_interest.cumsum()
        loan_data['Principal'] = paid_principal.cumsum()

        self.loan_df = pd.DataFrame(loan_data).set_index('Date')

    def describe(self):
        return f"Total interest: {self.loan_df['Interest'][-1]}\n" \
               f"Annual payment: {self.loan / self.pa_param}"


loan = AmortizedLoan(400000, 0.062, 30)
loan.calculate()
loan_data = loan.loan_df

print(loan.describe())

#Plotting
plt.figure(figsize=(12,5))
ax1 = plt.subplot(121)
#Subplot 1
loan_data.plot(ax=ax1)
plt.title(f"Amortized loan of {loan.loan}$ from {loan.years_number} years with rate {loan.interest_rate}")

#Subplot 2
plt.subplot(122)
pie_labels = ['Interest', 'Principal']
pie_values = [loan_data['Interest'][-1], loan_data['Principal'][-1]]
plt.pie(pie_values, labels=pie_labels, autopct='%1.1f%%')

plt.show()



