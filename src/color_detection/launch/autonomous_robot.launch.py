import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node


def generate_launch_description():

    robot_launch = os.path.join(
        get_package_share_directory('robot_description'),
        'launch',
        'display_robot.launch.py'
    )

    gazebo_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(robot_launch)
    )

    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            '/cmd_vel@geometry_msgs/msg/Twist]ignition.msgs.Twist',
            '/odom@nav_msgs/msg/Odometry[ignition.msgs.Odometry',
            '/camera/image@sensor_msgs/msg/Image[ignition.msgs.Image'
        ],
        output='screen'
    )

    camera_detector = Node(
        package='color_detection',
        executable='color_detector',
        output='screen'
    )

    camera_viewer = Node(
        package='rqt_image_view',
        executable='rqt_image_view',
        output='screen'
    )

    navigation_controller = Node(
        package='color_detection',
        executable='color_navigation_controller',
        output='screen'
    )

    return LaunchDescription([
        gazebo_launch,

        TimerAction(
            period=8.0,
            actions=[
                bridge,
                camera_detector,
                camera_viewer,
                navigation_controller
            ]
        )
    ])
