from enum import Enum


class Button(object):
    class Styles(Enum):
        blue = 1
        grey = 2
        green = 3
        red = 4
        url = 5

    DEFAULT_STYLE = 1
    COMPONENT_TYPE = 2

    def __init__(self, custom_id, **kwargs) -> None:
        # type is the same for all buttons
        self.type = self.COMPONENT_TYPE

        # mandatory fields
        self.custom_id = custom_id

        # optional fields with defaults
        self.label = kwargs.pop("label", self.custom_id)
        self.style = kwargs.pop("style", self.DEFAULT_STYLE)

        # add other fields if specified
        for k, v in kwargs.items():
            self.__dict__[k] = v
