from __future__ import annotations

import typing as t
from collections import defaultdict


T = t.TypeVar('T')
V = t.TypeVar('V')


class BaseCounter(t.Mapping[T, int]):
    __slots__ = ('_elements',)

    def __init__(self, mapping: t.Optional[t.Mapping[T, int]] = None) -> None:
        if isinstance(mapping, BaseCounter):
            self._elements = mapping._elements.copy()
            return

        self._elements = _elements = defaultdict(int)  # type: t.DefaultDict[T, int]

        if mapping is not None:
            self._elements.update(mapping)
                    
    def __new__(cls, mapping: t.Optional[t.Mapping[T, int]] = None):
        if cls is BaseCounter:
            raise TypeError("Cannot instantiate BaseCounter directly, use either Counter or FrozenCounter.")
        return super(BaseCounter, cls).__new__(cls)

    def __contains__(self, element) -> bool:
        return element in self._elements

    def __getitem__(self, element: T) -> int:
        return self._elements.__getitem__(element)

    def __str__(self) -> str:
        return '{{{}}}'.format(
            ', '.join(
                '{}: {}'.format(*items)
                for items in
                self._elements.items()
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
        return len(self._elements)

    def __bool__(self) -> bool:
        return bool(self._elements)

    def __iter__(self) -> t.Iterator[T]:
        return self._elements.__iter__()

    def difference(self, *others: t.Mapping[T, int]) -> BaseCounter[T]:
        result = self.__copy__()
        _elements = result._elements

        for other in map(self._as_counter, others):
            for element, multiplicity in other.items():
                if element in _elements:
                    new_multiplicity = _elements[element] - multiplicity
                    if new_multiplicity == 0:
                        del _elements[element]
                    else:
                        _elements[element] = new_multiplicity

        return result

    def __sub__(self, other: t.Mapping[T, int]) -> BaseCounter[T]:
        return self.difference(other)

    def __rsub__(self, other: t.Mapping[T, int]) -> BaseCounter[T]:
        return self._as_counter(other).difference(self)

    def combine(self, *others: t.Mapping[T, int]) -> BaseCounter[T]:
        result = self.__copy__()
        _elements = result._elements

        for other in map(self._as_mapping, others):
            for element, multiplicity in other.items():
                _elements[element] += multiplicity
                if _elements[element] == 0:
                    del _elements[element]

        return result

    def __add__(self, other: t.Mapping[T, int]) -> BaseCounter[T]:
        return self.combine(other)

    __radd__ = __add__

    def times(self, factor: int) -> BaseCounter[T]:
        if factor == 0:
            return self.__class__()
        result = self.__copy__()
        _elements = result._elements
        for element in _elements:
            _elements[element] *= factor
        return result

    def __mul__(self, factor: int) -> BaseCounter[T]:
        return self.times(factor)

    __rmul__ = __mul__

    def get(self, element: T, default: t.Optional[V] = None) -> t.Union[int, V, None]:
        return self._elements.get(element, default)

    @classmethod
    def from_elements(cls, elements: t.Iterable[T], multiplicity: int) -> BaseCounter[T]:
        return cls(dict.fromkeys(elements, multiplicity))

    def copy(self) -> BaseCounter[T]:
        return self.__class__(self)

    __copy__ = copy

    def items(self) -> t.Iterable[t.Tuple[T, int]]:
        return self._elements.items()

    def distinct_elements(self) -> t.KeysView[T]:
        return self._elements.keys()

    def multiplicities(self) -> t.ValuesView[int]:
        return self._elements.values()

    values = multiplicities #type: t.Callable[[], t.ValuesView[T]]

    @classmethod
    def _as_counter(cls, other: t.Mapping[T, int]) -> BaseCounter[T]:
        if isinstance(other, BaseCounter):
            return other
        return cls(other)

    @staticmethod
    def _as_mapping(mapping: t.Mapping[T, int]) -> t.Mapping[T, int]:
        if isinstance(mapping, BaseCounter):
            return mapping._elements
        return mapping

    def __getstate__(self):
        return self._elements

    def __setstate__(self, state):
        self._elements = state
        
        
class Counter(BaseCounter[T]):
    __slots__ = ()

    def __setitem__(self, element: T, multiplicity: int) -> None:
        _elements = self._elements
        if element in _elements:
            if multiplicity == 0:
                del _elements[element]
            else:
                _elements[element] = multiplicity
        elif multiplicity != 0:
            _elements[element] = multiplicity

    def __delitem__(self, element: T) -> None:
        if element in self._elements:
            del self._elements[element]
        else:
            raise KeyError("Could not delete {!r} from the Counter, because it is not in it.".format(element))

    def update(self, *others: t.Mapping[T, int]) -> Counter[T]:
        _elements = self._elements
        
        for other in map(self._as_mapping, others):
            for element, multiplicity in other.items():
                _elements[element] += multiplicity
                if _elements[element] == 0:
                    del _elements[element]

        return self

    def times_update(self, factor: int) -> Counter[T]:
        if factor == 0:
            self.clear()
        else:
            _elements = self._elements
            for element in _elements:
                _elements[element] *= factor

        return self

    def __imul__(self, factor: int) -> Counter[T]:
        return self.times_update(factor)

    def add(self, element: T, multiplicity: int = 1) -> Counter[T]:
        if multiplicity == 0:
            pass
        else:
            self._elements[element] += multiplicity

        return self

    def remove(self, element: T, multiplicity: int = 1) -> Counter[T]:
        return self.add(element, -multiplicity)

    def pop(self, element: T, default: t.Optional[V] = None) -> t.Union[int, V, None]:
        return self._elements.pop(element, default)

    def clear(self) -> BaseCounter[T]:
        self._elements.clear()
        return self
    
    
class FrozenCounter(BaseCounter[T]):
    __slots__ = ('_hash',)

    def __hash__(self) -> int:
        if not hasattr(self, '_hash') or self._hash is None:
            self._hash = hash(frozenset(self._elements.items()))
        return self._hash
