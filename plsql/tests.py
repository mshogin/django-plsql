import os
import re
import sys
import unittest
from importlib import import_module

import settings
from base import Schema
from parser import PlSqlParser
from dbgate import OraConnection

sys.path.append(settings.PLSQL_SCHEMA_ROOT)

TEST_PACKAGE = 'plsqlparsertestpackage'

class TestParser(unittest.TestCase):
    """
    Class implements tests for PLSQL parser
    """
    def setUp(self):
        self.fixtures = {}
        for item in os.listdir(os.path.dirname(__file__) + '/fixture'):
            match = re.match('(\w+)\.pkg', item)
            if match:
                f = open(os.path.dirname(__file__) + '/fixture/' + item)
                self.fixtures[match.group(1)] = f.read()
                f.close()

        self.parser = PlSqlParser()

    def test_parse_plsqlparsertestpackage(self):
        """
        Tests to parse PL/SQL package specification
        """
        functions, procedures, constants = self.parser.get_package_members(
            self.fixtures[TEST_PACKAGE]
        )

        self.assertEquals(len(functions), 12)
        self.assertEquals(len(procedures), 1)
        self.assertEquals(len(constants), 3)


class TestCreator(unittest.TestCase):
    """
    Class implements test to call functions and procedures
    """
    def setUp(self):
        self.connection = OraConnection.connect(
            settings.ORA_SID,
            settings.ORA_SCHEMA,
            settings.ORA_PASSWORD
        )
        self._create_package()

        # dump packages
        self.schema = Schema(self.connection)
        self.schema.generate_packages()

        # import packages modules to runtime
        module = import_module(settings.ORA_SCHEMA + '.' + TEST_PACKAGE)
        self.package = getattr(module, TEST_PACKAGE)
        self.package.connection = self.connection

    def _create_package(self):
        """
        Function to create test package in the schema
        """
        f = open(os.path.dirname(__file__) + '/fixture/' + TEST_PACKAGE + '.pkg')
        package_spec = f.read()
        f.close()

        f = open(os.path.dirname(__file__) + '/fixture/' + TEST_PACKAGE + '_body.pkg')
        package_body = f.read()
        f.close()

        cursor = self.connection.cursor()
        cursor.execute(package_spec)
        cursor.execute(package_body)


    def test_package_Empty_Arguments_Return_Clob(self):

        result = self.package.Empty_Arguments_Return_Clob()

        self.assertEqual(result, self.package.GC_CLOB_FOR_RETURN)

    def test_package_Empty_Arguments_Return_Number(self):

        result = self.package.Empty_Arguments_Return_Number()

        self.assertEqual(result, self.package.GC_NUMBER_FOR_RETURN)

    def test_package_Empty_Arguments_Return_String(self):

        result = self.package.Empty_Arguments_Return_String()

        self.assertEqual(result, self.package.GC_VARCHAR2_FOR_RETURN)

    def test_package_Empty_Arguments_Return_Cursor(self):

        cursor = self.package.Empty_Arguments_Return_Cursor()

        row = cursor.next()
        self.assertIsNotNone(row)
        self.assertEqual(row['val_number'], self.package.GC_NUMBER_FOR_RETURN)
        self.assertEqual(row['val_varchar'], self.package.GC_VARCHAR2_FOR_RETURN)

    def test_package_Return_Empty_Cursor(self):

        cursor = self.package.Return_Empty_Cursor()

        row = cursor.next()
        self.assertIsNone(row)

    def test_package_Return_Big_Cursor(self):

        cursor = self.package.Return_Big_Cursor()

        row = cursor.next()
        self.assertIsNotNone(row)
        while row:
            self.assertEqual(row['val_number'], self.package.GC_NUMBER_FOR_RETURN)
            self.assertEqual(row['val_varchar'], self.package.GC_VARCHAR2_FOR_RETURN)
            row = cursor.next()

    def test_package_In_Number_Return_Number(self):

        result = self.package.In_Number_Return_Number(1)

        self.assertEqual(result, 1)

    def test_package_In_Varchar2_Return_Varchar2(self):

        result = self.package.In_Varchar2_Return_Varchar2('test')

        self.assertEqual(result, 'test')

    def test_package_In_Complex_Return_Cursor(self):

        result = self.package.In_Complex_Return_Cursor(1, 'test', 'test')

        row = result.next()
        self.assertEqual(row['val_number'], 1)
        self.assertEqual(row['val_varchar'], 'test')
        self.assertEqual(row['val_clob'], 'test')

    def test_package_Out_Number_Return_Number(self):
        o_number, o_varchar2, o_clob, o_cursor = None, None, None, None

        result, o_number = self.package.Out_Number_Return_Number(o_number)

        self.assertEqual(result, self.package.GC_NUMBER_FOR_RETURN)
        self.assertEqual(o_number, self.package.GC_NUMBER_FOR_RETURN)

    def test_package_Out_Arguments_Return_Cursor(self):
        o_number, o_varchar2, o_clob, o_cursor = None, None, None, None

        result, o_number, o_varchar2, o_clob, o_cursor = \
            self.package.Out_Arguments_Return_Cursor(o_number, o_varchar2, o_clob, o_cursor)

        self.assertEqual(o_number, self.package.GC_NUMBER_FOR_RETURN)
        self.assertEqual(o_varchar2, self.package.GC_VARCHAR2_FOR_RETURN)
        self.assertEqual(o_clob, self.package.GC_CLOB_FOR_RETURN)
        row = o_cursor.next()
        self.assertEqual(row['val_number'], self.package.GC_NUMBER_FOR_RETURN)

    @unittest.case.skip("Don't know how to bind in out varchar2")
    def test_package_In_Out_Arguments_Return_Cursor(self):

        o_number, o_varchar2, o_clob, o_cursor = None, None, None, None

        result, o_number, o_varchar2, o_clob =\
        self.package.In_Out_Arguments_Return_Cursor(1, 'a', 'a')

        self.assertEqual(o_number, 1 + self.package.GC_NUMBER_FOR_RETURN)
        self.assertEqual(o_varchar2, 'a' + self.package.GC_VARCHAR2_FOR_RETURN)
        self.assertEqual(o_clob, 'a' + self.package.GC_CLOB_FOR_RETURN)

    def test_procedure_In_Args_Out_Cursor(self):
        o_cursor = self.package.In_Args_Out_Cursor(1, 'a', 'b')

        row = o_cursor.next()
        self.assertIsNotNone(row)

if __name__ == "main":
    unittest.main()