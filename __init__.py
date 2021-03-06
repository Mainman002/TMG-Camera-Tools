import bpy, sys, os

from . TMG_Camera_Panel import *

from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty, IntProperty, FloatProperty, FloatVectorProperty, PointerProperty
from bpy.types import Operator, Header
from bpy_extras.node_utils import find_node_input
from bl_ui.utils import PresetPanel


# GNU GENERAL PUBLIC LICENSE
# Version 3, 29 June 2007

# Extra online resources used in this script
# https://blender.stackexchange.com/questions/155515/how-do-a-create-a-foldout-ui-panel

# Thank you Curtis Holt for the random light color code snippets
# That's changed my workflow in weird, fun ways :)
# His video found here -> https://youtu.be/YyxirS699Zs

# Thank you all that download, suggest, and request features
# As well as the whole Blender community. You're all epic :)


bl_info = {
    "name": "TMG_Cam_Tools",
    "author": "Johnathan Mueller",
    "descrtion": "A panel to set camera sensor values for rendering",
    "blender": (2, 80, 0),
    "version": (0, 2, 9),
    "location": "View3D (ObjectMode) > Sidebar > TMG > Camera Tab",
    "warning": "",
    "category": "Object"
}

classes = (
    ## Properties
    TMG_Cam_Properties,

    ## Camera Operators
    OBJECT_PT_TMG_Cam_RenameOB,
    OBJECT_PT_TMG_Cam_SelectOB,
    OBJECT_PT_TMG_Cam_DeleteOB,
    
    ## Camera Panel
    OBJECT_PT_TMG_Cam_Parent_Panel, 
    OBJECT_PT_TMG_Cam_Panel, 
    OBJECT_PT_TMG_Cam_Panel_List,
    OBJECT_PT_TMG_Cam_Panel_Name, 
    OBJECT_PT_TMG_Cam_Panel_Perspective, 
    
    ## Constraints Panel
    OBJECT_PT_TMG_Cam_Constraints_Panel, 
    OBJECT_PT_TMG_Cam_Constraints_Panel_Floor, 
    OBJECT_PT_TMG_Cam_Constraints_Panel_Follow_Path, 
    OBJECT_PT_TMG_Cam_Constraints_Panel_Follow_Path_Spline_Scale, 
    OBJECT_PT_TMG_Cam_Constraints_Panel_Track_To, 
    
    ## Output Panel
    OBJECT_PT_TMG_Cam_Output_Panel,
    OBJECT_PT_TMG_Cam_Output_Panel_Image, 
    OBJECT_PT_TMG_Cam_Output_Panel_Image_Settings,
    
    ## Passes Panel
    OBJECT_PT_TMG_Cam_Passes_Panel, 
    OBJECT_PT_TMG_Cam_Passes_Panel_Cryptomatte, 
    OBJECT_PT_TMG_Cam_Passes_Panel_Data, 
    OBJECT_PT_TMG_Cam_Passes_Panel_Effects, 
    OBJECT_PT_TMG_Cam_Passes_Panel_Filter,
    OBJECT_PT_TMG_Cam_Passes_Panel_Light, 
    OBJECT_PT_TMG_Cam_Passes_Panel_Shader_AOV, 
    
    ## Render Panel
    OBJECT_PT_TMG_Cam_Render_Panel,
    OBJECT_PT_TMG_Cam_Render_Panel_Aspect, 
    OBJECT_PT_TMG_Cam_Render_Panel_Device,
    OBJECT_PT_TMG_Cam_Render_Panel_Film, 

    OBJECT_PT_TMG_Cam_Render_Panel_Performance,
    OBJECT_PT_TMG_Cam_Render_Panel_Performance_Acc_Structure,
    OBJECT_PT_TMG_Cam_Render_Panel_Performance_Final_Render,
    OBJECT_PT_TMG_Cam_Render_Panel_Performance_Tiles,
    OBJECT_PT_TMG_Cam_Render_Panel_Performance_Threads,
    OBJECT_PT_TMG_Cam_Render_Panel_Performance_Viewport,

    OBJECT_PT_TMG_Cam_Render_Panel_Resolution, 
    OBJECT_PT_TMG_Cam_Render_Panel_Sampling, 
    OBJECT_PT_TMG_Cam_Render_Panel_Sampling_Advanced,
    OBJECT_PT_TMG_Cam_Render_Panel_Sampling_Denoising,
    OBJECT_PT_TMG_Cam_Render_Panel_S_Denoising_Render,
    OBJECT_PT_TMG_Cam_Render_Panel_S_Denoising_Viewport,
    OBJECT_PT_TMG_Cam_Render_Panel_Sampling_Samples, 
    OBJECT_PT_TMG_Cam_Render_Panel_Cycles_Sampling_Samples, 
    OBJECT_PT_TMG_Cam_Render_Panel_Cycles_Sampling_Samples_Render,
    OBJECT_PT_TMG_Cam_Render_Panel_Cycles_Sampling_Samples_Viewport,
    OBJECT_PT_TMG_Cam_Render_Panel_Timeline, 
    
    ## Scene Effects Panel
    OBJECT_PT_TMG_Cam_Scene_Effects_Panel, 
    OBJECT_PT_TMG_Cam_Scene_Effects_Panel_AO, 
    OBJECT_PT_TMG_Cam_Scene_Effects_Panel_Bloom, 
    OBJECT_PT_TMG_Cam_Scene_Effects_Panel_Color_M,
    OBJECT_PT_TMG_Cam_Scene_Effects_Panel_Color_M_Use_Curves,

    OBJECT_PT_TMG_Cam_Scene_Effects_Panel_Depth_Of_Field, 
    OBJECT_PT_TMG_Cam_Scene_Effects_Panel_Depth_Of_Field_Aperture, 
    OBJECT_PT_TMG_Cam_Scene_Effects_Panel_Depth_Of_Field_Bokeh, 
    OBJECT_PT_TMG_Cam_Scene_Effects_Panel_Motion_Blur, 
    OBJECT_PT_TMG_Cam_Scene_Effects_Panel_Post_Processing,
    OBJECT_PT_TMG_Cam_Scene_Effects_Panel_Screen_Space_Reflections, 
    OBJECT_PT_TMG_Cam_Scene_Effects_Panel_Shadows, 
    OBJECT_PT_TMG_Cam_Scene_Effects_Panel_Stereoscopy, 
    OBJECT_PT_TMG_Cam_Scene_Effects_Panel_Subsurface_Scattering, 
    OBJECT_PT_TMG_Cam_Scene_Effects_Panel_Volumetrics_Cycles,
    OBJECT_PT_TMG_Cam_Scene_Effects_Panel_Vol_Eevee, 
    OBJECT_PT_TMG_Cam_Scene_Effects_Panel_Vol_Eevee_Lighting,
    # OBJECT_PT_TMG_Cam_Scene_Effects_Panel_Volumetrics_Samples,
    OBJECT_PT_TMG_Cam_Scene_Effects_Panel_Volumetrics_Eevee_Shadows,

    ## Selected Object Panel
    OBJECT_PT_TMG_Cam_Selected_Object_Panel,
    OBJECT_PT_TMG_Cam_S_OB_Name,

    ## Eevee 
    OBJECT_PT_TMG_Cam_EEVEE_Light,
    OBJECT_PT_TMG_Cam_EEVEE_Light_Distance,
    OBJECT_PT_TMG_Cam_EEVEE_Light_Beam_Shape,

    ## Cycles
    OBJECT_PT_TMG_Cam_CYCLES_Light,
    OBJECT_PT_TMG_Cam_CYCLES_Light_Beam_Shape,
    
    ## Randomize Selected Lights
    OBJECT_PT_TMG_Cam_Light_Randomize,
    OBJECT_PT_TMG_Cam_Light_Randomize_Options,

    ## Viewport Panel
    OBJECT_PT_TMG_Cam_Viewport_Panel, 
    OBJECT_PT_TMG_Cam_Viewport_Panel_Composition, 
    OBJECT_PT_TMG_Cam_Viewport_Panel_Display, 
    OBJECT_PT_TMG_Cam_Viewport_Panel_User_Preferences,
    OBJECT_PT_TMG_Cam_Viewport_Panel_View, 
    
    ## Extra Operators
    OBJECT_OT_TMG_Cam_Add_Constraint, 
    OBJECT_OT_TMG_Cam_Move_Constraint, 
    OBJECT_OT_TMG_Cam_Randomize_Selected_Light,
    OBJECT_OT_TMG_Cam_Remove_Constraint,
    OBJECT_OT_TMG_Cam_Select_Camera,
    # OBJECT_OT_TMG_Cam_Select_Object,
)

def register():
    for rsclass in classes:
        bpy.utils.register_class(rsclass)
        bpy.types.Scene.tmg_cam_vars = bpy.props.PointerProperty(type=TMG_Cam_Properties)

def unregister():
    for rsclass in classes:
        bpy.utils.unregister_class(rsclass)

if __name__ == "__main__":
    register()

