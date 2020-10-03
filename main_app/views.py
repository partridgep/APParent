from django.shortcuts import render, redirect
from .models import Child, Profile, Picture, Goal, Report_card, Daily_report, Availability_event, Meeting
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from .forms import ParentSignUpForm, NotParentSignUpForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from datetime import datetime, date, timedelta
import calendar
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
import uuid
import boto3
from django.utils.timezone import get_current_timezone

# S3_BASE_URL = 'https://s3-us-west-1.amazonaws.com/'
# BUCKET = 'seir-apparent'
# S3_BASE_URL = "https://pp-apparent.s3.amazonaws.com/"
# BUCKET = 'pp-apparent'
S3_BASE_URL = "https://hn-apparent.s3.us-east-2.amazonaws.com/"
BUCKET = "hn-apparent"

RATING = (('1', 'Good job'), ('2', 'Need work'), ('3', 'Bad'))

TRACKER = (('1', 'Completed'), ('2', 'On track'), ('3','Behind schedule'))
# HELPER FUNCTION

def generate_username(email):
    username = email.split('@')[0]
    try:
      user_with_existing_username = User.objects.get(username = username)
      print(f'user with existing username = {user_with_existing_username}')
      if user_with_existing_username:
        username += '1'
    except:
      pass
    return username

def invite_users(child, request, is_parent):
    child_name = f'{child.first_name} {child.last_name}'
    if is_parent:
        to_get = "coparents"
    else:
        to_get = "professionals"
    # get string with all emails
    emailStr = request.POST.get(to_get)
    # separate emails
    emails = emailStr.split(", ")
    # find ALL users in database
    users_already_signed_up = User.objects.all()
    # see if any match the list of emails
    found_users = User.objects.filter(email__in = emails)

    for user in found_users:
        # send invite email to all found users
        msg_plain = render_to_string('emails/added_to_child.txt', {'child_name': child_name})
        msg_html = render_to_string('emails/added_to_child.html', {'child_name': child_name})
        send_mail(
        f'APParent: You\'ve been added to {child_name}',
        msg_plain,
        settings.EMAIL_HOST_USER,
        [f'{user.email}'],
        html_message=msg_html,
        fail_silently=False,
        )
        # add user to child
        user_object = User.objects.get(email=user.email)
        child.profile_set.add(user_object.profile)
        child.save()
        # finally remove email from list of emails
        emails.remove(user.email)

    # remaining emails will be new users
    for email in emails:
        # create new user
        random_password = User.objects.make_random_password()
        generated_username = generate_username(email)
        new_user = User.objects.create_user(generated_username, email, random_password)
        new_user.save()
        new_user.profile.is_parent = is_parent
        new_user.save()
        # send invite email
        msg_plain = render_to_string('emails/new_user_email.txt', {'child_name': child_name, 'username': generated_username, 'password': random_password})
        msg_html = render_to_string('emails/new_user_email.html', {'child_name': child_name, 'username': generated_username, 'password': random_password})
        send_mail(
        f'APParent: You\'ve been invited to {child_name}',
        msg_plain,
        settings.EMAIL_HOST_USER,
        [f'{email}'],
        html_message=msg_html,
        fail_silently=False,
        )
        # add new user to child
        new_user_object = User.objects.get(email=email)
        child.profile_set.add(new_user_object.profile)
        child.save()


#VIEWS

def home(request):
    # redirect to children index on initial load
    # if user is not logged in, they will be redirected to login page
    return redirect('index')

def parent_signup(request):
    error_message = ''

    # if submitting the form
    if request.method == 'POST':
        # submit the parent form
        form = ParentSignUpForm(request.POST)

        # authenticate and login new user if valid
        if form.is_valid():
            user = form.save()
            user.refresh_from_db()
            user.profile.is_parent = True
            user.profile.relationship = form.cleaned_data.get('relationship')
            user.profile.first_name = form.cleaned_data.get('first_name')
            user.profile.last_name = form.cleaned_data.get('last_name')
            user.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=user.username, password=raw_password)
            login(request, user)
            # redirect to children login page
            return redirect('index')
        else:
            error_message = 'Invalid sign up, try again!'
    
    # present form
    form = ParentSignUpForm()
    # provide context for rendering page
    context = {'form': form, 'error_message': error_message}
    return render(request, 'registration/parent_signup.html', context)



def nonparent_signup(request):
    error_message = ''
    # if submitting the form
    if request.method == 'POST':
        # submit the parent form
        form = NotParentSignUpForm(request.POST)
        # authenticate and login new user if valid
        if form.is_valid():
            user = form.save()
            user.refresh_from_db()
            user.profile.is_parent = False
            user.profile.relationship = form.cleaned_data.get('relationship')
            user.profile.organization = form.cleaned_data.get('organization')
            user.profile.first_name = form.cleaned_data.get('first_name')
            user.profile.last_name = form.cleaned_data.get('last_name')
            user.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=user.username, password=raw_password)
            login(request, user)
            # redirect to children login page
            return redirect('index')
        else:
            error_message = 'Invalid sign up, try again!'
    
    # present form
    form = NotParentSignUpForm()
    # provide context for rendering page
    context = {'form': form, 'error_message': error_message}
    return render(request, 'registration/nonparent_signup.html', context)

def register_user(request):
    #if submitting form
    if request.method == "POST":
        # check if checkbox is checked
        parent_checked = request.POST.get('parent_check')
        # if so, user is parent
        if parent_checked == 'on':
            #redirect to signup form
            return redirect('parent_signup')
            is_parent = 1
        else:
            return redirect('nonparent_signup')
            is_parent = 0


    return render(request, 'register_user.html')

@login_required
def children_index(request):
    user = request.user
    return render(request, 'children/index.html')

@login_required
def add_child(request):
    user = request.user

    if request.method == "POST":
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        date_of_birth = request.POST.get("date_of_birth")
        notes = request.POST.get("notes")
        child = Child(first_name=first_name, last_name=last_name, date_of_birth=date_of_birth, notes=notes)
        child.save()

        child.profile_set.add(user.profile)
        child.save()
        print(child)
        return redirect('child_detail', child_id=child.id)
    
    return render(request, 'children/add.html')

@login_required
def add_picture(request, child_id):
    picture_file = request.FILES.get('picture-file', None)
    
    if picture_file:
        s3 = boto3.client('s3')
        key = uuid.uuid4().hex[:6] + picture_file.name[picture_file.name.rfind('.'):]
        try:
            s3.upload_fileobj(picture_file, BUCKET, key)
            url = f"{S3_BASE_URL}{key}"
            picture = Picture(url=url, child_id=child_id)
            picture.save()
        except:
            print('An error occurred uploading file to S3')
    return redirect('child_detail', child_id=child_id)

def change_picture(request, picture_id, child_id):
    picture_file = request.FILES.get('picture-file', None)
    picture = Picture.objects.get(id=picture_id)
    picture.delete()
    if picture_file:
        s3 = boto3.client('s3')
        key = uuid.uuid4().hex[:6] + picture_file.name[picture_file.name.rfind('.'):]
        try:
            s3.upload_fileobj(picture_file, BUCKET, key)
            url = f"{S3_BASE_URL}{key}"
            picture = Picture(url=url, child_id=child_id)
            picture.save()
        except:
            print('An error occurred uploading file to S3')
    return redirect('child_detail', child_id=child_id)

@login_required
def child_detail(request, child_id):
    child = Child.objects.get(id=child_id)
    current_user = request.user
    picture = child.picture_set.all()
    if len(picture):
        picture = picture[0]
    teammates = child.profile_set.all()
    other_parents = []
    professionals = []

    for teammate in teammates:
        if teammate.is_parent and teammate.user.id != current_user.profile.user.id:
            other_parents.append(teammate)
        elif teammate.is_parent == False and teammate.user.id != current_user.profile.user.id:
            professionals.append(teammate)

    return render(request, 'children/detail.html', {
        'child': child,
        'other_parents': other_parents,
        'professionals': professionals,
        'current_user': current_user,
        'picture' : picture,
    })

@login_required
def child_summary(request, child_id):
    child = Child.objects.get(id=child_id)
    does_have_teammates = child.profile_set.all().count() > 1
    current_user = request.user
    max_summaries = 2
    today = date.today()
    one_week_ago = today - timedelta(days = 7)
    created_meetings = current_user.meeting_invitee.filter(child=child_id)
    meetings_invited_to = current_user.meeting_created_by.filter(child=child_id)
    recent_report_cards = []
    recent_goals = []
    recent_daily_reports = []
    accepted_meetings = []
    new_meetings = []

    for meeting in created_meetings:
        if meeting.accepted and len(accepted_meetings) < max_summaries:
            accepted_meetings.append(meeting)

    for meeting in meetings_invited_to:
        if meeting.accepted and len(accepted_meetings) < max_summaries:
            accepted_meetings.append(meeting)
        elif len(new_meetings) < max_summaries:
            new_meetings.append(meeting)

    for report_card in child.report_card_set.all():
        if report_card.created_at.date() >= one_week_ago and len(recent_report_cards) < max_summaries:
            recent_report_cards.append(report_card)
    for goal in child.goal_set.all():
        if goal.created_at.date() >= one_week_ago and len(recent_goals) < max_summaries:
            recent_goals.append(goal)
    for daily_report in child.daily_report_set.all():
        if daily_report.created_at.date() >= one_week_ago and len(recent_daily_reports) < max_summaries:
            recent_daily_reports.append(daily_report)
    return render(request, 'children/summary.html', {
        'child': child,
        'does_have_teammates': does_have_teammates,
        'current_user': current_user,
        'recent_report_cards': recent_report_cards,
        'recent_goals': recent_goals,
        'recent_daily_reports': recent_daily_reports,
        'accepted_meetings': accepted_meetings,
        'new_meetings': new_meetings,
    })

@login_required
def child_edit(request, child_id):
    child = Child.objects.get(id=child_id)
    if request.method == "POST":
        child.first_name = request.POST.get("first_name")
        child.last_name = request.POST.get("last_name")
        child.date_of_birth = request.POST.get("date_of_birth")
        child.notes = request.POST.get("notes")
        child.save()

        print(child_edit)
        return redirect('child_detail', child_id=child.id)
    return render(request, 'children/edit.html', {
        'child': child,
    })

@login_required
def delete_child(request, child_id):
    child = Child.objects.get(id=child_id)
    if request.method == "POST":
        child.delete()
        return redirect('index')
    return render(request, 'children/delete.html', {
        'child': child,
    })

@login_required
def add_parent(request, child_id):
    child = Child.objects.get(id=child_id)
    current_user = request.user

    if request.method == "POST":
        invite_users(child, request, True)
        return redirect('child_detail', child_id=child.id)

    return render(request, 'children/add_parent.html', {
        'child': child,
        'current_user': current_user,
    })

@login_required
def add_professional(request, child_id):
    child = Child.objects.get(id=child_id)
    current_user = request.user

    if request.method == "POST":
        invite_users(child, request, False)
        return redirect('child_detail', child_id=child.id)

    return render(request, 'children/add_professional.html', {
        'child': child,
        'current_user': current_user,
    })


@login_required
def profile(request):
    user = request.user
    print(user)

    return render(request, 'users/profile.html', {'user': user})

@login_required
def edit_name(request):
    user = request.user
    error_message = ''

    # if submitting the form
    if request.method == 'POST':
        print(request.POST)
        # change name fields
        user.first_name = request.POST.get('first_name')
        user.last_name = request.POST.get('last_name')
        user.profile.first_name = request.POST.get('first_name')
        user.profile.last_name = request.POST.get('last_name')
        user.save()
        # redirect to profile  page
        return redirect('profile')
    else:
        error_message = 'Invalid name, try again!'

    return render(request, 'users/edit_name.html', {'user': user})


@login_required
def edit_relationship(request):
    user = request.user
    error_message = ''

    # if submitting the form
    if request.method == 'POST':
        print(request.POST)
        # change relationship fields
        user.profile.relationship = request.POST.get('relationship')
        user.save()
        # redirect to profile  page
        return redirect('profile')
    else:
        error_message = 'Invalid relationship, try again!'

    return render(request, 'users/edit_relationship.html', {'user': user})

@login_required
def edit_organization(request):
    user = request.user
    error_message = ''

    # if submitting the form
    if request.method == 'POST':
        print(request.POST)
        # change organization fields
        user.profile.organization = request.POST.get('organization')
        user.save()
        # redirect to profile  page
        return redirect('profile')
    else:
        error_message = 'Invalid organization, try again!'

    return render(request, 'users/edit_organization.html', {'user': user})

@login_required
def edit_username(request):
    user = request.user
    error_message = ''

    # if submitting the form
    if request.method == 'POST':
        print(request.POST)
        username = request.POST.get('username')
        # check that username is not already taken
        try:
            User.objects.get(username = username)
            existing_username = User.objects.get(username = username)
        except:
            existing_username = ''

        if existing_username and username != user.username:
            print("user exists")
            error_message = "Username already taken"
        else:
            # change username fields
            user.username = username
            user.save()
            # redirect to profile  page
            return redirect('profile')

    return render(request, 'users/edit_username.html', {'user': user, 'error_message': error_message})

@login_required
def edit_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important!
            messages.success(request, 'Your password was successfully updated!')
            return redirect('profile')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = PasswordChangeForm(request.user)

    return render(request, 'registration/edit_password.html', {
        'form': form
    })

def goals_index(request, child_id):
    child = Child.objects.get(id=child_id)
    goals = child.goal_set.all()
    user = request.user
    print(goals)
    return render(request, 'goals/index.html', {'child':child, 'user':user, 'goals':goals})

@login_required
def add_goal(request, child_id):
    user = request.user
    child = Child.objects.get(id=child_id)
    child= Child.objects.get(id=child_id)
    goal_tracker = TRACKER

    if request.method == "POST":
        title = request.POST.get("title")
        description = request.POST.get("description")
        created_at = datetime.today()

        goal_tracker = request.POST.get("goal_tracker")
        deadline = request.POST.get("deadline")

        goal = Goal(title=title, description=description, created_at=created_at, created_by=user, child_id=child_id, goal_tracker=goal_tracker, deadline=deadline)
        goal.save()
        print(goal)
        return redirect('goals_index', child_id=child_id)
    print(user)
    return render(request, 'goals/add.html', {
        'child_id': child_id,
        'child':child, 
        'user':user, 
        'goal_tracker': goal_tracker})


@login_required
def goal_detail(request, child_id, goal_id):
    goal = Goal.objects.get(id=goal_id)
    child = Child.objects.get(id=child_id)
    current_user = request.user
    return render(request, 'goals/detail.html', {
        'child_id' : child_id,
        'child': child,
        'goal_id': goal_id,
        'goal': goal,
    })

@login_required
def goal_edit(request, child_id, goal_id):
    child = Child.objects.get(id=child_id)
    goal = Goal.objects.get(id=goal_id)
    goal_tracker = TRACKER
    user = request.user

    if request.method == "POST":
        goal.title = request.POST.get("title")
        goal.description = request.POST.get("description")
        goal.goal_tracker = request.POST.get("goal_tracker")
        goal.deadline = request.POST.get("deadline")
        goal.save()

        print(goal_edit)
        return redirect('goal_detail', child_id=child_id, goal_id=goal.id)
    return render(request, 'goals/edit.html', {
        'child_id': child_id, 
        'child': child,
        'goal': goal, 
        'user':user, 
        'goal_tracker': goal_tracker 
    })

@login_required
def goal_delete(request, child_id, goal_id):
    goal = Goal.objects.get(id=goal_id)
    goal.delete()
    return redirect('goals_index', child_id=child_id)


@login_required
def report_card(request, child_id):
    child = Child.objects.get(id=child_id)
    report_cards = child.report_card_set.all()
    current_user = request.user
    return render(request, 'children/report_card.html', {
        'child': child,
        'report_cards': report_cards,
        'current_user': current_user,
    })

GRADING = (('A', 'A+'), 
            ('B', 'A'), 
            ('C', 'A-'), 
            ('D', 'B+'), 
            ('E', 'B'),
            ('F', 'B-'),
            ('G', 'C+'),
            ('H', 'C'),
            ('I', 'C-'),
            ('J', 'D+'),
            ('K', 'D'),
            ('L', 'D-'),
            ('M', 'F'))

@login_required
def add_report_card(request, child_id):
    child = Child.objects.get(id=child_id)
    current_user = request.user
    grades = GRADING

    if request.method == "POST":
        subject = request.POST.get("subject")
        title = request.POST.get("title")
        grade = request.POST.get("grade")
        notes = request.POST.get("notes")
        report_card = Report_card(subject=subject, title=title, grade=grade, notes=notes, child_id=child_id, created_by_id=current_user.id)
        report_card.save()
        print(report_card)
        return redirect('report_card', child_id=child.id)

    return render(request, 'children/new_report_card.html', {
        'child': child,
        'current_user': current_user,
        'grades': grades
    })

@login_required
def daily_reports_index(request, child_id):
    child = Child.objects.get(id=child_id)
    daily_reports = child.daily_report_set.all()
    user = request.user
    return render(request, 'daily_report/index.html', {'child':child, 'user':user, 'daily_reports':daily_reports})

@login_required
def add_daily_report(request, child_id):
    user = request.user
    child = Child.objects.get(id=child_id)
    daily_report_rating = RATING

    if request.method == "POST":
        title = request.POST.get("title")
        notes = request.POST.get("notes")
        created_at = datetime.today()

        daily_report_rating = request.POST.get("daily_report_rating")

        daily_report = Daily_report(title=title, notes=notes, created_at=created_at, created_by=user, child_id=child_id, rating=daily_report_rating,)
        daily_report.save()
        #print(daily_report)
        return redirect('daily_reports_index', child_id=child_id)
    print(user)
    return render(request, 'daily_report/add.html',{'child_id':child_id, 'child':child, 'user':user, 'daily_report_rating':daily_report_rating})

@login_required
def daily_report_detail(request, child_id, daily_report_id):
    daily_report = Daily_report.objects.get(id=daily_report_id)
    child = Child.objects.get(id=child_id)
    current_user = request.user
    return render(request, 'daily_report/detail.html', {
        'child_id': child_id,
        'child': child,
        'daily_report_id':daily_report_id,
        'daily_report':daily_report,
    })

@login_required
def daily_report_edit(request, child_id, daily_report_id):
    daily_report = Daily_report.objects.get(id=daily_report_id)
    child = Child.objects.get(id=child_id)
    daily_report_rating = RATING
    user = request.user

    if request.method == "POST":
        daily_report.title = request.POST.get("title")
        daily_report.notes = request.POST.get("notes")
        daily_report.daily_report_rating = request.POST.get("daily_report_rating")
        daily_report.save()

        #print(daily_report_edit)
        return redirect('daily_report_detail', child_id=child_id, daily_report_id=daily_report.id)
      
    return render(request, 'daily_report/edit.html', {
        'child_id':child_id, 
        'child': child,
        'daily_report': daily_report, 
        'user': user, 
        'daily_report_rating': daily_report_rating
        })


@login_required
def edit_report_card(request, child_id, report_card_id):
    child = Child.objects.get(id=child_id)
    report_card = Report_card.objects.get(id=report_card_id)
    current_user = request.user
    grades = GRADING

    if request.method == "POST":
        subject = request.POST.get("subject")
        title = request.POST.get("title")
        grade = request.POST.get("grade")
        notes = request.POST.get("notes")
        report_card.subject = subject
        report_card.title = title
        report_card.grade = grade
        report_card.notes = notes
        report_card.save()
        print(report_card)
        return redirect('report_card', child_id=child.id)

    return render(request, 'children/edit_report_card.html', {
        'child': child,
        'current_user': current_user,
        'report_card': report_card,
        'grades': grades
    })

@login_required
def meetings(request, child_id):
    child = Child.objects.get(id=child_id)
    does_have_teammates = child.profile_set.all().count() > 1
    current_user = request.user
    created_meetings = current_user.meeting_invitee.filter(child=child_id)
    meetings_invited_to = current_user.meeting_created_by.filter(child=child_id)


    accepted_meetings = []
    new_meetings = []
    meetings_requested = []

    for meeting in created_meetings:
        if meeting.accepted:
            accepted_meetings.append(meeting)
        else:
            meetings_requested.append(meeting)

    for meeting in meetings_invited_to:
        if meeting.accepted:
            accepted_meetings.append(meeting)
        else:
            new_meetings.append(meeting)

    print(accepted_meetings)
    print(new_meetings)
    print(meetings_requested)

    return render(request, 'meetings/index.html', {
        'child': child,
        'does_have_teammates': does_have_teammates,
        'current_user': current_user,
        'accepted_meetings': accepted_meetings,
        'new_meetings': new_meetings,
        'meetings_requested': meetings_requested,
    })

@login_required
def accept_meeting(request, child_id, meeting_id):
    meeting = Meeting.objects.get(id=meeting_id)
    child = Child.objects.get(id=child_id)
    current_user = request.user

    meeting.accepted = True
    meeting.save()


    return redirect("meetings", child_id=child_id)

@login_required
def add_meeting(request, child_id):
    child = Child.objects.get(id=child_id)
    does_have_teammates = child.profile_set.all().count() > 1
    current_user = request.user

    if request.method == "POST":
        teammate = request.POST.get("teammate")
        teammate_id = User.objects.get(username=teammate).id
        print(teammate_id)
        print(teammate)
        return redirect('set_date', 
            child_id=child_id,
            teammate_id=teammate_id,
        )

    return render(request, 'meetings/add_meeting.html', {
        'child': child,
        'does_have_teammates': does_have_teammates,
        'current_user': current_user,
    })

def get_possible_times(times_for_day):

    # get all time intervals
    hours = []
    minutes = []
    for i in range (0, 24):
        hours.append(i)
    for i in range(0, 60, 15):
        minutes.append(i)

    # initialize array of possible times
    possible_times = []
    # iterate through all hours in a day
    for hour in hours:
        # for every availability window
        for time_for_day in times_for_day:
            # if the hour is within availability window
            if hour >= time_for_day.start.hour and hour <= time_for_day.end.hour:
                # iterate through minutes
                for minute in minutes:
                    # if availability window is only within one hour
                    if time_for_day.start.hour == time_for_day.end.hour:
                        # only grab minutes of availability
                        if minute >= time_for_day.start.minute and minute < time_for_day.end.minute:
                            possible_times.append([hour, minute])
                    else:
                        # do not add if is last minute and last hour of availability
                        if hour == time_for_day.end.hour and minute == time_for_day.end.minute:
                            pass
                        # grab times after start time and before end time if the hour is the first hour
                        elif hour == time_for_day.start.hour:
                            if minute >= time_for_day.start.minute:
                                possible_times.append([hour, minute])
                        # grab all times if before the last hour of availability
                        elif hour < time_for_day.end.hour:
                            possible_times.append([hour, minute])
                        elif hour == time_for_day.end.hour:
                            if minute <= time_for_day.end.minute:
                                possible_times.append([hour, minute])
        
    return possible_times

def get_taken_days(teammate, possible_weekdays, availability_events):

    taken_times = []
    for weekday in possible_weekdays:
        taken_times.append({
            weekday[0]: {}
        })
    # print(taken_times)

    # first grab all meetings where teammate is invited
    teammate_meetings = teammate.meeting_invitee.all()
    for teammate_meeting in teammate_meetings:
            # only take those teammate has committed to
            # if teammate_meeting.accepted:
                # create dict of taken time
                taken_time = {
                    "weekday": teammate_meeting.date.weekday(), 
                    "year": teammate_meeting.date.year, 
                    "month": teammate_meeting.date.month, 
                    "day": teammate_meeting.date.day, 
                    "hour": teammate_meeting.date.hour, 
                    "minute": teammate_meeting.date.minute
                }

                # next go through array of taken times
                # for each corresponding weekday
                # add dictionary of that meeting date
                for taken_time_weekday in taken_times:
                    weekday = taken_time["weekday"]
                    # if dealing with correct weekday
                    if weekday in taken_time_weekday:
                        # grab year
                        year = taken_time["year"]
                        # add dictionary for corresponding year if it does not already exist
                        if year not in taken_time_weekday[weekday]:
                            taken_time_weekday[weekday] = {year: {}}
                        # next add month dictionary to year
                        month = taken_time["month"]
                        if month not in taken_time_weekday[weekday][year]:
                            taken_time_weekday[weekday][year] = {month: {}}
                        # next add date dictionary to month
                        day = taken_time["day"]
                        if day not in taken_time_weekday[weekday][year][month]:
                            taken_time_weekday[weekday][year][month] = {day: []}
                        # finally add times to date
                        time = [taken_time["hour"], taken_time["minute"]]
                        if time not in taken_time_weekday[weekday][year][month][day]:
                            taken_time_weekday[weekday][year][month][day].append(time)
                        taken_time_weekday[weekday][year][month][day].sort()

    # next grab all meetings teammate has created
    teammate_meetings = teammate.meeting_created_by.all()
    # grab all meetings, even those not confirmed
    # as they might be planning on their meetings to be eventually accepted
    for teammate_meeting in teammate_meetings:
        taken_time = {
            "weekday": teammate_meeting.date.weekday(), 
            "year": teammate_meeting.date.year, 
            "month": teammate_meeting.date.month, 
            "day": teammate_meeting.date.day, 
            "hour": teammate_meeting.date.hour, 
            "minute": teammate_meeting.date.minute
        }

        # next go through array of taken times
        # for each corresponding weekday
        # add dictionary of that meeting date
        for taken_time_weekday in taken_times:
            weekday = taken_time["weekday"]
            # if dealing with correct weekday
            if weekday in taken_time_weekday:
                # grab year
                year = taken_time["year"]
                # add dictionary for corresponding year if it does not already exist
                if year not in taken_time_weekday[weekday]:
                    taken_time_weekday[weekday] = {year: {}}
                # next add month dictionary to year
                month = taken_time["month"]
                if month not in taken_time_weekday[weekday][year]:
                    taken_time_weekday[weekday][year] = {month: {}}
                # next add date dictionary to month
                day = taken_time["day"]
                if day not in taken_time_weekday[weekday][year][month]:
                    taken_time_weekday[weekday][year][month] = {day: []}
                # finally add times to date
                time = [taken_time["hour"], taken_time["minute"]]
                if time not in taken_time_weekday[weekday][year][month][day]:
                    taken_time_weekday[weekday][year][month][day].append(time)
                taken_time_weekday[weekday][year][month][day].sort()

    print(taken_times)

    # next we want to check if all available times
    # have been taken for a given day
    taken_days = []
    for taken_time in taken_times:
        for weekday in taken_time:
            for year in taken_time[weekday]:
                for month in taken_time[weekday][year]:
                    for day in taken_time[weekday][year][month]:
                        times = taken_time[weekday][year][month][day]
                        # print(times)
                        times_for_day = []
                        for availability_event in availability_events:
                            if availability_event.start.weekday() == weekday:
                                # get all availability windows that match current day
                                times_for_day.append(availability_event)
                                # print(times_for_day)
                            # check if number of meetings taken matches number of available meetings
                            possible_times = get_possible_times(times_for_day)
                            if len(possible_times) == len(times) and [year, month, day] not in taken_days:
                                taken_days.append([year, month, day])
    # print(taken_days)

    return [taken_times, taken_days]

@login_required
def set_date(request, child_id, teammate_id):
    child = Child.objects.get(id=child_id)
    teammate = User.objects.get(id=teammate_id)
    current_user = request.user

    availability_events = teammate.availability_event_set.all()
    # print(availability_events)
    possible_weekdays = []
    for availability_event in availability_events:
        weekday = [availability_event.start.weekday(), calendar.day_name[availability_event.start.weekday()]]
        if weekday not in possible_weekdays:
            possible_weekdays.append(weekday)
    possible_weekdays.sort()

    # get all the unavailable days so they may not be selected
    taken_days = get_taken_days(teammate, possible_weekdays, availability_events)[1]

    if request.method == "POST":
        # get date from datepicker
        date = request.POST.get("date");
        print(date)
        # extract weekday and convert to int
        weekday = date[0:3]
        weekdays_abr = list(calendar.day_abbr)
        for weekday_abr in weekdays_abr:
            if weekday == weekday_abr:
                weekday_int = weekdays_abr.index(weekday_abr)
        print(weekday_int)
        # next extract month
        month = date[4:7]
        months_abr = list(calendar.month_abbr)
        for month_abr in months_abr:
            if month == month_abr:
                month_int = months_abr.index(month_abr)
        print(month_int)
        # next extract month date
        month_date = int(date[8:10])
        print(month_date)
        # finally make sure we have the correct year
        year = int(date[11:15])
        print(year)

        return redirect('set_time', 
            child_id = child_id,
            teammate_id = teammate_id,
            weekday = weekday_int,
            month = month_int,
            month_date = month_date,
            year = year
        )

    return render(request, 'meetings/set_date.html', {
        'child': child,
        'teammate': teammate,
        'current_user': current_user,
        'possible_weekdays': possible_weekdays,
        'taken_days': taken_days
    })


@login_required
def set_time(request, child_id, teammate_id, weekday, month, month_date, year):
    child = Child.objects.get(id=child_id)
    teammate = User.objects.get(id=teammate_id)
    current_user = request.user

    # get all availability windows
    availability_events = teammate.availability_event_set.all()

    possible_weekdays = []
    for availability_event in availability_events:
        if availability_event.start.weekday() not in possible_weekdays:
            possible_weekdays.append([availability_event.start.weekday(), calendar.day_name[availability_event.start.weekday()]])
    possible_weekdays.sort()

    # get all availability windows that match current day
    times_for_day = []
    for event in availability_events:
        if event.start.weekday() == weekday:
            times_for_day.append(event)

    # get all possible meeting times for that time
    possible_times = get_possible_times(times_for_day)

    # grab complete info for days with taken times
    days_with_meetings = get_taken_days(teammate, possible_weekdays, availability_events)[0]
    taken_times = []
    # for any day that matches the selected day,
    # grab all taken times
    for wday in days_with_meetings:
        if weekday in wday:
            if year in wday[weekday]:
                if month in wday[weekday][year]:
                    if month_date in wday[weekday][year][month]:
                        time = f"{wday[weekday][year][month][month_date][0][0]}:{wday[weekday][year][month][month_date][0][1]}"
                        if time not in taken_times:
                            taken_times.append(time)
    
    # get all the days where ALL meetings are selected so they may not be selected
    taken_days = get_taken_days(teammate, possible_weekdays, availability_events)[1]

    if request.method == "POST":
        time = request.POST.get("time")
        print(time)
        hour = int(time.split(',')[0][1:])
        minute = int(time.split(',')[1][1:-1])
        # redirect user to fill out details page to finalize meeting
        return redirect('create_meeting', 
            child_id=child_id,
            teammate_id=teammate_id,
            weekday=weekday,
            month=month,
            month_date=month_date,
            year=year,
            hour=hour,
            minute=minute
        )

    return render(request, 'meetings/set_time.html', {
        'child': child,
        'teammate': teammate,
        'current_user': current_user,
        'weekday': weekday,
        'month': month,
        'month_date': month_date,
        'year': year,
        'possible_weekdays': possible_weekdays,
        'possible_times': possible_times,
        'taken_days': taken_days,
        'taken_times': taken_times
    })

@login_required
def create_meeting(request, child_id, teammate_id, weekday, month, month_date, year, hour, minute):
    child = Child.objects.get(id=child_id)
    teammate = User.objects.get(id=teammate_id)
    current_user = request.user

    weekdays = list(calendar.day_name)
    formatted_weekday = weekdays[weekday]
    months = list(calendar.month_name)
    formatted_month = months[month]
    is_current_year = datetime.now().year == year
    if is_current_year:
        formatted_year = ''
    else:
        formatted_year = year
    formatted_time = [hour, minute, "AM"]
    if minute < 10:
        formatted_time[1] = "0"+str(minute)
    if hour > 12:
        formatted_time[2] = "PM"
        formatted_time[0] = hour - 12
    if hour == 0:
        formatted_time[2] == "PM"
        formatted_time[0] = 12

    # find current date
    d = datetime.now(tz=get_current_timezone())

    # place start and end times on chosen weekday
    date = d.replace(year=year, month=month, day=month_date, hour=hour, minute=minute, second=0, microsecond=0)
    # print(date)

    if request.method == "POST":
        subject = request.POST.get("subject")
        # print(subject)
        description = request.POST.get("description")
        # print(description)
        # create meeting
        meeting = Meeting(title=subject, description=description, invitee=teammate, created_by=current_user, child=child, date=date)
        print(meeting)
        # add time to both users' meetings
        meeting.save()
        # send out invitation by mail
        msg_plain = render_to_string('emails/new_meeting.txt', 
            {'user': current_user.username, 'child_name': child.first_name}
            )
        msg_html = render_to_string('emails/new_meeting.html', {'user': current_user.username, 'child_name': child.first_name})
        send_mail(
        f'APParent: {current_user.username} wants to have a meeting about {child.first_name}',
        msg_plain,
        settings.EMAIL_HOST_USER,
        [f'{teammate.email}'],
        html_message=msg_html,
        fail_silently=False,
        )
        # create notification
        # redirect to meetings page
        return redirect('meetings', 
            child_id=child_id,
        )

    return render(request, 'meetings/create_meeting.html', {
        'child': child,
        'teammate': teammate,
        'current_user': current_user,
        'weekday': weekday,
        'formatted_weekday': formatted_weekday,
        'month': month,
        'formatted_month': formatted_month,
        'month_date': month_date,
        'year': year,
        'formatted_year': formatted_year,
        'hour': hour,
        'minute': minute,
        'formatted_time': formatted_time
    })


@login_required
def set_availability(request):
    current_user = request.user
    hours = []
    minutes = []
    for i in range (0, 24):
        hours.append(i)
    for i in range(0, 60, 15):
        minutes.append(i)

    possible_times = []
    for hour in hours:
        for minute in minutes:
            possible_times.append([hour, minute])

    tz=get_current_timezone()
    print(tz)

    if request.method == "POST":
        weekday = int(request.POST.get("weekday"))
        start_time = request.POST.get("start_time")
        end_time = request.POST.get("end_time")

        # find current date
        d = datetime.now(tz=get_current_timezone())

        # find next instance of chosen weekday
        while d.weekday() != weekday:
            d += timedelta(1)

        # create start and end times from form
        start_hour = int(start_time.split(',')[0][1:])
        start_minute = int(start_time.split(',')[1][1:-1])
        end_hour = int(end_time.split(',')[0][1:])
        end_minute = int(end_time.split(',')[1][1:-1])

        # place start and end times on chosen weekday
        start = d.replace(hour=start_hour, minute=start_minute, second=0, microsecond=0)
        end = d.replace(hour=end_hour, minute=end_minute, second=0, microsecond=0)

        # create new time slot
        availability = Availability_event(user=current_user, start=start, end=end)
        availability.save()
        print(availability)
        return render(request, 'users/profile.html')

    return render(request, 'users/set_availability.html', {
        'current_user': current_user,
        'possible_times': possible_times
    })