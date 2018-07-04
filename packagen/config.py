import os
import sys
import yaml
from part import check_part_config
from common import is_list_of_string, print_error

config_filename = "package.yaml"

def config_error(args):
    print_error("Error in condfiguration:", args)

def check_name_syntax(ver):
    # TODO: implement the check
    return True

def check_version_syntax(ver):
    if not isinstance(ver, str):
        config_error("version must be a string (hint: quote the version number using ' or \")")
    return True

def addjust_keys(doc):
    if isinstance(doc, dict):
        for key, value in doc.iteritems():
            new_key = key.lower()
            if key != new_key:
                del doc[key]
                print "key: " + key
                doc[new_key] = value
            addjust_keys(value)
    elif isinstance(doc, list):
        for sub in doc:
            addjust_keys(sub)

def process_orig_line(text):
    new_text = ""
    i = 0
    while i < len(text):
        pos = text[i:].find("$(")
        if pos == -1:
            break
        pos += i
        pos2 = text[pos+2:].find(")") 
        if pos2 == -1:
            break
        new_text += text[i:pos]
        start = pos + 2
        end = start + pos2
        var_name = text[start:end]
        if var_name in os.environ:
            new_text += os.environ[var_name]
        i = end + 1
    new_text += text[i:]
    return new_text

def load_config():
    new_text = ""
    try:
        with open(config_filename, "r") as fp:
            for line in fp:
                new_text += process_orig_line(line)
            #print new_text
    except Exception as e:
        print_error("Cannot open configuration file:", e)

    try:
        doc = yaml.load(new_text)
    except Exception as e:
        print_error("Cannot open configuration file:", e)

    addjust_keys(doc)

    """ check the parameters in YAML file """
    if "name" not in doc:
        config_error("'name' is not specified")
    elif check_name_syntax(doc["name"]) is False:
        config_error("illegal syntax of 'name'")

    if "description" not in doc:
        config_error("'description' is not specified")

    if "architecture" not in doc:
        config_error("'architecture' is not specified")

    if "version" not in doc:
        config_error("'version' is not specified")
    check_version_syntax(doc["version"])

    if "part" not in doc or isinstance(doc["part"], dict) is False:
        config_error("'part' is not specified or specified in wrong syntax")

    if "depends" in doc and doc["depends"] is not None:
        if not is_list_of_string(doc["depends"]):
            config_error("'depends' must be a list of strings")
        doc["depends"] = ", ".join(doc["depends"])

    if "package" not in doc:
        doc["package"] = "debian"

    for name, part in doc["part"].iteritems():
        check_part_config(name, part)

    preserved = ["name", "version", "architecture", "description", "maintainer", "depends"]
    for p in preserved:
        if p not in doc or doc[p] is None:
            doc[p] = ""
    del doc["part"]
    return doc
