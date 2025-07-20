"""
Pydantic Version Compatibility Layer

This module provides compatibility functions that work with both
Pydantic V1 (1.10.x) and Pydantic V2 (2.x) to ensure the codebase
works across different Python versions and environments.
"""

import sys
from typing import Any, Dict, Type, TypeVar

try:
    import pydantic
    # Try multiple ways to get version
    if hasattr(pydantic, 'VERSION'):
        PYDANTIC_VERSION = tuple(map(int, pydantic.VERSION.split('.')[:2]))
    elif hasattr(pydantic, '__version__'):
        PYDANTIC_VERSION = tuple(map(int, pydantic.__version__.split('.')[:2]))
    else:
        PYDANTIC_VERSION = (2, 0)  # Default to V2 for modern installations
except ImportError:
    PYDANTIC_VERSION = (2, 0)  # Default to V2

IS_PYDANTIC_V2 = PYDANTIC_VERSION >= (2, 0)

# Import version-specific components
if IS_PYDANTIC_V2:
    from pydantic import BaseModel, Field
    try:
        from pydantic import field_validator
    except ImportError:
        # Fallback for older V2 versions
        from pydantic import validator as field_validator
else:
    from pydantic import BaseModel, Field, validator as field_validator

ModelType = TypeVar('ModelType', bound=BaseModel)


def model_dump_json(model: BaseModel, **kwargs) -> str:
    """
    Export model to JSON string in a version-agnostic way.

    Args:
        model: Pydantic model instance
        **kwargs: Additional arguments (indent, etc.)

    Returns:
        JSON string representation
    """
    if IS_PYDANTIC_V2:
        # For Pydantic V2
        if hasattr(model, 'model_dump_json'):
            return model.model_dump_json(**kwargs)
        else:
            # Fallback
            import json
            return json.dumps(model_dump(model), **kwargs)
    else:
        # For Pydantic V1
        return model.json(**kwargs)


def model_dump(model: BaseModel, **kwargs) -> Dict[str, Any]:
    """
    Export model to dictionary in a version-agnostic way.

    Args:
        model: Pydantic model instance
        **kwargs: Additional arguments

    Returns:
        Dictionary representation
    """
    if IS_PYDANTIC_V2:
        if hasattr(model, 'model_dump'):
            return model.model_dump(**kwargs)
        else:
            # Fallback
            return model.dict(**kwargs)
    else:
        return model.dict(**kwargs)


def model_validate(model_class: Type[ModelType], data: Dict[str, Any]) -> ModelType:
    """
    Create model from dictionary in a version-agnostic way.

    Args:
        model_class: Pydantic model class
        data: Dictionary data

    Returns:
        Model instance
    """
    if IS_PYDANTIC_V2:
        if hasattr(model_class, 'model_validate'):
            return model_class.model_validate(data)
        else:
            # Fallback
            return model_class(**data)
    else:
        return model_class(**data)


def model_validate_json(model_class: Type[ModelType], json_str: str) -> ModelType:
    """
    Create model from JSON string in a version-agnostic way.

    Args:
        model_class: Pydantic model class
        json_str: JSON string

    Returns:
        Model instance
    """
    if IS_PYDANTIC_V2:
        if hasattr(model_class, 'model_validate_json'):
            return model_class.model_validate_json(json_str)
        else:
            # Fallback
            import json
            return model_class(**json.loads(json_str))
    else:
        return model_class.parse_raw(json_str)


def create_validator(field_name: str, check_fields: bool = True):
    """
    Create a field validator that works with both Pydantic versions.

    Args:
        field_name: Name of the field to validate
        check_fields: Whether to check other fields (V1 compatibility)

    Returns:
        Decorator function
    """
    if IS_PYDANTIC_V2:
        try:
            from pydantic import field_validator
            return field_validator(field_name, mode='before')
        except ImportError:
            # Fallback for older V2 versions
            from pydantic import validator
            return validator(field_name, pre=True)
    else:
        from pydantic import validator
        return validator(field_name, always=True, check_fields=check_fields)


# Version info for debugging
def get_compatibility_info() -> Dict[str, Any]:
    """
    Get information about the current Pydantic setup.

    Returns:
        Dictionary with version and compatibility info
    """
    return {
        "pydantic_version": PYDANTIC_VERSION,
        "is_v2": IS_PYDANTIC_V2,
        "python_version": sys.version_info[:3],
        "available_features": {
            "model_dump_json": True,
            "model_validate": True,
            "field_validator": True,
            "config_dict": IS_PYDANTIC_V2
        }
    }


# Export commonly used functions and classes
__all__ = [
    "IS_PYDANTIC_V2",
    "PYDANTIC_VERSION",
    "BaseModel",
    "Field",
    "field_validator",
    "model_dump_json",
    "model_dump",
    "model_validate",
    "model_validate_json",
    "create_validator",
    "get_compatibility_info"
]
