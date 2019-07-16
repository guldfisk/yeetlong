"""
Forked from https://github.com/wheerd/multiset
Thanks my guy
"""
from __future__ import annotations

import typing as t

from collections import defaultdict

import itertools


T = t.TypeVar('T')

# _int_type = int
# _sequence_types = (tuple, list, range, set, frozenset, str)
# _iter_types = (type(iter([])), type((lambda: (yield))()))
#
# _all_basic_types = _sequence_types + _iter_types + (dict, )

__all__ = ['BaseMultiset', 'Multiset', 'FrozenMultiset']


class BaseMultiset(t.AbstractSet[T]):

    __slots__ = ('_elements',)

    def __init__(self, iterable: t.Optional[t.Iterable[T]]=None) -> None:
        if isinstance(iterable, BaseMultiset):
            self._elements = iterable._elements.copy()
            return

        self._elements = _elements = defaultdict(int) #type: t.DefaultDict[T, int]

        if iterable is not None:

            if isinstance(iterable, t.Mapping):
                for element, multiplicity in iterable.items():
                    if multiplicity > 0:
                        _elements[element] = multiplicity

            else:
                for element in iterable:
                    _elements[element] += 1

    def __new__(cls, iterable=None):
        if cls is BaseMultiset:
            raise TypeError("Cannot instantiate BaseMultiset directly, use either Multiset or FrozenMultiset.")
        return super(BaseMultiset, cls).__new__(cls)

    def __contains__(self, element) -> bool:
        return element in self._elements

    def __getitem__(self, element) -> int:
        return self._elements.get(element, 0)

    def __repr__(self) -> str:
        return '{}({{}})'.format(
            self.__class__.__name__,
            ', '.join(
                '{}: {}'.format(item, multiplicity)
                for item, multiplicity in
                self._elements.items()
            ),
        )

    def __len__(self) -> int:
        return sum(self._elements.values())

    def __bool__(self) -> bool:
        return bool(self._elements)

    def __iter__(self) -> t.Iterable[T]:
        return itertools.chain.from_iterable(
            itertools.starmap(
                itertools.repeat,
                self._elements.items()
            )
        )

    def isdisjoint(self, other) -> bool:
        if not isinstance(other, t.Container):
            other = self._as_multiset(other)
        return all(element not in other for element in self._elements.keys())

    def difference(self, *others: t.Iterable[T]) -> BaseMultiset[T]:
        result = self.__copy__()
        _elements = result._elements
        _total = result._total

        for other in map(self._as_multiset, others):
            for element, multiplicity in other.items():
                if element in _elements:
                    new_multiplicity = _elements[element] - multiplicity
                    if new_multiplicity > 0:
                        _elements[element] = new_multiplicity
                    else:
                        del _elements[element]

        return result

    def __sub__(self, other: t.Iterable) -> BaseMultiset[T]:
        return self.difference(other)

    def __rsub__(self, other: t.Iterable) -> BaseMultiset[T]:
        return self._as_multiset(other).difference(self)

    def union(self, *others: t.Iterable[T]) -> BaseMultiset[T]:
        result = self.__copy__()
        _elements = result._elements

        for other in map(self._as_mapping, others):
            for element, multiplicity in other.items():
                if multiplicity > _elements.get(element, 0):
                    _elements[element] = multiplicity

        return result

    def __or__(self, other: t.Iterable[T]) -> BaseMultiset[T]:
        return self.union(other)

    __ror__ = __or__

    def combine(self, *others: t.Iterable[T]) -> BaseMultiset[T]:
        result = self.__copy__()
        _elements = result._elements

        for other in map(self._as_mapping, others):
            for element, multiplicity in other.items():
                _elements[element] += multiplicity
                if _elements[element] <= 0:
                    del _elements[element]

        return result

    def __add__(self, other: t.Iterable[T]) -> BaseMultiset[T]:
        return self.combine(other)

    __radd__ = __add__

    def intersection(self, *others: t.Iterable[T]) -> BaseMultiset[T]:
        result = self.__copy__()
        _elements = result._elements

        for other in map(self._as_mapping, others):
            for element, multiplicity in list(_elements.items()):
                new_multiplicity = other.get(element, 0)
                if multiplicity > new_multiplicity > 0:
                    _elements[element] = new_multiplicity
                else:
                    del _elements[element]

        return result

    def __and__(self, other):
        return self.intersection(other)

    __rand__ = __and__

    def symmetric_difference(self, other: BaseMultiset[T]) -> BaseMultiset[T]:
        other = self._as_multiset(other)
        result = self.__class__()
        _elements = result._elements
        self_elements = self._elements
        other_elements = other._elements
        dist_elements = set(self_elements.keys()) | set(other_elements.keys())

        for element in dist_elements:
            multiplicity = self_elements.get(element, 0)
            other_multiplicity = other_elements.get(element, 0)
            new_multiplicity = (
                multiplicity - other_multiplicity
                if multiplicity > other_multiplicity else
                other_multiplicity - multiplicity
            )
            if new_multiplicity > 0:
                _elements[element] = new_multiplicity

        return result

    def __xor__(self, other):
        if isinstance(other, (BaseMultiset, set, frozenset)):
            pass
        elif not isinstance(other, Set):
            return NotImplemented
        return self.symmetric_difference(other)

    __rxor__ = __xor__

    def times(self, factor):
        if factor == 0:
            return self.__class__()
        if factor < 0:
            raise ValueError('The factor must no be negative.')
        result = self.__copy__()
        _elements = result._elements
        for element in _elements:
            _elements[element] *= factor
        result._total *= factor
        return result

    def __mul__(self, factor):
        if not isinstance(factor, _int_type):
            return NotImplemented
        return self.times(factor)

    __rmul__ = __mul__

    def _issubset(self, other, strict):
        other = self._as_multiset(other)
        self_len = self._total
        other_len = len(other)
        if self_len > other_len:
            return False
        if self_len == other_len and strict:
            return False
        return all(multiplicity <= other[element] for element, multiplicity in self.items())

    def issubset(self, other):
        return self._issubset(other, False)

    def __le__(self, other):
        if isinstance(other, (BaseMultiset, set, frozenset)):
            pass
        elif not isinstance(other, Set):
            return NotImplemented
        return self._issubset(other, False)

    def __lt__(self, other):
        if isinstance(other, (BaseMultiset, set, frozenset)):
            pass
        elif not isinstance(other, Set):
            return NotImplemented
        return self._issubset(other, True)

    def _issuperset(self, other, strict):
        other = self._as_multiset(other)
        other_len = len(other)
        if len(self) < other_len:
            return False
        if len(self) == other_len and strict:
            return False
        for element, multiplicity in other.items():
            if self[element] < multiplicity:
                return False
        return True

    def issuperset(self, other):
        return self._issuperset(other, False)

    def __ge__(self, other):
        if isinstance(other, (BaseMultiset, set, frozenset)):
            pass
        elif not isinstance(other, Set):
            return NotImplemented
        return self._issuperset(other, False)

    def __gt__(self, other):
        if isinstance(other, (BaseMultiset, set, frozenset)):
            pass
        elif not isinstance(other, Set):
            return NotImplemented
        return self._issuperset(other, True)

    def __eq__(self, other):
        if isinstance(other, BaseMultiset):
            return self._total == other._total and self._elements == other._elements
        if isinstance(other, (set, frozenset)):
            pass
        elif not isinstance(other, Set):
            return NotImplemented
        if self._total != len(other):
            return False
        return self._issubset(other, False)

    def __ne__(self, other):
        if isinstance(other, BaseMultiset):
            return self._total != other._total or self._elements != other._elements
        if isinstance(other, (set, frozenset)):
            pass
        elif not isinstance(other, Set):
            return NotImplemented
        if self._total != len(other):
            return True
        return not self._issubset(other, False)

    def get(self, element, default):
        return self._elements.get(element, default)

    @classmethod
    def from_elements(cls, elements, multiplicity):
        return cls(dict.fromkeys(elements, multiplicity))

    def copy(self):
        return self.__class__(self)

    __copy__ = copy

    def items(self):
        return self._elements.items()

    def distinct_elements(self):
        return self._elements.keys()

    def multiplicities(self):
        return self._elements.values()

    values = multiplicities

    @classmethod
    def _as_multiset(cls, other):
        if isinstance(other, BaseMultiset):
            return other
        return cls(other)

    @staticmethod
    def _as_mapping(iterable):
        if isinstance(iterable, BaseMultiset):
            return iterable._elements
        if isinstance(iterable, dict):
            return iterable
        if isinstance(iterable, _all_basic_types):
            pass  # create dictionary below
        elif isinstance(iterable, Mapping):
            return iterable
        elif not isinstance(iterable, Iterable):
            raise TypeError("'%s' object is not iterable" % type(iterable))
        mapping = dict()
        for element in iterable:
            if element in mapping:
                mapping[element] += 1
            else:
                mapping[element] = 1
        return mapping

    def __getstate__(self):
        return self._total, self._elements

    def __setstate__(self, state):
        self._total, self._elements = state

class Multiset(BaseMultiset):
    __slots__ = ()

    def __setitem__(self, element, multiplicity):
        if not isinstance(multiplicity, _int_type):
            raise TypeError('multiplicity must be an integer')
        _elements = self._elements
        if element in _elements:
            old_multiplicity = _elements[element]
            if multiplicity > 0:
                _elements[element] = multiplicity
                self._total += multiplicity - old_multiplicity
            else:
                del _elements[element]
                self._total -= old_multiplicity
        elif multiplicity > 0:
            _elements[element] = multiplicity
            self._total += multiplicity

    def __delitem__(self, element):
        _elements = self._elements
        if element in _elements:
            self._total -= _elements[element]
            del _elements[element]
        else:
            raise KeyError("Could not delete {!r} from the multiset, because it is not in it.".format(element))

    def update(self, *others):
        _elements = self._elements
        for other in map(self._as_mapping, others):
            for element, multiplicity in other.items():
                self[element] += multiplicity

    def union_update(self, *others):
        _elements = self._elements
        _total = self._total
        for other in map(self._as_mapping, others):
            for element, multiplicity in other.items():
                old_multiplicity = _elements.get(element, 0)
                if multiplicity > old_multiplicity:
                    _elements[element] = multiplicity
                    _total += multiplicity - old_multiplicity
        self._total = _total

    def __ior__(self, other):
        if isinstance(other, (BaseMultiset, set, frozenset)):
            pass
        elif not isinstance(other, Set):
            return NotImplemented
        self.union_update(other)
        return self

    def intersection_update(self, *others):
        for other in map(self._as_mapping, others):
            for element, current_count in list(self.items()):
                multiplicity = other.get(element, 0)
                if multiplicity < current_count:
                    self[element] = multiplicity

    def __iand__(self, other):
        if isinstance(other, (BaseMultiset, set, frozenset)):
            pass
        elif not isinstance(other, Set):
            return NotImplemented
        self.intersection_update(other)
        return self

    def difference_update(self, *others):
        for other in map(self._as_multiset, others):
            for element, multiplicity in other.items():
                self.discard(element, multiplicity)

    def __isub__(self, other):
        if isinstance(other, (BaseMultiset, set, frozenset)):
            pass
        elif not isinstance(other, Set):
            return NotImplemented
        self.difference_update(other)
        return self

    def symmetric_difference_update(self, other):
        other = self._as_multiset(other)
        elements = set(self.distinct_elements()) | set(other.distinct_elements())
        for element in elements:
            multiplicity = self[element]
            other_count = other[element]
            self[element] = (multiplicity - other_count if multiplicity > other_count else other_count - multiplicity)

    def __ixor__(self, other):
        if isinstance(other, (BaseMultiset, set, frozenset)):
            pass
        elif not isinstance(other, Set):
            return NotImplemented
        self.symmetric_difference_update(other)
        return self

    def times_update(self, factor):
        if factor < 0:
            raise ValueError("The factor must not be negative.")
        elif factor == 0:
            self.clear()
        else:
            _elements = self._elements
            for element in _elements:
                _elements[element] *= factor
            self._total *= factor

    def __imul__(self, factor):
        if not isinstance(factor, _int_type):
            raise TypeError("factor must be an integer.")
        self.times_update(factor)
        return self

    def add(self, element, multiplicity=1):
        if multiplicity < 1:
            raise ValueError("Multiplicity must be positive")
        self._elements[element] += multiplicity
        self._total += multiplicity

    def remove(self, element, multiplicity=None):
        _elements = self._elements
        if element not in _elements:
            raise KeyError
        old_multiplicity = _elements.get(element, 0)
        if multiplicity is None or multiplicity >= old_multiplicity:
            del _elements[element]
            self._total -= old_multiplicity
        elif multiplicity < 0:
            raise ValueError("Multiplicity must be not be negative")
        elif multiplicity > 0:
            _elements[element] -= multiplicity
            self._total -= multiplicity
        return old_multiplicity

    def discard(self, element, multiplicity=None):
        _elements = self._elements
        if element in _elements:
            old_multiplicity = _elements[element]
            if multiplicity is None or multiplicity >= old_multiplicity:
                del _elements[element]
                self._total -= old_multiplicity
            elif multiplicity < 0:
                raise ValueError("Multiplicity must not be negative")
            elif multiplicity > 0:
                _elements[element] -= multiplicity
                self._total -= multiplicity
            return old_multiplicity
        else:
            return 0

    def pop(self, element, default):
        return self._elements.pop(element, default)

    def setdefault(self, element, default):
        return self._elements.setdefault(element, default)

    def clear(self):
        self._elements.clear()
        self._total = 0


class FrozenMultiset(BaseMultiset):
    __slots__ = ()

    def __hash__(self):
        return hash(tuple(sorted(self._elements.items())))
