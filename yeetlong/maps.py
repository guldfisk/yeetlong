from __future__ import annotations

import typing as t

import copy

from collections import OrderedDict


K = t.TypeVar('K')
V = t.TypeVar('V')


class OrderedDefaultDict(OrderedDict, t.Generic[K, V]):
    
    def __init__(self, default_factory = t.Callable[[], V], *args: t.Tuple[K, V], **kwargs: t.Mapping[K, V]):
        OrderedDict.__init__(self, *args, **kwargs)
        self._default_factory = default_factory

    def __getitem__(self, key: K) -> V:
        try:
            return OrderedDict.__getitem__(self, key)
        except KeyError:
            return self.__missing__(key)

    def __missing__(self, key: K) -> V:
        self[key] = value = self._default_factory()
        return value

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
            self.items(),
        )