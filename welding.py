# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.model import Workflow, ModelView, ModelSQL, fields, DeactivableMixin,MultiValueMixin, sequence_ordered, Unique, Exclude
from trytond.transaction import Transaction
from trytond.pyson import Eval, If
from trytond.pool import Pool
from trytond.wizard import Wizard, StateTransition, StateView, Button, StateReport,StateAction
from trytond.report import Report
from os import path
from sql.operators import Concat, Equal
from sql.conditionals import Coalesce
from sql import Literal
import datetime
import numpy as np
from trytond.i18n import gettext
from trytond.model.exceptions import AccessError
from trytond.exceptions import UserError
from sql.functions import Round
STATES = {
    'readonly': Eval('state') != 'draft',
    }
DEPENDS = ['state']
class SchweißanweisungWps(Workflow, ModelSQL, ModelView):
    'Schweißanweisung WPS'
    __name__ = 'welding.schweißanweisung_wps'
    
    code = fields.Char('WPS-Nr', required=True, select=True,
        states={
            'readonly': Eval('code_readonly', True),
            },
        depends=['code_readonly'],
        help="The unique identifier of the party.")
    code_readonly = fields.Function(fields.Boolean('Code Readonly'),
        'get_code_readonly')

    erzeugnis = fields.Many2One('welding.erzeugnis', 'Erzeugnis')
    geeigneter_schweisser = fields.Many2One('welding.iso96061', 'Geeigneter Schweisser',
              help="Fügen Sie den Schweißperson aus dem Prüfungsbescheinigung nach EN ISO 9606-1")

    pendeh = fields.Char('z.B : Pendeh(max, Raupenbreite)')
    amplit = fields.Char('(Amplit,Frequ, Verweilzeit)')
    title = fields.Selection([
        ('schweißanweisung_wps', 'Schweißanweisung (WPS)'),
        ('vorläufig_schweißanweisung', 'vorläufige Schweißanweisung (pWPS) '),
        ('preliminary_wps', 'preliminary WPS (pWPS)'),
        ('Welding_procedure_specification_wps', 'Welding procedure specification (WPS)'),
        ('Welding_procedure_specification', 'Welding procedure specification'),
    ],"Title", select=True)
    
    grundwerkstoff1_nummer = fields.Function(fields.Char(
                "Grundwerkstoff1 Nummer",
                states={
                'invisible': ~Eval('grundwerkstoff1_nummer'),
                }, depends=['grundwerkstoff1']),'on_change_with_grundwerkstoff1_nummer')    
    grundwerkstoff2_nummer = fields.Function(fields.Char(
                "Grundwerkstoff2 Nummer",
                states={
                'invisible': ~Eval('grundwerkstoff2_nummer'),
                }, depends=['grundwerkstoff2']), 'on_change_with_grundwerkstoff2_nummer')
    einzelheiten_pulsschweissen = fields.Char('Einzelheiten für das Pulsschweißen')
    dike_des_schweißgutes = fields.Char('Dike des Schweißgutes [mm]',states={
    'invisible': Eval('nahtart').in_(['FW', 'CW', 'AS']),
    }, depends=['nahtart'])
    kehlnahtdicke = fields.Float('Kehlnahtdicke a [mm]',        
    states={
    'invisible': 
        (Eval('nahtart') == 'BW')
    }, depends=['nahtart'])
    amplit1 = fields.Char('(Amplit,Frequ, Verweilzeit)')
    amplit2 = fields.Char('(Amplit,Frequ, Verweilzeit)')
    stromkontaktrohrabstand = fields.Char('Stromkontaktrohrabstand[mm]')
    einzelheiten_plasmaschweissen = fields.Char('Einzelheiten plasmaschweißen')
    brenneranstellwinkel = fields.Char('Brenneranstellwinkel [Grad]')
    separation = fields.Char('Schweißplan')
    gestaltung = fields.Char('Gestaltung der Verbindung')
    schweissfolgen = fields.Char('Schweißfolgen')
    lines = fields.One2Many('welding.schweißanweisung_wps.einzelheiten_schweißenn','schweißanweisung_wps','Einzelheiten für das Schweißen',
        help="Die verschiedenen  des Einzelheiten für das Schweißen.")
    weitere_info=fields.Char('Weitere Informationen ¹)')
    sondervorschriften_info = fields.Char('Sondervorschriften für Trocknung')
    schutzgas_info = fields.Char('Schutzgas')
    schutzgas_info1 = fields.Char('Schutzgas-/Schweißpulverbezeichnung')
    wurzelschutz_info = fields.Char('Wurzelschutz')
    gasdurchflussmenge = fields.Char('Gasdurchflussmenge [l/min]')
    wolframelektrodenart_info = fields.Char('Wolframelektrodenart/Durchmesser')
    einzelheiten_info = fields.Char('Einzelheiten über Ausfugen/Badsicherung')
    vorwärmtemperatur_info = fields.Char('Vorwärmtemperatur')
    zwischenlagentemperatur_info = fields.Char('Zwischenlagentemperatur')
    bereich=fields.Char('Bereich')
    wasserstoffarm_info = fields.Char('Wasserstoffarmglühen')
    haltetemperatur = fields.Char('Haltetemperatur')
    wärmenachbehandlung = fields.Char('Wärmenachbehandlung')
    aufheiz = fields.Char('Aufheiz- und Abkühlungsraten ¹)')
    zeit = fields.Char('Zeit, Temperatur, Verfahren')
    prozess_iso4063_info=fields.Function(fields.Char(" Prozess Iso 4063"),'on_change_with_prozess_iso4063_info')
    fm0 = fields.Char('FM?')
    fabrikat0 = fields.Char('Fabrikat                            ')
    zulassung = fields.Char('Zulassung, Bemerkungen')
    szi_1 = fields.Many2One('welding.szi_data', 'SZ1=', ondelete='CASCADE', select=True)
    szi_2 = fields.Many2One('welding.szi_data', 'SZ2=', ondelete='CASCADE', select=True)
    szi_3 = fields.Many2One('welding.szi_data', 'SZ3=', ondelete='CASCADE', select=True)
    fm = fields.Function(fields.Char('FM?'),'on_change_with_fm')
    fabrikat = fields.Function(fields.Char('Fabrikat'),'on_change_with_fabrikat')
    bemerkung = fields.Char('Zulassung, Bemerkungen')
    fm1 = fields.Function(fields.Char('FM?'),'on_change_with_fm1')
    fabrikat1 = fields.Function(fields.Char('Fabrikat'),'on_change_with_fabrikat1')
    bemerkung1 = fields.Char('Zulassung, Bemerkungen')
    fm2 = fields.Function(fields.Char('FM?'),'on_change_with_fm2')
    fabrikat2 = fields.Function(fields.Char('Fabrikat'),'on_change_with_fabrikat2')
    bemerkung2 = fields.Char('Zulassung, Bemerkungen')
    rechts_bild = fields.Function(fields.Char("rechts bild "),'on_change_with_rechts_bild')
    empfehlung =fields.Function(fields.Char("Empfehlung"), 'on_change_with_empfehlung')
    einzelheiten=fields.Text('Einzelheiten der Fügenvorbereitung')
    intern_nr=fields.Char('Int-Nr')
    formular = fields.Selection([
        ('WPS-1S', 'WPS-1S|EN ISO 15609-1, Lichtbogenschw'),
        ('WPS-31', 'WPS-31|EN ISO 15609-2, Gasschweißen'),
        ('ASME', 'ASME|BPVC, Section IX, QW-482'),
    ], 'Formular',select=True)
    wpqnr = fields.Many2One('welding.wpqr_nr', 'WPQR-Nr', required=True,
        select=True)
    clss = fields.Many2One('welding.class', 'Class', ondelete='CASCADE', select=True)
    prozess = fields.Many2One('welding.process_iso4063', 'Prozess:ISO 4063-', ondelete='CASCADE', select=True)
    tropfenübergang = fields.Many2One('welding.tropfenuebergang', 'Tropfenübergang', ondelete='CASCADE', select=True )
    schweißposition = fields.Many2One('welding.schweissposition_iso6947', 'Schweißposition ISO 6947-',required=True,
     ondelete='CASCADE', select=True)
    naht_nr = fields.Function(fields.Char('Naht-Nr. nach EN 15085-3'),'on_change_with_naht_nr')
    schweißzusatz_info = fields.Many2One('welding.schweißzusatz', 'Schweißzusatz', required=True,
        select=True)
    list_gas = fields.Many2One('welding.list_gas_mischgase', 'List gas und mischgase', ondelete='CASCADE', select=True)
    list_gas1 = fields.Many2One('welding.list_gas_mischgase', 'List gas und mischgase', ondelete='CASCADE', select=True)
    list_gas2 = fields.Char('Schutzgas')
    list_gas3 = fields.Char('Wurzelschutz')
    grundwerkstoff1 = fields.Many2One('welding.grundwerkstoff_properties', 'Grundwerkstoff 1',required = True, ondelete='CASCADE', select=True)
    grundwerkstoff2 = fields.Many2One('welding.grundwerkstoff_properties', 'Grundwerkstoff 2',required = True, ondelete='CASCADE', select=True)
    wolframelektrodenart = fields.Many2One('welding.wolframelektrodenart_data', 'Wolframelektrodenart/Durchmesser',
     ondelete='CASCADE', select=True)
    wolframelektrodenart2 = fields.Many2One('welding.wolframelektrodenart2_properties', 'Wolframelektrodenart/Durchmesser', 
    ondelete='CASCADE', select=True)
    fugenbearbeitung = fields.Selection([
        ('Bush or Grind as necessary', 'Bush or Grind as necessary'),
        ('Nahtvorbereitung durch Laserschnitt', 'Nahtvorbereitung durch Laserschnitt'),
        ('Plasmaschneiden', 'Plasmaschneiden'),
        ('RP-Schweißmaschine', 'RP-Schweißmaschine'),
    ], 'Fugenbearbeitung',select=True)
    mechanisierungsgrad = fields.Selection([
        ('manuell', 'manuell'),
       ('teilmechanisch', 'teilmechanisch'),
        ('vollmechanisch', 'vollmechanisch'),
        ('automatisch', 'automatisch'),
    ], 'Mechanisierungsgrad',select=True)
    produktform= fields.Selection([
        ('P/P', 'P/P (Blech/Blech)'),
        ('T/P', 'T/P (Rohr/Blech)'),
        ('T/T', 'T/T (Rohr/Rohr)'),
    ], 'Produktform',select=True)
    nahtart= fields.Selection([
        ('BW', 'BW (Stumpfnaht/butt weld)'),
        ('FW', 'FW (Kehlnaht/fillet weld)'),
        ('CW', 'CW (Ecknaht/ corner weld)'),
        ('AS', 'AS Auftragschweißen'),
    ], 'Nahtart',select=True)
    nahtform = fields.Selection([
        ('3 HY', '3 HY'),
        ('3 HY/a2', '3 HY/a2'),
        ('4 HY/a3', '4 HY/a3'),
        ('5 HV', '5 HV'),
        ('5 HY', '5 HY'),
        ('5 V mG', '5 V mG'),
        ('6 HY', '6 HY'),
        ('8 V', '8 V'),
        ('8 V mG', '8 V mG'),
        ('a 3', 'a 3'),
        ('T-Rohr,O', 'T-Rohr,O'),
    ], 'Nahtform',select=True)
    nahtnr = fields.Char('Naht-Nr')
    revision = fields.Float('Revision')
    projekt_nr = fields.Char('Projekt-Nr')
    zeichn_nr = fields.Char('Zeichn-Nr')
    ort = fields.Char('Ort')
    falls_gefordert = fields.Char('¹)falls gefordert')
    name_datum_und_unterschrift = fields.Char('Name,Datum und Unterschrift') 
    name_datum_und_unterschrift2 = fields.Char('Name,Datum und Unterschrift')
    prüfer_oder_prüfstelle = fields.Char('Prüfer oder Prüfstelle') 
    belegnr = fields.Function(fields.Char("Beleg-Nr",
            help="Der Belegnr, der die allgemeinen Eigenschaften definiert  "),'on_change_with_belegnr')
    hersteller = fields.Char('Hersteller')
    werkstuckdicke1 = fields.Integer('Werkstückdicke t[mm]',
            domain=[
            ('werkstuckdicke1', '>=', 0),
            ])
    werkstuckdicke2 = fields.Integer('/')
    aussendurchmesser1 = fields.Integer('Außendurchmesser D[mm]',
            domain=[
            ('aussendurchmesser1', '>=', 0),
            ])
    aussendurchmesser2 = fields.Integer('/')
    photo = fields.Binary("Photo")
    logo_company = fields.Binary("Logo", readonly = True)
    skizze_info = fields.Many2One('welding.bilds_properties', '(Skizze)¹)', ondelete='CASCADE',select=True)
    schweißfolgen_data = fields.Many2One('welding.schweißfolgen_properties', 'Schweißfolgen Data)', ondelete='CASCADE',select=True)
    bild =fields.Function(fields.Binary("B_kizze",required=True), 'on_change_with_bild')
    state = fields.Selection([
            ('draft', 'Draft'),
            ('confirmed', 'Confirmed'),
            ('canceled', 'Cancelled'),
            ], 'State', required=True, readonly=True, select=True)
    @classmethod
    def __setup__(cls):
        super(SchweißanweisungWps, cls).__setup__()
        t = cls.__table__()
        cls._order.insert(1, ('id', 'DESC'))
        cls._sql_constraints += [
            ('schweißanweisung_code_unique', Unique(t,t.geeigneter_schweisser,t.code),
            'welding_certification.msg_schweißanweisung_code_unique'),
            ]
        cls._transitions |= set((
                ('draft', 'confirmed'),
                ('draft', 'canceled'),
                ('confirmed', 'canceled'),
                ('canceled', 'draft'),
                ))    
        cls._buttons.update({
                'cancel': {
                    'invisible': Eval('state') == 'canceled',
                    'icon': 'tryton-cancel',
                    },
                'draft': {
                    'invisible': Eval('state') != 'canceled',
                    'icon': 'tryton-clear',
                    },
                'confirm': {
                    'invisible': Eval('state') != 'draft',
                    'icon': 'tryton-save',
                    },
                })


    @staticmethod
    def default_state():
        return 'draft'
    @classmethod
    @ModelView.button
    @Workflow.transition('canceled')
    def cancel(cls, schweißanweisung_wpss):
        pass

    @classmethod
    @ModelView.button
    @Workflow.transition('draft')
    def draft(cls, schweißanweisung_wpss):
        pass

    @classmethod
    @ModelView.button
    @Workflow.transition('confirmed')
    def confirm(cls, schweißanweisung_wpss):
        pass


    @classmethod
    def delete(cls, schweißanweisung_wpss):
        for schweißanweisung_wps in schweißanweisung_wpss:
            if schweißanweisung_wps.state != 'draft':
                raise AccessError(gettext('welding_certification.delete_non_draft',
                    ws=schweißanweisung_wps.rec_name))
        super(SchweißanweisungWps, cls).delete(schweißanweisung_wpss)
            
    @classmethod
    def __register__(cls, module_name):
    
        cursor = Transaction().connection.cursor()
        sql_table = cls.__table__()
        table = cls.__table_handler__(module_name)

        table.column_rename('wps_nr', 'wps_code')
        table.column_rename('wps_nr', 'code')

        super(SchweißanweisungWps, cls).__register__(module_name)

        table = cls.__table_handler__(module_name)

        if table.column_exist('wps_nr'):
            table.drop_column('wps_nr')  
        if table.column_exist('wps_code'):
            table.drop_column('wps_code')            
    
    

    @staticmethod
    def order_code(tables):
        table, _ = tables[None]
        return [CharLength(table.code), table.code]
    @classmethod
    def _new_code(cls, **pattern):
        pool = Pool()
        Configuration = pool.get('welding_certification.configuration')
        config = Configuration(1)
        sequence = config.get_multivalue('welding_sequence', **pattern)
        if sequence:
            return sequence.get()    
    @classmethod
    def default_code_readonly(cls, **pattern):
        Configuration = Pool().get('welding_certification.configuration')
        config = Configuration(1)
        return bool(config.get_multivalue('welding_sequence', **pattern))

    def get_code_readonly(self, name):
        return True


    @classmethod
    def create(cls, vlist):
        vlist = [x.copy() for x in vlist]
        for values in vlist:
            if not values.get('code'):
                values['code'] = cls._new_code()
        return super(SchweißanweisungWps, cls).create(vlist)

    @classmethod
    def copy(cls, weldings, default=None):
        if default is None:
            default = {}
        else:
            default = default.copy()
        default.setdefault('code', None)
        return super(SchweißanweisungWps, cls).copy(weldings, default=default)
    
    
    @classmethod
    def search_global(cls, text):
        for record, rec_name, icon in super(SchweißanweisungWps, cls).search_global(text):
            icon = icon or 'Business_logo'
            yield record, rec_name, icon

    #after we should delete the previous records from interface for starting from scratch           
    @staticmethod
    def default_title():
        return "schweißanweisung_wps"             

    @staticmethod
    def default_geeigneter_schweisser():
        return Transaction().context.get('geeigneter_schweisser')
    @staticmethod
    def default_werkstuckdicke1():
        return 0
    @staticmethod
    def default_aussendurchmesser1():   
        return 0   
    
    @classmethod
    def default_logo_company(cls):
        path = "/home/afef/devel/trytonnew6/trytond/modules/welding_certification/img/logo_company.png"
        file_ = open(path, "rb")
        return file_.read()
    @classmethod
    def default_photo(cls):
        path = "/home/afef/devel/trytonv6/lib/python3.8/site-packages/trytond/modules/welding_certification/img/image.png"
        #path = "/home/msaidi/venv/geers/trytond/trytond/modules/welding_certification/img/White_background.png"
        file_ = open(path, "rb")
        return file_.read()

    @fields.depends('grundwerkstoff1')
    def on_change_with_grundwerkstoff1_nummer(self,name= None):

        if self.grundwerkstoff1:
           return self.grundwerkstoff1.nummer
        else:
           return None     

    @fields.depends('grundwerkstoff2')
    def on_change_with_grundwerkstoff2_nummer(self,name= None):

        if self.grundwerkstoff2:
           return self.grundwerkstoff2.nummer
        else:
           return None  

    @fields.depends('szi_1')    
    def on_change_with_fabrikat(self,name= None):
        if self.szi_1:
           return self.szi_1.handelsname 
        else:
           return None   
    @fields.depends('szi_1')
    def on_change_with_fm(self,name= None):
        if self.szi_1:
           return self.szi_1.werkstoffgruppe
        else:
           return None  

    @fields.depends('szi_2')       
    def on_change_with_fm1(self,name= None):
        if self.szi_2:
           return  self.szi_2.werkstoffgruppe
        else:
           return None  

    @fields.depends('szi_2') 
    def on_change_with_fabrikat1(self,name= None):
        if self.szi_2:
           return self.szi_2.handelsname   
        else:
           return None  
           
    @fields.depends('skizze_info')
    def on_change_with_naht_nr(self,name=None):
         if self.skizze_info and self.skizze_info.norm2:
           try:  
               var = self.skizze_info.norm2
               pos1 = var.find("- ")
               value = var[pos1+1:len(var)]
               return value  
           except AttributeError:
               pass          
    @fields.depends('skizze_info')
    def on_change_with_bild(self,name= None):
        if self.skizze_info:
           return self.skizze_info.bild
        else:
           return None   

    @fields.depends('skizze_info')
    def on_change_with_rechts_bild(self,name= None):
        if self.skizze_info:
           return self.skizze_info.rechts_name
        else:
           return None

    @fields.depends('szi_3')
    def on_change_with_fm2(self,name= None):
        if self.szi_3 :
           return self.szi_3.werkstoffgruppe
        else:
           return None 

    @fields.depends('szi_3')
    def on_change_with_fabrikat2(self,name= None):
        if self.szi_3 :
           return self.szi_3.handelsname
        else:
           return None 
    @fields.depends('prozess')       
    def on_change_with_prozess_iso4063_info(self,name=None):
        if self.prozess :
           return "für:  "+self.prozess.code2
        else:
           return None 
    @fields.depends('prozess','grundwerkstoff1','grundwerkstoff2','schweißposition','prozess','produktform','nahtart','werkstuckdicke1')
    def on_change_with_belegnr(self,name= None):

        if self.prozess and self.grundwerkstoff1 and self.grundwerkstoff2 and self.schweißposition:
           val_1 = self.grundwerkstoff1.werkstoffgruppe
           val_2 = self.grundwerkstoff2.werkstoffgruppe
           sep = "/"
           space = " "
           if(val_1 == val_2):
               val_info = val_1
               return "ISO 15609-1"+space+self.prozess.code1+space+str(self.produktform)+space+str(self.nahtart)+space+val_info+space+"t"+str(self.werkstuckdicke1)
           else:
               val_info = str(val_1)+"/"+str(val_2)
               return "ISO 15609-1"+space+self.prozess.code1+space+str(self.produktform)+space+str(self.nahtart)+space+val_info+space+"t"+str(self.werkstuckdicke1)

    @fields.depends('produktform','nahtart','schweißposition')
    def on_change_with_empfehlung(self,name=None):

        if self.schweißposition and self.produktform and self.nahtart:
           val_1 = self.produktform
           if(val_1 == "P/P"):
              val_1 ="PP"
           elif(val_1 == "T/P"):
              val_1 ="TP"
           else:
              val_1 ="TT"

           return val_1+self.nahtart+self.schweißposition.code


    def get_rec_name(self, name):
        if self.code:
           return "WPS-ID-00" + str(self.code)
        else:
           return "WPS-ID-00"
    @classmethod
    def search_rec_name(cls, name, clause):
        if clause[1].startswith('!') or clause[1].startswith('not '):
            bool_op = 'AND'
        else:
            bool_op = 'OR'
        return [bool_op,
            ('code',) + tuple(clause[1:]),
            ('intern_nr',) + tuple(clause[1:]),
            ] 


#en iso 96061
class Iso96061(Workflow, ModelSQL, ModelView):
    'Iso 96061'
    __name__ = 'welding.iso96061'
            
    name_des_schweißers = fields.Many2One('party.party', 'Name des Schweißers       ',states=STATES, depends=DEPENDS)
    bewertung = fields.Many2One('bewertung.bewertung','Bewertung', "Bewertungsbogen für Prüfungen nach EN ISO 96061-1/ EN 287-1 (stähle),EN ISO 9606-2 (Alu)", 
            ondelete='CASCADE')
    schweisspos = fields.Many2One('welding.schweissposition_iso6947', "Schweißposition",
            ondelete='CASCADE',required=True)
    hinweise = fields.Many2One('welding.hinweise', "Zusätzliche Hinweise",
            ondelete='CASCADE')
    hinweise_data = fields.Function(fields.Char("Hinweise Data"), 'on_change_with_hinweise_data')
    grundwerkstoff = fields.Many2One('welding.grundwerkstoff_properties', "des Grundwerkstoffes")
    schweisszusatz = fields.Many2One('welding.schweißzusatz', "Schweißzusatz", required=True)
    bezeichnung = fields.Many2One('welding.szi_data', "(Bezeichnung)")
    schutzgaz = fields.Many2One('welding.list_gas_mischgase', "Schutzgas")
    hilfsstoffe = fields.Many2One('welding.list_gas_mischgase', "Hilfsstoffe")
    lines_qualifikation = fields.One2Many( 'welding.iso96061.qualifikation_datumms','iso96061', "Verlängerung der Qualifikation durch den Prüfer oder die  Prüfstelle für die folgenden 3 Jahre (unter Bezug auf Abschnitt 9.3 a)")
    lines_welding = fields.One2Many('welding.iso96061.datumms', 'iso96061', "Bestätigung der Gültigkeit durch die Schweißaufsichtsperson oder dem Prüfer/der Prüfstelle für die folgenden 6 Monate (unter Bezug auf Abschnitt 9.2)")
    legitimation = fields.Function(fields.Char("Legitimation                    "), 'on_change_with_legitimation')
    art_der_legitimation = fields.Function(fields.Char("Art der Legitimation        "), 'on_change_with_art_der_legitimation')
    gebursdatum_und_ort = fields.Function(fields.Char("Gebursdatum und Ort    "), 'on_change_with_gebursdatum_und_ort')
    arbeitgeber = fields.Function(fields.Char("Arbeitgeber                    "), 'on_change_with_arbeitgeber')
    prufnorm = fields.Char("Prüfnorm")
    vorschrift_prüfnorm = fields.Selection([
        ('-', '-'),
        ('DIN EN ISO 9606-1:2013-12', 'DIN EN ISO 9606-1:2013-12|Schmelzschweißen-Stähle, Ausgabe:2013-12'),
        ('EN ISO 9606-1:2013', 'EN ISO 9606-1:2013 | Schmelzschweißen-Stähle, Ausgabe:2013'),
        ('DIN EN ISO 9606-1:2013-12,AD 2000 HP 3', 'DIN EN ISO 9606-1:2013-12,AD 2000 HP 3 | Geschweißte Druckbehälter'),
        ('DIN EN ISO 9606-1:2013-12,DIN 1090-2', 'DIN EN ISO 9606-1:2013-12,DIN 1090-2 | Stahltragwerke'),
        ('DIN EN ISO 9606-1:2013-12,DIN 18800-7', 'DIN EN ISO 9606-1:2013-12,DIN 18800-7 | Stahlbauten'),
        ('DIN EN ISO 9606-1:2013-12,DIN EN 15085-2', 'DIN EN ISO 9606-1:2013-12,DIN EN 15085-2 | Schweißen von Schienenfahrzeugen'),
        ('SN EN ISO 9606-1:2013-12', 'SN EN ISO 9606-1:2013-12 | Schweizerische Norm, Ausgabe: 2014-02'),
        ('ÖNORM EN ISO 9606-1:2014-04-15', 'ÖNORM EN ISO 9606-1:2014-04-15 | Österreichische Norm, Ausgabe:2014-02-01 '),
        ('MSZ EN ISO 9606-1:2014', 'MSZ EN ISO 9606-1:2014 | Ungarische Norm, Ausgabe: 2014'),
        ('MSZ EN ISO 9606-1:2014,MSZ EN 15085-2:2008', 'MSZ EN ISO 9606-1:2014,MSZ EN 15085-2:2008 | Ungarische Norm, Schienenfahrzeugbau'),
        ('DGRL 2014/68/EU, AD 2000 HP 3, EN ISO 9606-1', 'DGRL 2014/68/EU, AD 2000 HP 3, EN ISO 9606-1 | Zertifikat TÜV nach DGRL 2014/68/EU(ab 19.07.2016)'),
        ('2014/68/EU;EN ISO 9606-1:2013;AD 2000 HP 3', '2014/68/EU;EN ISO 9606-1:2013;AD 2000 HP 3 | Zertifikat DVS-PersZert2014/68/EU(ab 19.07.2016)'),
        ('97/23/EG,AD 2000 HP 3,EN ISO 9606-1:2013', '97/23/EG,AD 2000 HP 3,EN ISO 9606-1:2013 | Zertifikat nach DGR 97/23/EG(Stähle)'),
        ('DGRL 97/23/EG,EN ISO 9606-1:2013', 'DGRL 97/23/EG,EN ISO 9606-1:2013 | Zertifikat nach DGRL 97/23/EG(Stähle)'),
        ('DGRL 97/23/EG,EN 13445-4,EN ISO 9606-1:2013', 'DGRL 97/23/EG,EN 13445-4,EN ISO 9606-1:2013 | Zertifikat nach DGRL 97/23/EG(Stähle)'),
        ('97/23/EG;EN ISO 9606-1:2013; AD 2000 HP 3', '97/23/EG;EN ISO 9606-1:2013; AD 2000 HP 3 | Zertifikat DVS-PersZert 97/23/EG(Stähle)'),
        ('EN ISO 9606-1, SVTI504, AD 2000 HP 3 DGR', 'EN ISO 9606-1, SVTI504, AD 2000 HP 3 DGR | Schweizerische Norm'),
        ('DIN EN ISO 9606-1:1:2017-12', 'DIN EN ISO 9606-1:1:2017-12 | Schmelzschweißen-Stähle, Ausgabe:2017-12'),
        ('DIN EN ISO 9606-1:1:2017', 'DIN EN ISO 9606-1:1:2017-12 | Schmelzschweißen-Stähle, Ausgabe:2017'),
        ('DIN EN ISO 9606-1:1:2017-12,AD 2000 HP 3', 'DIN EN ISO 9606-1:1:2017-12,AD 2000 HP 3 | Geschweißte Druckbehälter'),
        ('DIN EN ISO 9606-1:1:2017-12,DIN 1090-2', 'DIN EN ISO 9606-1:1:2017-12,DIN 1090-2 | Stahltragwerke'),
        ('DIN EN ISO 9606-1:1:2017-12,DIN 15085-2', 'DIN EN ISO 9606-1:1:2017-12,DIN 15085-2 | Schweißen von Schienenfahrzeugen'),
        ('2014/68/EU;EN ISO 9606-1:2017;AD 2000 HP 3', '2014/68/EU;EN ISO 9606-1:2017;AD 2000 HP 3 | Zertifikat DVS-PersZert2014/68/EU'),
        ('PED 2014/68/EU,EN ISO 9606-1:2017', 'PED 2014/68/EU,EN ISO 9606-1:2017 | Zertifikat Pressure Equipement Directive'),
        ('2014/29/EU;EN ISO 9606-1:2017;AD 2000 HP 3', '2014/29/EU;EN ISO 9606-1:2017;AD 2000 HP 3 | Zertifikat Einfache Druckbehälterrichtinie'),
        ('SPVD 2014/29/EU,DIN EN ISO 9606-1:2017-12', 'SPVD 2014/29/EU,DIN EN ISO 9606-1:2017-12 | Zertifikat Simple Pressure Vessels Directive'),
        ('SPVD 2014/29/EU,EN ISO 9606-1:2017', 'SPVD 2014/29/EU,EN ISO 9606-1:2017 | Zertifikat Simple Pressure Vessels Directive'),
        ('MSZ EN ISO 9606-1:2017', 'MSZ EN ISO 9606-1:2017 | Ungarische Norm, Ausgabe: 2017-12-01'),
        ('MSZ EN ISO 9606-1:2017,MSZ EN 15085-2:2008', 'MSZ EN ISO 9606-1:2017,MSZ EN 15085-2:2008 | Ungarische Norm, Schienenfahrzeugbau'),    
    ], "Vorschrift/Prüfnorm      ")

    bemerkung = fields.Char("Bemerkung                   ")
    wps_bezug = fields.Many2One('welding.schweißanweisung_wps', "WPS-Bezug", ondelete='RESTRICT')
    wps_bezug1 = fields.Many2One('welding.schweißanweisung_wps', "WPS-Bezug", ondelete='RESTRICT')
    title = fields.Selection([
        ('Prüfungsbescheinigung', 'Schweißer-Prüfungsbescheinigung'),
        ('schweisser1', 'SCHWEISSER-PRÜFUNGSBESCHEINIGUNG'),
        ('zertifikat', 'Schweißer-Zertifikat'),
        ('prüfungszertifikat', 'Schweißer-Prüfungszertifikat'),
        ('zertifikatSchweißer_Prüfungsbescheinigung', 'ZERTIFIKAT/SCHWEIßER-PRÜFUNGSBESCHEINIGUNG'),
        ('welder_approver', 'WELDER APPROVAL TEST CERTIFICATE'),
    ], "Title" )
    bezeichnung1 = fields.Function(fields.Char("Bezeichnung(en)"), 'on_change_with_bezeichnung1')
    bezeichnung2 = fields.Function(fields.Char("Bezeichnung(en) 2"), 'on_change_with_bezeichnung2')

    prüfer_prüfstelle_beleg_nr = fields.Selection([
        ('0036 / DD1 MUE / JJMMTTsp', '0036 / DD1 MUE / JJMMTTsp'),
        ('0036 / DD1 ULM / JJMMTTsp', '0036 / DD1 ULM / JJMMTTsp'),
        ('ATK-36-04-8900', 'ATK-36-04-8900'),
        ('Heinz Geers / Geers-DL GmbH', 'Heinz Geers / Geers-DL GmbH'),
    ], "Prüfer oder Prüfstelle-Beleg-Nr")
    fachkunde = fields.Selection([
        ('-', '-'),
        ('bestanden', 'Bestanden'),
        ('Nicht geprüft', 'Nicht geprüft'),
    ], "Fachkunde                   ")
    schweißprozess = fields.Many2One('welding.schweißprozesse', "Schweißprozess(e)", required = True, ondelete='CASCADE', select=True)
    schweißprocess_geltungs = fields.Function(fields.Char("MAG"), 'on_change_with_schweißprocess_geltungs')
    schweißprocess_prüfstuk = fields.Function(fields.Char("Prüfstück2"), 'on_change_with_schweißprocess_prüfstuk')
    prüfstück = fields.Text("Prüfstück")
    geltungsbereich =fields.Text("Geltungsbereich")
    artdeswerkstoff = fields.Selection([
        ('-', '-'),
        ('D-Übergang', 'D-Übergang im Kurzschluss |  Kurzlichtbogen'),
        ('G-großtropfiger Übergang Langlichtbogen', 'G-großtropfiger Übergang | Langlichtbogen'),
        ('S-feintropfiger Übergang Sprühlichtbogen','S-feintropfiger Übergang | Sprühlichtbogen'),
        ('P-impulsgesteuerter Übergang Impulslichtbogen', 'P-impulsgesteuerter Übergang | Impulslichtbogen'),
    ], "Art des Werkstoffüberganges")
    artdeswerkstoff_geltungs =fields.Function(fields.Char("MAG"), 'on_change_with_artdeswerkstoff_geltungs')
    rohraußendurchmesser = fields.Float("Rohraußendurchmesser D(mm)",
            domain=[
            ('rohraußendurchmesser', '>=', 0),
            ])
    rohraußendurchmesser_geltungs =fields.Function(fields.Char("MAG"), 'on_change_with_rohraußendurchmesser_geltungs')

    produktform = fields.Selection([
        ('-', '-'),
        ('P', 'P Blech'),
        ('T', 'T Rohr'),
    ], "Produktform(Blech oder Rohr)", required=True
        )
    produktform_geltungs =fields.Function(fields.Char("MAG"), 'on_change_with_produktform_geltungs')
    nahtart2 = fields.Selection([
        ('FW', 'FW Kehlnaht für P'),
        ('None', ' '),
    ], "Nahtart", required=True
        )
    nahtart = fields.Selection([
        ('-', '-'),
        ('BW', 'BW | Stumpfnaht(butt weld)'),
        ('FW', 'FW | Kehlnaht (fillet weld)'),
        ('FW/BW', 'FW/BW | Kombiniertes FW/BW-Prüfstück'),
    ], "Nahtart", required=True
        )

    nahtart_geltungs =fields.Function(fields.Char("MAG"), 'on_change_with_nahtart_geltungs')
    werkstoffgruppe = fields.Selection([
        ('1.1', '1.1 | Stähle mit einer festgelegten Mindeststreckgrenze ReH <= 275 N/mm²'),
        ('1.2', '1.2 | Stähle mit einer Mindeststreckgrenze 275 < ReH <= 360 N/mm² '),
        ('1.3', '1.3 | Normalisierte Feinkornbaustähle mit einer Streckgrenze  ReH > 360 N/mm² '),
        ('1.4', '1.4 | Stähle mit einem erhöhten Widerstand gegen atmosphärische korrosion '),
        ('2.1', '2.1 | Thermomechanisch gewalzte Feinkornbaustähle mit 360 < ReH <=460 N/mm²'),
        ('2.2', '2.2 | Thermomechanisch gewalzte Feinkornbaustähle mit  ReH > 460 N/mm²'),
        ('3.1', '3.1 | Vergütete Feinkornbaustähle mit einer Streckgrenze 360< ReH <= 690 N/mm²'),
        ('3.2', '3.2 | Vergütete Feinkornbaustähle mit einer Mindeststreckgrenze ReH > 690 N/mm²'),
        ('3.3', '3.3 | Ausscheidungshärtende Feinkornbaustähle, jedoch keine nichtrostenden St'),
        ('4.1', '4.1 | Stähle mit Cr <= 0,3% und Ni <= 0,7%'),
        ('4.2', '4.2 | Stähle mit Cr <= 0,7% und Ni <= 1,5%'),
        ('5.1', '5.1 | Stähle mit 0,75 % <= Cr <= 1,5% und Mo <= 0,7%'),
        ('5.2', '5.2 | Stähle mit 1.5% <= Cr <= 3.5 % und 0.7 % < Mo <= 1.2%'),
        ('5.3', '5.3 | Stähle mit 3.5% < Cr <= 7.0% und 0.4% <Mo<=0.7%'),
        ('5.4', '5.4 | Stähle mit 7.0% < Cr <=10,0% und 0.7% <Mo<=1.2%'),
        ('6.1', '6.1 | Stähle mit 0,3%  <=C r <= 0,75 %, Mo <=0,7% und V<=0,35%'),
        ('6.2', '6.2 | Stähle mit 0,75%<Cr<= 3,5%,0,7%< Mo<= 1,2% und V<= 0,35%'),
        ('6.3', '6.3 | Stähle mit 3,5 % < Cr <= 7,0 %, Mo <= 0,7 % und 0,45 <= V <= 0,55 %'),
        ('6.4', '6.4 | Stähle mit 7,0%<Cr<= 12,5%,0,7%< Mo<= 1,2% und v<=0,35%'),
        ('7.1', '7.1 | Ferritische nichtrostende Stähle'),
        ('7.2', '7.2 | Martensitische nichtrostende Stähle'),
        ('7.3', '7.3 | Ausscheidungshartende nichtrostende Stähle'),
        ('8.1', '8.1 | Austenitische nichtrostende Stähle mit Cr <= 19 %'),
        ('8.2', '8.2 | Austenitische nichtrostende Stähle mit Cr > 19 %'),
        ('8.3', '8.3 | Hanganhaltige austenitische nichtrostende Stähle mit 4.0 % < Mn <= 12,0 %'),
        ('9.1', '9.1 | NickeIegierte Stähle mit Ni <= 3,0 %'),
        ('9.2', '9.2 | NickeIegierte Stähle mit 3,0 % <Ni <= 8,0%'),
        ('9.3', '9.3 | NickeIegierte Stähle mit 3,0 % <Ni <= 10,0%'),
        ('10.1', '10.1 | Austenitische ferritische nichtrostende Stähle mit Cr >24,0 %'),
        ('10.2', '10.2 | Austenitische ferritische nichtrostende Stähle mit Ni<= %'),
        ('10.3', '10.3 | Hanganhaltige ferritische  nichtrostende Stähle mit 4.0 % < Mn <= 12,0 %'),
        ('11', '11 | rimvkeflegwerte Stählemm [h <: ELI] 3:'),
        ('11.1', '11.1 | Stähle der Gruppe 1 2) mit Ausnahme 0,25 % < C <= 0,85 %'),
        ('11.2', '11.2 | Stähle wie in Gruppe 1 1 aufgeführt, mit 0,25 % < C <= 0,35 %'),
        ('11.3', '11.3 | Stähle wie in Gruppe 1 1 aufgeführt, mit 0,5 % < C <= 0,85 %'),
    ], "Werkstoffgruppe(n)/-untergruppe(n)",
        )
    werkstoffgruppe_geltungs = fields.Function(fields.Char("MAG"), 'on_change_with_werkstoffgruppe_geltungs')
    werkstoffgruppe_schweisszusatz_info =  fields.Many2One('welding.werkstoffgruppe_schweißzusatz', "Werkstoffgruppe(n) Schweißzusatz", required=True)
    werkstoffgruppe_schweisszusatz_geltungs = fields.Function(fields.Char("MAG"), 'on_change_with_werkstoffgruppe_schweisszusatz_geltungs')
    schweisszusatz_geltungs =fields.Function(fields.Char("MAG"), 'on_change_with_schweisszusatz_geltungs')
    stromart_und_polung = fields.Selection([
        ('-', '-'),
        ('AC', 'AC'),
        ('Wechselstrom', 'Wechselstrom'),
        ('DC(-)', 'DC(-)'),
        ('Gleichstrom', 'Gleichstrom (-)'),
        ('DC(+)', 'DC(+)'),
        ('Gleichstrom(+)', 'Gleichstrom (+)'),
        ('aaa: DC(-) / bbb : DC(+)', 'aaa: DC(-) / bbb : DC(+)'),
        ('aaa: DC(+) / bbb : DC(-)', 'aaa: DC(+) / bbb : DC(-)'),
    ], "Stromart und Polung",
        )

    
    werkstoffdicke = fields.Float("Werkstoffdicke t (mm)",
            domain=[
            ('werkstoffdicke', '>=', 0),
            ])
    werkstoffdicke_stück = fields.Float("Werkstoffdicke t (mm)",
            domain=[
            ('werkstoffdicke_stück', '>=', 0),
            ])
    werkstoffdicke_geltungs =fields.Function(fields.Char("MAGG"), 'on_change_with_werkstoffdicke_geltungs')
    dicke_des_schweißgutes = fields.Float("Dicke des Schweißgutes s(mm)",
            domain=[
            ('dicke_des_schweißgutes', '>=', 0),
            ])
    dicke_des_schweißgutes_stück = fields.Integer("Dicke des Schweißgutes Stück s(mm)")
    rohraussendurchmesser_stück = fields.Integer("Rohraussendurchmesser Stück")

    dicke_des_schweißgutes_geltungs =fields.Function(fields.Char("MAG"), 'on_change_with_dicke_des_schweißgutes_geltungs')
    wurzel = fields.Selection([
        ('1', '1'),
        ('2', '2'),
        ('3', '3'),
        ('4', '4'),
        ('5', '5'),
    ], "Wurzel", required=True
        )
    abmessungen_des_prüfstücks = fields.Selection([
        ('--', '--'),
        ('Beschreibt die Schweißgutdicke', 's'),
        ('Beschreibt die Werkstoffdicke', 't'),
        ('Beschreibt den äußeren Durchmesser', 'D'),
    ], "Abmessungen des Prüfstücks")

    schweißposition = fields.Selection([
        ("None"," "),
        ("PA", "PA P FW:waagerecht"),
        ("PB", "PB P FW:horizontal"),
        ("PC", "PC T BW:quer"),
        ("PD", "PD P FW:horizontal-Überkopf"),
        ("PF", "PF P FW:Steigend"),
        ("PG", "PG P FW:fallend")
    ],"Schweißposition", required=True)
    schweißposition_geltungs =fields.Function(fields.Char("MAG"), 'on_change_with_schweißposition_geltungs')

    schweißnahteinzelheiten = fields.Selection('on_change_with_schweißnahteinzelheiten', "Schweißnahteinzelheiten",
    states={
             'invisible': Eval('nahtart').in_(['-', 'FW', 'FW/BW']),
             'required': Eval('nahtart') == 'BW',
        }, depends=['nahtart'],)
    schweissnahteinzelheiten_geltungs = fields.Function(fields.Char("MAG",states={
             'invisible': Eval('nahtart').in_(['-', 'FW', 'FW/BW']),
             'required': Eval('nahtart') == 'BW',
                }),'on_change_with_schweissnahteinzelheiten_geltungs')

    mehrlageg_einlageg = fields.Selection('on_change_with_mehrlageg_einlageg',"Mehrlagig/einlagig", required=True)
    mehrlageg_einlageg_geltungs = fields.Function(fields.Char("MAG"), 'on_change_with_mehrlageg_einlageg_geltungs')
    erganzende = fields.Selection([
        ('-', '-'),
        ('nicht geschweißt', 'nicht geschweißt'),
        ('nicht einwandfrei', 'nicht einwandfrei'),
        ('einwandfrei', 'einwandfrei'),
    ], "Ergänzende Kehlnahtprüfung (in Kombination mit einer Stumpfnahtprüfung)")
    prüfungsart = fields.Text("Prüfungsart")
    ausgeführt = fields.Text("ausgeführt und bestanden")
    nichtgeprüft = fields.Text("nicht geprüft")
    sichtprüfung = fields.Text("Sichtprüfung")
    sichtprüfung_aus_und_bestanden = fields.Selection([
        ('X', 'X'),
        ('-', '-'),
    ], 'ausgeführt und bestanden ')
    sichtprüfung_nich_geprüft = fields.Selection('on_change_with_sichtprüfung_nich_geprüft', "Nicht geprüft")
    durchstrahlungsprüfung = fields.Text("Durchstrahlungsprüfung")
    durchstrahlungsprüfung_aus_und_bestanden = fields.Selection([
        ('X', 'X'),
        ('-', '-'),
    ], "Durchstrahlungsprüfung_aus_und_bestanden ")
    durchstrahlungsprüfung_nich_geprüft = fields.Selection('on_change_with_durchstrahlungsprüfung_nich_geprüft', "Durchstrahlungsprüfung_nich_geprüft")
    bruchprüfung = fields.Text("Bruchprüfung")
    bruchprüfung_aus_und_bestanden = fields.Selection([
        ('X', 'X'),
        ('-', '-'),
    ], "Bruchprufung_aus_und_bestanden")
    bruchprüfung_nich_geprüft = fields.Selection('on_change_with_bruchprüfung_nich_geprüft', "Bruchprufung_nich_geprüft")

    biegeprufüng = fields.Text("Biegeprüfung")

    biegeprufüng_aus_und_bestanden = fields.Selection([
        ('X', 'X'),
        ('-', '-'),
    ], "Biegeprufüng_aus_und_bestanden")

    biegeprufüng_nich_geprüft  = fields.Selection('on_change_with_biegeprufüng_nich_geprüft', "Biegeprufung_nich_geprüft")
    kerbzugprüfung = fields.Text("Kerbzugprüfung")
    kerbzugprüfung_aus_und_bestanden = fields.Selection([
        ('X', 'X'),
        ('-', '-'),
    ], "kerbzugprüfung_aus_und_bestanden")
    kerbzugprüfung_nich_geprüft = fields.Selection('on_change_with_kerbzugprüfung_nich_geprüft', "Kerbzugprüfung_nich_geprüft")

    makroskopiche_untersuchungen = fields.Text("Makroskopische Untersuchungen")

    makro_unter_aus_und_bestanden = fields.Selection([
        ('X', 'X'),
        ('-', '-'),
    ], "Makro_unter_aus_und_bestanden")
    makro_unter_nich_geprüft = fields.Selection('on_change_with_makro_unter_nich_geprüft',"Makro_unter_nich_geprüft")
    zusatzprüfungen = fields.Text("Zusatzprüfungen")

    zusatzprüfungen_aus_und_bestanden = fields.Selection([
        ('X', 'X'),
        ('-', '-'),
    ], "zusatzprüfungen_aus_und_bestanden")
    zusatzprüfungen_nich_geprüft = fields.Selection('on_change_with_zusatzprüfungen_nich_geprüft',"zusatzprüfungen_nich_geprüft")
    ort = fields.Char("Ort")
    gültigkeitsdauer_info = fields.Selection([
        ('9.3a', '9.3a) Neuer prüfung nach 3 Jahren'),
        ('9.3b', '9.3b) Prüfung wird nach 2 Jahren Verlängert'),
        ('9.3c', '9.3c) Verlängerung jeweils nach 6 Monaten'),
    ], "Gültigkeitsdauer")
    photo2 = fields.Binary("Photo")
    logo_company = fields.Binary("Logo Society", readonly = True,
         help="Sie können das Logo des Eigentümers nicht ändern oder löschen ")
    datum_schweissens = fields.Date("Datum des schweißens")
    datum_prüfung = fields.Date("Datum der prüfung")
    pruefstelle = fields.Many2One('welding.pruefstelle', "Name des Prüfers oder der Prüfstelle", ondelete='CASCADE')
    datum_ausgabe = fields.Date("Datum der Ausgabe")
    unterschrift = fields.Function(fields.Char(
                    "Name und Unterschrift",
                    states={
                   'invisible': ~Eval('unterschrift'),
                    }, depends=['pruefstelle']),'on_change_with_unterschrift')  
    gültigkeitsdauer = fields.Function(fields.Date(
                        "Gültigkeitsdauer bis",
                    states={
                   'invisible': ~Eval('gültigkeitsdauer'),
                    }, depends=['gültigkeitsdauer_info','datum_schweissens']),'on_change_with_gültigkeitsdauer')
    weitere_beleg_nr = fields.Char("Weitere Beleg-Nr")
    state = fields.Selection([
            ('draft', 'Draft'),
            ('confirmed', 'Confirmed'),
            ('canceled', 'Cancelled'),
            ], 'State', required=True, readonly=True, select=True)
    @classmethod
    def __setup__(cls):
        super(Iso96061, cls).__setup__()
        cls._order.insert(1, ('name_des_schweißers', 'ASC'))
        cls._transitions |= set((
                ('draft', 'confirmed'),
                ('draft', 'canceled'),
                ('confirmed', 'canceled'),
                ('canceled', 'draft'),
                ))    
        cls._buttons.update({
                'cancel': {
                    'invisible': Eval('state') == 'canceled',
                    'icon': 'tryton-cancel',
                    },
                'draft': {
                    'invisible': Eval('state') != 'canceled',
                    'icon': 'tryton-clear',
                    },
                'confirm': {
                    'invisible': Eval('state') != 'draft',
                    'icon': 'tryton-save',
                    },
                })
                
    @staticmethod
    def default_state():
        return 'draft'
    @classmethod
    @ModelView.button
    @Workflow.transition('canceled')
    def cancel(cls, iso96061s):
        pass

    @classmethod
    @ModelView.button
    @Workflow.transition('draft')
    def draft(cls, iso96061s):
        pass

    @classmethod
    @ModelView.button
    @Workflow.transition('confirmed')
    def confirm(cls, iso96061s):
        pass


    @classmethod
    def delete(cls, iso96061s):
        for iso96061 in iso96061s:
            if iso96061.state != 'draft':
                raise AccessError(gettext('welding_certification.delete_non_draft',
                    ws=iso96061.rec_name))
        super(Iso96061, cls).delete(iso96061s)
        
    @classmethod
    def default_logo_company(cls):
        path = "/home/afef/devel/trytonnew6/trytond/modules/welding_certification/img/logo_company.png"
        file_ = open(path, "rb")
        return file_.read()
    @staticmethod
    def default_werkstoffdicke_stück():
        return 0
    @staticmethod
    def default_werkstoffdicke():
        return 0    
    @staticmethod    
    def default_dicke_des_schweißgutes():
        return 0 
    @staticmethod    
    def default_schweißposition():
        return "None"
    @staticmethod    
    def default_nahtart2():
        return "None"
        
    @staticmethod    
    def default_rohraussendurchmesser_stück():
        return 0 
    @staticmethod    
    def default_rohraußendurchmesser():
        return 0          
    @staticmethod
    def default_title():
        return "Prüfungsbescheinigung"
    @staticmethod
    def default_vorschrift_prüfnorm():
        return "DIN EN ISO 9606-1:2013-12"
        
    @fields.depends('nahtart')
    def on_change_nahtart(self):
        if self.nahtart != "BW":
           self.schweißnahteinzelheiten = None
           
    @fields.depends('nahtart', 'schweißprozess')
    def on_change_with_schweißnahteinzelheiten(self):    
        if self.schweißprozess: 
            tab = [(None, '')]
            if(self.nahtart == "BW" and self.schweißprozess.code !="311"):
               tab.append(("-","-"))
               tab.append(("ss nb","ss nb | einseitig ohne Schweißbadsicherung"))
               tab.append(("ss mb","ss mb | einseitig mit Schweißbadsicherung"))
               tab.append(("bs","bs | beidseitiges Schweißen"))
               tab.append(("ss gb","ss gb | einseitig mit Gaswurzelschutz"))
               tab.append(("ci","ci | Schweißzusatzeinlageteil"))
               tab.append(("ss fb","ss fb | einseitig mit schweißpulverabstützung"))
            else:
             if(self.nahtart == "BW" and self.schweißprozess.code =="311"):
               tab.append(("-","-"))
               tab.append(("ss nb lw","ss nb lw | einseitig ohne Badsicherung, nach links"))
               tab.append(("ss nb rw","ss nb rw | einseitig ohne Badsicherung, nach rechts"))
               tab.append(("ss mb lw","ss mb lw | einseitig mit Badsicherung, nach links"))
               tab.append(("ss mb rw","ss mb rw | einseitig mit Badsicherung, nach rechts"))
               tab.append(("bs lw","bs lw | beidseitig, nach links Schweißen"))
               tab.append(("bs rw","bs rw | beidseitig, nach rechts Schweißen"))
               tab.append(("ss gb lw","ss gb lw | einseitig mit Gaswurzelschutz, nach links"))
               tab.append(("ss gb rw","ss gb rw | einseitig mit Gaswurzelschutz, nach rechts"))
               tab.append(("ci lw","ci lw | Schweißzusatzlageteil, nach links"))
               tab.append(("ci rw","ci rw | Schweißzusatzlageteil, nach rechts"))
            return tab     

    @fields.depends('hinweise')
    def on_change_with_hinweise_data(self,name=None):
        if self.hinweise:
            return self.hinweise.bemerkungen
        else:
            return None
            

    @fields.depends('pruefstelle')
    def on_change_with_unterschrift(self,name=None):
        if self.pruefstelle:
            return self.pruefstelle.prüfer
        else:
            return None

    @fields.depends('schweißprozess')
    def on_change_with_schweißprocess_prüfstuk(self,name=None):
        if (self.schweißprozess and self.schweißprozess.code == "111/121"):
            return "E/UP"
        elif(self.schweißprozess and self.schweißprozess.code == "111"):
            return "E"
        elif(self.schweißprozess and self.schweißprozess.code == "114"):
            return "MF"
        elif(self.schweißprozess and self.schweißprozess.code in ["121","125"]):
            return "UP"
        elif(self.schweißprozess and self.schweißprozess.code == "131"):
            return "MIG"
        elif(self.schweißprozess and self.schweißprozess.code == "135"):
            return "MAG"
        elif(self.schweißprozess and self.schweißprozess.code == "135/111"):
            return "MAG/E"
        elif(self.schweißprozess and self.schweißprozess.code == "135/121"):
            return "MAG/UP"
        elif(self.schweißprozess and self.schweißprozess.code == "135/136"):
            return "MAG/MAG"
        elif(self.schweißprozess and self.schweißprozess.code in ["136", "138"]):
            return "MAG"
        elif(self.schweißprozess and self.schweißprozess.code == "136/121"):
            return "MAG/UP"
        elif(self.schweißprozess and self.schweißprozess.code == "141"):
            return "WIG"
        elif(self.schweißprozess and self.schweißprozess.code == "141/111"):
            return "WIG/E"
        elif(self.schweißprozess and self.schweißprozess.code == "141/121"):
            return "WIG/UP"
        elif(self.schweißprozess and self.schweißprozess.code == "141/131"):
            return "WIG/MIG"
        elif(self.schweißprozess and self.schweißprozess.code in ["141/135","141/136"]):
            return "WIG/MAG"
        elif(self.schweißprozess and self.schweißprozess.code in ["142","143","145"]):
            return "WIG"
        elif(self.schweißprozess and self.schweißprozess.code == "142/111"):
            return "WIG/E"
        elif(self.schweißprozess and self.schweißprozess.code == "142/131"):
            return "WIG/MIG"
        elif(self.schweißprozess and self.schweißprozess.code == "142/135"):
            return "WIG/MAG"
        elif(self.schweißprozess and self.schweißprozess.code == "15"):
            return "WPL"
        elif(self.schweißprozess and self.schweißprozess.code == "311"):
            return "Gas"
        elif(self.schweißprozess and self.schweißprozess.code == "111/135"):
            return "E/MAG"
        else:
            return None   
                
    @fields.depends('sichtprüfung_aus_und_bestanden')
    def on_change_with_sichtprüfung_nich_geprüft(self,name=None):
        tabb = [(None, '')]
        if(self.sichtprüfung_aus_und_bestanden == "X"):
           tabb.append(("-","-"))
        else:
               tabb.append(("X","X"))
        return tabb

    @fields.depends('durchstrahlungsprüfung_aus_und_bestanden')
    def on_change_with_durchstrahlungsprüfung_nich_geprüft(self,name=None):
        tabb = [(None, '')]
        if(self.durchstrahlungsprüfung_aus_und_bestanden == "X"):
           tabb.append(("-","-"))
        else:
               tabb.append(("X","X"))
        return tabb

    @fields.depends('bruchprüfung_aus_und_bestanden')
    def on_change_with_bruchprüfung_nich_geprüft(self,name=None):
        tabb = [(None, '')]
        if(self.bruchprüfung_aus_und_bestanden == "X"):
           tabb.append(("-","-"))
        else:
               tabb.append(("X","X"))
        return tabb


    @fields.depends('biegeprufüng_aus_und_bestanden')
    def on_change_with_biegeprufüng_nich_geprüft(self,name=None):
        tabb = [(None, '')]
        if(self.biegeprufüng_aus_und_bestanden == "X"):
           tabb.append(("-","-"))
        else:
               tabb.append(("X","X"))
        return tabb

    @fields.depends('kerbzugprüfung_aus_und_bestanden')
    def on_change_with_kerbzugprüfung_nich_geprüft(self,name=None):
        tabb = [(None, '')]
        if(self.kerbzugprüfung_aus_und_bestanden == "X"):
           tabb.append(("-","-"))
        else:
               tabb.append(("X","X"))
        return tabb

    @fields.depends('makro_unter_aus_und_bestanden')
    def on_change_with_makro_unter_nich_geprüft(self,name=None):
        tabb = [(None, '')]
        if(self.makro_unter_aus_und_bestanden == "X"):
           tabb.append(("-","-"))
        else:
               tabb.append(("X","X"))
        return tabb

    @fields.depends('zusatzprüfungen_aus_und_bestanden')
    def on_change_with_zusatzprüfungen_nich_geprüft(self,name=None):
        tabb = [(None, '')]
        if(self.zusatzprüfungen_aus_und_bestanden == "X"):
           tabb.append(("-","-"))
        else:
               tabb.append(("X","X"))
        return tabb
      
    @fields.depends('name_des_schweißers')  
    def on_change_with_legitimation(self,name=None):
        if self.name_des_schweißers:
          return self.name_des_schweißers.legitimation
        else:
          return None
          
    @fields.depends('name_des_schweißers')
    def on_change_with_art_der_legitimation(self,name=None):
        if self.name_des_schweißers:
          return self.name_des_schweißers.legitimation_type
        else:
          return None
          
    @fields.depends('name_des_schweißers')      
    def on_change_with_gebursdatum_und_ort(self,name=None):
        if self.name_des_schweißers and self.name_des_schweißers.birthday:
            return str(self.name_des_schweißers.birthday)+" , "+self.name_des_schweißers.ort_birthday
        else:
          return None
          
    @fields.depends('name_des_schweißers')      
    def on_change_with_arbeitgeber(self,name=None):
        if self.name_des_schweißers and self.name_des_schweißers.employer :
          return self.name_des_schweißers.employer.name
        else:
          return None
    
    @fields.depends('produktform')      
    def on_change_produktform(self,name=None):
        if self.produktform == "P":
            self.rohraußendurchmesser_geltungs == "D >= 500 mm"
          

    @fields.depends('nahtart','produktform','schweißprozess','schweisszusatz','werkstoffgruppe_schweisszusatz_info',
    'schweisspos','mehrlageg_einlageg','dicke_des_schweißgutes','rohraußendurchmesser',
    'werkstoffdicke','wurzel','schweißnahteinzelheiten')         
    def on_change_with_bezeichnung1(self,name=None):
      if self.schweißprozess and self.werkstoffgruppe_schweisszusatz_info and self.schweisszusatz and self.schweisspos:
          if self.nahtart == "BW" and (self.schweißprozess.code in ["111","114","121","125" ,"131","135","136","138","141","142","143","145","15","311"]) and self.produktform == "P":
             return "EN ISO 9606-1"+" "+self.schweißprozess.code+" "+"P"+" "+"BW"+" "+self.werkstoffgruppe_schweisszusatz_info.wsgr+" "+self.schweisszusatz.code+" "+"s"+str(self.dicke_des_schweißgutes)+" "+self.schweisspos.code+" "+str(self.schweißnahteinzelheiten)                                 
          elif self.nahtart == "BW" and (self.schweißprozess.code not in ["111","114","121","125" ,"131","135","136","138","141","142","143","145","15","311"]) and self.produktform == "P":
             return "EN ISO 9606-1"+" "+self.schweißprozess.code+" "+"P"+" "+"BW"+" "+self.werkstoffgruppe_schweisszusatz_info.wsgr+" "+self.schweisszusatz.code+" "+"s"+str(self.dicke_des_schweißgutes)+"("+str(self.wurzel)+"/"+str(float(self.dicke_des_schweißgutes)-float(self.wurzel))+")"+" "+self.schweisspos.code+" "+str(self.schweißnahteinzelheiten)+"/mb"   
          elif self.nahtart == "BW" and (self.schweißprozess.code in ["111","114","121","125" ,"131","135","136","138","141","142","143","145","15","311"]) and self.produktform == "T":
             return "EN ISO 9606-1"+" "+self.schweißprozess.code+" "+"T"+" "+"BW"+" "+self.werkstoffgruppe_schweisszusatz_info.wsgr+" "+self.schweisszusatz.code+" "+"s"+str(self.dicke_des_schweißgutes)+" "+"D"+str(self.rohraußendurchmesser)+" "+self.schweisspos.code+" "+str(self.schweißnahteinzelheiten)
          elif self.nahtart == "BW" and (self.schweißprozess.code not in ["111","114","121","125" ,"131","135","136","138","141","142","143","145","15","311"]) and self.produktform == "T":
             return "EN ISO 9606-1"+" "+self.schweißprozess.code+" "+"T"+" "+"BW"+" "+self.werkstoffgruppe_schweisszusatz_info.wsgr+" "+self.schweisszusatz.code+" "+"s"+str(self.dicke_des_schweißgutes)+"("+str(self.wurzel)+"/"+str(float(self.dicke_des_schweißgutes)-float(self.wurzel))+")"+" "+"D"+str(self.rohraußendurchmesser)+" "+self.schweisspos.code+" "+str(self.schweißnahteinzelheiten)+"/mb"   
          elif self.nahtart == "FW" and self.produktform == "P":
             return "EN ISO 9606-1"+" "+self.schweißprozess.code+" "+"P"+" "+"FW"+" "+self.werkstoffgruppe_schweisszusatz_info.wsgr+" "+self.schweisszusatz.code+" "+"t"+str(self.werkstoffdicke)+" "+self.schweisspos.code+" "+str(self.mehrlageg_einlageg)  
          elif self.nahtart == "FW" and self.produktform == "T":
             return "EN ISO 9606-1"+" "+self.schweißprozess.code+" "+"T"+" "+"FW"+" "+self.werkstoffgruppe_schweisszusatz_info.wsgr+" "+self.schweisszusatz.code+" "+"t"+str(self.werkstoffdicke)+" "+"D"+str(self.rohraußendurchmesser)+" "+self.schweisspos.code+" "+str(self.mehrlageg_einlageg)
          elif self.nahtart == "FW/BW" and self.produktform == "P":
             return "EN ISO 9606-1"+" "+self.schweißprozess.code+" "+"P"+" "+"FW/BW"+" "+self.werkstoffgruppe_schweisszusatz_info.wsgr+" "+self.schweisszusatz.code+" "+self.schweisspos.code     
          else:
             if self.nahtart == "FW/BW" and self.produktform == "T":
                return "EN ISO 9606-1"+" "+self.schweißprozess.code+" "+"T"+" "+"FW/BW"+" "+self.werkstoffgruppe_schweisszusatz_info.wsgr+" "+self.schweisszusatz.code+" "+"D"+str(self.rohraußendurchmesser)+" "+self.schweisspos.code  

    @fields.depends('nahtart2','nahtart','produktform','schweißprozess','schweisszusatz','werkstoffgruppe_schweisszusatz_info', 'schweisspos','schweißposition','mehrlageg_einlageg','werkstoffdicke_stück','schweißnahteinzelheiten','rohraussendurchmesser_stück','dicke_des_schweißgutes_stück')
    def on_change_with_bezeichnung2(self,name=None):
      if self.schweißprozess and self.werkstoffgruppe_schweisszusatz_info and self.schweisszusatz and self.schweisspos:
        if self.nahtart =="BW" and self.produktform == "T" and (self.schweißprozess.code in ["111","114","121","125" ,"131","135","136","138","141","142","143","145","15","311"]):
             return "EN ISO 9606-1"+" "+self.schweißprozess.code+" "+"T"+" "+"BW"+" "+self.werkstoffgruppe_schweisszusatz_info.wsgr+" "+self.schweisszusatz.code+" "+"s"+str(self.dicke_des_schweißgutes_stück)+" "+"D"+str(self.rohraussendurchmesser_stück)+" "+self.schweisspos.code+" "+str(self.schweißnahteinzelheiten)  
        elif self.nahtart =="BW" and self.produktform == "T" and (self.schweißprozess.code not in ["111","114","121","125" ,"131","135","136","138","141","142","143","145","15","311"]):
             return "EN ISO 9606-1"+" "+self.schweißprozess.code+" "+"T"+" "+"BW"+" "+self.werkstoffgruppe_schweisszusatz_info.wsgr+" "+self.schweisszusatz.code+" "+"s"+str(self.dicke_des_schweißgutes_stück)+"("+str(self.wurzel)+"/"+str(float(self.dicke_des_schweißgutes)-float(self.wurzel))+")"+" "+"D"+str(self.rohraussendurchmesser_stück)+" "+self.schweisspos.code+" "+str(self.schweißnahteinzelheiten)+"/mb"      
        elif self.nahtart =="FW" and self.produktform == "T":
             return "EN ISO 9606-1"+" "+self.schweißprozess.code+" "+"T"+" "+"FW"+" "+self.werkstoffgruppe_schweisszusatz_info.wsgr+" "+self.schweisszusatz.code+" "+"t"+"??"+" "+"D"+str(self.rohraussendurchmesser_stück)+" "+self.schweisspos.code+" "+str(self.mehrlageg_einlageg)
        elif self.nahtart == "BW" and self.nahtart2 =="FW" and self.produktform == "P":
             return "EN ISO 9606-1"+" "+self.schweißprozess.code+" "+"P"+" "+"FW"+" "+self.werkstoffgruppe_schweisszusatz_info.wsgr+" "+self.schweisszusatz.code+" "+"t"+str(self.werkstoffdicke_stück)+" "+str(self.schweißposition)+" "+str(self.mehrlageg_einlageg)             
        else:     
          if self.nahtart =="FW/BW" and self.produktform == "T":
             return "EN ISO 9606-1"+" "+self.schweißprozess.code+" "+"T"+" "+"FW/BW"+" "+self.werkstoffgruppe_schweisszusatz_info.wsgr+" "+self.schweisszusatz.code+" "+"D"+str(self.rohraussendurchmesser_stück)+" "+self.schweisspos.code  
              
    @fields.depends('nahtart','schweißprozess')
    def on_change_with_mehrlageg_einlageg(self,name=None):
      if self.schweißprozess:
        if(self.nahtart in ["FW","BW","FW/BW"] and self.schweißprozess.code == "311" ):
            tab1 = [(None, '')]
            tab1.append(("-","-"))
            tab1.append(("sl lw", "sl lw | einlagig, nach links Schweißen"))
            tab1.append(("sl rw", "sl rw | einlagig, nach rechts Schweißen"))
            tab1.append(("ml lw", "ml lw | mehrlagig nach links Schweißen"))
            tab1.append(("ml rw", "ml rw | mehrlagig nach rechts Schweißen"))
        else:
            tab1=[]
            tab1.append(("-","-"))
            tab1.append(("sl", "sl einlagig (für Kehlnähte)"))
            tab1.append(("ml", "ml mehrlagig (für Kehlnähte)"))
        return tab1
        
    @fields.depends('mehrlageg_einlageg')
    def on_change_mehrlageg_einlageg(self,name=None):
        if not self.mehrlageg_einlageg:
            raise UserError(gettext(
                'welding_certification.msg_mehrlageg_einlageg_not_empty',
                    mehrlageg_einlageg=self.mehrlageg_einlageg,
                    ))                    
                    
    @fields.depends('nahtart')
    def on_change_nahtart(self,name=None):
        if self.nahtart=="BW":
             raise UserError(gettext(
                      'welding_certification.msg_schweißnahteinzelheiten_unoccupied',
                      nahtart=self.nahtart))                 

    @fields.depends('gültigkeitsdauer_info','datum_schweissens')
    def on_change_with_gültigkeitsdauer(self,name=None):

        if(self.gültigkeitsdauer_info == "9.3a" and self.datum_schweissens):
           return self.datum_schweissens + datetime.timedelta(days=1095)
        elif(self.datum_schweissens):
           Date = Pool().get('ir.date')
           return datetime.date(Date.today().year, 1, 1)
        elif(self.gültigkeitsdauer_info == "9.3b" and self.datum_schweissens):
           return self.datum_schweissens + datetime.timedelta(days=730) 
        elif(self.gültigkeitsdauer_info == "9.3c" and self.datum_schweissens):
               return self.datum_schweissens+datetime.timedelta(days=180)

        else:
               return None
               
    @fields.depends('mehrlageg_einlageg','nahtart')           
    def on_change_with_mehrlageg_einlageg_geltungs(self,name=None):

        if(self.mehrlageg_einlageg == "ml" and self.nahtart == "FW"):
          return "sl, ml (ein-und mehrlagig)"
        else:
          if(self.mehrlageg_einlageg == "sl" and self.nahtart == "FW"):
            return "sl (einlagig)"
            
    @fields.depends('schweisszusatz','schweißprozess')
    def on_change_with_schweisszusatz_geltungs(self,name=None):
      if self.schweisszusatz and self.schweißprozess:
        if self.schweißprozess.code in ["121","131","135"]:
            if self.schweisszusatz.code == "S":
               return "S,M"
        elif self.schweißprozess.code in ["141","141/135","145"]:
            if self.schweisszusatz.code == "S":
               return "S, M, nm"
        elif self.schweißprozess.code == "141/136":
            if self.schweisszusatz.code in["S/R","S/P"]:
               return "141: S, M, nm; 136: R, P, V, W, Y, Z"
        elif self.schweißprozess.code in ["142","311"]:
            if self.schweisszusatz.code == "S":
               return "S, nm"
            elif self.schweisszusatz.code == "nm": 
               return "nm"   
            elif self.schweisszusatz.code == "M":
                   return "S, M, nm"   
            else:
               return ", nm"
        elif self.schweißprozess.code == "141/111":
            if self.schweisszusatz.code == "S/B":
               return "141: S, M, nm; 111: alle außer C"
            else:
               if self.schweisszusatz.code in["S/R","S/RB"]:
                   return "141: S, M, nm; 111: alle außer B und C"
        elif self.schweißprozess.code == "135/111":
            if self.schweisszusatz.code == "S/B":
                return "135:S; 111: alle außer C"
            else:
                if self.schweisszusatz.code == "S/R" or self.schweisszusatz.code == "S/RB":
                   return "135:S; 111: alle außer B und C"
        elif self.schweißprozess.code == "135/136":
            if self.schweisszusatz.code in ["S/R","S/P"]:
                   return "135: S; 136:R, P, V, W, Y, Z"
        elif self.schweißprozess.code in ["111/121","111/135","135/121","136/121","141/121","141/131"]:     
            if self.schweisszusatz.code == "S":
                   return "S"   
            else:
              if self.schweisszusatz.code == "M":
                   return "S, M"
        elif self.schweißprozess.code == "143":
            if self.schweisszusatz.code == "B":
                return "B ,R, P, V, W, Y, Z, nm" 
            elif self.schweisszusatz.code == "M":
                   return "S, M, nm"
            else:
              if self.schweisszusatz.code in ["P","R","V","W","Y","Z"]:
                   return "R, P, V, W, Y, Z, nm"
        elif self.schweißprozess.code in ["114","125","136","138"]:
            if self.schweisszusatz.code == "B" :
                   return "B ,R, P, V, W, Y, Z"
            elif self.schweisszusatz.code == "M":
                   return "S, M"
            else:    
                if self.schweisszusatz.code in ["P","R","V","W","Y","Z"]:
                   return "R, P, V, W, Y, Z"
        elif self.schweißprozess.code == "111":
                if self.schweisszusatz.code in ["A","RA","RC","RR","RB","R"]:
                   return "A, RA, RB, RC, RR, R"
                if self.schweisszusatz.code == "C":
                   return "Umhüllung C"
                if self.schweisszusatz.code in ["14","24","19","20","27"]:
                   return "03, 13, 14, 19, 20, 24, 27"
                if self.schweisszusatz.Code in ["18","28"]:
                   return "alle Umhüllungen außer 10 und 11"
                else:
                   if self.schweisszusatz.code == "B":
                      return "alle Umhüllungen außer C"
        elif self.schweißprozess.code == "15":   
                if self.schweisszusatz.code in ["M","B","S/B","S/R","S/RB","S/P","P","R","V","W","Y","nm/B","nm/S"]:
                   return ", nm" 
                elif self.schweisszusatz.code == "S":
                   return "S, M, nm"   
                else:   
                  if self.schweisszusatz.code == "nm":
                   return "nm"                     
        elif self.schweißprozess.code in ["311","142"]:
                if self.schweisszusatz.code in ["B","S/B","S/R","S/RB","S/P","P","R","V","W","Y","nm/B","nm/S"]:
                   return ", nm"                 
      else:
           return None               

    @fields.depends('werkstoffgruppe')
    def on_change_with_werkstoffgruppe_geltungs(self,name=None):
        if(self.werkstoffgruppe):
           return str(round(float(self.werkstoffgruppe),0))
           
    @fields.depends('produktform','rohraußendurchmesser')       
    def on_change_with_produktform_geltungs(self,name=None):
         if (self.produktform == "P"):
                    return "P, T: D>=500; rotierend ab D=75 mm"
         elif (self.produktform == "T" and self.rohraußendurchmesser > 25): 
                    return "T, P"
         else:
              if (self.produktform == "T" and self.rohraußendurchmesser <= 25):
                    return "T"
     
    @fields.depends('nahtart','nahtart2')
    def on_change_with_nahtart_geltungs(self,name=None):
        if(self.nahtart == "BW"and self.nahtart2 == "FW"):
           return "BW, FW"         
        elif(self.nahtart == "BW" and self.nahtart2 != "FW"):
           return "BW"
        elif(self.nahtart == "FW"):
           return "FW"
        elif(self.nahtart =="FW/BW"):
           return "BW, FW (siehe 5.4 b)"
           
        else:
           return None   

    @fields.depends('schweißnahteinzelheiten')
    def on_change_with_schweissnahteinzelheiten_geltungs(self,name=None):
        if(self.schweißnahteinzelheiten == "ss nb"):
                  return "ss nb, ss mb, bs, ss gb, ss fb"
        elif(self.schweißnahteinzelheiten == "bs"):
                  return "ss mb, bs"
        elif(self.schweißnahteinzelheiten == "ss gb"):
                  return "ss mb, bs, ss gb"
        elif(self.schweißnahteinzelheiten == "ci"):
                  return "ss mb, bs, ci"
        elif(self.schweißnahteinzelheiten == "ss fb"):
                  return "ss mb, bs, ss fb"

        elif(self.schweißnahteinzelheiten == "ss mb"):
                  return "ss mb, bs"
        else:
                  return None

    @fields.depends('werkstoffgruppe_schweisszusatz_info')               
    def on_change_with_werkstoffgruppe_schweisszusatz_geltungs(self,name=None):
        val=False
        if self.werkstoffgruppe_schweisszusatz_info:
              val=self.werkstoffgruppe_schweisszusatz_info.wsgr  
              if(val =="FM1"):
                    return "FM1, FM2"
              elif(val =="FM3"):
                    return "FM1, FM2, FM3"
              elif(val =="FM4"):
                    return "FM1, FM2, FM3, FM4"
              elif(val =="FM5"):
                    return "FM5"
              elif(val =="FM6"):
                    return "FM5, FM6"

              elif(val =="FM2"):
                  return "FM1, FM2"
        else:
            return None

    @fields.depends('dicke_des_schweißgutes','schweißprozess','wurzel','produktform','nahtart','nahtart2')        
    def on_change_with_dicke_des_schweißgutes_geltungs(self,name=None):       
      try:
       if self.schweißprozess :
        subract = float(self.dicke_des_schweißgutes) - float(self.wurzel)
        if(self.produktform == "P" and self.nahtart == "BW" and self.nahtart2 != "FW" and (self.schweißprozess.code in["111","114","121","125","131","135","136","138","141","142","143","145","15"])):
          if(float(self.dicke_des_schweißgutes) <= 1.5):
            return str(self.dicke_des_schweißgutes)+" bis 3 mm"
          elif(1.5<float(self.dicke_des_schweißgutes) <= 3):
            return str(self.dicke_des_schweißgutes)+" bis "+str(2*float(self.dicke_des_schweißgutes))+" mm"
          elif(3 < float(self.dicke_des_schweißgutes) < 12):
            return "3 bis "+str(2*float(self.dicke_des_schweißgutes))+" mm"
          else:
            if(float(self.dicke_des_schweißgutes) >= 12):
               return "s >= 3 mm"
        elif(self.produktform == "P" and self.nahtart == "BW" and self.nahtart2 == "FW" and (self.schweißprozess.code in ["111","114","121","125","131","135","136","138","141","142","143","145","15"])):
          if(float(self.dicke_des_schweißgutes) <= 1.5):
            return "Für BW: "+str(self.dicke_des_schweißgutes)+" bis 3 mm"
          elif( 1.5 < float(self.dicke_des_schweißgutes) <= 3):
            return "Für BW: "+str(self.dicke_des_schweißgutes)+" bis "+str(2*float(self.dicke_des_schweißgutes))+" mm"
          elif(3 < float(self.dicke_des_schweißgutes) < 12):
            return "Für BW: 3 bis "+str(2*float(self.dicke_des_schweißgutes))+" mm"
          else:
            if(float(self.dicke_des_schweißgutes) >= 12):
               return "Für BW: s >= 3 mm"
        elif(self.produktform == "P" and self.nahtart == "BW" and self.nahtart2 == "FW" and self.schweißprozess.code == "311"):
          if(float(self.dicke_des_schweißgutes) <= 3):
               return "Für BW: "+str(float(self.dicke_des_schweißgutes))+" bis "+str(round(1.5 * float(self.dicke_des_schweißgutes), 1))+" mm"
          elif(3 < float(self.dicke_des_schweißgutes) < 12):
              return "Für BW: 3 bis "+str(round(1.5 * float(self.dicke_des_schweißgutes), 1))+" mm"
          else:
            if(float(self.dicke_des_schweißgutes) >= 12):
               return "Für BW: s >= 3 mm"
        elif(self.produktform == "P" and self.nahtart == "BW" and (self.schweißprozess.code in ["111/121","111/135","135/111","135/121","135/136","136/121","141/111","141/121","141/131","141/135","141/136","142/111","142/131","142/135"])):
          var_aux = self.schweißprozess.code
          pos1 = var_aux.find("/")
          prozess1 = var_aux[0:pos1]
          prozess2 = var_aux[pos1+1:len(var_aux)]
          if(self.wurzel == "1"):
                  val_wurzel = "1-3"
          elif(self.wurzel == "2"):
                  val_wurzel = "2-4"
          elif(self.wurzel == "3"):
                  val_wurzel = "3-6"
          elif(self.wurzel == "4"):
                  val_wurzel = "3-8"
          else:
                  val_wurzel ="3-10"
          if(float(self.dicke_des_schweißgutes) <= 1.5): 
            if (float(subract) < 0):
              res_aux = str(float(self.dicke_des_schweißgutes))
              pos1 = res_aux.find(".")
              part2 = res_aux[pos1+1:len(res_aux)]
              if(part2 != "0" and part2 != "00"):
                 res = float(self.dicke_des_schweißgutes)
              else:
                 res = int(float(self.dicke_des_schweißgutes))
              return str(res)+" bis 3 mm;"+prozess1+":"+val_wurzel+"; "+prozess2+": (nur mb)" 
            elif (float(subract) == 0): 
              res_aux = str(2*float(self.dicke_des_schweißgutes))
              pos1 = res_aux.find(".")
              part2 = res_aux[pos1+1:len(res_aux)]
              if(part2 != "0" and part2 != "00"):
                 res = 2*float(self.dicke_des_schweißgutes)
              else:
                 res = int(2*float(self.dicke_des_schweißgutes))
              return "1 bis 3 mm; "+prozess1+": "+val_wurzel+"; "+prozess2+": 0-3 (nur mb)"      
            else:
             if(float(subract) > 0):
                 res = round((float(self.dicke_des_schweißgutes) - int(self.wurzel)),1)
                 return str(self.dicke_des_schweißgutes)+" bis 3 mm;"+prozess1+":"+val_wurzel+"; "+prozess2+": "+str(res)+"-3 nur mb"
          elif(float(self.dicke_des_schweißgutes) > 1.5 and float(self.dicke_des_schweißgutes) < 3):
            if (float(subract) < 0):
              res_aux = str(float(self.dicke_des_schweißgutes))
              pos1 = res_aux.find(".")
              part2 = res_aux[pos1+1:len(res_aux)]
              if(part2 != "0" and part2 != "00"):
                 res = float(self.dicke_des_schweißgutes)
              else:
                 res = int(float(self.dicke_des_schweißgutes))
                 return str(res)+" bis "+str(2*res)+"mm; "+prozess1+": "+val_wurzel+"; "+prozess2+": (nur mb)"
            elif(0.1 < float(subract) < 0.4 or 0.5 < float(subract) < 1 or 1.1 < float(subract) < 1.5):
                 res_aux = str(float(self.dicke_des_schweißgutes))
                 pos1 = res_aux.find(".")
                 part2 = res_aux[pos1+1:len(res_aux)]
                 if(part2 != "0" and part2 != "00"):
                     res = float(self.dicke_des_schweißgutes)
                 else:
                     res = int(float(self.dicke_des_schweißgutes))
                 res1 = round((float(self.dicke_des_schweißgutes) - int(self.wurzel)),1)
                 return str(res)+" bis "+str(2*res)+"mm; "+prozess1+": "+val_wurzel+"; "+prozess2+": "+str(res1)+" - 3 nur m"
            elif(1.5 < float(subract) < 3):
                 res_aux = str(float(self.dicke_des_schweißgutes))
                 pos1 = res_aux.find(".")
                 part2 = res_aux[pos1+1:len(res_aux)]
                 if(part2 != "0" and part2 != "00"):
                     res = float(self.dicke_des_schweißgutes)
                 else:
                     res = int(float(self.dicke_des_schweißgutes))
                 res1 = round((float(self.dicke_des_schweißgutes) - int(self.wurzel)),1)
                 return str(res)+" bis "+str(2*res)+"mm; "+prozess1+": "+val_wurzel+"; "+prozess2+": "+str(res1)+" - "+str(2*res1)+" nur"
            elif (float(subract) == 1.5):
              res_aux = str(float(self.dicke_des_schweißgutes))
              pos1 = res_aux.find(".")
              part2 = res_aux[pos1+1:len(res_aux)]
              if(part2 != "0" and part2 != "00"):
                 res = float(self.dicke_des_schweißgutes)
              else:
                 res = int(float(self.dicke_des_schweißgutes))
              res1 = round(float(self.dicke_des_schweißgutes) - int(self.wurzel),2)
              return str(res)+" bis "+str(2*res)+"mm; "+prozess1+": "+val_wurzel+"; "+prozess2+": "+str(res1)+" - "+str(2*res1)+" nur mb"          
            elif (float(subract) == 0): 
              res_aux = str(2*float(self.dicke_des_schweißgutes))
              pos1 = res_aux.find(".")
              part2 = res_aux[pos1+1:len(res_aux)]
              if(part2 != "0" and part2 != "00"):
                 res = float(self.dicke_des_schweißgutes)
              else:
                 res = int(float(self.dicke_des_schweißgutes))
              return str(res)+" bis "+str(2*res)+"mm; "+prozess1+": "+val_wurzel+"; "+prozess2+": 0-3 (nur mb)" 
            else:
             if (float(subract)  == 2):    
              res_aux = str(float(self.dicke_des_schweißgutes))
              pos1 = res_aux.find(".")
              part2 = res_aux[pos1+1:len(res_aux)]
              if(part2 != "0" and part2 != "00"):
                 res = float(self.dicke_des_schweißgutes)
              else:
                 res = int(float(self.dicke_des_schweißgutes))
                 res_aux1 = str(float(float(self.dicke_des_schweißgutes) - int(self.wurzel)))
                 pos11 = res_aux1.find(".")
                 part21 = res_aux1[pos11+1:len(res_aux1)]
                 if(part21 != "0" and part21 != "00"):
                    res1 = round(float(float(self.dicke_des_schweißgutes) - int(self.wurzel)),2)
                 else:
                    res1 = int(float(float(self.dicke_des_schweißgutes) - int(self.wurzel)))
              return str(res)+" bis "+str(2*res)+"mm; "+prozess1+": "+val_wurzel+"; "+prozess2+": "+str(res1)+" - "+str(2*res1)+" (nur mb)"
          elif(3 <= float(self.dicke_des_schweißgutes) < 12)  :          
          
            if (float(subract) < 0):
              res_aux = str(2*float(self.dicke_des_schweißgutes))
              pos1 = res_aux.find(".")
              part2 = res_aux[pos1+1:len(res_aux)]
              if(part2 != "0" and part2 != "00"):
                 res = 2*float(self.dicke_des_schweißgutes)
              else:
                 res = int(2*float(self.dicke_des_schweißgutes))
              return "3 bis "+str(res)+"mm; "+prozess1+": "+val_wurzel+"; "+prozess2+": (nur mb)"
            elif (float(subract) == 0): 
              res_aux = str(2*float(self.dicke_des_schweißgutes))
              pos1 = res_aux.find(".")
              part2 = res_aux[pos1+1:len(res_aux)]
              if(part2 != "0" and part2 != "00"):
                 res = 2*float(self.dicke_des_schweißgutes)
              else:
                 res = int(2*float(self.dicke_des_schweißgutes))
              return "3 bis "+str(res)+"mm; "+prozess1+": "+val_wurzel+"; "+prozess2+": 0-3 (nur mb)"
            elif(2 < float(subract) < 2.5 or 2.5 < float(subract) < 3 ):
              res_aux = str(2*float(self.dicke_des_schweißgutes))
              pos1 = res_aux.find(".")
              part2 = res_aux[pos1+1:len(res_aux)]
              if(part2 != "0" and part2 != "00"):
                 res = 2*float(self.dicke_des_schweißgutes)
              else:
                 res = int(2*float(self.dicke_des_schweißgutes))
              res1 = round(float(self.dicke_des_schweißgutes) - int(self.wurzel),2)
              return "3 bis "+str(res)+"mm; "+prozess1+": "+val_wurzel+"; "+prozess2+": "+str(res1)+" - "+str(2*res1)+" nur m"
            elif(3 < float(subract) < 3.5 or 3.5 < float(subract) < 4 or 4 < float(subract) < 4.5 or 4.5 < float(subract) < 5):  
              res_aux = str(2*float(self.dicke_des_schweißgutes))
              res1 = round(float(float(self.dicke_des_schweißgutes) - int(self.wurzel)),1)
              pos1 = res_aux.find(".")
              part2 = res_aux[pos1+1:len(res_aux)]
              if(part2 != "0" and part2 != "00"):
                 res = 2*float(self.dicke_des_schweißgutes)   
              else:
                 res = int(2*float(self.dicke_des_schweißgutes))
              return "3 bis "+str(res)+"mm; "+prozess1+": "+val_wurzel+"; "+prozess2+": 3 - "+str(2*res1)+" nur mb"
            elif(5 < float(subract) < 5.5 or 5.5 < float(subract) < 6 or 6 < float(subract) < 6.5 or 6.5 < float(subract) < 7 or 7 < float(subract) < 7.5 or 7.5 < float(subract) < 8 or 8 < float(subract) < 8.5 or 8.5 < float(subract) < 9  or 9 < float(subract) < 9.5 or 9.5 < float(subract) < 10 or 10 < float(subract) < 10.5 or 10.5 < float(subract) < 11) :  
              res_aux = str(2*float(self.dicke_des_schweißgutes))
              res1 = round(float(float(self.dicke_des_schweißgutes) - int(self.wurzel)),1)
              pos1 = res_aux.find(".")
              part2 = res_aux[pos1+1:len(res_aux)]
              if(part2 != "0" and part2 != "00"):
                 res = 2*float(self.dicke_des_schweißgutes)   
              else:
                 res = int(2*float(self.dicke_des_schweißgutes))
              return "3 bis "+str(res)+"mm; "+prozess1+": "+val_wurzel+"; "+prozess2+": 3 - "+str(2*res1)+" nur m"  
            else:
              res_aux = str(2*float(self.dicke_des_schweißgutes))
              pos1 = res_aux.find(".")
              part2 = res_aux[pos1+1:len(res_aux)]
              if(part2 != "0" and part2 != "00"):
                 res = 2*float(self.dicke_des_schweißgutes)                   
              else:
                 res = int(2*float(self.dicke_des_schweißgutes))
                 res_aux1 = str(float(float(self.dicke_des_schweißgutes) - int(self.wurzel)))
                 pos11 = res_aux1.find(".")
                 part21 = res_aux1[pos11+1:len(res_aux1)]
                 if(part21 != "0" and part21 != "00"):
                    res1 = round(float(float(self.dicke_des_schweißgutes) - int(self.wurzel)), 1)
                 else:
                    res1 = int(float(float(self.dicke_des_schweißgutes) - int(self.wurzel)))
              return "3 bis "+str(res)+"mm; "+prozess1+": "+val_wurzel+"; "+prozess2+":"+str(res1)+"-"+str(2*res1)+" (nur mb)"
          elif(float(self.dicke_des_schweißgutes) >= 12 and float(subract) < 12):
              res_aux = str(2*(float(self.dicke_des_schweißgutes) - int(self.wurzel)))
              pos1 = res_aux.find(".")
              part2 = res_aux[pos1+1:len(res_aux)]
              if(part2 != "0" and part2 != "00"):
                 res = 2*(float(self.dicke_des_schweißgutes) - int(self.wurzel))
              else:
                 res = int(2*(float(self.dicke_des_schweißgutes) - int(self.wurzel)))
              return "s >= 3 mm; "+prozess1+": "+val_wurzel+"; "+prozess2+": 3- "+str(res)+" (nur mb)"
          elif(float(self.dicke_des_schweißgutes) > 12 and float(subract) > 12):
              return "s >= 3 mm; "+prozess1+": "+val_wurzel+"; "+prozess2+" t >= 3 (nur mb)"
          else:
              return None
        else:
          if(self.produktform == "P" and self.nahtart == "BW" and self.nahtart2 != "FW" and self.schweißprozess.code == "311"):
            if(float(self.dicke_des_schweißgutes) <= 3):
              res_aux = str(1.5*float(self.dicke_des_schweißgutes))
              pos1 = res_aux.find(".")
              part2 = res_aux[pos1+1:len(res_aux)]
              if(part2 != "0" and part2 != "00"):
                 res = round(1.5 * float(self.dicke_des_schweißgutes), 1) 
                 return str(float(self.dicke_des_schweißgutes))+" bis "+str(res)+" mm"
              else:
                 res = int(1.5*float(self.dicke_des_schweißgutes))
                 return str(int(float(self.dicke_des_schweißgutes)))+" bis "+str(res)+" mm"
            elif(float(self.dicke_des_schweißgutes) > 3 and float(self.dicke_des_schweißgutes) < 12):
              res_aux = str(1.5*float(self.dicke_des_schweißgutes))
              pos1 = res_aux.find(".")
              part2 = res_aux[pos1+1:len(res_aux)]
              if(part2 != "0" and part2 != "00"):
                 res = round(1.5 * float(self.dicke_des_schweißgutes), 1)
              else:
                 res = int(1.5*float(self.dicke_des_schweißgutes))
              return "3 bis "+str(res)+" mm"
            else:
              if(float(self.dicke_des_schweißgutes) >= 12):
                 return "s >= 3 mm"
      except Exception:
        return None  


    @fields.depends('werkstoffdicke','nahtart','nahtart2')
    def on_change_with_werkstoffdicke_geltungs(self,name=None):
      try:
        if(float(self.werkstoffdicke) <= 1.5 and  self.nahtart == "FW" ):
                  return str(self.werkstoffdicke)+" bis 3 mm"       
        elif(float(self.werkstoffdicke) <= 1.5 and self.nahtart == "BW" and self.nahtart2 == "FW"):
                  return "für FW : "+ str(self.werkstoffdicke)+" bis 3 mm"
        elif(float(self.werkstoffdicke) >= 3 and self.nahtart == "FW"):
                  return "t >= 3 mm"
        elif(float(self.werkstoffdicke) >= 3 and self.nahtart == "BW" and self.nahtart2 == "FW"):
                  return " für FW : t >= 3 mm"
        elif(1.5<float(self.werkstoffdicke)< 3 and self.nahtart == "BW" and self.nahtart2 == "FW"):
                  return "für FW : "+str(self.werkstoffdicke)+" bis "+str(2*float(self.werkstoffdicke))+"mm"
        elif(1.5<float(self.werkstoffdicke)< 3 and self.nahtart == "FW"):
                  return str(self.werkstoffdicke)+" bis "+str(2*float(self.werkstoffdicke))+"mm"
      except Exception:
        return None             
    @fields.depends('schweisspos','schweißposition','nahtart','produktform')
    def on_change_with_schweißposition_geltungs(self,name=None):
        if self.schweisspos :
            if(self.schweisspos.code == "PA" and self.nahtart in ["BW","FW"] and self.produktform in ["P","T"] and self.schweißposition == "None"):
                  return "PA"
            elif(self.schweisspos.code == "PC" and self.nahtart == "BW" and self.produktform in ["P","T"]):
                  return "PA, PC"
            elif(self.schweisspos.code == "PE" and self.nahtart == "BW" and self.produktform == "P"):
                  return "PA, PC, PE"
            elif(self.schweisspos.code == "PF" and self.nahtart == "BW" and self.produktform == "P" and self.schweißposition == "None"):
                  return "PA, PF"
            elif(self.schweisspos.code == "PA" and self.nahtart == "BW" and self.produktform == "P" and self.schweißposition == "PC"):
                  return "PA, PC"
            elif(self.schweisspos.code == "PA" and self.nahtart == "BW" and self.produktform == "P" and self.schweißposition == "PF"):
                  return "PA, PF"      
            elif(self.schweisspos.code == "PF" and self.nahtart == "BW" and self.produktform == "P" and self.schweißposition == "PC"):
                  return "PA, PC, PF"
            elif(self.schweisspos.code == "PG"  and self.nahtart in ["BW","FW"] and self.produktform == "P"):
                  return "PG"
            elif(self.schweisspos.code == "PH" and self.nahtart == "BW" and self.produktform == "T" and self.schweißposition == "None"):
                  return "PA, PE, PF, PH"
            elif(self.schweisspos.code == "PJ" and self.nahtart == "BW" and self.produktform == "T" and self.schweißposition == "None"):
                  return "PA, PE, PG, PJ"
            elif(self.schweisspos.code == "H-L045" and self.nahtart == "BW" and self.produktform == "T"):
                  return "PA, PC, PE,PF, PH, H-L045"
            elif(self.schweisspos.code == "PH" and self.nahtart == "BW" and self.produktform == "T" and self.schweißposition == "PC"):
                  return "PA, ,PC, PE, PF, PH, H-L045"
            elif(self.schweisspos.code == "PJ" and self.nahtart == "BW" and self.produktform == "T" and self.schweißposition == "PC"):
                  return "PA, PC, PE, PG, PJ, J-L045"
            elif(self.schweisspos.code == "J-L045" and self.nahtart == "BW" and self.produktform == "T"):
                  return "PA, PC, PE,PG, PJ, J-L045"
            elif(self.schweisspos.code == "PB" and self.nahtart == "FW" and self.produktform in ["P","T"] and self.schweißposition == "None"):
                  return "PA, PB"     
            elif(self.schweisspos.code == "PB" and self.nahtart == "FW" and self.produktform == "P" and self.schweißposition == "PF"):
                  return "PA, PB, PF"     
            elif(self.schweisspos.code == "PC" and self.nahtart == "FW" and self.produktform in ["P","T"]):
                  return "PA, PB, PC"
            elif(self.schweisspos.code == "PD" and self.nahtart == "FW" and self.produktform in ["P","T"]):
                  return "PA, PB, PC, PD, PE"
            elif(self.schweisspos.code == "PE" and self.nahtart == "FW" and self.produktform == "P"):
                  return "PA, PB, PC, PD, PE"   
            elif(self.schweisspos.code in [ "PF" ,"PB/PF"]and self.nahtart == "FW" and self.produktform == "P"):
                  return "PA, PB, PF" 
            elif(self.schweisspos.code == "PH" and self.nahtart == "FW" and self.produktform == "T"):
                  return "PA, PB, PC, PD, PE, PF, PH"                  
            else:
                if(self.schweisspos.code == "PJ" and self.nahtart == "FW" and self.produktform == "T"):
                  return "PA, PB, PD, PE, PG, PJ" 
         
    @fields.depends('rohraußendurchmesser','rohraussendurchmesser_stück','produktform','nahtart','nahtart2')
    def on_change_with_rohraußendurchmesser_geltungs(self,name=None):
      try:
        if(float(self.rohraußendurchmesser) <= 25 and self.produktform == "T" and self.nahtart2 != "FW"):
                  return str(self.rohraußendurchmesser)+" bis "+str(2*(float(self.rohraußendurchmesser)))+" mm"
        elif(float(self.rohraußendurchmesser) > 25 and self.produktform == "T" and (0.5*(float(self.rohraußendurchmesser)))>25 and self.nahtart2 != "FW"):
                  return "D >="+str(0.5*(float(self.rohraußendurchmesser)))+" mm"
        elif(float(self.rohraußendurchmesser) <= 25 and float(self.rohraussendurchmesser_stück) <= 25 and self.produktform == "T" and self.nahtart2 == "FW"):
              if(self.rohraußendurchmesser < self.rohraussendurchmesser_stück):
                  return str(self.rohraußendurchmesser)+" bis "+str(2*self.rohraussendurchmesser_stück)+" mm"
              else:
                  return str(self.rohraussendurchmesser_stück)+" bis "+str(2*self.rohraußendurchmesser)+" mm"
        elif(float(self.rohraußendurchmesser) <= 25 and float(self.rohraussendurchmesser_stück) > 25 and self.produktform == "T" and self.nahtart2 == "FW"):
                  return "D >= "+str(self.rohraußendurchmesser)+" mm"
        elif(float(self.rohraußendurchmesser) > 25 and float(self.rohraussendurchmesser_stück) <= 25 and self.produktform == "T" and self.nahtart2 == "FW"):
                  return "D >= "+str(self.rohraussendurchmesser_stück)+" mm"
        elif(((25 <= float(self.rohraußendurchmesser) <= 50 and float(self.rohraussendurchmesser_stück) >= 50) or (25 <= float(self.rohraussendurchmesser_stück) <= 50 and float(self.rohraußendurchmesser) >= 50 )or (25 <= float(self.rohraussendurchmesser_stück) <= 50 and 25 <= float(self.rohraußendurchmesser) <= 50 )) and self.produktform == "T" and self.nahtart2 == "FW"):
                  return "D >= 25 mm"
        elif(float(self.rohraußendurchmesser) > 50 and float(self.rohraussendurchmesser_stück) > 50 and self.produktform == "T" and self.nahtart2 == "FW"):
              if(float(self.rohraußendurchmesser) < float(self.rohraussendurchmesser_stück)):
                  return "D >= "+ str(0.5 * float(self.rohraußendurchmesser))+" mm"
              else:
                  return "D >= "+ str(0.5 * float(self.rohraussendurchmesser_stück))+" mm"
        elif(float(self.rohraußendurchmesser) > 25 and self.produktform == "T" and (0.5*(float(self.rohraußendurchmesser)))<25 and self.nahtart2 != "FW"):        
                  return "D >=25 mm"           
        else:
         if(self.produktform == "P"  and self.nahtart in ["BW","FW","FW/BW"]):
                  return "D >= 500 mm"
      except Exception:
         return None             
    @fields.depends('artdeswerkstoff','schweißprozess')
    def on_change_with_artdeswerkstoff_geltungs(self,name=None):
        if( self.schweißprozess and (self.schweißprozess.code in ["131","111/135","135/111","135","135/121","135/136","136/121","138","141/131","141/135","141/136","142/131","142/135"])):
              if (self.artdeswerkstoff == "D-Übergang"):
                   return "D,G,S,P (alle)"
              elif (self.artdeswerkstoff == "G-großtropfiger Übergang Langlichtbogen"):
                   return "G - großtropfig"
              elif (self.artdeswerkstoff == "S-feintropfiger Übergang Sprühlichtbogen") :    
                   return "S - feintropfig"
              elif(self.artdeswerkstoff == "P-impulsgesteuerter Übergang Impulslichtbogen"):
                   return "P - impulsgesteuert"
        else:
              return None                   

    @fields.depends('schweißprozess')
    def on_change_with_schweißprocess_geltungs(self,name=None):      
      value_schweißprozess = False
      if self.schweißprozess :
        value_schweißprozess = self.schweißprozess.code
        if(value_schweißprozess == "111"):
                   return "111"
        elif(value_schweißprozess == "111/121"):
                   return "111 / 121, 125"
        elif(value_schweißprozess == "111/135"):
                   return "111 / 135, 138"
        elif(value_schweißprozess == "114"):
                   return "114"
        elif(value_schweißprozess== "121"):
                   return "121, 125"
        elif(value_schweißprozess == "125"):
                   return "125, 121"
        elif(value_schweißprozess == "135/111"):
                   return "135, 138 / 111"
        elif(value_schweißprozess == "135/121"):
                   return "135, 138 / 121, 125"
        elif(value_schweißprozess == "135/136"):
                   return "135, 138 / 136"
        elif(value_schweißprozess == "15"):
                   return "15"
        elif(value_schweißprozess == "135"):
                   return "135, 138"
        elif(value_schweißprozess == "136"):
                   return  "136"
        elif(value_schweißprozess == "136/121"):
                   return  "136 / 121, 125"
        elif(value_schweißprozess == "138"):
                   return "135, 138"
        elif(value_schweißprozess == "141/111"):
                   return "141, 142, 143, 145 / 111"
        elif(value_schweißprozess == "141/121"):
                   return "141, 142, 143, 145 / 121, 125"
        elif(value_schweißprozess == "141/131"):
                   return "141 / 131"
        elif(value_schweißprozess == "141/135"):
                   return "141, 142, 143, 145 / 135, 138"
        elif(value_schweißprozess == "141/136"):
                   return "141, 142, 143, 145 / 136"
        elif(value_schweißprozess == "142"):
                   return "142"
        elif(value_schweißprozess == "142/111"):
                   return "142 / 111"
        elif(value_schweißprozess == "142/131"):
                   return "142 / 131"
        elif(value_schweißprozess == "142/135"):
                   return "142 / 135"
        elif(value_schweißprozess == "311"):
                   return "311"
        elif(value_schweißprozess == "143"):
                   return "141, 142, 143 und 145"
        elif(value_schweißprozess == "145"):
                   return "141, 142, 143 und 145"           

        elif(value_schweißprozess == "131"):
                   return "131"   
        else:
                   return "141, 142, 143 und 145"
      else:
                   return None
                   
    def get_rec_name(self, name):
      if self.bezeichnung1:
        return self.bezeichnung1
      else:
        return None
        
    @classmethod
    def search_rec_name(cls, name, clause):
        return [('schweißanweisung_wps.rec_name',) + tuple(clause[1:])]
        
class Tropfenuebergang(ModelSQL, ModelView):
    'Tropfenuebergang'
    __name__ = 'welding.tropfenuebergang'
    _order_name = 'rec_name'
    code = fields.Char('Code', translate=True,required=True)
    name = fields.Char('Name', translate=True)
    beschreibung = fields.Char('Beschreibung', translate=True)
    def get_rec_name(self, name):
        return self.code
    
    @classmethod
    def __setup__(cls):
        super().__setup__()
        t = cls.__table__()
        cls._sql_constraints += [
            ('Tropfenuebergang_code_unique', Unique(t,t.name,t.code),
            'welding_certification.msg_bezeichung_gas_unique'),
            ]    

class WeldingClass(ModelSQL, ModelView):
    'welding Class'
    __name__ = 'welding.class'
    _order_name = 'rec_name'

    cpinfo = fields.Char('CP', translate=True,required=True)
    beschreibung = fields.Char('Beschreibung', translate=True)
    ct = fields.Char('CT', translate=True )
    prufumfang = fields.Char('Prüfumfang', translate=True)

    def get_rec_name(self, name):
        return self.cpinfo
        
    @classmethod
    def __setup__(cls):
        super().__setup__()
        cls._order.insert(0, ('beschreibung', 'ASC'))
    @classmethod
    def order_rec_name(cls, tables):
        table, _ = tables[None]
        return [table.code]      
class GrundwerkstoffProperties(ModelSQL, ModelView):
    'Grundwerkstoff Properties'
    __name__ = 'welding.grundwerkstoff_properties'
    _order_name = 'rec_name'
    bezeichnung = fields.Char('Bezeichnung', translate=True,required=True)
    norm = fields.Char('NORM', translate=True)
    nummer = fields.Char('NUMMER', translate=True)
    werkstoffgruppe = fields.Char('WERKSTOFFGRUPPE', translate=True)
    archiv = fields.Char('ARCHIV', translate=True)
    bem_wnr = fields.Char('BEM_WNR', translate=True)
    name_din = fields.Char('NAME_DIN', translate=True)
    tens_strength = fields.Char('TENS_STRENGTH', translate=True)
    wsart = fields.Char('WSART', translate=True)

    def get_rec_name(self, name):
        return self.bezeichnung
        
    @classmethod
    def __setup__(cls):
        super().__setup__()
        cls._order.insert(0, ('bezeichnung', 'ASC'))    

class SchweißanweisungWpsEinzelheitenSchweissen(DeactivableMixin, sequence_ordered(), ModelSQL, ModelView):
    "Einzelheiten Schweißenn"
    __name__ = 'welding.schweißanweisung_wps.einzelheiten_schweißenn'

    schweißraupee = fields.Char('SchweißRaupee')
    schweiszusaetze = fields.Char('Schweißzusätze')
    stromst = fields.Char('Stromstärke[A]')
    spannung = fields.Char('Spannung [V]')
    schweissprozess = fields.Selection([
        ('1', '1'),
        ('101²)', '101²)'),
        ('11', '11'),
        ('111 || E', '111 || E'),
        ('112 || SK', '112 || SK'),
        ('113¹)', '113¹)'),
        ('114 || MF', '114 || MF'),
        ('115¹)', '115¹)'),
        ('118¹)', '118¹)'),
        ('12 || UP', '12 || UP'),
        ('121 || UP', '121 || UP'),
        ('122 || UP', '122 || UP'),
        ('123²) || UP', '123²) || UP'),
        ('124 || UP', '124 || UP'),
        ('125 || UP', '125 || UP'),
        ('126 || UP', '126 || UP'),
        ('13 || MSG', '13 || MSG'),
        ('131 || MIG', '131 || MIG'),
        ('132 || MIG', '132 || MIG'),
        ('133 || MIG', '133 || MIG'),
        ('135 || MAG', '135 || MAG'),
        ('136 || MAG', '136 || MAG'),
        ('137²)', '137²)'),
        ('138 || MAG', '138 || MAG'),
        ('14 || WSG', '14 || WSG'),
        ('141 || WIG', '141 || WIG'),
        ('142 || WIG', '142 || WIG'),
        ('143 || WIG', '143 || WIG'),
        ('145 || WIG', '145 || WIG'),
        ('146 || WIG', '146 || WIG'),
        ('147', '147'),
        ('149¹)', '149¹)'),
        ('15 || WPL', '15 || WPL'),
        ('151', '151'),
        ('152', '152'),
        ('153', '153'),
        ('154', '154'),
        ('155', '155'),
        ('18²)', '18²)'),
        ('181¹)', '181¹)'),
        ('185', '185'),
    ], 'Schweißprozess ISO 4063')
    schweiszusaetze_1 = fields.Selection([
        ('1,2', '1,2'),
        ('1.6', '1.6'),
        ('1/8 in.', '1/8 in.'),
        ('16 mm', '16 mm'),
        ('2,5', '2,5'),
        ('3', '3'),
        ('∅1,0', '∅1,0'),
    ], 'Schweißzusätz(e) O[mm]')
    schweiszusaetze_2 = fields.Selection([
  ('Ohne', 'Ohne'),
        ('=SZ1', '=SZ1'),
        ('=SZ2', '=SZ2'),
        ('=SZ3', '=SZ3'),
        ('N.N', 'N.N'),
    ], 'Schweißzusätz(e) Index für Fabrikat')


    stromart_polung = fields.Selection([
        ('AC', 'AC'),
        ('DC -', 'DC -'),
        ('DC +', 'DC +'),
        ('G/-', 'G/-'),
        ('G/+', 'G/+'),
        ('=/+', '=/+'),
        ('=/-', '=/-'),
    ], 'Stromart/Polung')

    drahtvorschub = fields.Char('Drahtvorschub[m/min]')
    vorschub_geschwindigkeit = fields.Char('Vorschub-geschwindigkeit ¹) [cm/min]')
    waermeeinbringung = fields.Char('Wärmeeinbringung ¹) [kJoule/cm]')
    schweißanweisung_wps = fields.Many2One('welding.schweißanweisung_wps','Schweißanweisung WPS',select=True)

    @staticmethod
    def default_schweißraupee():
        return 1   
class WolframelektrodenartData(ModelSQL, ModelView):
    'Wolframelektrodenart Data'
    __name__ = 'welding.wolframelektrodenart_data'
    _order_name = 'rec_name'
    kurzzeichen = fields.Char('Kurzzeichen', translate=True,required=True)
    hauptoxide = fields.Char('Hauptoxide', translate=True)
    gehalt = fields.Char('Gehalt', translate=True)
    kennfarbe = fields.Char('Kennfarbe', translate=True)
    farbwert = fields.Char('Farbwert', translate=True)

    def get_rec_name(self, name):
        return self.kurzzeichen

class Wolframelektrodenart2Properties(ModelSQL, ModelView):
    'Wolframelektrodenart2 Properties'
    __name__ = 'welding.wolframelektrodenart2_properties'
    _order_name = 'rec_name'
    durchmesser = fields.Char('Durchmesser', translate=True,required=True)
    toleranz = fields.Char('Toleranz', translate=True)
    dc_minus = fields.Char('DC (-)', translate=True)
    dc_plus = fields.Char('DC (+)', translate=True)
    ac = fields.Char('AC', translate=True)

    def get_rec_name(self, name):
        return self.durchmesser

class WpqrNr(ModelSQL, ModelView):
    'Wpqr'
    __name__ = 'welding.wpqr_nr'
    _order_name = 'rec_name'
    beleg_pruf = fields.Char('Beleg-Nr der prüfstelle', translate=True,required=True)
    beleg_hersteller = fields.Char('Beleg-Nr der Herstellers', translate=True)

    def get_rec_name(self, name):
        return self.beleg_pruf          
 
 
class ProcessIso4063(ModelSQL,ModelView):
    'Process Iso 4063'
    __name__ = 'welding.process_iso4063'
    _order_name = 'rec_name'
    code1 = fields.Char('Code', translate=True,required=True)
    code2 = fields.Char('Name', translate=True)
    beschreibung = fields.Char('Beschreibung', translate=True)

    def get_rec_name(self, name):
        return self.code1 

class Erzeugnis(ModelSQL, ModelView):
    'Erzeugnis'
    __name__ = 'welding.erzeugnis'
    _order_name = 'rec_name'
    erzeugnis = fields.Char('Erzeugnis', translate=True,required=True)
    projekt_nr = fields.Char('Projekt-Nr', translate=True)
    zeichn_nr = fields.Char('Zeichn-Nr', translate=True)

    def get_rec_name(self, name):
        return self.erzeugnis
 
class SziData(ModelSQL, ModelView):
    'Szi Data'
    __name__ = 'welding.szi_data'
    _order_name = 'rec_name'
    bezeichnung = fields.Char('Bezeichnung', translate=True,required=True)
    norm = fields.Char('Norm', translate=True)
    werkstoffgruppe = fields.Char('FM?', translate=True)
    handelsname = fields.Char('Handelsname', translate=True)
    hersteller = fields.Char('Hersteller', translate=True)
    eignung = fields.Char('Eignung', translate=True)
    def get_rec_name(self, name):
        return self.bezeichnung

class SchweisspositionIso6947(ModelSQL,ModelView):
    'Schweissposition Iso6947'
    __name__ = 'welding.schweissposition_iso6947'
    _order_name = 'rec_name'
    code = fields.Char('code', translate=True,required=True)
    name = fields.Char('Name', translate=True)
    beschreibung = fields.Char('Beschreibung', translate=True)
    
    @classmethod
    def __setup__(cls):
        super(SchweisspositionIso6947, cls).__setup__()
        cls._order.insert(0, ('code', 'ASC'))    

    def get_rec_name(self, name):

          return self.code


class NahtNr(ModelSQL,ModelView):
    'Naht_Nr'
    __name__ = 'welding.naht_nr'
    _order_name = 'rec_name'
    rechts_name = fields.Char('Name', translate=True
        )
    def get_rec_name(self, name):
        return self.rechts_name  

class Schweisszusatz(ModelSQL,ModelView):
    'Schweisszusatz'
    __name__ = 'welding.schweißzusatz'
    _order_name = 'rec_name'
    code = fields.Char('code', translate=True,required=True)
    beschreibung = fields.Char('Beschreibung', translate=True)

    def get_rec_name(self, name):
        return self.code 


class ListGasMischgase(ModelSQL,ModelView):
    'List_Gas_Mischgase'
    __name__ = 'welding.list_gas_mischgase'
    _order_name = 'rec_name'
    bezeichung = fields.Char('Bezeichung', translate=True,required=True)
    norm = fields.Char('Norm', translate=True)
    handelsname = fields.Char('Handelsname', translate=True)
    eignung = fields.Char('Eignung', translate=True)
    
        
    def get_rec_name(self, name):
        return self.bezeichung


class BildsProperties(
        DeactivableMixin, ModelSQL, ModelView):
    "Bilds Properties"
    __name__ = 'welding.bilds_properties'
    _order_name = 'rec_name'

    bild = fields.Binary('Bild')
    name = fields.Char('Name')
    rechts_name = fields.Char('Rechts Bild Name')
    norm1 = fields.Char('Norm 1')
    norm2 = fields.Char('Norm 2')
    def get_rec_name(self, name):
        return self.name

class SchweißfolgenProperties(
        DeactivableMixin, ModelSQL, ModelView):
    "Bilds Properties"
    __name__ = 'welding.schweißfolgen_properties'
    _order_name = 'rec_name'

    bild = fields.Binary('Bild')
    name = fields.Char('Name')
    
    def get_rec_name(self, name):
        return self.name
                
class Hinweise(ModelSQL,ModelView):
    'Hinweise'
    __name__ = 'welding.hinweise'

    kurzform = fields.Char("Kurzform")
    bemerkungen = fields.Text("Bemerkungen (3 zeilig möglich)")

    def get_rec_name(self,name):
        return self.kurzform

class Pruefstelle(ModelSQL,ModelView):
    'Pruefstelle'
    __name__ = 'welding.pruefstelle'

    prüfstelle = fields.Char("Prüfstelle")
    land = fields.Char("Land")
    art = fields.Char("Art")
    plz = fields.Char("PLZ")
    ort = fields.Char("Ort")
    prüfer = fields.Char("Prüfer")
    prüf_nr = fields.Char("Prüf-Nr")
    def get_rec_name(self,name):
        return self.prüfstelle


class WerkstoffgruppeSchweißzusatz(ModelSQL, ModelView):
    'werkstoffgruppe schweißzusatz'
    __name__ = 'welding.werkstoffgruppe_schweißzusatz'

    szw_zum_schweißen_von = fields.Char("Schweißzusatz-Gr. zum Schweißen von")
    beispiele_normen = fields.Char('Beispiele anwedbarer Normen')
    wsgr = fields.Selection([
        ('FM1', 'FM1'),
        ('FM2', 'FM2'),
        ('FM3', 'FM3'),
        ('FM4', 'FM4'),
        ('FM5', 'FM5'),
        ('FM6', 'FM6'),
    ], 'WS.-Gr.')
    def get_rec_name(self, name):
        return self.wsgr

class Schweißprozesse(ModelSQL, ModelView):
    'Schweisprozesse'
    __name__ = 'welding.schweißprozesse'
    _order_name = 'rec_name'
    
    code = fields.Char('Code', translate=True,required=True)
    name = fields.Char('Name', translate=True,required=True)

    def get_rec_name(self, name):
        return self.code


class WeldingDatumms(ModelSQL, ModelView):
    "ISO96061 Datumm 9.2"
    __name__ = 'welding.iso96061.datumms'
    

    datum = fields.Date("Datum")
    unterschrift = fields.Selection([
        ('Dipl.-Ing. B.Aufsicht', 'Dipl.-Ing. B.Aufsicht'),
        (' ', ' '),
    ], 'Name und Unterschrift', readonly = False,
        )
    title = fields.Char('Dienststellung oder Titel', translate=True
        )
    iso96061 = fields.Many2One('welding.iso96061', 'iso96061',
        ondelete='CASCADE', select=True)
       
    
    @staticmethod
    def default_Unterschrift():
        return " "        

class  QualifikationDatumms(ModelSQL, ModelView):
    "ISO96061 Datumm 9.3"
    __name__ = 'welding.iso96061.qualifikation_datumms'
    

    datum3 = fields.Date("Datum")
    unterschrift3 = fields.Selection([
        ('Dipl.-Ing. B.Aufsicht', 'Dipl.-Ing. B.Aufsicht'),
        (' ', ' '),
    ], 'Name und Unterschrift', readonly = False,
        )
    title3 = fields.Char('Dienststellung oder Titel', translate=True
        )
    iso96061 = fields.Many2One('welding.iso96061', 'iso96061',
        ondelete='CASCADE',select=True)  
        
    @staticmethod
    def default_Unterschrift3():
        return " "     

    

#DRUCKEN SchweißanweisungWps FORMULAR
        
class SchweißanweisungWpsReport(Report):

    @classmethod
    def header_key(cls, record):
        return super().header_key(record) + (('schweißanweisung_wps', record.schweißanweisung_wps),)

    @classmethod
    def get_context(cls, records, header, data):
        context = super().get_context(records, header, data)
        context['schweißanweisung_wps'] = header['schweißanweisung_wps']
        return context

            
#DRUCKEN ISO_96061 FORMULAR
        
class Iso96061Report(Report):

    @classmethod
    def header_key(cls, record):
        return super().header_key(record) + (('iso96061', record.iso96061),)

    @classmethod
    def get_context(cls, records, header, data):
        context = super().get_context(records, header, data)
        context['iso96061'] = header['iso96061']
        return context
class ZertifikatIso96061Report(Iso96061Report):
    __name__ = 'welding.zertifikat_iso96061'

    @classmethod
    def execute(cls, ids, data):
        with Transaction().set_context(zertifikat=True):
            return super(ZertifikatIso96061Report, cls).execute(ids, data)                                
        
                    


