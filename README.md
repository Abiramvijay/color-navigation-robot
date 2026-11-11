# Color Navigation Robot

A ROS 2 differential-drive robot simulated with Gazebo Fortress. The robot uses
an onboard forward-facing camera to detect colored targets and navigate toward
them.

## Requirements

- ROS 2 Humble
- Gazebo Fortress and the ROS-Gazebo integration packages
- `xacro`, `rqt_image_view`, and `cv_bridge`

## Build

From the workspace root:

```bash
source /opt/ros/humble/setup.bash
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install
source install/setup.bash
```

## Run the simulation

```bash
source install/setup.bash
ros2 launch color_detection autonomous_robot.launch.py
```

The launch starts Gazebo, the differential-drive robot, the camera-to-ROS image
bridge, color detection, and the navigation controller. The `rqt_image_view`
window opens alongside Gazebo; select `/camera/image` in its topic selector to
see the live view from the robot-mounted camera.

The camera image is published as `sensor_msgs/msg/Image` on `/camera/image`.
The detector publishes color results on `/detected_color`.

## Robot camera

The camera is fixed at the front of the chassis. Its body, lens, and mounting
bracket are visible in the robot model. The Gazebo camera sensor publishes a
640x480 RGB image at 30 Hz.

## Real camera option

`real_camera_detector` is a separate node for a host webcam at `/dev/video0`.
It is not started by the simulation launch; use it separately when working with
a physical camera.
