from __future__ import annotations

import pkgutil
import sys
import unittest.mock
from dataclasses import dataclass, field, replace
from typing import Any

from .errors import DoNotMockError


@dataclass
class ProtectedFunc:
    """A function that must not be mocked during a test."""

    name: str
    module_path: str
    obj: Any | None = None
    _self_obj: Any | None = field(default=None, repr=False)
    _module_name: str | None = field(default=None, repr=False)

    @classmethod
    def from_arg(cls, func: Any) -> ProtectedFunc:
        """Build from a function object or a dotted string path."""
        if isinstance(func, str):
            parts = func.rsplit(".", 1)
            name = parts[-1] if len(parts) == 2 else func
            mod = parts[0] if len(parts) == 2 else None
            return cls(name=name, module_path=func, _module_name=mod)

        name = getattr(func, "__name__", str(func))
        module = getattr(func, "__module__", None)
        self_obj = getattr(func, "__self__", None)
        full_path = f"{module}.{name}" if module else name
        return cls(name=name, module_path=full_path, obj=func, _self_obj=self_obj, _module_name=module)

    def resolve(self) -> ProtectedFunc:
        """Return a copy with the live function object imported and attached.

        String targets stay unresolved dotted paths until this point so that
        collecting tests never imports application code. A path that cannot
        be resolved raises rather than silently protecting nothing.
        """
        if self.obj is not None:
            return self
        try:
            obj = pkgutil.resolve_name(self.module_path)
        except (ImportError, AttributeError, ValueError) as exc:
            raise DoNotMockError(f"\n@pytest.mark.do_not_mock cannot resolve '{self.module_path}': {exc}\n") from exc
        return replace(self, obj=obj)

    def matches_patch_target(self, target: Any, attribute: str) -> bool:
        """Return True if a patch on *target.attribute* would affect this function.

        The primary check is object identity, which catches the function under
        any name it was imported as. The module-and-name check remains for
        targets without a resolved object.
        """
        if self._self_obj is not None:
            return target is self._self_obj and attribute == self.name
        if self.obj is not None and getattr(target, attribute, None) is self.obj:
            return True
        if self._module_name:
            return target is sys.modules.get(self._module_name) and attribute == self.name
        return False

    def is_mocked_in_namespace(self) -> bool:
        """Return True if this function has been replaced by a Mock in its module."""
        if self.obj is not None and isinstance(self.obj, unittest.mock.NonCallableMock):
            return True
        parts = self.module_path.rsplit(".", 1)
        if len(parts) != 2:
            return False
        mod_path, attr = parts
        mod = sys.modules.get(mod_path)
        if mod is None or not hasattr(mod, attr):
            return False
        return isinstance(getattr(mod, attr), unittest.mock.NonCallableMock)


def validate_no_mocks(protected: list[ProtectedFunc], test_name: str, phase: str) -> None:
    """Raise DoNotMockError if any protected function is currently mocked."""
    for pf in protected:
        if pf.is_mocked_in_namespace():
            raise DoNotMockError(
                f"\nTest '{test_name}' marked '{pf.name}' with @pytest.do_not_mock\n"
                f"but '{pf.module_path}' has been replaced with a Mock ({phase} test execution).\n"
                f"\nPlease remove the patch for '{pf.module_path}'.\n"
            )
