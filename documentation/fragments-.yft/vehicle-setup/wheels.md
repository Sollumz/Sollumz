# Wheels

Upon importing, you will notice that the vehicle has only one wheel. This is because the game instances (re-uses) `wheel_lf` for all other wheels.&#x20;

Wheel meshes do not have vertex groups but are instead rigged by a Child Of Constraint (as explained in [Drawables > Rigging](../../drawables-.ydr/rigging.md#linking-bones-to-drawable-models)).

<figure><img src="../../../.gitbook/assets/image (21).png" alt=""><figcaption><p>Wheel mesh rigging</p></figcaption></figure>

Also, wheel meshes have the `Is Wheel Mesh` property ticked under `Object Properties > Sollumz`.

<div align="left">

<figure><img src="../../../.gitbook/assets/image (23).png" alt=""><figcaption><p>Object Properties > Sollumz</p></figcaption></figure>

</div>

That's all that's needed for setting up wheel meshes!

### Previewing the Other Wheels

In `Sollumz Tools > Fragment > Create Fragment Objects` is a tool called `Generate Wheel Instances`. This tool will create instances of the wheel, allowing you to better preview what it looks like in-game. This is useful when positioning the wheel bones.

<div align="left">

<figure><img src="../../../.gitbook/assets/wheel_meshes.gif" alt=""><figcaption><p>Sollumz Tools > Fragment > Create Fragment Objects</p></figcaption></figure>

</div>
