import rospy
from yaw_controller import YawController
from pid import PID
from lowpass import LowPassFilter

GAS_DENSITY = 2.858
ONE_MPH = 0.44704
# Time between two meassurements = 1/50Hz
DELTA_T = 1./50.

# Maybe implement twiddle
P_THR = 0.3
I_THR = 0.05
D_THR = 0.0

MAX_THR = 0.9

TAU = 0.25 # Smooth accelerations over 0.25 ?
TS = 0 # This is delta_t


class Controller(object):
	def __init__(self, *args, **kwargs):
		# TODO: Implement

		self.vehicle_mass = kwargs['vehicle_mass']
		self.fuel_capacity = kwargs['fuel_capacity']
		self.brake_deadband = kwargs['brake_deadband']
		self.decel_limit = kwargs['decel_limit']
		self.accel_limit = kwargs['accel_limit']
		self.wheel_radius = kwargs['wheel_radius']
		self.wheel_base = kwargs['wheel_base']
		self.steer_ratio = kwargs['steer_ratio']
		self.max_lat_accel = kwargs['max_lat_accel']
		self.max_steer_angle = kwargs['max_steer_angle']
	
		# PID for throttle value
		self.pid_throttle = PID(P_THR, I_THR, D_THR, 0, MAX_THR)

		# I don't know how to use the lowpass filter, if anyone does go for it
		self.low_pass_filter = LowPassFilter(TAU, DELTA_T)

		# Brake torque, I got the info of how to calculate the torke in this page https://sciencing.com/calculate-brake-torque-6076252.html
		self.total_vehicle_mass = self.vehicle_mass + self.fuel_capacity/GAS_DENSITY

		# Steering controller
		self.yaw_controller = YawController(self.wheel_base, self.steer_ratio, 2.0, 
											self.max_lat_accel, self.max_steer_angle)


	def control(self, *args, **kwargs):
		# TODO: Change the arg, kwarg list to suit your needs
		# Return throttle, brake, steer
		linear_velocity = kwargs['proposed_linear']
		angular_velocity = kwargs['proposed_angular']
		current_velocity = max(kwargs['curr_vel'], 0)

		brake, steering, throttle = 0.0, 0.0, 0.0
		
                if linear_velocity < 1.0:
                    linear_velocity = 0.0

		# Throttle -> since DELTA_T is constant, we only need to know the difference between current velocity and proposed velocity
		diff_vel = linear_velocity - current_velocity
                #rospy.loginfo("linear: %s, current: %s, diff: %s", linear_velocity, current_velocity, diff_vel)

                # NOTE(jason): not sure if this is the correct usage of these
                # limits, but seems reasonable based on their configured values
                if diff_vel > self.accel_limit:
                    diff_vel = self.accel_limit
                if diff_vel < self.decel_limit:
                    diff_vel = self.decel_limit

		# Logic of throttle/break depending on diff_vel
                if diff_vel > self.brake_deadband:
                    throttle = self.pid_throttle.step(diff_vel, DELTA_T)
                elif diff_vel < -self.brake_deadband:
                    newtons = self.total_vehicle_mass * (diff_vel/DELTA_T)
                    brake_torque = newtons / self.wheel_radius
                    brake = brake_torque * diff_vel * DELTA_T**2 
                elif linear_velocity == 0.0:
                    # This makes sure the car stays still when it's
                    # supposed to be stopped and assumes the prior
                    # waypoints properly slowed down.
                    # Might need to modify if the car is on a hill to keep
                    # from moving.
                    brake = 10
                else:
                    # do nothing/coast
                    pass

		steering = self.yaw_controller.get_steering(linear_velocity, angular_velocity, current_velocity)
		#if steering > self.max_steer_angle: 
			# In order keep the lane, if the desired steering angle is > than max_steer_angle, we will 	have to slow down and set the steering to the maximum or slow down until steering < max_steer_angle
			#steering = max_steer_angle

                #rospy.loginfo("throttle: %s, brake: %s, steering: %s", throttle, brake, steering)
		return throttle, brake, steering

	def reset_pid(self):
		self.pid_throttle.reset()
