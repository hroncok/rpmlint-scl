# -*- coding: utf-8 -*-
#############################################################################
# File          : SCLCheck.py
# Package       : rpmlint
# Author        : Miro Hrončok
# Created on    : Wed Jul 24 20:25 2013
# Purpose       : Software Collections checks.
#############################################################################

import rpm, re

from Filter import addDetails, printError, printWarning
from TagsCheck import VALID_GROUPS
import AbstractCheck
import Config
import Pkg
import Common

# Compile all regexes here
global_scl_definition = re.compile(r'(^|\s)%(define|global)\s+scl\s+\S+$',re.M)
subpackage_runtime = re.compile(r'(^|\s)%package\s+runtime\s*$',re.M)
subpackage_build = re.compile(r'(^|\s)%package\s+build\s*$',re.M)
subpackage_alien = re.compile(r'(^|\s)%package\s+(?!(build|runtime))\S+\s*$',re.M)
requires = re.compile(r'^Requires:\s*(.*)', re.M)
buildrequires = re.compile(r'^BuildRequires:\s*(.*)', re.M)
scl_install = re.compile(r'(^|\s)%\{?\??scl_install\}?\s*$', re.M)
noarch = re.compile(r'^BuildArch:\s*noarch\s*$', re.M)
libdir = re.compile(r'%\{?\??_libdir\}?', re.M)
scl_files = re.compile(r'(^|\s)%\{?\??scl_files\}?\s*$', re.M)
scl_macros = re.compile(r'(^|\s)%\{?\??_root_sysconfdir\}?/rpm/macros\.%\{?\??scl\}?-config\s*^', re.M)

def index_or_sub(source, word, sub=0):
    '''Helper function that returns index of word in source or sub when not found'''
    try:
        return source.index(word)
    except:
        return sub

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
        spec = '\n'.join(Pkg.readlines(spec_file))
        if global_scl_definition.search(spec):
            self.check_metapackage(pkg, spec_file, spec)

    def check_binary(self, pkg):
        '''SCL binary package checks'''
        pass

    def check_metapackage(self, pkg, spec_file, spec):
        '''SCL metapackage spec checks'''
        
        # Examine subpackages
        runtime = subpackage_runtime.search(spec)
        if not runtime:
            printError(pkg, 'no-runtime-in-scl-metapackage', spec_file)
        
        build = subpackage_build.search(spec)
        if not build:
            printError(pkg, 'no-build-in-scl-metapackage', spec_file)
        else:
            # Get (B)Rs section for build subpackage
            end = index_or_sub(spec[build.end():],'%package',-1)
            if 'scl-utils-build' not in ' '.join(self.get_requires(spec[build.end():end])):
                printError(pkg, 'scl-build-without-requiring-scl-utils-build', spec_file)
        
        if subpackage_alien.search(spec):
            printError(pkg, 'weird-subpackage-in-scl-metapackage', spec_file)
        
        # Get (B)Rs section for main package
        end = index_or_sub(spec,'%package',-1)
        if 'scl-utils-build' not in ' '.join(self.get_build_requires(spec[:end])):
            printError(pkg, 'scl-metapackage-without-scl-utils-build-br', spec_file)
        
        # Enter %install section
        install_start = index_or_sub(spec,'%install')
        install_end = index_or_sub(spec,'%check')
        if not install_end: install_end = index_or_sub(spec,'%clean')
        if not install_end: install_end = index_or_sub(spec,'%files')
        if not install_end: install_end = index_or_sub(spec,'%changelog',-1)
        # Search %scl_install
        if not scl_install.search(spec[install_start:install_end]):
            printError(pkg, 'scl-metapackage-without-%scl_install', spec_file)
        if noarch.search(spec[:install_start]) and libdir.search(spec[install_start:install_end]):
            printError(pkg, 'noarch-scl-metapackage-with-libdir', spec_file)
        
        # Analyze %files
        if self.get_files(spec):
            printWarning(pkg, 'scl-main-metapackage-contains-files', spec_file)
        if runtime:
            if not scl_files.search('\n'.join(self.get_files(spec,'runtime'))):
                printError(pkg, 'scl-runtime-package-without-%scl_files', spec_file)
        if build:
            if not scl_macros.search('\n'.join(self.get_files(spec,'build'))):
                printError(pkg, 'scl-build-package-without-rpm-macros', spec_file)
            
    
    def get_requires(self, text, build=False):
        '''For given piece of spec, find Requires (or BuildRequires)'''
        if build:
            search = buildrequires
        else:
            search = requires
        res = []
        while True:
            more = search.search(text)
            if not more: break
            res.extend(more.groups())
            text = text[more.end():]
        return res
        
    def get_build_requires(self, text):
        '''Call get_requires() with build = True'''
        return self.get_requires(text,True)
    
    def get_files(self, text, subpackage=None):
        '''Return the list of files in %files section for given subpackage or main package'''
        if subpackage:
            pattern = r'%\{?\??files\}?(\s+-n)?\s+'+subpackage+'\s*$'
        else:
            pattern = r'%\{?\??files\}?\s*$'
        search = re.search(pattern, text, re.M)
        if not search: return []
        
        start = search.end()
        end = index_or_sub(text[start:],'%files')
        if not end: end = index_or_sub(text[start:],'%changelog',-1)
        return list(filter(None, text[start:start+end].strip().split('\n')))

# Create an object to enable the auto registration of the test
check = SCLCheck()

# Add information about checks
addDetails(
'no-runtime-in-scl-metapackage',
'SCL metapackage must have runtime subpackage',

'no-build-in-scl-metapackage',
'SCL metapackage must have build subpackage',

'weird-subpackage-in-scl-metapackage',
'Only allowed subpackages in SCL metapackage are build and runtime'

'scl-metapackage-without-scl-utils-build-br',
'SCL metapackage must BuildRequire scl-utils-build',

'scl-build-without-requiring-scl-utils-build',
'SCL runtime package must Require scl-utils-build',

'scl-metapackage-without-%scl_install',
'SCL metapackage must call %scl_install in the %install section',

'noarch-scl-metapackage-with-libdir',
'If "enable" script of SCL metapackage contains %{_libdir}, the package must be arch specific, otherwise it may be noarch',

'scl-main-metapackage-contains-files',
'Main package of SCL metapackage should not contain any files',

'scl-runtime-package-without-%scl_files',
'SCL runtime package must contain %scl_files in %files section',

'scl-build-package-without-rpm-macros',
'SCL build package must contain %{_root_sysconfdir}/rpm/macros.%{scl}-config in %files section'
)
