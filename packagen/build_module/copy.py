import os
from ..common import copy

def build(part, params, env):
    pass

def install(part, params, env):
    install_dir = part.install_path()
    copy("$(BUILD)/", "$(INSTALL)/", ".", install_dir)

def get_default_part_parameters():
    return { "source-strip": "no", "source-extract": "no" }
