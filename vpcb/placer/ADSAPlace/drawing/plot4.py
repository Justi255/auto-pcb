import numpy as np
from matplotlib.patches import  ConnectionPatch
from matplotlib import pyplot as plt

def zone_and_linked(ax,axins,zone_left,zone_right,x,y,linked='bottom',
                    x_ratio=0.05,y_ratio=0.05):
    xlim_left = x[zone_left]-(x[zone_right]-x[zone_left])*x_ratio
    xlim_right = x[zone_right]+(x[zone_right]-x[zone_left])*x_ratio

    y_data = np.hstack([yi[zone_left:zone_right] for yi in y])
    ylim_bottom = np.min(y_data)-(np.max(y_data)-np.min(y_data))*y_ratio
    ylim_top = np.max(y_data)+(np.max(y_data)-np.min(y_data))*y_ratio

    axins.set_xlim(xlim_left, xlim_right)
    axins.set_ylim(ylim_bottom, ylim_top)

    ax.plot([xlim_left,xlim_right,xlim_right,xlim_left,xlim_left],
            [ylim_bottom,ylim_bottom,ylim_top,ylim_top,ylim_bottom],"black")

    if linked == 'bottom':
        xyA_1, xyB_1 = (xlim_left,ylim_top), (xlim_left,ylim_bottom)
        xyA_2, xyB_2 = (xlim_right,ylim_top), (xlim_right,ylim_bottom)
    elif  linked == 'top':
        xyA_1, xyB_1 = (xlim_left,ylim_bottom), (xlim_left,ylim_top)
        xyA_2, xyB_2 = (xlim_right,ylim_bottom), (xlim_right,ylim_top)
    elif  linked == 'left':
        xyA_1, xyB_1 = (xlim_right,ylim_top), (xlim_left,ylim_top)
        xyA_2, xyB_2 = (xlim_right,ylim_bottom), (xlim_left,ylim_bottom)
    elif  linked == 'right':
        xyA_1, xyB_1 = (xlim_left,ylim_top), (xlim_right,ylim_top)
        xyA_2, xyB_2 = (xlim_left,ylim_bottom), (xlim_right,ylim_bottom)
        
    con = ConnectionPatch(xyA=xyA_1,xyB=xyB_1,coordsA="data",
                          coordsB="data",axesA=axins,axesB=ax)
    axins.add_artist(con)
    con = ConnectionPatch(xyA=xyA_2,xyB=xyB_2,coordsA="data",
                          coordsB="data",axesA=axins,axesB=ax)
    axins.add_artist(con)

data = np.loadtxt('s1.txt')
data1 = np.loadtxt('s2.txt')
# data2 = np.loadtxt('gr2.txt')


x = np.linspace(1,len(data),len(data))
# x2 = np.linspace(1,len(data2),len(data2))
# x3 = np.linspace(1,len(data3),len(data3))



fig, ax = plt.subplots(1,1,figsize=(12,7))
# plt.figure()
ax.plot(x, data, color='#f0bc94',label='no alignment',alpha = 0.7)
ax.plot(x, data1, color='#7fe2b3',label='add alignment',alpha = 0.7)
#ax.plot(x, data2, color='#cba0e6',label='stride 2500',alpha = 0.7)

# axins = ax.inset_axes((0.4, 0.1, 0.4, 0.3))
axins = ax.inset_axes((0.3, 0.2, 0.4, 0.4))

# 在缩放图中也绘制主图所有内容，然后根据限制横纵坐标来达成局部显示的目的
axins.plot(x,data,color='#f0bc94',label='No regression',alpha=0.7)
axins.plot(x,data1,color='#7fe2b3',label='stride 1250',alpha=0.7)
#axins.plot(x,data2,color='#cba0e6',label='stride 2500',alpha=0.7)

# 局部显示并且进行连线
#zone_and_linked(ax, axins, 300, 1200, x , [data,data1,data2], 'top')
zone_and_linked(ax, axins, 10, 2929, x , [data,data1], 'top')

plt.legend()
plt.xlabel('Move_250s/per elements')
plt.ylabel('Best_overlap')
plt.savefig('cost_function1.jpg')
plt.close()
