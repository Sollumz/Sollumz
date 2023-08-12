# Collision Physics

Each separable part of a Fragment must have an associated collision object in order for physics to work. This means each bone with `Use Physics` enabled should also have a collision object linked to it.

### Rigging Collisions

You link collisions to bones the same way you link Drawable Models to bones as described in [Drawables (.ydr) > Rigging](../drawables-.ydr/rigging.md#linking-bones-to-drawable-models).

<div align="left">

<figure><img src="../../.gitbook/assets/image (11).png" alt=""><figcaption><p>Collision object linked to bone via a Child Of constraint</p></figcaption></figure>

</div>

### Setting Mass

Each collision object under a Fragment also has a Physics subpanel where you can define its mass.

<div align="left">

<figure><img src="../../.gitbook/assets/image (8) (1).png" alt=""><figcaption><p>Object Properties > Sollumz > Physics</p></figcaption></figure>

</div>

#### Auto Mass Tool

There is also a tool for automatically calculating mass based on the collision material's density and the object's volume. Navigate to `Sollumz Tools > Fragment > Set Mass`. There you will find the `Calculate Collision Mass tool`.

<div align="left">

<figure><img src="../../.gitbook/assets/image (32).png" alt=""><figcaption><p>Sollumz Tools > Fragment > Set Mass</p></figcaption></figure>

</div>

In order for this tool to work, the collision object must have a collision material added.

### Volume and Inertia

Volume and Inertia are essential physics properties for collisions. You can find these options under `Object Properties > Sollumz`.

<div align="left">

<figure><img src="../../.gitbook/assets/image (18).png" alt=""><figcaption><p>Object Properties > Sollumz</p></figcaption></figure>

</div>

Typically when creating completely custom collisions, you would auto-calculate these values during export, as calculating these involves a lot of math relating to the dimensions and shape of your collisions.

<div align="left">

<figure><img src="../../.gitbook/assets/image (19).png" alt=""><figcaption><p>Export Codewalker XML > Collisions</p></figcaption></figure>

</div>
