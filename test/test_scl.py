import sys, os
# add rpmlint-scl, rpmlint and rpmlint/tools to PATH
# also add rpmlint-scl/tools, so this keeps working once merged with rpmlint
for directory in ['../rpmlint/tools','../rpmlint','../tools','..']:
    sys.path.insert(0,os.path.join(os.path.dirname(__file__),directory))

# rpmlint's Testing need's TESTPATH
os.environ['TESTPATH'] = os.path.dirname(__file__)


import Testing
import SCLCheck

class TestSCL:
    def test_silent(self):
        '''SCL check on non-SCL spec has to be silent'''
        self.pkg = Testing.getTestedSpecPackage('SpecCheck')
        Testing.startTest()
        SCLCheck.check.check_spec(self.pkg, self.pkg.name)
        assert not len(Testing.getOutput())
