# -*- coding: utf8 -*-

import csv
import json
import os as os
import re
import xml.sax
import module as module
from module import MANIFEST_NAMES

debug = True
verbose = True


def log(msg):
    if verbose or debug:
        print msg


def detail(msg):
    if debug:
        print msg


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
