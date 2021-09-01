# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.model import Workflow, ModelView, ModelSQL, fields, DeactivableMixin,MultiValueMixin, sequence_ordered, Unique
from trytond.transaction import Transaction
from trytond.pyson import Eval, If, Bool
from trytond.pool import Pool, PoolMeta
from trytond.wizard import Wizard, StateTransition, StateView, Button, StateReport
from trytond.report import Report
import datetime
import csv
import psycopg2
import shutil
import numpy as np
import binascii
import functools
import json

__all__ = ['Party', 'PartyBriefing', 'PartyOccupationalCheckup',
    'PartyProfession','iso14732','PrintISO96061Start','PrintISO96061',
    'ISO96061report','wps','uploadxlsISO96061',
    'UploadxmlStart','PrintWPSStart','PrintWPS','ISOWPSreport','iso96062','Datumm',
    'PrintENISO96062Start','PrintISO96062','ISO96062report','Datumm5_3','Datumm5','PrintENISO14732Start',
    'ISO14732report','PrintISO14732','Bewertung2','ISONORMES','PrintISONORMES','ISONORMES','ISONORMESreport','wpqr','schutzgaswpqr',
    'PrintISOWPQRStart','PrintWPQR','ISOWPQRreport','wpqrbericht1','prufergebnisse','Querzugversuch','Biegepruf','kerbschlabiegeversuch1',
    'Bericht1report','wpqrbericht2','Harteprufung','Harteprufung1','Bericht2report','wpqr2','hubzundungs',
    'PrintISOWPQR2Start','ISOWPQR2report','PrintWPQR2','wpqr3','PrintISOWPQR3Start','PrintWPQR3','ISOWPQR3report','wpqr4','kondersatorentladungs',
    'PrintISOWPQR4Start','PrintWPQR4','ISOWPQR4report','wpqr5','ISOWPQR5report','PrintWPQR5','PrintISOWPQR5Start','wpqr6',
    'material1','fm1','PrintISOWPQR6Start','PrintWPQR6','ISOWPQR6report','qw483','tensile','guidedbend','toughness','wq483report',
    'listeneintrag','zfptp','ZfPreport','PrintZfP','PrintZfPStart','WOPQ','PNumber','SFA','WPQResults','PrintWPQStart','PrintWPQ','WPQreport',
    'WOPQ2','UNS','WOPQResults','PrintWOPQStart','PrintWOPQ','WOPQreport',
    'process','pruf_prufstelle_Beleg_nr']

STATES = {
    'readonly': ~Eval('active'),
    }
DEPENDS = ['active']
tabll=[]
tabll1=[]
tab_prufumfang = []
tab_prufumfang2 = []
tab_prufumfang3 = []


# Eine Party ist ein natürlichen oder juristischen Person
class Party(metaclass=PoolMeta):
    __name__ = 'party.party'
    employer = fields.Many2One('party.party', 'Arbeitgeber') # Es ist eine Beziehung zwischen diese Klasse  und Party-klasse
    birthday = fields.Date('Geburtsdatum') #Geburtsdatum auf diese Party
    country_of_birth = fields.Many2One('country.country', 'Geburtsland',
        states=STATES, depends=DEPENDS) # Geburtsland dieser Party
    ort_birthday = fields.Char('Geburtsort ') # Geburtsort dieser Party
    legitimation = fields.Char('Legitimation')
    legitimation_type = fields.Char('Art der Legitimation')
    last_occupational_checkup = fields.Function(fields.Date(
            'Last Occupational Health Checkup'), 'get_last_checkup')
    occupational_checkups = fields.One2Many('party.occupational_checkup',
        'party', 'Occupational Health Check-ups')
    vision_aid_required = fields.Boolean('Vision Aid Required')
    profession = fields.Many2One('party.profession', 'Beruf') # Es ist eine Beziehung zwischen diese klasse und party.profession klasse
    briefings = fields.One2Many('party.briefing', 'party', 'Briefings')
    @staticmethod
    def default_country_of_birth(): #Diese Funktion definiert Deutschland als Default-Land.
        '''
        Set the default country to Germany.
        '''
        pool = Pool()
        Country = Pool().get('country.country')
        countries = Country.search([
                ('code', '=', 'DE'),
                    ], limit=1)
        if countries:
              country, = countries
              return country.id
        return None
    @staticmethod

    @staticmethod
    def default_vision_aid_required():
        return False

    @classmethod
    def get_resources(cls):
        pool = Pool()
        Attachment = pool.get('ir.attachment')
        Note = pool.get('ir.note')
        return [Attachment, Note]


    @staticmethod
    def get_last_checkup(parties, name):
        pool = Pool()
        Checkup = pool.get('party.occupational_checkup')
        Date = pool.get('ir.date')

        res = {}
        date = Transaction().context.get('date', Date.today())
        for party in parties:
            checkups = Checkup.search([
                    ('party', '=', party.id),
                    #('date', '<=', date),
                    ], limit=1, order=[('date', 'DESC')])
            if checkups:
                res[party.id] = checkups[0].date
            else:
                res[party.id] = None
        return res

class PartyBriefing(ModelSQL, ModelView):
    'Party Briefing'
    __name__ = 'party.briefing'

    party = fields.Many2One('party.party', 'Party', required=True,
            ondelete='CASCADE')
    date = fields.Date('Date', required=True, select=True)
    topic = fields.Text('Topic', required=True)

    @classmethod
    def __setup__(cls):
        super(PartyBriefing, cls).__setup__()
        cls._order.insert(0, ('date', 'DESC'))

    @staticmethod
    def default_date():
        Date = Pool().get('ir.date')
        return Date.today()

class PartyOccupationalCheckup(ModelSQL, ModelView):
    'Party Occupational Checkup'
    __name__ = 'party.occupational_checkup'
    _rec_name = 'date'

    party = fields.Many2One('party.party', 'Party', required=True,
            ondelete='CASCADE')
    date = fields.Date('Date', required=True, select=True)

    @classmethod
    def __setup__(cls):
        super(PartyOccupationalCheckup, cls).__setup__()
        cls._order.insert(0, ('date', 'DESC'))    

class PartyProfession(ModelSQL, ModelView):
    'Party Profession'
    __name__ = 'party.profession'

    name = fields.Char('Name', translate=True,
        required=True)


class Party_wolframelektrodenart(ModelSQL, ModelView):
    'Party Wolframelektrodenart'
    __name__ = 'party.wolframelektrodenart'
    _order_name = 'rec_name'
    Kurzzeichen = fields.Char('Kurzzeichen', translate=True,required=True,
      )
    Hauptoxide = fields.Char('Hauptoxide', translate=True
        )
    Gehalt = fields.Char('Gehalt', translate=True
        )
    Kennfarbe = fields.Char('Kennfarbe', translate=True
        )
    Farbwert = fields.Char('Farbwert', translate=True
        )
    def get_rec_name(self, Kurzzeichen):
        return self.Kurzzeichen

class Party_wolframelektrodenart2(ModelSQL, ModelView):
    'Party Wolframelektrodenart2'
    __name__ = 'party.wolframelektrodenart_2'
    _order_name = 'rec_name'
    Durchmesser = fields.Char('Durchmesser', translate=True,required=True,
      )
    Toleranz = fields.Char('Toleranz', translate=True
        )
    DC_minus = fields.Char('DC (-)', translate=True
        )
    DC_plus = fields.Char('DC (+)', translate=True
        )
    AC = fields.Char('AC', translate=True
        )
    def get_rec_name(self, Durchmesser):
        return self.Durchmesser


class Datumm(
        DeactivableMixin, sequence_ordered(), ModelSQL, ModelView):
    "Party Datumm9.2"
    __name__ = 'party.datumms9.2'

    Datum1 = fields.Date("Datum")
    Unterschrift = fields.Selection([
        ('Dipl.-Ing. B.Aufsicht', 'Dipl.-Ing. B.Aufsicht'),
        (' ', ' '),
    ], 'Name und Unterschrift', readonly = False,
        )
    Title = fields.Char('Dienststellung oder Titel', translate=True
        )
    test2 = fields.Many2One('party.iso96062', 'iso96062',required=True,
        ondelete='CASCADE', states=STATES, select=True, depends=DEPENDS)

    @staticmethod
    def default_Unterschrift():
        return " "

#P_number class
class PNumber(ModelSQL, ModelView):
    'Party PNumber'
    __name__ = 'party.pnumber'

    p_no = fields.Char("P-No")
    iso = fields.Char("ISO 15608")
    base = fields.Char("Base metal (Typical or Exemple)")
    group = fields.Char("Groups")

    def get_rec_name(self, p_no):
        return self.p_no
#SFA Class
class SFA(ModelSQL, ModelView):
    'Party SFA'
    __name__ = 'party.sfa'
    sfa = fields.Char("SFA")
    classification = fields.Char("Classification")
    f_no = fields.Char("F-No")
    trade_name = fields.Char("Trade name")
    manufacture = fields.Char("Manufacturer")
    eignung = fields.Char("Eignung")

    def get_rec_name(self, sfa):
        return self.sfa

class WPQResults(
        DeactivableMixin, sequence_ordered(), ModelSQL, ModelView):
    "WPQ Results"
    __name__ = 'wpq.results'
    type = fields.Char("type/Art")
    res = fields.Char("Result/Ergebnis")
    type1 = fields.Char("type/Art")
    res1 = fields.Char("Result/Ergebnis")
    type2 = fields.Char("type/Art")
    res2 = fields.Char("Result/Ergebnis")
    link_wpqresults = fields.Many2One('welding.performance.qualification', 'results',
        ondelete='CASCADE', states=STATES, select=True, depends=DEPENDS)
#Specification and UNS Number Class
class UNS(ModelSQL, ModelView):
    'Party UNS'
    __name__ = 'party.uns'
    astm = fields.Char("Name ASTM")
    name_en = fields.Char("Name EN")
    p_no = fields.Char("P-No")

    def get_rec_name(self, astm):
        return self.astm

class WOPQResults(
        DeactivableMixin, sequence_ordered(), ModelSQL, ModelView):
    "WOPQ Results"
    __name__ = 'wopq.results'
    type = fields.Char("type/Art")
    res = fields.Char("Result/Ergebnis")
    type1 = fields.Char("type/Art")
    res1 = fields.Char("Result/Ergebnis")
    type2 = fields.Char("type/Art")
    res2 = fields.Char("Result/Ergebnis")
    link_wopqresults = fields.Many2One('welding.operator.performance.qualification', 'results',
        ondelete='CASCADE', states=STATES, select=True, depends=DEPENDS)


# Welding Operator Performance Qualification (WOPQ)
class WOPQ2(DeactivableMixin, ModelView, ModelSQL, MultiValueMixin):
    'Welding Operator Performance Qualification'
    __name__ = 'welding.operator.performance.qualification'

    title = fields.Selection([
        ('welding_performance', '---------------------------------------------------------------------------------WELDING OPERATOR PERFORMANCE QUALIFICATION (WOPQ)---------------------------------------------------------------------------------')
    ], 'title', readonly = False,
        )
    space = fields.Char("                                                                                                                                         ")
    subtitle2 = fields.Char("  ")
    Tab_res = fields.One2Many('wopq.results','link_wopqresults',' ')

    welding_variable = fields.Char("Welding Variables (QW-361-1)                       ")
    welding_variable2 = fields.Char("Welding Variables (QW-361-2)              ")
    actuel_value = fields.Char("Actual Values")
    range_qualified = fields.Char("Range Qualified")
    operator_name = fields.Char("Welding operator's name                                                                     ")
    identification = fields.Char("Identification no.")
    stamp = fields.Char("Stamp no.")
    test_description = fields.Char("Test Description (Information Only)                                                    ")
    wps=fields.Many2One("party.wps","Identification of WPS followed                                                            ")
    base_metal=fields.Many2One("party.pnumber","Base metal P-Number                                                                        ")
    to_p_number=fields.Many2One("party.pnumber","to  P-Number        ")
    sfa =fields.Many2One("party.sfa","Filler metal (SFA) specification                                                          ")
    filler_metal_classification = fields.Function(fields.Char("Filler metal or electrode classification"),"On_Change_sfa")

    uns=fields.Many2One("party.uns","Specification and type/grade or UNS Number of base metal(s)        ")
    test_coupon = fields.Boolean("Test coupon")
    test_coupon_affichage = fields.Function(fields.Char(" "),"On_Change_test_coupon")
    production_weld = fields.Function(fields.Boolean("Production weld"),"On_Change_coupon")
    production_weld_affichage = fields.Function(fields.Char(" "),"On_Change_production_weld")
    thickness = fields.Char("Thickness")
    position = fields.Selection('on_change_blechrohr','Position qualified (2G,6G,3F,etc.)       ', readonly = False,)
    blech_rohr = fields.Selection([
        ('P', 'P | Plate(Blech)'),
        ('T', 'T | Pipe(Rohr)'),
    ], 'Blech oder Rohr                                                                                   ', readonly = False,
        )
    filler_used = fields.Selection([
        ('Yes', 'Yes | with filler metal'),
        ('with', 'with | with filler metal'),
        ('wm', 'wm | with filler metal'),
        ('Solid cored', 'Solid cored | Massivdraht/-stab '),
        ('Flux cored', 'Flux cored  | Fülldrahtelektrode'),
        ('Metall cored', 'Metall cored | Metallpulver-Fülldrahtlelektrode'),
        ('Powder', 'Powder  | Pulver'),
        ('No', 'No | without filler metal'),
        ('without', ' without | without filler metal'),
        ('none', 'none | none filler metal'),
        ('nm', 'nm | no filler metal'),
    ], 'Filler metal used (Yes/No)(EBW or LBW)     ', readonly = False,
        )
    filler_used_range = fields.Char(" ")
    type_laser = fields.Char("Type of Laser for LBW(CO2 to YAG, etc)       ")
    type_laser_range = fields.Char(" ")
    continuous_drive = fields.Selection([
        ('continuous drive', 'continuous drive | Kontinuierlichen Antrieb'),
        ('inertia welding', 'inertia welding | Rotationsreibschweißen'),
        ('inertia type drive', 'inertia type drive | Schwungradantrieb'),
    ], 'Continuous drive or inertia welding (FW)       ', readonly = False,
        )
    continuous_drive_range = fields.Char(" ")
    vacuum = fields.Selection([
        ('in vacuum', 'in vacuum | Schweißen unter Vakuum'),
        ('EBW-HV', 'EBW-HV | Schweißen unter Vakuum '),
        ('no vacuum', 'no vacuum | nicht in Vakuum'),
        ('atmosphere', 'atmosphere | Schweißen in Atmosphäre'),
        ('EBW-NV', 'EBW-NV | Schweißen in Atmosphäre'),
    ], 'Vacuum or out of vacuum (EBW)                   ', readonly = False,
        )
    vacuum_range = fields.Char(" ")


    type_welding = fields.Selection([
        ('automatic', 'automatic | automatisiert'),
        ('machine', 'machine | vollmechanisiert'),
    ], 'Type of welding                                                 ', readonly = False,
        )
    welding_process = fields.Selection('on_change_type_welding1','Welding process                                               ', readonly = False,)
    welding_process_gel = fields.Function(fields.Char(" "),"On_Change_welding_process")
    type_welding_gel = fields.Function(fields.Char(" "),"On_Change_type_welding")
    type_welding_machine = fields.Selection('on_change_type_welding_auto','Type of welding (Machine)                      ', readonly = False,)
    range_qualified_welding_machine = fields.Char(" ")
    welding_process_machine = fields.Selection('on_change_type_welding_machine1','Welding process                                     ', readonly = False,)
    welding_process_machine_gel = fields.Function(fields.Char(" "),"On_Change_welding_process_machine")
    nahtart = fields.Selection([
        ('BW', 'BW | Groove(Stumpfnaht)'),
        ('FW', 'FW | Fillet(Kehlnaht)'),
    ], 'Nahtart', readonly = False,
        )
    direct_remote_visual_comtrole = fields.Selection([
        ('direct', 'direct | direkt(mit bloßen Auge)'),
        ('remote', 'remote | entfernt(mit kamera,Videoskop,usw.)'),
    ], 'Direct or remote visual control               ', readonly = False,
        )
    direct_remote_visual_comtrole_range = fields.Char(" ")
    automatic_arc_voltage = fields.Selection([
        ('without', 'without | ohne Regelung'),
        ('with', 'with | mit Regelung'),
    ], 'Automatic arc voltage control (GTAW) ', readonly = False,
        )
    automatic_arc_voltage_range = fields.Char(" ")

    automatic_joint_tracking = fields.Selection([
        ('without', 'without | ohne Nahtsensor'),
        ('with', 'with | mit Nahtsensor'),
    ], 'Automatic joint tracking                          ', readonly = False,
        )
    automatic_joint_tracking_range = fields.Char(" ")

    comsumable_insert = fields.Selection([
        ('without', 'without | ohne aufschmelzende Einlage'),
        ('with', 'with | mit aufschmelzende Einlage'),
    ], 'Consumable inserts (GTAW or PAW)  ', readonly = False,
        )
    comsumable_insert_range = fields.Char(" ")

    backing = fields.Selection([
        ('without', 'without | ohne Badsicherung'),
        ('with', 'with | mit Badsicherung'),
        ('backing used', 'backing used | mit Badsicherung'),
        ('metal', 'metal | Badsicherung mit Metall'),
        ('weld metal', 'weld metal | Badsicherung mit Schweißgut'),
        ('nonmetallic', 'nonmetallic | nichtmetallische Badsicherung'),
        ('flux backing', 'flux backing | Badsicherung mit Schweißpulver'),
        ('gas backing', 'gas backing | gasförmiger Wurzelschutz'),
        ('gb', 'gb | gas backing'),
        ('mb', 'mb | material backing'),
        ('nb', 'nb | no backing'),
        ('no backing', 'no backing | Keine Badsicherung'),
        ('double-welded', 'double-welded | beidseitiges Schweißen'),
    ], 'Backing (with/without)                            ', readonly = False,
        )
    backing_range = fields.Char(" ")
    supervised_by = fields.Char(" ")

    single_multiple_passes = fields.Selection([
        ('single pass', 'single pass | einziger Durchlauf'),
        ('single layer', 'single layer | einlagig(Einzelraupe)'),
        ('sl', 'sl | single layer'),
        ('multiple passes', 'multiple passes | mehrere Durchläufe'),
        ('multi layer', 'multi layer | mehrlagig(Mehrfachraupen)'),
        ('ml', 'ml | multi layer'),
    ], 'Single or multiple passes per side        ', readonly = False,
        )
    single_multiple_passes_range = fields.Char(" ")
    position_range = fields.Char(" ")
    visual_completed_weld = fields.Selection([
        ('Not Applicable', 'Not Applicable | nicht anwendbar'),
        ('acceptable', 'acceptable | bestanden'),
    ], 'Visual examination of completed weld (QW-302.4)', readonly = False,
        )
    transverse_face = fields.Boolean("Transverse face and root bends[QW-462.3(a)]                                                                                                       ")
    transverse_face_affichage = fields.Function(fields.Char(" "),"On_Change_transverse_face")
    longitudinal_bends = fields.Boolean("Longitudinal bends[QW-462.3(b)]")
    longitudinal_bends_affichage = fields.Function(fields.Char(" "),"On_Change_longitudinal_bends")
    side_bends = fields.Boolean("Side bends[QW-462.2]")
    side_bends_affichage = fields.Function(fields.Char(" "),"On_Change_side_bends")


    pipe_bends = fields.Boolean("Pipe bend specimen,corrosion-resistant weld metal overlay[QW-462.5(c)]                                                       ")
    pipe_bends_affichage = fields.Function(fields.Char(" "),"On_Change_pipe_bends")
    plate_bends = fields.Boolean("Plate bend specimen,corrosion-resistant weld metal overlay[QW-462.5(d)]                                                      ")
    plate_bends_affichage = fields.Function(fields.Char(" "),"On_Change_plate_bends")
    pipe_specimen = fields.Boolean("Pipe Specimen, macro test for fusion [QW-462.5(b)]                                                                                           ")
    pipe_specimen_affichage = fields.Function(fields.Char(" "),"On_Change_pipe_specimen")
    plate_specimen = fields.Boolean("Plate Specimen, macro test for fusion [QW-462.5(e)]")
    plate_specimen_affichage = fields.Function(fields.Char(" "),"On_Change_plate_specimen")

    bezeichnung = fields.Function(fields.Char("Bezeichnung                                                                                        "),"On_Change_andere_options")
    value_diameter = fields.Char("Enter diameter[mm], if pipe or tube")
    pipe = fields.Function(fields.Boolean("Pipe                                                                                                     "),"On_Change_blech_oder_rohr")
    pipe_affichage = fields.Function(fields.Char(" "),"On_Change_pipe")
    plate_affichage = fields.Function(fields.Char(" "),"On_Change_plate")
    plate = fields.Function(fields.Boolean("Plate"),"On_Change_blech_oder_rohr1")
    subtitle1 = fields.Function(fields.Char("subtitle1"),"On_get_title")
    filler_metal = fields.Selection([
        ('1', '1 | Heavy rutile coated iron powder electrodes | SFA-5.1:EXX20, 22, 24, 27, 28;SFA-5.4;SFA-5.5'),
        ('2', '2 | Most Rutile consumables | SFA-5.1:EXX12, 13, 14, 19;SFA-5.5;E(X)XX13-X'),
        ('3', '3 | Cellulosic electrode | SFA-5.1:EXX10, 11;SFA-5.5:E(X)XX10-X, 11-X'),
        ('4', '4 | Basic coated electrodes | SFA-5.1:EXX15, 16, 18, 18M, 48;SFA-5.4;SFA-5.5'),
        ('5', '5 | High alloy austenitic stainless steel and duplex | SFA-5.4:EXXX(X)-15,-16,-17'),
        ('6', '6 | Any steel solid or cored wire (with flux or metal) | '),
        ('21', '21 | Aluminium and Aluminium Alloys | SFA-5.3:E1100,E3003;SFA-5.10'),
        ('22', '22 | Aluminium and Aluminium Alloys | SFA-5.10:ER5183,ER5356,...,R5183,R5356,...'),
        ('23', '23 | Aluminium and Aluminium Alloys | SFA-5.3:E4043;SFA-5.10'),
        ('24', '24 | Aluminium and Aluminium Alloys | SFA-5.10:R-A356.0,R-A357.0,...,R206.0,R357.0'),
        ('25', '25 | Aluminium and Aluminium Alloys | SFA-5.10:ER2319,R2319'),
        ('31', '31 | Copper and Copper Alloys | SFA-5.6:ECu;SFA-5.7:ERCu'),
        ('32', '32 | Copper and Copper Alloys | SFA-5.6:ECuSi;SFA-5.7:ERCuSi-A'),
        ('33', '33 | Copper and Copper Alloys | SFA-5.6:ECuSn-A;ECuSn-C;SFA-5.7:ERCuSn-A'),
        ('34', '34 | Copper and Copper Alloys | SFA-5.6:ECuNi;SFA-5.7:ERCuNi;SFA-5.30:IN67'),
        ('35', '35 | Copper and Copper Alloys | SFA-5.8:RBCuZn-A,-B,-C,-D'),
        ('36', '36 | Copper and Copper Alloys | SFA-5.6:ECuAI-A2, ECuAI-B;SFA-5.7:ERCuAI-A1,2,3'),
        ('37', '37 | Copper and Copper Alloys | SFA-5.6:ECuMnNiAI,ECuNiAI;SFA-5.7:ERCuNiAI'),
        ('41', '41 | Nickel and Nickel Alloys | SFA-5.11:ENi-1;SFA-5.14:ERNi-1;SFA-5.30:IN61'),
        ('42', '42 | Nickel and Nickel Alloys | SFA-5.11:ENiCu-7;SFA-5.14:ERNiCu-7,-8;SFA-5.30:IN60'),
        ('43', '43 | Nickel and Nickel Alloys | SFA-5.11:ENiCrFe-X,ENiCrMo-X;SFA-5.14;SFA-5.30'),
        ('44', '44 | Nickel and Nickel Alloys | SFA-5.11:ENiMo-X;SFA-5.14:ERNiMo-X'),
        ('45', '45 | Nickel and Nickel Alloys | SFA-5.11:ENiCrMo-X;SFA-5.14:ERNiCrMo-X,ERNiFeCr-1'),
        ('51', '51 | Titanium and Titanium Alloys | SFA-5.16:ERTi-1,-2,-3,-4'),
        ('52', '52 | Titanium and Titanium Alloys | SFA-5.16:ERTi-7'),
        ('53', '53 | Titanium and Titanium Alloys | SFA-5.16:ERTi-9,ERTi-9ELI'),
        ('54', '54 | Titanium and Titanium Alloys | SFA-5.16:ERTi-12'),
        ('55', '55 | Titanium and Titanium Alloys | SFA-5.16:ERTi-5,ERTi-5ELI,ERTi-6,ERTi-6ELI,ERTi-15'),
        ('61', '61 | Zirconium and Zirconium Alloys | SFA-5.24:ERZr2,3,4'),
        ('71', '71 | Hard-Facing Weld Metal Overlay | SFA-5.13'),
        ('72', '72 | Hard-Facing Weld Metal Overlay | SFA-5.21'),
    ], 'Filler metal F-Number                                                                        ', readonly = False,
        )

    alternativ_volumetric = fields.Selection([
        ('acceptable', 'acceptable | bestanden'),
        ('not applicable', 'not applicable | nicht anwendbar'),
    ], 'Alternative Volumetric Examination Results                                                                                       (QW-191)  ', readonly = False,
        )

    Fillet_welt = fields.Selection([
        ('acceptable', 'acceptable | bestanden'),
        ('not applicable', 'not applicable | nicht anwendbar'),
    ], 'Fillet weld - facture test (QW-181.2)                                                                                                                       ', readonly = False,
        )

    r_t = fields.Boolean("RT")
    affichage_r_t = fields.Function(fields.Char(" "),"On_Change_r_t")
    u_t = fields.Boolean("UT")
    affichage_u_t = fields.Function(fields.Char(" "),"On_Change_u_t")

    fillet_weld_plate = fields.Boolean("Fillet welds in plate [QW-462.4(b)]                                                                                                                         ")
    affichage_fillet_weld_plate=fields.Function(fields.Char(" "),"On_Change_fillet_weld_plate")
    fillet_weld_pipe = fields.Boolean("Fillet welds in pipe [QW-462.4(c)]")
    affichage_fillet_weld_pipe = fields.Function(fields.Char(" "),"On_Change_fillet_weld_pipe")

    macro_exam = fields.Selection([
        ('acceptable', 'acceptable | bestanden'),
        ('not applicable', 'not applicable | nicht anwendbar'),
    ], 'Macro examination (QW-184)                                                                                                                                 ', readonly = False,
        )

    certified_by = fields.Selection([
        ('Dipl.Ing. Prüfer', 'Dipl.Ing. Prüfer'),
        ('Dipl.Ing. Schulz', 'Dipl.Ing. Schulz'),
        ('Dipl.Ing. Tester', 'Dipl.Ing. Tester'),
        ('Dipl.Ing. zertifizierer', 'Dipl.Ing. zertifizierer'),
        ('P. L. Van Fosson', 'P. L. Van Fosson'),
        ('Dipl.Ing. Zertifizierer', 'Dipl.Ing. Zertifizierer'),
    ], 'Certified by                                                                                                                                                                ', readonly = False,
        )
    date = fields.Date("Date")


    fillet_size = fields.Char("Fillet size                                                                                                                                                                  ")
    convacity = fields.Char("Convacity/Convexity                                                                                                                                                 ")
    other_test = fields.Char("Other tests                                                                                                                                                                ")

    film_evaluated = fields.Char("Film or specimens evaluated by                                                                                                                              ")
    company = fields.Char("Company")
    mecanical_test = fields.Char("Mechanical tests conducted by                                                                                                                                ")
    labo_no = fields.Char("Laboratory tests no")
    supervised_by = fields.Char("Welding supervised by                                                                                                                                             ")
    index = fields.Char("We certify that the statements in this record are correct and that the test coupons were prepared, welded, and tested in accordance with the requirements of Section IX of the ASME BOILER AND PRESSURE VESSEL CODE  ")
    index1 = fields.Char("the requirements of Section IX of the ASME BOILER AND PRESSURE VESSEL CODE")
    organization = fields.Selection([
        ('DGZfP', 'DGZfP-Ausbildungszentrum Wittenberge'),
        ('Harrison', 'Harrison Mechanical Corporation'),
        ('MAN-Technologie', 'MAN-Technologie, Oberpfaffenhofen, Abtlg.WOP'),
    ], 'Organization                                                                                                                                                              ', readonly = False,
        )

    ruhende_prüfung = fields.Boolean("Ruhende Prüfung")
    prufung_archivieren = fields.Boolean("Prüfung archivieren")
    letzte_prufung = fields.Date("Letzte Prüfung")
    gultig_bis = fields.Date("gültig bis")
    next_termin = fields.Date("nächste Termin")


    def On_Change_r_t(self,r_t):
      if(self.r_t == True):
           return "|✘|"
      else:
           return "|  |"

    def On_Change_u_t(self,u_t):
      if(self.u_t == True):
           return "|✘|"
      else:
           return "|  |"

    def On_Change_fillet_weld_plate(self,fillet_weld_plate):
      if(self.fillet_weld_plate == True):
           return "|✘|"
      else:
           return "|  |"

    def On_Change_fillet_weld_pipe(self,fillet_weld_pipe):
      if(self.fillet_weld_pipe == True):
           return "|✘|"
      else:
           return "|  |"


    def On_Change_pipe_bends(self,pipe_bends):
      if(self.pipe_bends == True):
           return "|✘|"
      else:
           return "|  |"

    def On_Change_plate_bends(self,plate_bends):
      if(self.plate_bends == True):
           return "|✘|"
      else:
           return "|  |"

    def On_Change_pipe_specimen(self,pipe_specimen):
      if(self.pipe_specimen == True):
           return "|✘|"
      else:
           return "|  |"

    def On_Change_plate_specimen(self,plate_specimen):
      if(self.plate_specimen == True):
           return "|✘|"
      else:
           return "|  |"


    def On_Change_side_bends(self,side_bends):
        if(self.side_bends == True):
           return "|✘|"
        else:
           return "|  |"


    def On_Change_transverse_face(self,transverse_face):
        if(self.transverse_face == True):
           return "|✘|"
        else:
           return "|  |"

    def On_Change_longitudinal_bends(self,longitudinal_bends):
        if(self.longitudinal_bends == True):
           return "|✘|"
        else:
           return "|  |"


    def On_Change_plate(self,plate):
        if(self.plate == True):
           return "|✘|"
        else:
           return "|  |"

    def On_Change_pipe(self,pipe):
        if(self.pipe == True):
           return "|✘|"
        else:
           return "|  |"


    def On_Change_test_coupon(self,test_coupon):
        if(self.test_coupon == True):
           return "|✘|"
        else:
           return "|  |"

    def On_Change_production_weld(self,production_weld):
        if(self.production_weld == True):
           return "|✘|"
        else:
           return "|  |"


    @fields.depends('type_welding_machine', 'type_welding')
    def on_change_type_welding_auto(self):
        tab=[]
        if(self.type_welding == "automatic"):
          tab.append((" ", " "))
          return tab
        else:
          tab.append(("machine", "machine | vollmechanisiert "))
          return tab

    def On_Change_welding_process_machine(self,welding_process_machine):
         return self.welding_process_machine


    def On_Change_welding_process(self,welding_process):
       return self.welding_process

    @fields.depends('welding_process_machine', 'type_welding')
    def on_change_type_welding_machine1(self):
        tabb=[]
        if(self.type_welding == "machine"):
          tabb.append(("AW", "AW | Arc welding | 1 | "))
          tabb.append(("SMAW", "SMAW | Shielded metal arc welding | 111 | E "))
          tabb.append(("BMAW", "BMAW | Base metal arc welding ¹)  | 113 ¹) | "))
          tabb.append(("FCAW-S", "FCAW-S | Self-shielded tubular cored arc welding | 114 | MF"))
          tabb.append(("SAW", "SAW | Submerged arc welding | 12 | UP"))
          tabb.append(("GMAW", "GMAW | Gas metal arc welding | 13 | MSG"))
          tabb.append(("FCAW-S", "FCAW-S | Gas metal asc welding using inert gas and metal cored wire | 133 | MIG"))
          tabb.append(("GMAW", "GMAW | Gas metal arc welding using active gas with solid wire electrode | 135 | MAG"))
          tabb.append(("FCAW", "FCAW | Gas metal arc welding using active gas and flux cored electrode | 136 | MAG"))
          tabb.append(("GTAW", "GTAW | Gas tungesten arc welding | 14 | WSG"))
          tabb.append(("GTAW", "GTAW | Gas tungsten arc welding using inert gas and solid filler material (wire/rod) | 141 | WIG"))
          tabb.append(("AHW", "AHW | Atomic-hydrogen welding ¹) |  149 ¹)| "))
          tabb.append(("PAW", "PAW | Plasma arc welding | 15 | WPL"))
          tabb.append(("CAW", "CAW | Carbon-arc welding ¹) | 181 ¹) | "))
          tabb.append(("MIAW", "MIAW | Magnetically impelled arc welding | 185 | "))
          tabb.append(("RW", "RW | Resistance welding | 2 | "))
          tabb.append(("RSEW", "RSEW | Seam welding | 22 | RR"))
          tabb.append(("RSEW-MS", "RSEW-MS | Mash seam welding | 222 | "))
          tabb.append(("PW", "PW | Projection welding | 23 | RB "))
          tabb.append(("FW", "FW | Flash welding | 24 | RA"))
          tabb.append(("UW", "UW | Upset welding | 25 | "))
          tabb.append(("ROW", "ROW | High-frequency upset welding | 27 | "))
          tabb.append(("UW-HF", "UW-HF | High-frequency upset welding ²)| 291 ²) | "))
          tabb.append(("OFW", "OFW | Oxyfuel gas welding | 31 | Gas"))
          tabb.append(("OAW", "OAW | Oxyacetylene welding | 311 | Gas"))
          tabb.append(("OHW", "OHW | Oxyhydrogen welding | 313 | Gas"))
          tabb.append(("AAW", "AAW | Air acetylene welding ¹) | 321 ¹) | "))
          tabb.append(("SSW", "SSW | Welding with pressure | 4 | "))
          tabb.append(("USW", "USW | Ultrasonic welding | 41 | "))
          tabb.append(("FRW", "FRW | Friction welding | 42 | FR"))
          tabb.append(("FRW-DD", "FRW-DD | Direct drive friction welding | 421 | "))
          tabb.append(("FRW-I", "FRW-I | Inertia friction welding | 422 | "))
          tabb.append(("FSW", "FSW | Friction stir welding | 43 | "))
          tabb.append(("FOW", "FOW | Forge welding ¹) | 43 ¹) | "))
          tabb.append(("EXW", "EXW | Explosion welding | 441 | "))
          tabb.append(("DFW", "DFW | Diffusion welding | 45 | "))
          tabb.append(("PGW", "PGW | Pressure gas welding | 47 | "))
          tabb.append(("CW", "CW | Cold welding | 48 | "))
          tabb.append(("HPW", "HPW | Hot pressure welding | 49 | "))
          tabb.append(("EBW", "EBW | Electron beam welding | 51 | EB"))
          tabb.append(("EBW-HV", "EBW-HV | Electron beam welding in vacuum | 511 | EB"))
          tabb.append(("EBW-NV", "EBW-NV | Electron beam welding in atmosphere | 512 | EB"))
          tabb.append(("LBW", "LBW | Laser beam welding | 52 | LA"))
          tabb.append(("TW", "TW | Thermite welding | 71 | "))
          tabb.append(("ESW", "ESW | Electroslag welding| 72 | RES"))
          tabb.append(("EGW", "EGW | Electrogas welding | 73 | MSGG"))
          tabb.append(("IW", "IW | Induction welding | 74 | "))
          tabb.append(("UW-I", "UW-I | Induction upset welding | 741 | "))
          tabb.append(("RSEW-I", "RSEW-I | Induction seam welding | 742 | "))
          tabb.append(("PEW", "PEW| Percussion welding ²) | 77 ²) | "))
          tabb.append(("SW", "SW | Arc stud welding | 784 | DS"))
          tabb.append(("SW", "SW | Arc stud welding | 785 | DS"))
          tabb.append(("SW", "SW | Arc stud welding | 786 | TS"))
          tabb.append(("LBBW", "LBBW | Laser beam brazing | 913 | "))
          tabb.append(("BW", "BW | Braze welding | 97 | "))
          tabb.append(("ABW", "ABW | Arc braze welding  | 972 | "))
          tabb.append(("EBBW", "EBBW | Electron beam braze welding | 977 | "))
          return tabb
        else:
          tabb.append((" ", " "))
          return tabb

    @fields.depends('welding_process', 'type_welding')
    def on_change_type_welding1(self):
        tabb=[]
        if(self.type_welding == "automatic"):
          tabb.append(("AW", "AW | Arc welding | 1 | "))
          tabb.append(("SMAW", "SMAW | Shielded metal arc welding | 111 | E "))
          tabb.append(("BMAW", "BMAW | Base metal arc welding ¹)  | 113 ¹) | "))
          tabb.append(("FCAW-S", "FCAW-S | Self-shielded tubular cored arc welding | 114 | MF"))
          tabb.append(("SAW", "SAW | Submerged arc welding | 12 | UP"))
          tabb.append(("GMAW", "GMAW | Gas metal arc welding | 13 | MSG"))
          tabb.append(("FCAW-S", "FCAW-S | Gas metal asc welding using inert gas and metal cored wire | 133 | MIG"))
          tabb.append(("GMAW", "GMAW | Gas metal arc welding using active gas with solid wire electrode | 135 | MAG"))
          tabb.append(("FCAW", "FCAW | Gas metal arc welding using active gas and flux cored electrode | 136 | MAG"))
          tabb.append(("GTAW", "GTAW | Gas tungesten arc welding | 14 | WSG"))
          tabb.append(("GTAW", "GTAW | Gas tungsten arc welding using inert gas and solid filler material (wire/rod) | 141 | WIG"))
          tabb.append(("AHW", "AHW | Atomic-hydrogen welding ¹) |  149 ¹)| "))
          tabb.append(("PAW", "PAW | Plasma arc welding | 15 | WPL"))
          tabb.append(("CAW", "CAW | Carbon-arc welding ¹) | 181 ¹) | "))
          tabb.append(("MIAW", "MIAW | Magnetically impelled arc welding | 185 | "))
          tabb.append(("RW", "RW | Resistance welding | 2 | "))
          tabb.append(("RSEW", "RSEW | Seam welding | 22 | RR"))
          tabb.append(("RSEW-MS", "RSEW-MS | Mash seam welding | 222 | "))
          tabb.append(("PW", "PW | Projection welding | 23 | RB "))
          tabb.append(("FW", "FW | Flash welding | 24 | RA"))
          tabb.append(("UW", "UW | Upset welding | 25 | "))
          tabb.append(("ROW", "ROW | High-frequency upset welding | 27 | "))
          tabb.append(("UW-HF", "UW-HF | High-frequency upset welding ²)| 291 ²) | "))
          tabb.append(("OFW", "OFW | Oxyfuel gas welding | 31 | Gas"))
          tabb.append(("OAW", "OAW | Oxyacetylene welding | 311 | Gas"))
          tabb.append(("OHW", "OHW | Oxyhydrogen welding | 313 | Gas"))
          tabb.append(("AAW", "AAW | Air acetylene welding ¹) | 321 ¹) | "))
          tabb.append(("SSW", "SSW | Welding with pressure | 4 | "))
          tabb.append(("USW", "USW | Ultrasonic welding | 41 | "))
          tabb.append(("FRW", "FRW | Friction welding | 42 | FR"))
          tabb.append(("FRW-DD", "FRW-DD | Direct drive friction welding | 421 | "))
          tabb.append(("FRW-I", "FRW-I | Inertia friction welding | 422 | "))
          tabb.append(("FSW", "FSW | Friction stir welding | 43 | "))
          tabb.append(("FOW", "FOW | Forge welding ¹) | 43 ¹) | "))
          tabb.append(("EXW", "EXW | Explosion welding | 441 | "))
          tabb.append(("DFW", "DFW | Diffusion welding | 45 | "))
          tabb.append(("PGW", "PGW | Pressure gas welding | 47 | "))
          tabb.append(("CW", "CW | Cold welding | 48 | "))
          tabb.append(("HPW", "HPW | Hot pressure welding | 49 | "))
          tabb.append(("EBW", "EBW | Electron beam welding | 51 | EB"))
          tabb.append(("EBW-HV", "EBW-HV | Electron beam welding in vacuum | 511 | EB"))
          tabb.append(("EBW-NV", "EBW-NV | Electron beam welding in atmosphere | 512 | EB"))
          tabb.append(("LBW", "LBW | Laser beam welding | 52 | LA"))
          tabb.append(("TW", "TW | Thermite welding | 71 | "))
          tabb.append(("ESW", "ESW | Electroslag welding| 72 | RES"))
          tabb.append(("EGW", "EGW | Electrogas welding | 73 | MSGG"))
          tabb.append(("IW", "IW | Induction welding | 74 | "))
          tabb.append(("UW-I", "UW-I | Induction upset welding | 741 | "))
          tabb.append(("RSEW-I", "RSEW-I | Induction seam welding | 742 | "))
          tabb.append(("PEW", "PEW| Percussion welding ²) | 77 ²) | "))
          tabb.append(("SW", "SW | Arc stud welding | 784 | DS"))
          tabb.append(("SW", "SW | Arc stud welding | 785 | DS"))
          tabb.append(("SW", "SW | Arc stud welding | 786 | TS"))
          tabb.append(("LBBW", "LBBW | Laser beam brazing | 913 | "))
          tabb.append(("BW", "BW | Braze welding | 97 | "))
          tabb.append(("ABW", "ABW | Arc braze welding  | 972 | "))
          tabb.append(("EBBW", "EBBW | Electron beam braze welding | 977 | "))
          return tabb
        else:
          tabb.append((" ", " "))
          return tabb

    def On_Change_type_welding(self,type_welding):
      if(self.type_welding == "automatic"):
        return "automatic"

    def On_Change_sfa(self,sfa):
      if(self.sfa is not None):
         return self.sfa.classification


    def On_Change_blech_oder_rohr(self,blech_rohr):
      if(self.blech_rohr =="P"):
        return False
      else:
        return True

    def On_Change_blech_oder_rohr1(self,blech_rohr):
      if(self.blech_rohr =="P"):
        return True
      else:
        return False

    @fields.depends('position', 'blech_rohr')
    def on_change_blechrohr(self):
          tab=[]
          if(self.blech_rohr == "T"):
             tab.append(('1F', '1F | Wannenposition am rotierenden Rohr - Achse geneigt(45°) | PA'))
             tab.append(('1G', '1G | Wanne am rotierenden Rohr - Achse waagerecht | PA'))
             tab.append(('2F', '2F | horizontal-vertikal am festen Rohr - Achse senkrecht | PB'))
             tab.append(('2Fr', '2Fr | horizontal-vertikal am rotierenden Rohr - Achse waagerecht | PB'))
             tab.append(('2G', '2G | quer am festen Rohr - Achse senkrecht | PC'))
             tab.append(('2G/5G', '2G/5G | quer am festen Rohr / vertikal am festen Rohr'))
             tab.append(('4F', '4F | horizontal-überkopf am festen Rohr - Achse senkrecht | PD'))
             tab.append(('5F', '5F | steigend oder fallend am festen Rohr - Achse waagerecht'))
             tab.append(('5Fd', '5Fd | fallend am festen Rohr - Achse waagerecht | PJ'))
             tab.append(('5Fu', '5Fu | steigend am festen Rohr - Achse waagerecht | PH'))
             tab.append(('5G', '5G | steigend oder fallend am festen Rohr - Achse waagerecht'))
             tab.append(('5Gd', '5Gd | fallend am festen Rohr - Achse waagerecht | PJ'))
             tab.append(('5Gu', '5Gu | steigend am festen Rohr - Achse waagerecht | PH'))
             tab.append(('6G', '6G | steigend oder fallend am festen Rohr - Achse geneigt(45°)'))
             tab.append(('6Gd', '6Gd | fallend am festen Rohr - Achse geneigt(45°) | J-L045'))
             tab.append(('6Gu', '6Gu | steigend am festen Rohr - Achse geneigt(45°) | H-L045'))
             tab.append(('SP', 'SP | Sonderposition'))
             return tab

          else:
            if(self.blech_rohr == "P"):
             tab.append(('1F', '1F | Wannenposition | PA'))
             tab.append(('2F', '2F | horizontal-vertikalposition | PB'))
             tab.append(('3Fd', '3Fd | fallposition | PG'))
             tab.append(('3Fu', '3Fu | steigposition | PF'))
             tab.append(('3F', '3F | Vertikal steigend oder fallend | '))
             tab.append(('4F', '4F | Horizontal-Überkopfposition  | PD'))
             tab.append(('3F/4F', '3F/4F | Vertikalposition/Horizontal-Überkopfposition | '))
             tab.append(('1G', '1G | Wannenposition | PA'))
             tab.append(('2G', '2G | Querposition | PC'))
             tab.append(('3Gd', '3Gd | Fallposition | PG'))
             tab.append(('3Gu', '3Gu | Steigposition | PF'))
             tab.append(('3G', '3G | Vertikal steigend oder fallend | '))
             tab.append(('4G', '4G | Überkopfposition | PE'))
             tab.append(('3Gd/4G', '3Gd/4G | fallposition/Überkopfposition | PG/PE'))
             tab.append(('3Gu/4G', '3Gu/4G | Steigposition/Überkopfposition | PF/PE'))
             tab.append(('2/3/4G', '2/3/4G | Querposition/Vertikalposition/Überkopfposition | '))
             tab.append(('SP', 'SP | Sonderpositionen | '))
             return tab

    def On_Change_andere_options(self,type_welding):
      if(self.type_welding =="automatic"):
           return "ASME WOPQ A " +self.welding_process
      else:
           return "ASME WOPQ M "+self.welding_process_machine

    def On_Change_coupon(self,test_coupon):
      if(self.test_coupon == True):
        return False
      else:
        return True

    def On_get_title(self,title):
        return "                                                                                                                 See QW-301, Section IX, ASME Boiler and Pressure Vessel Code"
    @staticmethod
    def default_title():
       return "welding_performance"
    @staticmethod
    def default_subtitle2():
       return "                                                                                                                               Eignungsprüfung von Maschienenschweißern"


#classes for Print Fonction for wopq
# class view
class PrintWOPQStart(ModelView):
    'Print START WOPQ'
    __name__ = 'party.print_wopq.start'
    zertifikat = fields.Many2One('welding.operator.performance.qualification', 'Zertifikat', required=True)

#Wizard
class PrintWOPQ(Wizard):
    'Print WOPQ1'
    __name__ = 'party.print_wopq'
    start = StateView('party.print_wopq.start',
        'welding_certification.print_wopq1_cert_start_view_form', [
            Button('Cancel', 'end', 'tryton-cancel'),
            Button('Drucken', 'print_', 'tryton-print', default=True),
            ])
    print_ = StateReport('welding_certification.party.iso_wopq_report')
    def do_print_(self, action):
        data = {
            'zertifikat': self.start.zertifikat.id,
            }
        return action, data
#Report
class WOPQreport(Report):
    __name__ = 'welding_certification.party.iso_wopq_report'


    @classmethod
    def _get_records(cls, ids, model, data):
        Move = Pool().get('welding.operator.performance.qualification')

        clause = [

            ]

    @classmethod
    def get_context(cls, records, data):
        report_context = super(WOPQreport, cls).get_context(records, data)

        Zertifikat = Pool().get('welding.operator.performance.qualification')

        zertifikat = Zertifikat(data['zertifikat'])

        report_context['zertifikat'] = zertifikat
        report_context['title'] = zertifikat.title
        report_context['hersteller'] = zertifikat.wps.Herstellere
        report_context['operator_name'] = zertifikat.operator_name
        report_context['identification'] = zertifikat.identification
        report_context['stamp'] = zertifikat.stamp
        report_context['wps'] = zertifikat.wps.Beleg_Nr
        report_context['test_coupon'] = zertifikat.test_coupon_affichage
        report_context['production_weld'] = zertifikat.production_weld_affichage
        report_context['uns'] = zertifikat.uns.astm
        report_context['thickness'] = zertifikat.thickness
        report_context['base_metal'] = zertifikat.base_metal.p_no
        report_context['to_p_number'] = zertifikat.to_p_number.p_no
        report_context['position'] = zertifikat.position
        report_context['pipe_affichage'] = zertifikat.pipe_affichage
        report_context['plate_affichage'] = zertifikat.plate_affichage
        report_context['value_diameter'] = zertifikat.value_diameter
        report_context['filler_metal'] = zertifikat.filler_metal
        report_context['sfa'] = zertifikat.sfa.sfa
        report_context['filler_metal_classification'] = zertifikat.filler_metal_classification
        report_context['type_welding'] = zertifikat.type_welding
        report_context['type_welding_gel'] = zertifikat.type_welding_gel
        report_context['welding_process'] = zertifikat.welding_process
        report_context['welding_process_gel'] = zertifikat.welding_process_gel
        report_context['filler_used'] = zertifikat.filler_used
        report_context['filler_used_range'] = zertifikat.filler_used_range
        report_context['type_laser'] = zertifikat.type_laser
        report_context['type_laser_range'] = zertifikat.type_laser_range
        report_context['continuous_drive'] = zertifikat.continuous_drive
        report_context['continuous_drive_range'] = zertifikat.continuous_drive_range
        report_context['vacuum'] = zertifikat.vacuum
        report_context['vacuum_range'] = zertifikat.vacuum_range
        report_context['type_welding_machine'] = zertifikat.type_welding_machine
        report_context['range_qualified_welding_machine'] = zertifikat.range_qualified_welding_machine
        report_context['welding_process_machine'] = zertifikat.welding_process_machine
        report_context['welding_process_machine_gel'] = zertifikat.welding_process_machine_gel
        report_context['direct_remote_visual_comtrole'] = zertifikat.direct_remote_visual_comtrole
        report_context['direct_remote_visual_comtrole_range'] = zertifikat.direct_remote_visual_comtrole_range
        report_context['automatic_arc_voltage'] = zertifikat.automatic_arc_voltage
        report_context['automatic_arc_voltage_range'] = zertifikat.automatic_arc_voltage_range 
        report_context['automatic_joint_tracking'] = zertifikat.automatic_joint_tracking
        report_context['automatic_joint_tracking_range'] = zertifikat.automatic_joint_tracking_range
        report_context['comsumable_insert'] = zertifikat.comsumable_insert
        report_context['comsumable_insert_range'] = zertifikat.comsumable_insert_range
        report_context['position_range'] = zertifikat.position_range
        report_context['comsumable_insert'] = zertifikat.comsumable_insert
        report_context['comsumable_insert_range'] = zertifikat.comsumable_insert_range
        report_context['backing'] = zertifikat.backing
        report_context['backing_range'] = zertifikat.backing_range
        report_context['single_multiple_passes'] = zertifikat.single_multiple_passes
        report_context['single_multiple_passes_range'] = zertifikat.single_multiple_passes_range
        report_context['visual_completed_weld'] = zertifikat.visual_completed_weld
        report_context['transverse_face_affichage'] = zertifikat.transverse_face_affichage
        report_context['longitudinal_bends_affichage'] = zertifikat.longitudinal_bends_affichage
        report_context['side_bends_affichage'] = zertifikat.side_bends_affichage
        report_context['pipe_bends_affichage'] = zertifikat.pipe_bends_affichage
        report_context['plate_bends_affichage'] = zertifikat.plate_bends_affichage
        report_context['pipe_specimen_affichage'] = zertifikat.pipe_specimen_affichage
        report_context['plate_specimen_affichage'] = zertifikat.plate_specimen_affichage

        report_context['alternativ_volumetric'] = zertifikat.alternativ_volumetric
        report_context['Fillet_welt'] = zertifikat.Fillet_welt

        report_context['affichage_r_t'] = zertifikat.affichage_r_t
        report_context['affichage_u_t'] = zertifikat.affichage_u_t
        report_context['affichage_fillet_weld_plate'] = zertifikat.affichage_fillet_weld_plate
        report_context['affichage_fillet_weld_pipe'] = zertifikat.affichage_fillet_weld_pipe

        report_context['macro_exam'] = zertifikat.macro_exam
        report_context['fillet_size'] = zertifikat.fillet_size
        report_context['other_test'] = zertifikat.other_test
        report_context['convacity'] = zertifikat.convacity

        report_context['film_evaluated'] = zertifikat.film_evaluated
        report_context['company'] = zertifikat.company

        report_context['mecanical_test'] = zertifikat.mecanical_test
        report_context['labo_no'] = zertifikat.labo_no

        report_context['organization'] = zertifikat.organization

        report_context['date'] = zertifikat.date
        report_context['certified_by'] = zertifikat.certified_by
        report_context['supervised_by'] = zertifikat.supervised_by


        index = len (zertifikat.Tab_res)
        tab_type1=[]
        tab_type2=[]
        tab_type3=[]
        tab_res1=[]
        tab_res2=[]
        tab_res3=[]
        for i in range(0,index):
          tab_type1.append(zertifikat.Tab_res[i].type)
          tab_type2.append(zertifikat.Tab_res[i].type1)
          tab_type3.append(zertifikat.Tab_res[i].type2)
          tab_res1.append(zertifikat.Tab_res[i].res)
          tab_res2.append(zertifikat.Tab_res[i].res1)
          tab_res3.append(zertifikat.Tab_res[i].res2)
        if(index == 1):
          report_context['type1_0'] = tab_type1[0]
          report_context['type1_1'] = " "
          report_context['res1_0'] = tab_res1[0]
          report_context['res1_1'] = " "
          report_context['type2_0'] = tab_type2[0]
          report_context['type2_1'] = " "
          report_context['res2_0'] = tab_res2[0]
          report_context['res2_1'] = " "
          report_context['type3_0'] = tab_type3[0]
          report_context['type3_1'] = " "
          report_context['res3_0'] = tab_res3[0]
          report_context['res3_1'] = " "
        else:
          if(index == 2):
            report_context['type1_0'] = tab_type1[0]
            report_context['type1_1'] = tab_type1[1]
            report_context['res1_0'] = tab_res1[0]
            report_context['res1_1'] = tab_res1[1]
            report_context['type2_0'] = tab_type2[0]
            report_context['type2_1'] = tab_type2[1]
            report_context['res2_0'] = tab_res2[0]
            report_context['res2_1'] = tab_res2[1]
            report_context['type3_0'] = tab_type3[0]
            report_context['type3_1'] = tab_type3[1]
            report_context['res3_0'] = tab_res3[0]
            report_context['res3_1'] = tab_res3[1]

        return report_context

# Welding  Performance Qualification (WPQ)
class WOPQ(DeactivableMixin, ModelView, ModelSQL, MultiValueMixin):
    'Welding Performance Qualification'
    __name__ = 'welding.performance.qualification'

    title = fields.Selection([
        ('welding_performance', '---------------------------------------------------------------------------------WELDING PERFORMANCE QUALIFICATION (WPQ)---------------------------------------------------------------------------'),
    ], 'title', readonly = False,
        )
    Tab_res = fields.One2Many('wpq.results','link_wpqresults',' ')
    line_index = fields.Char("-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------")
    index2 = fields.Char("(*1)fillet qualifikation : all base material thicknesses,fillet sizes and diameters / kehlnahtqualifikation:alle Grundwerkstoffdicken,kehlnahtdicken und Durchmesser")
    index3 = fields.Char("(*2)including unassigned metals of similar chemical composition(see QW-423.1)/einschließlich nichtzugeordneter werkstoffe mit ähnlicher chem.Zusammensetzung")

    filler_metal_1 = fields.Many2One('party.sfa', 'Filler metal or electrode specification(s)                                                             (SFA)(info.only)',
           ondelete='CASCADE')
    filler_metal_2 = fields.Function(fields.Char("Filler metal or electrode classification(s)(info.only)                                                    (QW-404)"),"On_Change_filler_metal_1")
    subtitle = fields.Char("subtitle")
    subtitle2 = fields.Char("Test Description")
    wps = fields.Many2One('party.wps', 'Identification of WPS followed')
    base_metal = fields.Many2One('party.pnumber', 'Base metal P-Number to P-Number                                                                             (QW-403)')
    p_number = fields.Many2One('party.pnumber', 'to')
    test_coupon = fields.Boolean("Test coupon")
    affichage_test_coupon = fields.Function(fields.Char(" "),"On_Change_test_coupon")
    production_weld = fields.Function(fields.Boolean("Production weld"),"On_Change_coupon")
    affichage_production_weld = fields.Function(fields.Char(" "),"On_Change_production_weld")
    plate = fields.Boolean("Plate")
    plate_affichage = fields.Function(fields.Char(" "),"On_Change_platte")
    plate_geltungs = fields.Function(fields.Char(" "),"On_change_plate2")
    base_geltungs = fields.Function(fields.Char(" "),"On_change_base2")
    pipe = fields.Function(fields.Boolean("Pipe (enter diamter[mm], if pipe or tube)"),"On_Change_plate")
    pipe_affichage = fields.Function(fields.Char(" "),"On_Change_pippe")
    space = fields.Char("                                                                                                                                                   ")
    space1 = fields.Char(" ")
    subtitle1 = fields.Function(fields.Char("subtitle1"),"On_get_title")
    operator_name = fields.Char("Welder's name")
    identification_no = fields.Char("Identification no.")
    stamp_no = fields.Char("Stamp no.")
    specification = fields.Selection([
        ('A 1010 40', 'A 1010 40'),
    ], 'Specification and type/grade or UNS Number of base metal(s)', readonly = False,
        )
    blech_rohr = fields.Selection([
        ('P', 'P | Plate(Blech)'),
        ('T', 'T | Pipe(Rohr)'),
    ], 'Blech oder Rohr', readonly = False,
        )
    nahtart = fields.Selection([
        ('BW', 'BW | Groove(Stumpfnaht)'),
        ('FW', 'FW | Fillet(Kehlnaht)'),
    ], 'Nahtart', readonly = False,
        )

    consumable_insert = fields.Selection([
        ('without', 'Without'),
        ('with', 'With'),
    ], 'Consumable insert(GTAW or PAW)                                                                         (QW-404.22)', readonly = False,
        )
    filler_mettal_product = fields.Selection([
        ('Solid cored', 'Solid cored | Massivdraht/-stab'),
        ('Flux cored', 'Flux cored | Fülldrahtelektrode'),
        ('Metall cored', 'Metall cored | Metallpulver-Fülldrahtelektrode'),
        ('Powder', 'Powder | Pulver'),
    ], 'Filler Metal Product Form                                                                                   (GTAW or PAW)', readonly = False,
        )
    filler_mettal_product_gel =fields.Function(fields.Char(" "),"On_Change_filler_mettal_product")


    consumable_insert_gesltungs = fields.Function(fields.Char(" "),"On_Change_consumable_insert")
    backing = fields.Selection([
        ('with', 'with'),
        ('without', 'without'),
        ('no backing', 'no backing'),
        ('backing used', 'backing used'),
        ('metal', 'metal'),
        ('weld metal', 'weld metal'),
        ('double-welded', 'double welded'),
        ('flux', 'flux'),
    ], 'Backing(with/without)                                                                                                      (QW-402)', readonly = False,
        )

    backing_geltungs = fields.Function(fields.Char(" "),"On_Change_backing")

    type_used = fields.Selection([
        ('manual', 'manual'),
        ('semi-auto', 'semi-auto'),
        ('machine', 'machine'),
        ('automatic', 'automatic'),
    ], 'Type(i.e:manual,semi-automatic) used                                                                     (QW-410.25)', readonly = False,
        )
    type_used_geltungs = fields.Function(fields.Char(" "),"On_Change_type_used")
    thickness = fields.Char("Thickness")
    position1 = fields.Selection('on_change_blechrohr','Position qualified (2G,6G,3F,etc.)                                                                                 (QW-405)', readonly = False,)
    position = fields.Selection([
        ('1F', '1F | Wannenposition am rotierenden Rohr - Achse geneigt(45°) | PA'),
        ('1G', '1G | Wanne am rotierenden Rohr - Achse waagerecht | PA'),
        ('2F', '2F | horizontal-vertikal am festen Rohr - Achse senkrecht | PB'),
        ('2Fr', '2Fr | horizontal-vertikal am rotierenden Rohr - Achse waagerecht | PB'),
        ('2G', '2G | quer am festen Rohr - Achse senkrecht | PC'),
        ('2G/5G', '2G/5G | quer am festen Rohr / vertikal am festen Rohr'),
        ('4F', '4F | horizontal-überkopf am festen Rohr - Achse senkrecht | PD'),
        ('5F', '5F | steigend oder fallend am festen Rohr - Achse waagerecht'),
        ('5Fd', '5Fd | fallend am festen Rohr - Achse waagerecht | PJ'),
        ('5Fu', '5Fu | steigend am festen Rohr - Achse waagerecht | PH'),
        ('5G', '5G | steigend oder fallend am festen Rohr - Achse waagerecht'),
        ('5Gd', '5Gd | fallend am festen Rohr - Achse waagerecht | PJ'),
        ('5Gu', '5Gu | steigend am festen Rohr - Achse waagerecht | PH'),
        ('6G', '6G | steigend oder fallend am festen Rohr - Achse geneigt(45°)'),
        ('6Gd', '6Gd | fallend am festen Rohr - Achse geneigt(45°) | J-L045'),
        ('6Gu', '6Gu | steigend am festen Rohr - Achse geneigt(45°) | H-L045'),
        ('SP', 'SP | Sonderposition'),
    ], 'Position qualified (2G,6G,3F,etc.)                                                                                 (QW-405)', readonly = False,
        )
    welding_process = fields.Selection([
        ('OFW', 'OFW | Oxyfuel Gas Welding | 31 | Gas'),
        ('OHW', 'OHW | Oxyhydrogen Welding | 313 | Gas'),
        ('OAW', 'OAW | Oxyacetylene Welding | 311 | Gas'),
        ('SMAW', 'SMAW | Shielded Metal-Arc Welding | 111 | E'),
        ('SAW', 'SAW | Submerged-Arc Welding | 12 | UP'),
        ('FCAW', 'FCAW | Flux Cored-Arc Welding | 136 | MAG'),
        ('GMAW', 'GMAW | Gas Metal-Arc Welding | 135 | MAG'),
        ('GTAW', 'GTAW | Gas Tungsten-Arc Welding | 141 | WIG'),
        ('PAW', 'PAW | Plasma-Arc Welding | 15 | WPL'),
    ], 'Welding process(es)                                                                                                       (QW-401)', readonly = False,
        )
    welding_process_geltungs = fields.Function(fields.Char(" "),"On_Change_welding_process")
    pipe2 = fields.Integer(" ")
    pipe21 = fields.Integer(" ")
    deposit = fields.Integer("Deposit thickness for each process[mm]                                                                                     -")
    deposit_geltungs = fields.Function(fields.Char(" "),"On_Change_deposit")
    subtitle4 = fields.Char("Actual Values                              ")
    subtitle5 = fields.Char("           Range Qualified")
    subtitle3 = fields.Char("Testing Variables and Qualification Limits Welding Variables (QW-350)                                     ")
    filler_metal = fields.Selection([
        ('1', '1 | Heavy rutile coated iron powder electrodes | SFA-5.1:EXX20, 22, 24, 27, 28;SFA-5.4;SFA-5.5'),
        ('2', '2 | Most Rutile consumables | SFA-5.1:EXX12, 13, 14, 19;SFA-5.5;E(X)XX13-X'),
        ('3', '3 | Cellulosic electrode | SFA-5.1:EXX10, 11;SFA-5.5:E(X)XX10-X, 11-X'),
        ('4', '4 | Basic coated electrodes | SFA-5.1:EXX15, 16, 18, 18M, 48;SFA-5.4;SFA-5.5'),
        ('5', '5 | High alloy austenitic stainless steel and duplex | SFA-5.4:EXXX(X)-15,-16,-17'),
        ('6', '6 | Any steel solid or cored wire (with flux or metal) | '),
        ('21', '21 | Aluminium and Aluminium Alloys | SFA-5.3:E1100,E3003;SFA-5.10'),
        ('22', '22 | Aluminium and Aluminium Alloys | SFA-5.10:ER5183,ER5356,...,R5183,R5356,...'),
        ('23', '23 | Aluminium and Aluminium Alloys | SFA-5.3:E4043;SFA-5.10'),
        ('24', '24 | Aluminium and Aluminium Alloys | SFA-5.10:R-A356.0,R-A357.0,...,R206.0,R357.0'),
        ('25', '25 | Aluminium and Aluminium Alloys | SFA-5.10:ER2319,R2319'),
        ('31', '31 | Copper and Copper Alloys | SFA-5.6:ECu;SFA-5.7:ERCu'),
        ('32', '32 | Copper and Copper Alloys | SFA-5.6:ECuSi;SFA-5.7:ERCuSi-A'),
        ('33', '33 | Copper and Copper Alloys | SFA-5.6:ECuSn-A;ECuSn-C;SFA-5.7:ERCuSn-A'),
        ('34', '34 | Copper and Copper Alloys | SFA-5.6:ECuNi;SFA-5.7:ERCuNi;SFA-5.30:IN67'),
        ('35', '35 | Copper and Copper Alloys | SFA-5.8:RBCuZn-A,-B,-C,-D'),
        ('36', '36 | Copper and Copper Alloys | SFA-5.6:ECuAI-A2, ECuAI-B;SFA-5.7:ERCuAI-A1,2,3'),
        ('37', '37 | Copper and Copper Alloys | SFA-5.6:ECuMnNiAI,ECuNiAI;SFA-5.7:ERCuNiAI'),
        ('41', '41 | Nickel and Nickel Alloys | SFA-5.11:ENi-1;SFA-5.14:ERNi-1;SFA-5.30:IN61'),
        ('42', '42 | Nickel and Nickel Alloys | SFA-5.11:ENiCu-7;SFA-5.14:ERNiCu-7,-8;SFA-5.30:IN60'),
        ('43', '43 | Nickel and Nickel Alloys | SFA-5.11:ENiCrFe-X,ENiCrMo-X;SFA-5.14;SFA-5.30'),
        ('44', '44 | Nickel and Nickel Alloys | SFA-5.11:ENiMo-X;SFA-5.14:ERNiMo-X'),
        ('45', '45 | Nickel and Nickel Alloys | SFA-5.11:ENiCrMo-X;SFA-5.14:ERNiCrMo-X,ERNiFeCr-1'),
        ('51', '51 | Titanium and Titanium Alloys | SFA-5.16:ERTi-1,-2,-3,-4'),
        ('52', '52 | Titanium and Titanium Alloys | SFA-5.16:ERTi-7'),
        ('53', '53 | Titanium and Titanium Alloys | SFA-5.16:ERTi-9,ERTi-9ELI'),
        ('54', '54 | Titanium and Titanium Alloys | SFA-5.16:ERTi-12'),
        ('55', '55 | Titanium and Titanium Alloys | SFA-5.16:ERTi-5,ERTi-5ELI,ERTi-6,ERTi-6ELI,ERTi-15'),
        ('61', '61 | Zirconium and Zirconium Alloys | SFA-5.24:ERZr2,3,4'),
        ('71', '71 | Hard-Facing Weld Metal Overlay | SFA-5.13'),
        ('72', '72 | Hard-Facing Weld Metal Overlay | SFA-5.21'),
    ], 'Filler metal F-Number(s)                                                                                           (QW-404.15)', readonly = False,
        )
    filler_metal_geltungs = fields.Function(fields.Char(" "),"On_change_filler_metal")
    filler_metal_geltungs2 = fields.Function(fields.Char(" "),"On_change_filler_metal2")
    process1 = fields.Char("Process 1                                                                                                                                        ")
    process1_val = fields.Char("  ")
    process2_val = fields.Char("  ")
    type_fuelgaz = fields.Char("Type of fuel gas(OFW)                                                                                                                    ")
    process2 = fields.Char("Process 2                                                                                                                                        ")
    layer_min1 = fields.Boolean("3 layers minimum :Yes")
    affichage_layer_min1 = fields.Function(fields.Char(" "),"On_change_layer_min1")
    layer_min2 = fields.Boolean("3 layers minimum :Yes")
    affichage_layer_min2 = fields.Function(fields.Char(" "),"On_change_layer_min2")
    layer_min3 = fields.Function(fields.Boolean("No"),"On_Change_layer_min1")
    affichage_layer_min3 = fields.Function(fields.Char(" "),"On_change_layer_min3")
    layer_min4 = fields.Function(fields.Boolean("No"),"On_Change_layer_min2")
    affichage_layer_min4 = fields.Function(fields.Char(" "),"On_change_layer_min4")
    process_val1 = fields.Char(" ")
    process_val2 = fields.Char(" ")
    bezeichnung = fields.Function(fields.Char("Bezeichnung"),"On_Change_andere_options")
    groove1 = fields.Function(fields.Char("Groove : Stumpfnaht: Plate & Pipe > 24in. (610 mm)∅                                                               "),"On_Change_blech_nahtart")
    groove2 = fields.Function(fields.Char("Pipe <= 24in. (610 mm)∅                                                                                                              "),"On_Change_blech_nahtart1")
    fillet1 = fields.Function(fields.Char("Fillet : Kehlnaht : Plate & Pipe                                                                                                       "),"On_Change_blech_nahtart2")

    vertical_progression = fields.Selection([
        ('up', 'up | steigend'),
        ('down', 'down | fallend'),
        ('n.a.', 'n.a. | nicht anwendbar'),
    ], 'Vertical progression(uphill or downhill)                                                                                         ', readonly = False,
        )


    transfert_mode = fields.Selection([
        ('spray arc', 'spray arc'),
        ('globular arc', 'globular arc'),
        ('pulsating arc', 'pulsating arc'),
        ('short circuiting arc', 'short circuiting arc'),
    ], 'Transfer mode (spray/globular or pulse to short circuit-GMAW)                                                 ', readonly = False,
        )

    transfert_mode_gel = fields.Function(fields.Char(" "),"On_Change_transfert_mode")


    vertical_progression_gel = fields.Function(fields.Char(" "),"On_Change_vertical_progression")

    inert_gaz = fields.Selection('on_change_weld_process','Inert gas backing (GTAW, PAW, GMAW)                                                                    (QW-408)', readonly = False,)
    inert_gaz_gel = fields.Function(fields.Char(" "),"On_Change_inert_gaz")

    current_type = fields.Selection([
        ('AC', 'AC | Wechselstrom'),
        ('DCEP', 'DCEP | Gleichstrom mit positiver Elektrode'),
        ('DCEN', 'DCEN | Gleichstrom mit negativer Elektrode'),
    ], 'GTAW current type/polarity(AC,DCEP,DCEN)                                                         (QW-409.4)', readonly = False,
        )

    visual_examination = fields.Selection([
        ('acceptable', 'acceptable | bestanden'),
        ('not applicable', 'not applicable | nicht anwendbar'),
    ], 'Visual examination of completed weld(QW-302.4)                                                                                               ', readonly = False,
        )

    alternativ_volumetric = fields.Selection([
        ('acceptable', 'acceptable | bestanden'),
        ('not applicable', 'not applicable | nicht anwendbar'),
    ], 'Alternative Volumetric Examination Results                                                                                     (QW-191)  ', readonly = False,
        )

    Fillet_welt = fields.Selection([
        ('acceptable', 'acceptable | bestanden'),
        ('not applicable', 'not applicable | nicht anwendbar'),
    ], 'Fillet weld - facture test (QW-181.2)                                                                                                                     ', readonly = False,
        )

    r_t = fields.Boolean("RT")
    affichage_r_t = fields.Function(fields.Char(" "),"On_Change_r_t")
    u_t = fields.Boolean("UT")
    affichage_u_t = fields.Function(fields.Char(" "),"On_Change_u_t")

    fillet_weld_plate = fields.Boolean("Fillet welds in plate [QW-462.4(b)]                                                                                                                        ")
    affichage_fillet_weld_plate=fields.Function(fields.Char(" "),"On_Change_fillet_weld_plate")
    fillet_weld_pipe = fields.Boolean("Fillet welds in pipe [QW-462.4(c)]")
    affichage_fillet_weld_pipe = fields.Function(fields.Char(" "),"On_Change_fillet_weld_pipe")
    macro_exam = fields.Selection([
        ('acceptable', 'acceptable | bestanden'),
        ('not applicable', 'not applicable | nicht anwendbar'),
    ], 'Macro examination (QW-184)                                                                                                                               ', readonly = False,
        )

    fillet_size = fields.Char("Fillet size                                                                                                                                                                ")
    convacity = fields.Char("Convacity/Convexity                                                                                                                                              ")
    other_test = fields.Char("Other tests                                                                                                                                                              ")

    film_evaluated = fields.Char("Film or specimens evaluated by                                                                                                                           ")
    company = fields.Char("Company                                                                                                                                                                ")
    mecanical_test = fields.Char("Mechanical tests conducted by                                                                                                                             ")
    labo_no = fields.Char("Laboratory tests no                                                                                                                                                ")
    supervised_by = fields.Char("Welding supervised by                                                                                                                                          ")
    index = fields.Char("We certify that the statements in this record are correct and that the test coupons were prepared, welded, and tested in accordance with                                                        ")
    index1 = fields.Char("the requirements of Section IX of the ASME BOILER AND PRESSURE VESSEL CODE                                                                                                                                  ")
    organization = fields.Selection([
        ('DGZfP', 'DGZfP-Ausbildungszentrum Wittenberge'),
        ('Harrison', 'Harrison Mechanical Corporation'),
        ('MAN-Technologie', 'MAN-Technologie, Oberpfaffenhofen, Abtlg.WOP'),
    ], 'Organization                                                                                                                                                          ', readonly = False,
        )

    certified_by = fields.Selection([
        ('Dipl.Ing. Prüfer', 'Dipl.Ing. Prüfer'),
        ('Dipl.Ing. Schulz', 'Dipl.Ing. Schulz'),
        ('Dipl.Ing. Tester', 'Dipl.Ing. Tester'),
        ('Dipl.Ing. Zertifizierer', 'Dipl.Ing. Zertifizierer'),
    ], 'Certified by                                                                                                                                                            ', readonly = False,
        )
    date = fields.Date("Date")

    current_type_gel = fields.Function(fields.Char(" "),"On_Change_current_type")

    transverse_face = fields.Boolean("Transverse face and root bends[QW-362.3(a)]                                                                                                       ")
    affichage_transverse_face = fields.Function(fields.Char(" "),"On_Change_transverse_face")
    longitudinal_bends = fields.Boolean("Longitudinal bends[QW-462.3(b)]")
    affichage_longitudinal_bends = fields.Function(fields.Char(" "),"On_Change_longitudinal_bends")
    side_bends = fields.Boolean("Side bends[QW-462.2]")
    affichage_side_bends = fields.Function(fields.Char(" "),"On_Change_side_bends")

    pipe_bends = fields.Boolean("Pipe bend specimen,corrosion-resistant weld metal overlay[QW-462.5(c)]                                                       ")
    affichage_pipe_bends = fields.Function(fields.Char(" "),"On_Change_pipe_bends")
    plate_bends = fields.Boolean("Plate bend specimen,corrosion-resistant weld metal overlay[QW-462.5(d)]                                                      ")
    affichage_plate_bends = fields.Function(fields.Char(" "),"On_Change_plate_bends")
    pipe_specimen = fields.Boolean("Pipe Specimen, macro test for fusion [QW-462.5(b)]")
    affichage_pipe_specimen = fields.Function(fields.Char(" "),"On_Change_pipe_specimen")
    plate_specimen = fields.Boolean("Plate Specimen, macro test for fusion [QW-462.5(e)]")
    affichage_plate_specimen = fields.Function(fields.Char(" "),"On_Change_plate_specimen")



    @fields.depends('position1', 'blech_rohr')
    def on_change_blechrohr(self):
          tab=[]
          if(self.blech_rohr == "T"):
             tab.append(('1F', '1F | Wannenposition am rotierenden Rohr - Achse geneigt(45°) | PA'))
             tab.append(('1G', '1G | Wanne am rotierenden Rohr - Achse waagerecht | PA'))
             tab.append(('2F', '2F | horizontal-vertikal am festen Rohr - Achse senkrecht | PB'))
             tab.append(('2Fr', '2Fr | horizontal-vertikal am rotierenden Rohr - Achse waagerecht | PB'))
             tab.append(('2G', '2G | quer am festen Rohr - Achse senkrecht | PC'))
             tab.append(('2G/5G', '2G/5G | quer am festen Rohr / vertikal am festen Rohr'))
             tab.append(('4F', '4F | horizontal-überkopf am festen Rohr - Achse senkrecht | PD'))
             tab.append(('5F', '5F | steigend oder fallend am festen Rohr - Achse waagerecht'))
             tab.append(('5Fd', '5Fd | fallend am festen Rohr - Achse waagerecht | PJ'))
             tab.append(('5Fu', '5Fu | steigend am festen Rohr - Achse waagerecht | PH'))
             tab.append(('5G', '5G | steigend oder fallend am festen Rohr - Achse waagerecht'))
             tab.append(('5Gd', '5Gd | fallend am festen Rohr - Achse waagerecht | PJ'))
             tab.append(('5Gu', '5Gu | steigend am festen Rohr - Achse waagerecht | PH'))
             tab.append(('6G', '6G | steigend oder fallend am festen Rohr - Achse geneigt(45°)'))
             tab.append(('6Gd', '6Gd | fallend am festen Rohr - Achse geneigt(45°) | J-L045'))
             tab.append(('6Gu', '6Gu | steigend am festen Rohr - Achse geneigt(45°) | H-L045'))
             tab.append(('SP', 'SP | Sonderposition'))
             return tab
          else:
            if(self.blech_rohr == "P"):
             tab.append(('1F', '1F | Wannenposition | PA'))
             tab.append(('2F', '2F | horizontal-vertikalposition | PB'))
             tab.append(('3Fd', '3Fd | fallposition | PG'))
             tab.append(('3Fu', '3Fu | steigposition | PF'))
             tab.append(('3F', '3F | Vertikal steigend oder fallend | '))
             tab.append(('4F', '4F | Horizontal-Überkopfposition  | PD'))
             tab.append(('3F/4F', '3F/4F | Vertikalposition/Horizontal-Überkopfposition | '))
             tab.append(('1G', '1G | Wannenposition | PA'))
             tab.append(('2G', '2G | Querposition | PC'))
             tab.append(('3Gd', '3Gd | Fallposition | PG'))
             tab.append(('3Gu', '3Gu | Steigposition | PF'))
             tab.append(('3G', '3G | Vertikal steigend oder fallend | '))
             tab.append(('4G', '4G | Überkopfposition | PE'))
             tab.append(('3Gd/4G', '3Gd/4G | fallposition/Überkopfposition | PG/PE'))
             tab.append(('3Gu/4G', '3Gu/4G | Steigposition/Überkopfposition | PF/PE'))
             tab.append(('2/3/4G', '2/3/4G | Querposition/Vertikalposition/Überkopfposition | '))
             tab.append(('SP', 'SP | Sonderpositionen | '))
             return tab

    def On_Change_fillet_weld_plate(self,fillet_weld_plate):
       if(self.fillet_weld_plate == True):
        return "|✘|"
       else:
        return "|  |"

    def On_Change_fillet_weld_pipe(self,fillet_weld_pipe):
       if(self.fillet_weld_pipe == True):
        return "|✘|"
       else:
        return "|  |"


    def On_Change_r_t(self,r_t):
       if(self.r_t == True):
        return "|✘|"
       else:
        return "|  |"

    def On_Change_u_t(self,u_t):
       if(self.u_t == True):
        return "|✘|"
       else:
        return "|  |"


    def On_Change_plate_specimen(self,plate_specimen):
       if(self.plate_specimen == True):
        return "|✘|"
       else:
        return "|  |"



    def On_Change_pipe_specimen(self,pipe_specimen):
       if(self.pipe_specimen == True):
        return "|✘|"
       else:
        return "|  |"



    def On_Change_plate_bends(self,plate_bends):
       if(self.plate_bends == True):
        return "|✘|"
       else:
        return "|  |"



    def On_Change_pipe_bends(self,pipe_bends):
       if(self.pipe_bends == True):
        return "|✘|"
       else:
        return "|  |"


    def On_Change_transverse_face(self,transverse_face):
       if(self.transverse_face == True):
        return "|✘|"
       else:
        return "| |"

    def On_Change_longitudinal_bends(self,longitudinal_bends):
       if(self.longitudinal_bends == True):
        return "|✘|"
       else:
        return "| |"

    def On_Change_side_bends(self,side_bends):
       if(self.side_bends == True):
        return "|✘|"
       else:
        return "| |"


    def On_change_layer_min1(self,layer_min1):
       if(self.layer_min1 == True):
         return "✘"
       else:
         return "-"

    def On_change_layer_min2(self,layer_min2):
       if(self.layer_min2 == True):
         return "✘"
       else:
         return "-"

    def On_change_layer_min3(self,layer_min3):
       if(self.layer_min3 == True):
         return "✘"
       else:
         return "-"

    def On_change_layer_min4(self,layer_min4):
       if(self.layer_min4 == True):
         return "✘"
       else:
         return "-"


    def On_Change_pippe(self,pipe):
       if(self.pipe == True):
         return "✘"
       else:
         return " "


    def On_Change_platte(self,plate):
       if(self.plate == True):
         return "✘"
       else:
         return " "


    def On_Change_test_coupon(self,test_coupon):
       if(self.test_coupon == True):
         return "✘"
       else:
         return " "

    def On_Change_production_weld(self,production_weld):
       if(self.production_weld == True):
         return "✘"
       else:
         return " "


    def On_Change_layer_min1(self,layer_min1):
       if(self.layer_min1 == True):
         return False
       else:
         return True

    def On_Change_layer_min2(self,layer_min2):
       if(self.layer_min2 == True):
         return False
       else:
         return True


    def On_Change_current_type(self,current_type):
       return " "

    def On_Change_transfert_mode(self,transfert_mode):
       return " "

    def On_Change_inert_gaz(self,inert_gaz):
       return " "

    @fields.depends('inert_gaz', 'welding_process')
    def on_change_weld_process(self):
        tab=[]
        if(self.welding_process =="OFW" or self.welding_process =="OHW" or self.welding_process =="OAW" or self.welding_process =="SMAW" or self.welding_process =="SAW"):
            tab.append(("ISO 14175-N5-NH-20", "ISO 14175-N5-NH-20 | EN ISO 14175 | Formiergas 80/20 |    "))
            tab.append(("ISO 14175-R2-ArH-20", "ISO 14175-R2-ArH-20 | EN ISO 14175 | ARCAL PLASMA 62 |    "))
            return tab
        if(self.welding_process =="GTAW"):
            tab.append(("ISO 14175-I1-Ar", "ISO 14175-I1-Ar | EN ISO 14175 | ARCAL 1 | MIG,WIG,WPL"))
            tab.append(("ISO 14175-I2-He", "ISO 14175-I2-He | EN ISO 14175 | MIG,WIG"))
            tab.append(("ISO 14175-I3-ArHe-30", "ISO 14175-I3-ArHe-30 | EN ISO 14175 | ARCAL 33 | MIG,WIG,WPL"))
            tab.append(("ISO 14175-N2-ArN-2", "ISO 14175-N2-ArN-2 | EN ISO 14175 | ARCAL 391 | WIG"))
            tab.append(("ISO 14175-N4-ArNH-3/0,7", "ISO 14175-N4-ArNH-3/0,7 | EN ISO 14175 | ARCAL 405 | WIG"))
            tab.append(("ISO 14175-N5-NH-20", "ISO 14175-N5-NH-20 | EN ISO 14175 | Formiergas 80/20"))
            tab.append(("ISO 14175-R1-ArH-10", "ISO 14175-R1-ArH-10 | EN ISO 14175 | NOXAL 4 | WIG"))
            tab.append(("ISO 14175-R1-ArH-2,4", "ISO 14175-R1-ArH-2,4 | EN ISO 14175 |ARCAL 10 | WIG,WPL"))
            tab.append(("ISO 14175-R2-ArH-20", "ISO 14175-R2-ArH-20 | EN ISO 14175 | ARCAL PLASMA 62"))
            tab.append(("ISO 14175-Z-Ar+N-0,015", "ISO 14175-Z-Ar+N-0,015 | EN ISO 14175 | ARCAL 1N | WIG"))
            return tab
        if(self.welding_process =="PAW"):
           tab.append(("ISO 14175-I1-Ar", "ISO 14175-I1-Ar | EN ISO 14175 | ARCAL 1 | MIG,WIG,WPL"))
           tab.append(("ISO 14175-I3-ArHe-30", "ISO 14175-I3-ArHe-30 | EN ISO 14175 | ARCAL 33 | MIG,WIG,WPL"))
           tab.append(("ISO 14175-N5-NH-20", "ISO 14175-N5-NH-20 | EN ISO 14175 | Formiergas 80/20"))
           tab.append(("ISO 14175-R1-ArH-2,4", "ISO 14175-R2-ArH-2,4 | EN ISO 14175 | ARCAL 10 | WIG,WPL"))
           tab.append(("ISO 14175-R2-ArH-20", "ISO 14175-R2-ArH-20 | EN ISO 14175 | ARCAL PLASMA 62"))
           return tab
        else:
           if(self.welding_process =="FCAW" or self.welding_process =="GMAW"):
             tab.append(("ISO 14175-C1-C", "ISO 14175-C1-C | EN ISO 14175 |  | MAG "))
             tab.append(("ISO 14175-M12-ArC-2", "ISO 14175-M12-ArC-2 | EN ISO 14175 | ARCAL 12 | MAG"))
             tab.append(("ISO 14175-M12-ArHeC-18/1", "ISO 14175-M12-ArHeC-18/1 | EN ISO 14175 | ARCAL 121 | MAG"))
             tab.append(("ISO 14175-M13-ArO-2", "ISO 14175-M13-ArO-2 | EN ISO 14175 | CARGAL | MAG"))
             tab.append(("ISO 14175-M14-ArCO-3/1", "ISO 14175-M14-ArCO-3/1 | EN ISO 14175 | ARCAL 14 | MAG"))
             tab.append(("ISO 14175-M20-ArC-8", "ISO 14175-M20-ArC-8 | EN ISO 14175 | ARCAL 21 | MAG"))
             tab.append(("ISO 14175-M21-ArC-18", "ISO 14175-M21-ArC-18 | EN ISO 14175 | ATAL,ARCAL5 | MAG"))
             tab.append(("ISO 14175-M22-ArO-8", "ISO 14175-M22-ArO-8 | EN ISO 14175 | CARGAL4 | MAG"))
             tab.append(("ISO 14175-M23-ArCO-5/5", "ISO 14175-M23-ArCO-5/5 | EN ISO 14175 | TERAL | MAG"))
             tab.append(("ISO 14175-M24-ArCO-12/2", "ISO 14175-M24-ArCO-12/2 | EN ISO 14175 | ARCAL 24 | MAG"))
             tab.append(("ISO 14175-N5-NH-20", "ISO 14175-N5-NH-20 | EN ISO 14175 | Formiergas 80/20"))
             tab.append(("ISO 14175-R2-ArH-20", "ISO 14175-R2-ArH-20 | EN ISO 14175 | ARCAL PLASMA 62"))
             return tab



    def On_Change_vertical_progression(self,vertical_progression):
      if(self.vertical_progression == "up"):
         return "vertical up only"
      else:
        if(self.vertical_progression =="down"):
           return "vertical down only"

    def On_Change_blech_nahtart(self,blech_rohr):
      if(self.blech_rohr =="T" and self.nahtart =="FW" and (self.position1 == "1F" or self.position1 == "2Fr" or self.position1 == "2F" or self.position1 == "4F" or self.position1 == "5Fd" or self.position1 == "5Fu" or self.position1 == "5F" or self.position1 == "SP")):
         return "none / nicht"
      if(self.blech_rohr =="T" and self.nahtart =="BW" and self.position1 == "2G"):
         return "F,H/PA,PC"
      if(self.blech_rohr =="T" and self.nahtart =="BW" and self.position1 == "5Gd"):
         return "F,V,O/PA,PG,PE"
      if(self.blech_rohr =="T" and self.nahtart =="BW" and (self.position1 == "5Gu" or self.position1 == "5G")):
         return "F,V,O/PA,PF,PE"
      if(self.blech_rohr =="T" and self.nahtart =="BW" and (self.position1 == "6Gd" or self.position1 == "6Gu" or self.position1 == "6G" or self.position1 == "2G/5G")):
         return "all / alle"
      if(self.blech_rohr =="T" and self.nahtart =="BW" and self.position1 == "SP"):
         return "SP,F/SP,PA"
      if(self.blech_rohr =="P" and self.nahtart =="FW" and (self.position1 == "1F" or self.position1 == "2F" or self.position1 == "3Fd" or self.position1 == "3Fu" or self.position1 == "3F" or self.position1 == "4F" or self.position1 == "3F/4F")):
         return "none / nicht"
      if(self.blech_rohr =="P" and self.nahtart =="BW" and self.position1 == "1G"):
         return "F/PA"
      if(self.blech_rohr =="P" and self.nahtart =="BW" and self.position1 == "2G"):
         return "F,H/PA,PC"
      if(self.blech_rohr =="P" and self.nahtart =="BW" and self.position1 == "3Gd"):
         return "F,V/PA,PG"
      if(self.blech_rohr =="P" and self.nahtart =="BW" and (self.position1 == "3Gu" or self.position1 == "3G")):
         return "F,V/PA,PF"
      if(self.blech_rohr =="P" and self.nahtart =="BW" and self.position1 == "4G"):
         return "F,O/PA,PE"
      if(self.blech_rohr =="P" and self.nahtart =="BW" and self.position1 == "3Gd/4G"):
         return "F,V,O/PA,PG,PE"
      if(self.blech_rohr =="P" and self.nahtart =="BW" and self.position1 == "3Gu/4G"):
         return "F,V,O/PA,PF,PE"
      if(self.blech_rohr =="P" and self.nahtart =="BW" and self.position1 == "2/3/4G"):
         return "all / alle"
      if(self.blech_rohr =="P" and self.nahtart =="BW" and self.position1 == "SP"):
         return "SP,F/SP,PA"
      if(self.blech_rohr =="P" and self.nahtart =="FW" and self.position1 == "SP"):
         return "none / nicht"
      else:
        if(self.blech_rohr =="T" and self.nahtart =="BW" and self.position1 == "1G"):
          return "F/PA"


    def On_Change_blech_nahtart1(self,blech_rohr):
      if(self.blech_rohr =="T" and self.nahtart =="FW" and (self.position1 == "1F" or self.position1 == "2Fr" or self.position1 == "2F" or self.position1 == "4F" or self.position1 == "5Fd" or self.position1 == "5Fu" or self.position1 == "5F" or self.position1 == "SP")):
         return "none / nicht"
      if(self.blech_rohr =="T" and self.nahtart =="BW" and self.position1 == "2G"):
         return "F,H/PA,PC"
      if(self.blech_rohr =="T" and self.nahtart =="BW" and self.position1 == "5Gd"):
         return "F,V,O/PA,PG,PE"
      if(self.blech_rohr =="T" and self.nahtart =="BW" and (self.position1 == "5Gu" or self.position1 == "5G")):
         return "F,V,O/PA,PF,PE"
      if(self.blech_rohr =="T" and self.nahtart =="BW" and (self.position1 == "6Gd" or self.position1 == "6Gu" or self.position1 == "6G" or self.position1 == "2G/5G")):
         return "all / alle"
      if(self.blech_rohr =="T" and self.nahtart =="BW" and self.position1 == "SP"):
         return "SP,F/SP,PA"
      if(self.blech_rohr =="P" and self.nahtart =="FW" and (self.position1 == "1F" or self.position1 == "2F" or self.position1 == "3Fd" or self.position1 == "3Fu" or self.position1 == "3F" or self.position1 == "4F" or self.position1 == "3F/4F")):
         return "none / nicht"
      if(self.blech_rohr =="P" and self.nahtart =="BW" and self.position1 == "1G"):
         return "F/PA"
      if(self.blech_rohr =="P" and self.nahtart =="BW" and self.position1 == "2G"):
         return "F,H/PA,PC"
      if(self.blech_rohr =="P" and self.nahtart =="BW" and self.position1 == "3Gd"):
         return "F/PA"
      if(self.blech_rohr =="P" and self.nahtart =="BW" and (self.position1 == "3Gu" or self.position1 == "3G")):
         return "F/PA"
      if(self.blech_rohr =="P" and self.nahtart =="BW" and self.position1 == "4G"):
         return "F/PA"
      if(self.blech_rohr =="P" and self.nahtart =="BW" and self.position1 == "3Gd/4G"):
         return "F/PA"
      if(self.blech_rohr =="P" and self.nahtart =="BW" and self.position1 == "3Gu/4G"):
         return "F/PA"
      if(self.blech_rohr =="P" and self.nahtart =="BW" and self.position1 == "2/3/4G"):
         return "F,H/PA,PC"
      if(self.blech_rohr =="P" and self.nahtart =="BW" and self.position1 == "SP"):
         return "SP,F/SP,PA"
      if(self.blech_rohr =="P" and self.nahtart =="FW" and self.position1 == "SP"):
         return "none / nicht"
      else:
        if(self.blech_rohr =="T" and self.nahtart =="BW" and self.position1 == "1G"):
          return "F/PA"

    def On_Change_blech_nahtart2(self,blech_rohr):
      if(self.nahtart =="FW" and self.position1 == "1F"):
         return "F/PA"
      if(self.blech_rohr =="T" and self.nahtart =="FW" and self.position1 == "4F"):
         return "F,H,O/PA,PB,PD"
      if(self.blech_rohr =="T" and self.nahtart =="FW" and (self.position1 == "5Fd" or self.position1 == "5Fu" or self.position1 == "5F" )):
         return "all / alle"
      if(self.blech_rohr =="T" and self.nahtart =="BW" and self.position1 == "1G"):
         return "F/PA"
      if(self.blech_rohr =="T" and self.nahtart =="BW" and self.position1 == "2G"):
         return "F,H/PA,PB"
      if(self.blech_rohr =="T" and self.nahtart =="BW" and (self.position1 == "5Gd" or self.position1 == "5Gu" or self.position1 == "5G" or self.position1 == "6Gd" or self.position1 == "6Gu" or self.position1 == "6G" or self.position1 == "2G/5G")):
         return "all / alle"
      if(self.position1 == "SP"):
         return "SP,F/SP,PA"
      if(self.blech_rohr =="P" and self.nahtart =="FW" and self.position1 == "1F"):
         return "F/PA"
      if(self.blech_rohr =="P" and self.nahtart =="FW" and self.position1 == "2F"):
         return "F,H/PA,PB"
      if(self.blech_rohr =="P" and self.nahtart =="FW" and self.position1 == "3Fd"):
         return "F,H,V/PA,PB,PG"
      if(self.blech_rohr =="P" and self.nahtart =="FW" and (self.position1 == "3Fu" or self.position1 == "3F")):
         return "F,H,V/PA,PB,PF"
      if(self.blech_rohr =="P" and self.nahtart =="FW" and self.position1 == "4F"):
         return "F,H,O/PA,PB,PD"
      if(self.blech_rohr =="P" and self.nahtart =="FW" and self.position1 == "3F/4F"):
         return "all / alle"
      if(self.blech_rohr =="P" and self.nahtart =="BW" and self.position1 == "1G"):
         return "F/PA"
      if(self.blech_rohr =="P" and self.nahtart =="BW" and self.position1 == "2G"):
         return "F,H/PA,PB"
      if(self.blech_rohr =="P" and self.nahtart =="BW" and self.position1 == "3Gd"):
         return "F,H,V/PA,PP,PG"
      if(self.blech_rohr =="P" and self.nahtart =="BW" and (self.position1 == "3Gu" or self.position1 == "3G")):
         return "F,H,V/PA,PB,PF"
      if(self.blech_rohr =="P" and self.nahtart =="BW" and self.position1 == "4G"):
         return "F,H,O/PA,PB,PE"
      if(self.blech_rohr =="P" and self.nahtart =="BW" and (self.position1 == "3Gd/4G" or self.position1 == "3Gu/4G" or self.position1 == "2/3/4G")):
         return "all / alle"
      else:
        if(self.blech_rohr =="T" and self.nahtart =="FW" and (self.position1 == "2Fr" or self.position1 == "2F")):
          return "F,H/PA,PB"


    def On_Change_andere_options(self,welding_process):
      if(self.blech_rohr =="P"):
        if(self.deposit is not None and self.base_metal is not None):
           return "ASME WPQ "+self.welding_process+" "+self.blech_rohr+" "+self.nahtart+" P"+self.base_metal.p_no+" t"+str(self.deposit)+" "+self.position
        else:
           return " "
      else:
        if(self.pipe21 is not None and self.deposit is not None and self.base_metal is not None):
           return "ASME WPQ "+self.welding_process+" "+self.blech_rohr+" "+self.nahtart+" P"+self.base_metal.p_no+" t"+str(self.deposit)+" D"+str(self.pipe21)+" "+self.position
        else:
           return " "

    def On_Change_deposit(self,deposit):
      if(self.deposit is not None):
        if(self.nahtart == "BW"):
           return "<="+str(round(2*self.deposit,1))+" mm;fillet:all(*1)"
        if(self.nahtart == "FW" and self.blech_rohr =="P" and self.deposit<=4):
           return str(self.deposit)+"-"+str(round(2*self.deposit,1))+" mm;fillet: <= "+str(self.deposit)+" mm"
        if(self.nahtart == "FW" and self.blech_rohr =="P" and self.deposit > 4 and self.deposit <=10 ):
           return "all thicknesses & fillet size"
        if(self.nahtart == "FW" and self.blech_rohr =="P" and self.deposit>10):
           return "see QW-452.5"
        else:
           if(self.nahtart == "FW" and self.blech_rohr =="T"):
             return "fillet:all"
      else:
        return " "

    def On_Change_consumable_insert(self,consumable_insert):
      if(self.consumable_insert =="without"):
        return "not permitted"
    def On_Change_filler_mettal_product(self,filler_mettal_product):
       return " "
    def On_change_filler_metal2(self,filler_metal):
      if(self.filler_metal =="1" and (self.backing =="without" or self.backing =="no backing")):
        return "F-No. 1 with &"
      if(self.filler_metal =="3" and (self.backing =="without" or self.backing =="no backing")):
           return "F-No. 1 through 3 with &"
      if(self.filler_metal =="4" and (self.backing =="without" or self.backing =="no backing")):
           return "F-No. 1 through 4 with &"
      if(self.filler_metal =="5" and (self.backing =="without" or self.backing =="no backing")):
           return "F-No. 1 and 5 with &"
      if(self.filler_metal =="34" or self.filler_metal =="41" or self.filler_metal =="42" or self.filler_metal =="43" or self.filler_metal =="44" or self.filler_metal =="45"):
           return "F-No. 34 &"
      else:
        if(self.filler_metal =="2" and (self.backing =="without" or self.backing =="no backing")):
           return "F-No. 1 through 2 with &"


    def On_change_filler_metal(self,filler_metal):
      if(self.filler_metal =="1" and (self.backing =="with" or self.backing =="backing used" or self.backing =="metal" or self.backing =="weld metal" or self.backing =="double-welded" or self.backing =="flux")):
        return "F-No. 1 with backing"
      if(self.filler_metal =="2" and (self.backing =="with" or self.backing =="backing used" or self.backing =="metal" or self.backing =="weld metal" or self.backing =="double-welded" or self.backing =="flux")):
        return "F-No. 1 through 2 with backing"
      if(self.filler_metal =="2" and (self.backing =="without" or self.backing =="no backing")):
        return "F-No. 2 without backing"
      if(self.filler_metal =="3" and (self.backing =="with" or self.backing =="backing used" or self.backing =="metal" or self.backing =="weld metal" or self.backing =="double-welded" or self.backing =="flux")):
        return "F-No. 1 through 3 with backing"
      if(self.filler_metal =="3" and (self.backing =="without" or self.backing =="no backing")):
        return "F-No. 3 without backing"
      if(self.filler_metal =="4" and (self.backing =="with" or self.backing =="backing used" or self.backing =="metal" or self.backing =="weld metal" or self.backing =="double-welded" or self.backing =="flux")):
        return "F-No. 1 through 4 with backing"
      if(self.filler_metal =="4" and (self.backing =="without" or self.backing =="no backing")):
        return "F-No. 4 without backing"
      if(self.filler_metal =="5" and (self.backing =="with" or self.backing =="backing used" or self.backing =="metal" or self.backing =="weld metal" or self.backing =="double-welded" or self.backing =="flux")):
        return "F-No. 1 and 5 with backing"
      if(self.filler_metal =="5" and (self.backing =="without" or self.backing =="no backing")):
        return "F-No. 5 without backing"
      if(self.filler_metal =="6"):
        return "all F-No. 6[see QW-433(1)]"
      if(self.filler_metal =="21" or self.filler_metal =="22" or self.filler_metal =="23" or self.filler_metal =="24" or self.filler_metal =="25"):
        return "all F-No. 21 through 25"
      if(self.filler_metal =="31"):
        return "Only F-No. 31"
      if(self.filler_metal =="32"):
        return "Only F-No. 32"
      if(self.filler_metal =="33"):
        return "Only F-No. 33"
      if(self.filler_metal =="34" or self.filler_metal =="41" or self.filler_metal =="42" or self.filler_metal =="43" or self.filler_metal =="44" or self.filler_metal =="45"):
        return "all F-No. 41 through 45"
      if(self.filler_metal =="35"):
        return "Only F-No. 35"
      if(self.filler_metal =="36"):
        return "Only F-No. 36"
      if(self.filler_metal =="37"):
        return "Only F-No. 37"
      if(self.filler_metal =="51" or self.filler_metal =="52" or self.filler_metal =="53" or self.filler_metal =="54" or self.filler_metal =="55"):
        return "all F-No. 51 through 55"
      if(self.filler_metal =="61"):
        return "all F-No. 61"
      if(self.filler_metal =="71"):
        return "Only F-No. 71"
      if(self.filler_metal =="72"):
        return "Only F-No. 72"
      else:
         if(self.filler_metal =="1" and (self.backing =="without" or self.backing =="no backing")):
           return "F-No. 4 without backing"

    def On_Change_filler_metal_1(self,filler_metal_1):
      if(self.filler_metal_1 is not None):
        return self.filler_metal_1.classification
      else:
        return " "
    def On_change_base2(self,base_metal):
        return "P1-11,P34,P41-P47 & (*2)"
    def On_change_plate2(self,plate):
     if(self.pipe21 is not None):
       if(self.plate == True and self.nahtart =="BW"):
         return "∅ >=2 7/8 in. (73 mm);fillet: all(*1)"
       if(self.plate == True and self.nahtart =="FW"):
         return "fillet: ∅ >=2 7/8 in. (73 mm)"
       if(self.plate == False  and self.pipe21 >24 and self.pipe21 <=73 and self.nahtart =="BW"):
         return "∅ >= 1 in. (25 mm); fillet: all(*1)"
       if(self.plate == False  and self.pipe21 >74 and self.nahtart =="BW"):
         return "∅ >= 2 7/8 in. (73 mm);fillet: all(*1)"
       if(self.plate == False  and self.pipe21 <=24 and self.nahtart =="FW"):
         return "∅ >= "+str(self.pipe21)+" mm"
       if(self.plate == False  and self.pipe21 >24 and self.pipe21 <=73 and self.nahtart =="FW"):
         return "∅ >= 1 in. (25 mm)"
       if(self.plate == False  and self.pipe21 >74 and self.nahtart =="FW"):
         return "∅ >= 2 7/8 in. (73 mm)"
       else:
         if(self.plate == False  and self.pipe21 <=24 and self.nahtart =="BW"):
            return "∅ >= 0"+str(self.pipe2)+" mm; fillet: all(*1)"
     else:
        return " "

    def On_Change_backing(self,backing):
     if(self.backing =="with"):
      return "with"
     else:
      if(self.backing =="without"):
        return "with, without"

    def On_Change_type_used(self,type_used):
     if(self.type_used =="manual"):
      return "manual, semi-automatic"
     else:
      if(self.type_used =="semi-auto"):
        return "semi-auto"

    def On_Change_welding_process(self,welding_process):
     if(self.welding_process =="OFW"):
       return "OFW"
     if(self.welding_process =="OHW"):
       return "OHW"
     if(self.welding_process =="OAW"):
       return "OAW"
     if(self.welding_process =="SMAW"):
       return "SMAW"
     if(self.welding_process =="SAW"):
       return "SAW"
     if(self.welding_process =="FCAW"):
       return "FCAW"
     if(self.welding_process =="GMAW"):
       return "GMAW"
     if(self.welding_process =="GTAW"):
       return "GTAW"
     else:
      if(self.welding_process =="PAW"):
         return "PAW"

    def On_get_title(self,title):
        return "                                                                                           See QW-301, Section IX, ASME Boiler and Pressure Vessel Code"
    def On_Change_plate(self,plate):
      if(self.plate == True):
        return False
      else:
        return True


    def On_Change_coupon(self,test_coupon):
      if(self.test_coupon == True):
        return False
      else:
        return True
    @staticmethod
    def default_title():
        return "welding_performance"
    @staticmethod
    def default_subtitle():
        return  "                                                                                                                              Eignungsprüfung von Schweißern"
    def default_subtitle1():
        return "                                                                                                       See QW-301, Section IX, ASME Boiler and Pressure Vessel Code"
    def default_process1():
      return "GMAW"


#classes for Print Fonction for wpq
# class view
class PrintWPQStart(ModelView):
    'Print START WPQ'
    __name__ = 'party.print_wpq.start'
    zertifikat = fields.Many2One('welding.performance.qualification', 'Zertifikat', required=True)

#Wizard
class PrintWPQ(Wizard):
    'Print WPQ'
    __name__ = 'party.print_wpq'
    start = StateView('party.print_wpq.start',
        'welding_certification.print_wpq_cert_start_view_form', [
            Button('Cancel', 'end', 'tryton-cancel'),
            Button('Drucken', 'print_', 'tryton-print', default=True),
            ])
    print_ = StateReport('welding_certification.party.iso_wpq_report')
    def do_print_(self, action):
        data = {
            'zertifikat': self.start.zertifikat.id,
            }
        return action, data
#Report
class WPQreport(Report):
    __name__ = 'welding_certification.party.iso_wpq_report'


    @classmethod
    def _get_records(cls, ids, model, data):
        Move = Pool().get('welding.performance.qualification')

        clause = [

            ]

    @classmethod
    def get_context(cls, records, data):
        report_context = super(WPQreport, cls).get_context(records, data)

        Zertifikat = Pool().get('welding.performance.qualification')

        zertifikat = Zertifikat(data['zertifikat'])

        report_context['zertifikat'] = zertifikat
        report_context['title'] = zertifikat.title
        report_context['hersteller'] = zertifikat.wps.Herstellere
        report_context['bezeichnung'] = zertifikat.bezeichnung
        report_context['operator_name'] = zertifikat.operator_name
        report_context['identification_no'] = zertifikat.identification_no
        report_context['stamp_no'] = zertifikat.stamp_no
        report_context['wps_beleg_nr'] = zertifikat.wps.Beleg_Nr
        report_context['affichage_test_coupon'] = zertifikat.affichage_test_coupon
        report_context['affichage_production_weld'] = zertifikat.affichage_production_weld
        report_context['specification'] = zertifikat.specification
        report_context['thickness'] = zertifikat.thickness
        report_context['welding_process'] = zertifikat.welding_process
        report_context['welding_process_geltungs'] = zertifikat.welding_process_geltungs
        report_context['type_used'] = zertifikat.type_used
        report_context['type_used_geltungs'] = zertifikat.type_used_geltungs
        report_context['backing'] = zertifikat.backing
        report_context['backing_geltungs'] = zertifikat.backing_geltungs
        report_context['plate_affichage'] = zertifikat.plate_affichage
        report_context['pipe_affichage'] = zertifikat.pipe_affichage
        report_context['pipe21'] = zertifikat.pipe21
        report_context['plate_geltungs'] = zertifikat.plate_geltungs
        report_context['base_metal'] = zertifikat.base_metal.p_no
        report_context['p_num'] = zertifikat.p_number.p_no
        report_context['base_geltungs'] = zertifikat.base_geltungs
        report_context['filler_metal_1'] = zertifikat.filler_metal_1.sfa
        report_context['filler_metal_2'] = zertifikat.filler_metal_2
        report_context['filler_metal_geltungs2'] = zertifikat.filler_metal_geltungs2
        report_context['filler_metal'] = zertifikat.filler_metal
        report_context['filler_metal_geltungs'] = zertifikat.filler_metal_geltungs
        report_context['consumable_insert'] = zertifikat.consumable_insert
        report_context['consumable_insert_gesltungs'] = zertifikat.consumable_insert_gesltungs
        report_context['filler_mettal_product'] = zertifikat.filler_mettal_product
        report_context['filler_mettal_product_gel'] = zertifikat.filler_mettal_product_gel
        report_context['deposit'] = zertifikat.deposit
        report_context['deposit_geltungs'] = zertifikat.deposit_geltungs
        report_context['process1'] = zertifikat.process1
        report_context['layer_min1'] = zertifikat.affichage_layer_min1
        report_context['layer_min3'] = zertifikat.affichage_layer_min3
        report_context['process2'] = zertifikat.process2
        report_context['layer_min2'] = zertifikat.affichage_layer_min2
        report_context['layer_min4'] = zertifikat.affichage_layer_min4
        report_context['process1_val'] = zertifikat.process1_val
        report_context['process2_val'] = zertifikat.process2_val
        report_context['position'] = zertifikat.position
        report_context['groove100'] = zertifikat.groove1
        report_context['groove2'] = zertifikat.groove2
        report_context['fillet1'] = zertifikat.fillet1
        report_context['vertical_progression'] = zertifikat.vertical_progression
        report_context['vertical_progression_gel'] = zertifikat.vertical_progression_gel
        report_context['type_fuelgaz'] = zertifikat.type_fuelgaz
        report_context['inert_gaz_gel'] = zertifikat.inert_gaz_gel
        report_context['inert_gaz'] = zertifikat.inert_gaz
        report_context['transfert_mode_gel'] = zertifikat.transfert_mode_gel
        report_context['transfert_mode'] = zertifikat.transfert_mode
        report_context['current_type'] = zertifikat.current_type
        report_context['current_type_gel'] = zertifikat.current_type_gel
        report_context['visual_examination'] = zertifikat.visual_examination
        report_context['affichage_transverse_face'] = zertifikat.affichage_transverse_face
        report_context['affichage_longitudinal_bends'] = zertifikat.affichage_longitudinal_bends
        report_context['affichage_side_bends'] = zertifikat.affichage_side_bends
        report_context['affichage_pipe_bends'] = zertifikat.affichage_pipe_bends
        report_context['affichage_plate_bends'] = zertifikat.affichage_plate_bends
        report_context['affichage_pipe_specimen'] = zertifikat.affichage_pipe_specimen
        report_context['affichage_plate_specimen'] = zertifikat.affichage_plate_specimen
        report_context['alternativ_volumetric'] = zertifikat.alternativ_volumetric
        report_context['affichage_r_t'] = zertifikat.affichage_r_t
        report_context['affichage_u_t'] = zertifikat.affichage_u_t
        report_context['Fillet_welt'] = zertifikat.Fillet_welt
        report_context['affichage_fillet_weld_plate'] = zertifikat.affichage_fillet_weld_plate
        report_context['affichage_fillet_weld_pipe'] = zertifikat.affichage_fillet_weld_pipe
        report_context['macro_exam'] = zertifikat.macro_exam
        report_context['fillet_size'] = zertifikat.fillet_size
        report_context['convacity'] = zertifikat.convacity
        report_context['other_test'] = zertifikat.other_test
        report_context['film_evaluated'] = zertifikat.film_evaluated
        report_context['company'] = zertifikat.company
        report_context['mecanical_test'] = zertifikat.mecanical_test
        report_context['labo_no'] = zertifikat.labo_no
        report_context['supervised_by'] = zertifikat.supervised_by
        report_context['organization'] = zertifikat.organization
        report_context['date'] = zertifikat.date
        report_context['certified_by'] = zertifikat.certified_by

        index = len (zertifikat.Tab_res)
        tab_type1=[]
        tab_type2=[]
        tab_type3=[]
        tab_res1=[]
        tab_res2=[]
        tab_res3=[]
        for i in range(0,index):
          tab_type1.append(zertifikat.Tab_res[i].type)
          tab_type2.append(zertifikat.Tab_res[i].type1)
          tab_type3.append(zertifikat.Tab_res[i].type2)
          tab_res1.append(zertifikat.Tab_res[i].res)
          tab_res2.append(zertifikat.Tab_res[i].res1)
          tab_res3.append(zertifikat.Tab_res[i].res2)
        if(index == 1):
          report_context['type1_0'] = tab_type1[0]
          report_context['type1_1'] = " "
          report_context['res1_0'] = tab_res1[0]
          report_context['res1_1'] = " "
          report_context['type2_0'] = tab_type2[0]
          report_context['type2_1'] = " "
          report_context['res2_0'] = tab_res2[0]
          report_context['res2_1'] = " "
          report_context['type3_0'] = tab_type3[0]
          report_context['type3_1'] = " "
          report_context['res3_0'] = tab_res3[0]
          report_context['res3_1'] = " "
        else:
          if(index == 2):
            report_context['type1_0'] = tab_type1[0]
            report_context['type1_1'] = tab_type1[1]
            report_context['res1_0'] = tab_res1[0]
            report_context['res1_1'] = tab_res1[1]
            report_context['type2_0'] = tab_type2[0]
            report_context['type2_1'] = tab_type2[1]
            report_context['res2_0'] = tab_res2[0]
            report_context['res2_1'] = tab_res2[1]
            report_context['type3_0'] = tab_type3[0]
            report_context['type3_1'] = tab_type3[1]
            report_context['res3_0'] = tab_res3[0]
            report_context['res3_1'] = tab_res3[1]

        return report_context


# ZfP_Test_Personal class
class zfptp(DeactivableMixin, ModelView, ModelSQL, MultiValueMixin):
    'Zfp Test Personal'
    __name__ = 'party.zfp.testpersonal'
    bezeichnung = fields.Function(fields.Char("Bezeichnung(en)"),"On_Change_Qualifizierungs_stufe_2")
    space = fields.Char("                                                                                                                                                                                       ")
    prufbescheinigung = fields.Char("Prüfbescheinigung Nr.")
    weitere_beleg = fields.Char("Weitere Beleg-Nr.")
    besonderheiten = fields.Char("Einschränkungen oder Besonderheiten")
    prufer = fields.Many2One('party.party', 'Name des Prüfers')
    title = fields.Function(fields.Char(" "),"On_Change_bezeichnung")
    image = fields.Binary("Bild")
    leg = fields.Function(fields.Char("Legitimation"),"On_Change_prufer")
    art_leg = fields.Function(fields.Char("Art der Legitimation"),"On_Change_prufer1")
    geburtsdatum_ort = fields.Function(fields.Char("Geburtsdatum und ort"),"On_Change_prufer2")
    arbeitgeber = fields.Function(fields.Char("Arbeitgeber"),"On_Change_prufer3")
    pruf_norm = fields.Selection([
        ('DIN EN ISO 9712:2012-12', 'DIN EN ISO 9712:2012-12 | Qualifizierung und Zertifizierung von Personal der zerstörungsfreien Prüfung'),
        ('DIN EN 4179:2017-03', 'DIN EN 4179:2017-03 | Luft-und Raumfahrt-Qualifikation und Zulassung des Personals für ZfP'),
    ], 'Vorschrift/Prüfnorm', readonly = False,
        )
    #Qualifizierungs_stufe = fields.Selection([
     #   ('Stufe1', 'Stufe 1 | Schallemissionsprüfung Stufe 1 (AT) | AT 1 Q'),
     #   ('Stufe2', 'Stufe 2 | Schallemissionsprüfung Stufe 2 (AT) | AT 2 Q'),
     #   ('Stufe3', 'Stufe 3 | Schallemissionsprüfung Stufe 3 (AT) | AT 3 Q'),
  #  ], 'Qualifizierungsstufe', readonly = False,
   #     )
    Qualifizierungs_stufe2 = fields.Selection('on_change_verfahren','Qualifizierungsstufe', readonly = False,)
    zertifikat_art = fields.Selection([
        ('Bescheinigung', 'Bescheinigung'),
        ('Teilnahmebescheinigung', 'Teilnahmebescheinigung'),
        ('Prüfungsbescheinigung', 'Prüfungsbescheinigung'),
        ('Nachweis der Prüferqualifikation', 'Nachweis der Prüferqualifikation'),
        ('Qualifikationszeugnis', 'Qualifikationszeugnis'),
        ('Prüfungszeugnis', 'Prüfungszeugnis'),
        ('Prüfungszeugnis der DGZfP nach EN 473', 'Prüfungszeugnis der DGZfP nach EN 473'),
        ('Prüfungszeugnis der DGZfP nach EN ISO 9712', 'Prüfungszeugnis der DGZfP nach EN ISO 9712'),
        ('ZfP-Qualifikationsprüfung', 'ZfP-Qualifikationsprüfung'),
        ('Zertifikat der DGZfP nach EN 473', 'Zertifikat der DGZfP nach EN 473'),
        ('Zertifikat der DGZfP nach EN 9712', 'Zertifikat der DGZfP nach EN 9712'),
    ], 'zertifikat_art', readonly = False,
        )

    weitere_bemerkungen = fields.Selection([
        ('Test3Zeilen', 'Test 3 Zeilen'),
        ('TÜV-Abnahme', 'TÜV-Abnahme'),
        ('Löschen', 'Löschen'),
    ], 'Weitere Bemerkungen', readonly = False,
        )
    Bemerkungen=fields.Function(fields.Text(" "),"On_Change_Weitere")
    datum_prufung = fields.Date("Datum der Prüfung")
    gultigkeit_bis = fields.Function(fields.Date("Gültigkeitsdauer bis"),"On_Change_datum_prufung")
    gultigkeit_dauer = fields.Selection([
        ('1 jahr', 'verkürzte Dauer(1 Jahr)'),
        ('2 jahre', 'Standard (2 Jahre)'),
        ('3 jahre', '3 Jahre'),
        ('4 jahre', '4 Jahre'),
        ('5 jahre', 'Zertifikat ZfP(5 Jahre)'),
    ], 'Gültigkeitdauer', readonly = False,
        )

    prufer_prufstelle = fields.Selection([
        ('DGZfP', 'DGZfP-Ausbildungszentrum Wittenberge'),
        ('Harrison', 'Harrison Mechanical Corporation'),
        ('MAN-Technologie', 'MAN-Technologie, Oberpfaffenhofen, Abtlg.WOP'),
    ], 'Zertifizierungs-/Prüfstelle für ZfP-Personal', readonly = False,
        )

    unterschrift = fields.Selection([
        ('Dipl.Ing. Prüfer', 'Dipl.Ing. Prüfer'),
        ('Dipl.Ing. Schulz', 'Dipl.Ing. Schulz'),
        ('Dipl.Ing. Tester', 'Dipl.Ing. Tester'),
        ('Dipl.Ing. Zertifizierer', 'Dipl.Ing. Zertifizierer'),
    ], 'Prüfungsbeauftragter', readonly = False,
        )

    formular = fields.Selection([
        ('PQ', 'PQ | Zfp (EN ISO 9712) Prüfpersonal'),
    ], 'Formular', readonly = False,
        )
    next_termin = fields.Date("nächster Termin")
    ruhende_pruf = fields.Boolean("Ruhende Prüfung?")
    pruf_archiv = fields.Boolean("Prüfung archivieren?")


    datum_ausgabe = fields.Date("Datum der Ausgabe")

    ort = fields.Function(fields.Char("Ort"),"On_Change_prufer_prufstelle")

    industriesektor = fields.Selection([
        ('6', '6 | EN 473 : Metallerzeugung und Herstellung'),
        ('7', '7 | EN 473 : Dienstleistung an Ausrüstungen, Anlagen und Bauwerken'),
        ('8', '8 | EN 473 : Luft-und Raumfaht'),
        ('9', '9 | EN 473 : Eisenbahn-Instandhaltung'),
        ('Im', 'Im | Herstellung'),
        ('Is', 'Is | Dienstleistungsprüfung bei Fertigung und Instandhaltung'),
        ('Ir', 'Ir | Eisenbahn-Instandhaltung'),
        ('la', 'la | Luft-und Raumfahrt'),
    ], 'Industriesektor', readonly = False,
        )

    industriesektor_1 = fields.Function(fields.Char(" "),"On_Change_industriesektor")
    produkt_sector = fields.Selection([
        ('c', 'c | EN 473 : Gussstücke'),
        ('f', 'f | EN 473 : Schmiedestücke'),
        ('w', 'w | EN 473 : geschweißte Produkte'),
        ('t', 't | EN 473 : Rohre'),
        ('wp', 'wp | EN 473 : Walzerzeugnisse'),
        ('p', 'p | EN 473 : Verbundwerkstoffe'),
        ('Pc', 'Pc | Gussstücke'),
        ('Pf', 'Pf | Schmiedestücke'),
        ('Pw', 'Pw | geschweißte Produkte(eingeschlossen Lötungen)'),
        ('Pt', 'Pt | Rohre und Rohrleitungen(auch Flachprodukte für Rohre)'),
        ('Pwp', 'Pwp | Walzerzeugnisse(außer Schmiedestücke)'),
        ('Pp', 'Pp | Verbundwerkstoffe'),
    ], 'Produktsektor', readonly = False,
        )
    produkt_sector_1 = fields.Function(fields.Char(" "),"On_Change_produkt_sector")
    Qualifizierungs_stufe_1 = fields.Function(fields.Char(" "),"On_Change_Qualifizierungs_stufe")

    pruf_verfahren = fields.Selection([
        ('AT', 'AT | Schallemissionsprüfung'),
        ('DR', 'DR | Digitale Radiologie'),
        ('ET', 'ET | Wirbelstromprüfung'),
        ('HT', 'HT | Mobile Härteprüfung'),
        ('LT', 'LT | Dichtheitsprüfung/Lecksuche'),
        ('MT', 'MT | Magnetpulverprüfung'),
        ('PT', 'PT | Eindringprüfung'),
        ('RI', 'RI | Filmauswertung'),
        ('RT', 'RT | Durchstrahlungsprüfung'),
        ('RT D', 'RT D | Digitaler Filmersatz'),
        ('RT F', 'RT F | Durchstrahlungsprüfung'),
        ('RT S', 'RT S | Digitale Radioskopie'),
        ('ST', 'ST | Dehnungsmessstreifenprüfung'),
        ('TT', 'TT | Infrarotthermografieprüfung'),
        ('UT', 'UT | Ultraschallprüfung'),
        ('UT PA', 'UT PA | Ultraschallprüfung PA'),
        ('UT TOFD', 'UT TOFD| Ultraschallprüfung TOFD'),
        ('VT', 'VT | Sichtprüfung'),
    ], 'Prüfverfahren', readonly = False,
        )
    verfahren_1 = fields.Function(fields.Char(" "),"On_Change_pruf_verfahren")
    val1 = fields.Function(fields.Char(" "),"On_Change_produkt_sector1")
    produktsektor2 = fields.Char(" ")
    produktsektor3 = fields.Char(" ")

    industriesektor2 = fields.Char(" ")
    industriesektor3 = fields.Char(" ")

    @classmethod
    def __setup__(cls):
      super(zfptp, cls).__setup__()
      cls._buttons.update({
          'Actualiser': {},
          'Actualiser2': {},
          })

    @classmethod
    @ModelView.button
    def Actualiser(cls, zfptp):
        for norme in zfptp:
             val = norme.produkt_sector
             if(val == "c"):
               val3 = "Gussstücke (c)"
             if(val == "f"):
               val3 = "Schmiedestücke (f)"
             if(val == "w"):
               val3 = "geschweißte Produkte (w)"
             if(val == "t"):
               val3 = "Rohre (t)"
             if(val == "wp"):
               val3 = "Walzerzeugnisse (wp)"
             if(val == "p"):
               val3 = "Verbundwerkstoffe (p)"
             if(val == "Pc"):
               val3 = "Gussstücke (Pc)"
             if(val == "Pf"):
               val3 = "Schmiedestücke (Pf)"
             if(val == "Pw"):
               val3 = "geschweißte Produkte (Pw)"
             if(val == "Pt"):
               val3 = "Rohre und Rohrleitungen (Pt)"
             if(val == "Pwp"):
               val3 = "Walzerzeugnisse (Pwp)"
             else:
               if(val == "Pp"):
                  val3 = "Verbundwerkstoffe (Pp)"
             val2 = norme.produktsektor2
             val31 = norme.produktsektor3

             if(val31 == " "):
               val_res1 = val3
             else:
               val_res1 = str(val31)+ ","+str(val3)

             if(val2 == " "):
               val_res = val
             else:
               val_res = val2 + ","+val
             cls.write(zfptp,{
                 'produktsektor2': val_res,
                 'produktsektor3': val_res1,
                })
    @classmethod
    @ModelView.button
    def Actualiser2(cls, zfptp):
        for norme in zfptp:
             val = norme.industriesektor
             if(val == "6"):
               val3="EN 473 : Metallerzeugung und Herstellung (6)"
             if(val == "8"):
               val3="Luft-und Raumfaht (8)"
             if(val == "9"):
               val3="EN 473 : Eisenbahn-Instandhaltung (9)"
             if(val == "7"):
               val3="EN 473 : Dienstleistung an Ausrüstungen, Anlagen und Bauwerken (7)"
             if(val == "Im"):
               val3="Herstellung (Im)"
             if(val == "Is"):
               val3="Dienstleistungsprüfung bei Fertigung und Instandhaltung (Is)"
             if(val == "Ir"):
               val3="Eisenbahn-Instandhaltung (Ir)"
             else:
                if(val == "la"):
                  val3 = "Luft-und Raumfahrt (la)"
             val2 = norme.industriesektor2
             val31 = norme.industriesektor3
             if(val31 == " "):
               val_res1 = val3
             else:
               val_res1 = str(val31)+ ","+str(val3)

             if(val2 == " "):
               val_res = val
             else:
               val_res = val2 + ","+val
             cls.write(zfptp,{
                 'industriesektor2': val_res,
                 'industriesektor3': val_res1,
                })


    @staticmethod
    def default_produktsektor2():
       return " "
    @staticmethod
    def default_produktsektor3():
       return " "


    @staticmethod
    def default_industriesektor2():
       return " "

    @staticmethod
    def default_industriesektor3():
       return " "

    @fields.depends('Qualifizierungs_stufe2', 'pruf_verfahren')
    def on_change_verfahren(self):
        tabb=[]
        if(self.pruf_verfahren == "AT"):
          tabb.append(('Stufe1', 'Stufe 1 | Schallemissionsprüfung Stufe 1 (AT) | AT 1 Q'))
          tabb.append(('Stufe2', 'Stufe 2 | Schallemissionsprüfung Stufe 2 (AT) | AT 2 Q'))
          tabb.append(('Stufe3', 'Stufe 3 | Schallemissionsprüfung Stufe 3 (AT) | AT 3 Q'))
          return tabb
        if(self.pruf_verfahren == "DR"):
          tabb.append(('Stufe1', 'Stufe 1 | Digitale Radiologie Stufe 1 (DR) | DR 1 Q'))
          tabb.append(('Stufe2', 'Stufe 2 | Digitale Radiologie Stufe 2 (DR) | DR 2 Q'))
          return tabb
        if(self.pruf_verfahren == "ET"):
          tabb.append(('Stufe1', 'Stufe 1 | Wirbelstromprüfung Stufe 1 (ET) | ET 1 Q'))
          tabb.append(('Stufe2', 'Stufe 2 | Wirbelstromprüfung Stufe 2 (ET) | ET 2 Q'))
          tabb.append(('Stufe3', 'Stufe 3 | Wirbelstromprüfung Stufe 3 (ET) | ET 3 Q'))
          return tabb
        if(self.pruf_verfahren == "HT"):
          tabb.append(('Grundkurs1', 'Grundkurs | Mobile Härteprüfung Grundkurs (HT) | HT Q'))
          tabb.append(('Aufbaukurs1', 'Aufbaukurs | Mobile Härteprüfung Aufbaukurs (HT A) | HT A Q'))
          return tabb
        if(self.pruf_verfahren == "LT"):
          tabb.append(('Stufe1', 'Stufe 1 | Dichtheitsprüfung/Lecksuche Stufe 1 (LT) | LT 1 Q'))
          tabb.append(('Stufe2', 'Stufe 2 | Dichtheitsprüfung/Lecksuche Stufe 2 (LT) | LT 2 Q'))
          tabb.append(('Stufe3', 'Stufe 3 | Dichtheitsprüfung/Lecksuche Stufe 3 (LT) | LT 3 Q'))
          return tabb
        if(self.pruf_verfahren == "MT"):
          tabb.append(('Stufe1', 'Stufe 1 | Magnetpulverprüfung Stufe 1 (MT) | MT 1 Q'))
          tabb.append(('Stufe2', 'Stufe 2 | Magnetpulverprüfung Stufe 2 (MT) | MT 2 Q'))
          tabb.append(('Stufe3', 'Stufe 3 | Magnetpulverprüfung Stufe 3 (MT) | MT 3 Q'))
          return tabb
        if(self.pruf_verfahren == "PT"):
          tabb.append(('Stufe1', 'Stufe 1 | Eindringprüfung Stufe 1 (PT) | PT 1 Q'))
          tabb.append(('Stufe2', 'Stufe 2 | Eindringprüfung Stufe 2 (PT) | PT 2 Q'))
          tabb.append(('Stufe3', 'Stufe 3 | Eindringprüfung Stufe 3 (PT) | PT 3 Q'))
          return tabb
        if(self.pruf_verfahren == "RI"):
          tabb.append(('Stufe2', 'Stufe 2 | Filmauswertung von Schweißnahtaufnahmen (RI) | RI 2 Q'))
          return tabb
        if(self.pruf_verfahren == "RT"):
          tabb.append(('Stufe1', 'Stufe 1 | Durchstrahlungsprüfung Stufe 1 (RT) | RT 1 Q'))
          tabb.append(('Stufe2', 'Stufe 2 | Durchstrahlungsprüfung Stufe 2 (RT) | RT 2 Q'))
          tabb.append(('Stufe3', 'Stufe 3 | Durchstrahlungsprüfung Stufe 3 (RT) | RT 3 Q'))
          return tabb
        if(self.pruf_verfahren == "RT D"):
          tabb.append(('Stufe1', 'Stufe 1 | Durchstrahlungsprüfung Stufe 1 (RT D) | RT D 1 Q'))
          tabb.append(('Stufe2', 'Stufe 2 | Durchstrahlungsprüfung Stufe 2 (RT D) | RT D 2 Q'))
          tabb.append(('Stufe3', 'Stufe 3 | Durchstrahlungsprüfung Stufe 3 (RT) | RT 3 Q'))
          return tabb
        if(self.pruf_verfahren == "RT F"):
          tabb.append(('Stufe1', 'Stufe 1 | Durchstrahlungsprüfung Stufe 1 (RT F) | RT F 1 Q'))
          tabb.append(('Stufe2', 'Stufe 2 | Durchstrahlungsprüfung Stufe 2 (RT F) | RT F 2 Q'))
          tabb.append(('Stufe3', 'Stufe 3 | Durchstrahlungsprüfung Stufe 3 (RT) | RT 3 Q'))
          return tabb
        if(self.pruf_verfahren == "RT S"):
          tabb.append(('Stufe1', 'Stufe 1 | Durchstrahlungsprüfung Stufe 1 (RT S) | RT S 1 Q'))
          tabb.append(('Stufe2', 'Stufe 2 | Durchstrahlungsprüfung Stufe 2 (RT S) | RT S 2 Q'))
          tabb.append(('Stufe3', 'Stufe 3 | Durchstrahlungsprüfung Stufe 3 (RT) | RT 3 Q'))
          return tabb
        if(self.pruf_verfahren == "ST"):
          tabb.append(('Stufe1', 'Stufe 1 | Dehnungsmessstreifenprüfung Stufe 1 (ST) | ST 1 Q'))
          tabb.append(('Stufe2', 'Stufe 2 | Durchstrahlungsprüfung Stufe 2 (ST) | ST 1 Q'))
          return tabb
        if(self.pruf_verfahren == "TT"):
          tabb.append(('Stufe1', 'Stufe 1 | Infrarotthermografieprüfung Stufe 1 (TT) | TT 1 Q'))
          tabb.append(('Stufe2', 'Stufe 2 | Infrarotthermografieprüfung Stufe 2 (TT) | TT 2 Q'))
          tabb.append(('Stufe3', 'Stufe 3 | Infrarotthermografieprüfung Stufe 3 (TT) | TT 3 Q'))
          return tabb
        if(self.pruf_verfahren == "UT"):
          tabb.append(('Stufe1', 'Stufe 1 | Ultraschallprüfung Stufe 1 (UT) | UT 1 Q'))
          tabb.append(('Stufe2', 'Stufe 2 | Ultraschallprüfung Stufe 2 (UT) | UT 2 Q'))
          tabb.append(('Stufe3', 'Stufe 3 | Ultraschallprüfung Stufe 3 (UT) | UT 3 Q'))
          return tabb
        if(self.pruf_verfahren == "UT PA"):
          tabb.append(('Stufe2', 'Stufe 2 | Ultraschallprüfung PA Stufe 2 (UT PA) | UT 2 Q PA'))
          return tabb
        if(self.pruf_verfahren == "UT TOFD"):
          tabb.append(('Stufe2', 'Stufe 2 | Ultraschallprüfung TOFD Stufe 2 (UT TOFD) | UT 2 Q TOFD'))
          return tabb
        else:
          if(self.pruf_verfahren == "VT"):
            tabb.append(('Stufe1', 'Stufe 1 | Sichtprüfung Stufe 1 (VT) | VT 1 Q'))
            tabb.append(('Stufe2', 'Stufe 2 | Sichtprüfung Stufe 2 (VT) | VT 2 Q'))
            tabb.append(('Stufe3', 'Stufe 3 | Sichtprüfung Stufe 3 (VT) | VT 3 Q'))
            return tabb



    def On_Change_bezeichnung(self,prufer):
       return str(self.prufer.name) + ","+str(self.bezeichnung)

    def On_Change_Qualifizierungs_stufe_2(self,Qualifizierungs_stufe2):
      if(self.Qualifizierungs_stufe2 =="Stufe1" and self.pruf_verfahren == "DR"):
         return "Digitale Radiologie Stufe 1(DR)"
      if(self.Qualifizierungs_stufe2 =="Stufe1" and self.pruf_verfahren == "AT"):
         return "Schallemissionsprüfung Stufe 1(AT)"
      if(self.Qualifizierungs_stufe2 =="Stufe2" and self.pruf_verfahren == "AT"):
         return "Schallemissionsprüfung Stufe 2(AT)"
      if(self.Qualifizierungs_stufe2 =="Stufe3" and self.pruf_verfahren == "AT"):
         return "Schallemissionsprüfung Stufe 3(AT)"
      if(self.Qualifizierungs_stufe2 =="Stufe1" and self.pruf_verfahren == "ET"):
         return "Wirbelstromprüfung Stufe 1(ET)"
      if(self.Qualifizierungs_stufe2 =="Stufe2" and self.pruf_verfahren == "ET"):
         return "Wirbelstromprüfung Stufe 2(ET)"
      if(self.Qualifizierungs_stufe2 =="Stufe3" and self.pruf_verfahren == "ET"):
         return "Wirbelstromprüfung Stufe 3(ET)"
      if(self.Qualifizierungs_stufe2 =="Grundkurs1" and self.pruf_verfahren == "HT"):
         return "Mobile Härteprüfung Grundkurs(HT)"
      if(self.Qualifizierungs_stufe2 =="Aufbaukurs1" and self.pruf_verfahren == "HT"):
         return "Mobile Härteprüfung Aufbaukursus(HT A)"
      if(self.Qualifizierungs_stufe2 =="Stufe1" and self.pruf_verfahren == "LT"):
         return "Dichtheitsprüfung/Lecksuche Stufe 1(LT)"
      if(self.Qualifizierungs_stufe2 =="Stufe2" and self.pruf_verfahren == "LT"):
         return "Dichtheitsprüfung/Lecksuche Stufe 2(LT)"
      if(self.Qualifizierungs_stufe2 =="Stufe3" and self.pruf_verfahren == "LT"):
         return "Dichtheitsprüfung/Lecksuche Stufe 3(LT)"
      if(self.Qualifizierungs_stufe2 =="Stufe1" and self.pruf_verfahren == "MT"):
         return "Magnetpulverprüfung Stufe 1(MT)"
      if(self.Qualifizierungs_stufe2 =="Stufe2" and self.pruf_verfahren == "MT"):
         return "Magnetpulverprüfung Stufe 2(MT)"
      if(self.Qualifizierungs_stufe2 =="Stufe3" and self.pruf_verfahren == "MT"):
         return "Magnetpulverprüfung Stufe 3(MT)"
      if(self.Qualifizierungs_stufe2 =="Stufe1" and self.pruf_verfahren == "PT"):
         return "Eindringprüfung Stufe 1(PT)"
      if(self.Qualifizierungs_stufe2 =="Stufe2" and self.pruf_verfahren == "PT"):
         return "Eindringprüfung Stufe 2(PT)"
      if(self.Qualifizierungs_stufe2 =="Stufe3" and self.pruf_verfahren == "PT"):
         return "Eindringprüfung Stufe 3(PT)"
      if(self.pruf_verfahren == "RI"):
         return "Filmauswertung von Schweißnahtaufnahmen(RI)"
      if(self.Qualifizierungs_stufe2 =="Stufe1" and self.pruf_verfahren == "RT"):
         return "Durchstrahlungsprüfung Stufe 1(RT)"
      if(self.Qualifizierungs_stufe2 =="Stufe2" and self.pruf_verfahren == "RT"):
         return "Durchstrahlungsprüfung Stufe 2(RT)"
      if(self.Qualifizierungs_stufe2 =="Stufe3" and self.pruf_verfahren == "RT"):
         return "Durchstrahlungsprüfung Stufe 3(RT)"
      if(self.Qualifizierungs_stufe2 =="Stufe1" and self.pruf_verfahren == "RT D"):
         return "Durchstrahlungsprüfung Stufe 1(RT D)"
      if(self.Qualifizierungs_stufe2 =="Stufe2" and self.pruf_verfahren == "RT D"):
         return "Durchstrahlungsprüfung Stufe 2(RT D)"
      if(self.Qualifizierungs_stufe2 =="Stufe3" and self.pruf_verfahren == "RT D"):
         return "Durchstrahlungsprüfung Stufe 3(RT)"
      if(self.Qualifizierungs_stufe2 =="Stufe1" and self.pruf_verfahren == "RT F"):
         return "Durchstrahlungsprüfung Stufe 1(RT F)"
      if(self.Qualifizierungs_stufe2 =="Stufe2" and self.pruf_verfahren == "RT F"):
         return "Durchstrahlungsprüfung Stufe 2(RT F)"
      if(self.Qualifizierungs_stufe2 =="Stufe3" and self.pruf_verfahren == "RT F"):
         return "Durchstrahlungsprüfung Stufe 3(RT)"
      if(self.Qualifizierungs_stufe2 =="Stufe1" and self.pruf_verfahren == "RT S"):
         return "Durchstrahlungsprüfung Stufe 1(RT S)"
      if(self.Qualifizierungs_stufe2 =="Stufe2" and self.pruf_verfahren == "RT S"):
         return "Durchstrahlungsprüfung Stufe 2(RT S)"
      if(self.Qualifizierungs_stufe2 =="Stufe3" and self.pruf_verfahren == "RT S"):
         return "Durchstrahlungsprüfung Stufe 3(RT)"
      if(self.Qualifizierungs_stufe2 =="Stufe2" and self.pruf_verfahren == "ST"):
         return "Dehnungsmessstreifenprüfung Stufe 2(ST)"
      if(self.Qualifizierungs_stufe2 =="Stufe1" and self.pruf_verfahren == "ST"):
         return "Dehnungsmessstreifenprüfung Stufe 1(ST)"
      if(self.Qualifizierungs_stufe2 =="Stufe1" and self.pruf_verfahren == "TT"):
         return "Infrarotthermografieprüfung Stufe 1(TT)"
      if(self.Qualifizierungs_stufe2 =="Stufe2" and self.pruf_verfahren == "TT"):
         return "Infrarotthermografieprüfung Stufe 2(TT)"
      if(self.Qualifizierungs_stufe2 =="Stufe3" and self.pruf_verfahren == "TT"):
         return "Infrarotthermografieprüfung Stufe 3(TT)"
      if(self.Qualifizierungs_stufe2 =="Stufe1" and self.pruf_verfahren == "UT"):
         return "Ultraschallprüfung Stufe 1(UT)"
      if(self.Qualifizierungs_stufe2 =="Stufe2" and self.pruf_verfahren == "UT"):
         return "Ultraschallprüfung Stufe 2(UT)"
      if(self.Qualifizierungs_stufe2 =="Stufe3" and self.pruf_verfahren == "UT"):
         return "Ultraschallprüfung Stufe 3(UT)"
      if(self.pruf_verfahren == "UT PA"):
         return "Ultraschallprüfung Stufe 2(UT PA)"
      if(self.pruf_verfahren == "UT TOFD"):
         return "Ultraschallprüfung TOFD Stufe 2(UT TOFD)"
      if(self.Qualifizierungs_stufe2 =="Stufe1" and self.pruf_verfahren == "VT"):
         return "Sichtprüfung Stufe 1(VT)"
      if(self.Qualifizierungs_stufe2 =="Stufe2" and self.pruf_verfahren == "VT"):
         return "Sichtprüfung Stufe 2(VT)"
      if(self.Qualifizierungs_stufe2 =="Stufe3" and self.pruf_verfahren == "VT"):
         return "Sichtprüfung Stufe 3(VT)"
      else:
        if(self.Qualifizierungs_stufe2 =="Stufe2" and self.pruf_verfahren == "DR"):
          return "Digitale Radiologie Stufe 2(DR)"

    def On_Change_prufer_prufstelle(self,prufer_prufstelle):
      if(self.prufer_prufstelle =="DGZfP"):
        return "Wittenberge"
      if(self.prufer_prufstelle =="MAN-Technologie"):
        return "Weßling"
      else:
        if(self.prufer_prufstelle =="Harrison"):
          return "New YORK, NY"
    def On_Change_datum_prufung(self,datum_prufung):
      if(self.gultigkeit_dauer =="1 jahr"):
        return self.datum_prufung + datetime.timedelta(days=365)
      if(self.gultigkeit_dauer =="3 jahre"):
        return self.datum_prufung + datetime.timedelta(days=1095)
      if(self.gultigkeit_dauer =="4 jahre"):
        return self.datum_prufung + datetime.timedelta(days=1460)
      if(self.gultigkeit_dauer =="5 jahre"):
        return self.datum_prufung + datetime.timedelta(days=1825)
      else:
         if(self.gultigkeit_dauer =="2 jahre"):
           return self.datum_prufung + datetime.timedelta(days=730)


    def On_Change_Weitere(self,weitere_bemerkungen):
       if(self.weitere_bemerkungen =="Test3Zeilen"):
         return "In WPS Report  können in die Prüfungenbescheinigungen 3 Zeilen Bemerkungen mit jeweils ...\n 90 Zeilen eingetragen werden. In WPS Report können in die Prüfungenbescheinigungen ....\n 3 Zeilen Bemerkungen mit jeweils 90 Zeichen eingetragen werden .............."
       if(self.weitere_bemerkungen =="Löschen"):
         return " "
       else:
         if(self.weitere_bemerkungen =="TÜV-Abnahme"):
            return "Die Prüfung erfolgt im Einvernehmen mit dem Sachverständigen ...\n des TÜV Bayern Hessen Sachsen Südwest e.V. ....\n 3 Zeilen Bemerkungen mit jeweils 90 Zeichen eingetragen werden ........."

    def On_Change_industriesektor(self,industriesektor):
     if(len(tabll1)<=9):
        if(self.industriesektor == "6"):
         tabll1.append("6")
         return tabll1
        if(self.industriesektor == "7"):
         tabll1.append("7")
         return tabll1
        if(self.industriesektor == "8"):
         tabll1.append("8")
         return tabll1
        if(self.industriesektor == "9"):
         tabll1.append("9")
         return tabll1
        if(self.industriesektor == "Im"):
         tabll1.append("Im")
         return tabll1
        if(self.industriesektor == "Is"):
         tabll1.append("Is")
         return tabll1
        if(self.industriesektor == "Ir"):
         tabll1.append("Ir")
         return tabll1
        if(self.industriesektor == "Ia"):
         tabll1.append("Ia")
         return tabll1
     else:
         return tabll1


    def On_Change_produkt_sector1(self,produkt_sector):
     if(self.produkt_sector == "c"):
      return "c"

    def On_Change_produkt_sector(self,produkt_sector):
     if(len(tabll)<=10):
        if(self.produkt_sector == "c"):
         tabll.append("c")
         return tabll
        if(self.produkt_sector == "w"):
         tabll.append("w")
         return tabll
        if(self.produkt_sector == "t"):
         tabll.append("t")
         return tabll
        if(self.produkt_sector == "wp"):
         tabll.append("wp")
         return tabll
        if(self.produkt_sector == "p"):
         tabll.append("p")
         return tabll
        if(self.produkt_sector == "Pc"):
         tabll.append("Pc")
         return tabll
        if(self.produkt_sector == "Pf"):
         tabll.append("Pf")
         return tabll
        if(self.produkt_sector == "Pw"):
         tabll.append("Pw")
         return tabll
        if(self.produkt_sector == "Pt"):
         tabll.append("Pt")
         return tabll
        if(self.produkt_sector == "Pwp"):
         tabll.append("Pwp")
         return tabll
        if(self.produkt_sector == "Pp"):
         tabll.append("Pp")
         return tabll
        if(self.produkt_sector == "löschen"):
         tabll.clear()
         return tabll
        else:
          if(self.produkt_sector == "f"):
            tabll.append("f")
            return tabll
     else:
        return tabll


    def On_Change_Qualifizierungs_stufe(self,Qualifizierungs_stufe2):
      if(self.Qualifizierungs_stufe2 == "Stufe1" and self.pruf_verfahren == "AT"):
         return "AT 1 Q"
      if(self.Qualifizierungs_stufe2 == "Stufe2" and self.pruf_verfahren == "AT"):
         return "AT 2 Q"
      if(self.Qualifizierungs_stufe2 == "Stufe1" and self.pruf_verfahren == "DR"):
         return "DR 1 Q"
      if(self.Qualifizierungs_stufe2 == "Stufe2" and self.pruf_verfahren == "DR"):
         return "DR 2 Q"
      if(self.Qualifizierungs_stufe2 == "Stufe1" and self.pruf_verfahren == "ET"):
         return "ET 1 Q"
      if(self.Qualifizierungs_stufe2 == "Stufe2" and self.pruf_verfahren == "ET"):
         return "ET 2 Q"
      if(self.Qualifizierungs_stufe2 == "Stufe3" and self.pruf_verfahren == "ET"):
         return "ET 3 Q"
      if(self.Qualifizierungs_stufe2 == "Grundkurs1" and  self.pruf_verfahren == "HT"):
         return "HT Q"
      if(self.Qualifizierungs_stufe2 == "Aufbaukurs1" and  self.pruf_verfahren == "HT"):
         return "HT A Q"
      if(self.Qualifizierungs_stufe2 == "Stufe1" and self.pruf_verfahren == "LT"):
        return "LT 1 Q"
      if(self.Qualifizierungs_stufe2 == "Stufe2" and self.pruf_verfahren == "LT"):
        return "LT 2 Q"
      if(self.Qualifizierungs_stufe2 == "Stufe3" and self.pruf_verfahren == "LT"):
        return "LT 3 Q"
      if(self.Qualifizierungs_stufe2 == "Stufe1" and self.pruf_verfahren == "MT"):
        return "MT 1 Q"
      if(self.Qualifizierungs_stufe2 == "Stufe2" and self.pruf_verfahren == "MT"):
        return "MT 2 Q"
      if(self.Qualifizierungs_stufe2 == "Stufe3" and self.pruf_verfahren == "MT"):
        return "MT 3 Q"
      if(self.Qualifizierungs_stufe2 == "Stufe1" and self.pruf_verfahren == "PT"):
        return "PT 1 Q"
      if(self.Qualifizierungs_stufe2 == "Stufe2" and self.pruf_verfahren == "PT"):
        return "PT 2 Q"
      if(self.Qualifizierungs_stufe2 == "Stufe3" and self.pruf_verfahren == "PT"):
        return "PT 3 Q"
      if(self.pruf_verfahren == "RI"):
        return "RI 2 Q"
      if(self.Qualifizierungs_stufe2 == "Stufe1" and self.pruf_verfahren == "RT"):
        return "RT 1 Q"
      if(self.Qualifizierungs_stufe2 == "Stufe2" and self.pruf_verfahren == "RT"):
        return "RT 2 Q"
      if(self.Qualifizierungs_stufe2 == "Stufe3" and self.pruf_verfahren == "RT"):
        return "RT 3 Q"
      if(self.Qualifizierungs_stufe2 == "Stufe1" and self.pruf_verfahren == "RT D"):
        return "RT D 1 Q"
      if(self.Qualifizierungs_stufe2 == "Stufe2" and self.pruf_verfahren == "RT D"):
        return "RT D 2 Q"
      if(self.Qualifizierungs_stufe2 == "Stufe3" and self.pruf_verfahren == "RT D"):
        return "RT 3 Q"
      if(self.Qualifizierungs_stufe2 == "Stufe1" and self.pruf_verfahren == "RT F"):
        return "RT F 1 Q"
      if(self.Qualifizierungs_stufe2 == "Stufe2" and self.pruf_verfahren == "RT F"):
        return "RT F 2 Q"
      if(self.Qualifizierungs_stufe2 == "Stufe3" and self.pruf_verfahren == "RT F"):
        return "RT 3 Q"
      if(self.Qualifizierungs_stufe2 == "Stufe1" and self.pruf_verfahren == "RT S"):
        return "RT S 1 Q"
      if(self.Qualifizierungs_stufe2 == "Stufe2" and self.pruf_verfahren == "RT S"):
        return "RT S 2 Q"
      if(self.Qualifizierungs_stufe2 == "Stufe3" and self.pruf_verfahren == "RT S"):
        return "RT 3 Q"
      if(self.Qualifizierungs_stufe2 == "Stufe1" and self.pruf_verfahren == "ST"):
        return "ST 1 Q"
      if(self.Qualifizierungs_stufe2 == "Stufe2" and self.pruf_verfahren == "ST"):
        return "ST 1 Q"
      if(self.Qualifizierungs_stufe2 == "Stufe1" and self.pruf_verfahren == "TT"):
        return "TT 1 Q"
      if(self.Qualifizierungs_stufe2 == "Stufe2" and self.pruf_verfahren == "TT"):
        return "TT 2 Q"
      if(self.Qualifizierungs_stufe2 == "Stufe3" and self.pruf_verfahren == "TT"):
        return "TT 3 Q"
      if(self.Qualifizierungs_stufe2 == "Stufe1" and self.pruf_verfahren == "UT"):
        return "UT 1 Q"
      if(self.Qualifizierungs_stufe2 == "Stufe2" and self.pruf_verfahren == "UT"):
        return "UT 2 Q"
      if(self.Qualifizierungs_stufe2 == "Stufe3" and self.pruf_verfahren == "UT"):
        return "UT 3 Q"
      if(self.pruf_verfahren == "UT PA"):
        return "UT 2 Q PA"
      if(self.pruf_verfahren == "UT TOFD"):
        return "UT 2 Q TOFD"
      if(self.Qualifizierungs_stufe2 == "Stufe1" and self.pruf_verfahren == "VT"):
        return "VT 1 Q"
      if(self.Qualifizierungs_stufe2 == "Stufe2" and self.pruf_verfahren == "VT"):
        return "VT 2 Q"
      if(self.Qualifizierungs_stufe2 == "Stufe3" and self.pruf_verfahren == "VT"):
        return "VT 3 Q"
      else:
         if(self.Qualifizierungs_stufe2 == "Stufe3" and self.pruf_verfahren == "AT"):
           return "AT 3 Q"

    def On_Change_pruf_verfahren(self,pruf_verfahren):
          if(self.pruf_verfahren =="AT"):
            return "Schallemissionsprüfung"
          if(self.pruf_verfahren =="ET"):
            return "Wirbelstromprüfung"
          if(self.pruf_verfahren =="HT"):
            return "Mobile Härteprüfung"
          if(self.pruf_verfahren =="LT"):
            return "Dichtheitsprüfung/Lecksuche"
          if(self.pruf_verfahren =="MT"):
            return "Magnetpulverprüfung"
          if(self.pruf_verfahren =="PT"):
            return "Eindringprüfung"
          if(self.pruf_verfahren =="RI"):
            return "Filmauswertung"
          if(self.pruf_verfahren =="RT"):
            return "Durchstrahlungsprüfung"
          if(self.pruf_verfahren =="RT D"):
            return "Digitaler Filmersatz"
          if(self.pruf_verfahren =="RT F"):
            return "Durchstrahlungsprüfung"
          if(self.pruf_verfahren =="RT S"):
            return "Digitale Radioskopie"
          if(self.pruf_verfahren =="ST"):
            return "Dehnungsmessstreifenprüfung"
          if(self.pruf_verfahren =="TT"):
            return "Infrarotthermografieprüfung"
          if(self.pruf_verfahren =="UT"):
            return "Ultraschallprüfung"
          if(self.pruf_verfahren =="UT TOFD"):
            return "Ultraschallprüfung TOFD"
          if(self.pruf_verfahren =="UT PA"):
            return "Ultraschallprüfung PA"
          if(self.pruf_verfahren =="VT"):
            return "Sichtprüfung"
          else:
            if(self.pruf_verfahren =="DR"):
              return "Digitale Radiologie"


    def On_Change_prufer(self,prufer):
     if(self.prufer is not None):
        return self.prufer.legitimation
     else:
        return " "

    def On_Change_prufer1(self,prufer):
     if(self.prufer is not None):
        return self.prufer.legitimation_type
     else:
        return " "

    def On_Change_prufer2(self,prufer):
     if(self.prufer is not None):
        return str(self.prufer.birthday) + ","+str(self.prufer.country_of_birth.name)
     else:
        return " "

    def On_Change_prufer3(self,prufer):
     if(self.prufer is not None):
        return self.prufer.employer.name
     else:
        return " "

    @staticmethod
    def default_bezeichnung():
      return "ZfP Prüfung EN ISO 9712"


#classes for Print Fonction for ZfP
# class view
class PrintZfPStart(ModelView):
    'Print START ZfP'
    __name__ = 'party.print_zfp.start'
    zertifikat = fields.Many2One('party.zfp.testpersonal', 'Zertifikat', required=True)

#Wizard
class PrintZfP(Wizard):
    'Print ZfP'
    __name__ = 'party.print_zfp'
    start = StateView('party.print_zfp.start',
        'welding_certification.print_zfp_cert_start_view_form', [
            Button('Cancel', 'end', 'tryton-cancel'),
            Button('Drucken', 'print_', 'tryton-print', default=True),
            ])
    print_ = StateReport('welding_certification.party.iso_zfp_report')
    def do_print_(self, action):
        data = {
            'zertifikat': self.start.zertifikat.id,
            }
        return action, data
#Report
class ZfPreport(Report):
    __name__ = 'welding_certification.party.iso_zfp_report'


    @classmethod
    def _get_records(cls, ids, model, data):
        Move = Pool().get('party.zfp.testpersonal')

        clause = [

            ]


    @classmethod
    def get_context(cls, records, data):
        report_context = super(ZfPreport, cls).get_context(records, data)

        Zertifikat = Pool().get('party.zfp.testpersonal')

        zertifikat = Zertifikat(data['zertifikat'])

        report_context['zertifikat'] = zertifikat
        report_context['bezeichnung'] = zertifikat.bezeichnung
       # report_context['company'] = zertifikat.prufer.addresses.street
        #report_context['country'] = zertifikat.prufer.addresses
       # report_context['subdivi'] = zertifikat.prufer.addresses
        report_context['prufer'] = zertifikat.prufer_prufstelle
        report_context['prufer1'] = zertifikat.prufer.name
        report_context['image'] = zertifikat.image
        report_context['document'] = zertifikat.prufbescheinigung
        report_context['geburtsdatum_ort'] = zertifikat.geburtsdatum_ort
        report_context['pruf_norm'] = zertifikat.pruf_norm
        report_context['arbeitgeber'] = zertifikat.arbeitgeber
        report_context['bezeichnung'] = zertifikat.bezeichnung
        report_context['pruf_verfahren'] = zertifikat.pruf_verfahren
        report_context['produktsektor2'] = zertifikat.produktsektor2
        report_context['produktsektor3'] = zertifikat.produktsektor3
        report_context['industriesektor2'] = zertifikat.industriesektor2
        report_context['industriesektor3'] = zertifikat.industriesektor3
        report_context['datum_prufung'] = zertifikat.datum_prufung
        report_context['besonderheiten'] = zertifikat.besonderheiten
        report_context['Bemerkungen'] = zertifikat.Bemerkungen
        chaine=zertifikat.Bemerkungen
        pos1 = chaine.find("...\n")
        res1 = chaine[0:pos1+3]
        pos2 = chaine.find("....\n")
        res2 = chaine[pos1+3:pos2+4]
        res3 = chaine[pos2+4:len(chaine)]
        report_context['Bemerkungen1'] = res1
        report_context['Bemerkungen2'] = res2
        report_context['Bemerkungen3'] = res3
        report_context['ort'] = zertifikat.ort
        report_context['datum_ausgabe'] = zertifikat.datum_ausgabe
        report_context['gultigkeit_bis'] = zertifikat.gultigkeit_bis
        report_context['unterschrift'] = zertifikat.unterschrift
        report_context['zertifikat_art'] = zertifikat.zertifikat_art




        return report_context
# wpqr EN 288-x class
class wpqr3(DeactivableMixin, ModelView, ModelSQL, MultiValueMixin):
    'Party EN 288x'
    __name__ = 'party.en288x'
    hersteller = fields.Char("Hersteller")
    space = fields.Char("                                                                                                                                                                                                                        ")
    schweissverfahren = fields.Char("Schweißverfahrensprüfung des Herstellers")
    prufer1 = fields.Char("Prüfer oder Prüfstelle")
    beleg1 = fields.Function(fields.Char("Beleg-Nr"),"On_change_andere")
    beleg2 = fields.Char("Beleg-Nr")
    anschrift = fields.Char("Anschrift")
    regel = fields.Char("Regel/Prüfnorm")
    datum_schweissen = fields.Date("Datum der Schweißung")
    prufumfang = fields.Char("Prüfumfang")
    pulver = fields.Selection('on_change_schweisprocess1','Schutzgases/Pulver', readonly = False,)
    stromart = fields.Char("Stromart")

    prufer_prufstelle1 = fields.Many2One('welding.pruefstelle', 'Name des prüfers oder der prüfstelle',
            ondelete='CASCADE')

    unterschrift = fields.Selection([
        ('Dipl-Ing. Prüfer', 'Dipl-Ing. Prüfer'),
    ], 'Name, Datum und Unterschrift', readonly = False,
        )

    datum_ausstellung = fields.Date("Datum der Ausstellung")

    vorwarmung = fields.Char("Vorwärmung")
    warmenachbehandlung = fields.Char("Wärmenachbehandlung und/oder Aushärtung")
    sonstige = fields.Text("Sonstige Angaben")
    index = fields.Text("Hiermit wird bestätigt, dass die Prüfungsschweißungen in Übereinstimmung mit den Bedingungen der vorbezeichneten")
    index2 = fields.Text("Regeln bzw. Prüfnorm zufriedenstellend vorbereitet, geschweißt und geprüft wurden.:")
    ort = fields.Function(fields.Char("Ort"),"On_Change_prufer_prufstelle1")

    schweissposition = fields.Selection([
        ('PA', 'PA Wannenposition'),
        ('PB', 'PB Horizontalposition'),
        ('PC', 'PC Querposition'),
        ('PD', 'PD Horizontal-Überkopfposition'),
        ('PE', 'PE Überkopfposition'),
        ('PF', 'PF Steigposition'),
        ('PG', 'PG Fallposition'),
    ], 'Schweißposition', readonly = False,
        )
    schweissposition_gel = fields.Char("Geltungs bereich schweißposition")

    nahtart = fields.Selection([
        ('Stumpfnaht am Blech(P,BW) einseitig mit Schweißbadsicherung (ss,mb)', 'Stumpfnaht am Blech(P,BW) einseitig mit Schweißbadsicherung (ss,mb)'),
        ('Stumpfnaht am Blech (P,BW) einseitig ohne Schweißbadsicherung (ss,nb)', 'Stumpfnaht am Blech (P,BW) einseitig ohne Schweißbadsicherung (ss,nb)'),
        ('Stumpfnaht am Blech (P,BW) beidseitig mit Ausfugen(bs,gg)', 'Stumpfnaht am Blech (P,BW) beidseitig mit Ausfugen(bs,gg)'),
        ('Stumpfnaht am Blech (P,BW) beidseitig ohne Ausfugen(bs,ng)', 'Stumpfnaht am Blech (P,BW) beidseitig ohne Ausfugen(bs,ng)'),
        ('Stumpfnaht am Rohr (T,BW) mit Schweißbadsicherung (ss,mb)', 'Stumpfnaht am Rohr (T,BW) mit Schweißbadsicherung (ss,mb)'),
        ('Stumpfnaht am Rohr (T,BW) ohne Schweißbadsicherung (ss,nb)', 'Stumpfnaht am Rohr (T,BW) ohne Schweißbadsicherung (ss,nb)'),
        ('T-Stumpfstoß, kehlnaht am Blech ohne Fugenvorbereitung (P,FW)', 'T-Stumpfstoß, kehlnaht am Blech ohne Fugenvorbereitung (P,FW)'),
        ('Rohrabzweigung, kehlnaht am Rohr (T,FW)', 'Rohrabzweigung, kehlnaht am Rohr (T,FW)'),
        ('Kehlnaht am Rohr (T,FW)', 'Kehlnaht am Rohr (T,FW)'),
        ('Kehlnaht am Blech (P,FW) einseitig geschweißt (ss)', 'Kehlnaht am Blech (P,FW) einseitig geschweißt (ss)'),
        ('Kehlnaht am Blech (P,FW) beidseitig geschweißt (bs)', 'Kehlnaht am Blech (P,FW) beidseitig geschweißt (bs)'),
    ], 'Nahtart', readonly = False,
        )
    grundwerkstoffe = fields.Many2One('welding.grundwerkstoff_properties', 'Grundwerkstoffe 1',required =True)
    grundwerkstoffe2 = fields.Many2One('welding.grundwerkstoff_properties', 'Grundwerkstoffe 2',required =True)

    grup1 = fields.Function(fields.Char("grup1"),"On_change_grundwerkstoffe")
    grup2 = fields.Function(fields.Char("grup2"),"On_change_grundwerkstoffe2")

    nummer1 = fields.Function(fields.Char("nummer1"),"On_change_grundwerkstoffe3")
    nummer2 = fields.Function(fields.Char("nummer2"),"On_change_grundwerkstoffe4")
    hartegrade = fields.Char("Härtegrad")

    dicke = fields.Integer("Dicke des Grundwerkstoffes (mm)")
    dicke_gel =fields.Function(fields.Char("dicke geltungsbereich"),"On_change_dicke")

    aussendurchmesser = fields.Integer("Außendurchmesser (mm)")
    aussendurchmesser_gel =fields.Function(fields.Char("aussendurchmesser geltungsbereich"),"On_change_aussendurchmesser")

    zusatzwerkstoff = fields.Many2One('welding.szi_data', 'Art des Zusatzwerkstoffes')

    schweißprocess = fields.Selection([
         ('--', '--'),
        ('111  Lichtbogenhandschweißen', '111 Lichtbogenhandschweißen'),
        ('111/121 Wurzel E, Auffüllen mit UP (Stahl)', '111/121 Wurzel E, Auffüllen mit UP (Stahl)'),
        ('111/135 Wurzel E, Auffüllen mit MAG (Stahl)', '111/135 Wurzel E, Auffüllen mit MAG (Stahl)'),
        ('112 Schwerkraft-Lichtbogenschweißen', '112 Schwerkraft-Lichtbogenschweißen'),
        ('114 Metall-Lichtbogenschweißen mit Fülldrahtelektrode ohne Schutzgas', '114 Metall-Lichtbogenschweißen mit Fülldrahtelektrode ohne Schutzgas'),
        ('12 Unterpulverschweißen', '12 Unterpulverschweißen'),
        ('121 Unterpulverschweißen mit Massivdrahtelektrode','121 Unterpulverschweißen mit Massivdrahtelektrode'),
        ('122 Unterpulverschweißen mit Massivbandelektrode', '122 Unterpulverschweißen mit Massivbandelektrode'),
        ('124 Unterpulverschweißen mit Metallpulverzusatz', '124 Unterpulverschweißen mit Metallpulverzusatz'),
        ('125 Unterpulverschweißen mit Fülldrahtelektrode', '125 Unterpulverschweißen mit Fülldrahtelektrode'),
        ('126 Unterpulverschweißen mit Füllbandelektrode', '126 Unterpulverschweißen mit Füllbandelektrode '),
        ('131 Metall-Inertgasschweißen mit Massivdrahtelektrode', '131 Metall-Inertgasschweißen mit Massivdrahtelektrode'),
        ('132 Metall-Inertgasschweißen mit schweißpulvergefüllter Drahtelektrode', '132 Metall-Inertgasschweißen mit schweißpulvergefüllter Drahtelektrode'),
        ('133 Metall-Inertgasschweißen mit metallpulvergefüllter Drahtelektrode', '133 Metall-Inertgasschweißen mit metallpulvergefüllter Drahtelektrode'),
        ('135 Metall-Aktivgasschweißen mit Massivdrahtelektrode', '135 Metall-Aktivgasschweißen mit Massivdrahtelektrode'),
        ('135/111 Wurzel MAG, Auffüllen mit  E (Stahl)', '135/111 Wurzel MAG, Auffüllen mit  E (Stahl)'),
        ('135/121 Wurzel MAG, Auffüllen mit  UP (Stahl)', '135/121 Wurzel MAG, Auffüllen mit  UP (Stahl)'),
        ('136 Metall-Aktivgasschweißen mit schweißpulvergefüllter Drahtelektrode', '136 Metall-Aktivgasschweißen mit schweißpulvergefüllter Drahtelektrode'),
        ('136/121 Wurzel MAG, Auffüllen mit  UP (Stahl)', '136/121 Wurzel MAG, Auffüllen mit  UP (Stahl)'),
        ('138 Metall-Aktivgasschweißen mit metallpulvergefüllter Drahtelektrode', '138 Metall-Aktivgasschweißen mit metallpulvergefüllter Drahtelektrode'),
        ('141 Wolfram-Inertgasschweißen mit Massivdraht- oder Massivstabzusatz', '141 Wolfram-Inertgasschweißen mit Massivdraht- oder Massivstabzusatz'),
        ('141/111 Wurzel WIG, Auffüllen mit  E (Stahl, Cu, Ni)', '141/111  Wurzel WIG, Auffüllen mit  E (Stahl, Cu, Ni)'),
        ('141/121 Wurzel WIG, Auffüllen mit  UP (Stahl, Ni)', '141/121 Wurzel WIG, Auffüllen mit  UP (Stahl, Ni)'),
        ('141/131 Wurzel WIG, Auffüllen mit  MIG (Al, Cu, Ni, Ti)', '141/131 Wurzel WIG, Auffüllen mit  MIG (Al, Cu, Ni, Ti)'),
        ('141/135 Wurzel WIG, Auffüllen mit  MAG (Stahl, Ni)', '141/135 Wurzel WIG, Auffüllen mit  MAG (Stahl, Ni)'),
        ('141/136 Wurzel WIG, Auffüllen mit  MAG (Stahl)', '141/136 Wurzel WIG, Auffüllen mit  MAG (Stahl)'),
        ('142 Wolfram-Inertgasschweißen ohne Schweißzusatz', '142 Wolfram-Inertgasschweißen ohne Schweißzusatz'),
        ('143 Wolfram-Inertgasschweißen mit Fülldraht- oder Füllstabzusatz', '143 Wolfram-Inertgasschweißen mit Fülldraht- oder Füllstabzusatz'),
        ('145 WIG-Schweißen mit reduzierenden Gasanteilen und Massivzusatz(Draht/Stab)', '145 WIG-Schweißen mit reduzierenden Gasanteilen und Massivzusatz(Draht/Stab)'),
        ('146 WIG-Schweißen mit reduzierenden Gasanteilen und Füllzusatz(Draht/Stab)', '146 WIG-Schweißen mit reduzierenden Gasanteilen und Füllzusatz(Draht/Stab)'),
        ('147 Wolfram-Schutzgasschweißen mit aktiven Gesanteilen im inerten Schutzgas', '147 Wolfram-Schutzgasschweißen mit aktiven Gesanteilen im inerten Schutzgas'),
        ('15 Plasmaschweißen', '15 Plasmaschweißen'),
        ('151 Plasma-Metall-Inertgasschweißen', '151 Plasma-Metall-Inertgasschweißen'),
        ('152 Pulver-Plasmalichtbogenschweißen', '152 Pulver-Plasmalichtbogenschweißen'),
        ('311 Gasschweißen mit Sauerstoff-Acetylen-Flamme', '311 Gasschweißen mit Sauerstoff-Acetylen-Flamme'),
        ('312 Gasschweißen mit Sauerstoff-Propan-Flamme', '312 Gasschweißen mit Sauerstoff-Propan-Flamme'),
        ('313 asschweißen mit Sauerstoff-Wasserstoff-Flamme', '313 Gasschweißen mit Sauerstoff-Wasserstoff-Flamme'),
    ], 'Schweißprozess(e)', readonly = False,
        )
    schweiss_gel = fields.Function(fields.Char("Beleg-Nr"),"On_change_schweissprocess")


    def On_Change_prufer_prufstelle1(self,prufer_prufstelle1):
        return self.prufer_prufstelle1.ort

    @fields.depends('pulver', 'schweißprocess')
    def on_change_schweisprocess1(self):
        tab=[]
        if(self.schweißprocess == "111  Lichtbogenhandschweißen" or self.schweißprocess == "112 Schwerkraft-Lichtbogenschweißen" or self.schweißprocess == "114 Metall-Lichtbogenschweißen mit Fülldrahtelektrode ohne Schutzgas" or self.schweißprocess == "12 Unterpulverschweißen" or self.schweißprocess == "121 Unterpulverschweißen mit Massivdrahtelektrode" or self.schweißprocess == "122 Unterpulverschweißen mit Massivbandelektrode" or self.schweißprocess =="124 Unterpulverschweißen mit Metallpulverzusatz" or self.schweißprocess =="125 Unterpulverschweißen mit Fülldrahtelektrode" or self.schweißprocess =="126 Unterpulverschweißen mit Füllbandelektrode" or self.schweißprocess == "311 Gasschweißen mit Sauerstoff-Acetylen-Flamme"  or self.schweißprocess=="312 Gasschweißen mit Sauerstoff-Propan-Flamme" or self.schweißprocess=="313 asschweißen mit Sauerstoff-Wasserstoff-Flamme"):
          tab.append(("ISO 14175-N5-NH-20 nach EN ISO 14175(Formiergas80/20)", "ISO 14175-N5-NH-20 nach EN ISO 14175(Formiergas80/20)"))
          tab.append(("ISO 14175-R2-ArH-20 nach EN ISO 14175(ARCAL PLASMA 62)", "ISO 14175-R2-ArH-20 nach EN ISO 14175(ARCAL PLASMA 62)"))
          return tab
        if(self.schweißprocess == "131 Metall-Inertgasschweißen mit Massivdrahtelektrode" or self.schweißprocess == "132 Metall-Inertgasschweißen mit schweißpulvergefüllter Drahtelektrode" or self.schweißprocess=="133 Metall-Inertgasschweißen mit metallpulvergefüllter Drahtelektrode" or self.schweißprocess == "15 Plasmaschweißen"):
          tab.append(("ISO 14175-I1-Ar nach EN ISO 14175 (ARCAL 1)", "ISO 14175-I1-Ar nach EN ISO 14175 (ARCAL 1)"))
          tab.append(("ISO 14175-I2-He nach EN ISO 14175", "ISO 14175-I2-He nach EN ISO 14175"))
          tab.append(("ISO 14175-I3-ArHe-30 nach EN ISO 14175 (ARCAL 33)", "ISO 14175-I3-ArHe-30 nach EN ISO 14175 (ARCAL 33)"))
          tab.append(("ISO 14175-N5-NH-20 nach EN ISO 14175 (Fromiergas 80/20)", "ISO 14175-N5-NH-20 nach EN ISO 14175 (Fromiergas 80/20)"))
          tab.append(("ISO 14175-R2-ArH-20 nach EN ISO 14175 (ARCAL PLASMA 62)", "ISO 14175-R2-ArH-20 nach EN ISO 14175 (ARCAL PLASMA 62)"))
          return tab
        if(self.schweißprocess == "136 Metall-Aktivgasschweißen mit schweißpulvergefüllter Drahtelektrode" or self.schweißprocess == "138 Metall-Aktivgasschweißen mit metallpulvergefüllter Drahtelektrode"):
          tab.append(("ISO 14175-C1-C nach EN ISO 14175", "ISO 14175-C1-C nach EN ISO 14175"))
          tab.append(("ISO 14175-M12-ArC-2 nach EN ISO 14175(ARCAL 12)", "ISO 14175-M12-ArC-2 nach EN ISO 14175(ARCAL 12)"))
          tab.append(("ISO 14175-M12-ArHeC-18/1 nach EN ISO 14175(ARCAL 121)", "ISO 14175-M12-ArHeC-18/1 nach EN ISO 14175(ARCAL 121)"))
          tab.append(("ISO 14175-M13-ArO-2 nach EN ISO 14175(CARGAL)", "ISO 14175-M13-ArO-2 nach EN ISO 14175(CARGAL)"))
          tab.append(("ISO 14175-M14-ArCO-3/1 nach EN ISO 14175(ARCAL 14)", "ISO 14175-M14-ArCO-3/1 nach EN ISO 14175(ARCAL 14)"))
          tab.append(("ISO 14175-M20-ArC8 nach EN ISO 14175(ARCAL 21)", "ISO 14175-M20-ArC8 nach EN ISO 14175(ARCAL 21)"))
          tab.append(("ISO 14175-M21-ArC-18 nach EN ISO 14175(ATAL, ARCAL 5)", "ISO 14175-M21-ArC-18 nach EN ISO 14175(ATAL, ARCAL 5)"))
          tab.append(("ISO 14175-M22-ArO-8 nach EN ISO 14175(CARGAL 4)", "ISO 14175-M22-ArO-8 nach EN ISO 14175(CARGAL 4)"))
          tab.append(("ISO 14175-M23-ArCO-5/5 nach EN ISO 14175(TERAL)", "ISO 14175-M23-ArCO-5/5 nach EN ISO 14175(TERAL)"))
          tab.append(("ISO 14175-M24-ArCO-12/2 nach EN ISO 14175(ARCAL 24)", "ISO 14175-M24-ArCO-12/2 nach EN ISO 14175(ARCAL 24)"))
          tab.append(("ISO 14175-N5-NH-20 nach EN ISO 14175(Formiergas 80/20)", "ISO 14175-N5-NH-20 nach EN ISO 14175(Formiergas 80/20)"))
          tab.append(("ISO 14175-R2-ArH-20 nach EN ISO 14175(ARCAL PLASMA 62)", "ISO 14175-R2-ArH-20 nach EN ISO 14175(ARCAL PLASMA 62)"))

          return tab
        else:
          if(self.schweißprocess == "111/121 Wurzel E, Auffüllen mit UP (Stahl)" or self.schweißprocess == "111/135 Wurzel E, Auffüllen mit MAG (Stahl)" or self.schweißprocess == "135 Metall-Aktivgasschweißen mit Massivdrahtelektrode"  or self.schweißprocess =="135/111 Wurzel MAG, Auffüllen mit  E (Stahl)" or self.schweißprocess =="135/121 Wurzel MAG, Auffüllen mit  UP (Stahl)" or self.schweißprocess =="136/121 Wurzel MAG, Auffüllen mit  UP (Stahl)" or self.schweißprocess == "141 Wolfram-Inertgasschweißen mit Massivdraht- oder Massivstabzusatz" or self.schweißprocess == "141/111 Wurzel WIG, Auffüllen mit  E (Stahl, Cu, Ni)"  or self.schweißprocess =="141/121 Wurzel WIG, Auffüllen mit  UP (Stahl, Ni)" or self.schweißprocess=="141/131 Wurzel WIG, Auffüllen mit  MIG (Al, Cu, Ni, Ti)" or self.schweißprocess=="141/135 Wurzel WIG, Auffüllen mit  MAG (Stahl, Ni)" or self.schweißprocess=="141/136 Wurzel WIG, Auffüllen mit  MAG (Stahl)" or self.schweißprocess=="142 Wolfram-Inertgasschweißen ohne Schweißzusatz" or self.schweißprocess=="143 Wolfram-Inertgasschweißen mit Fülldraht- oder Füllstabzusatz" or self.schweißprocess=="145 WIG-Schweißen mit reduzierenden Gasanteilen und Massivzusatz(Draht/Stab)" or self.schweißprocess=="146 WIG-Schweißen mit reduzierenden Gasanteilen und Füllzusatz(Draht/Stab)"  or self.schweißprocess=="147 Wolfram-Schutzgasschweißen mit aktiven Gesanteilen im inerten Schutzgas" or self.schweißprocess=="151 Plasma-Metall-Inertgasschweißen" or self.schweißprocess=="152 Pulver-Plasmalichtbogenschweißen"):
             tab.append(("ISO 14175-C1-C nach EN ISO 14175", "ISO 14175-C1-C nach EN ISO 14175"))
             tab.append(("ISO 14175-I1-Ar nach EN ISO 14175(ARCAL 1)", "ISO 14175-I1-Ar nach EN ISO 14175(ARCAL 1)"))
             tab.append(("ISO 14175-I2-He nach EN ISO 14175", "ISO 14175-I2-He nach EN ISO 14175"))
             tab.append(("ISO 14175-I3-ArHe-30 nach EN ISO 14175(ARCAL 33)", "ISO 14175-I3-ArHe-30 nach EN ISO 14175(ARCAL 33)"))
             tab.append(("ISO 14175-M12-ArC-2 nach EN ISO 14175(ARCAL 12)", "ISO 14175-M12-ArC-2 nach EN ISO 14175(ARCAL 12)"))
             tab.append(("ISO 14175-M12-ArHeC-18/1 nach EN ISO 14175(ARCAL 121)", "ISO 14175-M12-ArHeC-18/1 nach EN ISO 14175(ARCAL 121)"))
             tab.append(("ISO 14175-M13-ArO-2 nach EN ISO 14175(CARGAL)", "ISO 14175-M13-ArO-2 nach EN ISO 14175(CARGAL)"))
             tab.append(("ISO 14175-M14-ArCO-3/1 nach EN ISO 14175(ARCAL 14)", "ISO 14175-M14-ArCO-3/1 nach EN ISO 14175(ARCAL 14)"))
             tab.append(("ISO 14175-M20-ArC-8 nach EN ISO 14175(ARCAL 21)", "ISO 14175-M20-ArC-8 nach EN ISO 14175(ARCAL 21)"))
             tab.append(("ISO 14175-M21-ArC-18 nach EN ISO 14175(ATAL,ARCAL 5)", "ISO 14175-M21-ArC-18 nach EN ISO 14175(ATAL,ARCAL5)"))
             tab.append(("ISO 14175-M22-ArO-8 nach EN ISO 14175(CARGAL 4)", "ISO 14175-M22-ArO-8 nach EN ISO 14175(CARGAL4)"))
             tab.append(("ISO 14175-M23-ArCO-5/5 nach EN ISO 14175(TERAL)", "ISO 14175-M23-ArCO-5/5 nach EN ISO 14175(TERAL)"))
             tab.append(("ISO 14175-M24-ArCO-12/2 nach EN ISO 14175(ARCAL 24)", "ISO 14175-M24-ArCO-12/2 nach EN ISO 14175(ARCAL 24)"))
             tab.append(("ISO 14175-N2-ArN-2 nach EN ISO 14175(ARCAL 391)", "ISO 14175-N2-ArN-2 nach EN ISO 14175(ARCAL 391)"))
             tab.append(("ISO 14175-N4-ArNH-3/0,7 nach EN ISO 14175(ARCAL 405)", "ISO 14175-N4-ArNH-3/0,7 nach EN ISO 14175(ARCAL 405)"))
             tab.append(("ISO 14175-N5-NH-20 nach EN ISO 14175(Formiergas 80/20)", "ISO 14175-N5-NH-20 nach EN ISO 14175(Formiergas 80/20)"))
             tab.append(("ISO 14175-R1-ArH-10 nach EN ISO 14175(NOXAL 4)", "ISO 14175-R1-ArH-10 nach EN ISO 14175(NOXAL 4)"))
             tab.append(("ISO 14175-R1-ArH-2,4 nach EN ISO 14175(ARCAL 10)", "ISO 14175-R1-ArH-2,4 nach EN ISO 14175(ARCAL 10)"))
             tab.append(("ISO 14175-R2-ArH-20 nach EN ISO 14175(ARCAL PLASMA 62)", "ISO 14175-R2-ArH-20 nach EN ISO 14175(ARCAL PLASMA 62)"))
             tab.append(("ISO 14175-Z-Ar+N-0,015 nach EN ISO 14175(ARCAL 1N)", "ISO 14175-Z-Ar+N-0,015 nach EN ISO 14175(ARCAL 1N)"))

             return tab

    def On_change_aussendurchmesser(self,aussendurchmesser):
      if(self.aussendurchmesser is not None):
        if(self.nahtart =="Stumpfnaht am Blech(P,BW) einseitig mit Schweißbadsicherung (ss,mb)" or self.nahtart=="Stumpfnaht am Blech (P,BW) einseitig ohne Schweißbadsicherung (ss,nb)" or self.nahtart=="Stumpfnaht am Blech (P,BW) beidseitig mit Ausfugen(bs,gg)" or self.nahtart=="Stumpfnaht am Blech (P,BW) beidseitig ohne Ausfugen(bs,ng)" or self.nahtart=="T-Stumpfstoß, kehlnaht am Blech ohne Fugenvorbereitung (P,FW)" or self.nahtart == "Kehlnaht am Blech (P,FW) einseitig geschweißt (ss)" or self.nahtart == "Kehlnaht am Blech (P,FW) beidseitig geschweißt (bs)"):
           return "Rohre mit D > 500 mm"
        if((self.nahtart == "Stumpfnaht am Rohr (T,BW) mit Schweißbadsicherung (ss,mb)" or self.nahtart == "Stumpfnaht am Rohr (T,BW) ohne Schweißbadsicherung (ss,nb)" or self.nahtart == "Rohrabzweigung, kehlnaht am Rohr (T,FW)" or self.nahtart == "Kehlnaht am Rohr (T,FW)") and (self.aussendurchmesser > 168)):
           return"Geltungsbereich: D>=250 mm und Bleche"
        if((self.nahtart == "Stumpfnaht am Rohr (T,BW) mit Schweißbadsicherung (ss,mb)" or self.nahtart == "Stumpfnaht am Rohr (T,BW) ohne Schweißbadsicherung (ss,nb)" or self.nahtart == "Rohrabzweigung, kehlnaht am Rohr (T,FW)" or self.nahtart == "Kehlnaht am Rohr (T,FW)") and (self.aussendurchmesser <= 168)):
           return "Geltungsbereich: "+str(round(0.5*self.aussendurchmesser,1))+" bis "+str(round(2*self.aussendurchmesser,1))+" mm"
      else:
        return" "

    def On_change_grundwerkstoffe(self,grundwerkstoffe):
       if(self.grundwerkstoffe is not None):
         return "Gruppe "+self.grundwerkstoffe.Werkstoffgruppe
       else:
         return " "
    def On_change_grundwerkstoffe2(self,grundwerkstoffe2):
       if(self.grundwerkstoffe2 is not None):
         return "Gruppe "+self.grundwerkstoffe2.Werkstoffgruppe
       else:
         return " "

    def On_change_grundwerkstoffe3(self,grundwerkstoffe):
      if(self.grundwerkstoffe is not None):
         return self.grundwerkstoffe.Nummer
      else:
         return " "
    def On_change_grundwerkstoffe4(self,grundwerkstoffe2):
       if(self.grundwerkstoffe2 is not None):
         return self.grundwerkstoffe2.Nummer
       else:
         return " "

    def On_change_dicke(self,dicke):
     if(self.dicke is not None):
       if(self.dicke > 0 and self.dicke <= 3):
         return "Geltungsbereich:einlagig("+str(round(0.8*self.dicke,1))+"-"+str(round(1.1*self.dicke,1))+" mm); mehrlagig("+str(round(1.0*self.dicke,1))+"-"+str(round(2.0*self.dicke,1))+" mm)"
       if(self.dicke > 12 and self.dicke <= 75):
         return "Geltungsbereich:einlagig("+str(round(0.8*self.dicke,1))+"-"+str(round(1.1*self.dicke,1))+" mm); mehrlagig("+str(round(0.5*self.dicke,1))+"-"+str(round(2.0*self.dicke,1))+" mm)"
       if(self.dicke > 75 and self.dicke <= 100):
         return "Geltungsbereich:einlagig("+str(round(0.8*self.dicke,1))+"-"+str(round(1.1*self.dicke,1))+" mm); mehrlagig("+str(round(0.5*self.dicke,1))+"-150,0  mm)"
       if(self.dicke > 100):
         return "Geltungsbereich:einlagig("+str(round(0.8*self.dicke,1))+"-"+str(round(1.1*self.dicke,1))+" mm); mehrlagig("+str(round(0.5*self.dicke,1))+"-"+str(round(1.5*self.dicke,1))+" mm)"
       if(self.dicke > 3 and self.dicke <= 12):
         return "Geltungsbereich:einlagig("+str(round(0.8*self.dicke,1))+"-"+str(round(1.1*self.dicke,1))+" mm); mehrlagig(3.0-"+str(round(2.0*self.dicke,1))+" mm)"
     else:
        return " "

    def On_change_schweissprocess(self,schweißprocess):
       if(self.schweißprocess == "111  Lichtbogenhandschweißen"):
          return "Lichtbogenhandschweißen (E)"
       if(self.schweißprocess == "111/135 Wurzel E, Auffüllen mit MAG (Stahl)"):
          return "Wurzel E, Auffüllen mit MAG (Stahl)(E/MAG)"
       if(self.schweißprocess == "112 Schwerkraft-Lichtbogenschweißen"):
          return "Schwerkraft-Lichtbogenschweißen (SK)"
       if(self.schweißprocess == "114 Metall-Lichtbogenschweißen mit Fülldrahtelektrode ohne Schutzgas"):
          return "Metall-Lichtbogenschweißen mit Fülldrahtelektrode ohne Schutzgas (MF)"
       if(self.schweißprocess == "12 Unterpulverschweißen"):
          return "Unterpulverschweißen (UP)"
       if(self.schweißprocess == "121 Unterpulverschweißen mit Massivdrahtelektrode"):
          return "Unterpulverschweißen mit Massivdrahtelektrode (UP)"
       if(self.schweißprocess == "122 Unterpulverschweißen mit Massivbandelektrode"):
          return "Unterpulverschweißen mit Massivbandelektrode (UP)"
       if(self.schweißprocess == "124 Unterpulverschweißen mit Metallpulverzusatz"):
          return "Unterpulverschweißen mit Metallpulverzusatz (UP)"
       if(self.schweißprocess == "125 Unterpulverschweißen mit Fülldrahtelektrode"):
          return "Unterpulverschweißen mit Fülldrahtelektrode (UP)"
       if(self.schweißprocess == "126 Unterpulverschweißen mit Füllbandelektrode"):
          return "Unterpulverschweißen mit Füllbandelektrode (UP)"
       if(self.schweißprocess == "131 Metall-Inertgasschweißen mit Massivdrahtelektrode"):
          return "Metall-Inertgasschweißen mit Massivdrahtelektrode (MIG)"
       if(self.schweißprocess == "132 Metall-Inertgasschweißen mit schweißpulvergefüllter Drahtelektrode"):
          return "Metall-Inertgasschweißen mit schweißpulvergefüllter Drahtelektrode(MIG)"
       if(self.schweißprocess == "133 Metall-Inertgasschweißen mit metallpulvergefüllter Drahtelektrode"):
          return "Metall-Inertgasschweißen mit metallpulvergefüllter Drahtelektrode (MIG)"
       if(self.schweißprocess == "135 Metall-Aktivgasschweißen mit Massivdrahtelektrode"):
          return "Metall-Aktivgasschweißen mit Massivdrahtelektrode(MAG)"
       if(self.schweißprocess == "135/111 Wurzel MAG, Auffüllen mit  E (Stahl)"):
          return "Wurzel MAG, Auffüllen mit  E (Stahl)(MAG/E)"
       if(self.schweißprocess == "135/111 Wurzel MAG, Auffüllen mit  E (Stahl)"):
          return "Wurzel MAG, Auffüllen mit  E (Stahl)(MAG/E)"
       if(self.schweißprocess == "135/121 Wurzel MAG, Auffüllen mit  UP (Stahl)"):
          return "Wurzel MAG, Auffüllen mit UP (Stahl)(MAG/UP)"
       if(self.schweißprocess == "136 Metall-Aktivgasschweißen mit schweißpulvergefüllter Drahtelektrode"):
          return "Metall-Aktivgasschweißen mit schweißpulvergefüllter Drahtelektrode (MAG)"
       if(self.schweißprocess == "136/121 Wurzel MAG, Auffüllen mit  UP (Stahl)"):
          return "Wurzel MAG, Auffüllen mit  UP (Stahl)"
       if(self.schweißprocess == "138 Metall-Aktivgasschweißen mit metallpulvergefüllter Drahtelektrode"):
          return "Metall-Aktivgasschweißen mit metallpulvergefüllter Drahtelektrode"
       if(self.schweißprocess == "141 Wolfram-Inertgasschweißen mit Massivdraht- oder Massivstabzusatz"):
          return "Wolfram-Inertgasschweißen mit Massivdraht- oder Massivstabzusatz"
       if(self.schweißprocess == "141/111 Wurzel WIG, Auffüllen mit  E (Stahl, Cu, Ni)"):
          return "Wurzel WIG, Auffüllen mit  E (Stahl, Cu, Ni)"
       if(self.schweißprocess == "141/121 Wurzel WIG, Auffüllen mit  UP (Stahl, Ni)"):
          return "Wurzel WIG, Auffüllen mit  UP (Stahl, Ni)"
       if(self.schweißprocess == "141/131 Wurzel WIG, Auffüllen mit  MIG (Al, Cu, Ni, Ti)"):
          return "Wurzel WIG, Auffüllen mit  MIG (Al, Cu, Ni, Ti)(WIG/MIG)"
       if(self.schweißprocess == "141/135 Wurzel WIG, Auffüllen mit  MAG (Stahl, Ni)"):
          return "Wurzel WIG, Auffüllen mit  MAG (Stahl, Ni)(WIG/MAG)"
       if(self.schweißprocess == "141/136 Wurzel WIG, Auffüllen mit  MAG (Stahl)"):
          return "Wurzel WIG, Auffüllen mit  MAG (Stahl)(WIG/MAG)"
       if(self.schweißprocess == "142 Wolfram-Inertgasschweißen ohne Schweißzusatz"):
          return "Wolfram-Inertgasschweißen ohne Schweißzusatz (WIG)"
       if(self.schweißprocess == "143 Wolfram-Inertgasschweißen mit Fülldraht- oder Füllstabzusatz"):
          return "Wolfram-Inertgasschweißen mit Fülldraht- oder Füllstabzusatz (WIG)"
       if(self.schweißprocess == "145 WIG-Schweißen mit reduzierenden Gasanteilen und Massivzusatz(Draht/Stab)"):
          return "WIG-Schweißen mit reduzierenden Gasanteilen und Massivzusatz(Draht/Stab)"
       if(self.schweißprocess == "146 WIG-Schweißen mit reduzierenden Gasanteilen und Füllzusatz(Draht/Stab)"):
          return "WIG-Schweißen mit reduzierenden Gasanteilen und Füllzusatz(Draht/Stab)"
       if(self.schweißprocess == "147 Wolfram-Schutzgasschweißen mit aktiven Gesanteilen im inerten Schutzgas"):
          return "Wolfram-Schutzgasschweißen mit aktiven Gesanteilen im inerten Schutzgas"
       if(self.schweißprocess == "15 Plasmaschweißen"):
          return "Plasmaschweißen (WPL)"
       if(self.schweißprocess == "151 Plasma-Metall-Inertgasschweißen"):
          return "Plasma-Metall-Inertgasschweißen"
       if(self.schweißprocess == "152 Pulver-Plasmalichtbogenschweißen"):
          return "Pulver-Plasmalichtbogenschweißen"
       if(self.schweißprocess == "311 Gasschweißen mit Sauerstoff-Acetylen-Flamme"):
          return "Gasschweißen mit Sauerstoff-Acetylen-Flamme"
       if(self.schweißprocess == "312 Gasschweißen mit Sauerstoff-Propan-Flamme"):
          return "Gasschweißen mit Sauerstoff-Propan-Flamme"
       if(self.schweißprocess == "313 asschweißen mit Sauerstoff-Wasserstoff-Flamme"):
          return "Gasschweißen mit Sauerstoff-Wasserstoff-Flamme"

       else:
         if(self.schweißprocess == "111/121 Wurzel E, Auffüllen mit UP (Stahl)"):
           return "Wurzel E, Auffüllen mit UP (Stahl)(E/UP)"



    def On_change_andere(self, schweißprocess):
        chaine=self.schweißprocess
        pos2 = chaine.find(" ")
        res = chaine[0:pos2]
        chaine1 = self.nahtart
        pos1 = chaine1.find("(")
        pos11 = chaine1.find(")")
        res1 = chaine1[pos1+1:pos11]
        if(self.grundwerkstoffe2 is None):
           return "EN 288-3 "+str(res)+" "+str(res1)+" G"+str(self.grundwerkstoffe.Werkstoffgruppe)+" t0"+str(self.dicke)+" "+str(self.schweissposition)
        else:
           return "EN 288-3 "+str(res)+" "+str(res1)+" G"+str(self.grundwerkstoffe.Werkstoffgruppe)+"/G"+str(self.grundwerkstoffe2.Werkstoffgruppe)+" t0"+str(self.dicke)+" "+str(self.schweissposition)

    @staticmethod
    def default_schweissposition_gel():
      return "Geltungsbereich: alles Positionen(Blech oder Rohr) (Siehe 8.4.2)"
    @staticmethod
    def default_regel():
       return "DIN EN 288-3(Schweißverfahrensprüfungen für das Lichtbogenschweißen von stählen)"

#classes for Print Fonction for WPQR3
# class view
class PrintISOWPQR3Start(ModelView):
    'Print START WPQR3'
    __name__ = 'party.print_isowpqr3.start'
    zertifikat = fields.Many2One('party.en288x', 'Zertifikat', required=True)

#Wizard
class PrintWPQR3(Wizard):
    'Print ISOWPQR3'
    __name__ = 'party.print_isowpqr3'
    start = StateView('party.print_isowpqr3.start',
        'welding_certification.print_isowpqr3_cert_start_view_form', [
            Button('Cancel', 'end', 'tryton-cancel'),
            Button('Drucken', 'print_', 'tryton-print', default=True),
            ])
    print_ = StateReport('welding_certification.party.iso_wpqr3_report')
    def do_print_(self, action):
        data = {
            'zertifikat': self.start.zertifikat.id,
            }
        return action, data

#Report
class ISOWPQR3report(Report):
    __name__ = 'welding_certification.party.iso_wpqr3_report'


    @classmethod
    def _get_records(cls, ids, model, data):
        Move = Pool().get('party.en288x')

        clause = [

            ]


    @classmethod
    def get_context(cls, records, data):
        report_context = super(ISOWPQR3report, cls).get_context(records, data)

        Zertifikat = Pool().get('party.en288x')

        zertifikat = Zertifikat(data['zertifikat'])

        report_context['zertifikat'] = zertifikat
        report_context['hersteller'] = zertifikat.hersteller
        report_context['anschrift'] = zertifikat.anschrift
        report_context['verfahrens'] = zertifikat.schweissverfahren
        report_context['prufer'] = zertifikat.prufer1
        report_context['beleg1'] = zertifikat.beleg1
        report_context['beleg2'] = zertifikat.beleg2
        report_context['regel'] = zertifikat.regel
        report_context['datum_schweissen'] = zertifikat.datum_schweissen
        report_context['prufumfang'] = zertifikat.prufumfang
        report_context['schweissprozess'] = zertifikat.schweißprocess
        report_context['schweissprozess_gel'] = zertifikat.schweiss_gel
        report_context['nahtart'] = zertifikat.nahtart
        report_context['bezeichnung1'] = zertifikat.grundwerkstoffe.Bezeichnung
        report_context['bezeichnung2'] = zertifikat.grundwerkstoffe2.Bezeichnung
        report_context['grup1'] = zertifikat.grup1
        report_context['grup2'] = zertifikat.grup2
        report_context['nummer1'] = zertifikat.nummer1
        report_context['nummer2'] = zertifikat.nummer2
        report_context['hartegrad'] = zertifikat.hartegrade
        report_context['dicke'] = zertifikat.dicke
        report_context['dicke_gel'] = zertifikat.dicke_gel
        report_context['aussendurchmesser'] = zertifikat.aussendurchmesser
        report_context['aussendurchmesser_gel'] = zertifikat.aussendurchmesser_gel
        report_context['zusatz'] = zertifikat.zusatzwerkstoff.Bezeichnung
        report_context['pulver'] = zertifikat.pulver
        report_context['stromart'] = zertifikat.stromart
        report_context['position'] = zertifikat.schweissposition
        report_context['position_gel'] = zertifikat.schweissposition_gel
        report_context['vorwaimung'] = zertifikat.vorwarmung
        report_context['aushertung'] = zertifikat.warmenachbehandlung
        report_context['sonstige'] = zertifikat.sonstige
        report_context['ort'] = zertifikat.ort
        report_context['prufer_prufstelle'] = zertifikat.prufer_prufstelle1.prufstelle
        report_context['unterschrift'] = zertifikat.unterschrift
        report_context['datum_ausstellung'] = zertifikat.datum_ausstellung


        return report_context






# schutzgas_pulver class
class schutzgaswpqr(DeactivableMixin, ModelView, ModelSQL, MultiValueMixin):
    'Party shutzgas'
    __name__ = 'party.schutzgas'
    bezeichnung = fields.Char("Bezeichnung")
    norm = fields.Selection([
        ('DIN EN 439', 'Schutzgase zum Lichtbogenschweißen und Schneiden'),
        ('EN ISO 14175', 'Gase und Mischgase für das Lichtbogenschweißen und verwandte Prozesse'),
        ('SFA-5.32', 'Schutzgase für das Schweißen '),
    ], 'Norm', readonly = False,
        )
    hersteller = fields.Char("Hersteller")
    kurztitel = fields.Char("Kurztitel Norm")
    handelsname = fields.Char("Handelsname")
    eignung = fields.Char("Eignung")
    komponenten = fields.Char("Komponenten")
    bemerkung = fields.Char("Bemerkungen")


    def get_rec_name(self, bezeichnung):
        return self.bezeichnung
#Prüfergebnisse ZfP Class
class prufergebnisse(DeactivableMixin, ModelView, ModelSQL, MultiValueMixin):
    'Party PrufErgebnisse'
    __name__ = 'party.pruf.ergebnisse'
    sichtprufung = fields.Char('Sichtprüfung nach EN ISO 17637')
    durchprufung = fields.Char('Durchstrahlungsprüfung* nach EN ISO 17636')
    eindringprufung = fields.Char('Eindringprüfung* nach EN ISO 3452-1')
    ultraprufung = fields.Char('Ultraschallprüfung* nach EN ISO 17640')
    magnetprufung = fields.Char('Magnetpulverprüfung* nach EN ISO 17638')
    index1 = fields.Char('*Falls gefordert')
    index2 = fields.Char('e = erfüllt/satisfactory')
    index3 = fields.Char('ne = nicht erfüllt/ not satisfactory')
    index4 = fields.Char('ng = nicht gefordert / not required')
    ergebnisse_link = fields.Many2One('party.wpqr.bericht1', 'berift1', required=True,
        ondelete='CASCADE', states=STATES, select=True, depends=DEPENDS)

#Querzugversuch Class
class Querzugversuch(DeactivableMixin, ModelView, ModelSQL, MultiValueMixin):
    'Party Querzugversuch'
    __name__ = 'party.querzugversuch'
    art_nr = fields.Char('Art / Nr')
    re = fields.Char('Re [MPa]')
    rm = fields.Char('Rm [MPa]')
    a = fields.Char('A [%]')
    z = fields.Char('Z [%]')
    bruchlage = fields.Char('Bruchlage')
    bemerkung = fields.Char('Bemerkungen')
    querzugversuch_link = fields.Many2One('party.wpqr.bericht1', 'berift1_1', required=True,
        ondelete='CASCADE', states=STATES, select=True, depends=DEPENDS)

#Querzugversuch Class
class Biegepruf(DeactivableMixin, ModelView, ModelSQL, MultiValueMixin):
    'Party Biegeprufung2'
    __name__ = 'party.wpqr.biegeprufung1'
    art_nr = fields.Char('Art / Nr')
    biege_winkel = fields.Char('Biegewinkel [°]')
    biegedorn = fields.Char('Biegedorndurchmesser[mm]')
    dehnung = fields.Char('Dehnung*')
    ergebnisse = fields.Char('Ergebnisse')
    biege_link = fields.Many2One('party.wpqr.bericht1', 'berift1_2', required=True,
        ondelete='CASCADE', states=STATES, select=True, depends=DEPENDS)



#Querzugversuch Class
class kerbschlabiegeversuch1(DeactivableMixin, ModelView, ModelSQL, MultiValueMixin):
    'Party Kerbschlabiegeversuch1'
    __name__ = 'party.kerbschlabiegeversuch1'
    kerblage_richtung = fields.Char('Kerblage / Richtung')
    art = fields.Char('Art')
    masse = fields.Char('Maße')
    anforderung = fields.Char('Anforderung')
    temperature = fields.Char('Temperatur [°C]')
    werte1 = fields.Char('Werte1')
    werte2 = fields.Char('Werte2')
    werte3 = fields.Char('Werte3')
    mittelwert = fields.Char('Mittelwert')
    Bemerkungen = fields.Char('Bemerkungen')

    kerbschlabiege_link = fields.Many2One('party.wpqr.bericht1', 'berift1_3', required=True,
        ondelete='CASCADE', states=STATES, select=True, depends=DEPENDS)

#härteprüfung class
class Harteprufung(DeactivableMixin, ModelView, ModelSQL, MultiValueMixin):
    'Party Harteprufung'
    __name__ = 'party.harteprufung'
    art_prufkraft = fields.Char('Art / Prüfkraft')

    harte_link = fields.Many2One('party.wpqr.bericht2', 'berift2_', required=True,
        ondelete='CASCADE', states=STATES, select=True, depends=DEPENDS)

class Harteprufung1(DeactivableMixin, ModelView, ModelSQL, MultiValueMixin):
    'Party Harteprufung_1'
    __name__ = 'party.harteprufung1'

    werte = fields.Char('Werte')
    grundwerkstof = fields.Char('Grundwerkstoff')
    wez = fields.Char('WEZ')
    schweissgut = fields.Char('Schweißgut')
    harte_1_link = fields.Many2One('party.wpqr.bericht2', 'berift3_', required=True,
        ondelete='CASCADE', states=STATES, select=True, depends=DEPENDS)


#Prufbericht2 class
class wpqrbericht2(DeactivableMixin, ModelView, ModelSQL, MultiValueMixin):
    'Party WPQR_BERICHT2'
    __name__ = 'party.wpqr.bericht2'
    hersteller = fields.Many2One('party.wpqr', 'Hersteller')
    wps = fields.Many2One('party.wps', 'pWPS-Nr des Herstelles')
    space = fields.Char("                                                                                                                                                                                                                               ")
    prufer = fields.Function(fields.Char("Prüfer oder Prüfstelle"),"On_change_hersteller")
    wpqr_nr = fields.Function(fields.Char("WPQR-Nr. des Herstellers"),"On_change_hersteller1")
    beleg_nr = fields.Function(fields.Char("Beleg-Nr"),"On_change_hersteller2")
    regel = fields.Function(fields.Char("Regel/Prüfnorm"),"On_change_hersteller3")
    datum_schweissen = fields.Function(fields.Date("Datum der Schweißung"),"On_change_hersteller4")
    anschrift = fields.Function(fields.Char("Anschrift"),"On_change_hersteller5")
    hartpruf1 = fields.One2Many('party.harteprufung','harte_link','Härteprüfung* nach EN ISO 9015-1[EN ISO 6507-1][1]')
    hartpruf2 = fields.One2Many('party.harteprufung1','harte_1_link','Härteprüfung* nach EN ISO 9015-1[EN ISO 6507-1][2]')
    Bild = fields.Binary("Bild")
    sonstige = fields.Char("Sonstige Prüfungen")
    bemerkungen = fields.Text("Bemerkungen")
    requirememt = fields.Char("Die Prüfungen werden ausgeführt in übereinstimmung mit den Anforderungen von")
    labor_bericht = fields.Char("Labor-Bericht-Nr")
    prufergebnisse = fields.Selection([
        ('erfüllt', 'erfüllt/satisfactory'),
        ('nicht erfüllt', 'nicht erfüllt/not satisfactory'),
    ], 'Die Prüfergebnisse sind:', readonly = False,
        )
    anwesenheit = fields.Char("Die Prüfungen werden ausgeführt in Anwesenheit von")
    @classmethod
    def __setup__(cls):
      super(wpqrbericht2, cls).__setup__()
      cls._buttons.update({
          'Print': {},
          })

    @classmethod
    @ModelView.button
    @ModelView.button_action('welding_certification.report_bericht_2')
    def Print(cls, wpqrbericht2):
       pass

    def do_Print(self, action):
        data = {
            'id': self.id,
            }
        return action, data


    def On_change_hersteller(self, hersteller):
        return self.hersteller.prufer_prufstelle
    def On_change_hersteller1(self, hersteller):
        return self.hersteller.wpqr_nr_1
    def On_change_hersteller2(self, hersteller):
        return self.hersteller.beleg_nr
    def On_change_hersteller3(self, hersteller):
        return self.hersteller.regel
    def On_change_hersteller4(self, hersteller):
        return self.hersteller.datum_schweissen
    def On_change_hersteller5(self, hersteller):
        return self.hersteller.anschrift


    def get_rec_name(self, hersteller):
        return "Prüfbericht Seite 2/2"

#report fur berich2
class Bericht2report(Report):
    __name__ = 'welding_certification.party.bericht2_report'



    @classmethod
    def _get_records(cls, ids, model, data):
        Move = Pool().get('party.wpqr.bericht2')

        clause = [

            ]


    @classmethod
    def get_context(cls, records, data):
        report_context = super(Bericht2report, cls).get_context(records, data)

        Company = Pool().get('party.wpqr.bericht2')
        company = Company(data['id'])

        report_context['company'] = company
        report_context['wps'] = company.wps.Beleg_Nr
        report_context['prufer'] = company.prufer
        report_context['regel'] = company.regel
        report_context['hersteller'] = company.wpqr_nr
        report_context['beleg'] = company.beleg_nr
        report_context['herst'] = company.hersteller.hersteller
        report_context['datum_schweiss'] = company.datum_schweissen
        report_context['Anscherift'] = company.anschrift
        report_context['labor_bericht'] = company.labor_bericht
        report_context['bemerkungen'] = company.bemerkungen
        report_context['requirememt'] = company.requirememt
        report_context['labo'] = company.labor_bericht
        report_context['ergebnisse'] = company.prufergebnisse
        report_context['anwesenheit'] = company.anwesenheit


        index=len(company.hartpruf1)
        if(index == 1):
           report_context['art0']=company.hartpruf1[0].art_prufkraft
           report_context['art1']=" "
        else:
           if(index == 2):
             report_context['art0']=company.hartpruf1[0].art_prufkraft
             report_context['art1']=company.hartpruf1[1].art_prufkraft
           else:
              report_context['art0']=" "
              report_context['art1']=" "

        index2=len(company.hartpruf2)
        if(index2 == 1):
          report_context['wert0']=company.hartpruf2[0].werte
          report_context['wert1']=" "
          report_context['wert2']=" "
          report_context['wert3']=" "
          report_context['grund0']=company.hartpruf2[0].grundwerkstof
          report_context['grund1']=" "
          report_context['grund2']=" "
          report_context['grund3']=" "
          report_context['wez0']=company.hartpruf2[0].wez
          report_context['wez1']=" "
          report_context['wez2']=" "
          report_context['wez3']=" "
          report_context['schweiss0']=company.hartpruf2[0].schweissgut
          report_context['schweiss1']=" "
          report_context['schweiss2']=" "
          report_context['schweiss3']=" "
        else:
           if(index2 == 2):
             report_context['wert0']=company.hartpruf2[0].werte
             report_context['wert1']=company.hartpruf2[1].werte
             report_context['wert2']=" "
             report_context['wert3']=" "
             report_context['grund0']=company.hartpruf2[0].grundwerkstof
             report_context['grund1']=company.hartpruf2[1].grundwerkstof
             report_context['grund2']=" "
             report_context['grund3']=" "
             report_context['wez0']=company.hartpruf2[0].wez
             report_context['wez1']=company.hartpruf2[1].wez
             report_context['wez2']=" "
             report_context['wez3']=" "
             report_context['schweiss0']=company.hartpruf2[0].schweissgut
             report_context['schweiss1']=company.hartpruf2[1].schweissgut
             report_context['schweiss2']=" "
             report_context['schweiss3']=" "
           else:
             if(index2 == 3):
                report_context['wert0']=company.hartpruf2[0].werte
                report_context['wert1']=company.hartpruf2[1].werte
                report_context['wert2']=company.hartpruf2[2].werte
                report_context['wert3']=" "
                report_context['grund0']=company.hartpruf2[0].grundwerkstof
                report_context['grund1']=company.hartpruf2[1].grundwerkstof
                report_context['grund2']=company.hartpruf2[2].grundwerkstof
                report_context['grund3']=" "
                report_context['wez0']=company.hartpruf2[0].wez
                report_context['wez1']=company.hartpruf2[1].wez
                report_context['wez2']=company.hartpruf2[2].wez
                report_context['wez3']=" "
                report_context['schweiss0']=company.hartpruf2[0].schweissgut
                report_context['schweiss1']=company.hartpruf2[1].schweissgut
                report_context['schweiss2']=company.hartpruf2[2].schweissgut
                report_context['schweiss3']=" "
             else:
                if(index2 == 4):
                  report_context['wert0']=company.hartpruf2[0].werte
                  report_context['wert1']=company.hartpruf2[1].werte
                  report_context['wert2']=company.hartpruf2[2].werte
                  report_context['wert3']=company.hartpruf2[3].werte
                  report_context['grund0']=company.hartpruf2[0].grundwerkstof
                  report_context['grund1']=company.hartpruf2[1].grundwerkstof
                  report_context['grund2']=company.hartpruf2[2].grundwerkstof
                  report_context['grund3']=company.hartpruf2[3].grundwerkstof
                  report_context['wez0']=company.hartpruf2[0].wez
                  report_context['wez1']=company.hartpruf2[1].wez
                  report_context['wez2']=company.hartpruf2[2].wez
                  report_context['wez3']=company.hartpruf2[3].wez
                  report_context['schweiss0']=company.hartpruf2[0].schweissgut
                  report_context['schweiss1']=company.hartpruf2[1].schweissgut
                  report_context['schweiss2']=company.hartpruf2[2].schweissgut
                  report_context['schweiss3']=company.hartpruf2[3].schweissgut
                else:
                  report_context['wert0']=company.hartpruf2[0].werte
                  report_context['wert1']=" "
                  report_context['wert2']=" "
                  report_context['wert3']=" "
                  report_context['grund0']=company.hartpruf2[0].grundwerkstof
                  report_context['grund1']=" "
                  report_context['grund2']=" "
                  report_context['grund3']=" "
                  report_context['wez0']=company.hartpruf2[0].wez
                  report_context['wez1']=" "
                  report_context['wez2']=" "
                  report_context['wez3']=" "
                  report_context['schweiss0']=company.hartpruf2[0].schweissgut
                  report_context['schweiss1']=" "
                  report_context['schweiss2']=" "
                  report_context['schweiss3']=" "

        return report_context

#Prufbericht1 class
class wpqrbericht1(DeactivableMixin, ModelView, ModelSQL, MultiValueMixin):
    'Party WPQR_BERICHT'
    __name__ = 'party.wpqr.bericht1'
    ng = fields.Char('ng = nicht gefordert / not required')
    hersteller = fields.Many2One('party.wpqr', 'Hersteller')
    wps = fields.Many2One('party.wps', 'pWPS-Nr des Herstelles')
    space = fields.Char("                                                                                                                                                                                                                        ")
    prufer = fields.Function(fields.Char("Prüfer oder Prüfstelle"),"On_change_hersteller")
    wpqr_nr = fields.Function(fields.Char("WPQR-Nr. des Herstellers"),"On_change_hersteller1")
    beleg_nr = fields.Function(fields.Char("Beleg-Nr"),"On_change_hersteller2")
    regel = fields.Function(fields.Char("Regel/Prüfnorm"),"On_change_hersteller3")
    datum_schweissen = fields.Function(fields.Date("Datum der Schweißung"),"On_change_hersteller4")
    anschrift = fields.Function(fields.Char("Anschrift"),"On_change_hersteller5")
    prufergebnisse = fields.One2Many('party.pruf.ergebnisse','ergebnisse_link','Prüfergebnisse ZfP')
    querzugversuch = fields.One2Many('party.querzugversuch','querzugversuch_link','Querzugversuch nach EN ISO 4136')
    biegepruf1 = fields.One2Many('party.wpqr.biegeprufung1','biege_link','Biegeprüfung nach EN ISO 5173')
    mackroskopische = fields.Char('Makroskopische Untersuchungen nach EN ISO 17639')
    mickroskopische = fields.Char('Mikroskopische Untersuchungen nach EN ISO 17639')

    Kerbschlabiegepruf1 = fields.One2Many('party.kerbschlabiegeversuch1','kerbschlabiege_link','Kerbschlagbiegeversuch* nach EN ISO 9016')


    index1 = fields.Char('*Falls gefordert')
    index2 = fields.Char('e = erfüllt/satisfactory')
    index3 = fields.Char('ne = nicht erfüllt/ not satisfactory')
    index4 = fields.Char('ng = nicht gefordert / not required')

    @classmethod
    def __setup__(cls):
      super(wpqrbericht1, cls).__setup__()
      cls._buttons.update({
          'Print': {},
          })

    @classmethod
    @ModelView.button
    @ModelView.button_action('welding_certification.report_bericht_1')
    def Print(cls, wpqrbericht1):
       pass

    def do_Print(self, action):
        data = {
            'id': self.id,
            }
        return action, data


    def On_change_hersteller(self, hersteller):
        return self.hersteller.prufer_prufstelle
    def On_change_hersteller1(self, hersteller):
        return self.hersteller.wpqr_nr_1
    def On_change_hersteller2(self, hersteller):
        return self.hersteller.beleg_nr
    def On_change_hersteller3(self, hersteller):
        return self.hersteller.regel
    def On_change_hersteller4(self, hersteller):
        return self.hersteller.datum_schweissen
    def On_change_hersteller5(self, hersteller):
        return self.hersteller.anschrift

    def get_rec_name(self, hersteller):
        return "Prüfbericht Seite 1/2"
class Bericht1report(Report):
    __name__ = 'welding_certification.party.bericht1_report'



    @classmethod
    def _get_records(cls, ids, model, data):
        Move = Pool().get('party.wpqr.bericht1')

        clause = [

            ]


    @classmethod
    def get_context(cls, records, data):
        report_context = super(Bericht1report, cls).get_context(records, data)

        Company = Pool().get('party.wpqr.bericht1')
        company = Company(data['id'])

        report_context['company'] = company
        report_context['wps'] = company.wps.Beleg_Nr
        report_context['prufer'] = company.prufer
        report_context['regel'] = company.regel
        report_context['hersteller'] = company.wpqr_nr
        report_context['beleg'] = company.beleg_nr
        report_context['herst'] = company.hersteller.hersteller
        report_context['datum_schweiss'] = company.datum_schweissen
        report_context['Anscherift'] = company.anschrift
        report_context['ergebnes'] = company.prufergebnisse[0].sichtprufung
        report_context['durch'] = company.prufergebnisse[0].durchprufung
        report_context['eindring'] = company.prufergebnisse[0].eindringprufung
        report_context['ultraprufung'] = company.prufergebnisse[0].ultraprufung
        report_context['magnetprufung'] = company.prufergebnisse[0].magnetprufung
        report_context['macrotest'] =company.mackroskopische
        report_context['microtest'] =company.mickroskopische
        index2 = len(company.Kerbschlabiegepruf1)
        tabb_art = []
        tabb_mass = []
        tabb_anforderung = []
        tabb_richtung = []
        tabb_temperatur = []
        tab_wert1 = []
        tab_wert2 = []
        tab_wert3 = []
        tabb_mittelwert = []
        tabb_bemerkung = []
        for k in range(0,index2):
            tabb_art.append(company.Kerbschlabiegepruf1[k].art)
            tabb_mass.append(company.Kerbschlabiegepruf1[k].masse)
            tabb_anforderung.append(company.Kerbschlabiegepruf1[k].anforderung)
            tabb_richtung.append(company.Kerbschlabiegepruf1[k].kerblage_richtung)
            tabb_temperatur.append(company.Kerbschlabiegepruf1[k].temperature)
            tab_wert1.append(company.Kerbschlabiegepruf1[k].werte1)
            tab_wert2.append(company.Kerbschlabiegepruf1[k].werte2)
            tab_wert3.append(company.Kerbschlabiegepruf1[k].werte3)
            tabb_mittelwert.append(company.Kerbschlabiegepruf1[k].mittelwert)
            tabb_bemerkung.append(company.Kerbschlabiegepruf1[k].Bemerkungen)
        if(index2 == 1):
          report_context['art_']=tabb_art[0]
          report_context['mass_']=tabb_mass[0]
          report_context['anforderung_']=tabb_anforderung[0]
          report_context['richtung_']=tabb_richtung[0]
          report_context['richtung_1']=" "
          report_context['richtung_2']=" "
          report_context['temp_']=tabb_temperatur[0]
          report_context['temp_1']=" "
          report_context['temp_2']=" "
          report_context['wert11']=tab_wert1[0]
          report_context['wert12']=" "
          report_context['wert13']=" "
          report_context['wert21']=tab_wert2[0]
          report_context['wert22']=" "
          report_context['wert23']=" "
          report_context['wert31']=tab_wert3[0]
          report_context['wert32']=" "
          report_context['wert33']=" "
          report_context['mittelwert1']=tabb_mittelwert[0]
          report_context['mittelwert2']=" "
          report_context['mittelwert3']=" "
          report_context['bemerk1']=tabb_bemerkung[0]
          report_context['bemerk2']=" "
          report_context['bemerk3']=" "
        else:
            if(index2 == 2):
              report_context['art_']=tabb_art[0]
              report_context['mass_']=tabb_mass[0]
              report_context['anforderung_']=tabb_anforderung[0]
              report_context['richtung_']=tabb_richtung[0]
              report_context['richtung_1']=tabb_richtung[1]
              report_context['richtung_2']=" "
              report_context['temp_']=tabb_temperatur[0]
              report_context['temp_1']=tabb_temperatur[1]
              report_context['temp_2']=" "
              report_context['wert11']=tab_wert1[0]
              report_context['wert12']=tab_wert1[1]
              report_context['wert13']=" "
              report_context['wert21']=tab_wert2[0]
              report_context['wert22']=tab_wert2[1]
              report_context['wert23']=" "
              report_context['wert31']=tab_wert3[0]
              report_context['wert32']=tab_wert3[1]
              report_context['wert33']=" "
              report_context['mittelwert1']=tabb_mittelwert[0]
              report_context['mittelwert2']=tabb_mittelwert[1]
              report_context['mittelwert3']=" " 
              report_context['bemerk1']=tabb_bemerkung[0]
              report_context['bemerk2']=tabb_bemerkung[1]
              report_context['bemerk3']=" "
            else:
               if(index2 == 3):
                 report_context['art_']=tabb_art[0]
                 report_context['mass_']=tabb_mass[0]
                 report_context['anforderung_']=tabb_anforderung[0]
                 report_context['richtung_']=tabb_richtung[0]
                 report_context['richtung_1']=tabb_richtung[1]
                 report_context['richtung_2']=tabb_richtung[2]
                 report_context['temp_']=tabb_temperatur[0]
                 report_context['temp_1']=tabb_temperatur[1]
                 report_context['temp_2']=tabb_temperatur[2]
                 report_context['wert11']=tab_wert1[0]
                 report_context['wert12']=tab_wert1[1]
                 report_context['wert13']=tab_wert1[2]
                 report_context['wert21']=tab_wert2[0]
                 report_context['wert22']=tab_wert2[1]
                 report_context['wert23']=tab_wert2[2]
                 report_context['wert31']=tab_wert3[0]
                 report_context['wert32']=tab_wert3[1]
                 report_context['wert33']=tab_wert3[2]
                 report_context['mittelwert1']=tabb_mittelwert[0]
                 report_context['mittelwert2']=tabb_mittelwert[1]
                 report_context['mittelwert3']=tabb_mittelwert[2]
                 report_context['bemerk1']=tabb_bemerkung[0]
                 report_context['bemerk2']=tabb_bemerkung[1]
                 report_context['bemerk3']=tabb_bemerkung[2]
               else:
                      report_context['art_']=" "
                      report_context['mass_']=" "
                      report_context['anforderung_']=" "
                      report_context['richtung_']=" "
                      report_context['richtung_1']=" "
                      report_context['richtung_2']=" "
                      report_context['temp_']=" "
                      report_context['temp_1']=" "
                      report_context['temp_2']=" "
                      report_context['wert11']=" "
                      report_context['wert12']=" "
                      report_context['wert13']=" "
                      report_context['wert21']=" "
                      report_context['wert22']=" "
                      report_context['wert23']=" "
                      report_context['wert31']=" "
                      report_context['wert32']=" "
                      report_context['wert33']=" "
                      report_context['mittelwert1']=" "
                      report_context['mittelwert2']=" "
                      report_context['mittelwert3']=" "
                      report_context['bemerk1']=" "
                      report_context['bemerk2']=" "
                      report_context['bemerk3']=" "


        index = len(company.querzugversuch)
  #      index1 = len(company.biegepruf)
        tab_art = []
        tab_re = []
        tab_rm = []
        tab_a = []
        tab_z = []
        tab_bruchlage = []
        tab_bemerk = []
        for i in range(0,index):
            tab_art.append(company.querzugversuch[i].art_nr)
            tab_re.append(company.querzugversuch[i].re)
            tab_rm.append(company.querzugversuch[i].rm)
            tab_a.append(company.querzugversuch[i].a)
            tab_z.append(company.querzugversuch[i].z)
            tab_bruchlage.append(company.querzugversuch[i].bruchlage)
            tab_bemerk.append(company.querzugversuch[i].bemerkung)
            i=i+1
        if(index == 1):
          report_context['art0']=tab_art[0]
          report_context['art1']=" "
          report_context['art2']=" "
          report_context['art3']=" "
          report_context['art4']=" "
          report_context['re0']=tab_re[0]
          report_context['re1']=" "
          report_context['re2']=" "
          report_context['re3']=" "
          report_context['re4']=" "
          report_context['rm0']=tab_rm[0]
          report_context['rm1']=" "
          report_context['rm2']=" "
          report_context['rm3']=" "
          report_context['rm4']=" "
          report_context['a0']=tab_a[0]
          report_context['a1']=" "
          report_context['a2']=" "
          report_context['a3']=" "
          report_context['a4']=" "
          report_context['z0']=tab_z[0]
          report_context['z1']=" "
          report_context['z2']=" "
          report_context['z3']=" "
          report_context['z4']=" "
          report_context['bruchlage0']=tab_bruchlage[0]
          report_context['bruchlage1']=" "
          report_context['bruchlage2']=" "
          report_context['bruchlage3']=" "
          report_context['bruchlage4']=" "
          report_context['bemerkung0']=tab_bemerk[0]
          report_context['bemerkung1']=" "
          report_context['bemerkung2']=" "
          report_context['bemerkung3']=" "
          report_context['bemerkung4']=" "
        else:
            if(index == 2):
              report_context['art0']=tab_art[0]
              report_context['art1']=tab_art[1]
              report_context['art2']=" "
              report_context['art3']=" "
              report_context['art4']=" "
              report_context['re0']=tab_re[0]
              report_context['re1']=tab_re[1]
              report_context['re2']=" "
              report_context['re3']=" "
              report_context['re4']=" "
              report_context['rm0']=tab_rm[0]
              report_context['rm1']=tab_rm[1]
              report_context['rm2']=" "
              report_context['rm3']=" "
              report_context['rm4']=" "
              report_context['a0']=tab_a[0]
              report_context['a1']=tab_a[1]
              report_context['a2']=" "
              report_context['a3']=" "
              report_context['a4']=" "
              report_context['z0']=tab_z[0]
              report_context['z1']=tab_z[1]
              report_context['z2']=" "
              report_context['z3']=" "
              report_context['z4']=" "
              report_context['bruchlage0']=tab_bruchlage[0]
              report_context['bruchlage1']=tab_bruchlage[1]
              report_context['bruchlage2']=" "
              report_context['bruchlage3']=" "
              report_context['bruchlage4']=" "
              report_context['bemerkung0']=tab_bemerk[0]
              report_context['bemerkung1']=tab_bemerk[1]
              report_context['bemerkung2']=" "
              report_context['bemerkung3']=" "
              report_context['bemerkung4']=" "
            else:
              if(index == 3):
                report_context['art0']=tab_art[0]
                report_context['art1']=tab_art[1]
                report_context['art2']=tab_art[2]
                report_context['art3']=" "
                report_context['art4']=" "
                report_context['re0']=tab_re[0]
                report_context['re1']=tab_re[1]
                report_context['re2']=tab_re[2]
                report_context['re3']=" "
                report_context['re4']=" "
                report_context['rm0']=tab_rm[0]
                report_context['rm1']=tab_rm[1]
                report_context['rm2']=tab_rm[2]
                report_context['rm3']=" "
                report_context['rm4']=" "
                report_context['a0']=tab_a[0]
                report_context['a1']=tab_a[1]
                report_context['a2']=tab_a[2]
                report_context['a3']=" "
                report_context['a4']=" "
                report_context['z0']=tab_z[0]
                report_context['z1']=tab_z[1]
                report_context['z2']=tab_z[2]
                report_context['z3']=" "
                report_context['z4']=" "
                report_context['bruchlage0']=tab_bruchlage[0]
                report_context['bruchlage1']=tab_bruchlage[1]
                report_context['bruchlage2']=tab_bruchlage[2]
                report_context['bruchlage3']=" "
                report_context['bruchlage4']=" "
                report_context['bemerkung0']=tab_bemerk[0]
                report_context['bemerkung1']=tab_bemerk[1]
                report_context['bemerkung2']=tab_bemerk[2]
                report_context['bemerkung3']=" "
                report_context['bemerkung4']=" "
              else:
                 if(index == 4):
                   report_context['art0']=tab_art[0]
                   report_context['art1']=tab_art[1]
                   report_context['art2']=tab_art[2]
                   report_context['art3']=tab_art[3]
                   report_context['art4']=" "
                   report_context['re0']=tab_re[0]
                   report_context['re1']=tab_re[1]
                   report_context['re2']=tab_re[2]
                   report_context['re3']=tab_re[3]
                   report_context['re4']=" "
                   report_context['rm0']=tab_rm[0]
                   report_context['rm1']=tab_rm[1]
                   report_context['rm2']=tab_rm[2]
                   report_context['rm3']=tab_rm[3]
                   report_context['rm4']=" "
                   report_context['a0']=tab_a[0]
                   report_context['a1']=tab_a[1]
                   report_context['a2']=tab_a[2]
                   report_context['a3']=tab_a[3]
                   report_context['a4']=" "
                   report_context['z0']=tab_z[0]
                   report_context['z1']=tab_z[1]
                   report_context['z2']=tab_z[2]
                   report_context['z3']=tab_z[3]
                   report_context['z4']=" "
                   report_context['bruchlage0']=tab_bruchlage[0]
                   report_context['bruchlage1']=tab_bruchlage[1]
                   report_context['bruchlage2']=tab_bruchlage[2]
                   report_context['bruchlage3']=tab_bruchlage[3]
                   report_context['bruchlage4']=" "
                   report_context['bemerkung0']=tab_bemerk[0]
                   report_context['bemerkung1']=tab_bemerk[1]
                   report_context['bemerkung2']=tab_bemerk[2]
                   report_context['bemerkung3']=tab_bemerk[3]
                   report_context['bemerkung4']=" "
                 else:
                   if(index == 5):
                      report_context['art0']=tab_art[0]
                      report_context['art1']=tab_art[1]
                      report_context['art2']=tab_art[2]
                      report_context['art3']=tab_art[3]
                      report_context['art4']=tab_art[4]
                      report_context['re0']=tab_re[0]
                      report_context['re1']=tab_re[1]
                      report_context['re2']=tab_re[2]
                      report_context['re3']=tab_re[3]
                      report_context['re4']=tab_re[4]
                      report_context['rm0']=tab_rm[0]
                      report_context['rm1']=tab_rm[1]
                      report_context['rm2']=tab_rm[2]
                      report_context['rm3']=tab_rm[3]
                      report_context['rm4']=tab_rm[4]
                      report_context['a0']=tab_a[0]
                      report_context['a1']=tab_a[1]
                      report_context['a2']=tab_a[2]
                      report_context['a3']=tab_a[3]
                      report_context['a4']=tab_a[4]
                      report_context['z0']=tab_z[0]
                      report_context['z1']=tab_z[1]
                      report_context['z2']=tab_z[2]
                      report_context['z3']=tab_z[3]
                      report_context['z4']=tab_z[4]
                      report_context['bruchlage0']=tab_bruchlage[0]
                      report_context['bruchlage1']=tab_bruchlage[1]
                      report_context['bruchlage2']=tab_bruchlage[2]
                      report_context['bruchlage3']=tab_bruchlage[3]
                      report_context['bruchlage4']=tab_bruchlage[4]
                      report_context['bemerkung0']=tab_bemerk[0]
                      report_context['bemerkung1']=tab_bemerk[1]
                      report_context['bemerkung2']=tab_bemerk[2]
                      report_context['bemerkung3']=tab_bemerk[3]
                      report_context['bemerkung4']=tab_bemerk[4]
                   else:
                      report_context['art0']=" "
                      report_context['art1']=" "
                      report_context['art2']=" "
                      report_context['art3']=" "
                      report_context['art4']=" "
                      report_context['re0']=" "
                      report_context['re1']=" "
                      report_context['re2']=" "
                      report_context['re3']=" "
                      report_context['re4']=" "
                      report_context['rm0']=" "
                      report_context['rm1']=" "
                      report_context['rm2']=" "
                      report_context['rm3']=" "
                      report_context['rm4']=" "
                      report_context['a0']=" "
                      report_context['a1']=" "
                      report_context['a2']=" "
                      report_context['a3']=" "
                      report_context['a4']=" "
                      report_context['z0']=" "
                      report_context['z1']=" "
                      report_context['z2']=" "
                      report_context['z3']=" "
                      report_context['z4']=" "
                      report_context['bruchlage0']=" "
                      report_context['bruchlage1']=" "
                      report_context['bruchlage2']=" "
                      report_context['bruchlage3']=" "
                      report_context['bruchlage4']=" "
                      report_context['bemerkung0']=" "
                      report_context['bemerkung1']=" "
                      report_context['bemerkung2']=" "
                      report_context['bemerkung3']=" "
                      report_context['bemerkung4']=" "
        index4 = len(company.biegepruf1)
        tab_art1 = []
        tab_biegewinkel = []
        tab_dom = []
        tab_dehnung = []
        tab_ergebnisse = []
        for w in range(0,index4):
            tab_art1.append(company.biegepruf1[w].art_nr)
            tab_biegewinkel.append(company.biegepruf1[w].biege_winkel)
            tab_dom.append(company.biegepruf1[w].biegedorn)
            tab_dehnung.append(company.biegepruf1[w].dehnung)
            tab_ergebnisse.append(company.biegepruf1[w].ergebnisse)
            w=w+1
        if(index4 == 1):
          report_context['art10']=tab_art1[0]
          report_context['art11']=" "
          report_context['art12']=" "
          report_context['art13']=" "
          report_context['art14']=" "
          report_context['tab_biegewinkel0']=tab_biegewinkel[0]
          report_context['tab_biegewinkel1']=" "
          report_context['tab_biegewinkel2']=" "
          report_context['tab_biegewinkel3']=" "
          report_context['tab_biegewinkel4']=" "
          report_context['dom0']=tab_dom[0]
          report_context['dom1']=" "
          report_context['dom2']=" "
          report_context['dom3']=" "
          report_context['dom4']=" "
          report_context['dehnung0']=tab_dehnung[0]
          report_context['dehnung1']=" "
          report_context['dehnung2']=" "
          report_context['dehnung3']=" "
          report_context['dehnung4']=" "
          report_context['ergebnis0']=tab_ergebnisse[0]
          report_context['ergebnis1']=" "
          report_context['ergebnis2']=" "
          report_context['ergebnis3']=" "
          report_context['ergebnis4']=" "
        else:
            if(index4 == 2):
              report_context['art10']=tab_art1[0]
              report_context['art11']=tab_art1[1]
              report_context['art12']=" "
              report_context['art13']=" "
              report_context['art14']=" "
              report_context['tab_biegewinkel0']=tab_biegewinkel[0]
              report_context['tab_biegewinkel1']=tab_biegewinkel[1]
              report_context['tab_biegewinkel2']=" "
              report_context['tab_biegewinkel3']=" "
              report_context['tab_biegewinkel4']=" "
              report_context['dom0']=tab_dom[0]
              report_context['dom1']=tab_dom[1]
              report_context['dom2']=" "
              report_context['dom3']=" "
              report_context['dom4']=" "
              report_context['dehnung0']=tab_dehnung[0]
              report_context['dehnung1']=tab_dehnung[1]
              report_context['dehnung2']=" "
              report_context['dehnung3']=" "
              report_context['dehnung4']=" "
              report_context['ergebnis0']=tab_ergebnisse[0]
              report_context['ergebnis1']=tab_ergebnisse[1]
              report_context['ergebnis2']=" "
              report_context['ergebnis3']=" "
              report_context['ergebnis4']=" "
            else:
                if(index4 == 3):
                  report_context['art10']=tab_art1[0]
                  report_context['art11']=tab_art1[1]
                  report_context['art12']=tab_art1[2]
                  report_context['art13']=" "
                  report_context['art14']=" "
                  report_context['tab_biegewinkel0']=tab_biegewinkel[0]
                  report_context['tab_biegewinkel1']=tab_biegewinkel[1]
                  report_context['tab_biegewinkel2']=tab_biegewinkel[2]
                  report_context['tab_biegewinkel3']=" "
                  report_context['tab_biegewinkel4']=" "
                  report_context['dom0']=tab_dom[0]
                  report_context['dom1']=tab_dom[1]
                  report_context['dom2']=tab_dom[2]
                  report_context['dom3']=" "
                  report_context['dom4']=" "
                  report_context['dehnung0']=tab_dehnung[0]
                  report_context['dehnung1']=tab_dehnung[1]
                  report_context['dehnung2']=tab_dehnung[2]
                  report_context['dehnung3']=" "
                  report_context['dehnung4']=" "
                  report_context['ergebnis0']=tab_ergebnisse[0]
                  report_context['ergebnis1']=tab_ergebnisse[1]
                  report_context['ergebnis2']=tab_ergebnisse[2]
                  report_context['ergebnis3']=" "
                  report_context['ergebnis4']=" "
                else:
                  if(index4 == 4):
                     report_context['art10']=tab_art1[0]
                     report_context['art11']=tab_art1[1]
                     report_context['art12']=tab_art1[2]
                     report_context['art13']=tab_art1[3]
                     report_context['art14']=" "
                     report_context['tab_biegewinkel0']=tab_biegewinkel[0]
                     report_context['tab_biegewinkel1']=tab_biegewinkel[1]
                     report_context['tab_biegewinkel2']=tab_biegewinkel[2]
                     report_context['tab_biegewinkel3']=tab_biegewinkel[3]
                     report_context['tab_biegewinkel4']=" "
                     report_context['dom0']=tab_dom[0]
                     report_context['dom1']=tab_dom[1]
                     report_context['dom2']=tab_dom[2]
                     report_context['dom3']=tab_dom[3]
                     report_context['dom4']=" "
                     report_context['dehnung0']=tab_dehnung[0]
                     report_context['dehnung1']=tab_dehnung[1]
                     report_context['dehnung2']=tab_dehnung[2]
                     report_context['dehnung3']=tab_dehnung[3]
                     report_context['dehnung4']=" "
                     report_context['ergebnis0']=tab_ergebnisse[0]
                     report_context['ergebnis1']=tab_ergebnisse[1]
                     report_context['ergebnis2']=tab_ergebnisse[2]
                     report_context['ergebnis3']=tab_ergebnisse[3]
                     report_context['ergebnis4']=" "
                  else:
                   if(index4 == 5):
                     report_context['art10']=tab_art1[0]
                     report_context['art11']=tab_art1[1]
                     report_context['art12']=tab_art1[2]
                     report_context['art13']=tab_art1[3]
                     report_context['art14']=tab_art1[4]
                     report_context['tab_biegewinkel0']=tab_biegewinkel[0]
                     report_context['tab_biegewinkel1']=tab_biegewinkel[1]
                     report_context['tab_biegewinkel2']=tab_biegewinkel[2]
                     report_context['tab_biegewinkel3']=tab_biegewinkel[3]
                     report_context['tab_biegewinkel4']=tab_biegewinkel[4]
                     report_context['dom0']=tab_dom[0]
                     report_context['dom1']=tab_dom[1]
                     report_context['dom2']=tab_dom[2]
                     report_context['dom3']=tab_dom[3]
                     report_context['dom4']=tab_dom[4]
                     report_context['dehnung0']=tab_dehnung[0]
                     report_context['dehnung1']=tab_dehnung[1]
                     report_context['dehnung2']=tab_dehnung[2]
                     report_context['dehnung3']=tab_dehnung[3]
                     report_context['dehnung4']=tab_dehnung[4]
                     report_context['ergebnis0']=tab_ergebnisse[0]
                     report_context['ergebnis1']=tab_ergebnisse[1]
                     report_context['ergebnis2']=tab_ergebnisse[2]
                     report_context['ergebnis3']=tab_ergebnisse[3]
                     report_context['ergebnis4']=tab_ergebnisse[4]
                   else:
                     report_context['art10']=" "
                     report_context['art11']=" "
                     report_context['art12']=" "
                     report_context['art13']=" "
                     report_context['art14']=" "
                     report_context['tab_biegewinkel0']=" "
                     report_context['tab_biegewinkel1']=" "
                     report_context['tab_biegewinkel2']=" "
                     report_context['tab_biegewinkel3']=" "
                     report_context['tab_biegewinkel4']=" "
                     report_context['dom0']=" "
                     report_context['dom1']=" "
                     report_context['dom2']=" "
                     report_context['dom3']=" "
                     report_context['dom4']=" "
                     report_context['dehnung0']=" "
                     report_context['dehnung1']=" "
                     report_context['dehnung2']=" "
                     report_context['dehnung3']=" "
                     report_context['dehnung4']=" "
                     report_context['ergebnis0']=" "
                     report_context['ergebnis1']=" "
                     report_context['ergebnis2']=" "
                     report_context['ergebnis3']=" "
                     report_context['ergebnis4']=" "

        return report_context





# Listeneintrag  class
class listeneintrag(DeactivableMixin, ModelView, ModelSQL, MultiValueMixin):
    'Party WPQR LISTENEINTRAG'
    __name__ = 'party.listeneintrag'
    hersteller = fields.Char('Hersteller')
    anschrift = fields.Char('Anschrift')
    title1 = fields.Char('Prüfungsbescheinigung')
    title2 = fields.Char('Qualifizierungssumfang')
  

    nummer1 = fields.Function(fields.Char("Nummer"),"on_change_grundwerkstoff3")
    nummer2 = fields.Function(fields.Char("Nummer"),"on_change_grundwerkstoff4")

    space1 = fields.Char(' ')
    sonstige = fields.Text('Sonstige Angaben')
    ort = fields.Function(fields.Char("Ort"),"on_change_prufer")
    datum_ausstellung = fields.Date("Datum der Ausstellung")
    unterschrift = fields.Selection([
        ('Dipl.Ing. Prüfer', 'Dipl.Ing. Prüfer'),
        ('Dipl.Ing. Schulz', 'Dipl.Ing. Schulz'),
        ('Dipl.Ing. Tester', 'Dipl.Ing. Tester'),
        ('Dipl.Ing. Zertifizierer', 'Dipl.Ing. Zertifizierer'),
        ('P.L Van Fosson', 'P.L Van Fosson'),
    ], 'Name, Datum und Unterschrift', readonly = False,
        )
    index1 = fields.Char('Hinweis')
    test = "Hinweis"
    index2 = fields.Char('Die Qualifizierung(Anerkennung)kan nicht gedruckt werden')
    index3 = fields.Char('Die Qualifizierung(Anerkennung) erscheint jedoch in der Liste und im Menü')

    gultig_bis = fields.Date("gültig bis")
    bereich = fields.Char("Bereich")
    int_nr = fields.Function(fields.Char("Int.Nr"),"get_automatic_id")
    formular = fields.Selection([
        ('WPQR', 'WPQR | ISO 15607 bis ISO 15614'),
        ('WPAR', 'WPAR | Normenreihe EN 288 '),
        ('WPQR-D', 'WPQR-D | ISO 14555 Anhang D, 783, 784'),
        ('WPQR-E', 'WPQR-E | ISO 14555 Anhang E, 785, 786'),
        ('BPAR', 'BPAR | EN 13134 Hartlöten'),
        ('PQR', 'PQR | ASME BPVC, Section IX,QW-483'),
    ], 'Formular', readonly = False,
        )


    beleg_hersteller = fields.Function(fields.Char("Beleg-Nr. des Herstellers"),"on_change_andere")
    regel = fields.Selection([
        ('iso15614-1', 'ISO 15614-1 | Schweißverfahrensprüfung - Teil1 : Stähle und Nickel'),
        ('iso15614-2', 'ISO 15614-2 | Schweißverfahrensprüfung - Teil2 : Aluminium und seinen Legierungen'),
        ('iso15614-3', 'ISO 15614-3 | Schweißverfahrensprüfung - Teil3 : Unlegiertes u. niedrig leg. Gusseisen'),
        ('iso15614-4', 'ISO 15614-4 | Schweißverfahrensprüfung - Teil4 : Ferigungsschweißen Aluminiumguss'),
        ('iso15614-5', 'ISO 15614-5 | Schweißverfahrensprüfung - Teil5 : Titan, Zirkonium und ihren Leg'),
        ('iso15614-6', 'ISO 15614-6 | Schweißverfahrensprüfung - Teil6 : Kupfer und seinen Legierungen'),
        ('iso15614-7', 'ISO 15614-7 | Schweißverfahrensprüfung - Teil7 : Auftragschweißen'),
        ('iso15614-8', 'ISO 15614-8 | Schweißverfahrensprüfung - Teil8 : Rohre in Rorhböden'),
        ('iso15614-9', 'ISO 15614-9 | Schweißverfahrensprüfung - Teil9 : Nassschweißen unter Überduck'),
        ('iso15614-10', 'ISO 15614-10 | Schweißverfahrensprüfung - Teil10 : Trockenschweißen unter Überduck'),
        ('iso15610', 'ISO 15610 Qualifizierung durch den Einsatz von geprüften Schweißzusätzen'),
        ('iso15611', 'ISO 15611 Qualifizierung aufgrund von vorliegender schweißtechnischer Erfahrung'),
        ('iso15612', 'ISO 15612 Qualifizierung durch Einsatz eines standardschweißverfahrens'),
        ('iso15613', 'ISO 15613 Qualifizierung aufgrund einer vorgezogenen Arbeitsprüfung'),
    ], 'Regel/Prüfnorm', readonly = False,
        )

    schweißprocess = fields.Selection([
         ('--', '--'),
        ('111', '111 Lichtbogenhandschweißen'),
        ('111/121', '111/121 Wurzel E, Auffüllen mit UP (Stahl)'),
        ('111/135', '111/135 Wurzel E, Auffüllen mit MAG (Stahl)'),
        ('112', '112 Schwerkraft-Lichtbogenschweißen'),
        ('114', '114 Metall-Lichtbogenschweißen mit Fülldrahtelektrode ohne Schutzgas'),
        ('12', '12 Unterpulverschweißen'),
        ('121','121 Unterpulverschweißen mit Massivdrahtelektrode'),
        ('122', '122 Unterpulverschweißen mit Massivbandelektrode'),
        ('124', '124 Unterpulverschweißen mit Metallpulverzusatz'),
        ('125', '125 Unterpulverschweißen mit Fülldrahtelektrode'),
        ('126', '126 Unterpulverschweißen mit Füllbandelektrode '),
        ('131', '131 Metall-Inertgasschweißen mit Massivdrahtelektrode'),
        ('132', '132 Metall-Inertgasschweißen mit schweißpulvergefüllter Drahtelektrode'),
        ('133', '133 Metall-Inertgasschweißen mit metallpulvergefüllter Drahtelektrode'),
        ('135', '135 Metall-Aktivgasschweißen mit Massivdrahtelektrode'),
        ('135/111','135/111 Wurzel MAG, Auffüllen mit  E (Stahl)'),
        ('135/121', '135/121 Wurzel MAG, Auffüllen mit  UP (Stahl)'),
        ('136', '136 Metall-Aktivgasschweißen mit schweißpulvergefüllter Drahtelektrode'),
        ('136/121', '136/121 Wurzel MAG, Auffüllen mit  UP (Stahl)'),
        ('138', '138 Metall-Aktivgasschweißen mit metallpulvergefüllter Drahtelektrode'),
        ('141', '141 Wolfram-Inertgasschweißen mit Massivdraht- oder Massivstabzusatz'),
        ('141/111', '141/111  Wurzel WIG, Auffüllen mit  E (Stahl, Cu, Ni)'),
        ('141/121', '141/121 Wurzel WIG, Auffüllen mit  UP (Stahl, Ni)'),
        ('141/131', '141/131 Wurzel WIG, Auffüllen mit  MIG (Al, Cu, Ni, Ti)'),
        ('141/135', '141/135 Wurzel WIG, Auffüllen mit  MAG (Stahl, Ni)'),
        ('141/136', '141/136 Wurzel WIG, Auffüllen mit  MAG (Stahl)'),
        ('142', '142 Wolfram-Inertgasschweißen ohne Schweißzusatz'),
        ('143', '143 Wolfram-Inertgasschweißen mit Fülldraht- oder Füllstabzusatz'),
        ('145', '145 WIG-Schweißen mit reduzierenden Gasanteilen und Massivzusatz(Draht/Stab)'),
        ('146','146 WIG-Schweißen  mit reduzierenden Gasanteilen und Füllzusatz(Draht/Stab)'),
        ('147', '147 Wolfram-Schutzgasschweißen mit aktiven Gesanteilen im inerten Schutzgas'),
        ('15', '15 Plasmaschweißen'),
        ('151', '151 Plasma-Metall-Inertgasschweißen'),
        ('152', '152 Pulver-Plasmalichtbogenschweißen'),
        ('311', '311 Gasschweißen mit Sauerstoff-Acetylen-Flamme'),
        ('312', '312 Gasschweißen mit Sauerstoff-Propan-Flamme'),
        ('313', '313 Gasschweißen mit Sauerstoff-Wasserstoff-Flamme'),
        ('42', '42 Reibschweißen'),
        ('51', '51 Elektronenstrahlschweißen'),
        ('511', '511 Elektronenstrahlschweißen unter Vakuum'),
        ('512', '512 Elektronenstrahlschweißen in Atmosphäre'),
        ('52', '52 Laserstrahlschweißen'),
        ('521', '521 Festkörper-Laserstrahlschweißen'),
        ('522', '522 Gas-Laserstrahlschweißen'),
        ('522+15', '522+15 Hybridschweißen:Laser-und Plasmaschweißen'),
        ('523', '523 Dioden-Laserstrahlschweißen, Halbleiter-Laserschweißen'),
        ('72', '72 Elektroschlackeschweißen'),
        ('721', '721 Elektroschlackeschweißen mit Bandelektrode'),
        ('722', '722 Elektroschlackeschweißen mit Drahtelektrode'),
        ('78', '78 Bolzenschweißen'),
        ('783', '783 Hubzündungs-Bolzenschweißen mit keramikring oder Schutzgas'),
        ('784', '784 kurzzeit-Bolzenschweißen mit Hubzündung'),
        ('785', '785 Kondensatorentladungs-Bolzenschweißen mit Hubzündung'),
        ('786', '786 Kondensatorentladungs-Bolzenschweißen mit Spitzenzündung'),
        ('787', '787 Bolzenschweißen mit Ringzündung'),
        ('91', '91 Hartlöten mit örtlich begrenzter Erwärmung'),
        ('911', '911 Infrarothartlöten'),
        ('912', '912 Flammhartlöten'),
        ('913', '913 Laserstrahlhartlöten'),
        ('914', '914 Elektronenstrahlhartlöten'),
        ('916', '916 Induktionshartlöten'),
        ('918', '918 Widerstandshartlöten'),
        ('919', '919 Diffusionshartlöten'),
        ('92', '92 Hartlöten mit vollständiger Erwärmung'),
        ('921', '921 Ofenhartlöten'),
        ('922', '922 Vakuumhartlöten'),
        ('923', '923 Lötbadhartlöten'),
        ('924', '924 Salzbadhartlöten'),
        ('925', '925 Flussmittelbadhartlöten'),
        ('926', '926 Tauchbadhartlöten'),
        ('93', '93 andere Hartlötverfahren'),
    ], 'Schweißprozess(e)', readonly = False,
        )
    schweißprocess_gel = fields.Function(fields.Char("Geltungs"),"On_change_schweissprocess")

    space = fields.Char('                                                                                                                                                                                              ')
    prufer_prufstelle = fields.Selection([
        ('DGZfP', 'DGZfP-Ausbildungszentrum Wittenberge'),
        ('Harrison', 'Harrison Mechanical Corporation'),
        ('MAN-Technologie', 'MAN-Technologie, Oberpfaffenhofen, Abtlg.WOP'),
    ], 'Prüfers oder Prüfstelle', readonly = False,
        )
    beleg_nr = fields.Char("Beleg-Nr")

    def get_automatic_id(self,id):
      return self.id

    @staticmethod
    def default_index1():
      return "Hinweis"

    @staticmethod
    def default_index2():
      return "Die Qualifizierung(Anerkennung)kan nicht gedruckt werden"

    @staticmethod
    def default_index3():
      return "Die Qualifizierung(Anerkennung) erscheint jedoch in der Liste und im Menü"

    def on_change_prufer(self,prufer_prufstelle):
      if(self.prufer_prufstelle == "DGZfP"):
         return "Wittenberge"
      if(self.prufer_prufstelle == "Harrison"):
         return "New York, NY"
      if(self.prufer_prufstelle == "MAN-Technologie"):
         return "Weßling"
      else:
         return " "
    def on_change_grundwerkstoff11(self,grundwerkstoff1):
      if(self.grundwerkstoff1 is not None):
        return self.grundwerkstoff1.Werkstoffgruppe
      else:
        return " "


    def on_change_andere(self,regel):
      return "ISO "+str(self.regel)+" "+str(self.schweißprocess)+" "+str(self.id)
    def On_change_schweissprocess(self,schweißprocess):
       if(self.schweißprocess == "111"):
          return "Lichtbogenhandschweißen (E)"
       if(self.schweißprocess == "111/135"):
          return "Wurzel E, Auffüllen mit MAG (Stahl)(E/MAG)"
       if(self.schweißprocess == "112"):
          return "Schwerkraft-Lichtbogenschweißen (SK)"
       if(self.schweißprocess == "114"):
          return "Metall-Lichtbogenschweißen mit Fülldrahtelektrode ohne Schutzgas (MF)"
       if(self.schweißprocess == "12"):
          return "Unterpulverschweißen (UP)"
       if(self.schweißprocess == "121"):
          return "Unterpulverschweißen mit Massivdrahtelektrode (UP)"
       if(self.schweißprocess == "122"):
          return "Unterpulverschweißen mit Massivbandelektrode (UP)"
       if(self.schweißprocess == "124"):
          return "Unterpulverschweißen mit Metallpulverzusatz (UP)"
       if(self.schweißprocess == "125"):
          return "Unterpulverschweißen mit Fülldrahtelektrode (UP)"
       if(self.schweißprocess == "126"):
          return "Unterpulverschweißen mit Füllbandelektrode (UP)"
       if(self.schweißprocess == "131"):
          return "Metall-Inertgasschweißen mit Massivdrahtelektrode (MIG)"
       if(self.schweißprocess == "132"):
          return "Metall-Inertgasschweißen mit schweißpulvergefüllter Drahtelektrode(MIG)"
       if(self.schweißprocess == "133"):
          return "Metall-Inertgasschweißen mit metallpulvergefüllter Drahtelektrode (MIG)"
       if(self.schweißprocess == "135"):
          return "Metall-Aktivgasschweißen mit Massivdrahtelektrode(MAG)"
       if(self.schweißprocess == "135/111"):
          return "Wurzel MAG, Auffüllen mit  E (Stahl)(MAG/E)"
       if(self.schweißprocess == "135/121"):
          return "Wurzel MAG, Auffüllen mit UP (Stahl)(MAG/UP)"
       if(self.schweißprocess == "136"):
          return "Metall-Aktivgasschweißen mit schweißpulvergefüllter Drahtelektrode (MAG)"
       if(self.schweißprocess == "136/121"):
          return "Wurzel MAG, Auffüllen mit  UP (Stahl)"
       if(self.schweißprocess == "138"):
          return "Metall-Aktivgasschweißen mit metallpulvergefüllter Drahtelektrode"
       if(self.schweißprocess == "141"):
          return "Wolfram-Inertgasschweißen mit Massivdraht- oder Massivstabzusatz"
       if(self.schweißprocess == "141/111"):
          return "Wurzel WIG, Auffüllen mit  E (Stahl, Cu, Ni)"
       if(self.schweißprocess == "141/121"):
          return "Wurzel WIG, Auffüllen mit  UP (Stahl, Ni)"
       if(self.schweißprocess == "141/131"):
          return "Wurzel WIG, Auffüllen mit  MIG (Al, Cu, Ni, Ti)(WIG/MIG)"
       if(self.schweißprocess == "141/135"):
          return "Wurzel WIG, Auffüllen mit  MAG (Stahl, Ni)(WIG/MAG)"
       if(self.schweißprocess == "141/136"):
          return "Wurzel WIG, Auffüllen mit  MAG (Stahl)(WIG/MAG)"
       if(self.schweißprocess == "142"):
          return "Wolfram-Inertgasschweißen ohne Schweißzusatz (WIG)"
       if(self.schweißprocess == "143"):
          return "Wolfram-Inertgasschweißen mit Fülldraht- oder Füllstabzusatz (WIG)"
       if(self.schweißprocess == "145"):
          return "WIG-Schweißen mit reduzierenden Gasanteilen und Massivzusatz(Draht/Stab)"
       if(self.schweißprocess == "146"):
          return "WIG-Schweißen mit reduzierenden Gasanteilen und Füllzusatz(Draht/Stab)"
       if(self.schweißprocess == "147"):
          return "Wolfram-Schutzgasschweißen mit aktiven Gesanteilen im inerten Schutzgas"
       if(self.schweißprocess == "15"):
          return "Plasmaschweißen (WPL)"
       if(self.schweißprocess == "151"):
          return "Plasma-Metall-Inertgasschweißen"
       if(self.schweißprocess == "152"):
          return "Pulver-Plasmalichtbogenschweißen"
       if(self.schweißprocess == "311"):
          return "Gasschweißen mit Sauerstoff-Acetylen-Flamme"
       if(self.schweißprocess == "312"):
          return "Gasschweißen mit Sauerstoff-Propan-Flamme"
       if(self.schweißprocess == "313"):
          return "Gasschweißen mit Sauerstoff-Wasserstoff-Flamme"

       else:
         if(self.schweißprocess == "111/121"):
           return "Wurzel E, Auffüllen mit UP (Stahl)(E/UP)"


#Material Class
class material1(DeactivableMixin, sequence_ordered(), ModelSQL, ModelView):
    'Party WPQR MATERIAL1'
    __name__ = 'party.matrial1'
    name = fields.Char('Name EN')
    p_no = fields.Char('P-No')
    gr_no = fields.Char('Gr-No')
    wst_nr = fields.Char('Wst-Nr')

#fm1 Class
class fm1(DeactivableMixin, sequence_ordered(), ModelSQL, ModelView):
    'Party WPQR FM'
    __name__ = 'party.fm1'
    classification = fields.Char('Classification')
    sfa = fields.Char('SFA')
    trade_name = fields.Char('Trade name')
    manufacture = fields.Char('Manufacturer')
    eignung = fields.Char('Eignung')

    def get_rec_name(self,classification):
      return self.classification

#Toughness Class
class toughness(DeactivableMixin, ModelView, ModelSQL, MultiValueMixin):
    'Party TOUGHNESS TEST'
    __name__ = 'party.toughness'
    specimen = fields.Char('Specimen No.')
    notch = fields.Char('Notch Location')
    specimen_size = fields.Char('Specimen Size')
    test_temperatur = fields.Char('Test temperature')
    impact_val1 = fields.Char('Impact Values(ft-lb or J)')
    impact_val2 = fields.Char('Impact Values(%Shear)')
    impact_val3 = fields.Char('Impact Values(Mils(in)or mm)')
    drop_weight = fields.Char('Drop Weight Break(Y/N)')
    link_toughness = fields.Many2One('party.wpqr.qw483', 'qw3', required=True,
        ondelete='CASCADE', states=STATES, select=True, depends=DEPENDS)



#Tensile Class
class tensile(DeactivableMixin, ModelView, ModelSQL, MultiValueMixin):
    'Party TENSILE TEST'
    __name__ = 'party.tensile'
    specimen = fields.Char('Specimen No.')
    width = fields.Char('Width')
    thickness = fields.Char('Thickness')
    area = fields.Char('Area')
    ultimate = fields.Char('Ultimate Total Load')
    ultimate2 = fields.Char('Ultimate Unit Stress, (psi or MPa)')
    type = fields.Char('Type of Failure and Location')

    link_qw483 = fields.Many2One('party.wpqr.qw483', 'qw1', required=True,
        ondelete='CASCADE', states=STATES, select=True, depends=DEPENDS)

class guidedbend(DeactivableMixin, ModelView, ModelSQL, MultiValueMixin):
    'Party GUIDED BEND'
    __name__ = 'party.bend'
    type_figure = fields.Char('Type and Figure No.')
    result = fields.Char('Result')
    link_guide = fields.Many2One('party.wpqr.qw483', 'qw2', required=True,
        ondelete='CASCADE', states=STATES, select=True, depends=DEPENDS)

#QW-483(Back)class
class qw483(DeactivableMixin, ModelView, ModelSQL, MultiValueMixin):
    'Party WPQR_QW483'
    __name__ = 'party.wpqr.qw483'
    result_satisfactory_yes = fields.Char('Result-Satisfactory : Yes')
    result_satisfactory_no = fields.Char('No')
    penetration_yes = fields.Char('Penetration into Parent Metal : Yes')
    penetration_no = fields.Char('No')
    space = fields.Char('                                                                                                                                                                                                                                         ')
    space2 = fields.Char("                                    ")
    pqr = fields.Function(fields.Char("PQR No."),"get_automatic_pqr")
    tensile = fields.One2Many('party.tensile','link_qw483','Tensile Test(QW-150)')
    guide = fields.One2Many('party.bend','link_guide','Guided-Bend Tests(QW-160)')
    toughness = fields.One2Many('party.toughness','link_toughness','Toughness Tests(QW-170)')
    comment = fields.Char('Comments')
    titre1 = fields.Char('Fillet-Welt Test(QW-180)',required=True)
    makro_res = fields.Char('Macro-Results')
    titre2 = fields.Char('Other Tests',required=True)
    type_test = fields.Char('Type of Test')
    deposit_analysis = fields.Char('Deposit Analysis')
    other = fields.Text('Other')
    welds_name = fields.Char('Welders Name')
    clock_num = fields.Char('Clock No')
    stamp_num = fields.Char('Stamp No')
    test_conducted = fields.Char('Tests conducted by')
    laboratory = fields.Char('Laboratory Test No.')
    title3 = fields.Text('We certify that the statements in this record are correct and that the test welds were prepared, welded and tested in accordance with the requirements of Section IX of the ASME Boiler and Pressure Vessel Code.')
    organisation = fields.Function(fields.Char('Organization'),"get_automatic_organisation")
    organisation_anschrift = fields.Function(fields.Char('Organization'),"get_automatic_anschrift")
    date = fields.Function(fields.Char('Date'),"get_automatic_date")
    certified_by = fields.Char('Certified by')
    detail = fields.Char('(Detail of record of tests are illustrative only and may be modified to conform to the type and number of tests required by the Code.)')

    @classmethod
    def __setup__(cls):
      super(qw483, cls).__setup__()
      cls._buttons.update({
          'Print': {},
          })

    @classmethod
    @ModelView.button
    @ModelView.button_action('welding_certification.report_qw483')
    def Print(cls, qw483):
       pass

    def get_automatic_date(self,comment):
          Party = Pool().get('party.wpqr6')
          party, = Party.search([
                 ('qw483', '=', self.id),
                 ])
          return party.Date

    def get_automatic_pqr(self,comment):
          Party = Pool().get('party.wpqr6')
          party, = Party.search([
                 ('qw483', '=', self.id),
                 ])
          return party.wps_nr


    def get_automatic_anschrift(self,comment):
          Party = Pool().get('party.wpqr6')
          party, = Party.search([
                 ('qw483', '=', self.id),
                 ])
          return party.organisation_anschrift

    def get_automatic_organisation(self,comment):
          Party = Pool().get('party.wpqr6')
          party, = Party.search([
                 ('qw483', '=', self.id),
                 ])
          return party.organisation



    def do_Print(self, action):
        data = {
            'id': self.id,
            }
        return action, data


    def get_rec_name(self,penetration_no):
      return "QW -483(Back)Sheet 2of2"
    @staticmethod
    def default_titre1():
       return " "

    @staticmethod
    def default_titre2():
       return " "


#report fur wq
class wq483report(Report):
    __name__ = 'welding_certification.party.wq483_report'



    @classmethod
    def _get_records(cls, ids, model, data):
        Move = Pool().get('party.wpqr.qw483')

        clause = [

            ]


    @classmethod
    def get_context(cls, records, data):
        report_context = super(wq483report, cls).get_context(records, data)

        Zertifikat = Pool().get('party.wpqr.qw483')
        zertifikat = Zertifikat(data['id'])

        report_context['zertifikat'] = zertifikat
        report_context['comment'] = zertifikat.comment
        report_context['laboratory'] = zertifikat.laboratory
        report_context['organisation'] = zertifikat.organisation
        report_context['organisation_anschrift'] = zertifikat.organisation_anschrift
        report_context['pqr'] = zertifikat.pqr
        report_context['result_satisfactory_yes'] = zertifikat.result_satisfactory_yes
        report_context['result_satisfactory_no'] = zertifikat.result_satisfactory_no
        report_context['penetration_yes'] = zertifikat.penetration_yes
        report_context['penetration_no'] = zertifikat.penetration_no
        report_context['makro_res'] = zertifikat.makro_res
        report_context['type_test'] = zertifikat.type_test
        report_context['deposit_analysis'] = zertifikat.deposit_analysis
        report_context['other'] = zertifikat.other
        report_context['weld_name'] = zertifikat.welds_name
        report_context['clock_no'] = zertifikat.clock_num
        report_context['stamp'] = zertifikat.stamp_num
        report_context['test_conducted'] = zertifikat.test_conducted
        report_context['laboratory'] = zertifikat.laboratory
        report_context['date'] = zertifikat.date
        report_context['certified'] = zertifikat.certified_by
        indx_1 = len(zertifikat.tensile)
        indx_2 = len(zertifikat.guide)
        indx_3 = len(zertifikat.toughness)

        tab_specim_t = []
        tab_location_t = []
        tab_size_t = []
        tab_temp_t = []
        tab_ft_t = []
        tab_shear_t = []
        tab_mils_t = []
        tab_weight_t = []

        for k in range(0,indx_3):
            tab_specim_t.append(zertifikat.toughness[k].specimen)
            tab_location_t.append(zertifikat.toughness[k].notch)
            tab_size_t.append(zertifikat.toughness[k].specimen_size)
            tab_temp_t.append(zertifikat.toughness[k].test_temperatur)
            tab_ft_t.append(zertifikat.toughness[k].impact_val1)
            tab_shear_t.append(zertifikat.toughness[k].impact_val2)
            tab_mils_t.append(zertifikat.toughness[k].impact_val3)
            tab_weight_t.append(zertifikat.toughness[k].drop_weight)

        if(indx_3 == 1):
           report_context['specimen_t_0'] = tab_specim_t[0]
           report_context['specimen_t_1'] = " "
           report_context['specimen_t_2'] = " "
           report_context['specimen_t_3'] = " "
           report_context['specimen_t_4'] = " "
           report_context['specimen_t_5'] = " "
           report_context['specimen_t_6'] = " "
           report_context['specimen_t_7'] = " "
           report_context['specimen_t_8'] = " "
           report_context['location_t_0'] = tab_location_t[0]
           report_context['location_t_1'] = " "
           report_context['location_t_2'] = " "
           report_context['location_t_3'] = " "
           report_context['location_t_4'] = " "
           report_context['location_t_5'] = " "
           report_context['location_t_6'] = " "
           report_context['location_t_7'] = " "
           report_context['location_t_8'] = " "
           report_context['size_t_0'] = tab_size_t[0]
           report_context['size_t_1'] = " "
           report_context['size_t_2'] = " "
           report_context['size_t_3'] = " "
           report_context['size_t_4'] = " "
           report_context['size_t_5'] = " "
           report_context['size_t_6'] = " "
           report_context['size_t_7'] = " "
           report_context['size_t_8'] = " "
           report_context['temp_t_0'] = tab_temp_t[0]
           report_context['temp_t_1'] = " "
           report_context['temp_t_2'] = " "
           report_context['temp_t_3'] = " "
           report_context['temp_t_4'] = " "
           report_context['temp_t_5'] = " "
           report_context['temp_t_6'] = " "
           report_context['temp_t_7'] = " "
           report_context['temp_t_8'] = " "
           report_context['ft_t_0'] = tab_ft_t[0]
           report_context['ft_t_1'] = " "
           report_context['ft_t_2'] = " "
           report_context['ft_t_3'] = " "
           report_context['ft_t_4'] = " "
           report_context['ft_t_5'] = " "
           report_context['ft_t_6'] = " "
           report_context['ft_t_7'] = " "
           report_context['ft_t_8'] = " "
           report_context['shear_t_0'] = tab_shear_t[0]
           report_context['shear_t_1'] = " "
           report_context['shear_t_2'] = " "
           report_context['shear_t_3'] = " "
           report_context['shear_t_4'] = " "
           report_context['shear_t_5'] = " "
           report_context['shear_t_6'] = " "
           report_context['shear_t_7'] = " "
           report_context['shear_t_8'] = " "
           report_context['mils_t_0'] = tab_mils_t[0]
           report_context['mils_t_1'] = " "
           report_context['mils_t_2'] = " "
           report_context['mils_t_3'] = " "
           report_context['mils_t_4'] = " "
           report_context['mils_t_5'] = " "
           report_context['mils_t_6'] = " "
           report_context['mils_t_7'] = " "
           report_context['mils_t_8'] = " "
           report_context['weight_t_0'] = tab_weight_t[0]
           report_context['weight_t_1'] = " "
           report_context['weight_t_2'] = " "
           report_context['weight_t_3'] = " "
           report_context['weight_t_4'] = " "
           report_context['weight_t_5'] = " "
           report_context['weight_t_6'] = " "
           report_context['weight_t_7'] = " "
           report_context['weight_t_8'] = " "
        else:
          if(indx_3 == 2):
           report_context['specimen_t_0'] = tab_specim_t[0]
           report_context['specimen_t_1'] = tab_specim_t[1]
           report_context['specimen_t_2'] = " "
           report_context['specimen_t_3'] = " "
           report_context['specimen_t_4'] = " "
           report_context['specimen_t_5'] = " "
           report_context['specimen_t_6'] = " "
           report_context['specimen_t_7'] = " "
           report_context['specimen_t_8'] = " "
           report_context['location_t_0'] = tab_location_t[0]
           report_context['location_t_1'] = tab_location_t[1]
           report_context['location_t_2'] = " "
           report_context['location_t_3'] = " "
           report_context['location_t_4'] = " "
           report_context['location_t_5'] = " "
           report_context['location_t_6'] = " "
           report_context['location_t_7'] = " "
           report_context['location_t_8'] = " "
           report_context['size_t_0'] = tab_size_t[0]
           report_context['size_t_1'] = tab_size_t[1]
           report_context['size_t_2'] = " "
           report_context['size_t_3'] = " "
           report_context['size_t_4'] = " "
           report_context['size_t_5'] = " "
           report_context['size_t_6'] = " "
           report_context['size_t_7'] = " "
           report_context['size_t_8'] = " "
           report_context['temp_t_0'] = tab_temp_t[0]
           report_context['temp_t_1'] = tab_temp_t[1]
           report_context['temp_t_2'] = " "
           report_context['temp_t_3'] = " "
           report_context['temp_t_4'] = " "
           report_context['temp_t_5'] = " "
           report_context['temp_t_6'] = " "
           report_context['temp_t_7'] = " "
           report_context['temp_t_8'] = " "
           report_context['ft_t_0'] = tab_ft_t[0]
           report_context['ft_t_1'] = tab_ft_t[1]
           report_context['ft_t_2'] = " "
           report_context['ft_t_3'] = " "
           report_context['ft_t_4'] = " "
           report_context['ft_t_5'] = " "
           report_context['ft_t_6'] = " "
           report_context['ft_t_7'] = " "
           report_context['ft_t_8'] = " "
           report_context['shear_t_0'] = tab_shear_t[0]
           report_context['shear_t_1'] = tab_shear_t[1]
           report_context['shear_t_2'] = " "
           report_context['shear_t_3'] = " "
           report_context['shear_t_4'] = " "
           report_context['shear_t_5'] = " "
           report_context['shear_t_6'] = " "
           report_context['shear_t_7'] = " "
           report_context['shear_t_8'] = " "
           report_context['mils_t_0'] = tab_mils_t[0]
           report_context['mils_t_1'] = tab_mils_t[1]
           report_context['mils_t_2'] = " "
           report_context['mils_t_3'] = " "
           report_context['mils_t_4'] = " "
           report_context['mils_t_5'] = " "
           report_context['mils_t_6'] = " "
           report_context['mils_t_7'] = " "
           report_context['mils_t_8'] = " "
           report_context['weight_t_0'] = tab_weight_t[0]
           report_context['weight_t_1'] = tab_weight_t[1]
           report_context['weight_t_2'] = " "
           report_context['weight_t_3'] = " "
           report_context['weight_t_4'] = " "
           report_context['weight_t_5'] = " "
           report_context['weight_t_6'] = " "
           report_context['weight_t_7'] = " "
           report_context['weight_t_8'] = " "
          else:
            if(indx_3 == 3):
              report_context['specimen_t_0'] = tab_specim_t[0]
              report_context['specimen_t_1'] = tab_specim_t[1]
              report_context['specimen_t_2'] = tab_specim_t[2]
              report_context['specimen_t_3'] = " "
              report_context['specimen_t_4'] = " "
              report_context['specimen_t_5'] = " "
              report_context['specimen_t_6'] = " "
              report_context['specimen_t_7'] = " "
              report_context['specimen_t_8'] = " "
              report_context['location_t_0'] = tab_location_t[0]
              report_context['location_t_1'] = tab_location_t[1]
              report_context['location_t_2'] = tab_location_t[2]
              report_context['location_t_3'] = " "
              report_context['location_t_4'] = " "
              report_context['location_t_5'] = " "
              report_context['location_t_6'] = " "
              report_context['location_t_7'] = " "
              report_context['location_t_8'] = " "
              report_context['size_t_0'] = tab_size_t[0]
              report_context['size_t_1'] = tab_size_t[1]
              report_context['size_t_2'] = tab_size_t[2]
              report_context['size_t_3'] = " "
              report_context['size_t_4'] = " "
              report_context['size_t_5'] = " "
              report_context['size_t_6'] = " "
              report_context['size_t_7'] = " "
              report_context['size_t_8'] = " "
              report_context['temp_t_0'] = tab_temp_t[0]
              report_context['temp_t_1'] = tab_temp_t[1]
              report_context['temp_t_2'] = tab_temp_t[2]
              report_context['temp_t_3'] = " "
              report_context['temp_t_4'] = " "
              report_context['temp_t_5'] = " "
              report_context['temp_t_6'] = " "
              report_context['temp_t_7'] = " "
              report_context['temp_t_8'] = " "
              report_context['ft_t_0'] = tab_ft_t[0]
              report_context['ft_t_1'] = tab_ft_t[1]
              report_context['ft_t_2'] = tab_ft_t[2]
              report_context['ft_t_3'] = " "
              report_context['ft_t_4'] = " "
              report_context['ft_t_5'] = " "
              report_context['ft_t_6'] = " "
              report_context['ft_t_7'] = " "
              report_context['ft_t_8'] = " "
              report_context['shear_t_0'] = tab_shear_t[0]
              report_context['shear_t_1'] = tab_shear_t[1]
              report_context['shear_t_2'] = tab_shear_t[2]
              report_context['shear_t_3'] = " "
              report_context['shear_t_4'] = " "
              report_context['shear_t_5'] = " "
              report_context['shear_t_6'] = " "
              report_context['shear_t_7'] = " "
              report_context['shear_t_8'] = " "
              report_context['mils_t_0'] = tab_mils_t[0]
              report_context['mils_t_1'] = tab_mils_t[1]
              report_context['mils_t_2'] = tab_mils_t[2]
              report_context['mils_t_3'] = " "
              report_context['mils_t_4'] = " "
              report_context['mils_t_5'] = " "
              report_context['mils_t_6'] = " "
              report_context['mils_t_7'] = " "
              report_context['mils_t_8'] = " "
              report_context['weight_t_0'] = tab_weight_t[0]
              report_context['weight_t_1'] = tab_weight_t[1]
              report_context['weight_t_2'] = tab_weight_t[2]
              report_context['weight_t_3'] = " "
              report_context['weight_t_4'] = " "
              report_context['weight_t_5'] = " "
              report_context['weight_t_6'] = " "
              report_context['weight_t_7'] = " "
              report_context['weight_t_8'] = " "
            else:
              if(indx_3 == 4):
                 report_context['specimen_t_0'] = tab_specim_t[0]
                 report_context['specimen_t_1'] = tab_specim_t[1]
                 report_context['specimen_t_2'] = tab_specim_t[2]
                 report_context['specimen_t_3'] = tab_specim_t[3]
                 report_context['specimen_t_4'] = " "
                 report_context['specimen_t_5'] = " "
                 report_context['specimen_t_6'] = " "
                 report_context['specimen_t_7'] = " "
                 report_context['specimen_t_8'] = " "
                 report_context['location_t_0'] = tab_location_t[0]
                 report_context['location_t_1'] = tab_location_t[1]
                 report_context['location_t_2'] = tab_location_t[2]
                 report_context['location_t_3'] = tab_location_t[3]
                 report_context['location_t_4'] = " "
                 report_context['location_t_5'] = " "
                 report_context['location_t_6'] = " "
                 report_context['location_t_7'] = " "
                 report_context['location_t_8'] = " "
                 report_context['size_t_0'] = tab_size_t[0]
                 report_context['size_t_1'] = tab_size_t[1]
                 report_context['size_t_2'] = tab_size_t[2]
                 report_context['size_t_3'] = tab_size_t[3]
                 report_context['size_t_4'] = " "
                 report_context['size_t_5'] = " "
                 report_context['size_t_6'] = " "
                 report_context['size_t_7'] = " "
                 report_context['size_t_8'] = " "
                 report_context['temp_t_0'] = tab_temp_t[0]
                 report_context['temp_t_1'] = tab_temp_t[1]
                 report_context['temp_t_2'] = tab_temp_t[2]
                 report_context['temp_t_3'] = tab_temp_t[3]
                 report_context['temp_t_4'] = " "
                 report_context['temp_t_5'] = " "
                 report_context['temp_t_6'] = " "
                 report_context['temp_t_7'] = " "
                 report_context['temp_t_8'] = " "
                 report_context['ft_t_0'] = tab_ft_t[0]
                 report_context['ft_t_1'] = tab_ft_t[1]
                 report_context['ft_t_2'] = tab_ft_t[2]
                 report_context['ft_t_3'] = tab_ft_t[3]
                 report_context['ft_t_4'] = " "
                 report_context['ft_t_5'] = " "
                 report_context['ft_t_6'] = " "
                 report_context['ft_t_7'] = " "
                 report_context['ft_t_8'] = " "
                 report_context['shear_t_0'] = tab_shear_t[0]
                 report_context['shear_t_1'] = tab_shear_t[1]
                 report_context['shear_t_2'] = tab_shear_t[2]
                 report_context['shear_t_3'] = tab_shear_t[3]
                 report_context['shear_t_4'] = " "
                 report_context['shear_t_5'] = " "
                 report_context['shear_t_6'] = " "
                 report_context['shear_t_7'] = " "
                 report_context['shear_t_8'] = " "
                 report_context['mils_t_0'] = tab_mils_t[0]
                 report_context['mils_t_1'] = tab_mils_t[1]
                 report_context['mils_t_2'] = tab_mils_t[2]
                 report_context['mils_t_3'] = tab_mils_t[3]
                 report_context['mils_t_4'] = " "
                 report_context['mils_t_5'] = " "
                 report_context['mils_t_6'] = " "
                 report_context['mils_t_7'] = " "
                 report_context['mils_t_8'] = " "
                 report_context['weight_t_0'] = tab_weight_t[0]
                 report_context['weight_t_1'] = tab_weight_t[1]
                 report_context['weight_t_2'] = tab_weight_t[2]
                 report_context['weight_t_3'] = tab_weight_t[3]
                 report_context['weight_t_4'] = " "
                 report_context['weight_t_5'] = " "
                 report_context['weight_t_6'] = " "
                 report_context['weight_t_7'] = " "
                 report_context['weight_t_8'] = " "
              else:
               if(indx_3 == 5):
                 report_context['specimen_t_0'] = tab_specim_t[0]
                 report_context['specimen_t_1'] = tab_specim_t[1]
                 report_context['specimen_t_2'] = tab_specim_t[2]
                 report_context['specimen_t_3'] = tab_specim_t[3]
                 report_context['specimen_t_4'] = tab_specim_t[4]
                 report_context['specimen_t_5'] = " "
                 report_context['specimen_t_6'] = " "
                 report_context['specimen_t_7'] = " "
                 report_context['specimen_t_8'] = " "
                 report_context['location_t_0'] = tab_location_t[0]
                 report_context['location_t_1'] = tab_location_t[1]
                 report_context['location_t_2'] = tab_location_t[2]
                 report_context['location_t_3'] = tab_location_t[3]
                 report_context['location_t_4'] = tab_location_t[4]
                 report_context['location_t_5'] = " "
                 report_context['location_t_6'] = " "
                 report_context['location_t_7'] = " "
                 report_context['location_t_8'] = " "
                 report_context['size_t_0'] = tab_size_t[0]
                 report_context['size_t_1'] = tab_size_t[1]
                 report_context['size_t_2'] = tab_size_t[2]
                 report_context['size_t_3'] = tab_size_t[3]
                 report_context['size_t_4'] = tab_size_t[4]
                 report_context['size_t_5'] = " "
                 report_context['size_t_6'] = " "
                 report_context['size_t_7'] = " "
                 report_context['size_t_8'] = " "
                 report_context['temp_t_0'] = tab_temp_t[0]
                 report_context['temp_t_1'] = tab_temp_t[1]
                 report_context['temp_t_2'] = tab_temp_t[2]
                 report_context['temp_t_3'] = tab_temp_t[3]
                 report_context['temp_t_4'] = tab_temp_t[4]
                 report_context['temp_t_5'] = " "
                 report_context['temp_t_6'] = " "
                 report_context['temp_t_7'] = " "
                 report_context['temp_t_8'] = " "
                 report_context['ft_t_0'] = tab_ft_t[0]
                 report_context['ft_t_1'] = tab_ft_t[1]
                 report_context['ft_t_2'] = tab_ft_t[2]
                 report_context['ft_t_3'] = tab_ft_t[3]
                 report_context['ft_t_4'] = tab_ft_t[4]
                 report_context['ft_t_5'] = " "
                 report_context['ft_t_6'] = " "
                 report_context['ft_t_7'] = " "
                 report_context['ft_t_8'] = " "
                 report_context['shear_t_0'] = tab_shear_t[0]
                 report_context['shear_t_1'] = tab_shear_t[1]
                 report_context['shear_t_2'] = tab_shear_t[2]
                 report_context['shear_t_3'] = tab_shear_t[3]
                 report_context['shear_t_4'] = tab_shear_t[4]
                 report_context['shear_t_5'] = " "
                 report_context['shear_t_6'] = " "
                 report_context['shear_t_7'] = " "
                 report_context['shear_t_8'] = " "
                 report_context['mils_t_0'] = tab_mils_t[0]
                 report_context['mils_t_1'] = tab_mils_t[1]
                 report_context['mils_t_2'] = tab_mils_t[2]
                 report_context['mils_t_3'] = tab_mils_t[3]
                 report_context['mils_t_4'] = tab_mils_t[4]
                 report_context['mils_t_5'] = " "
                 report_context['mils_t_6'] = " "
                 report_context['mils_t_7'] = " "
                 report_context['mils_t_8'] = " "
                 report_context['weight_t_0'] = tab_weight_t[0]
                 report_context['weight_t_1'] = tab_weight_t[1]
                 report_context['weight_t_2'] = tab_weight_t[2]
                 report_context['weight_t_3'] = tab_weight_t[3]
                 report_context['weight_t_4'] = tab_weight_t[4]
                 report_context['weight_t_5'] = " "
                 report_context['weight_t_6'] = " "
                 report_context['weight_t_7'] = " "
                 report_context['weight_t_8'] = " "
               else:
                if(indx_3 == 6):
                 report_context['specimen_t_0'] = tab_specim_t[0]
                 report_context['specimen_t_1'] = tab_specim_t[1]
                 report_context['specimen_t_2'] = tab_specim_t[2]
                 report_context['specimen_t_3'] = tab_specim_t[3]
                 report_context['specimen_t_4'] = tab_specim_t[4]
                 report_context['specimen_t_5'] = tab_specim_t[5]
                 report_context['specimen_t_6'] = " "
                 report_context['specimen_t_7'] = " "
                 report_context['specimen_t_8'] = " "
                 report_context['location_t_0'] = tab_location_t[0]
                 report_context['location_t_1'] = tab_location_t[1]
                 report_context['location_t_2'] = tab_location_t[2]
                 report_context['location_t_3'] = tab_location_t[3]
                 report_context['location_t_4'] = tab_location_t[4]
                 report_context['location_t_5'] = tab_location_t[5]
                 report_context['location_t_6'] = " "
                 report_context['location_t_7'] = " "
                 report_context['location_t_8'] = " "
                 report_context['size_t_0'] = tab_size_t[0]
                 report_context['size_t_1'] = tab_size_t[1]
                 report_context['size_t_2'] = tab_size_t[2]
                 report_context['size_t_3'] = tab_size_t[3]
                 report_context['size_t_4'] = tab_size_t[4]
                 report_context['size_t_5'] = tab_size_t[5]
                 report_context['size_t_6'] = " "
                 report_context['size_t_7'] = " "
                 report_context['size_t_8'] = " "
                 report_context['temp_t_0'] = tab_temp_t[0]
                 report_context['temp_t_1'] = tab_temp_t[1]
                 report_context['temp_t_2'] = tab_temp_t[2]
                 report_context['temp_t_3'] = tab_temp_t[3]
                 report_context['temp_t_4'] = tab_temp_t[4]
                 report_context['temp_t_5'] = tab_temp_t[5]
                 report_context['temp_t_6'] = " "
                 report_context['temp_t_7'] = " "
                 report_context['temp_t_8'] = " "
                 report_context['ft_t_0'] = tab_ft_t[0]
                 report_context['ft_t_1'] = tab_ft_t[1]
                 report_context['ft_t_2'] = tab_ft_t[2]
                 report_context['ft_t_3'] = tab_ft_t[3]
                 report_context['ft_t_4'] = tab_ft_t[4]
                 report_context['ft_t_5'] = tab_ft_t[5]
                 report_context['ft_t_6'] = " "
                 report_context['ft_t_7'] = " "
                 report_context['ft_t_8'] = " "
                 report_context['shear_t_0'] = tab_shear_t[0]
                 report_context['shear_t_1'] = tab_shear_t[1]
                 report_context['shear_t_2'] = tab_shear_t[2]
                 report_context['shear_t_3'] = tab_shear_t[3]
                 report_context['shear_t_4'] = tab_shear_t[4]
                 report_context['shear_t_5'] = tab_shear_t[5]
                 report_context['shear_t_6'] = " "
                 report_context['shear_t_7'] = " "
                 report_context['shear_t_8'] = " "
                 report_context['mils_t_0'] = tab_mils_t[0]
                 report_context['mils_t_1'] = tab_mils_t[1]
                 report_context['mils_t_2'] = tab_mils_t[2]
                 report_context['mils_t_3'] = tab_mils_t[3]
                 report_context['mils_t_4'] = tab_mils_t[4]
                 report_context['mils_t_5'] = tab_mils_t[5]
                 report_context['mils_t_6'] = " "
                 report_context['mils_t_7'] = " "
                 report_context['mils_t_8'] = " "
                 report_context['weight_t_0'] = tab_weight_t[0]
                 report_context['weight_t_1'] = tab_weight_t[1]
                 report_context['weight_t_2'] = tab_weight_t[2]
                 report_context['weight_t_3'] = tab_weight_t[3]
                 report_context['weight_t_4'] = tab_weight_t[4]
                 report_context['weight_t_5'] = tab_weight_t[5]
                 report_context['weight_t_6'] = " "
                 report_context['weight_t_7'] = " "
                 report_context['weight_t_8'] = " "
                else:
                  if(indx_3 == 7):
                    report_context['specimen_t_0'] = tab_specim_t[0]
                    report_context['specimen_t_1'] = tab_specim_t[1]
                    report_context['specimen_t_2'] = tab_specim_t[2]
                    report_context['specimen_t_3'] = tab_specim_t[3]
                    report_context['specimen_t_4'] = tab_specim_t[4]
                    report_context['specimen_t_5'] = tab_specim_t[5]
                    report_context['specimen_t_6'] = tab_specim_t[6]
                    report_context['specimen_t_7'] = " "
                    report_context['specimen_t_8'] = " "
                    report_context['location_t_0'] = tab_location_t[0]
                    report_context['location_t_1'] = tab_location_t[1]
                    report_context['location_t_2'] = tab_location_t[2]
                    report_context['location_t_3'] = tab_location_t[3]
                    report_context['location_t_4'] = tab_location_t[4]
                    report_context['location_t_5'] = tab_location_t[5]
                    report_context['location_t_6'] = tab_location_t[6]
                    report_context['location_t_7'] = " "
                    report_context['location_t_8'] = " "
                    report_context['size_t_0'] = tab_size_t[0]
                    report_context['size_t_1'] = tab_size_t[1]
                    report_context['size_t_2'] = tab_size_t[2]
                    report_context['size_t_3'] = tab_size_t[3]
                    report_context['size_t_4'] = tab_size_t[4]
                    report_context['size_t_5'] = tab_size_t[5]
                    report_context['size_t_6'] = tab_size_t[6]
                    report_context['size_t_7'] = " "
                    report_context['size_t_8'] = " "
                    report_context['temp_t_0'] = tab_temp_t[0]
                    report_context['temp_t_1'] = tab_temp_t[1]
                    report_context['temp_t_2'] = tab_temp_t[2]
                    report_context['temp_t_3'] = tab_temp_t[3]
                    report_context['temp_t_4'] = tab_temp_t[4]
                    report_context['temp_t_5'] = tab_temp_t[5]
                    report_context['temp_t_6'] = tab_temp_t[6]
                    report_context['temp_t_7'] = " "
                    report_context['temp_t_8'] = " "
                    report_context['ft_t_0'] = tab_ft_t[0]
                    report_context['ft_t_1'] = tab_ft_t[1]
                    report_context['ft_t_2'] = tab_ft_t[2]
                    report_context['ft_t_3'] = tab_ft_t[3]
                    report_context['ft_t_4'] = tab_ft_t[4]
                    report_context['ft_t_5'] = tab_ft_t[5]
                    report_context['ft_t_6'] = tab_ft_t[6]
                    report_context['ft_t_7'] = " "
                    report_context['ft_t_8'] = " "
                    report_context['shear_t_0'] = tab_shear_t[0]
                    report_context['shear_t_1'] = tab_shear_t[1]
                    report_context['shear_t_2'] = tab_shear_t[2]
                    report_context['shear_t_3'] = tab_shear_t[3]
                    report_context['shear_t_4'] = tab_shear_t[4]
                    report_context['shear_t_5'] = tab_shear_t[5]
                    report_context['shear_t_6'] = tab_shear_t[6]
                    report_context['shear_t_7'] = " "
                    report_context['shear_t_8'] = " "
                    report_context['mils_t_0'] = tab_mils_t[0]
                    report_context['mils_t_1'] = tab_mils_t[1]
                    report_context['mils_t_2'] = tab_mils_t[2]
                    report_context['mils_t_3'] = tab_mils_t[3]
                    report_context['mils_t_4'] = tab_mils_t[4]
                    report_context['mils_t_5'] = tab_mils_t[5]
                    report_context['mils_t_6'] = tab_mils_t[6]
                    report_context['mils_t_7'] = " "
                    report_context['mils_t_8'] = " "
                    report_context['weight_t_0'] = tab_weight_t[0]
                    report_context['weight_t_1'] = tab_weight_t[1]
                    report_context['weight_t_2'] = tab_weight_t[2]
                    report_context['weight_t_3'] = tab_weight_t[3]
                    report_context['weight_t_4'] = tab_weight_t[4]
                    report_context['weight_t_5'] = tab_weight_t[5]
                    report_context['weight_t_6'] = tab_weight_t[6]
                    report_context['weight_t_7'] = " "
                    report_context['weight_t_8'] = " "
                  else:
                   if(indx_3 == 8):
                    report_context['specimen_t_0'] = tab_specim_t[0]
                    report_context['specimen_t_1'] = tab_specim_t[1]
                    report_context['specimen_t_2'] = tab_specim_t[2]
                    report_context['specimen_t_3'] = tab_specim_t[3]
                    report_context['specimen_t_4'] = tab_specim_t[4]
                    report_context['specimen_t_5'] = tab_specim_t[5]
                    report_context['specimen_t_6'] = tab_specim_t[6]
                    report_context['specimen_t_7'] = tab_specim_t[7]
                    report_context['specimen_t_8'] = " "
                    report_context['location_t_0'] = tab_location_t[0]
                    report_context['location_t_1'] = tab_location_t[1]
                    report_context['location_t_2'] = tab_location_t[2]
                    report_context['location_t_3'] = tab_location_t[3]
                    report_context['location_t_4'] = tab_location_t[4]
                    report_context['location_t_5'] = tab_location_t[5]
                    report_context['location_t_6'] = tab_location_t[6]
                    report_context['location_t_7'] = tab_location_t[7]
                    report_context['location_t_8'] = " "
                    report_context['size_t_0'] = tab_size_t[0]
                    report_context['size_t_1'] = tab_size_t[1]
                    report_context['size_t_2'] = tab_size_t[2]
                    report_context['size_t_3'] = tab_size_t[3]
                    report_context['size_t_4'] = tab_size_t[4]
                    report_context['size_t_5'] = tab_size_t[5]
                    report_context['size_t_6'] = tab_size_t[6]
                    report_context['size_t_7'] = tab_size_t[7]
                    report_context['size_t_8'] = " "
                    report_context['temp_t_0'] = tab_temp_t[0]
                    report_context['temp_t_1'] = tab_temp_t[1]
                    report_context['temp_t_2'] = tab_temp_t[2]
                    report_context['temp_t_3'] = tab_temp_t[3]
                    report_context['temp_t_4'] = tab_temp_t[4]
                    report_context['temp_t_5'] = tab_temp_t[5]
                    report_context['temp_t_6'] = tab_temp_t[6]
                    report_context['temp_t_7'] = tab_temp_t[7]
                    report_context['temp_t_8'] = " "
                    report_context['ft_t_0'] = tab_ft_t[0]
                    report_context['ft_t_1'] = tab_ft_t[1]
                    report_context['ft_t_2'] = tab_ft_t[2]
                    report_context['ft_t_3'] = tab_ft_t[3]
                    report_context['ft_t_4'] = tab_ft_t[4]
                    report_context['ft_t_5'] = tab_ft_t[5]
                    report_context['ft_t_6'] = tab_ft_t[6]
                    report_context['ft_t_7'] = tab_ft_t[7]
                    report_context['ft_t_8'] = " "
                    report_context['shear_t_0'] = tab_shear_t[0]
                    report_context['shear_t_1'] = tab_shear_t[1]
                    report_context['shear_t_2'] = tab_shear_t[2]
                    report_context['shear_t_3'] = tab_shear_t[3]
                    report_context['shear_t_4'] = tab_shear_t[4]
                    report_context['shear_t_5'] = tab_shear_t[5]
                    report_context['shear_t_6'] = tab_shear_t[6]
                    report_context['shear_t_7'] = tab_shear_t[7]
                    report_context['shear_t_8'] = " "
                    report_context['mils_t_0'] = tab_mils_t[0]
                    report_context['mils_t_1'] = tab_mils_t[1]
                    report_context['mils_t_2'] = tab_mils_t[2]
                    report_context['mils_t_3'] = tab_mils_t[3]
                    report_context['mils_t_4'] = tab_mils_t[4]
                    report_context['mils_t_5'] = tab_mils_t[5]
                    report_context['mils_t_6'] = tab_mils_t[6]
                    report_context['mils_t_7'] = tab_mils_t[7]
                    report_context['mils_t_8'] = " "
                    report_context['weight_t_0'] = tab_weight_t[0]
                    report_context['weight_t_1'] = tab_weight_t[1]
                    report_context['weight_t_2'] = tab_weight_t[2]
                    report_context['weight_t_3'] = tab_weight_t[3]
                    report_context['weight_t_4'] = tab_weight_t[4]
                    report_context['weight_t_5'] = tab_weight_t[5]
                    report_context['weight_t_6'] = tab_weight_t[6]
                    report_context['weight_t_7'] = tab_weight_t[7]
                    report_context['weight_t_8'] = " "
                   else:
                     if(indx_3 >= 9):
                       report_context['specimen_t_0'] = tab_specim_t[0]
                       report_context['specimen_t_1'] = tab_specim_t[1]
                       report_context['specimen_t_2'] = tab_specim_t[2]
                       report_context['specimen_t_3'] = tab_specim_t[3]
                       report_context['specimen_t_4'] = tab_specim_t[4]
                       report_context['specimen_t_5'] = tab_specim_t[5]
                       report_context['specimen_t_6'] = tab_specim_t[6]
                       report_context['specimen_t_7'] = tab_specim_t[7]
                       report_context['specimen_t_8'] = tab_specim_t[8]
                       report_context['location_t_0'] = tab_location_t[0]
                       report_context['location_t_1'] = tab_location_t[1]
                       report_context['location_t_2'] = tab_location_t[2]
                       report_context['location_t_3'] = tab_location_t[3]
                       report_context['location_t_4'] = tab_location_t[4]
                       report_context['location_t_5'] = tab_location_t[5]
                       report_context['location_t_6'] = tab_location_t[6]
                       report_context['location_t_7'] = tab_location_t[7]
                       report_context['location_t_8'] = tab_location_t[8]
                       report_context['size_t_0'] = tab_size_t[0]
                       report_context['size_t_1'] = tab_size_t[1]
                       report_context['size_t_2'] = tab_size_t[2]
                       report_context['size_t_3'] = tab_size_t[3]
                       report_context['size_t_4'] = tab_size_t[4]
                       report_context['size_t_5'] = tab_size_t[5]
                       report_context['size_t_6'] = tab_size_t[6]
                       report_context['size_t_7'] = tab_size_t[7]
                       report_context['size_t_8'] = tab_size_t[8]
                       report_context['temp_t_0'] = tab_temp_t[0]
                       report_context['temp_t_1'] = tab_temp_t[1]
                       report_context['temp_t_2'] = tab_temp_t[2]
                       report_context['temp_t_3'] = tab_temp_t[3]
                       report_context['temp_t_4'] = tab_temp_t[4]
                       report_context['temp_t_5'] = tab_temp_t[5]
                       report_context['temp_t_6'] = tab_temp_t[6]
                       report_context['temp_t_7'] = tab_temp_t[7]
                       report_context['temp_t_8'] = tab_temp_t[8]
                       report_context['ft_t_0'] = tab_ft_t[0]
                       report_context['ft_t_1'] = tab_ft_t[1]
                       report_context['ft_t_2'] = tab_ft_t[2]
                       report_context['ft_t_3'] = tab_ft_t[3]
                       report_context['ft_t_4'] = tab_ft_t[4]
                       report_context['ft_t_5'] = tab_ft_t[5]
                       report_context['ft_t_6'] = tab_ft_t[6]
                       report_context['ft_t_7'] = tab_ft_t[7]
                       report_context['ft_t_8'] = tab_ft_t[8]
                       report_context['shear_t_0'] = tab_shear_t[0]
                       report_context['shear_t_1'] = tab_shear_t[1]
                       report_context['shear_t_2'] = tab_shear_t[2]
                       report_context['shear_t_3'] = tab_shear_t[3]
                       report_context['shear_t_4'] = tab_shear_t[4]
                       report_context['shear_t_5'] = tab_shear_t[5]
                       report_context['shear_t_6'] = tab_shear_t[6]
                       report_context['shear_t_7'] = tab_shear_t[7]
                       report_context['shear_t_8'] = tab_shear_t[8]
                       report_context['mils_t_0'] = tab_mils_t[0]
                       report_context['mils_t_1'] = tab_mils_t[1]
                       report_context['mils_t_2'] = tab_mils_t[2]
                       report_context['mils_t_3'] = tab_mils_t[3]
                       report_context['mils_t_4'] = tab_mils_t[4]
                       report_context['mils_t_5'] = tab_mils_t[5]
                       report_context['mils_t_6'] = tab_mils_t[6]
                       report_context['mils_t_7'] = tab_mils_t[7]
                       report_context['mils_t_8'] = tab_mils_t[8]
                       report_context['weight_t_0'] = tab_weight_t[0]
                       report_context['weight_t_1'] = tab_weight_t[1]
                       report_context['weight_t_2'] = tab_weight_t[2]
                       report_context['weight_t_3'] = tab_weight_t[3]
                       report_context['weight_t_4'] = tab_weight_t[4]
                       report_context['weight_t_5'] = tab_weight_t[5]
                       report_context['weight_t_6'] = tab_weight_t[6]
                       report_context['weight_t_7'] = tab_weight_t[7]
                       report_context['weight_t_8'] = tab_weight_t[8]
                     else:
                       report_context['specimen_t_0'] = " "
                       report_context['specimen_t_1'] = " "
                       report_context['specimen_t_2'] = " "
                       report_context['specimen_t_3'] = " "
                       report_context['specimen_t_4'] = " "
                       report_context['specimen_t_5'] = " "
                       report_context['specimen_t_6'] = " "
                       report_context['specimen_t_7'] = " "
                       report_context['specimen_t_8'] = " "
                       report_context['location_t_0'] = " "
                       report_context['location_t_1'] = " "
                       report_context['location_t_2'] = " "
                       report_context['location_t_3'] = " "
                       report_context['location_t_4'] = " "
                       report_context['location_t_5'] = " "
                       report_context['location_t_6'] = " "
                       report_context['location_t_7'] = " "
                       report_context['location_t_8'] = " "
                       report_context['size_t_0'] = " "
                       report_context['size_t_1'] = " "
                       report_context['size_t_2'] = " "
                       report_context['size_t_3'] = " "
                       report_context['size_t_4'] = " "
                       report_context['size_t_5'] = " "
                       report_context['size_t_6'] = " "
                       report_context['size_t_7'] = " "
                       report_context['size_t_8'] = " "
                       report_context['temp_t_0'] = " "
                       report_context['temp_t_1'] = " "
                       report_context['temp_t_2'] = " "
                       report_context['temp_t_3'] = " "
                       report_context['temp_t_4'] = " "
                       report_context['temp_t_5'] = " "
                       report_context['temp_t_6'] = " "
                       report_context['temp_t_7'] = " "
                       report_context['temp_t_8'] = " "
                       report_context['ft_t_0'] = " "
                       report_context['ft_t_1'] = " "
                       report_context['ft_t_2'] = " "
                       report_context['ft_t_3'] = " "
                       report_context['ft_t_4'] = " "
                       report_context['ft_t_5'] = " "
                       report_context['ft_t_6'] = " "
                       report_context['ft_t_7'] = " "
                       report_context['ft_t_8'] = " "
                       report_context['shear_t_0'] = " "
                       report_context['shear_t_1'] = " "
                       report_context['shear_t_2'] = " "
                       report_context['shear_t_3'] = " "
                       report_context['shear_t_4'] = " "
                       report_context['shear_t_5'] = " "
                       report_context['shear_t_6'] = " "
                       report_context['shear_t_7'] = " "
                       report_context['shear_t_8'] = " "
                       report_context['mils_t_0'] = " "
                       report_context['mils_t_1'] = " "
                       report_context['mils_t_2'] = " "
                       report_context['mils_t_3'] = " "
                       report_context['mils_t_4'] = " "
                       report_context['mils_t_5'] = " "
                       report_context['mils_t_6'] = " "
                       report_context['mils_t_7'] = " "
                       report_context['mils_t_8'] = " "
                       report_context['weight_t_0'] = " "
                       report_context['weight_t_1'] = " "
                       report_context['weight_t_2'] = " "
                       report_context['weight_t_3'] = " "
                       report_context['weight_t_4'] = " "
                       report_context['weight_t_5'] = " "
                       report_context['weight_t_6'] = " "
                       report_context['weight_t_7'] = " "
                       report_context['weight_t_8'] = " "


        tab_type_guide = []
        tab_result = []
        for j in range(0,indx_2):
            tab_type_guide.append(zertifikat.guide[j].type_figure)
            tab_result.append(zertifikat.guide[j].result)

        if(indx_2 == 1):
           report_context['type_guide_0'] = tab_type_guide[0]
           report_context['type_guide_1'] = " "
           report_context['type_guide_2'] = " "
           report_context['type_guide_3'] = " "
           report_context['result_0'] = tab_result[0]
           report_context['result_1'] = " "
           report_context['result_2'] = " "
           report_context['result_3'] = " "
        else:
         if(indx_2 == 2):
           report_context['type_guide_0'] = tab_type_guide[0]
           report_context['type_guide_1'] = tab_type_guide[1]
           report_context['type_guide_2'] = " "
           report_context['type_guide_3'] = " "
           report_context['result_0'] = tab_result[0]
           report_context['result_1'] = tab_result[1]
           report_context['result_2'] = " "
           report_context['result_3'] = " "
         else:
          if(indx_2 == 3):
           report_context['type_guide_0'] = tab_type_guide[0]
           report_context['type_guide_1'] = tab_type_guide[1]
           report_context['type_guide_2'] = tab_type_guide[2]
           report_context['type_guide_3'] = " "
           report_context['result_0'] = tab_result[0]
           report_context['result_1'] = tab_result[1]
           report_context['result_2'] = tab_result[2]
           report_context['result_3'] = " "
          else:
            if(indx_2 >= 4):
              report_context['type_guide_0'] = tab_type_guide[0]
              report_context['type_guide_1'] = tab_type_guide[1]
              report_context['type_guide_2'] = tab_type_guide[2]
              report_context['type_guide_3'] = tab_type_guide[3]
              report_context['result_0'] = tab_result[0]
              report_context['result_1'] = tab_result[1]
              report_context['result_2'] = tab_result[2]
              report_context['result_3'] = tab_result[3]
            else:
              report_context['type_guide_0'] = " "
              report_context['type_guide_1'] = " "
              report_context['type_guide_2'] = " "
              report_context['type_guide_3'] = " "
              report_context['result_0'] = " "
              report_context['result_1'] = " "
              report_context['result_2'] = " "
              report_context['result_3'] = " "


        tab_specimen = []
        tab_widht = []
        tab_thickness = []
        tab_area = []
        tab_ultimate1 = []
        tab_ultimate2 = []
        tab_type = []
        for i in range(0,indx_1):
            tab_specimen.append(zertifikat.tensile[i].specimen)
            tab_widht.append(zertifikat.tensile[i].width)
            tab_thickness.append(zertifikat.tensile[i].thickness)
            tab_area.append(zertifikat.tensile[i].area)
            tab_ultimate1.append(zertifikat.tensile[i].ultimate)
            tab_ultimate2.append(zertifikat.tensile[i].ultimate2)
            tab_type.append(zertifikat.tensile[i].type)
        if(indx_1 == 1):
              report_context['specimen_0'] = tab_specimen[0]
              report_context['specimen_1'] = " "
              report_context['specimen_2'] = " "
              report_context['specimen_3'] = " "
              report_context['widht_0'] = tab_widht[0]
              report_context['widht_1'] = " "
              report_context['widht_2'] = " "
              report_context['widht_3'] = " "
              report_context['thickness_0'] = tab_thickness[0]
              report_context['thickness_1'] = " "
              report_context['thickness_2'] = " "
              report_context['thickness_3'] = " "
              report_context['area_0'] = tab_area[0]
              report_context['area_1'] = " "
              report_context['area_2'] = " "
              report_context['area_3'] = " "
              report_context['ultimate1_0'] = tab_ultimate1[0]
              report_context['ultimate1_1'] = " "
              report_context['ultimate1_2'] = " "
              report_context['ultimate1_3'] = " "
              report_context['ultimate2_0'] = tab_ultimate2[0]
              report_context['ultimate2_1'] = " "
              report_context['ultimate2_2'] = " "
              report_context['ultimate2_3'] = " "
              report_context['type_0'] = tab_type[0]
              report_context['type_1'] = " "
              report_context['type_2'] = " "
              report_context['type_3'] = " "
        else:
           if(indx_1 == 2):
              report_context['specimen_0'] = tab_specimen[0]
              report_context['specimen_1'] = tab_specimen[1]
              report_context['specimen_2'] = " "
              report_context['specimen_3'] = " "
              report_context['widht_0'] = tab_widht[0]
              report_context['widht_1'] = tab_widht[1]
              report_context['widht_2'] = " "
              report_context['widht_3'] = " "
              report_context['thickness_0'] = tab_thickness[0]
              report_context['thickness_1'] = tab_thickness[1]
              report_context['thickness_2'] = " "
              report_context['thickness_3'] = " "
              report_context['area_0'] = tab_area[0]
              report_context['area_1'] = tab_area[1]
              report_context['area_2'] = " "
              report_context['area_3'] = " "
              report_context['ultimate1_0'] = tab_ultimate1[0]
              report_context['ultimate1_1'] = tab_ultimate1[1]
              report_context['ultimate1_2'] = " "
              report_context['ultimate1_3'] = " "
              report_context['ultimate2_0'] = tab_ultimate2[0]
              report_context['ultimate2_1'] = tab_ultimate2[1]
              report_context['ultimate2_2'] = " "
              report_context['ultimate2_3'] = " "
              report_context['type_0'] = tab_type[0]
              report_context['type_1'] = tab_type[1]
              report_context['type_2'] = " "
              report_context['type_3'] = " "
           else:
             if(indx_1 == 3):
                report_context['specimen_0'] = tab_specimen[0]
                report_context['specimen_1'] = tab_specimen[1]
                report_context['specimen_2'] = tab_specimen[2]
                report_context['specimen_3'] = " "
                report_context['widht_0'] = tab_widht[0]
                report_context['widht_1'] = tab_widht[1]
                report_context['widht_2'] = tab_widht[2]
                report_context['widht_3'] = " "
                report_context['thickness_0'] = tab_thickness[0]
                report_context['thickness_1'] = tab_thickness[1]
                report_context['thickness_2'] = tab_thickness[2]
                report_context['thickness_3'] = " "
                report_context['area_0'] = tab_area[0]
                report_context['area_1'] = tab_area[1]
                report_context['area_2'] = tab_area[2]
                report_context['area_3'] = " "
                report_context['ultimate1_0'] = tab_ultimate1[0]
                report_context['ultimate1_1'] = tab_ultimate1[1]
                report_context['ultimate1_2'] = tab_ultimate1[2]
                report_context['ultimate1_3'] = " "
                report_context['ultimate2_0'] = tab_ultimate2[0]
                report_context['ultimate2_1'] = tab_ultimate2[1]
                report_context['ultimate2_2'] = tab_ultimate2[2]
                report_context['ultimate2_3'] = " "
                report_context['type_0'] = tab_type[0]
                report_context['type_1'] = tab_type[1]
                report_context['type_2'] = tab_type[2]
                report_context['type_3'] = " "
             else:
               if(indx_1 == 4):
                  report_context['specimen_0'] = tab_specimen[0]
                  report_context['specimen_1'] = tab_specimen[1]
                  report_context['specimen_2'] = tab_specimen[2]
                  report_context['specimen_3'] = tab_specimen[3]
                  report_context['widht_0'] = tab_widht[0]
                  report_context['widht_1'] = tab_widht[1]
                  report_context['widht_2'] = tab_widht[2]
                  report_context['widht_3'] = tab_widht[3]
                  report_context['thickness_0'] = tab_thickness[0]
                  report_context['thickness_1'] = tab_thickness[1]
                  report_context['thickness_2'] = tab_thickness[2]
                  report_context['thickness_3'] = tab_thickness[3]
                  report_context['area_0'] = tab_area[0]
                  report_context['area_1'] = tab_area[1]
                  report_context['area_2'] = tab_area[2]
                  report_context['area_3'] = tab_area[3]
                  report_context['ultimate1_0'] = tab_ultimate1[0]
                  report_context['ultimate1_1'] = tab_ultimate1[1]
                  report_context['ultimate1_2'] = tab_ultimate1[2]
                  report_context['ultimate1_3'] = tab_ultimate1[3]
                  report_context['ultimate2_0'] = tab_ultimate2[0]
                  report_context['ultimate2_1'] = tab_ultimate2[1]
                  report_context['ultimate2_2'] = tab_ultimate2[2]
                  report_context['ultimate2_3'] = tab_ultimate2[3]
                  report_context['type_0'] = tab_type[0]
                  report_context['type_1'] = tab_type[1]
                  report_context['type_2'] = tab_type[2]
                  report_context['type_3'] = tab_type[3]
               else:
                 if(indx_1 > 4):
                  report_context['specimen_0'] = tab_specimen[0]
                  report_context['specimen_1'] = tab_specimen[1]
                  report_context['specimen_2'] = tab_specimen[2]
                  report_context['specimen_3'] = tab_specimen[3]
                  report_context['widht_0'] = tab_widht[0]
                  report_context['widht_1'] = tab_widht[1]
                  report_context['widht_2'] = tab_widht[2]
                  report_context['widht_3'] = tab_widht[3]
                  report_context['thickness_0'] = tab_thickness[0]
                  report_context['thickness_1'] = tab_thickness[1]
                  report_context['thickness_2'] = tab_thickness[2]
                  report_context['thickness_3'] = tab_thickness[3]
                  report_context['area_0'] = tab_area[0]
                  report_context['area_1'] = tab_area[1]
                  report_context['area_2'] = tab_area[2]
                  report_context['area_3'] = tab_area[3]
                  report_context['ultimate1_0'] = tab_ultimate1[0]
                  report_context['ultimate1_1'] = tab_ultimate1[1]
                  report_context['ultimate1_2'] = tab_ultimate1[2]
                  report_context['ultimate1_3'] = tab_ultimate1[3]
                  report_context['ultimate2_0'] = tab_ultimate2[0]
                  report_context['ultimate2_1'] = tab_ultimate2[1]
                  report_context['ultimate2_2'] = tab_ultimate2[2]
                  report_context['ultimate2_3'] = tab_ultimate2[3]
                  report_context['type_0'] = tab_type[0]
                  report_context['type_1'] = tab_type[1]
                  report_context['type_2'] = tab_type[2]
                  report_context['type_3'] = tab_type[3]
                 else:
                  report_context['specimen_0'] = " "
                  report_context['specimen_1'] = " "
                  report_context['specimen_2'] = " "
                  report_context['specimen_3'] = " "
                  report_context['widht_0'] = " "
                  report_context['widht_1'] = " "
                  report_context['widht_2'] = " "
                  report_context['widht_3'] = " "
                  report_context['thickness_0'] = " "
                  report_context['thickness_1'] = " "
                  report_context['thickness_2'] = " "
                  report_context['thickness_3'] = " "
                  report_context['area_0'] = " "
                  report_context['area_1'] = " "
                  report_context['area_2'] = " "
                  report_context['area_3'] = " "
                  report_context['ultimate1_0'] = " "
                  report_context['ultimate1_1'] = " "
                  report_context['ultimate1_2'] = " "
                  report_context['ultimate1_3'] = " "
                  report_context['ultimate2_0'] = " "
                  report_context['ultimate2_1'] = " "
                  report_context['ultimate2_2'] = " "
                  report_context['ultimate2_3'] = " "
                  report_context['type_0'] = " "
                  report_context['type_1'] = " "
                  report_context['type_2'] = " "
                  report_context['type_3'] = " "

        return report_context


# WPQR (ASME IX, QW-483) class
class wpqr6(DeactivableMixin, ModelView, ModelSQL, MultiValueMixin):
    'Party WPQR ASME'
    __name__ = 'party.wpqr6'
    organisation = fields.Char('Organization Name')
    organisation_anschrift = fields.Char(' ')
    procedure_qualification = fields.Function(fields.Char('Procedure Qualification Record No.'),"get_automatic_id")
    Date = fields.Function(fields.Date("Date"),"get_automatic_ausstellung")
    wps_nr = fields.Char("WPS No.")
    matrial22 = fields.Many2One('welding.grundwerkstoff_properties', 'Material Spec')
    fm1 = fields.Many2One('party.fm1', 'FM1')
    fm2 = fields.Many2One('party.fm1', 'FM2')
    qw483 = fields.Many2One('party.wpqr.qw483', ' ')
    sfa_specification1 = fields.Function(fields.Char("SFA Specification"),"on_Change_fm1")
    sfa_specification2 = fields.Function(fields.Char("SFA Specification"),"on_Change_fm2")
    aws_classification1 = fields.Function(fields.Char("AWS Classification"),"on_Change_fm11")
    aws_classification2 = fields.Function(fields.Char("AWS Classification"),"on_Change_fm21")
    filler_metal1 = fields.Function(fields.Char("Filler Metal F-No."),"on_Change_fm12")
    filler_metal2 = fields.Function(fields.Char("Filler Metal F-No."),"on_Change_fm22")
    weld_metal1 = fields.Char("Weld Metal Analysis A-No.")
    weld_metal2 = fields.Char("Weld Metal Analysis A-No.")
    size_filler1 = fields.Char("Size of Filler Metal.")
    size_filler2 = fields.Char("Size of Filler Metal.")
    flux_type1 = fields.Char("Flux Type, Name")
    flux_type2 = fields.Char("Flux Type, Name")
    weld_metal_thickness1 = fields.Char("Weld Metal Thickness")
    weld_metal_thickness2 = fields.Char("Weld Metal Thickness")
    other_filler1 = fields.Char("Other")
    other_filler2 = fields.Char("Other")

    title1 = fields.Char('QW-483 SUGGESTED FORMAT FOR PROCEDURE QUALIFICATION RECORDS (PQR)-')
    title2 = fields.Char('(See QW-200.2, Section IX, ASME Boiler and Pressure Vessel Code)')
    title3 = fields.Char('Record Actual Conditions Used to Weld Test Coupon')
    spacce1 = fields.Char('                                       ')
    spacce2 = fields.Char('         ')

    datum_ausstellung = fields.Date("Datum der Ausstellung")
    gultig_bis = fields.Date("gültig bis")
    bereich = fields.Char('Bereich')
    pqr_nr = fields.Integer("PQR-Nr")
    pqr_nr_des_hersteller = fields.Function(fields.Char("PQR-Nr des Herstellers"),"on_change_andere")
    wpqr_nr = fields.Function(fields.Integer("zugeordnete WPQR-Nr"),"on_change_automatique")
    pqr_nr_1 = fields.Function(fields.Char("PQR-Nr."),"on_change_automatique1")
    plate_pipe = fields.Selection([
        ('p/p', 'p/p | Plate/Plate'),
        ('T/P', 'T/P | Tube/Plate'),
        ('T/T', 'Tube/Tube'),
    ], 'Plate(P)/Pipe(T)', readonly = False,
        )
    bw_fw = fields.Selection([
        ('BW', 'Bw | Groove'),
        ('FW', 'FW | Fillet'),
    ], 'FW/BW', readonly = False,
        )

    formular = fields.Selection([
        ('PQR', 'PQR | ASME BPVC, Section IX,QW-483'),
        ('WPQR', 'WPQR | ISO 15607 bis ISO 15614'),
        ('WPAR', 'WPAR | Normenreihe EN 288'),
    ], 'Formular', readonly = False,
        )
    qualification = fields.Char('Für die Liste Qualifikationen(WPQR). Nahtart.z.B (T BW)')
    dicke = fields.Integer("Dicke(mm)")
    durchmesser = fields.Integer("Durchmesse(mm)")

    type_grade1 = fields.Selection('on_change_matriall','Type or Grade', readonly = False,)
    type_grade1_1 = fields.Char("Type or Grade2")
    matrial4 = fields.Char("Material Spec2")
    grou2 = fields.Selection('on_change_matriall5','Group No.', readonly = False,)

    thickness = fields.Char("Thickness of Test Coupon")
    diameter = fields.Char("Diameter of Test Coupon")
    max_thickness = fields.Char("Maximum Pass Thickness")
    other = fields.Char("Other")
    other1 = fields.Char("Other")
    other2 = fields.Char("Other")
    other3 = fields.Char("Other")
    other4 = fields.Char("Other")


    temperatur = fields.Char("Temperature")
    time = fields.Char("Temperature")
    other_postweld = fields.Char("Other")
    other_postweld1 = fields.Char("Other")
    other_postweld2 = fields.Char("Other")

    flow_rate1 = fields.Char("Flow Rate")
    flow_rate2 = fields.Char("Percent Composition")
    flow_rate3 = fields.Char("Gas(es)")
    other_gas_ = fields.Char("Other")

    position = fields.Selection([
        ('1F', '1F | Wannenposition (PA)'),
        ('2F', '2F | Horizontal-Vertikalposition (PB)'),
        ('2Fr', '2Fr | Horizontal-Vertikal am rotierenden Rohr-Achse waagerecht (PB)'),
        ('2F_', '2F  | Horizontal-Vertikal am festen Rohr-Achse senkrecht (PB)'),
        ('3Fd', '3Fd | Fallposition (PG)'),
        ('3Fu', '3Fu | Steigposition (PF)'),
        ('4F', '4F | Horizontal-Überkopfposition (PD)'),
        ('4F_', '4F | Horizontal-Überkopf am festen Rohr-Achse senkrecht (PD)'),
        ('5Fd', '5Fd | fallend am festen Rohr-Achse waagerecht (PJ)'),
        ('5Fu', '5Fu | Steigend am festen Rohr-Achse waagerecht (PH)'),
        ('1G', '1G | Wannenposition (PA)'),
        ('1G_', '1G | Wanne am rotierenden Rohr-Achse waagerecht (PA)'),
        ('2G', '2G | Querposition (PC)'),
        ('2G_', '2G | quer am festen Rohr-Achse senkrecht (PC)'),
        ('3Gd', '3Gd | fallposition (PG)'),
        ('3Gu', '3Gu | Steigposition (PF)'),
        ('4G', '4G | Überkopfposition (PE)'),
        ('5Gd', '5Gd | fallend am festen Rohr-Achse waagerecht (PJ)'),
        ('5Gu', '5Gu | steigend am festen Rohr-Achse waagerecht (PH)'),
        ('6Gd', '6Gd | fallend am festen Rohr-Achse geneigt(45°) (J-L045)'),
        ('6Gu', '6Gu | steigend am festen Rohr-Achse geneigt(45°) (H-L045)'),
    ], 'Position', readonly = False,
        )
    position_of_groove = fields.Function(fields.Char("Position of Groove"),"On_change_position")
    welding_prog = fields.Function(fields.Char("Welding Progression(Uphill, Downhill)"),"on_change_position2")
    other_position = fields.Char("Other")
    other_position1 = fields.Char("Other")

    preheat_temp = fields.Char("Preheat Temp")
    interpass_temp = fields.Char("Interpass Temp")
    other_preheat = fields.Char("Other")
    other_preheat1 = fields.Char("Other")

    travel_speed = fields.Char("Travel Speed")
    waeve_bead = fields.Char("String or Waeve Bead")
    oscillation = fields.Char("Oscillation")
    multipass = fields.Char("Multipass or single Pass (Per Side)")
    multi_elektrode = fields.Char("Single Or Multiple Elektrodes")
    other_technique = fields.Char("Other")
    other_technique1 = fields.Text("Other")

    schielding_1 = fields.Selection('on_change_welg_prezess','Schielding', readonly = False,)

    schielding = fields.Selection([
        ("ISO 14175-C1-C", "ISO 14175-C1-C | EN ISO 14175 | MAG"),
        ("ISO 14175-I1-Ar", "ISO 14175-I1-Ar | EN ISO 14175 | ARCAL 1 | MIG,WIG,WPL"),
        ("ISO 14175-I2-He", "ISO 14175-I2-He | EN ISO 14175 | MIG,WIG"),
        ("ISO 14175-I3-ArHe-30", "ISO 14175-I3-ArHe-30 | EN ISO 14175 | ARCAL 33 | MIG,WIG,WPL"),
        ("ISO 14175-M12-ArC-2", "ISO 14175-M12-ArC-2 | EN ISO 14175 | ARCAL 12 | MAG"),
        ("ISO 14175-M12-ArHeC-18/1", "ISO 14175-M12-ArHeC-18/1 | EN ISO 14175 | ARCAL 121 | MAG"),
        ("ISO 14175-M13-ArO-2", "ISO 14175-M13-ArO-2 | EN ISO 14175 | CARGAL | MAG"),
        ("ISO 14175-M14-ArCO-3/1", "ISO 14175-M14-ArCO-3/1 | EN ISO 14175 | ARCAL 14 | MAG"),
        ("ISO 14175-M20-ArC-8", "ISO 14175-M20-ArC-8 | EN ISO 14175 | ARCAL 21 | MAG"),
        ("ISO 14175-M21-ArC-18", "ISO 14175-M21-ArC-18 | EN ISO 14175 | ATAL,ARCAL5 | MAG"),
        ("ISO 14175-M22-ArO-8", "ISO 14175-M22-ArO-8 | EN ISO 14175 | CARGAL4 | MAG"),
        ("ISO 14175-M23-ArCO-5/5", "ISO 14175-M23-ArCO-5/5 | EN ISO 14175 | TERAL | MAG"),
        ("ISO 14175-M24-ArCO-12/2", "ISO 14175-M24-ArCO-12/2 | EN ISO 14175 | ARCAL 24 | MAG"),
        ("ISO 14175-N2-ArN-2", "ISO 14175-N2-ArN-2 | EN ISO 14175 | ARCAL 391 | WIG"),
        ("ISO 14175-N4-ArNH-3/0,7", "ISO 14175-N4-ArNH-3/0,7 | EN ISO 14175 | ARCAL 405 | WIG"),
        ("ISO 14175-N5-NH-20", "ISO 14175-N5-NH-20 | EN ISO 14175 | Formiergas 80/20"),
        ("ISO 14175-R1-ArH-10", "ISO 14175-R1-ArH-10 | EN ISO 14175 | NOXAL 4 | WIG"),
        ("ISO 14175-R1-ArH-2,4", "ISO 14175-R1-ArH-2,4 | EN ISO 14175 |ARCAL 10 | WIG,WPL"),
        ("ISO 14175-R2-ArH-20", "ISO 14175-R2-ArH-20 | EN ISO 14175 | ARCAL PLASMA 62"),
        ("ISO 14175-Z-Ar+N-0,015", "ISO 14175-Z-Ar+N-0,015 | EN ISO 14175 | ARCAL 1N | WIG"),
    ], 'Schielding', readonly = False,
        )
    schielding_ = fields.Function(fields.Char("(Mixture)"),"On_change_schielding")
    trailing = fields.Selection([
        ("ISO 14175-C1-C", "ISO 14175-C1-C | EN ISO 14175 | MAG"),
        ("ISO 14175-I1-Ar", "ISO 14175-I1-Ar | EN ISO 14175 | ARCAL 1 | MIG,WIG,WPL"),
        ("ISO 14175-I2-He", "ISO 14175-I2-He | EN ISO 14175 | MIG,WIG"),
        ("ISO 14175-I3-ArHe-30", "ISO 14175-I3-ArHe-30 | EN ISO 14175 | ARCAL 33 | MIG,WIG,WPL"),
        ("ISO 14175-M12-ArC-2", "ISO 14175-M12-ArC-2 | EN ISO 14175 | ARCAL 12 | MAG"),
        ("ISO 14175-M12-ArHeC-18/1", "ISO 14175-M12-ArHeC-18/1 | EN ISO 14175 | ARCAL 121 | MAG"),
        ("ISO 14175-M13-ArO-2", "ISO 14175-M13-ArO-2 | EN ISO 14175 | CARGAL | MAG"),
        ("ISO 14175-M14-ArCO-3/1", "ISO 14175-M14-ArCO-3/1 | EN ISO 14175 | ARCAL 14 | MAG"),
        ("ISO 14175-M20-ArC-8", "ISO 14175-M20-ArC-8 | EN ISO 14175 | ARCAL 21 | MAG"),
        ("ISO 14175-M21-ArC-18", "ISO 14175-M21-ArC-18 | EN ISO 14175 | ATAL,ARCAL5 | MAG"),
        ("ISO 14175-M22-ArO-8", "ISO 14175-M22-ArO-8 | EN ISO 14175 | CARGAL4 | MAG"),
        ("ISO 14175-M23-ArCO-5/5", "ISO 14175-M23-ArCO-5/5 | EN ISO 14175 | TERAL | MAG"),
        ("ISO 14175-M24-ArCO-12/2", "ISO 14175-M24-ArCO-12/2 | EN ISO 14175 | ARCAL 24 | MAG"),
        ("ISO 14175-N2-ArN-2", "ISO 14175-N2-ArN-2 | EN ISO 14175 | ARCAL 391 | WIG"),
        ("ISO 14175-N4-ArNH-3/0,7", "ISO 14175-N4-ArNH-3/0,7 | EN ISO 14175 | ARCAL 405 | WIG"),
        ("ISO 14175-N5-NH-20", "ISO 14175-N5-NH-20 | EN ISO 14175 | Formiergas 80/20"),
        ("ISO 14175-R1-ArH-10", "ISO 14175-R1-ArH-10 | EN ISO 14175 | NOXAL 4 | WIG"),
        ("ISO 14175-R1-ArH-2,4", "ISO 14175-R1-ArH-2,4 | EN ISO 14175 |ARCAL 10 | WIG,WPL"),
        ("ISO 14175-R2-ArH-20", "ISO 14175-R2-ArH-20 | EN ISO 14175 | ARCAL PLASMA 62"),
        ("ISO 14175-Z-Ar+N-0,015", "ISO 14175-Z-Ar+N-0,015 | EN ISO 14175 | ARCAL 1N | WIG"),
    ], 'Trailing', readonly = False,
        )
    trailing_ = fields.Function(fields.Char("trailing_"),"On_change_trailing")
    trailing_1 = fields.Selection('on_change_welg_prezess1','Trailing', readonly = False,)

    backing = fields.Selection([
        ("ISO 14175-C1-C", "ISO 14175-C1-C | EN ISO 14175 | MAG"),
        ("ISO 14175-I1-Ar", "ISO 14175-I1-Ar | EN ISO 14175 | ARCAL 1 | MIG,WIG,WPL"),
        ("ISO 14175-I2-He", "ISO 14175-I2-He | EN ISO 14175 | MIG,WIG"),
        ("ISO 14175-I3-ArHe-30", "ISO 14175-I3-ArHe-30 | EN ISO 14175 | ARCAL 33 | MIG,WIG,WPL"),
        ("ISO 14175-M12-ArC-2", "ISO 14175-M12-ArC-2 | EN ISO 14175 | ARCAL 12 | MAG"),
        ("ISO 14175-M12-ArHeC-18/1", "ISO 14175-M12-ArHeC-18/1 | EN ISO 14175 | ARCAL 121 | MAG"),
        ("ISO 14175-M13-ArO-2", "ISO 14175-M13-ArO-2 | EN ISO 14175 | CARGAL | MAG"),
        ("ISO 14175-M14-ArCO-3/1", "ISO 14175-M14-ArCO-3/1 | EN ISO 14175 | ARCAL 14 | MAG"),
        ("ISO 14175-M20-ArC-8", "ISO 14175-M20-ArC-8 | EN ISO 14175 | ARCAL 21 | MAG"),
        ("ISO 14175-M21-ArC-18", "ISO 14175-M21-ArC-18 | EN ISO 14175 | ATAL,ARCAL5 | MAG"),
        ("ISO 14175-M22-ArO-8", "ISO 14175-M22-ArO-8 | EN ISO 14175 | CARGAL4 | MAG"),
        ("ISO 14175-M23-ArCO-5/5", "ISO 14175-M23-ArCO-5/5 | EN ISO 14175 | TERAL | MAG"),
        ("ISO 14175-M24-ArCO-12/2", "ISO 14175-M24-ArCO-12/2 | EN ISO 14175 | ARCAL 24 | MAG"),
        ("ISO 14175-N2-ArN-2", "ISO 14175-N2-ArN-2 | EN ISO 14175 | ARCAL 391 | WIG"),
        ("ISO 14175-N4-ArNH-3/0,7", "ISO 14175-N4-ArNH-3/0,7 | EN ISO 14175 | ARCAL 405 | WIG"),
        ("ISO 14175-N5-NH-20", "ISO 14175-N5-NH-20 | EN ISO 14175 | Formiergas 80/20"),
        ("ISO 14175-R1-ArH-10", "ISO 14175-R1-ArH-10 | EN ISO 14175 | NOXAL 4 | WIG"),
        ("ISO 14175-R1-ArH-2,4", "ISO 14175-R1-ArH-2,4 | EN ISO 14175 |ARCAL 10 | WIG,WPL"),
        ("ISO 14175-R2-ArH-20", "ISO 14175-R2-ArH-20 | EN ISO 14175 | ARCAL PLASMA 62"),
        ("ISO 14175-Z-Ar+N-0,015", "ISO 14175-Z-Ar+N-0,015 | EN ISO 14175 | ARCAL 1N | WIG"),
    ], 'Backing', readonly = False,
        )
    backing_ = fields.Function(fields.Char("backing_"),"On_change_backing")
    backing_1 = fields.Selection('on_change_welg_prezess2','Backing', readonly = False,)

    current = fields.Selection([
        ('A.C.', 'A.C. | Wechselstrom'),
        ('Alternating Current', 'Alternating Current | Wechselstrom'),
        ('Alternating', 'Alternating | Wechselstrom'),
        ('D.C.', 'D.C. | Gleichstrom'),
        ('Direct Current', 'Direct Current | Gleichstrom'),
        ('Direct', 'Direct | Gleichstrom'),
    ], 'Current', readonly = False,
        )
    polarity = fields.Selection([
        ('plus', 'plus | + Pol an der Elektrode (Schweißdraht)'),
        ('minus', 'minus | - Pol an der Elektrode (Schweißdraht)'),
        ('Reverse', 'Reverse | entgegengesetzte Polarität'),
    ], 'Polarity', readonly = False,
        )
    amps = fields.Char("Amps")
    volt = fields.Char("Volts")
    tungsten = fields.Char("Tungsten Electrode Size")
    mode = fields.Char("Mode of Metal Transfert for GMAW (FCAW)")
    heat = fields.Char("Heat Input")
    other_electrical = fields.Char("Other")
    other_electrical1 = fields.Char("Other")


    p_no = fields.Selection('on_change_matriall3','P-No', readonly = False,)
    p_no1 = fields.Function(fields.Char("to P-No."),"on_change_matriall4")
    group_no1 = fields.Char("Group No")
    matrial3 = fields.Selection('on_change_matriall2','Material Spec2', readonly = False,)

    welding_prozess = fields.Selection([
        ('OFW', 'OFW | Oxyfuel Gas Welding | 31 | Gas'),
        ('OAW', 'OAW | Oxyacetylene Welding | 311 | Gas'),
        ('OHW', 'OHW | Oxyhydrogen Welding | 313 | Gas'),
        ('SMAW','SMAW | Shielded Metal-Arc Welding | 111 | E'),
        ('SMAW/SAW', 'SMAW/SAW | Root run SMAW, fill up with SAW | 111/121 | E/UP'),
        ('SMAW/GMAW', 'SMAW/GMAW | Root run SMAW, fill up with GMAW | 111/135 | E/MAG'),
        ('SAW', 'SAW | Submerged-Arc Welding | 12 | UP'),
        ('GMAW', 'GMAW | Gas Metal-Arc Welding | 135 | MAG'),
        ('FCAW', 'FCAW | Flux Cored-Arc Welding | 136 | MAG'),
        ('GMAW/SMAW', 'GMAW/SMAW |Root run GMAW, fill up with SMAW | 135/111 | MAG/E'),
        ('GMAW/SAW', 'GMAW/SAW | Root run GMAW, fill up with SAW | 135/121 | MAG/UP'),
        ('FCAW-S', 'FCAW-S | Metal Cored Wire-Arc Welding | 133 | MIG'),
        ('GTAW', 'GTAW | Gas Tungsten-Arc Welding | 141 | WIG'),
        ('GTAW/SMAW', 'GTAW/SMAW | Root run GTAW, fill up with SMAW | 141/111 | WIG/E '),
        ('GTAW/SAW', 'GTAW/SAW | Root run GTAW, fill up with SAW | 141/121 | WIG/UP'),
        ('GTAW/GMAW', 'GTAW/GMAW | Root run GTAW, fill up with GMAW | 141/135 | WIG/MAG'),
        ('PAW', 'PAW | Plasma-Arc Welding | 15 | WPL '),
        ('ESW', 'ESW | Electroslag Welding | 72 | RES'),
        ('EGW', 'EGW | Electrosgas Welding | 73 | MSGG'),
        ('EBW', 'EBW | Electron Beam Welding | 51 | EB'),
        ('EBW-HV', 'EBW-HV | Electron Beam Welding in vacuum | 511 | EB'),
        ('EBW-NV', 'EBW-NV | Electron Beam Welding in atmosphere | 512 | EB'),
        ('SW', 'SW | Stud Welding | 78 | DS'),
        ('FRW', 'FRW | Inertia and Continuous Drive Friction Welding | 42 | FR'),
        ('FRW-DD', 'FRW-DD | Direct Drive Friction Welding | 421'),
        ('FRW-I', 'FRW-I | Inertia Friction Welding | 422'),
        ('RW', 'Rw | Resistance Welding | 2'),
        ('LBW', 'LBW | Laser Beam Welding | 52 | LA'),
        ('FW', 'FW | Flash Welding | 24'),
        ('DFW', 'DFW | Diffusion Welding | 45'),
        ('FSW', 'FSW | Friction Stir Welding | 43'),
        ('LBW+GMAW', 'LBW+GMAW | Hybrid Laser-GMAW | 52+135 | LA+MAG'),
        ('PAW+GMAW', 'PAW+GMAW | Hybrid Plasma-GMAW | 15+135 | WPL+MAG'),
    ], 'Welding Process(es)', readonly = False,
        )
    welding1 = fields.Function(fields.Char(" "),"On_change_welding")
    welding2 = fields.Function(fields.Char(" "),"On_change_welding2")
    type = fields.Selection([
        ('Manual', 'Manual'),
        ('Semi-Auto', 'Semi-Auto'),
        ('Machine', 'Machine'),
        ('Automatic', 'Automatic'),
    ], 'Types (Manual, Automatic, Semi-Automatic)', readonly = False,
        )
    space = fields.Char("                                                                                                                                                        ")
    bild = fields.Binary("Groove Design of Test Coupon                                                                                              ")
    empfehlung = fields.Selection([
        ('_2_3_dv', '_2_3_dv | Unsymmetrische D(oppel)-V-Fuge'),
        ('_boerd_n', '_boerd_n | Kanten bördeln'),
        ('_dhu_bw', '_dhu_bw | DHU-Fuge am stumpfstoß'),
        ('_dhu_fw', '_dhu_fw | DHU-Fuge am T-Stoß'),
    ], 'Empfehlung', readonly = False,
        )
    alle = fields.Boolean("Alle")
    sous_titre = fields.Char("(For combination qualifications, the deposited weld metal thickness shall be recorded for each filler metal or process used.)")


    @fields.depends('backing_1', 'welding_prozess')
    def on_change_welg_prezess2(self):
      tab=[]
      if(self.welding_prozess=="LBW" or self.welding_prozess=="FRW" or self.welding_prozess=="SW" or self.welding_prozess=="EBW-NV" or self.welding_prozess=="EBW-HV" or self.welding_prozess=="EBW" or self.welding_prozess =="OFW" or self.welding_prozess == "OAW" or self.welding_prozess =="OHW" or self.welding_prozess=="SMAW" or self.welding_prozess=="SAW" or self.welding_prozess=="ESW"):
        tab.append(("ISO 14175-N5-NH-20","ISO 14175-N5-NH-20 | EN ISO 14175 | Formiergas 80/20"))
        tab.append(("ISO 14175-R2-ArH-20","ISO 14175-R2-ArH-20 | EN ISO 14175 | ARCAL PLASMA 62"))
        return tab
      if(self.welding_prozess =="FCAW-S" or self.welding_prozess=="PAW"):
        tab.append(("ISO 14175-I1-Ar", "ISO 14175-I1-Ar | EN ISO 14175 | ARCAL 1 | MIG,WIG,WPL"))
        tab.append(("ISO 14175-I2-He", "ISO 14175-I2-He | EN ISO 14175 | MIG,WIG"))
        tab.append(("ISO 14175-I3-ArHe-30", "ISO 14175-I3-ArHe-30 | EN ISO 14175 | ARCAL 33 | MIG,WIG,WPL"))
        tab.append(("ISO 14175-N5-NH-20", "ISO 14175-N5-NH-20 | EN ISO 14175 | Formiergas 80/20"))
        tab.append(("ISO 14175-R2-ArH-20", "ISO 14175-R2-ArH-20 | EN ISO 14175 | ARCAL PLASMA 62"))
        return tab
      if(self.welding_prozess =="GMAW" or self.welding_prozess =="FCAW"):
        tab.append(("ISO 14175-C1-C", "ISO 14175-C1-C | EN ISO 14175 | MAG"))
        tab.append(("ISO 14175-M12-ArC-2", "ISO 14175-M12-ArC-2 | EN ISO 14175 | ARCAL 12 | MAG"))
        tab.append(("ISO 14175-M12-ArHeC-18/1", "ISO 14175-M12-ArHeC-18/1 | EN ISO 14175 | ARCAL 121 | MAG"))
        tab.append(("ISO 14175-M13-ArO-2", "ISO 14175-M13-ArO-2 | EN ISO 14175 | CARGAL | MAG"))
        tab.append(("ISO 14175-M14-ArCO-3/1", "ISO 14175-M14-ArCO-3/1 | EN ISO 14175 | ARCAL 14 | MAG"))
        tab.append(("ISO 14175-M20-ArC-8", "ISO 14175-M20-ArC-8 | EN ISO 14175 | ARCAL 21 | MAG"))
        tab.append(("ISO 14175-M21-ArC-18", "ISO 14175-M21-ArC-18 | EN ISO 14175 | ATAL,ARCAL5 | MAG"))
        tab.append(("ISO 14175-M22-ArO-8", "ISO 14175-M22-ArO-8 | EN ISO 14175 | CARGAL4 | MAG"))
        tab.append(("ISO 14175-M23-ArCO-5/5", "ISO 14175-M23-ArCO-5/5 | EN ISO 14175 | TERAL | MAG"))
        tab.append(("ISO 14175-M24-ArCO-12/2", "ISO 14175-M24-ArCO-12/2 | EN ISO 14175 | ARCAL 24 | MAG"))
        tab.append(("ISO 14175-N5-NH-20", "ISO 14175-N5-NH-20 | EN ISO 14175 | Formiergas 80/20"))
        tab.append(("ISO 14175-R2-ArH-20", "ISO 14175-R2-ArH-20 | EN ISO 14175 | ARCAL PLASMA 62"))
        return tab
      else:
        if(self.welding_prozess== "PAW+GMAW" or self.welding_prozess=="LBW+GMAW" or self.welding_prozess=="FSW" or self.welding_prozess=="DFW" or self.welding_prozess=="FW" or self.welding_prozess=="RW" or self.welding_prozess=="FRW-I" or self.welding_prozess=="FRW-DD" or self.welding_prozess=="EGW" or self.welding_prozess=="GTAW/GMAW" or self.welding_prozess=="GTAW/SAW" or self.welding_prozess=="GTAW/SMAW" or self.welding_prozess=="GTAW" or self.welding_prozess == "SMAW/SAW" or self.welding_prozess=="SMAW/GMAW" or self.welding_prozess=="GMAW/SMAW" or self.welding_prozess=="GMAW/SAW"):
          tab.append(("ISO 14175-C1-C", "ISO 14175-C1-C | EN ISO 14175 | MAG"))
          tab.append(("ISO 14175-I1-Ar", "ISO 14175-I1-Ar | EN ISO 14175 | ARCAL 1 | MIG,WIG,WPL"))
          tab.append(("ISO 14175-I2-He", "ISO 14175-I2-He | EN ISO 14175 | MIG,WIG"))
          tab.append(("ISO 14175-I3-ArHe-30", "ISO 14175-I3-ArHe-30 | EN ISO 14175 | ARCAL 33 | MIG,WIG,WPL"))
          tab.append(("ISO 14175-M12-ArC-2", "ISO 14175-M12-ArC-2 | EN ISO 14175 | ARCAL 12 | MAG"))
          tab.append(("ISO 14175-M12-ArHeC-18/1", "ISO 14175-M12-ArHeC-18/1 | EN ISO 14175 | ARCAL 121 | MAG"))
          tab.append(("ISO 14175-M13-ArO-2", "ISO 14175-M13-ArO-2 | EN ISO 14175 | CARGAL | MAG"))
          tab.append(("ISO 14175-M14-ArCO-3/1", "ISO 14175-M14-ArCO-3/1 | EN ISO 14175 | ARCAL 14 | MAG"))
          tab.append(("ISO 14175-M20-ArC-8", "ISO 14175-M20-ArC-8 | EN ISO 14175 | ARCAL 21 | MAG"))
          tab.append(("ISO 14175-M21-ArC-18", "ISO 14175-M21-ArC-18 | EN ISO 14175 | ATAL,ARCAL5 | MAG"))
          tab.append(("ISO 14175-M22-ArO-8", "ISO 14175-M22-ArO-8 | EN ISO 14175 | CARGAL4 | MAG"))
          tab.append(("ISO 14175-M23-ArCO-5/5", "ISO 14175-M23-ArCO-5/5 | EN ISO 14175 | TERAL | MAG"))
          tab.append(("ISO 14175-M24-ArCO-12/2", "ISO 14175-M24-ArCO-12/2 | EN ISO 14175 | ARCAL 24 | MAG"))
          tab.append(("ISO 14175-N2-ArN-2", "ISO 14175-N2-ArN-2 | EN ISO 14175 | ARCAL 391 | WIG"))
          tab.append(("ISO 14175-N4-ArNH-3/0,7", "ISO 14175-N4-ArNH-3/0,7 | EN ISO 14175 | ARCAL 405 | WIG"))
          tab.append(("ISO 14175-N5-NH-20", "ISO 14175-N5-NH-20 | EN ISO 14175 | Formiergas 80/20"))
          tab.append(("ISO 14175-R1-ArH-10", "ISO 14175-R1-ArH-10 | EN ISO 14175 | NOXAL 4 | WIG"))
          tab.append(("ISO 14175-R1-ArH-2,4", "ISO 14175-R1-ArH-2,4 | EN ISO 14175 |ARCAL 10 | WIG,WPL"))
          tab.append(("ISO 14175-R2-ArH-20", "ISO 14175-R2-ArH-20 | EN ISO 14175 | ARCAL PLASMA 62"))
          tab.append(("ISO 14175-Z-Ar+N-0,015", "ISO 14175-Z-Ar+N-0,015 | EN ISO 14175 | ARCAL 1N | WIG"))
          return tab

    @fields.depends('trailing_1', 'welding_prozess')
    def on_change_welg_prezess1(self):
      tab=[]
      if(self.welding_prozess=="LBW" or self.welding_prozess=="FRW" or self.welding_prozess=="SW" or self.welding_prozess=="EBW-NV" or self.welding_prozess=="EBW-HV" or self.welding_prozess=="EBW" or self.welding_prozess =="OFW" or self.welding_prozess == "OAW" or self.welding_prozess =="OHW" or self.welding_prozess=="SMAW" or self.welding_prozess=="SAW" or self.welding_prozess=="ESW"):
        tab.append(("ISO 14175-N5-NH-20","ISO 14175-N5-NH-20 | EN ISO 14175 | Formiergas 80/20"))
        tab.append(("ISO 14175-R2-ArH-20","ISO 14175-R2-ArH-20 | EN ISO 14175 | ARCAL PLASMA 62"))
        return tab
      if(self.welding_prozess =="FCAW-S" or self.welding_prozess=="PAW"):
        tab.append(("ISO 14175-I1-Ar", "ISO 14175-I1-Ar | EN ISO 14175 | ARCAL 1 | MIG,WIG,WPL"))
        tab.append(("ISO 14175-I2-He", "ISO 14175-I2-He | EN ISO 14175 | MIG,WIG"))
        tab.append(("ISO 14175-I3-ArHe-30", "ISO 14175-I3-ArHe-30 | EN ISO 14175 | ARCAL 33 | MIG,WIG,WPL"))
        tab.append(("ISO 14175-N5-NH-20", "ISO 14175-N5-NH-20 | EN ISO 14175 | Formiergas 80/20"))
        tab.append(("ISO 14175-R2-ArH-20", "ISO 14175-R2-ArH-20 | EN ISO 14175 | ARCAL PLASMA 62"))
        return tab

      if(self.welding_prozess =="GMAW" or self.welding_prozess =="FCAW"):
        tab.append(("ISO 14175-C1-C", "ISO 14175-C1-C | EN ISO 14175 | MAG"))
        tab.append(("ISO 14175-M12-ArC-2", "ISO 14175-M12-ArC-2 | EN ISO 14175 | ARCAL 12 | MAG"))
        tab.append(("ISO 14175-M12-ArHeC-18/1", "ISO 14175-M12-ArHeC-18/1 | EN ISO 14175 | ARCAL 121 | MAG"))
        tab.append(("ISO 14175-M13-ArO-2", "ISO 14175-M13-ArO-2 | EN ISO 14175 | CARGAL | MAG"))
        tab.append(("ISO 14175-M14-ArCO-3/1", "ISO 14175-M14-ArCO-3/1 | EN ISO 14175 | ARCAL 14 | MAG"))
        tab.append(("ISO 14175-M20-ArC-8", "ISO 14175-M20-ArC-8 | EN ISO 14175 | ARCAL 21 | MAG"))
        tab.append(("ISO 14175-M21-ArC-18", "ISO 14175-M21-ArC-18 | EN ISO 14175 | ATAL,ARCAL5 | MAG"))
        tab.append(("ISO 14175-M22-ArO-8", "ISO 14175-M22-ArO-8 | EN ISO 14175 | CARGAL4 | MAG"))
        tab.append(("ISO 14175-M23-ArCO-5/5", "ISO 14175-M23-ArCO-5/5 | EN ISO 14175 | TERAL | MAG"))
        tab.append(("ISO 14175-M24-ArCO-12/2", "ISO 14175-M24-ArCO-12/2 | EN ISO 14175 | ARCAL 24 | MAG"))
        tab.append(("ISO 14175-N5-NH-20", "ISO 14175-N5-NH-20 | EN ISO 14175 | Formiergas 80/20"))
        tab.append(("ISO 14175-R2-ArH-20", "ISO 14175-R2-ArH-20 | EN ISO 14175 | ARCAL PLASMA 62"))
        return tab
      else:
        if(self.welding_prozess== "PAW+GMAW" or self.welding_prozess=="LBW+GMAW" or self.welding_prozess=="FSW" or self.welding_prozess=="DFW" or self.welding_prozess=="FW" or self.welding_prozess=="RW" or self.welding_prozess=="FRW-I" or self.welding_prozess=="FRW-DD" or self.welding_prozess=="EGW" or self.welding_prozess=="GTAW/GMAW" or self.welding_prozess=="GTAW/SAW" or self.welding_prozess=="GTAW/SMAW" or self.welding_prozess=="GTAW" or self.welding_prozess == "SMAW/SAW" or self.welding_prozess=="SMAW/GMAW" or self.welding_prozess=="GMAW/SMAW" or self.welding_prozess=="GMAW/SAW"):
          tab.append(("ISO 14175-C1-C", "ISO 14175-C1-C | EN ISO 14175 | MAG"))
          tab.append(("ISO 14175-I1-Ar", "ISO 14175-I1-Ar | EN ISO 14175 | ARCAL 1 | MIG,WIG,WPL"))
          tab.append(("ISO 14175-I2-He", "ISO 14175-I2-He | EN ISO 14175 | MIG,WIG"))
          tab.append(("ISO 14175-I3-ArHe-30", "ISO 14175-I3-ArHe-30 | EN ISO 14175 | ARCAL 33 | MIG,WIG,WPL"))
          tab.append(("ISO 14175-M12-ArC-2", "ISO 14175-M12-ArC-2 | EN ISO 14175 | ARCAL 12 | MAG"))
          tab.append(("ISO 14175-M12-ArHeC-18/1", "ISO 14175-M12-ArHeC-18/1 | EN ISO 14175 | ARCAL 121 | MAG"))
          tab.append(("ISO 14175-M13-ArO-2", "ISO 14175-M13-ArO-2 | EN ISO 14175 | CARGAL | MAG"))
          tab.append(("ISO 14175-M14-ArCO-3/1", "ISO 14175-M14-ArCO-3/1 | EN ISO 14175 | ARCAL 14 | MAG"))
          tab.append(("ISO 14175-M20-ArC-8", "ISO 14175-M20-ArC-8 | EN ISO 14175 | ARCAL 21 | MAG"))
          tab.append(("ISO 14175-M21-ArC-18", "ISO 14175-M21-ArC-18 | EN ISO 14175 | ATAL,ARCAL5 | MAG"))
          tab.append(("ISO 14175-M22-ArO-8", "ISO 14175-M22-ArO-8 | EN ISO 14175 | CARGAL4 | MAG"))
          tab.append(("ISO 14175-M23-ArCO-5/5", "ISO 14175-M23-ArCO-5/5 | EN ISO 14175 | TERAL | MAG"))
          tab.append(("ISO 14175-M24-ArCO-12/2", "ISO 14175-M24-ArCO-12/2 | EN ISO 14175 | ARCAL 24 | MAG"))
          tab.append(("ISO 14175-N2-ArN-2", "ISO 14175-N2-ArN-2 | EN ISO 14175 | ARCAL 391 | WIG"))
          tab.append(("ISO 14175-N4-ArNH-3/0,7", "ISO 14175-N4-ArNH-3/0,7 | EN ISO 14175 | ARCAL 405 | WIG"))
          tab.append(("ISO 14175-N5-NH-20", "ISO 14175-N5-NH-20 | EN ISO 14175 | Formiergas 80/20"))
          tab.append(("ISO 14175-R1-ArH-10", "ISO 14175-R1-ArH-10 | EN ISO 14175 | NOXAL 4 | WIG"))
          tab.append(("ISO 14175-R1-ArH-2,4", "ISO 14175-R1-ArH-2,4 | EN ISO 14175 |ARCAL 10 | WIG,WPL"))
          tab.append(("ISO 14175-R2-ArH-20", "ISO 14175-R2-ArH-20 | EN ISO 14175 | ARCAL PLASMA 62"))
          tab.append(("ISO 14175-Z-Ar+N-0,015", "ISO 14175-Z-Ar+N-0,015 | EN ISO 14175 | ARCAL 1N | WIG"))
          return tab


    @fields.depends('schielding_1', 'welding_prozess')
    def on_change_welg_prezess(self):
      tab=[]
      if(self.welding_prozess=="LBW" or self.welding_prozess=="FRW" or self.welding_prozess=="SW" or self.welding_prozess=="EBW-NV" or self.welding_prozess=="EBW-HV" or self.welding_prozess=="EBW" or self.welding_prozess =="OFW" or self.welding_prozess == "OAW" or self.welding_prozess =="OHW" or self.welding_prozess=="SMAW" or self.welding_prozess=="SAW" or self.welding_prozess=="ESW"):
        tab.append(("ISO 14175-N5-NH-20","ISO 14175-N5-NH-20 | EN ISO 14175 | Formiergas 80/20"))
        tab.append(("ISO 14175-R2-ArH-20","ISO 14175-R2-ArH-20 | EN ISO 14175 | ARCAL PLASMA 62"))
        return tab
      if(self.welding_prozess =="FCAW-S" or self.welding_prozess=="PAW"):
        tab.append(("ISO 14175-I1-Ar", "ISO 14175-I1-Ar | EN ISO 14175 | ARCAL 1 | MIG,WIG,WPL"))
        tab.append(("ISO 14175-I2-He", "ISO 14175-I2-He | EN ISO 14175 | MIG,WIG"))
        tab.append(("ISO 14175-I3-ArHe-30", "ISO 14175-I3-ArHe-30 | EN ISO 14175 | ARCAL 33 | MIG,WIG,WPL"))
        tab.append(("ISO 14175-N5-NH-20", "ISO 14175-N5-NH-20 | EN ISO 14175 | Formiergas 80/20"))
        tab.append(("ISO 14175-R2-ArH-20", "ISO 14175-R2-ArH-20 | EN ISO 14175 | ARCAL PLASMA 62"))
        return tab

      if(self.welding_prozess =="GMAW" or self.welding_prozess =="FCAW"):
        tab.append(("ISO 14175-C1-C", "ISO 14175-C1-C | EN ISO 14175 | MAG"))
        tab.append(("ISO 14175-M12-ArC-2", "ISO 14175-M12-ArC-2 | EN ISO 14175 | ARCAL 12 | MAG"))
        tab.append(("ISO 14175-M12-ArHeC-18/1", "ISO 14175-M12-ArHeC-18/1 | EN ISO 14175 | ARCAL 121 | MAG"))
        tab.append(("ISO 14175-M13-ArO-2", "ISO 14175-M13-ArO-2 | EN ISO 14175 | CARGAL | MAG"))
        tab.append(("ISO 14175-M14-ArCO-3/1", "ISO 14175-M14-ArCO-3/1 | EN ISO 14175 | ARCAL 14 | MAG"))
        tab.append(("ISO 14175-M20-ArC-8", "ISO 14175-M20-ArC-8 | EN ISO 14175 | ARCAL 21 | MAG"))
        tab.append(("ISO 14175-M21-ArC-18", "ISO 14175-M21-ArC-18 | EN ISO 14175 | ATAL,ARCAL5 | MAG"))
        tab.append(("ISO 14175-M22-ArO-8", "ISO 14175-M22-ArO-8 | EN ISO 14175 | CARGAL4 | MAG"))
        tab.append(("ISO 14175-M23-ArCO-5/5", "ISO 14175-M23-ArCO-5/5 | EN ISO 14175 | TERAL | MAG"))
        tab.append(("ISO 14175-M24-ArCO-12/2", "ISO 14175-M24-ArCO-12/2 | EN ISO 14175 | ARCAL 24 | MAG"))
        tab.append(("ISO 14175-N5-NH-20", "ISO 14175-N5-NH-20 | EN ISO 14175 | Formiergas 80/20"))
        tab.append(("ISO 14175-R2-ArH-20", "ISO 14175-R2-ArH-20 | EN ISO 14175 | ARCAL PLASMA 62"))
        return tab
      else:
        if(self.welding_prozess== "PAW+GMAW" or self.welding_prozess=="LBW+GMAW" or self.welding_prozess=="FSW" or self.welding_prozess=="DFW" or self.welding_prozess=="FW" or self.welding_prozess=="RW" or self.welding_prozess=="FRW-I" or self.welding_prozess=="FRW-DD" or self.welding_prozess=="EGW" or self.welding_prozess=="GTAW/GMAW" or self.welding_prozess=="GTAW/SAW" or self.welding_prozess=="GTAW/SMAW" or self.welding_prozess=="GTAW" or self.welding_prozess == "SMAW/SAW" or self.welding_prozess=="SMAW/GMAW" or self.welding_prozess=="GMAW/SMAW" or self.welding_prozess=="GMAW/SAW"):
          tab.append(("ISO 14175-C1-C", "ISO 14175-C1-C | EN ISO 14175 | MAG"))
          tab.append(("ISO 14175-I1-Ar", "ISO 14175-I1-Ar | EN ISO 14175 | ARCAL 1 | MIG,WIG,WPL"))
          tab.append(("ISO 14175-I2-He", "ISO 14175-I2-He | EN ISO 14175 | MIG,WIG"))
          tab.append(("ISO 14175-I3-ArHe-30", "ISO 14175-I3-ArHe-30 | EN ISO 14175 | ARCAL 33 | MIG,WIG,WPL"))
          tab.append(("ISO 14175-M12-ArC-2", "ISO 14175-M12-ArC-2 | EN ISO 14175 | ARCAL 12 | MAG"))
          tab.append(("ISO 14175-M12-ArHeC-18/1", "ISO 14175-M12-ArHeC-18/1 | EN ISO 14175 | ARCAL 121 | MAG"))
          tab.append(("ISO 14175-M13-ArO-2", "ISO 14175-M13-ArO-2 | EN ISO 14175 | CARGAL | MAG"))
          tab.append(("ISO 14175-M14-ArCO-3/1", "ISO 14175-M14-ArCO-3/1 | EN ISO 14175 | ARCAL 14 | MAG"))
          tab.append(("ISO 14175-M20-ArC-8", "ISO 14175-M20-ArC-8 | EN ISO 14175 | ARCAL 21 | MAG"))
          tab.append(("ISO 14175-M21-ArC-18", "ISO 14175-M21-ArC-18 | EN ISO 14175 | ATAL,ARCAL5 | MAG"))
          tab.append(("ISO 14175-M22-ArO-8", "ISO 14175-M22-ArO-8 | EN ISO 14175 | CARGAL4 | MAG"))
          tab.append(("ISO 14175-M23-ArCO-5/5", "ISO 14175-M23-ArCO-5/5 | EN ISO 14175 | TERAL | MAG"))
          tab.append(("ISO 14175-M24-ArCO-12/2", "ISO 14175-M24-ArCO-12/2 | EN ISO 14175 | ARCAL 24 | MAG"))
          tab.append(("ISO 14175-N2-ArN-2", "ISO 14175-N2-ArN-2 | EN ISO 14175 | ARCAL 391 | WIG"))
          tab.append(("ISO 14175-N4-ArNH-3/0,7", "ISO 14175-N4-ArNH-3/0,7 | EN ISO 14175 | ARCAL 405 | WIG"))
          tab.append(("ISO 14175-N5-NH-20", "ISO 14175-N5-NH-20 | EN ISO 14175 | Formiergas 80/20"))
          tab.append(("ISO 14175-R1-ArH-10", "ISO 14175-R1-ArH-10 | EN ISO 14175 | NOXAL 4 | WIG"))
          tab.append(("ISO 14175-R1-ArH-2,4", "ISO 14175-R1-ArH-2,4 | EN ISO 14175 |ARCAL 10 | WIG,WPL"))
          tab.append(("ISO 14175-R2-ArH-20", "ISO 14175-R2-ArH-20 | EN ISO 14175 | ARCAL PLASMA 62"))
          tab.append(("ISO 14175-Z-Ar+N-0,015", "ISO 14175-Z-Ar+N-0,015 | EN ISO 14175 | ARCAL 1N | WIG"))
          return tab

    def on_change_automatique(self,position):
         return self.id

    def on_change_automatique1(self,position):
         return "PQR-"+str(self.id)

    def get_automatic_id(self,position):
         return "PQR-"+str(self.id)

    def get_automatic_ausstellung(self,datum_ausstellung):
         return self.datum_ausstellung


    def on_change_andere(self,position):
       if(self.welding_prozess is not None):
         #return "ASME PQR "+self.welding_prozess+" "+self.position[1]+" "+self.p_no+"/"+self.p_no1+" "+self.position
         return "ASME PQR "
       else:
         return" "

    def On_change_position(self,position):
      if(self.position == "1F"):
        return"1F"
      if(self.position == "2F" or self.position == "2Fr" or self.position == "2F_"):
        return"2F"
      if(self.position == "3Fd" or self.position == "3Fu"):
        return"3F"
      if(self.position == "4F" or self.position == "4F_"):
        return"4F"
      if(self.position == "1G" or self.position == "1G_"):
        return"1G"
      if(self.position == "2G" or self.position == "2G_"):
        return"2G"
      if(self.position == "3Gd" or self.position == "3Gu"):
        return"3G"
      if(self.position == "4G"):
        return"4G"
      if(self.position == "5Gd" or self.position == "5Gu"):
        return"5G"
      if(self.position == "6Gd" or self.position == "6Gu"):
        return"6G"
      else:
        if(self.position == "5Fu" or self.position == "5Fd"):
          return "5F"

    def on_change_position2(self,position):
      if(self.position == "3Fd" or self.position =="5Fd" or self.position == "3Gd" or self.position == "5Gd" or self.position == "6Gd"):
        return "Downhill"
      else:
        if(self.position == "3Fu" or self.position =="5Fu" or self.position == "3Gu" or self.position == "5Gu" or self.position == "6Gu"):
          return "Uphill"

    def on_Change_fm12(self,fm1):
      if(self.fm1 is not None):
        return "-"
      else:
        return " "

    def on_Change_fm22(self,fm2):
      if(self.fm2 is not None):
        return "-"
      else:
        return " "


    def on_Change_fm11(self,fm1):
      if(self.fm1 is not None):
        return self.fm1.classification
      else:
        return " "

    def on_Change_fm21(self,fm2):
      if(self.fm2 is not None):
        return self.fm2.classification
      else:
        return " "


    def on_Change_fm1(self,fm1):
      if(self.fm1 is not None):
        return self.fm1.sfa
      else:
        return " "

    def on_Change_fm2(self,fm2):
      if(self.fm2 is not None):
        return self.fm2.sfa
      else:
        return " "

    def On_change_schielding(self,schielding):
      if(self.schielding == "ISO 14175-C1-C"):
         return "100%CO2"
      if(self.schielding == "ISO 14175-I2-He"):
         return "100%He"
      if(self.schielding == "ISO 14175-I3-ArHe-30"):
         return "70%Ar,30%He"
      if(self.schielding == "ISO 14175-M12-ArC-2"):
         return "98%Ar,2%CO2"
      if(self.schielding == "ISO 14175-M12-ArHeC-18/1"):
         return "81%Ar,18%He,1%CO2"
      if(self.schielding == "ISO 14175-M13-ArO-2"):
         return "98%Ar,2%O2"
      if(self.schielding == "ISO 14175-M14-ArCO-3/1"):
         return "96%Ar,3%CO2,1%O2"
      if(self.schielding == "ISO 14175-M20-ArC-8"):
         return "92%Ar, 8%CO2"
      if(self.schielding == "ISO 14175-M21-ArC-18"):
         return "82%Ar, 18%CO2"
      if(self.schielding == "ISO 14175-M22-ArO-8"):
         return "92%Ar, 8% O2"
      if(self.schielding == "ISO 14175-M23-ArCO-5/5"):
         return "90% Ar, 5%CO2, 5%O2"
      if(self.schielding == "ISO 14175-M24-ArCO-12/2"):
         return "86%Ar, 12%CO2, 2%O2"
      if(self.schielding == "ISO 14175-N2-ArN-2"):
         return "98% Ar, 2%N2"
      if(self.schielding == "ISO 14175-N4-ArNH-3/0,7"):
         return "96,3% Ar, 3%N2, 0,7%H2"
      if(self.schielding == "ISO 14175-N5-NH-20"):
         return "80%N2, 20%H2, "
      if(self.schielding == "ISO 14175-R1-ArH-10"):
         return "90%Ar, 10%H2"
      if(self.schielding == "ISO 14175-R1-ArH-2,4"):
         return "97,6%Ar, 2,4%H2"
      if(self.schielding == "ISO 14175-R2-ArH-20"):
         return "80%Ar, 20%H2"
      if(self.schielding == "ISO 14175-Z-Ar+N-0,015"):
         return "0,015%N2 in Ar"
      else:
       if(self.schielding == "ISO 14175-I1-Ar"):
         return "100%Ar"

    def On_change_backing(self,backing):
      if(self.backing == "ISO 14175-C1-C"):
         return "100%CO2"
      if(self.backing == "ISO 14175-I2-He"):
         return "100%He"
      if(self.backing == "ISO 14175-I3-ArHe-30"):
         return "70%Ar,30%He"
      if(self.backing == "ISO 14175-M12-ArC-2"):
         return "98%Ar,2%CO2"
      if(self.backing == "ISO 14175-M12-ArHeC-18/1"):
         return "81%Ar,18%He,1%CO2"
      if(self.backing == "ISO 14175-M13-ArO-2"):
         return "98%Ar,2%O2"
      if(self.backing == "ISO 14175-M14-ArCO-3/1"):
         return "96%Ar,3%CO2,1%O2"
      if(self.backing == "ISO 14175-M20-ArC-8"):
         return "92%Ar, 8%CO2"
      if(self.backing == "ISO 14175-M21-ArC-18"):
         return "82%Ar, 18%CO2"
      if(self.backing == "ISO 14175-M22-ArO-8"):
         return "92%Ar, 8% O2"
      if(self.backing == "ISO 14175-M23-ArCO-5/5"):
         return "90% Ar, 5%CO2, 5%O2"
      if(self.backing == "ISO 14175-M24-ArCO-12/2"):
         return "86%Ar, 12%CO2, 2%O2"
      if(self.backing == "ISO 14175-N2-ArN-2"):
         return "98% Ar, 2%N2"
      if(self.backing == "ISO 14175-N4-ArNH-3/0,7"):
         return "96,3% Ar, 3%N2, 0,7%H2"
      if(self.backing == "ISO 14175-N5-NH-20"):
         return "80%N2, 20%H2, "
      if(self.backing == "ISO 14175-R1-ArH-10"):
         return "90%Ar, 10%H2"
      if(self.backing == "ISO 14175-R1-ArH-2,4"):
         return "97,6%Ar, 2,4%H2"
      if(self.backing == "ISO 14175-R2-ArH-20"):
         return "80%Ar, 20%H2"
      if(self.backing == "ISO 14175-Z-Ar+N-0,015"):
         return "0,015%N2 in Ar"
      else:
       if(self.backing == "ISO 14175-I1-Ar"):
         return "100%Ar"

    def On_change_trailing(self,trailing):
      if(self.trailing == "ISO 14175-C1-C"):
         return "100%CO2"
      if(self.trailing == "ISO 14175-I2-He"):
         return "100%He"
      if(self.trailing == "ISO 14175-I3-ArHe-30"):
         return "70%Ar,30%He"
      if(self.trailing == "ISO 14175-M12-ArC-2"):
         return "98%Ar,2%CO2"
      if(self.trailing == "ISO 14175-M12-ArHeC-18/1"):
         return "81%Ar,18%He,1%CO2"
      if(self.trailing == "ISO 14175-M13-ArO-2"):
         return "98%Ar,2%O2"
      if(self.trailing == "ISO 14175-M14-ArCO-3/1"):
         return "96%Ar,3%CO2,1%O2"
      if(self.trailing == "ISO 14175-M20-ArC-8"):
         return "92%Ar, 8%CO2"
      if(self.trailing == "ISO 14175-M21-ArC-18"):
         return "82%Ar, 18%CO2"
      if(self.trailing == "ISO 14175-M22-ArO-8"):
         return "92%Ar, 8% O2"
      if(self.trailing == "ISO 14175-M23-ArCO-5/5"):
         return "90% Ar, 5%CO2, 5%O2"
      if(self.trailing == "ISO 14175-M24-ArCO-12/2"):
         return "86%Ar, 12%CO2, 2%O2"
      if(self.trailing == "ISO 14175-N2-ArN-2"):
         return "98% Ar, 2%N2"
      if(self.trailing == "ISO 14175-N4-ArNH-3/0,7"):
         return "96,3% Ar, 3%N2, 0,7%H2"
      if(self.trailing == "ISO 14175-N5-NH-20"):
         return "80%N2, 20%H2, "
      if(self.trailing == "ISO 14175-R1-ArH-10"):
         return "90%Ar, 10%H2"
      if(self.trailing == "ISO 14175-R1-ArH-2,4"):
         return "97,6%Ar, 2,4%H2"
      if(self.trailing == "ISO 14175-R2-ArH-20"):
         return "80%Ar, 20%H2"
      if(self.trailing == "ISO 14175-Z-Ar+N-0,015"):
         return "0,015%N2 in Ar"
      else:
       if(self.trailing == "ISO 14175-I1-Ar"):
         return "100%Ar"



    def On_change_welding(self,welding_prozess):
      if(self.welding_prozess == "OFW"):
          return "OFW (Oxyfuel Gas Welding)"
      if(self.welding_prozess == "OHW"):
          return "OHW (Oxyhydrogen Welding)"
      if(self.welding_prozess == "SMAW"):
          return "SMAW (Shielded Metal-Arc Welding)"
      if(self.welding_prozess == "SMAW/SAW"):
          return "SMAW/SAW (Root run SMAW, fill up with SAW)"
      if(self.welding_prozess == "SMAW/GMAW"):
          return "SMAW/GMAW (Root run SMAW, fill up with GMAW)"
      if(self.welding_prozess == "SAW"):
          return "SAW (Submerged-Arc Welding)"
      if(self.welding_prozess == "GMAW"):
          return "GMAW (Gas Metal-Arc Welding)"
      if(self.welding_prozess == "FCAW"):
          return "FCAW (Flux Cored-Arc Welding)"
      if(self.welding_prozess == "GMAW/SMAW"):
          return "GMAW/SMAW (Root run GMAW, fill up with SMAW)"
      if(self.welding_prozess == "GMAW/SAW"):
          return "GMAW/SAW (Root run GMAW, fill up with SAW)"
      if(self.welding_prozess == "FCAW-S"):
          return "FCAW-S (Metal Cored Wire-Arc Welding)"
      if(self.welding_prozess == "GTAW"):
          return "GTAW (Gas Tungsten-Arc Welding)"
      if(self.welding_prozess == "GTAW/SMAW"):
          return "GTAW/SMAW (Root run GTAW, fill up with SMAW)"
      if(self.welding_prozess == "GTAW/SAW"):
          return "GTAW/SAW (Root run GTAW, fill up with SAW)"
      if(self.welding_prozess == "GTAW/GMAW"):
          return "GTAW/GMAW (Root run GTAW, fill up with GMAW)"
      if(self.welding_prozess == "PAW"):
          return "PAW (Plasma-Arc Welding)"
      if(self.welding_prozess == "ESW"):
          return "ESW (Electroslag Welding)"
      if(self.welding_prozess == "EGW"):
          return "EGW (Electrogas Welding)"
      if(self.welding_prozess == "EBW"):
          return "EBW (Electron Beam Welding)"
      if(self.welding_prozess == "EBW-HV"):
          return "EBW-HV (Electron Beam Welding in vacuum)"
      if(self.welding_prozess == "EBW-NV"):
          return "EBW-NV (Electron Beam Welding in atmosphere)"
      if(self.welding_prozess == "SW"):
          return "SW (Stud Welding)"
      if(self.welding_prozess == "FRW"):
          return "FRW (Inertia and Continuous Drive Friction Welding)"
      if(self.welding_prozess == "FRW-DD"):
          return "FRW-DD (Direct Drive Friction Welding)"
      if(self.welding_prozess == "FRW-I"):
          return "FRW-I (Inertia Friction Welding)"
      if(self.welding_prozess == "RW"):
          return "RW (Resistance Welding)"
      if(self.welding_prozess == "LBW"):
          return "LBW (Laser Beam Welding)"
      if(self.welding_prozess == "OHW"):
          return "OHW (Oxyhydrogen Welding)"
      if(self.welding_prozess == "FW"):
          return "FW (Flash Welding)"
      if(self.welding_prozess == "DFW"):
          return "DFW (Diffusion Welding)"
      if(self.welding_prozess == "FSW"):
          return "FSW (Friction Stir Welding)"
      if(self.welding_prozess == "LBW-GMAW"):
          return "LBW+GMAW (Hybrid Laser-GMAW)"
      if(self.welding_prozess == "PAW+GMAW"):
          return "PAW+GMAW (Hybrid Plasma-GMAW)"
      else:
       if(self.welding_prozess =="OAW"):
         return "OAW (Oxyacertylene Welding)"

    def On_change_welding2(self,welding_prozess):
      if(self.welding_prozess == "OFW"):
          return "31     Gas"
      if(self.welding_prozess == "OHW"):
          return "313    Gas"
      if(self.welding_prozess == "SMAW"):
          return "111    E"
      if(self.welding_prozess == "SMAW/SAW"):
          return "111/121   E/UP"
      if(self.welding_prozess == "SMAW/GMAW"):
          return "111/135    E/MAG"
      if(self.welding_prozess == "SAW"):
          return "12    UP"
      if(self.welding_prozess == "GMAW"):
          return "135   MAG"
      if(self.welding_prozess == "FCAW"):
          return "136   MAG"
      if(self.welding_prozess == "GMAW/SMAW"):
          return "135/111    MAG/E"
      if(self.welding_prozess == "GMAW/SAW"):
          return "135/121   MAG/UP"
      if(self.welding_prozess == "FCAW-S"):
          return "133    MIG"
      if(self.welding_prozess == "GTAW"):
          return "141    WIG"
      if(self.welding_prozess == "GTAW/SMAW"):
          return "141/111    WIG/E"
      if(self.welding_prozess == "GTAW/SAW"):
          return "141/121    WIG/UP"
      if(self.welding_prozess == "GTAW/GMAW"):
          return "141/135    WIG/MAG"
      if(self.welding_prozess == "PAW"):
          return "15  WPL"
      if(self.welding_prozess == "ESW"):
          return "72    RES"
      if(self.welding_prozess == "EGW"):
          return "73    MSGG"
      if(self.welding_prozess == "EBW"):
          return "51    EB"
      if(self.welding_prozess == "EBW-HV"):
          return "511    EB"
      if(self.welding_prozess == "EBW-NV"):
          return "512    EB"
      if(self.welding_prozess == "SW"):
          return "78    DS"
      if(self.welding_prozess == "FRW"):
          return "42     FR"
      if(self.welding_prozess == "FRW-DD"):
          return "421     "
      if(self.welding_prozess == "FRW-I"):
          return "422      "
      if(self.welding_prozess == "RW"):
          return "2      "
      if(self.welding_prozess == "LBW"):
          return "52   LA"
      if(self.welding_prozess == "FW"):
          return "24       "
      if(self.welding_prozess == "DFW"):
          return "45       "
      if(self.welding_prozess == "FSW"):
          return "43       "
      if(self.welding_prozess == "LBW-GMAW"):
          return "52+135   LA+MAG"
      if(self.welding_prozess == "PAW+GMAW"):
          return "15+135    WPL+MAG"
      else:
       if(self.welding_prozess =="OAW"):
         return "311    Gas"


    @fields.depends('grou2', 'p_no')
    def on_change_matriall5(self):
      tab=[]
      if(self.p_no == "4" or self.p_no == "5B"):
        tab.append(("1","1 | Group1"))
        tab.append(("2","2 | Group2"))
        return tab
      if(self.p_no == "1"):
        tab.append(("1","1 | Group 1 -up to approx 65 ksi(450 MPa)"))
        tab.append(("2","2 | Group 2 -Approx 70 ksi(485 MPa)"))
        tab.append(("3","3 | Group 3 -Approx 80 ksi(550 MPa)"))
        tab.append(("4","4 | Group 4 -Approx 90 ksi(620 MPa)"))
        return tab
      if(self.p_no == "8"):
        tab.append(("1","1 | Group 1 - Grades 304, 316, 317, 347"))
        tab.append(("2","2 | Group 2 - Grades 309, 310 "))
        tab.append(("3","3 | Group 3 - High Manganese Grades"))
        tab.append(("4","4 | Group 4 - High Molybdenum Grades"))
        return tab

      if(self.p_no == "5C"):
        tab.append(("1","1 | Group 1"))
        tab.append(("2","2 | Group 2"))
        tab.append(("3","3 | Group 3"))
        tab.append(("4","4 | Group 4"))
        tab.append(("5","5 | Group 5"))
        return tab
      if(self.p_no == "6"):
        tab.append(("1","1 | Group 1"))
        tab.append(("2","2 | Group 2"))
        tab.append(("3","3 | Group 3"))
        tab.append(("4","4 | Group 4"))
        tab.append(("5","5 | Group 5"))
        tab.append(("6","6 | Group 6"))
        return tab
      if(self.p_no == "11A"):
        tab.append(("1","1 | Group 1 - Nickel Steels"))
        tab.append(("2","2 | Group 2"))
        tab.append(("3","3 | Group 3"))
        tab.append(("4","4 | Group 4"))
        tab.append(("5","5 | Group 5"))
        tab.append(("6","6 | Group 6"))
        return tab
      if(self.p_no == "11B"):
        tab.append(("1","1 | Group 1"))
        tab.append(("2","2 | Group 2"))
        tab.append(("3","3 | Group 3"))
        tab.append(("4","4 | Group 4"))
        tab.append(("5","5 | Group 5"))
        tab.append(("6","6 | Group 6"))
        tab.append(("7","7 | Group 7"))
        tab.append(("8","8 | Group 8"))
        tab.append(("9","9 | Group 9"))
        tab.append(("10","10 | Group 10"))
        return tab

      if(self.p_no == "3"):
        tab.append(("1","1 | Group 1"))
        tab.append(("2","2 | Group 2"))
        tab.append(("3","3 | Group 3"))
        return tab
      else:
         if(self.p_no == "5A" or self.p_no == "7" or self.p_no == "9A" or self.p_no == "9B" or self.p_no == "9C" or self.p_no == "10A" or self.p_no == "10B" or self.p_no == "10C" or self.p_no == "10F" or self.p_no == "10H" or self.p_no == "10I" or self.p_no == "10J" or self.p_no == "10K" or self.p_no == "15B" or self.p_no == "15C" or self.p_no == "15E" or self.p_no == "15F" or self.p_no == "21" or self.p_no == "22" or self.p_no == "23" or self.p_no == "25" or self.p_no == "31" or self.p_no == "32" or self.p_no == "33" or self.p_no == "34" or self.p_no == "35" or self.p_no == "41" or self.p_no == "42" or self.p_no == "43" or self.p_no == "44" or self.p_no == "45" or self.p_no == "46" or self.p_no == "47" or self.p_no == "51" or self.p_no == "52" or self.p_no == "52" or self.p_no == "61" or self.p_no == "62"):
           tab.append((" ","  "))
           return tab



    @fields.depends('p_no', 'matrial22')
    def on_change_matriall3(self):
      tab=[]
      if(self.matrial22 is not None):
        val=self.matrial22.Bezeichnung
        if(val == "10CrMo9-10" or val =="11CrMo9-10"):
          tab.append(("5A","5A | 5.2 | Two and a quater Chromium, one Molybdenum"))
          return tab

        if(val == "16Mo3"):
          tab.append(("3","3 |   | Half Molybdenum or half Chromium, half Molybdenum"))
          return tab

        if(val == "NiCr15Fe" or val =="NiCr22Mo9Nb" or val == "P235G1TH" or val =="P235GH" or val == "P235TR1" or val =="P235TR2" or val =="P255G1TH" or val =="P265GH" or val =="P275NH" or val == "P280GH" or val =="P295GH" or val =="P305GH" or val =="P355GH" or val =="P355NH" or val =="P355NL1" or val =="S235JR" or val =="S235JRG2"):
          tab.append(("43","43 |43,44,46 | Nickel, Chromium, Iron(Inconel)"))
          return tab

        if(val == "X10CrMoVNb9-1"):
          tab.append(("15E","15E | 6.4 | Creep-strength Enhanced Ferritic Alloys 9Cr(eg. 91,92,911)"))
          return tab

        if(val == "X10NiCrAITi32-21" or val == "X1NiCrMoCu25-20-5"):
          tab.append(("45","45 | 8.2, 45 | Nickel, Chromium(Incolory 800,825)"))
          return tab

        if(val == "X11CrMo5+I"):
          tab.append(("5B","5B | 5.3, 5.4 | Five Chromium, Half Molybdenum or nine Chromium, One Moly"))
          return tab

        if(val == "X2CrNi18-9" or val == "X2CrNi19-11" or val =="X2CrNiMo17-12-2" or val =="X2CrNiMo18-14-3" or val =="X2CrNiMoN17-11-2" or val =="X2CrNiMoN17-13-3" or val =="X2CrNiN18-10" or val =="X5CrNi18-10" or val =="X5CrNiMo17-12-2" or val =="X5CrNiN19-9" or val =="X6CrNi18-10" or val =="X6CrNiMoTi17-12-2" or val =="X6CrNiNb18-10" or val =="X6CrNiTi18-10" or val =="X8CrNiTi18-10"):
          tab.append(("8","8 | 8.1, 8.2, 8.3  | Austenitic Stainless Steels"))
          return tab

        if(val == "X2CrNiMoN22-5-3"):
          tab.append(("10H","10H | 10.1, 10.2 | Duplex and Super Duplex Stainless Steel(Grades 31803, 32750)"))
          return tab

        if(val == "X7Ni9" or val =="N8Ni9"):
          tab.append(("11A","11A | 3.1, 3.2, 9.2, 9,3 | Various high strength low alloy steels"))
          return tab

        if(val == "P235G1TH" or val =="P235GH" or val =="P235TR1" or val =="P235TR2" or val =="P255G1TH" or val =="P265GH" or val =="P275NH" or val =="P280GH" or val =="P295GH" or val =="P305GH" or val =="355GH" or val =="P355NH" or val =="P355NL1" or val =="S235JR" or val =="S235JRG2"):
          tab.append(("1","1 |      | Carbon Manganese Steels"))
          return tab
        if(val == "13CrMo4-5" or val =="13CrMoSi5-5"):
          tab.append(("4","4 | One and a quater Chromium, half Molybdenum"))
          return tab
        else:
          tab.append((" "," "))
          return tab
      else:
         tab.append(("1","1 |      | Carbon Manganese Steels"))
         tab.append(("3","3 |   | Half Molybdenum or half Chromium, half Molybdenum"))
         tab.append(("4","4 | One and a quater Chromium, half Molybdenum"))
         tab.append(("5A","5A | 5.2 | Two and a quater Chromium, one Molybdenum"))
         tab.append(("5B","5B | 5.3, 5.4 | Five Chromium, Half Molybdenum or nine Chromium, One Moly"))
         tab.append(("5C","5C | 5.2, 6.2 | Chromium, Molybdenum, Vanadium"))
         tab.append(("6","6 | 7.1, 7.2 | Martensitic Stainless Steels(Grade 410, 415, 429)"))
         tab.append(("7","7 | 7.1, 7.2 | Ferritic Stainless Steels(Grade 409, 430)"))
         tab.append(("9A","9A | 9.1    | Two to four Nickel Steels"))
         tab.append(("9B","9B | 9.2    | Two to four Nickel Steels"))
         tab.append(("9C","9C | 9.3    | Two to four Nickel Steels"))
         tab.append(("10A","10A | 2.1, 4.1 | Various low alloy steels "))
         tab.append(("10B","10B | 4.1 | Various low alloy steels "))
         tab.append(("10C","10C | 1.3 | Various low alloy steels "))
         tab.append(("10F","10F |     | Various low alloy steels "))
         tab.append(("10H","10H | 10.1, 10.2 | Duplex and Super Duplex Stainless Steel(Grades 31803, 32750) "))
         tab.append(("10I","10I | 7.1  | High Chromium (Typically 25 to 27)Stainless Steel"))
         tab.append(("10J","10J | 7.1  | High Chromium (Typically 29), Molybdenum Stainless Steel"))
         tab.append(("10K","10K | 7.1  | High Chromium, Molybdenum, Nickel Stainless Steel"))
         tab.append(("11A","11A | 3.1, 3.2, 9.2, 9,3 | Various high strength low alloy steels"))
         tab.append(("11B","11B | 3.1 | Various high strength low alloy steels"))
         tab.append(("15B","15B |     | Creep-strength Enhanced Ferritic Alloys 1-1/4Cr"))
         tab.append(("15C","15C |     | Creep-strength Enhanced Ferritic Alloys 2-1/4Cr(e.g.23,24)"))
         tab.append(("15E","15E | 6.4 | Creep-strength Enhanced Ferritic Alloys 9Cr(eg. 91,92,911)"))
         tab.append(("15F","15F |     | Creep-strength Enhanced Ferritic Alloys 12Cr(eg. 122, VM12)"))
         tab.append(("21","21 |21, 22.1, 22.2 | High Aluminium content(1000 and 3000 series)"))
         tab.append(("22","22 |22.3, 22.4 | Aluminium (5000 series-5052,5454)"))
         tab.append(("23","23 |23.1 | Aluminium (6000 series-6061,6063)"))
         tab.append(("25","25 |22.4 | Aluminium (5000 series-5083,5086, 5456)"))
         tab.append(("31","31 |     | High Copper content"))
         tab.append(("32","32 |32.1, 32.2  | Brass"))
         tab.append(("33","33 |31, 33, 37  | Copper Silicone"))
         tab.append(("34","34 |34  | Copper Nickel"))
         tab.append(("35","35 |35  | Copper Alluminium"))
         tab.append(("41","41 |41  | High Nickel content"))
         tab.append(("42","42 |42  | Nickel, Copper(Monel 500)"))
         tab.append(("43","43 |43,44,46 | Nickel, Chromium, Iron(Inconel)"))
         tab.append(("44","44 |44 | Nickel, Molybdenum (Hastelloy B2, C22, C276, X)"))
         tab.append(("45","45 | 8.2, 45 | Nickel, Chromium(Incolory 800,825)"))
         tab.append(("46","46 | 45, 46 | Nickel, Chromium, Silicone"))
         tab.append(("47","47 |    | Nickel, Chromium, Tungsten"))
         tab.append(("51","51 |    | Titanium Alloys"))
         tab.append(("52","52 |    | Titanium Alloys"))
         tab.append(("53","53 |    | Titanium Alloys"))
         tab.append(("61","61 |    | Zirconium Alloys"))
         tab.append(("62","62 |    | Zirconium Alloys"))
         return tab

    def on_change_matriall4(self,matrial22):
     if(self.matrial22 is not None):
      val=self.matrial22.Bezeichnung
      if(val == "10CrMo9-10"):
         return "5A"
      else:
         if(val == "13CrMo4-5"):
           return "4"
     else:
         return " "

    @fields.depends('matrial3', 'type_grade1')
    def on_change_matriall2(self):
      tab=[]
      if(self.type_grade1 == "A 573 65"):
         tab.append(("E335","E335 | 1.0060 | DIN EN 10025-2 | US Steels, ASME BPVC.IX"))
         tab.append(("P315NH","P315NH | 1.0506 |  US Steels, ASME BPVC.IX"))
         tab.append(("P315NL","P315NL | 1.0508 |  US Steels, ASME BPVC.IX"))
         return tab
      if(self.type_grade1 == "A 234 WPB"):
         tab.append(("C35","C35 | 1.0501 | DIN EN 10083-2 | US Steels, ASME BPVC.IX"))
         tab.append(("L245MB","L245MB | 1.0418 | DIN EN 10208-2 | US Steels, ASME BPVC.IX"))
         tab.append(("P235G1TH","P235G1TH | 1.0305 | US Steels, ASME BPVC.IX"))
         tab.append(("P255G1TH","P255G1TH | 1.0405 | DIN 17175 | US Steels, ASME BPVC.IX"))
         return tab
      if(self.type_grade1 == "A 830 UNS G10350 / SAE 1035"):
         tab.append(("C35","C35 | 1.0501 | DIN EN 10083-2 | US Steels, ASME BPVC.IX"))
         return tab
      else:
        if(self.type_grade1 == "A 106 B"):
          tab.append(("C35","C35 | 1.0501 | DIN EN 10083-2 | US Steels, ASME BPVC.IX"))
          tab.append(("L245MB","L245MB | 1.0418 | DIN EN 10208-2 | US Steels, ASME BPVC.IX"))
          tab.append(("L360NB","L360NB | 1.0582 | DIN EN 10208-2 | US Steels, ASME BPVC.IX"))
          tab.append(("P255G1TH","P255G1TH | 1.0405 | DIN 17175 | US Steels, ASME BPVC.IX"))
          return tab 

    @fields.depends('type_grade', 'matrial22')
    def on_change_matriall(self):
      tab=[]
      if(self.matrial22 is not None):
        val = self.matrial22.Bezeichnung
        if(val == "C35"):
           tab.append(("A 106 B","A 106 B(US Steels, ASME BPVC.IX)"))
           tab.append(("A 234 WPB","A 234 WPB(US Steels, ASME BPVC.IX)"))
           tab.append(("A 830 UNS G10350 / SAE 1035","A 830 UNS G10350 / SAE 1035 (Produktbereich Grobblech)"))
           return tab
        if(val == "13CrMo4-5"):
           tab.append(("A 182 F12, CI.1","A 182 F12, CI.1 | 4 | 1 | K11562 | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "13CrMoSi5-5"):
           tab.append(("EN 10028-2 13CrMoSi5-5+QT","EN 10028-2 13CrMoSi5-5+QT | 4 | 1 | ... | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "20MnMoNi5-5"):
           tab.append(("A 533 Type B CI. 1","A 533 Type B CI. 1 | 3 | 3 | K12539 | US Steels, ASME BPVC.IX"))
           tab.append(("A 533 Type C CI. 1","A 533 Type C CI. 1 | 3 | 3 | K12554 | US Steels, ASME BPVC.IX"))
           tab.append(("A 533 Type D CI. 1","A 533 Type D CI. 1 | 3 | 3 | K12529 | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "42CrMo4"):
           tab.append(("A 829 UNS G41400/SAE 4140","A 829 UNS G41400/SAE 4140 |   |   |      | Produktbereich Grobblech"))
           tab.append(("A 829 UNS G41420/SAE 4142","A 829 UNS G41420/SAE 4142 |   |   |      | Produktbereich Grobblech"))
           tab.append(("A 829 UNS G41450/SAE 4145","A 829 UNS G41450/SAE 4145 |   |   |      | Produktbereich Grobblech"))
           return tab
        if(val == "C22"):
           tab.append(("A 105...","A 105... | 1 | 2 | K03504  | US Steels, ASME BPVC.IX"))
           tab.append(("A 108 1020 CW","A 108 1020 CW | 1 | 1 | G10200  | US Steels, ASME BPVC.IX"))
           tab.append(("A 181 CI. 60","A 181 CI. 60 | 1 | 1 | K03502  | US Steels, ASME BPVC.IX"))
           tab.append(("A 266 1","A 266 1 | 1 | 1 | K03506 | US Steels, ASME BPVC.IX"))
           tab.append(("A 575 M 1020","A 575 M 1020 | 1 | 1 | ... | US Steels, ASME BPVC.IX"))
           tab.append(("A 576 1020","A 576 1020 | 1 | 1 | G10200 | US Steels, ASME BPVC.IX"))
           tab.append(("A 830 UNS G10220/SAE 1022","A 830 UNS G10220/SAE 1022 |   |   |      | Produktbereich Grobblech"))
           return tab
        if(val == "C22E"):
           tab.append(("A 513 1020 CW","A 513 1020 CW | 1 | 2 | G10200  | US Steels, ASME BPVC.IX"))
           tab.append(("A 575 M 1020","A 575 M 1020 | 1 | 1 | ...  | US Steels, ASME BPVC.IX"))
           tab.append(("A 576 1020 ","A 576 1020 | 1 | 1 | G10200  | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "G17CrMo5-5"):
           tab.append(("A 217 WC6","A 217 WC6 | 4 | 1 | J12072  | US Steels, ASME BPVC.IX"))
           tab.append(("A 356 6","A 356 6 | 4 | 1 | J12073  | US Steels, ASME BPVC.IX"))
           tab.append(("A 426 CP11 ","A 426 CP11 | 4 | 1 | J12072  | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "G17CrMo9-10"):
           tab.append(("A 426 CP22","A 426 CP22 | 5A | 1 | J21890  | US Steels, ASME BPVC.IX"))
           tab.append(("A 487 Gr.8, CI. B","A 487 Gr.8, CI. B | 5C | 4 | J22091  | US Steels, ASME BPVC.IX"))
           tab.append(("A 487 Gr.8, CI. C","A 487 Gr.8, CI. C | 5C | 4 | J22091  | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "G17CrMoV5-10"):
           tab.append(("A 356 9","A 356 9 | 4 | 1 | J21610  | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "G17Mn5"):
           tab.append(("A 352 LCC","A 352 LCC | 1 | 2 | J02505  | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "G18Mo5"):
           tab.append(("A 352 LCB","A 352 LCB | 1 | 1 | J03003  | US Steels, ASME BPVC.IX"))
           tab.append(("A 660 WCB","A 660 WCB | 1 | 2 | J03003  | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "G20Mn5"):
           tab.append(("A 352 LCC","A 352 LCC | 1 | 2 | J02505  | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "G20Mo5"):
           tab.append(("A 217 WC1","A 217 WC1 | 3 | 1 | J12524  | US Steels, ASME BPVC.IX"))
           tab.append(("A 352 LC1","A 352 LC1 | 3 | 1 | J12522  | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "G21Mn5"):
           tab.append(("A 216 WCC","A 216 WCC | 1 | 1 | J02503  | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "G9Ni10"):
           tab.append(("A 352 LC2","A 352 LC2 | 9A | 1 | J22500  | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "GE240"):
           tab.append(("A 420 WPL6","A 420 WPL6 | 1 | 1 | K03006  | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "GE260"):
           tab.append(("A541 2, CI. 1","A541 2, CI. 1 | 3 | 3 | K12765  | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "GP240GH"):
           tab.append(("A 216 WCA","A 216 WCA | 1 | 1 | J02502  | US Steels, ASME BPVC.IX"))
           tab.append(("A 216 WCB","A 216 WCA | 1 | 2 | J03002  | US Steels, ASME BPVC.IX"))
           tab.append(("A 216 WCC","A 216 WCA | 1 | 1 | J02503  | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "GP280GH"):
           tab.append(("A 216 WCC","A 216 WCC | 1 | 1 | J02503  | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "GX10NiCrSiNb32-20"):
           tab.append(("A 351 CT15C","A 351 CT15C | 45 | ... | N08151  | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "GX12Cr12"):
           tab.append(("A 487 CA15M CI. A","A 487 CA15M CI. A | 6 | 3 | J91151  | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "GX15CrMo5"):
           tab.append(("A 217 C5","A 217 C5 | 5B | 1 | J42045  | US Steels, ASME BPVC.IX"))
           tab.append(("A 426 CP5","A 426 CP5 | 5B | 1 | J42045  | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "GX2CrNi19-11"):
           tab.append(("A 351 CF3","A 351 CF3 | 8 | 1 | J92500  | US Steels, ASME BPVC.IX"))
           tab.append(("A 451 CPF3","A 451 CPF3 | 8 | 1 | J92500  | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "GX2CrNiMo19-11-2"):
           tab.append(("A 351 CF3M","A 351 CF3M | 8 | 1 | J92800  | US Steels, ASME BPVC.IX"))
           tab.append(("A 451 CPF3M","A 451 CPF3M | 8 | 1 | J92800  | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "GX4CrNi13-4"):
           tab.append(("A 352 CA6NM","A 352 CA6NM | 6 | 4 | J91540  | US Steels, ASME BPVC.IX"))
           tab.append(("A 487 CA6NM CI. B"," | 6 | 4 | J91540  | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "GX5CrNi19-10"):
           tab.append(("A 167 Type 308","A 167 Type 308 | 8 | 2 | S30800  | US Steels, ASME BPVC.IX"))
           tab.append(("A 351 CF8A","A 351 CF8A | 8 | 1 | J92600  | US Steels, ASME BPVC.IX"))
           tab.append(("A 351 CF8C","A 351 CF8C | 8 | 1 | J92710  | US Steels, ASME BPVC.IX"))
           tab.append(("A 451 CPF8A","A 451 CPF8A | 8 | 1 | J92600  | US Steels, ASME BPVC.IX"))
           tab.append(("A 451 CPF8C","A 451 CPF8C | 8 | 1 | J92710  | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "GX5CrNiMo19-11-2"):
           tab.append(("A 351 CF8M","A 351 CF8M | 8 | 1 | J92900  | US Steels, ASME BPVC.IX"))
           tab.append(("A 451 CPF8M","A 451 CPF8M | 8 | 1 | J92900  | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "GX5CrNiMo19-11-3"):
           tab.append(("A 351 CG8M","A 351 CG8M | 8 | 1 | J93000  | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "GX5CrNiMoNb19-11-2"):
           tab.append(("A 351 CF8M","A 351 CF8M | 8 | 1 | J92900  | US Steels, ASME BPVC.IX"))
           tab.append(("A 451 CPF8M","A 451 CPF8M | 8 | 1 | J92900  | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "GX5CrNiNb19-11"):
           tab.append(("A 351 CF8C","A 351 CF8C | 8 | 1 | J92710  | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "GX7CrNiMo12-1"):
           tab.append(("A 217 CA15","A 217 CA15 | 6 | 3 | J91150  | US Steels, ASME BPVC.IX"))
           tab.append(("A 426 CPCA15","A 426 CPCA15 | 6 | 3 | J91150  | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "GX8CrNi12"):
           tab.append(("A 217 CA15","A 217 CA15 | 6 | 3 | J91150  | US Steels, ASME BPVC.IX"))
           tab.append(("A 426 CPCA15","A 426 CPCA15 | 6 | 3 | J91150  | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "L210" or val =="L210GA"):
           tab.append(("API 5L A","API 5L A | 1 | 1 | ...  | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "L240NB"):
           tab.append(("A 333 Gr. 1","A 333 Gr. 1 |   |   |       | US Steels, ASME BPVC.IX"))
           tab.append(("A 333 Gr. 6","A 333 Gr. 6 |   |   |       | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "L245GA"):
           tab.append(("A 53 Gr. B(Type E)","A 53 Gr. B(Type E) |   |   |       | Produktbereich Grobblech"))
           tab.append(("API 5L B","API 5L B | 1  | 1  |  ...   | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "L245MB"):
           tab.append(("A 106 B","A 106 B | 1 | 1  | K03006 | US Steels, ASME BPVC.IX"))
           tab.append(("A 234 WPB","A 234 WPB | 1  | 1  | K03006  | US Steels, ASME BPVC.IX"))
           tab.append(("A 333 6","A 333 6 | 1  | 1  | K03006  | US Steels, ASME BPVC.IX"))
           tab.append(("A 334 6","A 334 6 | 1  | 1  | K03006  | US Steels, ASME BPVC.IX"))
           tab.append(("A 369 FPB","A 369 FPB | 1  | 1  | K03006  | US Steels, ASME BPVC.IX"))
           tab.append(("A 420 WPL6","A 420 WPL6 | 1  | 1  | K03006  | US Steels, ASME BPVC.IX"))
           tab.append(("A 53 Type S, Gr. B","A 53 Type S, Gr. B | 1  | 1  | K03005  | US Steels, ASME BPVC.IX"))
           tab.append(("A 556 C2","A 556 C2 | 1  | 2  | K03006  | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "L245NB"):
           tab.append(("API 5L B","API 5L B | 1 | 1 | ...  | US Steels, ASME BPVC.IX"))
           tab.append(("API 5L BR","API 5L BR | 1 | 1 | ...  | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "L290GA"):
           tab.append(("API 5L X42","API 5L X42 | 1 | 1 | ...  | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "L290MB"):
           tab.append(("API 5L X42","API 5L X42 | 1 | 1 | ...  | US Steels, ASME BPVC.IX"))
           tab.append(("API 5L X42R","API 5L X42R | 1 | 1 | ...  | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "L290NB"):
           tab.append(("A 860 WPHY 42","A 860 WPHY 42 | 1 | 1 | ...  | US Steels, ASME BPVC.IX"))
           tab.append(("API 5L X42","API 5L X42 | 1 | 1 | ...  | US Steels, ASME BPVC.IX"))
           tab.append(("API 5L X42R","API 5L X42R | 1 | 1 | ...  | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "L320"):
           tab.append(("A 860 WPHY 46","A 860 WPHY 46 | 1 | 1 | ...  | US Steels, ASME BPVC.IX"))
           tab.append(("API 5L X46","API 5L X46 | 1 | 1 | ...  | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "L360GA" or val == "L360MB"):
           tab.append(("API 5L X52","API 5L X52 | 1 | 1 | ...  | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "L360NB"):
           tab.append(("A 106 B","A 106 B | 1 | 1 | K03006  | US Steels, ASME BPVC.IX"))
           tab.append(("A 860 WPHY 52","A 860 WPHY 52 | 1 | 1 | ...  | US Steels, ASME BPVC.IX"))
           tab.append(("API 5L X52","API 5L X52 | 1 | 1 | ...  | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "L360QB"):
           tab.append(("API 5L X52Q","API 5L X52Q | 1 | 1 | ...  | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "L415MB"):
           tab.append(("API 5L X60","API 5L X60 | 1 | 2 | ...  | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "L415NB"):
           tab.append(("A 860 WPHY 60","A 860 WPHY 60 | 1 | 2 | ...  | US Steels, ASME BPVC.IX"))
           tab.append(("API 5L X60","API 5L X60 | 1 | 2 | ...  | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "L415QB"):
           tab.append(("API 5L X60Q","API 5L X60Q | 1 | 2 | ...  | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "L450MB"):
           tab.append(("A 860 WPHY 65","A 860 WPHY 65 | 1 | 3 | ...  | US Steels, ASME BPVC.IX"))
           tab.append(("API 5L X65","API 5L X65 | 1 | 2 | ...  | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "L450QB"):
           tab.append(("API 5L X65Q","API 5L X65Q | 1 | 2 | ...  | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "L485MB"):
           tab.append(("A 860 WPHY 70","A 860 WPHY 70 | 1 | 3 | ...  | US Steels, ASME BPVC.IX"))
           tab.append(("API 5L X70","API 5L X70 | 1 | 3 | ...  | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "L485QB"):
           tab.append(("API 5L X70Q","API 5L X70Q | 1 | 3 | ...  | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "L555QB"):
           tab.append(("API 5L X80Q","API 5L X80Q | 1 | 4 | ...  | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "NiCr15Fe"):
           tab.append(("B 166 UNS N06600","B 166 UNS N06600 |   |   |      | Nickel Base Alloy-Rod, Bar(Stangen)"))
           tab.append(("B 167 UNS N06600","B 167 UNS N06600 |   |   |      | Nickel Base Alloy-Seamless Pipes"))
           tab.append(("B 168 UNS N06600","B 168 UNS N06600 |   |   |      | Nickel Base Alloy-Plate"))
           tab.append(("B 366 WP NCI UNS N06600","B 366 WP NCI UNS N06600 |   |   |      | Nickel Base Alloy-Fittings(Flansche)"))
           tab.append(("B 517 UNS N06600","B 517 UNS N06600 |   |   |      | Nickel Base Alloy-Welded Pipes"))
           tab.append(("B 564 UNS N06600","B 564 UNS N06600 |   |   |      | Nickel Base Alloy-Forgings (Schmiedeteile)"))
           return tab
        if(val == "NiCr22Mo9Nb"):
           tab.append(("B 443 UNS N06625","B 443 UNS N06625 |   |   |      | Nickel Base Alloy-Plate"))
           tab.append(("B 444 UNS N06625","B 444 UNS N06625 |   |   |      | Nickel Base Alloy-Seamless Pipes"))
           tab.append(("B 446 UNS N06625","B 446 UNS N06625 |   |   |      | Nickel Base Alloy-Rod, Bar(Stangen)"))
           tab.append(("B 366 WP NCMC UNS N06625","B 366 WP NCMC UNS N06625 |   |   |      | Nickel Base Alloy-Fittings(Flansche)"))
           tab.append(("B 705 UNS N06625","B 705 UNS N06625 |   |   |      | Nickel Base Alloy-Welded Pipes"))
           tab.append(("B 564 UNS N06625","B 564 UNS N06625 |   |   |      | Nickel Base Alloy-Forgings (Schmiedeteile)"))
           return tab
        if(val == "P235G1TH"):
           tab.append(("A 106 A","A 106 A| 1  | 1  | K02501 | US Steels, ASME BPVC.IX"))
           tab.append(("A 106 Gr. A","A 106 Gr. A |    |    |      | Carbon steel - Seamless Pipes"))
           tab.append(("A 178 A","A 178 A | 1 | 1 | K01200 | US Steels, ASME BPVC.IX"))
           tab.append(("A 179...","A 179... | 1 | 1 | K01200 | US Steels, ASME BPVC.IX"))
           tab.append(("A 192...","A 192... | 1 | 1 | K01201 | US Steels, ASME BPVC.IX"))
           tab.append(("A 234 WPB","A 234 WPB | 1 | 1 | K03006 | US Steels, ASME BPVC.IX"))
           tab.append(("A 369 FPA","A 369 FPA | 1 | 1 | K02501 | US Steels, ASME BPVC.IX"))
           tab.append(("A 556 A2","A 556 A2 | 1 | 1 | K01807 | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "P235GH"):
           tab.append(("A 285 A","A 285 A| 1 | 1 | K01700 | US Steels, ASME BPVC.IX"))
           tab.append(("A 285 B","A 285 B| 1 | 1 | K02200 | US Steels, ASME BPVC.IX"))
           tab.append(("A 285 Gr. A","A 285 Gr. A|   |   |        | Hüttenindustrie EN 10028-2"))
           tab.append(("A 414 A","A 414 A| 1 | 1 | K01501 | US Steels, ASME BPVC.IX"))
           tab.append(("A 414 B","A 414 B| 1 | 1 | K02201 | US Steels, ASME BPVC.IX"))
           tab.append(("A 515 Gr. 55","|   |   |        | Hüttenindustrie EN 10028-2"))
           tab.append(("A 515 Gr. 60","A 515 Gr. 60|   |   |        | Hüttenindustrie EN 10028-2"))
           tab.append(("A 516 Gr. 55","A 516 Gr. 55|   |   |        | Hüttenindustrie EN 10028-2"))
           tab.append(("EN 10028-2 P235GH","EN 10028-2 P235GH| 1 | 1 | ... | US Steels, ASME BPVC.IX"))
           tab.append(("EN 10216-2 P235GH","EN 10216-2 P235GH| 1 | 1 | ... | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "P235S"):
           tab.append(("A 285 Gr. A","A 285 Gr. A|   |   |        | Produktbereich Grobblech"))
           tab.append(("A 285 Gr. B","A 285 Gr. B|   |   |        | Produktbereich Grobblech"))
           tab.append(("A 285 Gr. C","A 285 Gr. C|   |   |        | Produktbereich Grobblech"))
           return tab
        if(val == "P235TR1"):
           tab.append(("A 135 A","A 135 A| 1 | 1 | K02509 | US Steels, ASME BPVC.IX"))
           tab.append(("A 179...","A 179...| 1 | 1 | K01200 | US Steels, ASME BPVC.IX"))
           tab.append(("A 369 FPA","A 369 FPA| 1 | 1 | K02501 | US Steels, ASME BPVC.IX"))
           tab.append(("A 519 1020 HR","A 519 1020 HR| 1 | 1 | K10200 | US Steels, ASME BPVC.IX"))
           tab.append(("A 53 Type S, Gr. A","A 53 Type S, Gr. A| 1 | 1 | K02504 | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "P235TR2"):
           tab.append(("A 106 A","A 106 A| 1 | 1 | K02501 | US Steels, ASME BPVC.IX"))
           tab.append(("EN 10217-1 P235TR2","EN 10217-1 P235TR2| 1 | 1 | ... | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "P245GH"):
           tab.append(("A 266 1","A 266 1| 1 | 1 | K03506 | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "P250GH"):
           tab.append(("A 105...","A 105...| 1 | 2 | K03504 | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "P255G1TH"):
           tab.append(("A 106 B","A 106 B| 1 | 1 | K03006 | US Steels, ASME BPVC.IX"))
           tab.append(("A 106 Gr. B","A 106 Gr. B|   |   |        | Carbon steel-Seamless Pipes"))
           tab.append(("A 178 C","A 178 C| 1 | 1 | K03503 | US Steels, ASME BPVC.IX"))
           tab.append(("A 210 A-1","A 210 A-1| 1 | 1 | K02707 | US Steels, ASME BPVC.IX"))
           tab.append(("A 234 Gr. WP B","A 234 Gr. WP B|   |   |        | Carbon steel-Seamless Pipes"))
           tab.append(("A 234 WPB","A 234 WPB| 1 | 1 | K03006 | US Steels, ASME BPVC.IX"))
           tab.append(("A 333 6","A 333 6| 1 | 1 | K03006 | US Steels, ASME BPVC.IX"))
           tab.append(("A 334 6","A 334 6| 1 | 1 | K03006 | US Steels, ASME BPVC.IX"))
           tab.append(("A 369 FPB","A 369 FPB| 1 | 1 | K03006 | US Steels, ASME BPVC.IX"))
           tab.append(("A 420 WPL6","A 420 WPL6| 1 | 1 | K03006 | US Steels, ASME BPVC.IX"))
           tab.append(("A 556 B2","A 556 B2| 1 | 1 | K02707 | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "P265GH"):
           tab.append(("A 285 C","A 285 C| 1 | 1 | K02801 | US Steels, ASME BPVC.IX"))
           tab.append(("A 285 Gr. B","A 285 Gr. B|   |   |        | Hüttenindustrie EN 10028-2"))
           tab.append(("A 285 Gr. C","A 285 Gr. C|   |   |        | Carbon steel-Plates"))
           tab.append(("A 414 D","A 414 D| 1 | 1 | K02505 | US Steels, ASME BPVC.IX"))
           tab.append(("A 455...","A 455...| 1 | 2 | K03300 | US Steels, ASME BPVC.IX"))
           tab.append(("A 515 60","A 51560| 1 | 1 | K02401 | US Steels, ASME BPVC.IX"))
           tab.append(("A 515 Gr. 60","A 515 Gr. 60|   |   |        | Carbon steel-Plates"))
           tab.append(("A 515 Gr. 60","A 515 Gr. 60|   |   |        | Hüttenindustrie EN 10028-2"))
           tab.append(("A 516 60","A 516 60| 1 | 1 | K02100 | US Steels, ASME BPVC.IX"))
           tab.append(("A 516 Gr. 60","A 516 Gr. 60|   |   |        | Hüttenindustrie EN 10028-2"))
           tab.append(("A 662 A","A 662 A| 1 | 1 | K01701 | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "P265NB"):
           tab.append(("A 414 D","A 414 D| 1 | 1 | K02505 | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "P275N"):
           tab.append(("A 516 60","A 516 60| 1 | 1 | K02100 | US Steels, ASME BPVC.IX"))
           tab.append(("A 516 Gr. 55(380)","A 516 Gr. 55(380) |   |   |        | Produktbereich Grobblech"))
           tab.append(("A 516 Gr. 60","A 516 Gr. 60|   |   |        | Hüttenindustrie EN 10028-3"))
           tab.append(("A 516 Gr. 60(415)","A 516 Gr. 60(415)|   |   |        | Produktbereich Grobblech"))
           tab.append(("A 572 42","A 572 42| 1 | 1 | ... | US Steels, ASME BPVC.IX"))
           tab.append(("A 633 A","A 633 A| 1 | 1 | K01802 | US Steels, ASME BPVC.IX"))
           tab.append(("A 662 A","A 662 A| 1 | 1 | K01701 | US Steels, ASME BPVC.IX"))
           tab.append(("A 662 Gr. A","A 662 Gr. A|   |   |      | Hüttenindustrie EN 10028-3"))
           tab.append(("A 662 Gr. A","A 662 Gr. A|   |   |      | Produktbereich Grobblech"))
           tab.append(("A 662 Gr. B","A 662 Gr. B|   |   |      | Produktbereich Grobblech"))
           return tab
        if(val == "P275NH"):
           tab.append(("A 516 60","A 516 60| 1 | 1 | K02100 | US Steels, ASME BPVC.IX"))
           tab.append(("A 516 Gr. 60","A 516 Gr. 60|   |   |        | Hüttenindustrie EN 10028-3"))
           tab.append(("A 572 42","A 572 42| 1 | 1 | ... | US Steels, ASME BPVC.IX"))
           tab.append(("A 633 A","A 633 A| 1 | 1 | K01802 | US Steels, ASME BPVC.IX"))
           tab.append(("A 662 A","A 662 A| 1 | 1 | K01701 | US Steels, ASME BPVC.IX"))
           tab.append(("EN 10028-3 P275NH","EN 10028-3 P275NH| 1 | 1 | ... | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "P275NL1"):
           tab.append(("A 350 LF1","A 350 LF1| 1 | 1 | K03009 | US Steels, ASME BPVC.IX"))
           tab.append(("A 516 60","A 516 60| 1 | 1 | K02100 | US Steels, ASME BPVC.IX"))
           tab.append(("A 516 Gr.55(380)","A 516 Gr.55 (380)|   |   |        | Produktbereich Grobblech"))
           tab.append(("A 516 Gr. 60","A 516 Gr. 60|   |   |        | Hüttenindustrie EN 10028-3"))
           tab.append(("A 516 Gr. 60(415)","A 516 Gr. 60(415)|   |   |        | Produktbereich Grobblech"))
           tab.append(("A 529","A 529|   |   |        | Hüttenindustrie EN 10028-3"))
           tab.append(("A 572 42","A 572 42| 1 | 1 | ... | US Steels, ASME BPVC.IX"))
           tab.append(("A 633 A","A 633 A| 1 | 1 | K01802 | US Steels, ASME BPVC.IX"))
           tab.append(("A 662 A","A 662 A| 1 | 1 | K01701 | US Steels, ASME BPVC.IX"))
           tab.append(("A 662 Gr. A","A 662 Gr. A|   |   |        | Hüttenindustrie EN 10028-3"))
           return tab
        if(val == "P275NL2"):
           tab.append(("A 662 Gr. A","A 662 Gr. A|   |   |        | Produktbereich Grobblech"))
           tab.append(("A 662 Gr. B","A 662 Gr. B|   |   |        | Produktbereich Grobblech"))
           tab.append(("A 707 L1, CI. 1","A 707 L1, CI. 1|   |   |        |US Steels, ASME BPVC.IX "))
           return tab
        if(val == "P275T1"):
           tab.append(("A 135 B","A 135 B| 1 | 1 | K03018 | US Steels, ASME BPVC.IX"))
           tab.append(("A 139 B","A 139 B| 1 | 1 | K03003 | US Steels, ASME BPVC.IX"))
           tab.append(("A 333 6","A 333 6| 1 | 1 | K03006 | US Steels, ASME BPVC.IX"))
           tab.append(("A 369 FPB","A 369 FPB| 1 | 1 | K03006 | US Steels, ASME BPVC.IX"))
           tab.append(("A 420 WPL6","A 420 WPL6| 1 | 1 | K03006 | US Steels, ASME BPVC.IX"))
           tab.append(("A 556 C2","A 556 C2| 1 | 2 | K03006 | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "P275T2"):
           tab.append(("A 135 B","A 135 B| 1 | 1 | K03018 | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "P280GH"):
           tab.append(("A 516 60","A 516 60| 1 | 1 | K02100 | US Steels, ASME BPVC.IX"))
           tab.append(("A 662 A","A 662 A| 1 | 1 | K01701 | US Steels, ASME BPVC.IX"))
           tab.append(("EN 10222-2 P280GH","EN 10222-2 P280GH| 1 | 1 | ... | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "P295GH"):
           tab.append(("A 105","A 105|   |   |        | Carbon steel - Forgings(Schmiedeteile)"))
           tab.append(("A 106 C","A 106 C| 1 | 2 | K03501 | US Steels, ASME BPVC.IX"))
           tab.append(("A 139 E","A 139 E| 1 | 1 | K03012 | US Steels, ASME BPVC.IX"))
           tab.append(("A 210 C","A 210 C| 1 | 2 | K03501 | US Steels, ASME BPVC.IX"))
           tab.append(("A 234 WPC","A 234 WPC| 1 | 2 | K03501 | US Steels, ASME BPVC.IX"))
           tab.append(("A 414 F","A 414 F| 1 | 2 | K03102 | US Steels, ASME BPVC.IX"))
           tab.append(("A 515 70","A 515 70| 1 | 2 | K03101 | US Steels, ASME BPVC.IX"))
           tab.append(("A 515 Gr.65","A 515 Gr.65|   |   |        | Carbon steel-Plates"))
           tab.append(("A 515 Gr.70","A 515 Gr.70|   |   |        | Carbon steel-Plates"))
           tab.append(("A 515 Gr.70","A 515 Gr.70|   |   |        | Hüttenindustrie EN 10028-2"))
           tab.append(("A 516 70","A 516 70| 1 | 2 | K02700  | US Steels, ASME BPVC.IX"))
           tab.append(("A 516 Gr.70","A 516 Gr.70|   |   |        | Hüttenindustrie EN 10028-2"))
           tab.append(("A 556 C2","A 556 C2| 1 | 2 | K03006  | US Steels, ASME BPVC.IX"))
           tab.append(("A 662 B","A 662 B| 1 | 2 | K02007  | US Steels, ASME BPVC.IX"))
           tab.append(("A 662 Gr. B","A 662 Gr. B|   |   |         | Hüttenindustrie EN 10028-2"))
           tab.append(("EN 10028-2 P295GH","EN 10028-2 P295GH| 1 | 1 |...      | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "P305GH"):
           tab.append(("A 105 ...","A 105...| 1 | 2 | K03504 | US Steels, ASME BPVC.IX"))
           tab.append(("A 181 CI. 70","A 181 CI. 70| 1 | 2 | K03502 | US Steels, ASME BPVC.IX"))
           tab.append(("A 266 4","A 266 4| 1 | 2 | K03017 | US Steels, ASME BPVC.IX"))
           tab.append(("A 508 1A","A 508 1A| 1 | 2 | K13502 | US Steels, ASME BPVC.IX"))
           tab.append(("A 516 65","A 516 65| 1 | 1 | K02403 | US Steels, ASME BPVC.IX"))
           tab.append(("A 541 1A","A 541 1A| 1 | 2 | K03020 | US Steels, ASME BPVC.IX"))
           tab.append(("A 662 C","A 662 C| 1 | 1 | k02203 | US Steels, ASME BPVC.IX"))
           tab.append(("EN 10222-2 P305GH","EN 10222-2 P305GH| 1 | 2 |...      | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "P310GH"):
           tab.append(("A 299 A","A 299 A| 1 | 2 | K02803 | US Steels, ASME BPVC.IX"))
           tab.append(("A 414 G","A 414 G| 1 | 2 | K03103 | US Steels, ASME BPVC.IX"))
           tab.append(("A 455...","A 455...| 1 | 2 | K03300 | US Steels, ASME BPVC.IX"))
           tab.append(("A 515 70","A 515 70| 1 | 2 | K03101 | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "P310NB"):
           tab.append(("A 333 6","A 333 6| 1 | 1 | K03006 | US Steels, ASME BPVC.IX"))
           tab.append(("A 334 6","A 334 6| 1 | 1 | K03006 | US Steels, ASME BPVC.IX"))
           tab.append(("A 350 LF1","A 350 LF1| 1 | 1 | K03009 | US Steels, ASME BPVC.IX"))
           tab.append(("A 350 LF2","A 350 LF2| 1 | 2 | K03011 | US Steels, ASME BPVC.IX"))
           tab.append(("A 414 E","A 414 E| 1 | 1 | K02704 | US Steels, ASME BPVC.IX"))
           tab.append(("A 516 60","A 516 60| 1 | 1 | K02100 | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "P315N"):
           tab.append(("A 662 C","A 662 C| 1 | 1 | K02203 | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "P315NH" or val =="P315NL"):
           tab.append(("A 516 65","A 516 65| 1 | 1 | K02403 | US Steels, ASME BPVC.IX"))
           tab.append(("A 572 50","A 572 50| 1 | 1 | ...    | US Steels, ASME BPVC.IX"))
           tab.append(("A 573 65","A 573 65| 1 | 1 | ...    | US Steels, ASME BPVC.IX"))
           tab.append(("A 618 Ib","A 618 Ib| 1 | 2 | K02601 | US Steels, ASME BPVC.IX"))
           tab.append(("A 633 A","A 633 A  | 1 | 1 | K01802 | US Steels, ASME BPVC.IX"))
           tab.append(("A 662 B","A 662 B  | 1 | 2 | K02007 | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "P355GH"):
           tab.append(("A 299","A 299|   |   |        | Hüttenindustrie EN 10028-2"))
           tab.append(("A 299 A","A 299 A| 1 | 2 | K02803 | US Steels, ASME BPVC.IX"))
           tab.append(("A 299 Gr. A","A 299 Gr. A|   |   |        | Produktbereich Grobblech"))
           tab.append(("A 299 Gr. B","A 299 Gr. B|   |   |        | Produktbereich Grobblech"))
           tab.append(("A 414 G","A 414 G| 1 | 2 | K03103| US Steels, ASME BPVC.IX"))
           tab.append(("A 455","A 455|   |   |        | Hüttenindustrie EN 10028-2"))
           tab.append(("A 455...","A 455...| 1 | 2 | K03300 | US Steels, ASME BPVC.IX"))
           tab.append(("A 515 Gr. 70","A 515 Gr. 70|   |   |        | Hüttenindustrie EN 10028-2"))
           tab.append(("A 516 70","A 516 70| 1 | 2 | K02700 | US Steels, ASME BPVC.IX"))
           tab.append(("A 516 Gr. 70","A 516 Gr. 70|   |   |        | Hüttenindustrie EN 10028-2"))
           tab.append(("A 537 CI. 1","A 537 CI. 1| 1 | 2 | K12437 | US Steels, ASME BPVC.IX"))
           tab.append(("A 537 70","A 537 70| 1 | 2 | ... | US Steels, ASME BPVC.IX"))
           tab.append(("A 612","A 612|   |   |        | Hüttenindustrie EN 10028-2"))
           tab.append(("A 612...","A 612...| 10C | 1 | K02900 | US Steels, ASME BPVC.IX"))
           tab.append(("EN 10028-2 P355GH","EN 10028-2 P355GH| 1 | 2 | ... | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "P355M"):
           tab.append(("A 515 65","A 515 65| 1 | 1 | K02800 | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "P355ML1" or val == "P355ML2"):
           tab.append(("A 515 65","A 515 65| 1 | 1 | K02800 | US Steels, ASME BPVC.IX"))
           tab.append(("A 516 65","A 516 65| 1 | 1 | K02403 | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "P355NB"):
           tab.append(("A 414 F","A 414 F | 1 | 2 | K03102 | US Steels, ASME BPVC.IX"))
           tab.append(("A 414 G","A 414 G  | 1 | 2 | K03103 | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "P355NH"):
           tab.append(("A 181 CI. 70","A 181 CI. 70 | 1 | 2 | K03502 | US Steels, ASME BPVC.IX"))
           tab.append(("A 266 4","A 266 4| 1 | 2 | K03017 | US Steels, ASME BPVC.IX"))
           tab.append(("A 508 1A","A 508 1A| 1 | 2 | K13502 | US Steels, ASME BPVC.IX"))
           tab.append(("A 516 Gr. 70","A 516 Gr. 70|   |   |        | Carbon steel-Plates"))
           tab.append(("A 541 1A","A 541 1A| 1  | 2  | K03020 | US Steels, ASME BPVC.IX"))
           tab.append(("A 618 II","A 618 II| 1  | 2  | K12609 | US Steels, ASME BPVC.IX"))
           tab.append(("A 633 D","A 633 D| 1  | 2 | K12037 | US Steels, ASME BPVC.IX"))
           tab.append(("A 662 C","A 662 C| 1  | 1 | K02203 | US Steels, ASME BPVC.IX"))
           tab.append(("A 841 A, CI. 1","A 841 A, CI. 1| 1 | 2 | ... | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "P355NL1"):
           tab.append(("A 105","A 105 |   |   |        | Produktbereich Grobblech"))
           tab.append(("A 299","A 299 |   |   |        | Hüttenindustrie EN 10028-3"))
           tab.append(("A 350 LF2","A 350 LF2 | 1 | 2 | K03011 | US Steels, ASME BPVC.IX"))
           tab.append(("A 420 WPL6","A 420 WPL6 | 1 | 1 | K03006 | US Steels, ASME BPVC.IX"))
           tab.append(("A 516 Gr. 65(450)","A 516 Gr. 65(450) |   |   |        | Produktbereich Grobblech"))
           tab.append(("A 516 Gr. 70(485)","A 516 Gr. 70(485) |   |   |        | Produktbereich Grobblech"))
           tab.append(("A 541 3, CI. 1","A 541 3, CI. 1 | 3 | 3 | K12045 | US Steels, ASME BPVC.IX"))
           tab.append(("A 633 D","A 633 D | 1 | 2 | K12037 | US Steels, ASME BPVC.IX"))
           tab.append(("A 662 C","A 662 C | 1 | 1 | K02203 | US Steels, ASME BPVC.IX"))
           tab.append(("A 707 L2, CI. 1","A 707 L2, CI. 1 | 1 | 1 | K03301 | US Steels, ASME BPVC.IX"))
           tab.append(("A 738 Gr. A","A 738 Gr. A |   |   |        | Produktbereich Grobblech"))
           tab.append(("A 841 A. CI. 1","A 841 A. CI. 1 | 1 | 2 | ...  | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "P355NL2"):
           tab.append(("A 537 CI. 1","A 537 CI. 1 | 1 | 2 | K12437 | Produktbereich Grobblech"))
           tab.append(("A 662 B","A 622 B | 1 | 2 | K02007 | US Steels, ASME BPVC.IX"))
           tab.append(("A 662 Gr. C","A662 Gr. C |   |   |       | Produktbereich Grobblech"))
           tab.append(("A 707 L3, CI. 1","A 707 L3, CI. 1 | 1 | 1 | K12510 | US Steels, ASME BPVC.IX"))
           tab.append(("A 841 A, CI. 1","A 841 A, CI. 1 | 1 | 2 | ... | US Steels, ASME BPVC.IX"))
           tab.append(("A 841 B, CI. 2","A 841 B, CI. 2 | 1 | 3 | ... | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "P420NH"):
           tab.append(("A 572 60","A 572 60 | 1 | 2 | ... | US Steels, ASME BPVC.IX"))
           tab.append(("A 633 E","A 633 E | 1 | 3 | K12202 | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "P460M" or val =="P460ML1" or val =="P460ML2"):
           tab.append(("A 738 A","A 738 A | 1 | 1 | K12447 | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "P460N"):
           tab.append(("A 225 Gr. C","A 225 Gr. C |   |   |        | Produktbereich Grobblech"))
           tab.append(("A 225 Gr. D","A 225 GR. D |   |   |        | Produktbereich Grobblech"))
           tab.append(("A 537 CI. 2","A 537 CI. 2 | 1 | 2 |K12437  | US Steels, ASME BPVC.IX"))
           tab.append(("A 612","A 612 |   |   |        | Hüttenindustrie EN 10028-2"))
           tab.append(("A 633 E","A 633 E | 1 | 3 | K12202 | US Steels, ASME BPVC.IX"))
           tab.append(("A 737 Gr. C","A 737 Gr. C |   |   |        | Hüttenindustrie EN 10028-2"))
           tab.append(("A 737 Gr. C","A 737 Gr. C |   |   |        | Produktbereich Grobblech"))
           return tab
        if(val == "P460NH"):
           tab.append(("A 612","A 612 |   |   |        | Hüttenindustrie EN 10028-2"))
           tab.append(("A 612...","A 612... | 10C | 1 |K02900  | US Steels, ASME BPVC.IX"))
           tab.append(("A 633 E","A 633 E | 1 | 3 | K12202 | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "P460NL1"):
           tab.append(("A 537 CI. 2","A 537 CI. 2 | 1 | 2 | K12437 | US Steels, ASME BPVC.IX"))
           tab.append(("A 612","A 612             |   |   |        | Hüttenindustrie EN 10028-3"))
           tab.append(("A 633 E","A 633 E         | 1 | 3 | K12202 | US Steels, ASME BPVC.IX"))
           tab.append(("A 737 Gr. C","A 737 Gr. C |   |   |        | Hüttenindustrie EN 10028-3"))
           return tab
        if(val == "P460NL2"):
           tab.append(("A 537 CI. 2","A 537 CI. 2 | 1 | 2 | K12437 | US Steels, ASME BPVC.IX"))
           tab.append(("A 633 E","A 633 E         | 1 | 3 | K12202 | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "P460Q"):
           tab.append(("A 537 CI. 2","A 537 CI. 2 | 1 | 2 | K12437 | Hüttenindustrie EN 10028-6"))
           tab.append(("A 537 CI. 2","A 537 CI. 2 | 1 | 2 | K12437 | Produktbereich Grobblech"))
           tab.append(("A 537 CI. 3","A 537 CI. 3 |   |   |        | Hüttenindustrie EN 10028-6"))
           tab.append(("A 537 CI. 3","A 537 CI. 3 |   |   |        | Produktbereich Grobblech"))
           tab.append(("A 738 Gr. B","A 738 Gr. B |   |   |        | Produktbereich Grobblech"))
           tab.append(("A 738 Gr. C","A 738 Gr. C |   |   |        | Produktbereich Grobblech"))
           return tab
        if(val == "P460QL1"):
           tab.append(("A 738 Gr. B","A 738 Gr. B |   |   |        | Produktbereich Grobblech"))
           tab.append(("A 738 Gr. C","A 738 Gr. C |   |   |        | Produktbereich Grobblech"))
           return tab
        if(val == "P460QL2"):
           tab.append(("A 537 CI. 2","A 537 CI. 2 | 1 | 2 | K12437 | Produktbereich Grobblech"))
           tab.append(("A 537 CI. 3","A 537 CI. 3 |   |   |        | Produktbereich Grobblech"))
           return tab
        if(val == "P500Q" or val == "P500QL1"):
           tab.append(("A 738 Gr. D","A 738 Gr. D |   |   |        | Produktbereich Grobblech"))
           tab.append(("A 738 Gr. E","A 738 Gr. E |   |   |        | Produktbereich Grobblech"))
           return tab
        if(val == "P690Q"):
           tab.append(("A 517 Gr. B","A 517 Gr. B |   |   |        | Hüttenindustrie EN 10028-6"))
           tab.append(("A 517 Gr. F","A 517 Gr. F |   |   |        | Hüttenindustrie EN 10028-6"))
           tab.append(("A 517 Gr. H","A 517 Gr. H |   |   |        | Hüttenindustrie EN 10028-6"))
           tab.append(("A 517 Gr. Q","A 517 Gr. Q |   |   |        | Hüttenindustrie EN 10028-6"))
           return tab
        if(val == "P690QL1"):
           tab.append(("A 517 Gr. A","A 517 Gr. A |   |   |        | Produktbereich Grobblech"))
           tab.append(("A 517 Gr. B","A 517 Gr. B |   |   |        | Produktbereich Grobblech"))
           return tab
        if(val == "S185"):
           tab.append(("A 283 A","A 283 A | 1 | 1 | K01400 | US Steels, ASME BPVC.IX"))
           tab.append(("A 513 1010","A 513 1010 | 1 | 1| G10100 | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "S235J0"):
           tab.append(("A 283 C","A 283 C| 1 | 1 | K02401 | US Steels, ASME BPVC.IX"))
           tab.append(("A 576 1016","A 576 1016 | 1 | 1 | G10160 | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "S235J2G3"):
           tab.append(("A 283 B","A 283 B| 1 | 1 | K01702 | US Steels, ASME BPVC.IX"))
           tab.append(("A 284 Gr. C","A 284 Gr. C |   |   |        | Hüttenindustrie EN 10025"))
           tab.append(("A 284 Gr. D","A 284 Gr. D |   |   |        | Hüttenindustrie EN 10025"))
           tab.append(("A 524 II","A 524 II | 1 | 1 | K02104 | US Steels, ASME BPVC.IX"))
           tab.append(("A 573 58","A 573 58 | 1 | 1 | ...   | US Steels, ASME BPVC.IX"))
           tab.append(("A 573 Gr. 65","A 573 Gr. 65|   |   |       | Hüttenindustrie EN 10025"))
           tab.append(("A 618 II","A 618 II | 1 | 2 | K12609 | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "S235JR"):
           tab.append(("A 283 C","A 283 C| 1 | 1 | K02401 | US Steels, ASME BPVC.IX"))
           tab.append(("A 283 Gr.A","A 283 Gr.A|   |   |        | Produktbereich Grobblech"))
           tab.append(("A 283 Gr.B","A 283 Gr.B|   |   |        | Produktbereich Grobblech"))
           tab.append(("A 283 Gr.C","A 283 Gr.C|   |   |        | Hüttenindustrie EN 10025"))
           tab.append(("A 283 Gr.C","A 283 Gr.C|   |   |        | Produktbereich Grobblech"))
           tab.append(("A 36","A 36|   |   |        | Hüttenindustrie EN 10025"))
           tab.append(("A 501 B","A 501 B| 1 | 2 | K03000 | US Steels, ASME BPVC.IX"))
           tab.append(("A 519 1018 HR","A 519 1018 HR| 1 | 1 | G10180 | US Steels, ASME BPVC.IX"))
           tab.append(("A 53 Type E, Gr.A","A 53 Type E, Gr.A| 1 | 1 | K02504 | US Steels, ASME BPVC.IX"))
           tab.append(("A 53 Type S, Gr.A","A 53 Type S, Gr.A| 1 | 1 | K02504 | US Steels, ASME BPVC.IX"))
           tab.append(("A 53 Type S, Gr.A","A 53 Type S, Gr.A| 1 | 1 | K02504 | US Steels, ASME BPVC.IX"))
           tab.append(("EN 10025-2 S235JR","EN 10025-2 S235JR| 1 | 1 | ...    | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "S235JRG2"):
           tab.append(("A 283 C","A 283 C| 1 | 1 | K02401 | US Steels, ASME BPVC.IX"))
           tab.append(("A 501 B","A 501 B| 1 | 2 | K03000 | US Steels, ASME BPVC.IX"))
           tab.append(("A 53 Type E, Gr. A","A 53 Type E, Gr. A| 1 | 1 | K02504 | US Steels, ASME BPVC.IX"))
           tab.append(("A 53 Type S, Gr. A","A 53 Type S, Gr. A| 1 | 1 | K02504 | US Steels, ASME BPVC.IX"))
           tab.append(("A 570 Gr. 36","A 570 Gr. 36|   |   |        | Carbon steel - Fittings(Flansche)"))
           tab.append(("A 570 Gr. 36","A 570 Gr. 36|   |   |        | Carbon steel - Plates"))
           return tab

        if(val == "S235JRH"):
           tab.append(("A 283 C","A 283 C| 1 | 1 | K02401 | US Steels, ASME BPVC.IX"))
           tab.append(("A 501 B","A 501 B| 1 | 2 | K03000 | US Steels, ASME BPVC.IX"))
           return tab

        if(val == "S255N"):
           tab.append(("A 516 55","A 516 55| 1 | 1 | K01800 | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "S275J0"):
           tab.append(("A 283 D","A 283 D| 1 | 1 | K02702 | US Steels, ASME BPVC.IX"))
           tab.append(("A 572 42","A 572 42| 1 | 1 | ... | US Steels, ASME BPVC.IX"))
           tab.append(("A 572 Gr. 42","A 572 Gr. 42|   |   |  | Hüttenindustrie EN 10025"))
           tab.append(("A 633 C","A 633 C| 1 | 2 | K12000 | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "S275J2G3"):
           tab.append(("A 283 D","A 283 D| 1 | 1 | K02702 | US Steels, ASME BPVC.IX"))
           tab.append(("A 572 42","A 572 42| 1 | 1 | ... | US Steels, ASME BPVC.IX"))
           tab.append(("A 572 Gr. 42","A 572 Gr. 42|   |   |  | Hüttenindustrie EN 10025"))
           tab.append(("A 573 58","A 573 58| 1 | 1 | ... | US Steels, ASME BPVC.IX"))
           tab.append(("A 573 Gr. 70","A 573 Gr. 70|   |   |    | Hüttenindustrie EN 10025"))
           return tab
        if(val == "S275J2H"):
           tab.append(("A 573 70","A 573 70| 1 | 2 | ... | US Steels, ASME BPVC.IX"))
           tab.append(("A 572 42","A 572 42| 1 | 2 | ... | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "S275JR"):
           tab.append(("A 283 Gr. D","A 283 Gr. D|   |   |  | Hüttenindustrie EN 10025"))
           tab.append(("A 283 Gr. D","A 283 Gr. D|   |   |  | Produktbereich Grobblech"))
           tab.append(("A 36","A 36|   |   |  | Produktbereich Grobblech"))
           tab.append(("A 501 B","A 501 B| 1 | 2 | K03000 | US Steels, ASME BPVC.IX"))
           tab.append(("A 513 1026 CW","A 513 1026 CW| 1 | 3 | G10260 | US Steels, ASME BPVC.IX"))
           tab.append(("A 519 1026 HR","A 513 1026 HR| 1 | 1 | G10260 | US Steels, ASME BPVC.IX"))
           tab.append(("A 573 Gr. 58(400)","A 573 Gr. 58(400)|   |   |    | Produktbereich Grobblech"))
           tab.append(("A 633 A","A 633 A| 1 | 1 | K01802 | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "S275N"):
           tab.append(("A 572 Gr. 42(290)","A 572 Gr. 42(290)|   |   |    | Produktbereich Grobblech"))
           tab.append(("A 662 B","A 662 B| 1 | 2 | K02007 | US Steels, ASME BPVC.IX"))
           tab.append(("A 662 Gr. A","A 662 Gr. A|   |   |  | Hüttenindustrie EN 10113-2"))
           return tab
        if(val == "S275NL"):
           tab.append(("A 633 Gr. A","A 633 Gr. A|   |   |    | Produktbereich Grobblech"))
           tab.append(("A 662 A","A 662 A| 1 | 1 | K01701 | US Steels, ASME BPVC.IX"))
           tab.append(("A 662 Gr. A","A 662 Gr. A|   |   |  | Hüttenindustrie EN 10113-2"))
           return tab
        if(val == "S275NLH"):
           tab.append(("A 572 42","A 572 42| 1 | 1 | ...  | US Steels, ASME BPVC.IX"))
           tab.append(("A 633 A","A 633 A| 1 | 1 | K01802 | US Steels, ASME BPVC.IX"))
           tab.append(("A 662 A","A 662 A| 1 | 1 | K01701 | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "S355J0"):
           tab.append(("A 572 50","A 572 50| 1 | 1 | ...  | US Steels, ASME BPVC.IX"))
           tab.append(("A 572 Gr. 50","A 572 Gr. 50|   |   |     | Hüttenindustrie EN 10025"))
           return tab
        if(val == "S355J0H"):
           tab.append(("A 572 50","A 572 50| 1 | 1 | ...  | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "S355J0W"):
           tab.append(("A 588 A","A 588 A| 3 | 1 | K11430  | US Steels, ASME BPVC.IX"))
           tab.append(("A 588 B","A 588 B| 3 | 1 | K12043  | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "S355J2"):
           tab.append(("A 738 C","A 738 C| 1 | 3 | K02008  | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "S355J2G1W"):
           tab.append(("A 588 Gr. A","A 588 Gr. A|   |   |   | Hüttenindustrie EN 10155"))
           tab.append(("A 588 Gr. A","A 588 Gr. A|   |   |   | Produktbereich Grobblech"))
           tab.append(("A 588 Gr. B","A 588 Gr. B|   |   |   | Hüttenindustrie EN 10155"))
           tab.append(("A 588 Gr. B","A 588 Gr. B|   |   |   | Produktbereich Grobblech"))
           tab.append(("A 588 Gr. C","A 588 Gr. C|   |   |   | Hüttenindustrie EN 10155"))
           tab.append(("A 588 Gr. C","A 588 Gr. C|   |   |   | Produktbereich Grobblech"))
           tab.append(("A 588 Gr. K","A 588 Gr. K|   |   |   | Hüttenindustrie EN 10155"))
           tab.append(("A 588 Gr. K","A 588 Gr. K|   |   |   | Produktbereich Grobblech"))
           tab.append(("A 618 II","A 618 II| 1 | 2 | K12609  | Produktbereich Grobblech"))
           return tab
        if(val == "S355J2G3"):
           tab.append(("A 105...","A 105...| 1 | 2 | K03504  | US Steels, ASME BPVC.IX"))
           tab.append(("A 350 LF2","A 350 LF2| 1 | 2 | K03011  | US Steels, ASME BPVC.IX"))
           tab.append(("A 381 Y48","A 381 Y48| 1 | 1 | ...  | US Steels, ASME BPVC.IX"))
           tab.append(("A 381 Y50","A 381 Y50| 1 | 1 | ...  | US Steels, ASME BPVC.IX"))
           tab.append(("A 524 I","A 524 I| 1 | 1 | K02104  | US Steels, ASME BPVC.IX"))
           tab.append(("A 572 50","A 572 50| 1 | 1 | ...  | US Steels, ASME BPVC.IX"))
           tab.append(("A 572 Gr. 50","A 572 Gr. 50|   |   |     | Hüttenindustrie EN 10025"))
           tab.append(("A 633 D","A 633 D| 1 | 2 | K12037  | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "S355J2H"):
           tab.append(("A 516 65","A 516 65| 1 | 1 | K02403  | US Steels, ASME BPVC.IX"))
           tab.append(("A 572 50","A 572 50| 1 | 1 | ...  | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "S355J2WP"):
           tab.append(("A 242","A 242|  |   |     | Produktbereich Grobblech"))
           return tab
        if(val == "S355JR"):
           tab.append(("A 573 70","A 573 70| 1| 2 | ...    | US Steels, ASME BPVC.IX"))
           tab.append(("A 573 Gr. 65(450)","A 573 Gr. 65(450)|   |   |      | Produktbereich Grobblech"))
           tab.append(("A 573 Gr. 70(485)","A 573 Gr. 70(485)|   |   |      | Produktbereich Grobblech"))
           tab.append(("A 633 C","A 633 C| 1| 2 | K12000 | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "S355M"):
           tab.append(("A 572 42","A 572 42| 1| 1 | ...    | US Steels, ASME BPVC.IX"))
           tab.append(("A 633 A","A 633 A| 1| 1 | K01802 | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "S355ML"):
           tab.append(("A 572 42","A 572 42| 1| 1 | ...    | US Steels, ASME BPVC.IX"))
           tab.append(("A 572 50","A 572 50| 1| 1 | ... | US Steels, ASME BPVC.IX"))
           tab.append(("A 633 A","A 633 A| 1| 1 | K01802 | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "S355N"):
           tab.append(("A 299 A","A 299 A| 1| 2 | K02803  | US Steels, ASME BPVC.IX"))
           tab.append(("A 541 3, CI. 1","A 541 3, CI. 1| 3 | 3 | K12045 | US Steels, ASME BPVC.IX"))
           tab.append(("A 572 Gr. 50(345)","A 572 Gr. 50(345)|  |   |     | Produktbereich Grobblech"))
           tab.append(("A 588","A 588|   |   |        | Hüttenindustrie EN 10113-2"))
           tab.append(("A 588 B","A 588 B| 3 | 1 | K12043 | US Steels, ASME BPVC.IX"))
           tab.append(("A 618 Ib","A 618 Ib| 1 | 2 | K02601 | US Steels, ASME BPVC.IX"))
           tab.append(("A 633 D","A 633 D| 1 | 2 | K12037 | US Steels, ASME BPVC.IX"))
           tab.append(("A 633 Gr. D","A 633 Gr. D|   |   |        | Hüttenindustrie EN 10113-2"))
           tab.append(("A 662 C","A 662 C| 1 | 1 | K02203 | US Steels, ASME BPVC.IX"))
           tab.append(("A 662 Gr. B","A 662 Gr. B|   |   |        | Hüttenindustrie EN 10113-2"))
           return tab
        if(val == "S355NH"):
           tab.append(("A 225 D","A 225 D| 10A | 1 | K12004  | US Steels, ASME BPVC.IX"))
           tab.append(("A 299 A","A 299 A| 1 | 2 | K02803 | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "S355NL"):
           tab.append(("A 350 LF2","A 350 LF2| 1 | 2 | K03011  | US Steels, ASME BPVC.IX"))
           tab.append(("A 541 3, CI. 1","A 541 3, CI. 1| 3 | 3 | K12045 | US Steels, ASME BPVC.IX"))
           tab.append(("A 633 D","A 633 D| 1 | 2 | K12037 | US Steels, ASME BPVC.IX"))
           tab.append(("A 633 Gr. C","A 633 Gr. C|   |   |       | Produktbereich Grobblech"))
           tab.append(("A 633 Gr. D","A 633 Gr. D|   |   |        | Hüttenindustrie EN 10113-2"))
           tab.append(("A 633 Gr. D","A 633 Gr. D|   |   |       | Produktbereich Grobblech"))
           tab.append(("A 662 C","A 662 C| 1 | 1 | K02203 | US Steels, ASME BPVC.IX"))
           tab.append(("A 662 Gr. B","A 662 Gr. B|   |   |        | Hüttenindustrie EN 10113-2"))
           return tab
        if(val == "S355NLH"):
           tab.append(("A 618 II","A 618 II| 1 | 2 | K12609 | US Steels, ASME BPVC.IX"))
           tab.append(("A 633 D","A 633 D| 1 | 2 | K12037 | US Steels, ASME BPVC.IX"))
           tab.append(("A 724 C","A 724 C| 1 | 4 | K12037 | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "S380N"):
           tab.append(("A 633 E","A 633 E| 1 | 3 | K12202 | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "S420M" or val == "S420ML"):
           tab.append(("A 588 B","A 588 B| 3 | 1 | K12043 | US Steels, ASME BPVC.IX"))
           tab.append(("A 633 D","A 633 D| 1 | 2 | K12037 | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "S420N"):
           tab.append(("A 537","A 537|   |   |     | Hüttenindustrie EN 10113-2"))
           tab.append(("A 537 CI. 2","A 537 CI. 2| 1 | 2 | K12437 | US Steels, ASME BPVC.IX"))
           tab.append(("A 572 60","A 572 60| 1 | 2 | ...   | US Steels, ASME BPVC.IX"))
           tab.append(("A 572 Gr. 55(380)","A 572 Gr. 55(380)|   |   |     | Produktbereich Grobblech"))
           tab.append(("A 572 Gr. 60(415)","A 572 Gr. 60(415)|   |   |     | Produktbereich Grobblech"))
           tab.append(("A 633 E","A 633 E| 1 | 3 | K12202 | US Steels, ASME BPVC.IX"))
           tab.append(("A 633 Gr. E","A 633 Gr. E|   |   |     | Hüttenindustrie EN 10113-2"))
           tab.append(("A 737 Gr. C","A 737 Gr. C|   |   |     | Hüttenindustrie EN 10113-2"))
           tab.append(("API 5L X60","API 5L X60| 1 | 2 | ... | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "S420NL"):
           tab.append(("A 537 CI. 2","A 537 CI. 2| 1 | 2 | K12437 | US Steels, ASME BPVC.IX"))
           tab.append(("A 572 60","A 572 60| 1 | 2 | ...   | US Steels, ASME BPVC.IX"))
           tab.append(("A 633 E","A 633 E| 1 | 3 | K12202 | US Steels, ASME BPVC.IX"))
           tab.append(("A 633 Gr. E","A 633 Gr. E|   |   |     | Hüttenindustrie EN 10113-2"))
           tab.append(("A 633 Gr. E","A 633 Gr. E|   |   |     | Produktbereich Grobblech"))
           tab.append(("A 737 Gr. C","A 737 Gr. C|   |   |     | Hüttenindustrie EN 10113-2"))
           return tab
        if(val == "S460N"):
           tab.append(("A 572 Gr. 65","A 572 Gr. 65|   |   |     | Hüttenindustrie EN 10113-2"))
           tab.append(("A 572 Gr. 65(450)","A 572 Gr. 65(450)|   |   |     | Produktbereich Grobblech"))
           tab.append(("A 633 E","A 633 E| 1 | 3 | K12202  | US Steels, ASME BPVC.IX"))
           tab.append(("A 633 Gr. E","A 633 Gr. E|   |   |       | Hüttenindustrie EN 10113-2"))
           return tab

        if(val == "S460NL"):
           tab.append(("A 633 E","A 633 E| 1 | 3 | K12202  | US Steels, ASME BPVC.IX"))
           tab.append(("A 633 Gr. E","A 633 Gr. E|   |   |       | Hüttenindustrie EN 10113-2"))
           return tab

        if(val == "S460NLH"):
           tab.append(("A 633 E","A 633 E| 1 | 3 | K12202  | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "S500N"):
           tab.append(("A 225 C","A 225 C| 10A | 1 | K12524 | US Steels, ASME BPVC.IX"))
           tab.append(("A 514 B","A 514 B| 11B | 4 | K11630 | US Steels, ASME BPVC.IX"))
           tab.append(("A 514 F","A 514 F| 11B | 3 | K11576 | US Steels, ASME BPVC.IX"))
           tab.append(("A 514 Q","A 514 Q| 11B | 9 |...     | US Steels, ASME BPVC.IX"))
           tab.append(("A 517 B","A 517 B| 11B | 4 | K11630 | US Steels, ASME BPVC.IX"))
           tab.append(("A 517 F","A 517 F| 11B | 3 | K11576 | US Steels, ASME BPVC.IX"))
           tab.append(("A 517 P","A 517 P| 11B | 8 | K21650 | US Steels, ASME BPVC.IX"))
           tab.append(("A 592 F","A 592 F| 11B | 3 | K11576 | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "S550MC"):
           tab.append(("A 656 Gr. 80(550)","A 656 Gr. 80(550)|   |   |       | Produktbereich Grobblech"))
           return tab
        if(val == "S690Q"):
           tab.append(("A 514 Gr. B","A 514 Gr. B|   |   |       | Hüttenindustrie EN 10137-2"))
           tab.append(("A 514 Gr. F","A 514 Gr. F|   |   |       | Hüttenindustrie EN 10137-2"))
           tab.append(("A 514 Gr. H","A 514 Gr. H|   |   |       | Hüttenindustrie EN 10137-2"))
           tab.append(("A 514 Gr. Q","A 514 Gr. Q|   |   |       | Hüttenindustrie EN 10137-2"))
           tab.append(("A 514 Gr. S","A 514 Gr. S|   |   |       | Hüttenindustrie EN 10137-2"))
           return tab
        if(val == "S690QL"):
           tab.append(("A 514 F","A 514 F| 11B  | 3  |K11576 | US Steels, ASME BPVC.IX"))
           tab.append(("A 514 Gr. A","A 514 Gr. A|   |   |       | Produktbereich Grobblech"))
           tab.append(("A 514 Gr. B","A 514 Gr. B|   |   |       | Produktbereich Grobblech"))
           tab.append(("A 514 Q","A 514 Q| 11B | 9 |....   | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "X10CrMoVNb9-1"):
           tab.append(("A 182 F91","A 182 F91| 15E  | 1  |K90901 | US Steels, ASME BPVC.IX"))
           tab.append(("A 213 T91","A 213 T91| 15E  | 1  |K90901 | US Steels, ASME BPVC.IX"))
           tab.append(("A 234 WP91","A 234 WP91| 15E  | 1  |K90901 | US Steels, ASME BPVC.IX"))
           tab.append(("A 335 P91","A 335 P91| 15E  | 1  |K90901 | US Steels, ASME BPVC.IX"))
           tab.append(("A 236 F91","A 236 F91| 15E  | 1  |K90901 | US Steels, ASME BPVC.IX"))
           tab.append(("A 369 FP91","A 369 FP91| 15E  | 1  |K90901 | US Steels, ASME BPVC.IX"))
           tab.append(("A 387 91, CI. 2","A 387 91, CI. 2| 15E  | 1  |K90901 | US Steels, ASME BPVC.IX"))
           tab.append(("A 387 Gr. 91","A 387 Gr. 91|   |   |       | Produktbereich Grobblech"))
           tab.append(("EN 10216-2 X10CrMoVNb9-1","EN 10216-2 X10CrMoVNb9-1| 15E  | 1  |... | US Steels, ASME BPVC.IX"))
           tab.append(("EN 10222-2 X10CrMoVNb9-1","EN 10222-2 X10CrMoVNb9-1| 15E  | 1  |... | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "X10CrNi18-8"):
           tab.append(("A 240 Type 301","A 240 Type 301| 8 | 1 | S30100  | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "X10NiCrAITi32-21"):
           tab.append(("B 366 WP NIC UNS N08800","B 366 WP NIC UNS N08800|   |   |       | Nickel Base Alloy-Fittings(Flansche)"))
           tab.append(("B 407 UNS N08800","B 407 UNS N08800|   |   |       | Nickel Base Alloy-Seamless Pipes"))
           tab.append(("B 408 UNS N08800","B 408 UNS N08800|   |   |       | Nickel Base Alloy-Rod, Bar(Stangen)"))
           tab.append(("B 409 UNS N08800","B 409 UNS N08800|   |   |       | Nickel Base Alloy-Plate"))
           tab.append(("B 514 UNS N08800","B 514 UNS N08800|   |   |       | Nickel Base Alloy-Welded Pipes"))
           tab.append(("B 564 UNS N08800","B 564 UNS N08800|   |   |       | Nickel Base Alloy-Forgings(Schmiedeteile)"))
           return tab
        if(val == "X11CrMo5+I"):
           tab.append(("A 335 Gr. P 5","A 335 Gr. P 5|   |   |       | Carbon steel - Seamless Pipes"))
           tab.append(("A 336 Gr. F 5","A 336 Gr. F 5|   |   |       | Carbon steel - Fittings(Flansche)"))
           tab.append(("A 387 Gr. 5 CI. 2","A 387 Gr. 5 CI. 2|   |   |       | Carbon steel - Plates"))
           return tab
        if(val == "X12Cr13"):
           tab.append(("A 176 Gr. 410","A 176 Gr. 410|   |   | | Unbekannt"))
           tab.append(("A 182 F6a, CI. 2","A 182 F6a, CI. 2| 6 | 3 |S41000 | US Steels, ASME BPVC.IX"))
           tab.append(("A 240 Type 410","A 240 Type 410| 6 | 1 |S41000 | US Steels, ASME BPVC.IX"))
           tab.append(("A 268 TP410","A 268 TP410| 6 | 1 |S41000 | US Steels, ASME BPVC.IX"))
           tab.append(("A 276 TP410","A 276 TP410| 6 | 1 |S41000 | US Steels, ASME BPVC.IX"))
           tab.append(("A 336 F6","A 336 F6| 6 | 3 |S41000 | US Steels, ASME BPVC.IX"))
           tab.append(("A 479 410","A 479 410| 6 | 1 |S41000 | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "X12CrMo5"):
           tab.append(("A 182 F5","A 182 F5| 5B | 1 |K41545 | US Steels, ASME BPVC.IX"))
           tab.append(("A 213 T5","A 213 T5| 5B | 1 |K41545 | US Steels, ASME BPVC.IX"))
           tab.append(("A 234 WP5, CI. 1","A 234 WP5, CI. 1| 5B | 1 |K41545 | US Steels, ASME BPVC.IX"))
           tab.append(("A 335 P5","A 335 P5| 5B | 1 |K41545 | US Steels, ASME BPVC.IX"))
           tab.append(("A 335 P5c","A 335 P5c| 5B | 1 |K41245 | US Steels, ASME BPVC.IX"))
           tab.append(("A 369 FP5","A 369 FP5| 5B | 1 |K41545 | US Steels, ASME BPVC.IX"))
           tab.append(("A 387 5, CI. 1","A 387 5, CI. 1| 5B | 1 |K41545 | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "X12Ni5"):
           tab.append(("A 645 A","A 645 A| 11A | 2 | K41583 | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "X15Cr13"):
           tab.append(("A 182 F6a, CI. 2","A 182 F6a, CI. 2| 6 | 3 | S41000 | US Steels, ASME BPVC.IX"))
           tab.append(("A 240 Type 410","A 240 Type 410| 6 | 1 | S41000 | US Steels, ASME BPVC.IX"))
           tab.append(("A 268 TP410","A 268 TP410| 6 | 1 | S41000 | US Steels, ASME BPVC.IX"))
           tab.append(("A 276 TP410","A 276 TP410| 6 | 1 | S41000 | US Steels, ASME BPVC.IX"))
           tab.append(("A 336 F6","A 336 F6| 6 | 3 | S41000 | US Steels, ASME BPVC.IX"))
           tab.append(("A 479 410","A 479 410| 6 | 1 | S41000 | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "X15CrNiSi20-12"):
           tab.append(("A 167 Type 309","A 167 Type 309| 8 | 2 | S30900 | US Steels, ASME BPVC.IX"))
           tab.append(("A 403 WP309","A 403 WP309| 8 | 2 | S30900 | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "X15CrNiSi25-21"):
           tab.append(("A 167 Type 310","A 167 Type 310| 8 | 2 | S31000 | US Steels, ASME BPVC.IX"))
           tab.append(("A 182 F310","A 182 F310| 8 | 2 | S31000 | US Steels, ASME BPVC.IX"))
           tab.append(("A 409 TP310S","A 409 TP310S| 8 | 2 | S31008 | US Steels, ASME BPVC.IX"))
           tab.append(("A 965 F310","A 965 F310| 8 | 2 | S31000 | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "X16CrMo5-1"):
           tab.append(("A 182 F5","A 182 F5| 5B | 1 | S41545 | US Steels, ASME BPVC.IX"))
           tab.append(("A 336 F5","A 336 F5| 5B | 1 | S41545 | US Steels, ASME BPVC.IX"))
           tab.append(("A 369 FP5","A 369 FP5| 5B | 1 | S41545 | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "X1CrNiMoCuN20-18-7"):
           tab.append(("A 182 F44","A 182 F44| 8 | 4 | S31254 | US Steels, ASME BPVC.IX"))
           tab.append(("A 240 S31254","A 240 S31254| 8 | 4 | S31254 | US Steels, ASME BPVC.IX"))
           tab.append(("A 249 S31254","A 249 S31254| 8 | 4 | S31254 | US Steels, ASME BPVC.IX"))
           tab.append(("A 312 S31254","A 312 S31254| 8 | 4 | S31254 | US Steels, ASME BPVC.IX"))
           tab.append(("A 358 S31254","A 358 S31254| 8 | 4 | S31254 | US Steels, ASME BPVC.IX"))
           tab.append(("A 403...","A 403...| 8 | 4 | S31254 | US Steels, ASME BPVC.IX"))
           tab.append(("A 409 S31254","A 409 S31254| 8 | 4 | S31254 | US Steels, ASME BPVC.IX"))
           tab.append(("A 479 S31254","A 479 S31254| 8 | 4 | S31254 | US Steels, ASME BPVC.IX"))
           tab.append(("A 813 S31254","A 813 S31254| 8 | 4 | S31254 | US Steels, ASME BPVC.IX"))
           tab.append(("A 814 S31254","A 814 S31254| 8 | 4 | S31254 | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "X1CrNiMoN25-22-2"):
           tab.append(("A 182 F310MoLN","A 182 F310MoLN| 8 | 2 | S31050 | US Steels, ASME BPVC.IX"))
           tab.append(("A 213 TP310MoLN","A 213 TP310MoLN| 8 | 2 | S31050 | US Steels, ASME BPVC.IX"))
           tab.append(("A 240 Type 310MoLN","A 240 Type 310MoLN| 8 | 2 | S31050 | US Steels, ASME BPVC.IX"))
           tab.append(("A 249 TP310MoLN","A 249 TP310MoLN| 8 | 2 | S31050 | US Steels, ASME BPVC.IX"))
           tab.append(("A 312 TP310MoLN","A 312 TP310MoLN| 8 | 2 | S31050 | US Steels, ASME BPVC.IX"))
           return tab

        if(val == "X1NiCrMoCu25-20-5"):
           tab.append(("A 182 F904L","A 182 F904L| 45 | ... | N08904 | US Steels, ASME BPVC.IX"))
           tab.append(("A 240 Type 904L","A 240 Type 904L| 45 | ... | N08904 | US Steels, ASME BPVC.IX"))
           tab.append(("A 249 N08904","A 249 N08904| 45 | ... | N08904 | US Steels, ASME BPVC.IX"))
           tab.append(("A 312 N08904","A 312 N08904| 45 | ... | N08904 | US Steels, ASME BPVC.IX"))
           tab.append(("B 625 UNS N08904","B 625 UNS N08904|    |     |        | Nickel Base Alloy - Plate"))
           return tab
        if(val == "X20Cr13"):
           tab.append(("A 176 Gr. 403","A 176 Gr. 403|    |     |      | Unbekannt"))
           return tab
        if(val == "X2CrMnNiN17-7-5"):
           tab.append(("A 249 TP201","A 249 TP201| 8  | 3  | S20100 | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "X2CrMoTi18-2"):
           tab.append(("A 240 S44400","A 240 S44400| 7  | 2  | S44400 | US Steels, ASME BPVC.IX"))
           tab.append(("A 479 S44400","A 479 S44400| 7  | 2  | S44400 | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "X2CrNi12"):
           tab.append(("A 1010 40","A 1010 40| 7  | 1  | S41003 | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "X2CrNi18-9"):
           tab.append(("A 240 Type 304L","A 240 Type 304L| 8  | 1  | S30403 | US Steels, ASME BPVC.IX"))
           tab.append(("A 276 TP304L","A 276 TP304L| 8  | 1  | S30403 | US Steels, ASME BPVC.IX"))
           tab.append(("A 666 304L","A 666 304L| 8  | 1  | S30403 | US Steels, ASME BPVC.IX"))
           tab.append(("EN 10028-7 X2CrNi18-9","EN 10028-7 X2CrNi18-9| 8  | 1  | ... | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "X2CrNi19-11"):
           tab.append(("A 182 F304L","A 182 F304L| 8  | 1  | S30403 | US Steels, ASME BPVC.IX"))
           tab.append(("A 182 Gr. F 304L","A 182 Gr. F 304L|    |    |        | Austenitic steel-Forgings(Schmiedeteil) "))
           tab.append(("A 213 TP304L","A 213 TP304L| 8  | 1  | S30403 | US Steels, ASME BPVC.IX"))
           tab.append(("A 240 Type 304L","A 240 Type 304L|    |    |     | Austenitic steel-Plates"))
           tab.append(("A 240 Type 304L","A 240 Type 304L| 8  | 1 | S30403 | US Steels, ASME BPVC.IX"))
           tab.append(("A 249 TP304L","A 249 TP304L| 8  | 1 | S30403 | US Steels, ASME BPVC.IX"))
           tab.append(("A 269 TP304L","A 269 TP304L| 8  | 1 | S30403 | US Steels, ASME BPVC.IX"))
           tab.append(("A 276 TP304L","A 276 TP304L| 8  | 1 | S30403 | US Steels, ASME BPVC.IX"))
           tab.append(("A 312 Gr. TP 304L","A 312 Gr. TP 304L|    |    |        | Austenitic steel-Seamless Pipes "))
           tab.append(("A 312 Gr. TP 304L","A 312 Gr. TP 304L|    |    |        | Austenitic steel-welded Pipes "))
           tab.append(("A 312 TP304L","A 312 TP304L| 8  | 1 | S30403 | US Steels, ASME BPVC.IX"))
           tab.append(("A 358 304L","A 358 304L| 8  | 1 | S30403 | US Steels, ASME BPVC.IX"))
           tab.append(("A 403 Gr. WP 304L","A 403 Gr. WP 304L|    |    |        | Austenitic steel-Forgings(Schmiedeteil) "))
           tab.append(("A 403 WP304L","A 403 WP304L| 8  | 1  | S30403 | US Steels, ASME BPVC.IX"))
           tab.append(("A 409 TP304L","A 409 TP304L| 8  | 1  | S30403 | US Steels, ASME BPVC.IX"))
           tab.append(("A 451 CPF3","A 451 CPF3| 8  | 1  | J92500 | US Steels, ASME BPVC.IX"))
           tab.append(("A 479 304L","A 479 304L| 8  | 1  | S30403 | US Steels, ASME BPVC.IX"))
           tab.append(("A 688 TP304L","A 688 TP304L| 8  | 1  | S30403 | US Steels, ASME BPVC.IX"))
           tab.append(("A 813 TP304L","A 813 TP304L| 8  | 1  | S30403 | US Steels, ASME BPVC.IX"))
           tab.append(("A 814 TP304L","A 814 TP304L| 8  | 1  | S30403 | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "X2CrNiMnMoN25-18-6-5"):
           tab.append(("A 213 S34565","A 213 S34565| 8  | 4  | S34565 | US Steels, ASME BPVC.IX"))
           tab.append(("A 240 S34565","A 240 S34565| 8  | 4  | S34565 | US Steels, ASME BPVC.IX"))
           tab.append(("A 312 S34565","A 312 S34565| 8  | 4  | S34565 | US Steels, ASME BPVC.IX"))
           tab.append(("A 376 S34565","A 376 S34565| 8  | 4  | S34565 | US Steels, ASME BPVC.IX"))
           tab.append(("A 403 S34565","A 403 S34565| 8  | 4  | S34565 | US Steels, ASME BPVC.IX"))
           tab.append(("A 409 S34565","A 409 S34565| 8  | 4  | S34565 | US Steels, ASME BPVC.IX"))
           tab.append(("A 479 S34565","A 479 S34565| 8  | 4  | S34565 | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "X2CrNiMo17-12-2"):
           tab.append(("A 182 F316L","A 182 F316L| 8  | 1  | S31603 | US Steels, ASME BPVC.IX"))
           tab.append(("A 182 Gr. F 316L","A 182 Gr. F 316L|    |    |      | Austenitic steel-Forgings(Schmiedeteil)"))
           tab.append(("A 213 TP316L","A 213 TP316L| 8  | 1  | S31603 | US Steels, ASME BPVC.IX"))
           tab.append(("A 240 Type 316L","A 240 Type 316L|    |    |        | Austenitic steel-Plates"))
           tab.append(("A 240 Type 316L","A 240 Type 316L| 8  | 1  | S31603 | US Steels, ASME BPVC.IX"))
           tab.append(("A 249 TP316L","A 249 TP316L| 8  | 1 | S31603 | US Steels, ASME BPVC.IX"))
           tab.append(("A 276 TP316L","A 276 TP316L| 8  | 1  | S31603 | US Steels, ASME BPVC.IX"))
           tab.append(("A 312 Gr. TP 316L","A 312 Gr. TP 316L|    |    |        | Austenitic steel - Seamless Pipes"))
           tab.append(("A 312 Gr. TP 316L","A 312 Gr. TP 316L|    |    |        | Austenitic stell - Welded Pipes"))
           tab.append(("A 312 TP316L","A 312 TP316L| 8  | 1  | S31603 | US Steels, ASME BPVC.IX"))
           tab.append(("A 358 316L","A 358 316L| 8  | 1  | S31603 | US Steels, ASME BPVC.IX"))
           tab.append(("A 403 Gr. WP 316L","A 403 Gr. WP 316L|    |    |        | Austenitic stell - Fittings(Flansche)"))
           tab.append(("A 403 WP316L","A 403 WP316L| 8  | 1  | S31603 | US Steels, ASME BPVC.IX"))
           tab.append(("A 409 TP316L","A 409 TP316L| 8  | 1  | S31603 | US Steels, ASME BPVC.IX"))
           tab.append(("A 479 316LN","A 479 316LN| 8  | 1  | S31653 | US Steels, ASME BPVC.IX"))
           tab.append(("A 666 316L","A 666 316L| 8  | 1  | S31603 | US Steels, ASME BPVC.IX"))
           tab.append(("A 688 TP316L","A 688 TP316L| 8  | 1  | S31603 | US Steels, ASME BPVC.IX"))
           tab.append(("A 813 TP316L","A 813 TP316L| 8  | 1  | S31603 | US Steels, ASME BPVC.IX"))
           tab.append(("A 814 TP316L","A 814 TP316L| 8  | 1  | S31603 | US Steels, ASME BPVC.IX"))
           tab.append(("A 965 F316L","A 965 F316L| 8  | 1  | S31603 | US Steels, ASME BPVC.IX"))
           tab.append(("EN 10028-7 X2CrNiMo17-12-2","EN 10028-7 X2CrNiMo17-12-2| 8  | 1  | ... | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "X2CrNiMo17-12-3"):
           tab.append(("A 182 F316L","A 182 F316L| 8  | 1  | S31603 | US Steels, ASME BPVC.IX"))
           tab.append(("A 213 TP316L","A 213 TP316L| 8  | 1  | S31603 | US Steels, ASME BPVC.IX"))
           tab.append(("A 240 Type 316L","A 240 Type 316L| 8  | 1  | S31603 | US Steels, ASME BPVC.IX"))
           tab.append(("A 249 TP316L","A 249 TP316L| 8  | 1 | S31603 | US Steels, ASME BPVC.IX"))
           tab.append(("A 269 TP316L","A 269 TP316L| 8  | 1 | S31603 | US Steels, ASME BPVC.IX"))
           tab.append(("A 276 TP316L","A 276 TP316L| 8  | 1  | S31603 | US Steels, ASME BPVC.IX"))
           tab.append(("A 312 TP316L","A 312 TP316L| 8  | 1  | S31603 | US Steels, ASME BPVC.IX"))
           tab.append(("A 358 316L","A 358 316L| 8  | 1  | S31603 | US Steels, ASME BPVC.IX"))
           tab.append(("A 403 WP316L","A 403 WP316L| 8  | 1  | S31603 | US Steels, ASME BPVC.IX"))
           tab.append(("A 409 TP316L","A 409 TP316L| 8  | 1  | S31603 | US Steels, ASME BPVC.IX"))
           tab.append(("A 479 316LN","A 479 316LN| 8  | 1  | S31653 | US Steels, ASME BPVC.IX"))
           tab.append(("A 666 316L","A 666 316L| 8  | 1  | S31603 | US Steels, ASME BPVC.IX"))
           tab.append(("A 688 TP316L","A 688 TP316L| 8  | 1  | S31603 | US Steels, ASME BPVC.IX"))
           tab.append(("A 813 TP316L","A 813 TP316L| 8  | 1  | S31603 | US Steels, ASME BPVC.IX"))
           tab.append(("A 814 TP316L","A 814 TP316L| 8  | 1  | S31603 | US Steels, ASME BPVC.IX"))
           tab.append(("A 965 F316L","A 965 F316L| 8  | 1  | S31603 | US Steels, ASME BPVC.IX"))
           return tab

        if(val == "X2CrNiMo18-14-3"):
           tab.append(("A 182 F316L","A 182 F316L| 8  | 1  | S31603 | US Steels, ASME BPVC.IX"))
           tab.append(("A 213 TP316L","A 213 TP316L| 8  | 1  | S31603 | US Steels, ASME BPVC.IX"))
           tab.append(("A 240 Type 316L","A 240 Type 316L|    |    |        | Austenitic steel-Plates"))
           tab.append(("A 240 Type 316L","A 240 Type 316L| 8  | 1  | S31603 | US Steels, ASME BPVC.IX"))
           tab.append(("A 249 TP316L","A 249 TP316L| 8  | 1 | S31603 | US Steels, ASME BPVC.IX"))
           tab.append(("A 269 TP316L","A 269 TP316L| 8  | 1 | S31603 | US Steels, ASME BPVC.IX"))
           tab.append(("A 276 TP316L","A 276 TP316L| 8  | 1  | S31603 | US Steels, ASME BPVC.IX"))
           tab.append(("A 312 TP316L","A 312 TP316L| 8  | 1  | S31603 | US Steels, ASME BPVC.IX"))
           tab.append(("A 358 316L","A 358 316L| 8  | 1  | S31603 | US Steels, ASME BPVC.IX"))
           tab.append(("A 403 WP316L","A 403 WP316L| 8  | 1  | S31603 | US Steels, ASME BPVC.IX"))
           tab.append(("A 409 TP316L","A 409 TP316L| 8  | 1  | S31603 | US Steels, ASME BPVC.IX"))
           tab.append(("A 666 316L","A 666 316L| 8  | 1  | S31603 | US Steels, ASME BPVC.IX"))
           tab.append(("A 688 TP316L","A 688 TP316L| 8  | 1  | S31603 | US Steels, ASME BPVC.IX"))
           tab.append(("A 813 TP316L","A 813 TP316L| 8  | 1  | S31603 | US Steels, ASME BPVC.IX"))
           tab.append(("A 814 TP316L","A 814 TP316L| 8  | 1  | S31603 | US Steels, ASME BPVC.IX"))
           tab.append(("A 965 F316L","A 965 F316L| 8  | 1  | S31603 | US Steels, ASME BPVC.IX"))
           return tab

        if(val == "X2CrNiMo18-15-4"):
           tab.append(("A 182 F317L","A 182 F317L| 8  | 1  | S31703 | US Steels, ASME BPVC.IX"))
           tab.append(("A 213 TP317L","A 213 TP317L| 8  | 1  | S31703 | US Steels, ASME BPVC.IX"))
           tab.append(("A 240 Type 317L","A 240 Type 317L| 8  | 1  | S31703 | US Steels, ASME BPVC.IX"))
           tab.append(("A 249 TP317L","A 249 TP317L| 8  | 1  | S31703 | US Steels, ASME BPVC.IX"))
           tab.append(("A 312 TP317L","A 312 TP317L| 8  | 1  | S31703 | US Steels, ASME BPVC.IX"))
           tab.append(("A 403 WP317L","A 403 WP317L| 8  | 1  | S31703 | US Steels, ASME BPVC.IX"))
           tab.append(("A 813 TP317L","A 813 TP317L| 8  | 1  | S31703 | US Steels, ASME BPVC.IX"))
           tab.append(("A 814 TP317L","A 814 TP317L| 8  | 1  | S31703 | US Steels, ASME BPVC.IX"))
           return tab

        if(val == "X2CrNiMoCuN25-6-3"):
           tab.append(("A 240 S32550","A 240 S32550| 10H  | 1  | S32550 | US Steels, ASME BPVC.IX"))
           tab.append(("A 479 S32550","A 479 S32550| 10H  | 1  | S32550 | US Steels, ASME BPVC.IX"))
           tab.append(("A 789 S32550","A 789 S32550| 10H  | 1  | S32550 | US Steels, ASME BPVC.IX"))
           tab.append(("A 790 S32550","A 790 S32550| 10H  | 1  | S32550 | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "X2CrNiMoCuWN25-7-4"):
           tab.append(("A 182 F55","A 182 F55| 10H  | 1  | S32760 | US Steels, ASME BPVC.IX"))
           tab.append(("A 240 S32760","A 240 S32760| 10H  | 1  | S32760 | US Steels, ASME BPVC.IX"))
           tab.append(("A 789 S32760","A 789 S32760| 10H  | 1  | S32760 | US Steels, ASME BPVC.IX"))
           tab.append(("A 790 S32760","A 790 S32760| 10H  | 1  | S32760 | US Steels, ASME BPVC.IX"))
           tab.append(("A 815 S32760","A 815 S32760| 10H  | 1  | S32760 | US Steels, ASME BPVC.IX"))
           tab.append(("A 928 S32760","A 928 S32760| 10H  | 1  | S32760 | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "X2CrNiMoN17-11-2"):
           tab.append(("A 182 F316LN","A 182 F316LN| 8  | 1  | S31653 | US Steels, ASME BPVC.IX"))
           tab.append(("A 213 TP316LN","A 213 TP316LN| 8  | 1  | S31653 | US Steels, ASME BPVC.IX"))
           tab.append(("A 240 Type 316LN","A 240 Type 316LN| 8  | 1  | S31653 | US Steels, ASME BPVC.IX"))
           tab.append(("A 249 TP316LN","A 249 TP316LN| 8  | 1 | S31653 | US Steels, ASME BPVC.IX"))
           tab.append(("A 312 TP316LN","A 312 TP316LN| 8  | 1  | S31653 | US Steels, ASME BPVC.IX"))
           tab.append(("A 358 316LN","A 358 316LN| 8  | 1  | S31653 | US Steels, ASME BPVC.IX"))
           tab.append(("A 376 TP316LN","A 376 TP316LN| 8  | 1  | S31653 | US Steels, ASME BPVC.IX"))
           tab.append(("A 403 WP316LN","A 403 WP316LN| 8  | 1  | S31653 | US Steels, ASME BPVC.IX"))
           tab.append(("A 479 316LN","A 479 TP316LN| 8  | 1  | S31653 | US Steels, ASME BPVC.IX"))
           tab.append(("A 688 TP316LN","A 688 TP316LN| 8  | 1  | S31653 | US Steels, ASME BPVC.IX"))
           tab.append(("A 813 TP316LN","A 813 TP316LN| 8  | 1  | S31653 | US Steels, ASME BPVC.IX"))
           tab.append(("A 814 TP316LN","A 814 TP316LN| 8  | 1  | S31653 | US Steels, ASME BPVC.IX"))
           tab.append(("A 965 F316LN","A 965 F316LN| 8  | 1  | S31653 | US Steels, ASME BPVC.IX"))
           tab.append(("EN 10028-7 X2CrNiMoN17-11-2","EN 10028-7 X2CrNiMoN17-11-2| 8  | 1  | ... | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "X2CrNiMoN17-13-3"):
           tab.append(("A 182 F316LN","A 182 F316LN| 8  | 1  | S31653 | US Steels, ASME BPVC.IX"))
           tab.append(("A 213 TP316LN","A 213 TP316LN| 8  | 1  | S31653 | US Steels, ASME BPVC.IX"))
           tab.append(("A 240 Type 316LN","A 240 Type 316LN| 8  | 1  | S31653 | US Steels, ASME BPVC.IX"))
           tab.append(("A 249 TP316LN","A 249 TP316LN| 8  | 1 | S31653 | US Steels, ASME BPVC.IX"))
           tab.append(("A 312 TP316LN","A 312 TP316LN| 8  | 1  | S31653 | US Steels, ASME BPVC.IX"))
           tab.append(("A 358 316LN","A 358 316LN| 8  | 1  | S31653 | US Steels, ASME BPVC.IX"))
           tab.append(("A 403 WP316LN","A 403 WP316LN| 8  | 1  | S31653 | US Steels, ASME BPVC.IX"))
           tab.append(("A 479 316LN","A 479 TP316LN| 8  | 1  | S31653 | US Steels, ASME BPVC.IX"))
           tab.append(("A 688 TP316LN","A 688 TP316LN| 8  | 1  | S31653 | US Steels, ASME BPVC.IX"))
           tab.append(("A 813 TP316LN","A 813 TP316LN| 8  | 1  | S31653 | US Steels, ASME BPVC.IX"))
           tab.append(("A 814 TP316LN","A 814 TP316LN| 8  | 1  | S31653 | US Steels, ASME BPVC.IX"))
           tab.append(("A 965 F316LN","A 965 F316LN| 8  | 1  | S31653 | US Steels, ASME BPVC.IX"))
           tab.append(("EN 10028-7 X2CrNiMoN17-13-3","EN 10028-7 X2CrNiMoN17-13-3| 8  | 1  | ... | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "X2CrNiMoN17-13-5"):
           tab.append(("A 213 TP317LMN","A 213 TP317LMN| 8  | 4  | S31726 | US Steels, ASME BPVC.IX"))
           tab.append(("A 249 S31726 ","A 249 S31726| 8  | 4 | S31726 | US Steels, ASME BPVC.IX"))
           tab.append(("A 312 S31726 ","A 312 S31726| 8  | 4 | S31726 | US Steels, ASME BPVC.IX"))
           tab.append(("A 358 S31726 ","A 358 S31726| 8  | 4 | S31726 | US Steels, ASME BPVC.IX"))
           tab.append(("A 376 S31726 ","A 376 S31726| 8  | 4 | S31726 | US Steels, ASME BPVC.IX"))
           tab.append(("A 403 WP S31726 ","A 403 WP S31726| 8  | 4 | S31726 | US Steels, ASME BPVC.IX"))
           tab.append(("A 409 S31726 ","A 409 S31726| 8  | 4 | S31726 | US Steels, ASME BPVC.IX"))
           tab.append(("A 479 S31726 ","A 479 S31726| 8  | 4 | S31726 | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "X2CrNiMoN22-5-3"):
           tab.append(("A 182 F60 ","A 182 F60| 10H | 1 | S32205 | US Steels, ASME BPVC.IX"))
           tab.append(("A 240 S31803","A 240 S31803| 10H | 1 | S31803 | US Steels, ASME BPVC.IX"))
           tab.append(("A 240 Type 2205","A 240 Type 2205|   |   |        | Austenitic steel-Plates"))
           tab.append(("A 479...","A 479...| 10H | 1 | S31803 | US Steels, ASME BPVC.IX"))
           tab.append(("A 789 S31803","A 789 S31803| 10H | 1 | S31803 | US Steels, ASME BPVC.IX"))
           tab.append(("A 790 S31803","A 790 S31803| 10H | 1 | S31803 | US Steels, ASME BPVC.IX"))
           tab.append(("A 815 S31803","A 815 S31803| 10H | 1 | S31803 | US Steels, ASME BPVC.IX"))
           tab.append(("A 890 4A","A 890 4A| 10H | 1 | J92205 | US Steels, ASME BPVC.IX"))
           return tab

        if(val == "X2CrNiMoN25-7-4"):
           tab.append(("A 182 F53","A 182 F53| 10H | 1 | S32750 | US Steels, ASME BPVC.IX"))
           tab.append(("A 479 S32750","A 479 S32750| 10H | 1 | S32750 | US Steels, ASME BPVC.IX"))
           tab.append(("A 789 S32750","A 789 S32750| 10H | 1 | S32750 | US Steels, ASME BPVC.IX"))
           tab.append(("A 815 S2507","A 815 S2507| 10H | 1 | S32750 | US Steels, ASME BPVC.IX"))
           return tab

        if(val == "X2CrNiN18-10"):
           tab.append(("A 182 F304LN","A 182 F304LN| 8 | 1 | S30453 | US Steels, ASME BPVC.IX"))
           tab.append(("A 213 TP304LN","A 213 TP304LN| 8 | 1 | S30453 | US Steels, ASME BPVC.IX"))
           tab.append(("A 240 Type 304LN","A 240 Type 304LN| 8 | 1 | S30453 | US Steels, ASME BPVC.IX"))
           tab.append(("A 249 TP304LN","A 249 TP304LN| 8 | 1 | S30453 | US Steels, ASME BPVC.IX"))
           tab.append(("A 312 TP304LN","A 312 TP304LN| 8 | 1 | S30453 | US Steels, ASME BPVC.IX"))
           tab.append(("A 358 304LN","A 358 304LN| 8 | 1 | S30453 | US Steels, ASME BPVC.IX"))
           tab.append(("A 376 TP304LN","A 376 TP304LN| 8 | 1 | S30453 | US Steels, ASME BPVC.IX"))
           tab.append(("A 403 WP304LN","A 403 WP304LN| 8 | 1 | S30453 | US Steels, ASME BPVC.IX"))
           tab.append(("A 479 304LN","A 479 304LN| 8 | 1 | S30453 | US Steels, ASME BPVC.IX"))
           tab.append(("A 666 304LN","A 666 304LN| 8 | 1 | S30453 | US Steels, ASME BPVC.IX"))
           tab.append(("A 688 TP304LN","A 688 TP304LN| 8 | 1 | S30453 | US Steels, ASME BPVC.IX"))
           return tab

        if(val == "X2CrNiN23-4"):
           tab.append(("A 789 S32304","A 789 S32304| 10H | 1 | S32304 | US Steels, ASME BPVC.IX"))
           tab.append(("A 928 2304","A 928 2304| 10H | 1 | S32304 | US Steels, ASME BPVC.IX"))
           return tab

        if(val == "X2CrNiN23-4"):
           tab.append(("A 268 TP409","A 268 TP409| 7 | 1 | S40900 | US Steels, ASME BPVC.IX"))
           return tab

        if(val == "X3CrNiMo13-4"):
           tab.append(("A 182 F6NM","A 182 F6NM| 6 | 4 | S41500 | US Steels, ASME BPVC.IX"))
           tab.append(("A 240 S41500","A 240 S41500| 6 | 4 | S41500 | US Steels, ASME BPVC.IX"))
           tab.append(("A 268 S41500","A 268 S41500| 6 | 4 | S41500 | US Steels, ASME BPVC.IX"))
           tab.append(("A 352 CA6NM","A 352 CA6NM| 6 | 4 | J91540 | US Steels, ASME BPVC.IX"))
           tab.append(("A 479 S41500","A 479 S41500| 6 | 4 | S41500 | US Steels, ASME BPVC.IX"))
           tab.append(("A 487 CA6NM CI. B","A 487 CA6NM CI. B| 6 | 4 | J91540 | US Steels, ASME BPVC.IX"))
           tab.append(("A 815 S41500","A 815 S41500| 6 | 4 | S41500 | US Steels, ASME BPVC.IX"))
           return tab

        if(val == "X3CrNiMo17-13-3"):
           tab.append(("A 182 F310MoLN","A 182 F310MoLN| 8 | 2 | S31050 | US Steels, ASME BPVC.IX"))
           tab.append(("A 213 TP316","A 213 TP 316| 8 | 1 | S31600 | US Steels, ASME BPVC.IX"))
           tab.append(("A 240 Type 316","A 240 Type 316| 8 | 1 | S31600 | US Steels, ASME BPVC.IX"))
           tab.append(("A 249 TP316","A 249 TP316| 8 | 1 | S31600 | US Steels, ASME BPVC.IX"))
           tab.append(("A 269 TP316","A 269 TP316| 8 | 1 | S31600 | US Steels, ASME BPVC.IX"))
           tab.append(("A 276 TP316","A 276 TP316| 8 | 1 | S31600 | US Steels, ASME BPVC.IX"))
           tab.append(("A 312 TP316","A 312 TP316| 8 | 1 | S31600 | US Steels, ASME BPVC.IX"))
           tab.append(("A 409 TP316","A 312 TP316| 8 | 1 | S31600 | US Steels, ASME BPVC.IX"))
           tab.append(("A 479 316","A 479 316| 8 | 1 | S31600 | US Steels, ASME BPVC.IX"))
           tab.append(("A 666 316","A 666 316| 8 | 1 | S31600 | US Steels, ASME BPVC.IX"))
           tab.append(("A 688 TP316","A 688 TP316| 8 | 1 | S31600 | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "X3CrNiMoBN17-13-3"):
           tab.append(("A 182 F347H","A 182 F347H| 8 | 1 | S34709 | US Steels, ASME BPVC.IX"))
           tab.append(("A 213 TP347H","A 213 TP347H| 8 | 1 | S34709 | US Steels, ASME BPVC.IX"))
           tab.append(("A 249 TP347H","A 249 TP347H| 8 | 1 | S34709 | US Steels, ASME BPVC.IX"))
           tab.append(("A 312 TP347H","A 312 TP347H| 8 | 1 | S34709 | US Steels, ASME BPVC.IX"))
           tab.append(("A 376 TP347H","A 376 TP347H| 8 | 1 | S34709 | US Steels, ASME BPVC.IX"))
           tab.append(("A 403 WP347H","A 403 WP347H| 8 | 1 | S34709 | US Steels, ASME BPVC.IX"))
           tab.append(("A 479 347H","A 479 347H| 8 | 1 | S34709 | US Steels, ASME BPVC.IX"))
           tab.append(("A 813 TP347H","A 813 TP347H| 8 | 1 | S34709 | US Steels, ASME BPVC.IX"))
           tab.append(("A 814 TP347H","A 814 TP347H| 8 | 1 | S34709 | US Steels, ASME BPVC.IX"))
           tab.append(("A 965 F347H","A 965 F347H| 8 | 1 | S34709 | US Steels, ASME BPVC.IX"))
           return tab

        if(val == "X3CrNiMoN27-5-2"):
           tab.append(("A 182 F50","A 182 F50| 10H | 1 | S31200 | US Steels, ASME BPVC.IX"))
           tab.append(("A 240 Type 329","A 240 Type 329| 10H | 1 | S32900 | US Steels, ASME BPVC.IX"))
           tab.append(("A 789 S31200","A 789 S31200| 10H | 1 | S31200 | US Steels, ASME BPVC.IX"))
           tab.append(("A 790 S31200","A 790 S31200| 10H | 1 | S31200 | US Steels, ASME BPVC.IX"))
           return tab

        if(val == "X3CrTi17"):
           tab.append(("A 240 Type 439","A 240 Type 439| 7 | 2 | S43035 | US Steels, ASME BPVC.IX"))
           tab.append(("A 268 TP430Ti","A 268 TP430Ti| 7 | 2 | S43036 | US Steels, ASME BPVC.IX"))
           tab.append(("A 268 TP439","A 268 TP439| 7 | 2 | S43035 | US Steels, ASME BPVC.IX"))
           tab.append(("A 479 439","A 479 439| 7 | 2 | S43035 | US Steels, ASME BPVC.IX"))
           tab.append(("A 803 TP439","A 803 TP439| 7 | 2 | S43035 | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "X4CrNi18-12"):
           tab.append(("A 167 Type 308","A 167 Type 308| 8 | 2 | S30800 | US Steels, ASME BPVC.IX"))
           tab.append(("A 240 Type 305","A 240 Type 305| 8 | 1 | S30500 | US Steels, ASME BPVC.IX"))
           return tab

        if(val == "X5CrNi18-10"):
           tab.append(("A 182 F304","A 182 F304| 8 | 1 | S30400 | US Steels, ASME BPVC.IX"))
           tab.append(("A 182 Gr. F 304","A 182 Gr. F 304|   |   |  | Austenitic steel-Forgings(Schmiedeteil)"))
           tab.append(("A 182 Gr. F 304 H","A 182 Gr. F 304 H|   |   |  | Austenitic steel-Forgings(Schmiedeteil)"))
           tab.append(("A 213 TP304","A 213 TP304| 8 | 1 | S30400 | US Steels, ASME BPVC.IX"))
           tab.append(("A 240 Type 304","A 213 Type 304| 8 | 1 | S30400 | Austenitic steel-Plates"))
           tab.append(("A 240 Type 304","A 240 Type 304| 8 | 1 | S30400 | US Steels, ASME BPVC.IX"))
           tab.append(("A 240 Type 304 H","A 240 Type 304 H|   |   |   | Austenitic steel-Plates"))
           tab.append(("A 249 TP304","A 249 TP304| 8 | 1 | S30400 | US Steels, ASME BPVC.IX"))
           tab.append(("A 269 TP304","A 269 TP304| 8 | 1 | S30400 | US Steels, ASME BPVC.IX"))
           tab.append(("A 276 TP304","A 276 TP304| 8 | 1 | S30400 | US Steels, ASME BPVC.IX"))
           tab.append(("A 312 Gr. TP 304","A 312 Gr. TP 304|   |   |   | Austenitic steel-Seamless Pipes"))
           tab.append(("A 312 Gr. TP 304","A 312 Gr. TP 304|   |   |   | Austenitic steel-Welded Pipes"))
           tab.append(("A 312 Gr. TP 304 H","A 312 Gr. TP 304 H|   |   |   | Austenitic steel-Seamless Pipes"))
           tab.append(("A 312 Gr. TP 304 H","A 312 Gr. TP 304 H|   |   |   | Austenitic steel-Welded Pipes"))
           tab.append(("A 312 TP304","A 312 TP304| 8 | 1 | S30400  | US Steels, ASME BPVC.IX"))
           tab.append(("A 358 304","A 358 304| 8 | 1 | S30400  | US Steels, ASME BPVC.IX"))
           tab.append(("A 376 TP304","A 376 TP304| 8 | 1 | S30400  | US Steels, ASME BPVC.IX"))
           tab.append(("A 403 Gr. WP 304","A 403 Gr. WP 304|   |   |   | Austenitic steel-Fittings(Flansche)"))
           tab.append(("A 403 Gr. WP 304 H","A 403 Gr. WP 304 H|   |   |   | Austenitic steel-Fittings(Flansche)"))
           tab.append(("A 403 WP304","A 403 WP304| 8 | 1 | S30400  | US Steels, ASME BPVC.IX"))
           tab.append(("A 409 TP304","A 409 TP304| 8 | 1 | S30400  | US Steels, ASME BPVC.IX"))
           tab.append(("A 451 CPF8","A 451 CPF8| 8 | 1 | J92600  | US Steels, ASME BPVC.IX"))
           tab.append(("A 479 304","A 479 304| 8 | 1 | S30400  | US Steels, ASME BPVC.IX"))
           tab.append(("A 666 304","A 666 304| 8 | 1 | S30400  | US Steels, ASME BPVC.IX"))
           tab.append(("A 688 TP304","A 688 TP304| 8 | 1 | S30400  | US Steels, ASME BPVC.IX"))
           tab.append(("A 813 TP304","A 813 TP304| 8 | 1 | S30400  | US Steels, ASME BPVC.IX"))
           tab.append(("A 814 TP304","A 814 TP304| 8 | 1 | S30400  | US Steels, ASME BPVC.IX"))
           tab.append(("A 965 F304","A 965 F304| 8 | 1 | S30400  | US Steels, ASME BPVC.IX"))
           tab.append(("EN 10028-7 X5CrNi18-10","EN 10028-7 X5CrNi18-10| 8 | 1 | ...  | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "X5CrNiMo17-12-2"):
           tab.append(("A 182 F316","A 182 F316| 8 | 1 | S31600 | US Steels, ASME BPVC.IX"))
           tab.append(("A 182 Gr. F 316","A 182 Gr. F 316|   |   |  | Austenitic steel-Forgings(Schmiedeteil)"))
           tab.append(("A 312 TP316","A 312 TP316| 8 | 1 | S31600 | US Steels, ASME BPVC.IX"))
           tab.append(("A 240 Type 316","A 240 Type 316| 8 | 1 | S31600 | Austenitic steel- Plates"))
           tab.append(("A 240 Type 316","A 240 Type 316| 8 | 1 | S31600 | US Steels, ASME BPVC.IX"))
           tab.append(("A 249 TP316","A 249 TP316| 8 | 1 | S31600 | US Steels, ASME BPVC.IX"))
           tab.append(("A 269 TP316","A 269 TP316| 8 | 1 | S31600 | US Steels, ASME BPVC.IX"))
           tab.append(("A 276 TP316","A 276 TP316| 8 | 1 | S31600 | US Steels, ASME BPVC.IX"))
           tab.append(("A 312 Gr. TP 316","A 312 Gr. TP 316|   |   |   | Austenitic steel - Seamless Pipes"))
           tab.append(("A 312 Gr. TP 316","A 312 Gr. TP 316|   |   |   | Austenitic steel - Welded Pipes"))
           tab.append(("A 312 TP316","A 312 TP316| 8 | 1 | S31600 | US Steels, ASME BPVC.IX"))
           tab.append(("A 358 316","A 358 316| 8 | 1 | S31600 | US Steels, ASME BPVC.IX"))
           tab.append(("A 376 TP316","A 376 TP316| 8 | 1 | S31600 | US Steels, ASME BPVC.IX"))
           tab.append(("A 403 Gr. WP F 316","A 403 Gr. WP F 316|   |   |   | Austenitic steel-Fittings(Flansche)"))
           tab.append(("A 403 WP316","A 403 WP316| 8 | 1 | S31600 | US Steels, ASME BPVC.IX"))
           tab.append(("A 409 TP316","A 409 TP316| 8 | 1 | S31600 | US Steels, ASME BPVC.IX"))
           tab.append(("A 479 316","A 479 316| 8 | 1 | S31600 | US Steels, ASME BPVC.IX"))
           tab.append(("A 666 316","A 666 316| 8 | 1 | S31600 | US Steels, ASME BPVC.IX"))
           tab.append(("A 813 TP316","A 813 TP316| 8 | 1 | S31600 | US Steels, ASME BPVC.IX"))
           tab.append(("A 814 TP316","A 814 TP316| 8 | 1 | S31600 | US Steels, ASME BPVC.IX"))
           tab.append(("A 965 F316","A 965 F316| 8 | 1 | S31600 | US Steels, ASME BPVC.IX"))
           tab.append(("EN 10028-7 X5CrNiMo17-12-2","EN 10028-7 X5CrNiMo17-12-2| 8 | 1 | ... | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "X5CrNiN19-9"):
           tab.append(("A 182 F304N","A 182 F304N| 8 | 1 | S30451 | US Steels, ASME BPVC.IX"))
           tab.append(("A 213 TP304N","A 213 TP304N| 8 | 1 | S30451 | US Steels, ASME BPVC.IX"))
           tab.append(("A 240 Type 304N","A 240 Type 304N| 8 | 1 | S30451 | US Steels, ASME BPVC.IX"))
           tab.append(("A 249 TP304N","A 249 TP304N| 8 | 1 | S30451 | US Steels, ASME BPVC.IX"))
           tab.append(("A 312 TP304N","A 312 TP304N| 8 | 1 | S30451 | US Steels, ASME BPVC.IX"))
           tab.append(("A 358 304N","A 358 304N| 8 | 1 | S30451 | US Steels, ASME BPVC.IX"))
           tab.append(("A 376 TP304N","A 376 TP304N| 8 | 1 | S30451 | US Steels, ASME BPVC.IX"))
           tab.append(("A 479 304N","A 479 304N| 8 | 1 | S30451 | US Steels, ASME BPVC.IX"))
           tab.append(("A 666 304N","A 666 304N| 8 | 1 | S30451 | US Steels, ASME BPVC.IX"))
           tab.append(("A 688 TP304N","A 688 TP304N| 8 | 1 | S30451 | US Steels, ASME BPVC.IX"))
           tab.append(("A 813 TP304N","A 813 TP304N| 8 | 1 | S30451 | US Steels, ASME BPVC.IX"))
           tab.append(("A 814 TP304N","A 814 TP304N| 8 | 1 | S30451 | US Steels, ASME BPVC.IX"))
           tab.append(("A 965 F304N","A 965 F304N| 8 | 1 | S30451 | US Steels, ASME BPVC.IX"))
           tab.append(("EN 10028-7 X5CrNiN19-9","EN 10028-7 X5CrNiN19-9| 8 | 1 | ... | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "X6Cr13"):
           tab.append(("A 240 Type 410S","A 240 Type 410S| 7 | 1 | S41008 | US Steels, ASME BPVC.IX"))
           tab.append(("A 479 403","A 479 403| 6 | 1 | S40300 | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "X6Cr17"):
           tab.append(("A 240 Type 430","A 240 Type 430| 7 | 2 | S43000 | US Steels, ASME BPVC.IX"))
           tab.append(("A 268 TP430","A 268 TP430| 7 | 2 | S43000 | US Steels, ASME BPVC.IX"))
           tab.append(("A 479 430","A 479 430| 7 | 2 | S43000 | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "X6CrAI13"):
           tab.append(("A 240 Type 405","A 240 Type 405| 7 | 1 | S40500 | US Steels, ASME BPVC.IX"))
           tab.append(("A 268 TP405","A 268 TP405| 7 | 1 | S40500 | US Steels, ASME BPVC.IX"))
           tab.append(("A 479 405","A 479 405| 7 | 1 | S40500 | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "X6CrNi18-10"):
           tab.append(("A 182 F304H","A 182 F304H| 8 | 1 | S30409 | US Steels, ASME BPVC.IX"))
           tab.append(("A 182 Gr. F 304","A 182 Gr. F 304|   |   |  | Austenitic steel-Forgings(Schmiedeteil)"))
           tab.append(("A 182 Gr. F 304 H","A 182 Gr. F 304 H|   |   |  | Austenitic steel-Forgings(Schmiedeteil)"))
           tab.append(("A 213 TP304H","A 213 TP304H| 8 | 1 | S30409 | US Steels, ASME BPVC.IX"))
           tab.append(("A 240 Type 304","A 240 Type 304| 8 | 1 | S30400 | Austenitic steel - Plates"))
           tab.append(("A 240 Type 304 H","A 240 Type 304 H|   |   |   | Austenitic steel - Plates"))
           tab.append(("A 240 Type 304 H","A 240 Type 304 H| 8 | 1 | S30409 | US Steels, ASME BPVC.IX"))
           tab.append(("A 249 TP304H","A 249 TP304H| 8 | 1 | S30409 | US Steels, ASME BPVC.IX"))
           tab.append(("A 312 Gr. TP 304","A 312 Gr. TP 304|   |   |    | Austenitic steel - Seamless Pipes"))
           tab.append(("A 312 Gr. TP 304 H","A 312 Gr. TP 304 H|   |   |    | Austenitic steel - Seamless Pipes"))
           tab.append(("A 312 TP304H","A 312 TP304H| 8 | 1 | S30409 | US Steels, ASME BPVC.IX"))
           tab.append(("A 358 304H","A 358 304H| 8 | 1 | S30409 | US Steels, ASME BPVC.IX"))
           tab.append(("A 376 TP304H","A 376 TP304H| 8 | 1 | S30409 | US Steels, ASME BPVC.IX"))
           tab.append(("A 403 Gr. WP 304","A 403 Gr. WP 304|   |   |   | Austenitic steel-Fittings(Flansche)"))
           tab.append(("A 403 Gr. WP 304 H","A 403 Gr. WP 304 H|   |   |   | Austenitic steel-Fittings(Flansche)"))
           tab.append(("A 403 WP304H","A 403 WP304H| 8 | 1 | S30409 | US Steels, ASME BPVC.IX"))
           tab.append(("A 479 304H","A 479 304H| 8 | 1 | S30409 | US Steels, ASME BPVC.IX"))
           tab.append(("A 813 TP304H","A 813 TP304H| 8 | 1 | S30409 | US Steels, ASME BPVC.IX"))
           tab.append(("A 814 TP304H","A 814 TP304H| 8 | 1 | S30409 | US Steels, ASME BPVC.IX"))
           tab.append(("A 965 F304H","A 965 F304H| 8 | 1 | S30409 | US Steels, ASME BPVC.IX"))
           return tab

        if(val == "X6CrNi23-13"):
           tab.append(("A 213 TP309H","A 213 TP309H| 8 | 2 | S30909 | US Steels, ASME BPVC.IX"))
           tab.append(("A 240 Type 309H","A 240 Type 309H| 8 | 2 | S30909 | US Steels, ASME BPVC.IX"))
           tab.append(("A 249 TP309H","A 249 TP309H| 8 | 2 | S30909 | US Steels, ASME BPVC.IX"))
           tab.append(("A 312 TP309H","A 312 TP309H| 8 | 2 | S30909 | US Steels, ASME BPVC.IX"))
           return tab

        if(val == "X6CrNi25-20"):
           tab.append(("A 213 TP310H","A 213 TP310H| 8 | 2 | S31009 | US Steels, ASME BPVC.IX"))
           tab.append(("A 240 Type 310H","A 240 Type 310H| 8 | 2 | S31009 | US Steels, ASME BPVC.IX"))
           tab.append(("A 249 TP310H","A 249 TP310H| 8 | 2 | S31009 | US Steels, ASME BPVC.IX"))
           tab.append(("A 312 TP310H","A 312 TP310H| 8 | 2 | S31009 | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "X6CrNiMoNb17-12-2"):
           tab.append(("A 240 Type 316Cb","A 240 Type 316Cb| 8 | 1 | S31640 | US Steels, ASME BPVC.IX"))
           tab.append(("A 479 316Cb","A 479 316Cb| 8 | 1 | S31640 | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "X6CrNiMoTi17-12-2"):
           tab.append(("A 213 TP316Ti","A 213 TP316Ti| 8 | 1 | S31665 | US Steels, ASME BPVC.IX"))
           tab.append(("A 240 Type 316 Ti","A 240 Type 316 Ti|   |   |      | Austenitic steel - Plates"))
           tab.append(("A 240 Type 316Ti","A 240 Type 316Ti| 8 | 1 | S31635 | US Steels, ASME BPVC.IX"))
           tab.append(("A 312 TP316Ti","A 312 TP316Ti| 8 | 1 | S31635 | US Steels, ASME BPVC.IX"))
           tab.append(("A 403 WP316L","A 403 WP316L| 8 | 1 | S31603 | US Steels, ASME BPVC.IX"))
           tab.append(("A 479 316L","A 479 316L| 8 | 1 | S31603 | US Steels, ASME BPVC.IX"))
           tab.append(("EN 10088-2 X6CrNiMoTi17-12-2","EN 10088-2 X6CrNiMoTi17-12-2| 8 | 1 | ... | US Steels, ASME BPVC.IX"))
           return tab

        if(val == "X6CrNiNb18-10"):
           tab.append(("A 182 F347","A 182 F347| 8 | 1 | S34700 | US Steels, ASME BPVC.IX"))
           tab.append(("A 213 TP347","A 213 TP347| 8 | 1 | S34700 | US Steels, ASME BPVC.IX"))
           tab.append(("A 240 Type 347","A 240 Type 347| 8 | 1 | S34700 | Austenitic steel - Plates"))
           tab.append(("A 240 Type 347","A 240 Type 347| 8 | 1 | S34700 | US Steels, ASME BPVC.IX"))
           tab.append(("A 240 Type 348","A 240 Type 348|   |   |        | Austenitic steel - Plates"))
           tab.append(("A 249 TP347","A 249 TP347| 8 | 1 | S34700 | US Steels, ASME BPVC.IX"))
           tab.append(("A 312 TP347","A 312 TP347| 8 | 1 | S34700 | US Steels, ASME BPVC.IX"))
           tab.append(("A 376 TP347","A 376 TP347| 8 | 1 | S34700 | US Steels, ASME BPVC.IX"))
           tab.append(("A 403 WP347","A 403 WP347| 8 | 1 | S34700 | US Steels, ASME BPVC.IX"))
           tab.append(("A 409 TP347","A 409 TP347| 8 | 1 | S34700 | US Steels, ASME BPVC.IX"))
           tab.append(("A 479 347","A 479 347| 8 | 1 | S34700 | US Steels, ASME BPVC.IX"))
           tab.append(("A 813 TP347","A 813 TP347| 8 | 1 | S34700 | US Steels, ASME BPVC.IX"))
           tab.append(("A 814 TP347","A 814 TP347| 8 | 1 | S34700 | US Steels, ASME BPVC.IX"))
           tab.append(("A 965 F347","A 965 F347| 8 | 1 | S34700 | US Steels, ASME BPVC.IX"))
           return tab

        if(val == "X6CrNiTi18-10"):
           tab.append(("A 182 F321","A 182 F321| 8 | 1 | S32100 | US Steels, ASME BPVC.IX"))
           tab.append(("A 182 Gr. F 321","A 182 Gr. F 321|   |   |       | Austenitic steel-Forgings(Schmiedeteil)"))
           tab.append(("A 213 TP321","A 213 TP321| 8 | 1 | S32100 | US Steels, ASME BPVC.IX"))
           tab.append(("A 240 Type 321","A 240 Type 321| 8 | 1 | S31200 | Austenitic steel-Plates"))
           tab.append(("A 240 Type 321","A 240 Type 321| 8 | 1 | S31200 | US Steels, ASME BPVC.IX"))
           tab.append(("A 249 TP321","A 249 TP321| 8 | 1 | S32100 | US Steels, ASME BPVC.IX"))
           tab.append(("A 312 Gr. TP 321","A 312 Gr. TP 321|   |   |    | Austenitic steel - Seamless Pipes"))
           tab.append(("A 312 Gr. TP 321","A 312 Gr. TP 321|   |   |    | Austenitic steel - Welded Pipes"))
           tab.append(("A 312 TP321","A 312 TP321| 8 | 1 | S32100 | US Steels, ASME BPVC.IX"))
           tab.append(("A 358 321","A 358 321| 8 | 1 | S32100 | US Steels, ASME BPVC.IX"))
           tab.append(("A 376 TP321","A 376 TP321| 8 | 1 | S32100 | US Steels, ASME BPVC.IX"))
           tab.append(("A 403 Gr. WP 321","A 403 Gr. WP 321|   |   |   | Austenitic steel-Fittings(Flansche)"))
           tab.append(("A 403 WP321","A 403 WP321| 8 | 1 | S32100 | US Steels, ASME BPVC.IX"))
           tab.append(("A 409 TP321","A 409 TP321| 8 | 1 | S32100 | US Steels, ASME BPVC.IX"))
           tab.append(("A 479 321","A 479 321| 8 | 1 | S32100 | US Steels, ASME BPVC.IX"))
           tab.append(("A 813 TP321","A 813 TP321| 8 | 1 | S32100 | US Steels, ASME BPVC.IX"))
           tab.append(("A 814 TP321","A 814 TP321| 8 | 1 | S32100 | US Steels, ASME BPVC.IX"))
           tab.append(("A 965 F321","A 965 F321| 8 | 1 | S32100 | US Steels, ASME BPVC.IX"))
           tab.append(("EN 10028-7 X6CrNiTi18-10","EN 10028-7 X6CrNiTi18-10| 8 | 1 | ... | US Steels, ASME BPVC.IX"))
           return tab

        if(val == "X6CrNiTiB18-10"):
           tab.append(("A 240 Type 321","A 240 Type 321| 8 | 1 | S31200 | US Steels, ASME BPVC.IX"))
           tab.append(("A 240 Type 321H","A 240 Type 321H| 8 | 1 | S31209 | US Steels, ASME BPVC.IX"))
           return tab

        if(val == "X7Ni9"):
           tab.append(("A 353...","A 353...| 11A | 1 | K81340 | US Steels, ASME BPVC.IX"))
           tab.append(("EN 10028-4 X7Ni9","EN 10028-4 X7Ni9| 11A | 1 | ... | US Steels, ASME BPVC.IX"))
           return tab

        if(val == "X8CrNi25-21"):
           tab.append(("A 213 TP310S","A 213 TP310S| 8 | 2 | S31008 | US Steels, ASME BPVC.IX"))
           tab.append(("A 240 Type 310S","A 240 Type 310S| 8 | 2 | S31008 | US Steels, ASME BPVC.IX"))
           tab.append(("A 249 TP310S","A 249 TP310S| 8 | 2 | S31008 | US Steels, ASME BPVC.IX"))
           tab.append(("A 312 TP310S","A 312 TP310S| 8 | 2 | S31008 | US Steels, ASME BPVC.IX"))
           tab.append(("A 358 310S","A 358 310S| 8 | 2 | S31008 | US Steels, ASME BPVC.IX"))
           tab.append(("A 403 WP310S","A 403 WP310S| 8 | 2 | S31008 | US Steels, ASME BPVC.IX"))
           tab.append(("A 409 TP310S","A 409 TP310S| 8 | 2 | S31008 | US Steels, ASME BPVC.IX"))
           tab.append(("A 813 TP310S","A 813 TP310S| 8 | 2 | S31008 | US Steels, ASME BPVC.IX"))
           tab.append(("A 814 TP310S","A 814 TP310S| 8 | 2 | S31008 | US Steels, ASME BPVC.IX"))
           return tab

        if(val == "X8CrNiNb16-13"):
           tab.append(("A 312 TP347H","A 312 TP347H| 8 | 1 | S34709 | US Steels, ASME BPVC.IX"))
           return tab

        if(val == "X8CrNiTi18-10"):
           tab.append(("A 182 F321H","A 182 F312H| 8 | 1 | S32109 | US Steels, ASME BPVC.IX"))
           tab.append(("A 213 TP321H","A 213 TP321H| 8 | 1 | S82109 | US Steels, ASME BPVC.IX"))
           tab.append(("A 240 Type 321","A 240 Type 321| 8 | 1 | S31200 | Austenitic steel-Plates"))
           tab.append(("A 240 Type 321H","A 240 Type 321H| 8 | 1 | S31209 | US Steels, ASME BPVC.IX"))
           tab.append(("A 249 TP321H","A 249 TP321H| 8 | 1 | S32109 | US Steels, ASME BPVC.IX"))
           tab.append(("A 312 TP321H","A 312 TP321H| 8 | 1 | S32109 | US Steels, ASME BPVC.IX"))
           tab.append(("A 376 TP321H","A 376 TP321H| 8 | 1 | S32109 | US Steels, ASME BPVC.IX"))
           tab.append(("A 403 WP321H","A 403 WP321H| 8 | 1 | S32109 | US Steels, ASME BPVC.IX"))
           tab.append(("A 479 321H","A 479 321H| 8 | 1 | S32109 | US Steels, ASME BPVC.IX"))
           tab.append(("A 813 TP321H","A 813 TP321H| 8 | 1 | S32109 | US Steels, ASME BPVC.IX"))
           tab.append(("A 814 TP321H","A 814 TP321H| 8 | 1 | S32109 | US Steels, ASME BPVC.IX"))
           tab.append(("A 965 F321H","A 965 F321H| 8 | 1 | S32109 | US Steels, ASME BPVC.IX"))
           return tab

        if(val == "X8Ni9"):
           tab.append(("A 333 8","A 333 8| 11A | 1 | K81340 | US Steels, ASME BPVC.IX"))
           tab.append(("A 334 8","A 334 8| 11A | 1 | K81340 | US Steels, ASME BPVC.IX"))
           tab.append(("A 353","A 353|    |   |   | Hüttenindustrie EN 10028-4"))
           tab.append(("A 353","A 353|  |   |    | Produktbereich Grobblech"))
           tab.append(("A 353...","A 353...| 11A | 1 | K81340 | US Steels, ASME BPVC.IX"))
           tab.append(("A 420 WPL8","A 420 WPL8| 11A | 1 | K81340 | US Steels, ASME BPVC.IX"))
           tab.append(("A 522 Type I","A 522 Type I| 11A | 1 | K81340 | US Steels, ASME BPVC.IX"))
           tab.append(("A 553 I","A 553 | 11A | 1 | K81340 | US Steels, ASME BPVC.IX"))
           tab.append(("A 553 Type 1","A 553 Type 1|    |   |   | Hüttenindustrie EN 10028-4"))
           tab.append(("EN 10028-4 X8Ni9","EN 10028-4 X8Ni9| 11A | 1 | ...  | US Steels, ASME BPVC.IX"))
           return tab


        if(val == "P355N"):
           tab.append(("A 106 C","A 106 C  | 1 | 2 | K03501 | US Steels, ASME BPVC.IX"))
           tab.append(("A 299 A","A 299 A  | 1 | 2 | K02803 | US Steels, ASME BPVC.IX"))
           tab.append(("A 455","A 455      |   |   |        | Produktbereich Grobblech"))
           tab.append(("A 516 70","A 516 70| 1 | 2 | K02700 | US Steels, ASME BPVC.IX"))
           tab.append(("A 516 Gr. 65(450)","A 516 Gr. 65(450)|   |   |        | Produktbereich Grobblech"))
           tab.append(("A 516 Gr. 70","A 516 Gr. 70|   |   |        | Hüttenindustrie EN 10028-2"))
           tab.append(("A 516 Gr. 70(485)","A 516 Gr. 70(485)|   |   |        | Produktbereich Grobblech"))
           tab.append(("A 537 CI. 1","A 537 CI. 1| 1 | 2 | K12437 | Produktbereich Grobblech"))
           tab.append(("A 541 3, CI. 1","A 541 3, CI. 1| 3 | 3 | K12045 | US Steels, ASME BPVC.IX"))
           tab.append(("A 572 50","A 572 50| 1 | 1 | ... | US Steels, ASME BPVC.IX"))
           tab.append(("A 573 70","A 573 70| 1 | 2 | ... | US Steels, ASME BPVC.IX"))
           tab.append(("A 588 B","A 588 B| 3 | 1 | K12043 | US Steels, ASME BPVC.IX"))
           tab.append(("A 612","A 612|   |   |        | Produktbereich Grobblech"))
           tab.append(("A 618II","A 618II | 1 | 2 | K12609 | US Steels, ASME BPVC.IX"))
           tab.append(("A 633 D","A 633 D | 1 | 2 | K12037 | US Steels, ASME BPVC.IX"))
           tab.append(("A 662 B","A 662 B | 1 | 2 | K02007 | US Steels, ASME BPVC.IX"))
           tab.append(("A 662 Gr. C","A 662 Gr. C|   |   |        | Produktbereich Grobblech"))
           tab.append(("A 737 Gr. B","A 737 Gr. B|   |   |        | Hüttenindustrie EN 10028-3"))
           tab.append(("A 737 Gr. B","A 737 Gr. B|   |   |        | Produktbereich Grobblech"))
           tab.append(("A 738 Gr. A","A 738 Gr. A|   |   |        | Hüttenindustrie EN 10028-3"))
           tab.append(("A 738 Gr. A","A 738 Gr. A|   |   |        | Produktbereich Grobblech"))
           tab.append(("A 738 Gr. C","A 738 Gr. C|   |   |        | Hüttenindustrie EN 10028-3"))
           tab.append(("A 841 A, CI. 1","A 841 A, CI. 1| 1 | 2 | ...     | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "E295"):
           tab.append(("A 573 70","A 573 70 | 1 | 2 | ...   | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "20MnMoNi4-5"):
           tab.append(("A 533 Type B CI. 1","A 533 Type B CI. 1 |   |   |     | Produktbereich Grobblech"))
           tab.append(("A 533 Type B CI. 2","A 533 Type B CI. 2 |   |   |     | Produktbereich Grobblech"))
           tab.append(("A 533 Type B CI. 3","A 533 Type B CI. 3 |   |   |     | Produktbereich Grobblech"))
           tab.append(("A 533 Type B, CI. 1","A 533 Type B, CI. 1 | 3 | 3 |  K12539 | US Steels, ASME BPVC.IX"))
           tab.append(("A 533 Type C CI. 1","A 533 Type C CI. 1 |   |   |       | Produktbereich Grobblech"))
           tab.append(("A 533 Type C CI. 2","A 533 Type C CI. 2 |   |   |       | Produktbereich Grobblech"))
           tab.append(("A 533 Type C CI. 3","A 533 Type C CI. 3 |   |   |       | Produktbereich Grobblech"))
           tab.append(("A 533 Type D CI. 1","A 533 Type D CI. 1 |   |   |       | Produktbereich Grobblech"))
           tab.append(("A 533 Type D CI. 2","A 533 Type D CI. 2 |   |   |       | Produktbereich Grobblech"))
           tab.append(("A 533 Type D CI. 3","A 533 Type D CI. 3 |   |   |       | Produktbereich Grobblech"))
           return tab
        if(val == "15NiCuMoNb5-6-4"):
           tab.append(("A 302 D","A 302 D | 3 | 3 | K12054 | US Steels, ASME BPVC.IX"))
           tab.append(("A 508 3,CI. 1","A 508 3,CI. 1 | 3 | 3 | K12042 | US Steels, ASME BPVC.IX"))
           tab.append(("A 533 Type C, CI. 1","A 533 Type C, CI. 1 | 3 | 3 | K12554 | US Steels, ASME BPVC.IX"))
           return tab
        if(val == "13CrMoV9-10"):
           tab.append(("A 542 Type D CI. 1","A 542 Type D CI. 1 |   |   |     | Produktbereich Grobblech"))
           tab.append(("A 542 Type D CI. 2","A 542 Type D CI. 2 |   |   |     | Produktbereich Grobblech"))
           tab.append(("A 542 Type D CI. 3","A 542 Type D CI. 3 |   |   |     | Produktbereich Grobblech"))
           tab.append(("A 542 Type D CI. 4, 4a","A 542 Type D CI. 4, 4a |   |   |     | Produktbereich Grobblech"))
           return tab
        if(val == "11CrMo9-10"):
           tab.append(("A 182 F22, CI. 1","A 182 F22, CI. 1 | 5A | 1 | K21590 | US Steels, ASME BPVC.IX"))
           tab.append(("A 250 T22","A 250 T22 | 5A | 1 | K21590 | US Steels, ASME BPVC.IX"))
           tab.append(("A 336 F22, CI. 1"," A 336 F22, CI. 1 | 5A | 1 | K21590 | US Steels, ASME BPVC.IX"))
           tab.append(("A 336 F22, CI. 3","A 336 F22, CI. 3 | 5A | 1 | K21590 | US Steels, ASME BPVC.IX"))
           tab.append(("A 369 FP22","A 369 FP22 | 5A | 1 | K21590 | US Steels, ASME BPVC.IX"))
           tab.append(("A 387 22, CI. 1","A 387 22, CI. 1 | 5A | 1 | K21590 | US Steels, ASME BPVC.IX"))
           tab.append(("A 387 Gr.22","A 387 Gr.22 |   |   |   | Hüttenindustrie EN 10028-2"))
           tab.append(("EN 10222-2 11CrMo9-10","EN 10222-2 11CrMo9-10 | 5A | 1 |   | US Steels, ASME BPVC.IX"))
           return tab

        else:
          if(val == "E335"):
            tab.append(("A 573 65","A 573 65(US Steels, ASME BPVC.IX)"))
            return tab
      else:
         tab.append((" "," "))
         return tab



#Drucken WPQR6  Zerrifikat
# class view
class PrintISOWPQR6Start(ModelView):
    'Print START WPQR6'
    __name__ = 'party.print_isowpqr6.start'
    zertifikat = fields.Many2One('party.wpqr6', 'Zertifikat', required=True)

#Wizard
class PrintWPQR6(Wizard):
    'Print ISOWPQR6'
    __name__ = 'party.print_isowpqr6'
    start = StateView('party.print_isowpqr6.start',
        'welding_certification.print_isowpqr6_cert_start_view_form', [
            Button('Cancel', 'end', 'tryton-cancel'),
            Button('Drucken', 'print_', 'tryton-print', default=True),
            ])
    print_ = StateReport('welding_certification.party.iso_wpqr6_report')
    def do_print_(self, action):
        data = {
            'zertifikat': self.start.zertifikat.id,
            }
        return action, data
#Report
class ISOWPQR6report(Report):
    __name__ = 'welding_certification.party.iso_wpqr6_report'


    @classmethod
    def _get_records(cls, ids, model, data):
        Move = Pool().get('party.wpqr6')

        clause = [

            ]


    @classmethod
    def get_context(cls, records, data):
        report_context = super(ISOWPQR6report, cls).get_context(records, data)

        Zertifikat = Pool().get('party.wpqr6')

        zertifikat = Zertifikat(data['zertifikat'])

        report_context['zertifikat'] = zertifikat
        report_context['organisation'] = zertifikat.organisation
        report_context['organisation_anschrift'] = zertifikat.organisation_anschrift
        report_context['procedure_qualification'] = zertifikat.procedure_qualification
        report_context['Date'] = zertifikat.Date
        report_context['wps'] = zertifikat.wps_nr
        report_context['welding_prozess'] = zertifikat.welding_prozess
        report_context['type'] = zertifikat.type
        report_context['matrial2'] = zertifikat.matrial22.Bezeichnung
        report_context['type_grade'] = zertifikat.type_grade1
        report_context['p_no'] = zertifikat.p_no
        report_context['grou2'] = zertifikat.grou2
        report_context['p_no1'] = zertifikat.p_no1
        report_context['group_no1'] = zertifikat.group_no1
        report_context['thickness'] = zertifikat.thickness
        report_context['diameter'] = zertifikat.diameter
        report_context['max_thickness'] = zertifikat.max_thickness
        report_context['ohter1'] = zertifikat.other
        report_context['ohter5'] = zertifikat.other1
        report_context['ohter6'] = zertifikat.other2
        report_context['ohter7'] = zertifikat.other3
        report_context['ohter8'] = zertifikat.other4
        report_context['temperatur'] = zertifikat.temperatur
        report_context['time'] = zertifikat.time
        report_context['other2'] = zertifikat.other_postweld
        report_context['other3'] = zertifikat.other_postweld1
        report_context['other4'] = zertifikat.other_postweld2
        report_context['schielding'] = zertifikat.schielding
        report_context['schielding_'] = zertifikat.schielding_
        report_context['flow_rate1'] = zertifikat.flow_rate1
        report_context['trailing'] = zertifikat.trailing
        report_context['trailing_'] = zertifikat.trailing_
        report_context['flow_rate2'] = zertifikat.flow_rate2
        report_context['backing'] = zertifikat.backing
        report_context['backing_'] = zertifikat.backing_
        report_context['flow_rate3'] = zertifikat.flow_rate3
        report_context['other_gas'] = zertifikat.other_gas_
        report_context['sfa_specification1'] = zertifikat.sfa_specification1
        report_context['sfa_specification2'] = zertifikat.sfa_specification2
        report_context['aws_classification1'] = zertifikat.aws_classification1
        report_context['aws_classification2'] = zertifikat.aws_classification2
        report_context['filler_metal1'] = zertifikat.filler_metal1
        report_context['filler_metal2'] = zertifikat.filler_metal2
        report_context['weld_metal1'] = zertifikat.weld_metal1
        report_context['weld_metal2'] = zertifikat.weld_metal2
        report_context['size_filler1'] = zertifikat.size_filler1
        report_context['size_filler2'] = zertifikat.size_filler2
        report_context['flux_type1'] = zertifikat.flux_type1
        report_context['flux_type2'] = zertifikat.flux_type2
        report_context['weld_metal_thickness1'] = zertifikat.weld_metal_thickness1
        report_context['weld_metal_thickness2'] = zertifikat.weld_metal_thickness2
        report_context['other_filler1'] = zertifikat.other_filler1
        report_context['other_filler2'] = zertifikat.other_filler2
        report_context['current'] = zertifikat.current
        report_context['polarity'] = zertifikat.polarity
        report_context['amps'] = zertifikat.amps
        report_context['volt'] = zertifikat.volt
        report_context['tungsten'] = zertifikat.tungsten
        report_context['mode'] = zertifikat.mode
        report_context['heat'] = zertifikat.heat
        report_context['other_electrical'] = zertifikat.other_electrical
        report_context['other_electrical1'] = zertifikat.other_electrical1
        report_context['position_of_groove'] = zertifikat.position_of_groove
        report_context['welding_prog'] = zertifikat.welding_prog
        report_context['other_position'] = zertifikat.other_position
        report_context['other_position1'] = zertifikat.other_position1
        report_context['preheat_temp'] = zertifikat.preheat_temp
        report_context['interpass_temp'] = zertifikat.interpass_temp
        report_context['other_preheat'] = zertifikat.other_preheat
        report_context['other_preheat1'] = zertifikat.other_preheat1
        report_context['travel_speed'] = zertifikat.travel_speed
        report_context['waeve_bead'] = zertifikat.waeve_bead
        report_context['oscillation'] = zertifikat.oscillation
        report_context['multipass'] = zertifikat.multipass
        report_context['multi_elektrode'] = zertifikat.multi_elektrode
        report_context['other_technique'] = zertifikat.other_technique
        report_context['other_technique1'] = zertifikat.other_technique1


        return report_context


#END


# WPQR (13134) class
class wpqr5(DeactivableMixin, ModelView, ModelSQL, MultiValueMixin):
    'Party WPQR 13134'
    __name__ = 'party.wpqr5'
    hersteller = fields.Char('Name und Anschrift des Herstellers')
    hersteller1 = fields.Char('Name und Anschrift des Herstellers')
    prufer_prufstelle = fields.Selection([
        ('DGZfP', 'DGZfP-Ausbildungszentrum Wittenberge'),
        ('Harrison', 'Harrison Mechanical Corporation'),
        ('MAN-Technologie', 'MAN-Technologie, Oberpfaffenhofen, Abtlg.WOP'),
    ], 'Name und Anschrift des Prüfers oder Prüfstelle', readonly = False,
        )
    prufer1 = fields.Char('Name und Anschrift des Prüfers oder Prüfstelle')
    space = fields.Char('                                                                                                                                                                               ')
    beleg1_title = fields.Char('Hartlötverfahren des Herstellers')
    beleg1 = fields.Function(fields.Char('Beleg-Nr'),"On_change_methods")
    beleg2_title = fields.Char('Prüfer oder Prüfstelle')
    beleg2 = fields.Char('Beleg-Nr')
    Part2_title = fields.Char('Methoden der Anerkennung')
    method11 = fields.Selection([
        ('-', '-'),
        ('x', 'x'),
    ], 'a) mittels Vorlage dokumentierter Nachweise, dass ein entsprechendes Verfahren durch Erfahrung', readonly = False,
        )
    method1_ = fields.Char('erprobt und für eine Anerkennung durch einen Prüfer oder eine Prüfstelle verfügbar ist.')

    method21 = fields.Selection([
        ('-', '-'),
        ('x', 'x'),
    ], 'b) mittels Vorlage eines entsprechendes Verfahrens, das bereist von einem anderen Prüfer oder einer anderen Prüfstelle anerkannt ist.', readonly = False,
        )
    method31 = fields.Selection([
        ('-', '-'),
        ('x', 'x'),
    ], 'c) mittels Durchführung einer geeigneten Hartlötverfahrensprüfung durch einen Prüfer oder durch eine Prüfstelle.', readonly = False,
        )
   # method3 = fields.Selection('on_change_method1','c) mittels Durchführung einer geeigneten Hartlötverfahrensprüfung durch einen Prüfer oder durch eine Prüfstelle.', readonly = False,)

    streichen = fields.Char('(streichen, wenn nicht zutreffend)')
    bei_a_oder_b = fields.Char('Bei a) oder b) ist die Beleg-Nr. der vorgelegten Dokumente anzugeben')
    geltungsbereich = fields.Char('Geltungsbereich, falls vorhanden')
    geltungsbereich2 = fields.Char(' ')
    geltungsbereich3 = fields.Char(' ')

    beleg_dok = fields.Char('Beleg-Nr. der Dokumente, die zur Begründung der Erweiterung des Geltungsbereiches vorlagen')
    beleg_dok2 = fields.Char(' ')

    hermit = fields.Text('Hermit wird bestätigt, dass das Hartlötverfahren mit den Anforderungen der folgenden Normen oder vergleichbarer Dokumente übereinstimmt.')

    name_vertreters = fields.Char('Name des Vertreters des Herstellers')
    name_vertreters1 = fields.Char('Name des Prüfers oder des Vertreters der Prüfstelle')

    datum1 =fields.Date("Datum, Name und Unterschrift")
    datum_ausstellung =fields.Date("Datum, Name und Unterschrift")
    unterschrift2 = fields.Char(' ')

    unterschrift = fields.Selection([
        ('Dipl.Ing. Prüfet', 'Dipl.Ing. Prüfet'),
        ('Dipl.Ing. Schulz', 'Dipl.Ing. Schulz'),
        ('Dipl.Ing. Tester', 'Dipl.Ing. Tester'),
        ('Dipl.Ing. Zertifizierer', 'Dipl.Ing. Zertifizierer'),
        ('P.L. Van Fosson', 'P.L. Van Fosson'),
    ], 'Name, Datum und Unterschrift', readonly = False,
        )


    def On_change_methods(self,method11):
      if(self.method11 == "x" and self.method21 =="-" and self.method31 == "-"):
         return "EN 13134 A 0083"
      else:
         if(self.method11 == "-" and self.method21 =="x" and self.method31 == "-"):
            return "EN 13134 B 0083"
         else:
            return "EN 13134 C 0083"

    @staticmethod
    def default_method11():
        return  "x"
    @staticmethod
    def default_method21():
        return  "-"
    @staticmethod
    def default_method31():
        return  "-"
#Drucken Formular für wpqr5
# class view
class PrintISOWPQR5Start(ModelView):
    'Print START WPQR5'
    __name__ = 'party.print_isowpqr5.start'
    zertifikat = fields.Many2One('party.wpqr5', 'Zertifikat', required=True)

#Wizard
class PrintWPQR5(Wizard):
    'Print ISOWPQR5'
    __name__ = 'party.print_isowpqr5'
    start = StateView('party.print_isowpqr5.start',
        'welding_certification.print_isowpqr5_cert_start_view_form', [
            Button('Cancel', 'end', 'tryton-cancel'),
            Button('Drucken', 'print_', 'tryton-print', default=True),
            ])
    print_ = StateReport('welding_certification.party.iso_wpqr5_report')
    def do_print_(self, action):
        data = {
            'zertifikat': self.start.zertifikat.id,
            }
        return action, data

#Report
class ISOWPQR5report(Report):
    __name__ = 'welding_certification.party.iso_wpqr5_report'


    @classmethod
    def _get_records(cls, ids, model, data):
        Move = Pool().get('party.wpqr5')

        clause = [

            ]


    @classmethod
    def get_context(cls, records, data):
        report_context = super(ISOWPQR5report, cls).get_context(records, data)

        Zertifikat = Pool().get('party.wpqr5')

        zertifikat = Zertifikat(data['zertifikat'])

        report_context['zertifikat'] = zertifikat
        report_context['hersteller'] = zertifikat.hersteller
        report_context['anschrift'] = zertifikat.hersteller1
        report_context['prufer1'] = zertifikat.prufer1
        report_context['prufer_prufstelle'] = zertifikat.prufer_prufstelle
        report_context['beleg1'] = zertifikat.beleg1
        report_context['beleg2'] = zertifikat.beleg2
        report_context['method11'] = zertifikat.method11
        report_context['method21'] = zertifikat.method21
        report_context['method31'] = zertifikat.method31
        report_context['bei_a_oder_b'] = zertifikat.bei_a_oder_b
        report_context['geltungsbereich'] = zertifikat.geltungsbereich
        report_context['geltungsbereich2'] = zertifikat.geltungsbereich2
        report_context['geltungsbereich3'] = zertifikat.geltungsbereich3
        report_context['beleg_dok'] = zertifikat.beleg_dok
        report_context['beleg_dok2'] = zertifikat.beleg_dok2
        report_context['hermit'] = zertifikat.hermit
        report_context['datum_ausstellung'] = zertifikat.datum_ausstellung
        report_context['datum1'] = zertifikat.datum1
        report_context['unterschrift2'] = zertifikat.unterschrift2
        report_context['unterschrift'] = zertifikat.unterschrift

        return report_context



#END
class kondersatorentladungs(DeactivableMixin, ModelView, ModelSQL, MultiValueMixin):
    'Party WPQR kondersatorentladungs'
    __name__ = 'party.kondersatorentladungs'
    luftspalt = fields.Char('Luftspalt mm')
    ladespannung = fields.Char('Ladespannung V')
    kapazitat = fields.Char('Kapazität mF')
    feder = fields.Char('Federkraft N oder Eintauchgeschwindigkeit mm/s')
    bemerkungen = fields.Char('Bemerkungen')
    Link_kondersatorentladungs = fields.Many2One('party.wpqr4', 'kondersatorentladungs', required=True,
        ondelete='CASCADE', states=STATES, select=True, depends=DEPENDS)



# WPQR (14555-E) class
class wpqr4(DeactivableMixin, ModelView, ModelSQL, MultiValueMixin):
    'Party WPQR 14555E'
    __name__ = 'party.wpqr4'
    hersteller = fields.Char('Hersteller')
    beleg_nr = fields.Char('Beleg-Nr')
    wpqr = fields.Function(fields.Char('WPQR-Nr. des Herstellers'),"On_change_andere")
    kondersatorentladungs = fields.One2Many('party.kondersatorentladungs','Link_kondersatorentladungs','Kondensatorentladungs-Bolzenschweißen mit Spitzenzündung - 786 und Kondensatorentladungs-Bolzenschweißen mit Hubzündung - 785')
#    prufer_prufstelle = fields.Selection([
#        ('DGZfP', 'DGZfP-Ausbildungszentrum Wittenberge'),
 #       ('Harrison', 'Harrison Mechanical Corporation'),
 #       ('MAN-Technologie', 'MAN-Technologie, Oberpfaffenhofen, Abtlg.WOP'),
 #   ], 'Prüfer oder Prüstelle', readonly = False,
#        )
    prufer_prufstelle1 = fields.Many2One('welding.pruefstelle', 'Name des prüfers oder der prüfstelle',
            ondelete='CASCADE')

    anschrift = fields.Char('Anschrift')
    regel = fields.Char('Regel/Prüfnorm')
    space = fields.Char("                                                                                                                                                                 ")
    wps = fields.Char('Beleg-Nr. der Hersteller-WPS')
    ausstelleung = fields.Date("Datum der Ausstellung")
    schweissen = fields.Date("Datum der Schweißung")
    bediener = fields.Char('Name des Bedieners')
    prufumfang1 = fields.Function(fields.Char('Prüfumfang'),"On_change_prufumfang2")

    prufumfang2 = fields.Selection([
        ('Sicht-', 'Sicht-'),
        ('Durchstrahlungs-', 'Durchstrahlungs-'),
        ('Ultraschall-', 'Ultraschall-'),
        ('Oberflächenriss-', 'Oberflächenriss-'),
        ('Querzug-', 'Querzug-'),
        ('Querbiege-', 'Querbiege-'),
        ('Kerbschlagbiege-', 'Kerbschlagbiege-'),
        ('Harte-', 'Härte-'),
        ('Makroschliff-', 'Makroschliff-'),
        ('Löschen', 'Löschen'),
    ], ' ', readonly = False,
        )
    title = fields.Char('Einzelheiten des Schweißverfahrens')
    prozess = fields.Selection([
        ('78', '78|Bolzenschweißen'),
        ('783', '783|Hubzündungs-Bolzenschweißen mit keramikring oder schutzgas'),
        ('784', '784|kurzzeit-Bolzenschweißen mit Hubzündung'),
        ('785', '785|kondensatorentladungs-Bolzenschweißen mit Hubzündung'),
        ('786', '786|kondensatorentladungs-Bolzenschweißen mit Spitzenzündung'),
        ('787', '787 Bolzenschweißen mit Ringzündung'),
    ], 'Bolzenschweißprozess:ISO 4063-', readonly = False,
        )
    prozess_gel = fields.Function(fields.Char('Prozess Geltungsbereich'),"On_change_prozess")
    bolzenwerkstoff = fields.Char('Bolzenwerkstoff')
    bolzendurchmesser = fields.Integer("Bolzendurchmesser(mm)")
    grundwerkstoff = fields.Many2One("welding.grundwerkstoff_properties","Grundwerkstoff")
    bolzenlange = fields.Integer("Bolzenlänge(mm)")

    grup = fields.Function(fields.Char("Werkstoffgruppe"),"On_change_grundwerkstoffe")
    nummer = fields.Function(fields.Char("WSt-Nummer"),"On_change_grundwerkstoffe2")

    dicke = fields.Integer("Dicke des Grundwerkstoffes(mm)")
    bolzenbezeichnung = fields.Char('Bolzenbezeichnung')

    schweiss1 = fields.Boolean("mit Spalt")
    schweiss1_affichage = fields.Function(fields.Char("Value1"),"On_change_schweiss1")
    schweiss2 = fields.Boolean("mit Kontakt")
    schweiss2_affichage = fields.Function(fields.Char("Value2"),"On_change_schweiss2")
    schweiss = fields.Char('Schweißen')
    schutzgas = fields.Many2One('party.schutzgas', 'Schutzgas')
    stromquel = fields.Char('Stromquelle')
    durch = fields.Char('Durchflussmenge (I/min)')
    schweißpistole = fields.Char('Schweißpistole/-kopf')
    andere = fields.Text("Andere Angaben (Siehe auch 10.5)")

    index1 = fields.Char('Hiermit wird bestätigt, dass die Prüfschweißungen in Übereinstimmung mit den vorbezeichneten')
    index2 = fields.Char('Anforderungen oder der Prüfnorm zufrieden stellend vorbereitet, geschweißt und geprüft wurden')
    ort = fields.Char('Ort')
    unterschrift = fields.Selection([
        ('Dipl.Ing. Prüfet', 'Dipl.Ing. Prüfet'),
        ('Dipl.Ing. Schulz', 'Dipl.Ing. Schulz'),
        ('Dipl.Ing. Tester', 'Dipl.Ing. Tester'),
        ('Dipl.Ing. Zertifizierer', 'Dipl.Ing. Zertifizierer'),
        ('P.L. Van Fosson', 'P.L. Van Fosson'),
    ], 'Name, Datum und Unterschrift', readonly = False,
        )
    title1 = fields.Char('Qualifizierung eines Schweißverfahrens-Prüfungsbescheinigung')

    def On_change_schweiss1(self,schweiss1):
      if(self.schweiss1 == True):
         return "|X|"
      else:
         return "| |"

    def On_change_schweiss2(self,schweiss2):
      if(self.schweiss2 == True):
         return "|X|"
      else:
         return "| |"

    def On_change_andere(self,prozess):
      if(self.grundwerkstoff is not None and self.dicke is not None):
        return "ISO 14555 "+str(self.prozess)+" "+str(self.grundwerkstoff.Werkstoffgruppe)+" t0"+str(self.dicke)
      else:
        return "ISO 14555"

    def On_change_grundwerkstoffe(self,grundwerkstoff):
      if(self.grundwerkstoff is not None):
         return "Gruppe "+self.grundwerkstoff.Werkstoffgruppe
      else:
         return " "

    def On_change_grundwerkstoffe2(self,grundwerkstoff):
      if(self.grundwerkstoff is not None):
        return self.grundwerkstoff.Nummer
      else:
        return " "

    def On_change_prufumfang2(self,prufumfang2):

         if(len(tab_prufumfang3) == 0 and self.prufumfang2 != "Löschen"):
            tab_prufumfang3.append(self.prufumfang2)
            return  tab_prufumfang3
         if(len(tab_prufumfang3) > 0 and tab_prufumfang3[len(tab_prufumfang3) - 1] == self.prufumfang2):
            return  tab_prufumfang3
         if(len(tab_prufumfang3) > 0 and self.prufumfang2 == "Löschen"):
            del tab_prufumfang3[len(tab_prufumfang3) - 1]
            return  tab_prufumfang3
         else:
           if(len(tab_prufumfang3) > 0 and tab_prufumfang3[len(tab_prufumfang3) - 1] != self.prufumfang2 and self.prufumfang2 != "Löschen"):
            tab_prufumfang3.append(self.prufumfang2)
            return  tab_prufumfang3


    def On_change_prozess(self,prozess):
      if(self.prozess == "78"):
        return "Bolzenschweißen"
      if(self.prozess == "784"):
        return "Kurzzeit-Bolzenschweißen mit Hubzündung"
      if(self.prozess == "785"):
        return "Kondensatorentladungs-Bolzenschweißen mit Hubzündung"
      if(self.prozess == "786"):
        return "Kondensatorentladungs-Bolzenschweißen mit Spitzenzündung"
      if(self.prozess == "787"):
        return "Bolzenschweißen mit Ringzündung"
      else:
         if(self.prozess == "783"):
           return"Hubzündungs-Bolzenschweißen mit Keramiking oder Schutzgas"

    @staticmethod
    def default_regel():
      return "DIN EN ISO 14555(Qualifizierung des Schweißverfahrens -Lichtbogenbolzenschweißen )"


#Drucken Classes for EN ISO 14555-E
# class view
class PrintISOWPQR4Start(ModelView):
    'Print START WPQR4'
    __name__ = 'party.print_isowpqr4.start'
    zertifikat = fields.Many2One('party.wpqr4', 'Zertifikat', required=True)

#Wizard
class PrintWPQR4(Wizard):
    'Print ISOWPQR4'
    __name__ = 'party.print_isowpqr4'
    start = StateView('party.print_isowpqr4.start',
        'welding_certification.print_isowpqr4_cert_start_view_form', [
            Button('Cancel', 'end', 'tryton-cancel'),
            Button('Drucken', 'print_', 'tryton-print', default=True),
            ])
    print_ = StateReport('welding_certification.party.iso_wpqr4_report')
    def do_print_(self, action):
        data = {
            'zertifikat': self.start.zertifikat.id,
            }
        return action, data

#Report
class ISOWPQR4report(Report):
    __name__ = 'welding_certification.party.iso_wpqr4_report'


    @classmethod
    def _get_records(cls, ids, model, data):
        Move = Pool().get('party.wpqr4')

        clause = [

            ]


    @classmethod
    def get_context(cls, records, data):
        report_context = super(ISOWPQR4report, cls).get_context(records, data)

        Zertifikat = Pool().get('party.wpqr4')

        zertifikat = Zertifikat(data['zertifikat'])

        report_context['zertifikat'] = zertifikat
        report_context['wpqr'] = zertifikat.wpqr
        report_context['hersteller'] = zertifikat.hersteller
        report_context['anschrift'] = zertifikat.anschrift
        report_context['prufer'] = zertifikat.prufer_prufstelle1.prufstelle
        report_context['beleg'] = zertifikat.beleg_nr
        report_context['anschrift'] = zertifikat.anschrift
        report_context['regel'] = zertifikat.regel
        report_context['datum_schweissen'] = zertifikat.schweissen
        report_context['wps'] = zertifikat.wps
        report_context['bediener'] = zertifikat.bediener
        report_context['prufumfang'] = zertifikat.prufumfang1
        report_context['schweissprozess'] = zertifikat.prozess
        report_context['schweissprozess_gel'] = zertifikat.prozess_gel
        report_context['bolzenwerkstoff'] = zertifikat.bolzenwerkstoff
        report_context['bolzendurchmesser'] = zertifikat.bolzendurchmesser
        report_context['grundwerkstoff'] = zertifikat.grundwerkstoff.Bezeichnung
        report_context['bolzenlang'] = zertifikat.bolzenlange
        report_context['gruppe'] = zertifikat.grup
        report_context['nummer'] = zertifikat.nummer
        report_context['dicke'] = zertifikat.dicke
        report_context['belzenbezeichnung'] = zertifikat.bolzenbezeichnung
        report_context['shutzgas'] = zertifikat.schutzgas.bezeichnung
        report_context['stromquel'] = zertifikat.stromquel
        report_context['durch'] = zertifikat.durch
        report_context['schweißpistole'] = zertifikat.schweißpistole
        report_context['schweiss1_affichage'] = zertifikat.schweiss1_affichage
        report_context['schweiss2_affichage'] = zertifikat.schweiss2_affichage
        report_context['andere'] = zertifikat.andere
        report_context['luftspalt'] = zertifikat.kondersatorentladungs[0].luftspalt
        report_context['ladespannung'] = zertifikat.kondersatorentladungs[0].ladespannung
        report_context['kapazitat'] = zertifikat.kondersatorentladungs[0].kapazitat
        report_context['feder'] = zertifikat.kondersatorentladungs[0].feder
        report_context['bemerkungen'] = zertifikat.kondersatorentladungs[0].bemerkungen
        report_context['ort'] = zertifikat.ort
        report_context['ausstelleung'] = zertifikat.ausstelleung
        report_context['unterschrift'] = zertifikat.unterschrift





        return report_context



class hubzundungs(DeactivableMixin, ModelView, ModelSQL, MultiValueMixin):
    'Party WPQR Hubzundung'
    __name__ = 'party.hubzundungs'
    schweisstrom = fields.Char('Schweißstrom A')
    schweiszeit_ms = fields.Char('Schweißzeit ms (oder s)')
    uberstand = fields.Char('Überstand mm')
    hub = fields.Char('Hub mm')
    bemerkung = fields.Char('Bemerkungen')

    link_hubzundungs = fields.Many2One('party.wpqr2', 'hubzundung1', required=True,
        ondelete='CASCADE', states=STATES, select=True, depends=DEPENDS)


# WPQR (EN ISO 14555D) Class
class wpqr2(DeactivableMixin, ModelView, ModelSQL, MultiValueMixin):
    'Party WPQR 14555D'
    __name__ = 'party.wpqr2'
    hersteller = fields.Char('Hersteller')
    beleg_nr = fields.Char('Beleg-Nr')
    prufer_prufstelle1 = fields.Many2One('welding.pruefstelle', 'Name des prüfers oder der prüfstelle',
            ondelete='CASCADE')

    wpqr = fields.Char('WPQR-Nr. des Herstellers')
    wpqr_ = fields.Function(fields.Char('WPQR-Nr. des Herstellers'),"on_change_andere")

    ausstelleung = fields.Date("Tag der Ausstellung")
    ort = fields.Function(fields.Char("Ort"),"On_change_prufers")
    anschrift = fields.Char('Anschrift')
    index = fields.Char('Hiermit wird bestätigt, dass die Prüfschweißungen in Übereinstimmung mit den vorbezeichneten Anforderungen oder der Prüfnorm zufrieden stellend vorbereitet, geschweißt und geprüft wurden.')

    andere_angaben = fields.Text('Andere Angaben(Siehe auch 10.5)')

    hubzundung = fields.One2Many('party.hubzundungs','link_hubzundungs','Hubzündungs-Bolzenschweißen mit keramikring oder Schutzgas-783 und kurzzeit-Bolzenschweißen mit Hubzündung-784')

    keramikringes = fields.Char('Bezeichnung des Keramikringes')
    handelsname = fields.Char('Handelsname')
    invendung1 = fields.Boolean("Anwendung <= 100°C")
    invendung1_signe = fields.Function(fields.Char("Anwendung <= 100°C"),"On_Change_invendung1")

    invendung2 = fields.Boolean("Anwendung > 100°C")
    invendung2_signe = fields.Function(fields.Char("Anwendung <= 100°C"),"On_Change_invendung2")

    dampfung1 = fields.Boolean("Ja")
    dampfung1_signe = fields.Function(fields.Char("Ja"),"On_Change_dampfung1")

    dampfung2 = fields.Boolean("Nein")
    dampfung2_signe = fields.Function(fields.Char("Nein"),"On_Change_dampfung2")

    dampfung_title = fields.Char('Dämpfung')

    temperatur = fields.Char('Vorwärmtemperatur(°C)')
    stromquel = fields.Char('Stromquelle')

    schutzgas = fields.Many2One('party.schutzgas', 'Schutzgas')
    schweisspistole = fields.Char('Schweißpistole/-kopf')

    durchflussmenge = fields.Char('Durchflussmenge(I/min)')

    dicke_des_werkstoff = fields.Char('Dicke des Grundwerkstoffes(mm)')
    bolzenbezeichnung = fields.Char('Bolzenbezeichnung')
    bolzenwerkstoff = fields.Char('Bolzenwerkstoff')
    bolzendurchmesser = fields.Char('Bolzendurchmesser(mm)')
    bolzenlange = fields.Char('Bolzenlänge(mm)')
    grundwerkstoff = fields.Many2One("welding.grundwerkstoff_properties","Grundwerkstoff")
    regel = fields.Char('Regel/Prüfnorm')
    wps = fields.Char('Beleg-Nr. der Hersteller-WPS')
    datum_schweissen = fields.Date("Datum der Schweißung")
    name_bediener = fields.Char("Name des Bedieners")
    prufumfang1 = fields.Selection([
        ('Sicht-', 'Sicht-'),
        ('Surchstrahlungs-', 'Durchstrahlungs-'),
        ('Ultraschall-', 'Ultraschall-'),
        ('Oberflächenriss-', 'Oberflächenriss-'),
        ('Querzug-', 'Querzug-'),
        ('Querbiege-', 'Querbiege-'),
        ('Kerbschlagbiege-', 'Kerbschlagbiege-'),
        ('Harte-', 'Härte-'),
        ('Makroschliff-', 'Makroschliff-'),
        ('Löschen', 'Löschen'),
    ], ' ', readonly = False,
        )
    schweissposition2 = fields.Selection([
        ('PA', 'PA Wannenposition'),
        ('PB', 'PB Horizontalposition'),
        ('PC', 'PC Querposition'),
        ('PD', 'PD Horizontal-Überkopfposition'),
        ('PE', 'PE Überkopfposition'),
        ('PF', 'PF Steigposition'),
        ('PG', 'PG Fallposition'),
        ('PH', 'PH Rohrposition für steigendschweißen'),
        ('PJ', 'PJ Rohrposition für Fallendschweißen'),
        ('H-LO45', 'H-LO45 Steigend am Rohr, Neigungswinkel 45°'),
        ('J-LO45', 'J-LO45 Fallend  am Rohr, Neigungswinkel 45°'),
    ], 'Schweißposition:ISO 6947-', readonly = False,
        )

    space = fields.Char("                                                                                                                                            ")
    prufumfang2 = fields.Function(fields.Char("Prüfumfang"),'On_change_prufumfang1')
    title1 = fields.Char('Einzelheiten des Schweißverfahrens')
    prozess = fields.Selection([
        ('78', '78|Bolzenschweißen'),
        ('783', '783|Hubzündungs-Bolzenschweißen mit keramikring oder schutzgas'),
        ('784', '784|kurzzeit-Bolzenschweißen mit Hubzündung'),
        ('785', '785|kondensatorentladungs-Bolzenschweißen mit Hubzündung'),
        ('786', '786|kondensatorentladungs-Bolzenschweißen mit Spitzenzündung'),
        ('787', '787 Bolzenschweißen mit Ringzündung'),
    ], 'Bolzenschweißprozess:ISO 4063-', readonly = False,
        )
    prozess_gel = fields.Function(fields.Char("GeltungsBereich"),'On_change_prozess')
    werkstoffgrup = fields.Function(fields.Char("Werkstoffgruppe"),'On_change_grundwerkstoff')
    wst_nummer = fields.Function(fields.Char("WSt-Nummer"),'On_change_grundwerkstoff1')

    def On_Change_dampfung1(self,dampfung1):
        if(self.dampfung1 == True):
          return "|X|"
        else:
          return"| |"
    def On_Change_dampfung2(self,dampfung2):
        if(self.dampfung2 == True):
          return "|X|"
        else:
          return "| |"


    def On_Change_invendung1(self,invendung1):
        if(self.invendung1 == True):
           return "|X|"
        else:
           return "| |"
    def On_Change_invendung2(self,invendung2):
        if(self.invendung2 == True):
           return "|X|"
        else:
           return"| |"

    def on_change_andere(self,prozess):
        return"ISO 14555 "+str(self.prozess)+" "+str(self.grundwerkstoff.Werkstoffgruppe)+" t0"+str(self.dicke_des_werkstoff)+" "+str(self.schweissposition2)
    def On_change_grundwerkstoff(self,grundwerkstoff):
        return "Gruppe "+self.grundwerkstoff.Werkstoffgruppe
    def On_change_prufers(self,prufer_prufstelle1):
        return self.prufer_prufstelle1.ort


    def On_change_grundwerkstoff1(self,grundwerkstoff):
        return self.grundwerkstoff.Nummer

    def On_change_prozess(self,prozess):
      if(self.prozess == "78"):
          return "Bolzenschweißen"
      if(self.prozess == "784"):
          return "kurzzeit-Bolzenschweißen mit Hubzündung"
      if(self.prozess == "785"):
          return "kondensatorentladungs-Bolzenschweißen mit Hubzündung"
      if(self.prozess == "786"):
          return "kondensatorentladungs-Bolzenschweißen mit Spitzenzündung"
      if(self.prozess == "787"):
          return "Bolzenschweißen mit Ringzündung"
      else:
        if(self.prozess == "783"):
          return "Hubzündungs-Bolzenschweißen mit keramikring oder schutzgas"

    def On_change_prufumfang1(self,prufumfang1):
         if(len(tab_prufumfang) == 0 and self.prufumfang1 != "Löschen"):
            tab_prufumfang.append(self.prufumfang1)
            return  tab_prufumfang
         if(len(tab_prufumfang) > 0 and tab_prufumfang[len(tab_prufumfang) - 1] == self.prufumfang1):
            return  tab_prufumfang
         if(self.prufumfang1 == "Löschen"):
            del tab_prufumfang[len(tab_prufumfang) - 1]
            return tab_prufumfang
         else:
           if(len(tab_prufumfang) > 0 and tab_prufumfang[len(tab_prufumfang) - 1] != self.prufumfang1 and self.prufumfang1 != "Löschen"):
            tab_prufumfang.append(self.prufumfang1)
            return  tab_prufumfang

    @staticmethod
    def default_regel():
        return "DIN EN ISO 14555:2014-08,Anhang D"
#classes for Print Fonction for WPQR2
# class view
class PrintISOWPQR2Start(ModelView):
    'Print START WPQR2'
    __name__ = 'party.print_isowpqr2.start'
    zertifikat = fields.Many2One('party.wpqr2', 'Zertifikat', required=True)

#Wizard
class PrintWPQR2(Wizard):
    'Print ISOWPQR2'
    __name__ = 'party.print_isowpqr2'
    start = StateView('party.print_isowpqr2.start',
        'welding_certification.print_isowpqr2_cert_start_view_form', [
            Button('Cancel', 'end', 'tryton-cancel'),
            Button('Drucken', 'print_', 'tryton-print', default=True),
            ])
    print_ = StateReport('welding_certification.party.iso_wpqr2_report')
    def do_print_(self, action):
        data = {
            'zertifikat': self.start.zertifikat.id,
            }
        return action, data

#Report
class ISOWPQR2report(Report):
    __name__ = 'welding_certification.party.iso_wpqr2_report'


    @classmethod
    def _get_records(cls, ids, model, data):
        Move = Pool().get('party.wpqr2')

        clause = [

            ]


    @classmethod
    def get_context(cls, records, data):
        report_context = super(ISOWPQR2report, cls).get_context(records, data)

        Zertifikat = Pool().get('party.wpqr2')

        zertifikat = Zertifikat(data['zertifikat'])

        report_context['zertifikat'] = zertifikat
        report_context['wpqr'] = zertifikat.wpqr_
        report_context['prufer'] = zertifikat.prufer_prufstelle1.prufstelle
        report_context['hersteller'] = zertifikat.hersteller
        report_context['anschrift'] = zertifikat.anschrift
        report_context['beleg'] = zertifikat.beleg_nr
        report_context['regel'] = zertifikat.regel
        report_context['wps'] = zertifikat.wps
        report_context['datum_schweissen'] = zertifikat.datum_schweissen
        report_context['prufumfang'] = zertifikat.prufumfang2
        report_context['prozess'] = zertifikat.prozess
        report_context['prozess_gel'] = zertifikat.prozess_gel
        report_context['Bolzenwerkstoff'] = zertifikat.bolzenwerkstoff
        report_context['Bolzendurchmesser'] = zertifikat.bolzendurchmesser
        report_context['grundwerkstoff'] = zertifikat.grundwerkstoff.Bezeichnung
        report_context['bolzenlange'] = zertifikat.bolzenlange
        report_context['Werkstoffgruppe'] = zertifikat.werkstoffgrup
        report_context['wst'] = zertifikat.wst_nummer
        report_context['dicke'] = zertifikat.dicke_des_werkstoff
        report_context['Bolzenbezeichnung'] = zertifikat.bolzenbezeichnung
        report_context['keramikringes'] = zertifikat.keramikringes
        report_context['Handelsname'] = zertifikat.handelsname
        report_context['invendung1_signe'] = zertifikat.invendung1_signe
        report_context['invendung2_signe'] = zertifikat.invendung2_signe
        report_context['position'] = zertifikat.schweissposition2
        report_context['dampfung1_signe'] = zertifikat.dampfung1_signe
        report_context['dampfung2_signe'] = zertifikat.dampfung2_signe
        report_context['temperatur'] = zertifikat.temperatur
        report_context['stromquel'] = zertifikat.stromquel
        report_context['schutzgas'] = zertifikat.schutzgas.bezeichnung
        report_context['schweisspistole'] = zertifikat.schweisspistole
        report_context['durchflussmenge'] = zertifikat.durchflussmenge
        report_context['andere_angaben'] = zertifikat.andere_angaben
        report_context['strom'] = zertifikat.hubzundung[0].schweisstrom
        report_context['zeit'] = zertifikat.hubzundung[0].schweiszeit_ms
        report_context['uberstand'] = zertifikat.hubzundung[0].uberstand
        report_context['hub'] = zertifikat.hubzundung[0].hub
        report_context['bemerkung'] = zertifikat.hubzundung[0].bemerkung
        report_context['ort'] = zertifikat.ort
        report_context['ausstelleung'] = zertifikat.ausstelleung



        return report_context


# WPQR (EN ISO 15614) Class
class wpqr(DeactivableMixin, ModelView, ModelSQL, MultiValueMixin):
    'Party WPQR'
    __name__ = 'party.wpqr'
    wpqr = fields.Char('Qualifizierung eines Schweißverfahrens-Prüfungsbescheinigung')
    wpqr1 = fields.Char('Qualifizierungsumfang / Geltungsbereich')
    wpqr_nr = fields.Char('WPQR-Nr. des Herstellers')
    wpqr_nr_1 = fields.Function(fields.Char('WPQR-Nr. des Herstellers'),"On_change_andere_options")
#    prufer_prufstelle = fields.Selection([
 #       ('DGZfP', 'DGZfP-Ausbildungszentrum Wittenberge'),
  #      ('Harrison', 'Harrison Mechanical Corporation'),
#        ('MAN-Technologie', 'MAN-Technologie, Oberpfaffenhofen, Abtlg.WOP'),
 #   ], 'Prüfer oder Prüstelle', readonly = False,
#        )
    prufer_prufstelle1 = fields.Many2One('welding.pruefstelle', 'Name des prüfers oder der prüfstelle',
            ondelete='CASCADE')

    pericht1 = fields.Many2One('party.wpqr.bericht1', ' ')
    pericht2 = fields.Many2One('party.wpqr.bericht2', ' ')
    pulver = fields.Selection('on_change_schweisprocess','Bezeichnung des Schutzgases/Pulver', readonly = False,)
    pulver1 = fields.Selection('on_change_schweisprocess1','Bezeichnung des Schutzgases/Pulver', readonly = False,)

    space = fields.Char("                                                                                                                                            ")
    hersteller = fields.Char('Hersteller')
    beleg_nr = fields.Char('Beleg-Nr.')
    anschrift = fields.Char('Anschrift')
    auftrag_nr = fields.Char('Zertifikat/Auftrag-Nr')
    regel = fields.Selection([
        ('iso15614-1 (Schweißverfahrensprüfung für Stähle, Nickel und Nickelleg)', 'ISO 15614-1 | Schweißverfahrensprüfung - Teil1 : Stähle und Nickel'),
        ('iso15614-2 (Schweißverfahrensprüfung für Aluminium und seinen Legierungen)', 'ISO 15614-2 | Schweißverfahrensprüfung - Teil2 : Aluminium und seinen Legierungen'),
        ('iso15614-3 (Schweißverfahrensprüfung für Unleg. und niedrig leg. Gusseisen)', 'ISO 15614-3 | Schweißverfahrensprüfung - Teil3 : Unlegiertes u. niedrig leg. Gusseisen'),
        ('iso15614-4 (Schweißverfahrensprüfung - Ferigungsschweißen v. Aluminiumguss)', 'ISO 15614-4 | Schweißverfahrensprüfung - Teil4 : Ferigungsschweißen Aluminiumguss'),
        ('iso15614-5 (Schweißverfahrensprüfung für Titan, Zirkonium und ihren Leg)', 'ISO 15614-5 | Schweißverfahrensprüfung - Teil5 : Titan, Zirkonium und ihren Leg'),
        ('iso15614-6 (Schweißverfahrensprüfung für Kupfer und seinen Legierungen)', 'ISO 15614-6 | Schweißverfahrensprüfung - Teil6 : Kupfer und seinen Legierungen'),
        ('iso15614-7 (Schweißverfahrensprüfung - Auftragschweißen)', 'ISO 15614-7 | Schweißverfahrensprüfung - Teil7 : Auftragschweißen'),
        ('iso15614-8 (Schweißverfahrensprüfung - Einschweißen von Rohren in Rorhböden)', 'ISO 15614-8 | Schweißverfahrensprüfung - Teil8 : Rohre in Rorhböden'),
        ('iso15614-9 (Schweißverfahrensprüfung - Nassschweißen unter Überduck)', 'ISO 15614-9 | Schweißverfahrensprüfung - Teil9 : Nassschweißen unter Überduck'),
        ('iso15614-10 (Schweißverfahrensprüfung - Trockenschweißen unter Überduck)', 'ISO 15614-10 | Schweißverfahrensprüfung - Teil10 : Trockenschweißen unter Überduck'),
        ('iso15610 ( Qualifizierung durch den Einsatz von geprüften Schweißzusätzen)', 'ISO 15610 Qualifizierung durch den Einsatz von geprüften Schweißzusätzen'),
        ('iso15611 (Qualifizierung aufgrund von vorliegender schweißtechn. Erfahrung)', 'ISO 15611 Qualifizierung aufgrund von vorliegender schweißtechnischer Erfahrung'),
        ('iso15612 (Qualifizierung durch Einsatz eines standardschweißverfahrens)', 'ISO 15612 Qualifizierung durch Einsatz eines standardschweißverfahrens'),
        ('iso15613 (Qualifizierung aufgrund einer vorgezogenen Arbeitsprüfung)', 'ISO 15613 Qualifizierung aufgrund einer vorgezogenen Arbeitsprüfung'),
    ], 'Regel/Prüfnorm', readonly = False,
        )
    datum_schweissen = fields.Date("Datum der Schweißung")
    datum_ausstellung = fields.Date("Datum der Ausstellung")
    datum_bis = fields.Date("gültig bis")
    prufumfang1 = fields.Selection([
        ('Sicht-', 'Sicht-'),
        ('Durchstrahlungs', 'Durchstrahlungs-'),
        ('Ultraschall', 'Ultraschall-'),
        ('Oberflächenriss', 'Oberflächenriss-'),
        ('Querzug', 'Querzug-'),
        ('Querbiege', 'Querbiege-'),
        ('Kerbschlagbiege', 'Kerbschlagbiege-'),
        ('Löschen', 'Löschen'),
        ('Harte', 'Härte-'),
        ('Makroschliff', 'Makroschliff-'),
    ], ' ', readonly = False,
        )
    Stossart = fields.Selection([
        ('Stumpfnaht am Blech(P,BW) mit voller Durchschweißung', 'Stumpfnaht am Blech(P,BW) mit voller Durchschweißung'),
        ('Stumpfnaht am Rohr (T,BW) mit voller Durchschweißung', 'Stumpfnaht am Rohr (T,BW) mit voller Durchschweißung'),
        ('T-Stoß[zwei Bleche] für voll durchgeschweißte Stumpfnaht(P,BW)', 'T-Stoß(zwei Bleche) für voll durchgeschweißte Stumpfnaht(P,BW)'),
        ('T-Stoß [zwei Bleche] für kehlnähte (P,FW)', 'T-Stoß (zwei Bleche) für kehlnähte (P,FW)'),
        ('Rohrabzweigung für voll durchgeschweißte Verbindung(T,BW)', 'Rohrabzweigung für voll durchgeschweißte Verbindung(T,BW)'),
        ('Rohrabzweigung für Kehlnähte (T,FW)', 'Rohrabzweigung für Kehlnähte (T,FW)'),
    ], 'Stoßart/Nahtart', readonly = False,
        )
    Einlagig = fields.Selection([
        ('sl-einlagig', 'Sl-einlagig'),
        ('ml-mehrlagig', 'ml-mehrlagig'),
    ], 'Einlagig/Mehrlagig', readonly = False,
        )
    schweiss_nahteinzelheiten = fields.Selection([
        ('ss nb', 'ss nb | einseitig ohne Schweißbadsicherung'),
        ('ss mb', 'ss mb | einseitig mit Schweißbadsicherung'),
        ('bs', 'bs | beidseitig'),
        ('bs ng', 'bs ng | beidseitig ohne Ausfugen'),
        ('bs gg', 'bs gg | beidseitig mit Ausfugen'),
    ], 'Schweißnahteinzelheiten', readonly = False,
        )

    prufumfang2 = fields.Function(fields.Char("Prüfumfang"),'On_change_prufumfang1')
    prufumfangaux = fields.Function(fields.Char("Prufumfang2"),'On_change_prufumaux')

    schweißprocess = fields.Selection([
         ('--', '--'),
        ('111  Lichtbogenhandschweißen', '111 Lichtbogenhandschweißen'),
        ('111/121 Wurzel E, Auffüllen mit UP (Stahl)', '111/121 Wurzel E, Auffüllen mit UP (Stahl)'),
        ('111/135 Wurzel E, Auffüllen mit MAG (Stahl)', '111/135 Wurzel E, Auffüllen mit MAG (Stahl)'),
        ('112 Schwerkraft-Lichtbogenschweißen', '112 Schwerkraft-Lichtbogenschweißen'),
        ('114 Metall-Lichtbogenschweißen mit Fülldrahtelektrode ohne Schutzgas', '114 Metall-Lichtbogenschweißen mit Fülldrahtelektrode ohne Schutzgas'),
        ('12 Unterpulverschweißen', '12 Unterpulverschweißen'),
        ('121 Unterpulverschweißen mit Massivdrahtelektrode','121 Unterpulverschweißen mit Massivdrahtelektrode'),
        ('122 Unterpulverschweißen mit Massivbandelektrode', '122 Unterpulverschweißen mit Massivbandelektrode'),
        ('124 Unterpulverschweißen mit Metallpulverzusatz', '124 Unterpulverschweißen mit Metallpulverzusatz'),
        ('125 Unterpulverschweißen mit Fülldrahtelektrode', '125 Unterpulverschweißen mit Fülldrahtelektrode'),
        ('126 Unterpulverschweißen mit Füllbandelektrode', '126 Unterpulverschweißen mit Füllbandelektrode '),
        ('131 Metall-Inertgasschweißen mit Massivdrahtelektrode', '131 Metall-Inertgasschweißen mit Massivdrahtelektrode'),
        ('132 Metall-Inertgasschweißen mit schweißpulvergefüllter Drahtelektrode', '132 Metall-Inertgasschweißen mit schweißpulvergefüllter Drahtelektrode'),
        ('133 Metall-Inertgasschweißen mit metallpulvergefüllter Drahtelektrode', '133 Metall-Inertgasschweißen mit metallpulvergefüllter Drahtelektrode'),
        ('135 Metall-Aktivgasschweißen mit Massivdrahtelektrode', '135 Metall-Aktivgasschweißen mit Massivdrahtelektrode'),
        ('135/111 Wurzel MAG, Auffüllen mit  E (Stahl)', '135/111 Wurzel MAG, Auffüllen mit  E (Stahl)'),
        ('135/121 Wurzel MAG, Auffüllen mit  UP (Stahl)', '135/121 Wurzel MAG, Auffüllen mit  UP (Stahl)'),
        ('136 Metall-Aktivgasschweißen mit schweißpulvergefüllter Drahtelektrode', '136 Metall-Aktivgasschweißen mit schweißpulvergefüllter Drahtelektrode'),
        ('136/121 Wurzel MAG, Auffüllen mit  UP (Stahl)', '136/121 Wurzel MAG, Auffüllen mit  UP (Stahl)'),
        ('138 Metall-Aktivgasschweißen mit metallpulvergefüllter Drahtelektrode', '138 Metall-Aktivgasschweißen mit metallpulvergefüllter Drahtelektrode'),
        ('141 Wolfram-Inertgasschweißen mit Massivdraht- oder Massivstabzusatz', '141 Wolfram-Inertgasschweißen mit Massivdraht- oder Massivstabzusatz'),
        ('141/111 Wurzel WIG, Auffüllen mit  E (Stahl, Cu, Ni)', '141/111  Wurzel WIG, Auffüllen mit  E (Stahl, Cu, Ni)'),
        ('141/121 Wurzel WIG, Auffüllen mit  UP (Stahl, Ni)', '141/121 Wurzel WIG, Auffüllen mit  UP (Stahl, Ni)'),
        ('141/131 Wurzel WIG, Auffüllen mit  MIG (Al, Cu, Ni, Ti)', '141/131 Wurzel WIG, Auffüllen mit  MIG (Al, Cu, Ni, Ti)'),
        ('141/135 Wurzel WIG, Auffüllen mit  MAG (Stahl, Ni)', '141/135 Wurzel WIG, Auffüllen mit  MAG (Stahl, Ni)'),
        ('141/136 Wurzel WIG, Auffüllen mit  MAG (Stahl)', '141/136 Wurzel WIG, Auffüllen mit  MAG (Stahl)'),
        ('142 Wolfram-Inertgasschweißen ohne Schweißzusatz', '142 Wolfram-Inertgasschweißen ohne Schweißzusatz'),
        ('143 Wolfram-Inertgasschweißen mit Fülldraht- oder Füllstabzusatz', '143 Wolfram-Inertgasschweißen mit Fülldraht- oder Füllstabzusatz'),
        ('145 WIG-Schweißen mit reduzierenden Gasanteilen und Massivzusatz(Draht/Stab)', '145 WIG-Schweißen mit reduzierenden Gasanteilen und Massivzusatz(Draht/Stab)'),
        ('146 WIG-Schweißen mit reduzierenden Gasanteilen und Füllzusatz(Draht/Stab)', '146 WIG-Schweißen mit reduzierenden Gasanteilen und Füllzusatz(Draht/Stab)'),
        ('147 Wolfram-Schutzgasschweißen mit aktiven Gesanteilen im inerten Schutzgas', '147 Wolfram-Schutzgasschweißen mit aktiven Gesanteilen im inerten Schutzgas'),
        ('15 Plasmaschweißen', '15 Plasmaschweißen'),
        ('151 Plasma-Metall-Inertgasschweißen', '151 Plasma-Metall-Inertgasschweißen'),
        ('152 Pulver-Plasmalichtbogenschweißen', '152 Pulver-Plasmalichtbogenschweißen'),
        ('311 Gasschweißen mit Sauerstoff-Acetylen-Flamme', '311 Gasschweißen mit Sauerstoff-Acetylen-Flamme'),
        ('312 Gasschweißen mit Sauerstoff-Propan-Flamme', '312 Gasschweißen mit Sauerstoff-Propan-Flamme'),
        ('313 asschweißen mit Sauerstoff-Wasserstoff-Flamme', '313 Gasschweißen mit Sauerstoff-Wasserstoff-Flamme'),
    ], 'Schweißprozess(e)', readonly = False,
        )
    schweißprocess_gel = fields.Function(fields.Char("Prufumfang2"),'On_change_schweissprocess')
    grundwerkstoffe = fields.Many2One('welding.grundwerkstoff_properties', 'Grundwerkstoffe')
    grundwerkstoffe1 = fields.Many2One('welding.grundwerkstoff_properties', 'Grundwerkstoffe1')
    gruppen1 = fields.Function(fields.Char("Gruppe(n) und Untergruppe(n)"),'On_change_grund1')
    gruppen2 = fields.Function(fields.Char("Gruppe(n) und Untergruppe(n)"),'On_change_grund2')

    bezeich1 = fields.Function(fields.Char("Bezeichnung"),'On_change_grund3')
    bezeich2 = fields.Function(fields.Char("Bezeichnung"),'On_change_grund4')

    nummer1 = fields.Function(fields.Char("Nummer"),'On_change_grund5')
    nummer2 = fields.Function(fields.Char("Nummer"),'On_change_grund6')

    hartegrad = fields.Char("Härtegrad")

    dicke_des_grundwerkstoff = fields.Function(fields.Char("Dicke des Grundwerkstoffes(mm)"),'On_change_stossart')
    dicke_des_grundwerkstoff_value1 = fields.Integer("value")
    dicke_des_schweissgutes = fields.Integer("Dicke des Schweißgutes(mm)")
    prozess1 = fields.Char("Prozess 1")
    prozess2 = fields.Char("Prozess 2")
    Kehlnahtdicke = fields.Integer("Kehlnahtdicke(mm)")
    Kehlnahtdicke_geltungs = fields.Function(fields.Char("Kehlnaht"),'On_change_stossart2')
    val2 = " "
    rohraussendurchmesser = fields.Integer("Rohraußendurchmesser")
    rohrauss_geltungs = fields.Function(fields.Char("Rohraußendurchmesser Geltungs"),'On_change_stossart3')
    zusatzwerkstoff = fields.Many2One('welding.szi_data', 'Zusatzwerkstoff : Bezeichnung')
    fabrikat = fields.Function(fields.Char("Fabrikat (Hersteller)"),'On_change_zusatzwerkstoff')
    stromart_polung = fields.Char("Stromart und Polung")
    stromart_polung2 = fields.Char("Stromart und Polung")
    o1 = fields.Float("O(mm)")
    o2 = fields.Float("O(mm)")
    zusatzwerkstoff2 = fields.Many2One('welding.szi_data', 'Zusatzwerkstoff : Bezeichnung')
    fabrikat2 = fields.Function(fields.Char("Fabrikat (Hersteller)"),'On_change_zusatzwerkstoff2')

    schutzgas = fields.Many2One('party.schutzgas', 'Bezeichnung des Schutzgases/Pulver')
    schutzgas1 = fields.Many2One('party.schutzgas', ' ')

    formiergases = fields.Char("Bezeichnung des Formiergases")

    vorwarmungtemperatur = fields.Char("Vorwärmungtemperatur")
    zwischenlagentemperatur = fields.Char("Zwischenlagentemperatur")
    wasserstoffarmgluhen = fields.Char("Wasserstoffarmglühen")
    warmenachbehandlung = fields.Char("Wärmenachbehandlung")
    sonstige = fields.Text("Sonstige Angaben (Siehe auch 8.5)")
    index = fields.Char("Hiermit wird bestätig, dass die Prüfungsschweißungen in Übereinstimmung mit den Bedingungen der vorbezeichneten Regeln bzw. Prüfnorm zufriedenstellend vorbereitet, geschweißt und geprüft worden sind.")
    warmeeinbringung = fields.Char("Wärmeeinbringung")
    tropfenuebergande = fields.Selection([
        ('Kurzlichtbogen (D)', 'Kurzlichtbogen (D) : Short-circuit transfer (dip transfert)'),
        ('Langlichtbogen (G)', 'Langlichtbogen (G) | Globular transfer'),
        ('Sprühlichtbogen (S)', 'Sprühlichtbogen (S) | Spray transfer'),
        ('Impulslichtbogen (P)', 'Impulslichtbogen (P) | Pulsed transfer'),
    ], 'Art des Tropfenüberganges', readonly = False,
        )
    schweissposition = fields.Selection([
        ('PA', 'PA Wannenposition'),
        ('PB', 'PB Horizontalposition'),
        ('PC', 'PC Querposition'),
        ('PD', 'PD Horizontal-Überkopfposition'),
        ('PE', 'PE Überkopfposition'),
        ('PF', 'PF Steigposition'),
        ('PG', 'PG Fallposition'),
        ('PH', 'PH Rohrposition für steigendschweißen'),
        ('PJ', 'PJ Rohrposition für Fallendschweißen'),
        ('H-LO45', 'H-LO45 Steigend am Rohr, Neigungswinkel 45°'),
        ('J-LO45', 'J-LO45 Fallend  am Rohr, Neigungswinkel 45°'),
    ], 'Schweißposition', readonly = False,
        )
    schweissgeltung = fields.Function(fields.Char("Schweißposition Geltungsbereich"),'On_change_schweissposition')

    @fields.depends('pulver', 'schweißprocess')
    def on_change_schweisprocess(self):
        tab=[]
        if(self.schweißprocess == "111  Lichtbogenhandschweißen" or self.schweißprocess == "112 Schwerkraft-Lichtbogenschweißen" or self.schweißprocess == "114 Metall-Lichtbogenschweißen mit Fülldrahtelektrode ohne Schutzgas" or self.schweißprocess == "12 Unterpulverschweißen" or self.schweißprocess == "121 Unterpulverschweißen mit Massivdrahtelektrode" or self.schweißprocess == "122 Unterpulverschweißen mit Massivbandelektrode" or self.schweißprocess =="124 Unterpulverschweißen mit Metallpulverzusatz" or self.schweißprocess =="125 Unterpulverschweißen mit Fülldrahtelektrode" or self.schweißprocess =="126 Unterpulverschweißen mit Füllbandelektrode" or self.schweißprocess == "311 Gasschweißen mit Sauerstoff-Acetylen-Flamme" or self.schweißprocess=="312 Gasschweißen mit Sauerstoff-Propan-Flamme" or self.schweißprocess=="313 asschweißen mit Sauerstoff-Wasserstoff-Flamme"):
          tab.append(("ISO 14175-N5-NH-20 nach EN ISO 14175(Formiergas80/20)", "ISO 14175-N5-NH-20 nach EN ISO 14175(Formiergas80/20)"))
          tab.append(("ISO 14175-R2-ArH-20 nach EN ISO 14175(ARCAL PLASMA 62)", "ISO 14175-R2-ArH-20 nach EN ISO 14175(ARCAL PLASMA 62)"))
          return tab
        if(self.schweißprocess == "131 Metall-Inertgasschweißen mit Massivdrahtelektrode"  or self.schweißprocess == "132 Metall-Inertgasschweißen mit schweißpulvergefüllter Drahtelektrode" or self.schweißprocess =="133 Metall-Inertgasschweißen mit metallpulvergefüllter Drahtelektrode" or self.schweißprocess == "15 Plasmaschweißen"):
          tab.append(("ISO 14175-I1-Ar nach EN ISO 14175 (ARCAL 1)", "ISO 14175-I1-Ar nach EN ISO 14175 (ARCAL 1)"))
          tab.append(("ISO 14175-I2-He nach EN ISO 14175", "ISO 14175-I2-He nach EN ISO 14175"))
          tab.append(("ISO 14175-I3-ArHe-30 nach EN ISO 14175 (ARCAL 33)", "ISO 14175-I3-ArHe-30 nach EN ISO 14175 (ARCAL 33)"))
          tab.append(("ISO 14175-N5-NH-20 nach EN ISO 14175 (Fromiergas 80/20)", "ISO 14175-N5-NH-20 nach EN ISO 14175 (Fromiergas 80/20)"))
          tab.append(("ISO 14175-R2-ArH-20 nach EN ISO 14175 (ARCAL PLASMA 62)", "ISO 14175-R2-ArH-20 nach EN ISO 14175 (ARCAL PLASMA 62)"))
          return tab
        if(self.schweißprocess == "136 Metall-Aktivgasschweißen mit schweißpulvergefüllter Drahtelektrode" or self.schweißprocess == "138 Metall-Aktivgasschweißen mit metallpulvergefüllter Drahtelektrode"):
          tab.append(("ISO 14175-C1-C nach EN ISO 14175", "ISO 14175-C1-C nach EN ISO 14175"))
          tab.append(("ISO 14175-M12-ArC-2 nach EN ISO 14175(ARCAL 12)", "ISO 14175-M12-ArC-2 nach EN ISO 14175(ARCAL 12)"))
          tab.append(("ISO 14175-M12-ArHeC-18/1 nach EN ISO 14175(ARCAL 121)", "ISO 14175-M12-ArHeC-18/1 nach EN ISO 14175(ARCAL 121)"))
          tab.append(("ISO 14175-M13-ArO-2 nach EN ISO 14175(CARGAL)", "ISO 14175-M13-ArO-2 nach EN ISO 14175(CARGAL)"))
          tab.append(("ISO 14175-M14-ArCO-3/1 nach EN ISO 14175(ARCAL 14)", "ISO 14175-M14-ArCO-3/1 nach EN ISO 14175(ARCAL 14)"))
          tab.append(("ISO 14175-M20-ArC8 nach EN ISO 14175(ARCAL 21)", "ISO 14175-M20-ArC8 nach EN ISO 14175(ARCAL 21)"))
          tab.append(("ISO 14175-M21-ArC-18 nach EN ISO 14175(ATAL, ARCAL 5)", "ISO 14175-M21-ArC-18 nach EN ISO 14175(ATAL, ARCAL 5)"))
          tab.append(("ISO 14175-M22-ArO-8 nach EN ISO 14175(CARGAL 4)", "ISO 14175-M22-ArO-8 nach EN ISO 14175(CARGAL 4)"))
          tab.append(("ISO 14175-M23-ArCO-5/5 nach EN ISO 14175(TERAL)", "ISO 14175-M23-ArCO-5/5 nach EN ISO 14175(TERAL)"))
          tab.append(("ISO 14175-M24-ArCO-12/2 nach EN ISO 14175(ARCAL 24)", "ISO 14175-M24-ArCO-12/2 nach EN ISO 14175(ARCAL 24)"))
          tab.append(("ISO 14175-N5-NH-20 nach EN ISO 14175(Formiergas 80/20)", "ISO 14175-N5-NH-20 nach EN ISO 14175(Formiergas 80/20)"))
          tab.append(("ISO 14175-R2-ArH-20 nach EN ISO 14175(ARCAL PLASMA 62)", "ISO 14175-R2-ArH-20 nach EN ISO 14175(ARCAL PLASMA 62)"))
          return tab
        else:
          if(self.schweißprocess == "111/121 Wurzel E, Auffüllen mit UP (Stahl)"  or self.schweißprocess == "111/135 Wurzel E, Auffüllen mit MAG (Stahl)" or self.schweißprocess == "135 Metall-Aktivgasschweißen mit Massivdrahtelektrode" or self.schweißprocess =="135/111 Wurzel MAG, Auffüllen mit  E (Stahl)" or self.schweißprocess =="135/121 Wurzel MAG, Auffüllen mit  UP (Stahl)" or self.schweißprocess =="136/121 Wurzel MAG, Auffüllen mit  UP (Stahl)" or self.schweißprocess == "141 Wolfram-Inertgasschweißen mit Massivdraht- oder Massivstabzusatz" or self.schweißprocess == "141/111 Wurzel WIG, Auffüllen mit  E (Stahl, Cu, Ni)" or self.schweißprocess =="141/121 Wurzel WIG, Auffüllen mit  UP (Stahl, Ni)" or self.schweißprocess=="141/131 Wurzel WIG, Auffüllen mit  MIG (Al, Cu, Ni, Ti)" or self.schweißprocess=="141/135 Wurzel WIG, Auffüllen mit  MAG (Stahl, Ni)" or self.schweißprocess =="141/136 Wurzel WIG, Auffüllen mit  MAG (Stahl)" or self.schweißprocess =="142 Wolfram-Inertgasschweißen ohne Schweißzusatz" or self.schweißprocess=="143 Wolfram-Inertgasschweißen mit Fülldraht- oder Füllstabzusatz" or self.schweißprocess=="145 WIG-Schweißen mit reduzierenden Gasanteilen und Massivzusatz(Draht/Stab)" or self.schweißprocess =="146 WIG-Schweißen mit reduzierenden Gasanteilen und Füllzusatz(Draht/Stab)" or self.schweißprocess=="147 Wolfram-Schutzgasschweißen mit aktiven Gesanteilen im inerten Schutzgas" or self.schweißprocess=="151 Plasma-Metall-Inertgasschweißen" or self.schweißprocess=="152 Pulver-Plasmalichtbogenschweißen"):
             tab.append(("ISO 14175-C1-C nach EN ISO 14175", "ISO 14175-C1-C nach EN ISO 14175"))
             tab.append(("ISO 14175-I1-Ar nach EN ISO 14175(ARCAL 1)", "ISO 14175-I1-Ar nach EN ISO 14175(ARCAL 1)"))
             tab.append(("ISO 14175-I2-He nach EN ISO 14175", "ISO 14175-I2-He nach EN ISO 14175"))
             tab.append(("ISO 14175-I3-ArHe-30 nach EN ISO 14175(ARCAL 33)", "ISO 14175-I3-ArHe-30 nach EN ISO 14175(ARCAL 33)"))
             tab.append(("ISO 14175-M12-ArC-2 nach EN ISO 14175(ARCAL 12)", "ISO 14175-M12-ArC-2 nach EN ISO 14175(ARCAL 12)"))
             tab.append(("ISO 14175-M12-ArHeC-18/1 nach EN ISO 14175(ARCAL 121)", "ISO 14175-M12-ArHeC-18/1 nach EN ISO 14175(ARCAL 121)"))
             tab.append(("ISO 14175-M13-ArO-2 nach EN ISO 14175(CARGAL)", "ISO 14175-M13-ArO-2 nach EN ISO 14175(CARGAL)"))
             tab.append(("ISO 14175-M14-ArCO-3/1 nach EN ISO 14175(ARCAL 14)", "ISO 14175-M14-ArCO-3/1 nach EN ISO 14175(ARCAL 14)"))
             tab.append(("ISO 14175-M20-ArC-8 nach EN ISO 14175(ARCAL 21)", "ISO 14175-M20-ArC-8 nach EN ISO 14175(ARCAL 21)"))
             tab.append(("ISO 14175-M21-ArC-18 nach EN ISO 14175(ATAL,ARCAL 5)", "ISO 14175-M21-ArC-18 nach EN ISO 14175(ATAL,ARCAL5)"))
             tab.append(("ISO 14175-M22-ArO-8 nach EN ISO 14175(CARGAL 4)", "ISO 14175-M22-ArO-8 nach EN ISO 14175(CARGAL4)"))
             tab.append(("ISO 14175-M23-ArCO-5/5 nach EN ISO 14175(TERAL)", "ISO 14175-M23-ArCO-5/5 nach EN ISO 14175(TERAL)"))
             tab.append(("ISO 14175-M24-ArCO-12/2 nach EN ISO 14175(ARCAL 24)", "ISO 14175-M24-ArCO-12/2 nach EN ISO 14175(ARCAL 24)"))
             tab.append(("ISO 14175-N2-ArN-2 nach EN ISO 14175(ARCAL 391)", "ISO 14175-N2-ArN-2 nach EN ISO 14175(ARCAL 391)"))
             tab.append(("ISO 14175-N4-ArNH-3/0,7 nach EN ISO 14175(ARCAL 405)", "ISO 14175-N4-ArNH-3/0,7 nach EN ISO 14175(ARCAL 405)"))
             tab.append(("ISO 14175-N5-NH-20 nach EN ISO 14175(Formiergas 80/20)", "ISO 14175-N5-NH-20 nach EN ISO 14175(Formiergas 80/20)"))
             tab.append(("ISO 14175-R1-ArH-10 nach EN ISO 14175(NOXAL 4)", "ISO 14175-R1-ArH-10 nach EN ISO 14175(NOXAL 4)"))
             tab.append(("ISO 14175-R1-ArH-2,4 nach EN ISO 14175(ARCAL 10)", "ISO 14175-R1-ArH-2,4 nach EN ISO 14175(ARCAL 10)"))
             tab.append(("ISO 14175-R2-ArH-20 nach EN ISO 14175(ARCAL PLASMA 62)", "ISO 14175-R2-ArH-20 nach EN ISO 14175(ARCAL PLASMA 62)"))
             tab.append(("ISO 14175-Z-Ar+N-0,015 nach EN ISO 14175(ARCAL 1N)", "ISO 14175-Z-Ar+N-0,015 nach EN ISO 14175(ARCAL 1N)"))
             return tab

    @fields.depends('pulver1', 'schweißprocess')
    def on_change_schweisprocess1(self):
        tab=[]
        if(self.schweißprocess == "111  Lichtbogenhandschweißen" or self.schweißprocess == "112 Schwerkraft-Lichtbogenschweißen" or self.schweißprocess == "114 Metall-Lichtbogenschweißen mit Fülldrahtelektrode ohne Schutzgas" or self.schweißprocess == "12 Unterpulverschweißen" or self.schweißprocess == "121 Unterpulverschweißen mit Massivdrahtelektrode" or self.schweißprocess == "122 Unterpulverschweißen mit Massivbandelektrode" or self.schweißprocess =="124 Unterpulverschweißen mit Metallpulverzusatz" or self.schweißprocess =="125 Unterpulverschweißen mit Fülldrahtelektrode" or self.schweißprocess =="126 Unterpulverschweißen mit Füllbandelektrode" or self.schweißprocess == "311 Gasschweißen mit Sauerstoff-Acetylen-Flamme"  or self.schweißprocess=="312 Gasschweißen mit Sauerstoff-Propan-Flamme" or self.schweißprocess=="313 asschweißen mit Sauerstoff-Wasserstoff-Flamme"):
          tab.append(("ISO 14175-N5-NH-20 nach EN ISO 14175(Formiergas80/20)", "ISO 14175-N5-NH-20 nach EN ISO 14175(Formiergas80/20)"))
          tab.append(("ISO 14175-R2-ArH-20 nach EN ISO 14175(ARCAL PLASMA 62)", "ISO 14175-R2-ArH-20 nach EN ISO 14175(ARCAL PLASMA 62)"))
          return tab
        if(self.schweißprocess == "131 Metall-Inertgasschweißen mit Massivdrahtelektrode" or self.schweißprocess == "132 Metall-Inertgasschweißen mit schweißpulvergefüllter Drahtelektrode" or self.schweißprocess=="133 Metall-Inertgasschweißen mit metallpulvergefüllter Drahtelektrode" or self.schweißprocess == "15 Plasmaschweißen"):
          tab.append(("ISO 14175-I1-Ar nach EN ISO 14175 (ARCAL 1)", "ISO 14175-I1-Ar nach EN ISO 14175 (ARCAL 1)"))
          tab.append(("ISO 14175-I2-He nach EN ISO 14175", "ISO 14175-I2-He nach EN ISO 14175"))
          tab.append(("ISO 14175-I3-ArHe-30 nach EN ISO 14175 (ARCAL 33)", "ISO 14175-I3-ArHe-30 nach EN ISO 14175 (ARCAL 33)"))
          tab.append(("ISO 14175-N5-NH-20 nach EN ISO 14175 (Fromiergas 80/20)", "ISO 14175-N5-NH-20 nach EN ISO 14175 (Fromiergas 80/20)"))
          tab.append(("ISO 14175-R2-ArH-20 nach EN ISO 14175 (ARCAL PLASMA 62)", "ISO 14175-R2-ArH-20 nach EN ISO 14175 (ARCAL PLASMA 62)"))
          return tab
        if(self.schweißprocess == "136 Metall-Aktivgasschweißen mit schweißpulvergefüllter Drahtelektrode" or self.schweißprocess == "138 Metall-Aktivgasschweißen mit metallpulvergefüllter Drahtelektrode"):
          tab.append(("ISO 14175-C1-C nach EN ISO 14175", "ISO 14175-C1-C nach EN ISO 14175"))
          tab.append(("ISO 14175-M12-ArC-2 nach EN ISO 14175(ARCAL 12)", "ISO 14175-M12-ArC-2 nach EN ISO 14175(ARCAL 12)"))
          tab.append(("ISO 14175-M12-ArHeC-18/1 nach EN ISO 14175(ARCAL 121)", "ISO 14175-M12-ArHeC-18/1 nach EN ISO 14175(ARCAL 121)"))
          tab.append(("ISO 14175-M13-ArO-2 nach EN ISO 14175(CARGAL)", "ISO 14175-M13-ArO-2 nach EN ISO 14175(CARGAL)"))
          tab.append(("ISO 14175-M14-ArCO-3/1 nach EN ISO 14175(ARCAL 14)", "ISO 14175-M14-ArCO-3/1 nach EN ISO 14175(ARCAL 14)"))
          tab.append(("ISO 14175-M20-ArC8 nach EN ISO 14175(ARCAL 21)", "ISO 14175-M20-ArC8 nach EN ISO 14175(ARCAL 21)"))
          tab.append(("ISO 14175-M21-ArC-18 nach EN ISO 14175(ATAL, ARCAL 5)", "ISO 14175-M21-ArC-18 nach EN ISO 14175(ATAL, ARCAL 5)"))
          tab.append(("ISO 14175-M22-ArO-8 nach EN ISO 14175(CARGAL 4)", "ISO 14175-M22-ArO-8 nach EN ISO 14175(CARGAL 4)"))
          tab.append(("ISO 14175-M23-ArCO-5/5 nach EN ISO 14175(TERAL)", "ISO 14175-M23-ArCO-5/5 nach EN ISO 14175(TERAL)"))
          tab.append(("ISO 14175-M24-ArCO-12/2 nach EN ISO 14175(ARCAL 24)", "ISO 14175-M24-ArCO-12/2 nach EN ISO 14175(ARCAL 24)"))
          tab.append(("ISO 14175-N5-NH-20 nach EN ISO 14175(Formiergas 80/20)", "ISO 14175-N5-NH-20 nach EN ISO 14175(Formiergas 80/20)"))
          tab.append(("ISO 14175-R2-ArH-20 nach EN ISO 14175(ARCAL PLASMA 62)", "ISO 14175-R2-ArH-20 nach EN ISO 14175(ARCAL PLASMA 62)"))

          return tab
        else:
          if(self.schweißprocess == "111/121 Wurzel E, Auffüllen mit UP (Stahl)" or self.schweißprocess == "111/135 Wurzel E, Auffüllen mit MAG (Stahl)" or self.schweißprocess == "135 Metall-Aktivgasschweißen mit Massivdrahtelektrode"  or self.schweißprocess =="135/111 Wurzel MAG, Auffüllen mit  E (Stahl)" or self.schweißprocess =="135/121 Wurzel MAG, Auffüllen mit  UP (Stahl)" or self.schweißprocess =="136/121 Wurzel MAG, Auffüllen mit  UP (Stahl)" or self.schweißprocess == "141 Wolfram-Inertgasschweißen mit Massivdraht- oder Massivstabzusatz" or self.schweißprocess == "141/111 Wurzel WIG, Auffüllen mit  E (Stahl, Cu, Ni)"  or self.schweißprocess =="141/121 Wurzel WIG, Auffüllen mit  UP (Stahl, Ni)" or self.schweißprocess=="141/131 Wurzel WIG, Auffüllen mit  MIG (Al, Cu, Ni, Ti)" or self.schweißprocess=="141/135 Wurzel WIG, Auffüllen mit  MAG (Stahl, Ni)" or self.schweißprocess=="141/136 Wurzel WIG, Auffüllen mit  MAG (Stahl)" or self.schweißprocess=="142 Wolfram-Inertgasschweißen ohne Schweißzusatz" or self.schweißprocess=="143 Wolfram-Inertgasschweißen mit Fülldraht- oder Füllstabzusatz" or self.schweißprocess=="145 WIG-Schweißen mit reduzierenden Gasanteilen und Massivzusatz(Draht/Stab)" or self.schweißprocess=="146 WIG-Schweißen mit reduzierenden Gasanteilen und Füllzusatz(Draht/Stab)"  or self.schweißprocess=="147 Wolfram-Schutzgasschweißen mit aktiven Gesanteilen im inerten Schutzgas" or self.schweißprocess=="151 Plasma-Metall-Inertgasschweißen" or self.schweißprocess=="152 Pulver-Plasmalichtbogenschweißen"):
             tab.append(("ISO 14175-C1-C nach EN ISO 14175", "ISO 14175-C1-C nach EN ISO 14175"))
             tab.append(("ISO 14175-I1-Ar nach EN ISO 14175(ARCAL 1)", "ISO 14175-I1-Ar nach EN ISO 14175(ARCAL 1)"))
             tab.append(("ISO 14175-I2-He nach EN ISO 14175", "ISO 14175-I2-He nach EN ISO 14175"))
             tab.append(("ISO 14175-I3-ArHe-30 nach EN ISO 14175(ARCAL 33)", "ISO 14175-I3-ArHe-30 nach EN ISO 14175(ARCAL 33)"))
             tab.append(("ISO 14175-M12-ArC-2 nach EN ISO 14175(ARCAL 12)", "ISO 14175-M12-ArC-2 nach EN ISO 14175(ARCAL 12)"))
             tab.append(("ISO 14175-M12-ArHeC-18/1 nach EN ISO 14175(ARCAL 121)", "ISO 14175-M12-ArHeC-18/1 nach EN ISO 14175(ARCAL 121)"))
             tab.append(("ISO 14175-M13-ArO-2 nach EN ISO 14175(CARGAL)", "ISO 14175-M13-ArO-2 nach EN ISO 14175(CARGAL)"))
             tab.append(("ISO 14175-M14-ArCO-3/1 nach EN ISO 14175(ARCAL 14)", "ISO 14175-M14-ArCO-3/1 nach EN ISO 14175(ARCAL 14)"))
             tab.append(("ISO 14175-M20-ArC-8 nach EN ISO 14175(ARCAL 21)", "ISO 14175-M20-ArC-8 nach EN ISO 14175(ARCAL 21)"))
             tab.append(("ISO 14175-M21-ArC-18 nach EN ISO 14175(ATAL,ARCAL 5)", "ISO 14175-M21-ArC-18 nach EN ISO 14175(ATAL,ARCAL5)"))
             tab.append(("ISO 14175-M22-ArO-8 nach EN ISO 14175(CARGAL 4)", "ISO 14175-M22-ArO-8 nach EN ISO 14175(CARGAL4)"))
             tab.append(("ISO 14175-M23-ArCO-5/5 nach EN ISO 14175(TERAL)", "ISO 14175-M23-ArCO-5/5 nach EN ISO 14175(TERAL)"))
             tab.append(("ISO 14175-M24-ArCO-12/2 nach EN ISO 14175(ARCAL 24)", "ISO 14175-M24-ArCO-12/2 nach EN ISO 14175(ARCAL 24)"))
             tab.append(("ISO 14175-N2-ArN-2 nach EN ISO 14175(ARCAL 391)", "ISO 14175-N2-ArN-2 nach EN ISO 14175(ARCAL 391)"))
             tab.append(("ISO 14175-N4-ArNH-3/0,7 nach EN ISO 14175(ARCAL 405)", "ISO 14175-N4-ArNH-3/0,7 nach EN ISO 14175(ARCAL 405)"))
             tab.append(("ISO 14175-N5-NH-20 nach EN ISO 14175(Formiergas 80/20)", "ISO 14175-N5-NH-20 nach EN ISO 14175(Formiergas 80/20)"))
             tab.append(("ISO 14175-R1-ArH-10 nach EN ISO 14175(NOXAL 4)", "ISO 14175-R1-ArH-10 nach EN ISO 14175(NOXAL 4)"))
             tab.append(("ISO 14175-R1-ArH-2,4 nach EN ISO 14175(ARCAL 10)", "ISO 14175-R1-ArH-2,4 nach EN ISO 14175(ARCAL 10)"))
             tab.append(("ISO 14175-R2-ArH-20 nach EN ISO 14175(ARCAL PLASMA 62)", "ISO 14175-R2-ArH-20 nach EN ISO 14175(ARCAL PLASMA 62)"))
             tab.append(("ISO 14175-Z-Ar+N-0,015 nach EN ISO 14175(ARCAL 1N)", "ISO 14175-Z-Ar+N-0,015 nach EN ISO 14175(ARCAL 1N)"))

             return tab

    @staticmethod
    def default_dicke_des_grundwerkstoff_value1():
        return 0

    @staticmethod
    def default_schweissposition():
        return "PA"

    @staticmethod
    def default_Kehlnahtdicke():
        return 0

    def On_change_andere_options(self,schweissposition):
        val1 ="ISO"
        val2 = self.regel
        pos1 = val2.find('iso')
        pos2 = val2.find('(')
        #extraction que lq premiere partie
        val21 = val2[pos1:pos2]
        val3 = self.schweißprocess
        pos3 = val3.find(' ')
        val31 = val3[0:pos3]
        #
        val4 = self.Stossart
        pos41 = val4.find('(')
        pos42 = val4.find(')')
        val41 = val4[pos41+1:pos42]
        #
        if(self.Stossart == "Stumpfnaht am Blech(P,BW) mit voller Durchschweißung" or self.Stossart =="T-Stoß[zwei Bleche] für voll durchgeschweißte Stumpfnaht(P,BW)" or self.Stossart =="T-Stoß [zwei Bleche] für kehlnähte (P,FW)"):
            val5 = ""
        else:
          if(self.Stossart =="Stumpfnaht am Rohr (T,BW) mit voller Durchschweißung" or self.Stossart =="Rohrabzweigung für voll durchgeschweißte Verbindung(T,BW)" or self.Stossart =="Rohrabzweigung für Kehlnähte (T,FW)"):
             val5 = "D"+str(self.rohraussendurchmesser)
        return val1+" "+val21+" "+val31+" "+val41+" "+self.grundwerkstoffe.Werkstoffgruppe+"/"+self.grundwerkstoffe1.Werkstoffgruppe+" "+"t0"+str(self.dicke_des_grundwerkstoff_value1)+" "+val5+" "+self.schweissposition


    def On_change_schweissposition(self,schweissposition):
       if(self.schweissposition == "H-LO45" or self.schweissposition == "PH" or self.schweissposition == "PA" or self.schweissposition == "PB" or self.schweissposition == "PC" or self.schweissposition == "PD" or self.schweissposition == "PE" or self.schweissposition == "PF"):
         return "Geltungsbereich:alle außer fallendes Schweißen (Siehe 8.4.2)"
       else:
           if(self.schweissposition == "PG" or self.schweissposition == "PJ" or self.schweissposition == "J-LO45"):
              return "Geltungsbereich : PG, PJ und J-L045(Siehe 8.4.2)"

    def On_change_zusatzwerkstoff2(self,zusatzwerkstoff2):
         return self.zusatzwerkstoff2.Hersteller

    def On_change_zusatzwerkstoff(self,zusatzwerkstoff):
         return self.zusatzwerkstoff.Hersteller

    def On_change_stossart3(self,Stossart):
        if((self.regel == "iso15614-1 (Schweißverfahrensprüfung für Stähle, Nickel und Nickelleg)" or self.regel == "iso15614-2 (Schweißverfahrensprüfung für Aluminium und seinen Legierungen)" or self.regel == "iso15614-5 (Schweißverfahrensprüfung für Titan, Zirkonium und ihren Leg)" or self.regel == "iso15614-10 (Schweißverfahrensprüfung - Trockenschweißen unter Überduck)") and (self.Stossart == "T-Stoß [zwei Bleche] für kehlnähte (P,FW)" or self.Stossart =="Stumpfnaht am Blech(P,BW) mit voller Durchschweißung" or self.Stossart =="T-Stoß[zwei Bleche] für voll durchgeschweißte Stumpfnaht(P,BW)")):
           return "Rohre mit D >500 mm, für PA, PC rotierend: D > 150 mm"
        if((self.regel == "iso15614-1 (Schweißverfahrensprüfung für Stähle, Nickel und Nickelleg)" or self.regel == "iso15614-2 (Schweißverfahrensprüfung für Aluminium und seinen Legierungen)" or self.regel == "iso15614-5 (Schweißverfahrensprüfung für Titan, Zirkonium und ihren Leg)" or self.regel == "iso15614-10 (Schweißverfahrensprüfung - Trockenschweißen unter Überduck)") and (self.Stossart == "Stumpfnaht am Rohr (T,BW) mit voller Durchschweißung" or self.Stossart == "Rohrabzweigung für voll durchgeschweißte Verbindung(T,BW)" or self.Stossart =="Rohrabzweigung für Kehlnähte (T,FW)") and self.rohraussendurchmesser >25 and self.rohraussendurchmesser <=50):
               return "Geltungsbereich : D >= 25 mm"
        if((self.regel == "iso15614-1 (Schweißverfahrensprüfung für Stähle, Nickel und Nickelleg)" or self.regel == "iso15614-2 (Schweißverfahrensprüfung für Aluminium und seinen Legierungen)" or self.regel == "iso15614-5 (Schweißverfahrensprüfung für Titan, Zirkonium und ihren Leg)" or self.regel == "iso15614-10 (Schweißverfahrensprüfung - Trockenschweißen unter Überduck)")and (self.Stossart == "Stumpfnaht am Rohr (T,BW) mit voller Durchschweißung" or self.Stossart == "Rohrabzweigung für voll durchgeschweißte Verbindung(T,BW)" or self.Stossart =="Rohrabzweigung für Kehlnähte (T,FW)") and self.rohraussendurchmesser >50):
               return "Geltungsbereich : D >="+ str(0.5*self.rohraussendurchmesser)+"mm"
        if(self.regel == "iso15614-6 (Schweißverfahrensprüfung für Kupfer und seinen Legierungen)" and (self.Stossart == "T-Stoß [zwei Bleche] für kehlnähte (P,FW)" or self.Stossart =="Stumpfnaht am Blech(P,BW) mit voller Durchschweißung" or self.Stossart =="T-Stoß[zwei Bleche] für voll durchgeschweißte Stumpfnaht(P,BW)")):
               return "Die Qualifizierung für Bleche Schließt auch Rohre mit ein."
        if(self.regel == "iso15614-6 (Schweißverfahrensprüfung für Kupfer und seinen Legierungen)" and (self.Stossart == "Stumpfnaht am Rohr (T,BW) mit voller Durchschweißung" or self.Stossart == "Rohrabzweigung für voll durchgeschweißte Verbindung(T,BW)" or self.Stossart =="Rohrabzweigung für Kehlnähte (T,FW)")):
               return "Geltungsbereich: alles Rohre (siehe 9.3.2.4)"

        else:
           if((self.regel == "iso15614-1 (Schweißverfahrensprüfung für Stähle, Nickel und Nickelleg)" or self.regel == "iso15614-2 (Schweißverfahrensprüfung für Aluminium und seinen Legierungen)" or self.regel == "iso15614-5 (Schweißverfahrensprüfung für Titan, Zirkonium und ihren Leg)" or self.regel == "iso15614-10 (Schweißverfahrensprüfung - Trockenschweißen unter Überduck)") and (self.Stossart == "Stumpfnaht am Rohr (T,BW) mit voller Durchschweißung" or self.Stossart == "Rohrabzweigung für voll durchgeschweißte Verbindung(T,BW)" or self.Stossart =="Rohrabzweigung für Kehlnähte (T,FW)") and self.rohraussendurchmesser <=25):
               return "Geltungsbereich :"+" "+str(0.5*self.rohraussendurchmesser)+" "+"bis"+" "+str(2*self.rohraussendurchmesser)+"mm"

#

    def On_change_stossart2(self,Stossart):
        if((self.regel == "iso15614-1 (Schweißverfahrensprüfung für Stähle, Nickel und Nickelleg)" or self.regel =="iso15614-10 (Schweißverfahrensprüfung - Trockenschweißen unter Überduck)") and (self.Stossart == "T-Stoß [zwei Bleche] für kehlnähte (P,FW)" or self.Stossart == "Rohrabzweigung für Kehlnähte (T,FW)")):
            return "Geltungsbereich:Einlagig("+str(1.00*self.Kehlnahtdicke)+"mm);Mehrlagig(keine Einschränkung)"
        if(self.regel == "iso15614-2 (Schweißverfahrensprüfung für Aluminium und seinen Legierungen)" and (self.Stossart == "T-Stoß [zwei Bleche] für kehlnähte (P,FW)" or self.Stossart == "Rohrabzweigung für Kehlnähte (T,FW)") and self.Kehlnahtdicke <10):
            return "Geltungsbereich:"+str(0.75*self.Kehlnahtdicke)+" bis "+str(1.5*self.Kehlnahtdicke)+" mm"
        if(self.regel == "iso15614-2 (Schweißverfahrensprüfung für Aluminium und seinen Legierungen)" and (self.Stossart == "T-Stoß [zwei Bleche] für kehlnähte (P,FW)" or self.Stossart == "Rohrabzweigung für Kehlnähte (T,FW)") and self.Kehlnahtdicke >=10):
            return "Geltungsbereich: a>= 7.5 mm"
        if(self.regel == "iso15614-5 (Schweißverfahrensprüfung für Titan, Zirkonium und ihren Leg)" or self.regel =="iso15614-6 (Schweißverfahrensprüfung für Kupfer und seinen Legierungen)"):
            return "Geltungsbereich: Einlagig("+str(0.75*self.Kehlnahtdicke)+" bis "+str(1.5*self.Kehlnahtdicke)+"mm)"

#

    def On_change_stossart(self,Stossart):
       if(self.regel == "iso15614-1 (Schweißverfahrensprüfung für Stähle, Nickel und Nickelleg)" and (self.Stossart =="Stumpfnaht am Blech(P,BW) mit voller Durchschweißung" or self.Stossart =="Stumpfnaht am Rohr (T,BW) mit voller Durchschweißung" or self.Stossart =="T-Stoß(zwei Bleche) für voll durchgeschweißte Stumpfnaht(P,BW)" or self.Stossart =="Rohrabzweigung für voll durchgeschweißte Verbindung(T,BW)") and self.dicke_des_grundwerkstoff_value1 <=3):
            return "Geltungsbereich BW:Einlagig("+str(round(0.7*self.dicke_des_grundwerkstoff_value1,1))+"-"+str(round(1.3*self.dicke_des_grundwerkstoff_value1,1))+"mm); Merhrlagig("+str(0.7*self.dicke_des_grundwerkstoff_value1)+"-"+str(round(2.0*self.dicke_des_grundwerkstoff_value1,1))+"mm)"
       if(self.regel == "iso15614-1 (Schweißverfahrensprüfung für Stähle, Nickel und Nickelleg)" and (self.Stossart =="Stumpfnaht am Blech(P,BW) mit voller Durchschweißung" or self.Stossart =="Stumpfnaht am Rohr (T,BW) mit voller Durchschweißung" or self.Stossart =="T-Stoß(zwei Bleche) für voll durchgeschweißte Stumpfnaht(P,BW)" or self.Stossart =="Rohrabzweigung für voll durchgeschweißte Verbindung(T,BW)") and self.dicke_des_grundwerkstoff_value1 >6 and self.dicke_des_grundwerkstoff_value1 <=12 ):
            return "Geltungsbereich BW:Einlagig("+str(round(0.5*self.dicke_des_grundwerkstoff_value1,1))+"-"+str(round(1.3*self.dicke_des_grundwerkstoff_value1,1))+"mm); Merhrlagig(3,0-"+str(round(2.0*self.dicke_des_grundwerkstoff_value1,1))+"mm)"
       if(self.regel == "iso15614-1 (Schweißverfahrensprüfung für Stähle, Nickel und Nickelleg)" and (self.Stossart =="Stumpfnaht am Blech(P,BW) mit voller Durchschweißung" or self.Stossart =="Stumpfnaht am Rohr (T,BW) mit voller Durchschweißung" or self.Stossart =="T-Stoß(zwei Bleche) für voll durchgeschweißte Stumpfnaht(P,BW)" or self.Stossart =="Rohrabzweigung für voll durchgeschweißte Verbindung(T,BW)") and self.dicke_des_grundwerkstoff_value1 >12 and self.dicke_des_grundwerkstoff_value1 <=100 ):
            return "Geltungsbereich BW:Einlagig("+str(round(0.5*self.dicke_des_grundwerkstoff_value1,1))+"-"+str(round(1.1*self.dicke_des_grundwerkstoff_value1,1))+"mm); Merhrlagig("+str(round(0.5*self.dicke_des_grundwerkstoff_value1,1))+"-"+str(round(2.0*self.dicke_des_grundwerkstoff_value1,1))+"mm)"
       if(self.regel == "iso15614-1 (Schweißverfahrensprüfung für Stähle, Nickel und Nickelleg)" and (self.Stossart =="Stumpfnaht am Blech(P,BW) mit voller Durchschweißung" or self.Stossart =="Stumpfnaht am Rohr (T,BW) mit voller Durchschweißung" or self.Stossart =="T-Stoß(zwei Bleche) für voll durchgeschweißte Stumpfnaht(P,BW)" or self.Stossart =="Rohrabzweigung für voll durchgeschweißte Verbindung(T,BW)") and self.dicke_des_grundwerkstoff_value1 >100 ):
            return "Geltungsbereich BW:Einlagig(nicht anwendbar); Merhrlagig(50,0-"+str(round(2.0*self.dicke_des_grundwerkstoff_value1,1))+"mm)"
       if(self.regel == "iso15614-1 (Schweißverfahrensprüfung für Stähle, Nickel und Nickelleg)" and (self.Stossart =="Rohrabzweigung für Kehlnähte (T,FW)" or self.Stossart =="T-Stoß (zwei Bleche) für kehlnähte (P,FW)") and self.dicke_des_grundwerkstoff_value1 <=3):
            return "Geltungsbereich FW:"+str(round(0.7*self.dicke_des_grundwerkstoff_value1,1))+"bis"+str(round(2.0*self.dicke_des_grundwerkstoff_value1,1))+"mm"
       if(self.regel == "iso15614-1 (Schweißverfahrensprüfung für Stähle, Nickel und Nickelleg)" and (self.Stossart =="Rohrabzweigung für Kehlnähte (T,FW)" or self.Stossart =="T-Stoß (zwei Bleche) für kehlnähte (P,FW)") and self.dicke_des_grundwerkstoff_value1 >3 and self.dicke_des_grundwerkstoff_value1 <30):
            return "Geltungsbereich FW:"+str(round(0.5*self.dicke_des_grundwerkstoff_value1,1))+"bis"+str(round(2.0*self.dicke_des_grundwerkstoff_value1,1))+"mm"
       if(self.regel == "iso15614-1 (Schweißverfahrensprüfung für Stähle, Nickel und Nickelleg)" and (self.Stossart =="Rohrabzweigung für Kehlnähte (T,FW)" or self.Stossart =="T-Stoß (zwei Bleche) für kehlnähte (P,FW)") and self.dicke_des_grundwerkstoff_value1 >=30):
            return "Geltungsbereich FW: t >= 5mm"
       if(self.regel == "iso15614-2 (Schweißverfahrensprüfung für Aluminium und seinen Legierungen)" and (self.Stossart =="Stumpfnaht am Blech(P,BW) mit voller Durchschweißung" or self.Stossart =="Stumpfnaht am Rohr (T,BW) mit voller Durchschweißung" or self.Stossart =="T-Stoß(zwei Bleche) für voll durchgeschweißte Stumpfnaht(P,BW)" or self.Stossart =="Rohrabzweigung für voll durchgeschweißte Verbindung(T,BW)") and self.dicke_des_grundwerkstoff_value1 <=3):
            return "Geltungsbereich: "+str(round(0.5*self.dicke_des_grundwerkstoff_value1,1))+" "+"bis"+" "+str(round(2.0*self.dicke_des_grundwerkstoff_value1,1))+" mm (Einlagen-und Mehrlagentecknik)"
       if(self.regel == "iso15614-2 (Schweißverfahrensprüfung für Aluminium und seinen Legierungen)" and (self.Stossart =="Stumpfnaht am Blech(P,BW) mit voller Durchschweißung" or self.Stossart =="Stumpfnaht am Rohr (T,BW) mit voller Durchschweißung" or self.Stossart =="T-Stoß(zwei Bleche) für voll durchgeschweißte Stumpfnaht(P,BW)" or self.Stossart =="Rohrabzweigung für voll durchgeschweißte Verbindung(T,BW)") and self.dicke_des_grundwerkstoff_value1 >3 and self.dicke_des_grundwerkstoff_value1 <=20):
            return "Geltungsbereich: 3.0 bis"+" "+str(round(2.0*self.dicke_des_grundwerkstoff_value1,1))+" mm (Einlagen-und Mehrlagentecknik)"
       if(self.regel == "iso15614-2 (Schweißverfahrensprüfung für Aluminium und seinen Legierungen)" and (self.Stossart =="Stumpfnaht am Blech(P,BW) mit voller Durchschweißung" or self.Stossart =="Stumpfnaht am Rohr (T,BW) mit voller Durchschweißung" or self.Stossart =="T-Stoß(zwei Bleche) für voll durchgeschweißte Stumpfnaht(P,BW)" or self.Stossart =="Rohrabzweigung für voll durchgeschweißte Verbindung(T,BW)") and self.dicke_des_grundwerkstoff_value1 >20):
            return "Geltungsbereich: tw >= "+str(round(0.8*self.dicke_des_grundwerkstoff_value1,1))+" (Einlagen-und Mehrlagentecknik)"
       if(self.regel == "iso15614-5 (Schweißverfahrensprüfung für Titan, Zirkonium und ihren Leg)" and self.dicke_des_grundwerkstoff_value1 <=3):
            return "Geltungsbereich: Einlagig("+str(round(0.7*self.dicke_des_grundwerkstoff_value1,1))+"-"+str(round(1.5*self.dicke_des_grundwerkstoff_value1,1))+"mm); Mehrlagig("+str(round(0.7*self.dicke_des_grundwerkstoff_value1,1))+"-"+str(round(2.0*self.dicke_des_grundwerkstoff_value1,1))+"mm)"
       if(self.regel == "iso15614-5 (Schweißverfahrensprüfung für Titan, Zirkonium und ihren Leg)" and self.dicke_des_grundwerkstoff_value1 >3 and self.dicke_des_grundwerkstoff_value1<=12):
            return "Geltungsbereich: Einlagig("+str(round(0.7*self.dicke_des_grundwerkstoff_value1,1))+"-"+str(round(1.3*self.dicke_des_grundwerkstoff_value1,1))+"mm); Mehrlagig(3.0"+"-"+str(round(2.0*self.dicke_des_grundwerkstoff_value1,1))+"mm)"
       if(self.regel == "iso15614-5 (Schweißverfahrensprüfung für Titan, Zirkonium und ihren Leg)" and self.dicke_des_grundwerkstoff_value1 >12):
            return "Geltungsbereich: Einlagig("+str(round(0.7*self.dicke_des_grundwerkstoff_value1,1))+"-"+str(round(1.1*self.dicke_des_grundwerkstoff_value1,1))+"mm); Mehrlagig("+str(round(0.5*self.dicke_des_grundwerkstoff_value1,1))+"-"+str(round(2.0*self.dicke_des_grundwerkstoff_value1,1))+"mm)"
       if(self.regel == "iso15614-6 (Schweißverfahrensprüfung für Kupfer und seinen Legierungen)" and self.dicke_des_grundwerkstoff_value1 <=3):
            return "Geltungsbereich: "+str(round(0.5*self.dicke_des_grundwerkstoff_value1,1))+" bis "+str(round(2.0*self.dicke_des_grundwerkstoff_value1,1))+"mm"
       if(self.regel == "iso15614-6 (Schweißverfahrensprüfung für Kupfer und seinen Legierungen)" and self.dicke_des_grundwerkstoff_value1 >3 and self.dicke_des_grundwerkstoff_value1 <=20):
            return "Geltungsbereich: 3.0 bis "+ str(round(2.0*self.dicke_des_grundwerkstoff_value1,1))+"mm"
       if(self.regel == "iso15614-6 (Schweißverfahrensprüfung für Kupfer und seinen Legierungen)" and self.dicke_des_grundwerkstoff_value1 >20):
            return "Geltungsbereich: t >= "+ str(round(0.8*self.dicke_des_grundwerkstoff_value1,1))
       if(self.regel == "iso15614-10 (Schweißverfahrensprüfung - Trockenschweißen unter Überduck)" and self.dicke_des_grundwerkstoff_value1 <=3):
            return "Geltungsbereich FW: "+str(round(0.7*self.dicke_des_grundwerkstoff_value1,1))+" bis "+str(round(2.0*self.dicke_des_grundwerkstoff_value1,1))+"mm"
       if(self.regel == "iso15614-10 (Schweißverfahrensprüfung - Trockenschweißen unter Überduck)" and self.dicke_des_grundwerkstoff_value1>3 and self.dicke_des_grundwerkstoff_value1 <=6):
            return "Geltungsbereich FW: 3.0 bis "+str(round(2.0*self.dicke_des_grundwerkstoff_value1,1))+"mm"
       if(self.regel == "iso15614-10 (Schweißverfahrensprüfung - Trockenschweißen unter Überduck)" and self.dicke_des_grundwerkstoff_value1>6 and self.dicke_des_grundwerkstoff_value1 <30):
            return "Geltungsbereich FW: "+str(round(0.5*self.dicke_des_grundwerkstoff_value1,1))+" bis "+str(round(2.0*self.dicke_des_grundwerkstoff_value1,1))+" mm"
       if(self.regel == "iso15614-10 (Schweißverfahrensprüfung - Trockenschweißen unter Überduck)" and self.dicke_des_grundwerkstoff_value1>=30):
            return "Geltungsbereich FW: t>= 5 mm"

       else:
         if(self.regel == "iso15614-1 (Schweißverfahrensprüfung für Stähle, Nickel und Nickelleg)" and (self.Stossart =="Stumpfnaht am Blech(P,BW) mit voller Durchschweißung" or self.Stossart =="Stumpfnaht am Rohr (T,BW) mit voller Durchschweißung" or self.Stossart =="T-Stoß(zwei Bleche) für voll durchgeschweißte Stumpfnaht(P,BW)" or self.Stossart =="Rohrabzweigung für voll durchgeschweißte Verbindung(T,BW)") and self.dicke_des_grundwerkstoff_value1 >3 and self.dicke_des_grundwerkstoff_value1 <=6 ):
            return "Geltungsbereich BW:Einlagig(3-"+str(round(1.3*self.dicke_des_grundwerkstoff_value1,1))+"mm); Merhrlagig(3-"+str(round(2.0*self.dicke_des_grundwerkstoff_value1,1))+"mm)"

    def On_change_grund1(self,grundwerkstoffe):
         return "Gruppe "+self.grundwerkstoffe.Werkstoffgruppe

    def On_change_grund2(self,grundwerkstoffe1):
         return "Gruppe "+self.grundwerkstoffe1.Werkstoffgruppe

    def On_change_grund3(self,grundwerkstoffe):
         return self.grundwerkstoffe.Bezeichnung

    def On_change_grund4(self,grundwerkstoffe1):
         return self.grundwerkstoffe1.Bezeichnung

    def On_change_grund5(self,grundwerkstoffe):
         return self.grundwerkstoffe.Nummer

    def On_change_grund6(self,grundwerkstoffe1):
         return self.grundwerkstoffe1.Nummer



    def On_change_prufumaux(self,prufumfang2):
         return self.prufumfang2


    def On_change_prufumfang1(self,prufumfang1):
         if(len(tab_prufumfang2) == 0 and self.prufumfang1 != "Löschen" ):
            tab_prufumfang2.append(self.prufumfang1)
            return  tab_prufumfang2
         if(len(tab_prufumfang2) > 0 and tab_prufumfang2[len(tab_prufumfang2) - 1] == self.prufumfang1):
            return  tab_prufumfang2
         if(len(tab_prufumfang2) > 0 and  self.prufumfang1 == "Löschen"):
            del tab_prufumfang2[len(tab_prufumfang2) - 1]
            return tab_prufumfang2
         else:
           if(len(tab_prufumfang2) > 0 and tab_prufumfang2[len(tab_prufumfang2) - 1] != self.prufumfang1 and self.prufumfang1 != "Löschen"):
            tab_prufumfang2.append(self.prufumfang1)
            return  tab_prufumfang2



    def On_change_schweissprocess(self,schweißprocess):
       if(self.schweißprocess == "111  Lichtbogenhandschweißen"):
          return "Lichtbogenhandschweißen (E)"
       if(self.schweißprocess == "111/135 Wurzel E, Auffüllen mit MAG (Stahl)"):
          return "Wurzel E, Auffüllen mit MAG (Stahl)(E/MAG)"
       if(self.schweißprocess == "112 Schwerkraft-Lichtbogenschweißen"):
          return "Schwerkraft-Lichtbogenschweißen (SK)"
       if(self.schweißprocess == "114 Metall-Lichtbogenschweißen mit Fülldrahtelektrode ohne Schutzgas"):
          return "Metall-Lichtbogenschweißen mit Fülldrahtelektrode ohne Schutzgas (MF)"
       if(self.schweißprocess == "12 Unterpulverschweißen"):
          return "Unterpulverschweißen (UP)"
       if(self.schweißprocess == "121 Unterpulverschweißen mit Massivdrahtelektrode"):
          return "Unterpulverschweißen mit Massivdrahtelektrode (UP)"
       if(self.schweißprocess == "122 Unterpulverschweißen mit Massivbandelektrode"):
          return "Unterpulverschweißen mit Massivbandelektrode (UP)"
       if(self.schweißprocess == "124 Unterpulverschweißen mit Metallpulverzusatz"):
          return "Unterpulverschweißen mit Metallpulverzusatz (UP)"
       if(self.schweißprocess == "125 Unterpulverschweißen mit Fülldrahtelektrode"):
          return "Unterpulverschweißen mit Fülldrahtelektrode (UP)"
       if(self.schweißprocess == "126 Unterpulverschweißen mit Füllbandelektrode"):
          return "Unterpulverschweißen mit Füllbandelektrode (UP)"
       if(self.schweißprocess == "131 Metall-Inertgasschweißen mit Massivdrahtelektrode"):
          return "Metall-Inertgasschweißen mit Massivdrahtelektrode (MIG)"
       if(self.schweißprocess == "132 Metall-Inertgasschweißen mit schweißpulvergefüllter Drahtelektrode"):
          return "Metall-Inertgasschweißen mit schweißpulvergefüllter Drahtelektrode(MIG)"
       if(self.schweißprocess == "133 Metall-Inertgasschweißen mit metallpulvergefüllter Drahtelektrode"):
          return "Metall-Inertgasschweißen mit metallpulvergefüllter Drahtelektrode (MIG)"
       if(self.schweißprocess == "135 Metall-Aktivgasschweißen mit Massivdrahtelektrode"):
          return "Metall-Aktivgasschweißen mit Massivdrahtelektrode(MAG)"
       if(self.schweißprocess == "135/111 Wurzel MAG, Auffüllen mit  E (Stahl)"):
          return "Wurzel MAG, Auffüllen mit  E (Stahl)(MAG/E)"
       if(self.schweißprocess == "135/121 Wurzel MAG, Auffüllen mit  UP (Stahl)"):
          return "Wurzel MAG, Auffüllen mit UP (Stahl)(MAG/UP)"
       if(self.schweißprocess == "136 Metall-Aktivgasschweißen mit schweißpulvergefüllter Drahtelektrode"):
          return "Metall-Aktivgasschweißen mit schweißpulvergefüllter Drahtelektrode (MAG)"
       if(self.schweißprocess == "136/121 Wurzel MAG, Auffüllen mit  UP (Stahl)"):
          return "Wurzel MAG, Auffüllen mit  UP (Stahl)"
       if(self.schweißprocess == "138 Metall-Aktivgasschweißen mit metallpulvergefüllter Drahtelektrode"):
          return "Metall-Aktivgasschweißen mit metallpulvergefüllter Drahtelektrode"
       if(self.schweißprocess == "141 Wolfram-Inertgasschweißen mit Massivdraht- oder Massivstabzusatz"):
          return "Wolfram-Inertgasschweißen mit Massivdraht- oder Massivstabzusatz"
       if(self.schweißprocess == "141/111 Wurzel WIG, Auffüllen mit  E (Stahl, Cu, Ni)"):
          return "Wurzel WIG, Auffüllen mit  E (Stahl, Cu, Ni)"
       if(self.schweißprocess == "141/121 Wurzel WIG, Auffüllen mit  UP (Stahl, Ni)"):
          return "Wurzel WIG, Auffüllen mit  UP (Stahl, Ni)"
       if(self.schweißprocess == "141/131 Wurzel WIG, Auffüllen mit  MIG (Al, Cu, Ni, Ti)"):
          return "Wurzel WIG, Auffüllen mit  MIG (Al, Cu, Ni, Ti)(WIG/MIG)"
       if(self.schweißprocess == "141/135 Wurzel WIG, Auffüllen mit  MAG (Stahl, Ni)"):
          return "Wurzel WIG, Auffüllen mit  MAG (Stahl, Ni)(WIG/MAG)"
       if(self.schweißprocess == "141/136 Wurzel WIG, Auffüllen mit  MAG (Stahl)"):
          return "Wurzel WIG, Auffüllen mit  MAG (Stahl)(WIG/MAG)"
       if(self.schweißprocess == "142 Wolfram-Inertgasschweißen ohne Schweißzusatz"):
          return "Wolfram-Inertgasschweißen ohne Schweißzusatz (WIG)"
       if(self.schweißprocess == "143 Wolfram-Inertgasschweißen mit Fülldraht- oder Füllstabzusatz"):
          return "Wolfram-Inertgasschweißen mit Fülldraht- oder Füllstabzusatz (WIG)"
       if(self.schweißprocess == "145 WIG-Schweißen mit reduzierenden Gasanteilen und Massivzusatz(Draht/Stab)"):
          return "WIG-Schweißen mit reduzierenden Gasanteilen und Massivzusatz(Draht/Stab)"
       if(self.schweißprocess == "146 WIG-Schweißen mit reduzierenden Gasanteilen und Füllzusatz(Draht/Stab)"):
          return "WIG-Schweißen mit reduzierenden Gasanteilen und Füllzusatz(Draht/Stab)"
       if(self.schweißprocess == "147 Wolfram-Schutzgasschweißen mit aktiven Gesanteilen im inerten Schutzgas"):
          return "Wolfram-Schutzgasschweißen mit aktiven Gesanteilen im inerten Schutzgas"
       if(self.schweißprocess == "15 Plasmaschweißen"):
          return "Plasmaschweißen (WPL)"
       if(self.schweißprocess == "151 Plasma-Metall-Inertgasschweißen"):
          return "Plasma-Metall-Inertgasschweißen"
       if(self.schweißprocess == "152 Pulver-Plasmalichtbogenschweißen"):
          return "Pulver-Plasmalichtbogenschweißen"
       if(self.schweißprocess == "311 Gasschweißen mit Sauerstoff-Acetylen-Flamme"):
          return "Gasschweißen mit Sauerstoff-Acetylen-Flamme"
       if(self.schweißprocess == "312 Gasschweißen mit Sauerstoff-Propan-Flamme"):
          return "Gasschweißen mit Sauerstoff-Propan-Flamme"
       if(self.schweißprocess == "313 asschweißen mit Sauerstoff-Wasserstoff-Flamme"):
          return "Gasschweißen mit Sauerstoff-Wasserstoff-Flamme"

       else:
         if(self.schweißprocess == "111/121 Wurzel E, Auffüllen mit UP (Stahl)"):
           return "Wurzel E, Auffüllen mit UP (Stahl)(E/UP)"


    def get_rec_name(self,hersteller):
        return self.hersteller

#Classes for print WPQR zertifikat
# class view
class PrintISOWPQRStart(ModelView):
    'Print START WPQR'
    __name__ = 'party.print_isowpqr.start'
    zertifikat = fields.Many2One('party.wpqr', 'Zertifikat', required=True)

#Wizard
class PrintWPQR(Wizard):
    'Print ISOWPQR'
    __name__ = 'party.print_isowpqr'
    start = StateView('party.print_isowpqr.start',
        'welding_certification.print_isowpqr_cert_start_view_form', [
            Button('Cancel', 'end', 'tryton-cancel'),
            Button('Drucken', 'print_', 'tryton-print', default=True),
            ])
    print_ = StateReport('welding_certification.party.iso_wpqr_report')
    def do_print_(self, action):
        data = {
            'zertifikat': self.start.zertifikat.id,
            }
        return action, data

#Report
class ISOWPQRreport(Report):
    __name__ = 'welding_certification.party.iso_wpqr_report'


    @classmethod
    def _get_records(cls, ids, model, data):
        Move = Pool().get('party.wpqr')

        clause = [

            ]


    @classmethod
    def get_context(cls, records, data):
        report_context = super(ISOWPQRreport, cls).get_context(records, data)

        Zertifikat = Pool().get('party.wpqr')

        zertifikat = Zertifikat(data['zertifikat'])

        report_context['zertifikat'] = zertifikat
        report_context['wpqr'] = zertifikat.wpqr
        report_context['hersteller'] = zertifikat.hersteller
        report_context['Anschrift'] = zertifikat.anschrift
        report_context['wpqr_nr'] = zertifikat.hersteller
        report_context['prufer_prufstelle'] = zertifikat.anschrift
        report_context['beleg_nr'] = zertifikat.beleg_nr
        report_context['zertifikat'] = zertifikat.auftrag_nr
        report_context['regel'] = zertifikat.regel
        report_context['datum_schweissen'] = zertifikat.datum_schweissen
        report_context['schweißprocess'] = zertifikat.schweißprocess
        report_context['Stossart'] = zertifikat.Stossart
        report_context['Einlagig'] = zertifikat.Einlagig
        report_context['nahteinzelheiten'] = zertifikat.schweiss_nahteinzelheiten
        report_context['grundwerkstoffe'] = zertifikat.grundwerkstoffe
        report_context['grundwerkstoffe1'] = zertifikat.grundwerkstoffe1
        report_context['gruppen1'] = zertifikat.gruppen1
        report_context['gruppen2'] = zertifikat.gruppen2
        report_context['bezeich1'] = zertifikat.bezeich1
        report_context['bezeich2'] = zertifikat.bezeich2
        report_context['nummer1'] = zertifikat.nummer1
        report_context['nummer2'] = zertifikat.nummer2
        report_context['dicke_des_grundwerkstoff'] = zertifikat.dicke_des_grundwerkstoff
        report_context['dicke_des_grundwerkstoff_value1'] = zertifikat.dicke_des_grundwerkstoff_value1
        report_context['dicke_des_schweissgutes'] = zertifikat.dicke_des_schweissgutes
        report_context['prozess1'] = zertifikat.prozess1
        report_context['prozess2'] = zertifikat.prozess2
        report_context['Kehlnahtdicke'] = zertifikat.Kehlnahtdicke
        report_context['Kehlnahtdicke_geltungs'] = zertifikat.Kehlnahtdicke_geltungs
        report_context['rohraussendurchmesser'] = zertifikat.rohraussendurchmesser
        report_context['rohrauss_geltungs'] = zertifikat.rohrauss_geltungs
        report_context['zusatzwerkstoff'] = zertifikat.zusatzwerkstoff.Bezeichnung
        report_context['zusatzwerkstoff2'] = zertifikat.zusatzwerkstoff2.Bezeichnung
        report_context['fabrikat'] = zertifikat.fabrikat
        report_context['fabrikat2'] = zertifikat.fabrikat2
        report_context['o1'] = zertifikat.o1
        report_context['o2'] = zertifikat.o2
        report_context['stromart_polung'] = zertifikat.stromart_polung
        report_context['stromart_polung2'] = zertifikat.stromart_polung2
        report_context['schutzgas'] = zertifikat.pulver
        report_context['schutzgas1'] = zertifikat.pulver1
        report_context['Formiergases'] = zertifikat.formiergases
        report_context['wasserstoffarmgluhen'] = zertifikat.wasserstoffarmgluhen
        report_context['zwischenlagentemperatur'] = zertifikat.zwischenlagentemperatur
        report_context['vorwarmungtemperatur'] = zertifikat.vorwarmungtemperatur
        report_context['warmenachbehandlung'] = zertifikat.warmenachbehandlung
        report_context['sonstige'] = zertifikat.sonstige
        report_context['tropfenuebergande'] = zertifikat.tropfenuebergande
        report_context['warmeeinbringung'] = zertifikat.warmeeinbringung
        report_context['schweissposition'] = zertifikat.schweissposition
        report_context['schweissgeltung'] = zertifikat.schweissgeltung
        report_context['datum_ausstellung'] = zertifikat.datum_ausstellung
        return report_context
#

class wps(DeactivableMixin, ModelView, ModelSQL, MultiValueMixin):
    'Party WPS'
    __name__ = 'party.wps'
    wpqr=fields.Char('wpqr')
    Geigneter_Schweisser = fields.Char('Geigneter Schweißer')
    z_b = fields.Char('z.B : Pendeh(max, Raupenbreite)')
    Amplit = fields.Char('(Amplit,Frequ, Verweilzeit)')
    Einzelheiten_pulsschweissen = fields.Char('Einzelheiten für das Pulsschweißen')
    Amplit_1 = fields.Char('(Amplit,Frequ, Verweilzeit)')
    Amplit_2 = fields.Char('(Amplit,Frequ, Verweilzeit)')
    Stromkontakt = fields.Char('Stromkontaktrohrabstand[mm]')
    Einzelheiten_plasmaschweissen = fields.Char('Einzelheiten plasmaschweißen')
    Brenne = fields.Char('Brenneranstellwinkel [Grad]')
    naht_nr_nach=fields.Char('Naht-Nr. Nach EN 15085-3')
    separation = fields.Char('Schweißplan')
    Gestaltung = fields.Char('Gestaltung der Verbindung')
    Schweissfolgen = fields.Char('Schweißvolgen')
    title1=fields.Char('*****************************************************************************************')
    weitere_info=fields.Char('Weitere Informationen')
    Sonderforschriften_info = fields.Char('SonderVorschriften für Trocknung')
    Schutzgas_info = fields.Char('Schutzgas')
    Schutzgas_info1 = fields.Char('Schutzgas-/Schweißpulverbezeichnung')
    Wurzelschutz_info = fields.Char('Wurzelschutz')
    Gasdurchflussmenge = fields.Char('Gasdurchflussmenge [l/min]')
    Wolframelektrodenar_info = fields.Char('Wolframelektrodenart/-durchmesser')
    Einzelheiten_info = fields.Char('Einzelheiten über Ausfugen/Badesicherung')
    Vorwaermtemperatur_info = fields.Char('Vorwärmtemperatur')
    Zwichenlagetemperatur_info = fields.Char('Zwichenlagetemperatur')
    bereich=fields.Char('Bereich')
    Wasserstoffarm_info = fields.Char('Wasserstoffarm glühen')
    Haltetemperatur = fields.Char('Haltetemperatur')
    Waermenachbehandlung = fields.Char('Wärmenachbehandlung')
    Aufheiz = fields.Char('Aufheiz- und Abkülungsarten')
    Zeit = fields.Char('Zeit, Temperatur, Verfahren')
    SZ1=fields.Char('SZ1')
    SZ1_Werkstoffgruppe=fields.Char('SZ1_Werkstoffgruppe')
    SZ1_Handelsname=fields.Char('SZ1_Handelsname')
    SZ1_Bemerkung=fields.Char('SZ1_Bemerkung')
    space=fields.Char('-')
    SZ2=fields.Char('SZ2')
    SZ2_Werkstoffgruppe=fields.Char('SZ2_Werkstoffgruppe')
    SZ2_Handelsname=fields.Char('SZ2_Handelsname')
    SZ2_Bemerkung=fields.Char('SZ2_Bemerkung')
    SZ3=fields.Char('SZ3')
    SZ3_Werkstoffgruppe=fields.Char('SZ3_Werkstoffgruppe')
    SZ3_Handelsname=fields.Char('SZ3_Handelsname')
    SZ3_Bemerkung=fields.Char('SZ3_Bemerkung')

    WIG_E_UP_0 = fields.Char('WIG/E/UP')
    FM_0 = fields.Char('FM?')
    Fabrikat_0 = fields.Char('Fabrikat')
    Zulassung = fields.Char('Zulassung, Bemerkungen')
    szi_1 = fields.Many2One('welding.szi_data', 'SZ1=')
    szi_2 = fields.Many2One('welding.szi_data', 'SZ2=')
    szi_3 = fields.Many2One('welding.szi_data', 'SZ3=')

    WIG_E_UP = fields.Function(fields.Char('WIG/E/UP'), 'on_change_sz1')
    FM = fields.Function(fields.Char('FM?'),'on_change_sz1FM')
    Fabrikat = fields.Function(fields.Char('Fabrikat'),'on_change_sz1Fabrikat')
    Bemerkung = fields.Char('Zulassung, Bemerkungen')

    WIG_E_UP_1 = fields.Function(fields.Char('WIG/E/UP'), 'on_change_sz2')
    FM_1 = fields.Function(fields.Char('FM?'),'on_change_sz2FM')
    Fabrikat_1 = fields.Function(fields.Char('Fabrikat'),'on_change_sz2Fabrikat')
    Bemerkung_1 = fields.Char('Zulassung, Bemerkungen')

    WIG_E_UP_2 = fields.Function(fields.Char('WIG/E/UP'), 'on_change_sz3')
    FM_2 = fields.Function(fields.Char('FM?'),'on_change_sz3FM')
    Fabrikat_2 = fields.Function(fields.Char('Fabrikat'),'on_change_sz3Fabrikat')
    Bemerkung_2 = fields.Char('Zulassung, Bemerkungen')


    bild_name =fields.Function(fields.Char("Bild name"), 'on_change_skizze_1')
    rechts_bild_name = fields.Selection('on_change_bild_skizze','rechts_bild_name', readonly = False,)
    Empfehlumg =fields.Function(fields.Char("Empfehlung"), 'on_change_skizze_2')
    Schweisszusatz=fields.Char('Schweißzusatz')
    Werkstoffgruppetext=fields.Char('Werkstoffgruppe')
    Handelsnametext=fields.Char('Handelsname')
    Zulassung_Bemerkung=fields.Char('Zulassung /Bemerkung')
    Einzelheiten=fields.Text('Einzelheiten der Fügenvorbereitung')
    intern_nr=fields.Char('Intern-Nr')
    formular = fields.Selection([
        ('WPS-1S', 'WPS-1S|EN ISO 15609-1, Lichtbogenschw'),
        ('WPS-31', 'WPS-31|EN ISO 15609-2, Gasschweißen'),
        ('ASME', 'ASME|BPVC, Section IX, QW-482'),
    ], 'Formular', readonly = False,
        )
    

    erzeugniss = fields.Many2One('welding.erzeugnis', 'Erzeugnis')
    Bilds = fields.Many2One('welding.bilds_properties', 'Skizze')
    Bilds_1 = fields.Many2One('welding.bilds_properties', 'Naht-Nr. nach EN 15085-3')
    wpqnr = fields.Many2One('welding.wpqr_nr', 'WPQR-Nr')
    clss = fields.Many2One('welding.class', 'Class')
    prozess = fields.Many2One('welding.process_iso4063', 'Prozess:ISO 4063-',required=True)
    tropfenubergang = fields.Many2One('welding.tropfenuebergang', 'Tropfenübergang')
    sweissposition = fields.Many2One('welding.schweissposition_iso6947', 'Schweißposition ISO 6947-',required=True)
    sweisszusatz = fields.Many2One('welding.schweißzusatz', 'Schweißzusatz')
    liste_gase = fields.Many2One('welding.list_gas_mischgase', 'Liste Gase und mischgaze sortie')
    liste_gase1 = fields.Many2One('welding.list_gas_mischgase', 'Liste Gase und mischgaze sortie')
    liste_gase2 = fields.Many2One('welding.list_gas_mischgase', 'Liste Gase und mischgaze sortie')
    liste_gase3 = fields.Many2One('welding.list_gas_mischgase', 'Liste Gase und mischgaze sortie')
    grundwerkstoffe = fields.Many2One('welding.grundwerkstoff_properties', 'Grundwerkstoffe 1',required=True)
    grundwerkstoffe2 = fields.Many2One('welding.grundwerkstoff_properties', 'Grundwerkstoffe 2',required=True)
    wolframelektrodenart = fields.Many2One('party.wolframelektrodenart', 'Wolframelektrodenart/durchmesser')
    wolframelektrodenart2 = fields.Many2One('party.wolframelektrodenart_2', 'Wolframelektrodenart/durchmesser')
    Fugenbearbeitung1 = fields.Selection([
        ('Bush or Grind as necessary', 'Bush or Grind as necessary'),
        ('Nahtvorbereitung durch Laserschnitt', 'Nahtvorbereitung durch Laserschnitt'),
        ('Plasmaschneiden', 'Plasmaschneiden'),
        ('RP-Schweißmaschine', 'RP-Schweißmaschine'),
    ], 'Fugenbearbeitung', readonly = False,
        )
    Mechanisierungsgrad = fields.Selection([
        ('manuell', 'manuell'),
        ('teilmechanisch', 'teilmechanisch'),
        ('vollmechanisch', 'vollmechanisch'),
        ('automatisch', 'automatisch'),
    ], 'Mechanisierungsgrad', readonly = False,
        ) 
    Produktform= fields.Selection([
        ('P/P', 'P/P (Blech/Blech)'),
        ('T/P', 'T/P (Rohr/Blech)'),
        ('T/T', 'T/T (Rohr/Rohr)'),
    ], 'Produktform', readonly = False,
        )
    Nahtart= fields.Selection([
        ('BW', 'BW (Stumpfnaht/butt weld)'),
        ('FW', 'FW (Kehlnaht/fillet weld)'),
        ('CW', 'CW (Ecknaht/ corner weld)'),
        ('AS', 'AS Auftragschweißen'),
    ], 'Nahtart', readonly = False,
        ) 


    Nahtform = fields.Selection([
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
    ], 'Nahtform', readonly = False,
        )
    wps_nr = fields.Char('WPS-Nr')
    Naht_nr = fields.Char('Naht-Nr')
    Revision = fields.Float('Revision')
    Erzeugnis = fields.Char('Erzeugnis')
    Projekt_Nr = fields.Char('Projekt-Nr')
    Zeichn_Nr = fields.Char('Zeichn-Nr')
    Ort = fields.Char('Ort')
    prufer_oder_prufsteller = fields.Char('Prüfer oder Prüfstelle') 
    WPQR_Nrr = fields.Char('WPQR-Nr')
    Beleg_Nr = fields.Function(fields.Char("Beleg-Nr"), 'on_change_andereopts')
    Herstellere = fields.Char('Hersteller')
    erstellt_Geandert_von = fields.Char('Erstellt/ Geändert von')
    gepruft_Freigegeben_von = fields.Char('Geprüft/ Freigegeben von')
    schweissanweisung = fields.Char('Schweißanweisung')
    art_der_Vorbereitung = fields.Char('Art der Vorbereitung')
    art_der_Reinigung = fields.Char('Art der Reinigung')
    grundwerkstoff = fields.Char('Grundwerkstoff')
    Verbindungsart = fields.Char('Verbindungsart')
    Gruppen_Nr = fields.Char('Gruppen Nr.')
    Schweissprozess = fields.Char('Schweißprozess')
    Werkstuckdicke = fields.Float('Werkstückdicke t[mm]')
    Werkstuckdicke_1 = fields.Integer('Werkstückdicke t[mm]')
    Werkstuckdicke_2 = fields.Integer('/')
    Werkstuckdicke_2_ = fields.Integer('/')
    Aussendurchmesser = fields.Float('Außendurchmesser D[mm]')
    Aussendurchmesser_1 = fields.Integer('Außendurchmesser D[mm]')
    Aussendurchmesser_2 = fields.Float('/')
    Aussendurchmesser_2_ = fields.Integer('/')
    Kehlnahtdicke = fields.Float('Kehlnahtdicke a [mm]')
    Gestaltung_der_Verbindung = fields.Text('Gestaltung der Verbindung')
    Schweissfolge = fields.Text('Schweißfolge')
    Abmessungen_des_Zusatz_werkstoffes = fields.Float("Abmessungen des Zusatz werkstoffes in mm")
    Strom = fields.Float("Strom (A)")
    Spannung = fields.Float("Spannung (V)")
    Vorschubgeschw = fields.Float("Vorschubgeschw mm/min")
    Waermeeinbringung = fields.Float("Wärmeeinbringung kJ / mm")
    photo = fields.Binary("Photo")
    photo1 = fields.Binary("Photo1")

    photo_gestaltung = fields.Binary("Photo3")
    Billds = fields.Many2One('welding.bilds_properties', 'Skizze')
    @classmethod
    def __setup__(cls):
        super(wps, cls).__setup__()
        cls._buttons.update({
               'upload_cls': {
                    'depends': ['state'],
                    },
                })
    @classmethod
    @ModelView.button_action('welding_certification.wizard_upload')
    def upload_cls(cls, party):
        pass

    def get_rec_name(self,wps_nr):
        aux ="WPS-ID-00"
        ret_val = aux+str(self.wps_nr)
        return ret_val


    def on_change_sz1Fabrikat(self,szi_1):
        if(self.szi_1  is not None ):
           rett_val = self.szi_1.Handelsname
        else:
           rett_val = " "
        return rett_val

    def on_change_sz1FM(self,szi_1):
        if(self.szi_1  is not None):
          rett_val = self.szi_1.GRP_SZW
        else :
          rett_val = " "
        return rett_val

    def on_change_sz2(self,szi_2):
        if(self.szi_2 is not None):
          rett_val = self.szi_2.Bezeichnung
        else:
          rett_val = " "
        return rett_val
    def on_change_sz2FM(self,szi_2):
        if(self.szi_2 is not None):
          rett_val = self.szi_2.GRP_SZW
        else:
          rett_val = " "
        return rett_val
    def on_change_sz2Fabrikat(self,szi_2):
        if(self.szi_2 is not None):
          rett_val = self.szi_2.Handelsname
        else:
          rett_val = " "
        return rett_val

    def on_change_skizze_1(self,Billds):
        value_bild = self.Billds.name
        return value_bild
    def on_change_skizze_2(self,Produktform):
        val_1 = self.Produktform
        if(val_1 == "P/P"):
            val_1 ="PP"
        if(val_1 == "T/P"):
            val_1 ="TP"
        else:
            if(val_1 == "T/T"):
               val_1 ="TT"
        val_2 = self.Nahtart
        val_3 = self.sweissposition.Code
        value_empf = val_1+val_2+val_3
        return value_empf


    @fields.depends('rechts_bild_name', 'bild_name')
    def on_change_bild_skizze(self):
        tabb=[]
        if(self.bild_name == "_i_n"):
          tabb.append(("ppbwpc1i", "ppbwpc1i"))
          return tabb
        else:
          tabb.append(("ppbwpc1v", "ppbwpc1v"))
          return tabb
    def on_change_sz1(self,szi_1):
        if(self.szi_1 is not None):
          rett_val = self.szi_1.Bezeichnung
        else:
          rett_val = " "
        return rett_val
    def on_change_sz3(self,szi_3):
        if(self.szi_3 is not None):
          rett_val = self.szi_3.Bezeichnung
        else:
          rett_val = " "
        return rett_val
    def on_change_sz3FM(self,szi_3):
        if(self.szi_3 is not None):
          rett_val = self.szi_3.GRP_SZW
        else:
          rett_val = " "
        return rett_val
    def on_change_sz3Fabrikat(self,szi_3):
        if(self.szi_3 is not None):
          rett_val = self.szi_3.Handelsname
        else:
          rett_val = " "
        return rett_val



    def on_change_andereopts(self,Nahtart):
        fix_val = "ISO 15609-1"
        val_1 = self.prozess.Code1
        val_2 = self.Produktform
        val_3 = self.Nahtart
        val_4 = self.grundwerkstoffe.Werkstoffgruppe
        val_5 = self.grundwerkstoffe2.Werkstoffgruppe
        sep = "/"
        space = " "
        if(val_4 == val_5):
         val_45 = val_4
        else:
         val_45 = str(val_4)+"/"+str(val_5)
        val_6 = self.Werkstuckdicke_1
        val_7 = self.Aussendurchmesser_1
        val_8 = self.sweissposition.Code
        ret_val = fix_val+space+val_1+space+val_2+space+val_3+space+val_45+space+"t"+str(val_6)+space+"D"+str(val_7)+space+val_8
        return ret_val


    @classmethod
    def convert_photo(cls, data):
      if data and Image:
        image = Image.open(BytesIO(data))
        image.thumbnail((200, 200), Image.ANTIALIAS)
        data = BytesIO()
        image.save(data, image.format)
        data = fields.Binary.cast(data.getvalue())
      return data
    def on_change_Bildd(self,Billds):
        value_bild = self.Billds.Bild
        return value_bild
class uploadxlsISO96061(Wizard):
    'upload xls'
    __name__ = 'party.uploadxml'
    start = StateView('party.uplod_xls.start',
        'welding_certification.uplod_xls_start_view_form', [
            Button('Abbrechen ', 'end', 'tryton-cancel'),
            Button('Aktualisieren', 'uplod', 'tryton-ok', default=True),
            ])
    uplod = StateTransition()
    def transition_uplod(self):
        #Recuprer mon fichier
        #my_file = self.start.file
        #name_file = self.start.filename
        name_file = "/home/msaidi/part_szi.csv"
        aux ='"'+'Hersteller'+'"'+','+'"'+'Handelsname'+'"'+','+'"'+'norm'+'"'+','+'"'+'norm_eint'+'"'+','+'"'+'Bezeichnung'+'"'+','+'"'+'wnummer'+'"'+','+'"'+'GRP_SZW'+'"'+','+'"'+'norm_asme'+'"'+','+'"'+'bezeich_asme'+'"'+','+'"'+'f_nr'+'"'+','+'"'+'a_nr'+'"'+','+'"'+'Eignung'+'"'

        conn = psycopg2.connect("host=localhost dbname=tr-database user=postgres password=postgres")
        cur = conn.cursor()
        #with open(my_file, 'r') as f:
         #  reader = csv.reader(f)
           #next(reader) # Skip the header row.
        cur.execute(
           "ALTER TABLE party_wps DROP COLUMN szi_1;"
             )
        cur.execute(
           "ALTER TABLE party_wps DROP COLUMN szi_2;"
             )
        cur.execute(
           "ALTER TABLE party_wps DROP COLUMN szi_3;"
             )

        cur.execute(
        "DELETE FROM party_szi;"
         )

        cur.execute(
         "COPY party_szi("+aux+") FROM "+"'"+ name_file +"'"+" WITH CSV HEADER;"
         )
        cur.execute(
           "ALTER TABLE party_wps ADD COLUMN szi_1 integer;"
             )
        cur.execute(
           "ALTER TABLE party_wps ADD COLUMN szi_2 integer;"
             )
        cur.execute(
           "ALTER TABLE party_wps ADD COLUMN szi_3 integer;"
             )

        conn.commit()

class UploadxmlStart(ModelView):
    'upload xls'
    __name__ = 'party.uplod_xls.start'
    from_date = fields.Date('From Date', required=True)
    to_date = fields.Date('To Date', required=True)
    file =  fields.Binary("Upload the File","name")
    file_ =  fields.Char("Sie haben soeben die Klassenliste aktualisiert. Möchten Sie weitermachen ? ")
    filename = fields.Char("Filename")






class process(DeactivableMixin, ModelView, ModelSQL, MultiValueMixin):
    'Party Process'
    __name__ = 'party.process'

    code = fields.Char("Prozess")
    bechreibung = fields.Char("Beschreibung")
    liste = fields.Integer("liste")
    liste_=fields.Char("liste")

    def get_rec_name(self,code):
        return self.code




class PrintISONORMES(ModelView):
    'Print ISO normes'
    __name__ = 'party.iso_normes_1.start'
    from_date = fields.Date('From Date', required=True)
    to_date = fields.Date('To Date', required=True)
    company = fields.Many2One('bewertung.iso5817', 'Company', required=True)
    posted = fields.Boolean('Posted Move', help='Show only posted move')

    @staticmethod
    def default_from_date():
        Date = Pool().get('ir.date')
        return datetime.date(Date.today().year, 1, 1)

    @staticmethod
    def default_to_date():
        Date = Pool().get('ir.date')
        return Date.today()

    @staticmethod
    def default_company():
        return Transaction().context.get('company')

    @staticmethod
    def default_posted():
        return False

#BEW_NORMES
class ISONORMES(Wizard):
    'Bew ISONOMES'
    __name__ = 'party.isonormes'
    start = StateView('party.iso_normes_1.start',
        'welding_certification.iso_normes_1_start_view_form', [
            Button('Cancel', 'end', 'tryton-cancel'),
            Button('OK', 'print_', 'tryton-print', default=True),
            ])
    print_ = StateReport('welding_certification.party.iso_normes_report')
    def do_print_(self, action):
        data = {
            'company': self.start.company.id,
            }
        return action, data
#report

class ISONORMESreport(Report):
    __name__ = 'welding_certification.party.iso_normes_report'



    @classmethod
    def _get_records(cls, ids, model, data):
        Move = Pool().get('bewertung.iso5817')

        clause = [

            ]


    @classmethod
    def get_context(cls, records, data):
        report_context = super(ISONORMESreport, cls).get_context(records, data)

        Company = Pool().get('bewertung.iso5817')
        company = Company(data['id'])

        report_context['company'] = company
        report_context['Bemerkung1'] = company.Bemerkung_1
        report_context['d1'] = company.d1
        report_context['c1'] = company.c1
        report_context['b1'] = company.b1
        report_context['Bemerkung1_1'] = company.bemerkung1
        report_context['d2'] = company.d2
        report_context['c2'] = company.c2
        report_context['b2'] = company.b2
        report_context['Bemerkung1_2'] = company.bemerkung2
        report_context['d3'] = company.d3
        report_context['c3'] = company.c3
        report_context['b3'] = company.b3
        report_context['Bemerkung1_3'] = company.bemerkung3
        report_context['d4'] = company.d4
        report_context['c4'] = company.c4
        report_context['b4'] = company.b4
        report_context['Bemerkung1_4'] = company.bemerkung4
        report_context['d5'] = company.d5
        report_context['c5'] = company.c5
        report_context['b5'] = company.b5
        report_context['Bemerkung1_5'] = company.bemerkung5
        report_context['d6'] = company.d6
        report_context['c6'] = company.c6
        report_context['b6'] = company.b6
        report_context['Bemerkung1_6'] = company.bemerkung6
        report_context['d7'] = company.d7
        report_context['c7'] = company.c7
        report_context['b7'] = company.b7
        report_context['Bemerkung1_7'] = company.bemerkung7
        report_context['d8'] = company.d8
        report_context['c8'] = company.c8
        report_context['b8'] = company.b8
        report_context['Bemerkung1_8'] = company.bemerkung8
        report_context['d9'] = company.d9
        report_context['c9'] = company.c9
        report_context['b9'] = company.b9
        report_context['Bemerkung1_9'] = company.bemerkung9
        report_context['d10'] = company.d10
        report_context['c10'] = company.c10
        report_context['b10'] = company.b10
        report_context['Bemerkung1_10'] = company.bemerkung10
        report_context['d11'] = company.d11
        report_context['c11'] = company.c11
        report_context['b11'] = company.b11
        report_context['Bemerkung1_11'] = company.bemerkung11
        report_context['d12'] = company.d12
        report_context['c12'] = company.c12
        report_context['b12'] = company.b12
        report_context['Bemerkung1_12'] = company.bemerkung12
        report_context['d13'] = company.d13
        report_context['c13'] = company.c13
        report_context['b13'] = company.b13
        report_context['Bemerkung1_13'] = company.bemerkung13
        report_context['d14'] = company.d14
        report_context['c14'] = company.c14
        report_context['b14'] = company.b14
        report_context['Bemerkung1_14'] = company.bemerkung14
        report_context['d15'] = company.d15
        report_context['c15'] = company.c15
        report_context['b15'] = company.b15
        report_context['Bemerkung1_15'] = company.bemerkung15
        report_context['d16'] = company.d16
        report_context['c16'] = company.c16
        report_context['b16'] = company.b16
        report_context['Bemerkung1_16'] = company.bemerkung16
        report_context['d17'] = company.d17
        report_context['c17'] = company.c17
        report_context['b17'] = company.b17
        report_context['Bemerkung1_17'] = company.bemerkung17
        report_context['d18'] = company.d18
        report_context['c18'] = company.c18
        report_context['b18'] = company.b18
        report_context['Bemerkung1_18'] = company.bemerkung18
        report_context['d19'] = company.d19
        report_context['c19'] = company.c19
        report_context['b19'] = company.b19
        report_context['Bemerkung1_19'] = company.bemerkung19
        report_context['d20'] = company.d20
        report_context['c20'] = company.c20
        report_context['b20'] = company.b20
        report_context['Bemerkung1_20'] = company.bemerkung20
        report_context['d21'] = company.d21
        report_context['c21'] = company.c21
        report_context['b21'] = company.b21
        report_context['Bemerkung1_21'] = company.bemerkung21
        report_context['d22'] = company.d22
        report_context['c22'] = company.c22
        report_context['b22'] = company.b22
        report_context['Bemerkung1_22'] = company.bemerkung22
        report_context['d23'] = company.d23
        report_context['c23'] = company.c23
        report_context['b23'] = company.b23
        report_context['Bemerkung1_23'] = company.bemerkung23
        report_context['d24'] = company.d24
        report_context['c24'] = company.c24
        report_context['b24'] = company.b24
        report_context['Bemerkung1_24'] = company.bemerkung24
        report_context['d25'] = company.d25
        report_context['c25'] = company.c25
        report_context['b25'] = company.b25
        report_context['Bemerkung1_25'] = company.bemerkung25
        report_context['d26'] = company.d26
        report_context['c26'] = company.c26
        report_context['b26'] = company.b26
        report_context['Bemerkung1_26'] = company.bemerkung26
        report_context['d1_innere'] = company.d1_innere
        report_context['c1_innere'] = company.c1_innere
        report_context['b1_innere'] = company.b1_innere
        report_context['Bemerkung1_innere'] = company.bemerkung_innere
        report_context['d2_innere'] = company.d2_innere
        report_context['c2_innere'] = company.c2_innere
        report_context['b2_innere'] = company.b2_innere
        report_context['Bemerkung2_innere'] = company.bemerkung_innere2
        report_context['d3_innere'] = company.d3_innere
        report_context['c3_innere'] = company.c3_innere
        report_context['b3_innere'] = company.b3_innere
        report_context['Bemerkung3_innere'] = company.bemerkung_innere3
        report_context['d4_innere'] = company.d4_innere
        report_context['c4_innere'] = company.c4_innere
        report_context['b4_innere'] = company.b4_innere
        report_context['Bemerkung4_innere'] = company.bemerkung_innere4
        report_context['d5_innere'] = company.d5_innere
        report_context['c5_innere'] = company.c5_innere
        report_context['b5_innere'] = company.b5_innere
        report_context['Bemerkung5_innere'] = company.bemerkung_innere5
        report_context['d6_innere'] = company.d6_innere
        report_context['c6_innere'] = company.c6_innere
        report_context['b6_innere'] = company.b6_innere
        report_context['Bemerkung6_innere'] = company.bemerkung_innere6
        report_context['d7_innere'] = company.d7_innere
        report_context['c7_innere'] = company.c7_innere
        report_context['b7_innere'] = company.b7_innere
        report_context['Bemerkung7_innere'] = company.bemerkung_innere7
        report_context['d8_innere'] = company.d8_innere
        report_context['c8_innere'] = company.c8_innere
        report_context['b8_innere'] = company.b8_innere
        report_context['Bemerkung8_innere'] = company.bemerkung_innere8
        report_context['d9_innere'] = company.d9_innere
        report_context['c9_innere'] = company.c9_innere
        report_context['b9_innere'] = company.b9_innere
        report_context['Bemerkung9_innere'] = company.bemerkung_innere9
        report_context['d10_innere'] = company.d10_innere
        report_context['c10_innere'] = company.c10_innere
        report_context['b10_innere'] = company.b10_innere
        report_context['Bemerkung10_innere'] = company.bemerkung_innere10
        report_context['d11_innere'] = company.d11_innere
        report_context['c11_innere'] = company.c11_innere
        report_context['b11_innere'] = company.b11_innere
        report_context['Bemerkung11_innere'] = company.bemerkung_innere10
        report_context['d12_innere'] = company.d12_innere
        report_context['c12_innere'] = company.c12_innere
        report_context['b12_innere'] = company.b12_innere
        report_context['Bemerkung12_innere'] = company.bemerkung_innere12
        report_context['d13_innere'] = company.d13_innere
        report_context['c13_innere'] = company.c13_innere
        report_context['b13_innere'] = company.b13_innere
        report_context['Bemerkung13_innere'] = company.bemerkung_innere13
        report_context['d14_innere'] = company.d14_innere
        report_context['c14_innere'] = company.c14_innere
        report_context['b14_innere'] = company.b14_innere
        report_context['Bemerkung14_innere'] = company.bemerkung_innere14
        report_context['d15_innere'] = company.d15_innere
        report_context['c15_innere'] = company.c15_innere
        report_context['b15_innere'] = company.b15_innere
        report_context['Bemerkung15_innere'] = company.bemerkung_innere15
        report_context['d16_innere'] = company.d16_innere
        report_context['c16_innere'] = company.c16_innere
        report_context['b16_innere'] = company.b16_innere
        report_context['Bemerkung16_innere'] = company.bemerkung_innere16
        report_context['d17_innere'] = company.d17_innere
        report_context['c17_innere'] = company.c17_innere
        report_context['b17_innere'] = company.b17_innere
        report_context['Bemerkung17_innere'] = company.bemerkung_innere17
        report_context['d18_innere'] = company.d18_innere
        report_context['c18_innere'] = company.c18_innere
        report_context['b18_innere'] = company.b18_innere
        report_context['Bemerkung18_innere'] = company.bemerkung_innere18
        report_context['d19_innere'] = company.d19_innere
        report_context['c19_innere'] = company.c19_innere
        report_context['b19_innere'] = company.b19_innere
        report_context['Bemerkung19_innere'] = company.bemerkung_innere19
        report_context['d20_innere'] = company.d20_innere
        report_context['c20_innere'] = company.c20_innere
        report_context['b20_innere'] = company.b20_innere
        report_context['Bemerkung20_innere'] = company.bemerkung_innere20
        report_context['d21_innere'] = company.d21_innere
        report_context['c21_innere'] = company.c21_innere
        report_context['b21_innere'] = company.b21_innere
        report_context['Bemerkung21_innere'] = company.voll_
        report_context['d1_unregel'] = company.d1_unregel
        report_context['c1_unregel'] = company.c1_unregel
        report_context['b1_unregel'] = company.b1_unregel
        report_context['Bemerkung1_unregel'] = company.Bemerkung_unregel1
        report_context['d2_unregel'] = company.d2_unregel
        report_context['c2_unregel'] = company.c2_unregel
        report_context['b2_unregel'] = company.b2_unregel
        report_context['Bemerkung2_unregel'] = company.Bemerkung_unregel2
        report_context['d3_unregel'] = company.d3_unregel
        report_context['c3_unregel'] = company.c3_unregel
        report_context['b3_unregel'] = company.b3_unregel
        report_context['Bemerkung3_unregel'] = company.Bemerkung_unregel3
        report_context['d4_unregel'] = company.d4_unregel
        report_context['c4_unregel'] = company.c4_unregel
        report_context['b4_unregel'] = company.b4_unregel
        report_context['Bemerkung4_unregel'] = company.Bemerkung_unregel4
        report_context['d1_part4'] = company.d1_part4
        report_context['c1_part4'] = company.c1_part4
        report_context['b1_part4'] = company.b1_part4
        report_context['Bemerkung1_part4'] = company.Bemerkung1_part4

        report_context['d2_part4'] = company.d2_part4
        report_context['c2_part4'] = company.c2_part4
        report_context['b2_part4'] = company.b2_part4
        report_context['Bemerkung2_part4'] = company.Bemerkung2_part4


        return report_context
#Bew für iso 96062
class Bewertung2(DeactivableMixin, ModelView, ModelSQL, MultiValueMixin):
    'Party Bewertung2'
    __name__ = 'party.bewertung2'
    test_prufung_1 = fields.One2Many('bewertung.bewertungtest','testbewertung2','Sichtprüfung nach DIN EN ISO 17637- Decklage')
    prufung2_1 = fields.One2Many('test2','test26_2','Sichtprüfung nach DIN EN ISO 17637- Kehlnaht')
    Durch_tab_1 = fields.One2Many('test','testdurchstrahlungsprüfung2','Durchstrahlungsprüfung nach DIN EN ISO 17636-1/2(Film oder digitaler Detektor)')
    Bruch_tab_1 = fields.One2Many('party_bbruch','test_bruchprüfung2','Bruchprüfung nach DIN EN ISO 9017')
    Biege_tab_1 = fields.One2Many('party_biegeprufung','test_biegeprüfung2','Biegeprüfung nach EN ISO 5173')
    Weitere_tab_1 = fields.One2Many('party_weitereprufung','test_weitere_prüfung2','Weitere Prüfung nach DIN EN *5)')
    notice1 = fields.Text('Bewertungsgrundlage')
    notice2 = fields.Text('DIN EN ISO 5817 (Stahl, Nickel, Titan)')
    notice3 = fields.Text('DIN EN ISO 10042 (Aliminum)')
    notice4 = fields.Text('Bewertungsbogen')
    notice5 = fields.Text('zur Schweißer-Prüfungsbescheinigung nach')
    notice6 = fields.Text('(Abschnitt 7)')
    Name = fields.Char("Name")
    test = fields.Char("Test")
    Geburts_tag = fields.Date("Geburts-Tag")
    Kartei = fields.Integer("Kartei-Nr")
    Pers_Nr = fields.Integer("Pers.-Nr")
    prufstelle = fields.Char("Prüfstelle")
    Bezeichnung0 = fields.Many2One('party.iso96062', 'Bezeichnung', 
           ondelete='CASCADE')
    Bezeichnung01 =fields.Function(fields.Many2One('party.iso96062',"test"),'On_change_Bezeichnung01')
    Bezeichnung1 = fields.Many2One('party.iso96062', 'Bezeich1', 
           ondelete='CASCADE')
    Bezeichnung2 = fields.Many2One('party.iso96062', 'Bezeich2',
           ondelete='CASCADE')
    Bezeichnung3 = fields.Many2One('party.iso96062', 'Bezeich3',
           ondelete='CASCADE')
    Title_bezeichnung = fields.Text('Prüfungsbezeichnung')
    Title_Norm = fields.Text('Norm')
    Norm0 = fields.Function(fields.Char('Norm'),'On_change_Bezeichnung0')
    Norm1 = fields.Function(fields.Char('Norm1'),'On_change_Bezeichnung1')
    Norm2 = fields.Function(fields.Char('Norm2'),'On_change_Bezeichnung2')
    Norm3 = fields.Function(fields.Char('Norm3'),'On_change_Bezeichnung3')
    idd1_1=fields.Function(fields.Integer("test"),"get_id")
    Prufn_0 = fields.Function(fields.Char('Prüf.-Nr'),'On_change_Bezeichnung4')
    Prufn_1 = fields.Function(fields.Char('Pruf1'),'On_change_Bezeichnung5')
    Prufn_2 = fields.Function(fields.Char('Pruf2'),'On_change_Bezeichnung6')
    Prufn_3 = fields.Function(fields.Char('Pruf3'),'On_change_Bezeichnung7')

    Title_pruf_nr = fields.Text('Prüf.-Nr')
    text1 = fields.Text('Prüfungsbeauftrager')
    text2 = fields.Text('(Datum, Name und Unterschrift)')
    text3 = fields.Text('Datum und Unterschrift des Prüfers')
    ligne ="---------------"
    index1 = fields.Text('*1)e = erfüllt,ne = nicht erfüllt')
    index2 = fields.Text('*2)Ordnungsnummern der Unregelmäßigkeiten nach ISO 6520-1')
    index3 = fields.Text('*3)W = Wurzel, D=Decklage')
    index4 = fields.Text('*4)S = Schweißgut')
    index41 = fields.Text('100 Risse')
    index42 = fields.Text('5011 Einbrandkerbe')
    index43 = fields.Text('Ü Übergang')
    index44 = fields.Text('2011 Poren')
    index45 = fields.Text('5013 Wurzelkerbe')
    index46 = fields.Text('G = Grundwerkstoff')
    index47 = fields.Text('2013 Porennest')
    index48 = fields.Text('502 Zu große Nahtüberhöhung(BW)')
    index49 = fields.Text('2016 Schlauchporen')
    index491 = fields.Text('503 Zu große Nahtüberhöhung(FW)')
    index5 = fields.Text('*5) ISO 23277 Eindringprüfung')
    index51 = fields.Text('300 Feste Einchlüsse')
    index52 = fields.Text('504 Zu große Wurzelüberhöhung')
    index53 = fields.Text('ISO 23278 Magnetpulverprüfung')
    index54 = fields.Text('401 Bindefehler')
    index55 = fields.Text('507 Kantenversatz')
    index56 = fields.Text('ISO 17639 Mikro-/Makroskopie')
    index57 = fields.Text('402 Ungenügende')
    index58 = fields.Text('511 Decklagenunterwölbung')
    index59 = fields.Text('ISO 17640 Ultraschallprüfung')
    index60 = fields.Text('Durchschweißung')
    index61 = fields.Text('512 Übermäßige Asymmetrie (FW)')
    spac_notice4 = "                                                               "

    spc ="                               "
    spc1 =" "
    Fachkunde = fields.Selection([
        ('Bestanden', 'Bestanden'),
        ('nicht geprüft', 'nicht geprüft'),
        ('nicht bestanden', 'nich bestanden'),
    ], 'Fachkunde', readonly = False,
        )
    gesamt = fields.Selection([
        ('erfüllt', 'erfüllt'),
        ('erfüllt', 'nicht erfüllt'),
    ], 'Gesamt bewertung', readonly = False,
        )
    normes = fields.Selection([
        ('EN ISO 9606-1', 'EN ISO 9606-1'),
        ('DIN EN 287-1', 'DIN EN 287-1'),
    ], 'Normes', readonly = False,
        )

    About_normes = fields.Many2One('bewertung.iso5817', ' ',
            ondelete='CASCADE')


    space2 = fields.Char("                                                                                                                                                                                                                                     ")
#Declarer le bouton ISO_normes
    @classmethod
    def __setup__(cls):
      super(Bewertung2, cls).__setup__()
      cls._buttons.update({
          'ISO_Normes': {},
          })

    def get_rec_name(self,normes):
        val1 = "zur Schweißer-Prüfungsbescheinigung nach"
        val2 = self.normes
        val3 = "(Aschnitt7)"
        final_val = val1+val2+val3
        return final_val

    @classmethod
    @ModelView.button_action('welding_certification.wizart_normes')
    def ISO_Normes (cls,Bewertung2):
        pass
    def get_id(self):
        return self.id

    @staticmethod
    def default_Name():
       return " "

    def On_change_Bezeichnung01(self,Name):
          Party = Pool().get('party.iso96062')
          parties = Party.search([
                 ('Bewertung2', '=', self.id),
                 ], limit=1)
          if parties:
              party, = parties
              return party.id
          return None

    @staticmethod
    def default_test_prufung_1():

            return [{"Schw_position":"PC"}]


    def On_change_Bezeichnung0(self,Bezeichnung01):
      if(self.Bezeichnung01 is not None):
        value_ret = self.Bezeichnung01.pruf_nr
        return value_ret
      else:
        return " "
    def On_change_Bezeichnung1(self,Bezeichnung1):
      if(self.Bezeichnung1 is not None):
        value_ret = self.Bezeichnung1.pruf_nr
        return value_ret
      else:
        return " "
    def On_change_Bezeichnung2(self,Bezeichnung2):
      if(self.Bezeichnung2 is not None):
        value_ret = self.Bezeichnung2.pruf_nr
        return value_ret
      else:
        return " "
    def On_change_Bezeichnung3(self,Bezeichnung3):
      if(self.Bezeichnung3 is not None):
        value_ret = self.Bezeichnung3.pruf_nr
        return value_ret
      else:
        return " "

    def On_change_Bezeichnung4(self,Bezeichnung0):
      if(self.Bezeichnung0 is not None):
        value_ret = self.Bezeichnung0.pruf_nr
        return value_ret
      else:
        return " "
    def On_change_Bezeichnung5(self,Bezeichnung1):
      if(self.Bezeichnung1 is not None):
        value_ret = self.Bezeichnung1.pruf_nr
        return value_ret
      else:
        return " "
    def On_change_Bezeichnung6(self,Bezeichnung2):
      if(self.Bezeichnung2 is not None):
        value_ret = self.Bezeichnung2.pruf_nr
        return value_ret
      else:
        return " "
    def On_change_Bezeichnung7(self,Bezeichnung3):
      if(self.Bezeichnung3 is not None):
        value_ret = self.Bezeichnung3.pruf_nr
        return value_ret
      else:
        return " "

class pruf_prufstelle_Beleg_nr(DeactivableMixin, ModelView, ModelSQL, MultiValueMixin):
    'Party Prufer_prufstelle_beleg'
    __name__ = 'party.prufer_prufstelle_beleg'
    name=fields.Char('Name')


#EN ISO 9606-2

class iso96062(DeactivableMixin, ModelView, ModelSQL, MultiValueMixin):
    'Party Iso96062'
    __name__ = 'party.iso96062'

    legitimation = fields.Function(fields.Char('Legitimation'),'on_change_Sweisserr')
    Namedesschweisser = fields.Many2One('party.party', 'Name des Schweißers',
            ondelete='CASCADE')
    Bewertung2 = fields.Many2One('party.bewertung2', 'Bewertungsbogen', 
            ondelete='CASCADE')

    position_al1 = fields.Many2One('welding.schweissposition_iso6947', 'Schweißposition', 
            ondelete='CASCADE')
    space_pdf = fields.Function(fields.Char(" "),"insert_space_pdf")
    title = fields.Selection([
        ('Prüfungsbescheinigung', 'Schweißer-Prüfungsbescheinigung'),
        ('schweisser1', 'SCHWEISSER-PRÜFUNGSBESCHEINIGUNG'),
        ('zertifikat', 'Schweißer-Zertifikat'),
        ('prüfungszertifikat', 'Schweißer-Prüfungszertifikat'),
        ('zertifikatSchweißer_Prüfungsbescheinigung', 'ZERTIFIKAT/SCHWEIßER-PRÜFUNGSBESCHEINIGUNG'),
        ('welder_approver', 'WELDER APPROVAL TEST CERTIFICATE'),
    ], ' ', readonly = False,
        )

    grundwerkstoffe = fields.Many2One('welding.grundwerkstoff_properties', 'Grundwerkstoffe 1')

    bezeichnung = fields.Many2One('welding.szi_data', '(Bezeichnung)')
    schutzgaz_gel = fields.Function(fields.Char(" "),"on_change_schutzgazzz")
    Stromart_und_Polung = fields.Selection([
        ('-', '-'),
        ('AC', 'AC'),
        ('Wechselstrom', 'Wechselstrom'),
        ('DC(-)', 'DC(-)'),
        ('DC+/-', 'DC+/-'),
        ('Gleichstrom', 'Gleichstrom (-)'),
        ('DC(+)', 'DC(+)'),
        ('Gleichstrom(+)', 'Gleichstrom (+)'),
        ('aaa: DC(-) / bbb : DC(+)', 'aaa: DC(-) / bbb : DC(+)'),
        ('aaa: DC(+) / bbb : DC(-)', 'aaa: DC(+) / bbb : DC(-)'),
    ], 'Stromart und Polung', readonly = False,
        )
    Stromart_und_Polung_gel = fields.Function(fields.Char(" "),"on_change_Stromart_und_Polungg")
    prufstellle = fields.Many2One('welding.pruefstelle', 'Name des Prüfers oder der Prüfstelle',
            ondelete='CASCADE')
    Unterschrift_p = fields.Function(fields.Char("Unterschrift"),"On_Change_prufstellle")

    pruf_nr = fields.Char("Weitere Beleg-Nr")
    pruf_nr_weitere = fields.Char("Weitere Beleg-Nr")

    wps_bezug = fields.Many2One('party.wps', 'WPS-Bezug',
            ondelete='CASCADE')
    wps_bezug2 = fields.Many2One('party.wps', ' ',
            ondelete='CASCADE')
    pruf_pruff = fields.Many2One('party.prufer_prufstelle_beleg', 'Prüfer oder Prüfstelle - Beleg-Nr',
            ondelete='CASCADE')

    formular = fields.Selection([
        ('ISO13', 'ISO13 | EN ISO 9606-1:2013-Formular'),
        ('EN-04', 'EN-04 | EN ISO 9606-2,EN 287-6'),
        ('EN', 'EN | EN ISO 9606-3/4/5'),
        ('ASME', 'ASME | ASME Welder, Form QW-484A'),
    ], 'Formular', readonly = False,
        )
    prufnorm = fields.Selection([
        ('DIN EN ISO 9606-2:2005-03', 'DIN EN ISO 9606-2:2005-03 | Schmelzschweißen-Aluminium und Legierungen'),
        ('DIN EN ISO 9606-2', 'DIN EN ISO 9606-2 | Schmelzschweißen-Aluminium und Legierungen'),
        ('DIN EN ISO 9606-2:2005-03, AD 2000 HP 3', 'DIN EN ISO 9606-2:2005-03, AD 2000 HP 3 | Geschweißte Druckbehälter'),
        ('DIN EN ISO 9606-2:2005-03, EN 15085-2', 'DIN EN ISO 9606-2:2005-03, EN 15085-2 | Schweißen von Schienenfahrzeugen'),
        ('SN EN ISO 9606-2:2005-03', 'SN EN ISO 9606-2:2005-03 | Schweizerische Norm, Ausgaba:2005-03'),
        ('DGRL 2014/68/EU, AD 2000 HP 3,EN ISO 9606-2', 'DGRL 2014/68/EU, AD 2000 HP 3,EN ISO 9606-2 | Zertifikat TÜV nach DGRL 2014/68/EU (Aluminium)'),
        ('2014/68/EU;EN ISO 9606-2;AD 2000 HP 3', '2014/68/EU;EN ISO 9606-2;AD 2000 HP 3 | Zertifikat DVS-PersZert 2014/68/EU(Aluminium)'),
        ('97/23/EG, AD 2000 HP 3, EN ISO 9606-2', '97/23/EG, AD 2000 HP 3, EN ISO 9606-2 | Zertifikat nach DGR 97/23/EG(Aluminium)'),
        ('DGRL 97/23/EG, EN 13445-4, EN ISO 9606-2', 'DGRL 97/23/EG, EN 13445-4, EN ISO 9606-2 | Zertifikat nach DGRL 97/23/EG(Aluminium)'),
        ('EN ISO 9606-2, SVTI 504', 'EN ISO 9606-2, SVTI 504 | Schweizerische Norm'),
        ('EN ISO 9606-2, SVTI 504, AD 2000 HP 3', 'EN ISO 9606-2, SVTI 504, AD 2000 HP 3 | Schweizerische Norm'),
        ('EN ISO 9606-2, SVTI 504, DGR', 'EN ISO 9606-2, SVTI 504,DGR | Schweizerische Norm'),
        ('DIN EN 287-6:2010-05', 'DIN EN 287-6:2010-05 | Schmelzschweißen - Gusseisen'),
        ('SN EN 287-6:2010-06', 'SN EN 287-6:2010-06 | Schweizerische Norm, Ausgabe : 2010-06'),
        ('DGRL 2014/68/EU, AD 2000 HP 3, EN 287-6:2010', 'DGRL 2014/68/EU, AD 2000 HP 3, EN 287-6:2010 | Zertifikat TÜV nach DGRL 2014/68/EU (Gusseisen)'),
        ('2014/68/EU; EN 287-6:2010;AD 2000 HP 3', '2014/68/EU; EN 287-6:2010;AD 2000 HP 3 | Zertifikat DVS-PersZert 2014/68/EU(Gusseisen)'),
        ('DIN EN 287-1:2011-11', 'DIN EN 287-1:2011-11 | Schmelzschweißen - Stähle (zurückgezogen)'),
        ('DIN EN 287-1:2011-11,AD 2000 HP 3', 'DIN EN 287-1:2011-11,AD 2000 HP 3 | Geschweißte Druckbehälter'),
        ('DIN EN 287-1:2011-11,DIN 18800-7', 'DIN EN 287-1:2011-11,DIN 18800-7 | Stahlbauten'),
        ('DIN EN 287-1:2011-11,DIN EN 15085-2', 'DIN EN 287-1:2011-11,DIN EN 15085-2 | Schweißen von Schienenfahrzeugen'),
        ('SN EN 287-1:2011-09', 'SN EN 287-1:2011-09 | Schweizerische Norm, Ausgabe:2011-09'),
        ('ÖNORM EN 287-1:2011-09-01', 'ÖNORM EN 287-1:2011-09-01 | Österreichische Norm, Ausgabe:2011-09-01'),
        ('PN-EN 287-1:2011', 'PN-EN 287-1:2011 | Polnische Norm, Ausgabe:2011'),
        ('MSZ EN 287-1:2012', 'MSZ EN 287-1:2012 | Ungarische Norm, Ausgabe:2012'),
        ('DIN EN 287-1 in DIN EN ISO 9606-1 umwandeln', 'DIN EN 287-1 in DIN EN ISO 9606-1 umwandeln | Umwandlung der EN 287-1 Prüfung in EN ISO 9606-1'),
        ('97/23/EG,AD 2000 HP 3, EN 287-1:2011', '97/23/EG,AD 2000 HP 3, EN 287-1:2011 | Zertifikat nach DGR 97/23/EG (Stähle)'),
        ('DGRL 97/23/EG, EN 13445-4, EN 287-1:2011', 'DGRL 97/23/EG, EN 13445-4, EN 287-1:2011 | Zertifikat nach DGRL 97/23/EG (Stähle)'),
        ('SN EN 287-1:2011-09, RL 97/23/EG', 'SN EN 287-1:2011-09, RL 97/23/EG | Zertifikat Schweiz nach RL 97/23/EG (Stähle)'),
        ('DIN EN 287-1:2006-06', 'DIN EN 287-1:2006-06 | Schmelzschweißen - stähle (mit Änderung A2)'),
        ('DIN EN 287-1:2006-06, AD 2000 HP 3', 'DIN EN 287-1:2006-06, AD 2000 HP 3 | Geschweißte Druckbehälter'),
        ('DIN EN 287-1:2006-06, DIN 18800-7', 'DIN EN 287-1:2006-06, DIN 18800-7 | Stahlbauten'),
        ('DIN EN 287-1:2006-06, DIN EN 15085-2', 'DIN EN 287-1:2006-06, DIN EN 15085-2 | Schweißen von Schienenfahrzeugen'),
        ('DIN EN 287-1:2011, DB-Rili 951.0020A08', 'DIN EN 287-1:2011, DB-Rili 951.0020A08 | Ausbildung Schweißpersonal bei der DB AG'),
        ('DIN EN 287-1:2006, DB-Rili 951.0020A08', 'DIN EN 287-1:2006, DB-Rili 951.0020A08 | Ausbildung Schweißpersonal bei der DB AG'),
        ('DIN EN 287-1:2004-05', 'DIN EN 287-1:2004-05 | Schmelzschweißen-stähle (zurückgezogen)'),
        ('97/23/EG, AD 2000 HP 3, EN 287-1:2006', '97/23/EG, AD 2000 HP 3, EN 287-1:2006 | Zertifikat nach DGR 97/23/EG(Stähle) +A2'),
        ('DGRL 97/23/EG, EN 13445-4, EN 287-1:2006', 'DGRL 97/23/EG, EN 13445-4, EN 287-1:2006 | Zertifikat nach DGR 97/23/EG(Stähle) +A2'),
        ('EN 287-1:2011, SVTI 504', 'EN 287-1:2011, SVTI 504 | Schweizerische Norm'),
        ('EN 287-1:2011, SVTI 504, AD 2000 HP 3', 'EN 287-1:2011, SVTI 504, AD 2000 HP 3 | Schweizerische Norm'),
        ('EN 287-1:2011, SVTI 504, AD HP 3, DGR', 'EN 287-1:2011, SVTI 504, AD HP 3, DGR | Schweizerische Norm'),
        ('EN 287-1:2011, SVTI 504, DGR', 'EN 287-1:2011, SVTI 504, DGR | Schweizerische Norm'),
    ], 'Vorschrift/Prüfnorm', readonly = False,
        )



    Art_der_legitimation = fields.Function(fields.Char('Art der Legitimation'),'on_change_Sweisser_r')
    Gebursdatum_und_ort = fields.Function(fields.Char('Gebursdatum und Ort'),'on_change_Sweisser_2')
    Arbeitgeber = fields.Function(fields.Char('Arbeitgeber'),'on_change_Sweisser_3')
    Bemerkung = fields.Text("Bemerkung")
    Bemerkung = fields.Text("Bemerkung")
    text_1 = fields.Text("Bestätigung der Gültigkeit durch den Arbeitgeber/die Schweißaufsichtsperson für die folgenden 6 Monate (unter Bezug auf Abschnitt 9.2)", required=True)
    Hinweise = fields.Function(fields.Text("MAG"), 'on_change_Dok')
    pruf1 = fields.Text("Prüfstück1",required=True)
    pruf2 = fields.Text("Prüfstück2",required=True)
    ort = fields.Char("Ort")
    datum_ausgabe = fields.Date('Datum der Ausgabe')
    datum_schweissen = fields.Date('Datum des Schweißens')
    geltungs_bis = fields.Function(fields.Date('Gültigkeitsdauer bis'),'on_change_Sweiss_datum')
    datum_prufung = fields.Date('Datum der Prüfung')

    Datumms9_2 = fields.One2Many('party.datumms9.2','test2','Bestätigung der Gültigkeit durch den Arbeitgeber/die Schweißaufsichtsperson für die folgenden 6 Monate (unter Bezug auf Abschnitt 9.2)')
    Datumms9_3 = fields.One2Many('party.datumms9.3','test3','Verlängerung der Qualifizierung durch den Prüfer oder die Prüfstelle für die nächsten 2 Jahre (unter Bezug auf 9.3)')
    prufsart = fields.Char("Prüfungsart",required=True)
    prufsart2 = fields.Char("Ausgefürt und bestanden",required=True)
    prufsart3 = fields.Char("nicht geprüft",required=True)
    #pruf_prufstelle = fields.Char("Name des Prüfers oder Prüfstelle")
    sichprufung = fields.Char("Sichprüfung")
    sichprufung_bestanden = fields.Selection([
        ('x', 'x'),
        ('-', '-'),
    ], 'sichprufung_bestanden', readonly = False,
        )

    sichprufung_nichgepruft1 = fields.Selection('on_change_sichprufung_bestanden1','sichprufung_nichtgepruft', readonly = False,)

    Durchprüfung = fields.Char("Durchstrahlungsprüfung")
    Durchprüfung_bestanden = fields.Selection([
        ('x', 'x'),
        ('-', '-'),
    ], 'Durchprüfung_bestanden', readonly = False,
        )
    Durchprüfung_nichgepruft1 = fields.Selection('on_change_Durchprüfung_bestanden1','Durchprüfung_nichtgepruft', readonly = False,)

    Bruchprüfung = fields.Char("Bruchprüfung")
    Bruchprüfung_bestanden = fields.Selection([
        ('x', 'x'),
        ('-', '-'),
    ], 'Bruchprüfung_bestanden', readonly = False,
        )

    Bruchprüfung_nichgepruft1 = fields.Selection('on_change_Bruchprüfung_bestanden1','Bruchprüfung_nichtgepruft', readonly = False,)


    Biegeprüfung = fields.Char("Biegeprüfung")
    Biegeprüfung_bestanden = fields.Selection([
        ('x', 'x'),
        ('-', '-'),
    ], 'Biegeprüfung_bestanden', readonly = False,
        )
    Biegeprüfung_nichgepruft1 = fields.Selection('on_change_Biegeprüfung_bestanden1','Biegeprüfung_nichtgepruft', readonly = False,)


    Kerbzugprüfung = fields.Char("Kerbzugprüfung")
    Kerbzugprüfung_bestanden = fields.Selection([
        ('x', 'x'),
        ('-', '-'),
    ], 'Kerbzugprüfung_bestanden', readonly = False,
        )

    Kerbzugprüfung_nichgepruft1 = fields.Selection('on_change_Kerbzugprüfung_bestanden1','Kerbzugprüfung_nichtgepruft', readonly = False,)

    Makprüfung = fields.Char("Makroskopische Untersuchungen")
    Markprüfung_bestanden = fields.Selection([
        ('x', 'x'),
        ('-', '-'),
    ], 'Markprüfung_bestanden', readonly = False,
        )
    Markprüfung_nichgepruft1 = fields.Selection('on_change_Markprüfung_bestanden1','Markprüfung_nichtgepruft', readonly = False,)

    zutsatzprüfungen = fields.Char("Zusatsprüfungen")
    Zusatsprüfung_bestanden = fields.Selection([
        ('x', 'x'),
        ('-', '-'),
    ], 'Zusatsprüfung_bestanden', readonly = False,
        )
    Zusatsprüfung_nichgepruft = fields.Selection([
        ('x', 'x'),
        ('-', '-'),
    ], 'Zusatsprüfung_nichtgepruft', readonly = False,
        )
    Zusatsprüfung_nichgepruft1 = fields.Selection('on_change_Zusatsprüfung_bestanden1','Zusatsprüfung_nichtgepruft', readonly = False,)


    Date1 = fields.Date("Date1")
    Date2 = fields.Date("Date2")
    Date3 = fields.Date("Date3")

    Datum9_2 = fields.Char("Datum", required=True)
    unterchrift9_2 = fields.Char("Unterschrift",required=True)
    Titl9_2 = fields.Char("Dienststellung oder Titel",required=True)

    titl1 = fields.Char("Datum")
    titl2 = fields.Char("Unterschrift")
    titl3 = fields.Char("Dienststellung oder Titel")
    Bezeichnung = fields.Function(fields.Char("Bezeichnung(en)"), 'on_change_alles')
    Bezeichnung2 = fields.Function(fields.Char(" "), 'on_change_alles2')

    werkstoffdicke = fields.Integer("Werkstoffdicke (mm)")
    werkstoffdicke_1 = fields.Integer("Werkstoffdicke (mm)")
    werkstoffdicke_g = fields.Function(fields.Char("MAG"), 'on_change_werkstoffdicke2')
    rohraussendurchmesser = fields.Integer("Rohraußendurchmesser (mm)")
    rohraussendurchmesser_1 = fields.Integer("Rohraußendurchmesser (mm)")
    rohraussendurchmesser_g =fields.Function(fields.Char("MAG"), 'on_change_rohraussendurchmesser2')
    schweißprocess_Geltungs = fields.Function(fields.Char("MAG"), 'on_change_schweissprocess')
    prufstuk_Geltungs = fields.Function(fields.Char("MAG"), 'on_change_schweissprocess2')
    geltungs = fields.Text("Geltungsbereich",required=True)
    Fachkunde = fields.Selection([
        ('bestanden', 'bestanden'),
        ('nicht geprüft', 'nicht geprüft'),
    ], 'Fachkunde', readonly = False,
        )
    Schweissposition = fields.Selection([
        ('PA', 'PA Wannenposition'),
        ('PB', 'PB Horizontalposition'),
        ('PC', 'PC Querposition'),
        ('PD', 'PD Horizontal-Überkopfposition'),
        ('PE', 'PE Überkopfposition'),
        ('PF', 'PF Steigposition'),
        ('PG', 'PG Fallposition'),
        ('PH', 'PH Rohrposition für steigendschweißen'),
        ('PJ', 'PJ Rohrposition für Fallendschweißen'),
        ('H-LO45', 'H-LO45 Steigend am Rohr, Neigungswinkel 45°'),
        ('J-LO45', 'J-LO45 Fallend  am Rohr, Neigungswinkel 45°'),
        ('PF/PC', 'PF/PC 2 Positionen am Rohr/BW für D>=150 mm'),
        ('PG/PC', 'PG/PC 2 Positionen am Rohr/BW für D>=150 mm'),
        ('PH/PC', 'PH/PC 2 Positionen am Rohr/BW für D>=150 mm'),
        ('PJ/PC', 'PJ/PC 2 Positionen am Rohr/BW für D>=150 mm'),
        ('PF/PC', 'PF/PC kombination am Blech/BW oder FW'),
        ('PA/PC', 'PA/PC kombination am Blech/BW'),
        ('PA/PF', 'PA/PF kombination am Blech/BW'),
        ('PB/PF', 'PB/PF kombination am Blech/FW'),
        ('PF/PD', 'PF/PD kombination für FW am Blech oder Rohr'),
        (' ', ' '),
    ], 'Schweißposition', readonly = False,
        )
    Schweissposition_2 = fields.Selection([
        ('PA', 'PA | P FW: waagerecht'),
        ('PB', 'PB | P FW: Horizontal'),
        ('PF', 'PF | P FW: Steigend'),
        ('PG', 'PG | P FW: fallend'),
        ('PD', 'PD | P FW: Horizontal-überkopf'),
        ('PC', 'PC | T BW: quer'),
        (' ', ' '),
    ], 'Schweißposition', readonly = False,
        )
    schweissposition_Geltungs = fields.Function(fields.Char("MAG"), 'on_change_position')
    Dokument = fields.Selection([
        ('test3 zeilen', 'test3 zeilen'),
        ('tuv abnahme', 'TÜV-Abnahme'),
        ('delete', 'Löschen'),
    ], 'Zusätzliche Hinweise', readonly = False,
        )
    Wurzel = fields.Selection([
        ('-', '-'),
        ('1', '1'),
        ('2', '2'),
        ('3', '3'),
        ('4', '4'),
        ('5', '5'),
    ], 'Wurzel', readonly = False,
        )
    Schweisszusatze = fields.Selection([
        ('nm', 'nm kein | Zusatzwerkstoff'),
        ('nm/S', 'nm/S | 141:kein Zusatzwerkstoff; 131, 135:Massivdraht/-stab'),
        ('S', 'S | Massivdraht/-stab'),
        (' ', ' '),
    ], 'Schweißzusätze', readonly = False,
        )
    Schweissnahteinzelheiten = fields.Selection('on_change_NNNAhtart','Schweißnahteinzelheiten', readonly = False,)
    Schweissnahteinzelheiten2 = fields.Selection([
        ('sl', 'sl einlagig'),
        ('ml', 'ml mehrlagig'),
        (' ', ' '),
    ], 'Schweißnahteinzelheiten', readonly = False,
        )

    zelheiten_Geltungs = fields.Function(fields.Char("MAG"), 'on_change_zelheiten')
    Schweisszusatze_Geltungs = fields.Function(fields.Char("MAG"), 'on_change_ssSchweisszusatze')

    Werkstoffgruppen = fields.Selection([
        ('21', '21 Reinaluminium mit <= 1% Verunreinigungen oder Legierungsbestandteilen'),
        ('22', '22 Nichtaushärtbare Legierungen'),
        ('23', '23 Aushärtbare Aluminiumlegierungen'),
        ('24', '24 Aluminium-Silicium-Legierungen mit Cu <= 1%'),
        ('25', '25 Aluminium-Silicium-Kupfer-Leg. mit 5% <Si < 14%, 1% <= Cu <= 5% und Mg <= 0.8%'),
        ('26', '26 Aluminium-Kupfer-Legierungen mit 2% <Cu <= 6%'),
        (' ', ' '),
    ], 'Werkstoffgruppe(n)', readonly = False,
        )
    Werkstoff2 = fields.Selection('on_change_wwerkstoff','Werkstoffgruppen', readonly = False,)
    werkstoff_Geltungs = fields.Function(fields.Char("MAG"), 'on_change_werkstoff')

    Produktform = fields.Selection([
        ('P', 'P Blech'),
        ('T', 'T Rohr'),
        (' ', ' '),
    ], 'Produktform (Blech oder Rohr)', readonly = False,
        )
    Nahtart = fields.Selection([
        ('BW', 'BW Stumpfnaht (butt weld)'),
        ('FW', 'FW Kehlnaht (fillet weld)'),
        (' ', ' '),
    ], 'Nahtart', readonly = False,
        )
    Nahtart2 = fields.Selection([
        ('FW', 'FW Kehlnaht'),
        (' ', ' '),
    ], 'Nahtart2', readonly = False,
        )
    Nahtart_Geltungs = fields.Function(fields.Char("MAG"), 'on_change_nahtart')

    produktform_Geltungs = fields.Function(fields.Char("MAG"), 'on_change_produktform')

    Schweißprozess = fields.Selection([
        ('131', '131 Metall-Inertgasschweißen mit Massivdrahtelektrode'),
        ('141', '141 Wolfram-Inertgasschweißen mit Massivdraht-oder Massivstabzusatz'),
        ('141/131', '141/131 Wurzel WIG, Auffüllen mit MIG (Al, Cu, Ni, Ti)'),
        ('15', '15 Plasmaschweißen'),
        (' ', ' '),
    ], 'Schweißprozess(e)', readonly = False,
        )
    def get_rec_name(self,Bezeichnung):
         return self.Bezeichnung

    def on_change_Stromart_und_Polungg(self,Stromart_und_Polung):
         return "-"

    def insert_space_pdf(self,Bezeichnung):
         return " "


    @staticmethod
    def default_prufnorm():
      return "DIN EN ISO 9606-2:2005-03"


    @staticmethod
    def default_rohraussendurchmesser():
      return 0

    @staticmethod
    def default_rohraussendurchmesser_1():
      return 0

    @staticmethod
    def default_title():
      return "Prüfungsbescheinigung"


    def On_Change_prufstellle(self,prufstellle):
     if(self.prufstellle is not None):
          return self.prufstellle.prufer
     else:
          return " "


    @staticmethod
    def default_datum_schweissen():
        return datetime.date.today()

    @fields.depends('Schweissnahteinzelheiten', 'Nahtart')
    def on_change_NNNAhtart(self):
        tabb=[]
        if(self.Nahtart == "BW"):
             tabb.append(("ss nb","ss nb | einseitig ohne Schweißbadsicherung"))
             tabb.append(("ss mb","ss mb | einseitig mit Schweißbadsicherung"))
             tabb.append(("bs","bs | beidseitiges Schweißen"))
             return tabb
        else:
             tabb.append(("sl","sl | einlagig(für Kehlnaht)"))
             tabb.append(("ml","ml | mehrlagig(für Kehlnaht)"))
             return tabb 




    @fields.depends('sichprufung_nichgepruft1', 'sichprufung_bestanden')
    def on_change_sichprufung_bestanden1(self):
        tabb=[]
        if(self.sichprufung_bestanden == "x"):
             tabb.append(("-","-"))
             return tabb
        else:
           if(self.sichprufung_bestanden == "-"):
               tabb.append(("x","x"))
               return tabb

    @fields.depends('Durchprüfung_nichgepruft1', 'Durchprüfung_bestanden')
    def on_change_Durchprüfung_bestanden1(self):
        tabb=[]
        if(self.Durchprüfung_bestanden == "x"):
             tabb.append(("-","-"))
             return tabb
        else:
           if(self.Durchprüfung_bestanden == "-"):
               tabb.append(("x","x"))
               return tabb

    @fields.depends('Bruchprüfung_nichgepruft1', 'Bruchprüfung_bestanden')
    def on_change_Bruchprüfung_bestanden1(self):
        tabb=[]
        if(self.Bruchprüfung_bestanden == "x"):
             tabb.append(("-","-"))
             return tabb
        else:
           if(self.Bruchprüfung_bestanden == "-"):
               tabb.append(("x","x"))
               return tabb

    @fields.depends('Biegeprüfung_nichgepruft1', 'Biegeprüfung_bestanden')
    def on_change_Biegeprüfung_bestanden1(self):
        tabb=[]
        if(self.Biegeprüfung_bestanden == "x"):
             tabb.append(("-","-"))
             return tabb
        else:
           if(self.Biegeprüfung_bestanden == "-"):
               tabb.append(("x","x"))
               return tabb

    @fields.depends('Kerbzugprüfung_nichgepruft1', 'Kerbzugprüfung_bestanden')
    def on_change_Kerbzugprüfung_bestanden1(self):
        tabb=[]
        if(self.Kerbzugprüfung_bestanden == "x"):
             tabb.append(("-","-"))
             return tabb
        else:
           if(self.Kerbzugprüfung_bestanden == "-"):
               tabb.append(("x","x"))
               return tabb


    @fields.depends('Markprüfung_nichgepruft1', 'Markprüfung_bestanden')
    def on_change_Markprüfung_bestanden1(self):
        tabb=[]
        if(self.Markprüfung_bestanden == "x"):
             tabb.append(("-","-"))
             return tabb
        else:
           if(self.Markprüfung_bestanden == "-"):
               tabb.append(("x","x"))
               return tabb

    @fields.depends('Zusatsprüfung_nichgepruft1', 'Zusatsprüfung_bestanden')
    def on_change_Zusatsprüfung_bestanden1(self):
        tabb=[]
        if(self.Zusatsprüfung_bestanden == "x"):
             tabb.append(("-","-"))
             return tabb
        else:
           if(self.Zusatsprüfung_bestanden == "-"):
               tabb.append(("x","x"))
               return tabb


    @staticmethod
    def default_Name_unterschrift():
        return " "

    @staticmethod
    def default_Schweissposition():
        return " "


    @staticmethod
    def default_Schweissposition_2():
        return " "


    @staticmethod
    def default_Schweissnahteinzelheiten():
        return " "

    @staticmethod
    def default_Schweisszusatze():
        return " "

    @staticmethod
    def default_Werkstoff2():
        return " "

    @staticmethod
    def default_Werkstoffgruppen():
        return " "

    @staticmethod
    def default_Nahtart():
        return " "

    @staticmethod
    def default_Produktform():
        return " "

    @staticmethod
    def default_Schweißprozess():
        return " "


    @staticmethod
    def default_sichprufung_bestanden():
        return "x"

    @staticmethod
    def default_sichprufung_nichgepruft():
        return "-"


    @staticmethod
    def default_Durchprüfung_nichgepruft():
        return "-"

    @staticmethod
    def default_Durchprüfung_bestanden():
        return "x"

    @staticmethod
    def default_Bruchprüfung_bestanden():
        return "x"

    @staticmethod
    def default_Bruchprüfung_nichgepruft():
        return "-"

    @staticmethod
    def default_Biegeprüfung_nichgepruft():
        return "-"

    @staticmethod
    def default_Biegeprüfung_bestanden():
        return "x"

    @staticmethod
    def default_Kerbzugprüfung_bestanden():
        return "x"

    @staticmethod
    def default_Kerbzugprüfung_nichgepruft():
        return "-"

    @staticmethod
    def default_Markprüfung_bestanden():
        return "x"

    @staticmethod
    def default_Markprüfung_nichgepruft():
        return "-"

    @staticmethod
    def default_Zusatsprüfung_bestanden():
        return "x"

    @staticmethod
    def default_Zusatsprüfung_nichgepruft():
        return "-"

    @staticmethod
    def default_Dokument():
        return "delete"

    @staticmethod
    def default_Wurzel():
        return "1"


    @staticmethod
    def default_geltungs():
        return "Geltungsbereich "
    @staticmethod
    def default_text_1():
        return "Bestätigung der Gültigkeit durch den Arbeitgeber/die Schweißaufsichtsperson für die folgenden 6 Monate (unter Bezug auf Abschnitt 9.2)"

    @staticmethod
    def default_pruf1():
        return "Prüfstük1"

    @staticmethod
    def default_pruf2():
        return "Prüfstük2"

    @staticmethod
    def default_Schweissnahteinzelheiten2():
        return " "

    @staticmethod
    def default_Werkstoff2():
        return " "

    @staticmethod
    def default_Nahtart2():
        return " "

    @staticmethod
    def default_werkstoffdicke():
        return 0

    @staticmethod
    def default_werkstoffdicke_1():
        return 0


    @staticmethod
    def default_prufsart():
        return "Prüfungsart"

    @staticmethod
    def default_prufsart2():
        return "Ausgefürt und bestanden"

    @staticmethod
    def default_prufsart3():
        return "nicht geprüft"

    @staticmethod
    def default_Datum9_2():
        return "Datum"
    @staticmethod
    def default_unterchrift9_2():
        return "Unterschrift"
    @staticmethod
    def default_Titl9_2():
        return "Dienststellung oder Titel"

    @staticmethod
    def default_Bezeichnung2():
        return "EN ISO 9606-2 ?? ? ?? ? ? t?? ?? ??"


    @staticmethod
    def default_Bezeichnung():
        return "EN ISO 9606-2 ?? ? ?? ? ? t?? ?? ??"
    @staticmethod
    def default_Fachkunde():
        return "Bestanden"


    def on_change_schutzgazzz(self,Schweißprozess):
        if(self.Schweißprozess == "131" or self.Schweißprozess == "141/131"):
            return "siehe Abschnitt 5.6"
        else:
            return " "

    def on_change_Sweisserr(self,Namedesschweisser):
        value_leg = self.Namedesschweisser.legitimation
        return value_leg
    def on_change_Sweisser_r(self,Namedesschweisser):
        value_leg_art = self.Namedesschweisser.legitimation_type
        return value_leg_art

    def on_change_Sweisser_2(self,Namedesschweisser):
        value__geburtsdatum = self.Namedesschweisser.birthday
        value_country_birth = self.Namedesschweisser.ort_birthday
        ret_val = str(value__geburtsdatum)+" \ "+value_country_birth
        return ret_val
    def on_change_Sweisser_3(self,Namedesschweisser):
        value__arbeitgeber = self.Namedesschweisser.employer.name
        return value__arbeitgeber

    def on_change_Sweiss_datum(self,datum_schweissen):
         valu = self.datum_schweissen+datetime.timedelta(days=730)
         return valu

    def on_change_schweissprocess(self,Schweißprozess):
        if(self.Schweißprozess == "131"):
                   return_value = "131"
                   return return_value
        if(self.Schweißprozess == "141"):
                   return_value = "141"
                   return return_value
        if(self.Schweißprozess == "141/131"):
                   return_value = "141/131"
                   return return_value
        else:
           if(self.Schweißprozess == "15"):
                   return_value = "15"
                   return return_value
    def on_change_schweissprocess2(self,Schweißprozess):
        if(self.Schweißprozess == "131"):
                   return_value = "MIG"
                   return return_value
        if(self.Schweißprozess == "141"):
                   return_value = "WIG"
                   return return_value
        if(self.Schweißprozess == "141/131"):
                   return_value = "WIG/MIG"
                   return return_value
        else:
           if(self.Schweißprozess == "15"):
                   return_value = "WPL"
                   return return_value

    def on_change_alles(self,Schweißprozess):
         space = " "
         valu1 ="EN ISO 9606-2"+space+ self.Schweißprozess
         valu2 = self.Produktform
         valu3 = self.Nahtart
         valu4 = self.Werkstoffgruppen
         valu5 = self.Schweisszusatze
         valu6 = self.werkstoffdicke
         valu7 = self.position_al1.code
         valu8 = self.Schweissnahteinzelheiten
         valufinl = valu1+space+valu2+space+valu3+space+valu4+space+valu5+space+"t"+str(valu6)+space+valu7+space+valu8
         return valufinl

    def on_change_alles2(self,Schweißprozess):
       if(self.Nahtart2 == "FW" and self.Nahtart == "BW"):
         space = " "
         valu1 ="EN ISO 9606-2"+space+ self.Schweißprozess
         valu2 = self.Produktform
         valu3 = self.Nahtart
         valu4 = self.Nahtart2
         valu41 = self.Werkstoffgruppen
         valu5 = self.Schweisszusatze
         if(self.werkstoffdicke_1 is not None):
           valu6 = self.werkstoffdicke_1
         else:
           valu6 = self.werkstoffdicke
         valu7 = self.Schweissposition_2
         valu8 = self.Schweissnahteinzelheiten2
         valufinl = valu1+space+valu2+space+valu4+space+valu41+space+valu5+space+"t"+str(valu6)+space+valu7+space+valu8
         return valufinl
       else:
         return " "

    def on_change_produktform(self,Produktform):
        if(self.Produktform == "P"):
               return_value = "P,T (beachte t und D)"
               return return_value
        if(self.Produktform == "T"  and self.rohraussendurchmesser > 25):
               return_value = "T, P"
               return return_value
        else:
           if(self.Produktform == "T"  and self.rohraussendurchmesser <= 25):
               return_value = "T"
               return return_value
    def on_change_nahtart(self,Nahtart):
        if(self.Nahtart == "BW" and self.Nahtart2 != "FW"):
               return_value = "BW, FW (siehe 5.4 b)"
               return return_value
        if(self.Nahtart == "BW" and self.Nahtart2 == "FW"):
               return_value = "BW, FW"
               return return_value
        else:
           if(self.Nahtart == "FW"):
               return_value = "FW"
               return return_value

    def on_change_werkstoff(self,Werkstoffgruppen):
        if(self.Werkstoffgruppen == "21" or self.Werkstoffgruppen == "22"):
               return_value = "21, 22"
               return return_value
        if(self.Werkstoffgruppen == "24" or self.Werkstoffgruppen == "25"):
               return_value = "24, 25"
               return return_value
        if(self.Werkstoffgruppen == "26"):
               return_value = "24, 25, 26"
               return return_value

        else:
            if(self.Werkstoffgruppen == "23"):
               return_value = "21, 22, 23"
               return return_value

    def on_change_ssSchweisszusatze(self,Schweisszusatze):
        if(self.Schweisszusatze == "nm"):
               return_value = "nm"
               return return_value
        if(self.Schweisszusatze == "nm/S" and self.Schweißprozess == "141/131"):
               return_value = "141 : nm; 131 : S"
               return return_value
        if(self.Schweisszusatze == "S" and (self.Schweißprozess =="141" or self.Schweißprozess == "15") ):
               return_value = "S,nm (Siehe Abschnitt 5.6)"
               return return_value
        else:
          if(self.Schweisszusatze == "S" and (self.Schweißprozess =="131" or self.Schweißprozess == "141/131") ):
               return_value = "S(Siehe Abschnitt 5.6)"
               return return_value

    def on_change_zelheiten(self,Schweissnahteinzelheiten):
        if(self.Schweissnahteinzelheiten == "ss nb"):
               return_value = "ss nb, ss mb, bs;FW:sl, ml"
               return return_value
        if(self.Schweissnahteinzelheiten == "sl"):
               return_value = "sl"
               return return_value
        if(self.Schweissnahteinzelheiten == "ml"):
               return_value = "sl, ml"
               return return_value
        else:
          if(self.Schweissnahteinzelheiten == "ss mb" or self.Schweissnahteinzelheiten == "bs"):
               return_value = "ss mb, bs, für FW:sl, ml"
               return return_value

    def on_change_werkstoffdicke2(self,werkstoffdicke):
        space =" "
        if(self.Produktform == "P" and self.Nahtart == "FW"):
          if(self.werkstoffdicke < 3):
            return_value = str(self.werkstoffdicke)+" - 3 mm"
            return return_value
          else:
            return_value = "t >= 3 mm"
            return return_value
        if(self.Produktform == "T" and self.Nahtart == "FW" and self.Nahtart2 != " "):
          if(self.werkstoffdicke < 3 and self.werkstoffdicke_1 < 3 and self.werkstoffdicke < self.werkstoffdicke_1):
            return_value  =str(self.werkstoffdicke)+" bis 3 mm"
            return return_value
          if(self.werkstoffdicke < 3 and self.werkstoffdicke_1 >= 3):
            return_value  ="t >= "+str(self.werkstoffdicke)+" mm"
            return return_value
          if(self.werkstoffdicke_1 < 3 and self.werkstoffdicke >= 3):
            return_value  ="t >= "+str(self.werkstoffdicke_1)+" mm"
            return return_value
          if(self.werkstoffdicke_1 >= 3 and self.werkstoffdicke >= 3):
            return_value  ="t >= 3 mm"
            return return_value
          else:
           if(self.werkstoffdicke < 3 and self.werkstoffdicke_1 < 3 and self.werkstoffdicke_1 < self.werkstoffdicke):
            return_value  =str(self.werkstoffdicke_1)+" bis 3 mm"
            return return_value
        if(self.Produktform == "T" and self.Nahtart == "FW" and self.Nahtart2 == " "):
           if(self.werkstoffdicke < 3):
            return_value  =str(self.werkstoffdicke)+" bis 3 mm"
            return return_value
           else:
            return_value  ="t >= 3 mm"
            return return_value

        if(self.Produktform == "T" and self.Nahtart == "BW"):
          if(self.werkstoffdicke < 3  and self.Nahtart2 ==" " ):
            return_value  = "BW "+str(round(0.5 * self.werkstoffdicke,1))+" - "+str(round(2 * self.werkstoffdicke,1))+" mm; FW: "+str(self.werkstoffdicke)+" - 3 mm"
            return return_value
          if(self.werkstoffdicke > 6  and self.Nahtart2 ==" " ):
            return_value  = "BW: t >= 6 mm; FW: t >= 3 mm"
            return return_value
          else:
              if(self.werkstoffdicke >= 3 and self.werkstoffdicke <= 6  and self.Nahtart2 ==" " ):
                 return_value  ="BW "+str(round(0.5 * self.werkstoffdicke,1))+" - "+str(round(2 * self.werkstoffdicke,1))+" mm; FW: t >= 3 mm"
                 return return_value

          if(self.werkstoffdicke < 3 and self.werkstoffdicke_1 < 3 and self.werkstoffdicke < self.werkstoffdicke_1 and self.Nahtart2 !=" "):
            return_value  ="BW: "+str(round(0.5 * self.werkstoffdicke,1))+" bis "+str(round(2 * self.werkstoffdicke_1,1))+" mm; FW: "+str(self.werkstoffdicke)+"bis 3 mm"
            return return_value
          if(self.werkstoffdicke < 3 and self.werkstoffdicke_1 >= 3 and self.werkstoffdicke_1 <= 6  and self.Nahtart2 !=" "):
            return_value  ="BW: "+str(round(0.5 * self.werkstoffdicke,1))+" bis "+str(round(2 * self.werkstoffdicke_1,1))+"FW: t >="+str(self.werkstoffdicke)
            return return_value

          if(self.werkstoffdicke_1 < 3 and self.werkstoffdicke >= 3 and self.werkstoffdicke <= 6  and self.Nahtart2 !=" "):
            return_value  ="BW: "+str(round(0.5 * self.werkstoffdicke_1,1))+" bis "+str(round(2 * self.werkstoffdicke,1))+"FW: t >="+str(self.werkstoffdicke_1)
            return return_value

          if(self.werkstoffdicke >= 3 and self.werkstoffdicke <= 6 and self.werkstoffdicke_1 >= 3 and self.werkstoffdicke_1 <= 6 and self.werkstoffdicke < self.werkstoffdicke_1  and self.Nahtart2 !=" "):
            return_value  ="BW: "+str(round(0.5 * self.werkstoffdicke,1))+" bis "+str(round(2 * self.werkstoffdicke_1,1))+" mm; FW: t >= 3mm"
            return return_value

          if(self.werkstoffdicke >= 3 and self.werkstoffdicke <= 6 and self.werkstoffdicke_1 >= 3 and self.werkstoffdicke_1 <= 6 and self.werkstoffdicke_1 < self.werkstoffdicke  and self.Nahtart2 !=" "):
            return_value  ="BW: "+str(round(0.5 * self.werkstoffdicke_1,1))+" bis "+str(round(2 * self.werkstoffdicke,1))+" mm; FW: t >= 3mm"
            return return_value

          if(self.werkstoffdicke > 6 and self.werkstoffdicke_1 >= 3 and self.werkstoffdicke_1 <= 6  and self.Nahtart2 !=" "):
            return_value  ="BW: t >= "+str(round(0.5 * self.werkstoffdicke_1,1))+"mm; FW: t >= 3 mm"
            return return_value

          if(self.werkstoffdicke_1 > 6 and self.werkstoffdicke >= 3 and self.werkstoffdicke <= 6  and self.Nahtart2 !=" "):
            return_value  ="BW: t >= "+str(round(0.5 * self.werkstoffdicke,1))+"mm; FW: t >= 3 mm"
            return return_value

          if(self.werkstoffdicke_1 > 6 and self.werkstoffdicke > 6  and self.Nahtart2 !=" "):
            return_value  ="BW: t >= 6mm ; FW: t >= 3 mm"
            return return_value
          else:
            if(self.werkstoffdicke < 3 and self.werkstoffdicke_1 < 3 and self.werkstoffdicke > self.werkstoffdicke_1  and self.Nahtart2 !=" "):
               return_value  = "BW: "+str(round(0.5 * self.werkstoffdicke_1,1))+" bis "+str(round(2 * self.werkstoffdicke,1))+" mm; FW: "+str(self.werkstoffdicke_1)+"bis 3 mm"
               return return_value

        if(self.Produktform == "P" and self.Nahtart == "BW" and self.Nahtart2 == "FW"):
            if(self.werkstoffdicke < 6 and self.Schweißprozess == "141/131"):
              return_value = str(round(0.5 * self.werkstoffdicke,1))+" - "+str(round(2 * self.werkstoffdicke,1))+" mm ; 141: "+str(round(0.5 * int(self.Wurzel),1))+" - "+str(round(2 * int(self.Wurzel),1))+"; 131: "+str(round(0.5 * (self.werkstoffdicke - int(self.Wurzel)),1))+" - "+str(round(2 * (self.werkstoffdicke - int(self.Wurzel)),1))+"nur mb"
              return return_value
            if(self.werkstoffdicke > 6 and (self.werkstoffdicke - int(self.Wurzel)) <= 6 and self.Schweißprozess == "141/131"):
              return_value = "t >= 6mm ; 141: "+str(round(0.5 * int(self.Wurzel),1))+" - "+str(round(2 * int(self.Wurzel),1))+"; 131: "+str(round(0.5 * (self.werkstoffdicke - int(self.Wurzel)),1))+" - "+str(round(2 * (self.werkstoffdicke - int(self.Wurzel)),1))+"nur mb"
              return return_value

            if(self.werkstoffdicke > 6 and (self.werkstoffdicke - int(self.Wurzel)) > 6 and self.Schweißprozess == "141/131"):
              return_value = "t >= 6 mm; 141 :"+str(round(0.5 * int(self.Wurzel),1))+" - "+str(round(2 * int(self.Wurzel),1))+"; 131: t >= 6(nur mb)"
              return return_value

            if(self.werkstoffdicke <= 6  and self.werkstoffdicke_1 >= 3 and self.Schweißprozess != "141/131"):
              return_value = "BW: "+str(round(0.5 * self.werkstoffdicke,1))+" - "+str(round(2 * self.werkstoffdicke,1))+" mm ; FW: >= 3 mm"
              return return_value

            if(self.werkstoffdicke > 6  and self.werkstoffdicke_1 >= 3 and self.Schweißprozess != "141/131"):
              return_value = "BW: t >= 6 mm; FW: t >= 3 mm "
              return return_value

            else:
               if(self.werkstoffdicke <= 6  and self.werkstoffdicke_1 < 3 and self.Schweißprozess != "141/131"):
                  return_value = "BW: "+str(round(0.5 * self.werkstoffdicke,1))+" - "+str(round(2 * self.werkstoffdicke,1))+" mm ; FW: "+str(self.werkstoffdicke_1)+" - 3mm"
                  return return_value


        else:
          if(self.Produktform == "P" and self.Nahtart == "BW" and self.Nahtart2 == " "):
            if(self.werkstoffdicke < 3  and self.Schweißprozess != "141/131"):
              return_value = "BW: "+str(round(0.5 * self.werkstoffdicke,1))+" - "+str(round(2 * self.werkstoffdicke,1))+" mm ; FW: "+str(self.werkstoffdicke)+" - 3mm"
              return return_value
            if(self.werkstoffdicke < 6 and self.Schweißprozess == "141/131"):
              return_value = str(round(0.5 * self.werkstoffdicke,1))+" - "+str(round(2 * self.werkstoffdicke,1))+" mm ; 141: "+str(round(0.5 * int(self.Wurzel),1))+" - "+str(round(2 * int(self.Wurzel),1))+"; 131: "+str(round(0.5 * (self.werkstoffdicke - int(self.Wurzel)),1))+" - "+str(round(2 * (self.werkstoffdicke - int(self.Wurzel)),1))+"nur mb"
              return return_value
            if(self.werkstoffdicke > 6 and (self.werkstoffdicke - int(self.Wurzel)) <= 6 and self.Schweißprozess == "141/131"):
              return_value = "t >= 6mm ; 141: "+str(round(0.5 * int(self.Wurzel),1))+" - "+str(round(2 * int(self.Wurzel),1))+"; 131: "+str(round(0.5 * (self.werkstoffdicke - int(self.Wurzel)),1))+" - "+str(round(2 * (self.werkstoffdicke - int(self.Wurzel)),1))+"nur mb"
              return return_value

            if(self.werkstoffdicke > 6 and (self.werkstoffdicke - int(self.Wurzel)) > 6 and self.Schweißprozess == "141/131"):
              return_value = "t >= 6 mm; 141 :"+str(round(0.5 * int(self.Wurzel),1))+" - "+str(round(2 * int(self.Wurzel),1))+"; 131: t >= 6(nur mb)"
              return return_value

            if(self.werkstoffdicke > 6 and self.Schweißprozess != "141/131"):
              return_value = "BW: t >= 6 mm; FW: t >= 3mm"
              return return_value

            else:
              if(self.werkstoffdicke >= 3 and self.werkstoffdicke <= 6 and self.Schweißprozess != "141/131"):
                return_value = "BW: "+str(round(0.5 * self.werkstoffdicke,1))+" - "+str(round(2 * self.werkstoffdicke,1))+" mm ; FW : t >= 3 "
                return return_value


    def on_change_rohraussendurchmesser2(self,rohraussendurchmesser):
        space = " "
        if(self.Produktform == "P"):
          if(self.position_al1.code =="PB" or self.position_al1.code == "PD" or self.position_al1.code == "PG" or self.position_al1.code == "PH" or self.position_al1.code == "PJ" or self.position_al1.code == "H-L045" or self.position_al1.code == "J-L045" or self.position_al1.code == "PG/PC" or self.position_al1.code == "PH/PC" or self.position_al1.code == "PJ/PC" or self.position_al1.code == "PB/PF" or self.position_al1.code == "PF/PD"):
            return_value = "D >= 500 mm"
            return return_value
          if(self.position_al1.code =="PE" or self.position_al1.code == "PF/PC"):
            return_value = "D >= 500 mm: PA, PB, PC: D >= 150 mm"
            return return_value
          if(self.position_al1.code =="PF" or self.position_al1.code == "PA/PF"):
            return_value = "D >= 500 mm: PA, PB: D >= 150 mm"
            return return_value
          else:
            if(self.position_al1.code =="PA" or self.position_al1.code == "PC" or self.position_al1.code == "PA/PC"):
              return_value = "D >= 150 mm"
              return return_value
        else:
          if(self.Produktform == "T"):
            if(self.rohraussendurchmesser <= 25 and self.rohraussendurchmesser_1 <= 25):
               if(self.rohraussendurchmesser < self.rohraussendurchmesser_1):
                 return_value = str(self.rohraussendurchmesser)+" bis "+str(2 * round(self.rohraussendurchmesser_1,1))
                 return return_value
               else:
                 return_value = str(self.rohraussendurchmesser_1)+" bis "+str(2 * round(self.rohraussendurchmesser,1))
                 return return_value
            if(self.rohraussendurchmesser <= 25 and self.rohraussendurchmesser_1 > 25):
                 return_value ="D >="+str(self.rohraussendurchmesser)+" mm"
                 return return_value
            if(self.rohraussendurchmesser > 25 and self.rohraussendurchmesser_1 <= 25):
                 return_value ="D >="+str(self.rohraussendurchmesser_1)+" mm"
                 return return_value
            else:
              if(self.rohraussendurchmesser > 25 and self.rohraussendurchmesser_1 > 25):
                 return_value = "D >= 25"
                 return return_value

    def on_change_Dok(self,Dokument):
        if(self.Dokument == "test3 zeilen"):
           valu_text = "In WPS Report Können in die Prüfungenbescheinigungen 3 Zeilen Bemerkungen mit jeweils... \n 90 Zeichen eingetragen werden. In WPS Reoprt können in die Prüfungenbescheinigungen ...  \n 3 zeilen Bemerkungen mit jeweils 90 zeichen eingetragen werden "
           return valu_text
        if(self.Dokument == "delete"):
           valu_text = " "
           return valu_text
        else:
          if(self.Dokument == "tuv abnahme"):
           valu_text = "Die Prüfung erfolgt im Einvernehmen mit dem Dachverständigen \n des TÜV Bayern Hessen Sachsen Südwest e.V. \n 3 Zeilen Bemerkungen mit jeweils 90 zeichen eigetragen werden"
           return valu_text

    def on_change_position(self,position_al1):
      if(self.position_al1 is not None):
        if((self.position_al1.code == "PA" or self.position_al1.code == "PB") and self.Nahtart == "FW" and self.Produktform == "P" and self.Schweissposition_2 ==" "):
               return_value = "PA,PB"
               return return_value
        if((self.position_al1.code == "PA" or self.position_al1.code == "PB") and self.Nahtart == "FW" and self.Produktform == "T" and self.Schweissposition_2 ==" "):
               return_value = "PA,PB(nur FW)"
               return return_value
        if((self.position_al1.code == "PA") and self.Nahtart == "BW"  and self.Schweissposition_2 ==" "):
               return_value = "PA,PB(nur FW)"
               return return_value
        if(self.position_al1.code == "PD" and self.Nahtart == "FW" and self.Produktform == "T" and self.Schweissposition_2 == " "):
               return_value = "PA,PB,PC,PD,PE,PF(nur P)"
               return return_value
        if(self.position_al1.code == "PF"  and self.Produktform == "T" and self.Schweissposition_2 == " "):
               return_value = "PA,PB(nur FW),PD(nur FW),PE,PF"
               return return_value
        if(self.position_al1.code == "PG"  and self.Produktform == "T" and self.Schweissposition_2 ==" "):
               return_value = "PA,PB(nur FW),PD(nur FW),PE,PG"
               return return_value
        if(self.position_al1.code == "PH" and self.Produktform == "T" and self.Schweissposition_2 ==" "):
               return_value = "PA,PB(nur FW),PD(nur FW),PE,PF,PH"
               return return_value
        if(self.position_al1.code == "PJ" and self.Produktform == "T" and self.Schweissposition_2 ==" "):
               return_value = "PA,PB(nur FW),PD(nur FW),PE,PG,PJ"
               return return_value
        if(self.position_al1.code == "PC" and self.Nahtart == "BW" and self.Schweissposition_2 ==" "):
               return_value = "PA,PB(nur FW),PC"
               return return_value
        if((self.position_al1.code == "H-LO45" or self.position_al1.code == "PH/PC") and self.Nahtart == "BW" and self.Produktform == "T" and self.Schweissposition_2 ==" "):
               return_value = "alles außer fallendes schweißen"
               return return_value
        if(self.position_al1.code == "PF/PC" and self.Nahtart == "BW" and self.Produktform == "T" and self.Schweissposition_2 ==" "):
               return_value = "alles außer PG"
               return return_value
        if(self.position_al1.code == "PG/PC" and self.Nahtart == "BW" and self.Produktform == "T" and self.Schweissposition_2 ==" "):
               return_value = "PA,PB(nur FW),PC,PD(nur FW),PE,PG"
               return return_value
        if(self.position_al1.code == "PJ/PC" and self.Nahtart == "BW" and self.Produktform == "T" and self.Schweissposition_2 ==" "):
               return_value = "alles außer steigendes schweißen"
               return return_value
        if(self.position_al1.code == "PG" and self.Produktform == "P" and self.Schweissposition_2 ==" "):
               return_value = "PG(nur P)"
               return return_value
        if(self.position_al1.code == "PB/PF" and self.Nahtart == "FW" and self.Produktform == "P" and self.Schweissposition_2 ==" "):
               return_value = "PA,PB,PF(nur P)"
               return return_value
        if(self.position_al1.code == "PC" and self.Nahtart == "BW" and self.Produktform == "P" and self.Schweissposition_2 ==" "):
               return_value = "PA,PB(nur FW),PC"
               return return_value
        if(self.position_al1.code == "PE" and self.Nahtart == "BW" and self.Produktform == "P" and self.Schweissposition_2 ==" "):
               return_value = "PA,PB,PC,PD,PE,PF(nur P)"
               return return_value
        if(self.position_al1.code == "PF" and self.Produktform == "P" and self.Schweissposition_2 ==" "):
               return_value = "PA,PB(nur FW),PF(nur P)"
               return return_value
        if(self.position_al1.code == "PF/PC" and self.Nahtart == "BW" and self.Produktform == "P" and self.Schweissposition_2 ==" "):
               return_value = "PA,PB(nur FW),PC,PF(nur P)"
               return return_value
        if(self.position_al1.code == "PA/PC" and self.Nahtart == "BW" and self.Produktform == "P" and self.Schweissposition_2 ==" "):
               return_value = "PA,PB(nur FW),PC"
               return return_value
        if(self.position_al1.code == "PA/PF" and self.Nahtart == "BW" and self.Produktform == "P" and self.Schweissposition_2 ==" "):
               return_value = "PA,PB(nur FW),PF(nur P)"
               return return_value
        if(self.position_al1.code == "H-L045" and self.Nahtart == "BW" and self.Produktform == "T" and self.Schweissposition_2 ==" "):
               return_value = "alle außer fallendes Schweißen"
               return return_value
        if(self.position_al1.code == "PF/PC" and self.Nahtart == "BW" and self.Produktform == "T" and self.Schweissposition_2 ==" "):
               return_value = "alle außer PG"
               return return_value


        else:
          if(self.position_al1.code == "PD" and self.Nahtart == "FW" and self.Produktform == "P" and self.Schweissposition_2 ==" "):
               return_value = "PA,PB,PC,PD,PE,PF(nur P)"
               return return_value
      else:
           return " "

    @fields.depends('Werkstoff2', 'Werkstoffgruppen')
    def on_change_wwerkstoff(self):
        if(self.Werkstoffgruppen =="21"):
            tab=[]
            tab.append(("EN AW_AI 99,0", "EN AW_AI 99,0 | 21 | DIN EN 573-3 | 3.0205"))
            tab.append(("EN AW_AI 99,5", "EN AW_AI 99,5 | 21 | DIN EN 573-3 | 3.0255"))
            tab.append(("EN AW_AI 99,7", "EN AW_AI 99,7 | 21 | DIN EN 573-3 | 3.0275"))
            tab.append(("EN AW_AI 99,8(A)", "EN AW_AI 99,8(A) | 21 | DIN EN 573-3"))
            tab.append((" ", " "))
            return tab
        if(self.Werkstoffgruppen =="26"):
            tab=[]
            tab.append(("EN AW_AI Cu4Mg1", "EN AW_AI Cu4Mg1 | 26 | DIN EN 573-3 | 3.1355"))
            tab.append(("EN AW_AI Cu4MgSi(A)", "EN AW_AI Cu4MgSi(A) | 26 | DIN EN 573-3 | 3.1325"))
            tab.append(("EN AW_AI Cu4PbMgMn", "EN AW_AI Cu4PbMgMn | 26 | DIN EN 573-3 | 3.1645"))
            tab.append(("EN AW_AI Cu4SiMg", "EN AW_AI Cu4SiMg | 26 | DIN EN 573-3 | 3.1255"))
            tab.append(("EN AW_AI Cu6BiPb", "EN AW_AI Cu6BiPb | 26 | DIN EN 573-3 | 3.1655"))
            tab.append((" ", " "))
            return tab

        if(self.Werkstoffgruppen =="23"):
            tab=[]
            tab.append(("EN AW_AI Mg0,7Si", "EN AW_AI Mg0,7Si | 23.1 | DIN EN 573-3"))
            tab.append(("EN AW_AI Mg0,7Si(A)", "EN AW_AI Mg0,7Si(A) | 23.1 | DIN EN 573-3"))
            tab.append(("EN AW_AI Mg1SiCu", "EN AW_AI Mg1SiCu | 23.1 | DIN EN 573-3 | 3.3211"))
            tab.append(("EN AW_AI MgSi", "EN AW_AI MgSi | 23.1 | DIN EN 573-3 | 3.3206"))
            tab.append(("EN AW_AI MgSiPb", "EN AW_AI MgSiPb | 23.1 | DIN EN 573-3 | 3.0612"))
            tab.append(("EN AW_AI Si1MgMn", "EN AW_AI Si1MgMn | 23.1 | DIN EN 573-3 | 3.2315"))
            tab.append(("EN AW_AI SiMg(A)", "EN AW_AI SiMg(A) | 23.1 | DIN EN 573-3 | 3.3210"))
            tab.append(("EN AW_AI Zn4,5Mg1", "EN AW_AI Zn4,5Mg1 | 23.2 | DIN EN 573-3 | 3.4335"))
            tab.append(("EN AW_AI Zn5,5MgCu", "EN AW_AI Zn5,5MgCu | 23.2 | DIN EN 573-3 | 3.4365"))
            tab.append(("EN AW_AI Zn5Mg3Cu", "EN AW_AI Zn5Mg3Cu | 23.2 | DIN EN 573-3 | 3.4345"))
            tab.append((" ", " "))
            return tab
        else:
            tab=[]
            tab.append((" ", " "))
            return tab

#DRUCKEN EN ISO 96062 FORMULAR

class PrintENISO14732Start(ModelView):
    'Print ISO 14732'
    __name__ = 'party.print_iso14732.start'
    from_date = fields.Date('From Date', required=True)
    to_date = fields.Date('To Date', required=True)
    company = fields.Many2One('party.iso14732', 'Bitte wählen', required=True)
    posted = fields.Boolean('Posted Move', help='Show only posted move')

    @staticmethod
    def default_from_date():
        Date = Pool().get('ir.date')
        return datetime.date(Date.today().year, 1, 1)

    @staticmethod
    def default_to_date():
        Date = Pool().get('ir.date')
        return Date.today()
    @staticmethod
    def default_to_date():
        Date = Pool().get('ir.date')
        return Date.today()

    @staticmethod
    def default_company():
        return Transaction().context.get('company')

    @staticmethod
    def default_posted():
        return False

#begin wizard

class PrintISO14732(Wizard):
    'Print ISO14732'
    __name__ = 'party.print_iso14732_'
    start = StateView('party.print_iso14732.start',
        'welding_certification.print_iso14732_cert_start_view_form', [
            Button('Cancel', 'end', 'tryton-cancel'),
            Button('Drucken', 'print_', 'tryton-print', default=True),
            ])
    print_ = StateReport('welding_certification.party.iso_14732_report')
    def do_print_(self, action):
        data = {
            'company': self.start.company.id,
            }
        return action, data



#end wizard
class ISO14732report(Report):
    __name__ = 'welding_certification.party.iso_14732_report'



    @classmethod
    def _get_records(cls, ids, model, data):
        Move = Pool().get('party.iso14732')

        clause = [

            ]


    @classmethod
    def get_context(cls, records, data):
        report_context = super(ISO14732report, cls).get_context(records, data)

        Company = Pool().get('party.iso14732')

        company = Company(data['company'])

        report_context['company'] = company
        report_context['Names_des_biediner'] = company.Name_des_Schweißers
        report_context['WPS_ID'] = company.WPS_ID.wps_nr
        report_context['prüf_beleg_nr'] = company.Beleg_nr
        report_context['Legitimation'] = company.Legitimation
        report_context['Art_Legitimation'] = company.Art_der_Legitimation
        report_context['Geburtsdatum_ort'] = company.Geburtsdatum_ort
        report_context['bestatigt'] = company.Erstellt_Geändert_von
        report_context['Prufnorm'] = company.Prufnorm
        report_context['Prüfung_der_Funktionskenntnisse'] = company.Prüfung_der_Funktionskenntnisse
        report_context['Fachkunde'] = company.Fachkunde
        report_context['schweissprocess'] = company.Schweißprozesse_ISO
        report_context['Schweiss_g'] = company.Schweißprozesse_ISO_g
        report_context['Schweisseinrichtung'] = company.Schweisseinrichtung1
        report_context['Schweisseinrichtung_g'] = company.Schweisseinrichtung_g
        report_context['Schweiss_einheit'] = company.Schweiss_einheit
        report_context['Schweiss_einheit_g'] = company.Schweiss_einheit_g
        report_context['Details_1'] = company.Details_1

        report_context['Direkt'] = company.Direkte_oder_ferngesteurte_Sichtprüfung
        report_context['Direkt_g'] = company.Direkte_g
        report_context['Automatische_Lichtbogenlänge1'] = company.Automatische_Kontrolle_der_Lichtbogenlänge
        report_context['Automatische_Lichtbogenlänge1_g'] = company.Automatische_g
        report_context['Automatisches_Nahtvervolgungssystem'] = company.Automatisches_Nahtvervolgungssystem
        report_context['Automatische_naht_g'] = company.Automatische_naht_g
        report_context['schweissposition'] = company.Schweißposition_din
        report_context['emzelheiten'] = company.Einzellagen_Mehrlagentechnik
        report_context['Schweissbadsicherung'] = company.Schweißbadsicherung
        report_context['Schweisszusatzeinlagen'] = company.Schweißzusatzeinlagen

        report_context['Details2'] = "Details für mechanisches Schweißen:"
        report_context['Details_2'] = company.Details_2
        if(company.Details_1 == "nach 4.2.3"):
             report_context['Direkt_title'] = "Direkte oder ferngesteurte Sichtprüfung:"
             report_context['Auto_title'] ="Automatische Kontrolle der Lichtbogenlänge:"
             report_context['Auto_naht'] ="Automatisches Nahtvervolgungssystem:"
             report_context['position_title'] ="Schweißposition:"
             report_context['emzelheiten_title'] ="Einzellagen-/Mehrlagentechnik:"
             report_context['Schweissbadsicherung_title'] ="Schweißbadsicherung:"
             report_context['Schweisszusatzeinlagen_title'] ="Schweißzusatzeinlagen:"
             report_context['Nahtsensor'] = " "
             report_context['automatische2'] = " "
             report_context['Einzellagen_Mehrlagentechnik2'] = " "
             report_context['Art_Schweisseinrichtung'] = " "

        else:
            if(company.Details_1 == "unbenutzt"):
                report_context['Direkt_title'] =" "
                report_context['Auto_title'] =" "
                report_context['Auto_naht'] =" "
                report_context['position_title'] =" "
                report_context['emzelheiten_title'] =" "
                report_context['Schweissbadsicherung_title'] =" "
                report_context['Schweisszusatzeinlagen_title'] =" "
                report_context['Nahtsensor'] = "Nahtsensor"
                report_context['automatische2'] = "Automatische Kontrolle der Lichtbogenlänge"
                report_context['Einzellagen_Mehrlagentechnik2'] = "Einzellagen/Mehrlagentechnik"
                report_context['Art_Schweisseinrichtung'] = "Art der Schweißeinrichtung"


        report_context['Nahtsensor_val'] = company.Nahtsensor2_2
        report_context['automatische2_val'] = company.Automatische_Kontrolle_der_Lichtbogenlänge2
        report_context['Einzellagen_Mehrlagentechnik2_val'] = company.Einzellagen_Mehrlagentechnik2
        report_context['Art_Schweisseinrichtung_val'] = company.Art_Schweisseinrichtung
        report_context['Einzellagen_Mehrlagentechnik_g'] = company.Einzellagen_Mehrlagentechnik_g
        report_context['Schweißbadsicherung_g'] = company.Schweißbadsicherung_g
        report_context['Schweißzusatzeinlagen_g'] = company.Schweißzusatzeinlagen_g
        report_context['Nahtsensor2_g'] = company.Nahtsensor2_g
        report_context['Lichtbogenlänge_g_2'] = company.Lichtbogenlänge_g_2
        report_context['Einzellagen_Mehrlagentechnik_g_2'] = company.Einzellagen_Mehrlagentechnik_g_2
        report_context['Art_Schweisseinrichtung_g'] = company.Art_Schweisseinrichtung_g
        report_context['Zusätzliche'] = company.Zusätzliche
        report_context['Zusätzliche2'] = company.Zusätzliche2
        report_context['Schweißverfahrenprüfung'] = company.Schweißverfahrenprüfung
        report_context['Schweißtechnische'] = company.Schweißtechnische
        report_context['Datumprüfung'] = company.Datum_Prufung
        report_context['Name_unterschrift'] = company.Name_unterschrift
        report_context['Standardprüftück'] = company.Standardprüftück
        report_context['Fertigungsprüfung'] = company.Fertigungsprüfung
        report_context['Prufer_Prufstelle'] = company.Prufer_Prufstelle
        report_context['document_nr'] = company.document_nr
        report_context['Datum_Schweissen'] = company.Datum_Schweissen
        report_context['ort'] = company.Ort
        report_context['bis'] = company.Gultig_bis
        indx_1 = len(company.Datumms5_3)
        tab_Datum = []
        tab_unterschrift = []
        tab_title = []
        for i in range(0,indx_1):
            tab_Datum.append(company.Datumms5_3[i].Datum)
            tab_unterschrift.append(company.Datumms5_3[i].Unterschrift)
            tab_title.append(company.Datumms5_3[i].Title)
        if(indx_1 == 1):
              report_context['Datum5_3_0'] = tab_Datum[0]
              report_context['Datum5_3_1'] = " "
              report_context['Datum5_3_2'] = " "
              report_context['unterschrift5_3_0'] = tab_unterschrift[0]
              report_context['unterschrift5_3_1'] = " "
              report_context['unterschrift5_3_2'] = " "
              report_context['title5_3_0'] = tab_title[0]
              report_context['title5_3_1'] = " "
              report_context['title5_3_2'] = " "

        if(indx_1 == 2):
              report_context['Datum5_3_0'] = tab_Datum[0]
              report_context['Datum5_3_1'] = tab_Datum[1]
              report_context['Datum5_3_2'] = " "
              report_context['unterschrift5_3_0'] = tab_unterschrift[0]
              report_context['unterschrift5_3_1'] = tab_unterschrift[1]
              report_context['unterschrift5_3_2'] = " "
              report_context['title5_3_0'] = tab_title[0]
              report_context['title5_3_1'] = tab_title[1]
              report_context['title5_3_2'] = " "

        else:
           if(indx_1 == 3):
              report_context['Datum5_3_0'] = tab_Datum[0]
              report_context['Datum5_3_1'] = tab_Datum[1]
              report_context['Datum5_3_2'] = tab_Datum[2]
              report_context['unterschrift5_3_0'] = tab_unterschrift[0]
              report_context['unterschrift5_3_1'] = tab_unterschrift[1]
              report_context['unterschrift5_3_2'] = tab_unterschrift[2]
              report_context['title5_3_0'] = tab_title[0]
              report_context['title5_3_1'] = tab_title[1]
              report_context['title5_3_2'] = tab_title[2]

        indx_2 = len(company.Datumms5)
        tab_Datum5 = []
        tab_unterschrift5 = []
        tab_title5 = []
        for j in range(0,indx_2):
            tab_Datum5.append(company.Datumms5[j].Datum)
            tab_unterschrift5.append(company.Datumms5[j].Unterschrift)
            tab_title5.append(company.Datumms5[j].Title)
        if(indx_2 == 1):
              report_context['Datum5_0'] = tab_Datum5[0]
              report_context['Datum5_1'] = " "
              report_context['Datum5_2'] = " "
              report_context['Datum5_3'] = " "
              report_context['Datum5_4'] = " "
              report_context['unterschrift5_0'] = tab_unterschrift5[0]
              report_context['unterschrift5_1'] = " "
              report_context['unterschrift5_2'] = " "
              report_context['unterschrift5_3'] = " "
              report_context['unterschrift5_4'] = " "
              report_context['title5_0'] = tab_title5[0]
              report_context['title5_1'] = " "
              report_context['title5_2'] = " "
              report_context['title5_3'] = " "
              report_context['title5_4'] = " "

        if(indx_2 == 2):
              report_context['Datum5_0'] = tab_Datum5[0]
              report_context['Datum5_1'] = tab_Datum5[1]
              report_context['Datum5_2'] = " "
              report_context['Datum5_3'] = " "
              report_context['Datum5_4'] = " "

              report_context['unterschrift5_0'] = tab_unterschrift5[0]
              report_context['unterschrift5_1'] = tab_unterschrift5[1]
              report_context['unterschrift5_2'] = " "
              report_context['unterschrift5_3'] = " "
              report_context['unterschrift5_4'] = " "


              report_context['title5_0'] = tab_title5[0]
              report_context['title5_1'] = tab_title5[1]
              report_context['title5_2'] = " "
              report_context['title5_3'] = " "
              report_context['title5_4'] = " "
        if(indx_2 == 4):
              report_context['Datum5_0'] = tab_Datum5[0]
              report_context['Datum5_1'] = tab_Datum5[1]
              report_context['Datum5_2'] = tab_Datum5[2]
              report_context['Datum5_3'] = tab_Datum5[3]
              report_context['Datum5_4'] = " "

              report_context['unterschrift5_0'] = tab_unterschrift5[0]
              report_context['unterschrift5_1'] = tab_unterschrift5[1]
              report_context['unterschrift5_2'] = tab_unterschrift5[2]
              report_context['unterschrift5_3'] = tab_unterschrift5[3]
              report_context['unterschrift5_4'] = " "


              report_context['title5_0'] = tab_title5[0]
              report_context['title5_1'] = tab_title5[1]
              report_context['title5_2'] = tab_title5[2]
              report_context['title5_3'] = tab_title5[3]
              report_context['title5_4'] = " "
        if(indx_2 == 5):
              report_context['Datum5_0'] = tab_Datum5[0]
              report_context['Datum5_1'] = tab_Datum5[1]
              report_context['Datum5_2'] = tab_Datum5[2]
              report_context['Datum5_3'] = tab_Datum5[3]
              report_context['Datum5_4'] = tab_Datum5[4]

              report_context['unterschrift5_0'] = tab_unterschrift5[0]
              report_context['unterschrift5_1'] = tab_unterschrift5[1]
              report_context['unterschrift5_2'] = tab_unterschrift5[2]
              report_context['unterschrift5_3'] = tab_unterschrift5[3]
              report_context['unterschrift5_4'] = tab_unterschrift5[4]


              report_context['title5_0'] = tab_title5[0]
              report_context['title5_1'] = tab_title5[1]
              report_context['title5_2'] = tab_title5[2]
              report_context['title5_3'] = tab_title5[3]
              report_context['title5_4'] = tab_title5[4]



        else:
           if(indx_2 == 3):
              report_context['Datum5_0'] = tab_Datum5[0]
              report_context['Datum5_1'] = tab_Datum5[1]
              report_context['Datum5_2'] = tab_Datum5[2]
              report_context['Datum5_3'] = " "
              report_context['Datum5_4'] = " "

              report_context['unterschrift5_0'] = tab_unterschrift5[0]
              report_context['unterschrift5_1'] = tab_unterschrift5[1]
              report_context['unterschrift5_2'] = tab_unterschrift5[2]
              report_context['unterschrift5_3'] = " "
              report_context['unterschrift5_4'] = " "

              report_context['title5_0'] = tab_title5[0]
              report_context['title5_1'] = tab_title5[1]
              report_context['title5_2'] = tab_title5[2]
              report_context['title5_3'] = " "
              report_context['title5_4'] = " "



        return report_context




#END


#DRUCKEN EN ISO 96062 FORMULAR

class PrintENISO96062Start(ModelView):
    'Print ISO 96062'
    __name__ = 'party.print_iso96062.start'
    from_date = fields.Date('From Date', required=True)
    to_date = fields.Date('To Date', required=True)
    company = fields.Many2One('party.iso96062', 'Bitte wählen', required=True)
    posted = fields.Boolean('Posted Move', help='Show only posted move')

    @staticmethod
    def default_from_date():
        Date = Pool().get('ir.date')
        return datetime.date(Date.today().year, 1, 1)

    @staticmethod
    def default_to_date():
        Date = Pool().get('ir.date')
        return Date.today()
    @staticmethod
    def default_to_date():
        Date = Pool().get('ir.date')
        return Date.today()

    @staticmethod
    def default_company():
        return Transaction().context.get('company')

    @staticmethod
    def default_posted():
        return False

#
class PrintISO96062(Wizard):
    'Print ISO96062'
    __name__ = 'party.print_iso96062_'
    start = StateView('party.print_iso96062.start',
        'welding_certification.print_iso96062_cert_start_view_form', [
            Button('Cancel', 'end', 'tryton-cancel'),
            Button('Drucken', 'print_', 'tryton-print', default=True),
            ])
    print_ = StateReport('welding_certification.party.iso_96062_report')
    def do_print_(self, action):
        data = {
            'company': self.start.company.id,
            }
        return action, data
#
class ISO96062report(Report):
    __name__ = 'welding_certification.party.iso_96062_report'


  
    @classmethod
    def _get_records(cls, ids, model, data):
        Move = Pool().get('party.iso96062')

        clause = [

            ]
 

    @classmethod
    def get_context(cls, records, data):
        report_context = super(ISO96062report, cls).get_context(records, data)

        Company = Pool().get('party.iso96062')

        company = Company(data['company'])

        report_context['company'] = company
        report_context['bezeichnung1'] = company.bezeichnung.Bezeichnung
        report_context['bezeichnung'] = company.Bezeichnung
        report_context['ort'] = company.ort
        report_context['space_pdf'] = company.space_pdf
        report_context['schutzgaz'] = company.schutzgaz.Bezeichnung
        report_context['hilfsstoffe'] = company.hilfsstoffe.Bezeichnung
        report_context['Bezeichnung2'] = company.Bezeichnung2
        report_context['pruf_prufstelle'] = company.prufstellle.prufstelle
        report_context['Unterschrift_p'] = company.Unterschrift_p
        report_context['Stromart_und_Polung'] = company.Stromart_und_Polung
        report_context['Stromart_und_Polung_gel'] = company.Stromart_und_Polung_gel
        report_context['wps_bezug'] = company.wps_bezug.wps_nr
        report_context['wps_bezug2'] = company.wps_bezug2.wps_nr
        report_context['pruf_pruff'] = company.pruf_pruff.name
        report_context['Norm'] = company.prufnorm
        report_context['pruf_nr_weitere'] = company.pruf_nr_weitere
        report_context['name_schweisser'] = company.Namedesschweisser.name
        report_context['Firma'] = company.Namedesschweisser.employer.name
        report_context['legitimation'] = company.legitimation
        report_context['Art_legitimation'] = company.Art_der_legitimation
        report_context['GDatum_ort'] = company.Gebursdatum_und_ort
        report_context['Arbeitgeber'] = company.Arbeitgeber
        report_context['Bemerkung'] = company.Bemerkung
        report_context['Fachkunde'] = company.Fachkunde
        report_context['schweißprocess'] = company.Schweißprozess
        report_context['schweißprocess_g'] = company.schweißprocess_Geltungs
        if(company.Produktform == "T"):
           report_context['Produktform'] = "T (Rohr)"
        else:
           report_context['Produktform'] = "P (Blech)"
        report_context['Produktform_g'] = company.produktform_Geltungs
        if((company.Nahtart == "FW" and company.Nahtart2 ==" ") or(company.Nahtart == "FW" and company.Nahtart2 =="FW")):
          report_context['Nahtart'] = "Kehlnaht (FW)"
        if(company.Nahtart == "BW" and company.Nahtart2 =="FW"):
          report_context['Nahtart'] = "BW / FW"
        else:
          if(company.Nahtart == "BW" and company.Nahtart2 ==" "):
            report_context['Nahtart'] = "Stumpfnaht (BW)"

        report_context['Nahtart_g'] = company.Nahtart_Geltungs
        report_context['werkstoffgruppe'] = company.Werkstoffgruppen
        report_context['werkstoffgruppe_g'] = company.werkstoff_Geltungs
        report_context['schweisusatz'] = company.Schweisszusatze
        report_context['schweisusatz_g'] = company.Schweisszusatze_Geltungs
        report_context['werkstoffdicke'] = company.werkstoffdicke
        report_context['werkstoffdicke_g'] = company.werkstoffdicke_g
        report_context['rohraussen'] = company.rohraussendurchmesser
        report_context['rohraussen_g'] = company.rohraussendurchmesser_g
        report_context['schweissposition'] = company.position_al1.code
        report_context['schweissposition_g'] = company.schweissposition_Geltungs
        report_context['schweissnahteinzelheiten'] = company.Schweissnahteinzelheiten
        report_context['schweissnahteinzelheiten_g'] = company.zelheiten_Geltungs
        report_context['hinweise'] = company.Hinweise
        report_context['schutzgaz_gel'] = company.schutzgaz_gel

        report_context['sichprufbestanden'] = company.sichprufung_bestanden
        report_context['sichnichtgeruft'] = company.sichprufung_nichgepruft1
        report_context['Durchprufbestanden'] = company.Durchprüfung_bestanden
        report_context['Durchnichtgepruft'] = company.Durchprüfung_nichgepruft1
        report_context['Bruchprufbestanden'] = company.Bruchprüfung_bestanden
        report_context['Bruchnichtgepruft'] = company.Bruchprüfung_nichgepruft1
        report_context['Biegprufbestanden'] = company.Biegeprüfung_bestanden
        report_context['Biegnichtgepruft'] = company.Biegeprüfung_nichgepruft1
        report_context['kerbprufbestanden'] = company.Kerbzugprüfung_bestanden
        report_context['kerbnichtgepruft'] = company.Kerbzugprüfung_nichgepruft1
        report_context['Makprufbestanden'] = company.Markprüfung_bestanden
        report_context['Maknichtgepruft'] = company.Markprüfung_nichgepruft1
        report_context['zusatzprufbestanden'] = company.Zusatsprüfung_bestanden
        report_context['zusatznichtgepruft'] = company.Zusatsprüfung_nichgepruft1
        datump = str(company.datum_prufung)
        pos1 = datump.find("-")
        teil1 = datump[0:pos1]
        teil2 = datump[pos1+1:len(datump)]
        pos2= teil2.find("-")
        teil2_1 = teil2[0:pos2]
        teil2_2 = teil2[pos2+1:len(teil2)]
        report_context['Datum_prufung'] = teil2_2+"."+teil2_1+"."+teil1
        datums = str(company.datum_schweissen)
        pos1 = datums.find("-")
        teil1 = datums[0:pos1]
        teil2 = datums[pos1+1:len(datums)]
        pos2= teil2.find("-")
        teil2_1 = teil2[0:pos2]
        teil2_2 = teil2[pos2+1:len(teil2)]
        report_context['Datum_schweissen'] = teil2_2+"."+teil2_1+"."+teil1
        datumbis = str(company.geltungs_bis)
        pos1 = datumbis.find("-")
        teil1 = datumbis[0:pos1]
        teil2 = datumbis[pos1+1:len(datumbis)]
        pos2= teil2.find("-")
        teil2_1 = teil2[0:pos2]
        teil2_2 = teil2[pos2+1:len(teil2)]
        report_context['Datum_dauer_bis'] = teil2_2+"."+teil2_1+"."+teil1



        indx = len(company.Datumms9_3)
        indx_2 = len(company.Datumms9_2)
        tab_Datum = []
        tab_unterschrift = []
        tab_title = []

        tab_Datum2 = []
        tab_unterschrift2 = []
        tab_title2 = []
        if(indx_2 > 0):
          for j in range(0,indx_2):
            tab_Datum2.append(company.Datumms9_2[j].Datum1)
            tab_unterschrift2.append(company.Datumms9_2[j].Unterschrift)
            tab_title2.append(company.Datumms9_2[j].Title)
          if(indx_2 == 1):
              datum21 = str(tab_Datum2[0])
              pos1 = datum21.find("-")
              teil1 = datum21[0:pos1]
              teil2 = datum21[pos1+1:len(datum21)]
              pos2= teil2.find("-")
              teil2_1 = teil2[0:pos2]
              teil2_2 = teil2[pos2+1:len(teil2)]
              report_context['Datum2_0'] = teil2_2+"."+teil2_1+"."+teil1
              report_context['Datum2_1'] = " "
              report_context['Datum2_2'] = " "
              report_context['tab_unterschrift2_0'] = tab_unterschrift2[0]
              report_context['tab_unterschrift2_1'] = " "
              report_context['tab_unterschrift2_2'] = " "
              report_context['tab_title2_0'] = tab_title2[0]
              report_context['tab_title2_1'] = " "
              report_context['tab_title2_2'] = " "
          if(indx_2 == 2):
              datum21 = str(tab_Datum2[0])
              pos1 = datum21.find("-")
              teil1 = datum21[0:pos1]
              teil2 = datum21[pos1+1:len(datum21)]
              pos2= teil2.find("-")
              teil2_1 = teil2[0:pos2]
              teil2_2 = teil2[pos2+1:len(teil2)]
              report_context['Datum2_0'] = teil2_2+"."+teil2_1+"."+teil1

              datum22 = str(tab_Datum2[1])
              pos12 = datum22.find("-")
              teil12 = datum22[0:pos12]
              teil22 = datum22[pos12+1:len(datum22)]
              pos22= teil22.find("-")
              teil2_12 = teil22[0:pos22]
              teil2_22 = teil2[pos22+1:len(teil22)]
              report_context['Datum2_1'] = teil2_22+"."+teil2_12+"."+teil12
              report_context['Datum2_2'] = " "
              report_context['tab_unterschrift2_0'] = tab_unterschrift2[0]
              report_context['tab_unterschrift2_1'] = tab_unterschrift2[1]
              report_context['tab_unterschrift2_2'] = " "
              report_context['tab_title2_0'] = tab_title2[0]
              report_context['tab_title2_1'] = tab_title2[1]
              report_context['tab_title2_2'] = " "
          else:
            if(indx_2 >= 3):
              datum21 = str(tab_Datum2[0])
              pos1 = datum21.find("-")
              teil1 = datum21[0:pos1]
              teil2 = datum21[pos1+1:len(datum21)]
              pos2= teil2.find("-")
              teil2_1 = teil2[0:pos2]
              teil2_2 = teil2[pos2+1:len(teil2)]
              report_context['Datum2_0'] = teil2_2+"."+teil2_1+"."+teil1

              datum22 = str(tab_Datum2[1])
              pos12 = datum22.find("-")
              teil12 = datum22[0:pos12]
              teil22 = datum22[pos12+1:len(datum22)]
              pos22= teil22.find("-")
              teil2_12 = teil22[0:pos22]
              teil2_22 = teil22[pos22+1:len(teil22)]
              report_context['Datum2_1'] = teil2_22+"."+teil2_12+"."+teil12

              datum3 = str(tab_Datum2[2])
              pos3 = datum3.find("-")
              teil31 = datum3[0:pos3]
              teil32 = datum3[pos3+1:len(datum3)]
              pos4= teil32.find("-")
              teil3_1 = teil32[0:pos4]
              teil3_2 = teil32[pos4+1:len(teil32)]
              report_context['Datum2_2'] = teil3_2+"."+teil3_1+"."+teil31
              report_context['tab_unterschrift2_0'] = tab_unterschrift2[0]
              report_context['tab_unterschrift2_1'] = tab_unterschrift2[1]
              report_context['tab_unterschrift2_2'] = tab_unterschrift2[2]
              report_context['tab_title2_0'] = tab_title2[0]
              report_context['tab_title2_1'] = tab_title2[1]
              report_context['tab_title2_2'] = tab_title2[2]
        else:
              report_context['Datum2_0'] = " "
              report_context['Datum2_1'] = " "
              report_context['Datum2_2'] = " "
              report_context['tab_unterschrift2_0'] = " "
              report_context['tab_unterschrift2_1'] = " "
              report_context['tab_unterschrift2_2'] = " "
              report_context['tab_title2_0'] = " "
              report_context['tab_title2_1'] = " "
              report_context['tab_title2_2'] = " "


        if(indx > 0):
          for i in range(0,indx):
            tab_Datum.append(company.Datumms9_3[i].Datum3)
            tab_unterschrift.append(company.Datumms9_3[i].Unterschrift3)
            tab_title.append(company.Datumms9_3[i].Title3)
          if(indx == 1):
              datum1 = str(tab_Datum[0])
              pos1 = datum1.find("-")
              teil1 = datum1[0:pos1]
              teil2 = datum1[pos1+1:len(datum1)]
              pos2= teil2.find("-")
              teil2_1 = teil2[0:pos2]
              teil2_2 = teil2[pos2+1:len(teil2)]
              report_context['Datum3_0'] = teil2_2+"."+teil2_1+"."+teil1
              report_context['Datum3_1'] = " "
              report_context['Datum3_2'] = " "
              report_context['tab_unterschrift3_0'] = tab_unterschrift[0]
              report_context['tab_unterschrift3_1'] = " "
              report_context['tab_unterschrift3_2'] = " "
              report_context['tab_title3_0'] = tab_title[0]
              report_context['tab_title3_1'] = " "
              report_context['tab_title3_2'] = " "
          if(indx == 2):
              datum1 = str(tab_Datum[0])
              pos1 = datum1.find("-")
              teil1 = datum1[0:pos1]
              teil2 = datum1[pos1+1:len(datum1)]
              pos2= teil2.find("-")
              teil2_1 = teil2[0:pos2]
              teil2_2 = teil2[pos2+1:len(teil2)]
              report_context['Datum3_0'] = teil2_2+"."+teil2_1+"."+teil1
              datum2 = str(tab_Datum[1])
              pos12 = datum2.find("-")
              teil12 = datum2[0:pos12]
              teil22 = datum2[pos12+1:len(datum2)]
              pos22= teil22.find("-")
              teil2_12 = teil22[0:pos22]
              teil2_22 = teil22[pos22+1:len(teil22)]
              report_context['Datum3_1'] = teil2_22+"."+teil2_12+"."+teil12
              report_context['Datum3_2'] = " "
              report_context['tab_unterschrift3_0'] = tab_unterschrift[0]
              report_context['tab_unterschrift3_1'] = tab_unterschrift[1]
              report_context['tab_unterschrift3_2'] = " "
              report_context['tab_title3_0'] = tab_title[0]
              report_context['tab_title3_1'] = tab_title[1]
              report_context['tab_title3_2'] = " "
          else:
            if(indx >= 3):
              datum1 = str(tab_Datum[0])
              pos1 = datum1.find("-")
              teil1 = datum1[0:pos1]
              teil2 = datum1[pos1+1:len(datum1)]
              pos2= teil2.find("-")
              teil2_1 = teil2[0:pos2]
              teil2_2 = teil2[pos2+1:len(teil2)]
              report_context['Datum3_0'] = teil2_2+"."+teil2_1+"."+teil1
              datum2 = str(tab_Datum[1])
              pos12 = datum2.find("-")
              teil12 = datum2[0:pos12]
              teil22 = datum2[pos12+1:len(datum2)]
              pos22= teil22.find("-")
              teil2_12 = teil22[0:pos22]
              teil2_22 = teil22[pos22+1:len(teil22)]
              report_context['Datum3_1'] = teil2_22+"."+teil2_12+"."+teil12

              datum3 = str(tab_Datum[2])
              pos13 = datum3.find("-")
              teil13 = datum3[0:pos13]
              teil23 = datum3[pos13+1:len(datum3)]
              pos23= teil23.find("-")
              teil2_13 = teil23[0:pos23]
              teil2_23 = teil23[pos23+1:len(teil23)]
              report_context['Datum3_2'] = teil2_23+"."+teil2_13+"."+teil13

              report_context['tab_unterschrift3_0'] = tab_unterschrift[0]
              report_context['tab_unterschrift3_1'] = tab_unterschrift[1]
              report_context['tab_unterschrift3_2'] = tab_unterschrift[2]
              report_context['tab_title3_0'] = tab_title[0]
              report_context['tab_title3_1'] = tab_title[1]
              report_context['tab_title3_2'] = tab_title[2]
        else:
              report_context['Datum3_0'] = " "
              report_context['Datum3_1'] = " "
              report_context['Datum3_2'] = " "
              report_context['tab_unterschrift3_0'] = " "
              report_context['tab_unterschrift3_1'] = " "
              report_context['tab_unterschrift3_2'] = " "
              report_context['tab_title3_0'] = " "
              report_context['tab_title3_1'] = " "
              report_context['tab_title3_2'] = " "


        return report_context
#end


#DRUCKEN WPS FORMULAR

class PrintWPSStart(ModelView):
    'Print ISO 96061'
    __name__ = 'party.print_wps.start'
    from_date = fields.Date('From Date', required=True)
    to_date = fields.Date('To Date', required=True)
    company = fields.Many2One('party.wps', 'Company', required=True)
    posted = fields.Boolean('Posted Move', help='Show only posted move')

    @staticmethod
    def default_from_date():
        Date = Pool().get('ir.date')
        return datetime.date(Date.today().year, 1, 1)

    @staticmethod
    def default_to_date():
        Date = Pool().get('ir.date')
        return Date.today()
    @staticmethod
    def default_to_date():
        Date = Pool().get('ir.date')
        return Date.today()

    @staticmethod
    def default_company():
        return Transaction().context.get('company')

    @staticmethod
    def default_posted():
        return False
class PrintWPS(Wizard):
    'Print WPS'
    __name__ = 'party.print_wps_'
    start = StateView('party.print_wps.start',
        'welding_certification.print_wps_cert_start_view_form', [
            Button('Cancel', 'end', 'tryton-cancel'),
            Button('Drucken', 'print_', 'tryton-print', default=True),
            ])
    print_ = StateReport('welding_certification.party.iso_wps_report')
    def do_print_(self, action):
        data = {
            'company': self.start.company.id,
            }
        return action, data
class ISOWPSreport(Report):
    __name__ = 'welding_certification.party.iso_wps_report'


  
    @classmethod
    def _get_records(cls, ids, model, data):
        Move = Pool().get('party.wps')

        clause = [

            ]
 

    @classmethod
    def get_context(cls, records, data):
        indx = 0
        report_context = super(ISOWPSreport, cls).get_context(records, data)

        Company = Pool().get('party.wps')

        company = Company(data['company'])

        report_context['company'] = company

        report_context['Erzeugnis'] = company.erzeugnis.Erzeugnis
        report_context['Bereich'] = company.bereich
        report_context['Hersteller'] = company.Herstellere
        report_context['Prufer_prufstelle'] = company.prufer_oder_prufsteller
        report_context['InternNr'] = company.intern_nr
        report_context['ProjektNr'] = company.Projekt_Nr
        report_context['BelegNr'] = company.Beleg_Nr
        report_context['ZeichnNr'] = company.Zeichn_Nr
        report_context['GeigneterSchweisser'] = company.Geigneter_Schweisser
        report_context['Formular'] = company.formular
        report_context['Nahtform'] = company.Nahtform
        report_context['revision'] = company.Revision
        report_context['wpsnr'] = company.wps_nr
        report_context['Nahtart'] = company.Nahtart
        report_context['classs'] = company.clss.CP
        report_context['ort'] = company.Ort
        report_context['wpqnr'] = company.wpqnr.Beleg_pruf
        report_context['Fugenbearbeitung'] = company.Fugenbearbeitung1
        report_context['Grundwerkstoffe1'] = company.grundwerkstoffe.Bezeichnung
        report_context['Grundwerkstoffe2'] = company.grundwerkstoffe2.Bezeichnung
        report_context['prozess'] = company.prozess.Code1
        report_context['tropfenubergang'] = company.tropfenubergang.code
        report_context['Werkstuckdicke1'] = company.Werkstuckdicke_1
        report_context['Werkstuckdicke2'] = company.Werkstuckdicke_2_
        report_context['Aussendurchmesser1'] = company.Aussendurchmesser_1
        report_context['Aussendurchmesser2'] = company.Aussendurchmesser_2_
        report_context['Mechanisierungsgrad'] = company.Mechanisierungsgrad
        report_context['Produktform'] = company.Produktform
        report_context['Nahtart'] = company.Nahtart
        report_context['Kehlnahtdicke'] = company.Kehlnahtdicke
        report_context['sweissposition'] = company.sweissposition.Code
        report_context['skizze'] = company.Billds.code
        report_context['image1'] = company.Billds.Bild
        report_context['naht'] = company.naht_nr.Code
        report_context['bildname'] = company.bild_name
        report_context['bildrechtsname'] = company.rechts_bild_name
        report_context['empfehlung'] = company.Empfehlumg
        report_context['sweisszusatz'] = company.sweisszusatz.Code
        report_context['WIGEUP'] = company.WIG_E_UP
        report_context['FM'] = company.FM
        report_context['Fabrikat'] = company.Fabrikat
        report_context['WIGEUP1'] = company.WIG_E_UP_1
        report_context['FM1'] = company.FM_1
        report_context['Fabrikat1'] = company.Fabrikat_1
        report_context['WIGEUP2'] = company.WIG_E_UP_2
        report_context['FM2'] = company.FM_2
        report_context['Fabrikat2'] = company.Fabrikat_2
        report_context['Sonderforschrifteninfo'] = company.Sonderforschriften_info
        report_context['liste_gase'] = company.liste_gase.gasbezeichung
        report_context['liste_gase1'] = company.liste_gase1.gasbezeichung
        report_context['liste_gase2'] = company.liste_gase2.gasbezeichung
        report_context['liste_gase3'] = company.liste_gase3.gasbezeichung
        report_context['wolframelektrodenart'] = company.wolframelektrodenart.Kurzzeichen
        report_context['wolframelektrodenart2'] = company.wolframelektrodenart2.Durchmesser
        report_context['Einzelheiteninfo'] = company.Einzelheiten_info
        report_context['Vorwaermtemperaturinfo'] = company.Vorwaermtemperatur_info
        report_context['Zwichenlagetemperaturinfo'] = company.Zwichenlagetemperatur_info
        report_context['Wasserstoffarminfo'] = company.Wasserstoffarm_info
        report_context['Haltetemperatur'] = company.Haltetemperatur
        report_context['Waermenachbehandlung'] = company.Waermenachbehandlung
        report_context['Aufheiz'] = company.Aufheiz
        report_context['Zeit'] = company.Zeit
        report_context['z_b'] = company.z_b
        report_context['Amplit'] = company.Amplit
        report_context['Amplit_1'] = company.Amplit_1
        report_context['Amplit_2'] = company.Amplit_2
        report_context['Einzelheitenpulsschweissen'] = company.Einzelheiten_pulsschweissen
        report_context['Stromkontakt'] = company.Stromkontakt
        report_context['Einzelheitenplasmaschweissen'] = company.Einzelheiten_plasmaschweissen
        report_context['Brenne'] = company.Brenne
        report_context['myphoto'] = company.photo
        indx = len(company.Einzelheiten_Schweißen)
        tab_raupe = []
        tab_prozess = []
        tab_scheisszuts = []
        tab_scheisszuts1 = []
        tab_stromstarke = []
        tab_spannung = []
        tab_Stromart_Polung = []
        tab_Drahtvorschub = []
        tab_Vorschub_geschwindigkeit = []
        tab_waermeeinbringung = []
        for i in range(0,indx):
            tab_raupe.append("\n"+company.Einzelheiten_Schweißen[i].SchweißRaupee+"\n")
            tab_prozess.append(company.Einzelheiten_Schweißen[i].Schweissprozess_1+"\t")
            tab_scheisszuts.append(company.Einzelheiten_Schweißen[i].Schweiszusaetze_1+"\t")
            tab_scheisszuts1.append(company.Einzelheiten_Schweißen[i].Schweiszusaetze_2+"\t")
            tab_stromstarke.append(company.Einzelheiten_Schweißen[i].stromst+"\t")
            tab_spannung.append(company.Einzelheiten_Schweißen[i].Spannung+"\t")
            tab_Stromart_Polung.append(company.Einzelheiten_Schweißen[i].Stromart_Polung+"\t")
            tab_Drahtvorschub.append(company.Einzelheiten_Schweißen[i].Drahtvorschub+"\t")
            tab_Vorschub_geschwindigkeit.append(company.Einzelheiten_Schweißen[i].Vorschub_geschwindigkeit+"\t")
            tab_waermeeinbringung.append(company.Einzelheiten_Schweißen[i].waermeeinbringung+"\t")
            i=i+1
        if(indx == 1):
              report_context['raupe0'] = tab_raupe[0]
              report_context['raupe1'] = " "
              report_context['raupe2'] = " "
              report_context['raupe3'] = " "
              report_context['raupe4'] = " "
              report_context['schweissprozess0'] = tab_prozess[0]
              report_context['schweissprozess1'] = " "
              report_context['schweissprozess2'] = " "
              report_context['schweissprozess3'] = " "
              report_context['schweissprozess4'] = " "
              report_context['Schweiszusaetze10'] = tab_scheisszuts[0]
              report_context['Schweiszusaetze11'] = " "
              report_context['Schweiszusaetze12'] = " "
              report_context['Schweiszusaetze13'] = " "
              report_context['Schweiszusaetze14'] = " "
              report_context['Schweiszusaetze20'] = tab_scheisszuts1[0]
              report_context['Schweiszusaetze21'] = " "
              report_context['Schweiszusaetze22'] = " "
              report_context['Schweiszusaetze23'] = " "
              report_context['Schweiszusaetze24'] = " "
              report_context['stromstarke0'] = tab_stromstarke[0]
              report_context['stromstarke1'] = " "
              report_context['stromstarke2'] = " "
              report_context['stromstarke3'] = " "
              report_context['stromstarke4'] = " "
              report_context['spannung0'] = tab_spannung[0]
              report_context['spannung1'] = " "
              report_context['spannung2'] = " "
              report_context['spannung3'] = " "
              report_context['spannung4'] = " "
              report_context['Stromart_Polung0'] = tab_Stromart_Polung[0]
              report_context['Stromart_Polung1'] = " "
              report_context['Stromart_Polung2'] = " "
              report_context['Stromart_Polung3'] = " "
              report_context['Stromart_Polung4'] = " "
              report_context['Drahtvorschub0'] = tab_Drahtvorschub[0]
              report_context['Drahtvorschub1'] = " "
              report_context['Drahtvorschub2'] = " "
              report_context['Drahtvorschub3'] = " "
              report_context['Drahtvorschub4'] = " "
              report_context['Vorschub_geschwindigkeit0'] = tab_Vorschub_geschwindigkeit[0]
              report_context['Vorschub_geschwindigkeit1'] = " "
              report_context['Vorschub_geschwindigkeit2'] = " "
              report_context['Vorschub_geschwindigkeit3'] = " "
              report_context['Vorschub_geschwindigkeit4'] = " "
              report_context['waermeeinbringung0'] = tab_waermeeinbringung[0]
              report_context['waermeeinbringung1'] = " "
              report_context['waermeeinbringung2'] = " "
              report_context['waermeeinbringung3'] = " "
              report_context['waermeeinbringung4'] = " "

        else :

            if(indx == 2):
                  report_context['raupe0'] = tab_raupe[0]
                  report_context['raupe1'] = tab_raupe[1]
                  report_context['raupe2'] = " "
                  report_context['raupe3'] = " "
                  report_context['raupe4'] = " "
                  report_context['schweissprozess0'] = tab_prozess[0]
                  report_context['schweissprozess1'] = tab_prozess[1]
                  report_context['schweissprozess2'] = " "
                  report_context['schweissprozess3'] = " "
                  report_context['schweissprozess4'] = " "
                  report_context['Schweiszusaetze10'] = tab_scheisszuts[0]
                  report_context['Schweiszusaetze11'] = tab_scheisszuts[1]
                  report_context['Schweiszusaetze12'] = " "
                  report_context['Schweiszusaetze13'] = " "
                  report_context['Schweiszusaetze14'] = " "
                  report_context['Schweiszusaetze20'] = tab_scheisszuts1[0]
                  report_context['Schweiszusaetze21'] = tab_scheisszuts1[1]
                  report_context['Schweiszusaetze22'] = " "
                  report_context['Schweiszusaetze23'] = " "
                  report_context['Schweiszusaetze24'] = " "
                  report_context['stromstarke0'] = tab_stromstarke[0]
                  report_context['stromstarke1'] = tab_stromstarke[1]
                  report_context['stromstarke2'] = " "
                  report_context['stromstarke3'] = " "
                  report_context['stromstarke4'] = " "
                  report_context['spannung0'] = tab_spannung[0]
                  report_context['spannung1'] = tab_spannung[1]
                  report_context['spannung2'] = " "
                  report_context['spannung3'] = " "
                  report_context['spannung4'] = " "
                  report_context['Stromart_Polung0'] = tab_Stromart_Polung[0]
                  report_context['Stromart_Polung1'] = tab_Stromart_Polung[1]
                  report_context['Stromart_Polung2'] = " "
                  report_context['Stromart_Polung3'] = " "
                  report_context['Stromart_Polung4'] = " "
                  report_context['Drahtvorschub0'] = tab_Drahtvorschub[0]
                  report_context['Drahtvorschub1'] = tab_Drahtvorschub[1]
                  report_context['Drahtvorschub2'] = " "
                  report_context['Drahtvorschub3'] = " "
                  report_context['Drahtvorschub4'] = " "
                  report_context['Vorschub_geschwindigkeit0'] = tab_Vorschub_geschwindigkeit[0]
                  report_context['Vorschub_geschwindigkeit1'] = tab_Vorschub_geschwindigkeit[1]
                  report_context['Vorschub_geschwindigkeit2'] = " "
                  report_context['Vorschub_geschwindigkeit3'] = " "
                  report_context['Vorschub_geschwindigkeit4'] = " "
                  report_context['waermeeinbringung0'] = tab_waermeeinbringung[0]
                  report_context['waermeeinbringung1'] = tab_waermeeinbringung[1]
                  report_context['waermeeinbringung2'] = " "
                  report_context['waermeeinbringung3'] = " "
                  report_context['waermeeinbringung4'] = " "

            else:

                if(indx == 3):
                   report_context['raupe0'] = tab_raupe[0]
                   report_context['raupe1'] = tab_raupe[1]
                   report_context['raupe2'] = tab_raupe[2]
                   report_context['raupe3'] = " "
                   report_context['raupe4'] = " "
                   report_context['schweissprozess0'] = tab_prozess[0]
                   report_context['schweissprozess1'] = tab_prozess[1]
                   report_context['schweissprozess2'] = tab_prozess[2]
                   report_context['schweissprozess3'] = " "
                   report_context['schweissprozess4'] = " "
                   report_context['Schweiszusaetze10'] = tab_scheisszuts[0]
                   report_context['Schweiszusaetze11'] = tab_scheisszuts[1]
                   report_context['Schweiszusaetze12'] = tab_scheisszuts[2]
                   report_context['Schweiszusaetze13'] = " "
                   report_context['Schweiszusaetze14'] = " "
                   report_context['Schweiszusaetze20'] = tab_scheisszuts1[0]
                   report_context['Schweiszusaetze21'] = tab_scheisszuts1[1]
                   report_context['Schweiszusaetze22'] = tab_scheisszuts1[2]
                   report_context['Schweiszusaetze23'] = " "
                   report_context['Schweiszusaetze24'] = " "
                   report_context['stromstarke0'] = tab_stromstarke[0]
                   report_context['stromstarke1'] = tab_stromstarke[1]
                   report_context['stromstarke2'] = tab_stromstarke[2]
                   report_context['stromstarke3'] = " "
                   report_context['stromstarke4'] = " "
                   report_context['spannung0'] = tab_spannung[0]
                   report_context['spannung1'] = tab_spannung[1]
                   report_context['spannung2'] = tab_spannung[2]
                   report_context['spannung3'] = " "
                   report_context['spannung4'] = " "
                   report_context['Stromart_Polung0'] = tab_Stromart_Polung[0]
                   report_context['Stromart_Polung1'] = tab_Stromart_Polung[1]
                   report_context['Stromart_Polung2'] = tab_Stromart_Polung[2]
                   report_context['Stromart_Polung3'] = " "
                   report_context['Stromart_Polung4'] = " "
                   report_context['Drahtvorschub0'] = tab_Drahtvorschub[0]
                   report_context['Drahtvorschub1'] = tab_Drahtvorschub[1]
                   report_context['Drahtvorschub2'] = tab_Drahtvorschub[2]
                   report_context['Drahtvorschub3'] = " "
                   report_context['Drahtvorschub4'] = " "
                   report_context['Vorschub_geschwindigkeit0'] = tab_Vorschub_geschwindigkeit[0]
                   report_context['Vorschub_geschwindigkeit1'] = tab_Vorschub_geschwindigkeit[1]
                   report_context['Vorschub_geschwindigkeit2'] = tab_Vorschub_geschwindigkeit[2]
                   report_context['Vorschub_geschwindigkeit3'] = " "
                   report_context['Vorschub_geschwindigkeit4'] = " "
                   report_context['waermeeinbringung0'] = tab_waermeeinbringung[0]
                   report_context['waermeeinbringung1'] = tab_waermeeinbringung[1]
                   report_context['waermeeinbringung2'] = tab_waermeeinbringung[2]
                   report_context['waermeeinbringung3'] = " "
                   report_context['waermeeinbringung4'] = " "

                else:
                   if(indx == 4):
                      report_context['raupe0'] = tab_raupe[0]
                      report_context['raupe1'] = tab_raupe[1]
                      report_context['raupe2'] = tab_raupe[2]
                      report_context['raupe3'] = tab_raupe[3]
                      report_context['raupe4'] = " "
                      report_context['schweissprozess0'] = tab_prozess[0]
                      report_context['schweissprozess1'] = tab_prozess[1]
                      report_context['schweissprozess2'] = tab_prozess[2]
                      report_context['schweissprozess3'] = tab_prozess[3]
                      report_context['schweissprozess4'] = " "
                      report_context['Schweiszusaetze10'] = tab_scheisszuts[0]
                      report_context['Schweiszusaetze11'] = tab_scheisszuts[1]
                      report_context['Schweiszusaetze12'] = tab_scheisszuts[2]
                      report_context['Schweiszusaetze13'] = tab_scheisszuts[3]
                      report_context['Schweiszusaetze14'] = " "
                      report_context['Schweiszusaetze20'] = tab_scheisszuts1[0]
                      report_context['Schweiszusaetze21'] = tab_scheisszuts1[1]
                      report_context['Schweiszusaetze22'] = tab_scheisszuts1[2]
                      report_context['Schweiszusaetze23'] = tab_scheisszuts1[3]
                      report_context['Schweiszusaetze24'] = " "
                      report_context['stromstarke0'] = tab_stromstarke[0]
                      report_context['stromstarke1'] = tab_stromstarke[1]
                      report_context['stromstarke2'] = tab_stromstarke[2]
                      report_context['stromstarke3'] = tab_stromstarke[3]
                      report_context['stromstarke4'] = " "
                      report_context['spannung0'] = tab_spannung[0]
                      report_context['spannung1'] = tab_spannung[1]
                      report_context['spannung2'] = tab_spannung[2]
                      report_context['spannung3'] = tab_spannung[3]
                      report_context['spannung4'] = " "
                      report_context['Stromart_Polung0'] = tab_Stromart_Polung[0]
                      report_context['Stromart_Polung1'] = tab_Stromart_Polung[1]
                      report_context['Stromart_Polung2'] = tab_Stromart_Polung[2]
                      report_context['Stromart_Polung3'] = tab_Stromart_Polung[3]
                      report_context['Stromart_Polung4'] = " "
                      report_context['Drahtvorschub0'] = tab_Drahtvorschub[0]
                      report_context['Drahtvorschub1'] = tab_Drahtvorschub[1]
                      report_context['Drahtvorschub2'] = tab_Drahtvorschub[2]
                      report_context['Drahtvorschub3'] = tab_Drahtvorschub[3]
                      report_context['Drahtvorschub4'] = " "
                      report_context['Vorschub_geschwindigkeit0'] = tab_Vorschub_geschwindigkeit[0]
                      report_context['Vorschub_geschwindigkeit1'] = tab_Vorschub_geschwindigkeit[1]
                      report_context['Vorschub_geschwindigkeit2'] = tab_Vorschub_geschwindigkeit[2]
                      report_context['Vorschub_geschwindigkeit3'] = tab_Vorschub_geschwindigkeit[3]
                      report_context['Vorschub_geschwindigkeit4'] = " "
                      report_context['waermeeinbringung0'] = tab_waermeeinbringung[0]
                      report_context['waermeeinbringung1'] = tab_waermeeinbringung[1]
                      report_context['waermeeinbringung2'] = tab_waermeeinbringung[2]
                      report_context['waermeeinbringung3'] = tab_waermeeinbringung[3]
                      report_context['waermeeinbringung4'] = " "
                   else:
                       if(indx == 0):
                          report_context['raupe0'] = " "
                          report_context['raupe1'] = " "
                          report_context['raupe2'] = " "
                          report_context['raupe3'] = " "
                          report_context['raupe4'] = " "
                          report_context['schweissprozess0'] = " "
                          report_context['schweissprozess1'] = " "
                          report_context['schweissprozess2'] = " "
                          report_context['schweissprozess3'] = " "
                          report_context['schweissprozess4'] = " "
                          report_context['Schweiszusaetze10'] = " "
                          report_context['Schweiszusaetze11'] = " "
                          report_context['Schweiszusaetze12'] = " "
                          report_context['Schweiszusaetze13'] = " "
                          report_context['Schweiszusaetze14'] = " "
                          report_context['Schweiszusaetze20'] = " "
                          report_context['Schweiszusaetze21'] = " "
                          report_context['Schweiszusaetze22'] = " "
                          report_context['Schweiszusaetze23'] = " "
                          report_context['Schweiszusaetze24'] = " "
                          report_context['stromstarke0'] = " "
                          report_context['stromstarke1'] = " "
                          report_context['stromstarke2'] = " "
                          report_context['stromstarke3'] = " "
                          report_context['stromstarke4'] = " "
                          report_context['spannung0'] = " "
                          report_context['spannung1'] = " "
                          report_context['spannung2'] = " "
                          report_context['spannung3'] = " "
                          report_context['spannung4'] = " "
                          report_context['Stromart_Polung0'] = " "
                          report_context['Stromart_Polung1'] = " "
                          report_context['Stromart_Polung2'] = " "
                          report_context['Stromart_Polung3'] = " "
                          report_context['Stromart_Polung4'] = " "
                          report_context['Drahtvorschub0'] = " "
                          report_context['Drahtvorschub1'] = " "
                          report_context['Drahtvorschub2'] = " "
                          report_context['Drahtvorschub3'] = " "
                          report_context['Drahtvorschub4'] = " "
                          report_context['Vorschub_geschwindigkeit0'] = " "
                          report_context['Vorschub_geschwindigkeit1'] = " "
                          report_context['Vorschub_geschwindigkeit2'] = " "
                          report_context['Vorschub_geschwindigkeit3'] = " "
                          report_context['Vorschub_geschwindigkeit4'] = " "
                          report_context['waermeeinbringung0'] = " "
                          report_context['waermeeinbringung1'] = " "
                          report_context['waermeeinbringung2'] = " "
                          report_context['waermeeinbringung3'] = " "
                          report_context['waermeeinbringung4'] = " "
                       else:
                          report_context['raupe0'] = tab_raupe[0]
                          report_context['raupe1'] = tab_raupe[1]
                          report_context['raupe2'] = tab_raupe[2]
                          report_context['raupe3'] = tab_raupe[3]
                          report_context['raupe4'] = tab_raupe[4]
                          report_context['schweissprozess0'] = tab_prozess[0]
                          report_context['schweissprozess1'] = tab_prozess[1]
                          report_context['schweissprozess2'] = tab_prozess[2]
                          report_context['schweissprozess3'] = tab_prozess[3]
                          report_context['schweissprozess4'] = tab_prozess[4]
                          report_context['Schweiszusaetze10'] = tab_scheisszuts[0]
                          report_context['Schweiszusaetze11'] = tab_scheisszuts[1]
                          report_context['Schweiszusaetze12'] = tab_scheisszuts[2]
                          report_context['Schweiszusaetze13'] = tab_scheisszuts[3]
                          report_context['Schweiszusaetze14'] = tab_scheisszuts[4]
                          report_context['Schweiszusaetze20'] = tab_scheisszuts1[0]
                          report_context['Schweiszusaetze21'] = tab_scheisszuts1[1]
                          report_context['Schweiszusaetze22'] = tab_scheisszuts1[2]
                          report_context['Schweiszusaetze23'] = tab_scheisszuts1[3]
                          report_context['Schweiszusaetze24'] = tab_scheisszuts1[4]
                          report_context['stromstarke0'] = tab_stromstarke[0]
                          report_context['stromstarke1'] = tab_stromstarke[1]
                          report_context['stromstarke2'] = tab_stromstarke[2]
                          report_context['stromstarke3'] = tab_stromstarke[3]
                          report_context['stromstarke4'] = tab_stromstarke[4]
                          report_context['spannung0'] = tab_spannung[0]
                          report_context['spannung1'] = tab_spannung[1]
                          report_context['spannung2'] = tab_spannung[2]
                          report_context['spannung3'] = tab_spannung[3]
                          report_context['spannung4'] = tab_spannung[4]
                          report_context['Stromart_Polung0'] = tab_Stromart_Polung[0]
                          report_context['Stromart_Polung1'] = tab_Stromart_Polung[1]
                          report_context['Stromart_Polung2'] = tab_Stromart_Polung[2]
                          report_context['Stromart_Polung3'] = tab_Stromart_Polung[3]
                          report_context['Stromart_Polung4'] = tab_Stromart_Polung[4]
                          report_context['Drahtvorschub0'] = tab_Drahtvorschub[0]
                          report_context['Drahtvorschub1'] = tab_Drahtvorschub[1]
                          report_context['Drahtvorschub2'] = tab_Drahtvorschub[2]
                          report_context['Drahtvorschub3'] = tab_Drahtvorschub[3]
                          report_context['Drahtvorschub4'] = tab_Drahtvorschub[4]
                          report_context['Vorschub_geschwindigkeit0'] = tab_Vorschub_geschwindigkeit[0]
                          report_context['Vorschub_geschwindigkeit1'] = tab_Vorschub_geschwindigkeit[1]
                          report_context['Vorschub_geschwindigkeit2'] = tab_Vorschub_geschwindigkeit[2]
                          report_context['Vorschub_geschwindigkeit3'] = tab_Vorschub_geschwindigkeit[3]
                          report_context['Vorschub_geschwindigkeit4'] = tab_Vorschub_geschwindigkeit[4]
                          report_context['waermeeinbringung0'] = tab_waermeeinbringung[0]
                          report_context['waermeeinbringung1'] = tab_waermeeinbringung[1]
                          report_context['waermeeinbringung2'] = tab_waermeeinbringung[2]
                          report_context['waermeeinbringung3'] = tab_waermeeinbringung[3]
                          report_context['waermeeinbringung4'] = tab_waermeeinbringung[4]


        return report_context


#END

class PrintISO96061Start(ModelView):
    'Print ISO 96061'
    __name__ = 'party.print_iso_96061.start'
    from_date = fields.Date('From Date', required=True)
    to_date = fields.Date('To Date', required=True)
    company = fields.Many2One('welding.iso96061', 'Bitte wählen', required=True)
    posted = fields.Boolean('Posted Move', help='Show only posted move')

    @staticmethod
    def default_from_date():
        Date = Pool().get('ir.date')
        return datetime.date(Date.today().year, 1, 1)

    @staticmethod
    def default_to_date():
        Date = Pool().get('ir.date')
        return Date.today()
    @staticmethod
    def default_to_date():
        Date = Pool().get('ir.date')
        return Date.today()

    @staticmethod
    def default_company():
        return Transaction().context.get('company')

    @staticmethod
    def default_posted():
        return False

class PrintISO96061(Wizard):
    'Print ISO 960612'
    __name__ = 'party.print_iso_96061'
    start = StateView('party.print_iso_96061.start',
        'welding_certification.print_iso_cert_start_view_form', [
            Button('Cancel', 'end', 'tryton-cancel'),
            Button('Drucken', 'print_', 'tryton-print', default=True),
            ])
    print_ = StateReport('welding_certification.party.iso_96061_report')
    def do_print_(self, action):
        data = {
            'company': self.start.company.id,
            }
        return action, data
class ISO96061report(Report):
    __name__ = 'welding_certification.party.iso_96061_report'


  
    @classmethod
    def _get_records(cls, ids, model, data):
        Move = Pool().get('welding.iso96061')

        clause = [
           
            ]
   
    @classmethod
    def get_context(cls, records, data):
        report_context = super(ISO96061report, cls).get_context(records, data)

        Company = Pool().get('welding.iso96061')
        
        company = Company(data['company'])
        title = company.Name_des_schweißers.name
        report_context['company'] = company
        report_context['legitimation'] = company.legitimation
        report_context['Bezeichnung_1'] = company.Bezeichnung_1
        report_context['bemerkung'] = company.bemerkung
        report_context['wps_bezug_info1'] =  "WPS-ID-00"+str(company.wps_bezug1.wps_nr)
        report_context['prufstellle'] = company.prufstellle.prufstelle
        report_context['prufstellle_ort'] = company.prufstellle.ort
        report_context['ort'] = company.ort
        report_context['date_ausgabe'] = company.date_ausgabe
        report_context['prufstellle_unterschrift'] = company.Unterschrift_p
        report_context['Unterschrift_p'] = company.Unterschrift_p
        report_context['art_der_legitimation'] = company.Art_der_legitimation
        report_context['employer'] = company.Name_des_schweißers.name
        report_context['birthday'] = company.Gebursdatum_und_ort
        report_context['arbeitgeber'] = company.Arbeitgeber
        report_context['adress'] = company.Name_des_schweißers.addresses[0].street
        report_context['prufnorm'] = company.prufnorm
        report_context['Fachkunde'] = company.Fachkunde
        report_context['hinweise_gel'] = company.hinweise_gel
        report_context['logo_company'] = company.logo_company
        report_context['photo2'] = company.photo2
        report_context['weitere_beleg_nr'] = company.weitere_beleg_nr
        report_context['prufer_prufstelle_beleg_nr'] = company.prufer_prufstelle_beleg_nr
        report_context['schweisprozesse'] = company.schweißprozess
        report_context['schweißprocess_geltungs'] = company.schweißprocess_Geltungs
        report_context['Artdeswerkstoff'] = company.Artdeswerkstoff
        report_context['Artdeswerkstoff_g'] = company.Artdeswerkstoff_Geltungs
        if(company.Produktform == "P"):
            report_context['Produktform'] = "P (Blech)"
        else:
            report_context['Produktform'] = "T (Rohr)"

        report_context['Produktform_Geltungs'] = company.Produktform_Geltungs
        if(company.Nahtart == "FW"):
            report_context['Nahtart'] ="FW (Kehlnaht)"
        else:
          if(company.Nahtart == "BW"):
            report_context['Nahtart'] ="BW (Stumpfnaht)"
          else:
            report_context['Nahtart'] ="FW/BW"

        report_context['prufer_prufstelle_beleg_nr'] = company.prufer_prufstelle_beleg_nr
        report_context['Nahtart_Geltungs'] = company.Nahtart_Geltungs
        report_context['werkstoffgruppe'] = company.werkstoffgruppe
        report_context['werkstoffgruppe_Geltungs'] = company.werkstoffgruppe_geltungs
        report_context['Grundwerkstoffes'] = company.grundwerkstoffe.Bezeichnung
        report_context['werkstoffgruppe_Schweisszusatz'] = company.werkstoffgruppe_schweisszusatz_info_1
        report_context['werkstoffgruppe_Schweisszusatz_g'] = company.werkstoffgruppe_schweisszusatz_Geltungs_info_1
        report_context['Schweisszusatz'] = company.sweisszusatz.Code
        report_context['Schweisszusatz_g'] = company.Schweisszusatz_Geltungs
        report_context['Bezeichnung'] = company.Bezeichnung_
        report_context['Bezeichnung2'] = company.bezeichnung.Bezeichnung
        report_context['weitere_beleg_nr_'] = company.weitere_beleg_nr
        report_context['Schutzgas'] = company.schutzgaz.Bezeichnung
        report_context['Hilfsstoffe'] = company.hilfsstoffe.Bezeichnung
        report_context['Werkstoffdicke'] = company.Werkstoffdicke
        report_context['Werkstoffdicke_g'] = company.Werkstoffdicke_Geltungs
        report_context['dicke_des_Schweißgutes'] = company.dicke_des_Schweißgutes
        report_context['dicke_des_Schweißgutes_g'] = company.dicke_des_Schweißgutes_Geltungs
        report_context['Stromart_und_Polung'] = company.Stromart_und_Polung
        report_context['Wurzel'] = company.Wurzel
        report_context['Schweißposition'] = company.schweisspos.code
        report_context['Schweißposition_g'] = company.Schweißposition_Geltungs
        report_context['Schweißnahteinezelheiten'] = company.Schweißnahteinezelheiten_1
        report_context['Schweißnahteinezelheiten_g'] = company.Schweissnahteinezelheiten_Geltungs
        report_context['Mehrlageg_einlageg'] = company.Mehrlageg_einlageg1
        report_context['Mehrlageg_einlageg1_Geltungs'] = company.Mehrlageg_einlageg1_Geltungs
        report_context['Erganzende2'] = company.Erganzende2
        report_context['sichtprufung_aus_und_bestanden'] = company.sichtprufung_aus_und_bestanden
        report_context['sichtprufung_nich_geprüft'] = company.sichtprufung_nich_geprüft1
        report_context['Durchstrahlungsprüfung_aus_und_bestanden'] = company.Durchstrahlungsprüfung_aus_und_bestanden
        report_context['Durchstrahlungsprüfung_nich_geprüft'] = company.Durchstrahlungsprüfung_nich_geprüft1
        report_context['Bruchprufung_aus_und_bestanden'] = company.Bruchprufung_aus_und_bestanden
        report_context['Bruchprufung_nich_geprüft'] = company.Bruchprufung_nich_geprüft1
        report_context['Biegeprufung_aus_und_bestanden'] = company.Biegeprufung_aus_und_bestanden
        report_context['Biegeprufung_nich_geprüft'] = company.Biegeprufung_nich_geprüft1
        report_context['Kerbzugprufung_aus_und_bestanden'] = company.Kerbzugprufung_aus_und_bestanden
        report_context['Kerbzugprufung_nich_geprüft'] = company.Kerbzugprufung_nich_geprüft1
        report_context['Makro_unter_aus_und_bestanden'] = company.Makro_unter_aus_und_bestanden
        report_context['Makro_unter_nich_geprüft'] = company.Makro_unter_nich_geprüft1
        report_context['zusatzprüfungen_aus_und_bestanden'] = company.zusatzprüfungen_aus_und_bestanden
        report_context['zusatzprüfungen_nich_geprüft'] = company.zusatzprüfungen_nich_geprüft1
        report_context['prufer_prufstelle'] = company.Prufers_oder_prufstelle

        datump = str(company.date_pruf)
        pos1 = datump.find("-")
        teil1 = datump[0:pos1]
        teil2 = datump[pos1+1:len(datump)]
        pos2= teil2.find("-")
        teil2_1 = teil2[0:pos2]
        teil2_2 = teil2[pos2+1:len(teil2)]
        report_context['Datum_der_prüfing'] = teil2_2+"."+teil2_1+"."+teil1

        datums = str(company.date_schweissenn)
        pos1 = datums.find("-")
        teil1 = datums[0:pos1]
        teil2 = datums[pos1+1:len(datums)]
        pos2= teil2.find("-")
        teil2_1 = teil2[0:pos2]
        teil2_2 = teil2[pos2+1:len(teil2)]
        report_context['Datum_des_Schweissen'] = teil2_2+"."+teil2_1+"."+teil1

        datumbis = str(company.Gultigkeitsdauer)
        pos1 = datumbis.find("-")
        teil1 = datumbis[0:pos1]
        teil2 = datumbis[pos1+1:len(datumbis)]
        pos2= teil2.find("-")
        teil2_1 = teil2[0:pos2]
        teil2_2 = teil2[pos2+1:len(teil2)]
        report_context['Gültigkeitsdauer_bis'] = teil2_2+"."+teil2_1+"."+teil1

        report_context['Ort'] = company.Ort
        report_context['grunddd'] = company.grundwerkstoffe.Bezeichnung
        report_context['Erganzende2'] = company.Erganzende2
        report_context['pruf_nr'] = company.pruf_nr
        report_context['wps_bezug_info'] = "WPS-ID-00"+str(company.wps_bezug.wps_nr)
        report_context['Bezeichnung_tempo'] = company.Bezeichnung_tempo
        report_context['Gültigkeitsdauer'] = company.Gültigkeitsdauer
        report_context['Prufstuckdurchmesserr'] = company.Prufstuckdurchmesserr
        report_context['Prufstuckdurchmesserr_g'] = company.Prufstuckdurchmesser_Geltungs

        if(len(company.Datumms9_3) != 0):

          indx = len(company.Datumms9_3)
          tab_Datum = []
          tab_unterschrift = []
          tab_title = []
          for i in range(0,indx):
            tab_Datum.append(company.Datumms9_3[i].Datum)
            tab_unterschrift.append(company.Datumms9_3[i].Unterschrift)
            tab_title.append(company.Datumms9_3[i].Title)
          if(indx == 1):
              datum1 = str(tab_Datum[0])
              pos1 = datum1.find("-")
              teil1 = datum1[0:pos1]
              teil2 = datum1[pos1+1:len(datum1)]
              pos2= teil2.find("-")
              teil2_1 = teil2[0:pos2]
              teil2_2 = teil2[pos2+1:len(teil2)]
              report_context['Datum3_0'] = teil2_2+"."+teil2_1+"."+teil1
              report_context['Datum3_1'] = " "
              report_context['Datum3_2'] = " "
              report_context['tab_unterschrift3_0'] = tab_unterschrift[0]
              report_context['tab_unterschrift3_1'] = " "
              report_context['tab_unterschrift3_2'] = " "
              report_context['tab_title3_0'] = tab_title[0]
              report_context['tab_title3_1'] = " "
              report_context['tab_title3_2'] = " "
          if(indx == 2):
              datum1 = str(tab_Datum[0])
              pos1 = datum1.find("-")
              teil1 = datum1[0:pos1]
              teil2 = datum1[pos1+1:len(datum1)]
              pos2= teil2.find("-")
              teil2_1 = teil2[0:pos2]
              teil2_2 = teil2[pos2+1:len(teil2)]
              report_context['Datum3_0'] = teil2_2+"."+teil2_1+"."+teil1

              datum2 = str(tab_Datum[1])
              pos3 = datum2.find("-")
              teil3 = datum2[0:pos3]
              teil4 = datum2[pos3+1:len(datum2)]
              pos4= teil4.find("-")
              teil4_1 = teil4[0:pos4]
              teil4_2 = teil4[pos4+1:len(teil4)]
              report_context['Datum3_1'] = teil4_2+"."+teil4_1+"."+teil3
              report_context['Datum3_2'] = " "
              report_context['tab_unterschrift3_0'] = tab_unterschrift[0]
              report_context['tab_unterschrift3_1'] = tab_unterschrift[1]
              report_context['tab_unterschrift3_2'] = " "
              report_context['tab_title3_0'] = tab_title[0]
              report_context['tab_title3_1'] = tab_title[1]
              report_context['tab_title3_2'] = " "

          else:
           if(indx >= 3):
              datum1 = str(tab_Datum[0])
              pos1 = datum1.find("-")
              teil1 = datum1[0:pos1]
              teil2 = datum1[pos1+1:len(datum1)]
              pos2= teil2.find("-")
              teil2_1 = teil2[0:pos2]
              teil2_2 = teil2[pos2+1:len(teil2)]
              report_context['Datum3_0'] = teil2_2+"."+teil2_1+"."+teil1

              datum2 = str(tab_Datum[1])
              pos3 = datum2.find("-")
              teil3 = datum2[0:pos3]
              teil4 = datum2[pos3+1:len(datum2)]
              pos4= teil4.find("-")
              teil4_1 = teil4[0:pos4]
              teil4_2 = teil4[pos4+1:len(teil4)]
              report_context['Datum3_1'] = teil4_2+"."+teil4_1+"."+teil3

              datum3 = str(tab_Datum[2])
              pos5 = datum3.find("-")
              teil5 = datum3[0:pos5]
              teil6 = datum3[pos5+1:len(datum3)]
              pos6= teil6.find("-")
              teil6_1 = teil6[0:pos6]
              teil6_2 = teil6[pos6+1:len(teil6)]
              report_context['Datum3_2'] = teil6_2+"."+teil6_1+"."+teil5
              report_context['tab_unterschrift3_0'] = tab_unterschrift[0]
              report_context['tab_unterschrift3_1'] = tab_unterschrift[1]
              report_context['tab_unterschrift3_2'] = tab_unterschrift[2]
              report_context['tab_title3_0'] = tab_title[0]
              report_context['tab_title3_1'] = tab_title[1]
              report_context['tab_title3_2'] = tab_title[2]
        else:
              report_context['Datum3_0'] = " "
              report_context['Datum3_1'] = " "
              report_context['Datum3_2'] = " "
              report_context['tab_unterschrift3_0'] = " "
              report_context['tab_unterschrift3_1'] = " "
              report_context['tab_unterschrift3_2'] = " "
              report_context['tab_title3_0'] = " "
              report_context['tab_title3_1'] = " "
              report_context['tab_title3_2'] = " "


        if(len(company.Datumms9_2) != 0):
          indx_1 = len(company.Datumms9_2)
          tab_Datum1 = []
          tab_unterschrift1 = []
          tab_title1 = []

          for j in range(0,indx_1):
            tab_Datum1.append(company.Datumms9_2[j].Datum)
            tab_unterschrift1.append(company.Datumms9_2[j].Unterschrift)
            tab_title1.append(company.Datumms9_2[j].Title)
          if(indx_1 == 1):
              datum1 = str(tab_Datum1[0])
              pos1 = datum1.find("-")
              teil1 = datum1[0:pos1]
              teil2 = datum1[pos1+1:len(datum1)]
              pos2= teil2.find("-")
              teil2_1 = teil2[0:pos2]
              teil2_2 = teil2[pos2+1:len(teil2)]
              report_context['Datum2_0'] = teil2_2+"."+teil2_1+"."+teil1
              report_context['Datum2_1'] = " "
              report_context['Datum2_2'] = " "
              report_context['Datum2_3'] = " "
              report_context['Datum2_4'] = " "
              report_context['tab_unterschrift2_0'] = tab_unterschrift1[0]
              report_context['tab_unterschrift2_1'] = " "
              report_context['tab_unterschrift2_2'] = " "
              report_context['tab_unterschrift2_3'] = " "
              report_context['tab_unterschrift2_4'] = " "
              report_context['tab_title2_0'] = tab_title1[0]
              report_context['tab_title2_1'] = " "
              report_context['tab_title2_2'] = " "
              report_context['tab_title2_3'] = " "
              report_context['tab_title2_4'] = " "
          if(indx_1 == 2):
              datum1 = str(tab_Datum1[0])
              pos1 = datum1.find("-")
              teil1 = datum1[0:pos1]
              teil2 = datum1[pos1+1:len(datum1)]
              pos2= teil2.find("-")
              teil2_1 = teil2[0:pos2]
              teil2_2 = teil2[pos2+1:len(teil2)]
              report_context['Datum2_0'] = teil2_2+"."+teil2_1+"."+teil1

              datum2 = str(tab_Datum1[1])
              pos3 = datum2.find("-")
              teil3 = datum2[0:pos3]
              teil4 = datum2[pos3+1:len(datum2)]
              pos4= teil4.find("-")
              teil4_1 = teil4[0:pos4]
              teil4_2 = teil4[pos4+1:len(teil4)]
              report_context['Datum2_1'] = teil4_2+"."+teil4_1+"."+teil3

              report_context['Datum2_2'] = " "
              report_context['Datum2_3'] = " "
              report_context['Datum2_4'] = " "
              report_context['tab_unterschrift2_0'] = tab_unterschrift1[0]
              report_context['tab_unterschrift2_1'] = tab_unterschrift1[1]
              report_context['tab_unterschrift2_2'] = " "
              report_context['tab_unterschrift2_3'] = " "
              report_context['tab_unterschrift2_4'] = " "
              report_context['tab_title2_0'] = tab_title1[0]
              report_context['tab_title2_1'] = tab_title1[1]
              report_context['tab_title2_2'] = " "
              report_context['tab_title2_3'] = " "
              report_context['tab_title2_4'] = " "
          if(indx_1 == 3):
              datum1 = str(tab_Datum1[0])
              pos1 = datum1.find("-")
              teil1 = datum1[0:pos1]
              teil2 = datum1[pos1+1:len(datum1)]
              pos2= teil2.find("-")
              teil2_1 = teil2[0:pos2]
              teil2_2 = teil2[pos2+1:len(teil2)]
              report_context['Datum2_0'] = teil2_2+"."+teil2_1+"."+teil1

              datum2 = str(tab_Datum1[1])
              pos3 = datum2.find("-")
              teil3 = datum2[0:pos3]
              teil4 = datum2[pos3+1:len(datum2)]
              pos4= teil4.find("-")
              teil4_1 = teil4[0:pos4]
              teil4_2 = teil4[pos4+1:len(teil4)]
              report_context['Datum2_1'] = teil4_2+"."+teil4_1+"."+teil3

              datum3 = str(tab_Datum1[2])
              pos5 = datum3.find("-")
              teil5 = datum3[0:pos5]
              teil6 = datum3[pos5+1:len(datum3)]
              pos6= teil6.find("-")
              teil6_1 = teil6[0:pos6]
              teil6_2 = teil6[pos6+1:len(teil6)]
              report_context['Datum2_2'] = teil6_2+"."+teil6_1+"."+teil5

              report_context['Datum2_3'] = " "
              report_context['Datum2_4'] = " "
              report_context['tab_unterschrift2_0'] = tab_unterschrift1[0]
              report_context['tab_unterschrift2_1'] = tab_unterschrift1[1]
              report_context['tab_unterschrift2_2'] = tab_unterschrift1[2]
              report_context['tab_unterschrift2_3'] = " "
              report_context['tab_unterschrift2_4'] = " "
              report_context['tab_title2_0'] = tab_title1[0]
              report_context['tab_title2_1'] = tab_title1[1]
              report_context['tab_title2_2'] = tab_title1[2]
              report_context['tab_title2_3'] = " "
              report_context['tab_title2_4'] = " "
          if(indx_1 == 4):

              datum1 = str(tab_Datum1[0])
              pos1 = datum1.find("-")
              teil1 = datum1[0:pos1]
              teil2 = datum1[pos1+1:len(datum1)]
              pos2= teil2.find("-")
              teil2_1 = teil2[0:pos2]
              teil2_2 = teil2[pos2+1:len(teil2)]
              report_context['Datum2_0'] = teil2_2+"."+teil2_1+"."+teil1

              datum2 = str(tab_Datum1[1])
              pos3 = datum2.find("-")
              teil3 = datum2[0:pos3]
              teil4 = datum2[pos3+1:len(datum2)]
              pos4= teil4.find("-")
              teil4_1 = teil4[0:pos4]
              teil4_2 = teil4[pos4+1:len(teil4)]
              report_context['Datum2_1'] = teil4_2+"."+teil4_1+"."+teil3

              datum3 = str(tab_Datum1[2])
              pos5 = datum3.find("-")
              teil5 = datum3[0:pos5]
              teil6 = datum3[pos5+1:len(datum3)]
              pos6= teil6.find("-")
              teil6_1 = teil6[0:pos6]
              teil6_2 = teil6[pos6+1:len(teil6)]
              report_context['Datum2_2'] = teil6_2+"."+teil6_1+"."+teil5

              datum4 = str(tab_Datum1[3])
              pos7 = datum4.find("-")
              teil7 = datum4[0:pos7]
              teil8 = datum4[pos7+1:len(datum4)]
              pos8= teil8.find("-")
              teil8_1 = teil8[0:pos8]
              teil8_2 = teil8[pos8+1:len(teil8)]
              report_context['Datum2_3'] = teil8_2+"."+teil8_1+"."+teil7

              report_context['Datum2_4'] = " "
              report_context['tab_unterschrift2_0'] = tab_unterschrift1[0]
              report_context['tab_unterschrift2_1'] = tab_unterschrift1[1]
              report_context['tab_unterschrift2_2'] = tab_unterschrift1[2]
              report_context['tab_unterschrift2_3'] = tab_unterschrift1[3]
              report_context['tab_unterschrift2_4'] = " "
              report_context['tab_title2_0'] = tab_title1[0]
              report_context['tab_title2_1'] = tab_title1[1]
              report_context['tab_title2_2'] = tab_title1[2]
              report_context['tab_title2_3'] = tab_title1[3]
              report_context['tab_title2_4'] = " "



          else:
            if(indx_1 >= 5):

              datum1 = str(tab_Datum1[0])
              pos1 = datum1.find("-")
              teil1 = datum1[0:pos1]
              teil2 = datum1[pos1+1:len(datum1)]
              pos2= teil2.find("-")
              teil2_1 = teil2[0:pos2]
              teil2_2 = teil2[pos2+1:len(teil2)]
              report_context['Datum2_0'] = teil2_2+"."+teil2_1+"."+teil1

              datum2 = str(tab_Datum1[1])
              pos3 = datum2.find("-")
              teil3 = datum2[0:pos3]
              teil4 = datum2[pos3+1:len(datum2)]
              pos4= teil4.find("-")
              teil4_1 = teil4[0:pos4]
              teil4_2 = teil4[pos4+1:len(teil4)]
              report_context['Datum2_1'] = teil4_2+"."+teil4_1+"."+teil3

              datum3 = str(tab_Datum1[2])
              pos5 = datum3.find("-")
              teil5 = datum3[0:pos5]
              teil6 = datum3[pos5+1:len(datum3)]
              pos6= teil6.find("-")
              teil6_1 = teil6[0:pos6]
              teil6_2 = teil6[pos6+1:len(teil6)]
              report_context['Datum2_2'] = teil6_2+"."+teil6_1+"."+teil5

              datum4 = str(tab_Datum1[3])
              pos7 = datum4.find("-")
              teil7 = datum4[0:pos7]
              teil8 = datum4[pos7+1:len(datum4)]
              pos8= teil8.find("-")
              teil8_1 = teil8[0:pos8]
              teil8_2 = teil8[pos8+1:len(teil8)]
              report_context['Datum2_3'] = teil8_2+"."+teil8_1+"."+teil7

              datum5 = str(tab_Datum1[4])
              pos9 = datum5.find("-")
              teil9 = datum5[0:pos9]
              teil10 = datum5[pos9+1:len(datum5)]
              pos10= teil10.find("-")
              teil10_1 = teil10[0:pos10]
              teil10_2 = teil10[pos10+1:len(teil10)]
              report_context['Datum2_4'] = teil10_2+"."+teil10_1+"."+teil9

              report_context['tab_unterschrift2_0'] = tab_unterschrift1[0]
              report_context['tab_unterschrift2_1'] = tab_unterschrift1[1]
              report_context['tab_unterschrift2_2'] = tab_unterschrift1[2]
              report_context['tab_unterschrift2_3'] = tab_unterschrift1[3]
              report_context['tab_unterschrift2_4'] = tab_unterschrift1[4]
              report_context['tab_title2_0'] = tab_title1[0]
              report_context['tab_title2_1'] = tab_title1[1]
              report_context['tab_title2_2'] = tab_title1[2]
              report_context['tab_title2_3'] = tab_title1[3]
              report_context['tab_title2_4'] = tab_title1[4]
        else:

              report_context['Datum2_0'] = " "
              report_context['Datum2_1'] = " "
              report_context['Datum2_2'] = " "
              report_context['Datum2_3'] = " "
              report_context['Datum2_4'] = " "
              report_context['tab_unterschrift2_0'] = " "
              report_context['tab_unterschrift2_1'] = " "
              report_context['tab_unterschrift2_2'] = " "
              report_context['tab_unterschrift2_3'] = " "
              report_context['tab_unterschrift2_4'] = " "
              report_context['tab_title2_0'] = " "
              report_context['tab_title2_1'] = " "
              report_context['tab_title2_2'] = " "
              report_context['tab_title2_3'] = " "
              report_context['tab_title2_4'] = " "

        return report_context


class Datumm5_3(
        DeactivableMixin, sequence_ordered(), ModelSQL, ModelView):
    "Party Datumm5_3"
    __name__ = 'party.datumms5.3'

    Datum = fields.Date("Datum")
    Unterschrift = fields.Selection([
        ('Dipl.-Ing Prüfer', 'Dipl.-Ing Prüfer'),
        ('Dipl.-Ing Schulz', 'Dipl.-Ing Schulz'),
    ], 'Name und Unterschrift', readonly = False,
        )
    Title = fields.Char('Dienststellung oder Titel', translate=True
        )
    test4 = fields.Many2One('party.iso14732', 'iso14732',
        ondelete='CASCADE', states=STATES, select=True, depends=DEPENDS)

    @staticmethod
    def default_Unterschrift():
        return " "

class Datumm5(
        DeactivableMixin, sequence_ordered(), ModelSQL, ModelView):
    "Party Datumm5"
    __name__ = 'party.datumms5'

    Datum = fields.Date("Datum")
    Unterschrift = fields.Selection([
        ('Dipl.-Ing Prüfer', 'Dipl.-Ing Prüfer'),
        ('Dipl.-Ing Schulz', 'Dipl.-Ing Schulz'),
    ], 'Name und Unterschrift', readonly = False,
        )
    Title = fields.Char('Dienststellung oder Titel', translate=True
        )
    test5 = fields.Many2One('party.iso14732', 'iso14732', 
        ondelete='CASCADE', states=STATES, select=True, depends=DEPENDS)

    @staticmethod
    def default_Unterschrift():
        return " "
#Biediener_protokoll
class iso14732(DeactivableMixin, ModelView, ModelSQL, MultiValueMixin):
    'Party Iso14732'
    __name__ = 'party.iso14732'

    photo_bediener = fields.Binary("Photo")

    Title = fields.Selection([
        ('Prüfungsbescheinigung für', 'Prüfungsbescheinigung für'),
        ('Bediener-Prüfungsbescheinigung', 'Bediener-Prüfungsbescheinigung'),
        ('Einrichter-Prüfungsbescheinigung', 'Einrichter-Prüfungsbescheinigung'),
        ('Zertifikat für', 'Zertifikat für'),
        ('ZERTIFIKAT/PRÜFUNGSBESCHEINIGUNG', 'ZERTIFIKAT/PRÜFUNGSBESCHEINIGUNG'),
        ('ZERTIFIKAT/BEDIENER-PRÜFUNGSBESCHEINIGUNG', 'ZERTIFIKAT/BEDIENER-PRÜFUNGSBESCHEINIGUNG'),
        ('SCHWEISSER-PRÜFUNGSZERTIFIKAT', 'SCHWEISSER-PRÜFUNGSZERTIFIKAT'),
    ], 'Title', readonly = False,
        )
    space = fields.Char('                                                                                                                                                             ')
    prufstellle = fields.Many2One('welding.pruefstelle', 'Prüfers oder prüfstelle',
            ondelete='CASCADE')

    bediener = fields.Many2One('party.party', 'Name des Bedieners/Einrichters                                            ',ondelete='CASCADE')
    leg = fields.Function(fields.Char("Legitimation                                                                              "),"On_Change_bedieners")
    art_leg = fields.Function(fields.Char("Art der Legitimation                                                                 "),"On_Change_bediener1")
    geburts_ort = fields.Function(fields.Char("Geburtsdatum und -ort                                                             "),"On_Change_bediener2")

    hinweise = fields.Many2One('welding.hinweise', 'Zusätzliche Hinweise',
            ondelete='CASCADE')
    hinweise_gel = fields.Function(fields.Text(" "),"On_Change_hinweise_bediener")

    Unterschrift_p = fields.Function(fields.Char("Unterschrift"),"On_Change_prufstellle")
    Bezeichnung = fields.Selection([
        ('Bediener von Schweißeinrichtungen', 'Bediener von Schweißeinrichtungen'),
        ('Einrichter von Schweißeinrichtungen', 'Einrichter von Schweißeinrichtungen'),
        ('Welding operators for mechanized and automatic welding', 'Welding operators for mechanized and automatic welding'),
        ('Weld setters for mechanized and automatic welding', 'Weld setters for mechanized and automatic welding'),
    ], 'Bezeichnung                            ', readonly = False,
        )

    WPS_ID = fields.Many2One('party.wps', 'Hersteller-Schweißanweisung')
    Beleg_nr = fields.Char('Prüfer oder Prüfstelle Beleg-Nr')

    Erstellt_Geändert_von = fields.Char('Beschäftigt bei									      ')
    Erstellt_Geändert_am = fields.Char('Erstellt/ Geändert am: Datum')
    Geprüft_Freigegeben_von = fields.Char('Geprüft/ Freigegeben von: Name')
    Geprüft_Freigegeben_am = fields.Char('Geprüft/ Freigegeben am: Datum')
    Name_des_Schweißers = fields.Char('Name des Bedieners/Einrichters                 		          ')
    Legitimation = fields.Char('Legitimation                   				      			 ')
    Art_der_Legitimation = fields.Char('Art der Legitimation')
    Geburtsdatum_ort = fields.Char('Geburtsdatum,ort')
    Arbeitgeber = fields.Char('Arbeitgeber')
    Vorschrift_Prüfnorm = fields.Char('Vorschrift / Prüfnorm')
    Prufnorm = fields.Selection([
        ('DIN EN ISO 14732:2013-12 | Prüfung von Bedienern und Einrichtern', 'DIN EN ISO 14732:2013-12 | Prüfung von Bedienern und Einrichtern'),
        ('DIN EN ISO 14732:2013-12,AD-2000 HP3 | Geschweißte Druckbehälter', 'DIN EN ISO 14732:2013-12,AD-2000 HP3 | Geschweißte Druckbehälter'),
        ('DIN EN ISO 14732:2013-12,DIN EN 15085-2 | schweißen von schienenfahzeugen', 'DIN EN ISO 14732:2013-12,DIN EN 15085-2 | schweißen von schienenfahzeugen'),
        ('EN ISO 14732:2013, AD-2000 HP3, EN 15085-2 | Druckbehälter, schienenfahzeugbau', 'EN ISO 14732:2013, AD-2000 HP3, EN 15085-2 | Druckbehälter, schienenfahzeugbau'),
        ('MSZ EN ISO 14732:2014| Ungarische Norm,Ausgabe:2014', 'MSZ EN ISO 14732:2014| Ungarische Norm,Ausgabe:2014'),
        ('MSZ EN ISO 14732:2014, AD-2000 HP3|Geschweißte Druckbehälter', 'MSZ EN ISO 14732:2014, AD-2000 HP3|Geschweißte Druckbehälter'),
        ('MSZ EN ISO 14732:2014,MSZ EN 15085-2:2008|schweißen von schienenfahzeugen', 'MSZ EN ISO 14732:2014,MSZ EN 15085-2:2008|schweißen von schienenfahzeugen'),
        ('DGRL 2014/68/EU,AD 2000 HP 3, EN ISO 14732| Zertifikat TÜV nach DGRL 2014/68/EU(Bediener)', 'DGRL 2014/68/EU,AD 2000 HP 3, EN ISO 14732| Zertifikat TÜV nach DGRL 2014/68/EU(Bediener)'),
        ('DGRL 2014/68/EU EN ISO 14732, AD 2000 HP 3| Zertifikat TÜV NORD 2014/68/EU(Bediener)', 'DGRL 2014/68/EU EN ISO 14732, AD 2000 HP 3| Zertifikat TÜV NORD 2014/68/EU(Bediener)'),
        ('2014/68/EU;EN ISO 14732;AD 2000 HP 3| Zertifikat DVS-PersZert 2014/68/EU(Bediener)', '2014/68/EU;EN ISO 14732;AD 2000 HP 3| Zertifikat DVS-PersZert 2014/68/EU(Bediener)'),
    ], 'Vorschrift/Prüfnorm						                      ', readonly = False,
        )

    Prüfung_der_Funktionskenntnisse = fields.Selection([
        ('Nachweis', 'Nachweis'),
        ('Bestanden', 'Bestanden'),
    ], 'Prüfung der Funktionskenntnisse			                      ', readonly = False,
        )
    Fachkunde = fields.Selection([
        ('Nicht geprüft', 'Nicht geprüft'),
        ('Bestanden', 'Bestanden'),
    ], 'Fachkunde                                                                               ', readonly = False,
        )

    Art_Schweisseinrichtung2 = fields.Selection([
        ('CLOOS ROMAT 120', 'CLOOS ROMAT 120'),
        ('CLOOS ROMAT 260', 'CLOOS ROMAT 260'),
    ], 'Art der Schweißeinrichtung2', readonly = False,
        )

    Art_Schweisseinrichtung_g = fields.Function(fields.Char("Schweisseinrichtung2"),'on_change_SSSchweisseinrichtung2')

    Schweißprozesse_ISO = fields.Selection([
        ('121', '121 UP Unterpulverschweißen mit Massivdrahtelektrode'),
        ('122', '122 Up Unterpulverschweißen mit Massivdbandelektrode'),
        ('124', '124 Up Unterpulverschweißen mit Metallpulverzusatz'),
        ('125', '125 Up Unterpulverschweißen mit Fülldrahtelektrode'),
        ('126', '126 Up Unterpulverschweißen mit Füllbandelektrode'),
        ('15', '15 WPL Plasmaschweißen'),
        ('21', '21 RP Widerstandspunktschweißen'),
        ('211', '211 indirektes Widerstandspunktschweißen'),
        ('212', '212 direktes Widerstandspunktschweißen'),
        ('22', '22 RR Rollennahtschweißen'),
        ('23', '23 RB Buckelschweißen'),
        ('231', '231 einseitiges Buckelschweißen'),
        ('232', '232 zweiseitiges Buckelschweißen'),
        ('24', '24 RA Abbrennstumpfschweißen'),
        ('241', '241 Abbrennstumpfschweißen mit Vorwärmung'),
        ('242', '242 Abbrennstumpfschweißen ohne Vorwärmung'),
        ('25', '25 Pressstumpfschweißen'),
        ('29', '29 andere Widerstandsschweißverfahren'),
        ('41', '41 Ultraschallschweißen'),
        ('42', '42 FR ReibSchweißen'),
        ('44', '44 Schweißen mit hoher mechanisher Energie'),
        ('45', '45 Diffusionsschweißen'),
        ('51', '51 EB Elektronenstrahlschweißen'),
        ('511', '511 EB Elektronenstrahlschweißen unter Vakuum'),
        ('52', '52 LA Laserstrahlschweißen'),
        ('521', '521 LA Festkörper-Laserstrahlschweißen'),
        ('522', '522 LA Gas-Laserstrahlschweißen'),
        ('522+15', '522+15 Hybridschweißen: Laser-und Plasmaschweißen'),
        ('78', '78 Bolzenschweißen'),
        ('783', '783 DS Hubzündungs-Bolzenschweißen mit Keramikring oder Schutzgas'),
        ('784', '784 DS Kuzeit-Bolzenschweißen mit Hubzündung'),
        ('785', '785 DS Kondensatorentladungs-Bolzenschweißen mit Hubzündung'),
        ('786', '786 TS Kondensatorentladungs-Bolzenschweißen mit Spitzenzündung'),
        ('787', '787 Bolzenschweißen mit Ringzündung'),
    ], 'Schweißprozesse_ISO                                       ', readonly = False,
        )
    Schweißprozesse_ISO_2 =  fields.Function(fields.Char("Schweißprozesse2"),'on_change_Schweissprozesse')
    Schweißprozesse_ISO_g =  fields.Function(fields.Char("Schweißprozesse_g"),'on_change_SSSchweissprozesse_g')
    Schweisseinrichtung1 = fields.Selection('on_change_Richtung','Schweisseinrichtung                                           ', readonly = False,)
    Schweisseinrichtung2 = fields.Selection([
        ('ARO MO.S Buckelschweißm.BR 1', 'ARO MO.S Buckelschweißm.BR 1'),
        ('Kjellberg UP-Anlage Typ SOL', 'Kjellberg UP-Anlage Typ SOL'),
    ], 'Schweisseinrichtung2', readonly = False,
        )
    Schweisseinrichtung_g = fields.Function(fields.Char("Schweisseinrichtung_g"),'on_change_SSchweisseinrichtung')
    Schweiss_einheit = fields.Char('Schweißeinheit                                                    ')
    Schweiss_einheit_g = fields.Function(fields.Char("Schweißeinheit_g"), 'on_change_SSchweiss_einheit')

    Details_für_mechanisches_Schweißen = fields.Char("Details_für_mechanisches_Schweißen")

    Direkte_g = fields.Function(fields.Char("Direktg"),'on_change_DDirekt')

    Lichtbogenlänge_g_2 = fields.Function(fields.Char("Lichtbogenlänge_g"),'on_change_AAutomatische_Kontrolle_der_Lichtbogenlänge2')
    Lichtbogenlänge_g = fields.Function(fields.Char("Lichtbogenlänge_g"),'on_change_Automatische_Kontrolle_der_Lichtbogenlänge')
    Automatische_g = fields.Function(fields.Char("Auto"),'on_change_AAutomatisch')
    Automatische_naht_g = fields.Function(fields.Char("Auto_naht"),'on_change_nahtauto')

    Einzellagen_Mehrlagentechnik_g = fields.Function(fields.Char("Einzellagen"),'on_change_Einzellagen')
    Einzellagen_Mehrlagentechnik_g_2 = fields.Function(fields.Char("Einzellagen"),'on_change_Einzellagen2')

    Schweißbadsicherung_g = fields.Function(fields.Char("Schweißbadsicherung_g"),'on_change_SSchweißbadsicherung')

    Schweißzusatzeinlagen = fields.Selection([
        ('Ohne', 'Ohne'),
        ('mit', 'mit'),
    ], 'Schweißzusatzeinlagen                                  ', readonly = False,
        )

    Schweißzusatzeinlagen_g = fields.Function(fields.Char("Schweißzusatzeinlagen_g"),'on_change_SSchweißzusatzeinlagen')

    #Zusätzliche = fields.Selection([
    #    ('Test 3 Zeilen', 'Test 3 Zeilen'),
    #    ('TÜV-Abnahme', 'TÜV-Abnahme'),
     #   ('delete', 'Löschen'),
  #  ], 'Zusätzliche Hinweise', readonly = False,
 #       )
    Zusätzliche2 = fields.Function(fields.Text("Zusätzliche Hinweise"),'on_change_ZZusätzliche')

    Schweißverfahrenprüfung = fields.Selection([
        ('X', 'X'),
        ('-', '-'),
    ], 'Schweißverfahrenprüfung (siehe 4.1 a)                                                 ', readonly = False,
        )
    Schweißtechnische = fields.Selection([
        ('X', 'X'),
        ('-', '-'),
    ], 'Schweißtechnische Prüfung vor Fertigungsbeginn (siehe 4.1 b)         ', readonly = False,
        )
    Standardprüftück = fields.Selection([
        ('X', 'X'),
        ('-', '-'),
    ], 'Standardprüftück (siehe 4.1 c)                                                                ', readonly = False,
        )
    Fertigungsprüfung = fields.Selection([
        ('X', 'X'),
        ('-', '-'),
    ], 'Fertigungsprüfung oder Sichtprobenprüfung (siehe 4.1 d)                    ', readonly = False,
        )
    Details_1 = fields.Selection([
        ('unbenutzt', 'unbenutzt'),
        ('nach 4.2.3', 'nach 4.2.3'),
    ], 'Details für mechanisches Schweißen            ', readonly = False,required = True,
        )

    #Name_unterschrift = fields.Selection([
     #   ('Dipl.-Ing. Prüfer', 'Dipl.Ing. Prüfer'),
       # ('Dipl.-Ing. Schulz', 'Dipl.-Ing. Schulz'),
      #  ('Dipl.-Ing. Tester', 'Dipl.-Ing. Tester'),
        #('Dipl.-Ing. Zertifizierer', 'Dipl.-Ing. Zertifizierer'),
      #  ('P.L. Van Fosson', 'P.L. Van Fosson'),
    #], 'Name Und Unterschrift', readonly = False,
   #     )

    #Prufer_Prufstelle = fields.Selection([
     #   ('SK im BTZ Musterstadt', 'SK im BTZ Musterstadt'),
   #     ('SLV Halle GmbH', 'SLV Halle GmbH'),
  #  ], 'Prüfer oder Prüfstelle', readonly = False,
    #    )

    Gultig_dauer = fields.Selection([
        ('5.3 a)', '5.3 a) Neuqualifizierung nach 6 Jahren'),
        ('5.3 b)', '5.3 b) Verlängerung der Prüfung nach 3 Jahren'),
        ('5.3 c)', '5.3 c) Verlängerung jeweils nach 6 Monaten'),
    ], 'Gültigkeitdauer', readonly = False,
        )
    Ort = fields.Char("Ort                                                                                                            ")
    Datum_Ausgabe = fields.Date("Datum der Ausgabe")
    Datum_Schweissen = fields.Date("Datum des Schweißens")
    Datum_Prufung = fields.Date("Datum der Prüfung")
    Gultig_bis = fields.Function(fields.Date("Gültig bis"),"On_change_Datum_Prufung")
    Nahtsensor2 = fields.Char("Nahtsensor2")
    Nahtsensor2_g = fields.Function(fields.Char("Nahtsensor2_g"),'on_change_NNahtsensor2')
##
    Details_2 = fields.Selection('on_change_Details1','Details für mechanisches Schweißen            ', readonly = False, required=True)

    Nahtsensor2_2 = fields.Selection('on_change_DDetails1','Nahtsensor                                                           ', readonly = False)

    Automatische_Kontrolle_der_Lichtbogenlänge2 = fields.Selection('on_change_Automatische_Details1','Automatische Kontrolle der Lichtbogenlänge    ', readonly = False)

    Einzellagen_Mehrlagentechnik2 = fields.Selection('on_change_Einzellagen_Details1','Einzellagen-/Mehrlagentechnik                          ', readonly = False)
    Art_Schweisseinrichtung = fields.Selection('on_change_Art_Schweisseinrichtung_Details1','Art der Schweißeinrichtung                                ', readonly = False)

    Schweißzusatzeinlagen = fields.Selection('on_change_Schweißzusatzeinlagen_Details1','Schweißzusatzeinlagen                                      ', readonly = False)

    Schweißbadsicherung = fields.Selection('on_change_Schweißbadsicherung_Details1','Schweißbadsicherung                                         ', readonly = False)
    Einzellagen_Mehrlagentechnik = fields.Selection('on_change_Einzellagen_Mehrlagentechnik_Details1','Einzellagen-/Mehrlagentechnik                          ', readonly = False)

    Schweißposition_din = fields.Selection('on_change_Schweißposition_Details1','Schweißposition                                                  ', readonly = False)

    Automatisches_Nahtvervolgungssystem = fields.Selection('on_change_Automatisches_Nahtvervolgungssystem_Details1','Automatisches Nahtvervolgungssystem           ', readonly = False)

    Automatische_Kontrolle_der_Lichtbogenlänge = fields.Selection('on_change_Automatische_Kontrolle_der_Lichtbogenlänge_Details1','Automatische Kontrolle der Lichtbogenlänge    ', readonly = False)
    Direkte_oder_ferngesteurte_Sichtprüfung = fields.Selection('on_change_Direkte_Sichtprüfung_Details1','Direkte oder ferngesteurte Sichtprüfung             ', readonly = False)

###
    Ergebnisse_der_Prüfung = fields.Char('Ergebnisse der Prüfung füe die Qualifizierung siehe                            ')
    document_nr = fields.Char('Dokument-Nr                                                                                           ')
    text_end = fields.Char('(Bericht der Qualifizierung WPQR oder andere Prüfdokumente)')

    Details = fields.Function(fields.Char("Details für automatisches Schweißen ", required=True,),'on_change_ISO')
    Nahtsensor= fields.Function(fields.Char("Nahtsensor"),'on_change_nahtverfolgung')

    Datumms5_3 = fields.One2Many('party.datumms5.3','test4','Bestätigung der Gültigkeit durch den Prüfer oder die Prüfstelle für die folgenden 3 Jahre (bezogen auf 5.3b)')
    Datumms5 = fields.One2Many('party.datumms5','test5','Verlängerung der Prüfbescheinigung für die folgenden 6 Monate durch den Arbeitgeber/Schweißaufsicht oder durch den Prüfer/Prüfstelle (Siehe Abschnitt 5)')

    def On_Change_bedieners(self,bediener):
     if(self.bediener is not None):
        return self.bediener.legitimation
     else:
        return " "

    def On_Change_bediener1(self,bediener):
     if(self.bediener is not None):
        return self.bediener.legitimation_type
     else:
        return " "

    def On_Change_bediener2(self,bediener):
     if(self.bediener is not None):
        return str(self.bediener.birthday)+"\ "+self.bediener.ort_birthday
     else:
        return " "


    def On_Change_hinweise_bediener(self,hinweise):
     if(self.hinweise is not None):
          return self.hinweise.bemerkungen
     else:
          return " "

    def On_Change_prufstellle(self,prufstellle):
     if(self.prufstellle is not None):
          return self.prufstellle.prufer
     else:
          return " "

    def get_rec_name(self,Name_des_Schweißers):
        return self.Name_des_Schweißers


    def on_change_nahtverfolgung(self,Automatisches_Nahtvervolgungssystem):
                   return_valuee = self.Automatisches_Nahtvervolgungssystem
                   return return_valuee



    def On_change_Datum_Prufung(self,Gultig_dauer):
         if(self.Gultig_dauer == "5.3 a)" or self.Gultig_dauer == "5.3 c)"):
          val = self.Datum_Prufung + datetime.timedelta(days=183)
          return val
         else:
           if(self.Gultig_dauer =="5.3 b)"):
             val =self.Datum_Prufung + datetime.timedelta(days=1095)
             return val

    @fields.depends('Schweisseinrichtung1', 'Schweisseinrichtung2')
    def on_change_Richtung(self):
          if(self.Schweisseinrichtung2 == "Kjellberg UP-Anlage Typ SOL"):
             tab =[]
             tab.append(('Kjellberg UP-Anlage Typ SOL','Kjellberg UP-Anlage Typ SOL'))
             return tab
          else:
            if(self.Schweisseinrichtung2 == "ARO MO.S Buckelschweißm.BR 1"):
               tab =[]
               tab.append(('ARO MO.S Buckelschweißm.BR1', 'ARO MO.S BuckelSchweißm.BR1'))
               tab.append(('ARO MO.S Nahtschweißm.BR3', 'ARO MO.S NahtSchweißm.BR3'))
               tab.append(('ARO MO.S Punktschweißm.BR2', 'ARO MO.S Punktschweißm.BR2'))
               tab.append(('HW MF-Schweißmaschine', 'HW MF-Schweißmaschine'))
               tab.append(('WMA Buckelschweißm.BMP 20', 'WMA Buckelschweißm.BMP 20'))
               tab.append(('WMA Buckelschweißm.BMP 6.2', 'WMA Buckelschweißm.BMP 6.2'))
               tab.append(('WMA Nahtschweißm.NMP 12', 'WMA Nahtschweißm.NMP 12'))
               tab.append(('WMA Nahtschweißm.NMP 7', 'WMA Nahtschweißm.NMP 7'))
               tab.append(('WMA Punktschweißm.PMF 3', 'WMA Punktschweißm.PMF 3'))
               tab.append(('WMA Punktschweißm.PMP 3', 'WMA Punktschweißm.PMP 3'))
               return tab


    def on_change_Schweissprozesse(self,Schweißprozesse_ISO):
                   if(self.Schweißprozesse_ISO == "121" or self.Schweißprozesse_ISO == "122" or self.Schweißprozesse_ISO == "124" or self.Schweißprozesse_ISO == "125" or self.Schweißprozesse_ISO == "126"):
                      value_process="UP"
                      return value_process
                   if(self.Schweißprozesse_ISO =="21"):
                      value_process="RP"
                      return value_process
                   if(self.Schweißprozesse_ISO =="22"):
                      value_process="RR"
                      return value_process
                   if(self.Schweißprozesse_ISO =="23"):
                      value_process="RB"
                      return value_process
                   if(self.Schweißprozesse_ISO =="24"):
                      value_process="RA"
                      return value_process
                   if(self.Schweißprozesse_ISO =="42"):
                      value_process="FR"
                      return value_process
                   if(self.Schweißprozesse_ISO =="51"):
                      value_process="EB"
                      return value_process
                   if(self.Schweißprozesse_ISO =="511"):
                      value_process="EB"
                      return value_process
                   if(self.Schweißprozesse_ISO =="52"):
                      value_process="LA"
                      return value_process
                   if(self.Schweißprozesse_ISO =="521"):
                      value_process="LA"
                      return value_process
                   if(self.Schweißprozesse_ISO =="522"):
                      value_process="LA"
                      return value_process
                   if(self.Schweißprozesse_ISO =="783"):
                      value_process="DS"
                      return value_process
                   if(self.Schweißprozesse_ISO =="784"):
                      value_process="DS"
                      return value_process
                   if(self.Schweißprozesse_ISO =="785"):
                      value_process="DS"
                      return value_process
                   if(self.Schweißprozesse_ISO =="786"):
                      value_process="TS"
                      return value_process



                   else :
                      if(self.Schweißprozesse_ISO =="15"):
                          value_process="WPL"
                          return value_process

    def on_change_SSSchweissprozesse_g(self,Schweißprozesse_ISO):
                   if(self.Schweißprozesse_ISO == "121"):
                      value_process="ISO 4063 - 121 (UP)"
                      return value_process
                   if(self.Schweißprozesse_ISO == "122"):
                      value_process="ISO 4063 - 122 (UP)"
                      return value_process
                   if(self.Schweißprozesse_ISO == "124"):
                      value_process="ISO 4063 - 124 (UP)"
                      return value_process
                   if(self.Schweißprozesse_ISO == "125"):
                      value_process="ISO 4063 - 125 (UP)"
                      return value_process
                   if(self.Schweißprozesse_ISO == "126"):
                      value_process="ISO 4063 - 126 (UP)"
                      return value_process
                   if(self.Schweißprozesse_ISO =="21"):
                      value_process="ISO 4063 -21(RP)"
                      return value_process
                   if(self.Schweißprozesse_ISO =="211"):
                      value_process="ISO 4063 -211"
                      return value_process
                   if(self.Schweißprozesse_ISO =="212"):
                      value_process="ISO 4063 -212"
                      return value_process
                   if(self.Schweißprozesse_ISO =="22"):
                      value_process="ISO 4063 -22(RR)"
                      return value_process

                   if(self.Schweißprozesse_ISO =="23"):
                      value_process="ISO 4063 -23(RB)"
                      return value_process
                   if(self.Schweißprozesse_ISO =="231"):
                      value_process="ISO 4063 -231"
                      return value_process

                   if(self.Schweißprozesse_ISO =="232"):
                      value_process="ISO 4063 -232"
                      return value_process
                   if(self.Schweißprozesse_ISO =="24"):
                      value_process="ISO 4063 -24(RA)"
                      return value_process
                   if(self.Schweißprozesse_ISO =="241"):
                      value_process="ISO 4063 -241"
                      return value_process
                   if(self.Schweißprozesse_ISO =="242"):
                      value_process="ISO 4063 -242"
                      return value_process
                   if(self.Schweißprozesse_ISO =="25"):
                      value_process="ISO 4063 -25"
                      return value_process
                   if(self.Schweißprozesse_ISO =="29"):
                      value_process="ISO 4063 -29"
                      return value_process
                   if(self.Schweißprozesse_ISO =="41"):
                      value_process="ISO 4063 -41"
                      return value_process
                   if(self.Schweißprozesse_ISO =="42"):
                      value_process="ISO 4063 -42(FR)"
                      return value_process
                   if(self.Schweißprozesse_ISO =="44"):
                      value_process="ISO 4063 -44"
                      return value_process
                   if(self.Schweißprozesse_ISO =="45"):
                      value_process="ISO 4063 -45"
                      return value_process
                   if(self.Schweißprozesse_ISO =="51"):
                      value_process="ISO 4063 -51(EB)"
                      return value_process
                   if(self.Schweißprozesse_ISO =="511"):
                      value_process="ISO 4063 -511(EB)"
                      return value_process
                   if(self.Schweißprozesse_ISO =="52"):
                      value_process="ISO 4063 -52(LA)"
                      return value_process
                   if(self.Schweißprozesse_ISO =="521"):
                      value_process="ISO 4063 -521(LA)"
                      return value_process
                   if(self.Schweißprozesse_ISO =="522"):
                      value_process="ISO 4063 -522(LA)"
                      return value_process
                   if(self.Schweißprozesse_ISO =="522+15"):
                      value_process="ISO 4063 -522+15"
                      return value_process
                   if(self.Schweißprozesse_ISO =="78"):
                      value_process="ISO 4063- 78"
                      return value_process
                   if(self.Schweißprozesse_ISO =="783"):
                      value_process="ISO 4063- 783(DS)"
                      return value_process
                   if(self.Schweißprozesse_ISO =="784"):
                      value_process="ISO 4063- 784(DS)"
                      return value_process
                   if(self.Schweißprozesse_ISO =="785"):
                      value_process="ISO 4063- 785(DS)"
                      return value_process
                   if(self.Schweißprozesse_ISO =="786"):
                      value_process="ISO 4063- 786(TS)"
                      return value_process
                   if(self.Schweißprozesse_ISO =="787"):
                      value_process="ISO 4063- 787"
                      return value_process


                   else :
                      if(self.Schweißprozesse_ISO =="15"):
                          value_process="ISO 4063- 15(WPL)"
                          return value_process


    def on_change_ISO(self,ISO14732):
                  if(self.ISO14732 == "4.2.2"):
                     details_value = "4.2.2"
                     return details_value


    def on_change_ISO_p(self,ISO14732):
                  if(self.ISO14732 == "4.2.3"):
                     details_p_value = "nach 4.2.3"
                     return details_p_value

    def on_change_SSchweisseinrichtung(self,Schweisseinrichtung1):
          if(self.Schweisseinrichtung1 == "Kjellberg UP-Anlage Typ SOL"):
             val = "Kjellberg UP-Anlage Typ SOL"
             return val
          if(self.Schweisseinrichtung1 == "ARO MO.S Nahtschweißm.BR3"):
             val = "ARO MO.S Nahtschweißm.BR3"
             return val
          if(self.Schweisseinrichtung1 == "ARO MO.S Punktschweißm.BR2"):
             val = "ARO MO.S Punktschweißm.BR2"
             return val
          if(self.Schweisseinrichtung1 == "HW MF-Schweißmaschine"):
             val = "HW MF-Schweißmaschine"
             return val
          if(self.Schweisseinrichtung1 == "WMA Buckelschweißm.BMP 20"):
             val = "WMA Buckelschweißm.BMP 20"
             return val
          if(self.Schweisseinrichtung1 == "WMA Buckelschweißm.BMP 6.2"):
             val = "WMA Buckelschweißm.BMP 6.2"
             return val
          if(self.Schweisseinrichtung1 == "WMA Nahtschweißm.NMP 12"):
             val = "WMA Nahtschweißm.NMP 12"
             return val
          if(self.Schweisseinrichtung1 == "WMA Nahtschweißm.NMP 7"):
             val = "WMA Nahtschweißm.NMP 7"
             return val
          if(self.Schweisseinrichtung1 == "WMA Punktschweißm.PMF 3"):
             val = "WMA Punktschweißm.PMF 3"
             return val
          if(self.Schweisseinrichtung1 == "WMA Punktschweißm.PMP 3"):
             val = "WMA Punktschweißm.PMP 3"
             return val

          else:
            if(self.Schweisseinrichtung1 =="ARO MO.S Buckelschweißm.BR1"):
               val ="ARO MO.S Buckelschweißm.BR1"
               return val
    def on_change_SSchweiss_einheit(self,Schweiss_einheit):
          val = " "
          return val

    def on_change_DDirekt(self,Direkte_oder_ferngesteurte_Sichtprüfung):
          if(self.Direkte_oder_ferngesteurte_Sichtprüfung =="direkt"):
             val = "direkt(mit bloßem Auge)"
             return val
          else:
             if(self.Direkte_oder_ferngesteurte_Sichtprüfung =="remote"):
               val = "remote enfernt (mit kamera, 0.A.)"
               return val


    def on_change_AAutomatisch(self,Automatische_Kontrolle_der_Lichtbogenlänge):
          if(self.Automatische_Kontrolle_der_Lichtbogenlänge =="Ohne Kontrolle"):
             val ="ohne automatischer Kontrolle"
             return val
          else:
              if(self.Automatische_Kontrolle_der_Lichtbogenlänge =="mit Kontrolle"):
                 val ="mit automatischer Kontrolle"
                 return val



    def on_change_nahtauto(self,Automatisches_Nahtvervolgungssystem):
          if(self.Automatisches_Nahtvervolgungssystem == "Ohne Nahtverfolgung"):
              val = "Ohne Nahtverfolgung"
              return val
          else:
            if(self.Automatisches_Nahtvervolgungssystem == "mit Nahtverfolgung"):
                val = "mit Nahtverfolgung"
                return val

    def on_change_Einzellagen(self,Einzellagen_Mehrlagentechnik):
           if(self.Einzellagen_Mehrlagentechnik =="-"):
              val = "-"
              return val
           if(self.Einzellagen_Mehrlagentechnik =="ML"):
              val = "Einzel-und Mehrlagentechnik"
              return val
           if(self.Einzellagen_Mehrlagentechnik =="sl" or self.Einzellagen_Mehrlagentechnik =="einlagig"):
              val = "Einlagig"
              return val
           if(self.Einzellagen_Mehrlagentechnik =="ml"):
              val = "Einzel-und Mehrlagentechnik"
              return val
           if(self.Einzellagen_Mehrlagentechnik =="mehrlagig"):
              val = "ein-und mehrlagig"
              return val
           else:
              if(self.Einzellagen_Mehrlagentechnik =="EL"):
                  val ="Einzellagentechnik"
                  return val


    def on_change_Einzellagen2(self,Einzellagen_Mehrlagentechnik2):
           if(self.Einzellagen_Mehrlagentechnik2 =="-"):
              val = "-"
              return val
           if(self.Einzellagen_Mehrlagentechnik2 =="ML"):
              val = "Einzel-und Mehrlagentechnik"
              return val
           if(self.Einzellagen_Mehrlagentechnik2 =="sl" or self.Einzellagen_Mehrlagentechnik2 =="einlagig"):
              val = "Einlagig"
              return val
           if(self.Einzellagen_Mehrlagentechnik2 =="ml"):
              val = "Einzel-und Mehrlagentechnik"
              return val
           if(self.Einzellagen_Mehrlagentechnik2 =="mehrlagig"):
              val = "ein-und mehrlagig"
              return val
           else:
              if(self.Einzellagen_Mehrlagentechnik2 =="EL"):
                  val ="Einzellagentechnik"
                  return val

    def on_change_SSchweißbadsicherung(self,Schweißbadsicherung):
          if(self.Schweißbadsicherung == "Ohne" or self.Schweißbadsicherung == "nb"):
             val = "ohne Schweißbadsicherung"
             return val
          if(self.Schweißbadsicherung == "bs"):
             val = "bs"
             return val
          else:
              if(self.Schweißbadsicherung == "mit" or self.Schweißbadsicherung == "mb" or self.Schweißbadsicherung == "metal" or self.Schweißbadsicherung == "Weld metall" or self.Schweißbadsicherung=="nonmetallic" or self.Schweißbadsicherung=="flux backing" or self.Schweißbadsicherung == "gas backing" or self.Schweißbadsicherung == "gb"):
                   val = "mit Schweißbadsicherung"
                   return val


    def on_change_SSchweißzusatzeinlagen(self,Schweißzusatzeinlagen):
          if(self.Schweißzusatzeinlagen == "Ohne"):
             val ="Ohne Schweißzusatzeinlagen"
             return val
          else:
             if(self.Schweißzusatzeinlagen == "mit"):
                  val ="mit Schweißzusatzeinlagen"
                  return val



    def on_change_NNahtsensor2(self,Nahtsensor2_2):
          if(self.Nahtsensor2_2 == "Ohne"):
             val ="Ohne Mahtverfolgung"
             return val
          else:
            if(self.Nahtsensor2_2 == "Mit"):
               val ="Mit Mahtverfolgung"
               return val


    def on_change_Automatische_Kontrolle_der_Lichtbogenlänge(self,Automatische_Kontrolle_der_Lichtbogenlänge):
          val = "Noch nicht arbeitet"
          return val

    def on_change_AAutomatische_Kontrolle_der_Lichtbogenlänge2(self,Automatische_Kontrolle_der_Lichtbogenlänge2):
          if(self.Automatische_Kontrolle_der_Lichtbogenlänge2 =="Ohne Kontrolle"):
            val = "Ohne automatischer Kontrolle"
            return val
          else:
             if(self.Automatische_Kontrolle_der_Lichtbogenlänge2 =="mit Kontrolle"):
                val = "mit automatischer Kontrolle"
                return val


    def on_change_SSSchweisseinrichtung2(self,Art_Schweisseinrichtung):
           if(self.Art_Schweisseinrichtung == "CLOOS ROMAT 120"):
             val = "CLOOS ROMAT 120"
             return val
           if(self.Art_Schweisseinrichtung == "CLOOS ROMAT 310"):
             val = "CLOOS ROMAT 310"
             return val
           if(self.Art_Schweisseinrichtung == "igm RT 280"):
             val = "igm RT 280"
             return val
           if(self.Art_Schweisseinrichtung == "igm RT 330"):
             val = "igm RT 330"
             return val
           if(self.Art_Schweisseinrichtung == "igm RT 370"):
             val = "igm RT 370"
             return val
           if(self.Art_Schweisseinrichtung == "KUKA KR 30 L 15/2"):
             val = "KUKA KR 30 L 15/2"
             return val
           if(self.Art_Schweisseinrichtung == "KUKA KR 30/2"):
             val = "KUKA KR 30/2"
             return val
           if(self.Art_Schweisseinrichtung == "KUKA KR 45/2"):
             val = "KUKA KR 45/2"
             return val
           if(self.Art_Schweisseinrichtung == "MONTOMAN SK 16"):
             val = "MONTOMAN SK 16"
             return val
           if(self.Art_Schweisseinrichtung == "MONTOMAN SK 16-6"):
             val = "MONTOMAN SK 16-6"
             return val
           if(self.Art_Schweisseinrichtung == "MONTOMAN SK 6"):
             val = "MONTOMAN SK 6"
             return val
           else:
              if(self.Art_Schweisseinrichtung == "CLOOS ROMAT 260"):
                val = "CLOOS ROMAT 260"
                return val


    def on_change_ZZusätzliche(self,Zusätzliche):
        if(self.Zusätzliche == "Test 3 Zeilen"):
          val = "In WPS Report Können in die Prüfungenbescheinigungen 3 zeilen Bemerkungen mit jeweils .... \n 90 Zeichen eingetragen werden. In WPS Report können in die Prüfungenbescheinigungen"
          return val
        if(self.Zusätzliche == "delete"):
          val = " "
          return val
        else:
            if(self.Zusätzliche == "TÜV-Abnahme"):
               val = "Die Prüfung erfolgt im Einvernehmen mit dem Sachverständigen \n des TÜV Bayern Hessen Sachsen Südwest e.V."
               return val


    @staticmethod
    def default_Title():
       return "Prüfungsbescheinigung für"

    @staticmethod
    def default_Bezeichnung():
       return "Bediener von Schweißeinrichtungen"

    @staticmethod
    def default_Details_1():
       return "nach 4.2.3"

    @staticmethod
    def default_Details_2():
       return " "

    @fields.depends('Details_2', 'Details_1')
    def on_change_Details1(self):
        tab1=[]
        if(self.Details_1 =="nach 4.2.3"):
            tab1.append(('----------','----------'))
            return tab1
        else:
           if(self.Details_1 =="unbenutzt"):
            tab1.append(('unbenutzt','unbenutzt'))
            tab1.append(('nach 4.2.2','nach 4.2.2'))
            return tab1
    @fields.depends('Nahtsensor2_2', 'Details_1')
    def on_change_DDetails1(self):
        tab1=[]
        if(self.Details_1 =="nach 4.2.3"):
            tab1.append((' ',' '))
            return tab1
        else:
           if(self.Details_1 =="unbenutzt"):
            tab1.append(('Ohne','Ohne'))
            tab1.append(('Mit','mit'))
            return tab1

    @fields.depends('Automatische_Kontrolle_der_Lichtbogenlänge2', 'Details_1')
    def on_change_Automatische_Details1(self):
        tab1=[]
        if(self.Details_1 =="nach 4.2.3"):
            tab1.append((' ',' '))
            return tab1
        else:
           if(self.Details_1 =="unbenutzt"):
            tab1.append(('Ohne Kontrolle','Ohne'))
            tab1.append(('mit Kontrolle','mit'))
            return tab1

    @fields.depends('Einzellagen_Mehrlagentechnik2', 'Details_1')
    def on_change_Einzellagen_Details1(self):
        tab1=[]
        if(self.Details_1 =="nach 4.2.3"):
            tab1.append((' ',' '))
            return tab1
        else:
           if(self.Details_1 =="unbenutzt"):
            tab1.append(('-','- | Kein Lage'))
            tab1.append(('EL','EL | Einzellagentechnik'))
            tab1.append(('ML','ML | Mehrlagentechnik'))
            tab1.append(('sl','sl | einlagig'))
            tab1.append(('ml','ml | mehrlagig'))
            tab1.append(('einlagig','einlagig | einziger Durchlauf'))
            tab1.append(('mehrlagig','mehrlagig | mehrere Durchlaeufe'))
            return tab1

    @fields.depends('Art_Schweisseinrichtung', 'Details_1')
    def on_change_Art_Schweisseinrichtung_Details1(self):
        tab1=[]
        if(self.Details_1 =="nach 4.2.3"):
            tab1.append((' ',' '))
            return tab1
        else:
           if(self.Details_1 =="unbenutzt"):
            tab1.append(('CLOOS ROMAT 120', 'CLOOS ROMAT 120'))
            tab1.append(('CLOOS ROMAT 260', 'CLOOS ROMAT 260'))
            tab1.append(('CLOOS ROMAT 310', 'CLOOS ROMAT 310'))
            tab1.append(('igm RT 280', 'igm RT 280'))
            tab1.append(('igm RT 330', 'igm RT 330'))
            tab1.append(('igm RT 370', 'igm RT 370'))
            tab1.append(('KUKA KR 30 L 15/2', 'KUKA KR 30 L 15/2'))
            tab1.append(('KUKA KR 30/2', 'KUKA KR 30/2'))
            tab1.append(('KUKA KR 45/2', 'KUKA KR 45/2'))
            tab1.append(('MONTOMAN SK 16', 'MONTOMAN SK 16'))
            tab1.append(('MONTOMAN SK 16-6', 'MONTOMAN SK 16-6'))
            tab1.append(('MONTOMAN SK 6', 'MONTOMAN SK 6'))
            return tab1




    @fields.depends('Schweißzusatzeinlagen', 'Details_1')
    def on_change_Schweißzusatzeinlagen_Details1(self):
        tab1=[]
        if(self.Details_1 =="nach 4.2.3"):
            tab1.append(('Ohne','Ohne'))
            tab1.append(('mit','mit'))
            return tab1
        else:
           if(self.Details_1 =="unbenutzt"):
            tab1.append((' ',' '))
            return tab1

    @fields.depends('Schweißbadsicherung', 'Details_1')
    def on_change_Schweißbadsicherung_Details1(self):
        tab1=[]
        if(self.Details_1 =="nach 4.2.3"):
            tab1.append(('Ohne', 'Ohne | Ohne Badsicherung'))
            tab1.append(('nb', 'nb | Ohne Badsicherung'))
            tab1.append(('mit', 'mit | mit Badsicherung'))
            tab1.append(('mb', 'mb | mit Badsicherung'))
            tab1.append(('metal', 'metal | Badsicherung mit Metall'))
            tab1.append(('Weld metall', 'Weld metall | Badsicherung mit Schweißgut'))
            tab1.append(('nonmetallic', 'nonmetallic | nichtmetallische Badsicherung'))
            tab1.append(('flux backing', 'flux backing | Badsicherung mit schweißpulver'))
            tab1.append(('gas backing', 'gas backing | gasförmiger WurzelSchutz'))
            tab1.append(('gb', 'gb | gasförmiger WurzelSchutz'))
            tab1.append(('bs', 'bs | beidseitige Schweißen'))
            return tab1
        else:
           if(self.Details_1 =="unbenutzt"):
            tab1.append((' ',' '))
            return tab1


    @fields.depends('Einzellagen_Mehrlagentechnik', 'Details_1')
    def on_change_Einzellagen_Mehrlagentechnik_Details1(self):
        tab1=[]
        if(self.Details_1 =="nach 4.2.3"):
            tab1.append(('-', 'Kein Lage'))
            tab1.append(('EL', 'EL |  Einzellagentechnik'))
            tab1.append(('ML', 'ML | Mehrlagentechnik'))
            tab1.append(('sl', 'sl | einlagig'))
            tab1.append(('ml', 'ml | mehrlagig'))
            tab1.append(('einlagig', 'einlagig | einziger Durchlauf'))
            tab1.append(('mehrlagig', 'mehrlagig | mehrere Durchlaeufe'))
            return tab1
        else:
           if(self.Details_1 =="unbenutzt"):
            tab1.append((' ',' '))
            return tab1


    @fields.depends('Schweißposition_din', 'Details_1')
    def on_change_Schweißposition_Details1(self):
        tab1=[]
        if(self.Details_1 =="nach 4.2.3"):
            tab1.append(('PA', 'PA Wannenposition'))
            tab1.append(('PB', 'PB Horizontalposition'))
            tab1.append(('PC', 'PC Querposition'))
            tab1.append(('PD', 'PD Horizontal-Überkopfposition'))
            tab1.append(('PE', 'PE Überkopfposition'))
            tab1.append(('PF', 'PF Steigposition'))
            tab1.append(('PG', 'PG Fallposition'))
            tab1.append(('H-L045', 'H-L045 Steigposition'))
            tab1.append(('J-L045', 'J-L045 Fallposition'))
            tab1.append(('PH', 'PH Steigendschweißen'))
            tab1.append(('PJ', 'PJ Fallendschweißen'))
            return tab1
        else:
           if(self.Details_1 =="unbenutzt"):
            tab1.append((' ',' '))
            return tab1



    @fields.depends('Automatisches_Nahtvervolgungssystem', 'Details_1')
    def on_change_Automatisches_Nahtvervolgungssystem_Details1(self):
        tab1=[]
        if(self.Details_1 =="nach 4.2.3"):
            tab1.append(('Ohne Nahtverfolgung','Ohne'))
            tab1.append(('mit Nahtverfolgung','mit'))
            return tab1
        else:
           if(self.Details_1 =="unbenutzt"):
            tab1.append((' ',' '))
            return tab1

    @fields.depends('Automatische_Kontrolle_der_Lichtbogenlänge', 'Details_1')
    def on_change_Automatische_Kontrolle_der_Lichtbogenlänge_Details1(self):
        tab1=[]
        if(self.Details_1 =="nach 4.2.3"):
            tab1.append(('Ohne Kontrolle','Ohne'))
            tab1.append(('mit Kontrolle','mit'))
            return tab1
        else:
           if(self.Details_1 =="unbenutzt"):
            tab1.append((' ',' '))
            return tab1


    @fields.depends('Direkte_oder_ferngesteurte_Sichtprüfung', 'Details_1')
    def on_change_Direkte_Sichtprüfung_Details1(self):
        tab1=[]
        if(self.Details_1 =="nach 4.2.3"):
            tab1.append(('direkt','direkt'))
            tab1.append(('remote','remote'))
            return tab1
        else:
           if(self.Details_1 =="unbenutzt"):
            tab1.append((' ',' '))
            return tab1
