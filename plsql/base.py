import os
import re
from django.template.base import Template
from django.template.context import Context
from dbgate import DBA
from parser import PlSqlParser
import settings

"""
Oracle user_objects column identifiers
"""
PACKAGE_NAME = 0

"""
Ditionary with dependences between Oracle types and cx_Oracle types
"""
ORATYPES = {
    'sys_refcursor' : 'cx_Oracle.CURSOR',
    'raw'           : 'cx_Oracle.BINARY',
    'bfile'         : 'cx_Oracle.BFILE',
    'blob'          : 'cx_Oracle.BLOB',
    'clob'          : 'cx_Oracle.CLOB',
    'date'          : 'cx_Oracle.DATETIME',
    'char'          : 'cx_Oracle.FIXED_CHAR',
    'nchar'         : 'cx_Oracle.FIXED_UNICODE',
    'long row'      : 'cx_Oracle.LONG_BINARY',
    'nclob'         : 'cx_Oracle.NCLOB',
    'number'        : 'cx_Oracle.NUMBER',
    'rowid'         : 'cx_Oracle.ROWID',
    'varchar2'      : 'cx_Oracle.STRING',
    'timestamp'     : 'cx_Oracle.TIMESTAMP',
    'nvarchar2'     : 'cx_Oracle.UNICODE',
}

TEMPLATES_MAP = {
    'sys_refcursor' : 'cursor',
    'raw'           : 'generic',
    'bfile'         : 'generic',
    'blob'          : 'lob',
    'clob'          : 'lob',
    'date'          : 'generic',
    'char'          : 'generic',
    'nchar'         : 'generic',
    'long row'      : 'generic',
    'nclob'         : 'lob',
    'number'        : 'generic',
    'rowid'         : 'generic',
    'varchar2'      : 'generic',
    'timestamp'     : 'generic',
    'nvarchar2'     : 'generic',
}


def render_to_string(template_name, context):
    """
    Function to render parts of python module
    """
    f = open(settings.PLSQL_TEMPLATE_DIR + '/' + template_name)
    template_string = f.read()
    f.close()

    t = Template(template_string, template_string)
    return t.render(context)

class Package(object):
    """
    Class to represent Oracle package
    """
    def __init__(self, info):
        self.name = info[PACKAGE_NAME]
        self.members = []


    def set_members(self, members):
        # Function to set members of package. Member is one of the next: procedure, function, constant
        self.members = members


    def get_py_source(self):
        """
        Function to generate python code of package class
        """
        members = []
        for member in self.members:
            members.append(member.get_py_source())

        return render_to_string("package.html",
            Context({
                'package_name' : self.name.lower(),
                'members' : members
            })
        )

    def __unicode__(self):
        return "Package {0}.".format(self.name)

    def __str__(self):
        return self.__unicode__()


class Function(object):
    """
    Class to generate python function to call Oracle PL/SQL package function
    """
    def __init__(self, name, oratype, parent):
        """
        Constructor.

        Parameters:
        name       - function name
        oratype    - return type for PL/SQL function
        parent     - package
        """
        self.name = name
        self.oratype = oratype
        self.arguments = []
        self.parent = parent

    def add_argument(self, arg):
        # Function to add argument of function
        self.arguments.append(arg)

    def get_py_source(self):
        """
        Function to generate python code
        """

        ctx = Context({
            'name' : self.name,
            'args' : self.arguments,
            'return_type' : ORATYPES[self.oratype.lower()],
            'package_name' : self.parent.name.lower(),
        })

        return render_to_string(
            "function_{0}.html".format(TEMPLATES_MAP[self.oratype]),
            ctx
        )

    def __str__(self):
        return self.__unicode__()

    def __unicode__(self):
        return "Function {0}, oratype = {1}".format(self.name, self.oratype)


class Procedure(Function):
    """
     Class to generate python function to call Oracle PL/SQL package procedure
    """
    def __init__(self, name, parent):
        super(Procedure, self).__init__(name, None, parent)

    def get_py_source(self):
        ctx = Context({
            'name' : self.name,
            'args' : self.arguments,
            'package_name' : self.parent.name.lower(),
            })

        source = render_to_string("procedure.html", ctx)
        return source

    def __unicode__(self):
        return "Procedure {0}".format(self.name)


class Argument(object):
    """
    Class to represent argument of function/procedure
    """
    @staticmethod
    def create(name, type, oratype):
        """
        Factory method to create appropriate argument

        Parameters:
        name - argument name
        type - argument type ( in, out, in out or None)
        oratype - oracle pl/sql data type
        """
        if oratype in ('clob', 'nclob'):
            return ClobArgument(name, type, oratype)
        elif oratype in ('sys_refcursor'):
            return CursorArgument(name, type, oratype)
        else:
            return Argument(name, type, oratype)

    def __init__(self, name, type, oratype):
        # Constructor
        self._name = name
        self.type = type
        self.oratype = oratype

    def name(self):
        return self._name

    def arg_name(self):
        if self.type == 'out':
            return "{0} = None".format(self._name)
        return self._name

    def return_statement(self):
        if self.type and re.match('out', self.type):
            return " {0}".format(self._name)
        return ''

    def after_calling(self):
        if self.type and re.match('out', self.type):
            return "{0} = {0}.getvalue()".format(self._name)

        return ''

    def before_calling(self):
        """
        Template method to construct initial code before colling PLSQL function
        """
        plsql = self.pyora_create_temporary_name()

        plsql += self.cxora_create_variable()

        plsql += self.cxora_set_value()

        plsql += self.pyora_set_origin_name()

        return plsql

    def pyora_create_temporary_name(self) :
        # Generate python code to create new variable with None value
        return """
        {0}_tmp = None
        """.format(self.name())

    def cxora_create_variable(self) :
        # Generate python code to create required type of variable
        return """
        {0}_tmp = cursor.var({1})
        """.format(self.name(), ORATYPES[self.oratype])

    def cxora_set_value(self) :
        # Generate python code to set initial value
        return """
        {0}_tmp.setvalue(0, {0})
        """.format(self.name())

    def pyora_set_origin_name(self) :
        # Generate python code to set created variable origin name
        return """
        {0} = {0}_tmp
        """.format(self.name())

    def __str__(self):
        return self.__unicode__()

    def __unicode__(self):
        return self.name

class ClobArgument(Argument):

    def after_calling(self):
        if self.type and re.match('out', self.type):
            return """
        {0} = {0}.getvalue()
        {0} = {0}.read()
        """.format(self._name)
        return ''

class CursorArgument(Argument):

    def cxora_set_value(self):
        return ''

    def after_calling(self):
        if self.type and re.match('out', self.type):
            return """
        {0} = {0}.getvalue()
        {0} = Cursor({0})
        """.format(self._name)
        return ''

class Constant(object):
    def __init__(self, name, value):
        self._name = name
        self._value = value

    def get_py_source(self):
        return "{0} = {1}".format(self._name, self._value)


class Schema():
    def __init__(self, connection):
        self.dba = DBA(connection)
        self.parser = PlSqlParser()
        self.fs = SchemaIO()
        self.packages = []

    def generate_packages(self):
        """Dump PLSQL packages to filesystem"""
        self.fs.check_packages_storage()
        self._save_packages()

    def _save_packages(self):
        """
        Get packages, parse package specification, generate py and save
        """
        raw_packages = self.dba.get_packages()

        for package in raw_packages:
            package = Package(package)
            if package.name in settings.PLSQL_PACKAGES:
                # parse package to get package members
                members = self._get_package_members(package)
                package.set_members(members)
                self.packages.append(package)

                # save package to fs
                self.fs.save_package(
                    package.name.lower(),
                    package.get_py_source()
                )

    def _get_package_members(self, package):
        """
        Function to get package members

        Parameters:
        package   - instance of Package class
        """
        source = self.dba.get_spec_source(package.name)

        functions, procedures, constants = self.parser.get_package_members(source)

        members = []
        for proc in procedures:
            # create Procedure
            member = Procedure(proc['name'], package)
            for arg in proc['args']:
                member.add_argument(
                    Argument.create(arg['name'], arg['type'], arg['oratype'])
                )
            members.append(member)

        for func in functions:
            # create Function
            member = Function(func['name'], func['oratype'], package)
            for arg in func['args']:
                member.add_argument(
                    Argument.create(arg['name'], arg['type'], arg['oratype'])
                )
            members.append(member)

        for const in constants:
            members.append(Constant(const['name'], const['value']))

        return members

class SchemaIO(object):
    def check_packages_storage(self):
        """
        Create filesystem structure.
        PLSQL_SCHEMA_ROOT is the root folder for each schema
        """
        if not os.path.exists(settings.PLSQL_SCHEMA_ROOT):
            os.makedirs(settings.PLSQL_SCHEMA_ROOT)
            self._make_initpy(settings.PLSQL_SCHEMA_ROOT)

        if not os.path.exists(settings.PLSQL_SCHEMA_ROOT + settings.ORA_SCHEMA):
            os.makedirs(settings.PLSQL_SCHEMA_ROOT + settings.ORA_SCHEMA)
            self._make_initpy(settings.PLSQL_SCHEMA_ROOT + settings.ORA_SCHEMA)

    def save_package(self, fname, content):
        """
        Save plsql package stub module
        """
        f = open(settings.PLSQL_SCHEMA_ROOT + settings.ORA_SCHEMA + '/' + fname + '.py', 'w')
        f.write(content)
        f.close()


    def _make_initpy(self, root):
        f = open(root + '/__init__.py', 'w')
        f.close()