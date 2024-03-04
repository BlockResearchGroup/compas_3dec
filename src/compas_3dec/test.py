def contact_forces(self, output_3dec_per_vertex, scale_factor, region, mu, Shear=False):
        # visualise contact forces acting on a single block in compression in only one region is given as argument
        # otherwise it visualises action and reaction forces in all blocks
        # contacts = data_from_threedec_contact(str(contact_file))
        normals = []
        points = []
        c_forces = []
        cc_pos = []
        # loop per contact
        for contact in contacts:
            # check if the region is in the contact neighbours
            if region in contacts[contact]['neighbours']:
                #check if the contact has subcontacts otherwise there are no mechanical data from 3DEC
                if contacts[contact]['subcontacts']:
                    # check the position of the region(block) in the neighbours list
                    # according to the position [0] or [1] the contact's normal has to be flipped to visualise compression
                    # and get the contact's normal + the subcontacts' list
                    if contacts[contact]['neighbours'][0] == region:
                        s_dict = contacts[contact]['subcontacts']
                        normal = scale_vector(contacts[contact]['normal'], -1)
                    else:
                        s_dict = contacts[contact]['subcontacts']
                        normal = contacts[contact]['normal']
                    # get the vertices [x,y,z] of the contact face and create a list
                    verts = []
                    for sub in s_dict:
                        vertex = s_dict[sub]['coordinates']
                        verts.append(vertex)
                    #compute centroid from the vertex list
                    centroid = centroid_points(verts)

                    # 3DEC results post-processing 1st part
                    for sub in s_dict:
                        if s_dict[sub]['normal_force']:
                            vertex = s_dict[sub]['coordinates']
                            e1_plane = normalize_vector(
                                (vertex[0] - centroid[0], vertex[1] - centroid[1], vertex[2] - centroid[2]))
                            e2_plane = cross_vectors(normal, e1_plane)
                            break
                    MtorqueG = [0, 0, 0]
                    Mtot = [0, 0, 0]
                    Ntot = 0
                    Stot = [0, 0, 0]

                    # list of shear forces used later for pure shear calculation (no transportation couple)
                    slist = []
                    # 3DEC results post-processing 2nd part
                    for sub in s_dict:
                        vertex = s_dict[sub]['coordinates']
                        ri = ((vertex[0] - centroid[0], vertex[1] -
                            centroid[1], vertex[2] - centroid[2]))
                        Ni = s_dict[sub]['normal_force']

                        # visualise the normal contact forces per subcontact
                        rs.CurrentLayer('3dec_normals')
                        nnn = scale_vector(normal, Ni)
                        Nview = add_vectors(vertex,scale_vector(nnn,scale_factor))
                        if distance_point_point(vertex,Nview)>0.00001:
                            ln = rs.AddLine(vertex,Nview)
                            rs.CurveArrows(ln, 1)

                        # 3DEC results post-processing 2nd part
                        Mi = cross_vectors(ri, scale_vector(normal, Ni))
                        Mtot = sum_vectors([Mtot, Mi])
                        Ntot = Ntot + Ni
                        # check position of the region(block) to switch shear forces direction
                        if contacts[contact]['neighbours'][0] == region:
                            Si = (-1 * (s_dict[sub]['shear_force'][0]), -1 * (s_dict[sub]
                                                                            ['shear_force'][1]), -1 * (s_dict[sub]['shear_force'][2]))
                            Stot = (sum_vectors([Stot, Si]))
                            slist.append(Si)

                            # visualise the shear contact forces per subcontact
                            rs.CurrentLayer('3dec_shear')
                            sview = add_vectors(vertex,scale_vector(Si,scale_factor))
                            if distance_point_point(vertex,sview)>0.00001:
                                ls1 = rs.AddLine(vertex,sview)
                                rs.CurveArrows(ls1, 1)

                            # calculate torque
                            MtorqueGi = cross_vectors(ri, Si)
                            MtorqueG = sum_vectors([MtorqueG, MtorqueGi])

                        else:
                            Si = s_dict[sub]['shear_force']
                            Stot = (sum_vectors([Stot, Si]))
                            slist.append(Si)

                            # visualise the shear contact forces per subcontact
                            rs.CurrentLayer('3dec_shear')
                            sview = add_vectors(vertex,scale_vector(Si,scale_factor))
                            if distance_point_point(vertex,sview)>0.00001:
                                ls2 = rs.AddLine(vertex,sview)
                                rs.CurveArrows(ls2, 1)

                            # calculate torque
                            MtorqueGi = cross_vectors(ri, Si)
                            MtorqueG = sum_vectors([MtorqueG, MtorqueGi])

                    # 3DEC results post-processing 3rd part
                    if Ntot:
                        # contact position (to be checked if this is the pure point from 3DEC or post-processed based on resultant)
                        c_pos = contacts[contact]['position']
                        cc_pos.append(c_pos)

                        # compute the Z-component of the resultant shear contact force
                        Svert = dot_vectors(Stot,Vector.Zaxis())
                        Svert = scale_vector(Vector.Zaxis(),Svert)
                        # compute the third component of the resultant shear contact force after the Z one and the resultant
                        Sother = subtract_vectors(Stot,Svert)

                        # compute the resultant contact force
                        Ftot = sum_vectors([Stot, scale_vector(normal, Ntot)])
                        c_forces.append(Ftot)

                        NN = scale_vector(normal, Ntot)
                        b2 = dot_vectors(Mtot, e1_plane) / Ntot
                        b1 = -1 * dot_vectors(Mtot, e2_plane) / Ntot

                        # point of application of the resultant contact force
                        po = sum_vectors([centroid, scale_vector(
                            e1_plane, b1), scale_vector(e2_plane, b2)])
                        points.append(po)
                        normals.append(normal)

                        Mtorquepo = sum_vectors([MtorqueG, cross_vectors(
                        sum_vectors([centroid, scale_vector(po, -1)]), Stot)])

                        # calculation of the S/N ratio

                        # si = length_vector(Stot)/length_vector(NN)
                        # rs.AddTextDot("%.2f" % si,po)
                        # if (si <= 0.1):
                        #     rs.CurrentLayer('S/N<=0.1')
                        #     rs.AddPoint(po)
                        #     rs.AddTextDot("%.2f" % si,po)
                        # elif (si > 0.1) and (si <= 0.2):
                        #     rs.CurrentLayer('0.1<S/N<=0.2')
                        #     rs.AddPoint(po)
                        #     rs.AddTextDot("%.2f" % si,po)
                        # elif (si > 0.2) and (si <= 0.3):
                        #     rs.CurrentLayer('0.2<S/N<=0.3')
                        #     rs.AddPoint(po)
                        #     rs.AddTextDot("%.2f" % si,po)
                        # elif (si > 0.3) and (si <= 0.4):
                        #     rs.CurrentLayer('0.3<S/N<=0.4')
                        #     rs.AddPoint(po)
                        #     rs.AddTextDot("%.2f" % si,po)
                        # elif (si > 0.4) and (si <= 0.5):
                        #     rs.CurrentLayer('0.4<S/N<=0.5')
                        #     rs.AddPoint(po)
                        #     rs.AddTextDot("%.2f" % si,po)
                        # elif (si > 0.5) and (si <= 0.6):
                        #     rs.CurrentLayer('0.5<S/N<=0.6')
                        #     rs.AddPoint(po)
                        #     rs.AddTextDot("%.2f" % si,po)
                        # elif (si > 0.6) and (si <= 0.7):
                        #     rs.CurrentLayer('0.6<S/N<=0.7')
                        #     rs.AddPoint(po)
                        #     rs.AddTextDot("%.2f" % si,po)
                        # elif (si > 0.7) and (si <= 0.8):
                        #     rs.CurrentLayer('0.7<S/N<=0.8')
                        #     rs.AddPoint(po)
                        #     rs.AddTextDot("%.2f" % si,po)
                        # elif (si > 0.8) and (si <= 0.9):
                        #     rs.CurrentLayer('0.8<S/N<=0.9')
                        #     rs.AddPoint(po)
                        #     rs.AddTextDot("%.2f" % si,po)
                        # elif (si > 0.9) and (si <= 1.0):
                        #     rs.CurrentLayer('0.9<S/N<=1.0')
                        #     rs.AddPoint(po)
                        #     rs.AddTextDot("%.2f" % si,po)

                        rs.CurrentLayer('Default')
                        rs.LayerVisible('3dec_shear', False)

                        # calculation of the S/N*mu ratio
                        # closeness to limit
                        n_mu = (length_vector(NN))*mu
                        sil = length_vector(Stot)/n_mu
                        # rs.AddTextDot("%.2f" % sil,po)

                        if (sil <= 0.1):
                            rs.CurrentLayer('S/N*mu<=0.1')
                            rs.AddPoint(po)
                            rs.AddTextDot("%.2f" % sil,po)
                        elif (sil > 0.1) and (sil <= 0.2):
                            rs.CurrentLayer('0.1<S/N*mu<=0.2')
                            rs.AddPoint(po)
                            rs.AddTextDot("%.2f" % sil,po)
                        elif (sil > 0.2) and (sil <= 0.3):
                            rs.CurrentLayer('0.2<S/N*mu<=0.3')
                            rs.AddPoint(po)
                            rs.AddTextDot("%.2f" % sil,po)
                        elif (sil > 0.3) and (sil <= 0.4):
                            rs.CurrentLayer('0.3<S/N*mu<=0.4')
                            rs.AddPoint(po)
                            rs.AddTextDot("%.2f" % sil,po)
                        elif (sil > 0.4) and (sil <= 0.5):
                            rs.CurrentLayer('0.4<S/N*mu<=0.5')
                            rs.AddPoint(po)
                            rs.AddTextDot("%.2f" % sil,po)
                        elif (sil > 0.5) and (sil <= 0.6):
                            rs.CurrentLayer('0.5<S/N*mu<=0.6')
                            rs.AddPoint(po)
                            rs.AddTextDot("%.2f" % sil,po)
                        elif (sil > 0.6) and (sil <= 0.7):
                            rs.CurrentLayer('0.6<S/N*mu<=0.7')
                            rs.AddPoint(po)
                            rs.AddTextDot("%.2f" % sil,po)
                        elif (sil > 0.7) and (sil <= 0.8):
                            rs.CurrentLayer('0.7<S/N*mu<=0.8')
                            rs.AddPoint(po)
                            rs.AddTextDot("%.2f" % sil,po)
                        elif (sil > 0.8) and (sil <= 0.9):
                            rs.CurrentLayer('0.8<S/N*mu<=0.9')
                            rs.AddPoint(po)
                            rs.AddTextDot("%.2f" % sil,po)
                        elif (sil > 0.9) and (sil <= 1.0):
                            rs.CurrentLayer('0.9<S/N*mu<=1.0')
                            rs.AddPoint(po)
                            rs.AddTextDot("%.2f" % sil,po)

                        rs.CurrentLayer('Default')
                        rs.LayerVisible('Shear/N*mu', False)

                        # contact forces visualisation
                        end_point_2 = sum_vectors(
                            [po, scale_vector(Ftot, -scale_factor)])
                        end_point_4 = sum_vectors(
                            [po, scale_vector(NN, -scale_factor)])
                        end_point_6 = sum_vectors(
                            [po, scale_vector(Stot, -scale_factor)])
                        end_point_21 = sum_vectors(
                        [po, scale_vector(Mtorquepo, -scale_factor)])

                        end_point_Svert = sum_vectors(
                            [po, scale_vector(Svert, -scale_factor)])
                        end_point_Sother = sum_vectors(
                            [po, scale_vector(Sother, -scale_factor)])

                        rs.CurrentLayer('Thrust_pt')
                        rs.AddPoint(po)

                        rs.CurrentLayer('Thrust')
                        if distance_point_point(po, end_point_2) > 0.0001:
                            th1 = rs.AddLine(po, end_point_2)
                            rs.CurveArrows(th1, 1)

                        rs.CurrentLayer('Thrust_N')
                        if distance_point_point(po, end_point_4) > 0.0001:
                            tn1 = rs.AddLine(po, end_point_4)
                            rs.CurveArrows(tn1, 1)

                        rs.CurrentLayer('Thrust_S')
                        if distance_point_point(po, end_point_6) > 0.0001:
                            ts1 = rs.AddLine(po, end_point_6)
                            rs.CurveArrows(ts1, 1)

                        rs.CurrentLayer('Thrust_Svert')
                        if distance_point_point(po, end_point_Svert) > 0.0001:
                            tsv = rs.AddLine(po, end_point_Svert)
                            rs.CurveArrows(tsv, 1)

                        rs.CurrentLayer('Thrust_Sother')
                        if distance_point_point(po, end_point_Sother) > 0.0001:
                            tso = rs.AddLine(po, end_point_Sother)
                            rs.CurveArrows(tso, 1)

                        rs.CurrentLayer('Torque')
                        if distance_point_point(po, end_point_21) > 0.0001:
                            to1 = rs.AddLine(po, end_point_21)
                            rs.CurveArrows(to1, 1)


                        if Shear == True:
                            # pure shear visualisation
                            mvecs = [0,0,0]
                            refvecs = []
                            # loop in the vertex, shear forces lists per contact
                            for i,l in zip(verts,slist):
                                svec = Vector.from_start_end(i,l)
                                refvec = subtract_vectors(i,po)
                                mvec = cross_vectors(refvec,svec)
                                # resultant moment
                                mvecs = (sum_vectors([mvecs, mvec]))
                                refvecs.append(refvec)
                            normal = normalize_vector(cross_vectors(refvecs[1],refvecs[0]))
                            d = length_vector(mvecs)/length_vector(Stot)
                            dire = normalize_vector(cross_vectors(normal,Stot))
                            direc = add_vectors(po,scale_vector(dire,d))
                            rr = add_vectors(direc,scale_vector(Stot,scale_factor))

                            rs.CurrentLayer('Shear')
                            if distance_point_point(direc, rr) > 0.0001:
                                sh1 = rs.AddLine(rr, direc)
                                rs.CurveArrows(sh1, 2)

            rs.CurrentLayer('Default')
            rs.LayerVisible('Thrust', False)
            rs.LayerVisible('Thrust_N', False)
            rs.LayerVisible('Thrust_S', False)
            rs.LayerVisible('Thrust_Svert', False)
            rs.LayerVisible('Thrust_Sother', False)
            rs.LayerVisible('Thrust_pt', False)
            rs.LayerVisible('Torque', False)
            rs.LayerVisible('3dec_normals', False)
            rs.LayerVisible('3dec_shear', False)
            rs.LayerVisible('Shear', False)

        return [c_forces], [points], [normals], [cc_pos]
