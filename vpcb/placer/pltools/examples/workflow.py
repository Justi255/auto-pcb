# Desc: Example of using the framework
''' 
[not finished yet] Only protype this time
'''
import pltools.dataset as dataset
import pltools.modeling as modeling
import pltools.analyzer as analyzer
import pltools.checker as checker
import pltools.placer as placer
import pltools.optimizer as optimizer
import pltools.visualizer as visualizer

# load data
dataset = dataset.Dataset("data.txt")
data = dataset.load()

# buld model
model = modeling.Model()
model_data = model.build_model(data)

# analyze data and layout
analyzer = analyzer.Analyzer(data, model_data)
analyzer.analyze()

# place the components
placer = placer.Placer(analyzer.info, model_data)
placer.place_component()

# optimize the layout
optimizer = optimizer.Optimizer(analyzer.info, model_data)
optimizer.configure_optimizer()
optimizer.run()

# check validation and scoring
checker = checker.Checker(data, model_data)
checker.check_validation()
checker.scoring()

# visualization layout and analysis statistics
visualizer = visualizer.Visualizer(canvas_width=None, canvas_height=None)
visualizer.add_object(obj_list=None)
visualizer.visualize_layout()
