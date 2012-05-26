#!/usr/bin/env python

import unittest
import sys
import imp
import os
import datetime
import re
import logging
from xml.dom.minidom import parse, parseString
from xml_patent import XMLPatent
from optparse import OptionParser

# Test Files

xml_file1 = 'unittest/ipg120327.one.xml' #want to open with 'U' for unix line endings
xml_file2 = 'unittest/test2.xml'
xml_file3 = 'unittest/test3.xml'

# Data structures/variables used in testing

debug = False
xml_files = []
parsed_xml = []


"""

 Fields useful for legacy code testing: self.country, self.patent, self.kind, self.date_grant
 self.pat_type, self.date_app, self.country_app, self.patent_app (each patent should have these)

 self.code_app, self.clm_num, self.classes <-- can't easily test these, vary differently across all general patents, still thinking of a solution
 
"""

class TestXMLPatent(unittest.TestCase):

    def setUp(self):
        xml_files.append(xml_file1)     # Want to append all files to test, manually doing it for now, will change later 
        xml_files.append(xml_file2)
        xml_files.append(xml_file3)
        self.assertTrue(xml_files)      # Make sure you aren't testing nothing
        
    def test_patent_construction(self): # High-level test, testing legacy code construction
        for xml in xml_files:
            xml_patent = XMLPatent(open(xml, 'U'))
            parsed_xml.append((xml, xml_patent))# Storing tuple (original XML, parsed XML) for later, finer block testing
            #print xml_patent.invention_title

    def test_patent_fields(self): # Medium-level test, testing fields of the parsed XML
        for xml_tuple in parsed_xml: 
            parsed_fields = xml_tuple[1]                                                             # Note that str.isalum()/isdigit() intrinsically check for non-emptyness
            self.assertTrue(parsed_fields.pat_type.isalnum())                                        # Testing legitimate patent type, e.g. design, scientific, etc... is alphanumeric
            self.assertTrue(parsed_fields.patent.isalnum())                                          # Testing patent , e.g. D0656296
            self.assertTrue(parsed_fields.date_grant.isdigit() and len(parsed_fields.date_app) is 8) # Testing date/format of grant, e.g. 20123456
            self.assertTrue(parsed_fields.date_app.isdigit() and len(parsed_fields.date_grant) is 8) # Testing date/format of grant application date, e.g. 20124567
            self.assertTrue(parsed_fields.country.isalnum())                                         # Similar testing for the following....
            self.assertTrue(parsed_fields.country_app.isalnum())
            self.assertTrue(parsed_fields.kind.isalnum())

    def test_patent_validity(self): # Low-level test, testing presence of fields in original XML, thinking of compiling regex's but no point as each pattern only used once.
        for xml_tuple in parsed_xml:
            original_xml_string = open(xml_tuple[0]).read()
            parsed_fields = xml_tuple[1]
            country_match = re.search(r"[<]country[>]"+parsed_fields.country+"[<][/]country[>]", original_xml_string, re.I + re.S + re.X)
            self.assertTrue(country_match)
            kind_match = re.search(r"[<]kind[>]"+parsed_fields.kind+"[<][/]kind[>]", original_xml_string, re.I + re.S + re.X)
            self.assertTrue(kind_match)
            #print "[>]"+parsed_fields.invention_title+"[<][/]invention-title[>]"
            #invention_title_match = re.search("[>]"+parsed_fields.invention_title+"[<][/]invention-title[>]", original_xml_string, re.I + re.S + re.X)
            #self.assertTrue(invention_title_match) #still working on this one, may have annoying \n, whitespace in middle, need to use rstrip, lstrip

if __name__ == '__main__':
    
    parser = OptionParser()
    parser.add_option("-d", "--debugging", dest="debugging", action="store_true")                
    (options, args) = parser.parse_args()

    """
        Complications passing in command-line arguments along with unit-testing, 
        Need to delete sys.argv from index one onewards or else flag keeps getting interpreted, solution found 
        http://stackoverflow.com/questions/1029891/python-unittest-is-there-a-way-to-pass-command-line-options-to-the-app

    """
    
    if options.debugging:
        debug = True
    del sys.argv[1:]    
    
    unittest.main()




    
    
