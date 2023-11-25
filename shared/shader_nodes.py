import bpy
from enum import IntEnum


class SzShaderNodeParameterDisplayType(IntEnum):
    DEFAULT = 0
    RGB = 1
    RGBA = 2
    BOOL = 3
    HIDDEN_IN_UI = 4


class SzShaderNodeParameter(bpy.types.ShaderNode):
    bl_idname = "SOLLUMZ_NT_SHADER_Parameter"
    bl_label = "Parameter"

    num_cols: bpy.props.IntProperty(default=0, min=1, max=4)
    num_rows: bpy.props.IntProperty(default=0, min=1)
    display_type: bpy.props.IntProperty(default=SzShaderNodeParameterDisplayType.DEFAULT)

    def set_display_type(self, display_type: SzShaderNodeParameterDisplayType):
        self.display_type = display_type

    def set_size(self, num_cols: int, num_rows: int):
        assert 0 < num_cols <= 4, "`num_cols` must be between 1 and 4"
        assert num_rows >= 1, "`num_rows` must be greater than 0"

        element_names = ("X", "Y", "Z", "W")
        for i in range(num_cols * num_rows):
            element_i = i % num_cols
            name = element_names[element_i]
            if num_rows == 1:
                ident = name
            else:
                ident = f"{name}_{i / num_cols}"

            self.outputs.new("NodeSocketFloat", name, identifier=ident)

        self.num_cols = num_cols
        self.num_rows = num_rows

    def get(self, i: int | str) -> float:
        return self.outputs[i].default_value

    def set(self, i: int | str, value: float):
        self.outputs[i].default_value = value

    def get_float(self) -> float:
        return self.get(0)

    def set_float(self, value: float):
        self.set(0, value)

    def get_vec2(self) -> tuple[float, float]:
        return self.get(0), self.get(1)

    def set_vec2(self, value: tuple[float, float]):
        self.set(0, value[0])
        self.set(1, value[1])

    def get_vec3(self) -> tuple[float, float, float]:
        return self.get(0), self.get(1), self.get(2)

    def set_vec3(self, value: tuple[float, float, float]):
        self.set(0, value[0])
        self.set(1, value[1])
        self.set(2, value[2])

    def get_vec4(self) -> tuple[float, float, float, float]:
        return self.get(0), self.get(1), self.get(2), self.get(3)

    def set_vec4(self, value: tuple[float, float, float, float]):
        self.set(0, value[0])
        self.set(1, value[1])
        self.set(2, value[2])
        self.set(3, value[3])

    def get_bool(self) -> bool:
        return self.get(0) != 0.0

    def set_bool(self, value: bool):
        self.set(0, 1.0 if value else 0.0)

    as_float: bpy.props.FloatProperty(
        get=get_float, set=set_float
    )
    as_vec2: bpy.props.FloatVectorProperty(
        size=2, subtype="XYZ",
        get=get_vec2, set=set_vec2
    )
    as_vec3: bpy.props.FloatVectorProperty(
        size=3, subtype="XYZ",
        get=get_vec3, set=set_vec3
    )
    as_vec4: bpy.props.FloatVectorProperty(
        size=4, subtype="XYZ",
        get=get_vec4, set=set_vec4
    )
    as_rgb: bpy.props.FloatVectorProperty(
        size=3, subtype="COLOR", min=0.0, max=1.0,
        get=get_vec3, set=set_vec3
    )
    as_rgba: bpy.props.FloatVectorProperty(
        size=4, subtype="COLOR", min=0.0, max=1.0,
        get=get_vec4, set=set_vec4
    )
    as_bool: bpy.props.BoolProperty(
        get=get_bool, set=set_bool
    )

    def draw_buttons(self, context: bpy.types.Context, layout: bpy.types.UILayout):
        self.draw(context, layout, label="", compact=False, force_draw=True)

    def draw(self, context: bpy.types.Context, layout: bpy.types.UILayout, label: str = "", compact: bool = False, force_draw: bool = False):
        if not force_draw and self.display_type == SzShaderNodeParameterDisplayType.HIDDEN_IN_UI.value:
            return

        col = layout.column(align=True)
        col.use_property_split = True
        col.use_property_decorate = False
        match (self.num_cols, self.num_rows, self.display_type):
            case (1, 1, SzShaderNodeParameterDisplayType.BOOL):
                col.prop(self, "as_bool", text=label)
            case (3, 1, SzShaderNodeParameterDisplayType.RGB):
                col.prop(self, "as_rgb", text=label)
            case (4, 1, SzShaderNodeParameterDisplayType.RGBA):
                col.prop(self, "as_rgba", text=label)
            case (1, 1, _):
                col.prop(self, "as_float", text=label)
            case (2, 1, _):
                if compact:
                    row = col.row(align=True)
                    row.prop(self.outputs[0], "default_value", text=label)
                    row.prop(self.outputs[1], "default_value", text="")
                else:
                    col.prop(self, "as_vec2", text=label)
            case (3, 1, _):
                if compact:
                    row = col.row(align=True)
                    row.prop(self.outputs[0], "default_value", text=label)
                    row.prop(self.outputs[1], "default_value", text="", )
                    row.prop(self.outputs[2], "default_value", text="")
                else:
                    col.prop(self, "as_vec3", text=label)
            case (4, 1, _):
                if compact:
                    row = col.row(align=True)
                    row.prop(self.outputs[0], "default_value", text=label)
                    row.prop(self.outputs[1], "default_value", text="")
                    row.prop(self.outputs[2], "default_value", text="")
                    row.prop(self.outputs[3], "default_value", text="")
                else:
                    col.prop(self, "as_vec4", text=label)
            case _:
                for i, o in enumerate(self.outputs):
                    row_label = ""
                    if (i % self.num_cols) == 0:
                        row = col.row(align=True)
                        row_label = str(i // self.num_cols)
                        if i == 0 and label != "":
                            row_label = f"{label} {row_label}"
                        if not compact:
                            row.label(text=row_label)

                    row.prop(o, "default_value", text="" if not compact else row_label)


def register():
    bpy.utils.register_class(SzShaderNodeParameter)


def unregister():
    bpy.utils.unregister_class(SzShaderNodeParameter)
