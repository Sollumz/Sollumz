import bpy
from ...sollumz_properties import FlagPropertyGroup


class RoomFlags(FlagPropertyGroup, bpy.types.PropertyGroup):
    size = 10

    flag1: bpy.props.BoolProperty(
        name="Unknown 1", update=FlagPropertyGroup.update_flag)
    flag2: bpy.props.BoolProperty(
        name="Disables wanted level", update=FlagPropertyGroup.update_flag)
    flag3: bpy.props.BoolProperty(
        name="Disable exterior shadows", update=FlagPropertyGroup.update_flag)
    flag4: bpy.props.BoolProperty(
        name="Unknown 4", update=FlagPropertyGroup.update_flag)
    flag5: bpy.props.BoolProperty(
        name="Unknown 5", update=FlagPropertyGroup.update_flag)
    flag6: bpy.props.BoolProperty(
        name="Reduces vehicle population", update=FlagPropertyGroup.update_flag)
    flag7: bpy.props.BoolProperty(
        name="Reduces ped population", update=FlagPropertyGroup.update_flag)
    flag8: bpy.props.BoolProperty(
        name="Unknown 8", update=FlagPropertyGroup.update_flag)
    flag9: bpy.props.BoolProperty(
        name="Disable limbo portals", update=FlagPropertyGroup.update_flag)
    flag10: bpy.props.BoolProperty(
        name="Unknown 10", update=FlagPropertyGroup.update_flag)


class PortalFlags(FlagPropertyGroup, bpy.types.PropertyGroup):
    size = 14

    flag1: bpy.props.BoolProperty(
        name="Disables exterior rendering", update=FlagPropertyGroup.update_flag)
    flag2: bpy.props.BoolProperty(
        name="Disables interior rendering", update=FlagPropertyGroup.update_flag)
    flag3: bpy.props.BoolProperty(
        name="Mirror", update=FlagPropertyGroup.update_flag)
    flag4: bpy.props.BoolProperty(
        name="Extra bloom", update=FlagPropertyGroup.update_flag)
    flag5: bpy.props.BoolProperty(
        name="Unknown 5", update=FlagPropertyGroup.update_flag)
    flag6: bpy.props.BoolProperty(
        name="Use exterior LOD", update=FlagPropertyGroup.update_flag)
    flag7: bpy.props.BoolProperty(
        name="Hide when door closed", update=FlagPropertyGroup.update_flag)
    flag8: bpy.props.BoolProperty(
        name="Unknown 8", update=FlagPropertyGroup.update_flag)
    flag9: bpy.props.BoolProperty(
        name="Mirror exterior portals", update=FlagPropertyGroup.update_flag)
    flag10: bpy.props.BoolProperty(
        name="Unknown 10", update=FlagPropertyGroup.update_flag)
    flag11: bpy.props.BoolProperty(
        name="Mirror limbo entities", update=FlagPropertyGroup.update_flag)
    flag12: bpy.props.BoolProperty(
        name="Unknown 12", update=FlagPropertyGroup.update_flag)
    flag13: bpy.props.BoolProperty(
        name="Unknown 13", update=FlagPropertyGroup.update_flag)
    flag14: bpy.props.BoolProperty(
        name="Disable farclipping", update=FlagPropertyGroup.update_flag)


class EntityFlags(FlagPropertyGroup, bpy.types.PropertyGroup):
    flag1: bpy.props.BoolProperty(
        name="Allow full rotation", update=FlagPropertyGroup.update_flag)
    flag2: bpy.props.BoolProperty(
        name="Unknown 2", update=FlagPropertyGroup.update_flag)
    flag3: bpy.props.BoolProperty(
        name="Disable embedded collisions", update=FlagPropertyGroup.update_flag)
    flag4: bpy.props.BoolProperty(
        name="Unknown 4", update=FlagPropertyGroup.update_flag)
    flag5: bpy.props.BoolProperty(
        name="Unknown 5", update=FlagPropertyGroup.update_flag)
    flag6: bpy.props.BoolProperty(
        name="Static entity", update=FlagPropertyGroup.update_flag)
    flag7: bpy.props.BoolProperty(
        name="Object isn't dark at night", update=FlagPropertyGroup.update_flag)
    flag8: bpy.props.BoolProperty(
        name="Unknown 8", update=FlagPropertyGroup.update_flag)
    flag9: bpy.props.BoolProperty(
        name="Unknown 9", update=FlagPropertyGroup.update_flag)
    flag10: bpy.props.BoolProperty(
        name="Disable embedded light sources", update=FlagPropertyGroup.update_flag)
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
        name="Unknown 16", update=FlagPropertyGroup.update_flag)
    flag17: bpy.props.BoolProperty(
        name="Unknown 17", update=FlagPropertyGroup.update_flag)
    flag18: bpy.props.BoolProperty(
        name="Unknown 18", update=FlagPropertyGroup.update_flag)
    flag19: bpy.props.BoolProperty(name="Disable archetype extensions",
                                   update=FlagPropertyGroup.update_flag)
    flag20: bpy.props.BoolProperty(
        name="Unknown 20", update=FlagPropertyGroup.update_flag)
    flag21: bpy.props.BoolProperty(
        name="Unknown 21", update=FlagPropertyGroup.update_flag)
    flag22: bpy.props.BoolProperty(
        name="Unknown 22", update=FlagPropertyGroup.update_flag)
    flag23: bpy.props.BoolProperty(
        name="Disable shadow for entity", update=FlagPropertyGroup.update_flag)
    flag24: bpy.props.BoolProperty(
        name="Disable entity, shadow casted", update=FlagPropertyGroup.update_flag)
    flag25: bpy.props.BoolProperty(
        name="Object will not cast reflections", update=FlagPropertyGroup.update_flag)
    flag26: bpy.props.BoolProperty(
        name="Interior proxy", update=FlagPropertyGroup.update_flag)
    flag27: bpy.props.BoolProperty(
        name="Unknown 27", update=FlagPropertyGroup.update_flag)
    flag28: bpy.props.BoolProperty(
        name="Reflection proxy", update=FlagPropertyGroup.update_flag)
    flag29: bpy.props.BoolProperty(
        name="Unknown 29", update=FlagPropertyGroup.update_flag)
    flag30: bpy.props.BoolProperty(
        name="Mirror proxy", update=FlagPropertyGroup.update_flag)
    flag31: bpy.props.BoolProperty(
        name="Unknown 31", update=FlagPropertyGroup.update_flag)
    flag32: bpy.props.BoolProperty(
        name="Unknown 32", update=FlagPropertyGroup.update_flag)


class ArchetypeFlags(FlagPropertyGroup, bpy.types.PropertyGroup):
    flag1: bpy.props.BoolProperty(
        name="Unknown 1", update=FlagPropertyGroup.update_flag)
    flag2: bpy.props.BoolProperty(
        name="Unknown 2", update=FlagPropertyGroup.update_flag)
    flag3: bpy.props.BoolProperty(
        name="Unknown 3", update=FlagPropertyGroup.update_flag)
    flag4: bpy.props.BoolProperty(
        name="Unknown 4", update=FlagPropertyGroup.update_flag)
    flag5: bpy.props.BoolProperty(
        name="Unknown 5", update=FlagPropertyGroup.update_flag)
    flag6: bpy.props.BoolProperty(
        name="Static", update=FlagPropertyGroup.update_flag)
    flag7: bpy.props.BoolProperty(
        name="Unknown 7", update=FlagPropertyGroup.update_flag)
    flag8: bpy.props.BoolProperty(
        name="Instance", update=FlagPropertyGroup.update_flag)
    flag9: bpy.props.BoolProperty(
        name="Unknown 9", update=FlagPropertyGroup.update_flag)
    flag10: bpy.props.BoolProperty(
        name="Bone anims (YCD)", update=FlagPropertyGroup.update_flag)
    flag11: bpy.props.BoolProperty(
        name="UV anims (YCD)", update=FlagPropertyGroup.update_flag)
    flag12: bpy.props.BoolProperty(
        name="Invisible but blocks lights/shadows", update=FlagPropertyGroup.update_flag)
    flag13: bpy.props.BoolProperty(
        name="Unknown 13", update=FlagPropertyGroup.update_flag)
    flag14: bpy.props.BoolProperty(
        name="Object won't cast shadow", update=FlagPropertyGroup.update_flag)
    flag15: bpy.props.BoolProperty(
        name="Unknown 15", update=FlagPropertyGroup.update_flag)
    flag16: bpy.props.BoolProperty(
        name="Unknown 16", update=FlagPropertyGroup.update_flag)
    flag17: bpy.props.BoolProperty(
        name="Double-sided rendering", update=FlagPropertyGroup.update_flag)
    flag18: bpy.props.BoolProperty(
        name="Dynamic", update=FlagPropertyGroup.update_flag)
    flag19: bpy.props.BoolProperty(
        name="Unknown 19", update=FlagPropertyGroup.update_flag)
    flag20: bpy.props.BoolProperty(
        name="Unknown 20", update=FlagPropertyGroup.update_flag)
    flag21: bpy.props.BoolProperty(
        name="Unknown 21", update=FlagPropertyGroup.update_flag)
    flag22: bpy.props.BoolProperty(
        name="Unknown 22", update=FlagPropertyGroup.update_flag)
    flag23: bpy.props.BoolProperty(
        name="Unknown 23", update=FlagPropertyGroup.update_flag)
    flag24: bpy.props.BoolProperty(
        name="Unknown 24", update=FlagPropertyGroup.update_flag)
    flag25: bpy.props.BoolProperty(
        name="Unknown 25", update=FlagPropertyGroup.update_flag)
    flag26: bpy.props.BoolProperty(
        name="Unknown 26", update=FlagPropertyGroup.update_flag)
    flag27: bpy.props.BoolProperty(
        name="Enables special attribute", update=FlagPropertyGroup.update_flag)
    flag28: bpy.props.BoolProperty(
        name="Unknown 28", update=FlagPropertyGroup.update_flag)
    flag29: bpy.props.BoolProperty(
        name="Disable red vertex channel", update=FlagPropertyGroup.update_flag)
    flag30: bpy.props.BoolProperty(
        name="Disable green vertex channel", update=FlagPropertyGroup.update_flag)
    flag31: bpy.props.BoolProperty(
        name="Disable blue vertex channel", update=FlagPropertyGroup.update_flag)
    flag32: bpy.props.BoolProperty(
        name="Disable alpha vertex channel", update=FlagPropertyGroup.update_flag)


class UnknownFlags(FlagPropertyGroup, bpy.types.PropertyGroup):
    flag1: bpy.props.BoolProperty(
        name="Unknown 1", update=FlagPropertyGroup.update_flag)
    flag2: bpy.props.BoolProperty(
        name="Unknown 2", update=FlagPropertyGroup.update_flag)
    flag3: bpy.props.BoolProperty(
        name="Unknown 3", update=FlagPropertyGroup.update_flag)
    flag4: bpy.props.BoolProperty(
        name="Unknown 4", update=FlagPropertyGroup.update_flag)
    flag5: bpy.props.BoolProperty(
        name="Unknown 5", update=FlagPropertyGroup.update_flag)
    flag6: bpy.props.BoolProperty(
        name="Unknown 6", update=FlagPropertyGroup.update_flag)
    flag7: bpy.props.BoolProperty(
        name="Unknown 7", update=FlagPropertyGroup.update_flag)
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
        name="Unknown 16", update=FlagPropertyGroup.update_flag)
    flag17: bpy.props.BoolProperty(
        name="Unknown 17", update=FlagPropertyGroup.update_flag)
    flag18: bpy.props.BoolProperty(
        name="Unknown 18", update=FlagPropertyGroup.update_flag)
    flag19: bpy.props.BoolProperty(
        name="Unknown 19", update=FlagPropertyGroup.update_flag)
    flag20: bpy.props.BoolProperty(
        name="Unknown 20", update=FlagPropertyGroup.update_flag)
    flag21: bpy.props.BoolProperty(
        name="Unknown 21", update=FlagPropertyGroup.update_flag)
    flag22: bpy.props.BoolProperty(
        name="Unknown 22", update=FlagPropertyGroup.update_flag)
    flag23: bpy.props.BoolProperty(
        name="Unknown 23", update=FlagPropertyGroup.update_flag)
    flag24: bpy.props.BoolProperty(
        name="Unknown 24", update=FlagPropertyGroup.update_flag)
    flag25: bpy.props.BoolProperty(
        name="Unknown 25", update=FlagPropertyGroup.update_flag)
    flag26: bpy.props.BoolProperty(
        name="Unknown 26", update=FlagPropertyGroup.update_flag)
    flag27: bpy.props.BoolProperty(
        name="Unknown 27", update=FlagPropertyGroup.update_flag)
    flag28: bpy.props.BoolProperty(
        name="Unknown 28", update=FlagPropertyGroup.update_flag)
    flag29: bpy.props.BoolProperty(
        name="Unknown 29", update=FlagPropertyGroup.update_flag)
    flag30: bpy.props.BoolProperty(
        name="Unknown 30", update=FlagPropertyGroup.update_flag)
    flag31: bpy.props.BoolProperty(
        name="Unknown 31", update=FlagPropertyGroup.update_flag)
    flag32: bpy.props.BoolProperty(
        name="Unknown 32", update=FlagPropertyGroup.update_flag)
