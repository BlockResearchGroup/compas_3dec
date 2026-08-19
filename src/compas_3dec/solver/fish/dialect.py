class ThreeDECFishDialect:
    """Version-selected FISH generator with one stable output schema."""

    major_version = None
    output_schema = 3
    record_prefix = "COMPAS3DEC"

    def definitions(self):
        """Return FISH functions for block, gridpoint and contact output."""
        prefix = self.record_prefix
        version = self.major_version
        return """
; ============================================================================
; compas_3dec result output schema {schema}
; ============================================================================
fish define compas_3dec_write_results
    local out = io.out('{prefix}|META|schema|{schema}')
    out = io.out('{prefix}|META|fish_version|{version}')
    out = io.out('{prefix}|META|ratio_local|' + string(mech.solve('ratio-local')))
    out = io.out('{prefix}|META|timestep|' + string(mech.timestep))

    loop foreach local ib block.list
        local bid = block.id(ib)
        local region = block.region(ib)
        out = io.out('{prefix}|BLOCK|' + string(bid) + '|' + string(region) + ...
            '|' + string(block.pos.x(ib)) + '|' + string(block.pos.y(ib)) + '|' + string(block.pos.z(ib)) + ...
            '|' + string(block.mass(ib)) + '|' + string(block.vol(ib)) + ...
            '|' + string(block.vel.x(ib)) + '|' + string(block.vel.y(ib)) + '|' + string(block.vel.z(ib)) + ...
            '|' + string(block.force.unbal.x(ib)) + '|' + string(block.force.unbal.y(ib)) + '|' + string(block.force.unbal.z(ib)) + ...
            '|' + string(block.force.app.x(ib)) + '|' + string(block.force.app.y(ib)) + '|' + string(block.force.app.z(ib)) + ...
            '|' + string(block.moment.x(ib)) + '|' + string(block.moment.y(ib)) + '|' + string(block.moment.z(ib)))

        loop foreach local gp block.gplist(ib)
            out = io.out('{prefix}|GRIDPOINT|' + string(block.gp.id(gp)) + '|' + string(region) + ...
                '|' + string(block.gp.pos(gp)->x) + '|' + string(block.gp.pos(gp)->y) + '|' + string(block.gp.pos(gp)->z))
        endloop
    endloop

    loop foreach local contact block.contact.list()
        local cid = block.contact.id(contact)
        local region_a = block.region(block.contact.b1(contact))
        local region_b = block.region(block.contact.b2(contact))
        out = io.out('{prefix}|CONTACT|' + string(cid) + '|' + string(region_a) + '|' + string(region_b) + ...
            '|' + string(block.contact.type(contact)) + ...
            '|' + string(block.contact.pos(contact)->x) + '|' + string(block.contact.pos(contact)->y) + '|' + string(block.contact.pos(contact)->z) + ...
            '|' + string(block.contact.normal(contact)->x) + '|' + string(block.contact.normal(contact)->y) + '|' + string(block.contact.normal(contact)->z))

        loop foreach local subcontact block.contact.subcontactlist(contact)
            out = io.out('{prefix}|SUBCONTACT|' + string(block.subcontact.id(subcontact)) + '|' + string(cid) + ...
                '|' + string(block.subcontact.pos(subcontact)->x) + '|' + string(block.subcontact.pos(subcontact)->y) + '|' + string(block.subcontact.pos(subcontact)->z) + ...
                '|' + string(block.subcontact.force.norm(subcontact)) + ...
                '|' + string(block.subcontact.force.shear(subcontact)->x) + '|' + string(block.subcontact.force.shear(subcontact)->y) + '|' + string(block.subcontact.force.shear(subcontact)->z) + ...
                '|' + string(block.subcontact.disp.norm(subcontact)) + ...
                '|' + string(block.subcontact.disp.shear(subcontact)->x) + '|' + string(block.subcontact.disp.shear(subcontact)->y) + '|' + string(block.subcontact.disp.shear(subcontact)->z) + ...
                '|' + string(block.subcontact.stress.norm(subcontact)) + ...
                '|' + string(block.subcontact.stress.shear(subcontact)) + ...
                '|' + string(block.subcontact.area(subcontact)) + ...
                '|' + string(block.subcontact.state(subcontact)))
        endloop
    endloop
end
""".format(
            prefix=prefix,
            schema=self.output_schema,
            version=version,
        ).strip()

    def capture_results(self, filename):
        """Return commands that capture tagged ``io.out`` records."""
        return """
program log-file '{filename}'
program log on truncate
@compas_3dec_write_results
program log off
""".format(filename=str(filename).replace("'", "''")).strip()


class ThreeDECFish7(ThreeDECFishDialect):
    major_version = 7


class ThreeDECFish9(ThreeDECFishDialect):
    major_version = 9


def fish_dialect(version):
    """Return the FISH dialect selected once for a solver instance."""
    text = str(version).strip()
    try:
        major = int(text.split(".", 1)[0])
    except ValueError:
        raise ValueError("Unsupported 3DEC version {!r}.".format(version))

    if major == 7:
        return ThreeDECFish7()
    if major == 9:
        return ThreeDECFish9()
    raise ValueError("Unsupported 3DEC major version {}. Supported versions are 7 and 9.".format(major))
