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
# This file is part of the BitCurator Access Webtools application.
# Code is used from the samples provided in Lucene download package.
# It provides routines to index the given text files and to search for
# a specified string using these indexes.
#
INDEX_DIR = "IndexFiles.index"

import sys, os, lucene, threading, time
import logging
from datetime import datetime
import subprocess
from subprocess import Popen,PIPE

from java.io import File
from org.apache.lucene.analysis.miscellaneous import LimitTokenCountAnalyzer
from org.apache.lucene.analysis.standard import StandardAnalyzer
from org.apache.lucene.document import Document, Field, FieldType
from org.apache.lucene.index import FieldInfo, IndexWriter, IndexWriterConfig
from org.apache.lucene.store import SimpleFSDirectory
from org.apache.lucene.util import Version
from org.apache.lucene.queryparser.classic import QueryParser

class IndexFiles(object):
    """ IndexFiles takes the root of a directory structure and the destination
        directory as arguments to create Lucene indexes for the directory
        and copy the indexs into the target directory.
        Attributes:
        root: Root of the directory structure containing files to be indexed.
        store_dir: Output directory where indexes are to be stored.
    """
    def __init__(self, root, store_dir):

        if not os.path.exists(store_dir):
            os.mkdir(store_dir, 0777)


        # NOTE: Hardcoded the analyzer instead of passing it
        lucene.initVM()
        '''
        vm_env = lucene.getVMEnv()
        vm_env.attachCurrentThread()
        '''
        analyzer = StandardAnalyzer(Version.LUCENE_CURRENT)
        store = SimpleFSDirectory(File(store_dir))
        analyzer = LimitTokenCountAnalyzer(analyzer, 1048576)
        config = IndexWriterConfig(Version.LUCENE_CURRENT, analyzer)

        # Set the permissions to 777 for the index directory and the write.lock file
        chmod_indexdir_cmd = "chmod 0777 " + store_dir
        writelock_file = store_dir + "/" + "write.lock"
        chmod_writelock_cmd = "chmod 0777 " + writelock_file

        if os.path.exists(store_dir):
            cicmd=os.popen("sudo -S %s"%(chmod_indexdir_cmd), 'w').write('vagrant')

        if os.path.exists(writelock_file):
            cwcmd=os.popen("sudo -S %s"%(chmod_writelock_cmd), 'w').write('vagrant')

        # setting CREATE will rewrite over the existing indexes.
        ###config.setOpenMode(IndexWriterConfig.OpenMode.CREATE)

        writer = IndexWriter(store, config)

        self.indexDocs(root, writer)
        writer.close()

    def indexDocs(self, root, writer):

        # t1 is used for filenames and t2 is used for contents
        t1 = FieldType()
        t1.setIndexed(True)
        t1.setStored(True)
        t1.setTokenized(False)
        t1.setIndexOptions(FieldInfo.IndexOptions.DOCS_AND_FREQS)

        t2 = FieldType()
        t2.setIndexed(True)
        t2.setStored(False)
        t2.setTokenized(True)
        t2.setIndexOptions(FieldInfo.IndexOptions.DOCS_AND_FREQS_AND_POSITIONS)

        for root, dirnames, filenames in os.walk(root):
            for filename in filenames:
                # We can index only a certain types of files
                if not (filename.endswith('.txt') or filename.endswith('.pdf') or filename.endswith('.xml') or filename.endswith('.doc') or filename.endswith('.odt')):
                    continue
                try:
                    file_path = os.path.join(root, filename)
                    outfile_path = file_path

                    # First convert PDF and DOC files to text
                    if filename.endswith('.pdf'):
                        outfile = filename.replace('.pdf', '.txt')
                        outfile_path = os.path.join(root, outfile)
                        cmd = 'pdftotext ' + '-layout ' + "'"+ file_path +  "'" + ' ' + "'" + outfile_path + "'"
                        subprocess.check_output(cmd, shell=True)
                        file_path = outfile_path
                    elif filename.endswith('.doc'):
                        outfile = filename.replace('.doc', '.txt')
                        outfile_path = os.path.join(root, outfile)
                        cmd = 'antiword ' +  file_path + ' >> ' + outfile_path
                        subprocess.check_output(cmd, shell=True)
                        file_path = outfile_path
                    elif filename.endswith('.odt'):
                        outfile = filename.replace('.odt', '.txt')
                        outfile_path = os.path.join(root, outfile)
                        cmd = 'odttotext ' + '-layout ' + "'"+ file_path +  "'" + ' ' + "'" + outfile_path + "'"
                        subprocess.check_output(cmd, shell=True)
                        file_path = outfile_path

                    file = open(file_path)
                    contents = unicode(file.read(), 'iso-8859-1')
                    file.close()
                    doc = Document()
                    doc.add(Field("name", filename, t1))
                    doc.add(Field("path", root, t1))
                    if len(contents) > 0:
                        doc.add(Field("contents", contents, t2))
                    else:
                        logging.debug('warning: no content in %s', filename)
                    writer.addDocument(doc)
                except Exception, e:
                    logging.debug('Failed in indexDocs: %s', e)

def searchIndexedFiles(searcher, analyzer, search_text):
    """ Searces the Lucene index created by indexDocs for the given string,
        search_text
    """
    search_list = []
    logging.debug('Searching for: %s', search_text)
    query = QueryParser(Version.LUCENE_CURRENT, "contents",
                        analyzer).parse(search_text)
    scoreDocs = searcher.search(query, 50).scoreDocs
    logging.debug('%s total matching documents', len(scoreDocs))

    if len(scoreDocs) == 0:
        logging.debug('Query: Not found for : %s', search_text)
        return None
    else:
        for scoreDoc in scoreDocs:
            doc = searcher.doc(scoreDoc.doc)
            file_path = doc.get("path") + "/" + doc.get("name")
            search_list.append(file_path)
        return search_list
