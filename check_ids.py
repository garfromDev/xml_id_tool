# -*- coding: utf8 -*-

import argparse
import csv
import json
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
#    parcourir les répertoires data/ et views/, dans l'ordre du manifeste créer les ids en notant le module
#    et le fichier
#    parcourir aussi .py, noter les reférence (module, nom complet fichier, id du record, n° ligne?,
#    texte de la référence, id cherché)
#    maj au fur et a mesure le namespace du module += id crées dans le module
#    vérifier présence des ref dans le namespace

#  quand tout les répertoires sont parcourus,
#    noter l'ordre des fichiers

#
# Struture :
#   ModuleNameTree contient la liste des ModuleInfo et fournit la fonction de scan de répertoire
#   ModuleInfo contient les info d'identification d'un module, et  une méthode de fabrication à partir d'un répertoire
#   ModuleTree contient le dictionnaire des module et la méthode récursive de vérification des modules (dépend de
#       ModuleNameTree
#
#  ErrorCollector gère la compilation et le stockage des erreurs rencontrées
debug = True
verbose = True


def log(msg):
    if verbose or debug:
        print msg


def detail(msg):
    if debug:
        print msg


def main(argv):
    global verbose
    global debug
    detail("starting... with argv %s" % argv)
    parser = argparse.ArgumentParser(
        description=u"Check xml ids validity in this directory")
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


def analyze(base_dir, dirctrs):
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
    detail(map(lambda kv: kv[0], info_tree.mod_name_path.iteritems()))
    error_collector = ErrorCollector()
    log("buiding module tree")
    mod = ModuleTree(
        error_collector=error_collector,
        depndcy_provider=info_tree)
    for name in info_tree.mod_name_path.keys():
        log("checking module %s" % name)
        mod.check(name)


def usage():
    print("\n USAGE\n -----")
    print("check_ids -b <directory of odoo base module> <directory to scan>")
    print("Option -f or --no-base allows to skip looking for base module")
    print("will check all xml ids declared in the directory ans sub-directories,"
          " taking into account manifest dependancies")
    print("reference to non existing ids will be signalled\n")


def read_directory(dir_to_read, odoo_module):
    """
    :param dir_to_read: list of directory to read
    :param odoo_module: module to which the directory belongs
    :return: list of unique ids, list of doublons
    """
    #  TODO : prendre les fichiers dans l'ordre du manifeste
    handler = IdHandler(ids=[], o_module=odoo_module)
    for dirt in dir_to_read:
        files = [f for f in os.listdir(dirt) if f.split('.')[-1] == 'xml']
        for f in files:
            with open(os.path.join(dirt, f), 'r') as fichier:
                xml.sax.parse(fichier, handler)
    return handler.xml_ids, handler.override


class ModuleNameTree(object):
    def __init__(self):
        self.mod_name_path = {}

    def scan_directory(self, directory):
        dirs = (x[0] for x in os.walk(directory)
                if module.module_manifest(x[0]))
        for d in dirs:
            detail(
                "scanning dir %s - %s - is manifest %s" %
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
        return self.mod_name_path[name] if name in self.mod_name_path.keys(
        ) else None


class ModuleInfo(object):
    """ Information about a module (in term of name, path and other module dependancy"""

    def __init__(self, name, path, depends_name=None,
                 data=None, code_files=None):
        """

        :param name: {string}
        :param path:
        :param depends_name: [{string}]
        """
        self.name = name
        self.path = path
        self.depends_name = depends_name or []
        self.data = data or []
        self.code_files = code_files or []

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

        for dirt, _, files in os.walk(directory):
            for f_name in files:
                if f_name.split(
                        '.')[-1] == 'py' and f_name not in MANIFEST_NAMES:
                    py_files.append(
                        os.path.join(
                            os.path.abspath(dirt),
                            f_name))
        mod_descrpt = ModuleInfo(
            name=name,
            path=directory,
            depends_name=mnfst_infos['depends'],
            data=mnfst_infos['data'],
            code_files=py_files
        )
        return mod_descrpt


class ErrorCollector(object):
    """ Simple class to handle error, may be subclassed to used logging system or user display """

    def __init__(self):
        self.errors = []

    def register(self, errors):
        self.errors.append(errors)

    def get(self):
        return self.errors


class ModuleTree(object):
    """ the tree of module object (as a dictionary), handle the checking of ref validity during tree parsing
    !!! TODO : ne pas checker base !!!!!
        this is the main class
    """

    def __init__(self, error_collector, depndcy_provider):
        """
        :param error_collector: an object allowing to register XmlError objects
        :param depndcy_provider: an object allowing to get module info and dependant module for a given module name
        """
        self.module_tree = {}  # a dictionary {name: Module, }
        self.error_collector = error_collector
        self.dpndcy_provider = depndcy_provider
        for mod_name, mod_info in depndcy_provider.mod_name_path.iteritems():
            # la creation d'un module entraine la creation des modeles dependants, donc
            # on vérifie l'existance avant de le créer
            if not self.module_tree.get(mod_name, None):
                self.module_tree[mod_name] = self.create_module(
                    name=mod_name, module_info=mod_info)

    def check(self, mod_name):
        """ check the id of a module, creating it if necessary"""
        # no need to check if the module has already been loaded and checked
        module_to_check = self.module_tree.get(mod_name, None)
        if not module_to_check:
            log("ERROR  module %s not found " % mod_name)
            return

        for fich in module_to_check.module_info.data:
            handler = CheckerHandler(
                ids=module_to_check.namespace,
                o_module=mod_name,
                locator=xml.sax.xmlreader.Locator())

            with open(os.path.join(module_to_check.module_info.path, fich), 'r') as data_fic:
                # splitext returns a tuple (path, ext)
                ext = os.path.splitext(fich)[1]
                log("parsing %s with extension %s" % (fich, ext))
                errors = []
                if ext == '.xml':
                    detail("parsing xml")
                    xml.sax.parse(data_fic, handler)
                    errors = handler.errors
                detail("found %s errors" % (len(errors)))
                self.error_collector.register(errors)

    def check_all(self):
        for mod in self.dpndcy_provider.mod_name_path.keys:
            self.check(mod)

    def create_module(self, name, module_info):
        detail("creating module %s" % name)
        new_module = Module(name, module_info)
        xml_ids = []
        for mod_name in module_info.depends_name:
            if not self.module_tree.get(mod_name, False):
                #  create dependant module if not already existing
                self.module_tree[mod_name] =\
                    self.create_module(
                    name=mod_name,
                    module_info=self.dpndcy_provider.get_module_info(mod_name))
            new_module.depends.append(self.module_tree[mod_name])
            #  namespace of the module is union of dependant module's namespace
            new_module.namespace += self.module_tree[mod_name].namespace
        # parse all files in /data and /views, enrich namespace and check Ids
        # along
        detail("actually feeding module %s" % name)
        for fich in module_info.data:
            handler = IdHandler(
                ids=new_module.namespace,
                o_module=name,
                locator=xml.sax.xmlreader.Locator())
            with open(os.path.join(module_info.path, fich), 'r') as data_fic:
                # pliext returns a tuple (path, ext)
                ext = os.path.splitext(fich)[1]
                log("parsing %s with extension %s" % (fich, ext))
                if ext == '.xml':
                    detail("parsing xml")
                    xml.sax.parse(data_fic, handler)
                    xml_ids = handler.xml_ids
                elif ext == '.csv':
                    detail('parsing csv')
                    csvparser = CsvParser(o_module=name, xml_ids=xml_ids)
                    xml_ids, error = csvparser.parse(data_fic)
                    if error:
                        log("error parsing %s : %s" %
                            (fich, map(lambda e: e.description(), error)))
                detail("found %s ids : %s..." % (len(xml_ids), xml_ids[:5]))
                new_module.namespace.append(xml_ids)
        return new_module


class Module(object):
    def __init__(self, name, module_info):
        self.name = name
        self.files = []
        self.depends = []  # a list of dependent Module
        self.module_info = module_info
        # a dictionary of
        self.namespace = []  # a list of XmlObject


class File(object):
    def __init__(self, odoo_module, loaded_after=None, loaded_before=None):
        self.loaded_after = loaded_after
        self.loaded_before = loaded_before
        self.module = odoo_module


class Manifest(object):
    def __init__(self, file_name):
        with open(file_name, 'r') as mnfst:
            content = json.load(mnfst)
            detail(
                "contenu du manifest %s :\n%s" %
                (file_name, content['depends']))


class XmlError(object):
    def __init__(self, record, ref, text, context, filename="", line=""):
        """
        :param record: the record's xml_id
        :param ref: the expression containing the error
        :param text: the error message
        :param context: the module's name
        :param filename:
        """
        self.record = record
        self.ref = ref
        self.text = text
        self.context = context
        self.filename = filename
        self.line = line
        detail("error %s " % self.description())

    def description(self):
        return "%s not found in record %s in module %s%s\nline %s expression %s" % (
            self.ref, self.record, self.context, "/" + self.filename if self.filename else "", self.line, self.text)


def _xml(o_module="", _id=""):
    """ return fully qualified xml_id """
    if len(_id.split('.')) < 2:
        _id = "%s.%s" % (o_module, _id)
    else:
        _id = _id
    return _id


class CsvParser(object):
    """
    Retrieve id definition is .csv file (column 'id')
    Does not care about reference to other id in other column
    """

    def __init__(self, o_module, xml_ids=None):
        """
        :param o_module: module name
        :param xml_ids: existing ids
        """
        self.xml_ids = xml_ids if xml_ids else []
        self.module = o_module

    def parse(self, csv_file):
        """
        parse the csv file with header, add the ids of the column 'id' to the xml_ids list
        if no header, add an error to error list
        :param csv_file: file object to parse
        :returns ([Xml_id aka string], [XmlError])
        """
        reader = csv.DictReader(csv_file)
        errors = []

        def has_header(extract):
            try:
                return csv.Sniffer().has_header(extract)
            except csv.Error:
                return extract[:4] == '"id"'

        if has_header(csv_file.read(1024)):
            csv_file.seek(0)
            for row in reader:
                if row.get('id', False):
                    self.xml_ids.append(_xml(o_module=self.module,
                                             _id=row['id']))
        else:
            errors.append(XmlError(record="", ref="", text="Csv file has no header", context=self.module,
                                   filename=csv_file.name))
        return self.xml_ids, errors


class IdHandler(object, xml.sax.ContentHandler):
    def __init__(self, o_module, ids=None, locator=None):
        """
        identify ids and add them to xml_ids
        :param o_module: string technical name of the module
        :param ids: [XMLObject]
        """
        super(IdHandler, self).__init__()
        self.xml_ids = ids or []  # a list of XmlObject
        self.override = []
        self.module = o_module
        self.record = None
        self.text = ""
        self.locator = locator

    def setDocumentLocator(self, locator):
        self.locator = locator

    def startDocument(self):
        pass

    def startElement(self, name, attrs):
        self.text = ""
        if name == 'record':
            xid = attrs.getValue('id') if 'id' in attrs.getQNames() else None
            if xid:
                self.record = _xml(o_module=self.module, _id=xid)
                if self.record in self.xml_ids:
                    self.override.append(self.record)
                else:
                    self.xml_ids.append(self.record)

    def endElement(self, name):
        if name == 'record':
            self.record = None

    def characters(self, content):
        self.text += content


class CheckerHandler(object, xml.sax.ContentHandler):
    def __init__(self, o_module, ids=None, locator=None):
        """
        check ref made to ids and reports errors if incorrect ref
        :param o_module: string technical name of the module
        :param ids: [XMLObject]
        """
        super(CheckerHandler, self).__init__()
        self.xml_ids = ids or []  # a list of XmlObject
        self.errors = []
        self.module = o_module
        self.record = None
        self.text = ""
        self.locator = locator

    def setDocumentLocator(self, locator):
        self.locator = locator

    def startDocument(self):
        pass

    def startElement(self, name, attrs):
        self.text = ""
        if name == 'record':
            xid = attrs.getValue('id') if 'id' in attrs.getQNames() else None
            if xid:
                self.record = _xml(o_module=self.module, _id=xid)

        if name == 'field':
            # traitement des champs ref="id"
            ref = attrs.getValue(
                'ref') if 'ref' in attrs.getQNames() else None
            if ref:
                link = _xml(_id=ref, o_module=self.module)
                if link not in self.xml_ids:
                    self.errors.append(XmlError(record=self.record,
                                                ref=ref, context=self.module,
                                                text='ref="' + str(ref) + '"',
                                                line=self.locator.getLineNumber(),
                                                filename=self.locator.getSystemId()))
            # traitement des expressions eval="[(4, ref('i
            evalstr = attrs.getValue(
                'eval') if 'eval' in attrs.getQNames() else None
            # we use ungreedy .*? to avoid closing parenthesis to be included
            # in match
            regexp = re.compile(r".*, ref\('(.*?)'\)", re.IGNORECASE)
            if evalstr:
                link = regexp.match(evalstr)
                link = link and link.groups()[0] or False
                if link and _xml(
                        _id=link, o_module=self.module) not in self.xml_ids:
                    self.errors.append(XmlError(record=self.record,
                                                ref=link, context=self.module,
                                                text="eval='ref(%s" % link + "')",
                                                line=self.locator.getLineNumber(),
                                                filename=self.locator.getSystemId()
                                                )
                                       )

    def endElement(self, name):
        if name == 'record':
            self.record = None

    def characters(self, content):
        self.text += content


if __name__ == '__main__':
    main(sys.argv[1:])
    # main(['-d',  '-v' ,'-f',  '.'])
