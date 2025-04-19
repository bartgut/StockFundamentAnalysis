import numpy as np
import matplotlib.pyplot as plt

# Data
initial_investment = 10000.0
interest_rate = 0.065
years = np.arange(0, 20, 1)

#Calculations
roi_simple_per_year = (1 + interest_rate*years)*initial_investment
roi_periodic_year = (1 + interest_rate)**years * initial_investment
roi_periodic_semi_year = (1 + interest_rate/2)**(years*2)*initial_investment
roi_periodic_monthly = (1 + interest_rate/12)**(years*12)*initial_investment

#Plot
plt.figure(figsize=(8,5))
plt.plot(years, roi_simple_per_year, marker='o', linestyle='-', label='Simple ROI')
plt.plot(years, roi_periodic_year, marker='o', linestyle='-', label='Periodic(yearly payments)')
plt.plot(years, roi_periodic_semi_year, marker='o', linestyle='-', label='Periodic(semiyearly payments)')
plt.plot(years, roi_periodic_monthly, marker='o', linestyle='-', label='Periodic(monthly payments)')
plt.title("ROI over next 20 years")
plt.xlabel('Year')
plt.ylabel('ROI ($)')
plt.grid(True)
plt.legend()
plt.show()