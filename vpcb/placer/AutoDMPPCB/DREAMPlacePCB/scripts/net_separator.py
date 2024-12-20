import os
import sys
sys.path.append(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__))))
from Dataset import Dataset
sys.path.pop()
import scipy.sparse.csgraph as csgraph

import jax
from jax import jit, vmap, random, grad
from jax.example_libraries import optimizers
from jax import numpy as jnp

from functools import partial
import itertools

import numpy as np
import numpy.random as npr
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import collections as mc

import datetime
from tqdm import tqdm
import pdb

DEBUG=0
# read raw database
print(os.getcwd())
rawdb = Dataset(input_file_path="../../../../../examples/test_data/bm1/bm1.unrouted.kicad_pcb")
rawdb.load()

# write back path
path = "./output/bm1"
img_path = os.path.join(path,"plot")
os.makedirs(path, exist_ok=True)
os.makedirs(img_path, exist_ok=True)
        
"""net separator vars """
jax.config.update('jax_platform_name', 'cpu')

netss = [net.padlist for net in rawdb.Nets if len(net.pads)>= 2]
num_nets = len(netss)
num_nodes = len(rawdb.Nodes)
adj=np.zeros((num_nodes,num_nodes))
for netid, net in enumerate(netss):
    for padid1 in net:
        for padid2 in net:
            adj[rawdb.Pads[padid1].node_index,rawdb.Pads[padid2].node_index] += 1
A = adj
N = A.shape[0]
v = np.ones(N)
D = np.diag(v)
b = jnp.zeros(N)
d = jnp.zeros(N)

minx, miny, maxx, maxy = rawdb.layout
c1 = maxx-minx
c2 = maxy-miny
c3 = 0
C = jnp.block([[c1, c3],[c3, c2]])
assert c1*c2 >= c3
assert np.linalg.det(C) > 1e-5

"""net separator fns """
X_k = np.random.normal(size=(A.shape[0],2))
alpha=1e-2

def pairwise_dist(X):
    euc = lambda x: vmap(lambda y: jnp.linalg.norm(jnp.maximum(jnp.abs(x-y), eps))**2)(X)
    return vmap(euc)(X)

def _ec(X, U_i, r_i, A_i, B_i):
    
    # 打印输入变量的大小
    if DEBUG:
        print(f"X shape: {X.shape}")
        print(f"U_i shape: {U_i.shape}")
        print(f"r_i shape: {r_i.shape}")
        print(f"A_i shape: {A_i.shape}")
        print(f"B_i shape: {B_i.shape}")
    
    # 计算 term1
    A_i_T = A_i.T
    A_i_T_X = A_i_T @ X
    A_i_T_X_U_i = A_i_T_X @ U_i
    ones_vector = jnp.ones(U_i.shape[-1])
    r_i_plus_1 = (r_i + 1) * ones_vector
    term1 = -A_i_T_X_U_i + r_i_plus_1
    
    # 打印 term1 的中间结果大小
    if DEBUG:
        print(f"A_i.T shape: {A_i_T.shape}")
        print(f"A_i.T @ X shape: {A_i_T_X.shape}")
        print(f"A_i.T @ X @ U_i shape: {A_i_T_X_U_i.shape}")
        print(f"(r_i + 1) * ones shape: {r_i_plus_1.shape}")
        print(f"term1 shape: {term1.shape}")
    
    # 计算 term2
    B_i_T = B_i.T
    B_i_T_X = B_i_T @ X
    B_i_T_X_U_i = B_i_T_X @ U_i
    r_i_minus_1 = (r_i - 1) * ones_vector
    term2 = B_i_T_X_U_i - r_i_minus_1
    
    # 打印 term2 的中间结果大小
    if DEBUG:
        print(f"B_i.T shape: {B_i_T.shape}")
        print(f"B_i.T @ X shape: {B_i_T_X.shape}")
        print(f"B_i.T @ X @ U_i shape: {B_i_T_X_U_i.shape}")
        print(f"(r_i - 1) * ones shape: {r_i_minus_1.shape}")
        print(f"term2 shape: {term2.shape}")
    
    # 裁剪 term1 和 term2
    clipped_term1 = jnp.clip(term1, eps, None)
    clipped_term2 = jnp.clip(term2, eps, None)
    
    # 打印裁剪后的结果大小
    if DEBUG:
        print(f"clipped_term1 shape: {clipped_term1.shape}")
        print(f"clipped_term2 shape: {clipped_term2.shape}")
    
    # 计算范数
    norm1 = jnp.linalg.norm(clipped_term1)
    norm2 = jnp.linalg.norm(clipped_term2)
    
    # 计算结果
    result = norm1**2 + norm2**2    
    
    return X, U_i, r_i, A_i, B_i, term1, term2, clipped_term1, clipped_term2, norm1, norm2, result
    # return jnp.linalg.norm(jnp.clip(-A_i.T@X@U_i + (r_i + 1)*jnp.ones(U_i.shape[-1]), eps))**2 + \
    #        jnp.linalg.norm(jnp.clip(B_i.T@X@U_i - (r_i - 1)*jnp.ones(U_i.shape[-1]), eps))**2
    
def ec_objective(params, A, B):
    X, U, r = params
    X, U_i, r_i, A_i, B_i, term1, term2, clipped_term1, clipped_term2, norm1, norm2, result = vmap(partial(_ec, X))(U, r, A, B)
    
    if DEBUG:
        print(f"X shape: {X.shape}")
        print(f"U_i shape: {U_i.shape}")
        print(f"r_i shape: {r_i.shape}")
        print(f"A_i shape: {A_i.shape}")
        print(f"B_i shape: {B_i.shape}")
        print(f"term1 shape: {term1.shape}")
        print(f"term2 shape: {term2.shape}")
        print(f"clipped_term1 shape: {clipped_term1.shape}")
        print(f"clipped_term2 shape: {clipped_term2.shape}")
        print(f"result shape: {result.shape}")
        print(f"norm1 shape: {norm1.shape}")
        print(f"norm2 shape: {norm2.shape}")

        print(f"X: {X}")
        print(f"U_i: {U_i}")
        print(f"r_i: {r_i}")
        print(f"A_i: {A_i}")
        print(f"B_i: {B_i}")
        print(f"term1: {term1}")
        print(f"term2: {term2}")
        print(f"clipped_term1: {clipped_term1}")
        print(f"clipped_term2: {clipped_term2}")
        print(f"result: {result}")
        print(f"norm1: {norm1}")
        print(f"norm2: {norm2}")
        
    return jnp.sum(result)

@jit
def ec_step(i, opt_state, edgetensor, fixed_idx=None):
    params = get_params(opt_state)
    g = grad(ec_objective)(params, edgetensor, edgetensor)
    #g_0 = jax.ops.index_update(g[0], fixed_idx, 0)
    g_0 = g[0].at[jnp.array(fixed_idx)].set(0)
    g = (g_0,g[1],g[2])
    return opt_update(i, g, opt_state)

def stress(params, W, D):
    X,_,_ = params
    return jnp.trace(X.T@(D-W)@X) + l*jnp.linalg.norm(X)**2

@jit
def step(i, opt_state, W, D, idx, fixed_idx=None):
    p,U,r = get_params(opt_state)
    g = grad(stress)((p[idx],U,r), W[jnp.ix_(idx,idx)], D[jnp.ix_(idx,idx)])
    #g_0 = jax.ops.index_add(jnp.zeros_like(p), idx, g[0], 
    #                      indices_are_sorted=False, unique_indices=True)
    g_0 = jnp.zeros_like(p).at[jnp.array(idx)].add(g[0])
    #g_0 = jax.ops.index_update(g_0, fixed_idx, 0)
    g_0 = g_0.at[jnp.array(fixed_idx)].set(0)
    g = (g_0, g[1], g[2])
    return opt_update(i, g, opt_state)

def rescale(X_transformed, minx, maxx, miny, maxy):
    X_transformed_x_rescaled = minx + ((X_transformed[:,0] - X_transformed[:,0].min())*(maxx - minx))/(X_transformed[:,0].max() - X_transformed[:,0].min())
    X_transformed_y_rescaled = miny + ((X_transformed[:,1] - X_transformed[:,1].min())*(maxy - miny))/(X_transformed[:,1].max() - X_transformed[:,1].min())
    #X_transformed_x_rescaled = np.minimum(np.maximum(minx, X_transformed[:,0]+minx+(maxx-minx)/2), maxx)
    #X_transformed_y_rescaled = np.minimum(np.maximum(miny, X_transformed[:,1]+miny+(maxy-miny)/2),maxy)
    X_transformed_rescaled = np.stack([X_transformed_x_rescaled,X_transformed_y_rescaled],axis=-1)
    return X_transformed_rescaled

d = csgraph.shortest_path(adj, directed=False, unweighted=False)
d = np.nan_to_num(d,nan=0.0, posinf=np.where(np.isinf(d),-np.Inf,d).max()+1)
# weights
eps = 1e-8
w = jnp.square(jnp.reciprocal(d + np.eye(*d.shape)))
w = w - jnp.diag(jnp.diag(w))
l = 0
dd = np.ones_like(w)
for i in range(w.shape[0]):
    for j in range(w.shape[1]):
        dd[i,j]*=10*(max(rawdb.Nodes[i].height,rawdb.Nodes[i].width) + max(rawdb.Nodes[j].height,rawdb.Nodes[j].width))

d = d * dd

nx = np.array([node.x_left for node in rawdb.Nodes])
ny = np.array([node.y_bottom for node in rawdb.Nodes])

w = (adj > 0)
positions = np.vstack([nx,ny]).T
numedges = jnp.where(w == 1)[0].shape[0]
edgetensor = np.zeros((numedges,)+positions.shape)
edgelist = jnp.where(w == 1)
for i in range(numedges):
    e1 = edgelist[0][i].item()
    e2 = edgelist[1][i].item()
    edgetensor[i,e1,0] = 1
    edgetensor[i,e2,1] = 1
edgetensor = jnp.array(edgetensor)
w = adj
d = np.diag(w.sum(0) + 0.1)

seed = 0
# initialise an array of 2D positions
rng = random.PRNGKey(seed)

K=w
pi = jnp.zeros(K.shape)
x = jnp.zeros(K.shape)
U = jnp.ones((numedges,2))
r = jnp.ones(numedges)
# show the shortest paths in a heat map.
# If any squares are white, then infinite paths exist and the algorithm will fail.
plt.imshow(d)
plt.savefig(os.path.join(img_path, "d.png"))
n = d.shape[0]
fixed_idx = [i for i,node in enumerate(rawdb.Nodes) if node.lock==True]

#embedding = SpectralEmbedding(n_components=2, affinity='precomputed')
#X_transformed = embedding.fit_transform(w)

X_transformed = np.asarray(random.normal(rng, (n,2)))
X_transformed_rescaled = X_transformed

X_transformed_rescaled = rescale(X_transformed, minx, maxx, miny, maxy)
init_positions = np.array([ip if rawdb.Nodes[i].lock==False else [rawdb.Nodes[i].x_left,rawdb.Nodes[i].y_bottom] 
                           for i,ip in enumerate(X_transformed_rescaled) ])
m = np.array([(maxx + minx) / 2,(maxy + miny) / 2])
init_positions = init_positions - m
params = (init_positions, U, r)
opt_init, opt_update, get_params = optimizers.adam(5e-2, b1=0.9, b2=0.999, eps=1e-08)
opt_state = opt_init(params)

eta=1e-2
l=1e-1
itercount = itertools.count()

stress_hist = []
ec_hist = []
cvx_clst_hist = []
param_hist = []

for i in tqdm(range(1000)):
    idx = np.arange(n)
    for _ in range(10):
        opt_state = ec_step(i, opt_state, edgetensor, fixed_idx=fixed_idx)
    for _ in range(1):
        opt_state = step(i, opt_state, w, d, idx, fixed_idx=fixed_idx)
    
    params = get_params(opt_state)
    param_hist.append(params)
    stress_hist.append(stress(params, w, d))
    ec_hist.append(ec_objective(params, edgetensor, edgetensor))
        
end = datetime.datetime.now()
plt.plot(stress_hist)
plt.title(stress(params, w, d))
plt.savefig(os.path.join(img_path, "stress.png"))

tp = params[0] + m
xt = rescale(tp, minx, maxx, miny, maxy)
compx = xt[:,0]
compy = xt[:,1]

# update raw database
rawdb.update_nodes(compx[:rawdb.num_movable_nodes], compy[:rawdb.num_movable_nodes])
        
# write placement solution
gp_out_file = os.path.join(
    path,
    "%s.unrouted.%s" % ("bm1", "kicad_pcb"))
rawdb.wirte_back(gp_out_file)