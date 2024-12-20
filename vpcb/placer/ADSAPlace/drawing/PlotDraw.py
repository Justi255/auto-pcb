import numpy as np
import pandas as pd
from matplotlib import pyplot as plt

pd.plotting.register_matplotlib_converters()

data0 = np.loadtxt('placement_cost.txt')
data1 = np.loadtxt('routing_cost.txt')

n = np.linspace(1, len(data0), len(data1))

plt.figure()
plt.scatter(data0, data1)
plt.legend()
#plt.plot(n, data2)
plt.xlabel('Placement_cost')
plt.ylabel('Routing_cost')
plt.savefig('P&R.jpg')
plt.close()
