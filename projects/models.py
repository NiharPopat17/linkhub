from django.db import models
import uuid
from users.models import Profile
from django.templatetags.static import static
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

class Project(models.Model):
    owner = models.ForeignKey(Profile, null=True, blank=True, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    featured_image = models.ImageField(null=True, blank=True, default="default.jpg")
    demo_link = models.CharField(max_length=200, null=True, blank=True)
    source_link = models.CharField(max_length=200, null=True, blank=True)
    tags = models.ManyToManyField('Tag', blank=True)
    vote_total = models.IntegerField(default=0, null=True, blank=True)
    vote_ratio = models.IntegerField(default=0, null=True, blank=True)
    embedding = models.JSONField(null=True, blank=True)
    views = models.IntegerField(default=0)
    created = models.DateTimeField(auto_now_add=True)
    id = models.UUIDField(default=uuid.uuid4, unique=True, primary_key=True,editable=False)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-created']

    @property
    def reviewers(self):
        queryset = self.review_set.all().values_list('owner__id', flat=True)
        return queryset 
    
    @property
    def imageURL(self):
        try:
            url = self.featured_image.url
        except Exception:
            url = static('images/default.jpg')
        return url
    
    def getVoteCount(self):
        reviews = self.review_set.all()
        upVotes = reviews.filter(value='up').count()
        totalVotes = reviews.count()

        ratio = (upVotes / totalVotes) * 100 if totalVotes > 0 else 0
        self.vote_total = totalVotes
        self.vote_ratio = ratio

        self.save(update_fields=['vote_total', 'vote_ratio'])

class Review(models.Model):
    VOTE_TYPE = (
        ('up', 'Up Vote'),
        ('down', 'Down Vote'),
    )
    owner = models.ForeignKey(Profile, on_delete=models.CASCADE, null=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    body = models.TextField(null=True, blank=True)
    value = models.CharField(max_length=200, null=True, blank=True, choices=VOTE_TYPE)
    created = models.DateTimeField(auto_now_add=True)
    id = models.UUIDField(default=uuid.uuid4, unique=True, primary_key=True,editable=False)

    class Meta:
        unique_together = [['owner', 'project']]

    def __str__(self):
        return self.value


@receiver(post_save, sender=Review)
@receiver(post_delete, sender=Review)
def update_project_vote_count(sender, instance, **kwargs):
    instance.project.getVoteCount()


class Tag(models.Model):
    name = models.CharField(max_length=200)
    created = models.DateTimeField(auto_now_add=True)
    id = models.UUIDField(default=uuid.uuid4, unique=True, primary_key=True,editable=False)

    def __str__(self):
        return self.name


@receiver(post_save, sender=Project)
def update_project_embedding(sender, instance, created, update_fields, **kwargs):
    if update_fields and set(update_fields) <= {'embedding', 'vote_total', 'vote_ratio'}:
        return
    try:
        from ml.semantic_search import get_embedding
        tags = ' '.join(instance.tags.values_list('name', flat=True))
        text = f"{instance.title} {instance.description or ''} {tags}"
        Project.objects.filter(pk=instance.pk).update(embedding=get_embedding(text))
    except Exception:
        pass