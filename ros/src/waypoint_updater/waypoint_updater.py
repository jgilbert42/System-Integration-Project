#!/usr/bin/env python

import rospy
import tf
from geometry_msgs.msg import PoseStamped
from styx_msgs.msg import Lane, Waypoint

import math
import numpy as np

'''
This node will publish waypoints from the car's current position to some `x` distance ahead.

As mentioned in the doc, you should ideally first implement a version which does not care
about traffic lights or obstacles.

Once you have created dbw_node, you will update this node to use the status of traffic lights too.

Please note that our simulator also provides the exact location of traffic lights and their
current status in `/vehicle/traffic_lights` message. You can use this message to build this node
as well as to verify your TL classifier.

TODO (for Yousuf and Aaron): Stopline location for each traffic light.
'''

LOOKAHEAD_WPS = 200 # Number of waypoints we will publish. You can change this number

REF_VELOCITY = 4.5 


class WaypointUpdater(object):
	def __init__(self):
		rospy.init_node('waypoint_updater')

		rospy.Subscriber('/current_pose', PoseStamped, self.pose_cb)
		self.base_waypoints_sub = rospy.Subscriber('/base_waypoints', Lane, self.waypoints_cb)
		# TODO Later we will need this subscribers, not now
		#rospy.Subscriber('/traffic_waypoint', Lane, self.traffic_cb)
		#rospy.Subscriber('/obstacle_waypoint', Lane, self.obstacle_cb)



		self.final_waypoints_pub = rospy.Publisher('final_waypoints', Lane, queue_size=1)


		# TODO: Add other member variables you need below
		self.pose_x = 0
		self.pose_y = 0
		self.pose_z = 0
		self.yaw = 0
		self.pitch = 0
		self.roll = 0
		self.waypoints = []

		self.loop()


	def loop(self):
		rate = rospy.Rate(50) # Spin 50Hz
		while not rospy.is_shutdown():
			index = self.get_closest_waypoints()

			next_waypoints = Lane()
			next_waypoints.header.stamp = rospy.Time(0)

			next_waypoints.waypoints = self.waypoints[index:index+LOOKAHEAD_WPS]

			self.final_waypoints_pub.publish(next_waypoints)

			rate.sleep()
    

	def pose_cb(self, msg):

		self.pose_x = msg.pose.position.x
		self.pose_y = msg.pose.position.y
		self.pose_z = msg.pose.position.z # We don't need z position I think

		orientation = msg.pose.orientation
		# about the orientation: we only need yaw for this practice since going 10km/h will never make 	the car drift ;)
		euler = tf.transformations.euler_from_quaternion(
			[orientation.x,
			orientation.y,
			orientation.z,
			orientation.w])
		self.roll = euler[0]
		self.pitch = euler[1]
		self.yaw = euler[2]
	

	def waypoints_cb(self, waypoints):

		self.waypoints = waypoints.waypoints
		# Maybe we can unsubscribe from this node since we don't need it anymore
		self.base_waypoints_sub.unregister()

	def traffic_cb(self, msg):
		# TODO: Callback for /traffic_waypoint message. Implement
		pass

	def obstacle_cb(self, msg):
		# TODO: Callback for /obstacle_waypoint message. We will implement it later
		pass

	def get_closest_waypoints(self):
		# To get the closest waypoint we will use self.pose_x, self.pose_y, self.yaw and self.waypoints 
		closest_distance = 1000000
		closest_point = -1
		for i in range(len(self.waypoints)):
			wp_x = self.waypoints[i].pose.pose.position.x
			wp_y = self.waypoints[i].pose.pose.position.y
			
			distance = math.sqrt((self.pose_x - wp_x)**2 + (self.pose_y - wp_y)**2)

			# Since we want the closest waypoint ahead, we need to calculate the angle between the car 				and the waypoint
			psi = np.arctan2(self.pose_y - wp_y, self.pose_x - wp_x)
			dtheta = np.abs(psi - self.yaw)

			if (distance < closest_distance and dtheta < np.pi/4) :
				closest_distance = distance
				closest_point = i

		return closest_point

			

	def get_waypoint_velocity(self, waypoint):
		return waypoint.twist.twist.linear.x

	def set_waypoint_velocity(self, waypoints, waypoint, velocity):
		waypoints[waypoint].twist.twist.linear.x = velocity

	def distance(self, waypoints, wp1, wp2):
		dist = 0
		dl = lambda a, b: math.sqrt((a.x-b.x)**2 + (a.y-b.y)**2  + (a.z-b.z)**2)
		for i in range(wp1, wp2+1):
			dist += dl(waypoints[wp1].pose.pose.position, waypoints[i].pose.pose.position)
			wp1 = i
		return dist


if __name__ == '__main__':
	try:
		WaypointUpdater()
	except rospy.ROSInterruptException:
		rospy.logerr('Could not start waypoint updater node.')