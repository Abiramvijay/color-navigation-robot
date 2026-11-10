import cv2
import numpy as np
import rclpy

from collections import deque
from rclpy.node import Node
from std_msgs.msg import Empty, String


class RealCameraDetector(Node):

    def __init__(self):
        super().__init__('real_camera_detector')

        self.publisher = self.create_publisher(
            String, '/detected_color', 10
        )
        self.home_publisher = self.create_publisher(
            Empty, '/go_home', 10
        )

        self.camera = cv2.VideoCapture(0, cv2.CAP_V4L2)

        if not self.camera.isOpened():
            raise RuntimeError('Cannot open /dev/video0')

        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        self.history = deque(maxlen=5)
        self.last_published = None
        self.window_name = 'Stable Colour Detection'
        self.home_button_rect = None
        cv2.namedWindow(self.window_name, cv2.WINDOW_AUTOSIZE)
        cv2.setMouseCallback(self.window_name, self.handle_mouse_event)

        self.timer = self.create_timer(0.05, self.process_frame)

        self.get_logger().info('RED/GREEN/WHITE detector started.')

    def largest_area(self, mask, minimum_area=1500):
        contours, _ = cv2.findContours(
            mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        if not contours:
            return 0, None

        contour = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(contour)

        if area < minimum_area:
            return 0, None

        return area, cv2.boundingRect(contour)

    def request_home(self):
        self.home_publisher.publish(Empty())
        self.get_logger().info('Home requested.')

    def handle_mouse_event(self, event, x, y, _flags, _parameter):
        if (
            event == cv2.EVENT_LBUTTONUP
            and self.home_button_rect is not None
        ):
            left, top, right, bottom = self.home_button_rect
            if left <= x <= right and top <= y <= bottom:
                self.request_home()

    def process_frame(self):
        ret, frame = self.camera.read()

        if not ret:
            return

        height, width = frame.shape[:2]

        # Use the central 70% of the image as the detection region.
        x1 = int(width * 0.15)
        x2 = int(width * 0.85)
        y1 = int(height * 0.10)
        y2 = int(height * 0.90)

        roi = frame[y1:y2, x1:x2]
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

        # RED
        red_mask = (
            cv2.inRange(
                hsv, np.array([0, 100, 80]),
                np.array([10, 255, 255])
            )
            | cv2.inRange(
                hsv, np.array([160, 100, 80]),
                np.array([180, 255, 255])
            )
        )

        # GREEN
        green_mask = cv2.inRange(
            hsv,
            np.array([35, 80, 80]),
            np.array([85, 255, 255])
        )

        # WHITE: bright pixels with low saturation.
        white_mask = cv2.inRange(
            hsv,
            np.array([0, 0, 140]),
            np.array([180, 90, 255])
        )

        kernel = np.ones((5, 5), np.uint8)

        red_mask = cv2.morphologyEx(
            red_mask, cv2.MORPH_OPEN, kernel
        )
        green_mask = cv2.morphologyEx(
            green_mask, cv2.MORPH_OPEN, kernel
        )
        white_mask = cv2.morphologyEx(
            white_mask, cv2.MORPH_OPEN, kernel
        )

        red_area, red_box = self.largest_area(red_mask)
        green_area, green_box = self.largest_area(green_mask)
        white_area, white_box = self.largest_area(
            white_mask, minimum_area=700
        )

        detected = 'NO_OBJECT'
        box = None

        areas = {
            'RED': (red_area, red_box),
            'GREEN': (green_area, green_box),
            'WHITE': (white_area, white_box)
        }

        colour, (area, candidate_box) = max(
            areas.items(), key=lambda item: item[1][0]
        )

        if area > 0:
            detected = colour
            box = candidate_box

        self.history.append(detected)

        confirmed = 'NO_OBJECT'

        if len(self.history) == 5:
            most_common = max(
                set(self.history),
                key=self.history.count
            )

            if self.history.count(most_common) >= 4:
                confirmed = most_common

        if confirmed != self.last_published:
            msg = String()
            msg.data = confirmed
            self.publisher.publish(msg)
            self.last_published = confirmed

            self.get_logger().info(
                f'Confirmed colour: {confirmed}'
            )

        # Draw the detection region.
        cv2.rectangle(
            frame, (x1, y1), (x2, y2), (255, 255, 0), 2
        )

        # Draw detected object.
        if box is not None:
            x, y, w, h = box
            shrink_x = max(5, int(w * 0.08))
            shrink_y = max(5, int(h * 0.08))
            x1_box = x + x1 + shrink_x
            y1_box = y + y1 + shrink_y
            x2_box = x + x1 + w - shrink_x
            y2_box = y + y1 + h - shrink_y

            cv2.rectangle(
                frame,
                (x1_box, y1_box),
                (x2_box, y2_box),
                (0, 255, 0),
                2
            )

        cv2.putText(
            frame,
            f'Detected: {confirmed}',
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2
        )

        button_left = width - 125
        button_top = 8
        button_right = width - 10
        button_bottom = 42
        self.home_button_rect = (
            button_left, button_top, button_right, button_bottom
        )
        cv2.rectangle(
            frame,
            (button_left, button_top),
            (button_right, button_bottom),
            (0, 128, 0),
            -1
        )
        cv2.putText(
            frame,
            'HOME',
            (button_left + 24, button_top + 24),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (255, 255, 255),
            2
        )

        cv2.imshow(self.window_name, frame)
        key = cv2.waitKey(1) & 0xFF
        if key in (ord('h'), ord('H')):
            self.request_home()

    def destroy_node(self):
        self.camera.release()
        cv2.destroyAllWindows()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = None

    try:
        node = RealCameraDetector()
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    except Exception as error:
        print(f'Camera detector error: {error}')
    finally:
        if node is not None:
            node.destroy_node()

        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
