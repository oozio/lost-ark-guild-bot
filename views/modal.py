from enum import Enum

class Modal(object):
    class Styles(Enum):
        short = 1
        paragraph = 2

    DEFAULT_STYLE = 1
    COMPONENT_TYPE = 4

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

# // this is a modal
# {
#   "title": "My Cool Modal",
#   "custom_id": "cool_modal",
#   "components": [{
#     "type": 1,
#     "components": [{
#       "type": 4,
#       "custom_id": "name",
#       "label": "Name",
#       "style": 1,
#       "min_length": 1,
#       "max_length": 4000,
#       "placeholder": "John",
#       "required": true
#     }]
#   }]
# }