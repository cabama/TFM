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
from quaternion import Quaternion


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

	## Restructuramos el Skeleto
	@staticmethod
	def reskeleton(data):
		esqueleto = {}
		esqueleto['cabeza'] = data.SkeletonPositions[JointId.Head]
		esqueleto['hombroIzq'] = data.SkeletonPositions[JointId.ShoulderLeft]
		esqueleto['hombroDer'] = data.SkeletonPositions[JointId.ShoulderRight]
		esqueleto['codoIzq'] = data.SkeletonPositions[JointId.ElbowLeft]
		esqueleto['codoDer'] = data.SkeletonPositions[JointId.ElbowRight]
		esqueleto['manoIzq'] = data.SkeletonPositions[JointId.WristLeft]
		esqueleto['manoDer'] = data.SkeletonPositions[JointId.WristRight]
		## Empezamos con las rotaciones
		# giros = {}
		# rotElbowRight = data.calculate_bone_orientations()[JointId.ElbowRight]
		# quaterElbowRight =  rotElbowRight.absolute_rotation.rotation_quaternion
		# print quaterElbowRight
		# roll, pitch, yaw = Pepper.quaternion2euler(quaterElbowRight)
		# giros['shoulderPitch'] = yaw
		# giros['shoulderRoll'] = roll
		# Pepper.mierda(esqueleto['codoDer'], esqueleto['hombroDer'])
		return esqueleto


	# Calculamos los angulos que forman los dos puntos (articulaciones) en los tres planos.
	@staticmethod
	def angulosXplano (puntoA, puntoB, hombroDer=False):

		def calcularAngulo(uno, dos):
			# Compute the angle
			rads = math.atan2(-dos,uno)
			rads %= 2*math.pi
			degs = math.degrees(rads)
			return degs

		dx = puntoB.x - puntoA.x
		dy = puntoB.y - puntoA.y
		dz = puntoB.z - puntoA.z


		if hombroDer == True:
			dz = dz + 0.09
			if dz < 0.0001 and dy > 0:
				dz = 0.0001

		yaw  = calcularAngulo(dx, dy)
		roll = calcularAngulo(dy, dz)
		pitch = calcularAngulo(dx, dz)


		angulosEuler = {'roll': roll, 'pitch': pitch, 'yaw': yaw, 'dx': dx, 'dy':dy, 'dz':dz}
 		return angulosEuler
		#roll = ecRecta(110, -110, 350, 200, roll)
		#pitch = ecRecta(-0.5, -89.5, 230, 160, pitch)
		#print('Mierda roll {1}, yaw {0}, pitch {2}'.format(yaw,roll, pitch))
		#try:
		#	mot.setAngles('RShoulderPitch', math.radians(roll) , 0.5)
		#	mot.setAngles('RShoulderRoll', math.radians(pitch) , 0.5)
		#except:
		#	print('Fuera de rango')



	## Esta funcion crea un diccionario que contiene los angulos de euler por cada articulacion. (Pitch, Roll y Yaw).
	## Estos angulos se calcular llamanando a la funcion angulosXplano
	@staticmethod
	def giros(esqueleto):
		giros = {}
		giros['hombroDer']	= Pepper.angulosXplano(esqueleto['codoDer'], esqueleto['hombroDer'], hombroDer=True)
		giros['hombroIzq']	= Pepper.angulosXplano(esqueleto['codoIzq'], esqueleto['hombroIzq'], hombroDer=True)


		if giros['hombroIzq']['pitch'] < 180:
			giros['hombroIzq']['pitch'] = giros['hombroIzq']['pitch']+360

		#if giros['hombroDer']['pitch'] < 0:
		#	giros['hombroDer']['pitch'] = 360-giros['hombroDer']['pitch']

		giros['codoDer']	= Pepper.angulosXplano(esqueleto['manoDer'], esqueleto['codoDer'])
		giros['codoIzq']	= Pepper.angulosXplano(esqueleto['manoIzq'], esqueleto['codoIzq'])

		# render text
		myfont = pygame.font.SysFont("monospace", 20)
		#for gi in giros['codoDer']:
		#	label1 = myfont.render('roll: ' +str(giros['codoDer']['roll']), 1, (255,0,255))
		#	label2 = myfont.render('pitch: '+str(giros['codoDer']['pitch']), 1, (255,0,255))
		#	label3 = myfont.render('yaw: '  +str(giros['codoDer']['yaw']), 1, (255,0,255))
		#	screen.blit(label1, (50, 50))
		#	screen.blit(label2, (50, 75))
		#	screen.blit(label3, (50, 90))

		return giros



	@staticmethod
	def movimientos (giros):

		movimientos = {}

		def ecRecta(pprmin,pprmax,valmin, valmax, value):
			return ((pprmax-pprmin)/(valmax-valmin)) *  (value - valmin ) + pprmin

		movimientos['RshoulderRoll'] = ecRecta(-0.5, -89.5, 230, 160, giros['hombroDer']['pitch'])
		movimientos['RshoulderPitch'] = ecRecta(110, -110, 350, 200,  giros['hombroDer']['roll'])
		movimientos['LshoulderRoll'] = ecRecta(0.5, 89.5, 320, 400, giros['hombroIzq']['pitch'])
		movimientos['LshoulderPitch'] = ecRecta(110, -110, 370, 200,  giros['hombroIzq']['roll'])
		movimientos['RElbowRoll'] = ecRecta(0, 89.5, 250, 191,  giros['codoDer']['roll'])

		# render text
		myfont = pygame.font.SysFont("monospace", 20)
		#label1 = myfont.render("dx"+str(giros['hombroDer']['dx'] ), 1, (255,0,255))
		#label2 = myfont.render("dy"+str(giros['hombroDer']['dy'] ), 1, (255,0,255))
		label1 = myfont.render("pitch"+str(giros['hombroIzq']['roll']), 1, (255,0,255))
		label2  = myfont.render("pitch"+str(giros['codoDer']['pitch'] ), 1, (255,0,255))
		label3 = myfont.render("movimientos"+str(movimientos['RElbowRoll']), 1, (255,0,255))

		#label3 = myfont.render("Pitch"+str(giros['hombroDer']['pitch'] ), 1, (255,255,0))
		#screen.blit(label, (100, 100))
		screen.blit(label1, (100, 100))
		# screen.blit(label2, (100, 200))
		# screen.blit(label3, (100, 300))

		return movimientos


	@staticmethod
	def moverRobot (movimientos):

		try:
			mot.setAngles('RShoulderRoll',  math.radians(movimientos['RshoulderRoll']), 0.5)
			mot.setAngles('RShoulderPitch', math.radians(movimientos['RshoulderPitch']), 0.5)
			mot.setAngles('LShoulderRoll',  math.radians(movimientos['LshoulderRoll']), 0.5)
			mot.setAngles('LShoulderPitch', math.radians(movimientos['LshoulderPitch']), 0.5)
			#mot.setAngles('RElbowRoll', math.radians(movimientos['RElbowRoll']), 0.5)
		except:
			print('Algun movimiento no se encuentra dentro del rango de grados')

	@staticmethod
	def main_carlos(data):
		#print data
		esqueleto = Pepper.reskeleton(data)
		giros = Pepper.giros(esqueleto)
		movimientos = Pepper.movimientos(giros)

		def ecRecta(pprmin,pprmax,valmin, valmax, value):
			return ((pprmax-pprmin)/(valmax-valmin)) *  (value - valmin ) + pprmin
		rotElbowRight = data.calculate_bone_orientations()[JointId.WristRight].hierarchical_rotation.rotation_quaternion
		elbowRightQuat = Quaternion(rotElbowRight.w,rotElbowRight.x,rotElbowRight.y,rotElbowRight.z)
		elbowRightEuler = elbowRightQuat.quaternion2euler()
		elbowRightEuler2 = elbowRightQuat.quaternion2eulerZYZ()
		print(map(math.degrees, elbowRightEuler2))
		movCodoDerecho = ecRecta(0.5, 89, -5, 165,  math.degrees(elbowRightEuler[2]))
		try:
			mot.setAngles('RElbowRoll', math.radians(movCodoDerecho), 0.5)
		except:
			pass

		Pepper.moverRobot(movimientos)
		#giros_ada
		#ptados = Pepper.calculateGiros(giros)

		# giros = Pepper.calculateGiros(esqueleto)
		# Pepper.moverRobot(giros, 'localhost', 62669)
		# Pepper.main_carlos(esqueleto)
	#giros   = self.calculateGiros(skeleto)
	#print(data.SkeletonPositions[JointId.Head])


	## Calcular los angulos de la mecanica de los brazos
	#@staticmethod
	#def calculateGiros( giros ):
	#	girosEsperados = {}
	#	girosEsperados['shoulderPitch'] = ecuRecta(2.2, -0.5, -2.0857,  2.0857, giros['shoulderPitch'])
	#	girosEsperados['shoulderRoll']  = ecuRecta(2.2, -0.5, -1.5620, -0.0087, giros['shoulderRoll'])
	#	return girosEsperados

	#@staticmethod
	#def vector(a,b):
	#	vector = {}
	#	vector['x'] = b.x - a.x
	#	vector['y'] = b.y - a.y
	#	vector['z'] = b.z - a.z
	#	return vector
	#@staticmethod
	#def quaternion2euler(q):
	#	#print q
	#	t0   = 2 * (q.w * q.x + q.y * q.z)
	#	t1   = 1 - 2 * (q.x * q.x + q.y * q.y)
	#	pitch = math.atan2(t0, t1)

	#	t2 = +2 * (q.w * q.y - q.z * q.x )
	#	if t2 > 1:
	#		t2 = 1
	#	elif t2 < -1:
	#		t2 = -1
	#	yaw = math.asin(t2)

	#	t3 = 2 * (q.w * q.y + q.x *q.z)
	#	t4 = 1 -2 * (q.y * q.y + q.z * q.z)
	#	roll = math.atan2(t3, t4)

	#	#print("Roll: {0}, Pitch: {1}, Yaw: {2}".format(math.degrees(roll), math.degrees(pitch), math.degrees(yaw)))
	#	return [roll, pitch, yaw]

	### Calcular el angulo entre dos puntos
	#@staticmethod
	#def yaw( vector):
	#	return math.atan2(vector['x'], -vector['y'])

	#@staticmethod
	#def pitch ( vector):
	#	return math.atan2(math.sqrt(math.pow(vector['x'],2)+math.pow(vector['y'],2)), vector['z'])

	#@staticmethod
	#def ecuRecta(espeMin, espeMax, min, max, value):
	#	xmax = 2.2
	#	xmin = -0.5
	#	ymax = -2.0857
	#	ymin = +2.0857
	#	conve = ((ymax-ymin)/(xmax-xmin)) *  (giros - xmin ) + ymin
	#	print conve


	# ## Mover robot de maquina virtual
	# @staticmethod
	# def moverRobot(giros, ip, puerto):
	# 	#print('Pepper mov: {}'.format(math.degrees(conve)))
	# 	try:
	# 		mot.setAngles('RShoulderPitch', conve , 0.5)
	# 	except:
	# 		pass







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
			Pepper.main_carlos(data)
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
