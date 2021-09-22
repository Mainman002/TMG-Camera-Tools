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
    "version": (0, 1, 9),
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
            res_x = tmg_cam_vars.res[0]
            res_y = tmg_cam_vars.res[1]
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
        
        
def _set_render_slot(self, context):
    scene = context.scene
    tmg_cam_vars = scene.tmg_cam_vars
    try:
        slot = bpy.data.images["Render Result"].render_slots.active_index = int(tmg_cam_vars.render_slot)-1
    except:
        slot = None
   
   
def _add_constraint(self, context, _con):
    scene = context.scene
    tmg_cam_vars = scene.tmg_cam_vars
    camera = tmg_cam_vars.scene_camera

    camera.constraints.new(_con)
       
       
def _remove_constraint(self, context, _con):
    scene = context.scene
    tmg_cam_vars = scene.tmg_cam_vars
    camera = tmg_cam_vars.scene_camera
    
    for name, con in camera.constraints.items():
        if con.type == _con:
            camera.constraints.remove(con)


def _tmg_search_cameras(self, object):
    return object.type == 'CAMERA'


class OBJECT_OT_Add_Constraint(bpy.types.Operator):
    """Add constraint based on type"""
    bl_idname = 'object.tmg_add_constraint'
    bl_label = 'Add Constraint'
    
    con : bpy.props.StringProperty(name="FLOOR")
    
    def execute(self, context):
        _add_constraint(self, context, self.con)
        return {'FINISHED'}
    
    
class OBJECT_OT_Remove_Constraint(bpy.types.Operator):
    """Remove all constraints of type"""
    bl_idname = 'object.tmg_remove_constraint'
    bl_label = 'Remove Constraint'
    
    con : bpy.props.StringProperty(name="FLOOR")
    
    def execute(self, context):
        _remove_constraint(self, context, self.con)
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
    
    
class OBJECT_OT_Move_Constraint(bpy.types.Operator):
    """Remove all constraints of type"""
    bl_idname = 'object.tmg_move_constraint'
    bl_label = 'Move Constraint'
    
    con : bpy.props.StringProperty(name="FLOOR")
    dir : bpy.props.StringProperty(name="UP")
    
    def execute(self, context):
        _move_constraint(self, context, self.con, self.dir)
        return {'FINISHED'}


class TMG_Camera_Properties(bpy.types.PropertyGroup):
    scene_camera : bpy.props.PointerProperty(name='Camera', type=bpy.types.Object, poll=_tmg_search_cameras, description='Scene active camera', update=_change_scene_camera)
    render_slot : bpy.props.IntProperty(default=1, min=1, max=8, options={'ANIMATABLE'}, update=_set_render_slot)
    
    curve_lock_scale : bpy.props.BoolProperty(default=False)
    curve_size_x : bpy.props.FloatProperty(default=1, min=0.01, update=_curve_size)
    curve_size_y : bpy.props.FloatProperty(default=1, min=0.01, update=_curve_size)
    curve_size_z : bpy.props.FloatProperty(default=1, min=0.01, update=_curve_size)
    
    res_lock : bpy.props.BoolProperty(default=False, update=_change_res_lock)
    res : bpy.props.FloatVectorProperty(default=(1920.0, 1080.0), size=2, min=4, step=15, precision=0, update=_change_resolution_presets)


    cam_sensor_format : bpy.props.EnumProperty(name='Camera Profile', default='0', description='Camera presets',
    items=[
    ('0', '24mm', ''),
    ('1', '50mm', ''),
    ('2', '80mm', ''),
    ('3', '210mm', '')], update=_change_camera_presets)
    
    cam_type : bpy.props.EnumProperty(name='Camera Perspective', default='PERSP', description='Camera perspective type',
    items=[
    ('PERSP', 'Perspective', ''),
    ('ORTHO', 'Orthographic', ''),
    ('PANO', 'Panoramic', '')], update=_set_cam_values)
    
    cam_resolution_presets : bpy.props.EnumProperty(name='Resolution Presets', default='2', description='Different render resolution presets',
    items=[
    ('0', 'VGA', ''),
    ('1', 'HD', ''),
    ('2', 'HD-F', ''),
    ('3', '2k', ''),
    ('4', '4k', ''),
    ('5', '8k', '')], update=_change_resolution_presets)
    
    cam_resolution_mode_presets : bpy.props.EnumProperty(name='Resolution Mode', default='0', description='Resolution aspect mode presets',
    items=[
    ('0', 'Landscape', ''),
    ('1', 'Portrait', ''),
    ('2', 'Box', '')], update=_change_res_mode_presets)
    

class OBJECT_PT_TMG_Camera_Panel(bpy.types.Panel):
    bl_idname = 'OBJECT_PT_tmg_camera_panel'
    bl_category = 'TMG Camera'
    bl_label = 'Camera Tools'
    bl_context = "objectmode"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'

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
            layout.use_property_decorate = False  # No animation.
            col = layout.column(align=True)
            row = col.row(align=True)
        
            row.prop(tmg_cam_vars.scene_camera.data, 'type', text='')
            row.prop(tmg_cam_vars, 'cam_sensor_format', text='')
            
            row = col.row(align=True)
            row.label(text="Focal Length")
            row.prop(tmg_cam_vars.scene_camera.data, 'sensor_fit', text='')
            
            if tmg_cam_vars.scene_camera.data.type != "ORTHO":
                row = col.row(align=True)
                row.prop(tmg_cam_vars.scene_camera.data, 'lens', text='')
            else:
                row = col.row(align=True)
                row.prop(tmg_cam_vars.scene_camera.data, 'ortho_scale', text='')

            if tmg_cam_vars.scene_camera.data.sensor_fit != "VERTICAL":
                row.prop(tmg_cam_vars.scene_camera.data, 'sensor_width', text='')
            else:
                row.prop(tmg_cam_vars.scene_camera.data, 'sensor_height', text='')
                
            row = col.row(align=True)
            row.label(text="Clip Area")
            
            row = col.row(align=True)
            row.prop(tmg_cam_vars.scene_camera.data, 'clip_start', text='')
            row.prop(tmg_cam_vars.scene_camera.data, 'clip_end', text='')
                   
             
class OBJECT_PT_TMG_Camera_Panel_DOF(bpy.types.Panel):
    bl_idname = "OBJECT_PT_tmg_camera_panel_dof"
    bl_label = "Depth of Field"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = "OBJECT_PT_tmg_camera_panel"
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
        
#            camera = tmg_cam_vars.scene_camera
#            cons = camera.constraints.items()
#            
#            if tmg_cam_vars.scene_camera.data.dof.use_dof:
#                row.prop(tmg_cam_vars.scene_camera.data.dof, 'use_dof', text='', icon="HIDE_OFF")
#            else:
#                row.prop(tmg_cam_vars.scene_camera.data.dof, 'use_dof', text='', icon="HIDE_ON")

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
            
            if tmg_cam_vars.scene_camera.data.dof.use_dof:
                row.prop(tmg_cam_vars.scene_camera.data.dof, 'use_dof', text='', icon="HIDE_OFF")
            else:
                row.prop(tmg_cam_vars.scene_camera.data.dof, 'use_dof', text='', icon="HIDE_ON")
            
            if tmg_cam_vars.scene_camera.data.dof.use_dof:
                row = col.row(align=True)
                
                row.prop(tmg_cam_vars.scene_camera.data.dof, 'focus_object', text='')
                row.prop(tmg_cam_vars.scene_camera.data.dof, 'aperture_fstop', text='')
                 
            
class OBJECT_PT_TMG_Constraints_Panel(bpy.types.Panel):
    bl_idname = 'OBJECT_PT_tmg_constraints_panel'
    bl_category = 'TMG Camera'
    bl_label = 'Constraint Tools'
    bl_context = "objectmode"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.
        
                
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
                
                props = row.operator("object.tmg_remove_constraint", text='', icon="X")
                props.con = "FLOOR"
                
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
            layout = self.layout
            layout.use_property_split = True
            layout.use_property_decorate = False  # No animation.
            col = layout.column(align=True)
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
                
#                props = row.operator("object.tmg_remove_constraint", text='', icon="X")
#                props.con = "FOLLOW_PATH"
                
                row = col.row(align=True)
                row.prop(cn, 'target', text='')
                
                row = col.row(align=True)
                
                if cn.use_fixed_location:
                    row.prop(cn, 'offset_factor', text='')
                else:
                    row.prop(cn, 'offset', text='')
                
                row.prop(cn, 'use_fixed_location', text='', icon="CON_LOCLIMIT")
                row.prop(cn, 'use_curve_radius', text='', icon="CURVE_BEZCIRCLE")
                row.prop(cn, 'use_curve_follow', text='', icon="CON_FOLLOWPATH")
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
            layout.use_property_decorate = False  # No animation.
            col = layout.column(align=True)
            row = col.row(align=True)
        
            camera = tmg_cam_vars.scene_camera
            cons = camera.constraints.items()
            
            try:
                cn = camera.constraints["Follow Path"]
                
                if tmg_cam_vars.scene_camera and tmg_cam_vars.scene_camera.type == "CAMERA":
                    camera = tmg_cam_vars.scene_camera
                    cons = camera.constraints.items()
                    
                    if tmg_cam_vars.curve_lock_scale:
                        row.prop(tmg_cam_vars, 'curve_lock_scale', text='', icon="LOCKED")
                    else:
                        row.prop(tmg_cam_vars, 'curve_lock_scale', text='', icon="UNLOCKED")
            except:
                cn = None

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
                cn = camera.constraints["Follow Path"]
                
                if tmg_cam_vars.curve_lock_scale:
                    row = col.row(align=True)
                    row.label(text="X, Y, Z")
                    row.prop(tmg_cam_vars, 'curve_size_x', text='')
                else:
                    row = col.row(align=True)
                    row.label(text='X')
                    row.prop(tmg_cam_vars, 'curve_size_x', text='')
                    
                    row = col.row(align=True)
                    row.label(text='Y')
                    row.prop(tmg_cam_vars, 'curve_size_y', text='')
                    
                    row = col.row(align=True)
                    row.label(text='Z')
                    row.prop(tmg_cam_vars, 'curve_size_z', text='')
                    
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
                
                props = row.operator("object.tmg_remove_constraint", text='', icon="X")
                props.con = "TRACK_TO"

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
    bl_label = 'Render Tools'
    bl_context = "objectmode"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'

    def draw(self, context):
        scene = context.scene
        tmg_cam_vars = scene.tmg_cam_vars
        
        if tmg_cam_vars.scene_camera and tmg_cam_vars.scene_camera.type == "CAMERA":
            layout = self.layout
            layout.use_property_split = False
            layout.use_property_decorate = False  # No animation.
            col = layout.column(align=True)
            row = col.row(align=True)


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
            layout.use_property_decorate = False  # No animation.
            col = layout.column(align=True)
            row = col.row(align=True)
                
            if tmg_cam_vars.res_lock:
                row.prop(tmg_cam_vars, 'res_lock', text='', icon="LOCKED")
                row.prop(tmg_cam_vars, 'res', text='')
            else:
                row.prop(tmg_cam_vars, 'res_lock', text='', icon="UNLOCKED")
                row.prop(scene.render, 'resolution_x', text='')
                row.prop(scene.render, 'resolution_y', text='')
            
            row = col.row(align=True)
            row.prop(tmg_cam_vars, 'cam_resolution_presets', text='')
            row.prop(tmg_cam_vars, 'cam_resolution_mode_presets', text='')
            
            row = col.row(align=True)
            row.prop(scene.render, 'resolution_percentage', text='')
        

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
            layout.use_property_split = False
            layout.use_property_decorate = False  # No animation.
            col = layout.column(align=True)
            row = col.row(align=True)
                
            row.prop(scene.render, 'engine', text='')
            row.prop(scene.render, 'filepath', text='')
            
            row = col.row(align=True)
            row.prop(scene.render.image_settings, 'file_format', text='')
            row.prop(scene.render.image_settings, 'color_mode', text='')
            
            row = col.row(align=True)
            row.prop(tmg_cam_vars, 'render_slot', text='Slot', icon="RENDERLAYERS")
            row.prop(scene, 'use_nodes', icon="NODE_COMPOSITING")
                        
            row = col.row(align=True)
            row.operator("render.render", text='Image', icon="CAMERA_DATA")
            row.operator("render.render", text='Animation', icon="RENDER_ANIMATION").animation=True






classes = (
    TMG_Camera_Properties,
    OBJECT_PT_TMG_Camera_Panel,
    OBJECT_PT_TMG_Camera_Panel_Perspective,
    OBJECT_PT_TMG_Camera_Panel_DOF,
    OBJECT_PT_TMG_Constraints_Panel,
    OBJECT_PT_TMG_Constraints_Panel_Floor,
    OBJECT_PT_TMG_Constraints_Panel_Follow_Path,
    OBJECT_PT_TMG_Constraints_Panel_Follow_Path_Spline_Scale,
    OBJECT_PT_TMG_Constraints_Panel_Track_To,
    OBJECT_PT_TMG_Render_Panel,
    OBJECT_PT_TMG_Render_Panel_Timeline,
    OBJECT_PT_TMG_Render_Panel_Aspect,
    OBJECT_PT_TMG_Render_Panel_Resolution,
    OBJECT_PT_TMG_Render_Panel_Render,
    OBJECT_OT_Add_Constraint,
    OBJECT_OT_Remove_Constraint,
    OBJECT_OT_Move_Constraint,
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
    

