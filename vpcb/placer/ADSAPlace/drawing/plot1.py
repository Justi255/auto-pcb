import numpy as np
import math
from matplotlib import pyplot as plt
from scipy.signal import savgol_filter

data = np.loadtxt('center9.txt')
data2 = np.loadtxt('spiral9.txt')
data3 = np.loadtxt('greedy9.txt')
# center = np.convolve(data,100000,'valid')
# y = data[0::100000]
# y2 = data2[0::100000]
# y3 = data3[0::100000]
#yhat = savgol_filter(data, 1000000, 3)
data_1 = []
q=1
minx = data[0]
while q < len(data):
    if(data[q] < minx):
        data_1.append(data[q])
        minx = data[q]
    q += 1
x1 = np.linspace(1,len(data_1),len(data_1))

data_2 = []
w=1
minw = data2[0]
while w < len(data2):
    if(data2[w] < minw):
        data_2.append(data2[w])
        minw = data2[w]
    w += 1
x2 = np.linspace(1,len(data_2),len(data_2))

data_3 = []
e=1
mine = data3[0]
while e < len(data3):
    if(data3[e] < mine):
        data_3.append(data3[e])
        mine = data3[e]
    e += 1
x3 = np.linspace(1,len(data_3),len(data_3))

plt.figure()
plt.plot(x1, data_1, label='Center_placement')
plt.plot(x2, data_2, label='Spiral_placement')
plt.plot(x3, data_3, label='Greedy_placement')
# plt.ylim(3000,4000)
plt.legend()
plt.xlabel('Moves')
plt.ylabel('cost')
plt.savefig('benchmark_Cost_Move.jpg')
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
