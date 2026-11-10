from setuptools import find_packages, setup

package_name = 'color_detection'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
         ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch',
         ['launch/autonomous_robot.launch.py']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='abiram',
    maintainer_email='abiramvijay12@gmail.com',
    description='ROS 2 OpenCV colour detection node',
    license='Apache-2.0',
    entry_points={
        'console_scripts': [
            'color_detector = color_detection.color_detector:main',
            'real_camera_detector = color_detection.real_camera_detector:main',
            'color_navigation_controller = color_detection.color_navigation_controller:main',
        ],
    },
)
