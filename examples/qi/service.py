#!/usr/bin/env python
# -*- coding: utf-8 -*-


# IMPORTAMOS LIBRERIAS
import sys
import signal
import qi
import os
import time
import pykinect


## Partes de Pepper
# LShoulderPitch
# LShoulderRoll
# LElbowYaw
# LElbowRoll
# LWristYaw


# SERVICIO PRINCIPAL

class PythonAppMain(object):

	subscriber_list = []
	loaded_topic = ""

	def __init__(self, application):
		# Getting a session that will be reused everywhere
		self.application = application
		self.session = application.session
		self.service_name = self.__class__.__name__
		print("ServiceName:" + self.service_name)
		# Getting a logger. Logs will be in /var/log/naoqi/servicemanager/{application id}.{service name}
		self.logger = qi.Logger(self.service_name)
		# Do some initializations before the service is registered to NAOqi
		self.logger.info("Initializing...")

	@qi.nobind
	def start_app(self):

		print("Hemos comenzado el servicio")

		self.tts = self.session.service("ALTextToSpeech")
		self.tts.say('Hola soy pepper un robot pepperiano')

		self.mot = self.session.service("ALMotion")
		self.mot.setAngles(['RShoulderPitch', 'LShoulderPitch'], [2,0], 0.1)



if __name__ == "__main__":
	# with this you can run the script for tests on remote robots
	# run : python main.py --qi-url 123.123.123.123
	app = qi.Application(sys.argv)
	app.start()
	service_instance = PythonAppMain(app)



	service_id = app.session.registerService("robotronicaFacial1", service_instance)
	service_instance.start_app()
	app.run()
	#service_instance.cleanup()
	app.session.unregisterService(service_id)
