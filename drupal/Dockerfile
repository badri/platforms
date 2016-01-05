# Copyright 2015 basebuilder authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

# this file describes how to build a tsuru drupal 7 image
# to run it:
# 1- run: $ tsuru-admin platform-add drupal -d https://raw.github.com/badri/basebuilder/master/drupal/Dockerfile

FROM    ubuntu:14.04
RUN     apt-get dist-upgrade
RUN	apt-get update
RUN	apt-get install wget -y --force-yes
RUN	apt-get install mysql-client -y
RUN	apt-get install php5-gd -y
RUN	apt-get install php5-curl -y
RUN	apt-get install libssh2-php -y
RUN	apt-get install php5-mysql -y


RUN	mkdir /var/lib/tsuru
RUN	mkdir /shared
RUN     chmod a+w /shared
RUN	wget --no-check-certificate https://github.com/badri/basebuilder/tarball/master -O basebuilder.tar.gz
RUN	tar -xvf basebuilder.tar.gz -C /var/lib/tsuru --strip 1
RUN	rm basebuilder.tar.gz
RUN	cp /var/lib/tsuru/drupal/deploy /var/lib/tsuru
RUN	cp /var/lib/tsuru/drupal/start /var/lib/tsuru
RUN	/var/lib/tsuru/base/install
