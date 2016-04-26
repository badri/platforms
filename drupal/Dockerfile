# Copyright 2015 Lakshmi Narasimhan. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

FROM    tsuru/base-platform
RUN	echo 'deb http://ppa.launchpad.net/ondrej/php5-5.6/ubuntu trusty main' >> /etc/apt/sources.list
RUN     apt-get update

# shared dir for files/ folder

RUN	mkdir /shared
RUN     chmod a+w /shared

# deploy and install scripts

ADD	. /var/lib/tsuru/drupal
RUN	cp /var/lib/tsuru/drupal/deploy /var/lib/tsuru
RUN	/var/lib/tsuru/drupal/install
