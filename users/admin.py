from django.contrib import admin
from .models import Profile, Skill, Message, Conversation

admin.site.register(Profile)
admin.site.register(Skill)
admin.site.register(Message)
admin.site.register(Conversation)