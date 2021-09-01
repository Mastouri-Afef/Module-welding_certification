# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
from trytond import backend
from trytond.i18n import gettext
from trytond.model import ModelView, ModelSQL, ModelSingleton, fields
from trytond.model import MultiValueMixin, ValueMixin
from trytond.model.exceptions import AccessError
from trytond.pool import Pool
from trytond.tools.multivalue import migrate_property
from trytond.pyson import Id


welding_sequence = fields.Many2One('ir.sequence', 'Welding Certification Sequence',
    domain=[
        ('sequence_type', '=', Id('welding_certification', 'sequence_type_welding')),
        ],
    help="Used to generate the Welding Certification code.")


class Configuration(ModelSingleton, ModelSQL, ModelView, MultiValueMixin):
    'Welding Certification Configuration'
    __name__ = 'welding_certification.configuration'

    welding_sequence = fields.MultiValue(welding_sequence)


    @classmethod
    def default_welding_sequence(cls, **pattern):
        pool = Pool()
        ModelData = pool.get('ir.model.data')
        try:
            return ModelData.get_id('welding_certification', 'sequence_welding')
        except KeyError:
            return None
    @classmethod
    def create(cls, vlist):
        records = super().create(vlist)
        ModelView._fields_view_get_cache.clear()
        return records

    @classmethod
    def write(cls, *args):
        super().write(*args)
        ModelView._fields_view_get_cache.clear()

    @classmethod
    def delete(cls, records):
        super().delete(records)
        ModelView._fields_view_get_cache.clear()




class _ConfigurationValue(ModelSQL):

    _configuration_value_field = None

    @classmethod
    def __register__(cls, module_name):
        exist = backend.TableHandler.table_exist(cls._table)

        super(_ConfigurationValue, cls).__register__(module_name)
        if not exist:
            cls._migrate_property([], [], [])

    @classmethod
    def _migrate_property(cls, field_names, value_names, fields):
        field_names.append(cls._configuration_value_field)
        value_names.append(cls._configuration_value_field)
        migrate_property(
            'welding_certification.configuration', field_names, cls, value_names,
            fields=fields)


class ConfigurationSequence(_ConfigurationValue, ModelSQL, ValueMixin):
    'Welding Certification Configuration Sequence'
    __name__ = 'welding_certification.configuration.welding_sequence'
    welding_sequence = welding_sequence
    _configuration_value_field = 'welding_sequence'

    @classmethod
    def check_xml_record(cls, records, values):
        return True

