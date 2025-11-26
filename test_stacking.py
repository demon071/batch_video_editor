import sys
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.append(os.getcwd())

from core.ffmpeg_builder_python import FFmpegPythonBuilder
from models.video_task import VideoTask
from models.enums import VideoCodec

def test_stacking_command_generation():
    print("Testing Stacking Command Generation...")
    
    # Mock task
    task = VideoTask(
        input_path=Path("input.mp4"),
        output_path=Path("output.mp4"),
        codec=VideoCodec.H264
    )
    task.duration = 10.0
    task.original_resolution = (1920, 1080)
    
    # 1. Test HStack with Single File (Refined)
    print("\n--- Test 1: HStack with Single File (Refined) ---")
    task.stack_settings = {
        'mode': 'hstack',
        'type': 'file',
        'path': Path("secondary.mp4")
    }
    
    # Mock secondary file existence
    with open("input.mp4", "w") as f: f.write("dummy")
    with open("secondary.mp4", "w") as f: f.write("dummy")
    
    try:
        cmd = FFmpegPythonBuilder.build_command(task)
        cmd_str = " ".join(cmd)
        print(cmd_str)
        
        if 'hstack' not in cmd_str:
            print("FAILED: hstack filter not found")
        else:
            print("PASSED: hstack filter found")
            
        if 'stream_loop -1' not in cmd_str:
             print("FAILED: stream_loop -1 not found for file mode")
        else:
             print("PASSED: stream_loop -1 found")
             
        if 'shortest=1' in cmd_str:
             print("FAILED: shortest=1 found (should be removed)")
        else:
             print("PASSED: shortest=1 removed")
             
        if '-t 10.0' not in cmd_str:
             print("FAILED: -t 10.0 not found (duration constraint missing)")
        else:
             print("PASSED: -t 10.0 found")
             
        if 'amix' in cmd_str:
             print("FAILED: amix found (audio should not be mixed)")
        else:
             print("PASSED: amix not found (audio correct)")
             
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

    # 2. Test VStack with Random Folder (Refined)
    print("\n--- Test 2: VStack with Random Folder (Refined) ---")
    task.stack_settings = {
        'mode': 'vstack',
        'type': 'folder',
        'path': Path("stack_folder")
    }
    
    # Create dummy folder and file
    os.makedirs("stack_folder", exist_ok=True)
    with open("stack_folder/random1.mp4", "w") as f: f.write("dummy")
    with open("stack_folder/random2.mp4", "w") as f: f.write("dummy")
    
    # Patch get_video_info
    with patch('utils.system_check.get_video_info') as mock_info:
        # Return duration 5.0, so we need 2 files to reach 10.0
        mock_info.return_value = {'duration': 5.0, 'width': 1920, 'height': 1080}
        
        try:
            cmd = FFmpegPythonBuilder.build_command(task)
            cmd_str = " ".join(cmd)
            print(cmd_str)
            
            if 'vstack' not in cmd_str:
                print("FAILED: vstack filter not found")
            else:
                print("PASSED: vstack filter found")
                
            if 'concat' in cmd_str:
                 print("PASSED: concat filter found (multiple files used)")
            else:
                 print("CHECK: concat might not be used if 1 file was enough")
                 
            if '-t 10.0' not in cmd_str:
                 print("FAILED: -t 10.0 not found in vstack test")
            else:
                 print("PASSED: -t 10.0 found in vstack test")
                 
        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()
        
    # Cleanup
    try:
        os.remove("input.mp4")
        os.remove("secondary.mp4")
        import shutil
        shutil.rmtree("stack_folder")
    except:
        pass

if __name__ == "__main__":
    test_stacking_command_generation()
