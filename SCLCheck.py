# -*- coding: utf-8 -*-
#############################################################################
# File          : SCLCheck.py
# Package       : rpmlint
# Author        : Miro Hrončok
# Created on    : Wed Jul 24 20:25 2013
# Purpose       : Software Collections checks.
#############################################################################

import rpm

from Filter import addDetails, printError, printWarning
from TagsCheck import VALID_GROUPS
import AbstractCheck
import Config
import Pkg
import Common

class SCLCheck(AbstractCheck.AbstractCheck):
    '''Software Collections checks'''

    def __init__(self):
        AbstractCheck.AbstractCheck.__init__(self, "SCLCheck")
        self._spec_file = None

    def check(self, pkg):
        '''Determine what checks to run on what'''
        if not pkg.isSource():
            self.check_binary(pkg)
            return

        # lookup spec file
        for fname, pkgfile in pkg.files().items():
            if fname.endswith('.spec'):
                self._spec_file = pkgfile.path
                self.check_spec(pkg, self._spec_file)
    
    def check_spec(self, pkg, spec_file, spec_lines=[]):
        '''SCL spec file checks'''
        pass

    def check_binary(self, pkg):
        '''SCL binary package checks'''
        pass

# Create an object to enable the auto registration of the test
check = SCLCheck()
