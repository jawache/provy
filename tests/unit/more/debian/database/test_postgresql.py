from contextlib import contextmanager
from unittest import TestCase

from mock import MagicMock, patch
from nose.tools import istest

from provy.more.debian.database.postgresql import PostgreSQLRole


class PostgreSQLRoleTestCase(TestCase):
    def setUp(self):
        self.role = PostgreSQLRole(prov=None, context={})
        self.execute = MagicMock(side_effect=self.return_execution_result)
        self.execution_results = []
        self.execution_count = -1
        self.assertion_count = -1

    def successful_execution(self, *args, **kwargs):
        return self.execution(True, *args, **kwargs)

    def failed_execution(self, *args, **kwargs):
        return self.execution(False, *args, **kwargs)

    def return_execution_result(self, *args, **kwargs):
        self.execution_count += 1
        return self.execution_results[self.execution_count]

    @contextmanager
    def execution(self, return_value, *args, **kwargs):
        count = self.execution_count
        self.execution_results.append(return_value)
        with patch('provy.core.roles.Role.execute', self.execute) as mock_execute:
            yield
            self.assert_executed(*args, **kwargs)

    def assert_executed(self, *args, **kwargs):
        name, e_args, e_kwargs = self.execute.mock_calls[self.assertion_count]
        self.assertion_count -= 1
        self.assertEqual(e_args, args)
        self.assertEqual(e_kwargs, kwargs)


class PostgreSQLRoleTest(PostgreSQLRoleTestCase):
    @istest
    def nested_test(self):
        """This test is to guarantee that the execution results go from the outer to the inner context managers."""
        with self.successful_execution("1"), self.failed_execution("2"):
            self.assertTrue(self.execute("1"))
            self.assertFalse(self.execute("2"))

    @istest
    def creates_a_user_prompting_for_password(self):
        with self.successful_execution("createuser -P foo", stdout=False):
            self.assertTrue(self.role.create_user("foo"))

    @istest
    def creates_a_user_without_prompting_for_password(self):
        with self.successful_execution("createuser foo", stdout=False):
            self.assertTrue(self.role.create_user("foo", ask_password=False))

    @istest
    def drops_the_user(self):
        with self.successful_execution("dropuser foo", stdout=False):
            self.assertTrue(self.role.drop_user("foo"))

    @istest
    def verifies_that_the_user_exists(self):
        with self.successful_execution("psql -tAc \"SELECT 1 FROM pg_roles WHERE rolname='foo'\"", stdout=False):
            self.assertTrue(self.role.user_exists("foo"))

    @istest
    def verifies_that_the_user_doesnt_exist(self):
        with self.failed_execution("psql -tAc \"SELECT 1 FROM pg_roles WHERE rolname='bar'\"", stdout=False):
            self.assertFalse(self.role.user_exists("bar"))

    @istest
    def creates_user_if_it_doesnt_exist_yet(self):
        with self.failed_execution("psql -tAc \"SELECT 1 FROM pg_roles WHERE rolname='bar'\"", stdout=False):
            with self.successful_execution("createuser -P bar", stdout=False):
                self.assertTrue(self.role.ensure_user("bar"))

    @istest
    def doesnt_create_user_if_it_already_exists(self):
        with self.successful_execution("psql -tAc \"SELECT 1 FROM pg_roles WHERE rolname='baz'\"", stdout=False):
            self.assertTrue(self.role.ensure_user("baz"))

    @istest
    def creates_a_database(self):
        with self.successful_execution("createdb foo"):
            self.assertTrue(self.role.create_database("foo"))

    @istest
    def creates_a_database_with_a_particular_owner(self):
        with self.successful_execution("createdb foo -O bar"):
            self.assertTrue(self.role.create_database("foo", owner="bar"))

    @istest
    def drops_the_database(self):
        with self.successful_execution("dropdb foo"):
            self.assertTrue(self.role.drop_database("foo"))
