#!/usr/bin/env python

import sys
import time
import os
import platform
from helper import Helper
helper = Helper()

def main():
    helper.is_root()
    options = gather_information(get_defaults())
    helper.prepare()
    mount_volumes(options)
    mount_backup_storage(options)
    install_docker()
    install_nginx(options)
    install_mariadb(options)
    install_rancher(options)
    restore_volumes(options)
    install_ident(options)

def get_defaults():
    return {
        'email': 'email@example.com',
        'rancher_domain': 'cloud.yourdomain.com',
        'volumes_mount': 'local',
        'backup_volumes_mount': 'local',
        'cron_schedule': '0 0 * * *',
        'rancher_mysql_database': 'rancher',
        'mysql_root_password': 'hellodocker'
    }

def gather_information(defaults):
    options = {}
    options['email'] = helper.default_prompt('Email', defaults['email'])
    options['rancher_domain'] = helper.default_prompt('Rancher Domain', defaults['rancher_domain'])
    options['volumes_mount'] = helper.default_prompt('Volumes Mount', defaults['volumes_mount'])
    options['backup_volumes_mount'] = helper.default_prompt('Backup Storage Mount', defaults['backup_volumes_mount'])
    options['cron_schedule'] = helper.default_prompt('Cron Schedule', defaults['cron_schedule'])
    options['rancher_mysql_database'] = helper.default_prompt('Rancher Mysql Database', defaults['rancher_mysql_database'])
    options['mysql_root_password'] = helper.default_prompt('MYSQL Root Password', defaults['mysql_root_password'])
    return options

def mount_volumes(options):
    helper.mount(options['volumes_mount'], '/mnt/volumes')

def mount_backup_storage(options):
    helper.mount(options['backup_volumes_mount'], '/mnt/orch-backup')

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
    -v /volumes/certs:/etc/nginx/certs:ro \
    -v /etc/nginx/vhost.d \
    -v /usr/share/nginx/html \
    -v /var/run/docker.sock:/tmp/docker.sock:ro \
    jwilder/nginx-proxy
    docker run -d --name letsencrypt --restart=unless-stopped \
    -v /volumes/certs:/etc/nginx/certs:rw \
    --label ident=true \
    --volumes-from nginx-proxy \
    -v /var/run/docker.sock:/var/run/docker.sock:ro \
    alastaircoote/docker-letsencrypt-nginx-proxy-companion:latest
    ''')

def install_mariadb(options):
    os.system('''
    docker run -d --name rancherdb --restart=always \
    -v /volumes/rancher-data:/var/lib/mysql \
    -e MYSQL_DATABASE=''' + options['rancher_mysql_database'] + ''' \
    -e MYSQL_ROOT_PASSWORD=''' + options['mysql_root_password'] + ''' \
    --label ident=true \
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
    print('Waiting a minute for everything to start up . . .')
    time.sleep(60)
    os.system('''
    docker run --rm \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v /mnt/orch-backup:/backup \
    -e RESTORE_ALL=true \
    jamrizzi/ident:latest restore
    ''')

def install_ident(options):
    os.system('''
    docker run -d --name ident --restart=always \
    -v /mnt/orch-backup:/backup \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -e CRON_SCHEDULE="''' + options['cron_schedule'] + '''" \
    jamrizzi/ident:latest
    ''')

main()
