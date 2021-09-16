import bpy, sys, os
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty, IntProperty, FloatProperty, PointerProperty
from bpy.types import Operator


bl_info = {
    "name": "TMG_Camera_Tools",
    "author": "Johnathan Mueller",
    "descrtion": "A panel to set camera sensor values for rendering",
    "blender": (2, 80, 0),
    "version": (0, 1, 1),
    "location": "View3D (ObjectMode) > Sidebar > TMG_Camera Tab",
    "warning": "",
    "category": "Object"
}


active_dict = {
    "type" : "PERSP", ##[ PERSP, ORTHO, PANO ]
    "fStop" : 2.0,
    "sensor_w" : 36,
    "ortho_scale" : 6,
    "focal_l" : 24,
    "use_dof" : True,
}


def select_camera():
    scene = bpy.context.scene
    tmg_cam_vars = scene.tmg_cam_vars
    
    camera = None
    bpy.ops.object.select_all(action='DESELECT')
    camera = tmg_cam_vars.scene_camera
    
    if camera:
        bpy.data.scenes["Scene"].camera = camera
        
        camera.select_set(state=True)
        bpy.context.view_layer.objects.active = camera
    
        if bpy.context.active_object.type == "CAMERA":
            active_dict['type'] = camera.data.type
            active_dict['fStop'] = camera.data.dof.aperture_fstop
            active_dict['sensor_w'] = camera.data.lens
            active_dict['ortho_scale'] = camera.data.ortho_scale
            active_dict['focal_l'] = camera.data.sensor_width
            active_dict['use_dof'] = camera.data.dof.use_dof
            
        else:
            camera.select_set(state=False)
            bpy.context.view_layer.objects.active = None
            camera = None
            tmg_cam_vars.scene_camera = None
    
    ob = camera
    return ob
    return{'FINISHED'}


def _change_camera_presets(self, context):
    scene = context.scene
    tmg_cam_vars = scene.tmg_cam_vars
    
    if tmg_cam_vars.cam_sensor_format == '0':
        active_dict["fStop"] = 2.0
        active_dict["ortho_scale"] = 10
        active_dict["focal_l"] = 24
        active_dict["sensor_w"] = 36
        
    if tmg_cam_vars.cam_sensor_format == '1':
        active_dict["fStop"] = 2.0
        active_dict["ortho_scale"] = 5
        active_dict["focal_l"] = 50
        active_dict["sensor_w"] = 36
        
    if tmg_cam_vars.cam_sensor_format == '2':
        active_dict["fStop"] = 2.8
        active_dict["ortho_scale"] = 2.8
        active_dict["focal_l"] = 80
        active_dict["sensor_w"] = 36
        
    if tmg_cam_vars.cam_sensor_format == '3':
        active_dict["fStop"] = 2.8
        active_dict["ortho_scale"] = 1
        active_dict["focal_l"] = 210
        active_dict["sensor_w"] = 36
    
    _set_cam_values(self, context)
    
    
def _change_scene_camera(self, context):
    scene = context.scene
    tmg_cam_vars = scene.tmg_cam_vars

    camera = select_camera()

    if camera and camera.type == "CAMERA":
        
        active_dict['type'] = camera.data.type
        active_dict['fStop'] = camera.data.dof.aperture_fstop
        active_dict['sensor_w'] = camera.data.lens
        active_dict['ortho_scale'] = camera.data.ortho_scale
        active_dict['focal_l'] = camera.data.sensor_width
        active_dict['use_dof'] = camera.data.dof.use_dof
        
        context.object.data.type = active_dict['type']
        context.object.data.lens = active_dict['focal_l']
        context.object.data.ortho_scale = active_dict['ortho_scale']
                
        context.object.data.sensor_width = active_dict['sensor_w']
        context.object.data.dof.aperture_fstop = active_dict['fStop']
        context.object.data.dof.use_dof = active_dict['use_dof']
        context.space_data.lock_camera


def _set_cam_values(self, context):
    scene = context.scene
    tmg_cam_vars = scene.tmg_cam_vars
  
    camera = tmg_cam_vars.scene_camera
    print("Camera: ", camera.data.name)
    
    if camera:
        context.object.data.type = active_dict['type']
        context.object.data.lens = active_dict['focal_l']
        context.object.data.ortho_scale = active_dict['ortho_scale']
                
        context.object.data.sensor_width = active_dict['sensor_w']
        context.object.data.dof.aperture_fstop = active_dict['fStop']
        context.object.data.dof.use_dof = active_dict['use_dof']
        context.space_data.lock_camera
        
        

class TMG_Camera_Properties(bpy.types.PropertyGroup):
    
    scene_camera : bpy.props.PointerProperty(name='Camera', type=bpy.types.Object, description='Scene active camera', update=_change_scene_camera)
    
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
            
        if tmg_cam_vars.scene_camera:
            row = col.row(align=True)
            row.prop(context.object.data, 'type', text='')
            row.prop(tmg_cam_vars, 'cam_sensor_format', text='')
            
            if context.object.data.type != "ORTHO":
                row = col.row(align=True)
                row.label(text="Focal Length")
                row.prop(context.object.data, 'lens', text='')
            else:
                row = col.row(align=True)
                row.label(text="Focal Length")
                row.prop(context.object.data, 'ortho_scale', text='')

            row = col.row(align=True)
            row.label(text="Sensor Size")
            row.prop(context.object.data, 'sensor_width', text='')

            row = col.row(align=True)
            row.label(text="F-Stop")
            row.prop(context.object.data.dof, 'aperture_fstop', text='')
            
            row = col.row(align=True)
            row.label(text="Use DOF")
            row.prop(context.object.data.dof, 'use_dof', text='')
            
            row = col.row(align=True)
            row.label(text="Camera View Lock")
            row.prop(context.space_data, 'lock_camera', text='')
        

classes = (
    TMG_Camera_Properties,
    OBJECT_PT_TMG_Camera_Panel,
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
    

