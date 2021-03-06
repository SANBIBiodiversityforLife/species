from rest_framework import serializers
from taxa.models import Taxon, Info, CommonName, GeneralDistribution, Description, PointDistribution
from biblio.serializers import ReferenceDOISerializer
from rest_framework_gis.serializers import GeoFeatureModelSerializer

class ChildrenInfoField(serializers.RelatedField):
    """Used to return count, primary key, name and rank for all child nodes of a taxon, rather than just their pk"""
    def to_representation(self, value):
        child_count = Taxon.objects.get(id=value.id).get_children().count()
        return {'count': child_count, 'id': value.id, 'name': value.name, 'rank': value.rank.id, 'parent_id': value.id }


class ChildCountField(serializers.RelatedField):
    """Used to return count, primary key, name and rank for all child nodes of a taxon, rather than just their pk"""
    def to_representation(self, value):
        child_count = Taxon.objects.get(id=value).get_children().count()
        return child_count


class StringAndKeyField(serializers.RelatedField):
    """Used by jstree to depict rank as well as use rank id in CSS"""
    def to_representation(self, value):
        return {'id': value.id, 'name': value.name}


class TaxonBasicSerializerWithRank(serializers.ModelSerializer):
    parent = serializers.PrimaryKeyRelatedField(read_only=True)
    rank = StringAndKeyField(read_only=True)
    child_count = ChildCountField(read_only=True, source='id')
    get_latest_assessment = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Taxon
        fields = ('id', 'name', 'get_full_name', 'parent', 'rank', 'child_count', 'get_top_common_name', 'get_latest_assessment')


class TaxonChildrenSerializer(serializers.ModelSerializer):
    children = ChildrenInfoField(required=False, many=True, read_only=True)
    rank = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Taxon
        fields = ('id', 'name', 'rank', 'children')


class CommonNameSerializer(serializers.ModelSerializer):
    reference = ReferenceDOISerializer()
    language = serializers.StringRelatedField()

    class Meta:
        model = CommonName
        fields = ('name', 'language', 'reference')


class ArrayChoiceFieldSerializer(serializers.ListSerializer):
    def to_representation(self, value):
        return self.child.choices[value]


class InfoSerializer(serializers.ModelSerializer):
    habitats = serializers.StringRelatedField(read_only=True, many=True)
    reproductive_type = ArrayChoiceFieldSerializer(read_only=True, many=True,
                        child=serializers.ChoiceField(allow_blank=True, allow_null=True,
                        choices=Info.REPRODUCTIVE_TYPE_CHOICES, label='Congregatory', required=False))
    congregatory = ArrayChoiceFieldSerializer(read_only=True, many=True,
                        child=serializers.ChoiceField(allow_blank=True, allow_null=True,
                        choices=Info.CONGREGATORY_CHOICES, label='Congregatory', required=False))

    class Meta:
        model = Info
        fields = ('morphology',
                  'diagnostics',
                  'trophic',
                  'movement',
                  'migration_patterns',
                  'congregatory',
                  'reproduction',
                  'reproductive_type',
                  'habitat_narrative',
                  'habitats',
                  'altitude_or_depth_range',
                  'maturity_size_female',
                  'maturity_size_male',
                  'max_size',
                  'birth_size',
                  'size_units',
                  'generational_length',
                  'generational_length_narrative',
                  'maturity_age_female',
                  'maturity_age_male',
                  'longevity',
                  'reproductive_age',
                  'gestation_time',
                  'reproductive_periodicity',
                  'average_fecundity',
                  'natural_mortality',
                  'age_units')


class TaxonInfoSerializer(serializers.ModelSerializer):
    info = InfoSerializer()

    class Meta:
        model = Taxon
        fields = ('id', 'taxonomic_notes', 'info')


class DistributionSerializer(GeoFeatureModelSerializer):
    residency_status = serializers.CharField(source='get_residency_status_display')
    level = serializers.CharField(source='get_level_display')
    reference = serializers.StringRelatedField()

    class Meta:
        model = GeneralDistribution
        geo_field = "distribution_polygon"
        fields = ('date', 'residency_status', 'level', 'reference', 'description')


class PointSerializer(GeoFeatureModelSerializer):
    collector = serializers.StringRelatedField()

    class Meta:
        model = PointDistribution
        geo_field = "point"
        fields = ('date', 'collector', 'precision_m', 'origin_code')


class RankSerializer(serializers.ModelSerializer):
    class Meta:
        model = Taxon
        fields = ('id', 'name')


class CommonNameWriteSerializer(serializers.ModelSerializer):
    # language = serializers.PrimaryKeyRelatedField(queryset=Language.objects.all())

    class Meta:
        model = CommonName
        fields = ('name', 'language', 'taxon')


class TaxonWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Taxon
        fields = ('id', 'name', 'rank', 'parent', 'taxonomic_notes')


class DescriptionWriteSerializer(serializers.ModelSerializer):
    taxon = serializers.PrimaryKeyRelatedField(queryset=Taxon.objects.all())

    class Meta:
        model = Description
        fields = ('taxon', 'reference')


class InfoWriteSerializer(serializers.ModelSerializer):
    taxon = serializers.PrimaryKeyRelatedField(queryset=Taxon.objects.all())

    class Meta:
        model = Info
        fields = ('taxon', 'trophic', 'diagnostics', 'morphology', 'habitat_narrative', 'habitats')