#!/bin/sh

sudo uwsgi --emperor /etc/uwsgi-emperor/vassals/ --uid www-data --gid www-data


