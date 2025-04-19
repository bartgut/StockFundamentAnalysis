import numpy as np;
import matplotlib.pyplot as plt

# data
interest_rate = 0.065
payment_frequency = 10
money_to_earn = 20000.0
years = 10

years_array = np.arange(0, years, 1)

# Calculations
roi = money_to_earn*(1 + interest_rate/payment_frequency)**(-1*years_array*payment_frequency)

print(f"You would need to invest: {roi[years-1]} to earn {money_to_earn} in {years} years")

#Plot
plt.figure(figsize=(8,5))
plt.plot(years_array, np.flip(roi), marker='o', linestyle='-', label=f'Periodic({payment_frequency} payments per year)')
plt.title("ROI yearly")
plt.xlabel('Year')
plt.ylabel('ROI ($)')
plt.grid(True)
plt.legend()
plt.show()
