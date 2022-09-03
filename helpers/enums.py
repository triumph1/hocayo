from enum import Enum


class ChoiceMixin:
    @classmethod
    def choices(cls):
        # noinspection PyTypeChecker
        return [(e.value, e.label) for e in cls]

    @classmethod
    def values(cls):
        # noinspection PyTypeChecker
        return {e.value for e in cls}


class ValidValueMixin:
    @classmethod
    def valid_value(cls, value):
        try:
            cls(value)
            return True
        except ValueError:
            return False


class StrLabelPairEnum(str, ChoiceMixin, ValidValueMixin, Enum):
    # noinspection PyInitNewSignature
    def __new__(cls, value, label):
        # noinspection PyArgumentList
        self = str.__new__(cls, value)
        self._value_ = value
        self.label = label
        return self


class StrCodeEnum(str, ChoiceMixin, ValidValueMixin, Enum):
    # noinspection PyInitNewSignature
    def __new__(cls, code):
        # noinspection PyArgumentList
        self = str.__new__(cls, code)
        self._value_ = code
        self.label = code
        return self
