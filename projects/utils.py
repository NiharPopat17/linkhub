from django.db.models import Q
from .models import Project, Tag
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage

def paginateProjects(request, projects, results):

    page = request.GET.get('page')
    paginator = Paginator(projects, results)
    try:
        projects = paginator.page(page)
    except PageNotAnInteger:
        page = 1
        projects = paginator.page(page)
    except EmptyPage:
        page = paginator.num_pages
        projects = paginator.page(page)

    leftIndex = (int(page) - 4)

    if leftIndex < 1:
        leftIndex = 1

    rightIndex = (int(page) + 5)

    if rightIndex > paginator.num_pages:
        rightIndex = paginator.num_pages + 1

    custom_range = range(leftIndex, rightIndex)

    return custom_range, projects


def searchProjects(request):
    search_query = ''
    if request.GET.get('search_query'):
        search_query = request.GET.get('search_query')

    tags = Tag.objects.filter(name__icontains=search_query)

    keyword_matches = Project.objects.distinct().filter(
        Q(title__icontains=search_query) |
        Q(description__icontains=search_query) |
        Q(owner__name__icontains=search_query) |
        Q(tags__in=tags)
    )

    if search_query:
        projects_with_embeddings = Project.objects.filter(embedding__isnull=False)
        if projects_with_embeddings.exists():
            try:
                from ml.semantic_search import semantic_search
                # Semantic search across ALL projects that have embeddings
                semantic_results = semantic_search(search_query, list(projects_with_embeddings))
                # Append any keyword-only matches (no embedding) that aren't already included
                seen_pks = {p.pk for p in semantic_results}
                for p in keyword_matches.filter(embedding__isnull=True):
                    if p.pk not in seen_pks:
                        semantic_results.append(p)
                return semantic_results, search_query
            except Exception:
                pass

    return keyword_matches, search_query