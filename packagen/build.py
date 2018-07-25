import os
import shutil
from common import build_path, target_path, install_path, global_install_path
from common import print_error, print_warn, create_dir, remove_dir
from common import execute_script, copy

def build_prepare(part, env):
    state = part.get_build_state()
    if state in ["PREPARED", "BUILT", "INSTALLED"]:
        return

    if "build-prepare" in part.doc and part.doc["build-prepare"] is not None:
        prepare = part.doc["build-prepare"]
        if not isinstance(prepare, str):
            print_error("Part '{}': 'build-prepare' must be string".format(part.name))
        os.chdir(part.build_path())
        err = execute_script(prepare.split("\n"), env)
        if err:
            print_error(err)
    part.set_build_state("PREPARED")

def build_override(part, env):
    if "build-override" in part.doc:
        override = part.doc["build-override"]
        if override is None:
            override = ""
        elif not isinstance(override, str):
            print_error("Part '{}': 'build-override' must be string".format(part.name))
        print_warn("Part '{}': 'build-override' is specified and it overrides build() method in '{}' module".format(part.name, part.build))
        os.chdir(part.build_path())
        err = execute_script(override.split("\n"), env)
        if err:
            print_error(err)
        return True
    return False

def install_override(part, env):
    if "install-override" in part.doc:
        override = part.doc["install-override"]
        if override is None:
            override = ""
        elif not isinstance(override, str):
            print_error("Part '{}': 'install-override' must be string".format(part.name))
        print_warn("Part '{}': 'install-override' is specified and it overrides install() method in '{}' module".format(part.name, part.build))
        os.chdir(part.build_path())
        err = execute_script(override.split("\n"), env)
        if err:
            print_error(err)
        return True
    return False

def build_part(part):
    root_dir = global_install_path(part.gconfig)
    install_dir = part.install_path()
    source_dir = part.source_path()
    build_dir = part.build_path()

    if part.gconfig.clean_build:
        remove_dir(build_dir)

    # copy tree: source -> build
    if not os.path.exists(build_dir):
        shutil.copytree(source_dir, build_dir)
        part.set_build_state("CLEAN")
    else:
        print_warn("Part '{}' had even been built,".format(part.name),
                   "in order to perform a clean build, use --clean-build")

    remove_dir(install_dir)

    # get module parameters and put them in 'module_vars'
    var_name_prefix = part.build + "-"
    prefix_len = len(var_name_prefix)
    module_vars = dict((k[prefix_len:], v) for k, v in part.doc.iteritems() 
                            if len(k) > prefix_len and k[:prefix_len] == var_name_prefix)

    env = {
        "BUILD_ROOT": build_path(part.gconfig),
        "INSTALL_ROOT": install_path(part.gconfig),
        "BUILD_DIR": build_dir,
        "INSTALL_DIR": install_dir
    }

    # do the build prepare
    build_prepare(part, env.copy())

    # do the make main
    if build_override(part, env.copy()) is False:
        part.build_module.build(build_dir, root_dir, module_vars, env.copy())
    part.set_build_state("BUILT")

    # do the make install
    create_dir(install_dir)
    if install_override(part, env.copy()) is False:
        part.build_module.install(build_dir, install_dir, root_dir, module_vars, env.copy())
    part.set_build_state("INSTALLED")

def copy_targets(part, target_dir):
    install_dir = part.install_path()
    src_tag = "$(INSTALL)/"
    dst_tag = "$(TARGET)/"
    if len(part.targets) == 0:
        copy(src_tag, dst_tag, install_dir, target_dir)
        return
    for target in part.targets:
        if isinstance(target, str):
            copy(src_tag, dst_tag, install_dir, target_dir, target)
        elif isinstance(target, dict):
            for src, dest in target.iteritems():
                if dest.find("*") >= 0 or dest.find("?") >= 0:
                    print_error("target path cannot contain wildcards:", dest)
                dir, base = os.path.split(dest)
                if base != "":
                    dest = os.path.join(dest, "")
                copy(src_tag, dst_tag, install_dir, target_dir, src, dest)
        else:
            print_error("illegal target '{}' for part '{}'".format(target, part.name))

def build_parts(gconfig):
    from part import parts
    g_install_dir = global_install_path(gconfig)
    g_target_dir = target_path(gconfig)
    remove_dir(g_install_dir)
    remove_dir(g_target_dir)
    for part in parts:
        print "Build part '{}'".format(part.name)
        build_part(part)
        print "Prepare taregt environment"
        copy_targets(part, g_target_dir)
        copy("", "", part.install_path(), g_install_dir)
