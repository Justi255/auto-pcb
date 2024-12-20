import numpy as np
import shapely.geometry
import shapely.affinity

def min_bounding_rectangle(center, end):
    """
    Calculates the minimum bounding rectangle of a circle.

    Args:
        center: The coordinates of the center of the circle.
        end: The coordinates of the end of the radius of the circle.

    Returns:
        The coordinates of the four vertices of the minimum bounding rectangle.
    """

    # Calculate the radius of the circle.
    radius = np.sqrt((end.X - center.X)**2 + (end.Y - center.Y)**2)

    # Calculate the coordinates of the four vertices of the rectangle.
    left = center.X - radius
    right = center.X + radius
    top = center.Y - radius
    bottom = center.Y + radius

    # Return the coordinates of the four vertices of the rectangle.
    return left, right, top, bottom

def rotate(module, angle, center="center"):
    """
    Rotates a module by a given angle around a given center using Shapely and directly modifies the data.

    Args:
        Module: The module to be rotated.
        angle: The angle of rotation in degrees.
        center: The center of rotation.

    Returns:
        None.
    """
    # Create a Shapely polygon from the module.
    polygon = shapely.geometry.Polygon(module.poly)

    # Rotate the polygon.
    rotated_polygon = shapely.affinity.rotate(polygon, angle, origin=center)
    
    # Update the module's polygon.
    module.poly = list(rotated_polygon.exterior.coords)

    # Return the rotated polygon as a NumPy array.
    return module