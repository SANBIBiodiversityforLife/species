from django.shortcuts import render
from taxa import models
from biblio import models as biblio_models
from people import models as people_models
from redlist import models as redlist_models
import csv
from suds.client import Client
import requests
from mendeley import Mendeley
import re
from django.db.models import Count
from django.http import HttpResponse
import pandas as pd
from psycopg2.extras import NumericRange
from imports import sis_import


def get_or_create_author(surname, first=''):
    """
    Take in a surname and optional first name and try to retrieve an author from the database
    or create one if necessary
    :param surname:
    :param first:
    :return:
    """
    initials = ''
    if first != '':
        # If there's a dot it's definitely initials
        if '.' in first:
            initials = first.split('.')
            first = initials.pop(0).strip()
            initials = ''.join(initials)
        # If it's a very short string most probably it's a set of initials, with spaces or without
        elif len(first) < 4:
            initials = first.replace(' ', '')
            initials = list(initials)
            first = initials.pop(0).strip()
            initials = ''.join(initials)
        # If there are multiple names E.g. "Rukaya Sarah" split into first name and just store initials
        elif ' ' in first:
            initials = first.split(' ')
            first = initials.pop(0).strip()
            initials = [a[0] for a in initials]
            initials = ''.join(initials)

    # Get people with correct surname first
    p = people_models.Person.objects.filter(surname=surname).first()

    # If there's nobody there then make a new person
    if p is None:
        p = people_models.Person(surname=surname, first=first)
        p.save()
        return p

    # If there's no first name just return the surname person
    if first == '':
        return p

    # If we've got a first name then try and get the right person, or else add first name to the surname only person
    # if first != '':
    f = people_models.Person.objects.filter(surname=surname, first__iregex=r'^%s' % first).first()
    if f:
        return f
    else:
        p.first = first
        p.initials = initials
        p.save()
        return p


def create_taxon_description(authority, taxon):
    """
    Takes in a authority string like (Barnard, 1980), splits it into year and author
    Attempts to find the author and year in mendeley and in the database, otherwise it create a new reference
    Then creates a taxonomic description for a taxon
    :param authority:
    :return:
    """

    # Start the REST client for mendeley to try and automatically find publications
    mendeley_id = '3513'
    mendeley_secret = 'gOVvM5RmKseDgcmH'
    mendeley_redirect = 'http://species.sanbi.org'
    mendeley = Mendeley(mendeley_id, client_secret=mendeley_secret, redirect_uri=mendeley_redirect)
    mendeley_session = mendeley.start_client_credentials_flow().authenticate()

    # Splits up an authority string formatted in the standard way e.g. (Barnard, 1937) into year and author
    bracketed = '(' in authority
    authority = re.sub('[()]', '', authority)
    authority = authority.split(',')
    year = authority[-1].strip()
    authors = authority[0]

    # Sanity check, authority should have been split up into year and author list of length 2
    if len(authority) < 2:  # Someone is going to have to fix this...
        year = '0'

    # Try and find citation
    try:
        rs = mendeley_session.catalog.advanced_search(author=authors, min_year=year, max_year=year, view='bib')

        # Kind of embarrassing but i can't work out how to get len(rs.iter())
        cits = []
        for r in rs.iter():
            cits.append(r)
    except:
        import pdb;
        pdb.set_trace()

    # If we get only one result then hurrah we can use it to populate our references table
    if len(cits) == 1:
        cit = cits[0]

        # Get the authors from the mendeley result
        author_list = []
        for a in cit.authors:
            author = get_or_create_author(surname=a.last_name, first=a.first_name)
            author_list.append(author)

        # Get any reference which looks good in the db
        reference = biblio_models.Reference.objects.filter(authors__in=author_list, year=cit.year,
                                                           title__iexact=cit.title).annotate(num_tags=Count('authors')) \
            .filter(num_tags=len(author_list))

        # Hmm maybe we can just assume if title and year are the same it's all good? Let's try...
        reference = biblio_models.Reference.objects.filter(year=cit.year, title__iexact=cit.title)

        # If we couldn't find a reference we need to make one
        if len(reference) < 1:
            reference = biblio_models.Reference(year=cit.year, title=cit.title)
            reference.save()
            biblio_models.assign_multiple_authors(author_list=author_list, reference=reference)

            if cit.type == 'journal':
                biblio_models.Journal.objects.get_or_create(name=cit.source)
        else:
            reference = reference[0]
    # If we didn't get 1 mendeley result we need to add what reference info we can to the db
    else:
        # Insert or create authors
        author_list = []
        for surname in authors.split('&'):
            author = get_or_create_author(surname=surname)
            author_list.append(author)

        # Get citation reference, use whatever we can find in db
        print('getting citation reference from db...')
        try:
            reference = biblio_models.Reference.objects.filter(authors__in=author_list, year=year) \
                .annotate(num_tags=Count('authors')).filter(num_tags=len(author_list))
        except:
            import pdb;
            pdb.set_trace()

        # If we couldn't find a reference we need to make one
        if len(reference) < 1:
            reference = biblio_models.Reference(year=year)
            reference.save()
            biblio_models.assign_multiple_authors(author_list=author_list, reference=reference)

        else:
            reference = reference[0]

    # Make the description
    description, created = models.Description.objects.get_or_create(reference=reference,
                                                                    taxon=taxon,
                                                                    weight=int(bracketed))


def sis(request):
    sis_import.import_sis()


