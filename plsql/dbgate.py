import os
import re
import cx_Oracle

class OracleHomeError(EnvironmentError):
    pass

class FileNotFoundError(StandardError):
    pass

class SIDNotFound(StandardError):
    pass

class TnsOra(object):
    TNSNAMES_PATH = '/network/admin/tnsnames.ora'

    def __init__(self):
        self.services = {}
        self.initialize()

    def initialize(self):
        """
        Function tries to find tnsnames.ora and retrieve services
        """
        if not os.environ['ORACLE_HOME']:
            raise OracleHomeError()

        if not os.path.exists(os.environ['ORACLE_HOME'] + TnsOra.TNSNAMES_PATH):
            raise FileNotFoundError()

        f = open(os.environ['ORACLE_HOME'] + TnsOra.TNSNAMES_PATH, 'r')

        # Flag that it's stated service description
        service_begin = False
        # array of service descriptions
        service = list()

        service_name = ''

        for line in f.readlines():
            # Skip comments and new line symbols
            if re.match('^#', line) or re.match('\n', line):
                continue

            line = line.replace('\n', '')

            # try to find start of service description
            result = re.match('\s*(\w+)\s*=', line)
            if result:
                # say that service description was started
                service_begin = True

                # save previous service descriprion
                if len(service) > 0:
                    self.services[service_name] = ''.join(service)
                    service = []

                # save service name
                service_name = result.group(1)
            # skip first line of service description and save next lines
            elif service_begin:
                service.append(line)

        # save last service description
        if len(service) > 0:
            self.services[service_name] = ''.join(service)

        f.close()

    def get(self, sid):
        """
        Function to get connection string by service name

        Parameter:
        sid      - oracle service identifier
        """
        if not self.services.has_key(sid):
            raise SIDNotFound()
        return self.services[sid]

class OraConnection(cx_Oracle.Connection):
    @staticmethod
    def connect(sid, login, password):
        tns = TnsOra()
        service_description = tns.get(sid)
        connection_string = "{0}/{1}@{2}".format(login, password, service_description)

        return OraConnection(connection_string)


class DBA(object):
    """
    Class implements database access
    """
    def __init__(self, connection):
        self.connection = connection

    def get_packages(self):
        """
        Retrieve all user's plsql packages
        """
        cursor = self.connection.cursor()

        raw = cursor.execute("""
            select *
              from user_objects
             where object_type = 'PACKAGE'
            """)

        packages = raw.fetchall()
        cursor.close()

        return packages

    def get_spec_source(self, package_name):
        """
        Retrieve plsql package specification
        """
        cursor = self.connection.cursor()

        raw = cursor.execute("""
            select text
              from user_source
             where name = :name
               and type = 'PACKAGE'
        """, {':name' : package_name})

        raw_source = raw.fetchall()
        cursor.close()

        source = ''
        for line in raw_source:
            source += line[0]

        return source