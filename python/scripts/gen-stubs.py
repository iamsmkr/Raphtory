#!/usr/bin/env python3

import inspect
import textwrap
from importlib import import_module
from pathlib import Path
from types import (
    BuiltinFunctionType,
    BuiltinMethodType,
    GetSetDescriptorType,
    MethodDescriptorType,
    ModuleType,
)
from typing import List, Optional, Tuple, Union

TARGET_MODULES = ["raphtory", "builtins"]
TAB = " " * 4

MethodTypes = (BuiltinMethodType, MethodDescriptorType)


comment = """###############################################################################
#                                                                             #
#                      AUTOGENERATED TYPE STUB FILE                           #
#                                                                             #
#    This file was automatically generated. Do not modify it directly.        #
#    Any changes made here may be lost when the file is regenerated.          #
#                                                                             #
###############################################################################\n"""


def clean_signature(sig: str, is_method: bool = False) -> Tuple[str, Optional[str]]:
    sig = sig.replace("$self", "self")
    sig = sig.replace("$cls", "cls")

    decorator = None
    if is_method:
        decorator = "@staticmethod"
        if "cls" in sig:
            decorator = "@classmethod"
        if "self" in sig:
            decorator = None

    return sig, decorator


def insert_self(signature: str) -> str:
    # Remove the class name if present
    params = signature.strip("()")

    if params == "":
        new_params = "self"
    else:
        new_params = f"self, {params}"

    return f"({new_params})"


def from_raphtory(obj) -> bool:
    module = inspect.getmodule(obj)
    if module:
        return any(module.__name__.startswith(target) for target in TARGET_MODULES)
    return False


def format_docstring(docstr: Optional[str], tab: str, ellipsis: bool) -> str:
    if docstr:
        if "\n" in docstr:
            return f'{tab}"""\n{textwrap.indent(docstr, tab)}\n{tab}"""\n'
        else:
            return f'{tab}"""{docstr}"""\n'
    else:
        return f"{tab}...\n" if ellipsis else ""


def gen_fn(
    function: Union[BuiltinFunctionType, BuiltinMethodType, MethodDescriptorType],
    is_method: bool = False,
    signature_overwrite: Optional[str] = None,
) -> str:
    init_tab = TAB if is_method else ""
    fn_tab = TAB * 2 if is_method else TAB
    docstr = format_docstring(function.__doc__, tab=fn_tab, ellipsis=True)
    signature, decorator = clean_signature(
        signature_overwrite or function.__text_signature__,  # type: ignore
        is_method,
    )

    fn_str = f"{init_tab}def {function.__name__}{signature}:\n{docstr}"

    return f"{init_tab}{decorator}\n{fn_str}" if decorator else fn_str


def gen_property(prop: GetSetDescriptorType) -> str:
    prop_tab = TAB * 2
    docstr = format_docstring(prop.__doc__, tab=prop_tab, ellipsis=True)

    return f"{TAB}@property\n{TAB}def {prop.__name__}(self):\n{docstr}"


def gen_class(cls: type) -> str:
    contents = [getattr(cls, function) for function in dir(cls)]
    entities: list[str] = []

    for entity in contents:
        if not hasattr(entity, "__name__"):
            continue

        if entity.__name__ == "__init__":
            # Get __init__ signature from class info
            signature = insert_self(cls.__text_signature__ or "()")
            entities.append(
                gen_fn(entity, is_method=True, signature_overwrite=signature)
            )
        elif not entity.__name__.startswith("__"):
            if isinstance(entity, MethodTypes):
                entities.append(gen_fn(entity, is_method=True))
            elif isinstance(entity, GetSetDescriptorType):
                entities.append(gen_property(entity))

    docstr = format_docstring(cls.__doc__, tab=TAB, ellipsis=not entities)
    str_entities = "\n".join(entities)

    return f"class {cls.__name__}:\n{docstr}\n{str_entities}"


def gen_module(module: ModuleType, base: bool = False) -> None:
    objs = [getattr(module, obj) for obj in dir(module)]

    stubs: List[str] = []
    modules: List[ModuleType] = []

    for obj in objs:
        if isinstance(obj, type) and from_raphtory(obj):
            stubs.append(gen_class(obj))
        elif isinstance(obj, BuiltinFunctionType):
            stubs.append(gen_fn(obj))
        elif isinstance(obj, ModuleType) and obj.__loader__ is None:
            modules.append(obj)

    stub_file = "\n".join([comment, *sorted(stubs)])

    if base:
        path = Path(".", "python", "raphtory", "__init__.pyi")
    else:
        path = Path(".", "python", "raphtory", module.__name__, "__init__.pyi")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(stub_file)

    for module in modules:
        gen_module(module)

    return


if __name__ == "__main__":
    raphtory = import_module("raphtory")
    gen_module(raphtory, base=True)