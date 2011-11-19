# -*- coding: utf-8 -*-

# Copyright (C) 2011, Marine Biological Laboratory
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.
#
# Please read the docs/COPYING file.

description = "USEARCH module"

searchcmd = "usearch -query %(input)s -blast6out %(output)s -wdb %(target)s %(cmdparams)s &> %(log)s"
rfnparams = {'min_alignment_length': int, 
             'min_identity': float}


from pipeline.utils import utils
from pipeline.utils.logger import debug
from pipeline.utils.logger import error

class ModuleError(Exception):
    def __init__(self, e = None):
        Exception.__init__(self)
        self.e = e
        error(e)
        return
    def __str__(self):
        return 'Module Error: %s' % self.e

def clean(m):
    utils.check_dir(m.dirs['parts'], clean_dir_content = True)

def init(m):
    m.files['r1_parts'] = utils.split_fasta_file(m.files['in_r1'], m.dirs['parts'], prefix = 'r1-part')
    
    if not len(m.files['r1_parts']):
        raise ModuleError, 'split_fasta_file returned 0 for "%s"' % m.files['in_r1']

def run(m):
    parts = m.files['r1_parts']
    for part in parts:
        params = {'input': part, 'output': part + '.b6', 'target': m.target_db, 
                  'log': part + '.log', 'cmdparams': ' '.join(m.cmdparams)}
        debug('running part %d/%d (log: %s)' % (parts.index(part) + 1, len(parts), params['log']))
        cmdline = searchcmd % params
        utils.run_command(cmdline)

def finalize(m):
    dest_file = m.files['search_output']
    debug('Search results are being concatenating: %s' % dest_file)
    utils.concatenate_files(dest_file, [part + '.b6' for part in m.files['r1_parts']])

def refine(m):
    pass

def gen_filtered_ids(m):
    pass
