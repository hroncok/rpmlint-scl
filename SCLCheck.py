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
global_scl_definition = re.compile(r'(^|\s)%(define|global)\s+scl\s+\S+\s*$',re.M)
scl_package_definition = re.compile(r'(^|\s)%\{\?scl\s*:\s*%scl_package\s+\S+\s*\}\s*$',re.M)
scl_use = re.compile(r'%\{?\??\!?\??scl')
subpackage_runtime = re.compile(r'(^|\s)%package\s+runtime\s*$',re.M)
subpackage_build = re.compile(r'(^|\s)%package\s+build\s*$',re.M)
subpackage_alien = re.compile(r'(^|\s)%package\s+(-n\s+)?(?!(build|runtime))\S+\s*$',re.M)
requires = re.compile(r'^Requires:\s*(.*)', re.M)
buildrequires = re.compile(r'^BuildRequires:\s*(.*)', re.M)
name = re.compile(r'^Name:\s*(.*)', re.M)
scl_prefix = re.compile(r'%\{?\??scl_prefix\}?', re.M)
scl_prefix_strict = re.compile(r'^%\{?\?scl_prefix\}?', re.M)
scl_install = re.compile(r'(^|\s)%\{?\??scl_install\}?\s*$', re.M)
noarch = re.compile(r'^BuildArch:\s*noarch\s*$', re.M)
libdir = re.compile(r'%\{?\??_libdir\}?', re.M)
scl_files = re.compile(r'(^|\s)%\{?\??scl_files\}?\s*$', re.M)
scl_macros = re.compile(r'(^|\s)%\{?\??_root_sysconfdir\}?/rpm/macros\.%\{?\??scl\}?-config\s*^', re.M)
pkg_name = re.compile(r'(^|\s)%\{!\?scl:%(define|global)\s+pkg_name\s+%\{name\}\}\s*$', re.M)


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
            self.check_metapackage(pkg, spec)
        elif scl_package_definition.search(spec):
            self.check_scl_spec(pkg, spec)
        elif scl_use.search(spec):
            printError(pkg, 'undeclared-scl')

    def check_binary(self, pkg):
        '''SCL binary package checks'''
        pass

    def check_metapackage(self, pkg, spec):
        '''SCL metapackage spec checks'''
        
        # Examine subpackages
        runtime = subpackage_runtime.search(spec)
        if not runtime:
            printError(pkg, 'no-runtime-in-scl-metapackage')
        
        build = subpackage_build.search(spec)
        if not build:
            printError(pkg, 'no-build-in-scl-metapackage')
        else:
            # Get (B)Rs section for build subpackage
            end = index_or_sub(spec[build.end():],'%package',-1)
            if 'scl-utils-build' not in ' '.join(self.get_requires(spec[build.end():end])):
                printWarning(pkg, 'scl-build-without-requiring-scl-utils-build')
        
        alien = subpackage_alien.search(spec)
        if alien:
            printError(pkg, 'weird-subpackage-in-scl-metapackage', alien.group()[9:])
        
        # Get (B)Rs section for main package
        end = index_or_sub(spec,'%package',-1)
        if 'scl-utils-build' not in ' '.join(self.get_build_requires(spec[:end])):
            printError(pkg, 'scl-metapackage-without-scl-utils-build-br')
        
        # Enter %install section
        install_start = index_or_sub(spec,'%install')
        install_end = index_or_sub(spec,'%check')
        if not install_end: install_end = index_or_sub(spec,'%clean')
        if not install_end: install_end = index_or_sub(spec,'%files')
        if not install_end: install_end = index_or_sub(spec,'%changelog',-1)
        # Search %scl_install
        if not scl_install.search(spec[install_start:install_end]):
            printError(pkg, 'scl-metapackage-without-%scl_install')
        if noarch.search(spec[:install_start]) and libdir.search(spec[install_start:install_end]):
            printError(pkg, 'noarch-scl-metapackage-with-libdir')
        
        # Analyze %files
        files = self.get_files(spec)
        if files:
            printWarning(pkg, 'scl-main-metapackage-contains-files', ', '.join(files))
        if runtime:
            if not scl_files.search('\n'.join(self.get_files(spec,'runtime'))):
                printError(pkg, 'scl-runtime-package-without-%scl_files')
        if build:
            if not scl_macros.search('\n'.join(self.get_files(spec,'build'))):
                printError(pkg, 'scl-build-package-without-rpm-macros')
    
    def check_scl_spec(self, pkg, spec):
        '''SCL ready spec checks'''
        if not pkg_name.search(spec):
            printWarning(pkg, 'missing-pkg_name-definition')
        if not scl_prefix.search(self.get_name(spec)):
            printError(pkg, 'name-without-scl-prefix')
        elif not scl_prefix_strict.search(self.get_name(spec)):
            printWarning(pkg, 'name-with-scl-prefix-without-condition')
    
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
    
    def get_name(self, text):
        '''For given piece of spec, get the Name of the main package'''
        sname = name.search(text)
        if not sname: return None
        return sname.groups()[0].strip()
    
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
'undeclared-scl',
'SPEC contains %scl* macros, but was not recognized as SCL metapackage or SCL ready package. If this should be SCL metapackage, don\'t forget to define %scl macro. If this should be SCL ready package, run %scl conditionalized %scl_package macro, e.g. %{?scl:%scl_package foo}.'

'no-runtime-in-scl-metapackage',
'SCL metapackage must have runtime subpackage',

'no-build-in-scl-metapackage',
'SCL metapackage must have build subpackage',

'weird-subpackage-in-scl-metapackage',
'Only allowed subpackages in SCL metapackage are build and runtime'

'scl-metapackage-without-scl-utils-build-br',
'SCL metapackage must BuildRequire scl-utils-build',

'scl-build-without-requiring-scl-utils-build',
'SCL runtime package should Require scl-utils-build',

'scl-metapackage-without-%scl_install',
'SCL metapackage must call %scl_install in the %install section',

'noarch-scl-metapackage-with-libdir',
'If "enable" script of SCL metapackage contains %{_libdir}, the package must be arch specific, otherwise it may be noarch',

'scl-main-metapackage-contains-files',
'Main package of SCL metapackage should not contain any files',

'scl-runtime-package-without-%scl_files',
'SCL runtime package must contain %scl_files in %files section',

'scl-build-package-without-rpm-macros',
'SCL build package must contain %{_root_sysconfdir}/rpm/macros.%{scl}-config in %files section',

'missing-pkg_name-definition',
'%{!?scl:%global pkg_name %{name}} is missing in the spec',

'name-without-scl-prefix',
'Name of SCL package must start with %{?scl_prefix}',

'name-with-scl-prefix-without-condition',
'Name of SCL package starts with SCL prefix, but the prefix is not conditional - this won\'t work if the package is build outside of SCL - use %{?scl_prefix} with questionmark'
)
