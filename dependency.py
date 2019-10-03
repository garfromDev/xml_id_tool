# -*- coding: utf8 -*-

# (module, [modules...])
# un module se positionne au dessous de tous les modules dont il dépend

import re


class ModuleFile(object):
    def __init__(self, name, dependencies, fileName = ""):
        self.name = name
        self.dependancies = dependencies
        self.fileName = fileName


class DependencyGraph(object):
    def __init__(self):
        self.graph = []

    def insert(self, newModule):
        pos = 0
        for mod in newModule.dependencies:
            pos = max(pos, self.graph.index(mod))

        self.graph.insert(pos + 1, newModule)

    def get_uml(self):
        pass

class Extracter(object):
    def __init__(self):
        self.graph = DependencyGraph()

    def get_graph(self, directory):
        files = [f for f in os.listdir(dir) if f == '__openerp__.py']
        for file in files:
            self.graph.insert(get_module(file))
        return self.graph

    def get_module(self, file):
        regex = re.compile(r"\'depends\': \[(.+)\]")
        with  open(file, 'r') as fichier:
            dependencies = regexp.findall(fichier.readlines())
        return ModuleFile(name=file, dependencies=)

