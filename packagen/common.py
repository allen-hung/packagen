import os
import sys
import glob
import shlex
import shutil
import subprocess

current_dir = os.getcwd()

def is_list_of_string(value):
    if isinstance(value, list) is False:
        return False
    for e in value:
        if isinstance(e, str) is False:
            return False
    return True

def create_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def remove_dir(path):
    if os.path.exists(path) and os.path.isdir(path):
        shutil.rmtree(path)

def print_error(*args):
    msg = " ".join(str(arg) for arg in args)
    print >>sys.stderr, "\033[91m%s\033[0m" % msg
    exit(1)

def print_warn(*args):
    msg = " ".join(str(arg) for arg in args)
    print "\033[93m%s\033[0m" % msg

def execute(argv, env=None):
    cmdline = " ".join(argv)
    if len(cmdline) == 0:
        return None
    try:
        print "\033[92m%s\033[0m" % cmdline
        process = subprocess.Popen([cmdline], stderr=subprocess.PIPE, env=env, shell=True)
    except Exception as e:
        return "error in executing {}: {}".format(argv[0], str(e))

    err = process.communicate()[1]
    if process.wait() != 0:
        return "error in executing {}: {}".format(argv[0], err)
    return None

# TODO: this is a WRONG implement
def execute_script(lines, env=None):
    if env is not None:
        os_env = os.environ.copy()
        for k, v in env.iteritems():
            os_env[k] = v
        env = os_env

    err = None
    for line in lines:
        err = execute([line], env)
        if err:
            break
    return err

def copy(src_tag, dst_tag, src_root, dst_root, src_path="*", dst_path=None):
    def mkdir_r(path):
        if path == "" or os.path.exists(path):
            return
        parent, current = os.path.split(path)
        if not os.path.exists(parent):
            mkdir_r(parent)
        os.mkdir(path)

    is_print = src_tag != "" or dst_tag != ""
    os.chdir(src_root)
    if dst_path is None:
        dst_path = src_path
    while len(src_path) > 0 and src_path[0] == '/':
        src_path = src_path[1:]
    while len(dst_path) > 0 and dst_path[0] == '/':
        dst_path = dst_path[1:]
    for src in glob.glob(src_path):
        xx, basename = os.path.split(src)
        full_path = os.path.join(dst_root, dst_path)
        dest_dir, xx = os.path.split(full_path)
        dest = os.path.join(dest_dir, basename)
        show_dest_dir, name = os.path.split(dst_path)
        show_dest = os.path.join(show_dest_dir, basename)
        if os.path.isdir(src):
            if os.path.exists(dest):
                copy(src_tag, dst_tag, src_root, dst_root, os.path.join(src, "*"))
            else:
                if is_print:
                    print "{}{} -> {}{}".format(src_tag, src, dst_tag, show_dest)
                shutil.copytree(src, dest, symlinks=True)
        else:
            if is_print:
                print "{}{} -> {}{}".format(src_tag, src, dst_tag, show_dest_dir)
            mkdir_r(dest_dir)
            if os.path.islink(src):
                linkto = os.readlink(src)
                os.symlink(linkto, dest_dir)
            else:
                shutil.copy(src, dest_dir)

def sigstring(gconfig):
    strs = [gconfig.version, gconfig.architecture]
    return "_".join(strs)

_stage_dir = ".stage"

def source_path(gconfig):
    return os.path.join(current_dir, _stage_dir, sigstring(gconfig), "source")

def build_path(gconfig):
    return os.path.join(current_dir, _stage_dir, sigstring(gconfig), "build")

def install_path(gconfig):
    return os.path.join(current_dir, _stage_dir, sigstring(gconfig), "install")

def shared_root_path(gconfig):
    return os.path.join(current_dir, _stage_dir, sigstring(gconfig), "root")

def target_path(gconfig):
    return os.path.join(current_dir, _stage_dir, sigstring(gconfig), "target")

def release_path(gconfig):
    return os.path.join(current_dir, "release")

def remove_all():
    remove_dir(_stage_dir)
    remove_dir("release")

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
