from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Profile
from django.core.mail import send_mail
from django.conf import settings

def createProfile(sender, instance, created, **kwargs):
    print('Profile signal triggered')
    if created:
        user = instance
        profile = Profile.objects.create(
            user=user,
            username=user.username,
            name=user.first_name,
            email=user.email,
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
        except:
            print('Email failed to send...')

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


@receiver(post_save, sender=Profile)
def update_profile_embedding(sender, instance, created, update_fields, **kwargs):
    if update_fields and 'embedding' in update_fields:
        return
    try:
        from ml.semantic_search import get_embedding
        skills = ' '.join(instance.skill_set.values_list('name', flat=True))
        text = f"{instance.name or ''} {instance.short_intro or ''} {instance.bio or ''} {skills}"
        Profile.objects.filter(pk=instance.pk).update(embedding=get_embedding(text))
    except Exception:
        pass