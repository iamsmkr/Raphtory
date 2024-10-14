#!/usr/bin/env python3

import inspect
import logging
import textwrap
import types
from importlib import import_module
from pathlib import Path
from types import (
    BuiltinFunctionType,
    BuiltinMethodType,
    GetSetDescriptorType,
    MethodDescriptorType,
    ModuleType,
)
from typing import *
from raphtory import *
from raphtory.graphql import *
from raphtory.typing import *
from docstring_parser import parse, DocstringStyle, DocstringParam, ParseError
from datetime import datetime
from pandas import DataFrame

logger = logging.getLogger(__name__)
fn_logger = logger

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

imports = """
from typing import *
from raphtory import *
from raphtory.vectors import *
from raphtory.graphql import *
from raphtory.typing import *
from datetime import datetime
from pandas import DataFrame
"""


def format_type(obj) -> str:
    if isinstance(obj, type):
        return obj.__qualname__
    if obj is ...:
        return "..."
    if isinstance(obj, types.FunctionType):
        return obj.__name__
    if isinstance(obj, tuple):
        # Special case for `repr` of types with `ParamSpec`:
        return "[" + ", ".join(format_type(t) for t in obj) + "]"
    return repr(obj)


def format_param(param: inspect.Parameter) -> str:
    if param.kind == param.VAR_KEYWORD:
        name = f"**{param.name}"
    elif param.kind == param.VAR_POSITIONAL:
        name = f"*{param.name}"
    else:
        name = param.name
    if param.annotation is not param.empty:
        annotation = param.annotation
        if not isinstance(annotation, str):
            annotation = format_type(annotation)
        if param.default is not param.empty:
            return f"{name}: {annotation} = {param.default}"
        else:
            return f"{name}: {annotation}"
    else:
        if param.default is param.empty:
            return name
        else:
            return f"{name}={param.default}"


def format_signature(sig: inspect.Signature) -> str:
    sig_str = (
        "(" + ", ".join(format_param(param) for param in sig.parameters.values()) + ")"
    )
    if sig.return_annotation is not sig.empty:
        sig_str += f" -> {sig.return_annotation}"
    return sig_str


def same_default(doc_default: Optional[str], param_default: Any) -> bool:
    if doc_default is None:
        return param_default is None
    else:
        doc_val = eval(doc_default)
        if doc_val is None:
            return param_default is None
        return doc_val == param_default


def clean_parameter(
    param: inspect.Parameter, type_annotations: dict[str, dict[str, Any]]
):
    annotations = {}
    if param.default is not inspect.Parameter.empty:
        annotations["default"] = format_type(param.default)

    if param.name in type_annotations:
        annotations["annotation"] = type_annotations[param.name]["annotation"]
        if "default" in type_annotations[param.name]:
            default_from_docs = type_annotations[param.name]["default"]
            if param.default is not param.empty and param.default is not ...:
                if not same_default(default_from_docs, param.default):
                    fn_logger.warning(
                        f"mismatched default value: docs={repr(default_from_docs)}, signature={param.default}"
                    )
            else:
                annotations["default"] = default_from_docs
    return param.replace(**annotations)


def clean_signature(
    sig: inspect.Signature,
    is_method: bool,
    type_annotations: dict[str, dict[str, Any]],
    return_type: Optional[str] = None,
) -> Tuple[str, Optional[str]]:
    decorator = None
    if is_method:
        decorator = "@staticmethod"
        if "cls" in sig.parameters:
            decorator = "@classmethod"
        if "self" in sig.parameters:
            decorator = None

    new_params = [clean_parameter(p, type_annotations) for p in sig.parameters.values()]
    sig = sig.replace(parameters=new_params)
    if return_type is not None:
        sig = sig.replace(return_annotation=return_type)
    return format_signature(sig), decorator


def insert_self(signature: inspect.Signature) -> inspect.Signature:
    self_param = inspect.Parameter("self", kind=inspect.Parameter.POSITIONAL_OR_KEYWORD)
    return signature.replace(parameters=[self_param, *signature.parameters.values()])


def cls_signature(cls: type) -> inspect.Signature:
    try:
        cls_signature = inspect.signature(cls)
    except ValueError:
        cls_signature = inspect.Signature()
    return cls_signature


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


def extract_param_annotation(param: DocstringParam) -> dict:
    res = {}
    if param.type_name is None:
        res["annotation"] = Any
    else:
        type_val = param.type_name
        try:
            eval(type_val)
        except Exception as e:
            raise ParseError(f"Invalid type name {type_val}: {e}")

        if param.is_optional:
            type_val = f"Optional[{type_val}]"
        res["annotation"] = type_val
    if param.default is not None or param.is_optional:
        if param.default is not None:
            try:
                eval(param.default)
            except Exception as e:
                raise ParseError(f"Invalid default value {param.default}: {e}")
        res["default"] = param.default
    return res


def extract_types(obj) -> (dict[str, dict], Optional[str]):
    """
    Extract types from documentation
    """
    try:
        docstr = obj.__doc__
        if docstr is not None:
            parse_result = parse(docstr, DocstringStyle.GOOGLE)
            type_annotations = {
                param.arg_name: extract_param_annotation(param)
                for param in parse_result.params
            }
            if parse_result.returns is not None:
                return_type = parse_result.returns.type_name
            else:
                return_type = None
            return type_annotations, return_type
        else:
            return dict(), None
    except Exception as e:
        fn_logger.error(f"failed to parse docstring: {e}")
        return dict(), None


def gen_fn(
    function: Union[BuiltinFunctionType, BuiltinMethodType, MethodDescriptorType],
    is_method: bool = False,
    signature_overwrite: Optional[inspect.Signature] = None,
) -> str:
    global fn_logger
    fn_logger = logging.getLogger(repr(function))
    init_tab = TAB if is_method else ""
    fn_tab = TAB * 2 if is_method else TAB
    type_annotations, return_type = extract_types(function)
    docstr = format_docstring(function.__doc__, tab=fn_tab, ellipsis=True)
    signature = signature_overwrite or inspect.signature(function)
    signature, decorator = clean_signature(
        signature,  # type: ignore
        is_method,
        type_annotations,
        return_type,
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
            signature = insert_self(cls_signature(cls))
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
    logging.info("starting")
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

    stub_file = "\n".join([comment, imports, *sorted(stubs)])

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
