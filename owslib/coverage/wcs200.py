# -*- coding: ISO-8859-15 -*-
# =============================================================================
# Copyright (c) 2004, 2006 Sean C. Gillies
# Copyright (c) 2007 STFC <http://www.stfc.ac.uk>
#
# Authors : 
#          Dominic Lowe <d.lowe@rl.ac.uk>
#
# Contact email: d.lowe@rl.ac.uk
# =============================================================================

##########NOTE: Does not conform to new interfaces yet #################

from __future__ import (absolute_import, division, print_function)

import warnings

from owslib.coverage.wcsBase import WCSBase, WCSCapabilitiesReader, ServiceException
from owslib.util import openURL, testXMLValue
from urllib import urlencode

from owslib.etree import etree
import os
from owslib.coverage import gml

import lxml.etree as etree

import logging
from owslib.util import log

#class local_log(object):
#    def debug(self, string):
#        print('DEBUG: ', string)
##        if not string.startswith('WCS'):
##            raise Exception()
#
#log = local_log()

def ns(tag):
    return '{http://www.opengis.net/wcs/2.0}'+tag

from owslib.namespaces import Namespaces
from owslib.util import nspath_eval

# Define useful namespace lookup dictionaries.
WCS_names = Namespaces().get_namespaces(['wcs', 'wcs20', 'ows', 'ows200'])
WCS_names['wcs20ows'] = WCS_names['wcs20'] + '/ows'

VERSION = '2.0.0'


def find_element(document, name, namespaces):
    """
    Find an element in a document with multiple aliases for its namespace.

    Args:

    * document (etree):
        An xml fragment.
    * name (string):
        A tagname to search for.
    * namespaces (string or list of string):
        A set of namespace aliasses.

    Return the first match using any of the given namespaces in WCS_names.

    For example:

        find_element(capabilities, 'ServiceIdentification',
                     ['ows200', 'wcs20ows'])

        This will match either:
        * 'http://www.opengis.net/ows/2.0:ServiceIdentification'
            (aka 'ows200:ServiceIdentification'), *or*
        *  'http://www.opengis.net/wcs/2.0/ows:ServiceIdentification'
            (aka 'wcs20ows:ServiceIdentification').

    """
    if isinstance(namespaces, basestring):
        namespaces = [namespaces]
    for ns in namespaces:
        elem = document.find('{}:{}'.format(ns, name), namespaces=WCS_names)
        if elem is not None:
            return elem
    raise ValueError('Element {} not found.'.format(name))


class CoverageSummary(object):
    def __init__(self, service, coverage_id, subtype=None):
        self.service = service
        self.coverage_id = coverage_id
        self.subtype = subtype

    @classmethod
    def from_xml(cls, element, service):
        keywords = {'coverage_id': '{{{wcs20}}}CoverageId'.format(**WCS_names),
                    'subtype': '{{{wcs20}}}CoverageSubtype'.format(**WCS_names)}
        element_mapping = {identifier: keyword_name
                           for keyword_name, identifier in keywords.items()}
        keywords['service'] = service
        for child in element:
            if child.tag in element_mapping:
                keywords[element_mapping[child.tag]] = child.text
            else:
                log.debug('Coverage tag {} not supported.'.format(child.tag))
        return cls(**keywords)
    
    def describe(self):
        """
        Request describeCoverage for this coverage.

        """
        service = self.service
        coverage_operation = self.service._find_operation('DescribeCoverage')
        base_url = coverage_operation.href_via('HTTP', 'Get')

        #process kwargs
        request = {'version': service.version,
                   'request': 'DescribeCoverage',
                   'service':'WCS',
                   'CoverageId': self.coverage_id}
        #encode and request
        data = urlencode(request)

        return openURL(base_url, data, 'Get', service.cookies)


class WebCoverageService_2_0_0(WCSBase):
    """Abstraction for OGC Web Coverage Service (WCS), version 2.0.0
    Implements IWebCoverageService.

    """
    # Define which concepts will be recognised within the Extension block of a
    # capabilities response.
    # This is a dictionary {<xml-tag>: <object-builder-class>}
    recognised_capability_extensions = {}

    def __getitem__(self, name):
        ''' check contents dictionary to allow dict like access to service layers'''
        if name in self.__getattribute__('contents').keys():
            return self.__getattribute__('contents')[name]
        else:
            raise KeyError("No content named %s" % name)

    def __new__(cls, url, xml=None, cookies=None):
        if cookies is not None:
            raise ValueError('WCS2 does not support cookies')
        return WCSBase.__new__(cls, url, xml, None)

    def __init__(self, url, xml=None, _=None):
        self.version = VERSION
        self.url = url

        def absent(name):
            log.debug('WCS 2.0.0 DEBUG: '
                      'capabilities contains no {} component.'.format(name))

        reader = WCSCapabilitiesReader(self.version)
        if xml:
            self._capabilities = reader.readString(xml)
        else:
            self._capabilities = reader.read(self.url)

        # check for exceptions
        se = self._capabilities.find('wcs20:Exception', namespaces=WCS_names)
        if se is not None:
            err_message = str(se.text).strip()
            raise ServiceException(err_message, xml)

        # build metadata objects:

        # serviceIdentification metadata : may be absent
        identification = ServiceIdentification._find(self._capabilities)
        if identification is None:
            self.identification = None
            absent('ServiceIdentification')
        else:
            self.identification = ServiceIdentification(identification)

        # serviceProvider : may be absent.
        provider = ServiceProvider._find(self._capabilities)
        if provider is None:
            self.provider = None
            absent('ServiceProvider')
        else:
            self.provider = ServiceProvider(provider)

        # serviceOperations : may be absent, else contains a list of Operation.
        operations = Operation._find(self._capabilities)
        if operations is None:
            self.operations = []
            absent('OperationsMetadata')
        else:
            self.operations = [Operation(operation)
                               for operation in operations]

        # contents : may be absent
        contents = self._capabilities.find('wcs20:Contents', namespaces=WCS_names)
        self.contents = {}
        self.contents_extensions = []
        if contents is None:
            absent('Contents')
        else:
            for coverage in contents.findall('wcs20:CoverageSummary', namespaces=WCS_names):
                coverage = CoverageSummary.from_xml(coverage, self)
                self.contents[coverage.coverage_id] = coverage

            # any extensions
            for content_extensions in contents.findall('wcs20:Extension', namespaces=WCS_names):
                for extension in content_extensions:
                    recognised_types = WebCoverageService_2_0_0.recognised_capability_extensions
                    if extension.tag not in recognised_types:
                        log.debug('Unsupported content extension : {}'.format(extension.tag))
                    else:
                        cls = recognised_types[extension.tag]
                        extension = cls.from_xml(extension, self)
                        self.contents_extensions.append(extension)

    def _raw_capabilities(self):
        return etree.tostring(self._capabilities, encoding='utf8', method='xml')

    def items(self):
        return self.contents.items()

#    def describeCoverageCollection(self, collectionid):
#        if isinstance(collectionid, CoverageSummary):
#            collectionid = collectionid.collectionid

    def getCoverage(self, xml):
        coverage_collection = self._find_operation('GetCoverage')
        base_url = coverage_collection.href_via('HTTP', 'Post')
        from owslib.util import http_post
        return http_post(base_url, xml)

    def _find_operation(self, name):
        for item in self.operations:
            if item.name == name:
                return item
        raise KeyError("No operation named %s" % name)


class Operation(object):
    """Abstraction for operation metadata    
    Implements IOperationMetadata.
    """
    def __init__(self, elem):
        self.name = elem.get('name')
        methods = []
        for request_method in elem.findall('ows200:DCP/ows200:HTTP/*', namespaces=WCS_names):
            url = request_method.attrib['{http://www.w3.org/1999/xlink}href']
            methods.append((request_method.tag, {'url': url}))           
        self.methods = dict(methods)

    def href_via(self, protocol='HTTP', method='Get'):
        if protocol != 'HTTP' or method not in ['Get', 'Post']:
            raise ValueError('Unexpected method or protocol.')
        for method_type, content in self.methods.items():
            if method_type.endswith(method):
                return content['url']
        raise ValueError('{} method {} not found for {}.'.format(protocol, method, self.name))

    @classmethod
    def _find(cls, element):
        tags = ['ows200:OperationsMetadata']
        for tag in tags:
            operations_element = element.find(tag, namespaces=WCS_names)
            if operations_element is not None:
                return operations_element

class ServiceIdentification(object):
    """ Abstraction for ServiceIdentification Metadata 
    implements IServiceIdentificationMetadata"""
    def __init__(self, elem):        
        self.service = "WCS"
        self.version = VERSION
        self.title = find_element(elem, 'Title', ['ows', 'ows200']).text
        self.abstract = find_element(elem, 'Abstract', ['ows', 'ows200', 'wcs20ows']).text
        self.keywords = [f.text for f in elem.findall('{http://www.opengis.net/ows}Keywords/{http://www.opengis.net/ows}Keyword')] 
        if elem.find('{http://www.opengis.net/wcs/1.1/ows}Fees') is not None:            
            self.fees = elem.find('{http://www.opengis.net/wcs/1.1/ows}Fees').text
        else:
            self.fees = None
        if  elem.find('{http://www.opengis.net/wcs/1.1/ows}AccessConstraints') is not None:
            self.accessConstraints=elem.find('{http://www.opengis.net/wcs/1.1/ows}AccessConstraints').text
        else:
            self.accessConstraints=None

    @classmethod
    def _find(cls, element):
        tags = ['ows200:ServiceIdentification', 'wcs20ows:ServiceIdentification',
                'wcs20:ServiceIdentification']
        for tag in tags:
            service_element = element.find(tag, namespaces=WCS_names)
            return service_element


class ServiceProvider(object):
    """ Abstraction for ServiceProvider metadata 
    implements IServiceProviderMetadata """
    def __init__(self,elem):
        self.name = find_element(elem, 'ProviderName', ['ows', 'ows200']).text
        self.contact = ContactMetadata(elem.find)

    @classmethod
    def _find(cls, element):
        tags = ['ows200:ServiceProvider']
        for tag in tags:
            provider_element = element.find(tag, namespaces=WCS_names)
            return provider_element

class ContactMetadata(object):
    ''' implements IContactMetadata'''
    def __init__(self, elem):
        try:
            self.name = elem.find('{http://www.opengis.net/ows}ServiceContact/{http://www.opengis.net/ows}IndividualName').text
        except AttributeError:
            self.name = None

        try:
            self.delivery_point = elem.find('{http://www.opengis.net/ows}ServiceContact/{http://www.opengis.net/ows}ContactInfo/{http://www.opengis.net/ows}Address/{http://www.opengis.net/ows}DeliveryPoint').text
        except AttributeError:
            self.delivery_point = None
        try:
            self.city = elem.find('{http://www.opengis.net/ows}ServiceContact/{http://www.opengis.net/ows}ContactInfo/{http://www.opengis.net/ows}Address/{http://www.opengis.net/ows}City').text
        except AttributeError:
            self.city = None
        
        try:
            self.region = elem.find('{http://www.opengis.net/ows}ServiceContact/{http://www.opengis.net/ows}ContactInfo/{http://www.opengis.net/ows}Address/{http://www.opengis.net/ows}AdministrativeArea').text
        except AttributeError:
            self.region = None
        
        try:
            self.postcode = elem.find('{http://www.opengis.net/ows}ServiceContact/{http://www.opengis.net/ows}ContactInfo/{http://www.opengis.net/ows}Address/{http://www.opengis.net/ows}PostalCode').text
        except AttributeError:
            self.postcode = None
        
        try:
            self.country = elem.find('{http://www.opengis.net/ows}ServiceContact/{http://www.opengis.net/ows}ContactInfo/{http://www.opengis.net/ows}Address/{http://www.opengis.net/ows}Country').text
        except AttributeError:
            self.country = None
        
        try:
            self.email = elem.find('{http://www.opengis.net/ows}ServiceContact/{http://www.opengis.net/ows}ContactInfo/{http://www.opengis.net/ows}Address/{http://www.opengis.net/ows}ElectronicMailAddress').text
        except AttributeError:
            self.email = None
