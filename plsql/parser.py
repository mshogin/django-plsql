import re

__author__ = 'shogin'

class PlSqlParser:

    def get_package_members(self, package_specification):
        """
        Function to get public functions and procedures of PL/SQL package

        Parameters:
        package_specification - PL/SQL package specification

        Return tuple (functions, procedures). Structure of each item of tuple see below
        """
        functions =self._get_functions(package_specification)
        procedures = self._get_procedures(package_specification)
        constants = self._get_constants(package_specification)

        return functions, procedures, constants

    def _get_constants(self, source):
        """
        Function to get information about constants in package specification

        Parameters:
        source     - PL/QSL package specification

        Return array of dictionaries.
        Dictionary structure:
        {
            'name'    : "constant name",
            'value'   : "constant value",
            'oratype' : "constant Oracle type",
        }
        """
        constants = []

        # retrieve all constants from the source
        raw_constants = re.findall('.+?constant.*?:=.*?;', source, re.I | re.S)

        for item in raw_constants:
            item = item.replace('\n', '')
            result = re.search('''
                               (?P<name>\w+)            # constant name
                               \s*constant\s*           # keyword
                               (?P<oratype>[\w\(\)]+)   # constant Oracle type
                               \s*:=\s*
                               (?P<value>.*);           # constant value
                               ''', item, re.I | re.X)
            if result:
                constants.append({
                    'name' : result.group('name'),
                    'oratype' : result.group('oratype'),
                    'value' : result.group('value')
                })

        return constants

    def _get_functions(self, source):
        """
        Function to get information about function in package specification

        Parameters:
        source     - PL/QSL package specification

        Return array of dictionaries.
        Dictionary structure:
        {
            'name'    : "function name",
            'args'    : ["array of dictionaries of function arguments"],
            'oratype' : "function return Oracle type",
        }
        Dictionary of argument representation:
        {
            'name'    : "argument name",
            'type'    : "argument type, one of in, out, in out on None",
            'oratype' : "Oracle type of argument like a NUMBER, SYS_REFCURSOR, etc.",
        """
        functions = []

        # retrieve all functions from the source
        raw_functions = re.findall('(function\s+\w+\s*.+?;)', source, re.S | re.I )

        for item in raw_functions:
            item = item.replace('\n', '')

            # catch procedure name, return type and string of arguments
            result = re.search("""
                               function\s+                         # keyword
                               (?P<name>\w+)\s*                    # function name
                               (?:\((?P<args>.+)?\)\s*)?           # function arguments
                               return\s+(?P<return_oratype>\w+)    # function return Oracle type
                               """, item, re.I | re.S | re.X)

            function = {
                'name'    : result.group('name'),
                'oratype' : result.group('return_oratype'),
                'args'    : []
            }

            if result.group('args'):
                # split string of argument on the parts like  ['arg1 in number', 'arg2 in out varchar2', etc]
                for param in result.group('args').split(','):
                    param = param.strip(' ').lstrip(' ').replace('\s+', ' ')

                    # catch argument name, argument type, argument Oracle type
                    arg = re.search("""
                                    (?P<name>\w+)                                   # argument name
                                    \s+
                                    (?:(?P<type>(?:in\s+out)|(?:in)|(?:out))\s+)?   # argument type (in, out, in out)
                                    (?P<oratype>\w+)                                # argument oracle type
                                    """, param, re.X)
                    function['args'].append({
                        'name'    : arg.group('name'),
                        'type'    : arg.group('type'),
                        'oratype' : arg.group('oratype')
                    })
            functions.append(function)

        return functions

    def _get_procedures(self, source):
        """
        Function to get information about procedures in package specification

        Parameters:
        source     - PL/QSL package specification

        Return array of dictionaries.
        Dictionary structure:
        {
            'name' : "procedure name",
            'args' : ["array of dictionaries of procedure arguments"],
        }
        Dictionary of argument representation:
        {
            'name'    : "argument name",
            'type'    : "argument type, one of in, out, in out on None",
            'oratype' : "Oracle type of argument like a NUMBER, SYS_REFCURSOR, etc.",
        """
        procedures = []

        # retrieve all procedures from the source
        raw_procedures = re.findall('(procedure\s+\w+\s*.+?;)', source, re.S | re.I )

        for item in raw_procedures:
            item = item.replace('\n', '')

            # catch procedure name and string of arguments
            result = re.search("""
                               procedure\s+                     # keyword
                               (?P<name>\w+)\s*                 # procedure name
                               (?:\((?P<args>.+)?\)\s*)?        # procedure arguments
                               """, item, re.I | re.S | re.X)

            procedure = {
                'name' : result.group('name'),
                'args' : []
            }

            if result.group('args'):
                # split string of argument on the parts like  ['arg1 in number', 'arg2 in out varchar2', etc]
                for param in result.group('args').split(','):
                    param = param.strip(' ').lstrip(' ').replace('\s+', ' ')

                    # catch argument name, argument type, argument Oracle type
                    params = re.search("""
                                       (?P<name>\w+)                                   # argument name
                                       \s+
                                       (?:(?P<type>(?:in\s+out)|(?:in)|(?:out))\s+)?   # argument type (in, out, in out)
                                       (?P<oratype>\w+)                                # argument oracle type
                                       """, param, re.X)

                    procedure['args'].append({
                        'name'    : params.group('name'),
                        'type'    : params.group('type'),
                        'oratype' : params.group('oratype')
                    })
            procedures.append(procedure)

        return procedures
