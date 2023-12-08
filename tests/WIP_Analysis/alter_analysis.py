    @classmethod
    def geometry_dat_concave(cls, assembly_3dec, path):
        """Create the .dat files of the Blocks and Supports geometry for 3DEC from an
        Assembly_3DEC object with concave blocks.

        Parameters
        ----------
        assembly_3dec : _type_
            _description_
        path : _type_
            _description_

        Returns
        -------
        :files:`block_geometry.dat and support_geometry.dat`
        """
        string_s = ";__create geometry__" + "\n"
        string_b = ";__create geometry__" + "\n"
        s_comp_dict = {}
        b_comp_dict = {}
        for node in assembly_3dec.nodes():
            if assembly_3dec.graph.node_attribute(node, "is_support") == True:
                support = assembly_3dec.node_block(node)
                name = "support_geometry.dat"
                geometry_path_s = os.path.join(path, name)
                node_i = int(node)
                s_comp_group = assembly_3dec.graph.node_attribute(node_i, "comp_group")
                s_comp_dict[node_i] = s_comp_group
                string_s += threedec7_support_description(support, node_i, precision=10)
            else:
                block = assembly_3dec.node_block(node)
                group = assembly_3dec.graph.node_attribute(node, "3dec_group")
                name = "block_geometry.dat"
                geometry_path_b = os.path.join(path, name)
                node_j = int(node)
                b_comp_group = assembly_3dec.graph.node_attribute(node_j, "comp_group")
                b_comp_dict[node_j] = b_comp_group
                string_b += threedec7_block_description(block, group, node_j, precision=10)

        joined_block_names = find_duplicate_dict(b_comp_dict)
        for j in joined_block_names:
            string_b += ("block join range region {}".format(j)) + "\n"
        joined_block_s_names = find_duplicate_dict(s_comp_dict)
        for js in joined_block_s_names:
            string_s += ("block join range region {}".format(js)) + "\n"
        overwrite_file(geometry_path_s, string_s)
        overwrite_file(geometry_path_b, string_b)
        return

    @classmethod
    def geometry_dat_convex(cls, assembly_3dec, path):
        """Create the .dat files of the Blocks and Supports geometry for 3DEC from an
        Assembly_3DEC object with convex blocks.

        Parameters
        ----------
        assembly_3dec : _type_
            _description_
        path : _type_
            _description_

        Returns
        -------
        :files:`block_geometry.dat and support_geometry.dat`
        """
        string_s = ";__create geometry__" + "\n"
        string_b = ";__create geometry__" + "\n"

        for node in assembly_3dec.nodes():
            if assembly_3dec.graph.node_attribute(node, "is_support") == True:
                support = assembly_3dec.node_block(node)
                name = "support_geometry.dat"
                geometry_path_s = os.path.join(path, name)
                node_i = int(node)
                string_s += threedec7_support_description(support, node_i, precision=10)
            else:
                block = assembly_3dec.node_block(node)
                group = assembly_3dec.graph.node_attribute(node, "3dec_group")
                name = "block_geometry.dat"
                geometry_path_b = os.path.join(path, name)
                node_j = int(node)
                string_b += threedec7_block_description(block, group, node_j, precision=10)
        overwrite_file(geometry_path_s, string_s)
        overwrite_file(geometry_path_b, string_b)
        return
