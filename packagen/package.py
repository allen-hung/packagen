import importlib
from common import print_error
from part import parts

def load_module(gconfig):
    try:
        package_name = ".".join(__name__.split(".")[:-1])
        module_str = ".".join([package_name, "package_module", gconfig.package])
        module = importlib.import_module(module_str)
    except Exception as e:
        print_error("Failed to import package module '{}': {}".format(gconfig.package, e))
    return module

def verify_package_config(gconfig):
    module = load_module(gconfig)
    module.verify_package_config(gconfig)

def package(gconfig):
    print "Package '{}'".format(gconfig.name)
    module = load_module(gconfig)
    module.package(gconfig, parts)
