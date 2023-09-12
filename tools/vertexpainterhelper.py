from ..sollumz_properties import red_id, blue_id, green_id, alpha_id, valid_channel_ids, isolate_mode_name_prefix

def posterize(value, steps):
    return round(value * steps) / steps


def remap(value, min0, max0, min1, max1):
    r0 = max0 - min0
    if r0 == 0:
        return min1
    r1 = max1 - min1
    return ((value - min0) * r1) / r0 + min1


def channel_id_to_idx(id):
    if id is red_id:
        return 0
    if id is green_id:
        return 1
    if id is blue_id:
        return 2
    if id is alpha_id:
        return 3
    # default to red
    return 0


def get_active_channel_mask(active_channels):
    rgba_mask = [True if cid in active_channels else False for cid in valid_channel_ids]
    return rgba_mask


def get_isolated_channel_ids(vcol):
    vcol_id = vcol.name
    prefix = isolate_mode_name_prefix
    prefix_len = len(prefix)

    if vcol_id.startswith(prefix) and len(vcol_id) > prefix_len + 3:
        iso_vcol_id = vcol_id[prefix_len + 3:] # get vcol id from end of string
        iso_channel_id = vcol_id[prefix_len + 1] # get channel id
        if iso_channel_id in valid_channel_ids:
            return [iso_vcol_id, iso_channel_id]

    return None


def rgb_to_luminosity(color):
    # Y = 0.299 R + 0.587 G + 0.114 B
    return color[0] * 0.299 + color[1] * 0.587 + color[2] * 0.114


def convert_rgb_to_luminosity(mesh, src_vcol, dst_vcol, dst_channel_idx, dst_all_channels=False):
    if dst_all_channels:
        for loop_index, loop in enumerate(mesh.loops):
            c = src_vcol.data[loop_index].color
            luminosity = rgb_to_luminosity(c)
            c[0] = luminosity # assigning this way will preserve alpha
            c[1] = luminosity
            c[2] = luminosity
            dst_vcol.data[loop_index].color = c
    else:
        for loop_index, loop in enumerate(mesh.loops):
            luminosity = rgb_to_luminosity(src_vcol.data[loop_index].color)
            dst_vcol.data[loop_index].color[dst_channel_idx] = luminosity


# alpha_mode
# 'OVERWRITE' - replace with copied channel value
# 'PRESERVE' - keep existing alpha value
# 'FILL' - fill alpha with 1.0
def copy_channel(mesh, src_vcol, dst_vcol, src_channel_idx, dst_channel_idx, swap=False,
                 dst_all_channels=False, alpha_mode='PRESERVE'):
    if dst_all_channels:
        color_size = len(src_vcol.data[0].color) if len(src_vcol.data) > 0 else 3
        if alpha_mode == 'OVERWRITE' or color_size < 4:
            for loop_index, loop in enumerate(mesh.loops):
                src_val = src_vcol.data[loop_index].color[src_channel_idx]
                dst_vcol.data[loop_index].color = [src_val] * color_size
        elif alpha_mode == 'FILL':
            for loop_index, loop in enumerate(mesh.loops):
                src_val = src_vcol.data[loop_index].color[src_channel_idx]
                dst_vcol.data[loop_index].color = [src_val, src_val, src_val, 1.0]
        else: # default to preserve
            for loop_index, loop in enumerate(mesh.loops):
                c = src_vcol.data[loop_index].color
                src_val = c[src_channel_idx]
                c[0] = src_val
                c[1] = src_val
                c[2] = src_val
                dst_vcol.data[loop_index].color = c
    else:
        if swap:
            for loop_index, loop in enumerate(mesh.loops):
                src_val = src_vcol.data[loop_index].color[src_channel_idx]
                dst_val = dst_vcol.data[loop_index].color[dst_channel_idx]
                dst_vcol.data[loop_index].color[dst_channel_idx] = src_val
                src_vcol.data[loop_index].color[src_channel_idx] = dst_val
        else:
            for loop_index, loop in enumerate(mesh.loops):
                dst_vcol.data[loop_index].color[dst_channel_idx] = src_vcol.data[loop_index].color[src_channel_idx]

    mesh.update()


def blend_channels(mesh, src_vcol, dst_vcol, src_channel_idx, dst_channel_idx, result_channel_idx, operation='ADD'):
    if operation == 'ADD':
        for loop_index, loop in enumerate(mesh.loops):
            val = src_vcol.data[loop_index].color[src_channel_idx] + dst_vcol.data[loop_index].color[dst_channel_idx]
            dst_vcol.data[loop_index].color[result_channel_idx] = max(0.0, min(val, 1.0))  # clamp
    elif operation == 'SUB':
        for loop_index, loop in enumerate(mesh.loops):
            val = src_vcol.data[loop_index].color[src_channel_idx] - dst_vcol.data[loop_index].color[dst_channel_idx]
            dst_vcol.data[loop_index].color[result_channel_idx] = max(0.0, min(val, 1.0))  # clamp
    elif operation == 'MUL':
        for loop_index, loop in enumerate(mesh.loops):
            val = src_vcol.data[loop_index].color[src_channel_idx] * dst_vcol.data[loop_index].color[dst_channel_idx]
            dst_vcol.data[loop_index].color[result_channel_idx] = val
    elif operation == 'DIV':
        for loop_index, loop in enumerate(mesh.loops):
            src = src_vcol.data[loop_index].color[src_channel_idx]
            dst = dst_vcol.data[loop_index].color[dst_channel_idx]
            val = 0.0 if src == 0.0 else 1.0 if dst == 0.0 else src / dst
            dst_vcol.data[loop_index].color[result_channel_idx] = val
    elif operation == 'LIGHTEN':
        for loop_index, loop in enumerate(mesh.loops):
            src = src_vcol.data[loop_index].color[src_channel_idx]
            dst = dst_vcol.data[loop_index].color[dst_channel_idx]
            dst_vcol.data[loop_index].color[result_channel_idx] = src if src > dst else dst
    elif operation == 'DARKEN':
        for loop_index, loop in enumerate(mesh.loops):
            src = src_vcol.data[loop_index].color[src_channel_idx]
            dst = dst_vcol.data[loop_index].color[dst_channel_idx]
            dst_vcol.data[loop_index].color[result_channel_idx] = src if src < dst else dst
    elif operation == 'MIX':
        for loop_index, loop in enumerate(mesh.loops):
            dst_vcol.data[loop_index].color[result_channel_idx] = src_vcol.data[loop_index].color[src_channel_idx]
    else:
        return

    mesh.update()

def fill_selected(mesh, vcol, color, active_channels):
    if mesh.use_paint_mask:
        selected_faces = [face for face in mesh.polygons if face.select]
        for face in selected_faces:
            for loop_index in face.loop_indices:
                c = vcol.data[loop_index].color
                if red_id in active_channels:
                    c[0] = color[0]
                if green_id in active_channels:
                    c[1] = color[1]
                if blue_id in active_channels:
                    c[2] = color[2]
                if alpha_id in active_channels:
                    c[3] = color[3]
                vcol.data[loop_index].color = c
    else:
        vertex_mask = True if mesh.use_paint_mask_vertex else False
        verts = mesh.vertices

        for loop_index, loop in enumerate(mesh.loops):
            if not vertex_mask or verts[loop.vertex_index].select:
                c = vcol.data[loop_index].color
                if red_id in active_channels:
                    c[0] = color[0]
                if green_id in active_channels:
                    c[1] = color[1]
                if blue_id in active_channels:
                    c[2] = color[2]
                if alpha_id in active_channels:
                    c[3] = color[3]
                vcol.data[loop_index].color = c

    mesh.update()


def invert_selected(mesh, vcol, active_channels):
    if mesh.use_paint_mask:
        selected_faces = [face for face in mesh.polygons if face.select]
        for face in selected_faces:
            for loop_index in face.loop_indices:
                c = vcol.data[loop_index].color
                if red_id in active_channels:
                    c[0] = 1 - c[0]
                if green_id in active_channels:
                    c[1] = 1 - c[1]
                if blue_id in active_channels:
                    c[2] = 1 - c[2]
                if alpha_id in active_channels:
                    c[3] = 1 - c[3]
                vcol.data[loop_index].color = c
    else:
        vertex_mask = True if mesh.use_paint_mask_vertex else False
        verts = mesh.vertices

        for loop_index, loop in enumerate(mesh.loops):
            if not vertex_mask or verts[loop.vertex_index].select:
                c = vcol.data[loop_index].color
                if red_id in active_channels:
                    c[0] = 1 - c[0]
                if green_id in active_channels:
                    c[1] = 1 - c[1]
                if blue_id in active_channels:
                    c[2] = 1 - c[2]
                if alpha_id in active_channels:
                    c[3] = 1 - c[3]
                vcol.data[loop_index].color = c

    mesh.update()

def posterize_selected(mesh, vcol, steps, active_channels):
    if mesh.use_paint_mask:
        selected_faces = [face for face in mesh.polygons if face.select]
        for face in selected_faces:
            for loop_index in face.loop_indices:
                c = vcol.data[loop_index].color
                if red_id in active_channels:
                    c[0] = posterize(c[0], steps)
                if green_id in active_channels:
                    c[1] = posterize(c[1], steps)
                if blue_id in active_channels:
                    c[2] = posterize(c[2], steps)
                if alpha_id in active_channels:
                    c[3] = posterize(c[3], steps)
                vcol.data[loop_index].color = c
    else:
        vertex_mask = True if mesh.use_paint_mask_vertex else False
        verts = mesh.vertices

        for loop_index, loop in enumerate(mesh.loops):
            if not vertex_mask or verts[loop.vertex_index].select:
                c = vcol.data[loop_index].color
                if red_id in active_channels:
                    c[0] = posterize(c[0], steps)
                if green_id in active_channels:
                    c[1] = posterize(c[1], steps)
                if blue_id in active_channels:
                    c[2] = posterize(c[2], steps)
                if alpha_id in active_channels:
                    c[3] = posterize(c[3], steps)
                vcol.data[loop_index].color = c

    mesh.update()


def channel_id_to_idx(id):
    if id is red_id:
        return 0
    if id is green_id:
        return 1
    if id is blue_id:
        return 2
    if id is alpha_id:
        return 3
    # default to red
    return 0


def copy_channel(mesh, src_vcol, dst_vcol, src_channel_idx, dst_channel_idx, swap=False,
                 dst_all_channels=False, alpha_mode='PRESERVE'):
    if dst_all_channels:
        color_size = len(src_vcol.data[0].color) if len(src_vcol.data) > 0 else 3
        if alpha_mode == 'OVERWRITE' or color_size < 4:
            for loop_index, loop in enumerate(mesh.loops):
                src_val = src_vcol.data[loop_index].color[src_channel_idx]
                dst_vcol.data[loop_index].color = [src_val] * color_size
        elif alpha_mode == 'FILL':
            for loop_index, loop in enumerate(mesh.loops):
                src_val = src_vcol.data[loop_index].color[src_channel_idx]
                dst_vcol.data[loop_index].color = [src_val, src_val, src_val, 1.0]
        else: # default to preserve
            for loop_index, loop in enumerate(mesh.loops):
                c = src_vcol.data[loop_index].color
                src_val = c[src_channel_idx]
                c[0] = src_val
                c[1] = src_val
                c[2] = src_val
                dst_vcol.data[loop_index].color = c
    else:
        if swap:
            for loop_index, loop in enumerate(mesh.loops):
                src_val = src_vcol.data[loop_index].color[src_channel_idx]
                dst_val = dst_vcol.data[loop_index].color[dst_channel_idx]
                dst_vcol.data[loop_index].color[dst_channel_idx] = src_val
                src_vcol.data[loop_index].color[src_channel_idx] = dst_val
        else:
            for loop_index, loop in enumerate(mesh.loops):
                dst_vcol.data[loop_index].color[dst_channel_idx] = src_vcol.data[loop_index].color[src_channel_idx]

    mesh.update()

def remap_selected(mesh, vcol, min0, max0, min1, max1, active_channels):
    if mesh.use_paint_mask:
        selected_faces = [face for face in mesh.polygons if face.select]
        for face in selected_faces:
            for loop_index in face.loop_indices:
                c = vcol.data[loop_index].color
                if red_id in active_channels:
                    c[0] = remap(c[0], min0, max0, min1, max1)
                if green_id in active_channels:
                    c[1] = remap(c[1], min0, max0, min1, max1)
                if blue_id in active_channels:
                    c[2] = remap(c[2], min0, max0, min1, max1)
                if alpha_id in active_channels:
                    c[3] = remap(c[3], min0, max0, min1, max1)
                vcol.data[loop_index].color = c
    else:
        vertex_mask = True if mesh.use_paint_mask_vertex else False
        verts = mesh.vertices

        for loop_index, loop in enumerate(mesh.loops):
            if not vertex_mask or verts[loop.vertex_index].select:
                c = vcol.data[loop_index].color
                if red_id in active_channels:
                    c[0] = remap(c[0], min0, max0, min1, max1)
                if green_id in active_channels:
                    c[1] = remap(c[1], min0, max0, min1, max1)
                if blue_id in active_channels:
                    c[2] = remap(c[2], min0, max0, min1, max1)
                if alpha_id in active_channels:
                    c[3] = remap(c[3], min0, max0, min1, max1)
                vcol.data[loop_index].color = c

    mesh.update()