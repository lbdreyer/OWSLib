'''
Created on Jan 14, 2015

@author: itpp
'''
from lxml import etree
from owslib.coverage.wcs200 import WebCoverageService_2_0_0 as wcs
from owslib.coverage.wcs200 import log as wcs_log
from owslib.coverage.wcs200 import WCS_names
from owslib.coverage.gml import GMLTimePosition, GMLEnvelope

# Define useful namespace lookup dictionaries.
MO_names = {'meto': 'http://def.wmo.int/metce/2013/metocean'}
GML_names = {'gml32': 'http://www.opengis.net/gml/3.2'}

# A list of the subtypes of WCSExtension that we want to recognise.
_WCS_EXTENSION_SUBTYPES = []

class MetOceanCoverageCollection(object):
    def __init__(self, service, coverage_collection_id,
                 name=None, envelope=None, reference_times=None):
        #: The WebCoverageService instance that created this CoverageCollection.
        self.service = service

        self.name = name
        self.coverage_collection_id = coverage_collection_id
        self.envelope = envelope
        self.reference_times = reference_times

    @classmethod
    def from_xml(cls, element, service):
        get_text = lambda elem: elem.text
        element_mapping = {
            '{{{meto}}}coverageCollectionId'.format(**MO_names): ['coverage_collection_id', get_text],
            # The latest spect states that there will be an envelope at this level, but the test server has a boundedBy parenting the envelope.
            '{{{gml32}}}boundedBy'.format(**GML_names): ['envelope', GMLBoundedBy.from_xml],
            '{{{meto}}}referenceTimeList'.format(**MO_names): ['reference_times', MetOceanReferenceTimeList.from_xml],
            '{{{gml32}}}name'.format(**GML_names): ['name', get_text]
            }
        keywords = {'service': service}
        for child in element:
            if child.tag in element_mapping:
                keyword_name, element_fn = element_mapping[child.tag]
                keywords[keyword_name] = element_fn(child)
            else:
                wcs_log.debug('Coverage tag {} not found.'.format(child.tag))
        try:
            return cls(**keywords)
        except:
            print('Tried to initialise {} with {}'.format(cls, keywords))
            raise

    def describe(self):
        """
        Request describeCoverageCollection for this collection.

        """
        service = self.service
        coverage_collection = self.service.find_operation('DescribeCoverageCollection')
        base_url = coverage_collection.href_via('HTTP', 'Get')

        #process kwargs
        request = {'version': service.version,
                   'request': 'DescribeCoverageCollection',
                   'service':'WCS',
                   '{{{meto}}}coverageCollectionId'.format(**MO_names): self.coverage_collection_id}
        #encode and request
        data = urlencode(request)

        return openURL(base_url, data, 'Get', service.cookies)

# Add this class to our list of Extension subtypes that we want WCS2.0 to recognise.
_WCS_EXTENSION_SUBTYPES.append(MetOceanCoverageCollection)


class MetOceanReferenceTimeList(object):
    def __init__(self, times):
        self.times = times

    @classmethod
    def from_xml(cls, element):
        children = list(element[0])
        times = [GMLTimePosition.from_xml(child) for child in children]
        return cls(times)


class GMLBoundedBy(object):
    @classmethod
    def from_xml(cls, element):
        # This is a dumb class which just returns its only child (this is removed
        # from the spec in later revisions, but is still in place on the test server).
        return GMLEnvelope.from_xml(element[0])


def _GetCoverage_etree(coverage, fields=None, subsets=None,
                       result_format='NetCDF3'):
    """
    Construct an etree xml representation for a GetCoverage call.

    Args:
    * coverage (string):  (?? or CoverageDescription objects ??)
        which coverage to get
    * fields ((list of) string):  (?? or Field objects ???):
        which fields (aka phenomenon names).  (Default is all).
    * subsets (list of ???):
        specify dimension subsetting
    * result_format (string):
        type of file to return.

    """
    if isinstance(coverage, basestring):
        coverage_string = coverage
    else:
        coverage_string = coverage.name
    if fields is None:
        fields = all_fields  # TODO: need to define this somehow !
    if isinstance(fields, basestring):  #TODO: or Field type
        fields = [fields]
    field_names = [fld if isinstance(fld, basestring) else fld.name
                   for fld in fields]
    # Create the root GetCoverage element.
    tagname = '{{{wcs20}}}GetCoverage'.format(**WCS_names)
    root_el = etree.Element(tagname,
                            service='WCS', version='2.0.0')

    # Add the absolutely minimal root_el/Extension element, as required.
    tagname = '{{{wcs20}}}Extension'.format(**WCS_names)
    ext_el = etree.SubElement(root_el, tagname)
    # Add a root_el/Extension/RangeSubset, specifying the fields required.
    tagname = ('{http://www.opengis.net/wcs/range-subsetting/1.0}'
               'rangeSubset')
    subs_el = etree.SubElement(ext_el, tagname)
    for fld_name in field_names:
        tagname = ('{http://www.opengis.net/wcs/range-subsetting/1.0}'
                   'rangeComponent')
        fld_el = etree.Element(tagname)
        fld_el.text = fld_name
        subs_el.append(fld_el)
    # Add a root_el/Extension/GetCoverageCrs
    tagname = ('{http://www.opengis.net/wcs_service-extension_crs/1.0}'
               'GetCoverageCrs')
    crs_el = etree.SubElement(ext_el, tagname)
    # Add a root_el/Extension/GetCoverageCrs/subsettingCrs
    tagname = ('{http://www.opengis.net/wcs_service-extension_crs/1.0}'
               'subsettingCrs')
    crs_ss_el = etree.SubElement(crs_el, tagname)
    # N.B. insists on having one, and must have (at least) an empty text.
    crs_ss_el.text = ' \n '

    # Add the root/coverageId element.
    cov_el = etree.SubElement(root_el,
                           '{{{wcs20}}}CoverageId'.format(**WCS_names))
    cov_el.text = coverage_string

    # Add the format element.
    fmt_el = etree.SubElement(root_el,
                           '{{{wcs20}}}format'.format(**WCS_names))
    fmt_el.text = result_format
    return root_el


def GetCoverage_xml(self, *args, **kwargs):
    """
    Return xml for a GetCoverage call.

    Args:
    * coverage (string):  (?? or CoverageDescription objects ??)
        which coverage to get
    * fields ((list of) string):  (?? or Field objects ???):
        which fields (aka phenomenon names).  (Default is all).
    * subsets (list of ???):
        specify dimension subsetting
    * result_format (string):
        type of file to return.

    """
    tree = self._etree_for_GetCoverage(*args, **kwargs)
    text = etree.tostring(tree)
    return '<?xml version="1.0" encoding="UTF-8"?>' + text


def register_wcs_extension_subtypes():
    for cls in _WCS_EXTENSION_SUBTYPES:
        wcs.recognised_capability_extensions[cls.TAG] = cls
