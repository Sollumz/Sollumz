# 📋 Features

[**Key**](#user-content-fn-1)[^1]

🟩 Fully implemented

🟧 Partially implemented

🟥 Not implemented

{% hint style="info" %}
Sollumz cannot import binary formats directly. You must convert them to XML first using CodeWalker!
{% endhint %}

{% hint style="info" %}
Since this plugin was designed around CodeWalker's XML file formats, OpenIV is not explicitly supported. You may experience issues going from Sollumz > CodeWalker > OpenIV. It's highly recommended that you just use CodeWalker.
{% endhint %}

### **File Formats**

<table><thead><tr><th width="211">Asset Type</th><th width="138">File Extension</th><th width="84" align="center">Import</th><th align="center">Export</th></tr></thead><tbody><tr><td>Drawable</td><td>.ydr.xml</td><td align="center">🟩</td><td align="center">🟩</td></tr><tr><td>Drawable Dictionary</td><td>.ydd.xml</td><td align="center">🟩</td><td align="center">🟩</td></tr><tr><td>Static Collision</td><td>.ybn.xml</td><td align="center">🟩</td><td align="center">🟩</td></tr><tr><td>Fragment</td><td>.yft.xml</td><td align="center">🟧</td><td align="center">🟧</td></tr><tr><td>Clip Dictionary</td><td>.ycd.xml</td><td align="center">🟧</td><td align="center">🟧</td></tr><tr><td>Map Data</td><td>.ymap.xml</td><td align="center">🟩</td><td align="center">🟩</td></tr><tr><td>Archetype Definition</td><td>.ytyp.xml</td><td align="center">🟩</td><td align="center">🟩</td></tr></tbody></table>

### Specific Features

#### Drawable (.ydr)

<table><thead><tr><th width="416">Feature</th><th align="center">Support</th></tr></thead><tbody><tr><td>Mesh editing</td><td align="center">🟩</td></tr><tr><td>Embedded collisions</td><td align="center">🟩</td></tr><tr><td>Shader editing</td><td align="center">🟩</td></tr><tr><td>Terrain shader painting</td><td align="center">🟩</td></tr><tr><td>Tint shaders</td><td align="center">🟩</td></tr><tr><td>Props</td><td align="center">🟩</td></tr><tr><td>Shader preview</td><td align="center">🟧</td></tr></tbody></table>

#### Drawable Dictionary (.ydd)

<table><thead><tr><th width="414">Feature</th><th align="center">Support</th></tr></thead><tbody><tr><td>Editing Drawable Dictionaries</td><td align="center">🟩</td></tr><tr><td>Importing with external skeleton</td><td align="center">🟩</td></tr></tbody></table>

#### Static Collision (.ybn)

<table><thead><tr><th width="414">Feature</th><th align="center">Support</th></tr></thead><tbody><tr><td>Collision editing</td><td align="center">🟩</td></tr></tbody></table>

#### Fragment (.yft)

<table><thead><tr><th width="414">Feature</th><th align="center">Support</th></tr></thead><tbody><tr><td>Vehicles</td><td align="center">🟩</td></tr><tr><td>Breakable props (i.e. street lights)</td><td align="center">🟩</td></tr><tr><td>Explodable props (i.e. gas tanks)</td><td align="center">🟥</td></tr><tr><td>Ped yfts</td><td align="center">🟥</td></tr><tr><td>Cloth yfts</td><td align="center">🟥</td></tr></tbody></table>

<details>

<summary>Unsupported Ped YFTs</summary>

The following is a list of unsupported ped YFTs. These YFTs contain unknown ragdoll physics data that is not handled by Sollumz. Currently, it is not possible to create completely custom player skeletons.

```
z_z_alien.yft 
z_z_fred.yft 
z_z_fred_large.yft 
z_z_wilma.yft 
z_z_wilma_large.yft 
a_c_boar.yft 
a_c_cat_01.yft 
a_c_chickenhawk.yft 
a_c_chimp.yft 
a_c_cormorant.yft 
a_c_cow.yft 
a_c_coyote.yft 
a_c_crow.yft 
a_c_deer.yft 
a_c_dolphin.yft 
a_c_fish.yft 
a_c_hen.yft 
a_c_humpback.yft 
a_c_killerwhale.yft 
a_c_pig.yft 
a_c_pigeon.yft 
a_c_poodle.yft 
a_c_pug.yft 
a_c_rabbit_01.yft 
a_c_rat.yft 
a_c_rhesus.yft 
a_c_seagull.yft 
a_c_sharkhammer.yft 
a_c_stingray.yft 
a_c_westy.yft 
a_c_whalegrey.yft 
a_c_chop.yft 
a_c_husky.yft 
a_c_mtlion.yft 
a_c_retriever.yft 
a_c_rottweiler.yft 
a_c_sharktiger.yft 
a_c_shepherd.yft 
a_c_chimp_02.yft 
a_c_rabbit_02.yft 
a_c_panther.yft 
a_c_chickenhawk.yft 
a_c_rhesus.yft 
a_c_seagull.yft 
a_c_chop_02.yft 
a_c_chickenhawk.yft 
```

</details>

#### Clip Dictionary (.ycd)

<table><thead><tr><th width="416">Feature</th><th align="center">Support</th></tr></thead><tbody><tr><td>Skeletal Animations</td><td align="center">🟩</td></tr><tr><td>UV Animations (export only)</td><td align="center">🟧</td></tr><tr><td>Camera Animations</td><td align="center">🟥</td></tr><tr><td>Light Animations</td><td align="center">🟥</td></tr></tbody></table>

#### **Map Data (.ymap)**

<table><thead><tr><th width="414">Feature</th><th align="center">Support</th></tr></thead><tbody><tr><td>Entities</td><td align="center">🟩</td></tr><tr><td>Box Occluders</td><td align="center">🟩</td></tr><tr><td>Car Generators</td><td align="center">🟩</td></tr><tr><td>Model Occluders</td><td align="center">🟩</td></tr><tr><td>Physics Dictionaries</td><td align="center">🟥</td></tr><tr><td>Time Cycle</td><td align="center">🟥</td></tr><tr><td>Lod Lights</td><td align="center">🟥</td></tr></tbody></table>

#### Archetype Definition (.ytyp)

<table><thead><tr><th width="414">Feature</th><th align="center">Support</th></tr></thead><tbody><tr><td>Base Archetypes</td><td align="center">🟩</td></tr><tr><td>Time Archetypes</td><td align="center">🟩</td></tr><tr><td>MLO Archetypes</td><td align="center">🟩</td></tr><tr><td>Create rooms from vertices</td><td align="center">🟩</td></tr><tr><td>Create portals from vertices</td><td align="center">🟩</td></tr><tr><td>Entity Extensions</td><td align="center">🟩</td></tr><tr><td>Entity Sets</td><td align="center">🟩</td></tr></tbody></table>

[^1]: 
