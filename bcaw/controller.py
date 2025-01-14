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

import logging
import os
import urllib
from flask import Flask, render_template, send_file, send_from_directory
from flask import Response, stream_with_context, request
from textract import process
from textract.exceptions import ExtensionNotSupported

from bcaw import app
from bcaw.const import ConfKey, MimeTypes
from bcaw.disk_utils import ImageDir, ImageFile, FileSysEle
from bcaw.model import Image, Partition
from bcaw.utilities import identify_mime_path, sha1_path, map_mime_to_ext

@app.route('/')
def bcaw_home():
    """BCAW application home page, test DB is synched and display home."""
    # If there's a different number of images on disk than
    # in the DB table it's time to synch
    if DbSynch.is_synch_db():
        DbSynch.synch_db()

    return render_template('home.html', db_images=Image.images())

@app.route('/image/meta/<image_id>/')
def image_meta(image_id):
    """Image metadata page, retrieves image info from DB and displays it."""
    image = Image.byId(image_id)
    return render_template('image.html', image=image)

@app.route('/image/data/<image_id>/')
def image_dnld(image_id):
    """Image download request, returns the image binary"""
    image = Image.byId(image_id)
    parent = os.path.abspath(os.path.join(image.path, os.pardir))
    return send_from_directory(parent, image.name, as_attachment=True)

@app.route('/image/<image_id>/')
def image_parts(image_id):
    """Page listing the partition details for on image, retrieved from DB."""
    image = Image.byId(image_id)
    logging.debug("Getting parts for image: " + image.name)
    for part in image.partitions.all():
        logging.debug("Part " + str(part.id))
    return render_template('partitions.html', image=image, partitions=image.getPartitions())

@app.route('/image/<image_id>/<part_id>/')
def part_root(image_id, part_id):
    """Displays the root directory of a the chosen partition."""
    return file_handler(image_id, part_id, "/")

@app.route('/image/<image_id>/<part_id>/', defaults={'encoded_filepath': '/'})
@app.route('/image/<image_id>/<part_id>/<path:encoded_filepath>/')
def file_handler(image_id, part_id, encoded_filepath):
    """Display page for a file system element.
    If the element is a directory then the page displays the directory listing
    as read from the disk image.
    If a file is selected they files contents as a binary payload is sent in
    the Response.
    """
    file_path = urllib.unquote(encoded_filepath)
    image = Image.byId(image_id)
    image_part = Partition.byId(part_id)
    fs_ele = FileSysEle.fromImagePath(image.path, image_part, image.bps, file_path)
    # Check if we have a directory
    if fs_ele.isDirectory():
        # Render the dir listing template
        files = FileSysEle.listFiles(image.path, image_part, image.bps, file_path)
        return render_template('directory.html', image=image,
                               partition=image_part, files=files)
    # Its a file, do we want details or binary
    temp_file = FileSysEle.createTempCopy(image.path,
                                          image_part.start,
                                          image.bps, fs_ele)
    # Is this a blob request
    if request_wants_binary():
        return send_file(temp_file, mime_type=FileSysEle.GuessMimeType(fs_ele.name),
                         as_attachment=True, attachment_filename=fs_ele.name)

    mime_type = identify_mime_path(temp_file)
    sha1 = sha1_path(temp_file)
    logging.debug("MIME: %s SHA1:%s", mime_type, sha1)
    extension = map_mime_to_ext(mime_type)
    full_text = "N/A"
    if extension is not None:
        try:
            logging.debug("Textract for doc %s, extension map val %s", file_path, extension)
            full_text = process(temp_file, extension=extension, encoding='ascii')
        except ExtensionNotSupported as _:
            logging.exception("Textract extension not supported for ext %s", extension)
            logging.debug("Temp path for file is %s", temp_file)
            full_text = "N/A"
        except:
            logging.exception("Textract unexpectedly failed for temp_file %s", temp_file)
            raise

    return render_template('analysis.html', image=image, partition=image_part,
                           file_path=file_path, fs_ele=fs_ele, mime_type=mime_type,
                           sha1=sha1, full_text=full_text)

def request_wants_binary():
    """Checks the accepts MIME type of the incoming request and returns True
    if the user has requested a blob, i.e. application/octet-stream."""
    best = request.accept_mimetypes.best_match([MimeTypes.BINARY, MimeTypes.HTML])
    return best == MimeTypes.BINARY and request.accept_mimetypes[best] > \
                                        request.accept_mimetypes[MimeTypes.HTML]

class DbSynch(object):
# Keep a list of images
    """Class that synchs images in the application directory with the DB record.
    """
    image_dir = ImageDir.fromRootDir(app.config[ConfKey.IMAGE_DIR])
    __not_in_db__ = []
    __not_on_disk__ = []

    @classmethod
    def is_synch_db(cls):
        """Returns true if the database needs resynching with file system."""
        cls.disk_synch()
        return Image.imageCount() != DbSynch.image_dir.imageCount()

    @classmethod
    def disk_synch(cls):
        """Updates the list of disk images from the directory listing."""
        cls.image_dir = ImageDir.fromRootDir(app.config[ConfKey.IMAGE_DIR])

    @classmethod
    def synch_db(cls):
        """Updates the database with images found in the image directory."""
        if not cls.is_synch_db():
            return
        # Deal with images not in the database first
        cls.images_not_in_db()
        for image in cls.__not_in_db__:
            logging.info("Adding image: " + image.getPath() + " to database.")
            model_image = Image(**image.toImageDbMap())
            Image.addImage(model_image)
            ImageFile.populateParts(image)
            for part in image.getPartitions():
                Partition.addPart(Partition(**part.toPartDbMap(model_image.id)))

        for image in cls.__not_on_disk__:
            logging.warn("Image: " + image.path + " appears to have been deleted from disk.")

    @classmethod
    def images_not_in_db(cls):
        """Checks that images on the disk are also on database.
        Missing images are added to a member list,
        """
        del cls.__not_in_db__[:]
        for image in cls.image_dir.images:
            db_image = Image.byPath(image.getPath())
            if db_image is None:
                logging.debug("Image: " + image.getPath() + " not in database.")
                cls.__not_in_db__.append(image)

    @classmethod
    def images_not_on_disk(cls):
        """Checks that images in the database are also on disk.
        Missing images are added to a member list,
        """
        del cls.__not_on_disk__[:]
        for image in Image.images():
            if not os.path.isfile(image.path):
                logging.debug("Image: " + image.path + " is no longer on disk.")
                cls.__not_on_disk__.append(image)
