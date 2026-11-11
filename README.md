# Color Navigation Robot

A ROS 2 differential-drive robot simulated with Gazebo Fortress. Show a colored
target to the laptop webcam to control navigation. A separate camera mounted on
the robot streams its point of view so you can monitor the simulation.

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
bridge, laptop-webcam color detection, and the navigation controller. It opens
two camera windows:

- **Stable Colour Detection** shows the laptop webcam with the detected color
  and a `HOME` button. Hold a red, green, or other saturated-color target in
  front of this camera to send the robot to the corresponding pillar.
- **Robot camera view** (`rqt_image_view`) shows the robot-mounted camera. If
  needed, select `/camera/image` in the topic selector. Maximize the window for
  a larger live POV.

The robot camera publishes `sensor_msgs/msg/Image` on `/camera/image`. It is a
separate monitoring view; the laptop webcam is the input that selects the
navigation target. Color results are published on `/detected_color`.

The robot camera is fixed at the front of the chassis. Its body, lens, and
mounting bracket are visible in the robot model. Gazebo publishes a 640x480 RGB
image at 30 Hz.

The laptop webcam is opened from `/dev/video0`. Connect/enable the webcam and
allow desktop camera access before launching. The standalone
`color_detector` node is for detecting from the simulated camera instead; it is
not launched alongside the laptop detector, avoiding competing color commands.
