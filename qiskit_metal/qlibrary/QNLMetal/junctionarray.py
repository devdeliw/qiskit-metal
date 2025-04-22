# This code was written by Deval Deliwala.
# 
# This code is to be used by QNL. 
# 
# Any modifications or derivative works of this code must retain this 
# notice, and modified files need to carry a notice indicating 
# that they have been altered from the originals.  

""" JunctionArray. 

.. code-block::  

                     `wire1` 
        ________________|_______________
        ‾‾‾‾‾‾‾‾‾‾‾|‾‾‾|‾|‾‾‾‾‾‾‾‾‾‾‾‾‾‾
        ___________|___|_|______________
        ‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾|‾|‾‾‾|‾‾‾‾‾‾‾‾‾‾
        _______________|_|___|__________
        ‾‾‾‾‾‾‾‾‾‾‾|‾‾‾|‾|‾‾‾‾‾‾‾‾‾‾‾‾‾‾
        ___________|___|_|______________
        ‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾|‾|‾‾‾|‾‾‾‾‾‾‾‾‾‾
        _______________|*|___|__________
        ‾‾‾‾‾‾‾‾‾‾‾|‾‾‾|‾|‾‾‾‾‾‾‾‾‾‾‾‾‾‾
        ___________|___|_|______________
        ‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾|‾|‾‾‾|‾‾‾‾‾‾‾‾‾‾
        _______________|_|___|__________
        ‾‾‾‾‾‾‾‾‾‾‾|‾‾‾|‾|‾‾‾‾‾‾‾‾‾‾‾‾‾‾
        ___________|___|_|______________
        ‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾|‾|‾‾‾|‾‾‾‾‾‾‾‾‾‾
        _______________|_|___|__________
        ‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾|‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾
                     `wire2`
        

""" 

import numpy as np 
from qiskit_metal import draw, Dict 
from qiskit_metal.qlibrary.core import QComponent 
from qiskit_metal.toolbox_python.utility_functions import rotate_point
from qiskit_metal.toolbox_python.positioning import NodePositioner

class JunctionArray(NodePositioner, QComponent): 
    """ 
    Inherits from `QComponent` Class.  

    Description: 
        A two-angle bridge free junction array. 
        This implements a junction array superinductor, primarily for fluxonium qubits. 
        Designed in the style of Masluk et al. 2020. 

    Options: 
        * n (int): Number of junction lines 
        * jx/jy  : Dimensions for junction lines 
        * wx/wy  : Dimensions for central vertical wire pads 
                   `wy` determines the gap between the junction lines 
        * undercut: length of the undercut leads on junction line edges 
                    AND alternating central pads  
        * orientation  : 0-> is parallel to x-axis, with orientation (in degrees) counterclockwise
        * pos_x/_y     : `origin` position of junction lead on chip 
                         `origin` is the left-edge-center of the wide-section 
        * layer    : The layer number for the junction lines 
        * undercut_layer   : The layer number for the edge undercut leads
        * alternating_layer: The layer number for the alternating undercut pads 
        

    """
    
    # Default drawing options 
    default_options = Dict( 
        n=20, 
        jx='100um', 
        jy='10um', 
        wx='20um', 
        wy='10um', 
        undercut='15um', 
        orientation='0', 
        pos_x='0um', 
        pos_y='0um', 
        layer='1', 
        undercut_layer='2', 
        alternating_layer='2' 
    )

    # Component metadata 
    # Name prefix for component, if user doesn't provide name 
    component_metadata = Dict( 
        short_name='JunctionArray', 
        _qgeometry_table_poly='True', 
    )

    def make(self): 
        """ Converts self.options into QGeometry. """ 
        p = self.parse_options() 
        nodes = Dict()
 
        spacing = p.jy + p.wy 
        positions = (np.arange(p.n) - (p.n-1)/2)*spacing 

        # Junction lines and edge undercut leads 
        junction_rects = []
        lead_rects     = []
        for y in positions: 
            junction_rect = draw.rectangle(p.jx, p.jy) 
            junction_rect = draw.translate(junction_rect, 0, y) 

            base_undercut = draw.rectangle(p.undercut, p.jy)
            undercuts = [ 
                draw.translate(base_undercut, -(p.undercut + p.jx)/2, y), 
                draw.translate(base_undercut, +(p.undercut + p.jx)/2, y),
            ] 

            junction_rects.append(junction_rect) 
            lead_rects.extend(undercuts)       

        # Combining all junction lines into one component 
        # Combining all edge undercut leads into one component 
        junction_rects = draw.union(*junction_rects) 
        lead_rects     = draw.union(*lead_rects) 


        wire_rects = []
        pad_rects  = []
        for i, y in enumerate(positions[:-1]):
            wire_rect = draw.rectangle(p.wx, p.wy)
            wire_rect = draw.translate(wire_rect, 0, y + (p.jy + p.wy)/2)

            undercut = draw.rectangle(p.undercut, p.wy)
            if i%2: 
                undercut = draw.translate(undercut, +(p.wx + p.undercut)/2, y + (p.jy + p.wy)/2) 
            else: 
                undercut = draw.translate(undercut, -(p.wx + p.undercut)/2, y + (p.jy + p.wy)/2)

            wire_rects.append(wire_rect) 
            pad_rects.append(undercut)

        wire_rects = draw.union(*wire_rects) 
        pad_rects  = draw.union(*pad_rects)

        # Translations & Rotations 
        geom_list = [junction_rects, wire_rects, lead_rects, pad_rects] 
        geom_list = draw.rotate(geom_list, p.orientation)
        geom_list = draw.translate(geom_list, p.pos_x, p.pos_y) 
        [junction_rects, wire_rects, lead_rects, pad_rects] = geom_list 

        # Converting drawings to qgeometry
        self.add_qgeometry('poly', {'junction_rects': junction_rects}, layer = p.layer)
        self.add_qgeometry('poly', {'wire_rects': wire_rects}, layer=p.layer) 
        self.add_qgeometry('poly', {'edge_leads': lead_rects}, layer=p.undercut_layer) 
        self.add_qgeometry('poly', {'inner_pads': pad_rects}, layer=p.alternating_layer) 

        # Positioning nodes 
        nodes.origin = np.zeros(2) 
        nodes.wire1 = np.array((0, max(positions) + p.jy/2)) 
        nodes.wire2 = np.array((0, min(positions) - p.jy/2)) 

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
