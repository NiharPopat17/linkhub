from django.db.models import Q
from .models import Profile, Skill
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage

def paginateProfiles(request, profiles, results):
    page = request.GET.get('page')
    paginator = Paginator(profiles, results)

    try:
        profiles = paginator.page(page)
    except PageNotAnInteger:
        page = 1
        profiles = paginator.page(page)
    except EmptyPage:
        page = paginator.num_pages
        profiles = paginator.page(page)

    leftIndex = (int(page) - 4)

    if leftIndex < 1:
        leftIndex = 1

    rightIndex = (int(page) + 5)

    if rightIndex > paginator.num_pages:
        rightIndex = paginator.num_pages + 1

    custom_range = range(leftIndex, rightIndex)

    return custom_range, profiles

def searchProfiles(request):
    search_query = ''

    if request.GET.get('search_query'):
        search_query = request.GET.get('search_query')

    skills = Skill.objects.filter(name__icontains=search_query)

    keyword_matches = Profile.objects.distinct().filter(
        Q(name__icontains=search_query) |
        Q(username__icontains=search_query) |
        Q(short_intro__icontains=search_query) |
        Q(skill__in=skills)
    )

    if search_query:
        profiles_with_embeddings = Profile.objects.filter(embedding__isnull=False)
        if profiles_with_embeddings.exists():
            try:
                from ml.semantic_search import semantic_search
                # Semantic search across ALL profiles that have embeddings
                semantic_results = semantic_search(search_query, list(profiles_with_embeddings))
                # Append any keyword-only matches (no embedding) that aren't already included
                seen_pks = {p.pk for p in semantic_results}
                for p in keyword_matches.filter(embedding__isnull=True):
                    if p.pk not in seen_pks:
                        semantic_results.append(p)
                return semantic_results, search_query
            except Exception:
                pass

    return keyword_matches, search_query