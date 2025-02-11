import time
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

def measure_time_complexity(func, inputs):
    times = []
    for inp in inputs:
        start = time.time()
        func(inp)
        end = time.time()
        times.append(end - start)
    return np.array(times)

# Define complexity functions
def O_1(n, a, b): return a + b * np.ones_like(n)
def O_log_n(n, a, b): return a + b * np.log(n)
def O_n(n, a, b): return a + b * n
def O_n_log_n(n, a, b): return a + b * n * np.log(n)
def O_n2(n, a, b): return a + b * n**2
def O_n3(n, a, b): return a + b * n**3
def O_2n(n, a, b): return a + b * 2**n

def estimate_complexity(n_values, times):
    functions = {
        "O(1)": O_1,
        "O(log n)": O_log_n,
        "O(n)": O_n,
        "O(n log n)": O_n_log_n,
        "O(n^2)": O_n2,
        "O(n^3)": O_n3,
        "O(2^n)": O_2n,
    }
    
    best_fit = None
    best_error = float("inf")
    best_label = None
    
    for label, func in functions.items():
        try:
            popt, _ = curve_fit(func, n_values, times, maxfev=5000)
            predicted_times = func(n_values, *popt)
            error = np.linalg.norm(times - predicted_times)
            if error < best_error:
                best_fit = predicted_times
                best_error = error
                best_label = label
        except:
            continue
    
    # Plot results
    plt.figure(figsize=(8, 5))
    plt.scatter(n_values, times, label="Measured Times", color="blue")
    if best_fit is not None:
        plt.plot(n_values, best_fit, label=f"Best Fit: {best_label}", color="red")
    plt.xlabel("Input Size (n)")
    plt.ylabel("Execution Time (seconds)")
    plt.legend()
    plt.title("Time Complexity Estimation")
    plt.show()
    
    return best_label

# Example usage:
def example_function(n):
    return [i**2 for i in range(n)]

n_values = np.array([10, 100, 500, 1000, 5000, 10000])
times = measure_time_complexity(example_function, n_values)
complexity = estimate_complexity(n_values, times)
print("Estimated Complexity:", complexity)
