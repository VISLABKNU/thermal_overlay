#!/usr/bin/env python

import rospy
from sensor_msgs.msg import Image
from std_msgs.msg import Float32MultiArray
from cv_bridge import CvBridge, CvBridgeError
import cv2
import numpy as np
import matplotlib.pyplot as plt



def apply_thermal_overlay(image, thermal_values):
    """
    Apply a thermal overlay on an image using the given thermal values.
    
    Parameters:
        image (np.array): The input image array (height, width, 3).
        thermal_values (np.array): The thermal values as a 2D array (smaller resolution).
    
    Returns:
        overlay_image (np.array): The image with the thermal overlay applied.
    """
    #convert bgr to rgb
    # image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    height, width = image.shape[:2]
    thermal_resized = cv2.resize(thermal_values, (width, height), interpolation=cv2.INTER_LINEAR)

    thermal_normalized = cv2.normalize(thermal_resized, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    print(thermal_normalized.max())
    print(thermal_normalized.min())
    thermal_colormap = cv2.applyColorMap(255 -thermal_normalized, cv2.COLORMAP_JET)

    _, _, _, max_loc = cv2.minMaxLoc(thermal_resized)

    alpha = 0.5  # Transparency for overlay
    overlay_image = cv2.addWeighted(thermal_colormap, alpha, image, 1 - alpha, 0)

    cv2.circle(overlay_image, max_loc, 10, (255, 0, 0), 2)  # Mark hottest spot with a red circle

    cv2.putText(overlay_image, f'Max Temp: {thermal_values.max():.1f}', (10, 20), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1, cv2.LINE_AA)
    overlay_image = cv2.cvtColor(overlay_image, cv2.COLOR_BGR2RGB)

    return overlay_image




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
                heat_values = self.thermal_data

                print(heat_values)
                # reconstruct
                heat_values = np.array(heat_values)
                heat_values = heat_values.reshape(120, 160)  
                overlay_image = apply_thermal_overlay(self.cv_image, heat_values)
                # # Denormalize the x, y coordinates to pixel values
                # height, width, _ = self.cv_image.shape
                # x = int(norm_x * width)
                # y = int(norm_y * height)

                # # Draw a circle at the denormalized (x, y) coordinates
                # cv2.circle(self.cv_image, (x, y), radius=5, color=(0, 255, 0), thickness=-1)

                # # Put the temperature value as text near the circle
                # font = cv2.FONT_HERSHEY_SIMPLEX
                # cv2.putText(self.cv_image, f"{temperature:.2f}C", (x + 10, y - 10), font, 0.6, (255, 0, 0), 2)

                
                # Display the image with the overlay
                cv2.imshow("Image with Overlay", overlay_image)

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
