# Level of Detail (LODs) Editing

The LODs for each Drawable Model can be edited in the `Mesh Properties > Sollumz LODs` panel. As mentioned before, there are 4 LOD levels: **High**, **Medium**, **Low**, and **Very Low**. You will also see the "Very High" LOD level, but that is only used for YFT vehicles (see Fragments > [Vehicle Setup](../fragments-.yft/vehicle-setup/#import-with-\_hi)).

<div align="left">

<figure><img src="../../.gitbook/assets/image (3) (1) (1).png" alt="" width="493"><figcaption><p>Mesh Properties > Sollmz LODs</p></figcaption></figure>

</div>

### Setting LOD Level

For each LOD level, you can select the mesh it will use. You can also select any LOD level from the list and it will swap out the mesh that the Drawable Model uses.

<div align="left">

<figure><img src="../../.gitbook/assets/5lCjyGM.gif" alt="" width="489"><figcaption><p>Swapping LOD meshes</p></figcaption></figure>

</div>

LODs can also be changed for the entire hierarchy at once in the `Sollumz Tools > General > View` panel.

<div align="left">

<figure><img src="../../.gitbook/assets/blender_ehMPgjU9Q9.gif" alt=""><figcaption><p>Sollumz Tools > General > View</p></figcaption></figure>

</div>

Alternatively, press `Shift + V` to open a pie menu for quickly viewing different LOD levels.

<figure><img src="../../.gitbook/assets/blender_q6GniSsPAN.gif" alt=""><figcaption><p>LODs pie menu (Shift + V)</p></figcaption></figure>

### Auto LOD Tool

Sollumz provides a basic LOD generation tool that uses the decimate modifier.

Select the Drawable Model and Navigate to `Sollumz Tools > Drawable > LOD Tools`.

<div align="left">

<figure><img src="../../.gitbook/assets/image (28).png" alt=""><figcaption><p>Sollumz Tools > Drawable > LOD Tools</p></figcaption></figure>

</div>

From here you can select which LOD levels will get created. Normally you'd model the highest LOD first, convert to a Drawable Model, then use that high LOD mesh as the reference mesh. The reference mesh is not affected in this process. Each subsequent LOD level is decimated by `Decimate Step`.

<div align="left">

<figure><img src="../../.gitbook/assets/auto_lod.gif" alt=""><figcaption><p>Generating LODs using Suzanne.high</p></figcaption></figure>

</div>

Your results will vary depending on the mesh, as the decimate modifier does not work well for all topologies.&#x20;

### Extracting LODs into Separate Objects

You can also take advantage of Blender's instancing functionality and separate the LOD meshes into separate objects. This allows you to work on multiple LOD meshes at once.

Select the Drawable Model and Navigate to `Sollumz Tools > Drawable > LOD Tools`.

<div align="left">

<figure><img src="../../.gitbook/assets/image (29).png" alt=""><figcaption><p>Sollumz Tools > Drawable > LOD Tools</p></figcaption></figure>

</div>

From here you can select which LODs to extract as well as what to parent the new objects to. You can either parent the objects to a collection or an empty object.

<div align="left">

<figure><img src="../../.gitbook/assets/extract_lods.gif" alt=""><figcaption><p>Extract LODs</p></figcaption></figure>

</div>

Notice how these new objects are using the same meshes as the ones defined in the `Sollumz LODs` panel.

<div align="left">

<figure><img src="../../.gitbook/assets/image (30).png" alt=""><figcaption><p>Mesh Properties > Sollumz LODs</p></figcaption></figure>

</div>

Now, if you edit one of these object instances, the Drawable Model will be affected too.

<div align="left">

<figure><img src="../../.gitbook/assets/instances.gif" alt=""><figcaption><p>Editing Suzanne.high</p></figcaption></figure>

</div>
