import os, sys, bpy

current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)
from anigenblenderutils.RenameAction import RenameAction
from anigenblenderutils.FindAndImport import FindAndImport
from anigenblenderutils.BlendMotion import BlendMotion
from anigenblenderutils.AdjustFrames import AdjustFrames
from anigenblenderutils.MakeInvisible import MakeInvisible
from anigenblenderutils.Render import AnimationRenderer as Render
from anigenblenderutils.ExportFBX import FBXExporter as Exporter

import config as Config

def main():
    # TODO: Make this dynamically take input from external sources
    # motions = [
    #     "male_strut_walk",
    #     "running_with_intention",
    #     "dodging_to_the_right_place",
    #     "hook_punch",
    #     "covering_face_in_shame_after_defeat",
    # ]

    # Import the blender file and the fbx files
    import_path = Config.IMPORT_PATH
    motions = Config.MOTIONS
    fbx_files = [f"{motion}.fbx" for motion in motions]
    find_and_import = FindAndImport(import_path, fbx_files)
    find_and_import.run()

    # Rename the actions and blend the motions for each of the motions
    for motion in motions:
        rename_action = RenameAction(motion)
        rename_action.run()
    for motion in motions:
        blend_motion = BlendMotion("idle", motion)
        blend_motion.run()

    # Fix the strips timings for all the NLA tracks
    adjust_frames = AdjustFrames("idle", offset=10)
    adjust_frames.fix_strips_timings()

    # Make the armature objects invisible in the outliner
    make_invisible = MakeInvisible()
    make_invisible.run()
    # Render the animation
    # TODO: Change the path to a dynamic one
    render_path = Config.RENDER_PATH
    renderer = Render(
        render_path,
        "FFMPEG",
        1,
        Config.TOTAL_FRAMES,
    )
    renderer.run()
    # Export the armature as FBX
    export_fbx = Exporter(
        "idle", render_path + '\\', "idle.fbx"
    )
    export_fbx.run()
    # Saving the main file (not needed for now)
    # bpy.ops.wm.save_mainfile(
    #     filepath="C:\\Users\\User\\Desktop\\FYP\\blender-utils\\Xbot2.blend"
    # )


if __name__ == "__main__":
    main()
