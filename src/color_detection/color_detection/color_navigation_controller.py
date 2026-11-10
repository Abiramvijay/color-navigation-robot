import math

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from std_msgs.msg import Empty, String


class ColorNavigationController(Node):

    def __init__(self):
        super().__init__('color_navigation_controller')

        self.cmd_pub = self.create_publisher(
            Twist, '/cmd_vel', 10
        )

        self.color_sub = self.create_subscription(
            String, '/detected_color',
            self.color_callback, 10
        )

        self.home_sub = self.create_subscription(
            Empty, '/go_home',
            self.home_callback, 10
        )

        self.odom_sub = self.create_subscription(
            Odometry, '/odom',
            self.odom_callback, 10
        )

        self.pillar_goals = {
            'RED': (2.45, 0.0),
            'GREEN': (0.0, 2.45),
            'WHITE': (-2.45, 0.0)
        }

        self.current_color = None
        self.active_target = None
        self.x = None
        self.y = None
        self.yaw = None
        self.last_odom_time = None
        self.reached_target = False

        self.pillar_goal_tolerance = 0.08
        self.home_pose = (0.0, 0.0, 0.0)
        self.timer = self.create_timer(0.05, self.control_loop)

        self.get_logger().info(
            'Colour navigation controller started. '
            'Waiting for a color or home request.'
        )

    def publish_stop(self):
        self.cmd_pub.publish(Twist())

    def color_callback(self, msg):
        color = msg.data.strip().upper()

        if color not in self.pillar_goals:
            return

        if self.active_target is not None and not self.reached_target:
            return

        if self.reached_target and color == self.current_color:
            return

        self.current_color = color
        self.active_target = color
        self.reached_target = False
        self.get_logger().info(
            f'{color} detected. Driving to its map destination.'
        )

    def home_callback(self, _msg):
        self.publish_stop()
        self.active_target = 'HOME'
        self.reached_target = False
        self.get_logger().info(
            'Home requested. Returning to the starting pose.'
        )

    def odom_callback(self, msg):
        position = msg.pose.pose.position
        orientation = msg.pose.pose.orientation

        self.x = position.x
        self.y = position.y
        self.last_odom_time = self.get_clock().now()

        self.yaw = math.atan2(
            2.0 * (
                orientation.w * orientation.z
                + orientation.x * orientation.y
            ),
            1.0 - 2.0 * (
                orientation.y ** 2 + orientation.z ** 2
            )
        )

    @staticmethod
    def normalize_angle(angle):
        return math.atan2(math.sin(angle), math.cos(angle))

    def control_loop(self):
        if self.last_odom_time is None:
            self.publish_stop()
            return
        odom_age = (
            self.get_clock().now() - self.last_odom_time
        ).nanoseconds / 1e9
        if odom_age > 0.5:
            self.publish_stop()
            self.get_logger().error("Odometry timeout. Robot stopped.")
            return
        if (
            self.active_target is None
            or self.x is None
            or self.y is None
            or self.yaw is None
            or self.reached_target
        ):
            self.publish_stop()
            return

        returning_home = self.active_target == 'HOME'
        if returning_home:
            target_x, target_y, home_yaw = self.home_pose
            arrival_distance = 0.10
        else:
            target_x, target_y = self.pillar_goals[self.active_target]
            arrival_distance = self.pillar_goal_tolerance

        dx = target_x - self.x
        dy = target_y - self.y
        distance = math.hypot(dx, dy)

        if distance <= arrival_distance:
            self.publish_stop()
            if returning_home:
                heading_error = self.normalize_angle(home_yaw - self.yaw)
                if abs(heading_error) > 0.08:
                    cmd = Twist()
                    cmd.angular.z = max(
                        -0.5, min(0.5, 1.0 * heading_error)
                    )
                    self.cmd_pub.publish(cmd)
                    return

                self.get_logger().info('Returned to the home pose.')
            else:
                self.get_logger().info(
                    'Reached the staging point near the '
                    f'{self.active_target} pillar.'
                )
            self.reached_target = True
            return

        target_yaw = math.atan2(dy, dx)
        angle_error = self.normalize_angle(target_yaw - self.yaw)

        cmd = Twist()

        # Rotate first if the heading error is too large.
        if abs(angle_error) > 0.12:
            cmd.angular.z = max(
                -0.7, min(0.7, 1.2 * angle_error)
            )
        else:
            cmd.linear.x = min(0.30, 0.8 * distance)
            cmd.angular.z = max(
                -0.4, min(0.4, 1.0 * angle_error)
            )

        self.cmd_pub.publish(cmd)

    def destroy_node(self):
        self.publish_stop()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = ColorNavigationController()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.publish_stop()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
