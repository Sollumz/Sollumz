# Sollumz
Blender plugin to import, export, or create GTA V assets in the Codewalker XML format.

By Skylumz, Colton Fox and alexguirre.

## Join our Discord
Join the Sollumz [discord server](https://discord.sollumz.org/) to ask questions and chat with the community!
## Using the plugin
See the [wiki](https://docs.sollumz.org/) to get started. Make sure to read the wiki before posting an issue or asking questions! Also, see the Tutorials and Resources channel on the Discord server.

**Note:** The issue tracker should be for bug reports and feature requests only. If you are having an issue and you are not sure if it is a bug or not, ask on the Discord server first!

## Features ##

**Supported Formats**
  * YDD
  * YDR
  * YFT
  * YBN
  * YTYP
  * YCD
  * YMAP (Partial)

**General Features**
  * Import / Export
  * Automatic texture loading
  * Vertex colors
  * Bones and weights
  * Animations
  * Custom normals
  * Shader editing
  * Vehicle creation/editing
  * Dynamic prop creation/editing

## Requirements ##
  * Latest Codewalker release from [their discord](https://discord.gg/codewalker)
  * [Blender 4.0 or newer](http://www.blender.org/download/)

## Installation ##

Follow the [installation instructions on our wiki](https://docs.sollumz.org/getting-started/installation).

---
### Supporters ❤️ ###
- [GitBook](https://www.gitbook.com/)
- dexyfex and the [CodeWalker](https://github.com/dexyfex/CodeWalker) team

---
## What's New (custom build)

- LOD Tools: Delete LODs
  - New operator: `sollumz.delete_lods` to remove selected LOD levels from all selected Drawable Model objects.
  - UI: 3D Viewport Sidebar → Sollumz Tools → LOD Tools → Delete LODs.
  - Property: `Scene.sollumz_delete_lods_levels` to pick which levels to delete.
  - Removes LOD mesh references and deletes mesh datablocks if unused anywhere.

- Auto LOD enhancements
  - New operator: `sollumz.auto_lod_multi` (Generate LODs Per-Object).
    - Processes all selected Drawable Models; for each, uses its own Very High LOD as the reference.
    - Generates only the levels selected in `Scene.sollumz_auto_lod_levels` and applies decimation by `Scene.sollumz_auto_lod_decimate_step`.
  - UI: Auto LOD now shows two buttons: “Active Only” (`sollumz.auto_lod`) and “Per-Object” (`sollumz.auto_lod_multi`).
  - Behavior fix: The currently active view LOD mesh (e.g., High/Very High) is preserved unless that exact LOD level is selected for generation. Applies to both single-object and multi-object runs.
  - Optional pre-steps before decimation (toggle in Auto LOD panel):
    - Merge by Distance (`Scene.sollumz_auto_lod_pre_merge_by_distance`)
    - Reset Vectors / Recalculate Normals (`Scene.sollumz_auto_lod_pre_reset_vectors`)
    - Clear Custom Split Normals (`Scene.sollumz_auto_lod_pre_clear_custom_normals`)

- LOD Tools: LOD Materials (_low material creation)
  - New operator: `sollumz.create_low_materials` to duplicate a chosen material to a low variant and replace it on a chosen LOD level across all models using the original.
  - UI: 3D Viewport Sidebar → Sollumz Tools → Drawables → LOD Tools → LOD Materials.
  - Properties:
    - `Scene.sollumz_lodtools_source_material`: source material to duplicate (e.g., `vehicle_generic_smallspecmap [PRIMARY]`).
    - `Scene.sollumz_lodtools_target_lod`: LOD level to modify (default: Low).
    - `Scene.sollumz_lodtools_suffix`: name suffix inserted before any trailing bracket tag (default: `_low`).
  - Naming rule: preserves bracket tags. Example: `vehicle_generic_smallspecmap [PRIMARY]` → `vehicle_generic_smallspecmap_low [PRIMARY]`.

Usage tips
- Delete LODs: select one or more Drawable Models, choose levels, click Delete LODs.
- Auto LOD Per-Object: select multiple Drawable Models, choose target levels and decimate step, click Per-Object. The Very High mesh of each object is used as the reference; High/Very High remain untouched unless selected.
 - Auto LOD pre-steps: in the Auto LOD panel, enable desired pre-steps (Merge by Distance, Reset Vectors, Clear Custom Split Normals) before running.
 - LOD Materials: choose the source material, pick target LOD and suffix, then click “Create _low Materials”. Only meshes at the selected LOD that use the source material will be updated.
