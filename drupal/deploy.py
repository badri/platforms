# Copyright 2015 basebuilder authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import os
import yaml
import sys
import shlex, subprocess

from utils import parse_env

from interpretor import interpretors
from frontend import frontends


class ConfigurationException(Exception):
    pass


class InstallationException(Exception):
    pass


class Manager(object):
    def __init__(self, configuration, application):
        self.configuration = configuration
        self.application = application

        self.frontend = self.create_frontend()
        self.interpretor = self.create_interpretor()


    def install(self):
        # Calling pre-install hooks
        self.frontend.pre_install()
        if self.interpretor is not None:
            self.interpretor.pre_install()

        packages = self.frontend.get_packages()

        if self.interpretor is not None:
            packages += self.interpretor.get_packages()

        print('Installing system packages...')
        try:
            if os.system("apt-get install -y --force-yes %s" % (' '.join(packages))) != 0:
                raise InstallationException('An error appeared while installing needed packages')
        except InstallationException:
            os.system("apt-get update")
            if os.system("apt-get install -y --force-yes %s" % (' '.join(packages))) != 0:
                raise InstallationException('An error appeared while installing needed packages')

        # Calling post-install hooks
        self.frontend.post_install()
        if self.interpretor is not None:
            self.interpretor.post_install()

        # If there's no Procfile, create it
        Procfile_path = os.path.join(self.application.get('directory'), 'Procfile')
        if not os.path.isfile(Procfile_path):
            f = open(Procfile_path, 'w')
            f.write('frontend: %s\n' % self.frontend.get_startup_cmd())
            if self.interpretor is not None:
                f.write('interpretor: %s\n' % self.interpretor.get_startup_cmd())

            f.close()

        self.install_composer()        

    def install_composer(self):
        working_dir = self.application.get('directory')
        docroot = os.path.join(working_dir, 'docroot')
        if os.path.isdir(docroot):
            working_dir = docroot
        composer_phar = os.path.join(working_dir, 'composer.phar')
        if not os.path.isfile('/usr/local/bin/composer'):
            print('Composer is not found, downloading it')

            download_cmd = 'wget --quiet http://getcomposer.org/composer.phar -O %s && chmod +x %s' % \
                               (composer_phar, composer_phar)

            if os.system(download_cmd) != 0:
                raise InstallationException('Unable to download composer')

            mv_cmd = 'mv %s /usr/local/bin/composer' % (composer_phar)

            if os.system(mv_cmd) != 0:
                raise InstallationException('Unable to mv composer.phar')

        if os.path.isfile(os.path.join(working_dir, 'composer.json')):
            print('Installing composer dependencies')
            if os.system('cd %s && composer install' % (working_dir)) != 0:
                raise InstallationException('Unable to install composer dependencies')

        drupal_config =  self.configuration.get('drupal')

        drush_version = drupal_config.get('drush', 7)
        if drush_version == 8:
            if os.system('composer global require drush/drush:~8') != 0:
                raise InstallationException('Unable to install drush-dev')

        if drush_version == 7:
            if os.system('composer global require drush/drush:7.*') != 0:
                raise InstallationException('Unable to install drush 7')

        if drush_version == 6:
            if os.system('composer global require drush/drush:6.*') != 0:
                raise InstallationException('Unable to install drush 6')

        if not os.path.isfile('/usr/local/bin/drush'):
            if os.system('ln -s /home/ubuntu/.composer/vendor/bin/drush /usr/local/bin/drush') != 0:
                print('Unable to link drush to system path')

        profile = drupal_config.get('profile', 'standard')
        extra_opts = drupal_config.get('extra-opts')
        skip_site_install = drupal_config.get('skip-site-install', False)
        admin_password = drupal_config.get('admin-password', 'admin')

        db_dump_url = drupal_config.get('db-dump-url', '')
        file_dump_url = drupal_config.get('file-dump-url', '')


        os.system('chmod -R a+w /home/ubuntu/.drush')
        working_dir = self.application.get('directory')
        docroot = os.path.join(working_dir, 'docroot')
        if os.path.isdir(docroot):
            working_dir = docroot
            print('docroot is working dir')

        is_installed = "drush status --root={app_dir} | grep -i 'drupal bootstrap' | grep -i -q 'successful'".format(app_dir=working_dir)
        env = {
            "MYSQL_USER": os.environ.get("MYSQL_USER"),
            "MYSQL_PASSWORD": os.environ.get("MYSQL_PASSWORD"),
            "MYSQL_HOST": os.environ.get("MYSQL_HOST"),
            "MYSQL_PORT": os.environ.get("MYSQL_PORT", '3306'),
            "MYSQL_DATABASE_NAME": os.environ.get("MYSQL_DATABASE_NAME"),
            "TSURU_APPNAME": os.environ.get("TSURU_APPNAME"),
        }
        db = {'mysql_user': env['MYSQL_USER'], 'mysql_password': env['MYSQL_PASSWORD'], 'mysql_host': env['MYSQL_HOST'], 'mysql_port': env['MYSQL_PORT'], 'mysql_db_name': env['MYSQL_DATABASE_NAME']}
        data = {'site_profile': profile, 'working_dir':working_dir, 'site_name': 'test site', 'admin_password':admin_password, 'extra_opts': extra_opts}
        data.update(db)
        drush_si = "/usr/bin/env PHP_OPTIONS=\"-d sendmail_path=`which true`\" drush site-install {d[site_profile]} --root={d[working_dir]} --site-name=\"{d[site_name]}\" --account-pass=\"{d[admin_password]}\" --db-url=mysql://{d[mysql_user]}:{d[mysql_password]}@{d[mysql_host]}:{d[mysql_port]}/{d[mysql_db_name]} {d[extra_opts]} --yes".format(d=data)

        # create shared files dir always.
        shared_path = os.path.join(working_dir, 'sites', 'default', 'files')
        shared_files = 'ln  -s /shared %s' % shared_path
        print(shared_files)
        if os.system(shared_files) != 0:
            raise InstallationException('Unable to create shared files for %s' % (shared_path))

        print(is_installed)
        if os.system(is_installed) != 0:
            if db_dump_url:
                print('Drupal is not installed, but found a DB dump url %s' % (db_dump_url))
                wget_db = 'wget "%s" -q -O /tmp/db-dump.sql.gz' % (db_dump_url)
                if os.system(wget_db) != 0:
                    raise InstallationException('Unable download DB dump from %s.' % (db_dump_url))
                decompress_db = 'gzip -d /tmp/db-dump.sql.gz'
                if os.system(decompress_db) != 0:
                    raise InstallationException('Unable to decompress DB dump.')
                drush_import = 'drush sql-cli --root=%s < /tmp/db-dump.sql' % (working_dir)
                print drush_import
                if os.system(drush_import) != 0:
                    raise InstallationException('Unable to import DB using drush.')
                print('Successfully installed using DB dump url %s' % (db_dump_url))
            else:
                if skip_site_install:
                    print('Drupal is not installed. Installing Drupal...')
                    # install Drupal
                    print(drush_si)
                    o = open('/tmp/drush-error', 'w')
                    if subprocess.call(shlex.split(drush_si), stderr=o)  != 0:
                        print(open('/tmp/drush-error', 'r').read())
                        raise InstallationException('Unable to do drush site-install, %s' % (drush_si))
                else:
                    print('Skipping drush site-install command %s' % (drush_si))
            # change permissions of files dir
            file_permissions = 'sudo chmod -R a+w %s' % shared_path
            print(file_permissions)
            if os.system(file_permissions) != 0:
                raise InstallationException('Unable to give write permissions for %s' % (shared_path))
        else:
            print('Drupal is already installed.')


    def configure(self):
        if self.interpretor is not None:
            print('Configuring interpretor...')
            self.interpretor.configure(self.frontend)

        print('Configuring frontend...')
        self.frontend.configure(self.interpretor)

    def setup_environment(self):
        if self.interpretor is not None:
            self.interpretor.setup_environment()

        self.frontend.setup_environment()

    def create_frontend(self):
        frontend = self.configuration.get('frontend', {
            'name': 'apache-mod-php'
        })

        if 'name' not in frontend:
            raise ConfigurationException('Frontend name must be set')

        return self.get_frontend_by_name(frontend.get('name'))(frontend.get('options', {}), self.application)

    def create_interpretor(self):
        interpretor = self.configuration.get('interpretor', None)
        if interpretor is None:
            return None
        elif 'name' not in interpretor:
            raise ConfigurationException('Interpretor name must be set')

        return self.get_interpretor_by_name(interpretor.get('name'))(interpretor.get('options', {}), self.application)

    @staticmethod
    def get_interpretor_by_name(name):
        if name not in interpretors:
            raise ConfigurationException('Interpretor %s is unknown' % name)

        return interpretors.get(name)

    @staticmethod
    def get_frontend_by_name(name):
        if name not in frontends:
            raise ConfigurationException('Frontend %s is unknown' % name)

        return frontends.get(name)


def load_file(working_dir="/home/application/current"):
    files_name = ["tsuru.yml", "tsuru.yaml", "app.yaml", "app.yml"]
    for file_name in files_name:
        try:
            file_path = os.path.join(working_dir, file_name)
            if os.path.exists(file_path) and file_name[0:3] == 'app':
                print('[WARNING] The `%s` configuration file name is deprecated' % file_name)

            with open(file_path) as f:
                return f.read()
        except IOError:
            pass

    return ""


def load_configuration():
    result = yaml.load(load_file())
    if result:
        return result.get('php', {})

    return {}


def print_help():
    print('This have to be called with 1 argument, which is the action')
    print()
    print('Possible values are:')
    print('- install: Install dependencies and configure system')
    print('- environment: Setup the environment')

if __name__ == '__main__':
    # Load PHP configuration from `tsuru.yml`
    config = load_configuration()

    # Create an application object from environ
    application = {
        'directory': '/home/application/current',
        'user': 'ubuntu',
        'source_directory': '/var/lib/tsuru',
        'env': parse_env(config)
    }

    # Get the application manager
    manager = Manager(config, application)

    # Run installation & configuration
    if len(sys.argv) <= 1:
        print_help()
    elif sys.argv[1] == 'install':
        manager.install()
        manager.configure()
    elif sys.argv[1] == 'environment':
        manager.setup_environment()
    else:
        print('Action "%s" not found\n' % sys.argv[1])
        print_help()
