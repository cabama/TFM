class Plotting:

    def __init__(self):
        """
        Inicializamos la clase que se encarga de dibujar con PyGame.
        """
        # recipe to get address of surface: http://archives.seul.org/pygame/users/Apr-2008/msg00218.html
        if hasattr(ctypes.pythonapi, 'Py_InitModule4'):
            Py_ssize_t = ctypes.c_int
        elif hasattr(ctypes.pythonapi, 'Py_InitModule4_64'):
            Py_ssize_t = ctypes.c_int64
        else:
            raise TypeError("Cannot determine type of Py_ssize_t")
        # Parametros
        KINECTEVENT = pygame.USEREVENT
        DEPTH_WINSIZE = 320,240
        VIDEO_WINSIZE = 640,480
        pygame.init()
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

    def draw_skeleton_data(pSkelton, index, positions, width = 4):
    	start = pSkelton.SkeletonPositions[positions[0]]
    	for position in itertools.islice(positions, 1, None):
    		next = pSkelton.SkeletonPositions[position.value]
    		curstart = skeleton_to_depth_image(start, dispInfo.current_w, dispInfo.current_h)
    		curend = skeleton_to_depth_image(next, dispInfo.current_w, dispInfo.current_h)
    		pygame.draw.line(screen, SKELETON_COLORS[index], curstart, curend, width)
    		start = next

    def draw_skeletons(skeletons):
    	for index, data in enumerate(skeletons):
            # Si hay trackin de un esqueleto.
            # Mandamos los datos del skeleto a nuestra clase que se encarga de realizar los posteriores calculos.
    		if data.get_tracking_state() == skState.TRACKED:
    			Pepper.main_carlos(data)
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
    		address = self.surface_to_array(screen)
    		frame.image.copy_bits(address)
    		del address
    		if skeletons is not None and draw_skeleton:
    			draw_skeletons(skeletons)
    		pygame.display.update()
