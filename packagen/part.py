import os
from source import get_source
from common import source_path, build_path, install_path, target_path
from common import print_error, is_list_of_string

parts = []

def config_error(args):
    print_error("Error in condfiguration:", args)

class Part(object):
    def __init__(self, name):
        self.name = name
        self.source = None
        self.build = None
        self.doc = None
        self.gconfig = None
        self.targets = []
        self.depends = []

    def build_path(self):
        return os.path.join(build_path(self.gconfig), self.name)

    def source_path(self):
        return os.path.join(source_path(self.gconfig), self.name)

    def build_state_path(self):
        return os.path.join(build_path(self.gconfig), ".state." + self.name)

    def install_path(self):
        return os.path.join(install_path(self.gconfig), self.name)

    def set_build_state(self, state):
        path = self.build_state_path()
        try:
            fp = open(path, "w")
            fp.write(state+"\n")
            fp.close()
        except Exception as e:
            print_error("Failed to write file:", e)

    def get_build_state(self):
        path = self.build_state_path()
        try:
            fp = open(path, "r")
            state = fp.read().split("\n")[0]
            fp.close()
        except Exception as e:
            state = ""
        return state

def check_part_config(name, doc):
    if isinstance(doc, dict) is False:
        config_error("The syntax of part '{}' is illegal".format(name))

    """ check the mandatory parameters """
    if "source" not in doc:
        config_error("'source' is not specified in part '{}'".format(name))
    if "build" not in doc:
        config_error("'build' is not specified in part '{}'".format(name))

    part = Part(name)
    part.source = doc["source"]
    part.build = doc["build"]
    part.doc = doc
    if "depends" in doc:
        dep = doc["depends"]
        if is_list_of_string(dep):
            part.depends = dep
        elif isinstance(dep, str):
            part.depends = [dep]
        elif dep is not None:
            config_error("depends of part '{}' must be a (or a list of) string: {}".format(name, dep))

    if "targets" in doc:
        if not isinstance(doc["targets"], list):
            config_error("'targets' in part '{}' must be a list".format(name))
        part.targets = doc["targets"]

    parts.append(part)

def sort_by_dependency(origins, Object):
    def get_all_deps(obj, is_print, obj_map, level, dependers, visited):
        all_deps = []
        key = obj.get_key()
        if key in dependers:
            msg = "circular dependency detected. '{}' is {} itself".format(key, ", ".join(["depended by '{}'".format(d) for d in dependers]))
            raise RuntimeError(msg)
        if key in visited:
            return all_deps
        visited[key] = True
        for dep in obj.get_depends():
            dep_obj = obj_map[dep]
            all_deps += get_all_deps(dep_obj, is_print, obj_map, level+1, [key] + dependers, visited) + [dep_obj]
        return all_deps

    objs = [Object(o) for o in origins]
    obj_map = dict((o.get_key(), o) for o in objs)
    for o in objs:
        for dep in o.get_depends():
            if dep == o.get_key():
                raise RuntimeError("'{}' depends on itself".format(o.get_key()))
            elif dep not in obj_map:
                raise RuntimeError("'{}' depends on non-existent '{}'".format(o.get_key(), dep))

    visited = {}
    sorted = []
    for o in objs:
        all_deps = get_all_deps(o, False, obj_map, 0, [], {})
        for x in all_deps + [o]: 
            if x.get_key() not in visited:
                visited[x.get_key()] = True
                sorted.append(x.obj)
    return sorted

def sort_parts():
    class Object(object):
        def __init__(self, obj):
            self.obj = obj
        def get_depends(self):
            return self.obj.depends
        def get_key(self):
            return self.obj.name

    global parts
    try:
        parts = sort_by_dependency(parts, Object)
    except Exception as e:
        config_error(e)

def complete_parts(gconfig):
    sort_parts()
    for part in parts:
        print "Pull source of part '{}'".format(part.name)
        part.gconfig = gconfig
        get_source(part)
