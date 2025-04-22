import numpy as np 
from qiskit_metal import draw, Dict 
from qiskit_metal.qlibrary.core import QComponent 
from qiskit_metal.toolbox_python.utility_functions import rotate_point
from qiskit_metal.toolbox_python.positioning import NodePositioner

""" Two pocket Fluxonium. 

.. code-block:: 

                        `top` 
         _________________|_____________  
        |                               |
        |                               |
        |      _____          _____     | 
        |     |     |        |     |    | 
 `left` |     |  *  |    *   |  *  |    |
        |     |     |        |     |    | - `right`
        |      ‾‾‾‾‾          ‾‾‾‾‾     |
        |                               |  
        |                               | 
        |                               | 
         ‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾|‾‾‾‾‾‾‾‾‾‾‾‾‾‾ 
                      `bottom` 

 
"""


class Fluxonium(NodePositioner, QComponent): 
    default_options = Dict(
        width='475um', 
        height='300um', 
        pos_x='0um', 
        pos_y='0um', 
        qubit_length='100um', 
        pad_spacing='75um', 
        fillet='5um', 
        layer='1', 
    ) 

    component_metadata = Dict(
        short_name='fluxonium', 
        _qgeometry_table_poly='True', 
    ) 

    def make(self): 
        p=self.parse_options()

        p.width  -= p.fillet*2 
        p.height -= p.fillet*2
        p.qubit_length -= p.fillet*2

        pad = draw.rectangle(p.width, p.height).buffer(distance=p.fillet, quad_segs=30)
        pad = draw.translate(pad, p.pos_x, p.pos_y) 

        pocket = draw.rectangle(p.qubit_length, p.qubit_length).buffer(distance=p.fillet, quad_segs=30)
        left_pocket = draw.translate(pocket, p.pos_x-p.pad_spacing/2-p.qubit_length/2, p.pos_y) 
        right_pocket= draw.translate(pocket, p.pos_x+p.pad_spacing/2+p.qubit_length/2, p.pos_y) 

        self.add_qgeometry('poly', {'l_pocket': left_pocket}, layer=p.layer) 
        self.add_qgeometry('poly', {'r_pocket': right_pocket}, layer=p.layer) 
        self.add_qgeometry('poly', {'pad': pad}, layer=p.layer, subtract=True) 

        nodes = Dict() 
        nodes.origin    = np.zeros(2) 
        nodes.top       = np.array((0, +p.height/2+p.fillet)) 
        nodes.bottom    = np.array((0, -p.height/2-p.fillet)) 
        nodes.left      = np.array((-p.width/2-p.fillet, 0)) 
        nodes.right     = np.array((+p.width/2+p.fillet, 0))
        nodes.l_pocket  = np.array((-p.pad_spacing/2-p.qubit_length/2, 0)) 
        nodes.r_pocket  = np.array((+p.pad_spacing/2+p.qubit_length/2, 0))
        nodes.l_pocket_bottom = nodes.l_pocket + [0, -p.qubit_length/2-p.fillet] 
        nodes.l_pocket_top    = nodes.l_pocket + [0, +p.qubit_length/2+p.fillet] 
        nodes.l_pocket_right  = nodes.l_pocket + [+p.qubit_length/2+p.fillet, 0]
        nodes.l_pocket_left   = nodes.l_pocket + [-p.qubit_length/2-p.fillet, 0]
        nodes.r_pocket_bottom = nodes.r_pocket + [0, -p.qubit_length/2-p.fillet] 
        nodes.r_pocket_top    = nodes.r_pocket + [0, +p.qubit_length/2+p.fillet] 
        nodes.r_pocket_right  = nodes.r_pocket + [+p.qubit_length/2+p.fillet, 0]
        nodes.r_pocket_left   = nodes.r_pocket + [-p.qubit_length/2-p.fillet, 0]


        translation_vec = np.array((p.pos_x, p.pos_y)) 
        theta = np.deg2rad(0.0)
        for key, point in nodes.items():
            rotated = rotate_point(point, theta)
            nodes[key] = rotated + translation_vec
            
        self.nodes = nodes
        return 

    def node(self, key): 
        return self.nodes.get(key, None)
