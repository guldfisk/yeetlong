from __future__ import annotations

import typing as t

import operator
import copy
import collections


K = t.TypeVar('K')
V = t.TypeVar('V')


__all__ = [
    'IndexedOrderedDict',
    'OrderedDefaultDict',
    'IndexedOrderedDefaultDict',
]


class IndexedOrderedDict(t.MutableMapping[K, V]):
    __slots__ = ('_list', '_dict')

    def __init__(self, initial: t.Iterable[t.Tuple[K, V]] = ()):
        self._dict = {}
        self._list = []
        self.update(initial)

    def __setitem__(self, key: K, value: V) -> None:
        if key not in self._list:
            self._list.append(key)
        self._dict.__setitem__(key, value)

    def __delitem__(self, key: K) -> None:
        self._dict.__delitem__(key)
        self._list.remove(key)

    def __getitem__(self, key: K) -> V:
        return self._dict.__getitem__(key)

    def keys(self) -> t.AbstractSet[K]:
        return self._dict.keys()

    def values(self) -> t.ValuesView[V]:
        return self._dict.values()

    def items(self) -> t.AbstractSet[t.Tuple[K, V]]:
        return self._dict.items()

    def __len__(self) -> int:
        return len(self._list)

    def __iter__(self):
        return self._list.__iter__()

    def __reversed__(self):
        return self._list.__reversed__()

    def clear(self):
        self._list[:] = []
        self._dict.clear()

    def popitem(self, last=True):
        key = self._list.pop() if last else self._list.pop(0)
        value = self._dict.pop(key)
        return key, value

    def move_to_end(self, key, last=True):
        self._list.remove(key)
        if last:
            self._list.append(key)
        else:
            self._list.insert(0, key)
            
    def get_key_by_index(self, index: int) -> K:
        return self._list[index]
    
    def get_value_by_index(self, index: int) -> V:
        return self._dict[self._list[index]]
    
    def get_index_of_key(self, key: K) -> int:
        return self._list.index(key)

    _marker = object()

    def pop(self, key, default=_marker):
        if key in self:
            result = self[key]
            del self[key]
            return result
        if default is self._marker:
            raise KeyError(key)
        return default

    def setdefault(self, key: K, default: t.Optional[V] = None) -> t.Optional[V]:
        if key in self:
            return self[key]
        self[key] = default
        return default

    def __repr__(self) -> str:
        return '{}({})'.format(
            self.__class__.__name__,
            list(self.items()),
        )

    def __reduce__(self):
        inst_dict = {'_map': self._list, '_dict': self._dict}
        return self.__class__, (), inst_dict or None, None, iter(self.items())

    def copy(self) -> IndexedOrderedDict:
        return self.__class__(self)

    def __eq__(self, other: t.Mapping) -> bool:
        if isinstance(other, collections.OrderedDict) or isinstance(other, IndexedOrderedDict):
            return self._dict.__eq__(other) and all(map(operator.eq, self, other))
        return self._dict.__eq__(other)


class OrderedDefaultDict(t.MutableMapping[K, V]):
    __slots__ = ('_dict', '_default_factory')
    
    def __init__(self, default_factory: t.Callable[[], V], initial: t.Iterable[t.Tuple[K, V]] = ()):
        self._default_factory = default_factory
        self._dict = collections.OrderedDict(initial)

    def __getitem__(self, key: K) -> V:
        try:
            return self._dict.__getitem__(key)
        except KeyError:
            return self.__missing__(key)

    def __missing__(self, key: K) -> V:
        self._dict[key] = value = self._default_factory()
        return value

    def keys(self) -> t.AbstractSet[K]:
        return self._dict.keys()

    def values(self) -> t.ValuesView[V]:
        return self._dict.values()

    def items(self) -> t.AbstractSet[t.Tuple[K, V]]:
        return self._dict.items()

    def __len__(self) -> int:
        return self._dict.__len__()

    def __iter__(self) -> t.Iterator[V]:
        return self._dict.__iter__()

    def __setitem__(self, key: K, value: V) -> None:
        return self._dict.__setitem__(key, value)

    def __delitem__(self, key: K) -> None:
        self._dict.__delitem__(key)

    def __reduce__(self):
        return type(self), self._default_factory, None, None, self.items()

    def __copy__(self):
        return type(self)(self._default_factory, self)

    def __deepcopy__(self, memo) -> OrderedDefaultDict:
        return type(self)(
            self._default_factory,
            copy.deepcopy(self.items())
        )

    def __repr__(self) -> str:
        return '{}({}, {})'.format(
            self.__class__.__name__,
            self._default_factory,
            list(self._dict.items()),
        )


class IndexedOrderedDefaultDict(OrderedDefaultDict):

    def __init__(self, default_factory: t.Callable[[], V], initial: t.Iterable[t.Tuple[K, V]] = ()):
        self._default_factory = default_factory
        self._dict = IndexedOrderedDict(initial)

    def get_key_by_index(self, index: int) -> K:
        return self._dict.get_key_by_index(index)

    def get_value_by_index(self, index: int) -> V:
        return self._dict.get_value_by_index(index)
    
    def get_index_of_key(self, key: K) -> int:
        return self._dict.get_index_of_key(key)
