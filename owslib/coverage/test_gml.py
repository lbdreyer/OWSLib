from unittest import TestCase
from lxml import etree
import gml


XML_template = """
<?xml version="1.0" encoding="UTF-8"?>
<root xmlns:gml="http://www.opengis.net/gml/3.2">
{content}
</root>
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


class TestGMLDomainSet(TestCase):
    def setUp(self):
        root = etree.XML(DOMAINSET_EXAMPLE)
        self.ds = gml.GMLdomainSet.from_xml(root[0])

    def test_limits(self):
        envelope = self.ds.geometry.limits
        self.assertIsInstance(envelope, gml.GMLGridEnvelope)

    def test_axes(self):
        axes = self.ds.geometry.axes
        self.assertEqual(axes, ['x', 'y'])

    def test_origin(self):
        origin = self.ds.geometry.origin
        self.assertIsInstance(origin, gml.GMLPoint)

    def test_offset_vectors(self):
        offset_vectors = self.ds.geometry.offset_vectors
        for vector in offset_vectors:
            self.assertIsInstance(vector, gml.GMLVector)


class TestGMLVector(TestCase):
    def setUp(self):
        root = etree.XML(DOMAINSET_EXAMPLE)
        ds = gml.GMLdomainSet.from_xml(root[0])
        self.vector = ds.geometry.offset_vectors[0]

    def test_repr(self):
        self.assertEqual(repr(self.vector), 'GMLVector([0.5, 7.0467596052536985])')

    def test_attributes(self):
        self.assertEqual(self.vector.components, [0.5, 7.0467596052536985])


class TestGMLEnvelope(TestCase):
    def setUp(self):
        root = etree.XML(XML_template.format(content="""
          <gml:Envelope axisLabels="Long Lat" srsDimension="2" srsName="CRS:84" uomLabels="deg deg">
            <gml:lowerCorner>-180 -90</gml:lowerCorner>
            <gml:upperCorner>180 90</gml:upperCorner>
          </gml:Envelope>
        """))
        self.envelope = gml.GMLEnvelope.from_xml(root[0])

    def test_repr(self):
        self.assertEqual(repr(self.envelope),
                         'GMLEnvelope(lows=[-180.0, -90.0], highs=[180.0, 90.0])')

    def test_attributes(self):
        self.assertIsInstance(self.envelope.lows[0], float)
        self.assertEqual(self.envelope.lows, [-180.0, -90.0])
        self.assertEqual(self.envelope.highs, [180.0, 90.0])


class TestGMLGridEnvelope(TestCase):
    def setUp(self):
        root = etree.XML(DOMAINSET_EXAMPLE)
        ds = gml.GMLdomainSet.from_xml(root[0])
        self.envelope = ds.geometry.limits

    def test_repr(self):
        self.assertEqual(repr(self.envelope),
                         'GMLGridEnvelope(x0=0, y0=0, x1=719, y1=360)')

    def test_attributes(self):
        self.assertIsInstance(self.envelope.x0, int)
        self.assertEqual(self.envelope.x0, 0)
        self.assertEqual(self.envelope.y0, 0)
        self.assertEqual(self.envelope.x1, 719)
        self.assertEqual(self.envelope.y1, 360)


class TestGMLPoint(TestCase):
    def setUp(self):
        root = etree.XML(DOMAINSET_EXAMPLE)
        ds = gml.GMLdomainSet.from_xml(root[0])
        self.point = ds.geometry.origin

    def test_repr(self):
        self.assertEqual(repr(self.point),
                         'GMLPoint([0.0, -90.0])')

    def test_attributes(self):
        self.assertIsInstance(self.point.xy[0], float)
        self.assertEqual(self.point.xy, [0.0, -90.0])


# Chapter 14

class TestGMLTimePosition(TestCase):
    def setUp(self):
        root = etree.XML(XML_template.format(content="""
          <gml:timePosition>2015-01-11T15:31:52Z</gml:timePosition>
        """))
        self.time = gml.GMLTimePosition.from_xml(root[0])

    def test_repr(self):
        self.assertEqual(repr(self.time),
                         'GMLTimePosition(datetime.datetime(2015, 1, 11, 15, 31, 52))')

    def test_attributes(self):
        import datetime
        self.assertIsInstance(self.time.datetime, datetime.datetime)
        self.assertEqual(self.time.datetime, datetime.datetime(2015, 1, 11, 15, 31, 52))


if __name__ == '__main__':
    import nose
    nose.runmodule(argv=['-s', '--with-doctest'], exit=False)