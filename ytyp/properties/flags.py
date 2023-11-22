import bpy
from ...sollumz_properties import FlagPropertyGroup


class RoomFlags(FlagPropertyGroup, bpy.types.PropertyGroup):
    size = 10

    flag1: bpy.props.BoolProperty(
        name="Freeze Vehicles", update=FlagPropertyGroup.update_flag)
    flag2: bpy.props.BoolProperty(
        name="Freeze Peds", update=FlagPropertyGroup.update_flag)
    flag3: bpy.props.BoolProperty(
        name="No Directional Light", update=FlagPropertyGroup.update_flag)
    flag4: bpy.props.BoolProperty(
        name="No Exterior Lights", update=FlagPropertyGroup.update_flag)
    flag5: bpy.props.BoolProperty(
        name="Force Freeze", update=FlagPropertyGroup.update_flag)
    flag6: bpy.props.BoolProperty(
        name="Reduce Cars", update=FlagPropertyGroup.update_flag)
    flag7: bpy.props.BoolProperty(
        name="Reduce Peds", update=FlagPropertyGroup.update_flag)
    flag8: bpy.props.BoolProperty(
        name="Force Directional Light On", update=FlagPropertyGroup.update_flag)
    flag9: bpy.props.BoolProperty(
        name="Dont Render Exterior", update=FlagPropertyGroup.update_flag)
    flag10: bpy.props.BoolProperty(
        name="Mirror Potentially Visible", update=FlagPropertyGroup.update_flag)


class PortalFlags(FlagPropertyGroup, bpy.types.PropertyGroup):
    size = 14

    flag1: bpy.props.BoolProperty(
        name="One Way", update=FlagPropertyGroup.update_flag)
    flag2: bpy.props.BoolProperty(
        name="Link Interiors Together", update=FlagPropertyGroup.update_flag)
    flag3: bpy.props.BoolProperty(
        name="Mirror", update=FlagPropertyGroup.update_flag)
    flag4: bpy.props.BoolProperty(
        name="Disable Timecycle Modifier", update=FlagPropertyGroup.update_flag)
    flag5: bpy.props.BoolProperty(
        name="Mirror Using Expensive Shaders", update=FlagPropertyGroup.update_flag)
    flag6: bpy.props.BoolProperty(
        name="Low LOD Only", update=FlagPropertyGroup.update_flag)
    flag7: bpy.props.BoolProperty(
        name="Hide when door closed", update=FlagPropertyGroup.update_flag)
    flag8: bpy.props.BoolProperty(
        name="Mirror Can See Directional", update=FlagPropertyGroup.update_flag)
    flag9: bpy.props.BoolProperty(
        name="Mirror Using Portal Traversal", update=FlagPropertyGroup.update_flag)
    flag10: bpy.props.BoolProperty(
        name="Mirror Floor", update=FlagPropertyGroup.update_flag)
    flag11: bpy.props.BoolProperty(
        name="Mirror Can See Exterior View", update=FlagPropertyGroup.update_flag)
    flag12: bpy.props.BoolProperty(
        name="Water Surface", update=FlagPropertyGroup.update_flag)
    flag13: bpy.props.BoolProperty(
        name="Water Surface Extend To Horizon", update=FlagPropertyGroup.update_flag)
    flag14: bpy.props.BoolProperty(
        name="Use Light Bleed", update=FlagPropertyGroup.update_flag)


class EntityFlags(FlagPropertyGroup, bpy.types.PropertyGroup):
    flag1: bpy.props.BoolProperty(
        name="Allow full rotation", update=FlagPropertyGroup.update_flag)
    flag2: bpy.props.BoolProperty(
        name="Stream Low Priority", update=FlagPropertyGroup.update_flag)
    flag3: bpy.props.BoolProperty(
        name="Disable embedded collisions", update=FlagPropertyGroup.update_flag)
    flag4: bpy.props.BoolProperty(
        name="LOD in Parented YMAP", update=FlagPropertyGroup.update_flag)
    flag5: bpy.props.BoolProperty(
        name="LOD Adopt Me", update=FlagPropertyGroup.update_flag)
    flag6: bpy.props.BoolProperty(
        name="Static entity", update=FlagPropertyGroup.update_flag)
    flag7: bpy.props.BoolProperty(
        name="Interior LOD", update=FlagPropertyGroup.update_flag)
    flag8: bpy.props.BoolProperty(
        name="Unknown 8", update=FlagPropertyGroup.update_flag)
    flag9: bpy.props.BoolProperty(
        name="Unknown 9", update=FlagPropertyGroup.update_flag)
    flag10: bpy.props.BoolProperty(
        name="Unknown 10", update=FlagPropertyGroup.update_flag)
    flag11: bpy.props.BoolProperty(
        name="Unknown 11", update=FlagPropertyGroup.update_flag)
    flag12: bpy.props.BoolProperty(
        name="Unknown 12", update=FlagPropertyGroup.update_flag)
    flag13: bpy.props.BoolProperty(
        name="Unknown 13", update=FlagPropertyGroup.update_flag)
    flag14: bpy.props.BoolProperty(
        name="Unknown 14", update=FlagPropertyGroup.update_flag)
    flag15: bpy.props.BoolProperty(
        name="Unknown 15", update=FlagPropertyGroup.update_flag)
    flag16: bpy.props.BoolProperty(
        name="LOD Use Alt Fade", update=FlagPropertyGroup.update_flag)
    flag17: bpy.props.BoolProperty(
        name="Unused", update=FlagPropertyGroup.update_flag)
    flag18: bpy.props.BoolProperty(
        name="Does Not Touch Water", update=FlagPropertyGroup.update_flag)
    flag19: bpy.props.BoolProperty(name="Does Not Spawn Peds",
                                   update=FlagPropertyGroup.update_flag)
    flag20: bpy.props.BoolProperty(
        name="Cast Static Shadows", update=FlagPropertyGroup.update_flag)
    flag21: bpy.props.BoolProperty(
        name="Cast Dynamic Shadows", update=FlagPropertyGroup.update_flag)
    flag22: bpy.props.BoolProperty(
        name="Ignore Day Night Settings", update=FlagPropertyGroup.update_flag)
    flag23: bpy.props.BoolProperty(
        name="Disable shadow for entity", update=FlagPropertyGroup.update_flag)
    flag24: bpy.props.BoolProperty(
        name="Disable entity, shadow casted", update=FlagPropertyGroup.update_flag)
    flag25: bpy.props.BoolProperty(
        name="Dont Render In Reflections", update=FlagPropertyGroup.update_flag)
    flag26: bpy.props.BoolProperty(
        name="Only Render In Reflections", update=FlagPropertyGroup.update_flag)
    flag27: bpy.props.BoolProperty(
        name="Dont Render In Water Reflections", update=FlagPropertyGroup.update_flag)
    flag28: bpy.props.BoolProperty(
        name="Only Render In Water Reflections", update=FlagPropertyGroup.update_flag)
    flag29: bpy.props.BoolProperty(
        name="Dont Render In Mirror Reflections", update=FlagPropertyGroup.update_flag)
    flag30: bpy.props.BoolProperty(
        name="Only Render In Mirror Reflections", update=FlagPropertyGroup.update_flag)
    flag31: bpy.props.BoolProperty(
        name="Unknown 31", update=FlagPropertyGroup.update_flag)
    flag32: bpy.props.BoolProperty(
        name="Unknown 32", update=FlagPropertyGroup.update_flag)


class ArchetypeFlags(FlagPropertyGroup, bpy.types.PropertyGroup):
    flag1: bpy.props.BoolProperty(
        name="Wet Road Reflection", update=FlagPropertyGroup.update_flag)
    flag2: bpy.props.BoolProperty(
        name="Dont Fade", update=FlagPropertyGroup.update_flag)
    flag3: bpy.props.BoolProperty(
        name="Draw Last", update=FlagPropertyGroup.update_flag)
    flag4: bpy.props.BoolProperty(
        name="Climbable By AI", update=FlagPropertyGroup.update_flag)
    flag5: bpy.props.BoolProperty(
        name="Suppress HD TXDs", update=FlagPropertyGroup.update_flag)
    flag6: bpy.props.BoolProperty(
        name="Static", update=FlagPropertyGroup.update_flag)
    flag7: bpy.props.BoolProperty(
        name="Disable alpha sorting", update=FlagPropertyGroup.update_flag)
    flag8: bpy.props.BoolProperty(
        name="Tough For Bullets", update=FlagPropertyGroup.update_flag)
    flag9: bpy.props.BoolProperty(
        name="Is Generic", update=FlagPropertyGroup.update_flag)
    flag10: bpy.props.BoolProperty(
        name="Has Anim (YCD)", update=FlagPropertyGroup.update_flag)
    flag11: bpy.props.BoolProperty(
        name="UV anims (YCD)", update=FlagPropertyGroup.update_flag)
    flag12: bpy.props.BoolProperty(
        name="Shadow Only", update=FlagPropertyGroup.update_flag)
    flag13: bpy.props.BoolProperty(
        name="Damage Model", update=FlagPropertyGroup.update_flag)
    flag14: bpy.props.BoolProperty(
        name="Dont Cast Shadows", update=FlagPropertyGroup.update_flag)
    flag15: bpy.props.BoolProperty(
        name="Cast Texture Shadows", update=FlagPropertyGroup.update_flag)
    flag16: bpy.props.BoolProperty(
        name="Dont Collide With Flyer", update=FlagPropertyGroup.update_flag)
    flag17: bpy.props.BoolProperty(
        name="Double-sided rendering", update=FlagPropertyGroup.update_flag)
    flag18: bpy.props.BoolProperty(
        name="Dynamic", update=FlagPropertyGroup.update_flag)
    flag19: bpy.props.BoolProperty(
        name="Override Physics Bounds", update=FlagPropertyGroup.update_flag)
    flag20: bpy.props.BoolProperty(
        name="Auto Start Anim", update=FlagPropertyGroup.update_flag)
    flag21: bpy.props.BoolProperty(
        name="Has Pre Reflected Water Proxy", update=FlagPropertyGroup.update_flag)
    flag22: bpy.props.BoolProperty(
        name="Has Drawable Proxy For Water Reflections", update=FlagPropertyGroup.update_flag)
    flag23: bpy.props.BoolProperty(
        name="Does Not Provide AI Cover", update=FlagPropertyGroup.update_flag)
    flag24: bpy.props.BoolProperty(
        name="Does Not Provide Player Cover", update=FlagPropertyGroup.update_flag)
    flag25: bpy.props.BoolProperty(
        name="Is Ladder Deprecated", update=FlagPropertyGroup.update_flag)
    flag26: bpy.props.BoolProperty(
        name="Has Cloth", update=FlagPropertyGroup.update_flag)
    flag27: bpy.props.BoolProperty(
        name="Enable Door Physics", update=FlagPropertyGroup.update_flag)
    flag28: bpy.props.BoolProperty(
        name="Is Fixed For Navigation", update=FlagPropertyGroup.update_flag)
    flag29: bpy.props.BoolProperty(
        name="Dont Avoid By Peds", update=FlagPropertyGroup.update_flag)
    flag30: bpy.props.BoolProperty(
        name="Use Ambient Scale", update=FlagPropertyGroup.update_flag)
    flag31: bpy.props.BoolProperty(
        name="Is Debug", update=FlagPropertyGroup.update_flag)
    flag32: bpy.props.BoolProperty(
        name="Has Alpha Shadow", update=FlagPropertyGroup.update_flag)


class MloFlags(FlagPropertyGroup, bpy.types.PropertyGroup):
    size = 16

    flag1: bpy.props.BoolProperty(
        name="Unused", update=FlagPropertyGroup.update_flag)
    flag2: bpy.props.BoolProperty(
        name="Unused", update=FlagPropertyGroup.update_flag)
    flag3: bpy.props.BoolProperty(
        name="Unused", update=FlagPropertyGroup.update_flag)
    flag4: bpy.props.BoolProperty(
        name="Unused", update=FlagPropertyGroup.update_flag)
    flag5: bpy.props.BoolProperty(
        name="Unused", update=FlagPropertyGroup.update_flag)
    flag6: bpy.props.BoolProperty(
        name="Unused", update=FlagPropertyGroup.update_flag)
    flag7: bpy.props.BoolProperty(
        name="Unused", update=FlagPropertyGroup.update_flag)
    flag8: bpy.props.BoolProperty(
        name="Unused", update=FlagPropertyGroup.update_flag)
    flag9: bpy.props.BoolProperty(
        name="Subway", update=FlagPropertyGroup.update_flag)
    flag10: bpy.props.BoolProperty(
        name="Office", update=FlagPropertyGroup.update_flag)
    flag11: bpy.props.BoolProperty(
        name="Allow Run", update=FlagPropertyGroup.update_flag)
    flag12: bpy.props.BoolProperty(
        name="Cutscene Only", update=FlagPropertyGroup.update_flag)
    flag13: bpy.props.BoolProperty(
        name="LOD When Locked", update=FlagPropertyGroup.update_flag)
    flag14: bpy.props.BoolProperty(
        name="No Water Reflection", update=FlagPropertyGroup.update_flag)
    flag15: bpy.props.BoolProperty(
        name="Unused", update=FlagPropertyGroup.update_flag)
    flag16: bpy.props.BoolProperty(
        name="Has Low LOD Portals", update=FlagPropertyGroup.update_flag)
