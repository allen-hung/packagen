import os
from ..common import print_error, execute_script, is_list_of_string

module_name = "make"

def extra_paths(root_dir, env):
    c_include_dirs = ["usr/include", "usr/local/include"]
    c_include_path = ":".join(os.path.join(root_dir, dir) for dir in c_include_dirs)
    env["C_INCLUDE_PATH"] = c_include_path
    env["CPLUS_INCLUDE_PATH"] = c_include_path
    ld_dirs = ["usr/local/lib", "lib", "usr/lib"]
    ld_path = ":".join(os.path.join(root_dir, dir) for dir in ld_dirs)
    env["LD_LIBRARY_PATH"] = ld_path
    env["LIBRARY_PATH"] = ld_path

def make_parameters(vars):
    parameters = []
    if "makefile" in vars:
        parameters += ["-f", vars["makefile"]]
    if "parameters" in vars and vars["parameters"] is not None:
        if is_list_of_string(vars["parameters"]) is False:
            print_error("'{}' must be a list of string".format(module_name + "-parameters"))
        parameters += vars["parameters"]
    return parameters

def build(build_dir, root_dir, vars, env):
    extra_paths(root_dir, env) 
    os.chdir(build_dir)
    parameters = make_parameters(vars)
    command_line = " ".join(["make"] + parameters)
    err = execute_script([command_line], env)
    if err:
        print_error(err)

def install(build_dir, install_dir, root_dir, vars, env):
    extra_paths(root_dir, env) 
    os.chdir(build_dir)
    parameters = make_parameters(vars)
    command_line = " ".join(["fakeroot", "make"] + parameters + ["install"])
    install_var = "DESTDIR"
    if "install-var" in vars and vars["install-var"] is not None:
        install_var = vars["install-var"]
    env[install_var] = install_dir
    err = execute_script([command_line], env)
    if err:
        print_error(err)
