#!/usr/bin/env python2

import os
import sys
import platform

def main():
    if os.getuid() != 0:
        print('Requires root privileges')
        sys.exit('Exiting installer')

    if (platform.dist()[0] == 'centos'):
        os.system('''
        yum update -y
        yum install -y git curl
        ''')
    elif (platform.dist()[0] == 'Ubuntu'):
        os.system('''
        apt-get update -y
        apt-get install -y git curl
        ''')
    else:
        print('Operating system not supported')
        sys.exit('Exiting installer')

    os.system('''
    curl -L https://bootstrap.pypa.io/get-pip.py | python2.7
    git clone https://github.com/jamrizzi/rancher-ident.git
    pip install future
    ''')

    os.system('python2 ./rancher-ident/rancher-ident.py')

    os.system('rm -rf ./install.py ./rancher-ident')

main()
