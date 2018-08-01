import os
import glob
from ..common import release_path, target_path, current_dir
from ..common import execute, print_error, is_list_of_string

def debian_control_path(gconfig):
    return os.path.join(current_dir, "control")

def verify_package_config(gconfig):
    if hasattr(gconfig, "control"):
        if gconfig.control is None:
            gconfig.control = []
        if not is_list_of_string(gconfig.control):
            print_error("'control' must be a list of strings")
    else:
        gconfig.control = []

def generate_control_files(gconfig, parts):
    target_dir = target_path(gconfig)

    # Make dir "DEBIAN" for control files
    target_control_dir = os.path.join(target_dir, "DEBIAN")
    if not os.path.exists(target_control_dir):
        os.makedirs(target_control_dir)

    # Get the control scripts from the build module of each part, if any
    controls = {}
    for part in parts:
        if hasattr(part.build_module, "get_debian_controls"):
            part_controls = part.build_module.get_debian_controls(part)
            for key, value in part_controls.iteritems():
                if key not in controls:
                    controls[key] = ""
                controls[key] += "# from '{}'\n".format(part.name) + value + "\n"
    for key, value in controls.iteritems():
        controls[key] = "# Automatically added by packagen\n" + value + "# End automatically added section\n"

    # Get the specified control files locate in 'control' dir
    src_control_dir = debian_control_path(gconfig)
    existent_files = [os.path.split(path)[-1] for path in glob.glob(os.path.join(src_control_dir, "*"))]
    for cntl in gconfig.control:
        if cntl not in existent_files:
            print_error("cannot find file '{}' in {}".format(cntl, src_control_dir))
        try:
            path = os.path.join(src_control_dir, cntl)
            with open(path, "r") as file:
                content = file.read()
            if cntl in controls:
                content += "\n" + controls[cntl]
                del controls[cntl]
            path = os.path.join(target_control_dir, cntl)
            with open(path, "w") as file:
                file.write(content)
            st = os.stat(path)
            os.chmod(path, st.st_mode | 0o111)
        except Exception as e:
            print_error("Failed to access file:", e)

    for cntl, value in controls.iteritems():
        try:
            path = os.path.join(target_control_dir, cntl)
            with open(path, "w") as file:
                file.write("#!/bin/sh\nset -e\n")
                file.write(value)
            st = os.stat(path)
            os.chmod(path, st.st_mode | 0o111)
        except Exception as e:
            print_error("Failed to write '{}': {}".format(cntl, e))

    # Generate "control" file
    content = []
    content.append( "Package: {}".format(gconfig.name))
    content.append( "Version: {}".format(gconfig.version))
    content.append( "Architecture: {}".format(gconfig.architecture))
    content.append( "Maintainer: {}".format(gconfig.maintainer))
    if gconfig.depends != "":
        content.append( "Depends: {}".format(gconfig.depends))
    content.append( "Description: {}".format(gconfig.description))
    try:
        fp = open(os.path.join(target_control_dir, "control"), "w")
        for line in content:
            fp.write(line + "\n")
        fp.close()
    except Exception as e:
        print_error(e)

def package(gconfig, parts):
    generate_control_files(gconfig, parts)
    target_dir = target_path(gconfig)
    release_dir = release_path(gconfig)
    if not os.path.exists(release_dir):
        os.makedirs(release_dir)
    deb_file_name = "{}_{}_{}.deb".format(gconfig.name, gconfig.version, gconfig.architecture)
    deb_file_path = os.path.join(release_dir, deb_file_name)
    err = execute(["dpkg-deb", "--build", target_dir, deb_file_path])
    if err:
        print_error(err)
