# This code was written by Deval Deliwala.
# 
# This code is to be used by QNL. 
# 
# Any modifications or derivative works of this code must retain this 
# notice, and modified files need to carry a notice indicating 
# that they have been altered from the originals. 

""" Chip Boundary. 

.. code-block:: 

    _________________________
   |_|                     |_|
   |                         |
   |                         | 
   |                         |
   |            *            |
   |                         |
   |                         |  
   |_                       _|
   | |                     | |
    ‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾

"""

import numpy as np 
from qiskit_metal import draw, Dict 
from qiskit_metal.qlibrary.core import QComponent 

class Boundary(QComponent): 
    """ 
    Inherits `QComponent` class. 

    Description: 
        The chip boundary.  

    Options: 

    """ 

    # Default drawing options 
    default_options = Dict(
        lx          = '10mm', 
        ly          = '10mm', 
        thick       = '50um', 
        corner_size = '250um',
        no_cheese   = '30um', 
        pos_x       = '0um', 
        pos_y       = '0um', 
        layer       = '0', 
    )

    # Component metadata
    # Name prefix for component, if user doesn't provide name 
    component_metadata = Dict( 
        short_name='chip_boundary', 
        _qgeometry_table_poly='True', 
    )

    def make(self):
        """ Converts self.options into QGeometry. """ 
        p = self.parse_options() 

        outer_box = draw.rectangle(p.lx, p.ly) 
        inner_box = draw.rectangle(p.lx-2*p.thick, p.ly-2*p.thick) 
        boundary  = draw.subtract(outer_box, inner_box)

        corner = draw.rectangle(p.corner_size, p.corner_size) 
        tl_corner = draw.translate(corner, -p.lx/2+p.corner_size/2, +p.ly/2-p.corner_size/2) 
        tr_corner = draw.translate(corner, +p.lx/2-p.corner_size/2, +p.ly/2-p.corner_size/2) 
        bl_corner = draw.translate(corner, -p.lx/2+p.corner_size/2, -p.ly/2+p.corner_size/2) 
        br_corner = draw.translate(corner, +p.lx/2-p.corner_size/2, -p.ly/2+p.corner_size/2) 

        boundary = draw.union([boundary, tl_corner, tr_corner, bl_corner, br_corner]) 
        boundary = draw.translate(boundary, p.pos_x, p.pos_y)

        no_cheese_boundary = boundary.buffer(distance=p.no_cheese, quad_segs=30)
        
        no_cheese_boundary = draw.translate(no_cheese_boundary, p.pos_x, p.pos_y)

        self.add_qgeometry( 
            'poly', 
            {'boundary': boundary}, 
            layer=p.layer, 
            subtract=True, 
        )
        self.add_qgeometry( 
            'poly', 
            geometry        = {'no_cheese_chip': no_cheese_boundary},
            component_name  = 'no_cheese_chip',
            subtract        = True, 
            layer           = 2,
        )


