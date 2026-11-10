import os
import tempfile

from launch import LaunchDescription
from launch.actions import ExecuteProcess, TimerAction
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():

    pkg_dir = get_package_share_directory('robot_description')

    xacro_file = os.path.join(
        pkg_dir, 'urdf', 'differential_robot.urdf.xacro'
    )

    world_file = os.path.join(
        pkg_dir, 'worlds', 'robot_world.sdf'
    )

    urdf_file = os.path.join(
        tempfile.gettempdir(), 'differential_robot.urdf'
    )

    # Generate URDF from Xacro before spawning
    os.system(f'xacro "{xacro_file}" -o "{urdf_file}"')

    with open(urdf_file, 'r') as file:
        robot_description = file.read()

    gazebo = ExecuteProcess(
        cmd=['ign', 'gazebo', '-r', world_file],
        output='screen'
    )

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{
            'robot_description': robot_description,
            'use_sim_time': True
        }],
        output='screen'
    )

    spawn_robot = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=[
            '-world', 'robot_world',
            '-file', urdf_file,
            '-name', 'differential_robot',
            '-x', '0',
            '-y', '0',
            '-z', '0.10'
        ],
        output='screen'
    )

    return LaunchDescription([
        gazebo,
        robot_state_publisher,
        TimerAction(
            period=5.0,
            actions=[spawn_robot]
        )
    ])
