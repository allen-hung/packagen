import os
import stat
import glob
import shutil
import subprocess
from common import execute, source_path, print_error, print_warn, execute
from common import create_dir, remove_dir
from urlparse import urlparse

DEBUG = False

def move_dir(src, dest):
    remove_dir(dest)
    if DEBUG:
        shutil.copytree(src, dest)
    else:
        shutil.move(src, dest)

def extract_tarball(filename, dest_dir):
    def extract_tgz(tarball, dest_dir):
        return execute(["tar", "zxf", tarball, "-C", dest_dir])

    def extract_txz(tarball, dest_dir):
        return execute(["tar", "xf", tarball, "-C", dest_dir])

    def extract_tar(tarball, dest_dir):
        return execute(["tar", "xf", tarball, "-C", dest_dir])

    def extract_gzip(tarball, dest_dir):
        return "gzip is not yet supported"

    def extract_zip(tarball, dest_dir):
        return execute(["unzip", tarball, "-d", dest_dir])

    extensions = {
        ".tar.xz": extract_txz,
        ".txz": extract_txz,
        ".tar.gz": extract_tgz,
        ".tgz": extract_tgz,
        ".tar": extract_tar,
        ".gz": extract_gzip,
        ".zip": extract_zip,
    }

    match_ext = ""
    for ext, method in extensions.iteritems():
        if len(filename) > len(ext) and filename[-len(ext):] == ext:
            if len(ext) > len(match_ext):
                match_ext = ext
    if len(match_ext) == 0:
        return False

    print "Extracting '{}'".format(filename)
    create_dir(dest_dir)
    err = extensions[match_ext](filename, dest_dir)
    if err:
        raise RuntimeError(err)
    return True        

def get_local_file(input, output):
    black_list = ["package.yaml", "stage", "install", "target", "release", "control"]
    valid_components = []
    for path in input.split("/"):
        if path == ".":
            pass
        elif path == "..":
            raise RuntimeError("'..' is inhibited in specifying a local path")
        else:
            valid_components.append(path)

    if len(valid_components) > 0 and valid_components[0] in black_list:
        raise RuntimeError("'./{}' is reserved for system use and cannot be used to specify a local file".format(valid_components[0]))
    if len(valid_components) == 0:
        url = "*"
    else:
        url = os.path.join(*valid_components)

    file_list = glob.glob(url)
    if len(file_list) == 0:
        print_error("Cannot find any file in '{}'".format(url))
    create_dir(output)
    for file in file_list:
        if file in black_list:
            continue
        dest_path = os.path.join(output, file)
        print "{} -> {}".format(file, dest_path)
        if os.path.isdir(file):
            shutil.copytree(file, dest_path)
        else:
            shutil.copy(file, dest_path)

def get_from_git(url, output, vars):
    if "branch" in vars and vars["branch"] is not None:
        cmd = ["git", "clone", url, "--branch", vars["branch"], output]
    else:
        cmd = ["git", "clone", url, output]
    error = execute(cmd)
    if error:
        raise RuntimeError(error)

def get_by_wget(url, output):
    error = execute(["wget", url, "-P", output])
    if error:
        raise RuntimeError(error)

def pipe_raw(input, output, vars):
    url = input
    if len(url) > 4 and url[-4:] == ".git":
        get_from_git(url, output, vars)
    elif urlparse(url).netloc:
        get_by_wget(url, output)
    else:
        get_local_file(url, output)

def get_yes_no(obj, var_name):
    if isinstance(obj, bool):
        return obj
    elif isinstance(obj, str) and obj.lower() in ["yes", "no"]:
        return True if obj.lower() == "yes" else False
    print_error("'{}' should have value of 'yes' or 'no': {}".format(var_name, obj))

def pipe_extract(input, output, vars):
    if "extract" in vars:
        extract = get_yes_no(vars["extract"], "source-extract")
        if extract is False:
            move_dir(input, output)
            return
    entries = glob.glob(os.path.join(input, "*")) + glob.glob(os.path.join(input, ".*"))
    if len(entries) == 1 and not os.path.isdir(entries[0]):
        extracted = extract_tarball(entries[0], output)
    else:
        extracted = False
    if not extracted:
        move_dir(input, output)

def pipe_control(input, output, vars):
    if "commit" in vars and "tag" in vars:
        print_error("The option 'source-commit' and 'source-tag' are exclusive")

    move_dir(input, output)
    point = None
    if "commit" in vars:
        point = vars["commit"]
    if "tag" in vars:
        point = vars["tag"]
    if point is not None:
        git_dir = os.path.join(output, ".git")
        if not os.path.exists(git_dir) or not os.path.isdir(git_dir):
            print_error(output, "does not contain a git project at top level but checkout point '{}' is specified".format(point))
        os.chdir(output)
        cmd = ["git", "reset", "--hard", point]
        error = execute(cmd)
        if error:
            raise RuntimeError(error)

def pipe_strip(input, output, vars):
    if "strip" in vars:
        strip = get_yes_no(vars["strip"], "source-strip")
        if strip is False:
            move_dir(input, output)
            return
    stripped = []
    while True:
        entries = glob.glob(os.path.join(input, "*"))
        entries += glob.glob(os.path.join(input, ".*")) # take hidden files as well
        if len(entries) == 1 and os.path.isdir(entries[0]):
            input = entries[0]
            stripped.append(input.split("/")[-1])
        else:
            break

    if len(stripped) > 0:
        print "Directory '{}' is stripped".format(os.path.join(*stripped))
 
    move_dir(input, output)

def get_source(part):
    url = part.source
    if url is None or isinstance(url, str) is False or len(url) == 0:
        print "illegal syntax specified in 'source', in part '{}'".format(part.name)
        exit(1)

    gconfig = part.gconfig
    dest_dir = part.source_path()
    temp_dir = os.path.join(source_path(gconfig), ".staged." + part.name)
    remove_dir(temp_dir)
    if gconfig.refresh_source:
        remove_dir(dest_dir)
    elif os.path.exists(dest_dir):
        print_warn("The source of '{}' has been retrieved already,".format(part.name),
                   "in order to refresh the source by retrieving again, use --refresh-source")
        return

    # get source parameters and put them in 'source_vars'
    var_name_prefix = "source-"
    prefix_len = len(var_name_prefix)
    source_vars = dict((k[prefix_len:], v) for k, v in part.doc.iteritems() 
                        if len(k) > prefix_len and k[:prefix_len] == var_name_prefix)

    print "Get source of '{}' from {}".format(part.name, url) 
    input = url
    pipe = ["raw", "extract", "strip", "control"]
    for stage in pipe:
        method_name = "pipe_" + stage 
        method = globals()[method_name]
        output = os.path.join(temp_dir, stage)
        try:
            method(input, output, source_vars)
        except Exception as e:
            print_error("Pull source failed in '{}' stage: {}".format(stage, e)) 
        input = output

    move_dir(output, dest_dir)
    if not DEBUG:
        remove_dir(temp_dir)
    # As the source has been refreshed hereby, the build directory should be invalid.
    # Remove it!
    remove_dir(part.build_path())
