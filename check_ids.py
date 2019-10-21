# -*- coding: utf8 -*-

import os as os
import re
import xml.sax

#  recuperer les id des data et les id des view, commencer par data
#  record -> récupérer id et module, en utilisant les ids de type module.id
#  a checker :
#  les fields ref="id"
#  les fields eval="[(4, ref('id
#  dans les .py
#  .browse_ref("id")
#  .ref("id")
#
#  à chaque fois, construire la référence préfixée et vérifier qu'elle est dans la liste


def main():
    print("starting...")
    xml_ids, xml_override, errors = read_directory(['.'], module="sirail_config")
    print("%s xml id found with %s errors" % (len(xml_ids), len(errors)))
    for error in errors:
        print(error.description() + "\n")


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


class XmlObject(object):
    """
    object containg information about
    """

    def __init__(self, module="", id=""):
        if len(id.split('.')) < 2:
            self.raw_id = id
            self.id = "%s.%s" % (module, id)  # a string, including or not module prefix
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
    main()
