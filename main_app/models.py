from django.db import models
from django.contrib.auth.models import User

## Choices

RATING = (('1', 'Good job'), ('2', 'Need work'), ('3', 'Bad'))

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

TRACKER = (('1', 'Completed'), ('2', 'On track'), ('3','Behind schedule'))

## models

class Child(models.Model):
    first_name= models.CharField(max_length= 50)
    last_name = models.CharField(max_length=50)
    date_of_birth = models.DateField()

    def __str__(self):
        return f'{self.first_name} {self.last_name}'

class Organization(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

class Profile(models.Model):
    user= models.OneToOneField(User, on_delete=models.CASCADE)
    email= models.CharField(max_length= 100)
    first_name= models.CharField(max_length= 50)
    last_name = models.CharField(max_length=50)
    is_parent = models.BooleanField()
    relationship = models.CharField(max_length=50)
    child = models.ManyToManyField(Child)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
       
    def __str__(self):
        return f'{self.first_name} {self.last_name}'


class Picture(models.Model):
    url = models.CharField(max_length=200)
    child = models.ForeignKey(Child, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Picture for {self.child_id} @{self.url}'

class Daily_report(models.Model):
    title = models.CharField(max_length=50)
    notes = models.TextField(max_length=300)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    child = models.ForeignKey(Child, on_delete=models.CASCADE)
    rating = models.CharField(max_length=1, choices=RATING, default=RATING[0][0])

    def __str__(self):
        return f'{self.title} ({self.child})'

    class Meta:
        ordering = ['-created_at']

class Report_card(models.Model):
    title = models.CharField(max_length=50)
    notes = models.TextField(max_length=300)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    child = models.ForeignKey(Child, on_delete=models.CASCADE)
    grade = models.CharField(max_length=1, choices=GRADING, default=GRADING[0][0])
    subject = models.CharField(max_length=60)


    def __str__(self):
        return f'{self.grade}: {self.subject} ({self.child})'

    class Meta:
        ordering = ['-created_at']


class Goal(models.Model):
    title = models.CharField(max_length=50)
    description = models.TextField(max_length=300)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    child = models.ForeignKey(Child, on_delete=models.CASCADE)
    goal_tracker = models.CharField(max_length=1, choices=TRACKER, default=TRACKER[0][0])
    deadline = models.DateField()


    def __str__(self):
        return f'{self.title}: ({self.child})'

    class Meta:
        ordering = ['deadline']

class Meeting(models.Model):
    title = models.CharField(max_length=50)
    description = models.TextField(max_length=300)
    invitee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='meeting_invitee')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='meeting_created_by')
    child = models.ForeignKey(Child, on_delete=models.CASCADE)
    date = models.DateField()


    def __str__(self):
        return f'{self.created_by}/{self.invitee}'

    class Meta:
        ordering = ['date']
    

