# -*- coding: utf8 -*-

import functools
import getopt
import json
import operator
import os as os
import re
import xml.sax
import sys
import module as module
from module import MANIFEST_NAMES

#  recuperer les id des data et les id des view, commencer par data
# récupérer les ids des .CSV, 1ere colonne = id, prendre avant la virgule
#  record -> récupérer id et module, en utilisant les ids de type module.id
#  a checker :
#  les fields ref="id"
#  les fields eval="[(4, ref('id
#  dans les .py
#  .browse_ref("id")
#  .ref("id")
#
#  à chaque fois, construire la référence préfixée et vérifier qu'elle est dans la liste
#
#  un dictionnaire d'id préfixés avec lien vers objets ID
#  un dictionnaire de modules avec lien vers objet module

#  parcourir les répertoires
#  si répertoire contient un manifest, c'est un module
#    charger le manifest, noter les dépendances (en chaine provisoirement)
#    noter le module, son chemin, ses dépendances, ses fichiers
#  sinon parcourir sous-répertoires
#

#  creation des objets modules :
#  pour chaque module :
#    pour chaque module dépendants
#       créer le module si pas existant
#       lier le module
#    initialiser le namespace = namespace des modules dépendants
#    parcourir les répertoires data/ et views/, dans l'ordre du manifestecréer les ids en notant le module et le fichier
#    parcourir aussi .py, noter les reférence (module, nom complet fichier, id du record, n° ligne?, texte de la référence, id cherché)
#    maj au fur et a mesure le namespace du module += id crées dans le module
#    vérifier présence des ref dans le namespace

#  quand tout les répertoires sont parcourus,
#    noter l'ordre des fichiers

#

ODOO_BASE = '/Users/alistef/PycharmProjects/odoo'


def main(argv):
    print("starting...")

    try:
        opts, args = getopt.getopt(
            argv, "hfb:", [
                "help", "no-base", "base-directory="])
    except getopt.GetoptError:
        usage()
    base_dir = ODOO_BASE
    for o, a in opts:
        if o in ('-b', '--base-directory'):
            base_dir = a
        if o in ('-h', '--help') or not args:
            usage()
            return
        if o in ('-f', '--no-base'):
            base_dir = None
    analyze(base_dir, args[0])


def analyze(base_dir, dir):
    info_tree = ModuleNameTree()
    if base_dir:
        print("scanning odoo base")
        nb = len(info_tree.scan_directory(base_dir))
        print("%s modules found" % nb)
    print("scanning %s" % dir)
    info_tree.scan_directory(dir)
    print("%s modules found" % (len(info_tree.mod_infos) - nb))

    print(map(lambda kv: kv[0], info_tree.mod_name_path.iteritems()))
    error_collector =ErrorCollector()
    module = ModuleTree(
        error_collector=error_collector,
        depndcy_provider=info_tree)
    for name in info_tree.mod_name_path.keys():
        module.check(name)

    return
    # a = Manifest(file_name='__openerp__.py')
    # print(module.module_manifest('./test_module'))
    # info = module.load_information_from_description_file('test_module', './test_module')
    # print(info['depends'])
    return
    xml_ids, xml_override, errors = read_directory(
        ['.'], module="sirail_config")
    print("%s xml id found with %s errors" % (len(xml_ids), len(errors)))
    for error in errors:
        print(error.description() + "\n")


def usage():
    print("\n USAGE\n -----")
    print("check_ids -b <directory of odoo base module> <directory to scan>")
    print("Option -f or --no-base allows to skip looking for base module")
    print("will check all xml ids declared in the directory ans sub-directories,"
          " taking into account manifest dependancies")
    print("reference to non existing ids will be signalled\n")


def load_modules():
    # charger base
    pass


def read_directory(dir_to_read, module):
    """
    :param dir_to_read: list of directory to read
    :module: module to which the directory belongs
    :return: list of unique ids, list of doublons
    """
    #  TODO : prendre les fichiers dans l'ordre du manifeste
    handler = IdHandler(ids=[], module=module)
    for dir in dir_to_read:
        files = [f for f in os.listdir(dir) if f.split('.')[-1] == 'xml']
        for f in files:
            with open(os.path.join(dir, f), 'r') as fichier:
                xml.sax.parse(fichier, handler)
    return handler.xml_ids, handler.override, handler.errors


class ModuleNameTree(object):
    def __init__(self):
        """

        :param mod_infos: [ModuleInfo]
        """
        self.mod_name_path = {}

    def scan_directory(self, directory):
        dirs = (x[0] for x in os.walk(directory)
                if module.module_manifest(x[0]))
        for d in dirs:
            print(
                "dir %s - %s - is manifest %s" %
                (d,
                 os.path.basename(
                     os.path.abspath(d)),
                    module.module_manifest(d)))
            self.mod_name_path[os.path.basename(os.path.abspath(
                d))] = ModuleInfo.create_from_dir(os.path.abspath(d))

        return self.mod_name_path

    def get_dependent_module(self, name):
        return self.mod_name_path[name].depends_name if name in self.mod_name_path.keys else None

    def get_module_info(self, name):
        return self.mod_name_path[name] if name in self.mod_name_path.keys else None


class ModuleInfo(object):
    def __init__(self, name, path, depends_name=[], data=[], code_files=[]):
        """

        :param name: {string}
        :param path:
        :param depends_name: [{string}]
        """
        self.name = name
        self.path = path
        self.depends_name = depends_name
        self.data = data
        self.code_files = code_files

    @classmethod
    def create_from_dir(cls, directory):
        """
        create a ModuleInfo object from value in current directory
        :param directory: {string} the complete path to the directory
        :return: ModuleInfo object, or None if unable to create
        """
        mnfst = module.module_manifest(directory)
        if not mnfst:
            return None
        mnfst_infos = module.load_information_from_description_file(directory)
        #  name of the module is the name of the directory
        name = os.path.basename(os.path.normpath(directory))
        py_files = []

        for dir, _, files in os.walk(directory):
            for f_name in files:
                if f_name.split(
                        '.')[-1] == 'py' and f_name not in MANIFEST_NAMES:
                    py_files.append(os.path.join(os.path.abspath(dir), f_name))
        mod_descrpt = ModuleInfo(
            name=name,
            path=directory,
            depends_name=mnfst_infos['depends'],
            data=mnfst_infos['data'],
            code_files=py_files
        )
        return mod_descrpt


class ErrorCollector(object):
    def __init__(self):
        self.errors = []

    def register(self, errors):
        self.errors.append(errors)

    def get(self):
        return self.errors


class ModuleTree(object):
    def __init__(self, error_collector, depndcy_provider):
        """
        Configure the Module class for use by Module instance
        :param error_collector: an object allowing to register XmlError objects
        :param depndcy_provider: an object allowing to get module info and dependant module for a given module name
        """
        self.module_tree = {}
        self.error_collector = error_collector
        self.dpndcy_provider = depndcy_provider

    def check(self, mod_name):
        # no need to check if the module has already been loaded and checked
        if not self.module_tree.get(mod_name, False):
            Module.module_tree = self.module_tree
            # the initialization of the Module will trigger the checking
            self.module_tree[mod_name] = Module(name=mod_name,
                                                module_info=self.dpndcy_provider.get_module_info(mod_name))

    def check_all(self):
        for mod in self.dpndcy_provider.mod_name_path.keys:
            self.check(mod)


class Module(object):
    def __init__(self, name, module_info):
        self.name = name
        self.files = []
        self.depends = []
        self.module_info = module_info
        self.namespace = {}

        for mod_name in module_info.depends_name:
            if not Module.module_tree.get(mod_name, False):
                #  create dependant module if not already existing
                Module.module_tree[mod_name] = Module(name=mod_name,
                                                      module_info=Module.depndcy_provider.get_module_info(mod_name))
            self.depends.append(Module.module_tree[mod_name])
            #  namespace of the module is union of dependant module's namespace
            self.namespace.update(Module.module_tree[mod_name].namespace)
        # parse all files in /data and /views, enrich namspace and check Ids
        # along
        for fich in module_info.data:
            handler = IdHandler(ids=self.namespace, module=name)
            with open(os.path.join(module_info.path, fich), 'r') as data_fic:
                xml.sax.parse(data_fic, handler)
                self.namespace = handler.xml_ids
                Module.error_collector.register(handler.errors)


class File(object):
    def __init__(self, module, loaded_after=None, loaded_before=None):
        self.loaded_after = loaded_after
        self.loaded_before = loaded_before
        self.module = module


class Manifest(object):
    def __init__(self, file_name):
        with open(file_name, 'r') as mnfst:
            content = json.load(mnfst)
            print content['depends']


class XmlObject(object):
    """
    object containg information about
    """

    def __init__(self, module="", id=""):
        if len(id.split('.')) < 2:
            self.raw_id = id
            # a string, including or not module prefix
            self.id = "%s.%s" % (module, id)
        else:
            self.id = id
            self.raw_id = id.split('.')[-1]
        self.module = module


class XmlError(object):
    def __init__(self, record, ref, text):
        self.record = record
        self.ref = ref
        self.text = text

    def description(self):
        return "%s not found in object %s \n expression %s" % (
            self.ref, self.record.id, self.text)


class IdHandler(xml.sax.ContentHandler):
    def __init__(self, module, ids=[]):
        """
        identify ids and add them to xml_ids
        check ref made to ids and reports errors if incorrect ref
        :param module: string technical name of the module
        :param ids: [XMLObject]
        """
        self.xml_ids = ids
        self.override = []
        self.errors = []
        self.module = module
        self.record = None
        self.text = ""

    def startDocument(self):
        pass

    def startElement(self, name, attrs):
        self.text = ""
        if name == 'record':
            id = attrs.getValue('id') if 'id' in attrs.getQNames() else False
            if id:
                self.record = XmlObject(module=self.module, id=id)
                if id in [xml_id.id for xml_id in self.xml_ids]:
                    self.override.append(XmlObject(module=self.module, id=id))
                else:
                    self.xml_ids.append(XmlObject(module=self.module, id=id))

        if name == 'field':
            # traitement des champs ref="id"
            ref = attrs.getValue(
                'ref') if 'ref' in attrs.getQNames() else False
            if ref:
                link = XmlObject(id=ref, module=self.module)
                if link not in self.xml_ids:
                    self.errors.append(XmlError(record=self.record,
                                                ref=ref,
                                                text='ref="' + ref + '"'))
            # traitement des expressions eval="[(4, ref('i
            evalstr = attrs.getValue(
                'eval') if 'eval' in attrs.getQNames() else False
            regexp = re.compile(r".*, ref\((.*)\)", re.IGNORECASE)
            if evalstr:
                link = regexp.match(evalstr)
                if link and XmlObject(
                        id=link, module=self.module) not in self.xml_ids:
                    self.errors.append(XmlError(record=self.record,
                                                ref=link,
                                                text="eval='ref(" + link + "')"))

    def endElement(self, name):
        if name == 'record':
            self.record = None

    def characters(self, content):
        self.text += content


if __name__ == '__main__':
    main(sys.argv[1:])
