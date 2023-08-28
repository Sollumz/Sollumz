# 🌐 Drawables (.ydr)

Drawables are objects that hold mesh data, skeleton data, and shader data. It can be thought of as the game engine's mesh format. YDR files contain one Drawable and are typically used for static mapping but are also used for dynamic props in some cases. In cases where a prop consists of multiple breakable parts, [Fragment (.yft) ](../fragments-.yft/)objects are used instead.

### File Layout

```
Drawable
    ShaderGroup
        Shaders
        TextureDictionary
    Skeleton (sometimes)
    DrawableModelsHigh
        Geometries...
    DrawableModelsMed
        Geometries...
    DrawableModelsLow
        Geometries...
    DrawableModelsVeryLow
        Geometries...
    Lights (sometimes)
```

Drawables consist of multiple "Drawable Models" which hold the actual mesh data. Drawable Models are organized into High, Medium, Low, and Very Low detail levels. In every Drawable there is also a list of the shaders used and the parameters for each shader. Sometimes there are textures embedded in the file as well. Drawables can also contain skeleton data, but it is not required. This is usually only found in dynamic Drawables (objects affected by physics) such as props or in Drawables that are animated. Lastly, Drawables can contain lights, where each light contains light properties such as direction, falloff, color, etc.

### Blender Hierarchy

<div align="left" data-full-width="false">

<figure><img src="../../.gitbook/assets/image (6) (1).png" alt="" width="453"><figcaption><p>Example Drawable object</p></figcaption></figure>

</div>

In Blender, the hierarchy for Drawables consists of one parent Drawable object (either an empty or an armature depending on whether or not the Drawable has skeleton data) and Drawable Models (mesh objects).
