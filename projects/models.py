from django.db import models
import uuid
from users.models import Profile
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.urls import reverse

class Project(models.Model):
    owner = models.ForeignKey(Profile, null=True, blank=True, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    featured_image = models.BinaryField(null=True, blank=True, editable=True)
    featured_image_content_type = models.CharField(max_length=50, null=True, blank=True)
    demo_link = models.CharField(max_length=200, null=True, blank=True)
    source_link = models.CharField(max_length=200, null=True, blank=True)
    collaborators = models.ManyToManyField(
        'users.Profile', blank=True, related_name='collaborations'
    )
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
    def is_collaborative(self):
        return self.collaborators.exists()

    @property
    def reviewers(self):
        return self.review_set.all().values_list('owner__id', flat=True)

    @property
    def voters(self):
        return self.review_set.filter(value__isnull=False).exclude(value='').values_list('owner__id', flat=True) 
    
    @property
    def imageURL(self):
        return reverse('serve-project-image', args=[str(self.id)])
    
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
    id = models.UUIDField(default=uuid.uuid4, unique=True, primary_key=True, editable=False)

    class Meta:
        unique_together = [['owner', 'project']]

    def __str__(self):
        return self.value or 'No vote'


class ProjectComment(models.Model):
    owner = models.ForeignKey(Profile, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='comments')
    body = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    id = models.UUIDField(default=uuid.uuid4, unique=True, primary_key=True, editable=False)

    class Meta:
        ordering = ['-created']

    def __str__(self):
        return f'{self.owner} on {self.project} - {self.body[:50]}'


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


class CollaborationInvite(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
    )
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='collab_invites')
    sender = models.ForeignKey('users.Profile', on_delete=models.CASCADE, related_name='sent_invites')
    recipient = models.ForeignKey('users.Profile', on_delete=models.CASCADE, related_name='received_invites')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created = models.DateTimeField(auto_now_add=True)
    id = models.UUIDField(default=uuid.uuid4, unique=True, primary_key=True, editable=False)

    class Meta:
        unique_together = [['project', 'recipient']]

    def __str__(self):
        return f"{self.sender} → {self.recipient} ({self.project.title}) [{self.status}]"