# This code was written by Deval Deliwala.
# 
# This code is to be used by QNL. 
# 
# Any modifications or derivative works of this code must retain this 
# notice, and modified files need to carry a notice indicating 
# that they have been altered from the originals. 

""" CouplingPad. 

.. code-block:: 

                                        `pad` 
                                         /
         _______________________________/__________________________
        |                              /                           |
        | |‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾| | 
        | |                                                      | | 
        | |_________________________  * _________________________| | 
        |                           |  |                           |
         ‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾| |  | |‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾   
                                  | |  | | 
                                   ‾ /  ‾
                                   `cpw` 
""" 

import numpy as np 
from qiskit_metal import draw, Dict 
from qiskit_metal.qlibrary.core import QComponent 
from qiskit_metal.toolbox_python.utility_functions import rotate_point
from qiskit_metal.toolbox_python.positioning import NodePositioner

class CouplingPad(NodePositioner, QComponent): 
    """ 
    Inherits `QComponent` Class. 

    Description: 
        A coupling pad. 

    Options: 
        * cpw_width : The width of the CPW trace connected to the coupling pad 
        * cpw.gap   : The CPW gap of the trace connected to the coupling pad 
        * pad_length: The length (`y`) of the coupling pad 
        * pad_width : The width (`x`) of the coupling pad 
        * gap: The gap between the coupling pad and the ground plane 
        * cpw_length: The length of the CPW as measured from the origin 
        * pos_x/_y: position of the bandage on chip
        * orientation : 0-> is parallel to x-axis, with orientation (in degrees) counterclockwise 
        * layer   : the layer number for the bandage

    """ 

    # Default drawing options 
    default_options = Dict(
        cpw_width   ='20um', 
        cpw_gap     ='10um', 
        pad_length  ='300um', 
        pad_width   ='20um',
        gap         ='5um', 
        cpw_length  ='50um', 
        pos_x       ='0um', 
        pos_y       ='0um', 
        orientation ='0', 
        layer       ='1', 
    )

    # Component metadata
    # Name prefix for component, if user doesn't provide name 
    component_metadata = Dict( 
        short_name='CouplingPad', 
        _qgeometry_table_poly='True', 
    )

    def make(self): 
        """ Converts self.options into QGeometry. """ 
        p = self.parse_options() 
        nodes = Dict() 

        # Encompassing cutout 
        cutout = draw.rectangle(p.pad_length + 2*p.gap, p.pad_width + 2*p.gap)
        cutout = draw.translate(cutout, 0, +p.pad_width/2) 

        # Inner pad gap 
        pad = draw.rectangle(p.pad_length, p.pad_width) 
        pad = draw.translate(pad, 0, +p.pad_width/2) 

        # Encompassing cpw 
        cpw_cutout = draw.rectangle(p.cpw_width + 2*p.gap, p.cpw_length) 
        cpw_cutout = draw.translate(cpw_cutout, 0, -p.cpw_length/2)

        # CPW gap, 1e-10 to avoid rendering issues
        cpw = draw.rectangle(p.cpw_width, p.cpw_length+1e-10) 
        cpw = draw.translate(cpw, 0, -p.cpw_length/2) 

        # Translations \& Rotations 
        geom_list = [cutout, pad, cpw_cutout, cpw] 
        geom_list = draw.rotate(geom_list, p.orientation, origin=(0, 0)) 
        geom_list = draw.translate(geom_list, p.pos_x, p.pos_y) 
        [cutout, pad, cpw_cutout, cpw] = geom_list 

        # Combining components 
        coupling_pad = draw.union([pad, cpw]) 
        coupling_cut = draw.union([cutout, cpw_cutout]) 
        coupling_pad = draw.subtract(coupling_cut, coupling_pad) 

        # Converting to QGeometry
        self.add_qgeometry('poly', {'CouplingPad': coupling_pad}, layer=p.layer) 

        # Positioning nodes 
        nodes.origin = np.zeros(2) 
        nodes.cpw = nodes.origin + [0, -max(p.gap, p.cpw_length)] 
        nodes.pad = nodes.origin + [0, p.pad_width] 

        # Moving nodes along with component  
        translation_vec = np.array((p.pos_x, p.pos_y)) 
        theta = np.deg2rad(p.orientation) 

        for key, point in nodes.items():
            rotated = rotate_point(point, theta) 
            nodes[key] = rotated + translation_vec

        self.nodes = nodes 
        return 

    def node(self, key): 
        return self.nodes.get(key, None) 
