# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.

import unittest

from trytond.tests.test_tryton import install_module, with_transaction
from trytond.pool import Pool
from trytond.exceptions import UserError


class ModelView(unittest.TestCase):
    "Test ModelView"

    @classmethod
    def setUpClass(cls):
        install_module('tests')

    @with_transaction()
    def test_changed_values(self):
        "Test ModelView._changed_values"
        pool = Pool()
        Model = pool.get('test.modelview.changed_values')
        Target = pool.get('test.modelview.changed_values.target')

        record = Model()

        self.assertEqual(record._changed_values, {})

        record.name = 'foo'
        record.target = Target(1)
        record.ref_target = Target(2)
        record.targets = [Target(name='bar')]
        self.assertEqual(record._changed_values, {
                'name': 'foo',
                'target': 1,
                'ref_target': 'test.modelview.changed_values.target,2',
                'targets': {
                    'add': [
                        (0, {'name': 'bar'}),
                        ],
                    },
                })

        record = Model(name='test', target=1, targets=[
                {'id': 1, 'name': 'foo'},
                {'id': 2},
                ], m2m_targets=[5, 6, 7])

        self.assertEqual(record._changed_values, {})

        target = record.targets[0]
        target.name = 'bar'
        record.targets = [target]
        record.m2m_targets = [Target(9), Target(10)]
        self.assertEqual(record._changed_values, {
                'targets': {
                    'update': [{'id': 1, 'name': 'bar'}],
                    'remove': [2],
                    },
                'm2m_targets': [9, 10],
                })

        # change only one2many record
        record = Model(targets=[{'id': 1, 'name': 'foo'}])
        self.assertEqual(record._changed_values, {})

        target, = record.targets
        target.name = 'bar'
        record.targets = record.targets
        self.assertEqual(record._changed_values, {
                'targets': {
                    'update': [{'id': 1, 'name': 'bar'}],
                    },
                })

    @with_transaction(context={'_check_access': True})
    def test_button_access(self):
        'Test Button Access'
        pool = Pool()
        TestModel = pool.get('test.modelview.button')
        Model = pool.get('ir.model')
        Button = pool.get('ir.model.button')
        ModelAccess = pool.get('ir.model.access')
        Group = pool.get('res.group')

        model, = Model.search([('model', '=', 'test.modelview.button')])
        admin, = Group.search([('name', '=', 'Administration')])
        test = TestModel()

        # Without model/button access
        TestModel.test([test])

        # Without read access
        access = ModelAccess(model=model, group=None, perm_read=False)
        access.save()
        self.assertRaises(UserError, TestModel.test, [test])

        # Without write access
        access.perm_read = True
        access.perm_write = False
        access.save()
        self.assertRaises(UserError, TestModel.test, [test])

        # Without write access but with button access
        button = Button(name='test', model=model, groups=[admin])
        button.save()
        TestModel.test([test])

        # Without button access
        ModelAccess.delete([access])
        no_group = Group(name='no group')
        no_group.save()
        button.groups = [no_group]
        button.save()
        self.assertRaises(UserError, TestModel.test, [test])


def suite():
    func = unittest.TestLoader().loadTestsFromTestCase
    suite = unittest.TestSuite()
    for testcase in (ModelView,):
        suite.addTests(func(testcase))
    return suite
