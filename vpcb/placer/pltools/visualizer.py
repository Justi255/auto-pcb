# Desc: visualization
import matplotlib.pyplot as plt
import matplotlib.patches as patches

##TODO: add polygen visualiazation from matplotlib.patches import Polygon as MatplotlibPolygon

class VisualObject:
    def __init__(self, x, y, shape='rectangle', size1=None, size2=None, color='blue'):
        self.x = x
        self.y = y
        self.shape = shape
        self.size1 = size1
        self.size2 = size2
        self.color = color

class Visualizer:
    def __init__(self, canvas_width, canvas_height):
        self.objects = []
        self.canvas_width = canvas_width
        self.canvas_height = canvas_height
        self.fig, self.ax = plt.subplots()
        self.current_frame = []

    def add_object(self, visual_object):
        self.objects.extend(visual_object)

    def frame_objects(self):
        #config the canvas
        self.ax.set_aspect('equal')
        self.ax.set_xlim(0, self.canvas_width)  # Set canvas limits
        self.ax.set_ylim(0, self.canvas_height)
        self.ax.invert_yaxis() ##invert y axis to match the kicad coordinate system
        #place the objects
        for obj in self.objects:
            if obj.shape == 'rectangle':
                rect = patches.Rectangle((obj.x, obj.y), obj.size1, obj.size2, color=obj.color, ec = "black")
                self.current_frame.append(self.ax.add_patch(rect))
            elif obj.shape == 'circle':
                circle = patches.Circle((obj.x, obj.y), obj.size1, color=obj.color)
                self.current_frame.append(self.ax.add_patch(circle))
            elif obj.shape == 'polygon':
                polygon = patches.Polygon(obj.size1)
                self.current_frame.append(self.ax.add_patch(polygon))


    def visualize_layout(self, framing_on=False, frames=None, save_gif=False):
        if not framing_on:
            self.frame_objects()
            plt.show()
        else:
            if frames == None :
                raise Exception("framing is on, please input frames[]")
            else:
                import matplotlib.animation as animation
                ani = animation.ArtistAnimation(self.fig, frames, interval=200, blit=True)
                if save_gif:
                    ani.save('../output/output.gif')
                plt.show()


#example usage
if __name__ == '__main__':

    def print_config(visualizer, framing_on):
        print("***************************************************")
        print("canvas_width = ", visualizer.canvas_width)
        print("canvas_height = ", visualizer.canvas_height)
        print("faming = ", framing_on)
        print("***************************************************")

#example objects
    obj1 = VisualObject(2, 3, 'rectangle', 2,2, 'red')
    obj2 = VisualObject(5, 5, 'circle', 1.5, 1, 'green')
    obj3 = VisualObject(7, 2, 'rectangle', 1,1, 'blue')
    obj_list = [obj1, obj2, obj3]

#visualize one frame
    visualizer1 = Visualizer(20,10)    
    visualizer1.add_object(obj_list)

    print_config(visualizer1, False)
    visualizer1.visualize_layout()

#visualize multiple frames
    frames = [] #list containing frames

    ##initialial frame
    visualizer2 = Visualizer(20,10)
    visualizer2.add_object(obj_list)
    #update method for framing
    def update_frame():
        visualizer2.current_frame = []  # Clear the current frame
        for obj in visualizer2.objects:
            obj.x += 1
            obj.y += 1
    #generate frames         
    for i in range(10):
        visualizer2.frame_objects()
        frames.append(visualizer2.current_frame)
        update_frame()
    
    print_config(visualizer2, True)
    visualizer2.visualize_layout(framing_on=True, frames=frames, save_gif=True)




