import bpy, sys, os
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty, IntProperty, FloatProperty, PointerProperty
from bpy.types import Operator


bl_info = {
    "name": "TMG_Camera_Tools",
    "author": "Johnathan Mueller",
    "descrtion": "A panel to set camera sensor values for rendering",
    "blender": (2, 80, 0),
    "version": (0, 1, 7),
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
    
    
def _change_scene_camera(self, context):
    scene = context.scene
    tmg_cam_vars = scene.tmg_cam_vars

    camera = tmg_cam_vars.scene_camera

    if camera and camera.type == "CAMERA":
        scene.camera = camera
        
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
        
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = camera
        camera.select_set(True)  
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
    
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = camera
    camera.select_set(True)   
    
    for name, con in camera.constraints.items():
        if con.type == _con:
            mod = camera.constraints.get(con.name)
            print(mod)
            if _dir == "UP":
                bpy.ops.constraint.move_up(constraint=con.name, owner="OBJECT")
            else:
                bpy.ops.constraint.move_down(constraint=con.name, owner="OBJECT")
            
    
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
    render_slot : bpy.props.IntProperty(default=1, min=1, max=8, update=_set_render_slot)
    
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
        col = layout.column(align=True)
        row = col.row(align=True)
        
        row.prop(tmg_cam_vars, 'scene_camera', text='')
        
        if tmg_cam_vars.scene_camera or context.space_data.lock_camera:
            row.operator("object.tmg_select_camera", text='', icon="RESTRICT_SELECT_ON")
            row.prop(context.space_data, 'lock_camera', text='', icon="LOCKVIEW_ON")
        else:
            row.label(text='', icon="RESTRICT_SELECT_ON")
            row.label(text='', icon="LOCKVIEW_OFF")
            
        if tmg_cam_vars.scene_camera and tmg_cam_vars.scene_camera.type == "CAMERA":
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
#    bl_options = {'HIDE_HEADER'}

    def draw_header(self, context):
        scene = context.scene
        tmg_cam_vars = scene.tmg_cam_vars
        
        layout = self.layout
        col = layout.column(align=True)
        row = col.row(align=True)
        
        if tmg_cam_vars.scene_camera and tmg_cam_vars.scene_camera.type == "CAMERA":
            camera = tmg_cam_vars.scene_camera
            cons = camera.constraints.items()
            
            if tmg_cam_vars.scene_camera.data.dof.use_dof:
                row.prop(tmg_cam_vars.scene_camera.data.dof, 'use_dof', text='', icon="HIDE_OFF")
            else:
                row.prop(tmg_cam_vars.scene_camera.data.dof, 'use_dof', text='', icon="HIDE_ON")

    def draw(self, context):
        scene = context.scene
        tmg_cam_vars = scene.tmg_cam_vars
        
        layout = self.layout
        col = layout.column(align=True)
        row = col.row(align=True)
        
        if tmg_cam_vars.scene_camera and tmg_cam_vars.scene_camera.type == "CAMERA":
            camera = tmg_cam_vars.scene_camera
            cons = camera.constraints.items()
            
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
        
                
class OBJECT_PT_TMG_Constraints_Panel_Floor(bpy.types.Panel):
    bl_idname = "SUB_PT_Gensett"
    bl_label = "Floor"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = "OBJECT_PT_tmg_constraints_panel"
    bl_options = {"DEFAULT_CLOSED"}
#    bl_options = {'HIDE_HEADER'}

    def draw(self, context):
        scene = context.scene
        tmg_cam_vars = scene.tmg_cam_vars
        
        layout = self.layout
        col = layout.column(align=True)
        row = col.row(align=True)
        
        if tmg_cam_vars.scene_camera and tmg_cam_vars.scene_camera.type == "CAMERA":
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
                props = row.operator("object.tmg_add_constraint", text='', icon="CON_FLOOR")
                props.con = "FLOOR"
                             
                             
class OBJECT_PT_TMG_Constraints_Panel_Follow_Path(bpy.types.Panel):
    bl_idname = "OBJECT_PT_tmg_constraints_panel_follow_path"
    bl_label = "Follow Path"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = "OBJECT_PT_tmg_constraints_panel"
    bl_options = {"DEFAULT_CLOSED"}
#    bl_options = {'HIDE_HEADER'}

    def draw(self, context):
        scene = context.scene
        tmg_cam_vars = scene.tmg_cam_vars
        
        layout = self.layout
        col = layout.column(align=True)
        row = col.row(align=True)
        
        if tmg_cam_vars.scene_camera and tmg_cam_vars.scene_camera.type == "CAMERA":
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
                
                props = row.operator("object.tmg_remove_constraint", text='', icon="X")
                props.con = "FOLLOW_PATH"
                
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
                props = row.operator("object.tmg_add_constraint", text='', icon="CON_FOLLOWPATH")
                props.con = "FOLLOW_PATH"
                
                
class OBJECT_PT_TMG_Constraints_Panel_Track_To(bpy.types.Panel):
    bl_idname = "OBJECT_PT_tmg_constraints_panel_track_to"
    bl_label = "Track To"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = "OBJECT_PT_tmg_constraints_panel"
    bl_options = {"DEFAULT_CLOSED"}
#    bl_options = {'HIDE_HEADER'}

    def draw(self, context):
        scene = context.scene
        tmg_cam_vars = scene.tmg_cam_vars
        
        layout = self.layout
        col = layout.column(align=True)
        row = col.row(align=True)
        
        if tmg_cam_vars.scene_camera and tmg_cam_vars.scene_camera.type == "CAMERA":
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
                props = row.operator("object.tmg_add_constraint", text='', icon="CON_TRACKTO")
                props.con = "TRACK_TO"
                
            
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
        
        layout = self.layout
        col = layout.column(align=True)
        row = col.row(align=True)
            
        if tmg_cam_vars.scene_camera and tmg_cam_vars.scene_camera.type == "CAMERA":
            
            row = col.row(align=True)
            row.label(text="Timeline")
            row = col.row(align=True)
            row.prop(scene, 'use_preview_range', text='')
            row.prop(scene, 'frame_start', text='')
            row.prop(scene, 'frame_end', text='')
            
            row = col.row(align=True)
            row.label(text="Resolution")
            row = col.row(align=True)
            row.prop(scene.render, 'resolution_x', text='')
            row.prop(scene.render, 'resolution_y', text='')
            
            row = col.row(align=True)
            row.prop(scene.render, 'resolution_percentage', text='')
            
            row = col.row(align=True)
            row.label(text="Aspect")
            row = col.row(align=True)
            row.prop(scene.render, 'pixel_aspect_x', text='')
            row.prop(scene.render, 'pixel_aspect_y', text='')
            
            row = col.row(align=True)
            row.label(text="Render")
            
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
    OBJECT_PT_TMG_Camera_Panel_DOF,
    OBJECT_PT_TMG_Constraints_Panel,
    OBJECT_PT_TMG_Constraints_Panel_Floor,
    OBJECT_PT_TMG_Constraints_Panel_Follow_Path,
    OBJECT_PT_TMG_Constraints_Panel_Track_To,
    OBJECT_PT_TMG_Render_Panel,
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
    

