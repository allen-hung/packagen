import os
from ..common import print_error, execute_script, is_list_of_string, shared_root_path

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

def make_parameters(params):
    parameters = []
    if "makefile" in params:
        parameters += ["-f", params["makefile"]]
    if "parameters" in params and params["parameters"] is not None:
        if is_list_of_string(params["parameters"]) is False:
            print_error("'{}' must be a list of string".format(module_name + "-parameters"))
        parameters += params["parameters"]
    return parameters

def build(part, params, env):
    root_dir = shared_root_path(part.gconfig)
    extra_paths(root_dir, env) 
    parameters = make_parameters(params)
    command_line = " ".join(["make"] + parameters)
    err = execute_script([command_line], env)
    if err:
        print_error(err)

def install(part, params, env):
    install_dir = part.install_path()
    parameters = make_parameters(params)
    command_line = " ".join(["fakeroot", "make"] + parameters + ["install"])
    install_var = "DESTDIR"
    if "install-var" in params and params["install-var"] is not None:
        install_var = params["install-var"]
    env[install_var] = install_dir
    err = execute_script([command_line], env)
    if err:
        print_error(err)

def get_default_part_parameters():
    return { "source-strip": "yes", "source-extract": "yes" }
