from django.utils import timezone
from decimal import Decimal
from django.urls import reverse
from django.contrib.auth.models import User
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.shortcuts import get_object_or_404
from django.db.models import Sum, F, DecimalField
class Semester(models.Model):
    FIRST_TERM = 'First Term'
    SECOND_TERM = 'Second Term'
    THIRD_TERM = 'Third Term'

    SEMESTER_CHOICES = [
        (FIRST_TERM, 'First Term'),
        (SECOND_TERM, 'Second Term'),
        (THIRD_TERM, 'Third Term'),
    ]

    id = models.AutoField(primary_key=True)
    semester = models.CharField(
        max_length=50,
        choices=SEMESTER_CHOICES,
        default=FIRST_TERM,
    )
    objects = models.Manager()

    def __str__(self):
        return self.semester
'''class Semester(models.Model):
    id = models.AutoField(primary_key=True)
    semester = models.CharField(max_length=50)
    objects = models.Manager()
'''

class Academic_Year(models.Model):
    id = models.AutoField(primary_key=True)
    academic_year = models.CharField(max_length=255)
    objects = models.Manager()
    def __str__(self):
        return self.academic_year
class SchoolSettings(models.Model):
    current_academic_year = models.ForeignKey(Academic_Year, on_delete=models.SET_NULL, null=True, blank=True)
    current_semester = models.ForeignKey(Semester, on_delete=models.SET_NULL, null=True, blank=True)
    school_reopening_date = models.DateField(null=True, blank=True)
    def __str__(self):
        return "School Settings"

class CustomUser(AbstractUser):
    user_type_data = ((1, "HOD"), (2, "Staff"), (3, "Student"), (4, "Bursar"))
    user_type = models.CharField(
        default=1, choices=user_type_data, max_length=10)


class AdminHOD(models.Model):
    id = models.AutoField(primary_key=True)
    #custom_id = models.CharField(primary_key=True, max_length=8, unique=True, default=custom_id)
    admin = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)
    objects = models.Manager()


class Programmes(models.Model):
    id = models.AutoField(primary_key=True)
    programme_name = models.CharField(max_length=255)
    staff_id = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)
    objects = models.Manager()


class StudentLevel(models.Model):
    id = models.AutoField(primary_key=True)
    level_name = models.CharField(max_length=25)
    staff_id = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True)
    objects = models.Manager()
    def __str__(self):
        return self.level_name

class Courses(models.Model):
    id = models.AutoField(primary_key=True)
    course_name = models.CharField(max_length=255)
    course_code = models.CharField(max_length=7)
    #programme_id = models.ForeignKey(
        #Programmes, on_delete=models.CASCADE, default=1)
    student_level_id = models.ForeignKey(
        StudentLevel, on_delete=models.SET_NULL, null=True)
    #semester_id = models.ForeignKey(Semester, on_delete=models.CASCADE)
    staff_id = models.ForeignKey(CustomUser, on_delete=models.SET_NULL,null=True)
    #academic_year_id = models.Fore
    # ignKey(
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)
    objects = models.Manager()
    def __str__(self):
        return self.course_name

class Bursar(models.Model):
    id = models.AutoField(primary_key=True)
    admin = models.OneToOneField(CustomUser, on_delete=models.CASCADE, null=True, blank=True)
    phone_number = models.TextField()
    title = models.CharField(max_length=10, default="Mr.")
    gender = models.CharField(max_length=10)
    date_of_birth = models.DateField()
    #staff_salary = models.DecimalField(max_digits=6, decimal_places=2)
    firebase_token = models.TextField(default="")
    #email2 = models.TextField()
    address1 = models.TextField(null=True, blank=True)
    address2 = models.TextField()
    staff_profile_pic = models.FileField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)
    objects = models.Manager()


class Staffs(models.Model):
    id = models.AutoField(primary_key=True)
    admin = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    phone_number = models.TextField()
    title = models.CharField(max_length=10, default="Mr.")
    gender = models.CharField(max_length=10)
    date_of_birth = models.DateField()
    #staff_salary = models.DecimalField(max_digits=6, decimal_places=2)
    firebase_token = models.TextField(default="")
    #email2 = models.TextField()
    address1 = models.TextField()
    address2 = models.TextField()
    staff_profile_pic = models.FileField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)
    objects = models.Manager()


class Students(models.Model):
    id = models.AutoField(primary_key=True)
    admin = models.OneToOneField(CustomUser, on_delete=models.CASCADE, null=True, blank=True)
    plain_password = models.CharField(max_length=128, blank=True, null=True)
    promotion_date = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10)
    date_of_birth = models.DateField()
    profile_pic = models.FileField()
    home_town = models.TextField()
    parent_name = models.CharField(max_length=255)
    parent_phone = models.TextField()
    student_level_id = models.ForeignKey(StudentLevel, on_delete=models.SET_NULL, null=True)
    courses = models.ManyToManyField(Courses, related_name='students')
    firebase_token = models.TextField(default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)
    objects = models.Manager()

    def __str__(self):
        return self.admin.get_full_name()


class Attendance(models.Model):
    id = models.AutoField(primary_key=True)
    #course_id = models.ForeignKey(Courses, on_delete=models.DO_NOTHING, null=True)
    student_level_id = models.ForeignKey(StudentLevel, on_delete=models.SET_NULL, null=True)
    #subject_id = models.ForeignKey(Subjects, on_delete=models.DO_NOTHING)
    attendance_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    academic_year_id = models.ForeignKey(
        Academic_Year, on_delete=models.SET_NULL, null=True)
    semester_id = models.ForeignKey(Semester, on_delete=models.SET_NULL, null=True)
    updated_at = models.DateTimeField(auto_now_add=True)
    objects = models.Manager()


class AttendanceReport(models.Model):
    id = models.AutoField(primary_key=True)
    student_id = models.ForeignKey(Students, on_delete=models.DO_NOTHING, null=True)
    attendance_id = models.ForeignKey(Attendance, on_delete=models.SET_NULL, null=True)
    status = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)
    objects = models.Manager()


class StudentLeaveReport(models.Model):
    id = models.AutoField(primary_key=True)
    student_id = models.ForeignKey(Students, on_delete=models.SET_NULL, null=True)
    leave_date = models.CharField(max_length=255)
    leave_message = models.TextField()
    leave_status = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)
    objects = models.Manager()


class StaffLeaveReport(models.Model):
    id = models.AutoField(primary_key=True)
    staff_id = models.ForeignKey(Staffs, on_delete=models.SET_NULL, null=True)
    leave_date = models.CharField(max_length=255)
    leave_message = models.TextField()
    leave_status = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)
    objects = models.Manager()


class OnlineClassRoom(models.Model):
    id = models.AutoField(primary_key=True)
    room_name = models.CharField(max_length=255)
    room_pwd = models.CharField(max_length=255)
    course = models.ForeignKey(Courses, on_delete=models.SET_NULL, null=True)
    #programme_id = models.ForeignKey(
    #Programmes, on_delete=models.CASCADE)
    student_level_id = models.ForeignKey(
        StudentLevel, on_delete=models.SET_NULL, null=True)
    started_by = models.ForeignKey(Staffs, on_delete=models.SET_NULL, null=True)
    is_active = models.BooleanField(default=True)
    created_on = models.DateTimeField(auto_now_add=True)
    objects = models.Manager()


class StudentNotification(models.Model):
    id = models.AutoField(primary_key=True)
    student_id = models.ForeignKey(Students, on_delete=models.SET_NULL, null=True)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)
    objects = models.Manager()


class StaffNotification(models.Model):
    id = models.AutoField(primary_key=True)
    staff_id = models.ForeignKey(Staffs, on_delete=models.SET_NULL, null=True)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)
    objects = models.Manager()


class Fees(models.Model):
    id = models.AutoField(primary_key=True)
    arrears_from_last_term = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    school_fees = models.DecimalField(max_digits=20, decimal_places=2)
    extra_classes = models.DecimalField(max_digits=20, decimal_places=2)
    stationary = models.DecimalField(max_digits=20, decimal_places=2)
    sport_culture = models.DecimalField(max_digits=20, decimal_places=2)
    ict = models.DecimalField(max_digits=20, decimal_places=2)
    pta = models.DecimalField(max_digits=20, decimal_places=2)
    maintenance = models.DecimalField(max_digits=20, decimal_places=2)
    light_bill = models.DecimalField(max_digits=20, decimal_places=2)
    total_fees = models.DecimalField(max_digits=20, decimal_places=2)
    overall_fees = models.DecimalField(max_digits=25,decimal_places=2)
    balance_carry_forward = models.DecimalField(max_digits=25, decimal_places=2, default=0.00)
    amount_paid = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    #programme_id = models.ForeignKey(Programmes, on_delete=models.SET_NULL, null=True)
    student_level_id = models.ForeignKey(
        StudentLevel, on_delete=models.SET_NULL,null=True)
    #semester_id = models.ForeignKey(Semester, on_delete=models.SET_NULL, null=True)
    student_id = models.ForeignKey(Students, on_delete=models.SET_NULL, null=True)
    arrears_entered = models.BooleanField(default=False)  # New field to track if arrears have been entered
    def record_payment(self, amount_paid):
        if self.amount_paid is None:
            self.amount_paid = Decimal('0.00')
        self.amount_paid += amount_paid
        self.overall_fees -= amount_paid
        self.arrears_from_last_term -= amount_paid

        if self.overall_fees < Decimal('0.00'):
            self.overall_fees = Decimal('0.00')
        if self.arrears_from_last_term < Decimal('0.00'):
            self.arrears_from_last_term = Decimal('0.00')

        self.save()
class Payment(models.Model):
    student = models.ForeignKey(Students, on_delete=models.CASCADE)
    amount_paid = models.DecimalField(max_digits=20, decimal_places=2)
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, default=1)
    academic_year = models.ForeignKey(Academic_Year, on_delete=models.CASCADE, default=1)
    date = models.DateField(default=timezone.now)

    def __str__(self):
        return f"{self.student} - {self.amount_paid} on {self.date}"

class StudentResults(models.Model):
    id = models.AutoField(primary_key=True)
    student_id = models.ForeignKey(Students, on_delete=models.SET_NULL, null=True)
    course_id = models.ForeignKey(Courses, on_delete=models.SET_NULL, null=True)
    semester_id = models.ForeignKey(Semester, on_delete=models.SET_NULL, null=True)
    #class_id = models.ForeignKey(Classes, on_delete=models.CASCADE)
    academic_year_id = models.ForeignKey(
        Academic_Year, on_delete=models.SET_NULL, null=True)
    individual_test_score = models.DecimalField(max_digits=5, decimal_places=2)
    group_work_score = models.DecimalField(max_digits=5, decimal_places=2)
    class_test_score = models.DecimalField(max_digits=5, decimal_places=2)
    project_score = models.DecimalField(max_digits=5, decimal_places=2)
    assignment_mark = models.DecimalField(max_digits=5, decimal_places=2)
    exam_mark = models.DecimalField(max_digits=5, decimal_places=2)
    total_mark = models.DecimalField(max_digits=5, decimal_places=2)
    overral_mark = models.DecimalField(max_digits=5, decimal_places=2)
    aggregate = models.CharField(max_length=2)
    overral_mark_average = models.DecimalField(max_digits=5, decimal_places=2)
    grade = models.CharField(max_length=50)
    remark = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)
    objects = models.Manager()

## @brief This class represents the assignments in a course.


class Assignment(models.Model):
    ## The description of the assignment
    description = models.CharField(max_length=1000, default='')

    ## The file containing the problems for the assignment
    file = models.FileField(default='')

    ## The course associated with the assignment
    course = models.ForeignKey(Courses, on_delete=models.SET_NULL, null=True)

    ## The date,time of posting the assignment
    post_time = models.CharField(max_length=100)

    ## The deadline to complete the assignment for the students
    deadline = models.CharField(max_length=100)


## @brief This class represents the submissions for an assignment.
class Submission(models.Model):
    ## The file submitted by student
    file_submitted = models.FileField(default='')

    ## The date,time of uploading the submission
    time_submitted = models.CharField(max_length=100)

    ## The user associated with the submission(who uploaded the submission)
    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, default=1)

    ## The assignment associated with the submission
    assignment = models.ForeignKey(
        Assignment, on_delete=models.CASCADE, default=1)

## @brief This class represents the messages displayed in the forum.


class Resources(models.Model):
    file_resource = models.FileField(default='')
    title = models.CharField(max_length=100)
    course = models.ForeignKey(Courses, default=1, on_delete=models.SET_NULL, null=True)


class Notification(models.Model):
    ## The content of notification
    content = models.CharField(max_length=500)

    ## The course associated with the notification
    course = models.ForeignKey(Courses, models.SET_NULL, null=True)
    time = models.CharField(max_length=100)


@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        if instance.user_type == 1:
            AdminHOD.objects.create(admin=instance)
        if instance.user_type == 2:
            Staffs.objects.create(
                admin=instance, date_of_birth="1300-01-01",
                address1="", address2="", staff_profile_pic="", gender="",
                phone_number=""
            )
        if instance.user_type == 3:
            Students.objects.create(admin=instance,
                                    date_of_birth="2000-01-01",
                                    student_level_id=StudentLevel.objects.get(
                                        id=1),
                                    home_town="", profile_pic="", gender="")
        if instance.user_type == 4:
            Bursar.objects.create(
                admin=instance, date_of_birth="1300-01-01",
                address1="", address2="", staff_profile_pic="", gender="",
                phone_number=""
            )

@receiver(post_save, sender=CustomUser)
def save_user_profile(sender, instance, **kwargs):
    if instance.user_type == 1:
        instance.adminhod.save()
    if instance.user_type == 2:
        instance.staffs.save()
    if instance.user_type == 3:
        instance.students.save()
    if instance.user_type == 4:
        instance.bursar.save()
