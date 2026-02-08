import os
import sys
import textwrap
from collections.abc import Sequence
from enum import Enum, auto
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
    required: bool
    supported: bool
    license_url: str
    description: str
    safe_to_reload: bool
    extra_index_url: str
    version: str
    hashes: tuple[str, ...]


DEPENDENCIES = (
    Dependency(
        "szio",
        "szio",
        True,
        True,
        "",
        "Core functionality for import/export of asset files.",
        True,
        "",
        "1.1.0",
        ("ee6fd4300e48c2ce7b70f569878c615e1f642974787006ebafe40a4f3823a2b2",),
    ),
    Dependency(
        "pymateria",
        "PyMateria",
        False,
        sys.platform == "win32",
        "https://static.cfx.re/PyMateria-License-Agreement.pdf",
        "Allows direct binary assets import/export and automatic vehicle shattermap generation using the Materia library.",
        False,
        "https://static.cfx.re/whl/",
        "0.1.1",
        (
            {
                # win amd64
                (3, 10): "830867304a8986d89cfe4dc49f26c8e014f2c2558dd4e208ba3247588cf6ba16",
                (3, 11): "c204fafc411dfd85992565c8fe1c16af0ee4e7af47620e8403e25d5103103795",
                (3, 12): "24bfd244b95e2fa519116b62dcb1f49387e67da8032c1c9934769956d19f4135",
                (3, 13): "232052dd8c6942fa8a96af8bbaa5133708640e6008035ae3a32be285d52f297d",
                (3, 14): "91d384a543521089b0f4abb214e64b1839ef6afbedfa6574ee90be826944dbad",
            }.get(sys.version_info[:2], "unknown"),
        ),
    ),
)

DEPENDENCIES_REQUIRED = tuple(d for d in DEPENDENCIES if d.required)
DEPENDENCIES_OPTIONAL = tuple(d for d in DEPENDENCIES if not d.required)


class DependencyState(Enum):
    UNINSTALLED = auto()
    INSTALLED = auto()
    INSTALLED_OUTDATED = auto()


def get_module_version(name: str) -> str | None:
    import importlib.metadata

    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def check_module(name: str, version: str) -> DependencyState:
    import importlib.util

    if importlib.util.find_spec(name) is not None:
        if get_module_version(name) != version:
            return DependencyState.INSTALLED_OUTDATED
        return DependencyState.INSTALLED

    return DependencyState.UNINSTALLED


def dependencies_available_state() -> dict[str, DependencyState]:
    return {
        dep.name: check_module(dep.name, dep.version) if dep.supported else DependencyState.UNINSTALLED
        for dep in DEPENDENCIES
    }


def site_packages_path() -> Path:
    from .known_paths import data_directory_path

    ver_major, ver_minor = sys.version_info[:2]
    return Path(data_directory_path()) / "lib" / f"python{ver_major}.{ver_minor}" / "site-packages"


def requirements_path() -> Path:
    from .known_paths import data_directory_path

    data_dir = Path(data_directory_path())
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / "requirements.txt"


def offline_index_path() -> Path:
    return Path(__file__).parent / "offline_index"


def has_online_access() -> bool:
    return bpy.app.version < (4, 2, 0) or bpy.app.online_access


_needs_restart = False


def has_required_dependencies() -> bool:
    return (
        not _needs_restart
        and IS_SZIO_AVAILABLE
        and all(s != DependencyState.INSTALLED_OUTDATED for s in dependencies_available_state().values())
    )


def generate_requirements_file_contents(
    dependencies: Sequence[Dependency],
    offline_index: str | None,
) -> str:
    r = ""
    if offline_index:
        r += "--no-index\n"
        r += f"--find-links {offline_index}\n"
    else:
        for dep in dependencies:
            if not dep.extra_index_url:
                continue

            r += f"--extra-index-url {dep.extra_index_url}\n"

    for dep in dependencies:
        assert dep.name
        assert dep.version
        assert dep.hashes

        r += f"{dep.name}=={dep.version} "
        r += " ".join(f"--hash=sha256:{h}" for h in dep.hashes)
        r += "\n"

    return r


def filter_dependencies_to_install(
    dependencies: Sequence[Dependency],
    optional_dependencies_to_install: set[str],
) -> list[Dependency]:
    return [d for d in dependencies if d.supported and (d.required or d.name in optional_dependencies_to_install)]


def build_install_dependencies_command(
    requirements_file: str,
    site_packages: str,
) -> list[str]:
    return [
        sys.executable,
        "-m",
        "pip",
        "install",
        "-v",
        "--target",
        site_packages,
        "--no-deps",
        "--require-hashes",
        "-r",
        requirements_file,
    ]


def install_dependencies(online_access_override: bool = False, optional_dependencies_to_install: set[str] = set()):
    import subprocess

    site_packages = site_packages_path()
    offline_index = offline_index_path()
    has_offline_index = offline_index.is_dir()

    if not online_access_override and not has_online_access() and not has_offline_index:
        return False

    if site_packages.is_dir():
        # Rename existing site-packages instead of directly delete it because .pyd files may still be in use and
        # wouldn't be possible to delete them
        site_packages_old = site_packages.with_name("site-packages.old")
        if site_packages_old.is_dir():
            import shutil

            shutil.rmtree(site_packages_old)

        site_packages.rename(site_packages_old)

    dependencies_to_install = filter_dependencies_to_install(DEPENDENCIES, optional_dependencies_to_install)
    requirements_contents = generate_requirements_file_contents(
        dependencies_to_install, str(offline_index) if has_offline_index else None
    )
    requirements_file = requirements_path()
    requirements_file.write_text(requirements_contents)
    cmd = build_install_dependencies_command(
        str(requirements_file),
        str(site_packages),
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
        any_missing_dependencies = any(s != DependencyState.INSTALLED for s in state.values())
        if any_missing_dependencies:
            unmount_dependencies()
            install_dependencies(online_access_override=True, optional_dependencies_to_install={"pymateria"})
            _add_site_packages()
            state = dependencies_available_state()

    global IS_SZIO_AVAILABLE, IS_SZIO_NATIVE_AVAILABLE, PYMATERIA_REQUIRED_MSG
    IS_SZIO_AVAILABLE = state.get("szio", DependencyState.UNINSTALLED) == DependencyState.INSTALLED
    IS_SZIO_NATIVE_AVAILABLE = (
        IS_SZIO_AVAILABLE and state.get("pymateria", DependencyState.UNINSTALLED) == DependencyState.INSTALLED
    )
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


def reload_dependencies():
    module_names = list(sys.modules.keys())
    for dep in DEPENDENCIES:
        if not dep.safe_to_reload:
            continue

        dep_module_prefix = f"{dep.name}."
        for name in module_names:
            if name == dep.name or name.startswith(dep_module_prefix):
                del sys.modules[name]


def unmount_dependencies():
    site_packages = str(site_packages_path())
    if site_packages in sys.path:
        sys.path.remove(site_packages)

    reload_dependencies()


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
            state = dependencies_available_state()
            should_restart = any(
                (not dep.safe_to_reload and state[dep.name] == DependencyState.INSTALLED_OUTDATED)
                for dep in DEPENDENCIES_OPTIONAL
            )

            if install_dependencies(
                online_access_override=True, optional_dependencies_to_install=optional_dependencies_to_install
            ):
                global _needs_restart
                _needs_restart = should_restart
                if _needs_restart:
                    self.report({"INFO"}, "Successfully installed dependencies. Please, restart Blender.")
                else:
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

            state = dependencies_available_state()

            def _is_outdated(dep: Dependency) -> bool:
                return state.get(dep.name, DependencyState.UNINSTALLED) == DependencyState.INSTALLED_OUTDATED

            col = main_col.column()
            col.label(text="Required:")
            for dep in DEPENDENCIES_REQUIRED:
                label = f"{dep.ui_label}  {dep.version}"
                if _is_outdated(dep) and (installed_version := get_module_version(dep.name)):
                    label += f"  (installed {installed_version})"

                col.label(text=label, icon="DOT")
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
                label = f"   {dep.ui_label}  {dep.version}"
                if _is_outdated(dep) and (installed_version := get_module_version(dep.name)):
                    label += f"  (installed {installed_version})"

                row = col.row()
                row.alignment = "LEFT"
                subrow = row.row()
                subrow.alignment = "LEFT"
                subrow.enabled = dep.supported
                subrow.prop(self, "optional_dependencies", index=i, text=label)
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
            if _needs_restart:
                layout.label(text="Dependencies upgraded. Restart Blender.")
            else:
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
            if _needs_restart:
                row.label(text="Dependencies upgraded. Restart Blender.")
            else:
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
