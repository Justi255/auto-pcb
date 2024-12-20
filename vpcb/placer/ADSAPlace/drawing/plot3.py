import numpy as np
import math
from matplotlib import pyplot as plt
from scipy.signal import savgol_filter

data = np.loadtxt('c1.txt')
#data2 = np.loadtxt('s.txt')
#data3 = np.loadtxt('g.txt')
datac = np.loadtxt('c2.txt')


x = np.linspace(1,len(datac),len(datac))

plt.figure()
fig, ax = plt.subplots(1,1,figsize=(12,7))
# plt.figure()
ax.plot(x, data, color='k',label='no alignment',alpha = 0.7)
ax.plot(x, datac, color='r',label='add alignment',  alpha = 0.7)
# ax.plot(x, data2, color='#7fe2b3',label='Spiral_placement',alpha = 0.7)
# ax.plot(x, data3, color='#cba0e6',label='Greedy_placement',alpha = 0.7)
# plt.ylim(1000,4000)
# plt.xlim(10000,14000)
plt.legend()
plt.xlabel('Moves/250n')
plt.ylabel('best_overlap')
plt.savefig('Cost function.jpg')
plt.close()


# plt.figure()
# plt.plot(x, Data_0, 'r', label='Center_placement')
# plt.plot(x, Data_1, 'k', label='Spiral_placement')
# plt.plot(x, Data_2, 'b', label='Greedy_placement')
# plt.legend()
# #plt.xlim(1700000,1800000)
# #plt.ylim(1500,7000)
# #plt.ylim(0,1e9)
# plt.xlabel('Moves')
# plt.ylabel('cost')
# plt.savefig('benchmark_Cost_Move.jpg')
# plt.close()
