import os
import glob
import yaml
from ..common import print_error, execute, remove_dir, extract_tarball

def build(part, params, env):
    if "dir" in params:
        dir = params["dir"]
        print "Change directory to '{}'".format(dir)
        os.chdir(dir)
    if not os.path.exists("setup.py"):
        print_error("Missing 'setup.py' file")
    remove_dir("dist")
    cmd = ["python", "setup.py", "bdist"]
    ret = execute(cmd)
    if ret:
        print_error(ret)         

    tarballs = glob.glob("dist/*.tar.gz")
    if len(tarballs) == 0:
        print_error("No binary distribution or egg-info is generated")

    """
    eggs = glob.glob("*.egg-info/PKG-INFO")
    if len(eggs) == 0:
        print_error("No binary distribution or egg-info is generated")
    try:
        with open(eggs[0], "r") as file:
            doc = yaml.load(file)
    except Exception as e:
        print_error("Failed to load egg-info", e)
    print "Python package name:", doc["Name"]
    """

def install(part, params, env):
    if "dir" in params:
        os.chdir(params["dir"])
    install_dir = part.install_path()
    tarball = glob.glob("dist/*.tar.gz")[0]
    extract_tarball(tarball, install_dir)

# 'get_debian_controls' will be called by package/debian module
# This function is specific for "debian" packaging module, and may not be
# valid to the packaging modules that designed for other packaging formats
# (such as rpm)
def get_debian_controls(part):
    prerm_script = ("dpkg -L {} | grep \.py$ | while read file\n".format(part.gconfig.name) +
                    "do\n" +
                    "  rm -f \"$file\"[co] >/dev/null\n" +
                    "done\n")
    return { "prerm": prerm_script }
