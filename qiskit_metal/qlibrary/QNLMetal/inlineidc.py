# This code was written by Deval Deliwala.
# 
# This code is to be used by QNL. 
# 
# Any modifications or derivative works of this code must retain this 
# notice, and modified files need to carry a notice indicating 
# that they have been altered from the originals. 

""" InlineIDC (Interdigitated Capacitor). 

.. code-block::  

                       `cpw0`
                         / 
                   __   /  __ 
                 /  /      \  
                /  /        \  \ 
               /  /          \  
              /__/__ _ _ _ ___\__\ 
             |      | | | |      |
             |      ||||||||     |
             |      ||||*|||     |
             |      ||||||||     |
             |       | | | |     |
              \‾‾\‾‾ ‾ ‾ ‾  ‾‾/‾‾/
               \  \          /  /  
                \  \        /  /   
                 \  \      /  /
                  ‾‾   /    ‾‾
                      /
                   `cpw1'
                  
""" 

import numpy as np 
from qiskit_metal import draw, Dict 
from qiskit_metal.qlibrary.core import QComponent 
from qiskit_metal.toolbox_python.utility_functions import rotate_point
from qiskit_metal.toolbox_python.positioning import NodePositioner

class InlineIDC(NodePositioner, QComponent): 
    """ 
    Inherits `QComponent` Class. 

    Description: 
        Inline IDC (interdigitated capacitor) component. 

    Options: 
        * cpw_width: The width of the CPW trace 
        * cpw_gap  : The CPW gap of the connected trace
        * taper_length  : The length of the taper segment 
        * taper_gap     : The gap between inner trace & ground plane at widest point 
        * fingers_num   : The number of fingers 
        * fingers_width : The finger width 
        * fingers.length: The finger length  
        * fingers_horizontal_gap : Horizontal gap between fingers  
        * fingers_vertical_gap   : Vertical gap between fingers 
            * Note `Horizontal` & `Vertical` refer to default orientation 
        * pos_x/_y: position of the bandage on chip
        * orientation : 0-> is parallel to x-axis, with orientation (in degrees) counterclockwise 
        * layer: The layer for the Inline IDC

    """

    # Default Drawing options 
    default_options = Dict(
        cpw_width    = '17.5um', 
        cpw_gap      = '30um', 
        taper_length = '200um', 
        taper_gap    = '87.5um', 
        fingers_num  = '18',  
        fingers_width= '5um', 
        fingers_length         = '200um', 
        fingers_horizontal_gap ='5um', 
        fingers_vertical_gap   ='10um', 
        pos_x = '0um', 
        pos_y = '0um', 
        orientation = '0', 
        layer = '1', 
    ) 

    # Component metadata
    # Name prefix for component, if user doesn't provide name 
    component_metadata = Dict( 
        short_name='InlineIDC', 
        _qgeometry_table_poly='True', 
    )

    def make(self): 
        """ Converts self.options into QGeometry. """ 
        p = self.parse_options() 
        nodes = Dict()

        cpw_gap = p.cpw_width 
        cpw_width   = p.cpw_gap 
        taper_length = p.taper_length 
        taper_gap    = p.taper_gap 
        fingers_num  = p.fingers_num 
        fingers_width  = p.fingers_width 
        fingers_length = p.fingers_length 
        fingers_horizontal_gap = p.fingers_horizontal_gap 
        fingers_vertical_gap   = p.fingers_vertical_gap 
        pos_x = p.pos_x 
        pos_y = p.pos_y 
        orientation = p.orientation 
        layer = p.layer 

        ## Meandering Portion 
        ## ------------------

        # Encompassing Central Box Dimensions 
        box_width  = fingers_length 
        inner_box_length = fingers_num*fingers_horizontal_gap+(fingers_num-1)*fingers_width
        outer_box_length = taper_gap 
        box_length = inner_box_length + 2*outer_box_length

        # Build box and initialize CPW finger dimensions 
        box = draw.rectangle(box_length, box_width) 
        finger = draw.rectangle(
            fingers_horizontal_gap, 
            fingers_length - fingers_vertical_gap,  
        ) 

        # X positions for each finger 
        finger_x_positions = [
            -inner_box_length/2+fingers_horizontal_gap/2+i*(fingers_horizontal_gap+fingers_width)
            for i in range(int(fingers_num))
        ] 

        # Iteratively add each finger to list, alternating y-positions to create a meander
        finger_list = []
        for idx in range(int(fingers_num)): 
            if idx%2 == 0: 
                finger_list.append(
                    draw.translate(
                        finger, 
                        finger_x_positions[idx], 
                        -fingers_vertical_gap/2, 
                    )
                ) 
            else: 
                finger_list.append( 
                    draw.translate(
                        finger, 
                        finger_x_positions[idx], 
                        +fingers_vertical_gap/2, 
                    )
                )

        # Combine all unions into one component 
        fingers = draw.union(finger_list)

        # Upper and lower tapers 
        upper_taper = draw.Polygon([ 
            (-inner_box_length/2, +box_width/2), 
            (+inner_box_length/2, +box_width/2), 
            (+cpw_width/2, +box_width/2+taper_length), 
            (-cpw_width/2, +box_width/2+taper_length), 
        ])
        lower_taper = draw.Polygon([
            (-inner_box_length/2, -box_width/2), 
            (+inner_box_length/2, -box_width/2), 
            (+cpw_width/2, -box_width/2-taper_length), 
            (-cpw_width/2, -box_width/2-taper_length), 
        ])
        
        tapers = draw.union([upper_taper, lower_taper])
        tapers = draw.rotate(tapers, orientation, origin=(0, 0)) 
        tapers = draw.translate(tapers, pos_x, pos_y)
        self.add_qgeometry('poly', {'idc_no_cheese_tapers': tapers}, layer=2, subtract=True, helper=True) 


        inline_idc = draw.union([fingers, upper_taper, lower_taper])
        inline_idc = draw.rotate(inline_idc, orientation, origin=(0, 0)) 
        inline_idc = draw.translate(inline_idc, pos_x, pos_y) 
        self.add_qgeometry('poly', {'inline_idc_main': inline_idc}, layer=layer)

        # Create the meandering inner portion of encompassing box
        box = draw.subtract(box, fingers) 

        ## Tapering End Portion 
        ## -------------------- 

        # Building the cutoff triangles to create a taper 
        right_triangle = draw.Polygon([
            (-cpw_width/2, +box_width/2+taper_length), 
            (-cpw_width/2, +box_width/2), 
            (-inner_box_length/2, +box_width/2), 
        ])

        left_triangle = draw.Polygon([
            (-cpw_width/2-cpw_gap, +box_width/2+taper_length), 
            (-box_length/2, +box_width/2+taper_length), 
            (-box_length/2, +box_width/2), 
        ])
        cutoff_triangles = draw.union([left_triangle, right_triangle])

        # Initialize Encompassing Taper Box
        taper = draw.rectangle(-cpw_width/2 + box_length/2, taper_length) 

        # Center of mass locations for taper 
        x_centroid = -cpw_width/2-0.25*(-cpw_width + box_length) 
        y_centroid = (taper_length + box_width)/2
        taper = draw.translate(taper, x_centroid, y_centroid) 
        
        # Final Taper object
        taper1 = draw.subtract(taper, cutoff_triangles) 

        # Placing tapers on edges with proper orientation 
        taper2 = draw.scale(taper1, xfact=-1, origin=(0,0))
        taper3 = draw.scale(taper1, yfact=-1, origin=(0,0)) 
        taper4 = draw.scale(taper1, xfact=-1, yfact=-1, origin=(0,0)) 
        tapers = draw.union([taper1, taper2, taper3, taper4]) 

        # Final InlineIDC component 
        inlineIDC = draw.union([box, tapers]) 

        # Translations \& Rotations 
        inlineIDC = draw.rotate(inlineIDC, orientation, origin=(0, 0)) 
        inlineIDC = draw.translate(inlineIDC, pos_x, pos_y) 

        # Converting to QGeometry
        self.add_qgeometry('poly', {'inline_idc_back': inlineIDC}, layer=layer, subtract=True)

        ## Positioning Nodes 
        ## -----------------

        nodes.origin = np.zeros(2) 
        nodes.cpw0 = nodes.origin + [0, box_width/2 + taper_length] 
        nodes.cpw1 = -nodes.cpw0 

        # Moving nodes along with component  
        translation_vec = np.array((p.pos_x, p.pos_y)) 
        theta = np.deg2rad(p.orientation) 

        for key, point in nodes.items():
            rotated = rotate_point(point, theta) 
            nodes[key] = rotated + translation_vec

        self.nodes = nodes

        ## Pins 
        ## ---- 

        # top pin 
        cpw0_center = tuple(np.array(self.nodes.cpw0))
        normal_offset = (0, 0)
        cpw0_normal = tuple(np.array(cpw0_center) + np.array(normal_offset))

        self.add_pin("cpw0_pin",
                     [cpw0_center, cpw0_normal],
                     width=p.cpw_width,
                     gap=p.cpw_gap,
                     input_as_norm=True)
 
        # bottom pin
        cpw1_center = tuple(np.array(self.nodes.cpw1))
        normal_offset = (0, -0.1)
        cpw1_normal = tuple(np.array(cpw1_center) + np.array(normal_offset))


        self.add_pin("cpw1_pin",
             [cpw1_center, cpw1_normal],
             width=p.cpw_width,
             gap=p.cpw_gap,
             input_as_norm=True)

        return 

    def node(self, key): 
        return self.nodes.get(key, None)
