import os
import gdspy 
import logging
import numpy as np 
from shapely import difference 
from shapely import box
from shapely.ops import unary_union 
from shapely.geometry import Polygon, MultiPolygon
from shapely.errors import TopologicalError
from qiskit_metal import Dict 
from qiskit_metal.qlibrary.core import QComponent

# Python >=3.8
from functools import cached_property
logging.basicConfig(level=logging.INFO)

class Buffer(): 
    """ 
    Adds a global buffer to every component in qiskit-metal design.
    """

    def __init__(self, design, buffer_value='30um', no_cheese_layer=2):    
        """ 
        Args: 
            * design            (qiskit_metal.designs.DesignPlanar()): 
                Chip design. 
            * buffer_value      (float or string): 
                Buffer amount for no-cheese. 
            * no_cheese_layer   (int): 
                Layer for manual no-cheesing components.  
        """

        self.design             = design 
        self.buffer_value       = design.parse_value(buffer_value)
        self.no_cheese_layer    = no_cheese_layer

    @cached_property
    def export_to_gds(self, filename='ignore.gds'): 
        gds = self.design.renderers.gds
        gds.options.cheese['view_in_file'] = {'main': {1: False}} 
        gds.options.no_cheese['view_in_file'] = {'main': {1: False}}

        logging.info(f" Generating intermediate {filename}. Deleting afterwards.")
        gds.export_to_gds(filename)
        os.remove(filename)
        return gds 

    def extract_geometries(self):
        # Extract all geometries built in GDS file 
        info = self.export_to_gds.chip_info['main']
        ground_geometries = info[1]['q_subtract_true'].tolist() 

        # Convert all geometries back into Shapely 
        all_polys = []
        for g in ground_geometries:
            if isinstance(g, gdspy.path.FlexPath):
                shells = g.get_polygons()
            elif isinstance(g, gdspy.polygon.Polygon): 
                shells = g.polygons
            elif isinstance(g, gdspy.polygon.PolygonSet): 
                shells = g.polygons
            else: 
                continue 
            for pts in shells:
                all_polys.append(Polygon(pts))

        # Merge shapely polygons into one MultiPolygon object. 

        # To prevent fatal error, and allow for viewing messed up geometries 
        # afterwards, we iteratively add every shapely polgon to the merged
        # object. If a component is missing afterwards, that means its 
        # geometry got messed up along the way, and you have to fix it. 

        # expensive process, will find better alternative. 
        all_polys.sort(key=lambda p: p.area, reverse=True) 
        merged = None 
        for p in all_polys: 
            if merged is None: 
                merged = p 
                continue 
            try: 
                merged = merged.union(p) # expensive operation 
            except TopologicalError: 
                continue # throw out bad polygons 

        return merged 

    def buffer_polygons(self): 
        # Adds global buffer around every ground layer compoent in chip. 
        buffer_amount = self.design.parse_value(self.buffer_value)
        buffered_chip = self.extract_geometries().buffer(
            distance=buffer_amount, 
            quad_segs=30
        )
        return buffered_chip 

    def no_cheese_polygons(self):
        info = self.export_to_gds.chip_info['main']

        no_cheese_geometries = info[self.no_cheese_layer]['q_subtract_true'].tolist()
        no_cheese_polys = [] 
        for g in no_cheese_geometries: 
            shells = g.polygons 
            for pts in shells: 
                no_cheese_polys.append(Polygon(pts))

        no_cheese_polygon = unary_union(no_cheese_polys)
        return no_cheese_polygon 

    @cached_property
    def full_no_cheese(self):
        info = self.export_to_gds.chip_info['main'] 
        if self.no_cheese_layer in info: 
            return self.buffer_polygons().union(self.no_cheese_polygons()) 
        else:
            return self.buffer_polygons()

    def add_buffer(self):
        self.design.qgeometry.add_qgeometry( 
            'poly', 
            geometry        = {'global_buffer': self.full_no_cheese}, 
            component_name  = 'global_buffer', 
            subtract        = False, 
            layer           = 2, 
        )

class Cheese(Buffer): 
    """ 
    Adds cheese/periphery layer to chip, ignoring buffer regions and 
    components of layer `no_cheese_layer`.

    Assumes cheese options have been set in design.renderers.gds 
    and chip dimensions have been set in design.chips['main']. 
    
    i.e.
    a_gds = design.renderers.gds 
    a_gds.options['cheese']['cheese_0_x'] = '2um' 
    a_gds.options['cheese']['cheese_0_y'] = '2um' 
    a_gds.options['cheese']['delta_x'] = '8um' 
    a_gds.options['cheese']['delta_y'] = '8um'
    a_gds.options['cheese']['edge_nocheese'] = '200um' 

    chip = design.chips['main']
    chip['size']['size_x'] = '10mm' 
    chip['size']['size_y'] = '10mm'

    Generates cheeses of dimension '2um' x '2um' with an '8um' horizontal 
    and vertical spacing between them. And the chip boundary is defined 
    as '10mm' x '10mm'. Cheeses stop '200um' from the chip boundary. 

    """

    def __init__(self, design, buffer_value='30um', no_cheese_layer=2, cheese_layer=0): 
        self.design = design 
        self.buffer_value = buffer_value 
        self.no_cheese_layer = no_cheese_layer
        self.cheese_layer = cheese_layer

        self.add_buffer() # adds buffer around all chip components 

    def generate_cheese(self):
        logging.info(" Starting to build cheeses.   Usually takes <5min.")

        main    = self.design.chips['main']
        cx, cy  = self.design.parse_value([main['size']['center_x'], main['size']['center_y']])
        chip_w, chip_h = self.design.parse_value([main['size']['size_x'], main['size']['size_y']])
        
        cheese_opts = self.design.renderers.gds.options['cheese']
        dx = self.design.parse_value(cheese_opts['delta_x'])
        dy = self.design.parse_value(cheese_opts['delta_y'])
        cw = self.design.parse_value(cheese_opts['cheese_0_x'])
        ch = self.design.parse_value(cheese_opts['cheese_0_y'])
        edge = self.design.parse_value(cheese_opts['edge_nocheese'])
        
        # inner window bounds
        half_w = (chip_w / 2) - edge
        half_h = (chip_h / 2) - edge
        x_min, x_max = cx - half_w, cx + half_w
        y_min, y_max = cy - half_h, cy + half_h
        
        # center-to-center step
        step_x = cw + dx
        step_y = ch + dy
        
        # how many steps outwards to take
        max_i = int((half_w - cw/2) // step_x)
        max_j = int((half_h - ch/2) // step_y)
        
        # cheese centers 
        xs = cx + np.arange(-max_i, max_i + 1) * step_x 
        ys = cy + np.arange(-max_j, max_j + 1) * step_y 
        xx, yy = np.meshgrid(xs, ys) 

        # cheese corners  
        half_w, half_h = cw / 2, ch / 2
        left   = xx - half_w
        right  = xx + half_w
        bottom = yy - half_h
        top    = yy + half_h

        # mask out cheeses that cross chip boundary 
        mask = (left >= x_min) & (right <= x_max) & \
               (bottom >= y_min) & (top <= y_max) 

        cheese_boxes = box(left[mask], bottom[mask], right[mask], top[mask])

        # Merge into one MultiPolygon
        return unary_union(cheese_boxes) 

    def subtract_no_cheese(self): 
        cheese_pattern = self.generate_cheese() 
        no_cheese_area = self.full_no_cheese 

        return difference(cheese_pattern, no_cheese_area)

    def add_cheese(self): 
        qcomp = QComponent(self.design, 'cheeses', make=False) 
        qcomp.add_qgeometry( 
            'poly', 
            {'cheese': self.subtract_no_cheese()}, 
            layer=self.cheese_layer, 
            subtract=True, 
        )
    def export_with_cheese(self, filename='chip.gds'): 
        self.add_cheese() 

        logging.info(f" Exporting chip to {filename}. Usually takes <5min.")
        a_gds = self.design.renderers.gds
        a_gds.options.cheese['view_in_file'] = {'main': {1: False}} 
        a_gds.options.no_cheese['view_in_file'] = {'main': {1: False}}
        a_gds.options.negative_mask = Dict(
            main=[self.cheese_layer, 1, self.no_cheese_layer]
        ) 
        a_gds.export_to_gds(filename)
        logging.info(" Export completed.")











        



