import numpy as np 
from qiskit_metal import draw, Dict 
from qiskit_metal.qlibrary.core import QComponent 
from qiskit_metal.toolbox_python.utility_functions import rotate_point
from qiskit_metal.toolbox_python.positioning import NodePositioner

""" Two pocket Transmon. 

.. code-block:: 

                 `top`
         ______________________
        |                      |
        |                      | 
        |                      | 
        |    ____     ____     | 
        |   |    |   |    |    | 
 `left` |   |    |   |    |    | `right`
        |   |    |   |    |    | 
        |   |____|   |____|    | 
        |                      | 
        |                      | 
        |                      |  
        |______________________|
                `bottom`


"""

class Transmon(NodePositioner, QComponent): 
    default_options = Dict( 
        pos_x='0um', 
        pos_y='0um', 
        width='535um', 
        height='745um', 
        pocket_width='135um', 
        pocket_height='545um', 
        fillet='5um', 
        pad_spacing='65um', 
        orientation='0', 
        layer='1', 
    )

    component_metadata = Dict(
        short_name='transmon', 
        _qgeometry_table_poly='True', 
    ) 

    def make(self): 
        p=self.parse_options() 

        p.width  = p.width - p.fillet*2 
        p.height = p.height- p.fillet*2
        p.pocket_width = p.pocket_width - p.fillet*2 
        p.pocket_height= p.pocket_height- p.fillet*2 

        pad = draw.rectangle(p.width, p.height).buffer(distance=p.fillet, quad_segs=30)
        pad = draw.translate(pad, p.pos_x, p.pos_y) 

        pocket = draw.rectangle(p.pocket_width, p.pocket_height).buffer(distance=p.fillet, quad_segs=30) 
        left_pocket = draw.translate(pocket, p.pos_x-p.pad_spacing/2-p.pocket_width/2-p.fillet/2, p.pos_y) 
        right_pocket= draw.translate(pocket, p.pos_x+p.pad_spacing/2+p.pocket_width/2+p.fillet/2, p.pos_y) 

        self.add_qgeometry('poly', {'l_pocket': left_pocket}, layer=p.layer) 
        self.add_qgeometry('poly', {'r_pocket': right_pocket}, layer=p.layer) 
        self.add_qgeometry('poly', {'pad': pad}, layer=p.layer, subtract=True) 

        nodes = Dict() 
        nodes.origin = np.zeros(2) 
        nodes.top    = nodes.origin + [0, p.height/2 + p.fillet] 
        nodes.bottom = nodes.origin - [0, p.height/2 + p.fillet] 
        nodes.left   = nodes.origin - [p.width/2 + p.fillet, 0] 
        nodes.right  = nodes.origin + [p.width/2 + p.fillet, 0] 

        translation_vec = np.array((p.pos_x, p.pos_y)) 
        theta = np.deg2rad(0.0)
        for key, point in nodes.items():
            rotated = rotate_point(point, theta)
            nodes[key] = rotated + translation_vec

        self.nodes = nodes 
        return 
    
    def node(self, key): 
        return self.nodes.get(key, None)
            










