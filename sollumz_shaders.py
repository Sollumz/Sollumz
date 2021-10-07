import bpy 

def get_child_node(node):
    
    if(node == None): 
        return None
    
    for output in node.outputs:
        if(len(output.links) == 1):
            return output.links[0].to_node

def get_list_of_child_nodes(node):
    
    all_nodes = []
    all_nodes.append(node)
    
    searching = True 
    child = get_child_node(node)
    
    while(searching):        
        
        
        if(isinstance(child, bpy.types.ShaderNodeBsdfPrincipled)):
            pass
        elif(isinstance(child, bpy.types.ShaderNodeOutputMaterial)):
            pass
        else:
            all_nodes.append(child)
        
        child = get_child_node(child)
        
        if(child == None):
            searching = False
            
        
        
    return all_nodes

def check_if_node_has_child(node):
    
    haschild = False    
    for output in node.outputs:
        if(len(output.links) > 0):
                    haschild = True
    return haschild

def organize_node_tree(node_tree):
    
    level = 0
    singles_x = 0

    grid_x = 600
    grid_y = -300
    row_count = 0
    
    for n in node_tree.nodes:
        
        if(isinstance(n, bpy.types.ShaderNodeValue)):
            n.location.x = grid_x
            n.location.y = grid_y
            grid_x += 150
            row_count += 1
            if(row_count == 4):
                grid_y -= 100
                row_count = 0
                grid_x = 600
                
        if(isinstance(n, bpy.types.ShaderNodeBsdfPrincipled)):
            n.location.x = 0 
            n.location.y = -300
        if(isinstance(n, bpy.types.ShaderNodeOutputMaterial)):
            n.location.y = -300 
            n.location.x = 300
        
        if(isinstance(n, bpy.types.ShaderNodeTexImage)):
            
            haschild = check_if_node_has_child(n)
            if(haschild):
                level -= 250
                all_nodes = get_list_of_child_nodes(n)
                
                idx = 0
                for n in all_nodes:
                    try:
                        x = -300 * (len(all_nodes) - idx)
                        
                        n.location.x = x
                        n.location.y = level 
                        
                        idx += 1
                    except: 
                        print("error")
            else:
                n.location.x = singles_x
                n.location.y = 100
                singles_x += 300

def create_image_node(node_tree, param):
    
    imgnode = node_tree.nodes.new("ShaderNodeTexImage")
    imgnode.name = param.name
    #imgnode.img = param.DefaultValue
    bsdf = node_tree.nodes["Principled BSDF"]
    links = node_tree.links

    if("Diffuse" in param.name):    
        links.new(imgnode.outputs["Color"], bsdf.inputs["Base Color"])
        links.new(imgnode.outputs["Alpha"], bsdf.inputs["Alpha"])
    elif("Bump" in param.name):    
        normalmap = node_tree.nodes.new("ShaderNodeNormalMap")
        links.new(imgnode.outputs["Color"], normalmap.inputs["Color"])
        links.new(normalmap.outputs["Normal"], bsdf.inputs["Normal"])
    elif("Spec" in param.name):    
        links.new(imgnode.outputs["Color"], bsdf.inputs["Specular"])

def create_vector_nodes(node_tree, param):
    
    vnodex = node_tree.nodes.new("ShaderNodeValue")
    vnodex.name = param.name + "_x"
    vnodex.outputs[0].default_value = param.value[0]
    
    vnodey = node_tree.nodes.new("ShaderNodeValue")
    vnodey.name = param.name + "_y"
    vnodey.outputs[0].default_value = param.value[1]
    
    vnodez = node_tree.nodes.new("ShaderNodeValue")
    vnodez.name = param.name + "_z"
    vnodez.outputs[0].default_value = param.value[2]
    
    vnodew = node_tree.nodes.new("ShaderNodeValue")
    vnodew.name = param.name + "_w"
    vnodew.outputs[0].default_value = param.value[3]

def create_shader(shadername, shadermanager):

    mat = bpy.data.materials.new(shadername)
    mat.sollum_type = "sollumz_gta_material"
    mat.use_nodes = True

    parameters = shadermanager.shaders[shadername].parameters
    node_tree = mat.node_tree

    for param in parameters:
        if(param.type == "Texture"):
            create_image_node(node_tree, param)
        elif(param.type == "Vector"):
            create_vector_nodes(node_tree, param)

    organize_node_tree(node_tree)

    return mat

collisionmats = {
        0:["DEFAULT",(255,0,255,255)],
        1:["CONCRETE",(145,145,145,255)],
        2:["CONCRETE_POTHOLE",(145,145,145,255)],
        3:["CONCRETE_DUSTY",(145,140,130,255)],
        4:["TARMAC",(90,90,90,255)],
        5:["TARMAC_PAINTED",(90,90,90,255)],
        6:["TARMAC_POTHOLE",(70,70,70,255)],
        7:["RUMBLE_STRIP",(90,90,90,255)],
        8:["BREEZE_BLOCK",(145,145,145,255)],
        9:["ROCK",(185,185,185,255)],
        10:["ROCK_MOSSY",(185,185,185,255)],
        11:["STONE",(185,185,185,255)],
        12:["COBBLESTONE",(185,185,185,255)],
        13:["BRICK",(195,95,30,255)],
        14:["MARBLE",(195,155,145,255)],
        15:["PAVING_SLAB",(200,165,130,255)],
        16:["SANDSTONE_SOLID",(215,195,150,255)],
        17:["SANDSTONE_BRITTLE",(205,180,120,255)],
        18:["SAND_LOOSE",(235,220,190,255)],
        19:["SAND_COMPACT",(250,240,220,255)],
        20:["SAND_WET",(190,185,165,255)],
        21:["SAND_TRACK",(250,240,220,255)],
        22:["SAND_UNDERWATER",(135,130,120,255)],
        23:["SAND_DRY_DEEP",(110,100,85,255)],
        24:["SAND_WET_DEEP",(110,100,85,255)],
        25:["ICE",(200,250,255,255)],
        26:["ICE_TARMAC",(200,250,255,255)],
        27:["SNOW_LOOSE",(255,255,255,255)],
        28:["SNOW_COMPACT",(255,255,255,255)],
        29:["SNOW_DEEP",(255,255,255,255)],
        30:["SNOW_TARMAC",(255,255,255,255)],
        31:["GRAVEL_SMALL",(255,255,255,255)],
        32:["GRAVEL_LARGE",(255,255,255,255)],
        33:["GRAVEL_DEEP",(255,255,255,255)],
        34:["GRAVEL_TRAIN_TRACK",(145,140,130,255)],
        35:["DIRT_TRACK",(175,160,140,255)],
        36:["MUD_HARD",(175,160,140,255)],
        37:["MUD_POTHOLE",(105,95,75,255)],
        38:["MUD_SOFT",(105,95,75,255)],
        39:["MUD_UNDERWATER",(75,65,50,255)],
        40:["MUD_DEEP",(105,95,75,255)],
        41:["MARSH",(105,95,75,255)],
        42:["MARSH_DEEP",(105,95,75,255)],
        43:["SOIL",(105,95,75,255)],
        44:["CLAY_HARD",(160,160,160,255)],
        45:["CLAY_SOFT",(160,160,160,255)],
        46:["GRASS_LONG",(130,205,75,255)],
        47:["GRASS",(130,205,75,255)],
        48:["GRASS_SHORT",(130,205,75,255)],
        49:["HAY",(240,205,125,255)],
        50:["BUSHES",(85,160,30,255)],
        51:["TWIGS",(115,100,70,255)],
        52:["LEAVES",(70,100,50,255)],
        53:["WOODCHIPS",(115,100,70,255)],
        54:["TREE_BARK",(115,100,70,255)],
        55:["METAL_SOLID_SMALL",(155,180,190,255)],
        56:["METAL_SOLID_MEDIUM",(155,180,190,255)],
        57:["METAL_SOLID_LARGE",(155,180,190,255)],
        58:["METAL_HOLLOW_SMALL",(155,180,190,255)],
        59:["METAL_HOLLOW_MEDIUM",(155,180,190,255)],
        60:["METAL_HOLLOW_LARGE",(155,180,190,255)],
        61:["METAL_CHAINLINK_SMALL",(155,180,190,255)],
        62:["METAL_CHAINLINK_LARGE",(155,180,190,255)],
        63:["METAL_CORRUGATED_IRON",(155,180,190,255)],
        64:["METAL_GRILLE",(155,180,190,255)],
        65:["METAL_RAILING",(155,180,190,255)],
        66:["METAL_DUCT",(155,180,190,255)],
        67:["METAL_GARAGE_DOOR",(155,180,190,255)],
        68:["METAL_MANHOLE",(155,180,190,255)],
        69:["WOOD_SOLID_SMALL",(155,130,95,255)],
        70:["WOOD_SOLID_MEDIUM",(155,130,95,255)],
        71:["WOOD_SOLID_LARGE",(155,130,95,255)],
        72:["WOOD_SOLID_POLISHED",(155,130,95,255)],
        73:["WOOD_FLOOR_DUSTY",(165,145,110,255)],
        74:["WOOD_HOLLOW_SMALL",(170,150,125,255)],
        75:["WOOD_HOLLOW_MEDIUM",(170,150,125,255)],
        76:["WOOD_HOLLOW_LARGE",(170,150,125,255)],
        77:["WOOD_CHIPBOARD",(170,150,125,255)],
        78:["WOOD_OLD_CREAKY",(155,130,95,255)],
        79:["WOOD_HIGH_DENSITY",(155,130,95,255)],
        80:["WOOD_LATTICE",(155,130,95,255)],
        81:["CERAMIC",(220,210,195,255)],
        82:["ROOF_TILE",(220,210,195,255)],
        83:["ROOF_FELT",(165,145,110,255)],
        84:["FIBREGLASS",(255,250,210,255)],
        85:["TARPAULIN",(255,250,210,255)],
        86:["PLASTIC",(255,250,210,255)],
        87:["PLASTIC_HOLLOW",(240,230,185,255)],
        88:["PLASTIC_HIGH_DENSITY",(255,250,210,255)],
        89:["PLASTIC_CLEAR",(255,250,210,255)],
        90:["PLASTIC_HOLLOW_CLEAR",(240,230,185,255)],
        91:["PLASTIC_HIGH_DENSITY_CLEAR",(255,250,210,255)],
        92:["FIBREGLASS_HOLLOW",(240,230,185,255)],
        93:["RUBBER",(70,70,70,255)],
        94:["RUBBER_HOLLOW",(70,70,70,255)],
        95:["LINOLEUM",(205,150,80,255)],
        96:["LAMINATE",(170,150,125,255)],
        97:["CARPET_SOLID",(250,100,100,255)],
        98:["CARPET_SOLID_DUSTY",(255,135,135,255)],
        99:["CARPET_FLOORBOARD",(250,100,100,255)],
        100:["CLOTH",(250,100,100,255)],
        101:["PLASTER_SOLID",(145,145,145,255)],
        102:["PLASTER_BRITTLE",(225,225,225,255)],
        103:["CARDBOARD_SHEET",(120,115,95,255)],
        104:["CARDBOARD_BOX",(120,115,95,255)],
        105:["PAPER",(230,225,220,255)],
        106:["FOAM",(230,235,240,255)],
        107:["FEATHER_PILLOW",(230,230,230,255)],
        108:["POLYSTYRENE",(255,250,210,255)],
        109:["LEATHER",(250,100,100,255)],
        110:["TVSCREEN",(115,125,125,255)],
        111:["SLATTED_BLINDS",(255,250,210,255)],
        112:["GLASS_SHOOT_THROUGH",(205,240,255,255)],
        113:["GLASS_BULLETPROOF",(115,125,125,255)],
        114:["GLASS_OPAQUE",(205,240,255,255)],
        115:["PERSPEX",(205,240,255,255)],
        116:["CAR_METAL",(255,255,255,255)],
        117:["CAR_PLASTIC",(255,255,255,255)],
        118:["CAR_SOFTTOP",(250,100,100,255)],
        119:["CAR_SOFTTOP_CLEAR",(250,100,100,255)],
        120:["CAR_GLASS_WEAK",(210,245,245,255)],
        121:["CAR_GLASS_MEDIUM",(210,245,245,255)],
        122:["CAR_GLASS_STRONG",(210,245,245,255)],
        123:["CAR_GLASS_BULLETPROOF",(210,245,245,255)],
        124:["CAR_GLASS_OPAQUE",(210,245,245,255)],
        125:["WATER",(55,145,230,255)],
        126:["BLOOD",(205,5,5,255)],
        127:["OIL",(80,65,65,255)],
        128:["PETROL",(70,100,120,255)],
        129:["FRESH_MEAT",(255,55,20,255)],
        130:["DRIED_MEAT",(185,100,85,255)],
        131:["EMISSIVE_GLASS",(205,240,255,255)],
        132:["EMISSIVE_PLASTIC",(255,250,210,255)],
        133:["VFX_METAL_ELECTRIFIED",(155,180,190,255)],
        134:["VFX_METAL_WATER_TOWER",(155,180,190,255)],
        135:["VFX_METAL_STEAM",(155,180,190,255)],
        136:["VFX_METAL_FLAME",(155,180,190,255)],
        137:["PHYS_NO_FRICTION",(0,0,0,255)],
        138:["PHYS_GOLF_BALL",(0,0,0,255)],
        139:["PHYS_TENNIS_BALL",(0,0,0,255)],
        140:["PHYS_CASTER",(0,0,0,255)],
        141:["PHYS_CASTER_RUSTY",(0,0,0,255)],
        142:["PHYS_CAR_VOID",(0,0,0,255)],
        143:["PHYS_PED_CAPSULE",(0,0,0,255)],
        144:["PHYS_ELECTRIC_FENCE",(0,0,0,255)],
        145:["PHYS_ELECTRIC_METAL",(0,0,0,255)],
        146:["PHYS_BARBED_WIRE",(0,0,0,255)],
        147:["PHYS_POOLTABLE_SURFACE",(155,130,95,255)],
        148:["PHYS_POOLTABLE_CUSHION",(155,130,95,255)],
        149:["PHYS_POOLTABLE_BALL",(255,250,210,255)],
        150:["BUTTOCKS",(0,0,0,255)],
        151:["THIGH_LEFT",(0,0,0,255)],
        152:["SHIN_LEFT",(0,0,0,255)],
        153:["FOOT_LEFT",(0,0,0,255)],
        154:["THIGH_RIGHT",(0,0,0,255)],
        155:["SHIN_RIGHT",(0,0,0,255)],
        156:["FOOT_RIGHT",(0,0,0,255)],
        157:["SPINE0",(0,0,0,255)],
        158:["SPINE1",(0,0,0,255)],
        159:["SPINE2",(0,0,0,255)],
        160:["SPINE3",(0,0,0,255)],
        161:["CLAVICLE_LEFT",(0,0,0,255)],
        162:["UPPER_ARM_LEFT",(0,0,0,255)],
        163:["LOWER_ARM_LEFT",(0,0,0,255)],
        164:["HAND_LEFT",(0,0,0,255)],
        165:["CLAVICLE_RIGHT",(0,0,0,255)],
        166:["UPPER_ARM_RIGHT",(0,0,0,255)],
        167:["LOWER_ARM_RIGHT",(0,0,0,255)],
        168:["HAND_RIGHT",(0,0,0,255)],
        169:["NECK",(0,0,0,255)],
        170:["HEAD",(0,0,0,255)],
        171:["ANIMAL_DEFAULT",(0,0,0,255)],
        172:["CAR_ENGINE",(255,255,255,255)],
        173:["PUDDLE",(55,145,230,255)],
        174:["CONCRETE_PAVEMENT",(145,145,145,255)],
        175:["BRICK_PAVEMENT",(195,95,30,255)],
        176:["PHYS_DYNAMIC_COVER_BOUND",(0,0,0,255)],
        177:["VFX_WOOD_BEER_BARREL",(155,130,95,255)],
        178:["WOOD_HIGH_FRICTION",(155,130,95,255)],
        179:["ROCK_NOINST",(185,185,185,255)],
        180:["BUSHES_NOINST",(85,160,30,255)],
        181:["METAL_SOLID_ROAD_SURFACE",(155,180,190,255)]}

def create_collision_material_from_index(collisionindex: int):

    matinfo = collisionmats[collisionindex] 
    
    # Check for existing material
    # if matinfo[0] in bpy.data.materials.keys():
    #     return bpy.data.materials[matinfo[0]]

    mat = bpy.data.materials.new(matinfo[0])
    mat.sollum_type = "sollumz_gta_collision_material"
    mat.collision_properties.collision_index = collisionindex
    mat.use_nodes = True
    r = matinfo[1][0] / 255
    g = matinfo[1][1] / 255
    b = matinfo[1][2] / 255
    #a = matinfo[1][3] / 255
    bsdf = mat.node_tree.nodes["Principled BSDF"].inputs[0].default_value = (r, g, b, 1)
    
    return mat

def create_collision_material_from_type(materialtype : str):

    for i in range(len(collisionmats)):
        type = collisionmats[i][0]
        if(type == materialtype):
            return create_collision_material_from_index(i)