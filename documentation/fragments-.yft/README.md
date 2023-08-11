# 🚙 Fragments (.yft)

Fragments are objects that contain separable parts and react to physics. These objects are typically used in breakable props (i.e. street lamps) and vehicles. The file contains a Drawable and a Composite (collision), and sometimes multiple of each if there is a destroyed variant such as in gas tanks. However, Sollumz does not currently support editing destroyed variants of Fragments.

It's recommended that you read the documentation page on Drawables and collisions first, as Fragments are made up of these objects.

{% content-ref url="../drawables-.ydr/" %}
[drawables-.ydr](../drawables-.ydr/)
{% endcontent-ref %}

{% content-ref url="../collisions-.ybn.md" %}
[collisions-.ybn.md](../collisions-.ybn.md)
{% endcontent-ref %}

### File Layout

```
Fragment
    Drawable
    DrawableDamaged (sometimes)
    Physics
        Composite
        CompositeDamaged (sometimes)
        PhysicsGroups
        PhysicsChildren
    VehicleGlassWindows
    GlassWindows (currently not supported)
    Lights
```

{% hint style="info" %}
The file layout for Fragments is quite complex, even with the simplified layout shown above (if you wish to see the full file layout, just open a yft.xml). However, you don't need to understand how the file works internally to understand how it works in Sollumz.
{% endhint %}

The Fragment contains a main Drawable as well as a `Physics` section which contains the collisions and physics data. `PhysicsGroups` contains groups of physics data where each group is linked to a bone. This is essentially the physics properties for each bone. `PhysicsChildren` contains physics data for each collision (i.e. mass, inertia). Each physics child belongs to a `PhysicsGroup`, and multiple children can belong to a single group.

You'll also notice there is a `VehicleGlassWindows` section. As the name implies, this is where data relating to vehicle windows are stored. Non-vehicle fragments can also have `GlassWindows`, but that is not currently supported by Sollumz.

Finally, there are `Lights`, which, just like Drawables, contain any lights that the Fragment might have (only ever used in prop Fragments).

### Blender Hierarchy

<div align="left">

<figure><img src="../../.gitbook/assets/image (1) (1).png" alt=""><figcaption><p>Example Fragment object</p></figcaption></figure>

</div>

The Blender hierarchy for Fragments is quite simple. The Fragment object itself is an armature with a Bound Composite and Drawable parented to it. The Fragment can also contain lights. Lights are typically stored in an empty object called "Lights", but can also be stored loosely in the Fragment or under the Drawable. It's up to you where to store the lights, as, during export, it will search all children (recursively) for lights. The hierarchy for the Bound Composite and Drawable is exactly the same.
