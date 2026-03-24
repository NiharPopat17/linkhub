from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from .serializers import ProjectSerializer
from projects.models import Project, Review, Tag


@api_view(['GET'])
def getRoutes(request):

    routes = [
        {'GET': '/api/projects'},
        {'GET': '/api/projects/id'},
        {'POST': '/api/projects/id/vote'},
        {'POST': '/api/users/token'},
        {'POST': '/api/users/token/refresh'},
    ]
    return Response(routes)

@api_view(['GET'])
def getProjects(request):
    projects = Project.objects.all()
    serializer = ProjectSerializer(projects, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def getProject(request, pk):
    project = get_object_or_404(Project, id=pk)
    serializer = ProjectSerializer(project, many=False)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def projectVote(request, pk):
    project = get_object_or_404(Project, id=pk)
    user = request.user.profile
    data = request.data

    review, created = Review.objects.get_or_create(
        owner=user,
        project=project,
    )

    review.value = data['value']
    review.save()
    project.getVoteCount()

    serializer = ProjectSerializer(project, many=False)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def predictNextWord(request):
    text = request.data.get('text', '')
    from ml.next_word import predict_next_words
    suggestion = predict_next_words(text)
    return Response({'suggestion': suggestion})


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def removeTag(request):
    tagId = request.data.get('tagId')
    projectId = request.data.get('projectId')
    if not tagId or not projectId:
        return Response({'error': 'tagId and projectId are required'}, status=400)
    project = get_object_or_404(Project, id=projectId)
    tag = get_object_or_404(Tag, id=tagId)
    project.tags.remove(tag)
    return Response('Tag was deleted')


@api_view(['GET'])
@authentication_classes([SessionAuthentication])
def searchUsers(request):
    """Return up to 8 matching usernames for autocomplete."""
    query = request.GET.get('q', '').strip()
    if len(query) < 1:
        return Response([])
    from users.models import Profile
    profiles = Profile.objects.filter(
        user__username__icontains=query
    ).exclude(user__isnull=True).select_related('user')
    if request.user.is_authenticated:
        profiles = profiles.exclude(user=request.user)
    profiles = profiles[:8]
    results = [
        {
            'id': str(p.id),
            'username': p.user.username,
            'name': p.name or p.user.username,
            'image': p.imageURL,
        }
        for p in profiles
    ]
    return Response(results)