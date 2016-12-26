FROM	tsuru/alpine-base-platform

# shared dir for files/ folder
RUN	mkdir /shared
RUN     chmod a+w /shared

# deploy and install scripts
ADD	. /var/lib/tsuru/drupal
RUN	cp /var/lib/tsuru/drupal/deploy /var/lib/tsuru
RUN	/var/lib/tsuru/drupal/install
