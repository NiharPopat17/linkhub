import os
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Profile, Skill
from django.core.mail import send_mail
from django.conf import settings

def _get_default_image_data():
    """Read the default avatar PNG and return (bytes, content_type)."""
    path = os.path.join(settings.BASE_DIR, 'static', 'images', 'user-default.png')
    try:
        with open(path, 'rb') as f:
            return f.read(), 'image/png'
    except FileNotFoundError:
        return None, None


def createProfile(sender, instance, created, **kwargs):
    if created:
        user = instance
        img_data, img_ct = _get_default_image_data()
        profile = Profile.objects.create(
            user=user,
            username=user.username,
            name=user.first_name,
            email=user.email,
            profile_image=img_data,
            profile_image_content_type=img_ct,
        )

        subject = 'Welcome to LinkHub'
        message = 'We are glad you are here!'

        try:
            send_mail(
                subject,
                message,
                settings.EMAIL_HOST_USER,
                [profile.email],
                fail_silently=False,
            )
        except Exception:
            pass

def updateUser(sender, instance, created, **kwargs):
    profile = instance
    user = profile.user
    if created == False:
        user.first_name = profile.name or ''
        user.email = profile.email or ''
        if profile.username:
            user.username = profile.username
        user.save()

def deleteUser(sender, instance, **kwargs):
    try:
        user = instance.user
        user.delete() 
    except:
        pass

post_save.connect(createProfile, sender=User)
post_save.connect(updateUser, sender=Profile)
post_delete.connect(deleteUser, sender=Profile)


def _recompute_profile_embedding(profile):
    try:
        from ml.semantic_search import get_embedding
        skills = ' '.join(profile.skill_set.values_list('name', flat=True))
        text = f"{profile.name or ''} {profile.short_intro or ''} {profile.bio or ''} {skills}"
        Profile.objects.filter(pk=profile.pk).update(embedding=get_embedding(text))
    except Exception:
        pass


@receiver(post_save, sender=Profile)
def update_profile_embedding(sender, instance, created, update_fields, **kwargs):
    if update_fields and 'embedding' in update_fields:
        return
    _recompute_profile_embedding(instance)


@receiver(post_save, sender=Skill)
@receiver(post_delete, sender=Skill)
def update_embedding_on_skill_change(sender, instance, **kwargs):
    if instance.owner:
        _recompute_profile_embedding(instance.owner)