import sys
from config import load_config
from part import complete_parts
from build import build_parts
from package import package, package_verify_config
from common import print_error, remove_all

global_config = None

def check_arguments():
    def arg_refresh_source():
        global_config.refresh_source = True
        global_config.clean_build = True

    def arg_clean_build():
        global_config.clean_build = True

    def arg_clean_all():
        remove_all()
        exit(0)

    args = {
        "--refresh-source": arg_refresh_source,
        "--clean-build": arg_clean_build,
        "clean": arg_clean_all
    }

    for arg in sys.argv[1:]:
        if arg not in args:
            print_error("Unsupported option:", arg)
        args[arg]()

def main():
    config = load_config()
    config["refresh_source"] = False
    config["clean_build"] = False

    global global_config
    global_config = type("Config", (), config)
    package_verify_config(global_config)
    check_arguments()
    complete_parts(global_config)
    build_parts(global_config)
    package(global_config)

main()
