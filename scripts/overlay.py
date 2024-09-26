#!/usr/bin/env python

import rospy
from sensor_msgs.msg import Image
from std_msgs.msg import Float32MultiArray
from cv_bridge import CvBridge, CvBridgeError
import cv2
import numpy as np

class ThermalOverlay:
    def __init__(self):
        # Initialize the ROS node
        rospy.init_node('thermal_overlay', anonymous=True)

        # Create a CvBridge object for converting ROS Image messages to OpenCV images
        self.bridge = CvBridge()

        # Image and thermal data placeholders
        self.cv_image = None
        self.thermal_data = None

        # Flag to control running state
        self.running = True

        # Publisher for the overlay result
        self.image_pub = rospy.Publisher('/thermal_overlay_result', Image, queue_size=10)

        # Subscribe to the image topic
        rospy.Subscriber('/camera/image_raw', Image, self.image_callback)

        # Subscribe to the Float32MultiArray topic
        rospy.Subscriber('/thermal_image', Float32MultiArray, self.array_callback)

        # Run the loop to check for 'q' key press
        self.run()

    def image_callback(self, msg):
        try:
            # Convert the ROS Image message to an OpenCV image
            self.cv_image = self.bridge.imgmsg_to_cv2(msg, "bgr8")
        except CvBridgeError as e:
            rospy.logerr("CvBridge error: {}".format(e))

    def array_callback(self, msg):
        # Store the thermal data
        self.thermal_data = msg.data

    def run(self):
        rate = rospy.Rate(10)  # Loop at 10 Hz

        while not rospy.is_shutdown() and self.running:
            # Process image and thermal data if available
            if self.cv_image is not None and self.thermal_data is not None:
                # Assuming the Float32MultiArray contains [temperature, normalized_x, normalized_y]
                temperature = self.thermal_data[0]
                norm_x = self.thermal_data[1]
                norm_y = self.thermal_data[2]

                # Denormalize the x, y coordinates to pixel values
                height, width, _ = self.cv_image.shape
                x = int(norm_x * width)
                y = int(norm_y * height)

                # Draw a circle at the denormalized (x, y) coordinates
                cv2.circle(self.cv_image, (x, y), radius=5, color=(0, 255, 0), thickness=-1)

                # Put the temperature value as text near the circle
                font = cv2.FONT_HERSHEY_SIMPLEX
                cv2.putText(self.cv_image, f"{temperature:.2f}C", (x + 10, y - 10), font, 0.6, (255, 0, 0), 2)

                # Display the image with the overlay
                cv2.imshow("Image with Overlay", self.cv_image)

                # Convert the OpenCV image back to a ROS Image message
                try:
                    overlay_image_msg = self.bridge.cv2_to_imgmsg(self.cv_image, "bgr8")
                    # Publish the overlaid image
                    self.image_pub.publish(overlay_image_msg)
                except CvBridgeError as e:
                    rospy.logerr("CvBridge error: {}".format(e))

                # Check for 'q' key press to quit
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    self.running = False
                    break

            # Sleep to maintain loop rate
            rate.sleep()

        # When 'q' is pressed, close the window
        cv2.destroyAllWindows()

if __name__ == '__main__':
    try:
        ThermalOverlay()
    except rospy.ROSInterruptException:
        pass
