import bpy, sys, os
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty, IntProperty, FloatProperty, PointerProperty
from bpy.types import Operator


bl_info = {
    "name": "TMG_Camera_Tools",
    "author": "Johnathan Mueller",
    "descrtion": "A panel to set camera sensor values for rendering",
    "blender": (2, 80, 0),
    "version": (0, 1, 6),
    "location": "View3D (ObjectMode) > Sidebar > TMG_Camera Tab",
    "warning": "",
    "category": "Object"
}


active_dict = {
    "type" : "PERSP", ##[ PERSP, ORTHO, PANO ]
    "fStop" : 2.0,
    "sensor_w" : 36,
    "focal_l" : 24,
    "use_dof" : True,
}


def select_camera():
    scene = bpy.context.scene
    tmg_cam_vars = scene.tmg_cam_vars
    
    camera = None
    bpy.ops.object.select_all(action='DESELECT')
    camera = tmg_cam_vars.scene_camera
    
    print(tmg_cam_vars.scene_camera)
    
    if camera:
        bpy.data.scenes["Scene"].camera = camera
        
        camera.select_set(state=True)
        bpy.context.view_layer.objects.active = camera
    
        if bpy.context.active_object.type == "CAMERA":
            active_dict['type'] = camera.data.type
            active_dict['fStop'] = camera.data.dof.aperture_fstop
            active_dict['sensor_w'] = camera.data.lens
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


def pre_set_type(ob, dict):
    ob.data.type = dict["type"]
    return{'FINISHED'}


def pre_set_sensor(ob, dict):
    ob.data.sensor_width = dict["sensor_w"]
    return{'FINISHED'}


def pre_set_depth(ob, dict):
    ob.data.lens = dict["focal_l"]
    return{'FINISHED'}


def pre_set_dof(ob, dict):
    ob.data.dof.aperture_fstop = dict["fStop"]
    return{'FINISHED'}


def main():
    print("\nStart")
    camera = select_camera()
    print("Camera: ", camera.data.name)
    
    if camera:
        pre_set_type(camera, active_dict)
        pre_set_sensor(camera, active_dict)
        pre_set_depth(camera, active_dict)
        pre_set_dof(camera, active_dict)
    
    print("\nFinished")
    return{'FINISHED'}


def _change_camera_presets(self, context):
    scene = context.scene
    tmg_cam_vars = scene.tmg_cam_vars
    
#    active_dict["type"] = "PERSP"
#    active_dict["use_dof"] = True
    
    if tmg_cam_vars.cam_sensor_format == '0':
        active_dict["fStop"] = 2.0
        active_dict["focal_l"] = 24
        active_dict["sensor_w"] = 36
        
    if tmg_cam_vars.cam_sensor_format == '1':
        active_dict["fStop"] = 2.0
        active_dict["focal_l"] = 50
        active_dict["sensor_w"] = 36
        
    if tmg_cam_vars.cam_sensor_format == '2':
        active_dict["fStop"] = 2.8
        active_dict["focal_l"] = 80
        active_dict["sensor_w"] = 36
        
    if tmg_cam_vars.cam_sensor_format == '3':
        active_dict["fStop"] = 2.8
        active_dict["focal_l"] = 210
        active_dict["sensor_w"] = 36
    
#    tmg_cam_vars.cam_type = active_dict["type"]
    tmg_cam_vars.cam_fstop = active_dict["fStop"]
    tmg_cam_vars.cam_flength = active_dict["focal_l"]
    tmg_cam_vars.cam_ssize = active_dict["sensor_w"]
#    tmg_cam_vars.cam_use_dof = active_dict["use_dof"]
    
    bpy.context.space_data.lock_camera = tmg_cam_vars.cam_to_view
    
    _set_cam_values(self, context)
        
#    main()
    
    
def _change_scene_camera(self, context):
    scene = context.scene
    tmg_cam_vars = scene.tmg_cam_vars
    
#    camera = tmg_cam_vars.scene_camera

    camera = select_camera()

    if camera and camera.type == "CAMERA":
        
        active_dict['type'] = camera.data.type
        active_dict['fStop'] = camera.data.dof.aperture_fstop
        active_dict['sensor_w'] = camera.data.lens
        active_dict['focal_l'] = camera.data.sensor_width
        active_dict['use_dof'] = camera.data.dof.use_dof
        
    #    bpy.data.scenes["Scene"].camera = camera

        
        tmg_cam_vars.cam_type    = active_dict['type']
        tmg_cam_vars.cam_fstop   = active_dict['fStop']
        tmg_cam_vars.cam_flength = active_dict['sensor_w']
        tmg_cam_vars.cam_ssize   = active_dict['focal_l']
        tmg_cam_vars.cam_use_dof = active_dict['use_dof']
    


def _set_cam_values(self, context):
    scene = context.scene
    tmg_cam_vars = scene.tmg_cam_vars
  
    camera = tmg_cam_vars.scene_camera
    print("Camera: ", camera.data.name)
    
    if camera:
        active_dict["type"] = "PERSP"
        
        ## DOF
#        print(tmg_cam_vars.cam_type)
        camera.data.type = tmg_cam_vars.cam_type
        camera.data.dof.aperture_fstop = tmg_cam_vars.cam_fstop
        camera.data.lens = tmg_cam_vars.cam_flength
        camera.data.sensor_width = tmg_cam_vars.cam_ssize
        camera.data.dof.use_dof = tmg_cam_vars.cam_use_dof
        
        if bpy.context.space_data.type == 'VIEW_3D':
            bpy.context.space_data.lock_camera = tmg_cam_vars.cam_to_view
        
#        active_dict["sensor_w"] = 36
#        active_dict["focal_l"] = 24
        
        

class TMG_Camera_Properties(bpy.types.PropertyGroup):
    
    scene_camera : bpy.props.PointerProperty(name='Camera', type=bpy.types.Object, description='Scene active camera', update=_change_scene_camera)
    
    cam_sensor_format : bpy.props.EnumProperty(name='Camera Profile', default='0', description='Camera presets',
    items=[
    ('0', '24mm', ''),
    ('1', '50mm', ''),
    ('2', '80mm', ''),
    ('3', '210mm', '')], update=_change_camera_presets)
    
#    active_dict : bpy.props.StringProperty(name='mm80', description='Selected camera profile')

    
    ## Default FBX Export Options
#    exp_directory : bpy.props.StringProperty(name='Directory', description='Sets the folder directory path for the FBX models to export to')
#    exp_use_selection : bpy.props.BoolProperty(default=True, description='If you want to export only selected or everything in your blend file (Might not work correctly)')
#    exp_uvs_start_int : bpy.props.IntProperty(name='UV Start Index', default=1, min=0, soft_max=1, step=1, description='Integer value placed at the end of UV layer names')
    
    cam_type : bpy.props.EnumProperty(name='Camera Perspective', default='PERSP', description='Camera perspective type',
    items=[
    ('PERSP', 'Perspective', ''),
    ('ORTHO', 'Orthographic', ''),
    ('PANO', 'Panoramic', '')], update=_set_cam_values)
    
    cam_use_dof : bpy.props.BoolProperty(default=True, description='Use depth of field', update=_set_cam_values)
    cam_fstop : bpy.props.FloatProperty(name='F-Stop', default=2.0, soft_min=1.0, soft_max=50.0, step=1, precision=1, description='Camera aperture ratio', update=_set_cam_values)
    cam_flength : bpy.props.FloatProperty(name='Focal Length', default=24, soft_min=1, soft_max=300, step=1, precision=1, description='Camera focal length', update=_set_cam_values)
    cam_ssize : bpy.props.FloatProperty(name='Sensor Size', default=36, soft_min=1, soft_max=300, step=1, precision=1, description='Camera sensor size', update=_set_cam_values)

    cam_to_view : bpy.props.BoolProperty(default=False, description='Lock camera to view', update=_set_cam_values)


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
            row.prop(tmg_cam_vars, 'cam_type', text='')
            row.prop(tmg_cam_vars, 'cam_sensor_format', text='')
            
            row = col.row(align=True)
            row.label(text="Focal Length")
            row.prop(tmg_cam_vars, 'cam_flength', text='')
            
            row = col.row(align=True)
            row.label(text="Sensor Size")
            row.prop(tmg_cam_vars, 'cam_ssize', text='')
            
            row = col.row(align=True)
            row.label(text="F-Stop")
            row.prop(tmg_cam_vars, 'cam_fstop', text='')
            
            row = col.row(align=True)
            row.label(text="Use DOF")
            row.prop(tmg_cam_vars, 'cam_use_dof', text='')
            
            row = col.row(align=True)
            row.label(text="Camera To View")
            row.prop(tmg_cam_vars, 'cam_to_view', text='')
        

classes = (
    TMG_Camera_Properties,
    OBJECT_PT_TMG_Camera_Panel,
)


def register():
    for rsclass in classes:
        bpy.utils.register_class(rsclass)
        bpy.types.Scene.tmg_cam_vars = bpy.props.PointerProperty(type=TMG_Camera_Properties)
        bpy.context.scene.tmg_cam_vars.scene_camera = bpy.data.scenes["Scene"].camera


def unregister():
    for rsclass in classes:
        bpy.utils.unregister_class(rsclass)
#        del bpy.types.Object.theChosenObject


if __name__ == "__main__":
    register()
    

