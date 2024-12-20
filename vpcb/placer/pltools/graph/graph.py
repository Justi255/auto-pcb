from pltools.dataset import Dataset
from pltools.graph.layout import spring_layout, partitioned_spring_layout

import networkx as nx
import matplotlib.pyplot as plt

## load the board to be placed
banchmark = "bm3"
db = Dataset()
db.load(f'src/pltools/examples/testdata/tmp/PCBBenchmarks/{banchmark}/{banchmark}.unrouted.kicad_pcb')

# Create a graph
graph = nx.Graph()

# Add nodes for modules, nets, and pads
for module in db.Get_Modules():
    graph.add_node(module.id, node_color='purple', size=1000, label=module.name, subset=module.part_id)


# Add edges to represent connections
for net in db.Get_Nets():
    if len(net.module_id)==2:
        graph.add_edge(net.module_id[0], net.module_id[1], edge_color = 'black')
    elif len(net.module_id)>2:
        graph.add_node(net.name, node_color='green', size=300, label=net.name, subset='hypernet')
        # for module_id in net.module_id:
        #     graph.add_edge(net.name, module_id, edge_color = 'green')

# Extract node colors and sizes
node_sizes = [data['size'] for node, data in graph.nodes(data=True)]
node_colors = [data['node_color'] for node, data in graph.nodes(data=True)]
edge_colors = [data['edge_color'] for _, _, data in graph.edges(data=True)]


# Visualize the graph
pos = partitioned_spring_layout(graph, repulsion_factor=1)  #layout algorithms 
# pos = spring_layout(graph)  #layout algorithms 
nx.draw(graph, pos, with_labels=True, font_weight='bold', node_color=node_colors, node_size=node_sizes,
        font_size=6, edge_color=edge_colors, linewidths=0.5)

plt.show()




