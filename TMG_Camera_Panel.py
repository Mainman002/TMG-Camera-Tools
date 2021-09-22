import bpy, sys, os
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty, IntProperty, FloatProperty, FloatVectorProperty, PointerProperty
from bpy.types import Operator

## Extra online resources used in this script
## https://blender.stackexchange.com/questions/155515/how-do-a-create-a-foldout-ui-panel

bl_info = {
    "name": "TMG_Camera_Tools",
    "author": "Johnathan Mueller",
    "descrtion": "A panel to set camera sensor values for rendering",
    "blender": (2, 80, 0),
    "version": (0, 2, 0),
    "location": "View3D (ObjectMode) > Sidebar > TMG_Camera Tab",
    "warning": "",
    "category": "Object"
}


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
}


def _change_ob(self, context, _ob):
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = _ob
    _ob.select_set(True) 
    return _ob


def _change_camera_presets(self, context):
    scene = context.scene
    tmg_cam_vars = scene.tmg_cam_vars
    
    if tmg_cam_vars.cam_sensor_format == '0':
        active_dict["focal_l"] = 24
        active_dict["sensor_w"] = 36
        active_dict["sensor_h"] = 36
        active_dict["ortho_scale"] = 10
        active_dict["fStop"] = 2.0
        
    if tmg_cam_vars.cam_sensor_format == '1':
        active_dict["focal_l"] = 50
        active_dict["sensor_w"] = 36
        active_dict["sensor_h"] = 36
        active_dict["ortho_scale"] = 5
        active_dict["fStop"] = 2.0
        
    if tmg_cam_vars.cam_sensor_format == '2':
        active_dict["focal_l"] = 80
        active_dict["sensor_w"] = 36
        active_dict["sensor_h"] = 36
        active_dict["ortho_scale"] = 2.8
        active_dict["fStop"] = 2.8
        
    if tmg_cam_vars.cam_sensor_format == '3':
        active_dict["focal_l"] = 210
        active_dict["sensor_w"] = 36
        active_dict["sensor_h"] = 36
        active_dict["ortho_scale"] = 1
        active_dict["fStop"] = 2.8
    
    _set_cam_values(self, context)


def _change_resolution_presets(self, context):
    scene = context.scene
    tmg_cam_vars = scene.tmg_cam_vars
    camera = tmg_cam_vars.scene_camera
    
    camera["resolution"] = tmg_cam_vars.cam_resolution_presets
    _set_cam_res_values(self, context)


def _change_res_mode_presets(self, context):
    scene = context.scene
    tmg_cam_vars = scene.tmg_cam_vars
    camera = tmg_cam_vars.scene_camera
    
    camera["res_mode"] = tmg_cam_vars.cam_resolution_mode_presets
    _set_cam_res_values(self, context)


def _change_res_lock(self, context):
    scene = context.scene
    tmg_cam_vars = scene.tmg_cam_vars
    camera = tmg_cam_vars.scene_camera
    
    try:
        if tmg_cam_vars.res_lock:
            scene.render.resolution_x = camera["res_x"]
            scene.render.resolution_y = camera["res_y"]
    except:
        camera["res_x"] = scene.render.resolution_x
        camera["res_y"] = scene.render.resolution_y
    
    _set_cam_res_values(self, context)


def _set_cam_res_values(self, context):
    scene = context.scene
    tmg_cam_vars = scene.tmg_cam_vars
  
    camera = tmg_cam_vars.scene_camera
    print("Camera: ", camera.data.name)
    
    if camera:
        res_x = 1920
        res_y = 1080
        tmp_res_x = 1920
        tmp_res_y = 1080
        
        try:
            res = camera["resolution"]
            mode = camera["res_mode"]
        except:
            if not tmg_cam_vars.res_lock:
                res = tmg_cam_vars.cam_resolution_presets
                mode = tmg_cam_vars.cam_resolution_mode_presets
        
        if res == '0': # VGA
            tmp_res_x = 640
            tmp_res_y = 480
        elif res == '1': # HD
            tmp_res_x = 1280
            tmp_res_y = 720
        elif res == '2': # HD-F
            tmp_res_x = 1920
            tmp_res_y = 1080
        elif res == '3': # 2k
            tmp_res_x = 2560
            tmp_res_y = 1440
        elif res == '4': # 4k
            tmp_res_x = 3840
            tmp_res_y = 2160
        elif res == '5': # 8k
            tmp_res_x = 7680
            tmp_res_y = 4320
            
        if tmg_cam_vars.res_lock:
            res_x = tmg_cam_vars.res_x
            res_y = tmg_cam_vars.res_y
        else:
            if mode == '0':
                res_x = tmp_res_x
                res_y = tmp_res_y
            elif mode == '1':
                res_x = tmp_res_y
                res_y = tmp_res_x
            elif mode == '2':
                res_x = tmp_res_x
                res_y = tmp_res_x

        camera["res_x"] = int(res_x)
        camera["res_y"] = int(res_y)
        
        scene.render.resolution_x = int(res_x)
        scene.render.resolution_y = int(res_y)
    
    
def _change_scene_camera(self, context):
    scene = context.scene
    tmg_cam_vars = scene.tmg_cam_vars

    camera = tmg_cam_vars.scene_camera

    if camera and camera.type == "CAMERA":
        scene.camera = camera
        bpy.context.space_data.camera = camera
        
        try:
            if camera["resolution"]:
                tmg_cam_vars.cam_resolution_presets = camera["resolution"]
            if camera["res_mode"]:
                tmg_cam_vars.cam_resolution_mode_presets = camera["res_mode"]
            if camera["res_x"]:
                scene.render.resolution_x = int(camera["res_x"])
            if camera["res_y"]:
                scene.render.resolution_y = int(camera["res_y"])
        except:
            camera["res_mode"] = 0
            camera["resolution"] = 2
            camera["res_x"] = 1920
            camera["res_y"] = 1080
            
            tmg_cam_vars.cam_resolution_presets = str(camera["resolution"])
            tmg_cam_vars.cam_resolution_mode_presets = str(camera["res_mode"])
            scene.render.resolution_x = camera["res_x"]
            scene.render.resolution_y = camera["res_y"]
        
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
    print("Camera: ", camera.data.name)
    
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
    
    
def _move_constraint(self, context, _con, _dir):
    scene = context.scene
    tmg_cam_vars = scene.tmg_cam_vars
    camera = tmg_cam_vars.scene_camera
    original_ob = bpy.context.active_object
    
    _change_ob(self, context, camera)
    
    for name, con in camera.constraints.items():
        if con.type == _con:
            mod = camera.constraints.get(con.name)
            print(mod)
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


class TMG_Camera_Properties(bpy.types.PropertyGroup):
    scene_camera : bpy.props.PointerProperty(name='Camera', type=bpy.types.Object, poll=_tmg_search_cameras, description='Scene active camera', update=_change_scene_camera)
    render_slot : bpy.props.IntProperty(default=1, min=1, max=8, options={'ANIMATABLE'}, update=_set_render_slot)
    
    curve_lock_scale : bpy.props.BoolProperty(default=False)
    curve_size_x : bpy.props.FloatProperty(default=1, min=0.01, update=_curve_size)
    curve_size_y : bpy.props.FloatProperty(default=1, min=0.01, update=_curve_size)
    curve_size_z : bpy.props.FloatProperty(default=1, min=0.01, update=_curve_size)
    
    res_lock : bpy.props.BoolProperty(default=False, update=_change_res_lock)
#    res : bpy.props.FloatVectorProperty(default=(1920.0, 1080.0), subtype='PIXEL', unit='CAMERA', size=2, min=4, step=15, precision=0, update=_change_resolution_presets)
    res_x : bpy.props.FloatProperty(default=1920, subtype='PIXEL', min=4, step=15, precision=0, update=_change_resolution_presets)
    res_y : bpy.props.FloatProperty(default=1080, subtype='PIXEL', min=4, step=15, precision=0, update=_change_resolution_presets)

    cam_sensor_format : bpy.props.EnumProperty(name='Sensor Profile', default='0', description='Camera presets',
    items=[
    ('0', '24mm', ''),
    ('1', '50mm', ''),
    ('2', '80mm', ''),
    ('3', '210mm', '')], update=_change_camera_presets)
    
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
    

class OBJECT_PT_TMG_Camera_Panel(bpy.types.Panel):
    bl_idname = 'OBJECT_PT_tmg_camera_panel'
    bl_category = 'TMG Camera'
    bl_label = 'Camera'
    bl_context = "objectmode"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    
#    def draw_header_preset(self, context):
#        test : bpy.types.BoolProperty(default=False)

    def draw(self, context):
        scene = context.scene
        tmg_cam_vars = scene.tmg_cam_vars
        
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.
        col = layout.column(align=True)
        row = col.row(align=True)
        col.ui_units_y = 1.7

        row.prop(tmg_cam_vars, 'scene_camera', text='')
    
        if tmg_cam_vars.scene_camera or context.space_data.lock_camera:
            row = col.row(align=True)
            row.operator("object.tmg_select_camera", text='', icon="RESTRICT_SELECT_ON")
            row.operator('view3d.view_camera', text='', icon="CAMERA_DATA")
            row.operator('view3d.view_center_camera', text='', icon="SHADING_BBOX")
            row.prop(context.space_data, 'lock_camera', text='', icon="LOCKVIEW_ON")
        else:
            col.ui_units_y = 1.7
            col.label(text='Select a camera to begin')
        
            
class OBJECT_PT_TMG_Camera_Panel_Perspective(bpy.types.Panel):
    bl_idname = "OBJECT_PT_tmg_camera_panel_perspective"
    bl_label = "Perspective"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = "OBJECT_PT_tmg_camera_panel"
    bl_options = {"DEFAULT_CLOSED"}
#    bl_options = {'HIDE_HEADER'}
            
    def draw(self, context):
        scene = context.scene
        tmg_cam_vars = scene.tmg_cam_vars
             
        if tmg_cam_vars.scene_camera and tmg_cam_vars.scene_camera.type == "CAMERA":
            layout = self.layout
            layout.use_property_split = True
            layout.use_property_decorate = False 
            scene = context.scene
            props = scene.eevee
                
            col = layout.column()
        
            col.prop(tmg_cam_vars.scene_camera.data, 'type')
            col.prop(tmg_cam_vars, 'cam_sensor_format')
            
            col.prop(tmg_cam_vars.scene_camera.data, 'sensor_fit')
            col.label(text="Focal Length")
            
            if tmg_cam_vars.scene_camera.data.type != "ORTHO":
                col = layout.row(align=True)
                col.prop(tmg_cam_vars.scene_camera.data, 'lens', text='')
            else:
                col = layout.row(align=True)
                col.prop(tmg_cam_vars.scene_camera.data, 'ortho_scale', text='')

            if tmg_cam_vars.scene_camera.data.sensor_fit != "VERTICAL":
                col.prop(tmg_cam_vars.scene_camera.data, 'sensor_width', text='')
            else:
                col.prop(tmg_cam_vars.scene_camera.data, 'sensor_height', text='')
                
            row = layout.row(align=True)
            row.label(text="Clip Area")
            
            row = layout.row(align=True)
            row.prop(tmg_cam_vars.scene_camera.data, 'clip_start', text='')
            row.prop(tmg_cam_vars.scene_camera.data, 'clip_end', text='')
                                   
            
class OBJECT_PT_TMG_Constraints_Panel(bpy.types.Panel):
    bl_idname = 'OBJECT_PT_tmg_constraints_panel'
    bl_category = 'TMG Camera'
    bl_label = 'Constraints'
    bl_context = "objectmode"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
                 
class OBJECT_PT_TMG_Constraints_Panel_Floor(bpy.types.Panel):
    bl_idname = "SUB_PT_Gensett"
    bl_label = "Floor"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = "OBJECT_PT_tmg_constraints_panel"
    bl_options = {"DEFAULT_CLOSED"}
#    bl_options = {'HIDE_HEADER'}

    def draw_header(self, context):
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
                props = row.operator("object.tmg_remove_constraint", text='', icon="X")
                props.con = "FLOOR"
            except:
                cn = None
                props = row.operator("object.tmg_add_constraint", text='', icon="ADD")
                props.con = "FLOOR"

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
                
                props = row.operator("object.tmg_move_constraint", text='', icon="TRIA_UP")
                props.con = "FLOOR"
                props.dir = "UP"
                
                props = row.operator("object.tmg_move_constraint", text='', icon="TRIA_DOWN")
                props.con = "FLOOR"
                props.dir = "DOWN"
                
#                props = row.operator("object.tmg_remove_constraint", text='', icon="X")
#                props.con = "FLOOR"
                
                row = col.row(align=True)
                row.prop(cn, 'target', text='')
                row.prop(cn, 'offset', text='')
                
            except:
                cn = None
#                props = row.operator("object.tmg_add_constraint", text='', icon="CON_FLOOR")
#                props.con = "FLOOR"
                             
                             
class OBJECT_PT_TMG_Constraints_Panel_Follow_Path(bpy.types.Panel):
    bl_idname = "OBJECT_PT_tmg_constraints_panel_follow_path"
    bl_label = "Follow Path"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = "OBJECT_PT_tmg_constraints_panel"
    bl_options = {"DEFAULT_CLOSED"}
#    bl_options = {'HIDE_HEADER'}

    def draw_header(self, context):
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
                cn = camera.constraints["Follow Path"]
                props = row.operator("object.tmg_remove_constraint", text='', icon="X")
                props.con = "FOLLOW_PATH"
            except:
                cn = None
                props = row.operator("object.tmg_add_constraint", text='', icon="ADD")
                props.con = "FOLLOW_PATH"

    def draw(self, context):
        scene = context.scene
        tmg_cam_vars = scene.tmg_cam_vars
        
        if tmg_cam_vars.scene_camera and tmg_cam_vars.scene_camera.type == "CAMERA":
#            layout = self.layout
#            layout.use_property_split = True
#            layout.use_property_decorate = False  # No animation.
#            col = layout.column(align=True)
#            row = col.row(align=True)

            layout = self.layout
            layout.use_property_split = True
            layout.use_property_decorate = False 
            scene = context.scene
            props = scene.eevee
                
            col = layout.column()
            row = col.row(align=True)
        
            camera = tmg_cam_vars.scene_camera
            cons = camera.constraints.items()
                
            try:
                cn = camera.constraints["Follow Path"]
                row.prop(cn, 'mute', text='')
                
                props = row.operator("object.tmg_move_constraint", text='', icon="TRIA_UP")
                props.con = "FOLLOW_PATH"
                props.dir = "UP"
                
                props = row.operator("object.tmg_move_constraint", text='', icon="TRIA_DOWN")
                props.con = "FOLLOW_PATH"
                props.dir = "DOWN"

                row = col.row(align=True)
                row.prop(cn, 'target', text='')
                
                if cn.use_fixed_location:
                    row = col.row(align=True)
                    row.prop(cn, 'offset_factor')
                else:
                    row = col.row(align=True)
                    row.prop(cn, 'offset')
                    
                col_c = layout.column(align=True)
                row_c = col_c.row(align=True)
                col = row_c.column(align=True)
                col2 = row_c.column(align=True)
                col.alignment='RIGHT'
                col2.alignment='LEFT'
                
                col.label(text='Fixed Location')
                col2.prop(cn, 'use_fixed_location', text='', icon="CON_LOCLIMIT")
            
                col.label(text='Curve Radius')
                col2.prop(cn, 'use_curve_radius', text='', icon="CURVE_BEZCIRCLE")
                
                col.label(text='Follow Curve')
                col2.prop(cn, 'use_curve_follow', text='', icon="CON_FOLLOWPATH")
            except:
                cn = None
#                props = row.operator("object.tmg_add_constraint", text='', icon="CON_FOLLOWPATH")
#                props.con = "FOLLOW_PATH"
                
                
class OBJECT_PT_TMG_Constraints_Panel_Follow_Path_Spline_Scale(bpy.types.Panel):
    bl_idname = "OBJECT_PT_tmg_constraints_panel_follow_path_spline_scale"
    bl_label = "Spline Scale"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = "OBJECT_PT_tmg_constraints_panel_follow_path"
    bl_options = {"DEFAULT_CLOSED"}
#    bl_options = {'HIDE_HEADER'}

    def draw_header(self, context):
        scene = context.scene
        tmg_cam_vars = scene.tmg_cam_vars
        
        if tmg_cam_vars.scene_camera and tmg_cam_vars.scene_camera.type == "CAMERA":
            layout = self.layout
            layout.use_property_split = True
            layout.use_property_decorate = False 
            scene = context.scene
            props = scene.eevee
                
            col = layout.column()
        
            camera = tmg_cam_vars.scene_camera
            cons = camera.constraints.items()
            
            try:
                cn = camera.constraints["Follow Path"]
                
                if tmg_cam_vars.scene_camera and tmg_cam_vars.scene_camera.type == "CAMERA":
                    camera = tmg_cam_vars.scene_camera
                    cons = camera.constraints.items()
                    
                    if tmg_cam_vars.curve_lock_scale:
                        col.prop(tmg_cam_vars, 'curve_lock_scale', text='', icon="LOCKED")
                    else:
                        col.prop(tmg_cam_vars, 'curve_lock_scale', text='', icon="UNLOCKED")
            except:
                cn = None

    def draw(self, context):
        scene = context.scene
        tmg_cam_vars = scene.tmg_cam_vars
        
        if tmg_cam_vars.scene_camera and tmg_cam_vars.scene_camera.type == "CAMERA":
            layout = self.layout
            layout.use_property_split = True
            layout.use_property_decorate = False 
            scene = context.scene
            props = scene.eevee
                
            col = layout.column()
        
            camera = tmg_cam_vars.scene_camera
            cons = camera.constraints.items()
                
            try:
                cn = camera.constraints["Follow Path"]
                
                if tmg_cam_vars.curve_lock_scale:
                    col.prop(tmg_cam_vars, 'curve_size_x', text='Scale')
                else:
                    col.prop(tmg_cam_vars, 'curve_size_x', text='X')
                    col.prop(tmg_cam_vars, 'curve_size_y', text='Y')
                    col.prop(tmg_cam_vars, 'curve_size_z', text='Z')
            except:
                cn = None
                
                
class OBJECT_PT_TMG_Constraints_Panel_Track_To(bpy.types.Panel):
    bl_idname = "OBJECT_PT_tmg_constraints_panel_track_to"
    bl_label = "Track To"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = "OBJECT_PT_tmg_constraints_panel"
    bl_options = {"DEFAULT_CLOSED"}
#    bl_options = {'HIDE_HEADER'}

    def draw_header(self, context):
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
                cn = camera.constraints["Track To"]
                props = row.operator("object.tmg_remove_constraint", text='', icon="X")
                props.con = "TRACK_TO"
            except:
                cn = None
                props = row.operator("object.tmg_add_constraint", text='', icon="ADD")
                props.con = "TRACK_TO"

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
                cn = camera.constraints["Track To"]
                row.prop(cn, 'mute', text='')
                
                props = row.operator("object.tmg_move_constraint", text='', icon="TRIA_UP")
                props.con = "TRACK_TO"
                props.dir = "UP"
                
                props = row.operator("object.tmg_move_constraint", text='', icon="TRIA_DOWN")
                props.con = "TRACK_TO"
                props.dir = "DOWN"
                
#                props = row.operator("object.tmg_remove_constraint", text='', icon="X")
#                props.con = "TRACK_TO"

                row = col.row(align=True)
                row.prop(cn, 'target', text='')
                row.prop(cn, 'influence', text='')
            except:
                cn = None  
#                props = row.operator("object.tmg_add_constraint", text='', icon="CON_TRACKTO")
#                props.con = "TRACK_TO"
                
            
class OBJECT_PT_TMG_Render_Panel(bpy.types.Panel):
    bl_idname = 'OBJECT_PT_tmg_render_panel'
    bl_category = 'TMG Camera'
    bl_label = 'Render'
    bl_context = "objectmode"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        scene = context.scene
        tmg_cam_vars = scene.tmg_cam_vars
        
        if tmg_cam_vars.scene_camera and tmg_cam_vars.scene_camera.type == "CAMERA":
            layout = self.layout


class OBJECT_PT_TMG_Render_Panel_Aspect(bpy.types.Panel):
    bl_idname = "OBJECT_PT_tmg_render_panel_aspect"
    bl_label = "Aspect"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = "OBJECT_PT_tmg_render_panel"
    bl_options = {"DEFAULT_CLOSED"}
#    bl_options = {'HIDE_HEADER'}

    def draw(self, context):
        scene = context.scene
        tmg_cam_vars = scene.tmg_cam_vars
        
        if tmg_cam_vars.scene_camera and tmg_cam_vars.scene_camera.type == "CAMERA":
            layout = self.layout
            layout.use_property_split = True
            layout.use_property_decorate = False  # No animation.
            col = layout.column(align=True)
            row = col.row(align=True)

            row.prop(scene.render, 'pixel_aspect_x', text='')
            row.prop(scene.render, 'pixel_aspect_y', text='')
         
         
class OBJECT_PT_TMG_Render_Panel_Render(bpy.types.Panel):
    bl_idname = "OBJECT_PT_tmg_render_panel_render"
    bl_label = "Render"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = "OBJECT_PT_tmg_render_panel"
    bl_options = {"DEFAULT_CLOSED"}
#    bl_options = {'HIDE_HEADER'}

    def draw(self, context):
        scene = context.scene
        tmg_cam_vars = scene.tmg_cam_vars
        
        if tmg_cam_vars.scene_camera and tmg_cam_vars.scene_camera.type == "CAMERA":
            layout = self.layout
            layout.use_property_split = True
            layout.use_property_decorate = False 
            scene = context.scene
            props = scene.eevee
            
            col = layout.column()
            col.prop(scene.render, 'filepath')
            col.prop(scene.render, 'engine')
            
            col.prop(scene.render.image_settings, 'file_format')
            col.prop(scene.render.image_settings, 'color_mode')
            
            col.use_property_split = False
    
            row = col.row(align=True)
            row.prop(tmg_cam_vars, 'render_slot', text='Slot')
            row.operator("render.render", text='Image', icon="CAMERA_DATA")
                            
            row = col.row(align=True)
            row.prop(scene, 'use_nodes', icon="NODE_COMPOSITING")
            row.operator("render.render", text='Animation', icon="RENDER_ANIMATION").animation=True
             
        
class OBJECT_PT_TMG_Render_Panel_Resolution(bpy.types.Panel):
    bl_idname = "OBJECT_PT_tmg_render_panel_resolution"
    bl_label = "Resolution"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = "OBJECT_PT_tmg_render_panel"
    bl_options = {"DEFAULT_CLOSED"}
#    bl_options = {'HIDE_HEADER'}

    def draw(self, context):
        scene = context.scene
        tmg_cam_vars = scene.tmg_cam_vars
        
        if tmg_cam_vars.scene_camera and tmg_cam_vars.scene_camera.type == "CAMERA":
            layout = self.layout
            layout.use_property_split = True
            layout.use_property_decorate = False 
            scene = context.scene
            props = scene.eevee
                
            row = layout.row(align=True)
            
            if tmg_cam_vars.res_lock:
                row.prop(tmg_cam_vars, 'res_lock', text='', icon="LOCKED")
                row.prop(tmg_cam_vars, 'res_x', text='')
                row.prop(tmg_cam_vars, 'res_y', text='')
            else:
                row.prop(tmg_cam_vars, 'res_lock', text='', icon="UNLOCKED")
                row.prop(scene.render, 'resolution_x', text='')
                row.prop(scene.render, 'resolution_y', text='')
            
            layout.prop(tmg_cam_vars, 'cam_resolution_presets')
            layout.prop(tmg_cam_vars, 'cam_resolution_mode_presets')
            
            layout.prop(scene.render, 'resolution_percentage')


class OBJECT_PT_TMG_Render_Panel_Sampling(bpy.types.Panel):
    bl_idname = "OBJECT_PT_tmg_render_panel_sampling"
    bl_label = "Sampling"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = "OBJECT_PT_tmg_render_panel"
    bl_options = {"DEFAULT_CLOSED"}
#    bl_options = {'HIDE_HEADER'}

    def draw(self, context):
        scene = context.scene
        tmg_cam_vars = scene.tmg_cam_vars
        
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.
        col = layout.column(align=True)
    
        if tmg_cam_vars.scene_camera or context.space_data.lock_camera:
            camera = tmg_cam_vars.scene_camera

            layout = self.layout
            layout.use_property_split = True
            layout.use_property_decorate = False  # No animation.

            scene = context.scene
            props = scene.eevee

            col = layout.column(align=True)
            col.prop(props, "taa_render_samples", text="Render")
            col.prop(props, "taa_samples", text="Viewport")

            col = layout.column()
            col.prop(props, "use_taa_reprojection")
          
          
class OBJECT_PT_TMG_Render_Panel_Timeline(bpy.types.Panel):
    bl_idname = "OBJECT_PT_tmg_render_panel_timeline"
    bl_label = "Timeline"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = "OBJECT_PT_tmg_render_panel"
    bl_options = {"DEFAULT_CLOSED"}
#    bl_options = {'HIDE_HEADER'}

    def draw(self, context):
        scene = context.scene
        tool_settings = context.tool_settings
        screen = context.screen
        tmg_cam_vars = scene.tmg_cam_vars
        
        if tmg_cam_vars.scene_camera and tmg_cam_vars.scene_camera.type == "CAMERA":
            layout = self.layout
            layout.use_property_split = True
            layout.use_property_decorate = False  # No animation.
            col = layout.column(align=True)
            row = col.row(align=True)

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
        layout = self.layout
        
class OBJECT_PT_TMG_Scene_Effects_Panel_AO(bpy.types.Panel):
    bl_idname = "OBJECT_PT_tmg_scene_effects_panel_ao"
    bl_label = "Ambient Occlusion"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = "OBJECT_PT_tmg_scene_effects_panel"
    bl_options = {"DEFAULT_CLOSED"}
#    bl_options = {'HIDE_HEADER'}

    def draw_header(self, context):
        scene = context.scene
        tmg_cam_vars = scene.tmg_cam_vars
        props = scene.eevee
        
        if tmg_cam_vars.scene_camera or context.space_data.lock_camera:
            self.layout.prop(props, "use_gtao", text="")

    def draw(self, context):
        scene = context.scene
        tmg_cam_vars = scene.tmg_cam_vars
        
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.
        col = layout.column(align=True)
    
        if tmg_cam_vars.scene_camera or context.space_data.lock_camera:
            camera = tmg_cam_vars.scene_camera

            layout = self.layout
            layout.use_property_split = True
            layout.use_property_decorate = False
            scene = context.scene
            props = scene.eevee

            layout.active = props.use_gtao
            col = layout.column()
            col.prop(props, "gtao_distance")
            col.prop(props, "gtao_factor")
            col.prop(props, "gtao_quality")
            col.prop(props, "use_gtao_bent_normals")
            col.prop(props, "use_gtao_bounce")
               
            
class OBJECT_PT_TMG_Scene_Effects_Panel_Bloom(bpy.types.Panel):
    bl_idname = "OBJECT_PT_tmg_scene_effects_panel_bloom"
    bl_label = "Bloom"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = "OBJECT_PT_tmg_scene_effects_panel"
    bl_options = {"DEFAULT_CLOSED"}
#    bl_options = {'HIDE_HEADER'}

    def draw_header(self, context):
        scene = context.scene
        tmg_cam_vars = scene.tmg_cam_vars
        props = scene.eevee
        
        if tmg_cam_vars.scene_camera or context.space_data.lock_camera:
            self.layout.prop(props, "use_bloom", text="")

    def draw(self, context):
        scene = context.scene
        tmg_cam_vars = scene.tmg_cam_vars
        
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.
        col = layout.column(align=True)
    
        if tmg_cam_vars.scene_camera or context.space_data.lock_camera:
            camera = tmg_cam_vars.scene_camera

            layout = self.layout
            layout.use_property_split = True

            scene = context.scene
            props = scene.eevee

            layout.active = props.use_bloom
            col = layout.column()
            col.prop(props, "bloom_threshold")
            col.prop(props, "bloom_knee")
            col.prop(props, "bloom_radius")
            col.prop(props, "bloom_color")
            col.prop(props, "bloom_intensity")
            col.prop(props, "bloom_clamp")


class OBJECT_PT_TMG_Scene_Effects_Panel_Depth_Of_Field(bpy.types.Panel):
    bl_idname = "OBJECT_PT_tmg_scene_effects_panel_depth_of_field"
    bl_label = "Depth of Field"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = "OBJECT_PT_tmg_scene_effects_panel"
    bl_options = {"DEFAULT_CLOSED"}
#    bl_options = {'HIDE_HEADER'}

    def draw_header(self, context):
        scene = context.scene
        tmg_cam_vars = scene.tmg_cam_vars
        
        if tmg_cam_vars.scene_camera or context.space_data.lock_camera:
            self.layout.prop(tmg_cam_vars.scene_camera.data.dof, 'use_dof', text='')

    def draw(self, context):
        scene = context.scene
        tmg_cam_vars = scene.tmg_cam_vars
    
        if tmg_cam_vars.scene_camera or context.space_data.lock_camera:
            props = scene.eevee
            camera = tmg_cam_vars.scene_camera
            dof = camera.data.dof
            
            layout = self.layout
            layout.use_property_split = True
            layout.use_property_decorate = False
            col = layout.column()
            
            col.prop(dof, 'focus_object')


class OBJECT_PT_TMG_Scene_Effects_Panel_Depth_Of_Field_Aperture(bpy.types.Panel):
    bl_idname = "OBJECT_PT_tmg_scene_effects_panel_depth_of_aperture"
    bl_label = "Aperture"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = "OBJECT_PT_tmg_scene_effects_panel_depth_of_field"
    bl_options = {"DEFAULT_CLOSED"}
#    bl_options = {'HIDE_HEADER'}

    def draw(self, context):
        scene = context.scene
        tmg_cam_vars = scene.tmg_cam_vars
    
        if tmg_cam_vars.scene_camera or context.space_data.lock_camera:
            props = scene.eevee
            camera = tmg_cam_vars.scene_camera
            dof = camera.data.dof
            
            layout = self.layout
            layout.use_property_split = True
            layout.use_property_decorate = False
            col = layout.column()
            
            col.prop(dof, 'aperture_fstop')
            col.prop(dof, "aperture_blades")
            col.prop(dof, "aperture_rotation")
            col.prop(dof, "aperture_ratio")


class OBJECT_PT_TMG_Scene_Effects_Panel_Depth_Of_Field_Bokeh(bpy.types.Panel):
    bl_idname = "OBJECT_PT_tmg_scene_effects_panel_depth_of_bokeh"
    bl_label = "Bokeh"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = "OBJECT_PT_tmg_scene_effects_panel_depth_of_field"
    bl_options = {"DEFAULT_CLOSED"}
#    bl_options = {'HIDE_HEADER'}

    def draw(self, context):
        scene = context.scene
        tmg_cam_vars = scene.tmg_cam_vars
    
        if tmg_cam_vars.scene_camera or context.space_data.lock_camera:
            props = scene.eevee
            camera = tmg_cam_vars.scene_camera
            dof = camera.data.dof
            
            layout = self.layout
            layout.use_property_split = True
            layout.use_property_decorate = False
            col = layout.column()
            
            col.prop(props, "bokeh_max_size")
            col.prop(props, "bokeh_threshold")
            col.prop(props, "bokeh_neighbor_max")
            col.prop(props, "bokeh_denoise_fac")
            col.prop(props, "use_bokeh_high_quality_slight_defocus")
            col.prop(props, "use_bokeh_jittered")

            col = layout.column()
            col.active = props.use_bokeh_jittered
            col.prop(props, "bokeh_overblur")


class OBJECT_PT_TMG_Scene_Effects_Panel_Motion_Blur(bpy.types.Panel):
    bl_idname = "OBJECT_PT_tmg_scene_effects_panel_motion_blur"
    bl_label = "Motion Blur"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = "OBJECT_PT_tmg_scene_effects_panel"
    bl_options = {"DEFAULT_CLOSED"}
#    bl_options = {'HIDE_HEADER'}

    def draw_header(self, context):
        scene = context.scene
        tmg_cam_vars = scene.tmg_cam_vars
        props = scene.eevee
        
        if tmg_cam_vars.scene_camera or context.space_data.lock_camera:
            self.layout.prop(props, "use_motion_blur", text="")

    def draw(self, context):
        scene = context.scene
        tmg_cam_vars = scene.tmg_cam_vars
    
        if tmg_cam_vars.scene_camera or context.space_data.lock_camera:
            props = scene.eevee
            camera = tmg_cam_vars.scene_camera
            dof = camera.data.dof

            layout = self.layout
            layout.use_property_split = True
            layout.use_property_decorate = False
            scene = context.scene
            props = scene.eevee

            layout.active = props.use_motion_blur
            col = layout.column()
            col.prop(props, "motion_blur_position", text="Position")
            col.prop(props, "motion_blur_shutter")
            col.separator()
            col.prop(props, "motion_blur_depth_scale")
            col.prop(props, "motion_blur_max")
            col.prop(props, "motion_blur_steps", text="Steps")


class OBJECT_PT_TMG_Scene_Effects_Panel_Screen_Space_Reflections(bpy.types.Panel):
    bl_idname = "OBJECT_PT_tmg_scene_effects_panel_screen_space_reflections"
    bl_label = "Screen Space Reflections"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = "OBJECT_PT_tmg_scene_effects_panel"
    bl_options = {"DEFAULT_CLOSED"}
#    bl_options = {'HIDE_HEADER'}

    def draw_header(self, context):
        scene = context.scene
        tmg_cam_vars = scene.tmg_cam_vars
        props = scene.eevee
        
        if tmg_cam_vars.scene_camera or context.space_data.lock_camera:
            self.layout.prop(props, "use_ssr", text="")

    def draw(self, context):
        scene = context.scene
        tmg_cam_vars = scene.tmg_cam_vars
    
        if tmg_cam_vars.scene_camera or context.space_data.lock_camera:
            props = scene.eevee
            camera = tmg_cam_vars.scene_camera
            dof = camera.data.dof

            layout = self.layout
            layout.use_property_split = True
            layout.use_property_decorate = False

            scene = context.scene
            props = scene.eevee

            col = layout.column()
            col.active = props.use_ssr
            col.prop(props, "use_ssr_refraction", text="Refraction")
            col.prop(props, "use_ssr_halfres")
            col.prop(props, "ssr_quality")
            col.prop(props, "ssr_max_roughness")
            col.prop(props, "ssr_thickness")
            col.prop(props, "ssr_border_fade")
            col.prop(props, "ssr_firefly_fac")      
            

class OBJECT_PT_TMG_Viewport_Panel(bpy.types.Panel):
    bl_idname = 'OBJECT_PT_tmg_viewport_panel'
    bl_category = 'TMG Camera'
    bl_label = 'Viewport'
    bl_context = "objectmode"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout

class OBJECT_PT_TMG_Viewport_Panel_Composition(bpy.types.Panel):
    bl_idname = "OBJECT_PT_tmg_viewport_panel_composition"
    bl_label = "Composition"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = "OBJECT_PT_tmg_viewport_panel"
    bl_options = {"DEFAULT_CLOSED"}
#    bl_options = {'HIDE_HEADER'}

    def draw(self, context):
        scene = context.scene
        tmg_cam_vars = scene.tmg_cam_vars
        
        if tmg_cam_vars.scene_camera or context.space_data.lock_camera:
            layout = self.layout
            layout.use_property_split = True
            layout.use_property_decorate = False  # No animation.
            col = layout.column(align=True)
        
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
#    bl_options = {'HIDE_HEADER'}

    def draw(self, context):
        scene = context.scene
        tmg_cam_vars = scene.tmg_cam_vars
    
        if tmg_cam_vars.scene_camera or context.space_data.lock_camera:
            layout = self.layout
            layout.use_property_split = True
            layout.use_property_decorate = False  # No animation.
            col = layout.column(align=True)
            row = col.row(align=True)
            
            camera = tmg_cam_vars.scene_camera
            
            col.prop(camera.data, "display_size", text="Size")

            col = layout.column(heading="Show")
            col.prop(camera.data, "show_limits", text="Limits")
            col.prop(camera.data, "show_mist", text="Mist")
            col.prop(camera.data, "show_sensor", text="Sensor")
            col.prop(camera.data, "show_name", text="Name")

            col = layout.column(align=False, heading="Passepartout")
            col.use_property_decorate = False
            row = col.row(align=True)
            sub = row.row(align=True)
            sub.prop(camera.data, "show_passepartout", text="")
            sub = sub.row(align=True)
            sub.active = camera.data.show_passepartout
            sub.prop(camera.data, "passepartout_alpha", text="")
#            row.prop_decorator(camera.data, "passepartout_alpha")
        

classes = (
    ## Properties
    TMG_Camera_Properties,
    
    ## Camera Panel
    OBJECT_PT_TMG_Camera_Panel,
    OBJECT_PT_TMG_Camera_Panel_Perspective,
    
    ## Constraints Panel
    OBJECT_PT_TMG_Constraints_Panel,
    OBJECT_PT_TMG_Constraints_Panel_Floor,
    OBJECT_PT_TMG_Constraints_Panel_Follow_Path,
    OBJECT_PT_TMG_Constraints_Panel_Follow_Path_Spline_Scale,
    OBJECT_PT_TMG_Constraints_Panel_Track_To,
    
    ## Render Panel
    OBJECT_PT_TMG_Render_Panel,
    OBJECT_PT_TMG_Render_Panel_Aspect,
    OBJECT_PT_TMG_Render_Panel_Render,
    OBJECT_PT_TMG_Render_Panel_Resolution,
    OBJECT_PT_TMG_Render_Panel_Sampling,
    OBJECT_PT_TMG_Render_Panel_Timeline,
    
    ## Scene Effects Panel
    OBJECT_PT_TMG_Scene_Effects_Panel,
    OBJECT_PT_TMG_Scene_Effects_Panel_AO,
    OBJECT_PT_TMG_Scene_Effects_Panel_Bloom,
    OBJECT_PT_TMG_Scene_Effects_Panel_Depth_Of_Field,
    OBJECT_PT_TMG_Scene_Effects_Panel_Depth_Of_Field_Aperture,
    OBJECT_PT_TMG_Scene_Effects_Panel_Depth_Of_Field_Bokeh,
    OBJECT_PT_TMG_Scene_Effects_Panel_Motion_Blur,
    OBJECT_PT_TMG_Scene_Effects_Panel_Screen_Space_Reflections,
    
    ## Viewport Panel
    OBJECT_PT_TMG_Viewport_Panel,
    OBJECT_PT_TMG_Viewport_Panel_Composition,
    OBJECT_PT_TMG_Viewport_Panel_Display,
    
    ## Extra Operators
    OBJECT_OT_Add_Constraint,
    OBJECT_OT_Move_Constraint,
    OBJECT_OT_Remove_Constraint,
    OBJECT_OT_Select_Camera,
)


def register():
    for rsclass in classes:
        bpy.utils.register_class(rsclass)
        bpy.types.Scene.tmg_cam_vars = bpy.props.PointerProperty(type=TMG_Camera_Properties)


def unregister():
    for rsclass in classes:
        bpy.utils.unregister_class(rsclass)


if __name__ == "__main__":
    register()
    





