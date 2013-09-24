# -*- coding: utf-8 -*-
# * File Name :
#
# * Copyright (C) 2010 Gaston TJEBBES <g.t@majerti.fr>
# * Company : Majerti ( http://www.majerti.fr )
#
#   This software is distributed under GPLV3
#   License: http://www.gnu.org/licenses/gpl-3.0.txt
#
# * Creation Date : 04-09-2012
# * Last Modified :
#
# * Project :
#
"""
    Client model : represents customers
    Stores the company and its main contact

    >>> from autonomie.models.client import Client
    >>> c = Client()
    >>> c.contactLastName = u"Dupont"
    >>> c.contactFirstName = u"Jean"
    >>> c.name = u"Compagnie Dupont avec un t"
    >>> c.code = u"DUPT"
    >>> DBSESSION.add(c)

"""
import logging
from sqlalchemy import (
        Column,
        Integer,
        String,
        Text,
        ForeignKey,
    )
from sqlalchemy.orm import (
        relationship,
        deferred,
        )

from autonomie.models.types import CustomDateType
from autonomie.models.utils import get_current_timestamp
from autonomie.models.base import (
        DBBASE,
        default_table_args,
        )

log = logging.getLogger(__name__)


class Client(DBBASE):
    """
        Client model
        Stores the company and its main contact
        :param name: name of the company
        :param code: internal code of the customer (unique regarding the owner)
        :param multiline address: address of the company
        :param zipCode: zipcode of the company
        :param city: city
        :param country: country, default France
        :param contactLastName: lastname of the contact
        :param contactFirstName: firstname of the contact
        :param function: function of the contact
    """
    __tablename__ = 'customer'
    __table_args__ = default_table_args
    id = Column('id', Integer, primary_key=True)
    code = Column('code', String(4))
    comments = deferred(Column("comments", Text), group='edit')
    creationDate = Column("creationDate", CustomDateType,
                                            default=get_current_timestamp)
    updateDate = Column("updateDate", CustomDateType,
                                        default=get_current_timestamp,
                                        onupdate=get_current_timestamp)
    company_id = Column("company_id", Integer,
                                    ForeignKey('company.id'))
    intraTVA = deferred(Column("intraTVA", String(50)), group='edit')
    address = deferred(Column("address", String(255)), group='edit')
    zipCode = deferred(Column("zipCode", String(20)), group='edit')
    city = deferred(Column("city", String(255)), group='edit')
    country = deferred(Column("country", String(150), default=u'France'),
                                                            group='edit')
    phone = deferred(Column("phone", String(50)), group='edit')
    fax = deferred(Column("fax", String(50)), group="edit")
    function = deferred(Column("function", String(255)), group="edit")
    email = deferred(Column("email", String(255)), group='edit')
    contactLastName = deferred(Column("contactLastName",
                    String(255), default=None), group='edit')
    name = Column("name", String(255), default=None)
    contactFirstName = deferred(Column("contactFirstName",
                    String(255), default=None), group='edit')

    compte_cg = deferred(Column(String(125), default=""), group="edit")
    compte_tiers = deferred(Column(String(125), default=""), group="edit")

    def get_company_id(self):
        """
            :returns: the id of the company this client belongs to
        """
        return self.company.id

    def todict(self):
        """
            :returns: a dict version of the client object
        """
        projects = [project.todict() for project in self.projects]
        return dict(id=self.id,
                    code=self.code,
                    comments=self.comments,
                    intraTVA=self.intraTVA,
                    address=self.address,
                    zipCode=self.zipCode,
                    city=self.city,
                    country=self.country,
                    phone=self.phone,
                    email=self.email,
                    contactLastName=self.contactLastName,
                    contactFirstName=self.contactFirstName,
                    name=self.name,
                    projects=projects,
                    full_address=self.full_address
                    )

    @property
    def full_address(self):
        """
            :returns: the client address formatted in french format
        """
        address = u"{name}\n{address}\n{zipCode} {city}".format(name=self.name,
                address=self.address, zipCode=self.zipCode, city=self.city)
        if self.country not in ("France", "france"):
            address += u"\n{0}".format(self.country)
        return address