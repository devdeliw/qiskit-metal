# This code was written by Deval Deliwala.
# 
# This code is to be used by QNL. 
# 
# Any modifications or derivative works of this code must retain this 
# notice, and modified files need to carry a notice indicating 
# that they have been altered from the originals. 

""" AlignmentMarker. 

.. code-block:: 

    _________________________
   |                         |
   |                         |
   |                         | 
   |                         |
   |            *            |
   |                         |
   |                         |  
   |                         |
   |                         |
    ‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾

"""

import numpy as np 
from qiskit_metal import draw, Dict 
from qiskit_metal.qlibrary.core import QComponent 
from qiskit_metal.toolbox_python.utility_functions import rotate_point
from qiskit_metal.toolbox_python.positioning import NodePositioner

class AlignmentMarker(NodePositioner, QComponent): 
    """ 
    Inherits `QComponent` class. 

    Description: 
        A square alignment marker. 

    Options: 
        * size    : The side length of the alignment marker 
        * pos_x/_y: position of the bandage on chip
        * orientation : 0-> is parallel to x-axis, with orientation (in degrees) counterclockwise 
        * layer   : the layer number for the bandage

    """ 

    # Default drawing options 
    default_options = Dict(
        size='20um', 
        buffer='220um', 
        pos_x='0um', 
        pos_y='0um', 
        orientation='0', 
        layer='1', 
    )

    # Component metadata
    # Name prefix for component, if user doesn't provide name 
    component_metadata = Dict( 
        short_name='alignment_marker', 
        _qgeometry_table_poly='True', 
    )

    def make(self):
        """ Converts self.options into QGeometry. """ 
        p = self.parse_options() 

        marker = draw.rectangle(p.size, p.size) 
        marker = draw.rotate(marker, p.orientation)
        marker = draw.translate(marker, p.pos_x, p.pos_y)

        back = draw.rectangle(p.buffer, p.buffer) 
        back = draw.rotate(back, p.orientation) 
        back = draw.translate(back, p.pos_x, p.pos_y)

        self.add_qgeometry('poly', {'AlignmentMarker': marker}, layer=p.layer, subtract=True)
        self.add_qgeometry('poly', {'Background': back}, layer=2, subtract=True, helper=True)

        # Node doesn't change under rotation 
        # so just set the origin node as pos_x/_y location 
        nodes = Dict() 
        nodes.origin = np.array((p.pos_x, p.pos_y)) 

        self.nodes = nodes 
        return 

    def node(self, key): 
        return self.nodes.get(key, None) 
