# -*- coding: utf-8 -*-
# * File Name : model.py
#
# * Copyright (C) 2012 Majerti <tech@majerti.fr>
#   This software is distributed under GPLV3
#   License: http://www.gnu.org/licenses/gpl-3.0.txt
#
# * Creation Date : mer. 11 janv. 2012
# * Last Modified : mar. 17 juil. 2012 21:31:11 CEST
#
# * Project : autonomie
#
"""
    Autonomie's SQLA models
"""
import os
import datetime
import time
import logging

from hashlib import md5

from sqlalchemy import Table
from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import BigInteger
from sqlalchemy import Numeric
from sqlalchemy import Date
from sqlalchemy import DateTime
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.orm import validates
from sqlalchemy.orm import backref
from sqlalchemy.orm import deferred
from sqlalchemy import func

from autonomie.models.types import CustomDateType
from autonomie.models.types import CustomDateType2
from autonomie.models.types import CustomInteger
from autonomie.models.types import CustomFileType
from autonomie.models.utils import format_to_taskdate
from autonomie.models.utils import format_from_taskdate
from autonomie.models.utils import get_current_timestamp


from autonomie.models import DBBASE
from autonomie.utils.exception import Forbidden

log = logging.getLogger(__name__)

company_employee = Table('coop_company_employee', DBBASE.metadata,
    Column("IDCompany", Integer, ForeignKey('coop_company.IDCompany')),
    # IDEmployee est identique dans la table coop_employee
    Column("IDEmployee", Integer, ForeignKey('egw_accounts.account_id')),
        mysql_charset='utf8', mysql_engine='MyISAM',
    )

class Company(DBBASE):
    """
        `IDCompany` int(11) NOT NULL auto_increment,
        `name` varchar(150) NOT NULL,
        `object` varchar(255) NOT NULL,
        `email` varchar(255) default NULL,
        `phone` varchar(20) NOT NULL,
        `mobile` varchar(20) default NULL,
        `comments` text,
        `creationDate` int(11) NOT NULL,
        `updateDate` int(11) NOT NULL,
        `active` varchar(1) NOT NULL default 'Y',
        `IDGroup` int(11) NOT NULL,
        `logo` varchar(255) default NULL,
        `header` varchar(255) default NULL,
        `logoType` varchar(255) default NULL,
        `headerType` varchar(255) default NULL,
        `IDEGWUser` int(11) NOT NULL, # Company EGW account
        `RIB` varchar(255) default NULL,
        `IBAN` varchar(255) default NULL,
        PRIMARY KEY  (`IDCompany`)
    """
    __tablename__ = 'coop_company'
    __table_args__ = {'mysql_engine': 'MyISAM', "mysql_charset":'utf8'}
    id = Column("IDCompany", Integer, primary_key=True)
    name = Column("name", String(150))
    goal = deferred(Column("object", String(255)),
            group='edit')
    email = deferred(Column("email", String(255)),
            group='edit')
    phone = deferred(Column("phone", String(20), default=""),
            group='edit')
    mobile = deferred(Column("mobile", String(20)),
            group='edit')
    comments = deferred(Column("comments", Text),
            group='edit')
    creationDate = deferred(Column("creationDate", CustomDateType,
                                            default=get_current_timestamp))
    updateDate = deferred(Column("updateDate", CustomDateType,
                                        default=get_current_timestamp,
                                        onupdate=get_current_timestamp))
    active = deferred(Column("active", String(1), default="Y"))
    IDGroup = deferred(Column("IDGroup", Integer, default=0))
    logo = deferred(Column("logo", CustomFileType("logo_", 255)),
            group='edit')
    header = deferred(Column("header", CustomFileType("header_", 255)),
            group='edit')
    logoType = deferred(Column("logoType", String(255)))
    headerType = deferred(Column("headerType", String(255)))
    IDEGWUser = deferred(Column("IDEGWUser", Integer, default=0))
    RIB = deferred(Column("RIB", String(255)),
            group='edit')
    IBAN = deferred(Column("IBAN", String(255)),
            group='edit')
    clients = relationship("Client",
                            order_by="Client.id",
                            backref='company')
    projects = relationship("Project",
                            order_by="Project.id",
                            backref="company")

    def get_path(self):
        """
            get the relative filepath specific to the given company
        """
        return os.path.join("company", str(self.id))

    def get_header_filepath(self):
        """
            Returns the header's relative filepath
        """
        if self.header:
            return os.path.join(self.get_path(),
                            'header',
                            self.header['filename'])
        else:
            return None

    def get_logo_filepath(self):
        """
            Return the logo's relative filepath
        """
        if self.logo:
            return os.path.join(self.get_path(),
                            'logo',
                             self.logo['filename'])
        else:
            return None

    def get_company_id(self):
        """
            Return the current company id
            Allows company id access through request's context
        """
        return self.id

    @classmethod
    def query(cls, dbsession, keys=None):
        if keys:
            return dbsession.query(*keys)
        else:
            return dbsession.query(Company).order_by(Company.name)


class User(DBBASE):
    """
        `account_id` int(11) NOT NULL auto_increment,
        `account_lid` varchar(64) NOT NULL,
        `account_pwd` varchar(100) NOT NULL,
        `account_firstname` varchar(50) default NULL,
        `account_lastname` varchar(50) default NULL,
        `account_lastlogin` int(11) default NULL,
        `account_lastloginfrom` varchar(255) default NULL,
        `account_lastpwd_change` int(11) default NULL,
        `account_status` varchar(1) NOT NULL default 'A',
        `account_expires` int(11) default NULL,
        `account_type` varchar(1) default NULL,
        `person_id` int(11) default NULL,
        `account_primary_group` int(11) NOT NULL default '0',
        `account_email` varchar(100) default NULL,
        `account_challenge` varchar(100) default NULL,
        `account_response` varchar(100) default NULL,
        PRIMARY KEY  (`account_id`),
        UNIQUE KEY `egw_accounts_account_lid` (`account_lid`)

    """
    __tablename__ = 'egw_accounts'
    __table_args__ = {'mysql_engine': 'MyISAM', "mysql_charset":'utf8'}
    id = Column('account_id', Integer, primary_key=True)
    login = Column('account_lid', String(64))
    pwd = Column("account_pwd", String(100))
    firstname = Column("account_firstname", String(50))
    lastname = Column("account_lastname", String(50))
    primary_group = Column("account_primary_group",
                            Integer)
    email = Column("account_email", String(100))
    companies = relationship("Company",
                             secondary=company_employee,
                             backref="employees")
    code_compta = Column("code_compta", Integer,
                         default=0)

    @staticmethod
    def _encode_pass(password):
        if type(password) == unicode:
            password = password.encode('utf-8')
        return md5(password).hexdigest()

    def set_password(self, password):
        """
            Set the user's password
        """
        self.pwd = self._encode_pass(password)

    def auth(self, password):
        """
            Authentify the current record with password
        """
        if password:
            return self.pwd == self._encode_pass(password)
        else:
            return False

    def get_company(self, cid):
        """
            Return the company
        """
        if not isinstance(cid, int):
            cid = int(cid)
        for company in self.companies:
            if company.id == cid:
                return company
        raise KeyError

    def is_admin(self):
        """
            return true if the user is and administrator
        """
        return self.primary_group == 1

    def is_manager(self):
        """
            return True if the user is a manager
        """
        return self.primary_group == 2

    def is_contractor(self):
        """
            return True if the user is a contractor
        """
        return self.primary_group == 3

    @classmethod
    def query(cls, dbsession):
        """
            Query users
            Note : join on companies allows us to avoid egw accounts
                    which are not used inside egw's coopagest plugin
        """
        return dbsession.query(User).join(User.companies)

    @classmethod
    def get_code_compta(cls, dbsession):
        """
            Query the last available compta code
        """
        return dbsession.query(func.max(User.code_compta)).first()[0]

class Employee(DBBASE):
    """
        `IDEmployee` int(11) NOT NULL,
        `comments` text,
        `creationDate` int(11) NOT NULL,
        `updateDate` int(11) NOT NULL,
        `IDContact` int(11) default NULL,
        PRIMARY KEY  (`IDEmployee`)
    """
    __tablename__ = 'coop_employee'
    __table_args__ = {'mysql_engine': 'MyISAM', "mysql_charset":'utf8'}
    id = Column("IDEmployee", Integer, primary_key=True)
    creationDate = deferred(Column("creationDate", CustomDateType,
                                            default=get_current_timestamp))
    updateDate = deferred(Column("updateDate", CustomDateType,
                                        default=get_current_timestamp,
                                        onupdate=get_current_timestamp))

class Task(DBBASE):
    """
        Metadata pour une tâche (estimation, invoice)
      `IDTask` int(11) NOT NULL auto_increment, #identifiant de la tâche
      `IDPhase` int(11) NOT NULL,           # identifiant de la phase associée
      `name` varchar(150) NOT NULL,         # Nom de la tâche

      `CAEStatus` varchar(10) default NULL, # Statut de la tâche
             valid/abort/paid/draft/geninv/aboinv/aboest/sent/wait/none
      `statusComment` text,                 # Commentaire sur le statut
                                 communication entrepr/CAE
                                 information de paiement ([par chèque ...])
      `statusPerson` int(11) default NULL,  #Id de la personne associée
                                                aux informations de status
      `statusDate` int(11) default NULL,

      `customerStatus` varchar(10) default NULL, # Reste vide
      `taskDate` int(11) default '0',       # Date
      `IDEmployee` int(11) NOT NULL,        #Id de la personne propriétaire
      `document` varchar(255) default NULL,
      `creationDate` int(11) NOT NULL,
      `updateDate` int(11) NOT NULL,
      `description` text,                   #description
      `documentType` varchar(255) default NULL, # header à envoyer pour
                                l'ouverture du document
                                (doit être réservé aux tâches personnalisées)
      `rank` int(11) default NULL,  # Ordre des tâches
      PRIMARY KEY  (`IDTask`),
      KEY `IDPhase` (`IDPhase`),
      KEY `IDEmployee` (`IDEmployee`)
    """
    __tablename__ = 'coop_task'
    __table_args__ = {'mysql_engine': 'MyISAM', "mysql_charset":'utf8'}
    __mapper_args__ = {
                        'polymorphic_identity':'task',
                        }

    IDTask = Column(Integer, primary_key=True)
    IDPhase = Column("IDPhase", ForeignKey('coop_phase.IDPhase'))
    name = Column("name", String(255))
    CAEStatus = Column('CAEStatus', String(10))
    statusComment = Column("statusComment", Text)
    statusPerson = Column("statusPerson",
                          ForeignKey('egw_accounts.account_id'))
    statusDate = Column("statusDate", CustomDateType,
                                        default=get_current_timestamp,
                                        onupdate=get_current_timestamp)
    taskDate = Column("taskDate", CustomDateType2)
    IDEmployee = Column("IDEmployee",
                            ForeignKey('egw_accounts.account_id'))
    creationDate = deferred(Column("creationDate", CustomDateType,
                                            default=get_current_timestamp))
    updateDate = Column("updateDate", CustomDateType,
                                        default=get_current_timestamp,
                                        onupdate=get_current_timestamp)
    description = Column("description", Text)
    statusPersonAccount = relationship("User",
                        primaryjoin="Task.statusPerson==User.id",
                        backref="taskStatuses")
    owner = relationship("User",
                        primaryjoin="Task.IDEmployee==User.id",
                            backref="ownedTasks")


    def get_status_str(self):
        """
            Return human readable string for task status
        """
        if self.is_invoice():
            _type = "invoice"
        else:
            _type = "estimation"

        if self.statusPersonAccount:
            firstname = self.statusPersonAccount.firstname
            lastname = self.statusPersonAccount.lastname
        else:
            firstname = "Inconnu"
            lastname = ""
        if self.statusDate:
            if isinstance(self.statusDate, datetime.date) or \
                    isinstance(self.statusDate, datetime.datetime):
                date = self.statusDate.strftime("%d/%m/%Y")
            else:
                date = ""
        else:
            date = ""
        suffix = u" par {firstname} {lastname} le {date}".format(
                firstname=firstname, lastname=lastname, date=date)
        if _type == "estimation":
            genre = ""
        else:
            genre = "e"
        statuses = dict((
            ("draft", u"Brouillon modifié",),
            ("wait", u"Validation demandée",),
            ("valid", u"Validé{genre}"),
            ('invalid', u"Invalidé{genre}",),
            ("abort", u"Annulé{genre}",),
            ("geninv", u"Facture générée",),
            ("aboinv", u"Facture annulée",),
            ("aboest", u"Devis annulé",),
            ("sent", u"Document envoyé",),
            ("paid", u"Paiement reçu",),
            ("recinv", u"Client relancé",),
            ))
        if self.is_cancelinvoice() and self.CAEStatus == 'paid':
            status_str = u"Réglé "
        else:
            status_str = statuses.get(self.CAEStatus, u"Statut inconnu")
        status_str = status_str.format(genre=genre)
        return status_str + suffix

    def is_draft(self):
        """
            Return True if this task is in a draft status (or equivalent)
        """
        return self.CAEStatus in ('draft', 'invalid',)

    def is_editable(self, manage=False):
        """
            return True if this task is editable for the user
        """
        if manage:
            return self.CAEStatus in ('draft', 'invalid', 'wait',)
        else:
            return self.CAEStatus in ('draft', 'invalid',)

    def is_valid(self):
        """
            Return True if the task is valid
        """
        return self.CAEStatus == 'valid'

    def has_been_validated(self):
        """
            Return True if the task has been validated
        """
        return self.CAEStatus in ('valid', 'geninv', 'sent', "recinv",)

    def is_waiting(self):
        """
            Return True if the task is in a wait status
        """
        return self.CAEStatus == "wait"

    def is_sent(self):
        """
            Return True if the task is in a sent status
        """
        return self.CAEStatus == "sent"

    @validates('CAEStatus')
    def validate_status(self, key, status):
        """
            validate the caestatus change
        """
        message = u"Vous n'êtes pas autorisé à assigner ce statut {0} à ce \
document."
        log.debug(u"# CAEStatus change #")
        actual_status = self.CAEStatus
        log.debug(u" + was {0}, becomes {1}".format(actual_status, status))
        message = message.format(status)
        if status in ('draft', 'wait',):
            if not actual_status in (None, 'draft', 'invalid'):
                raise Forbidden(message)
        elif status in ('valid',):
            log.debug(self.is_cancelinvoice())
            if self.is_cancelinvoice():
                if not actual_status in ('draft',):
                    raise Forbidden(message)
            elif not actual_status in ('wait',):
                raise Forbidden(message)
        elif status in ('invalid',):
            if not actual_status in ('wait', ):
                raise Forbidden(message)
        elif status in ('aboest',):
            if not actual_status in ('valid', 'sent', 'invalid', 'wait'):
                raise Forbidden(message)
        elif status in ('geninv',):
            if not actual_status in ('valid', 'sent', ):
                raise Forbidden(message)
        elif status in ('sent',):
            if not actual_status in ('valid', "recinv"):
                raise Forbidden(message)
        elif status in ('paid',):
            if not actual_status in ('valid', 'sent', "recinv"):
                raise Forbidden(message)
        elif status in ('aboinv', 'abort',):
            if not actual_status in ('valid', 'sent', "recinv", "invalid", \
                                                                    "wait"):
                raise Forbidden(message)
        elif status in ('recinv',):
            if not actual_status in ('valid', 'sent', "recinv",):
                raise Forbidden(message)
        else:
            assert False
        return status

    def get_company(self):
        """
            Return the company owning this task
        """
        if self.project:
            return self.project.company
        else:
            return None

    def get_company_id(self):
        """
            Return the id of the company owning this task
        """
        return self.project.company.id

    @property
    def id(self):
        return self.IDTask

    def is_invoice(self):
        return hasattr(self, "IDEstimation")

    def is_estimation(self):
        return not self.is_invoice() and not self.is_cancelinvoice()

    def is_cancelinvoice(self):
        return hasattr(self, "IDInvoice")

    @classmethod
    def query(cls, dbsession):
        """
            return a query for getting all the Task objects
        """
        return dbsession.query(Task)

class Estimation(Task):
    """
       `IDTask` int(11) NOT NULL,
      `sequenceNumber` int(11) NOT NULL,        # Indice du devis dans la phase
      `number` varchar(100) NOT NULL,           # identifiant du devis
      `tva` int(11) NOT NULL default '196',     # tva à utiliser dans
                                                  ce devis (*100)
      `discount` int(11) NOT NULL default '0',  # Non utilisé
      `deposit` int(11) NOT NULL default '0',   # accompte (pourcentage)
      `paymentConditions` text,                 # condition de paiement
      `exclusions` text,                        # Notes
      `IDProject` int(11) NOT NULL,             # id du projet auquel
                                                  appartient ce devis
      `manualDeliverables` tinyint(4) default NULL, # les dates des conditions
                                        de paiement ont été fixées manuellement
      `course` tinyint(4) NOT NULL default '0',   # est-ce un cours (0/1)
      `displayedUnits` tinyint(4) NOT NULL default '0', # afficher les unités
                                                                        (0/1)
      `discountHT` int(11) NOT NULL default '0',    #remise HT
      `expenses` int(11) NOT NULL default '0',      # frais
      `paymentDisplay` varchar(20) default 'SUMMARY', #afficher les conditions
                            de paiement ALL/NONE/SUMMARY
      PRIMARY KEY  (`IDTask`),
      KEY `coop_estimation_sequenceNumber` (`sequenceNumber`),
      KEY `coop_estimation_IDProject` (`IDProject`),
      KEY `IDProject` (`IDProject`)
    """
    __tablename__ = 'coop_estimation'
    __table_args__ = {'mysql_engine': 'MyISAM', "mysql_charset":'utf8'}
    IDTask = Column("IDTask", ForeignKey('coop_task.IDTask'),
                primary_key=True, nullable=False)
    sequenceNumber = Column("sequenceNumber", Integer,
                nullable=False)
    number = Column("number", String(100), nullable=False)
    tva = Column("tva", Integer, nullable=False, default=196)
    deposit = Column("deposit", Integer, default=0)
    paymentConditions = deferred(Column("paymentConditions", Text),
                        group='edit')
    exclusions = deferred(Column("exclusions", Text),
                        group='edit')
    IDProject = Column("IDProject", ForeignKey('coop_project.IDProject'))
    manualDeliverables = deferred(Column("manualDeliverables", Integer),
                        group='edit')
    course = deferred(Column('course', Integer,
                                    nullable=False, default=0),
                                    group='edit')
    displayedUnits = deferred(Column('displayedUnits', Integer,
                                    nullable=False, default=0),
                                    group='edit')
    discountHT = Column('discountHT', Integer, default=0)
    expenses = deferred(Column('expenses', Integer, default=0),
                                group='edit')
    paymentDisplay = deferred(Column('paymentDisplay', String(20),
                                                default="SUMMARY"),
                                                group='edit')
    project = relationship("Project",
                            backref=backref('estimations',
                                            order_by='Estimation.taskDate')
                            )
    phase =  relationship("Phase",
                          backref=backref("estimations",
                          order_by='Estimation.taskDate'))
    __mapper_args__ = {
                        'polymorphic_identity':'estimation',
                       }

    def duplicate(self):
        """
            returns a duplicate estimation object
        """
        duple = Estimation()
        duple.IDPhase = self.IDPhase
        duple.taskDate = datetime.date.today()
        duple.IDEmployee = self.IDEmployee
        duple.description = self.description

        duple.tva = self.tva
        duple.deposit = self.deposit
        duple.paymentConditions = self.paymentConditions
        duple.exclusions = self.exclusions
        duple.IDProject = self.IDProject
        duple.manualDeliverables = self.manualDeliverables
        duple.course = self.course
        duple.displayedUnits = self.displayedUnits
        duple.discountHT = self.discountHT
        duple.expenses = self.expenses
        duple.paymentDisplay = self.paymentDisplay
        return duple

    def is_deletable(self):
        """
            Returns True if the estimation could be deleted
        """
        return self.CAEStatus not in ('geninv',)

    def is_cancelled(self):
        """
            Return True is the invoice has been cancelled
        """
        return self.CAEStatus == 'aboest'

    @classmethod
    def query(cls, dbsession):
        """
            Return a db query for Estimation
        """
        return dbsession.query(Estimation)

class Invoice(Task):
    """
       `IDTask` int(11) NOT NULL,
       `IDEstimation` int(11) DEFAULT '0',
       `IDProject` int(11) NOT NULL,
       `sequenceNumber` int(11) NOT NULL,
       `number` varchar(100) NOT NULL,
       `tva` int(11) NOT NULL DEFAULT '196',
       `discount` int(11) NOT NULL DEFAULT '0',
       `paymentConditions` text,
       `estimationDate` int(11) DEFAULT '0',
       `estimationNumber` varchar(100) DEFAULT NULL,
       `deposit` tinyint(4) NOT NULL DEFAULT '0',
       `course` tinyint(4) NOT NULL DEFAULT '0',
       `officialNumber` int(11) DEFAULT NULL,
       `paymentMode` varchar(10) DEFAULT NULL,
       `displayedUnits` tinyint(4) NOT NULL DEFAULT '0',
       `discountHT` int(11) NOT NULL DEFAULT '0',
       `expenses` int(11) NOT NULL DEFAULT '0',
       PRIMARY KEY (`IDTask`),
       KEY `IDProject` (`IDProject`),
       KEY `IDEstimation` (`IDEstimation`)
    """
    __tablename__ = 'coop_invoice'
    __table_args__ = {'mysql_engine': 'MyISAM', "mysql_charset":'utf8'}
    __mapper_args__ = {
                       'polymorphic_identity':'invoice',
                       }
    IDTask = Column("IDTask", ForeignKey('coop_task.IDTask'), primary_key=True)
    IDEstimation = Column("IDEstimation", ForeignKey('coop_estimation.IDTask'))
    IDProject = Column("IDProject", ForeignKey('coop_project.IDProject'))
    sequenceNumber = Column("sequenceNumber", Integer,
                nullable=False)
    number = Column("number", String(100), nullable=False)
    tva = Column("tva", Integer, nullable=False, default=196)
    paymentConditions = deferred(Column("paymentConditions", Text),
                                                        group='edit')
    deposit = deferred(Column('deposit', Integer,
                                    nullable=False, default=0),
                                    group='edit')
    course = deferred(Column('course', Integer,
                                    nullable=False, default=0),
                                    group='edit')
    officialNumber = Column("officialNumber", Integer)
    paymentMode = Column("paymentMode", String(10))
    displayedUnits = deferred(Column('displayedUnits', Integer,
                                    nullable=False, default=0),
                                    group='edit')
    discountHT = Column('discountHT', Integer, default=0)
    expenses = deferred(Column('expenses', Integer, default=0), group='edit')

    project = relationship("Project", backref=backref('invoices',
                                            order_by='Invoice.taskDate')
                            )
    phase =  relationship("Phase",
                          backref=backref("invoices",
                                          order_by='Invoice.taskDate')
                          )
    estimation = relationship("Estimation",
                      backref="invoice",
                      primaryjoin="Invoice.IDEstimation==Estimation.IDTask",
                                )

    def is_tolate(self):
        """
            Return True if a payment is expected since more than
            45 days
        """
        today = datetime.date.today()
        elapsed = today - self.taskDate
        if elapsed > datetime.timedelta(days=45):
            tolate = True
        else:
            tolate = False
        return self.CAEStatus in ('valid', 'sent','recinv') and tolate

    def is_paid(self):
        """
            Return True if the invoice is paid
        """
        return self.CAEStatus == 'paid'

    def is_cancelled(self):
        """
            Return True is the invoice has been cancelled
        """
        return self.CAEStatus == 'aboinv'

    def get_paymentmode_str(self):
        """
            Return a user-friendly string describing the payment Mode
        """
        if self.paymentMode == 'CHEQUE':
            return u"par chèque"
        elif self.paymentMode == 'VIREMENT':
            return u"par virement"
        else:
            return u"mode paiement inconnu"

    @validates("paymentMode")
    def validate_paymentMode(self, key, paymentMode):
        """
            Validate the paymentMode
        """
        if not paymentMode in ('CHEQUE', 'VIREMENT'):
            raise Forbidden(u'Mode de paiement inconnu')
        return paymentMode

    @classmethod
    def query(cls, dbsession):
        """
            Return a database query for invoices
        """
        return dbsession.query(Invoice)

    @classmethod
    def get_officialNumber(cls, dbsession):
        """
            Return the next officialNumber available in the Invoice's table
            Take the max of official Number
            when taskDate startswith the current year
            taskdate is a string (YYYYMMDD)
        """
        current_year = datetime.date.today().year
        return dbsession.query(func.max(Invoice.officialNumber)).filter(
                Invoice.taskDate.between(current_year*10000,
                                         (current_year+1)*10000
                                    ))

    def gen_cancel_invoice(self):
        """
            Return a cancel invoice with self's informations
        """
        cancelinvoice = CancelInvoice()
        cancelinvoice.IDPhase = self.IDPhase
        cancelinvoice.CAEStatus = 'draft'
        cancelinvoice.taskDate = datetime.date.today()
        cancelinvoice.description = self.description

        cancelinvoice.IDInvoice = self.IDTask
        cancelinvoice.IDProject = self.IDProject
        cancelinvoice.invoiceDate = self.taskDate
        cancelinvoice.invoiceNumber = self.officialNumber
        cancelinvoice.expenses = -1 * self.expenses
        cancelinvoice.displayedUnits = self.displayedUnits
        cancelinvoice.tva = self.tva
        return cancelinvoice

class EstimationLine(DBBASE):
    """
      `IDWorkLine` int(11) NOT NULL auto_increment,
      `IDTask` int(11) NOT NULL,
      `rowIndex` int(11) NOT NULL,          # index de la ligne
      `description` text,                   # "Prestation"
      `cost` int(11) default NULL,          # montant
      `quantity` double default NULL,       #quantité
      `creationDate` int(11) default NULL,
      `updateDate` int(11) default NULL,
      `unity` varchar(10) default NULL,     # unité
      PRIMARY KEY  (`IDWorkLine`),
      KEY `coop_estimation_line_IDTask` (`IDTask`),
      KEY `coop_estimation_line_rowIndex` (`rowIndex`),
      KEY `IDTask` (`IDTask`)
    """
    __tablename__ = 'coop_estimation_line'
    __table_args__ = {'mysql_engine': 'MyISAM', "mysql_charset":'utf8'}
    id = Column("IDWorkLine", Integer, primary_key=True)
    IDTask = Column(Integer, ForeignKey('coop_estimation.IDTask'))
    rowIndex = Column("rowIndex", Integer)
    description = Column("description", Text)
    cost = Column("cost", Integer)
    quantity = Column("quantity", Integer)
    creationDate = deferred(Column("creationDate", CustomDateType,
                                            default=get_current_timestamp))
    updateDate = deferred(Column("updateDate", CustomDateType,
                                        default=get_current_timestamp,
                                        onupdate=get_current_timestamp))
    unity = Column("unity", String(10))
    task = relationship("Estimation", backref=backref("lines",
                            order_by='EstimationLine.rowIndex'))

    def get_unity_label(self, pretty=False):
        """
            return unitie's label
        """
        if pretty:
            default = u""
        else:
            default = u"-"
        labels = dict(
                NONE=default,
                HOUR=u"heure(s)",
                DAY=u"jour(s)",
                WEEK=u"semaine(s)",
                MONTH=u"mois",
                FEUIL=u"feuillet(s)",
                PACK=u"forfait",
                )
        return labels.get(self.unity, default)

    def duplicate(self):
        """
            duplicate a line
        """
        newone = EstimationLine()
        newone.rowIndex = self.rowIndex
        newone.cost = self.cost
        newone.description = self.description
        newone.quantity = self.quantity
        newone.unity = self.unity
        return newone

class InvoiceLine(DBBASE):
    """
        Invoice lines
        `IDInvoiceLine` int(11) NOT NULL auto_increment,
        `IDTask` int(11) NOT NULL,
        `rowIndex` int(11) NOT NULL,
        `description` text,
        `cost` int(11) default '0',
        `quantity` double default '1',
        `creationDate` int(11) default '0',
        `updateDate` int(11) default '0',
        `unity` varchar(10) default NULL,
        PRIMARY KEY  (`IDInvoiceLine`),
    """
    __tablename__ = 'coop_invoice_line'
    __table_args__ = {'mysql_engine': 'MyISAM', "mysql_charset":'utf8'}
    id = Column("IDInvoiceLine", Integer, primary_key=True)
    IDTask = Column(Integer, ForeignKey('coop_invoice.IDTask'))
    rowIndex = Column("rowIndex", Integer)
    description = Column("description", Text)
    cost = Column("cost", Integer)
    quantity = Column("quantity", Integer)
    creationDate = deferred(Column("creationDate", CustomDateType,
                                            default=get_current_timestamp))
    updateDate = deferred(Column("updateDate", CustomDateType,
                                        default=get_current_timestamp,
                                        onupdate=get_current_timestamp))
    unity = Column("unity", String(10))
    task = relationship("Invoice", backref=backref("lines",
                            order_by='InvoiceLine.rowIndex'))

    def get_unity_label(self, pretty=False):
        """
            return unitie's label
        """
        if pretty:
            default = u""
        else:
            default = u"-"
        labels = dict(
                NONE=default,
                HOUR=u"heure(s)",
                DAY=u"jour(s)",
                WEEK=u"semaine(s)",
                MONTH=u"mois",
                FEUIL=u"feuillet(s)",
                PACK=u"forfait",
                )
        return labels.get(self.unity, default)

    def duplicate(self):
        """
            duplicate a line
        """
        newone = InvoiceLine()
        newone.rowIndex = self.rowIndex
        newone.cost = self.cost
        newone.description = self.description
        newone.quantity = self.quantity
        newone.unity = self.unity
        return newone

    def gen_cancel_invoice_line(self):
        """
            Return a cancel invoice line duplicating this one
        """
        newone = CancelInvoiceLine()
        newone.rowIndex = self.rowIndex
        newone.cost = -1 * self.cost
        newone.description = self.description
        newone.quantity = self.quantity
        newone.unity = self.unity
        return newone


class PaymentLine(DBBASE):
    """
        coop_estimation_payment
        `IDPaymentLine` int(11) NOT NULL auto_increment,
        `IDTask` int(11) NOT NULL,
        `rowIndex` int(11) NOT NULL,
        `description` text,
        `amount` int(11) default NULL,
        `creationDate` int(11) default NULL,
        `updateDate` int(11) default NULL,
        `paymentDate` int(11) default NULL,
    """
    __tablename__ = 'coop_estimation_payment'
    __table_args__ = {'mysql_engine': 'MyISAM', "mysql_charset":'utf8'}
    id = Column("IDPaymentLine", Integer, primary_key=True, nullable=False)
    IDTask = Column(Integer, ForeignKey('coop_estimation.IDTask'))
    rowIndex = Column("rowIndex", Integer)
    description = Column("description", Text)
    amount = Column("amount", Integer)
    creationDate = deferred(Column("creationDate", CustomDateType,
                                            default=get_current_timestamp))
    updateDate = deferred(Column("updateDate", CustomDateType,
                                        default=get_current_timestamp,
                                        onupdate=get_current_timestamp))
    paymentDate = Column("paymentDate", CustomDateType2(11))
    estimation = relationship("Estimation", backref=backref('payment_lines',
                    order_by='PaymentLine.rowIndex'))

    def duplicate(self):
        """
            duplicate a paymentline
        """
        newone = PaymentLine()
        newone.rowIndex = self.rowIndex
        newone.amount = self.amount
        newone.description = self.description
        newone.paymentDate = datetime.date.today()
        return newone

class Client(DBBASE):
    """
       `code` varchar(4) NOT NULL,
        `IDContact` int(11) default '0',
        `comments` text,
        `creationDate` int(11) NOT NULL,
        `updateDate` int(11) NOT NULL,
        `IDCompany` int(11) NOT NULL,
        `intraTVA` varchar(50) default NULL,
        `address` varchar(255) default NULL,
        `zipCode` varchar(20) default NULL,
        `city` varchar(255) default NULL,
        `country` varchar(150) default NULL,
        `phone` varchar(50) default NULL,
        `email` varchar(255) default NULL,
        `contactLastName` varchar(255) default NULL,
        `name` varchar(255) default NULL,
        `contactFirstName` varchar(255) default NULL,
        PRIMARY KEY  (`code`),
        KEY `IDCompany` (`IDCompany`)
    """
    __tablename__ = 'coop_customer'
    __table_args__ = {'mysql_engine': 'MyISAM', "mysql_charset":'utf8'}
    id = Column('code', String(4), primary_key=True)
    comments = deferred(Column("comments", Text), group='edit')
    creationDate = Column("creationDate", CustomDateType,
                                            default=get_current_timestamp)
    updateDate = Column("updateDate", CustomDateType,
                                        default=get_current_timestamp,
                                        onupdate=get_current_timestamp)
    id_company = Column("IDCompany", Integer,
                                    ForeignKey('coop_company.IDCompany'))
    intraTVA = deferred(Column("intraTVA", String(50)), group='edit')
    address = deferred(Column("address", String(255)), group='edit')
    zipCode = deferred(Column("zipCode", String(20)), group='edit')
    city = deferred(Column("city", String(255)), group='edit')
    country = deferred(Column("country", String(150)), group='edit')
    phone = deferred(Column("phone", String(50)), group='edit')
    email = deferred(Column("email", String(255)), group='edit')
    contactLastName = deferred(Column("contactLastName",
                    String(255), default=None), group='edit')
    name = Column("name", String(255), default=None)
    contactFirstName = deferred(Column("contactFirstName",
                    String(255), default=None), group='edit')
    projects = relationship("Project", backref="client")

    def get_company_id(self):
        return self.company.id

class Project(DBBASE):
    """
        `IDProject` int(11) NOT NULL auto_increment,
        `name` varchar(150) NOT NULL,
        `customerCode` varchar(4) NOT NULL,
        `type` varchar(150) default NULL,
        `code` varchar(4) NOT NULL,
        `definition` text,
        `creationDate` int(11) NOT NULL,
        `updateDate` int(11) NOT NULL,
        `startingDate` int(11) default NULL,
        `endingDate` int(11) default NULL,
        `status` varchar(20) NOT NULL,
        `IDCompany` int(11) NOT NULL,
        `dispatchType` varchar(10) NOT NULL default 'PERCENT',
        `archived` tinyint(4) NOT NULL default '0',
        PRIMARY KEY  (`IDProject`),
        KEY `IDCompany` (`IDCompany`)
    """
    __tablename__ = 'coop_project'
    __table_args__ = {'mysql_engine': 'MyISAM', "mysql_charset":'utf8'}
    id = Column('IDProject', Integer, primary_key=True)
    name = Column("name", String(255))
    code_client = Column("customerCode", String(4),
                                    ForeignKey('coop_customer.code'))
    code = Column("code", String(4), nullable=False)
    definition = deferred(Column("definition", Text), group='edit')

    id_company = Column("IDCompany", Integer,
                                    ForeignKey('coop_company.IDCompany'))
    creationDate = deferred(Column("creationDate", CustomDateType,
                                            default=get_current_timestamp))
    updateDate = deferred(Column("updateDate", CustomDateType,
                                        default=get_current_timestamp,
                                        onupdate=get_current_timestamp))
    startingDate = deferred(Column("startingDate", CustomDateType,
                                default=get_current_timestamp), group='edit')
    endingDate = deferred(Column("endingDate", CustomDateType,
                                default=get_current_timestamp), group='edit')

    type = deferred(Column('type', String(150)), group='edit')
    archived = Column("archived", String(255), default=0)

    def get_estimation(self, taskid):
        """
            Returns the estimation with id taskid
        """
        for estimation in self.estimations:
            if estimation.IDTask == int(taskid):
                return estimation
        raise KeyError("No such task in this project")

    def get_invoice(self, taskid):
        """
            Returns the estimation with id taskid
        """
        for invoice in self.invoices:
            if invoice.IDTask == int(taskid):
                return invoice
        raise KeyError("No such task in this project")

    def is_archived(self):
        """
            Return True if the project is archived
        """
        return self.archived == 1

    def is_deletable(self):
        """
            Return True if this project could be deleted
        """
        return self.archived == 1 and not self.invoices

    def get_company_id(self):
        return self.company.id


class Phase(DBBASE):
    """
        Phase d'un projet
        `IDPhase` int(11) NOT NULL auto_increment,
        `IDProject` int(11) NOT NULL,
        `name` varchar(150) NOT NULL,
        `IDPreviousPhase` int(11) NOT NULL default '0',
        `creationDate` int(11) NOT NULL,
        `updateDate` int(11) NOT NULL,
    """
    __tablename__ = 'coop_phase'
    __table_args__ = {'mysql_engine': 'MyISAM', "mysql_charset":'utf8'}
    id = Column('IDPhase', Integer, primary_key=True)
    id_project = Column('IDProject', Integer,
                        ForeignKey('coop_project.IDProject'))
    name = Column("name", String(150), default=u'Phase par défaut')
    project = relationship("Project", backref="phases")
    creationDate = deferred(Column("creationDate", CustomDateType,
                                            default=get_current_timestamp))
    updateDate = deferred(Column("updateDate", CustomDateType,
                                        default=get_current_timestamp,
                                        onupdate=get_current_timestamp))
    def is_default(self):
        """
            return True is this phase is a default one
        """
        return self.name in (u'Phase par défaut', u"default", u"défaut",)

class Tva(DBBASE):
    """
        coop_tva
        `id` int(2) NOT NULL auto_increment,
        `name` varchar(8) NOT NULL,
        `value` int(5)
        `default` int(2) default 0 #rajouté par mise à jour 1.2
    """
    __tablename__ = 'coop_tva'
    __table_args__ = {'mysql_engine': 'MyISAM', "mysql_charset":'utf8'}
    id = Column('id', Integer, primary_key=True)
    name = Column("name", String(8), nullable=False)
    value = Column("value", Integer)
    default = Column("default", Integer)

    @classmethod
    def query(cls, dbsession):
        return dbsession.query(Tva).order_by('value')

class TaskStatus(DBBASE):
    """
        `IDTask` int(11) NOT NULL,
        `statusCode` varchar(10) NOT NULL,
        `statusComment` text,
        `statusPerson` int(11) default NULL,
        `statusDate` int(11) default NULL,
        KEY `IDTask` (`IDTask`),
        KEY `statusCode` (`statusCode`)
    """
    __tablename__ = 'coop_task_status'
    __table_args__ = {'mysql_engine': 'MyISAM', "mysql_charset":'utf8'}
    id = Column("id", Integer, primary_key=True)
    id_task = Column('IDTask', Integer,
                        ForeignKey('coop_task.IDTask'))
    statusCode = Column("statusCode", String(10))
    statusComment = Column("statusComment", Text)
    statusDate = Column("statusDate", Integer)
    task = relationship("Task", backref="taskstatus")

class Config(DBBASE):
    """
        Table containing the main configuration
          `config_app` varchar(50) NOT NULL,
          `config_name` varchar(255) NOT NULL,
          `config_value` text,
          PRIMARY KEY  (`config_app`,`config_name`)
    """
    __tablename__ = 'egw_config'
    __table_args__ = {'mysql_engine': 'MyISAM', "mysql_charset":'utf8'}
    app = Column("config_app", String(50), primary_key=True)
    name = Column("config_name", String(255), primary_key=True)
    value = Column("config_value", Text())

class ManualInvoice(DBBASE):
    """
        symf_facture_manuelle
        `id` bigint(20) NOT NULL auto_increment,
        `sequence_id` bigint(20) NOT NULL,
        `libelle` varchar(255) character set utf8 default NULL,
        `montant_ht` decimal(18,2) default NULL,
        `tva` decimal(18,2) default NULL,
        `paiement_ok` tinyint(1) default NULL,
        `paiement_date` date default NULL,
        `paiement_comment` varchar(255) character set utf8 default NULL,
        `client_id` varchar(5) character set utf8 NOT NULL,
        `date_emission` date default NULL,
        `compagnie_id` bigint(20) NOT NULL,
        `created_at` datetime NOT NULL,
        `updated_at` datetime NOT NULL,
        PRIMARY KEY  (`id`),
        UNIQUE KEY `id` (`id`)
    """
    __tablename__ = 'symf_facture_manuelle'
    __table_args__ = {'mysql_engine': 'MyISAM', "mysql_charset":'utf8'}
    id = Column('id', BigInteger, primary_key=True)
    officialNumber = Column('sequence_id', BigInteger)
    description = Column('libelle', String(255))
    montant_ht = Column("montant_ht", Integer)
    tva = Column("tva", Integer)
    payment_ok = Column("paiement_ok", Integer)
    statusDate = Column("paiement_date", Date())
    paymentMode = Column("paiement_comment", String(255))
    client_id = Column('client_id', String(5),
                            ForeignKey('coop_customer.code'))
    taskDate = Column("date_emission", Date(),
                                default=datetime.datetime.now)
    company_id = Column('compagnie_id', BigInteger,
                            ForeignKey('coop_company.IDCompany'))
    created_at = deferred(Column("created_at", DateTime,
                                      default=datetime.datetime.now))
    updated_at = deferred(Column("updated_at", DateTime,
                                      default=datetime.datetime.now,
                                      onupdate=datetime.datetime.now))
    client = relationship("Client",
                primaryjoin="Client.id==ManualInvoice.client_id",
                  backref='manual_invoices')
    company = relationship("Company",
                primaryjoin="Company.id==ManualInvoice.company_id",
                  backref='manual_invoices')

    def is_paid(self):
        """
            return True if it's paid
        """
        return self.payment_ok == 1

    def get_paymentmode_str(self):
        """
            Return the payment mode string
        """
        if self.paymentMode == u'chèque':
            return u"par chèque"
        elif self.paymentMode == u'virement':
            return u"par virement"
        else:
            return u""

    @validates("paymentMode")
    def validate_paymentMode(self, key, paymentMode):
        """
            Validate the paymentMode
        """
        if not paymentMode in (u'chèque', u'virement'):
            raise Forbidden(u'Mode de paiement inconnu')
        return paymentMode

    def is_tolate(self):
        today = datetime.date.today()
        elapsed = today - self.taskDate
        return not self.is_paid() and elapsed > datetime.timedelta(days=45)

    @property
    def number(self):
        """
            return the invoice number
        """
        return u"FACT_MAN_{0}".format(self.officialNumber)

    @property
    def IDTask(self):
        return None

    @property
    def project(self):
        """
            return None
        """
        class Void:
            pass
        p = Void()
        p.client = self.client
        p.company = self.company
        return p

    def get_company(self):
        """
            return the company
        """
        return self.company

    def is_cancelinvoice(self):
        """
            return false
        """
        return False

    def is_invoice(self):
        """
            return false
        """
        return False

    @classmethod
    def get_officialNumber(cls, dbsession):
        """
            Return the greatest officialNumber actually used in the
            ManualInvoice table
        """
        current_year = datetime.date.today().year
        return dbsession.query(func.max(ManualInvoice.officialNumber)).filter(
                    func.year(ManualInvoice.taskDate) == current_year)

class OperationComptable(DBBASE):
    """
        Recense les opérations comptables
        `id` bigint(20) NOT NULL auto_increment,
        `montant` decimal(18,2) default NULL,
        `charge` tinyint(1) default NULL,
        `compagnie_id` bigint(20) NOT NULL,
        `date` date default NULL,
        `libelle` varchar(255) collate utf8_unicode_ci default NULL,
        `created_at` datetime NOT NULL,
        `updated_at` datetime NOT NULL,
        `annee` bigint(20) default NULL,
        `type` text collate utf8_unicode_ci,
        PRIMARY KEY  (`id`),
        UNIQUE KEY `id` (`id`)
    """
    __tablename__ = 'symf_operation_treso'
    __table_args__ = {'mysql_engine': 'MyISAM', "mysql_charset":'utf8'}
    id = Column('id', BigInteger, primary_key=True)
    amount = Column("montant", Numeric)
    charge = Column("charge", Integer, default=0)
    company_id = Column('compagnie_id', CustomInteger,
                            ForeignKey('coop_company.IDCompany'))
    date = Column("date", Date(), default=datetime.date.today)
    label = Column("libelle", String(255), default="")
    company = relationship("Company",
                       primaryjoin="Company.id==OperationComptable.company_id",
                       backref='operation_comptable')
    created_at = deferred(Column("created_at", DateTime,
                                        default=datetime.datetime.now))
    updated_at = deferred(Column("updated_at", DateTime,
                                        default=datetime.datetime.now,
                                        onupdate=datetime.datetime.now))
    year = Column("annee", BigInteger)
    type = Column("type", Text)

class CancelInvoice(Task):
    """
       `IDTask` int(11) NOT NULL,
       `sequenceNumber` int(11) NOT NULL,
       `number` varchar(100) NOT NULL,
       `tva` int(11) NOT NULL DEFAULT '196',
       `reimbursementConditions` text,
       `officialNumber` int(11) DEFAULT NULL,
       `paymentMode` varchar(10) DEFAULT NULL,
       `displayedUnits` tinyint(4) NOT NULL DEFAULT '0',
       `expenses` int(11) NOT NULL DEFAULT '0',
       `IDProject` int(11) NOT NULL,
       `IDInvoice` int(11) DEFAULT '0',
       `invoiceDate` int(11) DEFAULT '0',
       `invoiceNumber` varchar(100) DEFAULT NULL,
       PRIMARY KEY (`IDTask`),
       KEY `IDProject` (`IDProject`),
       KEY `IDEstimation` (`IDEstimation`)
    """
    __tablename__ = 'coop_cancel_invoice'
    __table_args__ = {'mysql_engine': 'MyISAM', "mysql_charset":'utf8'}
    __mapper_args__ = {
                        'polymorphic_identity':'cancelinvoice',
                        }
    IDTask = Column(Integer, ForeignKey('coop_task.IDTask'), primary_key=True)

    IDInvoice = Column(Integer, ForeignKey('coop_invoice.IDTask'),
                                                        default=None)
    IDProject = Column(Integer, ForeignKey('coop_project.IDProject'))
    sequenceNumber = deferred(Column(Integer), group='edit')
    number = Column(String(100))
    tva = Column(Integer, default=1960)
    reimbursementConditions = deferred(Column(String(255), default=None),
            group='edit')
    officialNumber = deferred(Column(Integer, default=None), group='edit')
    paymentMode = deferred(Column(String(80), default=None), group='edit')
    displayedUnits = Column(Integer, default=0)
    expenses = deferred(Column(Integer, default=0), group='edit')

    project = relationship("Project", backref=backref('cancelinvoices',
                                            order_by='CancelInvoice.taskDate')
                            )
    phase = relationship("Phase",
                          backref=backref("cancelinvoices",
                                          order_by='CancelInvoice.taskDate')
                          )
    invoice = relationship("Invoice",
                      backref="cancelinvoice",
                      primaryjoin="CancelInvoice.IDInvoice==Invoice.IDTask",
                                )
    def is_paid(self):
        """
            Return True if the invoice is paid
        """
        return self.CAEStatus == 'paid'

    def is_editable(self):
        """
            Return True if the current task is editable
        """
        return self.CAEStatus == 'draft'

    def get_paymentmode_str(self):
        """
            Return a user-friendly string describing the payment Mode
        """
        if self.paymentMode == 'CHEQUE':
            return u"par chèque"
        elif self.paymentMode == 'VIREMENT':
            return u"par virement"
        else:
            return u"mode paiement inconnu"

    @classmethod
    def get_officialNumber(cls, dbsession):
        """
            Return the greatest officialNumber actually used in the
            ManualInvoice table
        """
        current_year = datetime.date.today().year
        return dbsession.query(func.max(CancelInvoice.officialNumber)).filter(
                    func.year(CancelInvoice.taskDate) == current_year)

    def is_tolate(self):
        """
            Return False
        """
        return False

class CancelInvoiceLine(DBBASE):
    """
        CancelInvoice lines
        `id` int(11) NOT NULL auto_increment,
        `IDTask` int(11) NOT NULL,
        `rowIndex` int(11) NOT NULL,
        `description` text,
        `cost` int(11) default '0',
        `quantity` double default '1',
        `creationDate` int(11) default '0',
        `updateDate` int(11) default '0',
        `unity` varchar(10) default NULL,
        PRIMARY KEY  (`IDCancelInvoiceLine`),
    """
    __tablename__ = 'coop_cancel_invoice_line'
    __table_args__ = {'mysql_engine': 'MyISAM', "mysql_charset":'utf8'}
    id = Column(Integer, primary_key=True)
    IDTask = Column(Integer, ForeignKey('coop_cancel_invoice.IDTask'))
    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, default=datetime.datetime.now,
                                  onupdate=datetime.datetime.now)
    task = relationship("CancelInvoice", backref="lines",
                            order_by='CancelInvoiceLine.rowIndex'
                        )
    rowIndex = Column(Integer)
    description = Column(Text, default="")
    cost = Column(Integer, default=0)
    quantity = Column(Integer, default=1)
    unity = Column(String(10), default=None)

    def get_unity_label(self, pretty=False):
        """
            return unitie's label
        """
        if pretty:
            default = u""
        else:
            default = u"-"
        labels = dict(
                NONE=default,
                HOUR=u"heure(s)",
                DAY=u"jour(s)",
                WEEK=u"semaine(s)",
                MONTH=u"mois",
                FEUIL=u"feuillet(s)",
                PACK=u"forfait",
                )
        return labels.get(self.unity, default)

    def duplicate(self):
        """
            duplicate a line
        """
        newone = CancelInvoiceLine()
        newone.rowIndex = self.rowIndex
        newone.cost = self.cost
        newone.description = self.description
        newone.quantity = self.quantity
        newone.unity = self.unity
        return newone

class Holliday(DBBASE):
    """
        Hollidays table
        Stores the start and end date for holliday declaration
        user_id
        start_date
        end_date
    """
    __tablename__ = "coop_holliday"
    __table_args__ = {'mysql_engine': 'MyISAM', "mysql_charset":'utf8'}
    id = Column(Integer, primary_key=True)
    user_id = Column("user_id", Integer, ForeignKey('egw_accounts.account_id'))
    start_date = Column(Date)
    end_date = Column(Date)
    user = relationship("User",
                        backref=backref("hollidays",
                                        order_by="Holliday.start_date"),
                        primaryjoin="Holliday.user_id==User.id"
                        )

    @classmethod
    def query(cls, dbsession, user_id=None):
        """
            query the database for the current class instances
            @dbsession : instanciated dbsession
            @user_id: id of the user we want the holliday from
        """
        q = dbsession.query(Holliday)
        if user_id:
            q = q.filter(Holliday.user_id==user_id)
        return q.order_by("start_date")
