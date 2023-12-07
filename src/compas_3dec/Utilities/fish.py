__all__ = [
    "blocks_output",
    "save_blocks_output",
    "save_analysis",
    "restore_analysis",
    "contacts_output",
    "save_contacts_output",
    "gravity_equilibrium"
]


def blocks_output():
    """FISH function: get blocks data from 3DEC analysis:

    Returns
    -------
    per block:
        region n in 3DEC
            int
        centroid
            x,y,z (precision = 18)
        mass
            float [Kg]
        volume
            float [mc]
        out of balance force
            fx,fy,fz [N]
        moments
            mx,my,mz [Nm]
        loads
            lx,ly,lz [N]
        velocity
            (vx,vy,vz) [m/s]
        list of vertices (coordinates)
            x,y,z (precision = 18)
    """
    blocks_output = """

;___________________________________________________________________________
fish define blocks_output
    ii = io.out('solve ratio = '+' '+string(mech.solve('ratio-local')))
    ii = io.out('timestep = '+' '+string(mech.timestep))
    ii=io.out(' centr - result - veloc')
    ic = block.contact.head
    loop foreach ib block.list
        bid = block.id(ib)
        br=block.region(ib)
    ii=io.out('block '+string(bid))
    ii=io.out('region '+string(br))
    ii=io.out('centroid'+' '+'='+' '+string(block.pos.x(ib))+','+string(block.pos.y(ib))+','+string(block.pos.z(ib))+' '+string(br))
    ii=io.out('mass '+' '+string(block.mass(ib)))
    ii=io.out('volume '+' '+string(block.vol(ib)))
    vel=block.vel(ib)
    rx=block.force.unbal.x(ib)
    ry=block.force.unbal.y(ib)
    rz=block.force.unbal.z(ib)
    lx=block.force.app.x(ib)
    ly=block.force.app.y(ib)
    lz=block.force.app.z(ib)
    ; if there is gravity, the block weight should be added
    rz=block.force.unbal.z(ib)+block.mass(ib)*global.gravity.z
    ii=io.out('forces'+' '+'='+' '+string(rx)+','+string(ry)+','+string(rz)+' '+string(br))
    ii=io.out('moment'+' '+'='+' '+string(block.moment.x(ib))+','+string(block.moment.y(ib))+','+string(block.moment.z(ib))+' '+string(br))
    ii=io.out('loads'+' '+'='+' '+string(lx)+','+string(ly)+','+string(lz)+' '+string(br))
    ii=io.out('velocity'+' '+'='+' '+string(vel)+' '+string(br))
    loop foreach vi block.gplist(ib)
        ii = io.out('vertex'+' '+'='+' '+string(block.gp.pos(vi))+' '+string(block.region(block.gp.hostblock(vi))))
        vi = block.gp.next(vi)
    endloop
    ib = block.next(ib)
    endloop
end
;___________________________________________________________________________
"""
    return blocks_output


def save_blocks_output(state):
    save_blocks_output = """
;___________________________________________________________________________
log on
log-file '{}.txt'
@blocks_output
log off
;___________________________________________________________________________
""".format(
        state
    )
    return save_blocks_output


def contacts_output():
    """FISH function: get contacts data from 3DEC analysis:

    Returns
    -------

    """
    contacts_output = """
;___________________________________________________________________________
fish define contacts_output
  loop foreach ic block.contact.list()
  ii=io.out('contact'+' '+'='+' '+string(ic)+' '+string(block.contact.type(ic))+' '+string(block.id(block.contact.b1(ic)))+' '+string(block.id(block.contact.b2(ic)))+' '+string(block.contact.pos(ic))+' '+string(block.contact.normal(ic)))
    loop foreach si block.contact.subcontactlist(ic)
        ii=io.out('subcontact'+' '+'='+' '+string(block.subcontact.pos(si))+' '+string(block.subcontact.force.norm(si))+' '+string(block.subcontact.force.shear(si))+' '+string(si)+' '+string(block.subcontact.disp.norm(si))+' '+string(block.subcontact.disp.shear(si)))
        fi = block.subcontact.face(si)
        if fi then
            fo = block.face.bface(fi)
            ii = io.out('face centroid'+' '+'='+' '+string(block.face.pos(fo)))
        endif
        si = block.subcontact.next(si)
    endloop
  ic = block.contact.next(ic)
  endloop
  end
;___________________________________________________________________________
"""
    return contacts_output


def save_contacts_output(state):
    save_contacts_output = """
;___________________________________________________________________________
log on
log-file '{}.txt'
@contacts_output
log off
;___________________________________________________________________________
""".format(
        state
    )
    return save_contacts_output


def save_analysis(name, stage):
    """
    Stages:     init
                grav
                step
    """
    save_analysis = """
;_______SAVE ANALYSIS_______________________________________________________
    model save "./{}_{}.sav" compress
;___________________________________________________________________________
""".format(
        name, stage
    )
    return save_analysis


def restore_analysis(name, stage):
    """
    Stages:     init
                grav
                step
    """
    restore_analysis = """
;_______RESTORE ANALYSIS____________________________________________________
    model restore "./{}_{}.sav"
;___________________________________________________________________________
""".format(
        name, stage
    )
    return restore_analysis


def gravity_equilibrium(steps, keyword, ratio, time, final_ratio, time_final_step):
    """_summary_

    Parameters
    ----------
    steps : _type_
        _description_
    keyword : _type_
        _description_
    ratio : _type_
        _description_
    time : _type_
        _description_
    final_ratio : _type_
        _description_
    time_final_step : _type_
        _description_

    Returns
    -------
    _type_
        _description_
    """

    g = (-9.806 / steps)
    g = round(g, 3)
    text = ';GRAVITY APPLIED IN' + ' ' + str(steps) + ' ' + 'STEPS ' + '\n'
    text += ';^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^' + '\n'
    for i in range(steps):
        gr = g * (i+1)
        # header = ';^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^' + '\n'
        header = ';_____GRAVITY_____' + " " + 'step' + " " + str(i+1) + '\n'
        header += 'model gravity' + ' ' + '0' + " " + '0' + " " + str(gr) + '\n'
        header += 'model solve' + " " + str(keyword) +  " " + str(ratio) + \
            " " + 'time' + " " + str(time) + '\n'
        text += header
    text += 'model solve' + " " + str(keyword) + " " +str(final_ratio) + \
            " " + 'time' + " " + str(time_final_step) + '\n'
    text += ';^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^' + '\n'
    return text




