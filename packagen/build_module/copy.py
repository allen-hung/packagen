import os
from ..common import copy

def build(build_dir, root_dir, vars, env):
    pass

def install(build_dir, install_dir, root_dir, vars, env):
    copy("$(BUILD)/", "$(INSTALL)/", build_dir, install_dir)

def preferred_default_part_parameters():
    return { "source-strip": "no", "source-extract": "no" }
