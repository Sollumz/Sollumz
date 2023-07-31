# Rigging

Drawables can be rigged using either vertex groups (skinning) or Child Of constraints. The top-level Drawable object must be an armature.

### Skinning

Skinning Drawables works the same way you would normally do it in Blender. Simply create vertex groups where each group's name corresponds to a bone in the armature. Then, add an armature modifier and specify the Drawable as the armature object.

<div align="left">

<figure><img src="../../.gitbook/assets/blender_3Zw5StTfDu.png" alt="" width="503"><figcaption><p>Drawable Model setup for skinning</p></figcaption></figure>

</div>

### Linking bones to Drawable Models

Many Drawables aren't rigged using weighted vertex groups. You can instead link an entire Drawable Model to a bone by using a Child Of constraint.

<div align="left">

<figure><img src="../../.gitbook/assets/JITnx9V.png" alt=""><figcaption><p>Sollumz Tools > Drawable > Bone Tools</p></figcaption></figure>

</div>

Use the "Add Bone Constraint" operator with the Drawable Model Selected to add a Child Of Constraint with the properties setup for correct previewing.
