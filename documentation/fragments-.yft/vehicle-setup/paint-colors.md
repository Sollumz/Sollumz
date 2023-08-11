# Paint Colors

Paint colors allow you to determine which materials represent the **Primary** color, **Secondary** color, **Wheel** color, **Interior Trim** color, and **Dashboard** color. To select the paint color for a material, navigate to `Material Properties > Sollumz > Fragment`.

<figure><img src="../../../.gitbook/assets/image (9).png" alt=""><figcaption><p>Material Properties > Sollumz > Fragment</p></figcaption></figure>

By default it will be "Not Paintable", meaning the shader will not be affected by any paint color.&#x20;

{% hint style="info" %}
Not all shaders are paintable. If you are trying to set up a paintable vehicle material and you are getting the "Not a paint shader" message, then you need to use a different shader. Typically you'd want to use a `vehicle_paint` shader for the body of a vehicle.
{% endhint %}
