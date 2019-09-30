"""
Forked from https://github.com/wheerd/multiset
Thanks my guy
"""

from __future__ import annotations

import typing as t
import itertools
from collections import defaultdict

from yeetlong.maps import OrderedDefaultDict


T = t.TypeVar('T')
V = t.TypeVar('V')


__all__ = [
    'BaseMultiset',
    'BaseOrderedMultiset',
    'Multiset',
    'OrderedMultiset',
    'FrozenMultiset',
    'FrozenOrderedMultiset',
]


class BaseMultiset(t.AbstractSet[T]):
    __slots__ = ('_elements',)

    def __init__(self, iterable: t.Optional[t.Iterable[T]] = None) -> None:
        if isinstance(iterable, BaseMultiset):
            self._elements = iterable._elements.copy()
            return

        self._elements: t.DefaultDict[T, int] = defaultdict(int)

        if iterable is not None:

            if isinstance(iterable, t.Mapping):
                for element, multiplicity in iterable.items():
                    if multiplicity > 0:
                        self._elements[element] = multiplicity

            else:
                for element in iterable:
                    self._elements[element] += 1

    def __new__(cls, iterable: t.Optional[t.Iterable[T]] = None):
        if cls is BaseMultiset:
            raise TypeError("Cannot instantiate BaseMultiset directly, use either Multiset or FrozenMultiset.")
        return super(BaseMultiset, cls).__new__(cls)

    def __contains__(self, element: T) -> bool:
        return element in self._elements

    def __getitem__(self, element: T) -> int:
        return self._elements.__getitem__(element)

    def __str__(self) -> str:
        return '{{{}}}'.format(
            ', '.join(
                map(str, self)
            ),
        )

    def __repr__(self) -> str:
        return '{}({{{}}})'.format(
            self.__class__.__name__,
            ', '.join(
                '{}: {}'.format(*items)
                for items in
                self._elements.items()
            ),
        )

    def __len__(self) -> int:
        return sum(self._elements.values())

    def __bool__(self) -> bool:
        return bool(self._elements)

    def __iter__(self) -> t.Iterator[T]:
        return itertools.chain.from_iterable(
            itertools.starmap(
                itertools.repeat,
                self._elements.items()
            )
        )

    def isdisjoint(self, other: t.Counter[T]) -> bool:
        return all(element not in other for element in self._elements.keys())

    def difference(self, *others: t.Iterable[T]) -> BaseMultiset[T]:
        result = self.__copy__()
        _elements = result._elements

        for other in map(self._as_mapping, others):
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
                if new_multiplicity <= 0:
                    del _elements[element]
                elif multiplicity > new_multiplicity:
                    _elements[element] = new_multiplicity

        return result

    def __and__(self, other):
        return self.intersection(other)

    __rand__ = __and__

    def symmetric_difference(self, other: t.Iterable[T]) -> BaseMultiset[T]:
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

    def __xor__(self, other: t.Iterable[T]) -> BaseMultiset[T]:
        return self.symmetric_difference(other)

    __rxor__ = __xor__

    def times(self, factor: int) -> BaseMultiset[T]:
        if factor == 0:
            return self.__class__()
        if factor < 0:
            raise ValueError('The factor must no be negative.')
        result = self.__copy__()
        _elements = result._elements
        for element in _elements:
            _elements[element] *= factor
        return result

    def __mul__(self, factor: int) -> BaseMultiset[T]:
        return self.times(factor)

    __rmul__ = __mul__

    def _issubset(self, other: t.Iterable[T], strict: bool) -> bool:
        other = self._as_multiset(other)
        len_self = len(self)
        len_other = len(other)

        if len_self > len_other or strict and len_self == len_other:
            return False

        return all(
            multiplicity <= other[element]
            for element, multiplicity in
            self.items()
        )

    def issubset(self, other):
        return self._issubset(other, False)

    def __le__(self, other):
        return self._issubset(other, False)

    def __lt__(self, other):
        return self._issubset(other, True)

    def _issuperset(self, other: t.Collection[T], strict: bool) -> bool:
        other = self._as_multiset(other)
        len_self = len(self)
        len_other = len(other)

        if len_self < len_other or strict and len_self == len_other:
            return False

        return all(
            multiplicity <= self._elements[element]
            for element, multiplicity in
            other.items()
        )

    def issuperset(self, other: t.Collection[T]) -> bool:
        return self._issuperset(other, False)

    def __ge__(self, other: t.Collection[T]) -> bool:
        return self._issuperset(other, False)

    def __gt__(self, other: t.Collection[T]) -> bool:
        return self._issuperset(other, True)

    def __eq__(self, other: t.Collection[T]) -> bool:
        if isinstance(other, BaseMultiset):
            return self._elements == other._elements
        return self._issubset(other, False) and len(self) == len(other)

    def __ne__(self, other: t.Collection[T]) -> bool:
        if isinstance(other, BaseMultiset):
            return self._elements != other._elements
        return not self._issubset(other, False) and len(self) != len(other)

    def get(self, element: T, default: t.Optional[V] = None) -> t.Union[int, V, None]:
        return self._elements.get(element, default)

    @classmethod
    def from_elements(cls, elements: t.Iterable[T], multiplicity: int) -> BaseMultiset[T]:
        return cls(dict.fromkeys(elements, multiplicity))

    def copy(self) -> BaseMultiset[T]:
        return self.__class__(self)

    __copy__ = copy

    def items(self) -> t.Iterable[t.Tuple[T, int]]:
        return self._elements.items()

    def distinct_elements(self) -> t.KeysView[T]:
        return self._elements.keys()

    def multiplicities(self) -> t.Iterable[int]:
        return self._elements.values()

    def elements(self) -> t.Mapping[T, int]:
        return self._elements

    values = multiplicities  # type: t.Callable[[], t.ValuesView[T]]

    @classmethod
    def _as_multiset(cls, other: t.Iterable[T]) -> BaseMultiset[T]:
        if isinstance(other, BaseMultiset):
            return other
        return cls(other)

    @classmethod
    def _as_mapping(cls, iterable: t.Iterable[T]) -> t.Mapping[T, int]:
        if isinstance(iterable, BaseMultiset):
            return iterable._elements

        if isinstance(iterable, t.Mapping):
            return iterable

        mapping = defaultdict(int)
        for element in iterable:
            mapping[element] += 1
        return mapping

    def __getstate__(self):
        return self._elements

    def __setstate__(self, state):
        self._elements = state


class BaseOrderedMultiset(BaseMultiset[T]):
    
    def __init__(self, iterable: t.Optional[t.Iterable[T]] = None) -> None:
        if isinstance(iterable, BaseMultiset):
            self._elements = iterable._elements.copy()
            return

        self._elements: OrderedDefaultDict[T, int] = OrderedDefaultDict(int)

        if iterable is not None:

            if isinstance(iterable, t.Mapping):
                for element, multiplicity in iterable.items():
                    if multiplicity > 0:
                        self._elements[element] = multiplicity

            else:
                for element in iterable:
                    self._elements[element] += 1


class Multiset(BaseMultiset[T]):
    __slots__ = ()

    def __setitem__(self, element: T, multiplicity: int) -> None:
        _elements = self._elements
        if element in _elements:
            if multiplicity > 0:
                _elements[element] = multiplicity
            else:
                del _elements[element]
        elif multiplicity > 0:
            _elements[element] = multiplicity

    def __delitem__(self, element: T) -> None:
        if element in self._elements:
            del self._elements[element]
        else:
            raise KeyError("Could not delete {!r} from the multiset, because it is not in it.".format(element))

    def update(self, *others: t.Iterable[T]) -> Multiset[T]:
        for other in map(self._as_mapping, others):
            for element, multiplicity in other.items():
                self[element] += multiplicity

        return self

    def union_update(self, *others: t.Iterable[T]) -> Multiset[T]:
        _elements = self._elements

        for other in map(self._as_mapping, others):
            for element, multiplicity in other.items():
                old_multiplicity = _elements.get(element, 0)
                if multiplicity > old_multiplicity:
                    _elements[element] = multiplicity

        return self

    def __ior__(self, other: t.Iterable[T]) -> Multiset[T]:
        return self.union_update(other)

    def intersection_update(self, *others: t.Iterable[T]) -> Multiset[T]:
        for other in map(self._as_mapping, others):
            for element, current_count in self.items():
                multiplicity = other.get(element, 0)
                if multiplicity < current_count:
                    self[element] = multiplicity

        return self

    def __iand__(self, other: t.Iterable[T]) -> Multiset[T]:
        return self.intersection_update(other)

    def difference_update(self, *others: t.Iterable[T]) -> Multiset[T]:
        for other in map(self._as_multiset, others):
            for element, multiplicity in other.items():
                self.discard(element, multiplicity)

        return self

    def __isub__(self, other: t.Iterable[T]) -> Multiset[T]:
        return self.difference_update(other)

    def symmetric_difference_update(self, other: t.Iterable[T]) -> Multiset[T]:
        other = self._as_multiset(other)
        elements = self.distinct_elements() | other.distinct_elements()
        for element in elements:
            multiplicity = self[element]
            other_count = other[element]
            self[element] = (multiplicity - other_count if multiplicity > other_count else other_count - multiplicity)

        return self

    def __ixor__(self, other: t.Iterable[T]) -> Multiset[T]:
        return self.symmetric_difference_update(other)

    def times_update(self, factor: int) -> Multiset[T]:
        if factor < 0:
            raise ValueError("The factor must not be negative.")
        elif factor == 0:
            self.clear()
        else:
            _elements = self._elements
            for element in _elements:
                _elements[element] *= factor

        return self

    def __imul__(self, factor: int) -> Multiset[T]:
        return self.times_update(factor)

    def add(self, element: T, multiplicity = 1) -> Multiset[T]:
        if multiplicity < 1:
            raise ValueError("Multiplicity must be positive")
        self._elements[element] += multiplicity

        return self

    def remove(self, element: T, multiplicity: t.Optional[int] = None) -> int:
        _elements = self._elements
        if element not in _elements:
            raise KeyError
        old_multiplicity = _elements.get(element, 0)
        if multiplicity is None or multiplicity >= old_multiplicity:
            del _elements[element]
        elif multiplicity < 0:
            raise ValueError("Multiplicity must be not be negative")
        elif multiplicity > 0:
            _elements[element] -= multiplicity
        return old_multiplicity

    def discard(self, element: T, multiplicity: t.Optional[int] = None) -> int:
        _elements = self._elements
        if element in _elements:
            old_multiplicity = _elements[element]
            if multiplicity is None or multiplicity >= old_multiplicity:
                del _elements[element]
            elif multiplicity < 0:
                raise ValueError("Multiplicity must not be negative")
            elif multiplicity > 0:
                _elements[element] -= multiplicity
            return old_multiplicity
        else:
            return 0

    def pop(self, element: T, default: t.Optional[V] = None) -> t.Union[int, V, None]:
        return self._elements.pop(element, default)

    def clear(self) -> BaseMultiset[T]:
        self._elements.clear()
        return self


class OrderedMultiset(Multiset[T], BaseOrderedMultiset[T]):
    __slots__ = ()
    

class FrozenMultiset(BaseMultiset[T]):
    __slots__ = ('_hash',)

    def __hash__(self) -> int:
        if not hasattr(self, '_hash') or self._hash is None:
            self._hash = hash(frozenset(self._elements.items()))
        return self._hash


class FrozenOrderedMultiset(FrozenMultiset[T], BaseOrderedMultiset[T]):
    __slots__ = ()