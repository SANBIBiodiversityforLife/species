from taxa import models, helpers
from redlist import models as redlist_models
import pandas as pd
from imports import sis_import, spstatus_import, sarca_sabca, sabca
from imports import sis_import, spstatus_import
from imports import seakeys as seakeys_import
import json
import os
from django.contrib.gis.geos import Point, Polygon


# Run after all of the imports have gone through
def populate_higher_level_common_names(request):
    ranks = models.Rank.objects.filter(name__in=['Genus', 'Family', 'Order', 'Phylum', 'Class'])
    taxa = models.Taxon.objects.filter(rank__in=ranks, common_names__isnull=True)
    english = models.Language.objects.get(name='English')

    # Manually found some nodes common names
    pwd = os.path.abspath(os.path.dirname(__file__))
    common_names = {}
    with open(os.path.join(pwd, '..', 'data-sources', 'common_names.csv')) as csv_file:
        reader = csv.reader(csv_file)
        for row in reader:
            common_names[row[0]] = row[1]

    for taxon in taxa:
        taxon_name = taxon.name.lower()

        # Try and get it in my list first
        if taxon_name in common_names:
            common_name = models.CommonName.objects.get_or_create(name=common_names[taxon_name], taxon=taxon, language=english)
            continue

        # Otherwise search GBIF
        r = requests.get('http://api.gbif.org/v1/species/search?q=' + taxon.name.lower() + '&rank=' + str(taxon.rank))
        gbif = r.json()
        print('-----')
        try:
            print(taxon.name.lower())
        except:
            print('could not print')
        #import pdb; pdb.set_trace()
        try:
            for result in gbif['results']:
                if 'vernacularNames' in result and len(result['vernacularNames']) > 0:
                    for vn in result['vernacularNames']:
                        if vn['language'].lower() == '' or vn['language'].lower() == 'english':
                            common_name_text = vn['vernacularName'] # Reasonable to assume english?
                            common_name = models.CommonName.objects.get_or_create(name=common_name_text, taxon=taxon, language=english)
                            print('GBIF ' + taxon.name.lower() + ' : ' + common_name_text)
                            break
        except (KeyError, IndexError, UnicodeDecodeError, UnicodeEncodeError):
            import pdb; pdb.set_trace()
        # common_name.save()

    #r = requests.get('http://api.gbif.org/v1/species?' + )
    #r.json()


def import_phylums(request):
    sis_import.import_phylums()


# SIS: Amphibian, Mammals, Dragonflies, Reptiles, Freshwater Fish
def sis(request):
    sis_import.import_sis()


# Butterflies
def sarca(request):
    sarca_sabca.import_sql()


# Reptiles - going to move to SIS though
def sabca_r(request):
    sabca.import_sabca_sql()


# Legacy data - we're not importing this
def spstatus(request):
    spstatus_import.import_spstatus()


# Linefish
def seakeys(request):
    seakeys_import.import_seakeys()


# Note: Birds are run from the other django app
def bird_distribs(request):
    pwd = os.path.abspath(os.path.dirname(__file__))
    dir = os.path.join(pwd, '..', 'data-sources', 'bird_distribs')

    bird_parent_node = models.Taxon.objects.get(name='Aves')
    species_rank = models.Rank.objects.get(name='Species')
    subspecies_rank = models.Rank.objects.get(name='Subspecies')
    birds = bird_parent_node.get_descendants().filter(rank__in=[species_rank, subspecies_rank])
    for bird in birds:
        bird_file = os.path.join(dir, bird.name.replace(' ', '_') + '.json')
        if not os.path.exists(bird_file):
            continue

        with open(bird_file) as data_file:
            distributions = json.load(data_file)

            for distribution in distributions['features']:
                polygon_points = []
                for ring in distribution['geometry']['rings'][0]:
                    polygon_points.append((ring[0], ring[1]))
                polygon_tuple = tuple(polygon_points)
                polygon = Polygon(polygon_tuple, srid=4326)
                distrib = models.GeneralDistribution(taxon=bird, distribution_polygon=polygon)
                distrib.save()


# Gets all the butterfly 'broken' criteria strings and fix them
def convert_all_criteria_strings(request):
    needs_fixing = redlist_models.Assessment.objects.filter(redlist_criteria__contains='|')

    for assessment in needs_fixing:
        try:
            assessment.redlist_criteria = convert_criteria_string(assessment.redlist_criteria)
        except IndexError:
            import pdb; pdb.set_trace()
        assessment.save()


# Used to fix the criteria string in the butterfly/sabca db imports
def convert_criteria_string(string):
    # Construct a load of nested dictionaries with all of the individual components
    cons = {}
    for item in string.split('|'):
        # B
        letter = item[0].upper()
        if letter not in cons:
            cons[letter] = {}

        # B1, sometimes you just have D with no number
        if len(item) > 1:
            number = item[1]
            if number not in cons[letter]:
                cons[letter][number] = {}

            # B1a or B1b_iii, sometimes you just have D1 with no letter
            if len(item) > 2:
                small_letter = item[2].lower()
                if small_letter not in cons[letter][number]:
                    cons[letter][number][small_letter] = []

                if '_' in item:
                    roman_numerals = item.split('_')[1]
                    if roman_numerals not in cons[letter][number][small_letter]:
                        cons[letter][number][small_letter].append(roman_numerals)

    # Following is not used, just an example of what we're constructing
    # output_example = {'A': {'2': {'a': [], 'b': []}}, 'B': {'1': {'a': [], 'b': ['i', 'ii', 'iii']}}}

    # Join those dictionaries together, we also need to do some sorting once they are lists
    letter_strings = []
    for letter, number_dict in cons.items():
        number_strings = []

        for number, small_letter_dict in number_dict.items():
            small_letter_strings = []

            for small_letter, roman_numerals_list in small_letter_dict.items():
                small_letter_string = small_letter
                if roman_numerals_list:
                    small_letter_string += '(' + ','.join(roman_numerals_list) + ')'
                small_letter_strings.append(small_letter_string)

            # small_letter_string now looks like this: 'ab(i,ii,iii)'
            number_strings.append(number + ''.join(sorted(small_letter_strings)))

        # number_strings now looks like this ['2ab(i,ii,iii)', '1a']
        letter_strings.append(letter + '+'.join(sorted(number_strings)))

    # letter_strings now looks like this ['A2ab(i,ii,iii)', 'C1a']

    return '; '.join(sorted(letter_strings))


def reptile_distribs(request):
    pwd = os.path.abspath(os.path.dirname(__file__))
    dir = os.path.join(pwd, '..', 'data-sources', 'reptile_distribs')
    df = pd.read_csv(os.path.join(dir, 'simple.csv'), encoding='latin-1')
    mapping = {'decimalLat': 'lat',
               'decimalLon': 'long',
               'institution_code': 'Institutio',
               'year_colle': 'year',
               'month_coll': 'month',
               'day_collec': 'day'}
    for index, row in df.iterrows():
        row = {k.lower(): v for k, v in row.items() if pd.notnull(v)}
        for key in mapping:
            if key in row:
                row[mapping[key]] = row[key]
                del row[key]
        pt = helpers.create_point_distribution(row)


def dragonfly_distribs(request):
    pwd = os.path.abspath(os.path.dirname(__file__))
    dir = os.path.join(pwd, '..', 'data-sources', 'dragonfly_distribs')
    df = pd.read_csv(os.path.join(dir, 'simple.csv'))
    mapping = {'decimal_latitude': 'lat',
               'decimal_longitude': 'long',
               'institution_code': 'origin_code',
               'coordinate_uncertainty_in_meters': 'precision',
               'year_collected': 'year',
               'month_collected': 'month',
               'day_collected': 'day'}
    for index, row in df.iterrows():
        row = {k.lower(): v for k, v in row.items() if pd.notnull(v)}
        for key in mapping:
            if key in row:
                row[mapping[key]] = row[key]
                del row[key]
        pt = helpers.create_point_distribution(row)


def mammal_distribs(request):
    pwd = os.path.abspath(os.path.dirname(__file__))
    dir = os.path.join(pwd, '..', 'data-sources', 'mammal_distribs')
    mapping = {'decimallatitude': 'lat',
               'decimallongitude': 'long',
               'institutioncode': 'origin_code',
               'coordinateuncertaintyinmeters': 'precision',
               'specificepithet': 'species'}
    for file in os.listdir(dir):
        df = pd.read_excel(os.path.join(dir, file))
        for index, row in df.iterrows():
            row = {k.lower(): v for k, v in row.items() if pd.notnull(v)}
            for key in mapping:
                if key in row:
                    row[mapping[key]] = row[key]
                    del row[key]
            pt = helpers.create_point_distribution(row)
            if pt:
                import pdb; pdb.set_trace()


def st_process(request):
    pwd = os.path.abspath(os.path.dirname(__file__))
    dir = os.path.join(pwd, '..', 'website', 'static')
    #dir = "C:\\projects\\fhatani\\redlist\\gis\\"


    oceans = os.path.join(dir, 'oceans.json')
    with open(oceans) as data_file:
        distributions = json.load(data_file)

    for distribution in distributions['features']:

        polygons = []
        for ring in distribution['geometry']['rings']:
            polygon_points = []
            for point in ring:
                polygon_points.append((point[0], point[1]))
            polygon_tuple = tuple(polygon_points)
            polygons.append(Polygon(polygon_tuple, srid=4326))

    # get first polygon
    polygon_union = polygons[0]

    # update list
    polygons = polygons[1:]

    # loop through list of polygons
    for poly in polygons:
        polygon_union = polygon_union.union(poly)

    points_for_deleting = models.PointDistribution.objects.filter(point__within=polygon_union)
    import pdb; pdb.set_trace()
    #points_for_deleting.delete()
    #print (points_for_deleting.query)

    #print (points_for_deleting, len(points_for_deleting))
    for points in points_for_deleting:
        print(points.point)
