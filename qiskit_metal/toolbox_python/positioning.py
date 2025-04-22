from qiskit_metal.toolbox_metal.parsing import parse_entry

class NodePositioner():
    """
    Mixin to add a method for positioning a component based on one of its nodes.

    """
    def position(self, node_key: str, pos: tuple):
        """
        Moves the component so that the specified node is relocated to new_xy.

        Parameters
        ----------
        node_key : str
            The name of the node to reposition.
        new_xy : tuple of float
            The new global coordinates (x, y) where the node should be placed.

        """
        # Convert current pos_x and pos_y (which may be strings like '5mm') into floats.
        x_origin = parse_entry(self.options.pos_x, 'mm')
        y_origin = parse_entry(self.options.pos_y, 'mm')
        
        # Retrieve the current global position of the node.
        node_xy_curr = self.nodes.get(node_key)
        if node_xy_curr is None:
            raise ValueError(f"Node '{node_key}' not found in the component.")
        nx_curr, ny_curr = node_xy_curr

        # Calculate the shift needed.
        dx = pos[0] - nx_curr
        dy = pos[1] - ny_curr

        # Update the component's position.
        self.options.pos_x = x_origin + dx
        self.options.pos_y = y_origin + dy

        self.rebuild()
