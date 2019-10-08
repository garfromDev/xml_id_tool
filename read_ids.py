#!/usr/bin/env python
import os as os
import sys
import xml.sax


def main():
    if len(sys.argv) <= 1:
        print("usage :\n  xmlid_tool.py directory   to list all ids in the directory\n"
              "  xmlid_tool.py old_directory [new_directory] to compare ids in both directory")
        return
    dir1 = sys.argv[1]
    if len(sys.argv) > 2:
        dir2 = sys.argv[2]
        solo_ids, missing_ids = compare([dir1], [dir2])
        if len(missing_ids) > 0:
            print("%s ids are either created or missing" % len(solo_ids))
            print("%s ids missing in new data" % len(missing_ids))
            for id in missing_ids:
                print(id)
        else:
            print("no missing ids")
            print("%s created " % len(solo_ids))
    else:
        xml_ids, doublons = read_directory([dir1])
        for id in xml_ids:
            print(id)

def compare(dir1, dir2):
    ids1, doubl1 = read_directory(dir1)
    ids2, doubl2 = read_directory(dir2)
    s1, s2 = set(ids1), set(ids2)
    return s1 ^ s2, s1 - s2  # ids exists only in one of the 2 sets, missing id in set2 compare to set 1

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
