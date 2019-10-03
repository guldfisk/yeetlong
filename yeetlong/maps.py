from __future__ import annotations

import typing as t

import operator
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


class DefaultMixin(t.Generic[V]):

    def __init__(self, default_factory: t.Callable[[], V]):
        self._default_factory = default_factory

    def __getitem__(self, key: K) -> V:
        try:
            return super().__getitem__(key)
        except KeyError:
            return self.__missing__(key)

    def __missing__(self, key: K) -> V:
        v = self._default_factory()
        super().__setitem__(key, v)
        return v
    
    def __repr__(self) -> str:
        return '{}({}, {})'.format(
            self.__class__.__name__,
            self._default_factory,
            list(self.items()),
        )
    

class OrderedDefaultDict(DefaultMixin, collections.OrderedDict):
    __slots__ = ()

    def __init__(self, default_factory: t.Callable[[], V], initial: t.Iterable[t.Tuple[K, V]] = ()):
        collections.OrderedDict.__init__(self, initial)
        DefaultMixin.__init__(self, default_factory)


class IndexedOrderedDefaultDict(DefaultMixin, IndexedOrderedDict):
    __slots__ = ()

    def __init__(self, default_factory: t.Callable[[], V], initial: t.Iterable[t.Tuple[K, V]] = ()):
        IndexedOrderedDict.__init__(self, initial)
        DefaultMixin.__init__(self, default_factory)
