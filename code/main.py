#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function # Para poder actualizar una linea del print.
import time
import os
import sys

import json # Para el guardado.
import datetime # Para saber el guardado de la muestra.
import threading

class Main:

    """ Inicio del programa.
        En este prgrama preguntaremos si queremos obtener los parametros de un fichero,
        o si se quiere obtener a partir de la Kinect y actuará en consecuencia.
    """

    def __init__(self):
        os.system('clear')      # Limpiamos la consola.
        self.pantallaSeleccion()
        # self.cargandoTanto()

    def cabecera(self):
        print('* * * * * * * * * * * * * * * * * *')
        print(' Pepper Imitate With Kinect        ')
        print(' Developed by Carlos Barreiro Mata ')
        print('* * * * * * * * * * * * * * * * * *')
        print('')

    def pantallaSeleccion(self):
        # Imprimos la informacion
        self.cabecera()
        print('Como desea la imitación de Pepper, por kinect o por un archivo de configuración guardado anteriormente.')
        print('[1] - Mediante Kinect.')
        print('[2] - Mediante un archivo de configuración.')
        print('[3] - Ejemplo de guardado de fichero.') # DEBUG
        print('[4] - Ejemplo de lectura  de fichero.') # DEBUG
        # Gestionamos la respuesta del usuario.
        print("")
        respuesta = int(raw_input('Introduzca un número: '))
        if respuesta == 1:
            self.startWithKinect()
        elif respuesta == 2:
            # Pidiendo la ruta del fichero.
            file = raw_input('Escriba la ruta de su fichero: ')
            # Transformando la ruta en absoluta si no lo fuera.
            if not os.path.isabs(file):
                file = os.path.abspath(file)
                print('Es una ruta relatica y la hemos transformado en: {0}'.format(file))
            # Comprobar que el fichero existe, si no existe sale del programa.
            if not os.path.isfile(file):
                print('El fichero indicado no existe, el programa se cerrara.')
                exit(1)
            # Continuamos en startWithFile.
            self.startWithFile(file)

        # DEBUG
        elif respuesta == 3:
            self.guardandoDiccionario()

        elif respuesta == 4:
            self.lecturaDiccionario()

    def startWithFile(self, file):
        pass
    def startWithKinect(self):
        pass


    # def cargandoTanto(self):
    #     for x in range(100):
    #         print('Estoy cargando, {0} completado.'.format(x), end='\r')
    #         sys.stdout.flush()
    #         time.sleep(0.1)

    def __printContinuo__(self, stringer):
        sys.stdout.flush()
        print(stringer, end='\r')

    def guardandoDiccionario(self):
        # Parametros de esta funcion.
        fich = 'data/skeletonData'
        self.timeInicial = time.time()
        #os.remove(fich)
        # Funcion para guardar continuamente
        def append_record(record):
            with open(fich, 'a') as f:
                json.dump(record, f)
                f.write(os.linesep)
        # Guardamos mil muestras de ejemplo.
        for x in range(1000000):
            pomodoro = float(time.time() - self.timeInicial)
            diccionario = {'a':x , 'b':x, 'c':x, 'time': pomodoro}
            self.__printContinuo__(str(diccionario))
            # Thread para simular el de la kinect
            t = threading.Thread(target=append_record, args=(diccionario,))
            t.start()

    def lecturaDiccionario(self):
        # parametros
        path = 'data/skeletonData'
        fich = open(path)
        numeroLineas = fich.readlines()
        print('El numero de lineas del fichero es {}'.format(numeroLineas))
        self.timeInicial = time.time()
        # Leemos los 50 primeros valores que serán nuestro buffer.
        buffercillo = []
        for x in range(50):
            line = fich.next().strip()
            buffercillo.append(line)

        while

        fich.close()





if __name__ == '__main__':
    a = Main()
