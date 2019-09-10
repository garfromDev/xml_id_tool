import os as os
import xml.sax


def main():
    print("starting...")

    xml_ids, doublons = read_directory(['data/'], module="")
    print("%s xml id found with %s doublons" % (len(xml_ids), len(doublons)))
    for id in doublons:
        print(id)



def read_directory(dir_to_read, module):
    """
    :param dir_to_read: list of directory to read
    :return: list of unique ids, list of doublons
    """
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
            self.id = module + id  # a string, including or not module prefix
        else:
            self.id = id
        self.module = module

class XmlError(object):
    def __init__(self, record, ref, text ):
        self.record = record
        self.ref = ref
        self.text = text


class IdHandler(xml.sax.ContentHandler):
    def __init__(self, module, ids=[]):
        super(IdHandler, self).__init__(self)
        self.xml_ids = ids
        self.override = []
        self.errors = []
        self.module = module
        self.record = None


    def startDocument(self):
        pass

    def startElement(self, name, attrs):
        if name == 'record':
            id = attrs.getValue('id')
            self.record = id
            if id in [xml_id.id for xml_id in self.xml_ids]:
                self.override.append(XmlObject(module=self.module, id=id))
            else:
                self.xml_ids.append(XmlObject(module=self.module, id=id))

        if name == 'field':
            ref = attrs.getValue('ref')
            if ref not in [xml_id.id for xml_id in self.xml_ids]:
                self.errors.append(XmlError(record=XmlObject(module=self.module, id=id)),
                                   ref=ref,
                                   text=self.property_xml_string)


    def endElement(self, name):
        pass

    def characters(self, content):
        pass

if __name__ == '__main__':
    main()