#!/usr/bin/env python
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

    return overlay_image