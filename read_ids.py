import os as os
import xml.sax


def main():
    print("starting...")

    xml_ids, doublons = read_directory(['data/'])
    print("%s xml id found with %s doublons" % (len(xml_ids), len(doublons)))
    for id in doublons:
        print(id)

def compare(dir1, dir2):
    ids1, doubl1 = read_directory(dir1)
    ids2, doubl2 = read_directory(dir2)
    return set(ids2) ^ set(ids1)  # ids exists only in one of the 2 sets

def read_directory(dir_to_read):
    """
    :param dir_to_read: list of directory to read
    :return: list of unique ids, list of doublons
    """
    handler = IdHandler([])
    for dir in dir_to_read:
        files = [f for f in os.listdir(dir) if f.split('.')[-1] == 'xml']
        for f in files:
            with open(os.path.join(dir , f), 'r') as fichier:
                xml.sax.parse(fichier, handler)
    return handler.xml_ids, handler.doublons


class IdHandler(xml.sax.ContentHandler):
    def __init__(self, ids=[]):
        self.xml_ids = ids
        self.doublons = []

    def startDocument(self):
        pass

    def startElement(self, name, attrs):
        if name != 'record':
            return

        id = attrs.getValue('id')
        if id in self.xml_ids:
            self.doublons.append(id)
        else:
            self.xml_ids.append(id)

    def endElement(self, name):
        pass

    def characters(self, content):
        pass

if __name__ == '__main__':
    main()