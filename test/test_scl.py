import sys, os
# add rpmlint-scl, rpmlint and rpmlint/tools to PATH
# also add rpmlint-scl/tools, so this keeps working once merged with rpmlint
for directory in ['../rpmlint/tools','../rpmlint','../tools','..']:
    sys.path.insert(0,os.path.join(os.path.dirname(__file__),directory))

# rpmlint's Testing needs TESTPATH
os.environ['TESTPATH'] = os.path.dirname(__file__)


import Testing
import SCLCheck

class TestSCL(object):
    '''Tests of Software Collections checks'''

    def _spec_test_output(self, spec):
        '''Wrapper that checks spec file and returns output'''
        pkg = Testing.getTestedSpecPackage(spec)
        Testing.startTest()
        # call check_spec() directly, as check() doesn't work with getTestedSpecPackage()
        SCLCheck.check.check_spec(pkg, pkg.name)
        return Testing.getOutput()

    def _rpm_test_output(self, rpm):
        '''Wrapper that checks RPM package and returns output'''
        pkg = Testing.getTestedPackage(rpm)
        Testing.startTest()
        SCLCheck.check.check(pkg)
        return Testing.getOutput()

    def test_nonscl_spec_silent(self):
        '''SCL check on non-SCL spec has to be silent'''
        assert not self._spec_test_output('spec/SpecCheck')

    def test_nonscl_binary_silent(self):
        '''SCL check on non-SCL binary RPM has to be silent even with suspicious filename'''
        assert not self._rpm_test_output('binary/python3-power')

    def test_bunch_of_scl_source_rpms(self):
        '''A bunch of testing source RPM packages using SCL
        Assuming they are all OK and except silent output
        While adding more checks, this might change'''
        for package in ['nodejs010-1', 'nodejs010-nodejs-0.10.3', 'nodejs010-nodejs-forever']:
            assert not self._rpm_test_output(os.path.join('source',package))

    def test_bunch_of_scl_binary_rpms(self):
        '''A bunch of testing binary RPM packages using SCL
        Assuming they are all OK and except silent output
        While adding more checks, this might change'''
        for package in ['nodejs010-runtime', 'nodejs010-nodejs-0.10.3', 'nodejs010-nodejs-oauth']:
            assert not self._rpm_test_output(os.path.join('binary',package))

    def test_correct_nodejs(self):
        '''Tests probably correct nodejs.spec and nodejs010.spec'''
        assert not self._spec_test_output('spec/nodejs-good')
        assert not self._spec_test_output('spec/nodejs010')

    def test_nobuild(self):
        '''Tests SCL metapackage without build subpackage'''
        out = self._spec_test_output('spec/nodejs010-nobuild')
        assert len(out) == 1
        assert 'no-build-in-scl-metapackage' in out[0]

    def test_noruntime(self):
        '''Tests SCL metapackage without runtime subpackage'''
        out = self._spec_test_output('spec/nodejs010-noruntime')
        assert len(out) == 2
        out = '\n'.join(out)
        assert 'no-runtime-in-scl-metapackage' in out
        assert 'scl-main-metapackage-contains-files' in out

    def test_missing_requires(self):
        '''Tests SCL metapackage without scl-utils-build (B)Rs'''
        out = self._spec_test_output('spec/nodejs010-missing-requires')
        assert len(out) == 2
        out = '\n'.join(out)
        assert 'scl-metapackage-without-scl-utils-build-br' in out
        assert 'scl-build-without-requiring-scl-utils-build' in out

    def test_alien_subpackage(self):
        '''Tests SCL metapackage with extra subpackage'''
        for diff in ['','-n']:
            out = self._spec_test_output('spec/nodejs010-alien-subpackage'+diff)
            assert len(out) == 1
            assert 'weird-subpackage-in-scl-metapackage' in out[0]
            assert 'hehe' in out[0]
    
    def test_nosclinstall(self):
        '''Tests SCL metapackage that doesn't call %scl_install'''
        out = self._spec_test_output('spec/nodejs010-nosclinstall')
        assert len(out) == 1
        assert 'scl-metapackage-without-%scl_install' in out[0]
    
    def test_noarch(self):
        '''Tests noarch SCL metapackages (not) containing %{_libdir}'''
        assert not self._spec_test_output('spec/nodejs010-noarch-good')
        out = self._spec_test_output('spec/nodejs010-noarch-libdir')
        assert len(out) == 1
        assert 'noarch-scl-metapackage-with-libdir' in out[0]
    
    def test_badfiles(self):
        '''Tests SCL metapackage %files section checks'''
        out = self._spec_test_output('spec/nodejs010-badfiles')
        assert len(out) == 3
        out = '\n'.join(out)
        assert 'scl-main-metapackage-contains-files' in out
        assert 'scl-runtime-package-without-%scl_files' in out
        assert 'scl-build-package-without-rpm-macros' in out
        
    def test_undeclared(self):
        '''Tests SCL specs withou %scl definition or %scl_package calls'''
        for spec in ['nodejs010','nodejs']:
            out = self._spec_test_output('spec/'+spec+'-undeclared')
            assert len(out) == 1
            assert 'undeclared-scl' in out[0]
