#from __future__ import print_function
import lxml
import warnings


TEMPLATE_EXAMPLE = """
<?xml version="1.0" encoding="UTF-8"?>
<root xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:ows="http://www.opengis.net/ows/2.0" xmlns:wcs="http://www.opengis.net/wcs/2.0" xmlns:swe="http://www.opengis.net/swe/2.0" xmlns:gmlcov="http://www.opengis.net/gmlcov/1.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:om="http://www.opengis.net/om/2.0" xmlns:metocean="http://def.wmo.int/metce/2013/metocean" xmlns:metce="http://def.wmo.int/metce/2013" xmlns:sam="http://www.opengis.net/sampling/2.0" xmlns:sams="http://www.opengis.net/samplingSpatial/2.0" xmlns:gmlrgrid="http://www.opengis.net/gml/3.3/rgrid" xsi:schemaLocation="http://schemas.opengis.net/wcs/2.0 http://schemas.opengis.net/wcs/2.0/wcsAll.xsd http://def.wmo.int/metce/2013/metocean https://ogcie.iblsoft.com/schemas/wcs-2.0/wcsMetOceanDescribeCoverage.xsd">
    {content}
    
</root>
""".strip()

EXAMPLE = """
    <gmlcov:ReferenceableGridCoverage gml:id="rgc_maskId_GFS_Latest_ISBL_1">
                    <gml:boundedBy>
                      <gml:Envelope srsName="CRS:84" axisLabels="Long Lat" uomLabels="deg deg" srsDimension="2">
                        <gml:lowerCorner>-180 -90</gml:lowerCorner>
                        <gml:upperCorner>180 90</gml:upperCorner>
                      </gml:Envelope>
                    </gml:boundedBy>
                    <gml:domainSet>
                      <gmlrgrid:ReferenceableGridByArray gml:id="rgba_maskId_GFS_Latest_ISBL_1" dimension="2" srsName="http://www.opengis.net/def/crs-combine?1=http://codes.wmo.int/grib2/codeflag/4.5/100&amp;2=http://www.opengis.net/def/temporal/ISO8601" axisLabels="altitude time" uomLabels="hPa h">
                        <gml:limits>
                          <gml:GridEnvelope>
                            <gml:low>500 0</gml:low>
                            <gml:high>500 192</gml:high>
                          </gml:GridEnvelope>
                        </gml:limits>
                        <gml:axisLabels>z t</gml:axisLabels>
                        <gml:posList>
500 0
500 3
500 6
500 9
500 12
500 15
500 18
500 21
500 24
500 27
500 30
500 33
500 36
500 39
500 42
500 45
500 48
500 54
500 60
500 66
500 72
500 78
500 84
500 90
500 96
500 102
500 108
500 114
500 120
500 132
500 144
500 156
500 168
500 180
500 192
</gml:posList>
                        <gmlrgrid:sequenceRule axisOrder="+1 +2">Linear</gmlrgrid:sequenceRule>
                      </gmlrgrid:ReferenceableGridByArray>
                    </gml:domainSet>
                    <gml:rangeSet>
                      <gml:DataBlock>
                        <gml:rangeParameters/>
                        <gml:tupleList>
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
1
</gml:tupleList>
                      </gml:DataBlock>
                    </gml:rangeSet>
                    <gmlcov:rangeType>
                      <swe:DataRecord>
                        <swe:field name="datacompletenessomission">
                          <swe:Boolean>
                            <swe:quality>
                              <swe:Quantity>
                                <swe:uom></swe:uom>
                                <swe:constraint></swe:constraint>
                                <swe:value>1.0</swe:value>
                              </swe:Quantity>
                            </swe:quality>
                            <swe:nilValues>
                              <swe:NilValues>
                                <swe:nilValue reason="http://www.opengis.net/def/crs/EPSG/0/4326"/>
                              </swe:NilValues>
                            </swe:nilValues>
                            <swe:value>0</swe:value>
                          </swe:Boolean>
                        </swe:field>
                      </swe:DataRecord>
                    </gmlcov:rangeType>
                  </gmlcov:ReferenceableGridCoverage>
""".strip()


DOMAINSET_EXAMPLE = """
<?xml version="1.0" encoding="UTF-8"?>
<root xmlns:gml="http://www.opengis.net/gml/3.2">
<gml:domainSet>
  <gml:RectifiedGrid dimension="2" gml:id="GFS_Latest_ISBL_grid">
    <gml:limits>
      <gml:GridEnvelope>
        <gml:low>0 0</gml:low>
        <gml:high>719 360</gml:high>
      </gml:GridEnvelope>
    </gml:limits>
    <gml:axisName>x</gml:axisName>
    <gml:axisName>y</gml:axisName>
    <gml:origin>
      <gml:Point srsName="EPSG:4326" gml:id="GFS_Latest_ISBL_grid_origin">
        <gml:coordinates>0 -90</gml:coordinates>
      </gml:Point>
    </gml:origin>
    <gml:offsetVector srsName="EPSG:4326">0.5 7.0467596052536985</gml:offsetVector>
    <gml:offsetVector srsName="EPSG:4326">0 14.573944878270581</gml:offsetVector>
  </gml:RectifiedGrid>
</gml:domainSet>
</root>""".strip()


namespaces = {'gml': 'http://www.opengis.net/gml/3.2'}


class GeometryTypeTracking(type):
    """
    A metaclass to keep track of any abstract geometry subclasses.
    """
    def __init__(cls, name, bases, dct):
        # Update the _geometry_types dictionary for any subclass which
        # is created.
        cls._geometry_types[cls.TAG] = cls

        super(GeometryTypeTracking, cls).__init__(name, bases, dct)


def de_namespace(tag, namespaces):
    for key, namespace in namespaces.items():
        tag = tag.replace('{' + namespace + '}', key + ':')
    return tag


class GMLAbstractGeometry(object):
    # Ref: 10.1.3.1 AbstractGeometryType
    __metaclass__ = GeometryTypeTracking

    #: The GML tag that this geometry represents.
    TAG = None

    #: A mapping of GML tag to concrete implementation.
    #: This is updated automatically upon subclassing GMLAbstractGeometry
    #: and defining a suitable TAG class attribute.
    _geometry_types = {}

    @classmethod
    def subclass_from_xml(cls, element):
        geometry_class = cls._geometry_types[de_namespace(element.tag, namespaces)]
        return geometry_class.from_xml(element)


class GMLdomainSet(object):
    # Ref: 19.3.4 domainSet, DomainSetType
    def __init__(self, geometry):
        self.geometry = geometry

    @classmethod
    def from_xml(cls, element):
        geometry = GMLAbstractGeometry.subclass_from_xml(element[0])
        return cls(geometry)


class GMLGrid(GMLAbstractGeometry):
    # See 19.2.2 Grid
    TAG = 'gml:Grid'


class GMLPoint(GMLAbstractGeometry):
    # See 10.3.1 PointType, Point
    TAG = 'gml:Point'
    def __init__(self, xy):
        self.xy = xy

    @classmethod
    def from_xml(cls, element):
        coords = element.find('gml:coordinates', namespaces=namespaces).text.split()
        coords = [float(val) for val in coords]
        if not coords and element.find('gml:pos'):
            raise NotImplementedError('gml:pos not implemented yet. Very simple!')
        return cls(coords)

    def __repr__(self):
        return 'GMLPoint({})'.format(self.xy)


class GMLRectifiedGrid(GMLGrid):
    # See 19.2.3 RectifiedGrid
    TAG = 'gml:RectifiedGrid'

    def __init__(self, limits, axes, origin, offset_vectors):
        [self.limits, self.axes,
         self.origin, self.offset_vectors] = limits, axes, origin, offset_vectors

    @classmethod
    def from_xml(cls, element):
        limits = GMLGridEnvelope.from_xml(element.find('gml:limits', namespaces=namespaces)[0])

        axes = [axis.text for axis in element.findall('gml:axisName', namespaces=namespaces)]
        if not axes and element.find('gml:axisLabels', namespace=namespaces):
            warnings.warn('axisLabels not implemented for {}'.format(cls.__name__))

        origin_element = element.find('gml:origin', namespaces=namespaces)[0]
        origin = GMLAbstractGeometry.subclass_from_xml(origin_element)

        offset_vectors = [GMLVector.from_xml(vector)
                          for vector in element.findall('gml:offsetVector', namespaces=namespaces)]

        return cls(limits, axes, origin, offset_vectors)


class GMLEnvelope(object):
    # See 10.1.4.6 EnvelopeType, Envelope
    def __init__(self, lows, highs):
        self.lows, self.highs = lows, highs

    @classmethod
    def from_xml(cls, element):
        lows = element.find('gml:lowerCorner', namespaces=namespaces).text.split()
        highs = element.find('gml:upperCorner', namespaces=namespaces).text.split()
        lows = map(float, lows)
        highs = map(float, highs)
        return cls(lows, highs)

    def __repr__(self):
        return 'GMLEnvelope(lows={}, highs={})'.format(self.lows, self.highs)


class GMLGridEnvelope(object):
    # See 10.1.4.6 EnvelopeType, Envelope
    def __init__(self, x0, y0, x1, y1):
        self.x0, self.y0, self.x1, self.y1 = x0, y0, x1, y1

    @classmethod
    def from_xml(cls, element):
        # Note: We think this may be 2 dimensional.
        x0, y0 = element.find('gml:low', namespaces=namespaces).text.split()
        x1, y1 = element.find('gml:high', namespaces=namespaces).text.split()
        return cls(int(x0), int(y0), int(x1), int(y1))

    def __repr__(self):
        return 'GMLGridEnvelope(x0={}, y0={}, x1={}, y1={})'.format(self.x0, self.y0, self.x1, self.y1)



class GMLVector(object):
    # See 10.1.4.5 VectorType, Vector
    def __init__(self, components):
        self.components = components

    @classmethod
    def from_xml(cls, element):
        components = [float(val) for val in element.text.split()]
        return cls(components)

    def __repr__(self):
        return 'GMLVector({})'.format(self.components)


# Chapter 14

class GMLTimePosition(object):
    # See 14.2.2.7 TimePositionType, timePosition
    def __init__(self, datetime):
        self.datetime = datetime

    @classmethod
    def from_xml(cls, element):
        from datetime import datetime
        dt = datetime.strptime(element.text, '%Y-%m-%dT%H:%M:%SZ')
        return cls(dt)

    def __repr__(self):
        return 'GMLTimePosition({!r})'.format(self.datetime)




#def de_namelist(element):
#    """
#    Convert a namelist to a real list.
#    
#    See 8.2.4.1 booleanList, doubleList, integerList, NameList, NCNameList, QNameList,
#                booleanOrNilReasonList, NameOrNilReasonList, doubleOrNilReasonList,
#                integerOrNilReasonList
#
#    """




if __name__ == '__main__':
    from lxml import etree

    xml = TEMPLATE_EXAMPLE.format(content=EXAMPLE)
    xml = DOMAINSET_EXAMPLE
    root = etree.XML(xml)

    for element in root[0].findall('gml:domainSet', namespaces=namespaces):
        print GMLdomainSet.from_xml(element)
        print element.tag
#        ds = GMLdomainSet.from_xml(element)
#        print ds
#        print ds.geometry.limits, ds.geometry.axes, ds.geometry.origin, ds.geometry.offset_vectors
