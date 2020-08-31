# -*- coding: utf8 -*-

import argparse
import sys

from module_graph import ModuleNameTree, ErrorCollector, ModuleTree, detail, log


def main(argv):
    global verbose
    global debug
    detail("starting  with argv %s" % argv)
    parser = argparse.ArgumentParser(
        description=u"Build dependency graph of modules in this directory")
    parser.add_argument(
        "directories",
        nargs='+',
        help=u"Directories to parse recursively")
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "-b",
        "--base",
        help="Base directory of odoo, to include in ids")
    group.add_argument(
        "-f",
        "--nobase",
        help=u"No base directory",
        action="store_true")
    parser.add_argument("-d", "--debug", action="store_true")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()
    verbose = args.verbose
    debug = args.debug
    analyze(args.base, args.directories)


def buil_tree(base_dir, dirctrs):
    info_tree = ModuleNameTree()
    nb = 0
    if base_dir:
        log("scanning odoo base")
        nb = len(info_tree.scan_directory(base_dir))
        log("%s modules found" % nb)
    for dirctr in dirctrs:
        log("scanning %s" % dirctr)
        info_tree.scan_directory(dirctr)
    log("%s modules found" % (len(info_tree.mod_name_path) - nb))
    return info_tree

