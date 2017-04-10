# PyKinect
# Copyright(c) Microsoft Corporation
# All rights reserved.
# 
# Licensed under the Apache License, Version 2.0 (the License); you may not use
# this file except in compliance with the License. You may obtain a copy of the
# License at http://www.apache.org/licenses/LICENSE-2.0
# 
# THIS CODE IS PROVIDED ON AN  *AS IS* BASIS, WITHOUT WARRANTIES OR CONDITIONS
# OF ANY KIND, EITHER EXPRESS OR IMPLIED, INCLUDING WITHOUT LIMITATION ANY
# IMPLIED WARRANTIES OR CONDITIONS OF TITLE, FITNESS FOR A PARTICULAR PURPOSE,
# MERCHANTABLITY OR NON-INFRINGEMENT.
# 
# See the Apache Version 2.0 License for specific language governing
# permissions and limitations under the License.

import thread
import itertools
import ctypes
import math
from quaternion import Quaternion

import pykinect
from pykinect import nui
from pykinect.nui import JointId
from pykinect.nui import SkeletonTrackingState as skState

import pygame
from pygame.color import THECOLORS
from pygame.locals import *


import sys
import signal
import qi
import os
import time

from naoqi import ALProxy
mot = ALProxy("ALMotion", 'localhost', 61535)
KINECTEVENT = pygame.USEREVENT
DEPTH_WINSIZE = 320,240
VIDEO_WINSIZE = 640,480
pygame.init()


# Color que se le pone a cada uno de los esqueletos
SKELETON_COLORS = [THECOLORS["red"], THECOLORS["blue"], THECOLORS["green"],  THECOLORS["orange"], 
					THECOLORS["purple"], THECOLORS["yellow"],  THECOLORS["violet"]]
# Conjuntos de articulaciones por miembro.
LEFT_ARM = (JointId.ShoulderCenter, JointId.ShoulderLeft, JointId.ElbowLeft, JointId.WristLeft,	JointId.HandLeft)
RIGHT_ARM = (JointId.ShoulderCenter, JointId.ShoulderRight, JointId.ElbowRight, JointId.WristRight, JointId.HandRight)
LEFT_LEG = (JointId.HipCenter, JointId.HipLeft, JointId.KneeLeft, JointId.AnkleLeft, JointId.FootLeft)
RIGHT_LEG = (JointId.HipCenter, JointId.HipRight, JointId.KneeRight, JointId.AnkleRight, JointId.FootRight)
SPINE = (JointId.HipCenter, JointId.Spine, JointId.ShoulderCenter, JointId.Head)
# Simplificamos la llamada a la funcion
skeleton_to_depth_image = nui.SkeletonEngine.skeleton_to_depth_image




class Pepper:
	""" 
		Creamos la clase Pepper, en esta clase se va encargar de calcular los angulos que forman cada articulacion 
		y se encarga tambien de pasarle estos movimientos al robot virtual.
	"""


	def dibujar (self, euler):
		# render text
		myfont = pygame.font.SysFont("monospace", 20)

		label1 = myfont.render(str(euler[0]), 1, (255,0,0))
		label2 = myfont.render(str(euler[1]), 1, (255,0,0))
		label3 = myfont.render(str(euler[2]), 1, (255,0,0))

		screen.blit(label1, (100, 100))
		screen.blit(label2, (100, 200))
		screen.blit(label3, (100, 300))

	def run(self, data):

		def ecRecta(pprmin,pprmax,valmin, valmax, value):
			return ((pprmax-pprmin)/(valmax-valmin)) *  (value - valmin ) + pprmin


		rotElbowRight = data.calculate_bone_orientations()[JointId.WristRight].hierarchical_rotation.rotation_quaternion
		#print(dir(rotElbowRight))
		#print(rotElbowRight.start_joint)
		#print('Quaternion enviado: [{0}, {1}, {2}, {3}]'.format(rotElbowRight.w,rotElbowRight.x,rotElbowRight.y,rotElbowRight.z))
		elbowRightQuat = Quaternion(rotElbowRight.w,rotElbowRight.x,rotElbowRight.y,rotElbowRight.z)
		elbowRightEuler = elbowRightQuat.quaternion2euler()
		movCodoDerecho = ecRecta(0.5, 89, -5, 165,  math.degrees(elbowRightEuler[2]))
		#print(movCodoDerecho)

		try:
			mot.setAngles('RElbowRoll', math.radians(movCodoDerecho), 0.5)
		except:
			pass

		#print(math.degrees(elbowRightEuler[2]))
		
		rotShoulderRight = data.calculate_bone_orientations()[JointId.ElbowRight].absolute_rotation.rotation_quaternion
		shoulderRightQuat = Quaternion(rotShoulderRight.w,rotShoulderRight.x,rotShoulderRight.y,rotShoulderRight.z)
		shoulderRightEuler = shoulderRightQuat.quaternion2euler()
		movShoulderPitch = ecRecta(110, -110, -180, 0,  math.degrees(shoulderRightEuler[2]))
		movShoulderRoll = ecRecta(-0.5, -89.5, 0, 90,  math.degrees(shoulderRightEuler[1]))
		#x.append(time.time())
		#y.append(shoulderRightEuler[0])
		#plt.scatter(x,y)
		#plt.show()
		try:
			mot.setAngles('RShoulderPitch', math.radians(movShoulderPitch), 0.5)
			mot.setAngles('RShoulderRoll', math.radians(movShoulderRoll), 0.5)
		except:
			pass

		self.dibujar(map(math.degrees, shoulderRightEuler))
		print(map(math.degrees, shoulderRightEuler))


pepper = Pepper()








# recipe to get address of surface: http://archives.seul.org/pygame/users/Apr-2008/msg00218.html
if hasattr(ctypes.pythonapi, 'Py_InitModule4'):
	 Py_ssize_t = ctypes.c_int
elif hasattr(ctypes.pythonapi, 'Py_InitModule4_64'):
	 Py_ssize_t = ctypes.c_int64
else:
	 raise TypeError("Cannot determine type of Py_ssize_t")

_PyObject_AsWriteBuffer = ctypes.pythonapi.PyObject_AsWriteBuffer
_PyObject_AsWriteBuffer.restype = ctypes.c_int
_PyObject_AsWriteBuffer.argtypes = [ctypes.py_object, ctypes.POINTER(ctypes.c_void_p),ctypes.POINTER(Py_ssize_t)]

def surface_to_array(surface):
	 buffer_interface = surface.get_buffer()
	 address = ctypes.c_void_p()
	 size = Py_ssize_t()
	 _PyObject_AsWriteBuffer(buffer_interface, ctypes.byref(address), ctypes.byref(size))
	 bytes = (ctypes.c_byte * size.value).from_address(address.value)
	 bytes.object = buffer_interface
	 return bytes


# Funcion que dibuja una parte del esqueleto
# pSkeleton -> data
# index -> index
# positions -> LeftArm, RightArm, LeftLeg, RightLeg
# width -> opcional, creo que es el grosor de la linea.

def draw_skeleton_data(pSkelton, index, positions, width = 4):
	start = pSkelton.SkeletonPositions[positions[0]]
		 
	for position in itertools.islice(positions, 1, None):
		next = pSkelton.SkeletonPositions[position.value]
		
		curstart = skeleton_to_depth_image(start, dispInfo.current_w, dispInfo.current_h) 
		curend = skeleton_to_depth_image(next, dispInfo.current_w, dispInfo.current_h)

		pygame.draw.line(screen, SKELETON_COLORS[index], curstart, curend, width)
		
		start = next

# Funcion que manda a dibujar el esqueleto entero.
# Skeletons contiene los distintos skeletos de las distintas personas.
# Por ello se debe de recorrer como un bucle.
# index -> numero de jugador; data-> skeleto de este jugador.
## data.SkeletonPosition[JointId.Head] -> devuelve X Y, Z y W de la posicion.
### x va de -1 a 1.
### y va de -+0.5 [not sure].
### w la distancia a la kinect.

def draw_skeletons(skeletons):
	for index, data in enumerate(skeletons):
		# print('Ususario {0} estado: {1}'.format(index, data.get_tracking_state()))
		if data.get_tracking_state() == skState.TRACKED:
			pepper.run(data)
			#print('Esqueleto {0} no esta siendo tracking'.format(index))
		#elif data.get_tracking_state() == skState.NOT_TRACKED:
		#	print('Esqueleto {0} esta siendo tracking'.format(index))

		# draw the Head
		HeadPos = skeleton_to_depth_image(data.SkeletonPositions[JointId.Head], dispInfo.current_w, dispInfo.current_h) 
		draw_skeleton_data(data, index, SPINE, 10)
		pygame.draw.circle(screen, SKELETON_COLORS[index], (int(HeadPos[0]), int(HeadPos[1])), 20, 0)

		# drawing the limbs
		draw_skeleton_data(data, index, LEFT_ARM)
		draw_skeleton_data(data, index, RIGHT_ARM)
		#draw_skeleton_data(data, index, LEFT_LEG)
		#draw_skeleton_data(data, index, RIGHT_LEG)


def depth_frame_ready(frame):
	if video_display:
		return

	with screen_lock:
		address = surface_to_array(screen)
		frame.image.copy_bits(address)
		del address
		if skeletons is not None and draw_skeleton:
			draw_skeletons(skeletons)
		pygame.display.update()    


def video_frame_ready(frame):
	if not video_display:
		return

	with screen_lock:
		address = surface_to_array(screen)
		frame.image.copy_bits(address)
		del address
		if skeletons is not None and draw_skeleton:
			draw_skeletons(skeletons)
		pygame.display.update()

if __name__ == '__main__':
	full_screen = False
	draw_skeleton = True
	video_display = False

	screen_lock = thread.allocate()

	screen = pygame.display.set_mode(DEPTH_WINSIZE,0,16)    
	pygame.display.set_caption('Python Kinect Demo')
	skeletons = None
	screen.fill(THECOLORS["black"])

	kinect = nui.Runtime()
	kinect.skeleton_engine.enabled = True
	def post_frame(frame):
		try:
			pygame.event.post(pygame.event.Event(KINECTEVENT, skeletons = frame.SkeletonData))
		except:
			# event queue full
			pass

	#def pintar(frame):
		#print('esqueleto listo')

	kinect.skeleton_frame_ready += post_frame
	
	kinect.depth_frame_ready += depth_frame_ready    
	kinect.video_frame_ready += video_frame_ready    
	
	kinect.video_stream.open(nui.ImageStreamType.Video, 2, nui.ImageResolution.Resolution640x480, nui.ImageType.Color)
	kinect.depth_stream.open(nui.ImageStreamType.Depth, 2, nui.ImageResolution.Resolution320x240, nui.ImageType.Depth)
	print('ALO?')
	print(dir(nui))
	print('Controls: ')
	print('     d - Switch to depth view')
	print('     v - Switch to video view')
	print('     s - Toggle displaing of the skeleton')
	print('     u - Increase elevation angle')
	print('     j - Decrease elevation angle')

	# main game loop
	done = False

	while not done:
		e = pygame.event.wait()
		dispInfo = pygame.display.Info()
		if e.type == pygame.QUIT:
			done = True
			break
		elif e.type == KINECTEVENT:
			skeletons = e.skeletons
			if draw_skeleton:
				draw_skeletons(skeletons)
				pygame.display.update()
		elif e.type == KEYDOWN:
			if e.key == K_ESCAPE:
				done = True
				break
			elif e.key == K_d:
				with screen_lock:
					screen = pygame.display.set_mode(DEPTH_WINSIZE,0,16)
					video_display = False
			elif e.key == K_v:
				with screen_lock:
					screen = pygame.display.set_mode(VIDEO_WINSIZE,0,32)    
					video_display = True
			elif e.key == K_s:
				draw_skeleton = not draw_skeleton
			elif e.key == K_u:
				kinect.camera.elevation_angle = kinect.camera.elevation_angle + 2
			elif e.key == K_j:
				kinect.camera.elevation_angle = kinect.camera.elevation_angle - 2
			elif e.key == K_x:
				kinect.camera.elevation_angle = 2
