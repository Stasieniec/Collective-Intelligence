import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

# Define the functions
def P_join(n, a):
    return 0.03 + 0.48 * (1 - np.exp(-a * n))

def P_leave(n, b):
    return np.exp(-b * n)

# Generate data
n_values = np.array([0, 1, 2, 3])
P_join_values = P_join(n_values, 0.6)  # Use initial guess for 'a'
P_leave_values = P_leave(n_values, 2.1)  # Use initial guess for 'b'

# Plot the data
plt.figure(figsize=(10, 5))

# Plot P_join
plt.subplot(1, 2, 1)
plt.plot(n_values, P_join_values, 'o-', label='P_join')
plt.xlabel('n')
plt.ylabel('P_join')
plt.title('P_join vs n')
plt.legend()

# Plot P_leave
plt.subplot(1, 2, 2)
plt.plot(n_values, P_leave_values, 'o-', label='P_leave')
plt.xlabel('n')
plt.ylabel('P_leave')
plt.title('P_leave vs n')
plt.legend()

# Optimize parameters
popt_join, pcov_join = curve_fit(P_join, n_values, P_join_values)
popt_leave, pcov_leave = curve_fit(P_leave, n_values, P_leave_values)

# Generate optimized curves
n_fit = np.linspace(0, 5, 100)
P_join_fit = P_join(n_fit, *popt_join)
P_leave_fit = P_leave(n_fit, *popt_leave)

# Plot optimized curves
plt.subplot(1, 2, 1)
plt.plot(n_fit, P_join_fit, label='Optimized P_join')
plt.legend()

plt.subplot(1, 2, 2)
plt.plot(n_fit, P_leave_fit, label='Optimized P_leave')
plt.legend()

plt.show()

print("Optimized parameters for P_join:", popt_join)
print("Optimized parameters for P_leave:", popt_leave)
