# 🚦 Vertex Groups, hierarchy and armature

### Create and assign Vertex Groups

To create a new vertex group, go to **Data** tab, click `+` in **Vertex Groups**, double click on the Group name and rename it to **bonnet**.

<figure><img src="../../.gitbook/assets/4_create_vertexgroup.gif" alt=""><figcaption><p>Process of creating a vertex group</p></figcaption></figure>

1. Change **Object Mode** to **Edit Mode.**
2. Switch to **Face Select.**
3. Select all faces by pressing `A` or using the `CTRL+A` shortcut.
4. Go to **Vertex Groups**, click Assign button and exit **Edit Mode**.

Now all of the selected faces are properly set to the **bonnet** vertex group**.**

<figure><img src="../../.gitbook/assets/5_assign_vertexgroup.gif" alt=""><figcaption><p>Assignment of faces to vertex group</p></figcaption></figure>

### Hierarchy

Our new custom bonnet model has to be considered by Sollumz as a valid part, so we have to move the mesh by expanding Adder's armature then drag and drop bonnet's Drawable Model inside `adder.mesh`

<figure><img src="../../.gitbook/assets/6_move_in_hierarchy.gif" alt=""><figcaption><p>Bonnet part moved into adder.mesh</p></figcaption></figure>

{% hint style="info" %}
You can delete the original bonnet, since is not needed anymore.
{% endhint %}

<figure><img src="../../.gitbook/assets/7_delete_bonnet.gif" alt=""><figcaption><p>Removal of vanilla bonnet part of adder.</p></figcaption></figure>

### Armature

A replacement custom part has also to be linked to the armature, you can do this via **Armature** modifier.

1. Go to **Modifiers** tab.
2. Add an **Armature** modifier.
3. Select your vehicle's armature.

<figure><img src="../../.gitbook/assets/8_armature.gif" alt=""><figcaption><p>Armature modifier creation</p></figcaption></figure>
