#!/usr/bin/env python

"""
General purpose XML parsing driver for use as a content handler through
Python's xml.sax module.  Works in conjunction with lib/xml_util.py, which
provides useful helper methods to handle the parsed data.
"""

import functools
from collections import deque
from xml.sax import make_parser, handler
import xml_util

class ChainList(list):
    """
    This is the base structure that handles the tree created by XMLElement
    and XMLHandler. Overriding __getattr__ allows us to chain queries on
    a list in order to traverse the tree.
    """

    def contents_of(self, tag, default=[''], as_string=False, upper=True):
        res = []
        for item in self:
            res.extend(item.contents_of(tag, upper=upper))
        if as_string:
            res = [r for r in res if type(r).__name__ not in ('tuple', 'list')]
            return ' '.join(res) if res else ''
        return ChainList(res) if res else default

    def __getattr__(self, key):
        res = []
        scope = deque(self)
        while scope:
            current = scope.popleft()
            if current._name == key: res.append(current)
            else: scope.extend(current.children)
        return ChainList(res)

    def __reduce__(self): return (ChainList, (), None, iter(self), None)
    def __getstate__(self): return None

class XMLElement(object):
    """
    Represents XML elements from a document. These will assist
    us in representing an XML document as a Python object.
    Heavily inspired from: https://github.com/stchris/untangle/blob/master/untangle.py
    """

    def __init__(self, name, attributes):
        self._name = name
        self._attributes = attributes
        self.content = []
        self.children = ChainList()
        self.is_root = False

    def __getstate__(self):
        return self.__dict__

    def __iter__(self):
        yield self

    def __nonzero__(self):
        return self.is_root or self._name is not None

    def __getitem__(self, key):
        return self.get_attribute(key)

    def __getattr__(self, key):
        res = []
        scope = deque(self.children)
        while scope:
            current = scope.popleft()
            if current._name == key: res.append(current)
            else: scope.extend(current.children)
        if res:
            self.__dict__[key] = ChainList(res)
            return ChainList(res)
        else:
            return ChainList('')

    def contents_of(self, key, default=ChainList(''), as_string=False, upper=True):
        candidates = self.__getattr__(key)
        if candidates:
            res = [x.get_content(upper=upper) for x in candidates]
        else:
            res = default
        if as_string:
            if not res:
                return ''
            # handle corner case of [['content', 'here']]
            elif isinstance(res, list)\
                 and len(res) == 1\
                 and isinstance(res[0], list):
                res = res[0]
            return ' '.join(filter(lambda x: x, filter(lambda x: not isinstance(x, list), res)))
        return res

    def get_content(self, upper=True):
        if len(self.content) == 1:
            return xml_util.clean(self.content[0], upper=upper)
        else:
            return map(functools.partial(xml_util.clean, upper=upper), self.content)

    def put_content(self, content, lastlinenumber, linenumber):
        if not self.content or lastlinenumber != linenumber:
            self.content.append(content)
        else:
            self.content[-1] += content

    def add_child(self, child):
        self.children.append(child)

    def get_attribute(self, key, upper=True):
        return xml_util.clean(self._attributes.get(key, None), upper=upper)

    def get_xmlelements(self, name):
        return filter(lambda x: x._name == name, self.children) \
               if name else \
               self.children


class XMLHandler(handler.ContentHandler):
    """
    SAX Handler to create the Python object while parsing
    """

    def __init__(self):
        self.root = XMLElement(None, None)
        self.root.is_root = True
        self.elements = ChainList()
        handler.ContentHandler.__init__(self)
        self.lastline = -1

    def startElement(self, name, attributes):
        name = name.replace('-','_').replace('.','_').replace(':','_')
        xmlelem = XMLElement(name, dict(attributes.items()))
        if self.elements:
            self.elements[-1].add_child(xmlelem)
        else:
            self.root.add_child(xmlelem)
        self.elements.append(xmlelem)

    def endElement(self, name):
        if self.elements:
            self.elements.pop()

    def characters(self, content):
        currentlinenumber = self._locator.getLineNumber()
        if content.strip():
          if self.elements[-1]._name in ('b','i'):
            self.elements[-2].put_content(content, self.lastline, currentlinenumber)
          elif self.elements[-1]._name == 'sub':
            newtxt = u"<sub>"+content+u"</sub>"
            self.elements[-2].put_content(newtxt, self.lastline, currentlinenumber)
          else:
            self.elements[-1].put_content(content, self.lastline, currentlinenumber)
        self.lastline = self._locator.getLineNumber()
