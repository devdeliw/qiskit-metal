# This code was written by Deval Deliwala.
# 
# This code is to be used by QNL. 
# 
# Any modifications or derivative works of this code must retain this 
# notice, and modified files need to carry a notice indicating 
# that they have been altered from the originals. 

""" Claw. 

.. code-block:: 


                `finger0`   `finger1` 
                    /          / 
               |‾‾‾/‾|    |‾‾‾/‾| 
               | |‾| |    | |‾| | 
               | | | |    | | | | 
               | | | |    | | | | 
               | | |  ‾/‾‾  | | | 
               | |  ‾‾//‾‾‾‾  | | 
               |  ‾‾‾//  |‾‾‾‾  | 
                ‾‾‾‾//| *| |‾‾‾‾
                   // |  | | 
   `pad_cutout`__ //| |  | | 
                  /  ‾ /  ‾
         `pad` __/    /
                     /
            `cpw` __/
"""

import numpy as np
from shapely.geometry import JOIN_STYLE 
from qiskit_metal import draw, Dict 
from qiskit_metal.qlibrary.core import QComponent 
from qiskit_metal.toolbox_python.utility_functions import rotate_point
from qiskit_metal.toolbox_python.positioning import NodePositioner

class Claw(NodePositioner, QComponent): 
    """ 
    Inherits `QComponent` class. 

    Description: 
        A claw-shaped coupling pad.  

    Options: 
        * cpw_width: The width of the CPW trace 
        * cpw_gap  : The CPW gap of the connected trace 
        * base_length: The length (`x`) of the base segment 
        * base_width : The width (`y`) of the base segment 
        * finger_length: The length (`y`) of the finger measured w.r.t bottom of base 
        * finger_width : The width (`x`) of the fingers 
        * gap: The substrate gap between the coupling pad and the ground plane 
        * cpw_length   : The length of the CPW as measured from the origin (*)
        * pos_x/_y: position of the bandage on chip
        * orientation : 0-> is parallel to x-axis, with orientation (in degrees) counterclockwise 
        * layer   : the layer number for the bandage

    """ 

    # Default drawing options 
    default_options = Dict(
        cpw_width='10um', 
        cpw_gap='20um', 
        base_length='100um', 
        base_width='20um',
        finger_length='100um', 
        finger_width='20um', 
        gap='5um', 
        cpw_length='30um', 
        fillet='5um', 
        pos_x='0um', 
        pos_y='0um', 
        orientation='0', 
        layer='1',
    )

    # Component metadata
    # Name prefix for component, if user doesn't provide name 
    component_metadata = Dict( 
        short_name='Claw', 
        _qgeometry_table_poly='True', 
    )

    def make(self): 
        """ Convert self.options into QGeometry. """ 
        p = self.parse_options() 
        nodes = Dict() 

        # Base section 
        base = draw.rectangle(p.base_length, p.base_width) 
        base = draw.translate(base, 0, p.base_width/2)

        base_cutout = draw.rectangle(p.base_length + 2*p.cpw_width, p.base_width + 2*p.cpw_width) 
        base_cutout = draw.translate(base_cutout, 0, p.base_width/2)

        # Left and right fingers 
        finger = draw.rectangle(p.finger_width, p.finger_length) 
        l_fing = draw.translate(finger, (-p.base_length+p.finger_width)/2, p.finger_length/2)
        r_fing = draw.translate(finger, (+p.base_length-p.finger_width)/2, p.finger_length/2)

        finger_cutout = draw.rectangle(p.finger_width + 2*p.cpw_width, p.finger_length + 2*p.cpw_width) 
        l_fing_cutout = draw.translate(finger_cutout, (-p.base_length+p.finger_width)/2, p.finger_length/2) 
        r_fing_cutout = draw.translate(finger_cutout, (+p.base_length-p.finger_width)/2, p.finger_length/2)

        # Bottom connecting CPW section 
        cpw_rect = draw.rectangle(p.cpw_gap, p.cpw_length) 
        cpw_rect = draw.translate(cpw_rect, 0, -p.cpw_length/2) 

        cpw_cutout = draw.rectangle(p.cpw_gap + p.cpw_width*2, p.cpw_length) 
        cpw_cutout = draw.translate(cpw_cutout, 0, -p.cpw_length/2) 

        # Performing rotations and translations 
        geom_list = [
            base, l_fing, r_fing, cpw_rect, 
            base_cutout, l_fing_cutout, r_fing_cutout, cpw_cutout, 
        ] 
        geom_list = draw.rotate(geom_list, p.orientation, origin=(0,0)) 
        geom_list = draw.translate(geom_list, p.pos_x, p.pos_y) 
        [
            base, l_fing, r_fing, cpw_rect, base_cutout, 
            l_fing_cutout, r_fing_cutout, cpw_cutout,
        ] = geom_list 

        # Finishing component
        claw_main = draw.union([base, l_fing, r_fing]) \
            .buffer(distance=+p.fillet, quad_segs=30, join_style=JOIN_STYLE.round) \
            .buffer(distance=-2*p.fillet, quad_segs=30, join_style=JOIN_STYLE.round) \
            .buffer(distance=+p.fillet, quad_segs=30, join_style=JOIN_STYLE.round)
        cutout = draw.union([base_cutout, l_fing_cutout, r_fing_cutout]) 
        claw_background = draw.subtract(cutout, claw_main) \
            .buffer(distance=+p.fillet, quad_segs=30, join_style=JOIN_STYLE.round) \
            #.buffer(distance=-2*p.fillet, quad_segs=30, join_style=JOIN_STYLE.round) \
            #.buffer(distance=+p.fillet, quad_segs=30, join_style=JOIN_STYLE.round)
        claw_background = draw.subtract(claw_background, cpw_rect)

        # Converting to QGeometry
        claw_main = draw.union([claw_main, cpw_rect])
        claw_back = draw.union([claw_background, cpw_cutout])
        self.add_qgeometry('poly', {'claw_back': claw_back}, layer=p.layer, subtract=True) 
        self.add_qgeometry('poly', {'claw_main': claw_main}, layer=p.layer, subtract=False)

        # Positioning nodes 
        nodes.origin = np.zeros(2) 
        nodes.pad = nodes.origin + [0, p.base_width] 
        nodes.pad_cutout = nodes.pad + [0, p.cpw_width] 
        nodes.cpw = nodes.origin + [0, -max(p.cpw_length, p.cpw_width)] 
        nodes.finger1 = nodes.origin + [+(p.base_length-p.finger_width)/2, p.finger_length] 
        nodes.finger0 = np.array((-nodes.finger1[0], nodes.finger1[1]))

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
