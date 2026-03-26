from rest_framework import serializers
from projects.models import Project, Tag,Review
from users.models import Profile


class ProfileSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        exclude = ['profile_image']

    def get_image_url(self, obj):
        return obj.imageURL

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'  

class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = '__all__'  

class ProjectSerializer(serializers.ModelSerializer):
    owner = ProfileSerializer(many=False)
    tags = TagSerializer(many=True)
    reviews = serializers.SerializerMethodField(method_name='get_reviews')
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Project
        exclude = ['featured_image']

    def get_reviews(self, obj):
        reviews = obj.review_set.all()
        serializer = ReviewSerializer(reviews, many=True)
        return serializer.data

    def get_image_url(self, obj):
        return obj.imageURL


