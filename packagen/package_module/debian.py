import os
import glob
import shutil
from ..common import release_path, target_path, current_dir
from ..common import execute, print_error, is_list_of_string

def control_path(gconfig):
    return os.path.join(current_dir, "control")

def verify_config(gconfig):
    if hasattr(gconfig, "control"):
        if not is_list_of_string(gconfig.control):
            print_error("'control' must be a list of strings")

def package(gconfig):
    deb_file_name = "{}_{}_{}.deb".format(gconfig.name, gconfig.version, gconfig.architecture)
    target_dir = target_path(gconfig)
    debain_dir = os.path.join(target_dir, "DEBIAN")
    if not os.path.exists(debain_dir):
        os.makedirs(debain_dir)

    control_dir = control_path(gconfig)
    files = [os.path.split(path)[1] for path in glob.glob(os.path.join(control_dir, "*"))]
    for e in (gconfig.control if hasattr(gconfig, "control") else []):
        if e not in files:
            print_error("cannot find file '{}' in {}".format(e, control_dir))
        shutil.copy(os.path.join(control_dir, e), debain_dir)

    content = []
    content.append( "Package: {}".format(gconfig.name))
    content.append( "Version: {}".format(gconfig.version))
    content.append( "Architecture: {}".format(gconfig.architecture))
    content.append( "Maintainer: {}".format(gconfig.maintainer))
    if gconfig.depends != "":
        content.append( "Depends: {}".format(gconfig.depends))
    content.append( "Description: {}".format(gconfig.description))

    try:
        fp = open(os.path.join(debain_dir, "control"), "w")
        for line in content:
            fp.write(line + "\n")
        fp.close()
    except Exception as e:
        print_error(e)

    release_dir = release_path(gconfig)
    if not os.path.exists(release_dir):
        os.makedirs(release_dir)
    deb_file_path = os.path.join(release_dir, deb_file_name)

    err = execute(["dpkg-deb", "--build", target_dir, deb_file_path])
    if err:
        print_error(err)
