import importlib

class ConnectorSpecificationBuilder:
    @staticmethod
    def get_specification(actor_type: str, module_name: str, actor_name: str):
        try:
            # Import from the module's specs.py file
            module = importlib.import_module(f"verified_{actor_type}s.{module_name}.specs")
            spec_class = getattr(module, f"{actor_name}Specification")
            return spec_class
        except (ImportError, AttributeError) as e:
            raise ValueError(f"Unable to find specification for {actor_name}: {str(e)}")
    
    @staticmethod
    def get_source_class(actor_type: str, module_name: str, actor_name: str):
        try:
            # Import the actor's main source class (assumed to be in destination.py or similar)
            module = importlib.import_module(f"verified_{actor_type}s.{module_name}.{actor_type}")
            source_class = getattr(module, actor_name)
            return source_class
        except (ImportError, AttributeError) as e:
            raise ValueError(f"Unable to find source class for {actor_name}: {str(e)}")
