from dat_core.pydantic_models.base import EnumWithStr

class CustomModel:

    @classmethod
    def convert_enums_to_str(cls, data):
        """
        Converts all EnumWithStr instances within a dictionary to strings.
        """
        if isinstance(data, EnumWithStr):
            return str(data)
        else:
            return data
