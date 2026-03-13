from django.core.management.base import BaseCommand
from users.models import Profile
from projects.models import Project
from ml.semantic_search import get_embedding


class Command(BaseCommand):
    help = 'Batch compute embeddings for all Profile and Project records'

    def handle(self, *args, **kwargs):
        self.stdout.write('Computing Profile embeddings...')
        for profile in Profile.objects.filter(embedding__isnull=True):
            skills = ' '.join(profile.skill_set.values_list('name', flat=True))
            text = f"{profile.name or ''} {profile.short_intro or ''} {profile.bio or ''} {skills}"
            Profile.objects.filter(pk=profile.pk).update(embedding=get_embedding(text))
            self.stdout.write(f'  Profile: {profile.username}')

        self.stdout.write('Computing Project embeddings...')
        for project in Project.objects.filter(embedding__isnull=True):
            tags = ' '.join(project.tags.values_list('name', flat=True))
            text = f"{project.title} {project.description or ''} {tags}"
            Project.objects.filter(pk=project.pk).update(embedding=get_embedding(text))
            self.stdout.write(f'  Project: {project.title}')

        self.stdout.write(self.style.SUCCESS('Done.'))
