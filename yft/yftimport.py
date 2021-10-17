from Sollumz.ydr.ydrimport import drawable_to_obj

def fragment_to_obj(fragment, filepath):

    drawable_to_obj(fragment.drawable, "", fragment.name)
    
    return