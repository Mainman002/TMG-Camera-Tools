import bpy, sys, os
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty, IntProperty, FloatProperty, FloatVectorProperty, PointerProperty
from bpy.types import Operator, Header
from bpy_extras.node_utils import find_node_input
from bl_ui.utils import PresetPanel


active_dict = {
    "type" : "PERSP", ##[ PERSP, ORTHO, PANO ]
    "focal_l" : 24,
    "sensor_w" : 36,
    "sensor_h" : 36,
    "ortho_scale" : 6,
    "clip_start" : 0.1,
    "clip_end" : 100,
    "use_dof" : True,
    "fStop" : 2.0,
    "track_to" : False,
    "cam_floor" : False,
    "cam_follow_path" : False,
    "cam_track_to" : False,
    "passepartout_alpha" : 0.5,
}

###### Blender Functions #################################################################

# Adapt properties editor panel to display in node editor. We have to
# copy the class rather than inherit due to the way bpy registration works.
def node_panel(cls):
    node_cls = type('NODE_' + cls.__name__, cls.__bases__, dict(cls.__dict__))

    node_cls.bl_space_type = 'NODE_EDITOR'
    node_cls.bl_region_type = 'UI'
    node_cls.bl_category = "Options"
    if hasattr(node_cls, 'bl_parent_id'):
        node_cls.bl_parent_id = 'NODE_' + node_cls.bl_parent_id

    return node_cls


def get_device_type(context):
    return context.preferences.addons[__package__].preferences.compute_device_type


def use_cpu(context):
    cscene = context.scene.cycles

    return (get_device_type(context) == 'NONE' or cscene.device == 'CPU')


def use_opencl(context):
    cscene = context.scene.cycles

    return (get_device_type(context) == 'OPENCL' and cscene.device == 'GPU')


def use_cuda(context):
    cscene = context.scene.cycles

    return (get_device_type(context) == 'CUDA' and cscene.device == 'GPU')


def use_optix(context):
    cscene = context.scene.cycles

    return (get_device_type(context) == 'OPTIX' and cscene.device == 'GPU')


def use_branched_path(context):
    cscene = context.scene.cycles

    return (cscene.progressive == 'BRANCHED_PATH' and not use_optix(context))


def use_sample_all_lights(context):
    cscene = context.scene.cycles

    return cscene.sample_all_lights_direct or cscene.sample_all_lights_indirect


def show_device_active(context):
    cscene = context.scene.cycles
    if cscene.device != 'GPU':
        return True
    return context.preferences.addons[__package__].preferences.has_active_device()

def show_optix_denoising(context):
    # OptiX AI denoiser can be used when at least one device supports OptiX
    return bool(context.preferences.addons[__package__].preferences.get_devices_for_type('OPTIX'))


def draw_samples_info(layout, context):
    cscene = context.scene.cycles
    integrator = cscene.progressive

    # Calculate sample values
    if integrator == 'PATH':
        aa = cscene.samples
        if cscene.use_square_samples:
            aa = aa * aa
    else:
        aa = cscene.aa_samples
        d = cscene.diffuse_samples
        g = cscene.glossy_samples
        t = cscene.transmission_samples
        ao = cscene.ao_samples
        ml = cscene.mesh_light_samples
        sss = cscene.subsurface_samples
        vol = cscene.volume_samples

        if cscene.use_square_samples:
            aa = aa * aa
            d = d * d
            g = g * g
            t = t * t
            ao = ao * ao
            ml = ml * ml
            sss = sss * sss
            vol = vol * vol

    # Draw interface
    # Do not draw for progressive, when Square Samples are disabled
    if use_branched_path(context) or (cscene.use_square_samples and integrator == 'PATH'):
        col = layout.column(align=True)
        col.scale_y = 0.6
        col.label(text="Total Samples:")
        col.separator()
        if integrator == 'PATH':
            col.label(text="%s AA" % aa)
        else:
            col.label(text="%s AA, %s Diffuse, %s Glossy, %s Transmission" %
                      (aa, d * aa, g * aa, t * aa))
            col.separator()
            col.label(text="%s AO, %s Mesh Light, %s Subsurface, %s Volume" %
                      (ao * aa, ml * aa, sss * aa, vol * aa))


###### TMG Functions #################################################################


def _change_ob(self, context, _ob):
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = _ob
    _ob.select_set(True) 
    return _ob


def _change_camera_presets(self, context):
    scene = context.scene
    tmg_cam_vars = scene.tmg_cam_vars
    camera = tmg_cam_vars.scene_camera

    
    ## divide sensor by 1.293 to get focal length (sometimes good values)
    
    if tmg_cam_vars.cam_sensor_format == '0':
        active_dict["focal_l"] = 18.56
        active_dict["sensor_w"] = 50
        active_dict["sensor_h"] = 50
        active_dict["ortho_scale"] = 33.17
#        active_dict["fStop"] = 2.0
        
    if tmg_cam_vars.cam_sensor_format == '1':
        active_dict["focal_l"] = 27.84
        active_dict["sensor_w"] = 50
        active_dict["sensor_h"] = 50
        active_dict["ortho_scale"] = 13.82
#        active_dict["fStop"] = 2.0
        
    if tmg_cam_vars.cam_sensor_format == '2':
        active_dict["focal_l"] = 38.66
        active_dict["sensor_w"] = 50
        active_dict["sensor_h"] = 50
        active_dict["ortho_scale"] = 5.76
#        active_dict["fStop"] = 2.0
        
    if tmg_cam_vars.cam_sensor_format == '3':
        active_dict["focal_l"] = 61.87
        active_dict["sensor_w"] = 50
        active_dict["sensor_h"] = 50
        active_dict["ortho_scale"] = 2.4
#        active_dict["fStop"] = 2.8
        
    if tmg_cam_vars.cam_sensor_format == '4':
        active_dict["focal_l"] = 162.41
        active_dict["sensor_w"] = 50
        active_dict["sensor_h"] = 50
        active_dict["ortho_scale"] = 1
#        active_dict["fStop"] = 2.8
    
    active_dict["fStop"] = camera.data.dof.aperture_fstop
    _set_cam_values(self, context)


def _get_aspect(_mode, _x, _y):
    if _mode == 0:
        tx = _x
        ty = _y

    elif _mode == 1:
        tx = _y
        ty = _x

    elif _mode == 2:
        tx = _x
        ty = _x

    return tx, ty


def _set_custom_property(_ob, _prop, _value):
    _ob[str(_prop)] = _value


def _get_custom_property(_ob, _prop):
    return _ob[str(_prop)]


def _get_res_preset(_mode):
    tmp_res_x = 640
    tmp_res_y = 480

    if _mode == 0: # VGA
        tmp_res_x = 640
        tmp_res_y = 480
    if _mode == 1: # HD
        tmp_res_x = 1280
        tmp_res_y = 720
    if _mode == 2: # HD-F
        tmp_res_x = 1920
        tmp_res_y = 1080
    if _mode == 3: # 2k
        tmp_res_x = 2560
        tmp_res_y = 1440
    if _mode == 4: # 4k
        tmp_res_x = 3840
        tmp_res_y = 2160
    if _mode == 5: # 8k
        tmp_res_x = 7680
        tmp_res_y = 4320

    return tmp_res_x, tmp_res_y


def _change_resolution_presets(self, context):
    scene = context.scene
    tmg_cam_vars = scene.tmg_cam_vars
    camera = tmg_cam_vars.scene_camera
    
    if tmg_cam_vars.cam_res_lock_modes == 0:
        tmg_cam_vars.const_res_x = scene.render.resolution_x
        tmg_cam_vars.const_res_y = scene.render.resolution_y
        
    if tmg_cam_vars.cam_res_lock_modes == 1:
        tmg_cam_vars.res_x = scene.render.resolution_x
        tmg_cam_vars.res_y = scene.render.resolution_y

    
    _set_custom_property( camera, "resolution", int(tmg_cam_vars.cam_resolution_presets) )
    _set_cam_res_values(self, context)


def _change_res_mode_presets(self, context):
    scene = context.scene
    tmg_cam_vars = scene.tmg_cam_vars
    camera = tmg_cam_vars.scene_camera
    
    _set_custom_property( camera, "res_mode", int(tmg_cam_vars.cam_resolution_mode_presets) )
    _set_cam_res_values(self, context)


def _change_res_lock(self, context):
    scene = context.scene
    tmg_cam_vars = scene.tmg_cam_vars
    camera = tmg_cam_vars.scene_camera
    
    if tmg_cam_vars.cam_res_lock_modes == '0':
        scene.render.resolution_x = tmg_cam_vars.const_res_x
        scene.render.resolution_y = tmg_cam_vars.const_res_y
        
    if tmg_cam_vars.cam_res_lock_modes == '1':
        scene.render.resolution_x = _get_custom_property(camera, "res_x")
        scene.render.resolution_y = _get_custom_property(camera, "res_y")
        
    if tmg_cam_vars.cam_res_lock_modes == '2':
        scene.render.resolution_x = tmg_cam_vars.res_x
        scene.render.resolution_y = tmg_cam_vars.res_y
    
    _set_cam_res_values(self, context)


def _set_cam_res_values(self, context):
    scene = context.scene
    tmg_cam_vars = scene.tmg_cam_vars
    camera = tmg_cam_vars.scene_camera
    
    if camera:
        tmp_res_x = 1920
        tmp_res_y = 1080
        res_x = tmp_res_x
        res_y = tmp_res_y
        
        res = _get_custom_property(camera, "resolution")
        mode = _get_custom_property(camera, "res_mode")
            
        if tmg_cam_vars.cam_res_lock_modes == '0':
            res_x = tmg_cam_vars.const_res_x
            res_y = tmg_cam_vars.const_res_y
            tmp_di = { 'x': _get_aspect( int(tmg_cam_vars.cam_resolution_mode_presets), res_x, res_y)[0], 'y': _get_aspect( int(tmg_cam_vars.cam_resolution_mode_presets), res_x, res_y)[1] }

        if tmg_cam_vars.cam_res_lock_modes == '1':
            res_x = _get_custom_property(camera, "res_x")
            res_y = _get_custom_property(camera, "res_y")
            tmp_di = { 'x': _get_aspect( int(tmg_cam_vars.cam_resolution_mode_presets), res_x, res_y)[0], 'y': _get_aspect( int(tmg_cam_vars.cam_resolution_mode_presets), res_x, res_y)[1] }

        if tmg_cam_vars.cam_res_lock_modes == '2':
            tmp_di = { 'x':_get_res_preset(res)[0], 'y':_get_res_preset(res)[1] }
            res_x = int( tmp_di['x'] )
            res_y = int( tmp_di['y'] )
            tmp_di = { 'x': _get_aspect( int(tmg_cam_vars.cam_resolution_mode_presets), res_x, res_y)[0], 'y': _get_aspect( int(tmg_cam_vars.cam_resolution_mode_presets), res_x, res_y)[1] }

        scene.render.resolution_x = int( tmp_di["x"] )
        scene.render.resolution_y = int( tmp_di["y"] )
    
    
def _change_scene_camera(self, context):
    scene = context.scene
    tmg_cam_vars = scene.tmg_cam_vars

    camera = tmg_cam_vars.scene_camera

    if camera and camera.type == "CAMERA":
        scene.camera = camera
        bpy.context.space_data.camera = camera
        tmg_cam_vars.camera_name = camera.name

        if "res_x" in camera:
            pass
        else:
            camera["res_x"] = 1920

        if "res_y" in camera:
            pass
        else:
            camera["res_y"] = 1080

        if "resolution" in camera:
            pass
        else:
            camera["resolution"] = 0

        if "res_mode" in camera:
            pass
        else:
            camera["res_mode"] = 0
        
        camera.data.passepartout_alpha = tmg_cam_vars.camera_passepartout_alpha
        camera.data.show_passepartout = tmg_cam_vars.use_camera_passepartout_alpha
        
        if tmg_cam_vars.camera_name_lock:
            tmg_cam_vars.camera_data_name = camera.name
        else:
            tmg_cam_vars.camera_data_name = camera.data.name
            
        if tmg_cam_vars.cam_res_lock_modes == '0':
            scene.render.resolution_x = tmg_cam_vars.const_res_x
            scene.render.resolution_y = tmg_cam_vars.const_res_y
            
        if tmg_cam_vars.cam_res_lock_modes == '1':
            tmg_cam_vars.res_x = _get_custom_property(camera, "res_x")
            tmg_cam_vars.res_y = _get_custom_property(camera, "res_y")
            
        tmg_cam_vars.cam_resolution_presets = str( _get_custom_property(camera, "resolution") )
        tmg_cam_vars.cam_resolution_mode_presets = str( _get_custom_property(camera, "res_mode") )
        
        active_dict['type'] = camera.data.type
        active_dict['focal_l'] = camera.data.lens 
        active_dict['sensor_w'] = camera.data.sensor_width
        active_dict['sensor_h'] = camera.data.sensor_height
        active_dict['ortho_scale'] = camera.data.ortho_scale
        active_dict['clip_start'] = camera.data.clip_start
        active_dict['clip_end'] = camera.data.clip_end
        active_dict['use_dof'] = camera.data.dof.use_dof
        active_dict['fStop'] = camera.data.dof.aperture_fstop 
#        active_dict['track_to'] = camera.data.dof.aperture_fstop
        
        camera.data.type = active_dict['type']
        camera.data.lens = active_dict['focal_l']     
        camera.data.sensor_width = active_dict['sensor_w']
        camera.data.sensor_height = active_dict['sensor_h']
        camera.data.ortho_scale = active_dict['ortho_scale']
        camera.data.clip_start = active_dict['clip_start']
        camera.data.clip_end = active_dict['clip_end']
        camera.data.dof.use_dof = active_dict['use_dof']
        camera.data.dof.aperture_fstop = active_dict['fStop']
        context.space_data.lock_camera


def _set_cam_values(self, context):
    scene = context.scene
    tmg_cam_vars = scene.tmg_cam_vars
  
    camera = tmg_cam_vars.scene_camera
    
    if camera:
        active_dict['type'] = camera.data.type
        active_dict['use_dof'] = camera.data.dof.use_dof
        active_dict['clip_start'] = camera.data.clip_start
        active_dict['clip_end'] = camera.data.clip_end
        
        camera.data.type = active_dict['type']
        camera.data.lens = active_dict['focal_l']
        camera.data.sensor_width = active_dict['sensor_w']
        camera.data.sensor_height = active_dict['sensor_h']
        camera.data.ortho_scale = active_dict['ortho_scale']
        camera.data.clip_start = active_dict['clip_start']
        camera.data.clip_end = active_dict['clip_end']
        camera.data.dof.use_dof = active_dict['use_dof']
        camera.data.dof.aperture_fstop = active_dict['fStop']
        context.space_data.lock_camera


def _tmg_search_cameras(self, object):
    return object.type == 'CAMERA'


def _set_render_slot(self, context):
    scene = context.scene
    tmg_cam_vars = scene.tmg_cam_vars
    try:
        slot = bpy.data.images["Render Result"].render_slots.active_index = int(tmg_cam_vars.render_slot)-1
    except:
        slot = None


def _curve_size(self, context):
    scene = context.scene
    tmg_cam_vars = scene.tmg_cam_vars
    camera = tmg_cam_vars.scene_camera
    original_ob = bpy.context.active_object
    
    if tmg_cam_vars.scene_camera and tmg_cam_vars.scene_camera.type == "CAMERA":
        camera = tmg_cam_vars.scene_camera
        cons = camera.constraints.items()
            
        try:
            cn = camera.constraints["Follow Path"]
            cn.target
            
            _change_ob(self, context, cn.target)
            
            bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
            
            cn.target.scale[0] = 1
            cn.target.scale[1] = 1
            cn.target.scale[2] = 1
            
            if tmg_cam_vars.curve_lock_scale:
                cn.target.bound_box.data.dimensions = (tmg_cam_vars.curve_size_x, tmg_cam_vars.curve_size_x, tmg_cam_vars.curve_size_x)
            else:
                cn.target.bound_box.data.dimensions = (tmg_cam_vars.curve_size_x, tmg_cam_vars.curve_size_y, tmg_cam_vars.curve_size_z)
            
            bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
            
        except:
            cn = None
            
    _change_ob(self, context, original_ob)


def _add_constraint(self, context, _con):
    scene = context.scene
    tmg_cam_vars = scene.tmg_cam_vars
    camera = tmg_cam_vars.scene_camera

    camera.constraints.new(_con)


class OBJECT_OT_Add_Constraint(bpy.types.Operator):
    """Add constraint based on type"""
    bl_idname = 'object.tmg_add_constraint'
    bl_label = 'Add Constraint'
    
    con : bpy.props.StringProperty(name="FLOOR")
    
    def execute(self, context):
        _add_constraint(self, context, self.con)
        return {'FINISHED'}
    
    
def _camera_passepartout_alpha(self, context):
    scene = context.scene
    tmg_cam_vars = scene.tmg_cam_vars
    camera = tmg_cam_vars.scene_camera

    if camera.data.passepartout_alpha != tmg_cam_vars.camera_passepartout_alpha:
        camera.data.passepartout_alpha = tmg_cam_vars.camera_passepartout_alpha
    
    camera.data.show_passepartout = tmg_cam_vars.use_camera_passepartout_alpha
    
    
def _move_constraint(self, context, _con, _dir):
    scene = context.scene
    tmg_cam_vars = scene.tmg_cam_vars
    camera = tmg_cam_vars.scene_camera
    original_ob = bpy.context.active_object
    
    _change_ob(self, context, camera)
    
    for name, con in camera.constraints.items():
        if con.type == _con:
            mod = camera.constraints.get(con.name)
#            print(mod)
            if _dir == "UP":
                bpy.ops.constraint.move_up(constraint=con.name, owner="OBJECT")
            else:
                bpy.ops.constraint.move_down(constraint=con.name, owner="OBJECT")
                
    _change_ob(self, context, original_ob)
    
    
class OBJECT_OT_Move_Constraint(bpy.types.Operator):
    """Remove all constraints of type"""
    bl_idname = 'object.tmg_move_constraint'
    bl_label = 'Move Constraint'
    
    con : bpy.props.StringProperty(name="FLOOR")
    dir : bpy.props.StringProperty(name="UP")
    
    def execute(self, context):
        _move_constraint(self, context, self.con, self.dir)
        return {'FINISHED'}
    
    
def _remove_constraint(self, context, _con):
    scene = context.scene
    tmg_cam_vars = scene.tmg_cam_vars
    camera = tmg_cam_vars.scene_camera
    
    for name, con in camera.constraints.items():
        if con.type == _con:
            camera.constraints.remove(con)
    
    
class OBJECT_OT_Remove_Constraint(bpy.types.Operator):
    """Remove all constraints of type"""
    bl_idname = 'object.tmg_remove_constraint'
    bl_label = 'Remove Constraint'
    
    con : bpy.props.StringProperty(name="FLOOR")
    
    def execute(self, context):
        _remove_constraint(self, context, self.con)
        return {'FINISHED'}
    
def _rename_camera(self, context):
    scene = context.scene
    tmg_cam_vars = scene.tmg_cam_vars
    camera = tmg_cam_vars.scene_camera
    
    if camera.name != tmg_cam_vars.camera_name:
        camera.name = tmg_cam_vars.camera_name
        
        if tmg_cam_vars.camera_name_lock:
            _rename_camera_data(self, context)
    

def _rename_camera_data(self, context):
    scene = context.scene
    tmg_cam_vars = scene.tmg_cam_vars
    camera = tmg_cam_vars.scene_camera
    
    if tmg_cam_vars.camera_name_lock:
        if camera.data.name != tmg_cam_vars.camera_name:
            camera.data.name = tmg_cam_vars.camera_name
    else:
        if camera.data.name != tmg_cam_vars.camera_data_name:
            camera.data.name = tmg_cam_vars.camera_data_name
    

def _get_ob_name(self):
    return self.get("ob_name", bpy.context.active_object.name)


def _set_ob_name(self, value):
    scene = bpy.context.scene
    tmg_cam_vars = scene.tmg_cam_vars
    ob = bpy.context.active_object

    if ob.name != value:
        ob.name = value

    if tmg_cam_vars.ob_name_lock:
        if ob.data and ob.data.name != value:
            ob.data.name = value


def _get_ob_data_name(self):
    if bpy.context.active_object.data:
        return self.get("ob_data_name", bpy.context.active_object.data.name)


def _set_ob_data_name(self, value):
    scene = bpy.context.scene
    tmg_cam_vars = scene.tmg_cam_vars
    ob = bpy.context.active_object

    if ob.data.name != value:
        ob.data.name = value

    if tmg_cam_vars.ob_name_lock:
        if ob.data and ob.data.name != value:
            ob.data.name = value

    
class OBJECT_OT_Select_Camera(bpy.types.Operator):
    """Select scene camera"""
    bl_idname = 'object.tmg_select_camera'
    bl_label = 'Select Camera'
    
    def execute(self, context):
        scene = context.scene
        tmg_cam_vars = scene.tmg_cam_vars
        camera = tmg_cam_vars.scene_camera
        _change_ob(self, context, camera)
        return {'FINISHED'}
    

def _update_res_x(self, context):
    scene = context.scene
    tmg_cam_vars = scene.tmg_cam_vars
    camera = tmg_cam_vars.scene_camera
    _set_custom_property( camera, "res_x", int(tmg_cam_vars.res_x) )
    scene.render.resolution_x = int( _get_custom_property(camera, "res_x") )
 
    
def _update_res_y(self, context):
    scene = context.scene
    tmg_cam_vars = scene.tmg_cam_vars
    camera = tmg_cam_vars.scene_camera
    _set_custom_property( camera, "res_y", int(tmg_cam_vars.res_y) )
    scene.render.resolution_y = int( _get_custom_property(camera, "res_y") )


def _update_const_res_x(self, context):
    scene = context.scene
    tmg_cam_vars = scene.tmg_cam_vars
    camera = tmg_cam_vars.scene_camera
    scene.render.resolution_x = int( tmg_cam_vars.const_res_x )
    
    
def _update_const_res_y(self, context):
    scene = context.scene
    tmg_cam_vars = scene.tmg_cam_vars
    camera = tmg_cam_vars.scene_camera
    scene.render.resolution_y = int( tmg_cam_vars.const_res_y )


class TMG_Camera_Properties(bpy.types.PropertyGroup):
    scene_camera : bpy.props.PointerProperty(name='Camera', type=bpy.types.Object, poll=_tmg_search_cameras, description='Scene active camera', update=_change_scene_camera)
    
    camera_name_lock : bpy.props.BoolProperty(name='Linked Name', default=True)
    camera_name : bpy.props.StringProperty(name='Object', default='Camera', update=_rename_camera)
    camera_data_name : bpy.props.StringProperty(name='Data', default='Camera', update=_rename_camera_data)

    ob_name_lock : bpy.props.BoolProperty(name='Linked Name', default=True)
    ob_name : bpy.props.StringProperty(name='Object', default='Object', set=_set_ob_name, get=_get_ob_name)
    ob_data_name : bpy.props.StringProperty(name='Data', default='Object', set=_set_ob_data_name, get=_get_ob_data_name)

    render_slot : bpy.props.IntProperty(default=1, min=1, max=8, options={'ANIMATABLE'}, update=_set_render_slot)
    
    curve_lock_scale : bpy.props.BoolProperty(default=False)
    curve_size_x : bpy.props.FloatProperty(default=1, min=0.01, update=_curve_size)
    curve_size_y : bpy.props.FloatProperty(default=1, min=0.01, update=_curve_size)
    curve_size_z : bpy.props.FloatProperty(default=1, min=0.01, update=_curve_size)

    res_x : bpy.props.FloatProperty(default=1920, subtype='PIXEL', min=4, step=15, precision=0, update=_update_res_x, description='Sets res_x Custom_Property')
    res_y : bpy.props.FloatProperty(default=1080, subtype='PIXEL', min=4, step=15, precision=0, update=_update_res_y, description='Sets res_y Custom_Property')

    const_res_x : bpy.props.FloatProperty(default=1920, subtype='PIXEL', min=4, step=15, precision=0, update=_update_const_res_x, description='Sets res_x Custom_Property')
    const_res_y : bpy.props.FloatProperty(default=1080, subtype='PIXEL', min=4, step=15, precision=0, update=_update_const_res_y, description='Sets res_y Custom_Property')

    use_camera_passepartout_alpha : bpy.props.BoolProperty(default=True, update=_camera_passepartout_alpha)
    camera_passepartout_alpha : bpy.props.FloatProperty(default=0.5, min=0.0, max=1.0, update=_camera_passepartout_alpha)

    cam_sensor_format : bpy.props.EnumProperty(name='Sensor Profile', default='0', description='Camera presets',
    items=[
    ('0', '24mm', ''),
    ('1', '36mm', ''),
    ('2', '50mm', ''),
    ('3', '80mm', ''),
    ('4', '210mm', '')], update=_change_camera_presets)
    
    cam_type : bpy.props.EnumProperty(name='Perspective', default='PERSP', description='Camera perspective type',
    items=[
    ('PERSP', 'Perspective', ''),
    ('ORTHO', 'Orthographic', ''),
    ('PANO', 'Panoramic', '')], update=_set_cam_values)
    
    cam_resolution_presets : bpy.props.EnumProperty(name='Resolution', default='2', description='Different render resolution presets',
    items=[
    ('0', 'VGA', ''),
    ('1', 'HD', ''),
    ('2', 'HD-F', ''),
    ('3', '2k', ''),
    ('4', '4k', ''),
    ('5', '8k', '')], update=_change_resolution_presets)
    
    cam_resolution_mode_presets : bpy.props.EnumProperty(name='Aspect', default='0', description='Resolution aspect mode presets',
    items=[
    ('0', 'Landscape', ''),
    ('1', 'Portrait', ''),
    ('2', 'Box', '')], update=_change_res_mode_presets)
    
    cam_res_lock_modes : bpy.props.EnumProperty(name='Resolution Lock', default='0', description='Lock modes used when swapping between cameras',
    items=[
    ('0', 'Constant', ''),
    ('1', 'Per Camera', ''),
    ('2', 'Preset', '')], update=_change_res_lock)
    

class OBJECT_PT_TMG_Camera_Panel(bpy.types.Panel):
    bl_idname = 'OBJECT_PT_tmg_camera_panel'
    bl_category = 'TMG Camera'
    bl_label = 'Camera'
    bl_context = "objectmode"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'

    def draw(self, context):
        scene = context.scene
        tmg_cam_vars = scene.tmg_cam_vars

        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False 
        layout = layout.column()
        col1 = layout.column()
        col2 = layout.column()
        layout.ui_units_y = 2

        row = col1.row(align=True)
        row.prop(tmg_cam_vars, 'scene_camera', text='')
    
        if tmg_cam_vars.scene_camera or context.space_data.lock_camera:
            row = col2.row(align=True)
            row.operator("object.tmg_select_camera", text='', icon="RESTRICT_SELECT_ON")
            row.operator('view3d.view_camera', text='', icon="CAMERA_DATA")
            row.operator('view3d.view_center_camera', text='', icon="SHADING_BBOX")
            row.prop(context.space_data, 'lock_camera', text='', icon="LOCKVIEW_ON")
            
            row.prop(scene.render, 'engine', text='')
        else:
            layout.ui_units_y = 1.8
            row = col1.row(align=True)
            row.label(text='Select a camera to begin')
        

class OBJECT_PT_TMG_Camera_Panel_Name(bpy.types.Panel):
    bl_idname = "OBJECT_PT_tmg_camera_panel_name"
    bl_label = "Name"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = "OBJECT_PT_tmg_camera_panel"
    bl_options = {"DEFAULT_CLOSED"}
            
    def draw(self, context):
        scene = context.scene
        props = scene.eevee
        tmg_cam_vars = scene.tmg_cam_vars
             
        if tmg_cam_vars.scene_camera and tmg_cam_vars.scene_camera.type == "CAMERA":
            layout = self.layout
            layout.use_property_split = True
            layout.use_property_decorate = False 
            layout = layout.column()
                
            layout.prop(tmg_cam_vars, 'camera_name_lock')
            
            if tmg_cam_vars.camera_name_lock:
                layout.prop(tmg_cam_vars, 'camera_name')
            else:
                layout.prop(tmg_cam_vars, 'camera_name')
                layout.prop(tmg_cam_vars, 'camera_data_name')
        
            
class OBJECT_PT_TMG_Camera_Panel_Perspective(bpy.types.Panel):
    bl_idname = "OBJECT_PT_tmg_camera_panel_perspective"
    bl_label = "Perspective"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = "OBJECT_PT_tmg_camera_panel"
    bl_options = {"DEFAULT_CLOSED"}
            
    def draw(self, context):
        scene = context.scene
        props = scene.eevee
        tmg_cam_vars = scene.tmg_cam_vars
             
        if tmg_cam_vars.scene_camera and tmg_cam_vars.scene_camera.type == "CAMERA":
            layout = self.layout
            layout.use_property_split = True
            layout.use_property_decorate = False 
            layout = layout.column()
        
            layout.prop(tmg_cam_vars.scene_camera.data, 'type')
            layout.prop(tmg_cam_vars, 'cam_sensor_format')
            
            layout.prop(tmg_cam_vars.scene_camera.data, 'sensor_fit')
            
            if tmg_cam_vars.scene_camera.data.type != "ORTHO":
                layout.prop(tmg_cam_vars.scene_camera.data, 'lens')
            else:
                layout.prop(tmg_cam_vars.scene_camera.data, 'ortho_scale')

            if tmg_cam_vars.scene_camera.data.sensor_fit != "VERTICAL":
                layout.prop(tmg_cam_vars.scene_camera.data, 'sensor_width')
            else:
                layout.prop(tmg_cam_vars.scene_camera.data, 'sensor_height')
                
            layout.prop(tmg_cam_vars.scene_camera.data, 'clip_start')
            layout.prop(tmg_cam_vars.scene_camera.data, 'clip_end')            
                                   
            
class OBJECT_PT_TMG_Constraints_Panel(bpy.types.Panel):
    bl_idname = 'OBJECT_PT_tmg_constraints_panel'
    bl_category = 'TMG Camera'
    bl_label = 'Constraints'
    bl_context = "objectmode"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        pass
                 
class OBJECT_PT_TMG_Constraints_Panel_Floor(bpy.types.Panel):
    bl_idname = "OBJECT_PT_TMG_constraints_panel_floor"
    bl_label = ""
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = "OBJECT_PT_tmg_constraints_panel"
    bl_options = {"DEFAULT_CLOSED"}

    def draw_header(self, context):
        scene = context.scene
        tmg_cam_vars = scene.tmg_cam_vars
        
        if tmg_cam_vars.scene_camera and tmg_cam_vars.scene_camera.type == "CAMERA":
            layout = self.layout
            
            camera = tmg_cam_vars.scene_camera
            cons = camera.constraints.items()
            
            try:
                cn = camera.constraints["Floor"]
                layout.label(text='Floor')
                layout.active = layout.active= not cn.mute
            except:
                cn = None
                
                layout.label(text='Floor')
                layout.active = layout.active= False
        else:
            layout = self.layout
            layout.label(text='Floor')
            layout.active = layout.active= False

    def draw(self, context):
        scene = context.scene
        tmg_cam_vars = scene.tmg_cam_vars
        
        if tmg_cam_vars.scene_camera and tmg_cam_vars.scene_camera.type == "CAMERA":
            layout = self.layout
            layout.use_property_split = True
            layout.use_property_decorate = False  # No animation.
            col = layout.column(align=True)
            row = col.row(align=True)
            
            camera = tmg_cam_vars.scene_camera
            cons = camera.constraints.items()
                
            try:
                cn = camera.constraints["Floor"]
                row.prop(cn, 'mute', text='')
                layout.active= not cn.mute
                
                props = row.operator("object.tmg_move_constraint", text='', icon="TRIA_UP")
                props.con = "FLOOR"
                props.dir = "UP"
                
                props = row.operator("object.tmg_move_constraint", text='', icon="TRIA_DOWN")
                props.con = "FLOOR"
                props.dir = "DOWN"
                
                props = row.operator("object.tmg_remove_constraint", text='', icon="X")
                props.con = "FLOOR"
                
#                row = col.row(align=True)
                layout.prop(cn, 'target')
                layout.prop(cn, 'offset')
                
            except:
                cn = None
#                props = row.operator("object.tmg_add_constraint", text='', icon="CON_FLOOR")
#                props.con = "FLOOR"

                c1 = row.row(align=True)
                c2 = row.row(align=True)

                props = c1.operator("object.tmg_add_constraint", text='', icon="CON_TRACKTO")
                props.con = "FLOOR"
                c1.enabled = True
                
                c2.enabled = False
                
                props = c2.operator("object.tmg_move_constraint", text='', icon="TRIA_UP")
                props.con = "FLOOR"
                props.dir = "UP"
                
                props = c2.operator("object.tmg_move_constraint", text='', icon="TRIA_DOWN")
                props.con = "FLOOR"
                props.dir = "DOWN"
                
                props = c2.operator("object.tmg_remove_constraint", text='', icon="X")
                props.con = "FLOOR"
                             
                             
class OBJECT_PT_TMG_Constraints_Panel_Follow_Path(bpy.types.Panel):
    bl_idname = "OBJECT_PT_tmg_constraints_panel_follow_path"
    bl_label = ""
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = "OBJECT_PT_tmg_constraints_panel"
    bl_options = {"DEFAULT_CLOSED"}

    def draw_header(self, context):
        scene = context.scene
        tmg_cam_vars = scene.tmg_cam_vars
        
        if tmg_cam_vars.scene_camera and tmg_cam_vars.scene_camera.type == "CAMERA":
            layout = self.layout
            
            camera = tmg_cam_vars.scene_camera
            cons = camera.constraints.items()
            
            try:
                cn = camera.constraints["Follow Path"]
                layout.label(text='Follow Path')
                layout.active = layout.active= not cn.mute
            except:
                cn = None
                
                layout.label(text='Follow Path')
                layout.active = layout.active= False
                
        else:
            layout = self.layout
            layout.label(text='Follow Path')
            layout.active = layout.active= False

    def draw(self, context):
        scene = context.scene
        props = scene.eevee
        tmg_cam_vars = scene.tmg_cam_vars
        
        if tmg_cam_vars.scene_camera and tmg_cam_vars.scene_camera.type == "CAMERA":
            layout = self.layout
            layout.use_property_split = True
            layout.use_property_decorate = False 
            layout = layout.column(align=True)
            row = layout.row(align=True)
        
            camera = tmg_cam_vars.scene_camera
            cons = camera.constraints.items()
                
            try:
                cn = camera.constraints["Follow Path"]
                row.prop(cn, 'mute', text='')
                layout.active= not cn.mute
                
                props = row.operator("object.tmg_move_constraint", text='', icon="TRIA_UP")
                props.con = "FOLLOW_PATH"
                props.dir = "UP"
                
                props = row.operator("object.tmg_move_constraint", text='', icon="TRIA_DOWN")
                props.con = "FOLLOW_PATH"
                props.dir = "DOWN"
                
                props = row.operator("object.tmg_remove_constraint", text='', icon="X")
                props.con = "FOLLOW_PATH"

                layout.prop(cn, 'target', text='')
                
                if cn.use_fixed_location:
                    layout.prop(cn, 'offset_factor')
                else:
                    layout.prop(cn, 'offset')
                    
                layout.prop(cn, 'use_fixed_location')
                layout.prop(cn, 'use_curve_radius')
                layout.prop(cn, 'use_curve_follow')
            except:
                cn = None
                c1 = row.row(align=True)
                c2 = row.row(align=True)

                props = c1.operator("object.tmg_add_constraint", text='', icon="CON_FOLLOWPATH")
                props.con = "FOLLOW_PATH"
                c1.enabled = True
                
                c2.enabled = False
                
                props = c2.operator("object.tmg_move_constraint", text='', icon="TRIA_UP")
                props.con = "FOLLOW_PATH"
                props.dir = "UP"
                
                props = c2.operator("object.tmg_move_constraint", text='', icon="TRIA_DOWN")
                props.con = "FOLLOW_PATH"
                props.dir = "DOWN"
                
                props = c2.operator("object.tmg_remove_constraint", text='', icon="X")
                props.con = "FOLLOW_PATH"
                
                
class OBJECT_PT_TMG_Constraints_Panel_Follow_Path_Spline_Scale(bpy.types.Panel):
    bl_idname = "OBJECT_PT_tmg_constraints_panel_follow_path_spline_scale"
    bl_label = ""
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = "OBJECT_PT_tmg_constraints_panel_follow_path"
    bl_options = {"DEFAULT_CLOSED"}

    def draw_header(self, context):
        scene = context.scene
        tmg_cam_vars = scene.tmg_cam_vars
        
        if tmg_cam_vars.scene_camera and tmg_cam_vars.scene_camera.type == "CAMERA":
            layout = self.layout
            
            camera = tmg_cam_vars.scene_camera
            cons = camera.constraints.items()
            
            try:
                cn = camera.constraints["Follow Path"]
                layout.label(text='Spline Scale')
                layout.active = layout.active= not cn.mute
            except:
                cn = None
                
                layout.label(text='Spline Scale')
                layout.active = layout.active= False
        
        else:
            layout = self.layout
            layout.label(text='Spline Scale')
            layout.active = layout.active= False

    def draw(self, context):
        scene = context.scene
        props = scene.eevee
        tmg_cam_vars = scene.tmg_cam_vars
        
        if tmg_cam_vars.scene_camera and tmg_cam_vars.scene_camera.type == "CAMERA":
            layout = self.layout
            layout.use_property_split = True
            layout.use_property_decorate = False 
        
            camera = tmg_cam_vars.scene_camera
            cons = camera.constraints.items()
                
            try:
                cn = camera.constraints["Follow Path"]
                layout.active= not cn.mute
                
                if not cn.mute:
                    cn = camera.constraints["Follow Path"]
                    col = layout.column(align=True)
                    col.enabled = True
                    
                    if tmg_cam_vars.curve_lock_scale:
                        col.prop(tmg_cam_vars, 'curve_lock_scale', text='Lock Scale')
                    else:
                        col.prop(tmg_cam_vars, 'curve_lock_scale', text='Lock Scale')
                    
                    if tmg_cam_vars.curve_lock_scale:
                        col.prop(tmg_cam_vars, 'curve_size_x', text='XYZ')
                    else:
                        col.prop(tmg_cam_vars, 'curve_size_x', text='X')
                        col.prop(tmg_cam_vars, 'curve_size_y', text='Y')
                        col.prop(tmg_cam_vars, 'curve_size_z', text='Z')
                else:
                    cn = camera.constraints["Follow Path"]
                    col = layout.column(align=True)
                    col.enabled = False
                    
                    if tmg_cam_vars.curve_lock_scale:
                        col.prop(tmg_cam_vars, 'curve_lock_scale', text='Lock Scale')
                    else:
                        col.prop(tmg_cam_vars, 'curve_lock_scale', text='Lock Scale')
                    
                    if tmg_cam_vars.curve_lock_scale:
                        col.prop(tmg_cam_vars, 'curve_size_x', text='XYZ')
                    else:
                        col.prop(tmg_cam_vars, 'curve_size_x', text='X')
                        col.prop(tmg_cam_vars, 'curve_size_y', text='Y')
                        col.prop(tmg_cam_vars, 'curve_size_z', text='Z')
            except:
                cn = None
                
                
class OBJECT_PT_TMG_Constraints_Panel_Track_To(bpy.types.Panel):
    bl_idname = "OBJECT_PT_tmg_constraints_panel_track_to"
    bl_label = ""
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = "OBJECT_PT_tmg_constraints_panel"
    bl_options = {"DEFAULT_CLOSED"}

    def draw_header(self, context):
        scene = context.scene
        tmg_cam_vars = scene.tmg_cam_vars
        
        if tmg_cam_vars.scene_camera and tmg_cam_vars.scene_camera.type == "CAMERA":
            layout = self.layout
            
            camera = tmg_cam_vars.scene_camera
            cons = camera.constraints.items()
            
            try:
                cn = camera.constraints["Track To"]
                layout.label(text='Track To')
                layout.active = layout.active= not cn.mute
            except:
                cn = None
                
                layout.label(text='Track To')
                layout.active = layout.active= False
                
        else:
            layout = self.layout
            layout.label(text='Track To')
            layout.active = layout.active= False

    def draw(self, context):
        scene = context.scene
        tmg_cam_vars = scene.tmg_cam_vars
        
        if tmg_cam_vars.scene_camera and tmg_cam_vars.scene_camera.type == "CAMERA":
            layout = self.layout
            layout.use_property_split = True
            layout.use_property_decorate = False  # No animation.
            layout = layout.column()
            row = layout.row(align=True)
        
            camera = tmg_cam_vars.scene_camera
            cons = camera.constraints.items()
                
            try:
                cn = camera.constraints["Track To"]
                row.prop(cn, 'mute', text='')
                layout.active= not cn.mute
                
                props = row.operator("object.tmg_move_constraint", text='', icon="TRIA_UP")
                props.con = "TRACK_TO"
                props.dir = "UP"
                
                props = row.operator("object.tmg_move_constraint", text='', icon="TRIA_DOWN")
                props.con = "TRACK_TO"
                props.dir = "DOWN"
                
                props = row.operator("object.tmg_remove_constraint", text='', icon="X")
                props.con = "TRACK_TO"

#                row = layout.row(align=True)
                layout.prop(cn, 'target')
                layout.prop(cn, 'influence')
            except:
                cn = None  
                c1 = row.row(align=True)
                c2 = row.row(align=True)

                props = c1.operator("object.tmg_add_constraint", text='', icon="CON_TRACKTO")
                props.con = "TRACK_TO"
                c1.enabled = True
                
                c2.enabled = False
                
                props = c2.operator("object.tmg_move_constraint", text='', icon="TRIA_UP")
                props.con = "TRACK_TO"
                props.dir = "UP"
                
                props = c2.operator("object.tmg_move_constraint", text='', icon="TRIA_DOWN")
                props.con = "TRACK_TO"
                props.dir = "DOWN"
                
                props = c2.operator("object.tmg_remove_constraint", text='', icon="X")
                props.con = "TRACK_TO"
   
   
class OBJECT_PT_TMG_Output_Panel(bpy.types.Panel):
    bl_idname = 'OBJECT_PT_tmg_output_panel'
    bl_category = 'TMG Camera'
    bl_label = 'Output'
    bl_context = "objectmode"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        pass      
         
            
class OBJECT_PT_TMG_Output_Panel_Image(bpy.types.Panel):
    bl_idname = "OBJECT_PT_tmg_output_panel_image"
    bl_label = "Image"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = "OBJECT_PT_tmg_output_panel"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        scene = context.scene
        props = scene.eevee
        tmg_cam_vars = scene.tmg_cam_vars
        
        if tmg_cam_vars.scene_camera and tmg_cam_vars.scene_camera.type == "CAMERA":
            layout = self.layout
            layout.use_property_split = True
            layout.use_property_decorate = False  # No animation.

            rd = context.scene.render
            image_settings = rd.image_settings

            layout.prop(rd, "filepath", text="")
            
            row = layout.row(align=True)
            row.operator("render.render", text='Image', icon="CAMERA_DATA")
            row.operator("render.render", text='Animation', icon="RENDER_ANIMATION").animation=True
            
            layout.prop(tmg_cam_vars, 'render_slot', text='Render Slot')


class OBJECT_PT_TMG_Output_Panel_Image_Settings(bpy.types.Panel):
    bl_idname = "OBJECT_PT_tmg_output_panel_image_settings"
    bl_label = "Image Settings"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = "OBJECT_PT_tmg_output_panel"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        scene = context.scene
        props = scene.eevee
        tmg_cam_vars = scene.tmg_cam_vars
        
        if tmg_cam_vars.scene_camera and tmg_cam_vars.scene_camera.type == "CAMERA":
            layout = self.layout
            layout.use_property_split = True
            layout.use_property_decorate = False  # No animation.

            rd = context.scene.render
            image_settings = rd.image_settings

            layout.prop(scene, 'use_nodes')

            layout = layout.column(heading="Saving")
            layout.prop(rd, "use_file_extension")
            layout.prop(rd, "use_render_cache")

            layout.prop(scene.render.image_settings, 'file_format')
            layout.prop(scene.render.image_settings, 'color_mode')

            if not rd.is_movie_format:
                layout = layout.column(heading="Image Sequence")
                layout.prop(rd, "use_overwrite")
                layout.prop(rd, "use_placeholder")          

            
class OBJECT_PT_TMG_Passes_Panel(bpy.types.Panel):
    bl_idname = 'OBJECT_PT_tmg_passes_panel'
    bl_category = 'TMG Camera'
    bl_label = 'Passes'
    bl_context = "objectmode"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        pass
    
    
class OBJECT_PT_TMG_Passes_Panel_Cryptomatte(bpy.types.Panel):
    bl_idname = "OBJECT_PT_tmg_passes_panel_cryptomatte"
    bl_label = ""
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = "OBJECT_PT_tmg_passes_panel"
    bl_options = {"DEFAULT_CLOSED"}

    def draw_header(self, context):
        scene = context.scene
        scene_eevee = scene.eevee
        rd = scene.render
        tmg_cam_vars = scene.tmg_cam_vars
        
        layout = self.layout
        layout.label(text='Cryptomatte')
        
        if tmg_cam_vars.scene_camera and tmg_cam_vars.scene_camera.type == "CAMERA":
            if rd.engine == "BLENDER_EEVEE" or rd.engine == "CYCLES":
                layout.active = True
            else:
                layout.active = False
        else:
            layout.active = False

    def draw(self, context):
        scene = context.scene
        rd = scene.render
        tmg_cam_vars = scene.tmg_cam_vars
        
        if tmg_cam_vars.scene_camera and tmg_cam_vars.scene_camera.type == "CAMERA":
            if rd.engine == "BLENDER_EEVEE" or rd.engine == "CYCLES":
                layout = self.layout
                layout.use_property_split = True
                layout.use_property_decorate = False  # No animation.
                layout = layout.column()

                view_layer = context.view_layer

                layout.prop(view_layer, "use_pass_cryptomatte_object", text="Object")
                layout.prop(view_layer, "use_pass_cryptomatte_material", text="Material")
                layout.prop(view_layer, "use_pass_cryptomatte_asset", text="Asset")
    #            col = layout.column()
                layout.active = any((view_layer.use_pass_cryptomatte_object, view_layer.use_pass_cryptomatte_material, view_layer.use_pass_cryptomatte_asset))
                layout.prop(view_layer, "pass_cryptomatte_depth", text="Levels")
                layout.prop(view_layer, "use_pass_cryptomatte_accurate", text="Accurate Mode")
        
    
class OBJECT_PT_TMG_Passes_Panel_Data(bpy.types.Panel):
    bl_idname = "OBJECT_PT_tmg_passes_panel_data"
    bl_label = ""
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = "OBJECT_PT_tmg_passes_panel"
    bl_options = {"DEFAULT_CLOSED"}

    def draw_header(self, context):
        scene = context.scene
        scene_eevee = scene.eevee
        rd = scene.render
        tmg_cam_vars = scene.tmg_cam_vars
        
        layout = self.layout
        layout.label(text='Data')
            
        if tmg_cam_vars.scene_camera and tmg_cam_vars.scene_camera.type == "CAMERA":
            if rd.engine == "BLENDER_EEVEE" or rd.engine == "CYCLES":
                layout.active = True
            else:
                layout.active = False
        else:
            layout.active = False

    def draw(self, context):
        scene = context.scene
        rd = scene.render
        tmg_cam_vars = scene.tmg_cam_vars
        
        if tmg_cam_vars.scene_camera and tmg_cam_vars.scene_camera.type == "CAMERA":
            layout = self.layout
            layout.use_property_split = True
            layout.use_property_decorate = False  # No animation.
            layout = layout.column()

            view_layer = context.view_layer

            if rd.engine == "BLENDER_EEVEE":
                layout = layout.column(heading="Include", align=True)
                layout.prop(view_layer, "use_pass_combined")
                layout.prop(view_layer, "use_pass_z")
                layout.prop(view_layer, "use_pass_mist")
                layout.prop(view_layer, "use_pass_normal")
        

            if rd.engine == "CYCLES":
                cycles_view_layer = view_layer.cycles
                layout = layout.column(heading="Include", align=True)
                layout.prop(view_layer, "use_pass_combined")
                layout.prop(view_layer, "use_pass_z")
                layout.prop(view_layer, "use_pass_mist")
                layout.prop(view_layer, "use_pass_normal")
                sub = layout.column()
                sub.active = not rd.use_motion_blur
                sub.prop(view_layer, "use_pass_vector")
                layout.prop(view_layer, "use_pass_uv")

                layout.prop(cycles_view_layer, "denoising_store_passes", text="Denoising Data")

                layout = layout.column(heading="Indexes", align=True)
                layout.prop(view_layer, "use_pass_object_index")
                layout.prop(view_layer, "use_pass_material_index")

                layout = layout.column(heading="Debug", align=True)
                layout.prop(cycles_view_layer, "pass_debug_render_time", text="Render Time")
                layout.prop(cycles_view_layer, "pass_debug_sample_count", text="Sample Count")

                layout.prop(view_layer, "pass_alpha_threshold")
    
    
class OBJECT_PT_TMG_Passes_Panel_Effects(bpy.types.Panel):
    bl_idname = "OBJECT_PT_tmg_passes_panel_effects"
    bl_label = ""
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = "OBJECT_PT_tmg_passes_panel"
    bl_options = {"DEFAULT_CLOSED"}

    def draw_header(self, context):
        scene = context.scene
        scene_eevee = scene.eevee
        rd = scene.render
        tmg_cam_vars = scene.tmg_cam_vars
        
        layout = self.layout
        layout.label(text='Effects')
        
        if tmg_cam_vars.scene_camera and tmg_cam_vars.scene_camera.type == "CAMERA":
            if rd.engine != "BLENDER_EEVEE":
                layout.active = False
        else:
            layout.active = False

    def draw(self, context):
        scene = context.scene
        scene_eevee = scene.eevee
        rd = scene.render
        tmg_cam_vars = scene.tmg_cam_vars
        
        if tmg_cam_vars.scene_camera and tmg_cam_vars.scene_camera.type == "CAMERA":
            if rd.engine == "BLENDER_EEVEE":
                layout = self.layout
                layout.use_property_split = True
                layout.use_property_decorate = False  # No animation.
                layout = layout.column()

                view_layer = context.view_layer
                view_layer_eevee = view_layer.eevee

                layout.prop(view_layer_eevee, "use_pass_bloom", text="Bloom")
                layout.active = scene_eevee.use_bloom
                
                if rd.engine != "BLENDER_EEVEE":
                    layout.active = False
        
    
class OBJECT_PT_TMG_Passes_Panel_Light(bpy.types.Panel):
    bl_idname = "OBJECT_PT_tmg_passes_panel_light"
    bl_label = ""
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = "OBJECT_PT_tmg_passes_panel"
    bl_options = {"DEFAULT_CLOSED"}

    def draw_header(self, context):
        scene = context.scene
        scene_eevee = scene.eevee
        rd = scene.render
        tmg_cam_vars = scene.tmg_cam_vars
        
        layout = self.layout
        layout.label(text='Light')
        
        if tmg_cam_vars.scene_camera and tmg_cam_vars.scene_camera.type == "CAMERA":
            if rd.engine == "BLENDER_EEVEE" or rd.engine == "CYCLES":
                layout.active = True
            else:
                layout.active = False
        else:
            layout.active = False

    def draw(self, context):
        scene = context.scene
        rd = scene.render
        tmg_cam_vars = scene.tmg_cam_vars
        
        if tmg_cam_vars.scene_camera and tmg_cam_vars.scene_camera.type == "CAMERA":
            layout = self.layout
            layout.use_property_split = True
            layout.use_property_decorate = False  # No animation.
            layout = layout.column()

            view_layer = context.view_layer

            if rd.engine == "BLENDER_EEVEE":
                view_layer_eevee = view_layer.eevee
                layout = layout.column(heading="Diffuse", align=True)
                layout.prop(view_layer, "use_pass_diffuse_direct", text="Light")
                layout.prop(view_layer, "use_pass_diffuse_color", text="Color")

                layout = layout.column(heading="Specular", align=True)
                layout.prop(view_layer, "use_pass_glossy_direct", text="Light")
                layout.prop(view_layer, "use_pass_glossy_color", text="Color")

                layout = layout.column(heading="Volume", align=True)
                layout.prop(view_layer_eevee, "use_pass_volume_direct", text="Light")

                layout = layout.column(heading="Other", align=True)
                layout.prop(view_layer, "use_pass_emit", text="Emission")
                layout.prop(view_layer, "use_pass_environment")
                layout.prop(view_layer, "use_pass_shadow")
                layout.prop(view_layer, "use_pass_ambient_occlusion", text="Ambient Occlusion")
            
            if rd.engine == "CYCLES":
                cycles_view_layer = view_layer.cycles
                layout = layout.column(heading="Diffuse", align=True)
                layout.prop(view_layer, "use_pass_diffuse_direct", text="Direct")
                layout.prop(view_layer, "use_pass_diffuse_indirect", text="Indirect")
                layout.prop(view_layer, "use_pass_diffuse_color", text="Color")

                layout = layout.column(heading="Glossy", align=True)
                layout.prop(view_layer, "use_pass_glossy_direct", text="Direct")
                layout.prop(view_layer, "use_pass_glossy_indirect", text="Indirect")
                layout.prop(view_layer, "use_pass_glossy_color", text="Color")

                layout = layout.column(heading="Transmission", align=True)
                layout.prop(view_layer, "use_pass_transmission_direct", text="Direct")
                layout.prop(view_layer, "use_pass_transmission_indirect", text="Indirect")
                layout.prop(view_layer, "use_pass_transmission_color", text="Color")

                layout = layout.column(heading="Volume", align=True)
                layout.prop(cycles_view_layer, "use_pass_volume_direct", text="Direct")
                layout.prop(cycles_view_layer, "use_pass_volume_indirect", text="Indirect")

                layout = layout.column(heading="Other", align=True)
                layout.prop(view_layer, "use_pass_emit", text="Emission")
                layout.prop(view_layer, "use_pass_environment")
                layout.prop(view_layer, "use_pass_shadow")
                layout.prop(view_layer, "use_pass_ambient_occlusion", text="Ambient Occlusion")
    
    
class OBJECT_PT_TMG_Passes_Panel_Shader_AOV(bpy.types.Panel):
    bl_idname = "OBJECT_PT_tmg_passes_panel_shader_aov"
    bl_label = ""
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = "OBJECT_PT_tmg_passes_panel"
    bl_options = {"DEFAULT_CLOSED"}

    def draw_header(self, context):
        scene = context.scene
        scene_eevee = scene.eevee
        rd = scene.render
        tmg_cam_vars = scene.tmg_cam_vars
        
        layout = self.layout
        layout.label(text='Shader AOV')
            
        if tmg_cam_vars.scene_camera and tmg_cam_vars.scene_camera.type == "CAMERA":
            if rd.engine == "BLENDER_EEVEE" or rd.engine == "CYCLES":
                layout.active = True
            else:
                layout.active = False
        else:
            layout.active = False

    def draw(self, context):
        scene = context.scene
        rd = scene.render
        tmg_cam_vars = scene.tmg_cam_vars
        
        if tmg_cam_vars.scene_camera and tmg_cam_vars.scene_camera.type == "CAMERA":
            if rd.engine == "BLENDER_EEVEE" or rd.engine == "CYCLES":
                layout = self.layout
                layout.use_property_split = True
                layout.use_property_decorate = False  # No animation.
    #            layout = layout.column()

                view_layer = context.view_layer
                view_layer_eevee = view_layer.eevee

                row = layout.row()
                col = row.column()
                col.template_list("VIEWLAYER_UL_aov", "aovs", view_layer,
                                  "aovs", view_layer, "active_aov_index", rows=2)

                col = row.column()
                sub = col.column(align=True)
                sub.operator("scene.view_layer_add_aov", icon='ADD', text="")
                sub.operator("scene.view_layer_remove_aov", icon='REMOVE', text="")

                aov = view_layer.active_aov
                if aov and not aov.is_valid:
                    layout.label(
                        text="Conflicts with another render pass with the same name", icon='ERROR')
    
            
class OBJECT_PT_TMG_Render_Panel(bpy.types.Panel):
    bl_idname = 'OBJECT_PT_tmg_render_panel'
    bl_category = 'TMG Camera'
    bl_label = 'Render'
    bl_context = "objectmode"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        pass


class OBJECT_PT_TMG_Render_Panel_Aspect(bpy.types.Panel):
    bl_idname = "OBJECT_PT_tmg_render_panel_aspect"
    bl_label = "Aspect"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = "OBJECT_PT_tmg_render_panel"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        scene = context.scene
        tmg_cam_vars = scene.tmg_cam_vars
        
        if tmg_cam_vars.scene_camera and tmg_cam_vars.scene_camera.type == "CAMERA":
            layout = self.layout
            layout.use_property_split = True
            layout.use_property_decorate = False  # No animation.
            layout = layout.column()

            layout.prop(tmg_cam_vars, 'cam_resolution_mode_presets', text='Preset')
            layout.prop(scene.render, 'pixel_aspect_x', text='X')
            layout.prop(scene.render, 'pixel_aspect_y', text='Y')
         

class OBJECT_PT_TMG_Render_Panel_Device(bpy.types.Panel):
    bl_idname = "OBJECT_PT_tmg_render_panel_device"
    bl_label = "Device"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = "OBJECT_PT_tmg_render_panel"
    COMPAT_ENGINES = {'CYCLES'}
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context):
        engine = context.scene.render.engine
        return engine in cls.COMPAT_ENGINES
            
    def draw(self, context):
        scene = context.scene
        tmg_cam_vars = scene.tmg_cam_vars
             
        if tmg_cam_vars.scene_camera and tmg_cam_vars.scene_camera.type == "CAMERA":
            layout = self.layout
            layout.use_property_split = True
            layout.use_property_decorate = False 
            layout = layout.column()

            engine = context.scene.render.engine
            cscene = scene.cycles

            col = layout.column()
            col.prop(cscene, "device")

            col = layout.column()
            col.prop(cscene, "feature_set")


            col.prop(cscene, "shading_system")

         
class OBJECT_PT_TMG_Render_Panel_Film(bpy.types.Panel):
    bl_idname = "OBJECT_PT_tmg_render_panel_film"
    bl_label = "Film"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = "OBJECT_PT_tmg_render_panel"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        scene = context.scene
        rd = scene.render
        props = scene.eevee
        tmg_cam_vars = scene.tmg_cam_vars
        
        if tmg_cam_vars.scene_camera and tmg_cam_vars.scene_camera.type == "CAMERA":
            layout = self.layout
            layout.use_property_split = True
            layout.use_property_decorate = False  # No animation.
            layout = layout.column()

            col = layout.column()
            col.prop(rd, "filter_size")
            col.prop(rd, "film_transparent", text="Transparent")

            col = layout.column(align=False, heading="Overscan")
            row = col.row(align=True)
            sub = row.row(align=True)
            sub.prop(props, "use_overscan", text="")
            sub = sub.row(align=True)
            sub.active = props.use_overscan
            sub.prop(props, "overscan_size", text="")


class OBJECT_PT_TMG_Render_Panel_Cycles_Light_Paths(bpy.types.Panel):
    bl_idname = "OBJECT_PT_tmg_render_panel_cycles_light_paths"
    bl_label = "Light Paths"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = "OBJECT_PT_tmg_render_panel"
    COMPAT_ENGINES = {'CYCLES'}
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context):
        engine = context.scene.render.engine
        return engine in cls.COMPAT_ENGINES

    # def draw_header_preset(self, context):
    #     CYCLES_PT_integrator_presets.draw_panel_header(self.layout)

    def draw(self, context):
        pass


class OBJECT_PT_TMG_Render_Panel_Cycles_Max_Bounces(bpy.types.Panel):
    bl_idname = "OBJECT_PT_tmg_render_panel_cycles_max_bounces"
    bl_label = "Max Bounces"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = "OBJECT_PT_tmg_render_panel_cycles_light_paths"
    COMPAT_ENGINES = {'CYCLES'}
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context):
        engine = context.scene.render.engine
        return engine in cls.COMPAT_ENGINES

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        scene = context.scene
        cscene = scene.cycles

        col = layout.column(align=True)
        col.prop(cscene, "max_bounces", text="Total")

        col = layout.column(align=True)
        col.prop(cscene, "diffuse_bounces", text="Diffuse")
        col.prop(cscene, "glossy_bounces", text="Glossy")
        col.prop(cscene, "transparent_max_bounces", text="Transparency")
        col.prop(cscene, "transmission_bounces", text="Transmission")
        col.prop(cscene, "volume_bounces", text="Volume")


class OBJECT_PT_TMG_Render_Panel_Cycles_Clamping(bpy.types.Panel):
    bl_idname = "OBJECT_PT_tmg_render_panel_cycles_clamping"
    bl_label = "Clamping"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = "OBJECT_PT_tmg_render_panel_cycles_light_paths"
    COMPAT_ENGINES = {'CYCLES'}
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context):
        engine = context.scene.render.engine
        return engine in cls.COMPAT_ENGINES

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        scene = context.scene
        cscene = scene.cycles

        col = layout.column(align=True)
        col.prop(cscene, "sample_clamp_direct", text="Direct Light")
        col.prop(cscene, "sample_clamp_indirect", text="Indirect Light")


class OBJECT_PT_TMG_Render_Panel_Cycles_Caustics(bpy.types.Panel):
    bl_idname = "OBJECT_PT_tmg_render_panel_cycles_caustics"
    bl_label = "Caustics"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = "OBJECT_PT_tmg_render_panel_cycles_light_paths"
    COMPAT_ENGINES = {'CYCLES'}
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context):
        engine = context.scene.render.engine
        return engine in cls.COMPAT_ENGINES

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        scene = context.scene
        cscene = scene.cycles

        col = layout.column()
        col.prop(cscene, "blur_glossy")
        col = layout.column(heading="Caustics", align=True)
        col.prop(cscene, "caustics_reflective", text="Reflective")
        col.prop(cscene, "caustics_refractive", text="Refractive")


class OBJECT_PT_TMG_Render_Panel_Cycles_Fast_GI_Approximation(bpy.types.Panel):
    bl_idname = "OBJECT_PT_tmg_render_panel_cycles_fast_gi_approximation"
    bl_label = "Fast GI Approximation"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = "OBJECT_PT_tmg_render_panel_cycles_light_paths"
    COMPAT_ENGINES = {'CYCLES'}
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context):
        engine = context.scene.render.engine
        return engine in cls.COMPAT_ENGINES

    def draw_header(self, context):
        scene = context.scene
        cscene = scene.cycles

        self.layout.prop(cscene, "use_fast_gi", text="")

    def draw(self, context):
        scene = context.scene
        cscene = scene.cycles
        world = scene.world

        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        col = layout.column(align=True)
        col.prop(cscene, "ao_bounces", text="Viewport Bounces")
        col.prop(cscene, "ao_bounces_render", text="Render Bounces")

        if world:
          light = world.light_settings
          col = layout.column(align=True)
          col.prop(light, "ao_factor", text="AO Factor")
          col.prop(light, "distance", text="AO Distance")
  
  
class OBJECT_PT_TMG_Render_Panel_Performance(bpy.types.Panel):
    bl_idname = "OBJECT_PT_tmg_render_panel_performance"
    bl_label = "Performance"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = "OBJECT_PT_tmg_render_panel"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        pass
        
        
class OBJECT_PT_TMG_Render_Panel_Performance_Acceleration_Structure(bpy.types.Panel):
    bl_idname = "OBJECT_PT_tmg_render_panel_performance_acceleration_structure"
    bl_label = ""
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = "OBJECT_PT_tmg_render_panel_performance"
    bl_options = {"DEFAULT_CLOSED"}

    def draw_header(self, context):
        scene = context.scene
        scene_eevee = scene.eevee
        rd = scene.render
        tmg_cam_vars = scene.tmg_cam_vars
        
        layout = self.layout
        layout.label(text='Acceleration Structure')
            
        if tmg_cam_vars.scene_camera and tmg_cam_vars.scene_camera.type == "CAMERA":
            if rd.engine == "CYCLES":
                layout.active = True
            else:
                layout.active = False
        else:
            layout.active = False

    def draw(self, context):
        scene = context.scene
        rd = scene.render
        tmg_cam_vars = scene.tmg_cam_vars
        
        if tmg_cam_vars.scene_camera and tmg_cam_vars.scene_camera.type == "CAMERA":
            import _cycles

            layout = self.layout
            layout.use_property_split = True
            layout.use_property_decorate = False

            scene = context.scene
            cscene = scene.cycles
            use_cpu = context.scene.cycles

            col = layout.column()

            use_embree = False
            if use_cpu:
                use_embree = _cycles.with_embree
                if not use_embree:
                    sub = col.column(align=True)
                    sub.label(text="Cycles built without Embree support")
                    sub.label(text="CPU raytracing performance will be poor")

            col.prop(cscene, "debug_use_spatial_splits")
            sub = col.column()
            sub.active = not use_embree
            sub.prop(cscene, "debug_use_hair_bvh")
            sub = col.column()
            sub.active = not cscene.debug_use_spatial_splits and not use_embree
            sub.prop(cscene, "debug_bvh_time_steps")
            
            if rd.engine == "CYCLES":
                layout.active = True
            else:
                layout.active = False
        
        
class OBJECT_PT_TMG_Render_Panel_Performance_Final_Render(bpy.types.Panel):
    bl_idname = "OBJECT_PT_tmg_render_panel_performance_final_render"
    bl_label = ""
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = "OBJECT_PT_tmg_render_panel_performance"
    bl_options = {"DEFAULT_CLOSED"}

    def draw_header(self, context):
        scene = context.scene
        scene_eevee = scene.eevee
        rd = scene.render
        tmg_cam_vars = scene.tmg_cam_vars
        
        layout = self.layout
        layout.label(text='Final Render')
            
        if tmg_cam_vars.scene_camera and tmg_cam_vars.scene_camera.type == "CAMERA":
            if rd.engine == "CYCLES":
                layout.active = True
            else:
                layout.active = False
        else:
            layout.active = False

    def draw(self, context):
        scene = context.scene
        rd = scene.render
        tmg_cam_vars = scene.tmg_cam_vars
        
        if tmg_cam_vars.scene_camera and tmg_cam_vars.scene_camera.type == "CAMERA":
            layout = self.layout
            layout.use_property_split = True
            layout.use_property_decorate = False

            scene = context.scene
            rd = scene.render

            col = layout.column()

            col.prop(rd, "use_save_buffers")
            col.prop(rd, "use_persistent_data", text="Persistent Data")
            
            if rd.engine == "CYCLES":
                layout.active = True
            else:
                layout.active = False
        
        
class OBJECT_PT_TMG_Render_Panel_Performance_Tiles(bpy.types.Panel):
    bl_idname = "OBJECT_PT_tmg_render_panel_performance_tiles"
    bl_label = ""
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = "OBJECT_PT_tmg_render_panel_performance"
    bl_options = {"DEFAULT_CLOSED"}

    def draw_header(self, context):
        scene = context.scene
        scene_eevee = scene.eevee
        rd = scene.render
        tmg_cam_vars = scene.tmg_cam_vars
        
        layout = self.layout
        layout.label(text='Tiles')
            
        if tmg_cam_vars.scene_camera and tmg_cam_vars.scene_camera.type == "CAMERA":
            if rd.engine == "CYCLES":
                layout.active = True
            else:
                layout.active = False
        else:
            layout.active = False

    def draw(self, context):
        scene = context.scene
        rd = scene.render
        tmg_cam_vars = scene.tmg_cam_vars
        
        if tmg_cam_vars.scene_camera and tmg_cam_vars.scene_camera.type == "CAMERA":
            layout = self.layout
            layout.use_property_split = True
            layout.use_property_decorate = False

            scene = context.scene
            rd = scene.render
            cscene = scene.cycles

            col = layout.column()

            sub = col.column(align=True)
            sub.prop(rd, "tile_x", text="Tiles X")
            sub.prop(rd, "tile_y", text="Y")
            col.prop(cscene, "tile_order", text="Order")

            sub = col.column()
            sub.active = not rd.use_save_buffers and not cscene.use_adaptive_sampling
            sub.prop(cscene, "use_progressive_refine")
            
            if rd.engine == "CYCLES":
                layout.active = True
            else:
                layout.active = False
        
        
class OBJECT_PT_TMG_Render_Panel_Performance_Threads(bpy.types.Panel):
    bl_idname = "OBJECT_PT_tmg_render_panel_performance_threads"
    bl_label = ""
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = "OBJECT_PT_tmg_render_panel_performance"
    bl_options = {"DEFAULT_CLOSED"}

    def draw_header(self, context):
        scene = context.scene
        scene_eevee = scene.eevee
        rd = scene.render
        tmg_cam_vars = scene.tmg_cam_vars
        
        layout = self.layout
        layout.label(text='Threads')
            
        if tmg_cam_vars.scene_camera and tmg_cam_vars.scene_camera.type == "CAMERA":
            if rd.engine == "CYCLES":
                layout.active = True
            else:
                layout.active = False
        else:
            layout.active = False

    def draw(self, context):
        scene = context.scene
        rd = scene.render
        tmg_cam_vars = scene.tmg_cam_vars
        
        if tmg_cam_vars.scene_camera and tmg_cam_vars.scene_camera.type == "CAMERA":
            layout = self.layout
            layout.use_property_split = True
            layout.use_property_decorate = False

            scene = context.scene
            rd = scene.render

            layout.prop(rd, "threads_mode")
            sub = layout.column(align=True)
            sub.enabled = rd.threads_mode == 'FIXED'
            sub.prop(rd, "threads")
            
            if rd.engine == "CYCLES":
                layout.active = True
            else:
                layout.active = False
        
        
class OBJECT_PT_TMG_Render_Panel_Performance_Viewport(bpy.types.Panel):
    bl_idname = "OBJECT_PT_tmg_render_panel_viewport"
    bl_label = ""
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = "OBJECT_PT_tmg_render_panel_performance"
    bl_options = {"DEFAULT_CLOSED"}

    def draw_header(self, context):
        scene = context.scene
        scene_eevee = scene.eevee
        rd = scene.render
        tmg_cam_vars = scene.tmg_cam_vars
        
        layout = self.layout
        layout.label(text='Viewport')
            
        if tmg_cam_vars.scene_camera and tmg_cam_vars.scene_camera.type == "CAMERA":
            if rd.engine == "CYCLES":
                layout.active = True
            else:
                layout.active = False
        else:
            layout.active = False

    def draw(self, context):
        scene = context.scene
        rd = scene.render
        tmg_cam_vars = scene.tmg_cam_vars
        
        if tmg_cam_vars.scene_camera and tmg_cam_vars.scene_camera.type == "CAMERA":
            layout = self.layout
            layout.use_property_split = True
            layout.use_property_decorate = False

            scene = context.scene
            rd = scene.render
            cscene = scene.cycles

            col = layout.column()
            col.prop(rd, "preview_pixel_size", text="Pixel Size")
            col.prop(cscene, "preview_start_resolution", text="Start Pixels")
            
            if rd.engine == "CYCLES":
                layout.active = True
            else:
                layout.active = False
        
        
class OBJECT_PT_TMG_Render_Panel_Resolution(bpy.types.Panel):
    bl_idname = "OBJECT_PT_tmg_render_panel_resolution"
    bl_label = "Resolution"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = "OBJECT_PT_tmg_render_panel"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        scene = context.scene
        props = scene.eevee
        tmg_cam_vars = scene.tmg_cam_vars
        camera = tmg_cam_vars.scene_camera
        
        if tmg_cam_vars.scene_camera and tmg_cam_vars.scene_camera.type == "CAMERA":
            layout = self.layout
            layout.use_property_split = True
            layout.use_property_decorate = False  # No animation.
            layout = layout.column()
            
            ## Global Scene Resolution
            if tmg_cam_vars.cam_res_lock_modes == '0':
                row = layout.row(align=True)

                row.prop(tmg_cam_vars, 'const_res_x', text='')
                row.prop(tmg_cam_vars, 'const_res_y', text='')

            ## Per Camera
            if tmg_cam_vars.cam_res_lock_modes == '1':
                row = layout.row(align=True)
                row.prop(tmg_cam_vars, 'res_x', text='')
                row.prop(tmg_cam_vars, 'res_y', text='')

            ## Presets             
            if tmg_cam_vars.cam_res_lock_modes == '2':
                 res_prop = layout.row(align=True)
                 res_prop.prop(scene.render, 'resolution_x', text='')
                 res_prop.prop(scene.render, 'resolution_y', text='')
                 res_prop.enabled = False
            
            layout.prop(tmg_cam_vars, 'cam_res_lock_modes', text="Lock")

            preset = layout.column()
            preset.prop(tmg_cam_vars, 'cam_resolution_presets', text="Presets")

            if tmg_cam_vars.cam_res_lock_modes == '2':
                preset.enabled = True
                preset.active = True
            else:
                preset.enabled = False
                preset.active = False

            layout.prop(scene.render, 'resolution_percentage', text="%")
            
            
class OBJECT_PT_TMG_Render_Panel_Sampling(bpy.types.Panel):
    bl_idname = "OBJECT_PT_tmg_render_panel_sampling"
    bl_label = "Sampling"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = "OBJECT_PT_tmg_render_panel"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        pass      
            
            
class OBJECT_PT_TMG_Render_Panel_Sampling_Advanced(bpy.types.Panel):
    bl_idname = "OBJECT_PT_tmg_render_panel_sampling_advanced"
    bl_label = ""
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = "OBJECT_PT_tmg_render_panel_sampling"
    COMPAT_ENGINES = {'CYCLES'}
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context):
        engine = context.scene.render.engine
        return engine in cls.COMPAT_ENGINES

    def draw_header(self, context):
        scene = context.scene
        scene_eevee = scene.eevee
        rd = scene.render
        tmg_cam_vars = scene.tmg_cam_vars
        
        layout = self.layout
        layout.label(text='Advanced')
        
        if tmg_cam_vars.scene_camera and tmg_cam_vars.scene_camera.type == "CAMERA":
            if rd.engine == "CYCLES":
                layout.active = True
            else:
                layout.active = False
        else:
            layout.active = False

    def draw(self, context):
        scene = context.scene
        scene_eevee = scene.eevee
        rd = scene.render
        cscene = scene.cycles
        tmg_cam_vars = scene.tmg_cam_vars
    
        if tmg_cam_vars.scene_camera and tmg_cam_vars.scene_camera.type == "CAMERA":
            camera = tmg_cam_vars.scene_camera
            
            layout = self.layout
            layout.use_property_split = True
            layout.use_property_decorate = False  # No animation.
            layout = layout.column()

            row = layout.row(align=True)
            row.prop(cscene, "seed")
            row.prop(cscene, "use_animated_seed", text="", icon='TIME')

            col = layout.column(align=True)
            col.active = not(cscene.use_adaptive_sampling)
            col.prop(cscene, "sampling_pattern", text="Pattern")

            layout.prop(cscene, "use_square_samples")

            layout.separator()

            col = layout.column(align=True)
            col.prop(cscene, "min_light_bounces")
            col.prop(cscene, "min_transparent_bounces")
            col.prop(cscene, "light_sampling_threshold", text="Light Threshold")

            if cscene.progressive != 'PATH' and use_branched_path(context):
                col = layout.column(align=True)
                col.prop(cscene, "sample_all_lights_direct")
                col.prop(cscene, "sample_all_lights_indirect")

            for view_layer in scene.view_layers:
                if view_layer.samples > 0:
                    layout.separator()
                    layout.row().prop(cscene, "use_layer_samples")
                    break
                
            if rd.engine == "CYCLES":
                layout.active = True
            else:
                layout.active = False
       
            
class OBJECT_PT_TMG_Render_Panel_Sampling_Denoising(bpy.types.Panel):
    bl_idname = "OBJECT_PT_tmg_render_panel_sampling_denoising"
    bl_label = ""
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = "OBJECT_PT_tmg_render_panel_sampling"
    COMPAT_ENGINES = {'CYCLES'}
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context):
        engine = context.scene.render.engine
        return engine in cls.COMPAT_ENGINES

    def draw_header(self, context):
        scene = context.scene
        tmg_cam_vars = scene.tmg_cam_vars
        
        layout = self.layout
        layout.label(text='Denoising')
        
        if tmg_cam_vars.scene_camera and tmg_cam_vars.scene_camera.type == "CAMERA":
            layout.active = True
        else:
            layout.active = False

    def draw(self, context):
        scene = context.scene
        scene_eevee = scene.eevee
        rd = scene.render
        cscene = scene.cycles
        tmg_cam_vars = scene.tmg_cam_vars
    
        if tmg_cam_vars.scene_camera and tmg_cam_vars.scene_camera.type == "CAMERA":
            camera = tmg_cam_vars.scene_camera
                
            layout = self.layout
            layout.use_property_split = True
            layout.use_property_decorate = False  # No animation.
            layout = layout.column()
            
            heading = layout.column(align=True, heading="Render")
            row = heading.row(align=True)
            row.prop(cscene, "use_denoising", text="")
            sub = row.row()

            sub.active = cscene.use_denoising
            for view_layer in scene.view_layers:
                if view_layer.cycles.denoising_store_passes:
                    sub.active = True

            sub.prop(cscene, "denoiser", text="")

            layout.separator()

            heading = layout.column(align=False, heading="Viewport")
            row = heading.row(align=True)
            row.prop(cscene, "use_preview_denoising", text="")
            sub = row.row()
            sub.active = cscene.use_preview_denoising
            sub.prop(cscene, "preview_denoiser", text="")

            sub = heading.row(align=True)
            sub.active = cscene.use_preview_denoising
            sub.prop(cscene, "preview_denoising_start_sample", text="Start Sample")
            sub = heading.row(align=True)
            sub.active = cscene.use_preview_denoising
            sub.prop(cscene, "preview_denoising_input_passes", text="Input Passes")
            
            layout.active = True
        else:
            layout.active = False
         

class OBJECT_PT_TMG_Render_Panel_Sampling_Samples(bpy.types.Panel):
    bl_idname = "OBJECT_PT_tmg_render_panel_sampling_samples"
    bl_label = "Samples"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = "OBJECT_PT_tmg_render_panel_sampling"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        scene = context.scene
        props = scene.eevee
        tmg_cam_vars = scene.tmg_cam_vars
    
        if tmg_cam_vars.scene_camera and tmg_cam_vars.scene_camera.type == "CAMERA":
            camera = tmg_cam_vars.scene_camera
            
            layout = self.layout
            layout.use_property_split = True
            layout.use_property_decorate = False  # No animation.
            layout = layout.column()

            layout.prop(props, "taa_render_samples", text="Render")
            layout.prop(props, "taa_samples", text="Viewport")
            layout.prop(props, "use_taa_reprojection")

          
class OBJECT_PT_TMG_Render_Panel_Timeline(bpy.types.Panel):
    bl_idname = "OBJECT_PT_tmg_render_panel_timeline"
    bl_label = "Timeline"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = "OBJECT_PT_tmg_render_panel"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        scene = context.scene
        tool_settings = context.tool_settings
        screen = context.screen
        tmg_cam_vars = scene.tmg_cam_vars
        
        if tmg_cam_vars.scene_camera and tmg_cam_vars.scene_camera.type == "CAMERA":
            layout = self.layout
            layout.use_property_split = True
            layout.use_property_decorate = False  # No animation.
            layout = layout.column()

            row = layout.row(align=True)
            row.prop(scene, 'use_preview_range', text='')
            row.prop(scene, 'frame_start', text='')
            row.prop(scene, 'frame_end', text='')

            row = layout.row(align=True)
            row.operator("screen.frame_jump", text="", icon='REW').end = False
            row.operator("screen.keyframe_jump", text="", icon='PREV_KEYFRAME').next = False
            if not screen.is_animation_playing:
                # if using JACK and A/V sync:
                #   hide the play-reversed button
                #   since JACK transport doesn't support reversed playback
                if scene.sync_mode == 'AUDIO_SYNC' and context.preferences.system.audio_device == 'JACK':
                    row.scale_x = 2
                    row.operator("screen.animation_play", text="", icon='PLAY')
                    row.scale_x = 1
                else:
                    row.operator("screen.animation_play", text="", icon='PLAY_REVERSE').reverse = True
                    row.operator("screen.animation_play", text="", icon='PLAY')
            else:
                row.scale_x = 2
                row.operator("screen.animation_play", text="", icon='PAUSE')
                row.scale_x = 1
            row.operator("screen.keyframe_jump", text="", icon='NEXT_KEYFRAME').next = True
            row.operator("screen.frame_jump", text="", icon='FF').end = True
            
#            row = layout.row(align=True)
#            if scene.show_subframe:
#                row.scale_x = 1.15
#                row.prop(scene, "frame_float", text="")
#            else:
#                row.scale_x = 0.95
#                row.prop(scene, "frame_current", text="")
     
          
class OBJECT_PT_TMG_Scene_Effects_Panel(bpy.types.Panel):
    bl_idname = 'OBJECT_PT_tmg_scene_effects_panel'
    bl_category = 'TMG Camera'
    bl_label = 'Scene Effects'
    bl_context = "objectmode"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        pass
    
        
class OBJECT_PT_TMG_Scene_Effects_Panel_AO(bpy.types.Panel):
    bl_idname = "OBJECT_PT_tmg_scene_effects_panel_ao"
    bl_label = ""
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = "OBJECT_PT_tmg_scene_effects_panel"
    COMPAT_ENGINES = {'BLENDER_EEVEE'}
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context):
        engine = context.scene.render.engine
        return engine in cls.COMPAT_ENGINES

    def draw_header(self, context):
        scene = context.scene
        rd = scene.render
        props = scene.eevee
        tmg_cam_vars = scene.tmg_cam_vars
        
        layout = self.layout
        
        if tmg_cam_vars.scene_camera and tmg_cam_vars.scene_camera.type == "CAMERA":
            layout.prop(props, "use_gtao")
            layout.active = props.use_gtao
        
        else:
            layout.label(text='Ambient Occlusion')
            layout.active = layout.active= False
            
        if rd.engine == "BLENDER_EEVEE":
            layout.active = True
        else:
            layout.active = False
            

    def draw(self, context):
        scene = context.scene
        rd = scene.render
        props = scene.eevee
        tmg_cam_vars = scene.tmg_cam_vars
    
        if tmg_cam_vars.scene_camera and tmg_cam_vars.scene_camera.type == "CAMERA":
            camera = tmg_cam_vars.scene_camera

            layout = self.layout
            layout.use_property_split = True
            layout.use_property_decorate = False  # No animation.
            layout = layout.column()
            layout.active = props.use_gtao
            
            layout.prop(props, "gtao_distance")
            layout.prop(props, "gtao_factor")
            layout.prop(props, "gtao_quality")
            layout.prop(props, "use_gtao_bent_normals")
            layout.prop(props, "use_gtao_bounce")
            
            if rd.engine == "BLENDER_EEVEE":
                layout.active = True
            else:
                layout.active = False
               
            
class OBJECT_PT_TMG_Scene_Effects_Panel_Bloom(bpy.types.Panel):
    bl_idname = "OBJECT_PT_tmg_scene_effects_panel_bloom"
    bl_label = ""
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = "OBJECT_PT_tmg_scene_effects_panel"
    COMPAT_ENGINES = {'BLENDER_EEVEE'}
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context):
        engine = context.scene.render.engine
        return engine in cls.COMPAT_ENGINES

    def draw_header(self, context):
        scene = context.scene
        rd = scene.render
        props = scene.eevee
        tmg_cam_vars = scene.tmg_cam_vars
        
        layout = self.layout
        
        if tmg_cam_vars.scene_camera and tmg_cam_vars.scene_camera.type == "CAMERA":
            layout.prop(props, "use_bloom")
            layout.active = props.use_bloom
            
        else:
            layout.label(text='Bloom')
            layout.active = layout.active= False
            
        if rd.engine == "BLENDER_EEVEE":
            layout.active = True
        else:
            layout.active = False

    def draw(self, context):
        scene = context.scene
        rd = scene.render
        props = scene.eevee
        tmg_cam_vars = scene.tmg_cam_vars
    
        if tmg_cam_vars.scene_camera and tmg_cam_vars.scene_camera.type == "CAMERA":
            camera = tmg_cam_vars.scene_camera

            layout = self.layout
            layout.use_property_split = True
            layout.use_property_decorate = False  # No animation.
            layout.active = props.use_bloom
            
            layout = layout.column()
            layout.prop(props, "bloom_threshold")
            layout.prop(props, "bloom_knee")
            layout.prop(props, "bloom_radius")
            layout.prop(props, "bloom_color")
            layout.prop(props, "bloom_intensity")
            layout.prop(props, "bloom_clamp")
            
            if rd.engine == "BLENDER_EEVEE":
                layout.active = True
            else:
                layout.active = False


class OBJECT_PT_TMG_Scene_Effects_Panel_Color_M(bpy.types.Panel):
    bl_idname = "OBJECT_PT_tmg_scene_effects_panel_color_m"
    bl_label = "Color Management"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = "OBJECT_PT_tmg_scene_effects_panel"
    COMPAT_ENGINES = {'BLENDER_RENDER', 'BLENDER_EEVEE', 'BLENDER_WORKBENCH'}
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        scene = context.scene
        rd = scene.render
        props = scene.eevee
        tmg_cam_vars = scene.tmg_cam_vars
        view = scene.view_settings

        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.


        if tmg_cam_vars.scene_camera and tmg_cam_vars.scene_camera.type == "CAMERA":  
            flow = layout.grid_flow(row_major=True, columns=0, even_columns=False, even_rows=False, align=True)

            col = flow.column()
            col.prop(scene.display_settings, "display_device")

            col.separator()

            col.prop(view, "view_transform")
            col.prop(view, "look")

            col = flow.column()
            col.prop(view, "exposure")
            col.prop(view, "gamma")

            col.separator()

            col.prop(scene.sequencer_colorspace_settings, "name", text="Sequencer")


class OBJECT_PT_TMG_Scene_Effects_Panel_Color_M_Use_Curves(bpy.types.Panel):
    bl_idname = "OBJECT_PT_tmg_scene_effects_panel_color_m_use_curves"
    bl_label = "Use Curves"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = "OBJECT_PT_tmg_scene_effects_panel_color_m"
    COMPAT_ENGINES = {'BLENDER_RENDER', 'BLENDER_EEVEE', 'BLENDER_WORKBENCH'}
    bl_options = {"DEFAULT_CLOSED"}

    def draw_header(self, context):

        scene = context.scene
        view = scene.view_settings

        self.layout.prop(view, "use_curve_mapping", text="")

    def draw(self, context):
        scene = context.scene
        rd = scene.render
        props = scene.eevee
        tmg_cam_vars = scene.tmg_cam_vars
        view = scene.view_settings

        layout = self.layout
        layout.use_property_split = False
        layout.use_property_decorate = False  # No animation.

        if tmg_cam_vars.scene_camera and tmg_cam_vars.scene_camera.type == "CAMERA":
            layout.enabled = view.use_curve_mapping
            layout.template_curve_mapping(view, "curve_mapping", type='COLOR', levels=True)


class OBJECT_PT_TMG_Scene_Effects_Panel_Depth_Of_Field(bpy.types.Panel):
    bl_idname = "OBJECT_PT_tmg_scene_effects_panel_depth_of_field"
    bl_label = ""
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = "OBJECT_PT_tmg_scene_effects_panel"
    bl_options = {"DEFAULT_CLOSED"}

    def draw_header(self, context):
        scene = context.scene
        tmg_cam_vars = scene.tmg_cam_vars
        
        if tmg_cam_vars.scene_camera and tmg_cam_vars.scene_camera.type == "CAMERA":
            camera = tmg_cam_vars.scene_camera
            dof = camera.data.dof
            
            self.layout.prop(tmg_cam_vars.scene_camera.data.dof, 'use_dof')
            self.layout.active = dof.use_dof
            
        else:
            layout = self.layout
            layout.label(text='Depth of Field')
            layout.active = layout.active= False

    def draw(self, context):
        scene = context.scene
        props = scene.eevee
        tmg_cam_vars = scene.tmg_cam_vars
    
        if tmg_cam_vars.scene_camera and tmg_cam_vars.scene_camera.type == "CAMERA":
            camera = tmg_cam_vars.scene_camera
            dof = camera.data.dof
            
            layout = self.layout
            layout.use_property_split = True
            layout.use_property_decorate = False
            layout = layout.column()
            layout.ui_units_y = 0.7
            layout.active = camera.data.dof.use_dof
            
            layout.prop(dof, 'focus_object')


class OBJECT_PT_TMG_Scene_Effects_Panel_Depth_Of_Field_Aperture(bpy.types.Panel):
    bl_idname = "OBJECT_PT_tmg_scene_effects_panel_depth_of_aperture"
    bl_label = ""
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = "OBJECT_PT_tmg_scene_effects_panel_depth_of_field"
    bl_options = {"DEFAULT_CLOSED"}

    def draw_header(self, context):
        scene = context.scene
        tmg_cam_vars = scene.tmg_cam_vars
        
        if tmg_cam_vars.scene_camera and tmg_cam_vars.scene_camera.type == "CAMERA":
            camera = tmg_cam_vars.scene_camera
            dof = camera.data.dof
            
            layout = self.layout
            layout.label(text='Aperture')
            layout.active = dof.use_dof
        
        else:
            layout = self.layout
            layout.label(text='Aperture')
            layout.active = layout.active= False
            

    def draw(self, context):
        scene = context.scene
        props = scene.eevee
        tmg_cam_vars = scene.tmg_cam_vars
    
        if tmg_cam_vars.scene_camera and tmg_cam_vars.scene_camera.type == "CAMERA":
            camera = tmg_cam_vars.scene_camera
            dof = camera.data.dof
            
            layout = self.layout
            layout.use_property_split = True
            layout.use_property_decorate = False
            layout = layout.column()
            layout.active = camera.data.dof.use_dof
            
            layout.prop(dof, 'aperture_fstop')
            layout.prop(dof, "aperture_blades")
            layout.prop(dof, "aperture_rotation")
            layout.prop(dof, "aperture_ratio")


class OBJECT_PT_TMG_Scene_Effects_Panel_Depth_Of_Field_Bokeh(bpy.types.Panel):
    bl_idname = "OBJECT_PT_tmg_scene_effects_panel_depth_of_bokeh"
    bl_label = ""
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = "OBJECT_PT_tmg_scene_effects_panel_depth_of_field"
    bl_options = {"DEFAULT_CLOSED"}

    def draw_header(self, context):
        scene = context.scene
        tmg_cam_vars = scene.tmg_cam_vars
        
        if tmg_cam_vars.scene_camera and tmg_cam_vars.scene_camera.type == "CAMERA":
            camera = tmg_cam_vars.scene_camera
            dof = camera.data.dof
            
            layout = self.layout
            layout.label(text='Bokeh')
            layout.active = dof.use_dof
            
        else:
            layout = self.layout
            layout.label(text='Bokeh')
            layout.active = layout.active= False

    def draw(self, context):
        scene = context.scene
        props = scene.eevee
        tmg_cam_vars = scene.tmg_cam_vars
    
        if tmg_cam_vars.scene_camera and tmg_cam_vars.scene_camera.type == "CAMERA":
            camera = tmg_cam_vars.scene_camera
            dof = camera.data.dof
            
            layout = self.layout
            layout.use_property_split = True
            layout.use_property_decorate = False
            layout = layout.column()
            layout.active = camera.data.dof.use_dof
            
            layout.prop(props, "bokeh_max_size")
            layout.prop(props, "bokeh_threshold")
            layout.prop(props, "bokeh_neighbor_max")
            layout.prop(props, "bokeh_denoise_fac")
            layout.prop(props, "use_bokeh_high_quality_slight_defocus")
            layout.prop(props, "use_bokeh_jittered")

            layout = layout.column()
            layout.active = props.use_bokeh_jittered
            layout.prop(props, "bokeh_overblur")


class OBJECT_PT_TMG_Scene_Effects_Panel_Motion_Blur(bpy.types.Panel):
    bl_idname = "OBJECT_PT_tmg_scene_effects_panel_motion_blur"
    bl_label = ""
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = "OBJECT_PT_tmg_scene_effects_panel"
    bl_options = {"DEFAULT_CLOSED"}

    def draw_header(self, context):
        scene = context.scene
        tmg_cam_vars = scene.tmg_cam_vars
        props = scene.eevee
        
        if tmg_cam_vars.scene_camera and tmg_cam_vars.scene_camera.type == "CAMERA":
            self.layout.prop(props, "use_motion_blur")
            self.layout.active = props.use_motion_blur
            
        else:
            layout = self.layout
            layout.label(text='Motion Blur')
            layout.active = layout.active= False

    def draw(self, context):
        scene = context.scene
        props = scene.eevee
        tmg_cam_vars = scene.tmg_cam_vars
    
        if tmg_cam_vars.scene_camera and tmg_cam_vars.scene_camera.type == "CAMERA":
            camera = tmg_cam_vars.scene_camera
            dof = camera.data.dof

            layout = self.layout
            layout.use_property_split = True
            layout.use_property_decorate = False
            layout = layout.column(align=False)

            layout.active = props.use_motion_blur
            layout.prop(props, "motion_blur_position", text="Position")
            layout.prop(props, "motion_blur_shutter")
            layout.separator()
            layout.prop(props, "motion_blur_depth_scale")
            layout.prop(props, "motion_blur_max")
            layout.prop(props, "motion_blur_steps", text="Steps")


class OBJECT_PT_TMG_Scene_Effects_Panel_Screen_Space_Reflections(bpy.types.Panel):
    bl_idname = "OBJECT_PT_tmg_scene_effects_panel_screen_space_reflections"
    bl_label = ""
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = "OBJECT_PT_tmg_scene_effects_panel"
    COMPAT_ENGINES = {'BLENDER_EEVEE'}
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context):
        engine = context.scene.render.engine
        return engine in cls.COMPAT_ENGINES

    def draw_header(self, context):
        scene = context.scene
        rd = scene.render
        props = scene.eevee
        tmg_cam_vars = scene.tmg_cam_vars
        
        layout = self.layout
        
        if tmg_cam_vars.scene_camera and tmg_cam_vars.scene_camera.type == "CAMERA":
            layout.prop(props, "use_ssr")
            layout.active = props.use_ssr
            
        else:
            layout.label(text='Screen Space Reflections')
            layout.active = layout.active= False
            
        if rd.engine == "BLENDER_EEVEE":
            layout.active = True
        else:
            layout.active = False

    def draw(self, context):
        scene = context.scene
        rd = scene.render
        props = scene.eevee
        tmg_cam_vars = scene.tmg_cam_vars
    
        if tmg_cam_vars.scene_camera and tmg_cam_vars.scene_camera.type == "CAMERA":
            camera = tmg_cam_vars.scene_camera
            dof = camera.data.dof

            layout = self.layout
            layout.use_property_split = True
            layout.use_property_decorate = False
            layout = layout.column(align=True)

            layout.active = props.use_ssr
            layout.prop(props, "use_ssr_refraction", text="Refraction")
            layout.prop(props, "use_ssr_halfres")
            
            layout = layout.column(align=False)
            layout.prop(props, "ssr_quality")
            layout.prop(props, "ssr_max_roughness")
            layout.prop(props, "ssr_thickness")
            layout.prop(props, "ssr_border_fade")
            layout.prop(props, "ssr_firefly_fac")  
            
        if rd.engine == "BLENDER_EEVEE":
            self.layout.active = True
        else:
            self.layout.active = False    
            
            
class OBJECT_PT_TMG_Scene_Effects_Panel_Shadows(bpy.types.Panel):
    bl_idname = "OBJECT_PT_tmg_scene_sffects_panel_shadows"
    bl_label = ""
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = "OBJECT_PT_tmg_scene_effects_panel"
    COMPAT_ENGINES = {'BLENDER_EEVEE'}
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context):
        engine = context.scene.render.engine
        return engine in cls.COMPAT_ENGINES

    def draw_header(self, context):
        scene = context.scene
        rd = scene.render
        props = scene.eevee
        tmg_cam_vars = scene.tmg_cam_vars
        
        layout = self.layout
        
        layout.label(text='Shadows')
            
        if rd.engine == "BLENDER_EEVEE":
            layout.active = True
        else:
            layout.active = False

    def draw(self, context):
        scene = context.scene
        rd = scene.render
        props = scene.eevee
        tmg_cam_vars = scene.tmg_cam_vars
        
        if tmg_cam_vars.scene_camera and tmg_cam_vars.scene_camera.type == "CAMERA":
            layout = self.layout
            layout.use_property_split = True
            layout.use_property_decorate = False  # No animation.
            layout = layout.column()

            layout.prop(props, "shadow_cube_size", text="Cube Size")
            layout.prop(props, "shadow_cascade_size", text="Cascade Size")
            layout.prop(props, "use_shadow_high_bitdepth")
            layout.prop(props, "use_soft_shadows")
            layout.prop(props, "light_threshold")
            
        if rd.engine == "BLENDER_EEVEE":
            self.layout.active = True
        else:
            self.layout.active = False 


class OBJECT_PT_TMG_Scene_Effects_Panel_Stereoscopy(bpy.types.Panel):
    bl_idname = "OBJECT_PT_tmg_scene_sffects_panel_stereoscopy"
    bl_label = ""
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = "OBJECT_PT_tmg_scene_effects_panel"
    bl_options = {"DEFAULT_CLOSED"}

    def draw_header(self, context):
        scene = context.scene
        tmg_cam_vars = scene.tmg_cam_vars
        rd = scene.render
        layout = self.layout
        
        if tmg_cam_vars.scene_camera and tmg_cam_vars.scene_camera.type == "CAMERA":
            layout.prop(rd, "use_multiview", text="Stereoscopy")
        else:
            layout.label(text='Stereoscopy')
            
        layout.active = layout.active = rd.use_multiview

    def draw(self, context):
        scene = context.scene
        props = scene.eevee
        rd = scene.render
        rv = rd.views.active
        tmg_cam_vars = scene.tmg_cam_vars
        
        if tmg_cam_vars.scene_camera and tmg_cam_vars.scene_camera.type == "CAMERA":
            layout = self.layout
            layout.use_property_split = True
            layout.use_property_decorate = False  # No animation.
            layout = layout.column()

            layout.active = rd.use_multiview
            basic_stereo = rd.views_format == 'STEREO_3D'

            row = layout.row()
            layout.row().prop(rd, "views_format", expand=True)

            if basic_stereo:
                row = layout.row()
                row.template_list("RENDER_UL_renderviews", "name", rd, "stereo_views", rd.views, "active_index", rows=2)

                row = layout.row()
                row.use_property_split = True
                row.use_property_decorate = False
                row.prop(rv, "file_suffix")

            else:
                row = layout.row()
                row.template_list("RENDER_UL_renderviews", "name", rd, "views", rd.views, "active_index", rows=2)

                col = row.column(align=True)
                col.operator("scene.render_view_add", icon='ADD', text="")
                col.operator("scene.render_view_remove", icon='REMOVE', text="")

                row = layout.row()
                row.use_property_split = True
                row.use_property_decorate = False
                row.prop(rv, "camera_suffix")


class OBJECT_PT_TMG_Scene_Effects_Panel_Subsurface_Scattering(bpy.types.Panel):
    bl_idname = "OBJECT_PT_tmg_scene_sffects_panel_subsurface_scattering"
    bl_label = ""
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = "OBJECT_PT_tmg_scene_effects_panel"
    COMPAT_ENGINES = {'BLENDER_EEVEE'}
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context):
        engine = context.scene.render.engine
        return engine in cls.COMPAT_ENGINES

    def draw_header(self, context):
        scene = context.scene
        rd = scene.render
        props = scene.eevee
        tmg_cam_vars = scene.tmg_cam_vars
        
        layout = self.layout
        
        layout.label(text='Subsurface Scattering')
            
        if rd.engine == "BLENDER_EEVEE":
            layout.active = True
        else:
            layout.active = False

    def draw(self, context):
        scene = context.scene
        rd = scene.render
        props = scene.eevee
        tmg_cam_vars = scene.tmg_cam_vars
        
        if tmg_cam_vars.scene_camera and tmg_cam_vars.scene_camera.type == "CAMERA":
            layout = self.layout
            layout.use_property_split = True
            layout.use_property_decorate = False  # No animation.
            layout = layout.column()

            layout = layout.column()
            layout.prop(props, "sss_samples")
            layout.prop(props, "sss_jitter_threshold")
            
        if rd.engine == "BLENDER_EEVEE":
            self.layout.active = True
        else:
            self.layout.active = False 
            

class OBJECT_PT_TMG_Scene_Effects_Panel_Volumetrics_Eevee(bpy.types.Panel):
    bl_idname = "OBJECT_PT_tmg_scene_effects_panel_volumetrics_eevee"
    bl_label = ""
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = "OBJECT_PT_tmg_scene_effects_panel"
    COMPAT_ENGINES = {'BLENDER_EEVEE'}
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context):
        engine = context.scene.render.engine
        return engine in cls.COMPAT_ENGINES

    def draw_header(self, context):
        scene = context.scene
        rd = scene.render        
        tmg_cam_vars = scene.tmg_cam_vars
        
        layout = self.layout
        layout.label(text='Volumetrics')

    def draw(self, context):
        scene = context.scene
        rd = scene.render
        props = scene.eevee
        tmg_cam_vars = scene.tmg_cam_vars
        
        if tmg_cam_vars.scene_camera and tmg_cam_vars.scene_camera.type == "CAMERA":                           
            layout = self.layout
            layout.use_property_split = True
            layout.use_property_decorate = False  # No animation.
            
            layout = layout.column(align=True)
            layout.prop(props, "volumetric_start")
            layout.prop(props, "volumetric_end")

            layout = layout.column()
            layout.prop(props, "volumetric_tile_size")
            layout.prop(props, "volumetric_samples")
            layout.prop(props, "volumetric_sample_distribution", text="Distribution") 

            self.layout.active = True
        else:
            self.layout.active = False 


class OBJECT_PT_TMG_Scene_Effects_Panel_Volumetrics_Eevee_Samples(bpy.types.Panel):
    bl_idname = "OBJECT_PT_tmg_scene_effects_panel_volumetrics_eevee_samples"
    bl_label = ""
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = "OBJECT_PT_tmg_scene_effects_panel_volumetrics_eevee"
    COMPAT_ENGINES = {'BLENDER_EEVEE'}
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context):
        engine = context.scene.render.engine
        return engine in cls.COMPAT_ENGINES

    def draw_header(self, context):
        scene = context.scene
        rd = scene.render
        tmg_cam_vars = scene.tmg_cam_vars
                           
        layout = self.layout
        layout.label(text='Samples')

    def draw(self, context):
        scene = context.scene
        rd = scene.render
        props = scene.eevee
        tmg_cam_vars = scene.tmg_cam_vars
        
        if tmg_cam_vars.scene_camera and tmg_cam_vars.scene_camera.type == "CAMERA":
            layout = self.layout
            layout.use_property_split = True
            layout.use_property_decorate = False  # No animation.

                                       
            layout = layout.column()
            layout.prop(props, "volumetric_samples", text="Render")
            layout.prop(props, "volumetric_samples", text="Viewport")

            self.layout.active = True
        else:
            self.layout.active = False 


class OBJECT_PT_TMG_Scene_Effects_Panel_Volumetrics_Eevee_Lighting(bpy.types.Panel):
    bl_label = "Lighting"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = "OBJECT_PT_tmg_scene_effects_panel_volumetrics_eevee"
    COMPAT_ENGINES = {'BLENDER_EEVEE'}
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context):
        engine = context.scene.render.engine
        return engine in cls.COMPAT_ENGINES

    def draw_header(self, context):
        scene = context.scene
        rd = scene.render   
        props = scene.eevee        
        tmg_cam_vars = scene.tmg_cam_vars
                   
        self.layout.prop(props, "use_volumetric_lights", text="")

    def draw(self, context):
        scene = context.scene
        rd = scene.render     
        props = scene.eevee   
        tmg_cam_vars = scene.tmg_cam_vars
        
        if tmg_cam_vars.scene_camera and tmg_cam_vars.scene_camera.type == "CAMERA":
            layout = self.layout
            layout.use_property_split = True
            scene = context.scene
                           
            layout.active = props.use_volumetric_lights
            layout.prop(props, "volumetric_light_clamp", text="Light Clamping")

            self.layout.active = True
        else:
            self.layout.active = False 


class OBJECT_PT_TMG_Scene_Effects_Panel_Volumetrics_Eevee_Shadows(bpy.types.Panel):
    bl_label = "Shadows"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = "OBJECT_PT_tmg_scene_effects_panel_volumetrics_eevee"
    COMPAT_ENGINES = {'BLENDER_EEVEE'}
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context):
        engine = context.scene.render.engine
        return engine in cls.COMPAT_ENGINES

    def draw_header(self, context):
        scene = context.scene
        rd = scene.render
        props = scene.eevee   
        tmg_cam_vars = scene.tmg_cam_vars
   
        self.layout.prop(props, "use_volumetric_shadows", text="")

    def draw(self, context):
        scene = context.scene
        rd = scene.render
        props = scene.eevee
        tmg_cam_vars = scene.tmg_cam_vars
        
        if tmg_cam_vars.scene_camera and tmg_cam_vars.scene_camera.type == "CAMERA":
            layout = self.layout
            layout.use_property_split = True
         
            layout.active = props.use_volumetric_shadows
            layout.prop(props, "volumetric_shadow_samples", text="Samples")

            self.layout.active = True
        else:
            self.layout.active = False 


class OBJECT_PT_TMG_Scene_Effects_Panel_Volumetrics_Cycles(bpy.types.Panel):
    bl_idname = "OBJECT_PT_tmg_scene_effects_panel_volumetrics_cycles"
    bl_label = ""
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = "OBJECT_PT_tmg_scene_effects_panel"
    COMPAT_ENGINES = {'CYCLES'}
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context):
        engine = context.scene.render.engine
        return engine in cls.COMPAT_ENGINES

    def draw_header(self, context):
        scene = context.scene
        rd = scene.render        
        tmg_cam_vars = scene.tmg_cam_vars
        
        layout = self.layout
        layout.label(text='Volumetrics')

    def draw(self, context):
        scene = context.scene
        rd = scene.render
        props = scene.eevee
        tmg_cam_vars = scene.tmg_cam_vars
        
        if tmg_cam_vars.scene_camera and tmg_cam_vars.scene_camera.type == "CAMERA":                           
            layout = self.layout
            layout.use_property_split = True
            layout.use_property_decorate = False

            scene = context.scene
            cscene = scene.cycles

            col = layout.column(align=True)
            col.prop(cscene, "volume_step_rate", text="Step Rate Render")
            col.prop(cscene, "volume_preview_step_rate", text="Viewport")
            layout.prop(cscene, "volume_max_steps", text="Max Steps")
            col.prop(rd, "simplify_volumes", text="Volume Resolution")

            self.layout.active = True
        else:
            self.layout.active = False 


class OBJECT_PT_TMG_Selected_Object_Panel(bpy.types.Panel):
    bl_idname = 'OBJECT_PT_tmg_selected_object_panel'
    bl_category = 'TMG Camera'
    bl_label = 'Selected Object'
    bl_context = "objectmode"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        pass


class OBJECT_PT_TMG_S_OB_Name(bpy.types.Panel):
    bl_idname = "OBJECT_PT_tmg_s_ob_name"
    bl_category = 'TMG Camera'
    bl_label = "Name"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = "OBJECT_PT_tmg_selected_object_panel"
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context):
        if bpy.context.active_object:
            ob = context.active_object
        else:
            ob = None
        return ob

    def draw(self, context):
        scene = context.scene
        props = scene.eevee
        tmg_cam_vars = scene.tmg_cam_vars

        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False 

        # if tmg_cam_vars.scene_camera and tmg_cam_vars.scene_camera.type == "CAMERA":
        if bpy.context.active_object:
            ob = context.active_object
        else:
            ob = None

        if ob:
            layout = layout.column()
            layout.prop(tmg_cam_vars, 'ob_name_lock')
            
            if tmg_cam_vars.ob_name_lock:
                layout.prop(tmg_cam_vars, 'ob_name')
            else:
                layout.prop(tmg_cam_vars, 'ob_name')

                if bpy.context.active_object.data != None:
                    layout.prop(tmg_cam_vars, 'ob_data_name')


class OBJECT_PT_TMG_EEVEE_Light(bpy.types.Panel):
    bl_idname = "OBJECT_PT_tmg_eevee_light"
    bl_category = 'TMG Camera'
    bl_label = "Light"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = "OBJECT_PT_tmg_selected_object_panel"
    bl_options = {"DEFAULT_CLOSED"}
    COMPAT_ENGINES = {'BLENDER_EEVEE'}

    @classmethod
    def poll(cls, context):
        engine = context.scene.render.engine

        if bpy.context.active_object and bpy.context.active_object.type == "LIGHT":
            light = context.active_object.data
        else:
            light = None

        return engine in cls.COMPAT_ENGINES and light

    def draw(self, context):
        layout = self.layout        

        if bpy.context.active_object and bpy.context.active_object.type == "LIGHT":
            light = context.active_object.data
        else:
            light = None

        if light:
            # Compact layout for node editor.
            if self.bl_space_type == 'PROPERTIES':
                layout.row().prop(light, "type", expand=True)
                layout.use_property_split = True
            else:
                layout.use_property_split = True
                layout.row().prop(light, "type")

            col = layout.column()
            col.prop(light, "color")
            col.prop(light, "energy")

            col.separator()

            col.prop(light, "diffuse_factor", text="Diffuse")
            col.prop(light, "specular_factor", text="Specular")
            col.prop(light, "volume_factor", text="Volume")


class OBJECT_PT_TMG_EEVEE_Light_Distance(bpy.types.Panel):
    bl_idname = "OBJECT_PT_tmg_eevee_light_distance"
    bl_label = "Custom Distance"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = "OBJECT_PT_tmg_eevee_light"
    COMPAT_ENGINES = {'BLENDER_EEVEE'}
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context):
        engine = context.scene.render.engine

        if bpy.context.active_object and bpy.context.active_object.type == "LIGHT":
            if context.active_object.data.type != "SUN":
                light = context.active_object.data
            else:
                light = None
        else:
            light = None

        return engine in cls.COMPAT_ENGINES and light

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        if bpy.context.active_object and bpy.context.active_object.type == "LIGHT":
            light = context.active_object.data
        else:
            light = None

        if light:
            layout.prop(light, "cutoff_distance", text="Distance")

            # layout.active = light.use_custom_distance


class OBJECT_PT_TMG_EEVEE_Light_Beam_Shape(bpy.types.Panel):
    bl_idname = "OBJECT_PT_tmg_eevee_light_beam_shape"
    bl_label = "Beam Shape"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = "OBJECT_PT_tmg_eevee_light"
    COMPAT_ENGINES = {'BLENDER_EEVEE'}
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context):
        engine = context.scene.render.engine

        if bpy.context.active_object and bpy.context.active_object.type == "LIGHT":    
            light = context.active_object.data            
        else:
            light = None

        return engine in cls.COMPAT_ENGINES and light

    def draw(self, context):
        scene = context.scene
        rd = scene.render
        props = scene.eevee
        tmg_cam_vars = scene.tmg_cam_vars
        
        # if tmg_cam_vars.scene_camera and tmg_cam_vars.scene_camera.type == "CAMERA":                           
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        if context.active_object.type == "LIGHT":        
            light = context.active_object.data                
        else:
            light = None

        if light:
            if light.type == "SPOT":
                layout.prop(light, "shadow_soft_size", text="Radius")
                layout.prop(light, "spot_size", text="Size")
                layout.prop(light, "spot_blend", text="Blend", slider=True)
                layout.prop(light, "show_cone")
            
            if light.type == 'AREA':
                layout.prop(light, "shape")                    

                sub = layout.column(align=True)

                if light.shape in {'SQUARE', 'DISK'}:
                    sub.prop(light, "size")
                elif light.shape in {'RECTANGLE', 'ELLIPSE'}:
                    sub.prop(light, "size", text="Size X")
                    sub.prop(light, "size_y", text="Y")

            if light.type == 'POINT':
                layout.prop(light, "shadow_soft_size", text="Radius")

            if light.type == 'SUN':
                layout.prop(light, "angle", text="Angle")
            

class OBJECT_PT_TMG_CYCLES_Light(bpy.types.Panel):
    bl_idname = "OBJECT_PT_TMG_cycles_light"
    bl_category = 'TMG Camera'
    bl_label = "Light"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = "OBJECT_PT_tmg_selected_object_panel"
    bl_options = {"DEFAULT_CLOSED"}
    COMPAT_ENGINES = {'CYCLES'}

    @classmethod
    def poll(cls, context):
        engine = context.scene.render.engine

        if bpy.context.active_object and bpy.context.active_object.type == "LIGHT":
            light = context.active_object.data
        else:
            light = None

        return engine in cls.COMPAT_ENGINES and light

    def draw(self, context):
        layout = self.layout

        if bpy.context.active_object and bpy.context.active_object.type == "LIGHT":
            light = context.active_object.data
        else:
            light = None

        if light:
            clamp = light.cycles

            if self.bl_space_type == 'PROPERTIES':
                layout.row().prop(light, "type", expand=True)
                layout.use_property_split = True
            else:
                layout.use_property_split = True
                layout.row().prop(light, "type")

            col = layout.column()

            col.prop(light, "color")
            col.prop(light, "energy")
            col.separator()

            if not (light.type == 'AREA' and clamp.is_portal):
                sub = col.column()
                if use_branched_path(context):
                    subsub = sub.row(align=True)
                    subsub.active = use_sample_all_lights(context)
                    subsub.prop(clamp, "samples")
                sub.prop(clamp, "max_bounces")

            sub = col.column(align=True)
            sub.active = not (light.type == 'AREA' and clamp.is_portal)
            sub.prop(clamp, "cast_shadow")
            sub.prop(clamp, "use_multiple_importance_sampling", text="Multiple Importance")

            if light.type == 'AREA':
                col.prop(clamp, "is_portal", text="Portal")


class OBJECT_PT_TMG_CYCLES_Light_Beam_Shape(bpy.types.Panel):
    bl_idname = "OBJECT_PT_TMG_cycles_light_beam_shape"
    bl_category = 'TMG Camera'
    bl_label = "Beam Shape"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_context = "data"
    bl_parent_id = "OBJECT_PT_TMG_cycles_light"
    bl_options = {"DEFAULT_CLOSED"}
    COMPAT_ENGINES = {'CYCLES'}

    @classmethod
    def poll(cls, context):
        engine = context.scene.render.engine

        if bpy.context.active_object and bpy.context.active_object.type == "LIGHT":
            if bpy.context.active_object.data.type in {'SPOT', "AREA"}:
                light = context.active_object.data
            else:
                light = None
        else:
            light = None

        return engine in cls.COMPAT_ENGINES and light

    def draw(self, context):
        layout = self.layout

        if bpy.context.active_object and bpy.context.active_object.type == "LIGHT":
            light = context.active_object.data
        else:
            light = Noneroperty_split = True
        layout.use_property_decorate = False

        if light:
            
            layout.use_property_split = True
            col = layout.column()

            if light.type in {'POINT', 'SPOT'}:
                col.prop(light, "shadow_soft_size", text="Radius")

            if light.type == 'SUN':
                col.prop(light, "angle")

            if light.type == 'SPOT':
                col.prop(light, "spot_size", text="Spot Size")
                col.prop(light, "spot_blend", text="Blend", slider=True)
                col.prop(light, "show_cone")
            
            if light.type == 'AREA':
                # if light.type == 'AREA':
                col.prop(light, "shape", text="Shape")
                sub = col.column(align=True)

                if light.shape in {'SQUARE', 'DISK'}:
                    sub.prop(light, "size")
                elif light.shape in {'RECTANGLE', 'ELLIPSE'}:
                    sub.prop(light, "size", text="Size X")
                    sub.prop(light, "size_y", text="Y")

                col.prop(light, "spread", text="Spread")


class OBJECT_PT_TMG_Viewport_Panel(bpy.types.Panel):
    bl_idname = 'OBJECT_PT_tmg_viewport_panel'
    bl_category = 'TMG Camera'
    bl_label = 'Viewport'
    bl_context = "objectmode"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        pass


class OBJECT_PT_TMG_Viewport_Panel_Composition(bpy.types.Panel):
    bl_idname = "OBJECT_PT_tmg_viewport_panel_composition"
    bl_label = ""
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = "OBJECT_PT_tmg_viewport_panel"
    bl_options = {"DEFAULT_CLOSED"}

    def draw_header(self, context):
        scene = context.scene
        tmg_cam_vars = scene.tmg_cam_vars
        props = scene.eevee
        
        if tmg_cam_vars.scene_camera and tmg_cam_vars.scene_camera.type == "CAMERA":
            layout = self.layout
            layout.use_property_split = True
            layout.use_property_decorate = False  # No animation.
            
            layout.label(text='Composition')
            layout.active = context.space_data.overlay.show_overlays
            
        else:
            layout = self.layout
            layout.label(text='Composition')
            layout.active = layout.active= False

    def draw(self, context):
        scene = context.scene
        tmg_cam_vars = scene.tmg_cam_vars
        
        if tmg_cam_vars.scene_camera and tmg_cam_vars.scene_camera.type == "CAMERA":
            layout = self.layout
            layout.use_property_split = True
            layout.use_property_decorate = False  # No animation.
            layout = layout.column(align=True)
            layout.active = context.space_data.overlay.show_overlays
        
            camera = tmg_cam_vars.scene_camera
            
            layout.prop(camera.data, "show_composition_thirds")

            col = layout.column(heading="Center", align=True)
            col.prop(camera.data, "show_composition_center")
            col.prop(camera.data, "show_composition_center_diagonal", text="Diagonal")

            col = layout.column(heading="Golden", align=True)
            col.prop(camera.data, "show_composition_golden", text="Ratio")
            col.prop(camera.data, "show_composition_golden_tria_a", text="Triangle A")
            col.prop(camera.data, "show_composition_golden_tria_b", text="Triangle B")

            col = layout.column(heading="Harmony", align=True)
            col.prop(camera.data, "show_composition_harmony_tri_a", text="Triangle A")
            col.prop(camera.data, "show_composition_harmony_tri_b", text="Triangle B")


class OBJECT_PT_TMG_Viewport_Panel_Display(bpy.types.Panel):
    bl_idname = "OBJECT_PT_tmg_viewport_panel_display"
    bl_label = "Display"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = "OBJECT_PT_tmg_viewport_panel"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        scene = context.scene
        tmg_cam_vars = scene.tmg_cam_vars
    
        if tmg_cam_vars.scene_camera and tmg_cam_vars.scene_camera.type == "CAMERA":
            layout = self.layout
            layout.use_property_split = True
            layout.use_property_decorate = False  # No animation.
            c1 = layout.column(align=True)
            c2 = layout.column(align=True)
            c1.active = context.space_data.overlay.show_overlays
            
            camera = tmg_cam_vars.scene_camera
            
            c1.prop(camera.data, "display_size", text="Size")

            c1 = c1.column(heading="Show")
            c1.prop(camera.data, "show_limits", text="Limits")
            c1.prop(camera.data, "show_mist", text="Mist")
            c1.prop(camera.data, "show_sensor", text="Sensor")
            c1.prop(camera.data, "show_name", text="Name")

            c2 = layout.column(align=False, heading="Passepartout")
            c2.use_property_decorate = False
            row = c2.row(align=True)
            sub = row.row(align=True)
            sub.prop(tmg_cam_vars, "use_camera_passepartout_alpha", text="")
            sub = sub.row(align=True)
            sub.active = camera.data.show_passepartout
            sub.prop(tmg_cam_vars, "camera_passepartout_alpha", text="")
        
        
class OBJECT_PT_TMG_Viewport_Panel_User_Preferences(bpy.types.Panel):
    bl_idname = "OBJECT_PT_tmg_viewport_panel_user_preferences"
    bl_label = "User Preferences"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = "OBJECT_PT_tmg_viewport_panel"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        scene = context.scene
        tmg_cam_vars = scene.tmg_cam_vars
        prefs = context.preferences
        view = prefs.view
        system = prefs.system
    
        if tmg_cam_vars.scene_camera and tmg_cam_vars.scene_camera.type == "CAMERA":
            layout = self.layout
            layout.use_property_split = True
            layout.use_property_decorate = False  # No animation.

            import sys
            prefs = context.preferences
            inputs = prefs.inputs

            layout.prop(inputs, "use_mouse_emulate_3_button")
            if sys.platform[:3] != "win":
                layout.prop(inputs, "mouse_emulate_3_button_modifier")
                layout.active = inputs.use_mouse_emulate_3_button

            layout.prop(system, "use_region_overlap")
            layout.prop(view, "render_display_type", text='Render In')
            
            
class OBJECT_PT_TMG_Viewport_Panel_View(bpy.types.Panel):
    bl_idname = "OBJECT_PT_tmg_viewport_panel_view"
    bl_label = "View"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = "OBJECT_PT_tmg_viewport_panel"
    bl_options = {"DEFAULT_CLOSED"}
            
    def draw(self, context):
        scene = context.scene
        view = context.space_data
        tmg_cam_vars = scene.tmg_cam_vars
             
        if tmg_cam_vars.scene_camera and tmg_cam_vars.scene_camera.type == "CAMERA":
            layout = self.layout
            layout.use_property_split = True
            layout.use_property_decorate = False 
            layout = layout.column()

            subcol = layout.column()
            subcol.active = bool(view.region_3d.view_perspective != 'CAMERA' or view.region_quadviews)
            subcol.prop(view, "lens", text="Focal Length")

            subcol = layout.column(align=True)
            subcol.prop(view, "clip_start", text="Clip Start")
            subcol.prop(view, "clip_end", text="End")

            layout = layout.column(align=True)
            layout.prop(view, "use_render_border")
            layout.active = view.region_3d.view_perspective != 'CAMERA'  
        

