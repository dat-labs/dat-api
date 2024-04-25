from datetime import datetime
from decimal import Decimal
import enum
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class ModelDict:
    def to_dict(self):
        return {key: value for key, value in self.__dict__.items()
                if not key.startswith('_')}
    
    def _to_dict(self, ):
        return_dct = {}
        for attribute, value in self.__dict__.items():
            if type(value) not in (str, float, int, bool, dict, Decimal) \
                    and value is not None \
                        and not isinstance(value, enum.Enum) \
                            and not isinstance(value, datetime):
                continue
            try:
                return_dct[attribute] = value.name
            except AttributeError:
                if isinstance(value, Decimal):
                    return_dct[attribute] = int(value)
                else:
                    return_dct[attribute] = value
        return return_dct
