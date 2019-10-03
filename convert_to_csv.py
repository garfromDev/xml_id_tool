# -*- coding: utf8 -*-
from __future__ import unicode_literals

import io
import sys
import os.path
import xml.sax

field_map = [
    ('name', None),
    ('loc_barcode', None),
    ('location_id', None),
    ('removal_strategy_id', u""),
    ('active', u"True"),
    ('scrap_location', u"False"),
    ('company_id', u""),
    ('usage', u"internal"),
    ('orderpoint_visible', u"False"),
]


class Field(object):
    def __init__(self, name=u""):
        self.name = name
        self.value = u""


class IdHandler(xml.sax.ContentHandler):

    def __init__(self, csv_file, field_map):
        self.csv_file = csv_file
        self.field_map = field_map
        self.field = None
        self.fields = {}
        self.recording = False

    def startDocument(self):
        self.csv_file.write(u"id," + u",".join([l.replace('_id', '_id:id') for l, v in field_map]) + u"\n")

    def startElement(self, name, attrs):
        if name == 'record':
            self.recording = True
            self.id = str(attrs.getValue('id'))
        if name == 'field' and self.recording:
            self.field = Field(name=attrs.getValue('name'))
            print("beginning field %s" % self.field.name)

    def endElement(self, name):
        if name == 'field' and self.recording:
            self.fields[self.field.name] = self.field.value
        if name == 'record':
            result = [self.id] + [self.fields.get(k, v) for k, v in self.field_map]
            self.csv_file.write((u",".join(result) + u"\n").decode('utf-8'))

    def characters(self, content):
        if self.field:
            self.field.value += content.decode('utf-8')


def main():

    fichier = io.open("sirail_locations.xml", 'r', encoding='utf-8')
    csv_file = io.open("test.csv", 'w', encoding='utf-8')
    handler = IdHandler(csv_file=csv_file, field_map=field_map)
    inp_src = xml.sax.InputSource()
    inp_src.setEncoding('utf-8')
    inp_src.setByteStream(fichier)
    parser = xml.sax.make_parser()
    parser.setContentHandler(handler)
    try:
        parser.parse(inp_src)
    finally:
        fichier.close()
        csv_file.close()

if __name__ == "__main__":
    reload(sys)
    sys.setdefaultencoding('utf-8')
    main()
