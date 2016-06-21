import json
from subprocess import check_output
from os.path import realpath, join, dirname
import shutil
from os import system

from pkg_resources import resource_string
from .mesh import Mesh
from ..utils import Struct

mypath = (realpath(__file__))[:-9]

with open(join(mypath, "default.json"), "r") as f:
    default_config = json.load(f)
#default_config = json.loads(resource_string("nekpy.tools", "default.json").decode())

with open(join(mypath, "template.SIZE"), "r") as f:
    size_template = f.read()

with open(join(mypath, "template.size_mod"), "r") as f:
    size_mod_template = f.read()

with open(join(mypath, "template.rea"), "r") as f:
    rea_template = f.read()

with open(join(mypath, "template.box"), "r") as f:
    box_template = f.read()

rea_legacy = """{}
  ***** CURVED SIDE DATA *****
           0 Curved sides follow IEDGE,IEL,CURVE(I),I=1,5, CCURVE
  ***** BOUNDARY CONDITIONS *****
  ***** FLUID   BOUNDARY CONDITIONS *****
{}
  ***** THERMAL BOUNDARY CONDITIONS *****
{}"""

rea_new = """{elements_total:11d}  3 {elements_total:11d}           NEL,NDIM,NELV
{root_mesh[0]: E} {extent_mesh[0]: E} {shape_mesh[0]}
{root_mesh[1]: E} {extent_mesh[1]: E} {shape_mesh[1]}
{root_mesh[2]: E} {extent_mesh[2]: E} {shape_mesh[2]}
{left_bound:3s} {right_bound:3s} {front_bound:3s} {back_bound:3s} {bottom_bound:3s} {top_bound:3s}
{left_boundv:3s} {right_boundv:3s} {front_boundv:3s} {back_boundv:3s} {bottom_boundv:3s} {top_boundv:3s}
 **TAIL OPTS**"""

def genrun(name, config_in, tusr, 
        do_map=False, 
        do_clean=False, 
        do_make=False, 
        legacy=False, 
        makenek="makenek",
        tools=None):

    config = {}
    config.update(default_config)
    config.update(config_in)

    legacy = legacy or "legacy" in config_in

    if legacy:
        nek_dir = join(dirname(makenek),"..")
    else:
        nek_dir = dirname(makenek)

    with open("{:s}.json".format(name), "w") as f:
        json.dump(config, f, indent=2)

    ''' Computing stuff '''

    # loads the configuration into current variable scope
    c = Struct(config)

    c.dealiasing_order = c.order * 3 / 2
    c.ltorder = abs(c.torder)

    # Manipulate the configuration here
    c.elements_total = c.shape_mesh[0] * c.shape_mesh[1] * c.shape_mesh[2]

    if c.left_bound == 'P':
        c.left_boundv = 'P'

    if c.right_bound == 'P':
        c.right_boundv = 'P'

    if c.front_bound == 'P':
        c.front_boundv = 'P'

    if c.back_bound == 'P':
        c.back_boundv = 'P'

    if c.top_bound == 'P':
        c.top_boundv = 'P'

    if c.bottom_bound == 'P':
        c.bottom_boundv = 'P'

    if legacy:
        # Create a mesh object with a single box
        msh = Mesh(c.root_mesh, c.extent_mesh, c.shape_mesh,
        [c.left_bound, c.front_bound, c.right_bound, c.back_bound, c.top_bound, c.bottom_bound])

        # Generate the list of elements
        msh.generate_elements()
        # Get the elements in corner format for the rea file
        mesh_data = msh.get_mesh_data()

        # Generate the list of boundaries, i.e. element faces
        msh.generate_faces()
        # Get the fluid boundaries in the rea format
        fluid_boundaries = msh.get_fluid_boundaries()
        # Switch some fluid boundaries to corresponding thermal boundaries
        thermal_boundaries = fluid_boundaries.replace('SYM', 'I  ').replace('W  ', 'I  ')

        # Assemble the bits of the rea file together
        mesh_rea = rea_legacy.format(mesh_data, fluid_boundaries, thermal_boundaries)

        # map the mesh, targeting c.procs ranks
        msh.set_map(c.procs)
        # get the map in the format nek is expecting
        map_data = msh.get_map()
 
    else:
        # Assemble the bits of the rea file together
        mesh_rea = rea_new.format(**c._attrs)

    # writes the current variable scope to the configuration
    config = c._attrs

    ''' Writing stuff '''

    size = size_template.format(**config)
    with open("SIZE", "w") as f:
        f.write(size)

    size = size_mod_template.format(**config)
    with open("size_mod.F90", "w") as f:
        f.write(size)

    rea = rea_template.format(mesh_rea=mesh_rea, **config)
    with open("{:s}.rea".format(name), "w") as f:
        f.write(rea)

    box = box_template.format(**config)
    with open("{:s}.box".format(name), "w") as f:
        f.write(box)
    
    usr = tusr.format(**config)
    with open("{:s}.usr".format(name), "w") as f:
        f.write(usr)

    if legacy:
        with open("{:s}.map".format(name), "w") as f:
            f.write(map_data)

    log = ""
    if do_clean:
        cmd = [makenek, "clean" , nek_dir]
        log += check_output(cmd).decode() + "\n"

    if do_make:
        print(makenek, name, nek_dir)
        cmd = [makenek, name, nek_dir] 
        log += check_output(cmd).decode()

    return log
