# This code was written by Deval Deliwala.
# 
# This code is to be used by QNL. 
# 
# Any modifications or derivative works of this code must retain this 
# notice, and modified files need to carry a notice indicating 
# that they have been altered from the originals.

""" BridgeFreeJunction. 

.. code-block:: 

                      `+y` 
               ________|_____
             /        | |     ∖ 
            |      ___|_|_*    | 
            |    |        |____|              
            |      `+x_+y`|____|- `+x`              
            |    |        |    |              
            |    |        |    | 
            |     ‾‾‾‾‾‾‾‾     | 
             ∖                / 
               ‾‾‾‾‾‾‾‾‾‾‾‾‾‾

"""

import numpy as np 
from qiskit_metal import draw, Dict 
from qiskit_metal.qlibrary.core import QComponent 
from qiskit_metal.toolbox_python.utility_functions import rotate_point
from qiskit_metal.toolbox_python.positioning import NodePositioner

             
class BridgeFreeJunction(NodePositioner, QComponent): 
    """ 
    Inherits `QComponent` Class. 

    Description: 
        A bridge-free junction design similar to the manhattan style junctions. 

    Options: 
        * width       : The width of the junction overlap rectangle 
        * height      : The height of the junction overlap rectangle 
        * wire_width  : The width of the junction wires 
        * wire_x_offset: The offset in x direction w.r.t origin -- sign doesn't matter
        * wire_y_offset: The offset in y direction w.r.t origin -- sign doesn't matter 
        * pos_x/_y    : position of junction on chip 
        * fillet      : The fillet radius of the corners of the junction overlap rectangle 
        * undercut    : The size of the undercut region around the junction overlap rectangle 
        * orientation : 0-> is parallel to x-axis, with orientation (in degrees) counterclockwise 
        * origin: A string representing the corner of the rectangle the wires will be placed next to
                  Valid Options: 
                      * 'upper right' DEFAULT 
                      * 'upper left' 
                      * 'lower right' 
                      * 'lower left' 
        * layer: the layer number for the junction 
        * undercut_layer: the layer number for the undercut 


    """ 

    # Default drawing options 
    default_options = Dict(
        width='100um',
        height='100um', 
        wire_width='5um', 
        wire_x_offset='5um', 
        wire_y_offset='5um', 
        pos_x='0um', 
        pos_y='0um', 
        fillet='0um', 
        undercut='25um', 
        orientation='0', 
        origin='upper right',
        layer='1',
        undercut_layer='2', 
    ) 

    # Component metadata
    # Name prefix for component, if user doesn't provide name 
    component_metadata = Dict( 
        short_name='bridgefreejunction', 
        _qgeometry_table_poly='True', 
    )

    def make(self): 
        """ Convert self.options into QGeometry. """ 
        p = self.parse_options() # string options -> numbers 
        nodes = Dict() 

        # junction overlap rectangle 
        junc_rect = draw.rectangle(p.width, p.height) 

        # surrounding undercut 
        undercut = draw.rectangle(p.width+2*p.undercut, p.height+2*p.undercut) 
        undercut = undercut.buffer(p.fillet) 

        if p.origin == 'upper right': 
            nodes.origin = np.array((+p.width/2, +p.height/2)) 
            p.wire_x_offset = -abs(p.wire_x_offset) 
            p.wire_y_offset = -abs(p.wire_y_offset)
            x_translation = nodes.origin + [p.wire_x_offset, p.undercut/2+p.fillet/2] 
            y_translation = nodes.origin + [p.undercut/2+p.fillet/2, p.wire_y_offset] 
        elif p.origin == 'upper left': 
            nodes.origin = np.array((-p.width/2, +p.height/2)) 
            p.wire_x_offset = +abs(p.wire_x_offset) 
            p.wire_y_offset = -abs(p.wire_y_offset) 
            x_translation = nodes.origin + [p.wire_x_offset, p.undercut/2+p.fillet/2] 
            y_translation = nodes.origin + [-p.undercut/2-p.fillet/2, p.wire_y_offset] 
        elif p.origin == 'lower right': 
            nodes.origin = np.array((+p.width/2, -p.height/2)) 
            p.wire_x_offset = -abs(p.wire_x_offset) 
            p.wire_y_offset = +abs(p.wire_y_offset) 
            x_translation = nodes.origin + [p.wire_x_offset, -p.undercut/2-p.fillet/2] 
            y_translation = nodes.origin + [p.undercut/2+p.fillet/2, p.wire_y_offset] 
        elif p.origin == 'lower left': 
            nodes.origin = np.array((-p.width/2, -p.height/2)) 
            p.wire_x_offset = +abs(p.wire_x_offset) 
            p.wire_y_offset = +abs(p.wire_y_offset) 
            x_translation = nodes.origin + [p.wire_x_offset, -p.undercut/2-p.fillet/2] 
            y_translation = nodes.origin + [-p.undercut/2-p.fillet/2, p.wire_y_offset]
        else: 
            raise Exception('`origin` option not defined correctly') 

        # Wires  
        # `wire_x` is the wire that gets offset translated along x-direction 
        # `wire_y` is the wire that gets offset translated along y-direction
        wire_x = draw.rectangle(p.wire_width, p.undercut+p.fillet) 
        wire_y = draw.rectangle(p.undercut+p.fillet, p.wire_width) 
        
        wire_x = draw.translate(wire_x, *x_translation)
        wire_y = draw.translate(wire_y, *y_translation)  

        junction = draw.union([junc_rect, wire_x, wire_y]) 
        undercut = draw.subtract(undercut, junction) 

        # Translations & Rotations 
        geom_list = [junction, undercut] 
        geom_list = draw.rotate(geom_list, p.orientation, origin=(0, 0)) 
        geom_list = draw.translate(geom_list, p.pos_x, p.pos_y) 
        [junction, undercut] = geom_list
        
        # Converting drawing to qgeometry  
        self.add_qgeometry('poly', {'junction': junction}, layer=p.layer) 
        self.add_qgeometry('poly', {'undercut': undercut}, layer=p.undercut_layer) 

        # Positioning nodes
        nodes['+x_+y'] = nodes.origin + [p.wire_x_offset, p.wire_y_offset] 
        if p.origin == 'upper right':
            nodes['+x'] = nodes.origin + [p.undercut, p.wire_y_offset] 
            nodes['+y'] = nodes.origin + [p.wire_x_offset, p.undercut]
        if p.origin == 'upper left':
            nodes['+x'] = nodes.origin + [-p.undercut, p.wire_y_offset] 
            nodes['+y'] = nodes.origin + [p.wire_x_offset, p.undercut]
        if p.origin == 'lower right':
            nodes['+x'] = nodes.origin + [p.undercut, p.wire_y_offset] 
            nodes['+y'] = nodes.origin + [p.wire_x_offset, -p.undercut]
        if p.origin == 'lower left':
            nodes['+x'] = nodes.origin + [-p.undercut, p.wire_y_offset] 
            nodes['+y'] = nodes.origin + [p.wire_x_offset, -p.undercut]

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
