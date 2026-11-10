import cv2
import numpy as np

import rclpy
from rclpy.node import Node

from sensor_msgs.msg import Image
from std_msgs.msg import String
from cv_bridge import CvBridge


class ColorDetector(Node):

    def __init__(self):
        super().__init__('color_detector')

        self.bridge = CvBridge()

        self.image_sub = self.create_subscription(
            Image,
            '/camera/image',
            self.image_callback,
            10
        )

        self.color_pub = self.create_publisher(
            String,
            '/detected_color',
            10
        )

        self.get_logger().info('Color detector started.')

    def image_callback(self, msg):

        try:
            frame = self.bridge.imgmsg_to_cv2(
                msg,
                desired_encoding='bgr8'
            )

            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

            # Red has two HSV ranges because hue wraps around.
            red_lower1 = np.array([0, 100, 100])
            red_upper1 = np.array([10, 255, 255])

            red_lower2 = np.array([160, 100, 100])
            red_upper2 = np.array([180, 255, 255])

            green_lower = np.array([35, 80, 80])
            green_upper = np.array([85, 255, 255])

            red_mask = (
                cv2.inRange(hsv, red_lower1, red_upper1)
                | cv2.inRange(hsv, red_lower2, red_upper2)
            )

            green_mask = cv2.inRange(
                hsv,
                green_lower,
                green_upper
            )

            # Ignore tiny noise regions.
            red_area = cv2.countNonZero(red_mask)
            green_area = cv2.countNonZero(green_mask)

            minimum_area = 500

            if red_area >= minimum_area and red_area > green_area:
                detected = 'RED'

            elif green_area >= minimum_area and green_area > red_area:
                detected = 'GREEN'

            elif red_area >= minimum_area and green_area >= minimum_area:
                detected = 'RED' if red_area > green_area else 'GREEN'

            else:
                detected = 'WHITE'

            output = String()
            output.data = detected
            self.color_pub.publish(output)

        except Exception as error:
            self.get_logger().error(
                f'Image processing failed: {error}'
            )


def main(args=None):

    rclpy.init(args=args)

    node = ColorDetector()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
