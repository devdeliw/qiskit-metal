# This code was written by Deval Deliwala.
# 
# This code is to be used by QNL. 
# 
# Any modifications or derivative works of this code must retain this 
# notice, and modified files need to carry a notice indicating 
# that they have been altered from the originals. 

""" Bandage. 

.. code-block:: 

                        `top` 
      `top_left` _________|________ `top_right` 
                |                  |
                |                  |
                |                  | 
                |                  | 
       `left` - |         *        | - `right`
                |                  |
                |                  |  
                |                  | 
                |                  | 
                |                  | 
   `bottom_left` ‾‾‾‾‾‾‾‾‾|‾‾‾‾‾‾‾‾ `bottom_right` 
                      `bottom` 

 
""" 

import numpy as np 
from qiskit_metal import draw, Dict 
from qiskit_metal.qlibrary.core import QComponent 
from qiskit_metal.toolbox_python.utility_functions import rotate_point
from qiskit_metal.toolbox_python.positioning import NodePositioner


class Bandage(NodePositioner, QComponent): 
    """ 
    Inherits `QComponent` class. 

    Description: 
        A rectangular bandage structure. 

    Options: 
        * width   : width of the rectangle 
        * height  : height of the rectangle 
        * pos_x/_y: position of the bandage on chip
        * orientation : 0-> is parallel to x-axis, with orientation (in degrees) counterclockwise 
        * layer   : the layer number for the bandage

    """ 

    # Default drawing options 
    default_options = Dict(
        width='100um', 
        height='200um',
        pos_x='0um', 
        pos_y='0um', 
        orientation='0', 
        layer='1', 
    )

    # Component metadata
    # Name prefix for component, if user doesn't provide name 
    component_metadata = Dict( 
        short_name='bandage', 
        _qgeometry_table_poly='True', 
    )

    def make(self): 
        """ Convert self.options into QGeometry. """ 
        p = self.parse_options() # string options -> numbers 
        
        bandage = draw.rectangle(p.width, p.height)
        bandage = draw.rotate(bandage, p.orientation)
        bandage = draw.translate(bandage, p.pos_x, p.pos_y)

        # Converting drawing to qgeometry 
        self.add_qgeometry('poly', {'bandage': bandage}, layer=p.layer, subtract=True)

        # Positioning nodes 
        nodes = Dict() 
        nodes.origin    = np.zeros(2)
        nodes.top       = np.array((0, +p.height/2)) 
        nodes.bottom    = np.array((0, -p.height/2))
        nodes.left      = np.array((-p.width/2, 0)) 
        nodes.right     = np.array((+p.width/2, 0))
        nodes.top_left  = nodes.top + nodes.left 
        nodes.top_right = nodes.top + nodes.right 
        nodes.bottom_left   = nodes.bottom + nodes.left 
        nodes.bottom_right  = nodes.bottom + nodes.right

        # Moving all nodes along with component
        translation_vec = np.array((p.pos_x, p.pos_y)) 
        theta = np.deg2rad(p.orientation)
        for key, point in nodes.items():
            rotated = rotate_point(point, theta)
            nodes[key] = rotated + translation_vec
            
        self.nodes = nodes 
        return 

    def node(self, key): 
        return self.nodes.get(key, None) 
