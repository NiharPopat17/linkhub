from django.shortcuts import render,redirect,get_object_or_404
from django.contrib.auth import authenticate,login,logout
from .models import Profile,Skill,Message,Conversation
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from .forms import CustomUserCreationForm
from .forms import ProfileForm
from .forms import SkillForm
from .forms import MessageForm
from django.db.models import Q, F, Count
from .utils import searchProfiles, paginateProfiles
from projects.models import Project

def loginUser(request):
    if request.user.is_authenticated:
        return redirect('profiles')
    if request.method == 'POST':
        username = request.POST.get('username').lower()
        password = request.POST.get('password')

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            messages.error(request, "Username does not exist")
            return render(request, 'users/login_register.html')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect(request.GET.get('next', 'profiles'))
        else:
            messages.error(request, "Password is incorrect")
    return render(request, 'users/login_register.html')

def logoutUser(request):
    logout(request)
    messages.info(request,"Logged out successfully")
    return redirect('login')

def registerUser(request):
    page = 'register'
    form = CustomUserCreationForm()

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = user.username.lower()
            user.save()

            messages.success(request, 'User account was created!')
            login(request,user)
            return redirect('edit-account')
        else:
            messages.error(request,'An error has occured during registration')

    context = {'page': page, 'form': form}
    return render(request, 'users/login_register.html', context)

def profiles(request):
    profiles, search_query = searchProfiles(request)

    if search_query:
        # Search active — show results, excluding the logged-in user
        if request.user.is_authenticated:
            if hasattr(profiles, 'exclude'):
                profiles = profiles.exclude(user=request.user)
            else:
                profiles = [p for p in profiles if p.user != request.user]
    else:
        # No search — show recommendations as the main listing
        if request.user.is_authenticated:
            try:
                from ml.recommendations import get_developer_recommendations
                profiles = get_developer_recommendations(request.user.profile, limit=50)
            except Exception:
                profiles = Profile.objects.exclude(user=request.user).annotate(
                    followers_count=Count('followers')
                ).order_by('-followers_count')
        else:
            profiles = Profile.objects.annotate(
                followers_count=Count('followers')
            ).order_by('-followers_count')

    custom_range, profiles = paginateProfiles(request, profiles, 6)
    context = {
        'profiles': profiles,
        'search_query': search_query,
        'custom_range': custom_range,
    }
    return render(request, 'users/profiles.html', context)

def userProfile(request,pk):
    profile = Profile.objects.get(id=pk)
    is_own_profile = request.user.is_authenticated and str(request.user.profile.id) == str(pk)
    if not is_own_profile:
        viewed_profiles = request.session.get('viewed_profiles', [])
        if str(pk) not in viewed_profiles:
            Profile.objects.filter(pk=pk).update(views=F('views') + 1)
            viewed_profiles.append(str(pk))
            request.session['viewed_profiles'] = viewed_profiles
        profile.refresh_from_db()
    show_views = not is_own_profile
    topSkills = profile.skill_set.exclude(description__exact="")
    otherSkills = profile.skill_set.filter(description="")

    is_following = False
    if request.user.is_authenticated:
        is_following = request.user.profile.following.filter(id=profile.id).exists()

    context = {
        'profile': profile,
        'topSkills': topSkills,
        'otherSkills': otherSkills,
        'is_following': is_following,
        'show_views': show_views,
    }
    return render(request, 'users/user-profile.html', context)

@login_required(login_url='login')
def userAccount(request):
    profile = request.user.profile
    skills = profile.skill_set.all()
    projects = profile.project_set.all()
    following_count = profile.following.count()
    context = {
        'profile': profile,
        'skills': skills,
        'projects': projects,
        'following_count': following_count,
    }
    return render(request, 'users/account.html',context)

@login_required(login_url='login')
def editAccount(request):
    profile = request.user.profile
    form = ProfileForm(instance=profile)
    if request.method == 'POST':
        form = ProfileForm(request.POST,request.FILES,instance=profile)
        if form.is_valid():
            form.save()
            return redirect('account')
    context = {'form': form}
    return render(request, 'users/profile_form.html',context)

@login_required(login_url='login')
def createSkill(request):
    profile = request.user.profile
    form = SkillForm()
    if request.method == 'POST':
        form = SkillForm(request.POST)
        if form.is_valid():
            skill = form.save(commit=False)
            skill.owner = profile
            skill.save()
            messages.success(request, 'Skill was added successfully!')
            return redirect('account')  
    context = {'form': form}
    return render(request, 'users/skill_form.html', context)

@login_required(login_url='login')
def updateSkill(request, pk):
    profile = request.user.profile
    skill = get_object_or_404(Skill, id=pk, owner=profile)
    form = SkillForm(instance=skill)

    if request.method == 'POST':
        form = SkillForm(request.POST, instance=skill)
        if form.is_valid():
            form.save()
            messages.success(request, 'Skill was updated successfully!')
            return redirect('account')

    context = {'form': form}
    return render(request, 'users/skill_form.html', context)


@login_required(login_url='login')
def deleteSkill(request, pk):
    profile = request.user.profile
    skill = get_object_or_404(Skill, id=pk, owner=profile)
    if request.method == 'POST':
        skill.delete()
        messages.success(request, 'Skill was deleted successfully!')
        return redirect('account')

    context = {'object': skill}
    return render(request, 'delete_template.html', context)


@login_required(login_url='login')
def inbox(request):
    profile = request.user.profile
    convs = profile.conversations.prefetch_related('participants', 'message_set').all()

    conv_data = []
    for conv in convs:
        other = conv.participants.exclude(id=profile.id).first()
        last_msg = conv.message_set.order_by('-created').first()
        unread_count = conv.message_set.filter(recipient=profile, is_read=False).count()
        conv_data.append({
            'conv': conv,
            'other': other,
            'last_msg': last_msg,
            'unread_count': unread_count,
        })

    conv_data.sort(
        key=lambda x: x['last_msg'].created if x['last_msg'] else x['conv'].created,
        reverse=True,
    )

    total_unread = Message.objects.filter(recipient=profile, is_read=False).count()
    context = {'conv_data': conv_data, 'total_unread': total_unread, 'profile': profile}
    return render(request, 'users/inbox.html', context)


@login_required(login_url='login')
def viewMessage(request, pk):
    profile = request.user.profile
    message = profile.messages.get(id=pk)
    if message.is_read == False:
        message.is_read = True
        message.save()
    context = {'message': message}
    return render(request, 'users/message.html', context)


@login_required(login_url='login')
def conversationThread(request, pk):
    profile = request.user.profile
    try:
        conv = Conversation.objects.get(id=pk)
    except Conversation.DoesNotExist:
        messages.error(request, "Conversation not found.")
        return redirect('inbox')

    if not conv.participants.filter(id=profile.id).exists():
        messages.error(request, "You are not part of this conversation.")
        return redirect('inbox')

    conv.message_set.filter(recipient=profile, is_read=False).update(is_read=True)

    thread_messages = conv.message_set.order_by('created')
    other = conv.participants.exclude(id=profile.id).first()

    if request.method == 'POST':
        body = request.POST.get('body', '').strip()
        if body:
            Message.objects.create(
                sender=profile,
                recipient=other,
                conversation=conv,
                name=profile.name,
                email=profile.email,
                subject='',
                body=body,
                is_read=False,
            )
            conv.save()
            return redirect('conversation', pk=conv.id)

    context = {
        'conv': conv,
        'thread_messages': thread_messages,
        'other': other,
        'profile': profile,
    }
    return render(request, 'users/conversation.html', context)

@login_required(login_url='login')
def followUser(request, pk):
    target_profile = Profile.objects.get(id=pk)
    my_profile = request.user.profile

    if target_profile == my_profile:
        messages.error(request, "You cannot follow yourself.")
        return redirect('user-profile', pk=pk)

    if my_profile.following.filter(id=target_profile.id).exists():
        my_profile.following.remove(target_profile)
        messages.info(request, f"You unfollowed {target_profile.name}.")
    else:
        my_profile.following.add(target_profile)
        messages.success(request, f"You are now following {target_profile.name}.")

    return redirect('user-profile', pk=pk)


@login_required(login_url='login')
def followingList(request):
    profile = request.user.profile
    following = profile.following.all()
    context = {'following': following}
    return render(request, 'users/following.html', context)


@login_required(login_url='login')
def toggleBookmark(request, pk):
    project = Project.objects.get(id=pk)
    profile = request.user.profile
    if profile.bookmarks.filter(id=pk).exists():
        profile.bookmarks.remove(project)
        messages.info(request, 'Bookmark removed.')
    else:
        if project.owner == profile:
            messages.error(request, "You cannot bookmark your own project.")
            return redirect('project', pk=pk)
        profile.bookmarks.add(project)
        messages.success(request, 'Project bookmarked!')
    return redirect('project', pk=pk)


def createMessage(request, pk):
    recipient = Profile.objects.get(id=pk)
    form = MessageForm()
    try:
        sender = request.user.profile
    except Exception:
        sender = None

    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.sender = sender
            message.recipient = recipient

            if sender:
                message.name = sender.name
                message.email = sender.email

                existing = Conversation.objects.filter(
                    participants=sender).filter(participants=recipient)
                if existing.exists():
                    conv = existing.first()
                else:
                    conv = Conversation.objects.create()
                    conv.participants.add(sender, recipient)

                message.conversation = conv
                message.save()
                conv.save()

                messages.success(request, 'Your message was successfully sent!')
                return redirect('conversation', pk=conv.id)
            else:
                message.save()
                messages.success(request, 'Your message was successfully sent!')
                return redirect('user-profile', pk=recipient.id)

    context = {'recipient': recipient, 'form': form}
    return render(request, 'users/message_form.html', context)