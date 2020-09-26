from django.shortcuts import render, redirect
from .models import Child, Profile, Picture, Goal, Report_card, Daily_report, Availability_event
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

# S3_BASE_URL = 'https://s3-us-west-1.amazonaws.com/'
# BUCKET = 'seir-apparent'
S3_BASE_URL = "https://pp-apparent.s3.amazonaws.com/"
BUCKET = 'pp-apparent'

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

        

@login_required
def child_detail(request, child_id):
    child = Child.objects.get(id=child_id)
    does_have_teammates = child.profile_set.all().count() > 1
    current_user = request.user
    return render(request, 'children/detail.html', {
        'child': child,
        'does_have_teammates': does_have_teammates,
        'current_user': current_user,
    })

@login_required
def child_summary(request, child_id):
    child = Child.objects.get(id=child_id)
    does_have_teammates = child.profile_set.all().count() > 1
    current_user = request.user
    max_summaries = 2
    today = date.today()
    one_week_ago = today - timedelta(days = 7)
    recent_report_cards = []
    recent_goals = []
    for report_card in child.report_card_set.all():
        if report_card.created_at.date() >= one_week_ago and len(recent_report_cards) < max_summaries:
            recent_report_cards.append(report_card)
    for goal in child.goal_set.all():
        if goal.created_at.date() >= one_week_ago and len(recent_goals) < max_summaries:
            recent_goals.append(goal)
    return render(request, 'children/summary.html', {
        'child': child,
        'does_have_teammates': does_have_teammates,
        'current_user': current_user,
        'recent_report_cards': recent_report_cards,
        'recent_goals': recent_goals
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
    return render(request, 'goals/add.html', {'child_id': child_id, 'user':user, 'goal_tracker': goal_tracker})


@login_required
def goal_detail(request, child_id, goal_id):
    goal = Goal.objects.get(id=goal_id)
    current_user = request.user
    return render(request, 'goals/detail.html', {
        'child_id' : child_id,
        'goal_id': goal_id,
        'goal': goal,
    })

@login_required
def goal_edit(request, child_id, goal_id):
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
    return render(request, 'goals/edit.html', { 'child_id': child_id, 'goal': goal, 'user':user, 'goal_tracker': goal_tracker })

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
def daily_report_index(request, child_id):
    child = Child.objects.get(id=child_id)
    daily_report = child.daily_report_set.all()
    user = request.user
    print(daily_report)
    return render(request, 'daily_report/index.html', {'child':child, 'user':user, 'daily_report':daily_report})

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

        daily_report = Daily_report(title=title, notes=notes, created_at=created_at, created_by=user, child_id=child_id)
        daily_report.save()
        print(daily_report)
        return redirect('daily_report_index', child_id=child_id)
    print(user)
    return render(request, 'daily_report/add.html',{'child_id':child_id, 'user':user, 'daily_report_rating':daily_report_rating})

@login_required
def daily_report_detail(request, daily_report_id):
    daily_report = Daily_report.objects.get(id=daily_report_id)
    current_user = request.user
    return render(request, 'daily_report/detail.html', {
        'daily_report':daily_report,
    })

@login_required
def daily_report_edit(request, daily_report_id):
    daily_report = Daily_report.objects.get(id=daily_report_id)
    daily_report_rating = RATING
    user = request.user

    if request.method == "POST":
        daily_report.title = request.POST.get("title")
        daily_report.notes = request.POST.get("notes")
        daily_report.daily_report_rating = request.POST.get("daily_report_rating")
        daily_report.save()

        print(daily_report_edit)
        return redirect('daily_report_detail', daily_report_id=daily_report.id)
    return render(request, 'daily_reports/edit.html', {'daily_report': daily_report, 'user':user, 'daily_report_rating':daily_report_rating})


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
    return render(request, 'meetings/index.html', {
        'child': child,
        'does_have_teammates': does_have_teammates,
        'current_user': current_user,
    })

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
        return redirect('set_time', 
            child_id=child_id,
            teammate_id=teammate_id,
        )

    return render(request, 'meetings/add_meeting.html', {
        'child': child,
        'does_have_teammates': does_have_teammates,
        'current_user': current_user,
    })

@login_required
def set_time(request, child_id, teammate_id):
    child = Child.objects.get(id=child_id)
    teammate = User.objects.get(id=teammate_id)
    current_user = request.user

    availability_events = teammate.availability_event_set.all()
    print(availability_events)
    possible_weekdays = []
    for availability_event in availability_events:
        if availability_event.start.weekday() not in possible_weekdays:
            possible_weekdays.append(availability_event.start.weekday())
    print(possible_weekdays)

    # if request.method == "POST":
    #     teammate = request.POST.get("teammate")
    #     print(teammate)
    #     return render(request, 'meetings/set_time.html', {
    #         'child': child,
    #         'teammate': teammate,
    #         'current_user': current_user,
    #     })

    return render(request, 'meetings/set_time.html', {
        'child': child,
        'teammate': teammate,
        'current_user': current_user,
        'possible_weekdays': possible_weekdays
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

    if request.method == "POST":
        weekday = int(request.POST.get("weekday"))
        start_time = request.POST.get("start_time")
        end_time = request.POST.get("end_time")

        # find current date
        d = datetime.today()

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