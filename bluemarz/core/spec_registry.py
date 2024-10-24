from abc import ABC, abstractmethod
import json
import os
from pathlib import Path
from typing import Generic, TypeVar

from pydantic import HttpUrl
import urllib.request
from bluemarz.core.models import AssignmentSpec

T = TypeVar("T")


class SpecRegistry(Generic[T], ABC):
    @abstractmethod
    def get_by_id(self, id: str) -> T:
        pass
    @abstractmethod
    def save_by_id(self, id: str, spec: T) -> None:
        pass


__assignment_spec: SpecRegistry[AssignmentSpec] = None


class InMemmoryRegistry(Generic[T], SpecRegistry[T]):
    _registry: dict[str, T]
    
    def __init__(self, registry: dict[str, T] = None):
        if registry is None:
            self._registry = []
        else:
            self._registry = registry

    def get_by_id(self, id: str) -> T:
        return self._registry[id]
    
    def save_by_id(self, id: str, spec: T) -> None:
        self._registry[id] = spec
    
    @classmethod
    def from_file(cls, path :Path) -> "InMemmoryRegistry[T]":
        if not path.is_file:
            raise Exception(f"path {path} not a file")
        
        init_dict = None
        with path.open() as file:
            init_dict = json.load(file)

        if not init_dict or not isinstance(init_dict, dict):
            raise Exception(f"File does not contain valid json")
        
        final_dict: dict[str, T] = {}
        for key in init_dict:
            init_dict[key] = cls.__args__[0](init_dict[key])

        return cls(final_dict)

    @classmethod
    def from_url(cls, path :HttpUrl) -> "InMemmoryRegistry[T]":
        urllib.request.urlretrieve(str(path), "temp.json")
        registry = cls.from_file(Path("temp.json"))
        os.remove("temp.json")
        return registry
    
    
class StaticInMemmoryRegistry(Generic[T], SpecRegistry[T]):
    _registry: dict[str, T]
    
    def __init__(self, registry: dict[str, T]):
        if registry is None:
            self._registry = []
        else:
            self._registry = registry

    def get_by_id(self, id: str) -> T:
        return self._registry[id]
    
    def save_by_id(self, id: str, spec: T) -> None:
        raise Exception("Unsupported operation, StaticInMemmoryRegistry is immutable")
    
    @classmethod
    def from_file(cls, path :Path) -> "StaticInMemmoryRegistry[T]":
        if not path.is_file:
            raise Exception(f"path {path} not a file")
        
        init_dict = None
        with path.open() as file:
            init_dict = json.load(file)

        if not init_dict or not isinstance(init_dict, dict):
            raise Exception(f"File does not contain valid json")
        
        final_dict: dict[str, T] = {}
        for key in init_dict:
            init_dict[key] = cls.__args__[0](init_dict[key])

        if not final_dict:
            raise Exception(f"Cannot create StaticInMemmoryRegistry with empty registry contents")

        return cls(final_dict)

    @classmethod
    def from_url(cls, path :HttpUrl) -> "StaticInMemmoryRegistry[T]":
        urllib.request.urlretrieve(str(path), "temp.json")
        registry = cls.from_file(Path("temp.json"))
        os.remove("temp.json")
        return registry
    

def set_assignment_registry(registry: SpecRegistry[AssignmentSpec]):
   global __assignment_spec 
   __assignment_spec = registry


def get_assignment_by_id(id :str) -> AssignmentSpec:
    if __assignment_spec is None:
        raise Exception("AssignmentSpec registry not set")
    
    return __assignment_spec.get_by_id(id)


def save_assignment(id :str, spec: AssignmentSpec) -> None:
    if __assignment_spec is None:
        raise Exception("AssignmentSpec registry not set")
    
    __assignment_spec.save_by_id(id, spec)

