# Copyright 2015 Lakshmi Narasimhan. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

FROM    tsuru/base-platform
RUN     echo 'deb http://archive.ubuntu.com/ubuntu/ vivid main restricted universe multiverse' >> /etc/apt/sources.list
RUN     echo 'deb http://archive.ubuntu.com/ubuntu/ vivid-security main restricted universe multiverse' >> /etc/apt/sources.list
RUN     echo 'APT::Default-Release "trusty";' >> /etc/apt/apt.conf.d/01ubuntu
RUN     apt-get update

# shared dir for files/ folder

RUN	mkdir /shared
RUN     chmod a+w /shared

# deploy and install scripts

ADD	. /var/lib/tsuru/drupal
RUN	cp /var/lib/tsuru/drupal/deploy /var/lib/tsuru
RUN	/var/lib/tsuru/drupal/install
