#!/usr/bin/env python

import sys
import os
import platform
from builtins import input
from helper import Helper
helper = Helper()

def main():
    helper.is_root()
    options = gather_information(get_defaults())
    helper.prepare()
    create_volumes_dir(options)
    install_docker()
    install_nginx(options)
    install_mariadb(options)
    install_rancher(options)
    restore_volumes(options)
    install_dockplicity(options)

def get_defaults():
    return {
        'email': 'email@example.com',
        'rancher_domain': 'cloud.yourdomain.com',
        'backup_storage_target_url': '',
        'backup_storage_access_key': '',
        'backup_storage_secret_key': '',
	'backup_storage_volume': '/backup',
        'cron_schedule': '0 0 0 * * *',
        'volumes_directory': '/volumes',
        'volumes_mount': 'local',
        'rancher_mysql_database': 'rancher',
        'mysql_root_password': 'hellodocker'
    }

def gather_information(defaults):
    options = {}
    options['email'] = default_prompt('Email', defaults['email'])
    options['rancher_domain'] = default_prompt('Rancher Domain', defaults['rancher_domain'])
    options['backup_storage_volume'] = default_prompt('Backup Storage Volume', defaults['backup_storage_volume'])
    options['backup_storage_target_url'] = default_prompt('Backup Storage Target URL', defaults['backup_storage_target_url'])
    options['backup_storage_access_key'] = default_prompt('Backup Storage Access Key', defaults['backup_storage_access_key'])
    options['backup_storage_secret_key'] = default_prompt('Backup Storage Secret Key', defaults['backup_storage_secret_key'])
    options['cron_schedule'] = default_prompt('Cron Schedule', defaults['cron_schedule'])
    options['volumes_directory'] = default_prompt('Volumes Directory', defaults['volumes_directory'])
    options['volumes_mount'] = default_prompt('Volumes Mount', defaults['volumes_mount'])
    options['rancher_mysql_database'] = default_prompt('Rancher Mysql Database', defaults['rancher_mysql_database'])
    options['mysql_root_password'] = default_prompt('MYSQL Root Password', defaults['mysql_root_password'])
    return options

def default_prompt(name, fallback):
    response = input(name + ' (' + fallback + '): ')
    assert isinstance(response, str)
    if (response):
        return response
    else:
        return fallback

def create_volumes_dir(options):
    os.system('mkdir -p ' + options['volumes_directory'])
    if os.system(options['volumes_mount']):
        os.system('mkfs.xfs -i size=512 ' + options['volumes_mount'])
        os.system('echo ' + options['volumes_mount'] + options['volumes_directory'] + ' xfs defaults 1 2" >> /etc/fstab')
        os.system('mount -a && mount')

def install_docker():
	os.system('''
    curl -L https://get.docker.com/ | bash
    service docker start
    docker run hello-world
    ''')

def install_nginx(options):
    os.system('''
    docker run -d --name nginx --restart=always -p 80:80 -p 443:443 \
    --name nginx-proxy \
    -v ''' + options['volumes_directory'] + '''/certs:/etc/nginx/certs:ro \
    -v /etc/nginx/vhost.d \
    -v /usr/share/nginx/html \
    -v /var/run/docker.sock:/tmp/docker.sock:ro \
    jwilder/nginx-proxy
    docker run -d --name letsencrypt --restart=unless-stopped \
    -v ''' + options['volumes_directory'] + '''/certs:/etc/nginx/certs:rw \
    --label dockplicity=true \
    --volumes-from nginx-proxy \
    -v /var/run/docker.sock:/var/run/docker.sock:ro \
    alastaircoote/docker-letsencrypt-nginx-proxy-companion:latest
    ''')

def install_mariadb(options):
    os.system('''
    docker run -d --name rancherdb --restart=always \
    -v ''' + options['volumes_directory'] + '''/rancher-data:/var/lib/mysql \
    -e MYSQL_DATABASE=''' + options['rancher_mysql_database'] + ''' \
    -e MYSQL_ROOT_PASSWORD=''' + options['mysql_root_password'] + ''' \
    --label dockplicity=true \
    mariadb:latest
    ''')

def install_rancher(options):
    os.system('''
    docker run -d --name rancher --restart=unless-stopped --link rancherdb:mysql \
    -e VIRTUAL_HOST=''' + options['rancher_domain'] + ''' \
    -e VIRTUAL_PORT=8080 \
    -e LETSENCRYPT_HOST=''' + options['rancher_domain'] + ''' \
    -e LETSENCRYPT_EMAIL=''' + options['email'] + ''' \
    rancher/server:latest \
    --db-host mysql \
    --db-port 3306 \
    --db-user root \
    --db-pass ''' + options['mysql_root_password'] + ''' \
    --db-name ''' + options['rancher_mysql_database'] + '''
    ''')

def restore_volumes(options):
    os.system('''
    docker run --rm \
    -v /var/run/docker.sock:/var/run/docker.sock \
    ''' + (('-v ' + options['storage_volume'] + ':/borg') if options['storage_volume'] != '' else '') + ''' \
    -e STORAGE_ACCESS_KEY=''' + options['backup_storage_access_key'] + ''' \
    -e STORAGE_SECRET_KEY=''' + options['backup_storage_secret_key'] + ''' \
    -e STORAGE_TARGET_URL=''' + options['backup_storage_target_url'] + ''' \
    -e RESTORE_ALL=true \
    jamrizzi/dockplicity:latest restore
    ''')

def install_dockplicity(options):
    os.system('''
    docker run -d --name dockplicity --restart=always \
    -v /var/run/docker.sock:/var/run/docker.sock \
    ''' + (('-v ' + options['storage_volume'] + ':/borg') if options['storage_volume'] != '' else '') + ''' \
    -e STORAGE_ACCESS_KEY=''' + options['backup_storage_access_key'] + ''' \
    -e STORAGE_SECRET_KEY=''' + options['backup_storage_secret_key'] + ''' \
    -e STORAGE_TARGET_URL=''' + options['backup_storage_target_url'] + ''' \
    -e CRON_SCHEDULE="''' + options['cron_schedule'] + '''" \
    jamrizzi/dockplicity:latest
    ''')

main()
