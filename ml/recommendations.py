import numpy as np
from django.db.models import Count
from ml.semantic_search import cosine_similarity


def get_developer_recommendations(profile, limit=50):
    from users.models import Profile
    following_ids = list(profile.following.values_list('id', flat=True))
    exclude_ids = following_ids + [profile.id]

    no_embedding = list(
        Profile.objects.exclude(id__in=exclude_ids)
        .filter(embedding__isnull=True)
        .annotate(followers_count=Count('followers'))
        .order_by('-followers_count')
    )

    my_projects = list(profile.project_set.filter(embedding__isnull=False))
    if not my_projects:
        with_embedding = list(
            Profile.objects.exclude(id__in=exclude_ids)
            .filter(embedding__isnull=False)
            .annotate(followers_count=Count('followers'))
            .order_by('-followers_count')
        )
        return (with_embedding + no_embedding)[:limit]

    my_vec = np.mean([p.embedding for p in my_projects], axis=0)
    candidates = Profile.objects.exclude(id__in=exclude_ids).filter(embedding__isnull=False)
    scored = sorted(
        candidates,
        key=lambda p: cosine_similarity(my_vec, p.embedding),
        reverse=True,
    )
    return (scored + no_embedding)[:limit]


def get_project_recommendations(profile, limit=50):
    from projects.models import Project, Review
    following_ids = list(profile.following.values_list('id', flat=True))

    upvoted_ids = list(
        Review.objects.filter(owner=profile, value='up').values_list('project_id', flat=True)
    )

    # Exclude: own projects, followed users' projects, already-upvoted projects
    base_exclude = (
        Project.objects
        .exclude(owner=profile)
        .exclude(owner__id__in=following_ids)
        .exclude(id__in=upvoted_ids)
    )

    no_embedding = list(
        base_exclude.filter(embedding__isnull=True)
        .order_by('-vote_ratio', '-vote_total')
    )

    upvoted_with_emb = list(Project.objects.filter(id__in=upvoted_ids, embedding__isnull=False))
    if not upvoted_with_emb:
        with_embedding = list(
            base_exclude.filter(embedding__isnull=False)
            .order_by('-vote_ratio', '-vote_total')
        )
        return (with_embedding + no_embedding)[:limit]

    taste_vec = np.mean([p.embedding for p in upvoted_with_emb], axis=0)
    candidates = base_exclude.filter(embedding__isnull=False)
    scored = sorted(
        candidates,
        key=lambda p: cosine_similarity(taste_vec, p.embedding),
        reverse=True,
    )
    return (scored + no_embedding)[:limit]
