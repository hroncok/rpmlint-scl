import sys, os
# add rpmlint-scl, rpmlint and rpmlint/tools to PATH
# also add rpmlint-scl/tools, so this keeps working once merged with rpmlint
for directory in ['../rpmlint/tools','../rpmlint','../tools','..']:
    sys.path.insert(0,os.path.join(os.path.dirname(__file__),directory))

# rpmlint's Testing needs TESTPATH
os.environ['TESTPATH'] = os.path.dirname(__file__)


import Testing
import SCLCheck

class TestSCL:
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
