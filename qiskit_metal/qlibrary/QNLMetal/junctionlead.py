# This code was written by Deval Deliwala.
# 
# This code is to be used by QNL. 
# 
# Any modifications or derivative works of this code must retain this 
# notice, and modified files need to carry a notice indicating 
# that they have been altered from the originals.  

""" BridgeFreeJunction. 

.. code-block:: 


                                           `lead_1
            |‾‾‾‾‾‾‾‾‾‾‾‾|‾‾ --- ___          | 
            |            |            ‾‾‾|‾‾‾‾‾|‾‾∖
           *|            |               |  /‾‾|   |- `lead_0`
            |           /|               | /   |  /
            |          / |    ___ --- ‾‾‾ /‾‾‾‾|‾‾
             ‾‾‾‾‾‾‾‾‾/‾‾ ‾‾‾            /  `lead_2` 
                     /                  /     
                   "taper"        `inner_lead`
"""

import numpy as np 
from qiskit_metal import draw, Dict 
from qiskit_metal.qlibrary.core import QComponent 
from qiskit_metal.toolbox_python.utility_functions import rotate_point
from qiskit_metal.toolbox_python.positioning import NodePositioner



class JunctionLead(NodePositioner, QComponent): 
    """ 
    Inherits `QComponent` Class. 

    Description: 
        Large Junction leads. 
        These are the large junction leads that connect the SQUID loop or junction wires to 
        the capacitor pads.  

    Options: 
        * outer_length : The length of the wide section.
                         will be computed from the total length and the lengths of the other segments
        * outer_width  : The width of the wide section 
        * inner_length : The length of the narrow section 
        * inner_width  : The width of the narrow section 
        * taper_length : The length of the taper 
        * pos_x/_y     : `origin` position of junction lead on chip 
                         `origin` is the left-edge-center of the wide-section 
        * fillet : The radius of the fillet. Only the two corners at the end of the narrow section 
                   will be filleted. 
        * extension    : The length of the narrow section past the junction wires. 
        * orientation  : 0-> is parallel to x-axis, with orientation (in degrees) counterclockwise 
        * layer: the layer number for the JunctionLead


    """ 

    # Default drawing options 
    default_options = Dict( 
        outer_length='500um', 
        outer_width='250um', 
        inner_length='250um', 
        inner_width='125um', 
        taper_length='700um', 
        fillet='0um', 
        extension='0um', 
    )

    # Component metadata 
    # Name prefix for component, if user doesn't provide name 
    component_metadata = Dict( 
        short_name='JunctionLead', 
        _qgeometry_table_poly='True', 
    )

    def make(self): 
        """ Convert self.options into QGeometry. """ 
        p = self.parse_options() 
        nodes = Dict() 

        # Wide section 
        wide_rect = draw.rectangle(p.outer_length, p.outer_width) 

        # Tapered section -- Built via subtract
        tapered_rect = draw.rectangle(p.taper_length, p.outer_width) 

        upper_triangle = draw.Polygon([
            (-p.taper_length/2, +p.outer_width/2), 
            (+p.taper_length/2, +p.outer_width/2), 
            (+p.taper_length/2, +p.inner_width/2), 
        ]) 
        lower_triangle = draw.Polygon([
            (-p.taper_length/2, -p.outer_width/2), 
            (+p.taper_length/2, -p.outer_width/2), 
            (+p.taper_length/2, -p.inner_width/2), 
        ]) 
        
        tapered_rect = draw.subtract(tapered_rect, upper_triangle) 
        tapered_rect = draw.subtract(tapered_rect, lower_triangle) 
        
        # Inner section 
        inner_rect = draw.rectangle(p.inner_length, p.inner_width) 
        
        def fillet_right_corners(L, W, r, num_points=10): 
            """ 
            Returns a shapely polyon for a rectangle of (`L` x `W`) centered at 
            (0, 0), where only the two right corners are filleted with radius `r`. 

            This is for the filleted-narrow-end of the JunctionLead. 

            """ 

            if r > W/2 or r > L/2: 
                raise ValueError('Fillet radius is too large for the provided rectangle dimensions.') 

            # Non-filleted corners 
            top_left    = (-L/2, +W/2) 
            bottom_left = (-L/2, -W/2) 

            # Tangent points where the fillets begin/end 
            top_right_straight = (L/2-r, W/2) 
            bottom_right_straight = (L/2, -W/2) 

            # Top right fillet 
            center_tr = (L/2 - r, W/2 - r) 
            arc_tr = [] 
            for i in range(num_points + 1): 
                theta = np.pi/2 * (1 - i/num_points) 
                x = center_tr[0] + r * np.cos(theta) 
                y = center_tr[1] + r * np.sin(theta) 
                arc_tr.append((x, y))

            # Bottom right fillet 
            center_br = (L/2 - r, -W/2 + r) 
            arc_br = [] 
            for i in range(num_points + 1): 
                theta = 0 - (np.pi/2) * (i/num_points) 
                x = center_br[0] + r * np.cos(theta) 
                y = center_br[1] + r * np.sin(theta) 
                arc_br.append((x, y)) 

            coords = []
            coords.append(bottom_left)                
            coords.append(top_left)                    
            coords.append(top_right_straight)          
            coords.extend(arc_tr)                      
            coords.append((L/2, -W/2 + r))
            coords.extend(arc_br)                      
            coords.append(bottom_left)

            return draw.Polygon(coords)
            
        if p.extension != 0.0: 
            extended_rect = draw.rectangle(p.extension, p.inner_width)  
            extended_rect = fillet_right_corners(p.extension, p.inner_width, p.fillet) 
        else: 
            inner_rect = fillet_right_corners(p.inner_length, p.inner_width, p.fillet)
            extended_rect = draw.rectangle(0, 0) # default to null rectangle

        # Positioning all sections correctly 
        tapered_rect = draw.translate(tapered_rect, (p.outer_length + p.taper_length)/2, 0) 
        inner_rect = draw.translate(inner_rect, p.taper_length + (p.outer_length + p.inner_length)/2, 0)
        extended_rect = draw.translate(extended_rect, p.taper_length + p.inner_length + (p.outer_length + p.extension)/2, 0)
            
        # Translations & Rotations 
        junction_lead = draw.union([wide_rect, tapered_rect, inner_rect, extended_rect] )
        junction_lead = draw.rotate(junction_lead, p.orientation)
        junction_lead = draw.translate(junction_lead, p.pos_x + p.outer_length/2, p.pos_y) 

        # Converting drawing to qgeometry  
        self.add_qgeometry('poly', {'junction_lead': junction_lead}, layer = p.layer) 

        # Positioning nodes 
        nodes.origin = np.zeros(2)
        nodes.taper = nodes.origin + [p.outer_length, 0] 
        nodes.lead_0 = nodes.origin + [p.outer_length+p.taper_length+p.inner_length+p.extension, 0]
        nodes.lead_1 = nodes.lead_0 + [-p.extension, p.inner_width/2] 
        nodes.lead_2 = nodes.lead_0 + [-p.extension, -p.inner_width/2]
        nodes.inner_lead = nodes.lead_0 + [-p.extension, 0] 

        # Moving nodes along with component 
        # pivot necessary as origin is not defined at center of object
        pivot = np.array([(p.outer_length + p.taper_length + p.inner_length + p.extension)/2, 0])
        theta = np.deg2rad(p.orientation)
        translation_vec = np.array((p.pos_x, p.pos_y)) 
        for key, point in nodes.items(): 
            relative = point - pivot
            rotated_relative = rotate_point(relative, theta)
            rotated = pivot + rotated_relative
            nodes[key] = rotated + translation_vec

        self.nodes = nodes
        return  

    def node(self, key): 
        return self.nodes.get(key, None) 
