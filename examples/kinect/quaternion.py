import sys
import math

# http://www.euclideanspace.com/maths/geometry/rotations/conversions/quaternionToEuler/index.htm

class Quaternion:

	def __init__(self,w,x,y,z):
		self.x = x
		self.y = y
		self.z = z
		self.w = w
		#print(self.x, self.y, self.z, self.w)

	def quaternion2euler(self):
		q = self
		qx2 = q.x * q.x
		qy2 = q.y * q.y
		qz2 = q.z * q.z

		test = q.x*q.y + q.z*q.w

		if (test > 0.499):
			roll 	= math.radians(360/math.pi*math.atan2(q.x,q.w))
			#roll 	%= 2*math.pi
			pitch 	= math.pi/2
			yaw 	= 0
		elif (test < -0.499):
			roll 	= math.radians(-360/math.pi*math.atan2(q.x,q.w))
			#roll 	%= 2*math.pi
			pitch 	= -math.pi/2
			yaw 	= 0

		else:
			#print q
			roll = math.atan2(2 * q.y * q.w - 2 * q.x * q.z, 1 - 2 * qy2 - 2 * qz2)
			#roll %= 2*math.pi
			pitch = math.asin(2*q.x*q.y+2*q.z*q.w)
			#pitch %= 2*math.pi
			yaw = math.atan2(2*q.x*q.w-2*q.y*q.z,1-2*qx2-2*qz2)
			#yaw %= 2*math.pi



		#print("Roll: {0}, Pitch: {1}, Yaw: {2}".format(roll, pitch, yaw))
		return [roll, pitch, yaw]

	def quaternion2eulerZYZ(self):
		q = self

		roll = math.atan2(2 * (q.w * q.x + q.y * q.z), 1 - 2 * (q.x * q.x + q.y * q.y))

		t2 = +2 * (q.w * q.y - q.z * q.x )
		if t2 > 1:
			t2 = 1
		elif t2 < -1:
			t2 = -1
		pitch = math.asin(t2)

		t3 = 2 * (q.w * q.z + q.x *q.y)
		t4 = 1 -2 * (q.y * q.y + q.z * q.z)
		yaw = math.atan2(t3, t4)

		#print("Roll: {0}, Pitch: {1}, Yaw: {2}".format(math.degrees(roll), math.degrees(pitch), math.degrees(yaw)))
		return [roll, pitch, yaw]


if __name__ == '__main__':
	argumentos = sys.argv[1:5]
	argumentos = map(float,argumentos)
	print(argumentos)
	quat = Quaternion(*argumentos)
	print(quat.quaternion2euler())
	print(quat.quaternion2eulerZYZ())