import sys
import os
import platform

class Helper:
    def prepare(self):
        if (platform.dist()[0] == 'centos'):
            os.system('''
            yum clean all
            rpm --rebuilddb
            yum update -y
            yum install -y nfs-utils nfs-utils-lib
            ''')
        elif (platform.dist()[0] == 'Ubuntu'):
            os.system('''apt-get update -y
            apt-get install -y nfs-common
            ''')
        else:
            print('Operating system not supported')
            sys.exit('Exiting installer')

    def is_root(self):
        if os.getuid() != 0:
            print('Requires root privileges')
            sys.exit('Exiting installer')
