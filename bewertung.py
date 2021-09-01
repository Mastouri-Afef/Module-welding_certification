# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.model import (
    Workflow, ModelView, ModelSQL, fields,DeactivableMixin, MultiValueMixin, Unique, sequence_ordered, tree)
from trytond.transaction import Transaction
from trytond.pyson import Eval, If, Bool
from trytond.pool import Pool, PoolMeta
from trytond.wizard import Wizard, StateTransition, StateView, Button, StateReport
from trytond.report import Report
from collections import defaultdict, namedtuple
import datetime



#Bewertung für iso 96061
class Bewertung(Workflow, ModelSQL, ModelView):
    'Bewertung'
    __name__ = 'bewertung.bewertung'
    name_des_schweißers = fields.Many2One('party.party', "Name",
        ondelete='CASCADE', select=True)               
    bezeichnung_info = fields.Many2One('welding.iso96061', "Bezeichnung Info",
        ondelete='CASCADE', select=True)
    bezeichnung2 = fields.Many2One('welding.iso96061', "Bezeichnung 2",
        ondelete='CASCADE', select=True)
    bezeichnung3 = fields.Many2One('welding.iso96061', "Bezeichnung 3", 
        ondelete='CASCADE', select=True)
    about_normes = fields.Many2One('bewertung.iso5817', "About Normes", 
        ondelete='CASCADE', select=True)
    decklages = fields.One2Many('bewertung.bewertung.sichtprüfung_decklage','bewertung',
        "Sichtprüfung nach DIN EN ISO 17637- Decklage",
        states={
            'invisible': Bool(Eval('unsichtbar'))})
    kehlnahts = fields.One2Many('bewertung.bewertung.sichtprüfung_kehlnaht','bewertung',
        "Sichtprüfung nach DIN EN ISO 17637- Kehlnaht",
        states={
            'invisible': Bool(Eval('unsichtbar2'))})        
    durchstrahlungsprüfungs = fields.One2Many('bewertung.bewertung.durchstrahlungsprüfung','bewertung',
        "Durchstrahlungsprüfung nach DIN EN ISO 17636-1/2(Film oder digitaler Detektor)",
        states={ 
            'invisible': Bool(Eval('unsichtbar3'))})                
    bruchprüfungs = fields.One2Many('bewertung.bewertung.bruchprüfung','bewertung',
        "Bruchprüfung nach DIN EN ISO 9017",
        states={
            'invisible': Bool(Eval('unsichtbar4'))})                        
    biegeprüfungs = fields.One2Many('bewertung.bewertung.biegeprüfung','bewertung',
        "Biegeprüfung nach EN ISO 5173",
        states={
            'invisible': Bool(Eval('unsichtbar5'))})          
    weiteres = fields.One2Many('bewertung.bewertung.weitere_prüfung','bewertung',
        "Weitere Prüfung nach DIN EN *5)")
    geburts_tag = fields.Function(fields.Char("Geburts-Tag"), 'on_change_with_geburts_tag')      
    prüf_nr = fields.Function(fields.Char(
        "Prüf-Nr Bezeichnung 1"),'on_change_with_prüf_nr')
    norm_bezeichnung_info = fields.Function(fields.Char(
        "Bezeichnung"),'on_change_with_norm_bezeichnung_info')   
    bezeichnung1 = fields.Function(fields.Char(
        "Bezeichnung"),'on_change_with_bezeichnung1') 
    norm2 = fields.Function(fields.Char(
        "Norm 2"),'on_change_with_norm2')
    norm3 = fields.Function(fields.Char(
        "Norm 3"),'on_change_with_norm3')
    prüf_nr2 = fields.Function(fields.Char(
        "Prüf-Nr 2"),'on_change_with_prüf_nr2')
    prüf_nr3 = fields.Function(fields.Char(
        "Prüf-Nr 3"),'on_change_with_prüf_nr3')                                   
    sichtprüfung_wurzel = fields.Char("Sichtprüfung Wurzel",
        states={
            'invisible': Bool(Eval('unsichtbar'))})   
    keine_stumpfnaht = fields.Char("Keine Stumpfnaht",
        states={
            'invisible': (~Eval('unsichtbar') == True)
        },
        depends=['unsichtbar'])
    state = fields.Selection([
            ('draft', 'Draft'),
            ('confirmed', 'Confirmed'),
            ('canceled', 'Cancelled'),
            ], 'State', required=True, readonly=True, select=True)        
    keine_kehlnaht = fields.Char("Keine Kehlnaht",
        states={
            'invisible': (~Eval('unsichtbar2') == True)
        },
        depends=['unsichtbar2'])     
    keine_durchstrahlungsprüfung = fields.Char("Durchstrahlungsprüfung nicht gefordert",
        states={
            'invisible': (~Eval('unsichtbar3') == True)
        },
        depends=['unsichtbar3'])   
    keine_bruchprüfung = fields.Char("Bruchprüfung nicht gefordert",
        states={
            'invisible': (~Eval('unsichtbar4') == True)
        }, 
        depends=['unsichtbar4']) 
    keine_biegeprüfung = fields.Char("Biegeprüfung nicht gefordert",
        states={
            'invisible': (~Eval('unsichtbar5') == True)
        },
        depends=['unsichtbar4'])         
    unsichtbar = fields.Boolean("Unsichtbar") 
    unsichtbar2 = fields.Boolean("Unsichtbar")         
    unsichtbar3 = fields.Boolean("Unsichtbar") 
    unsichtbar4 = fields.Boolean("Unsichtbar") 
    unsichtbar5 = fields.Boolean("Unsichtbar")                                                             
    fachkunde = fields.Selection([
        ('Bestanden', 'Bestanden'),
        ('nicht geprüft', 'nicht geprüft'),
        ('nicht bestanden', 'nich bestanden'),
        ], "Fachkunde")
    gesamt = fields.Selection([
        ('erfüllt', 'erfüllt'),
        ('erfüllt', 'nicht erfüllt'),
        ], "Gesamt bewertung")
    normes = fields.Selection([
        ('EN ISO 9606-1', 'EN ISO 9606-1'),
        ('DIN EN 287-1', 'DIN EN 287-1'),
        ], "Normes")       
    title_bezeichnung = fields.Text("Prüfungsbezeichnung")
    title_norm = fields.Text("Norm")
    prüf_nr1 = fields.Char("Prüf-Nr 1")
    norm1 = fields.Char("Norm 1")       
    notice1 = fields.Text("Bewertungsgrundlage")
    notice2 = fields.Text("DIN EN ISO 5817 (Stahl, Nickel, Titan)")
    notice3 = fields.Text("DIN EN ISO 10042 (Aliminum)")
    bewertungs_id = fields.Char("Bewertungs ID")
    prüf_nr_info = fields.Char("int Prüf.-Nr")
    notice5 = fields.Text("zur Schweißer-Prüfungsbescheinigung nach")
    notice6 = fields.Text("(Abschnitt 7)")
    test = fields.Char("Test")
    kartei = fields.Integer("Kartei-Nr")
    pers_nr = fields.Integer("Pers.-Nr")
    pruefstelle = fields.Char("Prüfstelle")
    title_pruef_nr = fields.Text("Prüf.-Nr")
    text1 = fields.Text("Prüfungsbeauftrager")
    text2 = fields.Text("(Datum, Name und Unterschrift)")
    text3 = fields.Char("Datum und Unterschrift des Prüfers")
    datum_info = fields.Date("Datum des Prüfers")
    index1 = fields.Text("*1)e = erfüllt,ne = nicht erfüllt")
    index2 = fields.Text("*2)Ordnungsnummern der Unregelmäßigkeiten nach ISO 6520-1")
    index3 = fields.Text("*3)W = Wurzel, D=Decklage")
    index4 = fields.Text("*4)S = Schweißgut")
    index41 = fields.Text("100 Risse")
    index42 = fields.Text("5011 Einbrandkerbe")
    index43 = fields.Text("Ü Übergang")
    index44 = fields.Text("2011 Poren")
    index45 = fields.Text("5013 Wurzelkerbe")
    index46 = fields.Text("G = Grundwerkstoff")
    index47 = fields.Text("2013 Porennest")
    index48 = fields.Text("502 Zu große Nahtüberhöhung(BW)")
    index49 = fields.Text("2016 Schlauchporen")
    index491 = fields.Text("503 Zu große Nahtüberhöhung(FW)")
    index5 = fields.Text("*5) ISO 23277 Eindringprüfung")
    index51 = fields.Text("300 Feste Einchlüsse")
    index52 = fields.Text('504 Zu große Wurzelüberhöhung')
    index53 = fields.Text("ISO 23278 Magnetpulverprüfung")
    index54 = fields.Text("401 Bindefehler")
    index55 = fields.Text("507 Kantenversatz")
    index56 = fields.Text("ISO 17639 Mikro-/Makroskopie")
    index57 = fields.Text("402 Ungenügende")
    index58 = fields.Text("511 Decklagenunterwölbung")
    index59 = fields.Text("ISO 17640 Ultraschallprüfung")
    index60 = fields.Text("Durchschweißung")
    index61 = fields.Text("512 Übermäßige Asymmetrie (FW)")
    bestätigung_gemäß = fields.Text("Bestätigung gemäß")
    din_en_iso =fields.Text("DIN EN ISO 9606-1")
    tabelle = fields.Text("Tabelle 12 Index")
    prüfungsbeauftrager = fields.Char("Prüfungsbeauftrager")
    vorgaben = fields.Char("Vorgaben für Grenzwerte löschen: ")    
    

    @classmethod
    def __setup__(cls):
        super().__setup__()
        cls._order.insert(0, ('name_des_schweißers', 'ASC'))   
        cls._transitions |= set((
                ('draft', 'confirmed'),
                ('draft', 'canceled'),
                ('confirmed', 'canceled'),
                ('canceled', 'draft'),
                ))    
        cls._buttons.update({
                'print': {},        
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
                                                      
    @staticmethod
    def default_biegeprüfung():
        return [{"Prob_nr":"1","Biege_richtung":"3","Befund":"4","Bewertung":"5"}]
  
    @fields.depends('bezeichnung2')
    def on_change_with_norm2(self,name=None):
        if self.bezeichnung2:
            return self.bezeichnung2.vorschrift_prüfnorm  
        else:
            return ''  
            
    @fields.depends('name_des_schweißers')
    def on_change_with_geburts_tag(self,name=None):
        if self.name_des_schweißers:
            return self.name_des_schweißers.birthday             
              
    @fields.depends('bezeichnung3')
    def on_change_with_norm3(self,name=None):
        if self.bezeichnung3:
            return self.bezeichnung3.vorschrift_prüfnorm
        else:
            return ''
                          
    @fields.depends('bezeichnung2')
    def on_change_with_prüf_nr2(self,name=None):
        if self.bezeichnung2:
            return self.bezeichnung2.prüfer_prüfstelle_beleg_nr
        else:
            return '' 
                  
    @fields.depends('bezeichnung3')
    def on_change_with_prüf_nr3(self,name=None):
        if self.bezeichnung3:
            return self.bezeichnung3.prüfer_prüfstelle_beleg_nr
        else:
            return ''   
            
    @fields.depends('bezeichnung_info')
    def on_change_with_prüf_nr(self,name=None):
        if self.bezeichnung_info:
            return self.bezeichnung_info.prüfer_prüfstelle_beleg_nr
        else:
            return ''    
                      
    @fields.depends('bezeichnung_info')
    def on_change_with_norm_bezeichnung_info(self,name=None):
        if self.bezeichnung_info:
            return self.bezeichnung_info.vorschrift_prüfnorm
        else:
            return '' 
                  
    @fields.depends('bezeichnung_info')
    def on_change_with_bezeichnung1(self,name=None):
        if self.bezeichnung_info:
            return self.bezeichnung_info.bezeichnung2   
        else:
            return ''   
                       
    def get_rec_name(self,normes):
        return "Bewertung"

    @classmethod
    @ModelView.button_action('welding_certification.report_bewertung')
    def print(cls, bewertungs):
       pass

    @classmethod
    @ModelView.button
    @Workflow.transition('canceled')
    def cancel(cls, bewertungs):
        pass

    @classmethod
    @ModelView.button
    @Workflow.transition('draft')
    def draft(cls, bewertungs):
        pass

    @classmethod
    @ModelView.button
    @Workflow.transition('confirmed')
    def confirm(cls, bewertungs):
        pass


    @classmethod
    def delete(cls, bewertungs):
        for bewertung in bewertungs:
            if bewertung.state != 'draft':
                raise AccessError(gettext('welding_certification.delete_non_draft',
                    ws=bewertung.rec_name))
        super(Bewertung, cls).delete(bewertungs)

#Formulaires für ISO Normes
class BewertungIso5817(Workflow, ModelSQL, ModelView):
    'Bewertung Iso 5817'
    __name__ = 'bewertung.iso5817'
    bewertungsgrundlage = fields.Function(fields.Char(
        "Bewertungsgrundlage                                "), 'compute_selection') 
    rohwand_nennmaß = fields.Function(fields.Char(
        "t-Rohwand_Nennmaß"), 'compute_selection1') 
    breite_der_nahtüberhöhung = fields.Function(fields.Char(
        "b - Breite der Nahtüberhöhung: mm; b - Breite der Wurzelüberhöhung: mm"), 'compute_selection2')  
    nenmaß_kehlnahtdicke = fields.Selection('on_change_fw_kehlnaht_1', "a-Nenmaß der Kehlnahtdicke(mm)",
        states = {'invisible': Bool(Eval('stahl'))})   
    breite_nahtüberhöhung = fields.Selection('on_change_fw_kehlnahtt_2', "b - Breite der Nahtüberhöhung(mm)") 
    nennmaß_stumpfnahtdicke = fields.Selection('on_change_Rohrwand2', "s - Nennmaß der Stumpfnahtdicke (mm)")  
    breite_wurzelüberhöhung = fields.Selection('on_change_Rohrwand3', "b - Breite der Wurzelüberhöhung(mm)")  
    data_bemerkung = fields.Function(fields.Char("Bemerkung"),"On_change_aliminium") # Fonction pour Bemerkung 
    res_d1 = fields.Function(fields.Char("Res_D1"),"on_change_Rohrwand_d1") # fonction pour d1
    res_c1 = fields.Function(fields.Char("Res_C1"),"on_change_Rohrwand_c1") # fonction pour c1
    res_b1 = fields.Function(fields.Char("Res_B1"),"on_change_Rohrwand_b1") # fonction pour b1    
    res_d2 = fields.Function(fields.Char("Res_D2"),"on_change_Rohrwand_d2") # fonction pour d2
    res_c2 = fields.Function(fields.Char("Res_C2"),"on_change_Rohrwand_c2") # fonction pour c2
    res_b2 = fields.Function(fields.Char("Res_B2"),"on_change_Rohrwand_b2") # fonction pour b2
    res_d3 = fields.Function(fields.Char("Res_D3"),"on_change_Rohrwand_d3") # fonction pour d3
    res_c3 = fields.Function(fields.Char("Res_C3"),"on_change_Rohrwand_c3") # fonction pour c3
    res_b3 = fields.Function(fields.Char("Res_B3"),"on_change_Rohrwand_b3") # fonction pour b3
    res_d4 = fields.Function(fields.Char("Res_D4"),"on_change_Rohrwand_d4") # fonction pour d4
    res_c4 = fields.Function(fields.Char("Res_C4"),"on_change_Rohrwand_c4") # fonction pour c4
    res_b4 = fields.Function(fields.Char("Res_B4"),"on_change_Rohrwand_b4") # fonction pour b4
    res_d5 = fields.Function(fields.Char("Res_D5"),"on_change_Rohrwand_d5") # fonction pour d5
    res_c5 = fields.Function(fields.Char("Res_C5"),"on_change_Rohrwand_c5") # fonction pour c5
    res_b5 = fields.Function(fields.Char("Res_B5"),"on_change_Rohrwand_b5") # fonction pour b5
    res_d6 = fields.Function(fields.Char("Res_D6"),"on_change_Rohrwand_d6") # fonction pour d6
    res_c6 = fields.Function(fields.Char("Res_C6"),"on_change_Rohrwand_c6") # fonction pour c6
    res_b6 = fields.Function(fields.Char("Res_B6"),"on_change_Rohrwand_b6") # fonction pour b6
    res_d7 = fields.Function(fields.Char("Res_D7"),"on_change_Rohrwand_d7") # fonction pour d7
    res_c7 = fields.Function(fields.Char("Res_C7"),"on_change_Rohrwand_c7") # fonction pour c7
    res_b7 = fields.Function(fields.Char("Res_B7"),"on_change_Rohrwand_b7") # fonction pour b7
    res_d8 = fields.Function(fields.Char("Res_D8"),"on_change_Rohrwand_d8") # fonction pour d8
    res_c8 = fields.Function(fields.Char("Res_C8"),"on_change_Rohrwand_c8") # fonction pour c8
    res_b8 = fields.Function(fields.Char("Res_B8"),"on_change_Rohrwand_b8") # fonction pour b8
    res_d9 = fields.Function(fields.Char("Res_D9"),"on_change_Rohrwand_d9") # fonction pour d9
    res_c9 = fields.Function(fields.Char("Res_C9"),"on_change_Rohrwand_c9") # fonction pour c9
    res_b9 = fields.Function(fields.Char("Res_B9"),"on_change_Rohrwand_b9") # fonction pour b9
    res_d10 = fields.Function(fields.Char("Res_D10"),"on_change_Rohrwand_d10") # fonction pour d10
    res_c10 = fields.Function(fields.Char("Res_C10"),"on_change_Rohrwand_c10") # fonction pour c10
    res_b10 = fields.Function(fields.Char("Res_B10"),"on_change_Rohrwand_b10") # fonction pour b10
    res_d11 = fields.Function(fields.Char("Res_D11"),"on_change_Rohrwand_d11") # fonction pour d11
    res_c11 = fields.Function(fields.Char("Res_C11"),"on_change_Rohrwand_c11") # fonction pour c11
    res_b11 = fields.Function(fields.Char("Res_B11"),"on_change_Rohrwand_b11") 
    res_d12 = fields.Function(fields.Char("Res_D12"),"on_change_Rohrwand_d12") # fonction pour d12
    res_c12 = fields.Function(fields.Char("Res_C12"),"on_change_Rohrwand_c12") # fonction pour c12
    res_b12 = fields.Function(fields.Char("Res_B12"),"on_change_Rohrwand_b12") # fonction pour b12 
    res_d13 = fields.Function(fields.Char("Res_D13"),"on_change_Rohrwand_d13") # fonction pour d13
    res_c13 = fields.Function(fields.Char("Res_C13"),"on_change_Rohrwand_c13") # fonction pour c13
    res_b13 = fields.Function(fields.Char("Res_B13"),"on_change_Rohrwand_b13") # fonction pour b13
    res_d14 = fields.Function(fields.Char("Res_D14"),"on_change_Rohrwand_d14") # fonction pour d14
    res_c14 = fields.Function(fields.Char("Res_C14"),"on_change_Rohrwand_c14") # fonction pour c14
    res_b14 = fields.Function(fields.Char("Res_B14"),"on_change_Rohrwand_b14") # fonction pour b14
    res_d15 = fields.Function(fields.Char("Res_D15"),"on_change_Rohrwand_d15") # fonction pour d15
    res_c15 = fields.Function(fields.Char("Res_C15"),"on_change_Rohrwand_c15") # fonction pour c15
    res_b15 = fields.Function(fields.Char("Res_B15"),"on_change_Rohrwand_b15") # fonction pour b15
    res_d16 = fields.Function(fields.Char("Res_D16"),"on_change_Rohrwand_d16") # fonction pour d16
    res_c16 = fields.Function(fields.Char("Res_C16"),"on_change_Rohrwand_c16") # fonction pour c16
    res_b16 = fields.Function(fields.Char("Res_B16"),"on_change_Rohrwand_b16") # fonction pour b16
    res_d17 = fields.Function(fields.Char("Res_D17"),"on_change_Rohrwand_d17") # fonction pour d17
    res_c17 = fields.Function(fields.Char("Res_C17"),"on_change_Rohrwand_c17") # fonction pour c17
    res_b17 = fields.Function(fields.Char("Res_B17"),"on_change_Rohrwand_b17") # fonction pour b17
    res_d18 = fields.Function(fields.Char("Res_D18"),"on_change_Rohrwand_d18") # fonction pour d18
    res_c18 = fields.Function(fields.Char("Res_C18"),"on_change_Rohrwand_c18") # fonction pour c18
    res_b18 = fields.Function(fields.Char("Res_B18"),"on_change_Rohrwand_b18") # fonction pour b18
    res_d19 = fields.Function(fields.Char("Res_D19"),"on_change_Rohrwand_d19") # fonction pour d19
    res_c19 = fields.Function(fields.Char("Res_C19"),"on_change_Rohrwand_c19") # fonction pour c19
    res_b19 = fields.Function(fields.Char("Res_B19"),"on_change_Rohrwand_b19") # fonction pour b19
    res_d20 = fields.Function(fields.Char("Res_D20"),"on_change_Rohrwand_d20") # fonction pour d20
    res_c20 = fields.Function(fields.Char("Res_C20"),"on_change_Rohrwand_c20") # fonction pour c20
    res_b20 = fields.Function(fields.Char("Res_B20"),"on_change_Rohrwand_b20") # fonction pour b20
    res_d21 = fields.Function(fields.Char("Res_D21"),"on_change_Rohrwand_d21") # fonction pour d21
    res_c21 = fields.Function(fields.Char("Res_C21"),"on_change_Rohrwand_c21") # fonction pour c21
    res_b21 = fields.Function(fields.Char("Res_B21"),"on_change_Rohrwand_b21") # fonction pour b21
    res_d22 = fields.Function(fields.Char("Res_D22"),"on_change_Rohrwand_d22") # fonction pour d22
    res_c22 = fields.Function(fields.Char("Res_C22"),"on_change_Rohrwand_c22") # fonction pour c22
    res_b22 = fields.Function(fields.Char("Res_B22"),"on_change_Rohrwand_b22") # fonction pour b22
    res_d23 = fields.Function(fields.Char("Res_D23"),"on_change_Rohrwand_d23") # fonction pour d23
    res_c23 = fields.Function(fields.Char("Res_C23"),"on_change_Rohrwand_c23") # fonction pour c23
    res_b23 = fields.Function(fields.Char("Res_B23"),"on_change_Rohrwand_b23") # fonction pour b23
    res_d24 = fields.Function(fields.Char("Res_D24"),"on_change_Rohrwand_d24") # fonction pour d24
    res_c24 = fields.Function(fields.Char("Res_C24"),"on_change_Rohrwand_c24") # fonction pour c24
    res_b24 = fields.Function(fields.Char("Res_B24"),"on_change_Rohrwand_b24") # fonction pour b24
    res_d25 = fields.Function(fields.Char("Res_D25"),"on_change_Rohrwand_d25") # fonction pour d25
    res_c25 = fields.Function(fields.Char("Res_C25"),"on_change_Rohrwand_c25") # fonction pour c25
    res_b25 = fields.Function(fields.Char("Res_B25"),"on_change_Rohrwand_b25") # fonction pour b25
    res_d26 = fields.Function(fields.Char("Res_D26"),"on_change_Rohrwand_d26") # fonction pour d26
    res_c26 = fields.Function(fields.Char("Res_C26"),"on_change_Rohrwand_c26") # fonction pour c26
    res_b26 = fields.Function(fields.Char("Res_B26"),"on_change_Rohrwand_b26") # fonction pour b26
    res_d1_innere = fields.Function(fields.Char("Res_D1 Innere"),"on_change_Rohrwand_d1_innere") # fonction pour d1_innere
    res_c1_innere = fields.Function(fields.Char("Res_C1 Innere"),"on_change_Rohrwand_c1_innere") # fonction pour c1_innere
    res_b1_innere = fields.Function(fields.Char("Res_B1 Innere"),"on_change_Rohrwand_b1_innere") # fonction pour b1_innere
    res_d2_innere = fields.Function(fields.Char("Res_D2 Innere"),"on_change_Rohrwand_d2_innere") # fonction pour d2_innere
    res_c2_innere = fields.Function(fields.Char("Res_C2 Innere"),"on_change_Rohrwand_c2_innere") # fonction pour c2_innere
    res_b2_innere = fields.Function(fields.Char("Res_B2 Innere"),"on_change_Rohrwand_b2_innere") # fonction pour b2_innere
    res_d3_innere = fields.Function(fields.Char("Res_D3 Innere"),"on_change_Rohrwand_d3_innere") # fonction pour d3_innere
    res_c3_innere = fields.Function(fields.Char("Res_C3 Innere"),"on_change_Rohrwand_c3_innere") # fonction pour c3_innere
    res_b3_innere = fields.Function(fields.Char("Res_B3 Innere"),"on_change_Rohrwand_b3_innere") # fonction pour b3_innere
    res_d4_innere = fields.Function(fields.Char("Res_D4 Innere"),"on_change_Rohrwand_d4_innere") # fonction pour d4_innere
    res_c4_innere = fields.Function(fields.Char("Res_C4 Innere"),"on_change_Rohrwand_c4_innere") # fonction pour c4_innere
    res_b4_innere = fields.Function(fields.Char("Res_B4 Innere"),"on_change_Rohrwand_b4_innere") # fonction pour b4_innere
    res_d5_innere = fields.Function(fields.Char("Res_D5 Innere"),"on_change_Rohrwand_d5_innere") # fonction pour d5_innere
    res_c5_innere = fields.Function(fields.Char("Res_C5 Innere"),"on_change_Rohrwand_c5_innere") # fonction pour c5_innere
    res_b5_innere = fields.Function(fields.Char("Res_B5 Innere"),"on_change_Rohrwand_b5_innere") # fonction pour b5_innere
    res_d6_innere = fields.Function(fields.Char("Res_D6 Innere"),"on_change_Rohrwand_d6_innere") # fonction pour d6_innere
    res_c6_innere = fields.Function(fields.Char("Res_C6 Innere"),"on_change_Rohrwand_c6_innere") # fonction pour c6_innere
    res_b6_innere = fields.Function(fields.Char("Res_B6 Innere"),"on_change_Rohrwand_b6_innere") # fonction pour b6_innere
    res_d7_innere = fields.Function(fields.Char("Res_D7 Innere"),"on_change_Rohrwand_d7_innere") # fonction pour d7_innere
    res_c7_innere = fields.Function(fields.Char("Res_C7 Innere"),"on_change_Rohrwand_c7_innere") # fonction pour c7_innere
    res_b7_innere = fields.Function(fields.Char("Res_B7 Innere"),"on_change_Rohrwand_b7_innere") # fonction pour b7_innere
    res_d8_innere = fields.Function(fields.Char("Res_D8 Innere"),"on_change_Rohrwand_d8_innere") # fonction pour d8_innere
    res_c8_innere = fields.Function(fields.Char("Res_C8 Innere"),"on_change_Rohrwand_c8_innere") # fonction pour c8_innere
    res_b8_innere = fields.Function(fields.Char("Res_B8 Innere"),"on_change_Rohrwand_b8_innere") # fonction pour b8_innere
    res_d9_innere = fields.Function(fields.Char("Res_D9 Innere"),"on_change_Rohrwand_d9_innere") # fonction pour d9_innere
    res_c9_innere = fields.Function(fields.Char("Res_C9 Innere"),"on_change_Rohrwand_c9_innere") # fonction pour c9_innere
    res_b9_innere = fields.Function(fields.Char("Res_B9 Innere"),"on_change_Rohrwand_b9_innere") # fonction pour b9_innere
    res_d10_innere = fields.Function(fields.Char("Res_D10 Innere"),"on_change_Rohrwand_d10_innere") # fonction pour d10_innere
    res_c10_innere = fields.Function(fields.Char("Res_C10 Innere"),"on_change_Rohrwand_c10_innere") # fonction pour c10_innere
    res_b10_innere = fields.Function(fields.Char("Res_B10 Innere"),"on_change_Rohrwand_b10_innere") # fonction pour b10_innere
    res_d11_innere = fields.Function(fields.Char("Res_D11 Innere"),"on_change_Rohrwand_d11_innere") # fonction pour d11_innere
    res_c11_innere = fields.Function(fields.Char("Res_C11 Innere"),"on_change_Rohrwand_c11_innere") # fonction pour c11_innere
    res_b11_innere = fields.Function(fields.Char("Res_B11 Innere"),"on_change_Rohrwand_b11_innere") # fonction pour b11_innere
    res_d12_innere = fields.Function(fields.Char("Res_D12 Innere"),"on_change_Rohrwand_d12_innere") # fonction pour d12_innere
    res_c12_innere = fields.Function(fields.Char("Res_C12 Innere"),"on_change_Rohrwand_c12_innere") # fonction pour c12_innere
    res_b12_innere = fields.Function(fields.Char("Res_B12 Innere"),"on_change_Rohrwand_b12_innere") # fonction pour b12_innere
    res_d13_innere = fields.Function(fields.Char("Res_D13 Innere"),"on_change_Rohrwand_d13_innere") # fonction pour d13_innere
    res_c13_innere = fields.Function(fields.Char("Res_C13 Innere"),"on_change_Rohrwand_c13_innere") # fonction pour c13_innere
    res_b13_innere = fields.Function(fields.Char("Res_B13 Innere"),"on_change_Rohrwand_b13_innere") # fonction pour b13_innere
    res_d14_innere = fields.Function(fields.Char("Res_D14 Innere"),"on_change_Rohrwand_d14_innere") # fonction pour d14_innere
    res_c14_innere = fields.Function(fields.Char("Res_C14 Innere"),"on_change_Rohrwand_c14_innere") # fonction pour c14_innere
    res_b14_innere = fields.Function(fields.Char("Res_B14 Innere"),"on_change_Rohrwand_b14_innere") # fonction pour b14_innere
    res_d15_innere = fields.Function(fields.Char("Res_D15 Innere"),"on_change_Rohrwand_d15_innere") # fonction pour d15_innere
    res_c15_innere = fields.Function(fields.Char("Res_C15 Innere"),"on_change_Rohrwand_c15_innere") # fonction pour c15_innere
    res_b15_innere = fields.Function(fields.Char("Res_B15 Innere"),"on_change_Rohrwand_b15_innere") # fonction pour b15_innere
    res_d16_innere = fields.Function(fields.Char("Res_D16 Innere"),"on_change_Rohrwand_d16_innere") # fonction pour d16_innere
    res_c16_innere = fields.Function(fields.Char("Res_C16 Innere"),"on_change_Rohrwand_c16_innere") # fonction pour c16_innere
    res_b16_innere = fields.Function(fields.Char("Res_B16 Innere"),"on_change_Rohrwand_b16_innere") # fonction pour b16_innere   
    res_d17_innere = fields.Function(fields.Char("Res_D17 Innere"),"on_change_Rohrwand_d17_innere") # fonction pour d17_innere
    res_c17_innere = fields.Function(fields.Char("Res_C17 Innere"),"on_change_Rohrwand_c17_innere") # fonction pour c17_innere
    res_b17_innere = fields.Function(fields.Char("Res_B17 Innere"),"on_change_Rohrwand_b17_innere") # fonction pour b17_innere
    res_d18_innere = fields.Function(fields.Char("Res_D18 Innere"),"on_change_Rohrwand_d18_innere") # fonction pour d18_innere
    res_c18_innere = fields.Function(fields.Char("Res_C18 Innere"),"on_change_Rohrwand_c18_innere") # fonction pour c18_innere
    res_b18_innere = fields.Function(fields.Char("Res_B18 Innere"),"on_change_Rohrwand_b18_innere") # fonction pour b18_innere
    res_d19_innere = fields.Function(fields.Char("Res_D19 Innere"),"on_change_Rohrwand_d19_innere") # fonction pour d19_innere
    res_c19_innere = fields.Function(fields.Char("Res_C19 Innere"),"on_change_Rohrwand_c19_innere") # fonction pour c19_innere
    res_b19_innere = fields.Function(fields.Char("Res_B19 Innere"),"on_change_Rohrwand_b19_innere") # fonction pour b19_innere
    res_d20_innere = fields.Function(fields.Char("Res_D20 Innere"),"on_change_Rohrwand_d20_innere") # fonction pour d20_innere
    res_c20_innere = fields.Function(fields.Char("Res_C20 Innere"),"on_change_Rohrwand_c20_innere") # fonction pour c20_innere
    res_b20_innere = fields.Function(fields.Char("Res_B20 Innere"),"on_change_Rohrwand_b20_innere") # fonction pour b20_innere
    res_d21_innere = fields.Function(fields.Char("Res_D21 Innere"),"on_change_Rohrwand_d21_innere") # fonction pour d21_innere
    res_c21_innere = fields.Function(fields.Char("Res_C21 Innere"),"on_change_Rohrwand_c21_innere") # fonction pour c21_innere
    res_b21_innere = fields.Function(fields.Char("Res_B21 Innere"),"on_change_Rohrwand_b21_innere") # fonction pour b21_innere
    res_d1_unregel = fields.Function(fields.Char("Res_D1 Unregel"),"on_change_d1_Unregel") # fonction pour d1 Unregelmäßigkeit
    res_c1_unregel = fields.Function(fields.Char("Res_C1 Unregel"),"on_change_c1_Unregel") # fonction pour c1 Unregelmäßigkeit
    res_b1_unregel = fields.Function(fields.Char("Res_B1 Unregel"),"on_change_b1_Unregel") # fonction pour b1 Unregelmäßigkeit
    res_d2_unregel = fields.Function(fields.Char("Res_D2 Unregel"),"on_change_d2_Unregel") # fonction pour d2 Unregelmäßigkeit
    res_c2_unregel = fields.Function(fields.Char("Res_C2 Unregel"),"on_change_c2_Unregel") # fonction pour c2 Unregelmäßigkeit
    res_b2_unregel = fields.Function(fields.Char("Res_B2 Unregel"),"on_change_b2_Unregel") # fonction pour b2 Unregelmäßigkeit
    res_d3_unregel = fields.Function(fields.Char("Res_D3 Unregel"),"on_change_d3_Unregel") # fonction pour d3 Unregelmäßigkeit
    res_c3_unregel = fields.Function(fields.Char("Res_C3 Unregel"),"on_change_c3_Unregel") # fonction pour c3 Unregelmäßigkeit
    res_b3_unregel = fields.Function(fields.Char("Res_B3 Unregel"),"on_change_b3_Unregel") # fonction pour b3 Unregelmäßigkeit
    res_d4_unregel = fields.Function(fields.Char("Res_D4 Unregel"),"on_change_d4_Unregel") # fonction pour d4 Unregelmäßigkeit
    res_c4_unregel = fields.Function(fields.Char("Res_C4 Unregel"),"on_change_c4_Unregel") # fonction pour c4 Unregelmäßigkeit
    res_b4_unregel = fields.Function(fields.Char("Res_B4 Unregel"),"on_change_b4_Unregel") # fonction pour b4 Unregelmäßigkeit
    res_d1_part4 = fields.Function(fields.Char("Res_D1 Part4"),"on_change_d1_Part4") # fonction pour d1 Mahrfachunregelmäßigkeit
    res_c1_part4 = fields.Function(fields.Char("Res_C1 Part4"),"on_change_c1_Part4") # fonction pour c1 Mahrfachunregelmäßigkeit
    res_b1_part4 = fields.Function(fields.Char("Res_B1 Part4"),"on_change_b1_Part4") # fonction pour b1 Mahrfachunregelmäßigkeit
    res_d2_part4 = fields.Function(fields.Char("Res_D2 Part4"),"on_change_d2_Part4") # fonction pour d2 Mahrfachunregelmäßigkeit
    res_c2_part4 = fields.Function(fields.Char("Res_C2 Part4"),"on_change_c2_Part4") # fonction pour c2 Mahrfachunregelmäßigkeit
    res_b2_part4 = fields.Function(fields.Char("Res_B2 Part4"),"on_change_b2_Part4") # fonction pour b2 Mahrfachunregelmäßigkeit  
    res_bemerkung5 = fields.Function(fields.Char("Res_B5"),"on_change_Rohrwand_bemerkung5") # fonction pour b5
    res2 = fields.Function(fields.Char("Result2"),"on_change_Rohrwand1")    
    state = fields.Selection([
            ('draft', 'Draft'),
            ('confirmed', 'Confirmed'),
            ('canceled', 'Cancelled'),
            ], 'State', required=True, readonly=True, select=True)                           
    rohrwand = fields.Selection([
        ('0', '0'),    
        ('0,5', '0.5'),
        ('1,0', '1'),
        ('2,0', '2'),
        ('3,0', '3'),
        ('4,0', '4'),
        ('5,0', '5'),
        ('6,0', '6'),
        ('7,0', '7'),
        ('8,0', '8'),
        ('9,0', '9'),
        ('10,0', '10'),
        ('11,0', '11'),
        ('12,0', '12'),
        ('13,0', '13'),
        ('14,0', '14'),
        ('15,0', '15'),
        ('16,0', '16'),
        ('17,0', '17'),
        ('18,0', '18'),
        ('20,0', '20'),
        ('25,0', '25'),
        ('30,0', '30'),
        ('63,0', '63'),
        ], 't - Rohrwand oder Blechdicke (mm)')                      
    aliminium = fields.Boolean("Aluminium")
    stahl = fields.Boolean("Stahl, Nickel, Titan")
    bw_stumpfnaht = fields.Boolean("BW-Stumpfnaht")
    fw_kehlnaht = fields.Boolean("FW-Kehlnaht")
    voll_durchgeschweißt = fields.Boolean("voll durchgeschweißt") 
    number = fields.Char("Nr.")
    ordn_nr = fields.Char("Ordn.Nr. nach ISO 6520-1") 
    unregelmäßigkeit_benennung = fields.Char("Unregelmäßigkeit Benennung")        
    niedrig = fields.Char("niedrig (D)")
    mittel = fields.Char("mittel (C)")
    hoch = fields.Char("hoch (B)") 
    oberflächenunregelmäßigkeiten = fields.Char("1 Oberflächenunregelmäßigkeiten")      
    number_val1 = fields.Char("1.01")
    number_val2 = fields.Char("1.02")
    number_val3 = fields.Char("1.03")
    number_val4 = fields.Char("1.04")
    number_val5 = fields.Char("1.05")
    number_val6 = fields.Char("1.06")
    number_val7 = fields.Char("1.07")
    number_val8 = fields.Char("1.08")
    number_val9 = fields.Char("1.09")
    number_val10 = fields.Char("1.10")
    number_val11 = fields.Char("1.11")
    number_val12 = fields.Char("1.12")
    number_val13 = fields.Char("1.13")
    number_val14 = fields.Char("1.14")
    number_val15 = fields.Char("1.15")
    number_val16 = fields.Char("1.16")
    number_val17 = fields.Char("1.17")
    number_val18 = fields.Char("1.18")
    number_val19 = fields.Char("1.19")
    number_val20 = fields.Char("1.20")
    number_val21 = fields.Char("1.21")
    number_val22 = fields.Char("1.22")
    number_val23 = fields.Char("1.23") 
    ordn_nr_val1 = fields.Char("100")
    ordn_nr_val2 = fields.Char("104")
    ordn_nr_val3 = fields.Char("2017")
    ordn_nr_val4 = fields.Char("2025")
    ordn_nr_val5 = fields.Char("401")
    ordn_nr_val6 = fields.Char("4021")
    ordn_nr_val7 = fields.Char("5011")
    ordn_nr_val8 = fields.Char("5012")
    ordn_nr_val9 = fields.Char("5013")
    ordn_nr_val10 = fields.Char("502")
    ordn_nr_val11 = fields.Char("503")
    ordn_nr_val12 = fields.Char("504")
    ordn_nr_val13 = fields.Char("505")
    ordn_nr_val14 = fields.Char("506")
    ordn_nr_val15 = fields.Char("509")
    ordn_nr_val16 = fields.Char("511")
    ordn_nr_val17 = fields.Char("510")
    ordn_nr_val18 = fields.Char("512")
    ordn_nr_val19 = fields.Char("515")
    ordn_nr_val20 = fields.Char("516")
    ordn_nr_val21 = fields.Char("517")
    ordn_nr_val22 = fields.Char("5213")
    ordn_nr_val23 = fields.Char("5214")
    ordn_nr_val24 = fields.Char("601")
    ordn_nr_val25 = fields.Char("602")
    nr_1 = fields.Char("2.01")
    nr_2 = fields.Char("2.02")
    nr_3 = fields.Char("2.03")
    nr_4 = fields.Char("2.04")
    nr_5 = fields.Char("2.05")
    nr_6 = fields.Char("2.06")
    nr_7 = fields.Char("2.07")
    nr_8 = fields.Char("2.08")
    nr_9 = fields.Char("2.09")
    nr_10 = fields.Char("2.10")
    nr_11 = fields.Char("2.11")
    nr_12 = fields.Char("2.12")
    nr_13 = fields.Char("2.13")
    nr_14 = fields.Char("100")
    nr_15 = fields.Char("1001")
    nr_16 = fields.Char("2011")
    nr_17 = fields.Char("2012")
    nr_18 = fields.Char("2013")
    nr_19 = fields.Char("2014")
    nr_20 = fields.Char("2015")
    nr_21 = fields.Char("2016")
    nr_22 = fields.Char("202")
    nr_23 = fields.Char("2024")
    nr_24 = fields.Char("300")
    nr_25 = fields.Char("301")
    nr_26 = fields.Char("302")
    nr_27 = fields.Char("303")
    nr_28 = fields.Char("304")
    nr_29 = fields.Char("3042")
    nr_30 = fields.Char("401")
    nr_31 = fields.Char("4011")
    nr_32 = fields.Char("4012")
    nr_33 = fields.Char("4013")
    nr_34 = fields.Char("402")
    nr_35 = fields.Char("3.01")
    nr_36 = fields.Char("3.02")  
    nr_37 = fields.Char("5071")
    nr_38 = fields.Char("5072")
    nr_39 = fields.Char("508")
    nr_40 = fields.Char("617")
    nr_41 = fields.Char("4.01")
    nr_42 = fields.Char("4.02")      
    unregelmäßigkeit_benennung_val1 = fields.Char("Riss")
    unregelmäßigkeit_benennung_val2 = fields.Char("Endkraterriss")
    unregelmäßigkeit_benennung_val3 = fields.Char("Oberflächenpore")
    unregelmäßigkeit_benennung_val4 = fields.Char("Offener Endkraterlunker")
    unregelmäßigkeit_benennung_val5 = fields.Char("Bindefehler(unvollständige Bindung)")
    unregelmäßigkeit_benennung_val6 = fields.Char("Mikro-Bindefehler")
    unregelmäßigkeit_benennung_val7 = fields.Char("Ungenügender Wurzeleinbrand")
    unregelmäßigkeit_benennung_val8 = fields.Char("Durchlaufende Einbrandkerbe")
    unregelmäßigkeit_benennung_val9 = fields.Char("Nicht durchlaufende Einbrandkerbe")
    unregelmäßigkeit_benennung_val10 = fields.Char("Wurzelkerbe")
    unregelmäßigkeit_benennung_val11 = fields.Char("Zu große Nahtüberhöhung(Stumpfnaht)")
    unregelmäßigkeit_benennung_val12 = fields.Char("Zu große Nahtüberhöhung(Kehlnaht)")
    unregelmäßigkeit_benennung_val13 = fields.Char("Zu große Wurzelüberhöhung")
    unregelmäßigkeit_benennung_val14 = fields.Char("Schroffer Nahtübergang")
    unregelmäßigkeit_benennung_val15 = fields.Char("Schweißgutüberlauf")
    unregelmäßigkeit_benennung_val16 = fields.Char("Verlaufenes Schweißgut")
    unregelmäßigkeit_benennung_val17 = fields.Char("Decklagenunterwölbung")
    unregelmäßigkeit_benennung_val18 = fields.Char("Durchbrand")
    unregelmäßigkeit_benennung_val19 = fields.Char("Übermäßige Asymmetrie der kehlnaht")
    unregelmäßigkeit_benennung_val20 = fields.Char("Wurzelrückfall")
    unregelmäßigkeit_benennung_val21 = fields.Char("Wurzelporosität")
    unregelmäßigkeit_benennung_val22 = fields.Char("Ansatzfehler")
    unregelmäßigkeit_benennung_val23 = fields.Char("zu kleine Kehlnahtdicke")
    unregelmäßigkeit_benennung_val24 = fields.Char("Zu große Kehlnahtdicke")
    unregelmäßigkeit_benennung_val25 = fields.Char("Zündstelle")
    unregelmäßigkeit_benennung_val26 = fields.Char("Schweißspritzer") 
    risse = fields.Char("Risse")
    mikrorisse = fields.Char("Mikrorisse")
    pore = fields.Char("Pore")
    porosität = fields.Char("Porosität(gleichmäßig verteilt)")
    porennest = fields.Char("Porennest")
    porenzeile = fields.Char("Porenzeile")
    gaskanal = fields.Char("Gaskanal")
    schlauchpore = fields.Char("Schlauchpore")
    lunker = fields.Char("Lunker")
    endkraterlunker = fields.Char("Endkraterlunker")
    fester_einschluss = fields.Char("Fester Einschluss")
    schlackeneinschluss = fields.Char("Schlackeneinschluss")
    flussmitteleinschluss = fields.Char("Flussmitteleinschluss")
    oxideinschluss = fields.Char("Oxideinschluss")
    metallischer = fields.Char("Metallischer Einschluss außer kupfer")
    kupfereinschluss = fields.Char("Kupfereinschluss")
    bindefehler = fields.Char("Bindefehler (unvollständige bindung)")
    flankenbindefehler = fields.Char("Flankenbindefehler")
    lagenbindefehler = fields.Char("Lagenbindefehler")
    wurzelbindefehler = fields.Char("Wurzelbindefehler")
    ungenügende_durchschweißung = fields.Char("Ungenügende Durchschweißung") 
    kantenversatz_blechen = fields.Char("Kantenversatz bei Blechen")
    kantenversatz_rohren = fields.Char("Kantenversatz bei Rohren und Hohlprofilen")
    winkelversatz = fields.Char("Winkelversatz")
    schlechte_kehlnähten = fields.Char("Schlechte Passung an Kehlnähten")
    keine = fields.Char("Keine")
    mehrfachunregelmäßigkeit = fields.Char("Mehrfachunregelmäßigkeit in beliebigem QuerSchnitt")
    abbildungsfläche = fields.Char("Abbildungsfläche oder Querschnittsfläche in Längsrichtung")
    index1 = fields.Char("Bewertungsgrundlage : DIN EN ISO 10042(Aluminium);Stumpfnaht")
    index2 = fields.Char("zul - zulässig;nz - nicht zulässig - nicht zulässig ")
    index3 = fields.Char("b - Breite der Nahtüberhöhung:25 mm; b-Breite der Wurzelüberhöhung: 7 mm")
    index4 = fields.Char("zul - Zulässig; ns - nicht Zulässig")
    index5 = fields.Char("ö zul - örtlich zulässig; *1) siehe Norm")
    index6 = fields.Char("kU - nur kurze Unregelmäßigkeit zulässig")  
    result = fields.Char("result")
    d1 = fields.Char("D1")
    c1 = fields.Char("C1")
    b1 = fields.Char("B1")
    bemerkung1 = fields.Char("Bemerkung1")
    d2 = fields.Char("D2")
    c2 = fields.Char("C2")
    b2 = fields.Char("B2")
    bemerkung2 = fields.Char("Bemerkung2")
    d3 = fields.Char("D3")
    c3 = fields.Char("C3")
    b3 = fields.Char("B3")
    bemerkung3 = fields.Char("Bemerkung3")
    d4 = fields.Char("D4")
    c4 = fields.Char("C4")
    b4 = fields.Char("B4")
    bemerkung4 = fields.Char("Bemerkung4")
    d5 = fields.Char("D5")
    c5 = fields.Char("C5")
    b5 = fields.Char("B5")
    bemerkung5 = fields.Char("Bemerkung5")
    d6 = fields.Char("D6")
    c6 = fields.Char("C6")
    b6 = fields.Char("B6")
    bemerkung6 = fields.Char("Bemerkung6")
    d7 = fields.Char("D7")
    c7 = fields.Char("C7")
    b7 = fields.Char("B7")
    bemerkung7 = fields.Char("Bemerkung7")
    d8 = fields.Char("D8")
    c8 = fields.Char("C8")
    b8 = fields.Char("B8")
    bemerkung8 = fields.Char("Bemerkung8")
    d9 = fields.Char("D9")
    c9 = fields.Char("C9")
    b9 = fields.Char("B9")
    bemerkung9 = fields.Char("Bemerkung9")
    d10 = fields.Char("D10")
    c10 = fields.Char("C10")
    b10 = fields.Char("B10")
    bemerkung10 = fields.Char("Bemerkung10")
    d11 = fields.Char("D11")
    c11 = fields.Char("C11")
    b11 = fields.Char("B11")
    bemerkung11 = fields.Char("Bemerkung11")
    d12 = fields.Char("D12")
    c12 = fields.Char("C12")
    b12 = fields.Char("B12")
    bemerkung12 = fields.Char("Bemerkung12")
    d13 = fields.Char("D13")
    c13 = fields.Char("C13")
    b13 = fields.Char("B13")
    bemerkung13 = fields.Char("Bemerkung13")
    d14 = fields.Char("D14")
    c14 = fields.Char("C14")
    b14 = fields.Char("B14")
    bemerkung14 = fields.Char("Bemerkung14")
    d15 = fields.Char("D15")
    c15 = fields.Char("C15")
    b15 = fields.Char("B15")
    bemerkung15 = fields.Char("Bemerkung15")
    d16 = fields.Char("D16")
    c16 = fields.Char("C16")
    b16 = fields.Char("B16")
    bemerkung16 = fields.Char("Bemerkung16")
    d17 = fields.Char("D17")
    c17 = fields.Char("C17")
    b17 = fields.Char("B17")
    bemerkung17 = fields.Char("Bemerkung17")
    d18 = fields.Char("D18")
    c18 = fields.Char("C18")
    b18 = fields.Char("B18")
    bemerkung18 = fields.Char("Bemerkung18")
    d19 = fields.Char("D19")
    c19 = fields.Char("C19")
    b19 = fields.Char("B19")
    bemerkung19 = fields.Char("Bemerkung19")
    d20 = fields.Char("D20")
    c20 = fields.Char("C20")
    b20 = fields.Char("B20")
    bemerkung20 = fields.Char("Bemerkung20")
    d21 = fields.Char("D21")
    c21 = fields.Char("C21")
    b21 = fields.Char("B21")
    bemerkung21 = fields.Char("Bemerkung21")
    d22 = fields.Char("D22")
    c22 = fields.Char("C22")
    b22 = fields.Char("B22")
    bemerkung22 = fields.Char("Bemerkung22")
    d23 = fields.Char("D23")
    c23 = fields.Char("C23")
    b23 = fields.Char("B23")
    bemerkung23 = fields.Char("Bemerkung23")
    d24 = fields.Char("D24")
    c24 = fields.Char("C24")
    b24 = fields.Char("B24")
    bemerkung24 = fields.Char("Bemerkung24")
    d25 = fields.Char("D25")
    c25 = fields.Char("C25")
    b25 = fields.Char("B25")
    bemerkung25 = fields.Char("Bemerkung25")
    d26 = fields.Char("D26")
    c26 = fields.Char("C26")
    b26 = fields.Char("B26")
    bemerkung26 = fields.Char("Bemerkung26")
    bemerkung = fields.Char("Bemerkung")
    d1_innere = fields.Char("D1 Innere")
    c1_innere = fields.Char("C1 Innere")
    b1_innere = fields.Char("B1 Innere")
    bemerkung_innere = fields.Char("Bemerkung1 Innere")
    d2_innere = fields.Char("D2 Innere")
    c2_innere = fields.Char("C2 Innere")
    b2_innere = fields.Char("B2 Innere")
    bemerkung_innere2 = fields.Char("Bemerkung2 Innere")
    d3_innere = fields.Char("D3 Innere")
    c3_innere = fields.Char("C3 Innere")
    b3_innere = fields.Char("B3 Innere")
    bemerkung_innere3 = fields.Char("Bemerkung3 Innere")
    d4_innere = fields.Char("D4 Innere")
    c4_innere = fields.Char("C4 Innere")
    b4_innere = fields.Char("B4 Innere")
    bemerkung_innere4 = fields.Char("Bemerkung4 Innere")
    d5_innere = fields.Char("D5 Innere")
    c5_innere = fields.Char("C5 Innere")
    b5_innere = fields.Char("B5 Innere")
    bemerkung_innere5 = fields.Char("Bemerkung5 Innere")
    d6_innere = fields.Char("D6 Innere")
    c6_innere = fields.Char("C6 Innere")
    b6_innere = fields.Char("B6 Innere")
    bemerkung_innere6 = fields.Char("Bemerkung6 Innere")
    d7_innere = fields.Char("D7 Innere")
    c7_innere = fields.Char("C7 Innere")
    b7_innere = fields.Char("B7 Innere")
    bemerkung_innere7 = fields.Char("Bemerkung7 Innere")
    d8_innere = fields.Char("D8 Innere")
    c8_innere = fields.Char("C8 Innere")
    b8_innere = fields.Char("B8 Innere")
    bemerkung_innere8 = fields.Char("Bemerkung8 Innere")
    d9_innere = fields.Char("D9 Innere")
    c9_innere = fields.Char("C9 Innere")
    b9_innere = fields.Char("B9 Innere")
    bemerkung_innere9 = fields.Char("Bemerkung9 Innere")
    d10_innere = fields.Char("D10 Innere")
    c10_innere = fields.Char("C10 Innere")
    b10_innere = fields.Char("B10 Innere")
    bemerkung_innere10 = fields.Char("Bemerkung10 Innere")
    d11_innere = fields.Char("D11 Innere")
    c11_innere = fields.Char("C11 Innere")
    b11_innere = fields.Char("B11 Innere")
    bemerkung_innere11 = fields.Char("Bemerkung11 Innere")
    d12_innere = fields.Char("D12 Innere")
    c12_innere = fields.Char("C12 Innere")
    b12_innere = fields.Char("B12 Innere")
    bemerkung_innere12 = fields.Char("Bemerkung12 Innere")
    d13_innere = fields.Char("D13 Innere")
    c13_innere = fields.Char("C13 Innere")
    b13_innere = fields.Char("B13 Innere")
    bemerkung_innere13 = fields.Char("Bemerkung13 Innere")
    d14_innere = fields.Char("D14 Innere")
    c14_innere = fields.Char("C14 Innere")
    b14_innere = fields.Char("B14 Innere")
    bemerkung_innere14 = fields.Char("Bemerkung14 Innere")
    d15_innere = fields.Char("D15 Innere")
    c15_innere = fields.Char("C15 Innere")
    b15_innere = fields.Char("B15 Innere")
    bemerkung_innere15 = fields.Char("Bemerkung15 Innere")
    d16_innere = fields.Char("D16 Innere")
    c16_innere = fields.Char("C16 Innere")
    b16_innere = fields.Char("B16 Innere")
    bemerkung_innere16 = fields.Char("Bemerkung16 Innere")
    d17_innere = fields.Char("D17 Innere")
    c17_innere = fields.Char("C17 Innere")
    b17_innere = fields.Char("B17 Innere")
    bemerkung_innere17 = fields.Char("Bemerkung17 Innere")
    d18_innere = fields.Char("D18 Innere")
    c18_innere = fields.Char("C18 Innere")
    b18_innere = fields.Char("B18 Innere")
    bemerkung_innere18 = fields.Char("Bemerkung18 Innere")
    d19_innere = fields.Char("D19 Innere")
    c19_innere = fields.Char("C19 Innere")
    b19_innere = fields.Char("B19 Innere")
    bemerkung_innere19 = fields.Char("Bemerkung19 Innere")
    d20_innere = fields.Char("D20 Innere")
    c20_innere = fields.Char("C20 Innere")
    b20_innere = fields.Char("B20 Innere")
    bemerkung_innere20 = fields.Char("Bemerkung20 Innere")
    d21_innere = fields.Char("D21 Innere")
    c21_innere = fields.Char("C21 Innere")
    b21_innere = fields.Char("B21 Innere")
    d1_unregel = fields.Char("D1 Unregelmäßigkeit")
    c1_unregel = fields.Char("C1 Unregelmäßigkeit")
    b1_unregel = fields.Char("B1 Unregelmäßigkeit")
    bemerkung_unregel = fields.Char("Bemerkung1 Unregelmäßigkeit")
    d2_unregel = fields.Char("D2 Unregelmäßigkeit")
    c2_unregel = fields.Char("C2 Unregelmäßigkeit")
    b2_unregel = fields.Char("B2 Unregelmäßigkeit")
    bemerkung_unregel2 = fields.Char("Bemerkung2 Unregelmäßigkeit")
    d3_unregel = fields.Char("D3 Unregelmäßigkeit")
    c3_unregel = fields.Char("C3 Unregelmäßigkeit")
    b3_unregel = fields.Char("B3 Unregelmäßigkeit")
    bemerkung_unregel3 = fields.Char("Bemerkung3 Unregelmäßigkeit")
    d4_unregel = fields.Char("D4 Unregelmäßigkeit")
    c4_unregel = fields.Char("C4 Unregelmäßigkeit")
    b4_unregel = fields.Char("B4 Unregelmäßigkeit")
    bemerkung_unregel4 = fields.Char("Bemerkung4 Unregelmäßigkeit")
    d1_mahrfachunregelmäßigkeit = fields.Char("D1 Mahrfachunregelmäßigkeit")
    c1_mahrfachunregelmäßigkeit = fields.Char("C1 Mahrfachunregelmäßigkeit")
    b1_mahrfachunregelmäßigkeit = fields.Char("B1 Mahrfachunregelmäßigkeit")
    bemerkung_mahrfachunregelmäßigkeit_1 = fields.Char("Bemerkung 1 Mahrfachunregelmäßigkeit")
    d2_mahrfachunregelmäßigkeit = fields.Char("D2 Mahrfachunregelmäßigkeit")
    c2_mahrfachunregelmäßigkeit = fields.Char("C2 Mahrfachunregelmäßigkeit")
    b2_mahrfachunregelmäßigkeit = fields.Char("B2 Mahrfachunregelmäßigkeit")
    bemerkung_mahrfachunregelmäßigkeit_2 = fields.Char("Bemerkung 2 Mahrfachunregelmäßigkeit")

    @classmethod
    def __setup__(cls):
        super().__setup__()
        cls._transitions |= set((
                ('draft', 'confirmed'),
                ('draft', 'canceled'),
                ('confirmed', 'canceled'),
                ('canceled', 'draft'),
                ))    
        cls._buttons.update({
                'print': {},
                'compute': {},       
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
                                                                                                                                                                                                                  
    @staticmethod
    def default_nenmaß_kehlnahtdicke():
        return None
        
    @staticmethod
    def default_number():
        return " "
        
    @staticmethod
    def default_ordn_nr():
        return " "
        
    @staticmethod
    def default_unregelmäßigkeit_benennung():
        return " "
        
    @staticmethod
    def default_niedrig():
        return " "
        
    @staticmethod
    def default_mittel():
        return " "
        
    @staticmethod
    def default_hoch():
        return " "
        
    @fields.depends('stahl','bw_stumpfnaht','aliminium','fw_kehlnaht')
    def compute_selection(self,name=None):
        if(self.stahl == True and self.bw_stumpfnaht  == True):
            return "Bewertungsgrundlage: EN ISO 5817:2014 (Stahl,Nickel,Titan);Stumpfnaht"
        elif(self.stahl == True and self.fw_kehlnaht  == True):
            return "Bewertungsgrundlage: EN ISO 5817:2014 (Stahl,Nickel,Titan);Kehlnaht"
        elif(self.aliminium == True and self.fw_kehlnaht  == True):
            return "Bewertungsgrundlage: EN ISO 5817:2014 (Aluminium);Kehlnaht"
        else :
            return "Bewertungsgrundlage: EN ISO 5817:2014 (Aluminium);Stumpfnaht"
            
    @fields.depends('stahl','bw_stumpfnaht','aliminium','fw_kehlnaht')
    def compute_selection1(self,name=None):
        if(self.stahl == True and self.bw_stumpfnaht  == True) or (self.aliminium == True and self.bw_stumpfnaht == True):
            value_rohrwand = self.rohrwand
            value_nennmaß_stumpfnahtdicke = self.nennmaß_stumpfnahtdicke
            return "t-Rohrwand-oder Blechdicke: "+str(value_rohrwand)+"mm"+"; "+"s-Nennmaß der Stumpfnahtdicke:"+str(value_nennmaß_stumpfnahtdicke)+"mm"
        elif(self.stahl == True and self.fw_kehlnaht  == True) or (self.aliminium == True and self.fw_kehlnaht  == True):
            value_rohrwand = self.rohrwand
            value_breite_nahtüberhöhung = self.breite_nahtüberhöhung
            return "t-Rohrwand-oder Blechdicke: "+str(value_rohrwand)+"mm"+"; "+"a-Nenmaß der Kehlnahtdicke:"+str(value_breite_nahtüberhöhung)+"mm"
        else :
            return ""     

    @fields.depends('stahl','bw_stumpfnaht','aliminium','fw_kehlnaht')
    def compute_selection2(self,name=None):
        if(self.stahl == True and self.bw_stumpfnaht  == True) or (self.aliminium == True and self.bw_stumpfnaht == True):
            value_breite_nahtüberhöhung = self.breite_nahtüberhöhung
            value_breite_wurzelüberhöhung = self.breite_wurzelüberhöhung
            return "b-Breite der Nahtüberhöhung: "+str(value_breite_nahtüberhöhung)+" mm"+";"+" b-Breite der Wurzelüberhöhung: "+str(value_breite_wurzelüberhöhung)+" mm"
        elif(self.stahl == True and self.fw_kehlnaht  == True) or (self.aliminium == True and self.fw_kehlnaht  == True):
            value_breite_nahtüberhöhung = self.breite_nahtüberhöhung
            return "b-Breite der Nahtüberhöhung: "+str(value_breite_nahtüberhöhung)+" mm"
        else :
            return ""

    @classmethod
    @ModelView.button
    def compute(cls, BewertungIso5817):
        for norme in BewertungIso5817:
             val = norme.res2
             val1 = norme.res_d1
             val_c1 = norme.res_c1
             val_b1 = norme.res_b1
             val_D2 = norme.res_d2
             val_C2 = norme.res_c2
             val_B2 = norme.res_b2
             val_D3 = norme.res_d3
             val_C3 = norme.res_c3
             val_B3 = norme.res_b3
             val_D4 = norme.res_d4
             val_C4 = norme.res_c4
             val_B4 = norme.res_b4
             val_D5 = norme.res_d5
             val_C5 = norme.res_c5
             val_B5 = norme.res_b5
             val_Bemerkung5 = norme.res_bemerkung5
             val_D6 = norme.res_d6
             val_C6 = norme.res_c6
             val_B6 = norme.res_b6
             val_D7 = norme.res_d7
             val_C7 = norme.res_c7
             val_B7 = norme.res_b7
             val_D8 = norme.res_d8
             val_C8 = norme.res_c8
             val_B8 = norme.res_b8
             val_D9 = norme.res_d9
             val_C9 = norme.res_c9
             val_B9 = norme.res_b9
             val_D10 = norme.res_d10
             val_C10 = norme.res_c10
             val_B10 = norme.res_b10
             val_D11 = norme.res_d11
             val_C11 = norme.res_c11
             val_B11 = norme.res_b11
             val_D12 = norme.res_d12
             val_C12 = norme.res_c12
             val_B12 = norme.res_b12
             val_D13 = norme.res_d13
             val_C13 = norme.res_c13
             val_B13 = norme.res_b13
             val_D14 = norme.res_d14
             val_C14 = norme.res_c14
             val_B14 = norme.res_b14
             val_D15 = norme.res_d15
             val_C15 = norme.res_c15
             val_B15 = norme.res_b15
             val_D16 = norme.res_d16
             val_C16 = norme.res_c16
             val_B16 = norme.res_b16
             val_D17 = norme.res_d17
             val_C17 = norme.res_c17
             val_B17 = norme.res_b17
             val_D18 = norme.res_d18
             val_C18 = norme.res_c18
             val_B18 = norme.res_b18
             val_D19 = norme.res_d19
             val_C19 = norme.res_c19
             val_B19 = norme.res_b19
             val_D20 = norme.res_d20
             val_C20 = norme.res_c20
             val_B20 = norme.res_b20
             val_D21 = norme.res_d21
             val_C21 = norme.res_c21
             val_B21 = norme.res_b21
             val_D22 = norme.res_d22
             val_C22 = norme.res_c22
             val_B22 = norme.res_b22
             val_D23 = norme.res_d23
             val_C23 = norme.res_c23
             val_B23 = norme.res_b23
             val_D24 = norme.res_d24
             val_C24 = norme.res_c24
             val_B24 = norme.res_b24
             val_D25 = norme.res_d25
             val_C25 = norme.res_c25
             val_B25 = norme.res_b25
             val_D26 = norme.res_d26
             val_C26 = norme.res_c26
             val_B26 = norme.res_b26
             val_bemerkung = norme.data_bemerkung
             ValD1_innere =  norme.res_d1_innere
             ValC1_innere =  norme.res_c1_innere
             ValB1_innere =  norme.res_b1_innere
             ValD2_innere =  norme.res_d2_innere
             ValC2_innere =  norme.res_c2_innere
             ValB2_innere =  norme.res_b2_innere
             ValD3_innere =  norme.res_d3_innere
             ValC3_innere =  norme.res_c3_innere
             ValB3_innere =  norme.res_b3_innere
             ValD4_innere =  norme.res_d4_innere
             ValC4_innere =  norme.res_c4_innere
             ValB4_innere =  norme.res_b4_innere
             ValD5_innere =  norme.res_d5_innere
             ValC5_innere =  norme.res_c5_innere
             ValB5_innere =  norme.res_b5_innere
             ValD6_innere =  norme.res_d6_innere
             ValC6_innere =  norme.res_c6_innere
             ValB6_innere =  norme.res_b6_innere
             ValD7_innere =  norme.res_d7_innere
             ValC7_innere =  norme.res_c7_innere
             ValB7_innere =  norme.res_b7_innere
             ValD8_innere =  norme.res_d8_innere
             ValC8_innere =  norme.res_c8_innere
             ValB8_innere =  norme.res_b8_innere
             ValD9_innere =  norme.res_d9_innere
             ValC9_innere =  norme.res_c9_innere
             ValB9_innere =  norme.res_b9_innere
             ValD10_innere =  norme.res_d10_innere
             ValC10_innere =  norme.res_c10_innere
             ValB10_innere =  norme.res_b10_innere
             ValD11_innere =  norme.res_d11_innere
             ValC11_innere =  norme.res_c11_innere
             ValB11_innere =  norme.res_b11_innere
             ValD12_innere =  norme.res_d12_innere
             ValC12_innere =  norme.res_c12_innere
             ValB12_innere =  norme.res_b12_innere
             ValD13_innere =  norme.res_d13_innere
             ValC13_innere =  norme.res_c13_innere
             ValB13_innere =  norme.res_b13_innere
             ValD14_innere =  norme.res_d14_innere
             ValC14_innere =  norme.res_c14_innere
             ValB14_innere =  norme.res_b14_innere
             ValD15_innere =  norme.res_d15_innere
             ValC15_innere =  norme.res_c15_innere
             ValB15_innere =  norme.res_b15_innere
             ValD16_innere =  norme.res_d16_innere
             ValC16_innere =  norme.res_c16_innere
             ValB16_innere =  norme.res_b16_innere
             ValD17_innere =  norme.res_d17_innere
             ValC17_innere =  norme.res_c17_innere
             ValB17_innere =  norme.res_b17_innere
             ValD18_innere =  norme.res_d18_innere
             ValC18_innere =  norme.res_c18_innere
             ValB18_innere =  norme.res_b18_innere
             ValD19_innere =  norme.res_d19_innere
             ValC19_innere =  norme.res_c19_innere
             ValB19_innere =  norme.res_b19_innere
             ValD20_innere =  norme.res_d20_innere
             ValC20_innere =  norme.res_c20_innere
             ValB20_innere =  norme.res_b20_innere
             ValD21_innere =  norme.res_d21_innere
             ValC21_innere =  norme.res_c21_innere
             ValB21_innere =  norme.res_b21_innere
             ValD1_unregel = norme.res_d1_unregel
             ValC1_unregel = norme.res_c1_unregel
             ValB1_unregel = norme.res_b1_unregel
             ValD2_unregel = norme.res_d2_unregel
             ValC2_unregel = norme.res_c2_unregel
             ValB2_unregel = norme.res_b2_unregel
             ValD3_unregel = norme.res_d3_unregel
             ValC3_unregel = norme.res_c3_unregel
             ValB3_unregel = norme.res_b3_unregel
             ValD4_unregel = norme.res_d4_unregel
             ValC4_unregel = norme.res_c4_unregel
             ValB4_unregel = norme.res_b4_unregel
             ValD1part4 = norme.res_d1_part4
             ValC1part4 = norme.res_c1_part4
             ValB1part4 = norme.res_b1_part4
             ValD2part4 = norme.res_d2_part4
             ValC2part4 = norme.res_c2_part4
             ValB2part4 = norme.res_b2_part4
             cls.write(BewertungIso5817,{
                 'd1_mahrfachunregelmäßigkeit': ValD1part4,
                 'c1_mahrfachunregelmäßigkeit': ValC1part4,
                 'b1_mahrfachunregelmäßigkeit': ValB1part4,
                 'bemerkung_mahrfachunregelmäßigkeit_1': " ",
                 'd2_mahrfachunregelmäßigkeit': ValD2part4,
                 'c2_mahrfachunregelmäßigkeit': ValC2part4,
                 'b2_mahrfachunregelmäßigkeit': ValB2part4,
                 'bemerkung_mahrfachunregelmäßigkeit_2': " ",
                 'd1_unregel': ValD1_unregel,
                 'c1_unregel': ValC1_unregel,
                 'b1_unregel': ValB1_unregel,
                 'bemerkung_unregel': " ",
                 'd2_unregel': ValD2_unregel,
                 'c2_unregel': ValC2_unregel,
                 'b2_unregel': ValB2_unregel,
                 'bemerkung_unregel2': " ",
                 'd3_unregel': ValD3_unregel,
                 'c3_unregel': ValC3_unregel,
                 'b3_unregel': ValB3_unregel,
                 'bemerkung_unregel3': "für Prüfungen nicht angewendet",
                 'd4_unregel': ValD4_unregel,
                 'c4_unregel': ValC4_unregel,
                 'b4_unregel': ValB4_unregel,
                 'bemerkung_unregel4': " ",
                 'd1_innere': ValD1_innere,
                 'c1_innere': ValC1_innere,
                 'b1_innere': ValB1_innere,
                 'bemerkung_innere': " ",
                 'd2_innere': ValD2_innere,
                 'c2_innere': ValC2_innere,
                 'b2_innere': ValB2_innere,
                 'bemerkung_innere2': " ",
                 'd3_innere': ValD3_innere,
                 'c3_innere': ValC3_innere,
                 'b3_innere': ValB3_innere,
                 'bemerkung_innere3': " Größtmaß einer Einzelpore",
                 'd4_innere': ValD4_innere,
                 'c4_innere': ValC4_innere,
                 'b4_innere': ValB4_innere,
                 'bemerkung_innere4': " ",
                 'd5_innere': ValD5_innere,
                 'c5_innere': ValC5_innere,
                 'b5_innere': ValB5_innere,
                 'bemerkung_innere5': " ",
                 'd6_innere': ValD6_innere,
                 'c6_innere': ValC6_innere,
                 'b6_innere': ValB6_innere,
                 'bemerkung_innere6': " ",
                 'd7_innere': ValD7_innere,
                 'c7_innere': ValC7_innere,
                 'b7_innere': ValB7_innere,
                 'bemerkung_innere7': " ",
                 'd8_innere': ValD8_innere,
                 'c8_innere': ValC8_innere,
                 'b8_innere': ValB8_innere,
                 'bemerkung_innere8': " ",
                 'd9_innere': ValD9_innere,
                 'c9_innere': ValC9_innere,
                 'b9_innere': ValB9_innere,
                 'bemerkung_innere9': " ",
                 'd10_innere': ValD10_innere,
                 'c10_innere': ValC10_innere,
                 'b10_innere': ValB10_innere,
                 'bemerkung_innere10': " ",
                 'd11_innere': ValD11_innere,
                 'c11_innere': ValC11_innere,
                 'b11_innere': ValB11_innere,
                 'bemerkung_innere11': " ",
                 'd12_innere': ValD12_innere,
                 'c12_innere': ValC12_innere,
                 'b12_innere': ValB12_innere,
                 'bemerkung_innere12': " ",
                 'd13_innere': ValD13_innere,
                 'c13_innere': ValC13_innere,
                 'b13_innere': ValB13_innere,
                 'bemerkung_innere13': " ",
                 'd14_innere': ValD15_innere,
                 'c14_innere': ValC14_innere,
                 'b14_innere': ValB14_innere,
                 'bemerkung_innere14': " ",
                 'd15_innere': ValD15_innere,
                 'c15_innere': ValC15_innere,
                 'b15_innere': ValB15_innere,
                 'bemerkung_innere15': " ",
                 'd16_innere': ValD16_innere,
                 'c16_innere': ValC16_innere,
                 'b16_innere': ValB16_innere,
                 'bemerkung_innere16': " ",
                 'd17_innere': ValD17_innere,
                 'c17_innere': ValC17_innere,
                 'b17_innere': ValB17_innere,
                 'bemerkung_innere17': " ",
                 'd18_innere': ValD18_innere,
                 'c18_innere': ValC18_innere,
                 'b18_innere': ValB18_innere,
                 'bemerkung_innere18': " ",
                 'd19_innere': ValD19_innere,
                 'c19_innere': ValC19_innere,
                 'b19_innere': ValB19_innere,
                 'bemerkung_innere19': " ",
                 'd20_innere': ValD20_innere,
                 'c20_innere': ValC20_innere,
                 'b20_innere': ValB20_innere,
                 'bemerkung_innere20': " ",
                 'd21_innere': ValD21_innere,
                 'c21_innere': ValC21_innere,
                 'b21_innere': ValB21_innere,
                 'result': val,
                 'd1': val1,
                 'c1': val_c1,
                 'b1': val_b1,
                 'd2': val_D2,
                 'c2': val_C2,
                 'b2': val_B2,
                 'd3': val_D3,
                 'c3': val_C3,
                 'b3': val_B3,
                 'bemerkung3': "Größtmaß einer Einzelpore",
                 'd4': val_D4,
                 'c4': val_C4,
                 'b4': val_B4,
                 'bemerkung4': "Höhe des Endkraterlunkers",
                 'd5': val_D5,
                 'c5': val_C5,
                 'b5': val_B5,
                 'bemerkung5': val_Bemerkung5,
                 'd6': val_D6,
                 'c6': val_C6,
                 'b6': val_B6,
                 'd7': val_D7,
                 'c7': val_C7,
                 'b7': val_B7,
                 'bemerkung6':"Mikroskopische Untersuchnung",
                 'bemerkung7':"Für einseitig geschw. Stumpfnähte",
                 'd8': val_D8,
                 'c8': val_C8,
                 'b8': val_B8,
                 'bemerkung8':"Weicher Übergang wird verlangt",
                 'd9': val_D9,
                 'c9': val_C9,
                 'b9': val_B9,
                 'bemerkung9':"Weicher Übergang wird verlangt",
                 'd10': val_D10,
                 'c10': val_C10,
                 'b10': val_B10,
                 'bemerkung10':"Weicher Übergang wird verlangt",
                 'd11': val_D11,
                 'c11': val_C11,
                 'b11': val_B11,
                 'bemerkung11':"Weicher Übergang wird verlangt",
                 'd12': val_D12,
                 'c12': val_C12,
                 'b12': val_B12,
                 'bemerkung12':" ",
                 'd13': val_D13,
                 'c13': val_C13,
                 'b13': val_B13,
                 'bemerkung13':" ",
                 'd14': val_D14,
                 'c14': val_C14,
                 'b14': val_B14,
                 'bemerkung14':"Nahtübergangswinkel >= Grenzwert",
                 'd15': val_D15,
                 'c15': val_C15,
                 'b15': val_B15,
                 'bemerkung15':" ",
                 'd16': val_D16,
                 'c16': val_C16,
                 'b16': val_B16,
                 'bemerkung16':"Weicher Übergang wird verlangt",
                 'd17': val_D17,
                 'c17': val_C17,
                 'b17': val_B17,
                 'bemerkung17':"Weicher Übergang wird verlangt",
                 'd18': val_D18,
                 'c18': val_C18,
                 'b18': val_B18,
                 'bemerkung18':" ",
                 'd19': val_D19,
                 'c19': val_C19,
                 'b19': val_B19,
                 'bemerkung19':" Wenn Unsymmetrie nicht festgelegt",
                 'd20': val_D20,
                 'c20': val_C20,
                 'b20': val_B20,
                 'bemerkung20':"Weicher Übergang wird verlangt",
                 'd21': val_D21,
                 'c21': val_C21,
                 'b21': val_B21,
                 'bemerkung21':"  ",
                 'd22': val_D22,
                 'c22': val_C22,
                 'b22': val_B22,
                 'bemerkung22':"  ",
                 'd23': val_D23,
                 'c23': val_C23,
                 'b23': val_B23,
                 'bemerkung23':"  ",
                 'd24': val_D24,
                 'c24': val_C24,
                 'b24': val_B24,
                 'bemerkung24':" noch ... ",
                 'd25': val_D25,
                 'c25': val_C25,
                 'b25': val_B25,
                 'bemerkung25':"  ",
                 'd26': val_D26,
                 'c26': val_C26,
                 'b26': val_B26,
                 'bemerkung26':"  ",
                 'bemerkung': val_bemerkung,
                    })

    def on_change_Rohrwand_d1(self,rohrwand):
          if(self.rohrwand is not None):
             return "nz"
    def on_change_Rohrwand_c1(self,rohrwand):
          if(self.rohrwand is not None):
             return "nz"
    def on_change_Rohrwand_b1(self,rohrwand):
          if(self.rohrwand is not None):
             return "nz"

    def on_change_Rohrwand_d2(self,rohrwand):
          if(self.rohrwand is not None):
             return "2,2"
    def on_change_Rohrwand_c2(self,rohrwand):
          if(self.rohrwand is not None):
             return "nz"
    def on_change_Rohrwand_b2(self,rohrwand):
          if(self.rohrwand is not None):
             return "nz"
    def on_change_Rohrwand_d3(self,rohrwand):
          if(self.rohrwand is not None):
             return "nz"
    def on_change_Rohrwand_c3(self,rohrwand):
          if(self.rohrwand is not None):
             return "nz"
    def on_change_Rohrwand_b3(self,rohrwand):
          if(self.rohrwand is not None):
             return "nz"
    def on_change_Rohrwand_d4(self,rohrwand):
          if(self.rohrwand is not None):
             return "nz"
    def on_change_Rohrwand_c4(self,rohrwand):
          if(self.rohrwand is not None):
             return "nz"
    def on_change_Rohrwand_b4(self,rohrwand):
          if(self.rohrwand is not None):
             return "nz"

    def on_change_Rohrwand_d5(self,rohrwand):
          if(self.rohrwand is not None):
             return "nz"
    def on_change_Rohrwand_c5(self,rohrwand):
          if(self.rohrwand is not None):
             return "nz"
    def on_change_Rohrwand_b5(self,rohrwand):
          if(self.rohrwand is not None):
             return "nz"
    def on_change_Rohrwand_bemerkung5(self,aliminium):
          if(self.aliminium == True):
             return "Summe der Bindefehler"

    def on_change_Rohrwand_d6(self,rohrwand):
          if(self.rohrwand is not None):
             return "nz"
    def on_change_Rohrwand_c6(self,rohrwand):
          if(self.rohrwand is not None):
             return "nz"
    def on_change_Rohrwand_b6(self,rohrwand):
          if(self.rohrwand is not None):
             return "nz"
    def on_change_Rohrwand_d7(self,rohrwand):
          if(self.rohrwand is not None):
             return "nz"
    def on_change_Rohrwand_c7(self,rohrwand):
          if(self.rohrwand is not None):
             return "nz"
    def on_change_Rohrwand_b7(self,rohrwand):
          if(self.rohrwand is not None):
             return "nz"
    def on_change_Rohrwand_d8(self,rohrwand):
          if(self.rohrwand is not None):
             return "nz"
    def on_change_Rohrwand_c8(self,rohrwand):
          if(self.rohrwand is not None):
             return "nz"
    def on_change_Rohrwand_b8(self,rohrwand):
          if(self.rohrwand is not None):
             return "nz"
#
    def on_change_Rohrwand_d9(self,rohrwand):
          if(self.rohrwand is not None):
             return "nz"
    def on_change_Rohrwand_c9(self,rohrwand):
          if(self.rohrwand is not None):
             return "nz"
    def on_change_Rohrwand_b9(self,rohrwand):
          if(self.rohrwand is not None):
             return "nz"
#
    def on_change_Rohrwand_d10(self,rohrwand):
          if(self.rohrwand is not None):
             return "nz"
    def on_change_Rohrwand_c10(self,rohrwand):
          if(self.rohrwand is not None):
             return "nz"
    def on_change_Rohrwand_b10(self,rohrwand):
          if(self.rohrwand is not None):
             return "nz"
#
    def on_change_Rohrwand_d11(self,rohrwand):
          if(self.rohrwand is not None):
             return "nz"
    def on_change_Rohrwand_c11(self,rohrwand):
          if(self.rohrwand is not None):
             return "nz"
    def on_change_Rohrwand_b11(self,rohrwand):
          if(self.rohrwand is not None):
             return "nz"
#
    def on_change_Rohrwand_d12(self,rohrwand):
          if(self.rohrwand is not None):
             return "nz"
    def on_change_Rohrwand_c12(self,rohrwand):
          if(self.rohrwand is not None):
             return "nz"
    def on_change_Rohrwand_b12(self,rohrwand):
          if(self.rohrwand is not None):
             return "nz"
#
    def on_change_Rohrwand_d13(self,rohrwand):
          if(self.rohrwand is not None):
             return "nz"
    def on_change_Rohrwand_c13(self,rohrwand):
          if(self.rohrwand is not None):
             return "nz"
    def on_change_Rohrwand_b13(self,rohrwand):
          if(self.rohrwand is not None):
             return "nz"
#
    def on_change_Rohrwand_d14(self,rohrwand):
          if(self.rohrwand is not None):
             return "nz"
    def on_change_Rohrwand_c14(self,rohrwand):
          if(self.rohrwand is not None):
             return "nz"
    def on_change_Rohrwand_b14(self,rohrwand):
          if(self.rohrwand is not None):
             return "nz"
#
    def on_change_Rohrwand_d15(self,rohrwand):
          if(self.rohrwand is not None):
             return "nz"
    def on_change_Rohrwand_c15(self,rohrwand):
          if(self.rohrwand is not None):
             return "nz"
    def on_change_Rohrwand_b15(self,rohrwand):
          if(self.rohrwand is not None):
             return "nz"
#
    def on_change_Rohrwand_d16(self,rohrwand):
          if(self.rohrwand is not None):
             return "nz"
    def on_change_Rohrwand_c16(self,rohrwand):
          if(self.rohrwand is not None):
             return "nz"
    def on_change_Rohrwand_b16(self,rohrwand):
          if(self.rohrwand is not None):
             return "nz"
#
    def on_change_Rohrwand_d17(self,rohrwand):
          if(self.rohrwand is not None):
             return "nz"
    def on_change_Rohrwand_c17(self,rohrwand):
          if(self.rohrwand is not None):
             return "nz"
    def on_change_Rohrwand_b17(self,rohrwand):
          if(self.rohrwand is not None):
             return "nz"
#
    def on_change_Rohrwand_d18(self,rohrwand):
          if(self.rohrwand is not None):
             return "nz"
    def on_change_Rohrwand_c18(self,rohrwand):
          if(self.rohrwand is not None):
             return "nz"
    def on_change_Rohrwand_b18(self,rohrwand):
          if(self.rohrwand is not None):
             return "nz"
#
    def on_change_Rohrwand_d19(self,rohrwand):
          if(self.rohrwand is not None):
             return "nz"
    def on_change_Rohrwand_c19(self,rohrwand):
          if(self.rohrwand is not None):
             return "nz"
    def on_change_Rohrwand_b19(self,rohrwand):
          if(self.rohrwand is not None):
             return "nz"
#
    def on_change_Rohrwand_d20(self,rohrwand):
          if(self.rohrwand is not None):
             return "nz"
    def on_change_Rohrwand_c20(self, rohrwand):
          if(self.rohrwand is not None):
             return "nz"
    def on_change_Rohrwand_b20(self, rohrwand):
          if(self.rohrwand is not None):
             return "nz"
#
    def on_change_Rohrwand_d21(self, rohrwand):
          if(self.rohrwand is not None):
             return "nz"
    def on_change_Rohrwand_c21(self, rohrwand):
          if(self.rohrwand is not None):
             return "nz"
    def on_change_Rohrwand_b21(self, rohrwand):
          if(self.rohrwand is not None):
             return "nz"
#

    def on_change_Rohrwand_d22(self, rohrwand):
          if(self.rohrwand is not None):
             return "nz"
    def on_change_Rohrwand_c22(self, rohrwand):
          if(self.rohrwand is not None):
             return "nz"
    def on_change_Rohrwand_b22(self, rohrwand):
          if(self.rohrwand is not None):
             return "nz"
#
    def on_change_Rohrwand_d23(self, rohrwand):
          if(self.rohrwand is not None):
             return "nz"
    def on_change_Rohrwand_c23(self, rohrwand):
          if(self.rohrwand is not None):
             return "nz"
    def on_change_Rohrwand_b23(self, rohrwand):
          if(self.rohrwand is not None):
             return "nz"
#

    def on_change_Rohrwand_d24(self, rohrwand):
          if(self.rohrwand is not None):
             return "nz"
    def on_change_Rohrwand_c24(self, rohrwand):
          if(self.rohrwand is not None):
             return "nz"
    def on_change_Rohrwand_b24(self, rohrwand):
          if(self.rohrwand is not None):
             return "nz"
#
    def on_change_Rohrwand_d25(self, rohrwand):
          if(self.rohrwand is not None):
             return "nz"
    def on_change_Rohrwand_c25(self, rohrwand):
          if(self.rohrwand is not None):
             return "nz"
    def on_change_Rohrwand_b25(self, rohrwand):
          if(self.rohrwand is not None):
             return "nz"
#
    def on_change_Rohrwand_d26(self, rohrwand):
          if(self.rohrwand is not None):
             return "nz"
    def on_change_Rohrwand_c26(self, rohrwand):
          if(self.rohrwand is not None):
             return "nz"
    def on_change_Rohrwand_b26(self, rohrwand):
          if(self.rohrwand is not None):
             return "nz"
#
    def on_change_Rohrwand_d1_innere(self, rohrwand):
          if(self.rohrwand is not None):
             return "nz"
    def on_change_Rohrwand_c1_innere(self, rohrwand):
          if(self.rohrwand is not None):
             return "nz"
    def on_change_Rohrwand_b1_innere(self, rohrwand):
          if(self.rohrwand is not None):
             return "nz"
#
    def on_change_Rohrwand_d2_innere(self, rohrwand):
          if(self.rohrwand is not None):
             return "nz"
    def on_change_Rohrwand_c2_innere(self, rohrwand):
          if(self.rohrwand is not None):
             return "nz"
    def on_change_Rohrwand_b2_innere(self, rohrwand):
          if(self.rohrwand is not None):
             return "nz"
#
    def on_change_Rohrwand_d3_innere(self, rohrwand):
          if(self.rohrwand is not None):
             return "nz"
    def on_change_Rohrwand_c3_innere(self, rohrwand):
          if(self.rohrwand is not None):
             return "nz"
    def on_change_Rohrwand_b3_innere(self, rohrwand):
          if(self.rohrwand is not None):
             return "nz"
#
    def on_change_Rohrwand_d4_innere(self, rohrwand):
          if(self.rohrwand is not None):
             return " "
    def on_change_Rohrwand_c4_innere(self, rohrwand):
          if(self.rohrwand is not None):
             return " "
    def on_change_Rohrwand_b4_innere(self, rohrwand):
          if(self.rohrwand is not None):
             return " "

#
    def on_change_Rohrwand_d5_innere(self, rohrwand):
          if(self.rohrwand is not None):
             return " "
    def on_change_Rohrwand_c5_innere(self, rohrwand):
          if(self.rohrwand is not None):
             return " "
    def on_change_Rohrwand_b5_innere(self, rohrwand):
          if(self.rohrwand is not None):
             return " "
#
    def on_change_Rohrwand_d6_innere(self, rohrwand):
          if(self.rohrwand is not None):
             return "nz"
    def on_change_Rohrwand_c6_innere(self, rohrwand):
          if(self.rohrwand is not None):
             return "nz"
    def on_change_Rohrwand_b6_innere(self, rohrwand):
          if(self.rohrwand is not None):
             return "nz"
#
    def on_change_Rohrwand_d7_innere(self, rohrwand):
          if(self.rohrwand is not None):
             return "nz"
    def on_change_Rohrwand_c7_innere(self, rohrwand):
          if(self.rohrwand is not None):
             return "nz"
    def on_change_Rohrwand_b7_innere(self, rohrwand):
          if(self.rohrwand is not None):
             return "nz"
#
    def on_change_Rohrwand_d8_innere(self, rohrwand):
          if(self.rohrwand is not None):
             return "nz"
    def on_change_Rohrwand_c8_innere(self, rohrwand):
          if(self.rohrwand is not None):
             return "nz"
    def on_change_Rohrwand_b8_innere(self, rohrwand):
          if(self.rohrwand is not None):
             return "nz"
#
    def on_change_Rohrwand_d9_innere(self, rohrwand):
          if(self.rohrwand is not None):
             return "nz"
    def on_change_Rohrwand_c9_innere(self, rohrwand):
          if(self.rohrwand is not None):
             return "nz"
    def on_change_Rohrwand_b9_innere(self, rohrwand):
          if(self.rohrwand is not None):
             return "nz"
#
    def on_change_Rohrwand_d10_innere(self, rohrwand):
          if(self.rohrwand is not None):
             return "nz"
    def on_change_Rohrwand_c10_innere(self, rohrwand):
          if(self.rohrwand is not None):
             return "nz"
    def on_change_Rohrwand_b10_innere(self, rohrwand):
          if(self.rohrwand is not None):
             return "nz"
#
    def on_change_Rohrwand_d11_innere(self, rohrwand):
          if(self.rohrwand is not None):
             return "nz"
    def on_change_Rohrwand_c11_innere(self, rohrwand):
          if(self.rohrwand is not None):
             return "nz"
    def on_change_Rohrwand_b11_innere(self, rohrwand):
          if(self.rohrwand is not None):
             return "nz"
#
    def on_change_Rohrwand_d12_innere(self, rohrwand):
          if(self.rohrwand is not None):
             return "nz"
    def on_change_Rohrwand_c12_innere(self, rohrwand):
          if(self.rohrwand is not None):
             return "nz"
    def on_change_Rohrwand_b12_innere(self, rohrwand):
          if(self.rohrwand is not None):
             return "nz"
#
    def on_change_Rohrwand_d13_innere(self, rohrwand):
          if(self.rohrwand is not None):
             return "nz"
    def on_change_Rohrwand_c13_innere(self, rohrwand):
          if(self.rohrwand is not None):
             return "nz"
    def on_change_Rohrwand_b13_innere(self, rohrwand):
          if(self.rohrwand is not None):
             return "nz"
#
    def on_change_Rohrwand_d14_innere(self, rohrwand):
          if(self.rohrwand is not None):
             return "nz"
    def on_change_Rohrwand_c14_innere(self, rohrwand):
          if(self.rohrwand is not None):
             return "nz"
    def on_change_Rohrwand_b14_innere(self, rohrwand):
          if(self.rohrwand is not None):
             return "nz"
#
    def on_change_Rohrwand_d15_innere(self, rohrwand):
          if(self.rohrwand is not None):
             return "nz"
    def on_change_Rohrwand_c15_innere(self, rohrwand):
          if(self.rohrwand is not None):
             return "nz"
    def on_change_Rohrwand_b15_innere(self, rohrwand):
          if(self.rohrwand is not None):
             return "nz"
#
    def on_change_Rohrwand_d16_innere(self, rohrwand):
          if(self.rohrwand is not None):
             return "nz"
    def on_change_Rohrwand_c16_innere(self, rohrwand):
          if(self.rohrwand is not None):
             return "nz"
    def on_change_Rohrwand_b16_innere(self, rohrwand):
          if(self.rohrwand is not None):
             return "nz"
#
    def on_change_Rohrwand_d17_innere(self, rohrwand):
          if(self.rohrwand is not None):
             return "nz"
    def on_change_Rohrwand_c17_innere(self, rohrwand):
          if(self.rohrwand is not None):
             return "nz"
    def on_change_Rohrwand_b17_innere(self, rohrwand):
          if(self.rohrwand is not None):
             return "nz"
#
    def on_change_Rohrwand_d18_innere(self, rohrwand):
          if(self.rohrwand is not None):
             return "nz"
    def on_change_Rohrwand_c18_innere(self, rohrwand):
          if(self.rohrwand is not None):
             return "nz"
    def on_change_Rohrwand_b18_innere(self, rohrwand):
          if(self.rohrwand is not None):
             return "nz"
#
    def on_change_Rohrwand_d19_innere(self, rohrwand):
          if(self.rohrwand is not None):
             return "nz"
    def on_change_Rohrwand_c19_innere(self, rohrwand):
          if(self.rohrwand is not None):
             return "nz"
    def on_change_Rohrwand_b19_innere(self, rohrwand):
          if(self.rohrwand is not None):
             return "nz"
#
    def on_change_Rohrwand_d20_innere(self, rohrwand):
          if(self.rohrwand is not None):
             return "nz"
    def on_change_Rohrwand_c20_innere(self, rohrwand):
          if(self.rohrwand is not None):
             return "nz"
    def on_change_Rohrwand_b20_innere(self, rohrwand):
          if(self.rohrwand is not None):
             return "nz"
#
    def on_change_Rohrwand_d21_innere(self, rohrwand):
          if(self.rohrwand is not None):
             return "nz"
    def on_change_Rohrwand_c21_innere(self, rohrwand):
          if(self.rohrwand is not None):
             return "nz"
    def on_change_Rohrwand_b21_innere(self, rohrwand):
          if(self.rohrwand is not None):
             return "nz"
#
    def on_change_d1_Unregel(self, rohrwand):
          if(self.rohrwand is not None):
             return "nz"
    def on_change_c1_Unregel(self, rohrwand):
          if(self.rohrwand is not None):
             return "nz"
    def on_change_b1_Unregel(self, rohrwand):
          if(self.rohrwand is not None):
             return "nz"
#
    def on_change_d2_Unregel(self, rohrwand):
          if(self.rohrwand is not None):
             return "nz"
    def on_change_c2_Unregel(self, rohrwand):
          if(self.rohrwand is not None):
             return "nz"
    def on_change_b2_Unregel(self, rohrwand):
          if(self.rohrwand is not None):
             return "nz"
#
    def on_change_d3_Unregel(self, rohrwand):
          if(self.rohrwand is not None):
             return "nz"
    def on_change_c3_Unregel(self, rohrwand):
          if(self.rohrwand is not None):
             return "nz"
    def on_change_b3_Unregel(self, rohrwand):
          if(self.rohrwand is not None):
             return "nz"
#
    def on_change_d4_Unregel(self, rohrwand):
          if(self.rohrwand is not None):
             return "nz"
    def on_change_c4_Unregel(self, rohrwand):
          if(self.rohrwand is not None):
             return "nz"
    def on_change_b4_Unregel(self, rohrwand):
          if(self.rohrwand is not None):
             return "nz"
#
    def on_change_d1_Part4(self, rohrwand):
          if(self.rohrwand is not None):
             return "nz"
    def on_change_c1_Part4(self, rohrwand):
          if(self.rohrwand is not None):
             return "nz"
    def on_change_b1_Part4(self, rohrwand):
          if(self.rohrwand is not None):
             return "nz"
#
    def on_change_d2_Part4(self, rohrwand):
          if(self.rohrwand is not None):
             return "nz"
    def on_change_c2_Part4(self, rohrwand):
          if(self.rohrwand is not None):
             return "nz"
    def on_change_b2_Part4(self, rohrwand):
          if(self.rohrwand is not None):
             return "nz"
#


    def on_change_Rohrwand1(self, rohrwand):
       if(self.rohrwand == "0,5" and self.fw_kehlnaht == True and self.bw_stumpfnaht ==False and self.stahl == True and self.aliminium == False):
         return "0,2 ≤ a ≤ 0,4"
       if(self.rohrwand == "2,0" and self.fw_kehlnaht == True and self.bw_stumpfnaht ==False and self.stahl == True and self.aliminium == False):
         return "1,0 ≤ a ≤ 1,4"
       if(self.rohrwand == "3,0" and self.fw_kehlnaht == True and self.bw_stumpfnaht ==False and self.stahl == True and self.aliminium == False):
         return "1,5 ≤ a ≤ 2,1"
       if(self.rohrwand == "4,0" and self.fw_kehlnaht == True and self.bw_stumpfnaht ==False and self.stahl == True and self.aliminium == False):
         return "2,0 ≤ a ≤ 2,8"
       if(self.rohrwand == "5,0" and self.fw_kehlnaht == True and self.bw_stumpfnaht ==False and self.stahl == True and self.aliminium == False):
         return "2,5 ≤ a ≤ 3,5"
       if(self.rohrwand == "6,0" and self.fw_kehlnaht == True and self.bw_stumpfnaht ==False and self.stahl == True and self.aliminium == False):
         return "3,0 ≤ a ≤ 4,2"
       if(self.rohrwand == "7,0" and self.fw_kehlnaht == True and self.bw_stumpfnaht ==False and self.stahl == True and self.aliminium == False):
         return "3,5 ≤ a ≤ 4,9"
       if(self.rohrwand == "8,0" and self.fw_kehlnaht == True and self.bw_stumpfnaht ==False and self.stahl == True and self.aliminium == False):
         return "4,0 ≤ a ≤ 5,6"
       if(self.rohrwand == "9,0" and self.fw_kehlnaht == True and self.bw_stumpfnaht ==False and self.stahl == True and self.aliminium == False):
         return "4,5 ≤ a ≤ 6,3"
       if(self.rohrwand == "10,0" and self.fw_kehlnaht == True and self.bw_stumpfnaht ==False and self.stahl == True and self.aliminium == False):
         return "5,0 ≤ a ≤ 7,0"
       if(self.rohrwand == "11,0" and self.fw_kehlnaht == True and self.bw_stumpfnaht ==False and self.stahl == True and self.aliminium == False):
         return "5,5 ≤ a ≤ 7,7"
       if(self.rohrwand == "12,0" and self.fw_kehlnaht == True and self.bw_stumpfnaht ==False and self.stahl == True and self.aliminium == False):
         return "6,0 ≤ a ≤ 8,4"
       if(self.rohrwand == "13,0" and self.fw_kehlnaht == True and self.bw_stumpfnaht ==False and self.stahl == True and self.aliminium == False):
         return "6,5 ≤ a ≤ 9,1"
       if(self.rohrwand == "14,0" and self.fw_kehlnaht == True and self.bw_stumpfnaht ==False and self.stahl == True and self.aliminium == False):
         return "7,0 ≤ a ≤ 9,8"
       if(self.rohrwand == "15,0" and self.fw_kehlnaht == True and self.bw_stumpfnaht ==False and self.stahl == True and self.aliminium == False):
         return "7,5 ≤ a ≤ 10,5"
       if(self.rohrwand == "16,0" and self.fw_kehlnaht == True and self.bw_stumpfnaht ==False and self.stahl == True and self.aliminium == False):
         return "8,0 ≤ a ≤ 11,2"
       if(self.rohrwand == "17,0" and self.fw_kehlnaht == True and self.bw_stumpfnaht ==False and self.stahl == True and self.aliminium == False):
         return "8,5 ≤ a ≤ 11,9"
       if(self.rohrwand == "18,0" and self.fw_kehlnaht == True and self.bw_stumpfnaht ==False and self.stahl == True and self.aliminium == False):
         return "9,0 ≤ a ≤ 12,6"
       if(self.rohrwand == "20,0" and self.fw_kehlnaht == True and self.bw_stumpfnaht ==False and self.stahl == True and self.aliminium == False):
         return "10,0 ≤ a ≤ 14,0"
       if(self.rohrwand == "25,0" and self.fw_kehlnaht == True and self.bw_stumpfnaht ==False and self.stahl == True and self.aliminium == False):
         return "12,5 ≤ a ≤ 17,5"
       if(self.rohrwand == "30,0" and self.fw_kehlnaht == True and self.bw_stumpfnaht ==False and self.stahl == True and self.aliminium == False):
         return "15,0 ≤ a ≤ 21,0"
       if(self.rohrwand == "63,0" and self.fw_kehlnaht == True and self.bw_stumpfnaht ==False and self.stahl == True and self.aliminium == False):
         return "31,5 ≤ a ≤ 44,1"
       if(self.rohrwand == "0,5" and self.fw_kehlnaht == True and self.bw_stumpfnaht ==False and self.stahl == False and self.aliminium == True):
         return "0,2 ≤ a ≤ 0,5"
       if(self.rohrwand == "1,0" and self.fw_kehlnaht == True and self.bw_stumpfnaht ==False and self.stahl == False and self.aliminium == True):
         return "0,5 ≤ a ≤ 1,0"
       if(self.rohrwand == "2,0" and self.fw_kehlnaht == True and self.bw_stumpfnaht ==False and self.stahl == False and self.aliminium == True):
         return "1,0 ≤ a ≤ 2,0"
       if(self.rohrwand == "3,0" and self.fw_kehlnaht == True and self.bw_stumpfnaht ==False and self.stahl == False and self.aliminium == True):
         return "1,5 ≤ a ≤ 3,0"
       if(self.rohrwand == "4,0" and self.fw_kehlnaht == True and self.bw_stumpfnaht ==False and self.stahl == False and self.aliminium == True):
         return "2,0 ≤ a ≤ 4,0"
       if(self.rohrwand == "5,0" and self.fw_kehlnaht == True and self.bw_stumpfnaht ==False and self.stahl == False and self.aliminium == True):
         return "2,5 ≤ a ≤ 5,0"
       if(self.rohrwand == "6,0" and self.fw_kehlnaht == True and self.bw_stumpfnaht ==False and self.stahl == False and self.aliminium == True):
         return "a ≤ 3,0"
       if(self.rohrwand == "7,0" and self.fw_kehlnaht == True and self.bw_stumpfnaht ==False and self.stahl == False and self.aliminium == True):
         return "a ≤ 3,5"
       if(self.rohrwand == "8,0" and self.fw_kehlnaht == True and self.bw_stumpfnaht ==False and self.stahl == False and self.aliminium == True):
         return "a ≤ 4,0"
       if(self.rohrwand == "9,0" and self.fw_kehlnaht == True and self.bw_stumpfnaht ==False and self.stahl == False and self.aliminium == True):
         return "a ≤ 4,5"
       if(self.rohrwand == "10,0" and self.fw_kehlnaht == True and self.bw_stumpfnaht ==False and self.stahl == False and self.aliminium == True):
         return "a ≤ 5,0"
       if(self.rohrwand == "11,0" and self.fw_kehlnaht == True and self.bw_stumpfnaht ==False and self.stahl == False and self.aliminium == True):
         return "a ≤ 5,5"
       if(self.rohrwand == "12,0" and self.fw_kehlnaht == True and self.bw_stumpfnaht ==False and self.stahl == False and self.aliminium == True):
         return "a ≤ 6,0"
       if(self.rohrwand == "13,0" and self.fw_kehlnaht == True and self.bw_stumpfnaht ==False and self.stahl == False and self.aliminium == True):
         return "a ≤ 6,5"
       if(self.rohrwand == "14,0" and self.fw_kehlnaht == True and self.bw_stumpfnaht ==False and self.stahl == False and self.aliminium == True):
         return "a ≤ 7,0"
       if(self.rohrwand == "15,0" and self.fw_kehlnaht == True and self.bw_stumpfnaht ==False and self.stahl == False and self.aliminium == True):
         return "a ≤ 7,5"
       if(self.rohrwand == "16,0" and self.fw_kehlnaht == True and self.bw_stumpfnaht ==False and self.stahl == False and self.aliminium == True):
         return "a ≤ 8,0"
       if(self.rohrwand == "17,0" and self.fw_kehlnaht == True and self.bw_stumpfnaht ==False and self.stahl == False and self.aliminium == True):
         return "a ≤ 8,5"
       if(self.rohrwand == "18,0" and self.fw_kehlnaht == True and self.bw_stumpfnaht ==False and self.stahl == False and self.aliminium == True):
         return "a ≤ 9,0"
       if(self.rohrwand == "20,0" and self.fw_kehlnaht == True and self.bw_stumpfnaht ==False and self.stahl == False and self.aliminium == True):
         return "a ≤ 10,0"
       if(self.rohrwand == "25,0" and self.fw_kehlnaht == True and self.bw_stumpfnaht ==False and self.stahl == False and self.aliminium == True):
         return "a ≤ 12,5"
       if(self.rohrwand == "30,0" and self.fw_kehlnaht == True and self.bw_stumpfnaht ==False and self.stahl == False and self.aliminium == True):
         return "a ≤ 15,0"
       if(self.rohrwand == "63,0" and self.fw_kehlnaht == True and self.bw_stumpfnaht ==False and self.stahl == False and self.aliminium == True):
         return "a ≤ 31,5"

       else:
         if(self.rohrwand == "1,0" and self.fw_kehlnaht == True and self.bw_stumpfnaht ==False and self.stahl == True and self.aliminium == False):
           return "0,5 ≤ a ≤ 0,7"


    @fields.depends('breite_wurzelüberhöhung', 'fw_kehlnaht','rohrwand','bw_stumpfnaht')
    def on_change_Rohrwand3(self):
        tab=[]
        if((self.rohrwand == "0,5" or self.rohrwand == "1,0" or self.rohrwand == "2,0" or self.rohrwand == "3,0") and self.fw_kehlnaht == False and self.bw_stumpfnaht ==True):
          tab.append(('1', '1'))
          return tab
        if((self.rohrwand == "4,0" or self.rohrwand == "5,0" or self.rohrwand == "6,0") and self.fw_kehlnaht == False and self.bw_stumpfnaht ==True):
          tab.append(('2', '2'))
          return tab
        if((self.rohrwand == "7,0" or self.rohrwand == "8,0") and self.fw_kehlnaht == False and self.bw_stumpfnaht ==True):
          tab.append(('3', '3'))
          return tab
        if((self.rohrwand == "9,0" or self.rohrwand == "10,0" or self.rohrwand == "11,0") and self.fw_kehlnaht == False and self.bw_stumpfnaht ==True):
          tab.append(('4', '4'))
          return tab
        if((self.rohrwand == "12,0" or self.rohrwand == "13,0") and self.fw_kehlnaht == False and self.bw_stumpfnaht ==True):
          tab.append(('5', '5'))
          return tab
        if((self.rohrwand == "14,0" or self.rohrwand == "15,0" or self.rohrwand == "16,0") and self.fw_kehlnaht == False and self.bw_stumpfnaht ==True):
          tab.append(('6', '6'))
          return tab
        if((self.rohrwand == "17,0" or self.rohrwand == "18,0") and self.fw_kehlnaht == False and self.bw_stumpfnaht ==True):
          tab.append(('7', '7'))
          return tab
        if((self.rohrwand == "20,0") and self.fw_kehlnaht == False and self.bw_stumpfnaht ==True):
          tab.append(('8', '8'))
          return tab
        if((self.rohrwand == "25,0") and self.fw_kehlnaht == False and self.bw_stumpfnaht ==True):
          tab.append(('10', '10'))
          return tab
        if((self.rohrwand == "30,0") and self.fw_kehlnaht == False and self.bw_stumpfnaht ==True):
          tab.append(('12', '12'))
          return tab
        if((self.rohrwand == "63,0") and self.fw_kehlnaht == False and self.bw_stumpfnaht ==True):
          tab.append(('25', '25'))
          return tab
        if(self.fw_kehlnaht == True and self.bw_stumpfnaht ==False):
          tab.append(('0', '0'))        
          tab.append(('1,0', '1'))
          tab.append(('1,5', '1.5'))
          tab.append(('2,0', '2'))
          tab.append(('2,5', '2.5'))
          tab.append(('3,0', '3'))
          tab.append(('3,5', '3.5'))
          tab.append(('4,0', '4'))
          tab.append(('4,5', '4.5'))
          tab.append(('5,0', '5'))
          tab.append(('5,5', '5.5'))
          tab.append(('6,0', '6'))
          tab.append(('6,5', '6.5'))
          tab.append(('7,0', '7'))
          tab.append(('8,0', '8'))
          return tab

    @fields.depends('nennmaß_stumpfnahtdicke', 'fw_kehlnaht','rohrwand','bw_stumpfnaht')
    def on_change_Rohrwand2(self):
        tab=[]
        if(self.rohrwand == "0,5" and self.fw_kehlnaht == False and self.bw_stumpfnaht ==True):
          tab.append(('0,5', '0.5'))
          return tab
        if(self.rohrwand == "1,0" and self.fw_kehlnaht == False and self.bw_stumpfnaht ==True):
          tab.append(('1,0', '1'))
          return  tab
        if(self.rohrwand == "2,0" and self.fw_kehlnaht == False and self.bw_stumpfnaht ==True):
          tab.append(('2,0', '2'))
          return tab
        if(self.rohrwand == "3,0" and self.fw_kehlnaht == False and self.bw_stumpfnaht ==True):
          tab.append(('3,0', '3'))
          return tab
        if(self.rohrwand == "4,0" and self.fw_kehlnaht == False and self.bw_stumpfnaht ==True):
          tab.append(('4,0', '4'))
          return tab
        if(self.rohrwand == "5,0" and self.fw_kehlnaht == False and self.bw_stumpfnaht ==True):
          tab.append(('5,0', '5'))
          return tab
        if(self.rohrwand == "6,0" and self.fw_kehlnaht == False and self.bw_stumpfnaht ==True):
          tab.append(('6,0', '6'))
          return tab
        if(self.rohrwand == "7,0" and self.fw_kehlnaht == False and self.bw_stumpfnaht ==True):
          tab.append(('7,0', '7'))
          return tab
        if(self.rohrwand == "8,0" and self.fw_kehlnaht == False and self.bw_stumpfnaht ==True):
          tab.append(('8,0', '8'))
          return tab
        if(self.rohrwand == "9,0" and self.fw_kehlnaht == False and self.bw_stumpfnaht ==True):
          tab.append(('9,0', '9'))
          return tab
        if(self.rohrwand == "10,0" and self.fw_kehlnaht == False and self.bw_stumpfnaht ==True):
          tab.append(('10,0', '10'))
          return tab
        if(self.rohrwand == "11,0" and self.fw_kehlnaht == False and self.bw_stumpfnaht ==True):
          tab.append(('11,0', '11'))
          return tab
        if(self.rohrwand == "12,0" and self.fw_kehlnaht == False and self.bw_stumpfnaht ==True):
          tab.append(('12,0', '12'))
          return tab
        if(self.rohrwand == "13,0" and self.fw_kehlnaht == False and self.bw_stumpfnaht ==True):
          tab.append(('13,0', '13'))
          return tab
        if(self.rohrwand == "14,0" and self.fw_kehlnaht == False and self.bw_stumpfnaht ==True):
          tab.append(('14,0', '14'))
          return tab
        if(self.rohrwand == "15,0" and self.fw_kehlnaht == False and self.bw_stumpfnaht ==True):
          tab.append(('15,0', '15'))
          return tab
        if(self.rohrwand == "16,0" and self.fw_kehlnaht == False and self.bw_stumpfnaht ==True):
          tab.append(('16,0', '16'))
          return tab
        if(self.rohrwand == "17,0" and self.fw_kehlnaht == False and self.bw_stumpfnaht ==True):
          tab.append(('17,0', '17'))
          return tab
        if(self.rohrwand == "18,0" and self.fw_kehlnaht == False and self.bw_stumpfnaht ==True):
          tab.append(('18,0', '18'))
          return tab
        if(self.rohrwand == "20,0" and self.fw_kehlnaht == False and self.bw_stumpfnaht ==True):
          tab.append(('20,0', '20'))
          return tab
        if(self.rohrwand == "25,0" and self.fw_kehlnaht == False and self.bw_stumpfnaht ==True):
          tab.append(('25,0', '25'))
          return tab
        if(self.rohrwand == "30,0" and self.fw_kehlnaht == False and self.bw_stumpfnaht ==True):
          tab.append(('30,0', '30'))
          return tab
        if(self.rohrwand == "63,0" and self.fw_kehlnaht == False and self.bw_stumpfnaht ==True):
          tab.append(('63,0', '63'))
          return tab
        if(self.fw_kehlnaht == True and self.bw_stumpfnaht ==False):
          tab.append(('0', '0'))        
          tab.append(('0,5', '0.5'))
          tab.append(('1,0', '1'))
          tab.append(('2,0', '2'))
          tab.append(('3,0', '3'))
          tab.append(('4,0', '4'))
          tab.append(('5,0', '5'))
          tab.append(('6,0', '6'))
          tab.append(('7,0', '7'))
          tab.append(('8,0', '8'))
          tab.append(('9,0', '9'))
          tab.append(('10,0', '10'))
          tab.append(('11,0', '11'))
          tab.append(('12,0', '12'))
          tab.append(('13,0', '13'))
          tab.append(('14,0', '14'))
          tab.append(('15,0', '15'))
          tab.append(('16,0', '16'))
          tab.append(('17,0', '17'))
          tab.append(('18,0', '18'))
          tab.append(('20,0', '20'))
          tab.append(('25,0', '25'))
          tab.append(('30,0', '30'))
          tab.append(('63,0', '63'))
          return tab


    @fields.depends('breite_nahtüberhöhung', 'fw_kehlnaht','rohrwand','bw_stumpfnaht')
    def on_change_fw_kehlnahtt_2(self):
        tab=[]
        if(self.rohrwand == "0,5" and self.fw_kehlnaht == True and self.bw_stumpfnaht ==False):
          tab.append(('0,5', '0.5'))
          return tab
        if(self.rohrwand == "1,0" and self.fw_kehlnaht == True and self.bw_stumpfnaht ==False):
          tab.append(('1,0', '1'))
          return  tab
        if(self.rohrwand == "2,0" and self.fw_kehlnaht == True and self.bw_stumpfnaht ==False):
          tab.append(('2,0', '2'))
          return tab
        if(self.rohrwand == "3,0" and self.fw_kehlnaht == True and self.bw_stumpfnaht ==False):
          tab.append(('3,0', '3'))
          return tab
        if(self.rohrwand == "4,0" and self.fw_kehlnaht == True and self.bw_stumpfnaht ==False):
          tab.append(('4,0', '4'))
          return tab
        if(self.rohrwand == "5,0" and self.fw_kehlnaht == True and self.bw_stumpfnaht ==False):
          tab.append(('5,0', '5'))
          return tab
        if(self.rohrwand == "6,0" and self.fw_kehlnaht == True and self.bw_stumpfnaht ==False):
          tab.append(('6,0', '6'))
          return tab
        if(self.rohrwand == "7,0" and self.fw_kehlnaht == True and self.bw_stumpfnaht ==False):
          tab.append(('7,0', '7'))
          return tab
        if(self.rohrwand == "8,0" and self.fw_kehlnaht == True and self.bw_stumpfnaht ==False):
          tab.append(('8,0', '8'))
          return tab
        if(self.rohrwand == "9,0" and self.fw_kehlnaht == True and self.bw_stumpfnaht ==False):
          tab.append(('9,0', '9'))
          return tab
        if(self.rohrwand == "10,0" and self.fw_kehlnaht == True and self.bw_stumpfnaht ==False):
          tab.append(('10,0', '10'))
          return tab
        if(self.rohrwand == "11,0" and self.fw_kehlnaht == True and self.bw_stumpfnaht ==False):
          tab.append(('11,0', '11'))
          return tab
        if(self.rohrwand == "12,0" and self.fw_kehlnaht == True and self.bw_stumpfnaht ==False):
          tab.append(('12,0', '12'))
          return tab
        if(self.rohrwand == "13,0" and self.fw_kehlnaht == True and self.bw_stumpfnaht ==False):
          tab.append(('13,0', '13'))
          return tab
        if(self.rohrwand == "14,0" and self.fw_kehlnaht == True and self.bw_stumpfnaht ==False):
          tab.append(('14,0', '14'))
          return tab
        if(self.rohrwand == "15,0" and self.fw_kehlnaht == True and self.bw_stumpfnaht ==False):
          tab.append(('15,0', '15'))
          return tab
        if(self.rohrwand == "16,0" and self.fw_kehlnaht == True and self.bw_stumpfnaht ==False):
          tab.append(('16,0', '16'))
          return tab
        if(self.rohrwand == "17,0" and self.fw_kehlnaht == True and self.bw_stumpfnaht ==False):
          tab.append(('17,0', '17'))
          return tab
        if(self.rohrwand == "18,0" and self.fw_kehlnaht == True and self.bw_stumpfnaht ==False):
          tab.append(('18,0', '18'))
          return tab
        if(self.rohrwand == "20,0" and self.fw_kehlnaht == True and self.bw_stumpfnaht ==False):
          tab.append(('20,0', '20'))
          return tab
        if(self.rohrwand == "25,0" and self.fw_kehlnaht == True and self.bw_stumpfnaht ==False):
          tab.append(('25,0', '25'))
          return tab
        if(self.rohrwand == "30,0" and self.fw_kehlnaht == True and self.bw_stumpfnaht ==False):
          tab.append(('30,0', '30'))
          return tab
        if(self.rohrwand == "63,0" and self.fw_kehlnaht == True and self.bw_stumpfnaht ==False):
          tab.append(('63,0', '63'))
          return tab
###Quand stumpfnaht est selectionne
        if((self.rohrwand == "0,5" or self.rohrwand == "1,0" or  self.rohrwand == "2,0" or  self.rohrwand == "3,0") and self.fw_kehlnaht == False and self.bw_stumpfnaht ==True):
          tab.append(('4', '4'))
          return tab
        if(self.rohrwand == "4,0" and self.fw_kehlnaht == False and self.bw_stumpfnaht ==True):
          tab.append(('6', '6'))
          return  tab
        if(self.rohrwand == "5,0" and self.fw_kehlnaht == False and self.bw_stumpfnaht ==True):
          tab.append(('7', '7'))
          return tab
        if(self.rohrwand == "6,0" and self.fw_kehlnaht == False and self.bw_stumpfnaht ==True):
          tab.append(('8', '8'))
          return tab
        if(self.rohrwand == "7,0" and self.fw_kehlnaht == False and self.bw_stumpfnaht ==True):
          tab.append(('10', '10'))
          return tab
        if(self.rohrwand == "8,0" and self.fw_kehlnaht == False and self.bw_stumpfnaht ==True):
          tab.append(('11', '11'))
          return tab
        if(self.rohrwand == "9,0" and self.fw_kehlnaht == False and self.bw_stumpfnaht ==True):
          tab.append(('13', '13'))
          return tab
        if(self.rohrwand == "10,0" and self.fw_kehlnaht == False and self.bw_stumpfnaht ==True):
          tab.append(('14', '14'))
          return  tab
        if(self.rohrwand == "11,0" and self.fw_kehlnaht == False and self.bw_stumpfnaht ==True):
          tab.append(('15', '15'))
          return tab
        if(self.rohrwand == "12,0" and self.fw_kehlnaht == False and self.bw_stumpfnaht ==True):
          tab.append(('17', '17'))
          return tab
        if(self.rohrwand == "13,0" and self.fw_kehlnaht == False and self.bw_stumpfnaht ==True):
          tab.append(('18', '18'))
          return tab
        if(self.rohrwand == "14,0" and self.fw_kehlnaht == False and self.bw_stumpfnaht ==True):
          tab.append(('20', '20'))
          return tab
        if(self.rohrwand == "15,0" and self.fw_kehlnaht == False and self.bw_stumpfnaht ==True):
          tab.append(('21', '21'))
          return tab
        if(self.rohrwand == "16,0" and self.fw_kehlnaht == False and self.bw_stumpfnaht ==True):
          tab.append(('22', '22'))
          return  tab
        if(self.rohrwand == "17,0" and self.fw_kehlnaht == False and self.bw_stumpfnaht ==True):
          tab.append(('24', '24'))
          return tab
        if(self.rohrwand == "18,0" and self.fw_kehlnaht == False and self.bw_stumpfnaht ==True):
          tab.append(('25', '25'))
          return tab
        if(self.rohrwand == "20,0" and self.fw_kehlnaht == False and self.bw_stumpfnaht ==True):
          tab.append(('28', '28'))
          return tab
        if(self.rohrwand == "25,0" and self.fw_kehlnaht == False and self.bw_stumpfnaht ==True):
          tab.append(('35', '35'))
          return tab
        if(self.rohrwand == "30,0" and self.fw_kehlnaht == False and self.bw_stumpfnaht ==True):
          tab.append(('42', '42'))
          return tab
        if(self.rohrwand == "63,0" and self.fw_kehlnaht == False and self.bw_stumpfnaht ==True):
          tab.append(('88', '88'))
          return tab

    @fields.depends('nenmaß_kehlnahtdicke', 'fw_kehlnaht','rohrwand','bw_stumpfnaht')
    def on_change_fw_kehlnaht_1(self):
        tab = [(None, '')]
        if(self.rohrwand == "0,5" and self.fw_kehlnaht == True and self.bw_stumpfnaht ==False):
          tab.append(('0,2', '0.2'))
          return tab
        if(self.rohrwand == "1,0" and self.fw_kehlnaht == True and self.bw_stumpfnaht ==False):
          tab.append(('0,5', '0.5'))
          return  tab
        if(self.rohrwand == "2,0" and self.fw_kehlnaht == True and self.bw_stumpfnaht ==False):
          tab.append(('1,0', '1'))
          return tab
        if(self.rohrwand == "3,0" and self.fw_kehlnaht == True and self.bw_stumpfnaht ==False):
          tab.append(('1,5', '1.5'))
          return tab
        if(self.rohrwand == "4,0" and self.fw_kehlnaht == True and self.bw_stumpfnaht ==False):
          tab.append(('2,0', '2'))
          return tab
        if(self.rohrwand == "5,0" and self.fw_kehlnaht == True and self.bw_stumpfnaht ==False):
          tab.append(('2,5', '2.5'))
          return tab
        if(self.rohrwand == "6,0" and self.fw_kehlnaht == True and self.bw_stumpfnaht ==False):
          tab.append(('3,0', '3'))
          return tab
        if(self.rohrwand == "7,0" and self.fw_kehlnaht == True and self.bw_stumpfnaht ==False):
          tab.append(('3,5', '3.5'))
          return tab
        if(self.rohrwand == "8,0" and self.fw_kehlnaht == True and self.bw_stumpfnaht ==False):
          tab.append(('4,0', '4'))
          return tab
        if(self.rohrwand == "9,0" and self.fw_kehlnaht == True and self.bw_stumpfnaht ==False):
          tab.append(('4,5', '4.5'))
          return tab
        if(self.rohrwand == "10,0" and self.fw_kehlnaht == True and self.bw_stumpfnaht ==False):
          tab.append(('5,0', '5'))
          return tab
        if(self.rohrwand == "11,0" and self.fw_kehlnaht == True and self.bw_stumpfnaht ==False):
          tab.append(('5,5', '5.5'))
          return tab
        if(self.rohrwand == "12,0" and self.fw_kehlnaht == True and self.bw_stumpfnaht ==False):
          tab.append(('6,0', '6'))
          return tab
        if(self.rohrwand == "13,0" and self.fw_kehlnaht == True and self.bw_stumpfnaht ==False):
          tab.append(('6,5', '6.5'))
          return tab
        if(self.rohrwand == "14,0" and self.fw_kehlnaht == True and self.bw_stumpfnaht ==False):
          tab.append(('7,0', '7'))
          return tab
        if(self.rohrwand == "15,0" and self.fw_kehlnaht == True and self.bw_stumpfnaht ==False):
          tab.append(('7,5', '7.5'))
          return tab
        if(self.rohrwand == "16,0" and self.fw_kehlnaht == True and self.bw_stumpfnaht ==False):
          tab.append(('8,0', '8'))
          return tab
        if(self.rohrwand == "17,0" and self.fw_kehlnaht == True and self.bw_stumpfnaht ==False):
          tab.append(('8,5', '8.5'))
          return tab
        if(self.rohrwand == "18,0" and self.fw_kehlnaht == True and self.bw_stumpfnaht ==False):
          tab.append(('9,0', '9'))
          return tab
        if(self.rohrwand == "20,0" and self.fw_kehlnaht == True and self.bw_stumpfnaht ==False):
          tab.append(('10,0', '10'))
          return tab
        if(self.rohrwand == "25,0" and self.fw_kehlnaht == True and self.bw_stumpfnaht ==False):
          tab.append(('12,5', '12.5'))
          return tab
        if(self.rohrwand == "30,0" and self.fw_kehlnaht == True and self.bw_stumpfnaht ==False):
          tab.append(('15,0', '15'))
          return tab
        if(self.rohrwand == "63,0" and self.fw_kehlnaht == True and self.bw_stumpfnaht ==False):
          tab.append(('31,5', '31.5'))
          return tab
        else:
          tab.append(("None", " "))
          return tab

    def On_change_fw_kehlnaht(self,fw_kehlnaht):
          if(self.fw_kehlnaht == True):
             return "a < 9,0"
          else:
             return "1<a<18"

    def On_change_aliminium(self,aliminium):
        if(self.aliminium == True and self.stahl == False):
          return "in EN ISO 9606-2:  *2) wird C angewendet, sonst B"
        else:
          if(self.aliminium == False and self.stahl == True):
              return "in EN ISO 9606-1, EN 287-1:  *2) wird C angewendet, sonst B  *3) in EN 287-1 wird C angewendet"

    def get_rec_name(self,Nenma2):
        val1 = "EN ISO 5817 / EN ISO 10042"
        return val1

    @classmethod
    @ModelView.button_action('welding_certification.report_bewertung_iso5817')
    def print(cls, bewertungsiso5817):
        pass
   
    @classmethod
    @ModelView.button
    @Workflow.transition('canceled')
    def cancel(cls, bewertungsiso5817):
        pass

    @classmethod
    @ModelView.button
    @Workflow.transition('draft')
    def draft(cls, bewertungsiso5817):
        pass

    @classmethod
    @ModelView.button
    @Workflow.transition('confirmed')
    def confirm(cls, bewertungsiso5817):
        pass


    @classmethod
    def delete(cls, bewertungsiso5817):
        for iso5817 in bewertungsiso5817:
            if iso5817.state != 'draft':
                raise AccessError(gettext('welding_certification.delete_bewertung_iso_5817_non_draft',
                    ws=iso5817.rec_name))
        super(BewertungIso5817, cls).delete(bewertungsiso5817)

       
class BewertungSichtprüfungDecklage(sequence_ordered(), ModelSQL, ModelView):
    'Bewertung Test'
    __name__ = 'bewertung.bewertung.sichtprüfung_decklage'
    bewertung = fields.Many2One('bewertung.bewertung','Bewertung',
        'Bewertungsbogen für Prüfungen nach EN ISO 96061-1/ EN 287-1 (stähle),EN ISO 9606-2 (Alu)',
         ondelete='CASCADE', select=True)
    bezeichnung = fields.Many2One('welding.iso96061', 'Schweißer Prüfungsbescheinigung', ondelete='CASCADE',
        select=True)
    prob_nr = fields.Integer("Probe.Nr")
    nahtbreite = fields.Selection([
        ('1,0', '1'),
        ('2,0', '2'),
        ('3,0', '3'),
        ('4,0', '4'),
        ('6,0', '6'),
        ('8,0', '8'),
        ('10,0', '10'),
        ('12,0', '12'),
        ('14,0', '14'),
        ('16,0', '16'),
        ('18,0', '18'),
        ('20,0', '20'),
        ('22,0', '22'),
        ('24,0', '24'),
        ('26,0', '26'),
        ('28,0', '28'),
        ('30,0', '30'),
        ('32,0', '32'),
        ('34,0', '34'),
        ('36,0', '36'),
        ('38,0', '38'),
        ('40,0', '40'),
        ('42,0', '42'),
        ('50,0', '50'),
        ], 'Nahtbreite b(mm)')
    grenzwert_502 = fields.Float("502 Nahtüberhohung(mm): Grenzwert")
    istwert_502 = fields.Float("502 Nahtüberhohung(mm): Istwert")
    grenzwert_511 = fields.Float("511 Decklagen unterwölbung: Grenzwert")
    istwert_511 = fields.Char("511 Decklagen unterwölbung: Istwert")
    anzätze = fields.Char("Anzätze/Gleich mäßigkeit")
    nahtüber = fields.Char("Nahtüber gänge/Einbrandkerben")
    bewertung1 = fields.Char("Bewertung *1)")
    wurzelbreite = fields.Selection([
        ('0', '0'),
        ('1,0', '1'),
        ('1,5', '1.5'),
        ('2,0', '2'),
        ('2,5', '2.5'),
        ('3,0', '3'),
        ('3,5', '3.5'),
        ('4,0', '4'),
        ('4,5', '4.5'),
        ('5,0', '5'),
        ('5,5', '5.5'),
        ('6,0', '6'),
        ('6,5', '6.5'),
        ('7,0', '7'),
        ('7,5', '7.5'),
        ('8,0', '8'),
        ], 'Wurzelbreite b(mm)')
    grenzwert_504 = fields.Float("504 Wurzelüber höhung(mm): Grenzwert")
    istwert_504 = fields.Char("504 Wurzelüber höhung(mm): Istwert")
    wurzel_ausbildung = fields.Char("Wurzel ausbildung")
    bewertung2 = fields.Char("Bewertung *1)")
    position = fields.Function(fields.Char("Schw.Position"),'on_change_with_position')
    
    @classmethod
    def __register__(cls, module_name):
        super(BewertungSichtprüfungDecklage, cls).__register__(module_name)

        table = cls.__table_handler__(module_name)
        
    @fields.depends('bezeichnung')
    def on_change_with_position(self,name=None):
    
        if self.bezeichnung and self.bezeichnung.schweisspos:
            return self.bezeichnung.schweisspos.code
        else:
            return ''   
         
class BewertungSichtprüfungKehlnaht(sequence_ordered(), ModelSQL, ModelView):
    'Bewertung Sichtprüfung Kehlnaht'
    __name__ = 'bewertung.bewertung.sichtprüfung_kehlnaht'
    bewertung = fields.Many2One('bewertung.bewertung','Bewertung',
        'Bewertungsbogen für Prüfungen nach EN ISO 96061-1/ EN 287-1 (stähle),EN ISO 9606-2 (Alu)', ondelete='CASCADE')
    bezeichnung = fields.Many2One('welding.iso96061', 'Schweißer Prüfungsbescheinigung',
        ondelete='CASCADE', select=True)        
    prob_nr = fields.Integer("Probe.Nr")
    sollmass = fields.Selection([
        ('3,0', '3'),
        ('4,0', '4'),
        ('5,0', '5'),
        ('6,0', '6'),
        ('7,0', '7'),
        ('8,0', '8'),
        ('9,0', '9'),
        ('10,0', '10'),
        ('11,0', '11'),
        ('12,0', '12'),
        ('13,0', '13'),
        ('14,0', '14'),
        ('15,0', '15'),
        ('16,0', '16'),
        ('17,0', '17'),
        ('18,0', '18'),
        ('40,0', '40'),
        ], 'Sollmaß der Kehlnahtdicke a(mm) ')
    kehlnahtdicke_grenzwerte = fields.Char("5213-5214 Kehlnahtdicke a(mm): Grenzwerte")
    kehlnahtdicke_istwert = fields.Char("5213-5214 Kehlnahtdicke a(mm): Istwert")
    schenkligkeit_grenzwerte = fields.Float("512 Ungleich Schenkligkeit(mm): Grenzwert")
    schenkligkeit_grenzwerte_istwert = fields.Char("512 Ungleich Schenkligkeit(mm): Istwert")
    anzätze = fields.Char("Ansätze/Gleich mäßigkeit")
    nahtüber = fields.Char("Nahtüber gänge/Einbrandkerben")
    bewertung1 = fields.Char("Bewertung *1)")
    position = fields.Function(fields.Char("Schw.Position"),'on_change_with_position')
    
    @fields.depends('bezeichnung')
    def on_change_with_position(self,name=None):
    
        if self.bezeichnung and self.bezeichnung.schweisspos:
            return self.bezeichnung.schweisspos.code
        else:
            return '' 
               
class BewertungDurchstrahlungsprüfung(sequence_ordered(), ModelSQL, ModelView):
    'Bewertung Durchstrahlungsprüfung'
    __name__ = 'bewertung.bewertung.durchstrahlungsprüfung'
    bewertung = fields.Many2One('bewertung.bewertung','Bewertung',
        'Bewertungsbogen für Prüfungen nach EN ISO 96061-1/ EN 287-1 (stähle),EN ISO 9606-2 (Alu)', ondelete='CASCADE')
    bezeichnung = fields.Many2One('welding.iso96061', 'Schweißer Prüfungsbescheinigung',
        ondelete='CASCADE', select=True)         
    bewertung1 = fields.Char("Bewertung *1)")
    prob_nr = fields.Integer("Probe.Nr")
    film_nr = fields.Char("Film-Nr")
    bildgüte = fields.Char("Bildgüte zahl")
    befund_100e = fields.Char("Befund 100E")
    befund_2011 = fields.Char("Befund 2011 Aa")
    befund_2013 = fields.Char("Befund 2013 Ac")
    befund_2016 = fields.Char("Befund 2016 Ab")
    befund_300 = fields.Char("Befund 300 Bb")
    befund_401c = fields.Char("Befund 401 C")
    befund_402d = fields.Char("Befund 402 D")
    befund_5011f = fields.Char("Befund 5011 F")
    befund_5013f = fields.Char("Befund 5013 F(D)")
    befund_507h = fields.Char("Befund 507 H")
    ohne_befund = fields.Char("Ohne Befund")
    schweissposition = fields.Function(fields.Char("Schw.Position"),'on_change_with_schweissposition')
    
    @fields.depends('bezeichnung')
    def on_change_with_schweissposition(self,name=None):
    
        if self.bezeichnung and self.bezeichnung.schweisspos:
            return self.bezeichnung.schweisspos.code
        else:
            return ''


class BewertungBruchprüfung(sequence_ordered(), ModelSQL, ModelView):
    'Bewertung Bruchprüfung'
    __name__ = 'bewertung.bewertung.bruchprüfung'
    bewertung = fields.Many2One('bewertung.bewertung','Bewertung',
        'Bewertungsbogen für Prüfungen nach EN ISO 96061-1/ EN 287-1 (stähle),EN ISO 9606-2 (Alu)', ondelete='CASCADE')
    bezeichnung = fields.Many2One('welding.iso96061', 'Schweißer Prüfungsbescheinigung',
        ondelete='CASCADE', select=True)           
    prob_nr = fields.Integer("Probe.Nr")
    bw_fw = fields.Char("BW/FW")
    schw_position = fields.Function(fields.Char("Schw.Position"),'on_change_with_schweissposition')
    biegerichtung = fields.Char("Biegerichtung *3)")
    bruchlage = fields.Char("Bruchlage")
    befund_100e = fields.Char("Befund - Art der Unregelmäßigkeit*2) 100 E")
    befund_2011 = fields.Char("Befund - Art der Unregelmäßigkeit*2) 2011 Aa")
    befund_2013 = fields.Char("Befund - Art der Unregelmäßigkeit*2) 2013 Ac")
    befund_2016 = fields.Char("Befund - Art der Unregelmäßigkeit*2) 2016 Ab")
    befund_300 = fields.Char("Befund - Art der Unregelmäßigkeit*2) 300 Ba")
    befund_401 = fields.Char("Befund - Art der Unregelmäßigkeit*2) 401 C")
    befund_402 = fields.Char("Befund - Art der Unregelmäßigkeit*2) 402 D")
    ohne_befund = fields.Char("Ohne Befund")
    bewertung1 = fields.Char("Bewertung *1)")
    
    @fields.depends('bezeichnung')
    def on_change_with_schweissposition(self,name=None):
    
        if self.bezeichnung and self.bezeichnung.schweisspos:
            return self.bezeichnung.schweisspos.code
        else:
            return ''
class BewertungBiegeprüfung(sequence_ordered(), ModelSQL, ModelView):
    'Bewertung Biegeprüfung '
    __name__ = 'bewertung.bewertung.biegeprüfung'
    bewertung = fields.Many2One('bewertung.bewertung','Bewertung',
        'Bewertungsbogen für Prüfungen nach EN ISO 96061-1/ EN 287-1 (stähle),EN ISO 9606-2 (Alu)', ondelete='CASCADE')
    prob_nr = fields.Integer("Probe.Nr")
    biege_richtung = fields.Char("Biege richtung/winkel")
    befund_art = fields.Char("Befund -Art der Unregel-mäßigkeit *2)")
    bewertung1 = fields.Char("Bewertung *1)")

class BewertungWeiterePrüfung(sequence_ordered(), ModelSQL, ModelView):
    'Bewertung Weitere Prüfung'
    __name__ = 'bewertung.bewertung.weitere_prüfung'
    bewertung = fields.Many2One('bewertung.bewertung','Bewertung',
        'Bewertungsbogen für Prüfungen nach EN ISO 96061-1/ EN 287-1 (stähle),EN ISO 9606-2 (Alu)', ondelete='CASCADE')    
    prob_nr = fields.Integer("Probe.Nr")
    art_prüfung = fields.Char("Art der Prüfung")
    befund = fields.Char("Befund")
    bewertung_info = fields.Char("Bewertung *1)")

#DRUCKEN Bewertung FORMULAR
        
class BewertungReport(Report):

    @classmethod
    def header_key(cls, record):
        return super().header_key(record) + (('bewertung', record.bewertung),)

    @classmethod
    def get_context(cls, records, header, data):
        context = super().get_context(records, header, data)
        context['bewertung'] = header['bewertung']
        return context
class ZertifikatBewertungReport(BewertungReport):
    __name__ = 'bewertung.zertifikat_bewertung_iso96061'

    @classmethod
    def execute(cls, ids, data):
        with Transaction().set_context(zertifikat=True):
            return super(ZertifikatBewertungReport, cls).execute(ids, data)         
        
#DRUCKEN Bewertung FORMULAR
        
class BewertungIso5817Report(Report):

    @classmethod
    def header_key(cls, record):
        return super().header_key(record) + (('iso5817', record.iso5817),)

    @classmethod
    def get_context(cls, records, header, data):
        context = super().get_context(records, header, data)
        context['iso5817'] = header['iso5817']
        return context
class ZertifikatBewertungIso5817Report(BewertungIso5817Report):
    __name__ = 'bewertung.zertifikat_bewertung_iso5817'

    @classmethod
    def execute(cls, ids, data):
        with Transaction().set_context(zertifikat=True):
            return super(ZertifikatBewertungIso5817Report, cls).execute(ids, data)        
                

