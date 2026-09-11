"""Selected BPU workload; the camera stays alive across mode changes."""
import os
from pathlib import Path
from launch import LaunchDescription
from launch.actions import ExecuteProcess, RegisterEventHandler, EmitEvent
from launch.event_handlers import OnProcessExit
from launch.events import Shutdown
from launch_ros.actions import Node

ROOT = Path(__file__).resolve().parents[1]
PREFIX = Path('/opt/tros/humble')

def generate_launch_description():
    mode=os.environ['RDK_MODE']
    nodes=[]
    if mode=='yolo':
        nodes.append(ExecuteProcess(cmd=['/usr/bin/python3',str(ROOT/'scripts/run.py'),
            '--source','framefile:/run/rdk-vision/left.jpg','--port','8081','--keep-camera-settings'],cwd=str(ROOT),output='screen'))
    elif mode=='stereo':
        nodes.append(Node(package='hobot_stereonet',executable='stereonet_model_node',name='StereoNetNode',
            parameters=[{'stereonet_model_file_path':str(PREFIX/'share/hobot_stereonet/config/DStereoV2.4_int16_640_480.bin'),
                'stereo_image_topic':'/sub_image_combine_raw',
                'camera_info_topic':'/sub_image_combine_raw/right/camera_info',
                'left_camera_info_topic':'/sub_image_combine_raw/left/camera_info',
                'render_type':'outdoor',
                'save_result_flag':False,'publish_pcd_enabled':False,'publish_visual_enabled':False,'render_perf':False}],
            arguments=['--ros-args','--log-level','warn'],output='screen'))
    elif mode=='body':
        nodes.append(Node(package='mono2d_body_detection',executable='mono2d_body_detection',
            cwd=str(ROOT/'output/body'),parameters=[{'is_shared_mem_sub':0,'model_type':0,'ros_img_topic_name':'/rdk/image_raw',
            'model_file_name':str(PREFIX/'lib/mono2d_body_detection/config/multitask_body_head_face_hand_kps_960x544.hbm')}],
            arguments=['--ros-args','--log-level','error'],output='screen'))
        nodes.append(Node(package='face_age_detection',executable='face_age_detection',
            parameters=[{'is_shared_mem_sub':0,'model_file_name':str(PREFIX/'share/face_age_detection/config/faceAge.hbm'),
                         'ai_msg_pub_topic_name':'/hobot_face_age_detection','max_slide_window_size':15}],
            remappings=[('/image_raw','/rdk/image_raw')],arguments=['--ros-args','--log-level','error'],output='screen'))
    handlers=[RegisterEventHandler(OnProcessExit(target_action=n,on_exit=[EmitEvent(event=Shutdown(reason="workload exited"))])) for n in nodes]
    return LaunchDescription(nodes+handlers)
