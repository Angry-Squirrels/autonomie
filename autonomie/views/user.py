# -*- coding: utf-8 -*-
# * File Name : user.py
#
# * Copyright (C) 2010 Gaston TJEBBES <g.t@majerti.fr>
# * Company : Majerti ( http://www.majerti.fr )
#
#   This software is distributed under GPLV3
#   License: http://www.gnu.org/licenses/gpl-3.0.txt
#
# * Creation Date : 08-06-2012
# * Last Modified :
#
# * Project : Autonomie
#
"""
    User related views
"""
import logging

from sqlalchemy import or_
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound
from pyramid.security import has_permission

from deform import Form
from deform import ValidationFailure

from autonomie.models.model import User
from autonomie.models.model import Company
from autonomie.utils.forms import merge_session_with_post
from autonomie.utils.widgets import ViewLink
from autonomie.utils.widgets import ActionMenu
from autonomie.utils.widgets import SearchForm
from autonomie.utils.views import submit_btn
from autonomie.views.forms import pwdSchema
from autonomie.views.forms import get_user_schema

from .base import ListView

log = logging.getLogger(__name__)

@view_config(route_name='account', renderer='account.mako',
        permission='view')
def account(request):
    """
        Account handling page
    """
    avatar = request.user
    pwdformschema = pwdSchema.bind(check=True)
    pwdform = Form(pwdformschema, buttons=(submit_btn,))
    html_form = pwdform.render({'login':avatar.login})
    if "submit" in request.params:
        controls = request.params.items()
        try:
            datas = pwdform.validate(controls)
        except ValidationFailure, e:
            html_form = e.render()
        else:
            log.debug(u"# User {0} has changed his password #".format(
                                                    request.user.login))
            dbsession = request.dbsession()
            new_pass = datas['pwd']
            avatar.set_password(new_pass)
            dbsession.merge(avatar)
            dbsession.flush()
            request.session.flash(u"Votre mot de passe a bien été modifié",
                                                                    'main')

    return dict(title="Mon compte",
                html_form=html_form,
                account=avatar
                )

class UserView(ListView):
    """
        User related views
    """
    columns = ("account_lastname", "account_email", )
    default_sort = 'account_lastname'
    default_direction = 'asc'

    def _get_user_form(self, edit=False):
        """
            Return the user add form
        """
        schema = get_user_schema(self.request, edit)
        if edit:
            form = Form(schema, buttons=(submit_btn,))
        else:
            form = Form(schema,
                action=self.request.route_path('users', _query=dict(new=1)),
                buttons=(submit_btn,))
        return form


    @view_config(route_name='users', renderer='users.mako',
            permission='view')
    def directory(self):
        """
            User directory
        """
        search, sort, direction, current_page, items_per_page = \
                                                self._get_pagination_args()
        query = self._get_users()
        if search:
            query = self._filter_search(query, search)
        users = query.order_by(sort + " " + direction).all()

        records = self._get_pagination(users, current_page, items_per_page)
        ret_dict = dict(title=u"Annuaire des utilisateurs",
                        users=records,
                        action_menu=self.actionmenu)
        self._set_item_menu()
        if has_permission('add', self.request.context, self.request):
            # Add user form
            form = self._get_user_form(edit=False)
            ret_dict['html_form'] = form.render()
            add_link = ViewLink(u"Ajouter un utilisateur", "add",
                                js="$('#addform').dialog('open');")
            self.actionmenu.add(add_link)
        self.actionmenu.add(SearchForm(u"Nom ou entreprise"))
        return ret_dict

    def _get_users(self):
        """
            return the user query
        """
        return self.dbsession.query(User).join(User.companies)

    def _filter_search(self, query, search):
        """
            Return a filtered query
        """
        return query.filter( or_(User.lastname.like(search+"%"),
                     User.companies.any(Company.name.like(search+"%"))))

    def _set_item_menu(self, user=None, edit=False):
        self.actionmenu.add(ViewLink(u"Annuaire", "view",
                                     path="users"))
        if edit:
            self.actionmenu.add(ViewLink(u"Voir", "view",
                        path="user", id=user.id))
            self.actionmenu.add(ViewLink(u"Éditer", "edit",
                          path="user", id=user.id, _query=dict(action="edit")))

    @view_config(route_name='users', renderer='user_edit.mako',
                        request_method='POST', permission='add')
    @view_config(route_name='user', renderer='user_edit.mako',
                        request_param='action=edit', permission='edit')
    def user_edit(self):
        """
            Add / Edit a user
        """
        log.debug(u"# In UserView.user #")
        log.debug(u" + request's context {0}".format(self.request.context))
        if self.request.context.__name__ == 'user':
            user = self.request.context
            edit = True
            title = u"Édition de {0} {1}".format(user.lastname, user.firstname)
            validate_msg = u"Le compte a bien été édité"
        else:
            user = User()
            edit = False
            title = u"Ajout d'un nouveau compte"
            validate_msg = u"Le compte a bien été ajouté"
        self._set_item_menu(user, edit=edit)

        form = self._get_user_form(edit=edit)
        if 'submit' in self.request.params:
            datas = self.request.params.items()
            log.debug(u" + Submitted datas")
            log.debug(datas)
            try:
                app_datas = form.validate(datas)
            except ValidationFailure, errform:
                html_form = errform.render()
            else:
                # Validation OK
                # Création/édition du compte de l'utilisateur
                # Création (ou non) de la/des entreprise(s)
                # Création du lien entre les deux
                merge_session_with_post(user, app_datas['user'])
                if app_datas.has_key('password'):
                    if app_datas['password']['pwd']:
                        user.set_password(app_datas['password']['pwd'])
                #avoid creating duplicate companies at this level
                if app_datas.has_key('companies'):
                    companies = set(app_datas.get('companies'))
                    user.companies = []
                    for company_name in companies:
                        company = self.dbsession.query(Company).filter(
                               Company.name==company_name).first()
                        if not company:
                            log.debug(u" + Adding company : %s" % company_name)
                            company = Company()
                            company.name = company_name
                            company.goal = u"Entreprise de {0}".format(
                                user.firstname, user.lastname)
                            company = self.dbsession.merge(company)
                            log.debug(u"Flushing")
                            self.dbsession.flush()
                            log.debug(u"Adding company to the user")
                        user.companies.append(company)
                log.debug(u" + Adding/Editing user : {0}" .format(user.login))
                user = self.dbsession.merge(user)
                log.debug(u"Flushing")
                self.dbsession.flush()
                self.request.session.flash(validate_msg, queue="main")
                return HTTPFound(self.request.route_path("user", id=user.id))
        else:
            html_form = form.render({'user':user.appstruct(),
                        'companies': [comp.name for comp in user.companies]})
        return dict(title=title,
                    html_form=html_form,
                    action_menu=self.actionmenu)

    @view_config(route_name='user', renderer='user.mako', permission='view')
    def user_view(self):
        """
            User view
        """
        user = self.request.context
        self._set_item_menu(user, edit=True)
        return dict(title=u"{0} {1}".format(user.lastname, user.firstname),
                    user=user,
                    action_menu=self.actionmenu)
