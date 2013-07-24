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

    def test_spec_silent(self):
        '''SCL check on non-SCL spec has to be silent'''
        self.pkg = Testing.getTestedSpecPackage('SpecCheck')
        Testing.startTest()
        # call check_spec() directly, as check() doesn't work with getTestedSpecPackage()
        SCLCheck.check.check_spec(self.pkg, self.pkg.name)
        assert not len(Testing.getOutput())

    def test_binary_silent(self):
        '''SCL check on non-SCL binary RPM has to be silent even with suspicious filename'''
        self.pkg = Testing.getTestedPackage('python3-power')
        Testing.startTest()
        SCLCheck.check.check(self.pkg)
        assert not len(Testing.getOutput())
