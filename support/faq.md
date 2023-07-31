---
description: Frequently Asked Questions
---

# ❔ FAQ

### How do I import files to Blender with Sollumz?

* Sollumz can only import XML files exported from CodeWalker. Make sure you install the latest version of CodeWalker as described[ here](../#requirements).

***

### When I import a YDR/YFT/YDD the textures are not loaded

* From the CodeWalker RPF Explorer, open the asset with the textures.
* Click the save icon in the top right, then click "Save All Textures"
* In Blender, press the `V` key, then click `Find Missing Files` and select the folder where you saved the textures.

<div align="left">

<figure><img src="https://i.imgur.com/vbXzGXx.gif" alt="" width="563"><figcaption></figcaption></figure>

</div>

* **Alternatively**, export all textures into a folder with the same name as the file you are importing. For instance, if you wanted to import `adder.yft` with all of its textures, you would export all textures to a folder called `adder` in the same directory. Then, when you import into Sollumz, all textures will be automatically loaded from the `adder` folder.

***

### My MLO shows up in CodeWalker but not in game.

* Make sure you generate a "\_manifest.ymf" file from the CodeWalker project window with your MLO, YMAP, and YTYP in it.

***

### I'm getting an error when importing a file.

* 9 out of 10 times it is due to having an outdated Sollumz version. Try updating.

***

### I'm getting the message `No Sollumz objects in the scene to export!` or `No Sollumz objects selected for export!`

* Check if the "Limit to Selected" export option is ticked. If so, only the selected objects will export.
* Make sure all of your objects have their sollum type set, otherwise, they will not be recognized by the add-on.
* As a last resort, you can select the parent object and use `Sollumz Tools > General > Debug > Fix Hierarchy`

***

### I'm getting the error `TypeError: create_uvsphere: keyword "diameter" is invalid for this operator.`

* Update your Sollumz.

***

### I'm getting the error `KeyError: 'bpy_prop_collection[key]: key "Image Texture" not found'`

* One of your materials has a missing node connection between Color node and an Image Texture, which is 100% needed in order to export the model.
* Check shading tab to find more.

***

### I'm getting the error `KeyError: 'bpy_prop_collection[key]: key "Principled BSDF" not found'`

* Only the Principled BSDF shader is supported during material conversion operations, anything else must be converted or recreated using Principled BSDF as base.
* Make sure Blender language is set to **English**.

***

### I created a collision (external or embedded) but it isn't working.

* Remember to apply `General (default)` flags to your `Bound GeometryBVH` object from the `Sollumz Tools > Collision Tools > Flag Presets` menu.

***

### I'm having issues importing the file into OpenIV

* Since this plugin was designed around CodeWalker's XML file formats, OpenIV is not explicitly supported. You may experience issues going from Sollumz > CodeWalker > OpenIV. It's highly recommended that you just use CodeWalker.
