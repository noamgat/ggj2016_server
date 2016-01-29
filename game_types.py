from schematics.models import Model
from schematics.types import FloatType, IntType
from schematics.types.compound import ListType

__author__ = 'noam'


class PatternPoint(object):
    x = 0
    y = 0

    def __iter__(self):
        yield self.x
        yield self.y


class PatternPointType(ListType):
    def __init__(self):
        ListType.__init__(self, FloatType(), min_size=2, max_size=2)

    def to_native(self, value, context=None):
        point = PatternPoint()
        point.x = value[0]
        point.y = value[1]
        return point

    def to_primitive(self, value, context=None):
        return [value.x, value.y]


class PatternEdge(object):
    src = 0
    dst = 0

    def __iter__(self):
        yield self.src
        yield self.dst


class PatternEdgeType(ListType):
    def __init__(self):
        ListType.__init__(self, IntType(), min_size=2, max_size=2)

    def to_native(self, value, context=None):
        point = PatternEdge()
        point.src = value[0]
        point.dst = value[1]
        return point

    def to_primitive(self, value, context=None):
        return [value.src, value.dst]


class PatternModel(Model):
    points = ListType(PatternPointType())
    edges = ListType(PatternEdgeType())
