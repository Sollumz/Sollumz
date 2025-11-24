import os
import sys
import textwrap
from pathlib import Path
from typing import NamedTuple

import bpy
from bpy.props import (
    BoolVectorProperty,
)
from bpy.types import (
    AddonPreferences,
    Operator,
    Panel,
    UILayout,
)


class Dependency(NamedTuple):
    name: str
    ui_label: str
    version: str
    required: bool
    supported: bool
    license_url: str
    description: str
    safe_to_reload: bool
    extra_index_url: str


DEPENDENCIES = (
    Dependency(
        "szio",
        "szio",
        "1.0.0",
        True,
        True,
        "",
        "Core functionality for import/export of asset files.",
        True,
        "",
    ),
    Dependency(
        "pymateria",
        "PyMateria",
        "0.1.0",
        False,
        sys.platform == "win32",
        "https://static.cfx.re/PyMateria-License-Agreement.pdf",
        "Allows direct binary assets import/export and automatic vehicle shattermap generation using the Materia library.",
        False,
        "https://static.cfx.re/whl/",
    ),
)

DEPENDENCIES_REQUIRED = tuple(d for d in DEPENDENCIES if d.required)
DEPENDENCIES_OPTIONAL = tuple(d for d in DEPENDENCIES if not d.required)


def check_module(name: str, version: str) -> bool:
    import importlib.metadata
    import importlib.util

    return importlib.util.find_spec(name) is not None and importlib.metadata.version(name) == version


def dependencies_available_state() -> dict[str, bool]:
    return {dep.name: dep.supported and check_module(dep.name, dep.version) for dep in DEPENDENCIES}


def site_packages_path() -> Path:
    from .known_paths import data_directory_path

    ver_major, ver_minor = sys.version_info[:2]
    return Path(data_directory_path()) / "lib" / f"python{ver_major}.{ver_minor}" / "site-packages"


def offline_index_path() -> Path:
    return Path(__file__).parent / "offline_index"


def has_online_access() -> bool:
    return bpy.app.version < (4, 2, 0) or bpy.app.online_access


def has_required_dependencies() -> bool:
    return IS_SZIO_AVAILABLE


def build_install_dependencies_command(
    dependencies: list[Dependency],
    optional_dependencies_to_install: set[str],
    site_packages: str,
    offline_index: str | None,
) -> list[str]:
    has_offline_index = bool(offline_index)

    packages = [
        f"{dep.name}=={dep.version}"
        for dep in dependencies
        if dep.supported and (dep.required or dep.name in optional_dependencies_to_install)
    ]
    offline_index_args = (
        [
            "--no-index",
            "--find-links",
            offline_index,
        ]
        if has_offline_index
        else []
    )
    extra_index_args = (
        [
            arg
            for dep in dependencies
            if dep.supported and dep.extra_index_url
            for arg in ("--extra-index-url", str(dep.extra_index_url))
        ]
        if not has_offline_index
        else []
    )

    cmd = (
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "-v",
            "--target",
            site_packages,
            "--force-reinstall",
            "--no-deps",
        ]
        + offline_index_args
        + extra_index_args
        + packages
    )

    return cmd


def install_dependencies(online_access_override: bool = False, optional_dependencies_to_install: set[str] = set()):
    import subprocess

    site_packages = site_packages_path()
    offline_index = offline_index_path()
    has_offline_index = offline_index.is_dir()

    if not online_access_override and not has_online_access() and not has_offline_index:
        return False

    cmd = build_install_dependencies_command(
        DEPENDENCIES,
        optional_dependencies_to_install,
        str(site_packages),
        str(offline_index) if has_offline_index else None,
    )
    print(f"{cmd=}")
    retcode = subprocess.call(cmd)
    return retcode == 0


def mount_dependencies():
    def _add_site_packages():
        site_packages = site_packages_path()
        if site_packages.is_dir():
            site_packages = str(site_packages)
            if site_packages not in sys.path:
                sys.path.append(site_packages)

    _add_site_packages()
    state = dependencies_available_state()

    if os.getenv("CI"):
        # On CI, force install the dependencies
        any_missing_dependencies = any(not available for available in state.values())
        if any_missing_dependencies:
            unmount_dependencies()
            install_dependencies(online_access_override=True, optional_dependencies_to_install={"pymateria"})
            _add_site_packages()
            state = dependencies_available_state()

    global IS_SZIO_AVAILABLE, IS_SZIO_NATIVE_AVAILABLE, PYMATERIA_REQUIRED_MSG
    IS_SZIO_AVAILABLE = state.get("szio", False)
    IS_SZIO_NATIVE_AVAILABLE = IS_SZIO_AVAILABLE and state.get("pymateria", False)
    PYMATERIA_REQUIRED_MSG = (
        ""
        if IS_SZIO_NATIVE_AVAILABLE
        else PYMATERIA_UNAVAILABLE_MSG
        if IS_SZIO_NATIVE_SUPPORTED
        else PYMATERIA_UNSUPPORTED_MSG
    )

    if not has_required_dependencies():

        def _ask_to_install_dependencies():
            bpy.ops.sollumz.install_dependencies("INVOKE_DEFAULT")

        bpy.app.timers.register(_ask_to_install_dependencies, first_interval=0.5, persistent=True)


def unmount_dependencies():
    site_packages = str(site_packages_path())
    if site_packages in sys.path:
        sys.path.remove(site_packages)

    module_names = list(sys.modules.keys())
    for dep in DEPENDENCIES:
        if not dep.safe_to_reload:
            continue

        dep_module_prefix = f"{dep.name}."
        for name in module_names:
            if name == dep.name or name.startswith(dep_module_prefix):
                del sys.modules[name]


IS_SZIO_AVAILABLE = False
IS_SZIO_NATIVE_AVAILABLE = False
IS_SZIO_NATIVE_SUPPORTED = DEPENDENCIES_OPTIONAL[0].supported  # pymateria

PYMATERIA_UNAVAILABLE_MSG = "Binary resource formats require PyMateria which is not available."
PYMATERIA_UNSUPPORTED_MSG = "Binary resource formats require PyMateria which is not supported on this platform."
PYMATERIA_REQUIRED_MSG = ""

OFFLINE_MSG = (
    'Internet access is required to download the missing dependencies but it is currently disabled in "System" '
    'preferences. Clicking "Install" will override this preference and proceed with the installation.'
)


_minimal_classes = []


def register_minimal():
    """When missing required dependencies, only this will be registered instead of the whole add-on."""

    if has_required_dependencies():
        return

    # Defines these classes here as in regular usage these won't be used at all, more hidden this way.
    class SOLLUMZ_OT_install_dependencies(Operator):
        bl_idname = "sollumz.install_dependencies"
        bl_label = "Sollumz: Install Dependencies?"
        bl_description = "Install dependencies"

        optional_dependencies: BoolVectorProperty(
            size=len(DEPENDENCIES_OPTIONAL), default=(True,) * len(DEPENDENCIES_OPTIONAL)
        )

        def execute(self, context):
            optional_dependencies_to_install = {
                DEPENDENCIES_OPTIONAL[i].name for i, enabled in enumerate(self.optional_dependencies) if enabled
            }

            if install_dependencies(
                online_access_override=True, optional_dependencies_to_install=optional_dependencies_to_install
            ):
                self.report({"INFO"}, "Successfully installed dependencies. Reloading add-ons...")
                bpy.ops.script.reload()
                return {"FINISHED"}
            else:
                self.report({"ERROR"}, "Failed to install dependencies.")
                return {"CANCELLED"}

        def invoke(self, context: bpy.types.Context, event):
            if bpy.app.version >= (4, 1, 0):
                return context.window_manager.invoke_props_dialog(
                    self,
                    width=450,
                    title="Sollumz: Install Dependencies?",
                    confirm_text="Install",
                )
            else:
                return context.window_manager.invoke_props_dialog(self, width=450)

        def draw(self, context):
            layout = self.layout
            main_col = layout.column()

            _draw_wrapped_text(
                context,
                main_col,
                "These dependencies are needed for Sollumz to work correctly.",
                width=550,
                width_percent=1.0,
                dim=False,
            )

            col = main_col.column()
            col.label(text="Required:")
            for dep in DEPENDENCIES_REQUIRED:
                col.label(text=f"{dep.ui_label}  {dep.version}", icon="DOT")
                _draw_wrapped_text(
                    context,
                    col,
                    dep.description,
                    width=400,
                    width_percent=1.0,
                    dim=False,
                    icon="BLANK1",
                    char_pixels=6,
                )

            col = main_col.column()
            col.label(text="Optional:")
            for i, dep in enumerate(DEPENDENCIES_OPTIONAL):
                row = col.row()
                row.alignment = "LEFT"
                subrow = row.row()
                subrow.alignment = "LEFT"
                subrow.enabled = dep.supported
                subrow.prop(self, "optional_dependencies", index=i, text=f"   {dep.ui_label}  {dep.version}")
                subrow = row.row()
                subrow.alignment = "LEFT"
                subrow.emboss = "PULLDOWN_MENU"
                subrow.operator("wm.url_open", text="License", icon="URL").url = dep.license_url

                if not dep.supported:
                    _draw_wrapped_text(
                        context,
                        col,
                        f"{dep} is not supported on this platform.",
                        width=400,
                        width_percent=1.0,
                        dim=False,
                        icon="ERROR",
                        char_pixels=6,
                    )

                _draw_wrapped_text(
                    context,
                    col,
                    dep.description,
                    width=400,
                    width_percent=1.0,
                    dim=False,
                    icon="BLANK1",
                    char_pixels=6,
                )

            if not has_online_access():
                main_col.separator()
                main_col.separator()
                main_col.separator()
                _draw_wrapped_text(
                    context, main_col, OFFLINE_MSG, width=450, width_percent=1.0, dim=False, icon="ERROR", char_pixels=6
                )

    class SOLLUMZ_PT_deps_minimal(Panel):
        bl_label = "Missing Dependencies"
        bl_idname = "SOLLUMZ_PT_deps_minimal"
        bl_category = "Sollumz Tools"
        bl_space_type = "VIEW_3D"
        bl_region_type = "UI"
        bl_options = set()
        bl_order = 0

        def draw_header(self, context):
            self.layout.label(text="", icon="ERROR")

        def draw(self, context):
            layout = self.layout
            layout.operator(SOLLUMZ_OT_install_dependencies.bl_idname, text="Install Dependencies")

    class SollumzDepsMinimalAddonPreferences(AddonPreferences):
        bl_idname = __package__

        def draw(self, context):
            layout = self.layout

            # Based on CenterAlignMixIn from Blender's scripts/startup/bl_ui/space_userpref.py
            width = context.region.width
            ui_scale = context.preferences.system.ui_scale
            # No horizontal margin if region is rather small.
            is_wide = width > (550 * ui_scale)

            layout.use_property_split = True
            layout.use_property_decorate = False  # No animation.

            row = layout.row()
            if is_wide:
                row.label()  # Needed so col below is centered.

            col = row.column()
            col.ui_units_x = 95

            self._draw_install_dependencies(context, layout)

            if is_wide:
                row.label()  # Needed so col above is centered.

        def _draw_install_dependencies(self, context, layout: UILayout):
            row = layout.row()
            row.label(text="Missing dependencies", icon="ERROR")
            row.operator(SOLLUMZ_OT_install_dependencies.bl_idname, text="Install")

    def _draw_wrapped_text(
        context,
        layout: UILayout,
        text: str,
        width_percent: float = 0.99,
        dim: bool = True,
        width: int | None = None,
        icon: str | None = None,
        char_pixels: int = 7,
    ):
        chars = int((width or context.region.width) * width_percent / char_pixels)
        col = layout.column()
        col.active = False if dim else True
        col.scale_y = 0.65
        has_icon = bool(icon)
        icon = icon or "NONE"
        for text_line in text.splitlines():
            first_indent = len(text_line) - len(text_line.lstrip(" "))
            wrapper = textwrap.TextWrapper(width=chars, subsequent_indent=" " * first_indent)
            for wrapped_text_line in wrapper.wrap(text=text_line):
                col.label(text=wrapped_text_line, icon=icon)
                if has_icon:
                    icon = "BLANK1"

    _minimal_classes.extend(
        [
            SollumzDepsMinimalAddonPreferences,
            SOLLUMZ_OT_install_dependencies,
            SOLLUMZ_PT_deps_minimal,
        ]
    )

    for cls in _minimal_classes:
        bpy.utils.register_class(cls)


def unregister_minimal():
    for cls in reversed(_minimal_classes):
        bpy.utils.unregister_class(cls)
