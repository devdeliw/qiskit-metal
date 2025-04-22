import numpy as np 
from qiskit_metal import draw, Dict 
from qiskit_metal.qlibrary.core import QComponent 
from qiskit_metal.toolbox_python.utility_functions import rotate_point
from qiskit_metal.toolbox_python.positioning import NodePositioner

""" Fluxline. 

.. code-block:: 

      __ ______ __
      ` `      / /
       ` `    / /
        `_`__/_/
            
"""     

class FluxLine(NodePositioner, QComponent): 
    default_options = Dict(
        starting_width = '5um', 
        starting_gap   = '8um', 
        end_width = '1um', 
        end_gap   = '2um', 
        taper_length = '212um',
        start_length = '0um', 
        pos_x = '0um', 
        pos_y = '0um', 
        layer = '1', 
        orientation = '0', 
    )
    
    component_metadata = Dict( 
        short_name='fluxline', 
        _qgeometry_table_poly='True', 
    )

    def make(self): 
        p = self.parse_options()

        gap_start = draw.rectangle(p.starting_gap, p.start_length)
        gap_start = draw.translate(gap_start, p.pos_x, p.pos_y+p.start_length/2)

        trace_start=draw.rectangle(p.starting_width, p.start_length) 
        l_trace_start=draw.translate(trace_start, p.pos_x-(p.starting_gap+p.starting_width)/2, p.pos_y+p.start_length/2) 
        r_trace_start=draw.translate(trace_start, p.pos_x+(p.starting_gap+p.starting_width)/2, p.pos_y+p.start_length/2)

        pos_x = p.pos_x 
        pos_y = p.pos_y + p.start_length 

        gap_taper = draw.Polygon([
            (pos_x-p.starting_gap/2, pos_y), (pos_x+p.starting_gap/2, pos_y), 
            (pos_x+p.end_gap/2, pos_y+p.taper_length), (pos_x-p.end_gap/2, pos_y+p.taper_length), 
        ])

        left_trace_taper = draw.Polygon([ 
            (pos_x-p.starting_gap/2, pos_y), (pos_x-p.starting_gap/2-p.starting_width, pos_y), 
            (pos_x-p.end_gap/2-p.end_width, pos_y+p.taper_length), (pos_x-p.end_gap/2, pos_y+p.taper_length)
        ])

        right_trace_taper = draw.Polygon([
            (pos_x+p.starting_gap/2, pos_y), (pos_x+p.starting_gap/2+p.starting_width, pos_y), 
            (pos_x+p.end_gap/2+p.end_width, pos_y+p.taper_length), (pos_x+p.end_gap/2, pos_y+p.taper_length)
        ])

        gap = draw.union([gap_start, gap_taper])
        l_trace=draw.union([l_trace_start, left_trace_taper])
        r_trace=draw.union([r_trace_start, right_trace_taper])

        gap = draw.rotate(gap, p.orientation, origin=(p.pos_x, p.pos_y)) 
        l_trace = draw.rotate(l_trace, p.orientation, origin=(p.pos_x, p.pos_y)) 
        r_trace = draw.rotate(r_trace, p.orientation, origin=(p.pos_x, p.pos_y))

        self.add_qgeometry('poly', {'fluxline_gap': gap}, layer=p.layer) 
        self.add_qgeometry('poly', {'fluxline_trace': draw.union([l_trace, r_trace])}, layer=p.layer, subtract=True)

        nodes = Dict() 
        nodes.origin = np.zeros(2)
        nodes.thin_gap_center = nodes.origin + [0, p.start_length+p.taper_length]
        nodes.thin_trace_left = nodes.origin + [-(p.starting_gap+p.starting_width)/2, p.start_length+p.taper_length] 
        nodes.thin_trace_right= nodes.origin + [+(p.starting_gap+p.starting_width)/2, p.start_length+p.taper_length] 
        nodes.wide_gap_center = nodes.origin + [0, -(p.taper_length+p.start_length)/2] 
        nodes.wide_trace_left = nodes.origin + [-(p.starting_gap+p.starting_width)/2, 0] 
        nodes.wide_trace_right= nodes.origin + [+(p.starting_gap+p.starting_width)/2, 0] 

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
