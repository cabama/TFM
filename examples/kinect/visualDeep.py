"""
An example that shows how to draw the depth map of a scene
"""

import thread
import pygame
from pykinect import nui

DEPTH_WINSIZE = 320,240

screen_lock = thread.allocate()
screen = None

tmp_s = pygame.Surface(DEPTH_WINSIZE, 0, 16)


def depth_frame_ready(frame):
    with screen_lock:
        # Copy raw data in a temp surface
        frame.image.copy_bits(tmp_s._pixels_address)
        
        # Get actual depth data in mm
        arr2d = (pygame.surfarray.pixels2d(tmp_s) >> 3) & 4095
        
        # Process depth data as you prefer
        # arr2d = some_function(arr2d)
        
        # Get an 8-bit depth map (useful to be drawn as a grayscale image)
        arr2d >>= 4
        
        # Copy the depth map in the main surface
        pygame.surfarray.blit_array(screen, arr2d)

        # Update the screen
        pygame.display.update()


def main():
    """Initialize and run the game."""
    pygame.init()

    # Initialize PyGame
    global screen
    screen = pygame.display.set_mode(DEPTH_WINSIZE, 0, 8)
    screen.set_palette(tuple([(i, i, i) for i in range(256)]))
    pygame.display.set_caption('PyKinect Depth Map Example')

    with nui.Runtime() as kinect:
        kinect.depth_frame_ready += depth_frame_ready   
        kinect.depth_stream.open(nui.ImageStreamType.Depth, 2, nui.ImageResolution.Resolution320x240, nui.ImageType.Depth)

        # Main game loop
        while True:
            event = pygame.event.wait()

            if event.type == pygame.QUIT:
                break

if __name__ == '__main__':
    main()