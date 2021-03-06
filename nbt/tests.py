from nbt import *
import unittest

class ReadWriteTest(unittest.TestCase):
    # test that we can read the test file correctly
    def readBigTest(self):
        mynbt = NBTFile("Bigtest.py")
        self.assertTrue(mynbt.file != None)
    
    # test that we can write the test file correctly
    def writeBigTest(self):
        mynbt = NBTFile("Bigtest.py")
        mynbt.write_file("output file.nbt")
        self.assertTrue(True)
                
class TreeManipulationTest(unittest.TestCase):
    
    def setUp(self):
        self.nbtfile = NBTFile()
    
    def testRootNodeSetup(self):
        self.nbtfile.name = TAG_String("Hello World")
        self.assertEqual(self.nbtfile.name.value, "Hello World")
        
    def testTagAdd(self):
        self.testRootNodeSetup()
        #try a simple byte tag
        self.nbtfile.append(TAG_Byte(name="TestByte", value=10))
        self.assertEqual(self.nbtfile["TestByte"].value, 10)
        #etcetera..... will finish later
        
    def tearDown(self):
        del self.nbtfile
        
if __name__ == '__main__':
    unittest.main()
