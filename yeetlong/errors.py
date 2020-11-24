import typing as t


class Errors(object):

    def __init__(self, errors: t.Optional[t.Sequence[str]] = None):
        self._errors = [] if errors is None else errors

    @property
    def errors(self) -> t.Sequence[str]:
        return self._errors

    def __bool__(self) -> bool:
        return not self._errors

    def __iter__(self):
        yield bool(self)
        yield self._errors

    def __getitem__(self, item):
        if item == 0:
            return bool(self)
        if item == 1:
            return self._errors
        raise IndexError()

    def __repr__(self) -> str:
        return '{}({})'.format(
            self.__class__.__name__,
            self._errors,
        )
