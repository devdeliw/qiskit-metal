# This code was written by Deval Deliwala.
# 
# This code is to be used by QNL. 
# 
# Any modifications or derivative works of this code must retain this 
# notice, and modified files need to carry a notice indicating 
# that they have been altered from the originals.  

""" ManhattanJunction 

.. code-block::   


                      `vlead0` 
                          | 
                          ‖ `inside_corner` 
                         |‾|   / 
                         | |  / 
          __________     | | / 
         |       _  |____|_|/___________ 
         |      | |=|    |*|            |=- `hlead_0` 
         |     / ‾ /|‾‾‾‾|‾|‾‾‾‾‾‾‾‾‾‾‾‾ 
          ‾‾‾‾/‾‾‾/‾     | | 
             /   /       | | `vlead1`  
        `hcontact`       | |  /
               /         | | / 
              /          | |/  
          `hlead1`    |‾‾ ‖ ‾‾| 
                      |  |‾|  | 
                      |  /‾   | 
                      | /     | 
                      |/      | 
                      /‾‾‾‾‾‾‾
                  `vcontact` 

""" 

import numpy as np 
from qiskit_metal import draw, Dict 
from qiskit_metal.qlibrary.core import QComponent 
from qiskit_metal.toolbox_python.utility_functions import rotate_point
from qiskit_metal.toolbox_python.positioning import NodePositioner

class ManhattanJunction(NodePositioner, QComponent): 
    """ 
    Inherits from `QComponent` Class. 

    Description: 
        QNL Manhattan Junctions. 
        This junction mask design has been optimized for wafer scale junction uniformity. 

    Options: 
        * junction_hw: Horizontal junction width 
        * junction_vw: Vertical junction width 
        * junction_hl: Horizontal junction length 
        * junction_vl: Vertical junction length 
        * wire_hw : Horizontal wire width 
        * wire_vw : Vertical wire width 
        * taper_length: Length of taper from wire width to junction width 
        * extra_hl: Extra length for horizontal junction segment AFTER intersection
        * extra_vl: Extra length for vertical junction segment   AFTER intersection
        * contact_nw : A multiplier specifying the width of the narrow contact piece 
                       This is multiplied by the junction width 
        * contact_ww : A multiplier specifying the width of the wide contact piece 
                       This is multiplied by the junction width 
        * contact_nl : The length of the narrow contact piece 
        * contact_wl : THe length of the wide contact piece 
        * undercut_l : The length of the undercut after the junction segments
        * undercut_w : The width of the undercut after the junction segments 
        * orientation  : 0-> is parallel to x-axis, with orientation (in degrees) counterclockwise
        * pos_x/_y     : `origin` position of junction lead on chip 
                         `origin` is the left-edge-center of the wide-section 
        * layer    : The layer number for the junction lines 
        * undercut_layer   : The layer number for the edge undercut leads 
        

    """

    # Default drawing options 
    default_options = Dict( 
        junction_hw='10um', 
        junction_vw='10um', 
        junction_hl='100um', 
        junction_vl='100um', 
        wire_hw='5um', 
        wire_vw='5um', 
        taper_length='20um', 
        extra_hl='10um', 
        extra_vl='50um', 
        contact_nw=0.5, 
        contact_ww=1, 
        contact_nl='2um', 
        contact_wl='5um', 
        undercut_l= '150um',
        undercut_w='30um', 
        orientation='0', 
        pos_x='0um', 
        pos_y='0um', 
        layer='1', 
        undercut_layer='2',
    ) 

    # Component metadata 
    # Name prefix for component, if user doesn't provide name 
    component_metadata = Dict( 
        short_name='ManhattanJunction', 
        _qgeometry_table_poly='True', 
    )

    def make(self): 
        """ Converts self.options into QGeometry. """ 
        p = self.parse_options() 
        nodes = Dict() 

        # Junction Rectangles 
        h_junction = draw.rectangle(p.junction_hl, p.junction_hw) 
        h_junction = draw.translate(h_junction, (p.junction_hl-p.junction_vw)/2, 0) 
        
        v_junction = draw.rectangle(p.junction_vl, p.junction_vw) 
        v_junction = draw.translate(v_junction, (p.junction_vl-p.junction_hw)/2, 0) 
        
        # Wire-Junction taper
        h_triangles = [ 
            draw.Polygon([
                (-p.taper_length/2, +p.junction_hw/2), 
                (+p.taper_length/2, +p.junction_hw/2), 
                (+p.taper_length/2, +p.wire_hw/2), 
            ]), 
            draw.Polygon([ 
                (-p.taper_length/2, -p.junction_hw/2), 
                (+p.taper_length/2, -p.junction_hw/2), 
                (+p.taper_length/2, -p.wire_hw/2), 
            ]), 
        ] 

        v_triangles = [ 
            draw.Polygon([
                (-p.taper_length/2, +p.junction_vw/2), 
                (+p.taper_length/2, +p.junction_vw/2), 
                (+p.taper_length/2, +p.wire_vw/2), 
            ]), 
            draw.Polygon([ 
                (-p.taper_length/2, -p.junction_vw/2), 
                (+p.taper_length/2, -p.junction_vw/2), 
                (+p.taper_length/2, -p.wire_vw/2), 
            ]), 
        ]

        h_taper = draw.rectangle(p.taper_length, p.junction_hw) 
        h_taper = draw.subtract(h_taper, h_triangles[0]) 
        h_taper = draw.subtract(h_taper, h_triangles[1]) 
        h_taper = draw.translate(h_taper, p.junction_hl + (-p.junction_vw+p.taper_length)/2, 0)

        v_taper = draw.rectangle(p.taper_length, p.junction_vw)
        v_taper = draw.subtract(v_taper, v_triangles[0]) 
        v_taper = draw.subtract(v_taper, v_triangles[1]) 
        v_taper = draw.translate(v_taper, p.junction_vl + (-p.junction_hw+p.taper_length)/2, 0)

        
        # Junction Extensions 
        h_extension = draw.rectangle(p.extra_hl, p.junction_hw) 
        h_extension = draw.translate(h_extension, -(p.junction_vw+p.extra_hl)/2, 0) 

        v_extension = draw.rectangle(p.extra_vl, p.junction_vw) 
        v_extension = draw.translate(v_extension, -(p.junction_hw+p.extra_vl)/2, 0) 
        
        # Narrow contacts 
        h_narrow = draw.rectangle(p.contact_nl, p.contact_nw*p.junction_hw)
        v_narrow = draw.rectangle(p.contact_nl, p.contact_nw*p.junction_vw) 

        h_narrow = draw.translate(h_narrow, -(p.extra_hl + (p.contact_nl + p.junction_vw)/2), 0) 
        v_narrow = draw.translate(v_narrow, -(p.extra_vl + (p.contact_nl + p.junction_hw)/2), 0)

        # Wide contacts  
        h_wide = draw.rectangle(p.contact_wl, p.contact_ww*p.junction_hw)
        v_wide = draw.rectangle(p.contact_wl, p.contact_ww*p.junction_vw) 

        h_wide = draw.translate(h_wide, -(p.extra_hl + p.contact_nl + (p.contact_wl + p.junction_vw)/2), 0) 
        v_wide = draw.translate(v_wide, -(p.extra_vl + p.contact_nl + (p.contact_wl + p.junction_hw)/2), 0)

        # Undercut pads 
        undercut = draw.rectangle(p.undercut_l, p.undercut_w) 
        h_undercut = draw.translate(undercut, -(p.extra_hl + (p.junction_vw+p.undercut_l)/2), 0)
        v_undercut = draw.translate(undercut, -(p.extra_vl + (p.junction_hw+p.undercut_l)/2), 0)

        # Combining all non-undercut components into `junction` 
        # Applying 90 deg rotation to vertical junction 
        h_junction = draw.union([h_junction, h_taper, h_extension, h_narrow, h_wide]) 
        v_junction = draw.union([v_junction, v_taper, v_extension, v_narrow, v_wide]) 

        v_undercut = draw.rotate(v_undercut, 90.0, origin=(0, 0))
        v_junction = draw.rotate(v_junction, 90.0, origin=(0, 0)) 
        junction = draw.union([h_junction, v_junction])  
        undercut = draw.union([h_undercut, v_undercut]) 

        # Translations & Rotations 
        geom_list = [junction, undercut] 
        geom_list = draw.rotate(geom_list, p.orientation, origin=(0, 0)) 
        geom_list = draw.translate(geom_list, p.pos_x, p.pos_y) 
        junction, undercut = geom_list

        # Converting drawing to qgeometry
        self.add_qgeometry('poly', {'junction': junction}, layer=p.layer)
        self.add_qgeometry('poly', {'undercut': undercut}, layer=p.undercut_layer) 

        # Positioning nodes 
        nodes.origin = np.zeros(2) 
        nodes.hlead0 = np.array((p.taper_length + p.junction_hl - p.junction_vw/2, 0)) 
        nodes.hlead1 = np.array((-(p.junction_vw/2 + p.extra_hl), 0)) 
        nodes.vlead0 = np.array((0, p.taper_length + p.junction_vl - p.junction_hw/2)) 
        nodes.vlead1 = np.array((0, -(p.junction_hw/2 + p.extra_vl)))
        nodes.hcontact = nodes.hlead1 + np.array((-p.contact_wl-p.contact_nl, 0))
        nodes.vcontact = nodes.vlead1 + np.array((0, -p.contact_wl-p.contact_nl))
        nodes.inside_corner = nodes.origin + np.array((p.junction_hw/2, p.junction_vw/2)) 

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
