#!/usr/bin/python
# coding=UTF-8
#
# BitCurator Access Webtools (Disk Image Access for the Web)
# Copyright (C) 2014 - 2016
# All rights reserved.
#
# This code is distributed under the terms of the GNU General Public
# License, Version 3. See the text file "COPYING" for further details
# about the terms of this license.
#
# Default settings for bca-webtools and database setup
#

IMAGEDIR = '/var/www/bcaw/disk-images'
DELETED_FILES = True
INDEX_DIR = "/var/www/bcaw/lucene_index"
FILES_TO_INDEX_DIR = "/var/www/bcaw/files_to_index"
SERVER_HOST_NAME = "127.0.0.1"

# FILESEARCH_DB: If set, searches for the filenames in the DB as opposed to
# searching the index
FILESEARCH_DB = True

# FILE_IDEXDIR is the directory where the index for filename search is stored.
FILENAME_INDEXDIR = "/var/www/bcaw/filenames_to_index"

# Celery related configuration: RabbitMQ is used as the broker and the backend.
# The broker URL tells Celery where the broker service is running.
# The backend is the resource which returns the results of a completed task
# from Celery. amqp is a custom protocol that RabbitMQ utilizes.
# (http://www.amqp.org/)
CELERY_BROKER_URL = 'amqp://guest@localhost//'
CELERY_RESULT_BACKEND = 'amqp://guest@localhost//'

MAIL_SERVER = 'smtp.gmail.com'
MAIL_PORT = 465
MAIL_USE_SSL = True
MAIL_USERNAME = 'contact@example.com'
MAIL_PASSWORD = 'your-password'
SQLALCHEMY_DATABASE_URI = 'postgresql://vagrant:vagrant@localhost/bca_db'
