from collections import defaultdict
from django.shortcuts import render
from django.db.models.fields import files
from django.db.models import FloatField
from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
import json
from django.shortcuts import render
from .models import Students, StudentLevel
from django.contrib import admin, messages
from django.urls.conf import path
from django.contrib.auth.models import auth
from django.shortcuts import get_object_or_404
from django.core.files.storage import FileSystemStorage
from great_alliance_portal.forms import *
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from django.views.generic import ListView
import json
from great_alliance_portal.models import *
from django.core.mail import send_mail
import logging
import smtplib
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from datetime import datetime
from django.contrib.auth.decorators import login_required
from itertools import islice
from django.db.models import Q

def hod_all_attendance(request):
    student_levels = StudentLevel.objects.all().order_by("level_name")
    selected_level_id = request.GET.get('level_id', None)
    # Filter students based on the selected level
    if selected_level_id:
        students = Students.objects.filter(student_level_id=selected_level_id).order_by("admin__last_name")
        if not students:
            messages.error(request, "There are currently no students enrolled in the selected class.")
    else:
        students = Students.objects.none()  # No students to display if no level is selected

    return render(request, "hod_templates/all_attendance.html", {"student_levels": student_levels,
    "students": students, "selected_level": selected_level_id})
def hod_view_all_attendance(request, student_id):
    try:
        student = Students.objects.get(id=student_id)
    except Students.DoesNotExist:
        # Handle the case where the student does not exist
        return render(request, '404.html', status=404)

    academic_years = Academic_Year.objects.all()
    semesters = Semester.objects.all()

    academic_year_id = request.GET.get('academic_year_id', None)
    semester_id = request.GET.get('semester_id', None)
    attendance_reports = []
    chunked_attendance_reports = []
    attendance_present = 0
    attendance_absent = 0
    total_attendance = 0
    if academic_year_id and semester_id:
        attendance_reports = AttendanceReport.objects.filter(
            student_id=student,
            attendance_id__academic_year_id=academic_year_id,
            attendance_id__semester_id=semester_id,
        )
        if not attendance_reports:
            messages.error(request, "No attendance records available.")
        attendance_present = attendance_reports.filter(status=True).count()
        attendance_absent = attendance_reports.filter(status=False).count()
        total_attendance = attendance_reports.count()
        # Chunk the attendance reports into lists of 10
        iterator = iter(attendance_reports)
        for chunk in iter(lambda: list(islice(iterator, 10)), []):
            if chunk:  # Only append non-empty chunks
                chunked_attendance_reports.append(chunk)
    context = {
        'student': student,
        'attendance_reports': attendance_reports,
        'academic_years': academic_years,
        'semesters': semesters,
        'selected_academic_year': academic_year_id,
        'selected_semester': semester_id,
        'attendance_present': attendance_present,
        'attendance_absent': attendance_absent,
        'total_attendance': total_attendance,
        'chunked_attendance_reports': chunked_attendance_reports
    }

    return render(request, 'hod_templates/hod_view_all_attendance.html', context)

def admin_homepage(request):
    user = CustomUser.objects.get(id=request.user.id)
    return render(request, "hod_templates/admin_homepage.html", {"user": user})
def manage_staffs(request):
    return render(request, "hod_templates/manage_staffs.html")
def manage_students(request):
    return render(request, "hod_templates/manage_students.html")
def academic_affairs(request):
    return render(request, "hod_templates/academic_affairs.html")
def about(request):
    return render(request, "hod_templates/about.html")


@login_required
def update_school_settings(request):
    settings, created = SchoolSettings.objects.get_or_create(id=1)
    if request.method == 'POST':
        form = SchoolSettingsForm(request.POST, instance=settings)
        if form.is_valid():
            form.save()
            messages.success(request, "Academic settings have been successfully updated.")
            return redirect('update_school_settings')  # Redirect to a success page
    else:
        form = SchoolSettingsForm(instance=settings)
    return render(request, 'hod_templates/update_school_settings.html', {'form': form})

def students_by_level(request):
    try:
        year_query = request.GET.get('year')
        # Get all student levels for the dropdown
        levels = StudentLevel.objects.all().order_by("level_name")
        # Get the selected level from the request
        selected_level_id = request.GET.get('level_id', None)

        # Initialize students as None
        students = None

        # Check if form is submitted (i.e., if there's a selected level)
        if selected_level_id:
            selected_level = StudentLevel.objects.get(id=selected_level_id)
            if selected_level.level_name == "Alumni":
                students = Students.objects.filter(student_level_id=selected_level_id).order_by("admin__last_name")
                if year_query:
                    try:
                        # Filter students based on the promotion date year
                        students = students.filter(promotion_date__year=year_query)
                    except ValueError:
                        # Handle invalid year format
                        messages.error(request, "Kindly enter a valid year.")
                        return render(request, "hod_templates/students_by_level.html", {"levels": levels, "selected_level": selected_level_id})

                if not students.exists():
                    messages.error(request, f"No records found for students who completed in the year {year_query}. Please verify the year and try again.")
            else:
                students = Students.objects.filter(student_level_id=selected_level_id).order_by("admin__last_name")
                if not students.exists():
                    messages.error(request, "No students have been found for the selected class. Please verify your selection and try again.")
        elif request.GET:  # If the form is submitted without selecting a level
            messages.error(request, "Please select a class.")

        context = {
            'levels': levels,
            'students': students,
            'selected_level': selected_level_id,
            'year_query': year_query,
        }

        return render(request, 'hod_templates/students_by_level.html', context)
    except:
        messages.error(request, "Kindly enter a valid year.")
        return render(request, "hod_templates/students_by_level.html", {"levels": levels, "selected_level": selected_level_id})



def view_student_results(request, student_id):
    try:
        student = Students.objects.get(id=student_id)
    except Students.DoesNotExist:
        # Handle the case where the student does not exist
        return render(request, '404.html', status=404)

    academic_years = Academic_Year.objects.all()
    semesters = Semester.objects.all()

    academic_year_id = request.GET.get('academic_year_id', None)
    semester_id = request.GET.get('semester_id', None)

    results = []
    level_name = None
    semester = None
    academic_year = None
    overall_position = None
    student_total_mark = None
    staff_assigned_to_a_level = None

    if academic_year_id and semester_id:
        all_results = StudentResults.objects.filter(
            student_id=student_id,
            academic_year_id=academic_year_id,
            semester_id=semester_id
        )

        if not all_results.exists():
            messages.error(request, "No assessment records for the specified academic year and semester.")
            return render(request, 'hod_templates/view_student_results.html', {
                'student': student,
                'academic_years': academic_years,
                'semesters': semesters,
                'selected_academic_year': academic_year_id,
                'selected_semester': semester_id,
            })

        level_id = all_results.first().course_id.student_level_id.id
        courses = Courses.objects.filter(staff_id=request.user.id)
        #staff_assigned_to_a_level = StudentLevel.objects.filter(staff_id=request.user.id)

        #if staff_assigned_to_a_level:
        results = all_results
        #else:
            #results = all_results.filter(course_id__in=courses)

        if results.exists():
            level_name = results.first().course_id.student_level_id.level_name.upper()
            semester = results.first().semester_id.semester.upper()
            academic_year = results.first().academic_year_id.academic_year

            # Calculate positions in each course
            for result in results:
                course_results = StudentResults.objects.filter(
                    course_id=result.course_id,
                    academic_year_id=academic_year_id,
                    semester_id=semester_id
                ).order_by('-total_mark')

                student_position_in_course = list(course_results).index(result) + 1
                result.course_position = f'{student_position_in_course}{get_position_suffix(student_position_in_course)}'

            # Calculate overall position based on total marks across all students who have results
            total_marks = StudentResults.objects.filter(
                course_id__student_level_id=level_id,
                academic_year_id=academic_year_id,
                semester_id=semester_id
            ).values('student_id').annotate(total=Sum('total_mark')).order_by('-total')

            student_total_mark = results.aggregate(total=Sum('total_mark', output_field=FloatField()))['total'] or 0.0
            student_ids = list(map(lambda x: x['student_id'], total_marks))

            # Check if the student's ID is in the list before getting the index
            if student_id in student_ids:
                overall_position = student_ids.index(student_id) + 1
            else:
                overall_position = None

    context = {
        'student': student,
        'results': results,
        'academic_years': academic_years,
        'semesters': semesters,
        'selected_academic_year': academic_year_id,
        'selected_semester': semester_id,
        'level_name': level_name,
        'semester': semester,
        'academic_year': academic_year,
        'student_total_mark': student_total_mark,
        'overall_position': f'{overall_position}{get_position_suffix(overall_position)}' if overall_position else None,
    }

    return render(request, 'hod_templates/view_student_results.html', context)


def get_position_suffix(position):
    if 10 <= position % 100 <= 20:
        return 'TH'
    else:
        return {1: 'ST', 2: 'ND', 3: 'RD'}.get(position % 10, 'TH')


def add_bursar(request):
    form = AddBursarForm()
    return render(request, "hod_templates/add_bursar.html", {"form":form})
def add_staff(request):
    form = AddStaffForm()
    return render(request, "hod_templates/add_staff.html", {"form": form})

def manage_course(request):
    # Initialize empty variables
    courses = []
    level = None

    if request.method == 'POST':
        selected_level_id = request.POST.get('level_name')
        if selected_level_id:
            level = get_object_or_404(StudentLevel, id=selected_level_id)
            courses = Courses.objects.filter(student_level_id=selected_level_id).order_by('course_name')

    levels = StudentLevel.objects.all().exclude(level_name="Alumni").order_by("level_name")

    return render(request, "hod_templates/manage_course.html", {
        "courses": courses,
        "levels": levels,
        "selected_level": level
    })




def manage_programme(request):
    programmes = Programmes.objects.all()
    return render(request, "hod_templates/manage_programme.html", {
        "programmes": programmes
    })


def view_staffs(request):
    staffs = Staffs.objects.all()
    bursar = Bursar.objects.all()
    return render(request, "hod_templates/view_staffs.html", {"staffs": staffs, "bursar": bursar})

logger = logging.getLogger(__name__)

def add_bursar_save(request):
    head = CustomUser.objects.get(id=request.user.id)
    if request.method != "POST":
        return HttpResponse("Method not allowed")
    else:
        gender = request.POST.get("gender")
        form = AddBursarForm(request.POST, request.FILES)
        if form.is_valid():
            title= form.cleaned_data["title"]
            email = form.cleaned_data["email"]
            first_name = form.cleaned_data["first_name"]
            last_name = form.cleaned_data["last_name"]
            username = (first_name[0] + last_name).lower()
            phone_number = form.cleaned_data["phone_number"]
            gender = form.cleaned_data["gender"]
            address1 = form.cleaned_data["address1"]
            address2 = form.cleaned_data["address2"]
            date_of_birth = form.cleaned_data["date_of_birth"]
            staff_profile_pic = request.FILES['staff_profile_pic']
            fs = FileSystemStorage()
            filename = fs.save(staff_profile_pic.name, staff_profile_pic)
            profile_pic_url = fs.url(filename)
            # Ensure the username is unique
            original_username = username
            counter = 1
            while CustomUser.objects.filter(username=username).exists():
                username = f"{original_username}{counter}"
                counter += 1
            try:
                password = CustomUser.objects.make_random_password(
                    length=8, allowed_chars="abcdefghjkmnpqrstuvwxyz01234567889")
                user = CustomUser.objects.create_user(
                    username=username, password=password, email=email, last_name=last_name, first_name=first_name, user_type=4)
                user.bursar.address1 = address1
                user.bursar.address2 = address2
                user.bursar.phone_number = phone_number
                user.bursar.title = title
                user.bursar.gender = gender
                user.bursar.date_of_birth = date_of_birth
                user.bursar.staff_profile_pic = profile_pic_url
                user.save()
                try:
                    #email context
                    context = {
                        'user': user,
                        'username': username,
                        'password': password,
                        'head': head,
                        'logo_url': 'https://kingloth.pythonanywhere.com/static/assets/img/clients/client-4.png',
                        'year': datetime.now().year,
                    }

                    # Render the HTML email
                    html_content = render_to_string('hod_templates/staff_registration_email.html', context)

                    # Send email
                    subject = "Login Details for Great Alliance Portal"
                    email = EmailMultiAlternatives(
                        subject,
                        "",  # Text content can be left empty or used for plain text fallback
                        from_email=None,
                        to=[email]
                    )
                    email.attach_alternative(html_content, "text/html")
                    email.send()

                except smtplib.SMTPException as e:
                    messages.error(request, f"Failed to send email: {e}")
                    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

                messages.success(
                request, message=f"Success! {user.bursar.title} {user.first_name} {user.last_name} has been successfully registered as a bursar to the school system. Login credentials have been sent to {user.bursar.title} {user.last_name}'s email.")
                return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
            except Exception as e:
                logger.error(f"We encountered an issue. Please try again, or contact support if the problem persists. {e}", exc_info=True)
                messages.error(request, "We encountered an issue. Please try again, or contact support if the problem persists.")
                return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        else:
            form = AddBursarForm(request.POST)
            return render(request, "hod_templates/add_bursar.html", {"form": form})


logger = logging.getLogger(__name__)

def add_staff_save(request):
    head = CustomUser.objects.get(id=request.user.id)
    if request.method != "POST":
        return HttpResponse("Method not allowed")
    else:
        gender = request.POST.get("gender")
        form = AddStaffForm(request.POST, request.FILES)
        if form.is_valid():
            title = form.cleaned_data["title"]
            email = form.cleaned_data["email"]
            first_name = form.cleaned_data["first_name"]
            last_name = form.cleaned_data["last_name"]
            username = (first_name[0] + last_name).lower()
            phone_number = form.cleaned_data["phone_number"]
            gender = form.cleaned_data["gender"]
            address1 = form.cleaned_data["address1"]
            address2 = form.cleaned_data["address2"]
            date_of_birth = form.cleaned_data["date_of_birth"]
            staff_profile_pic = request.FILES['staff_profile_pic']
            fs = FileSystemStorage()
            filename = fs.save(staff_profile_pic.name, staff_profile_pic)
            profile_pic_url = fs.url(filename)
            # Ensure the username is unique
            original_username = username
            counter = 1
            while CustomUser.objects.filter(username=username).exists():
                username = f"{original_username}{counter}"
                counter += 1
            try:
                password = CustomUser.objects.make_random_password(
                    length=8, allowed_chars="abcdefghjkmnpqrstuvwxyz01234567889")
                user = CustomUser.objects.create_user(
                    username=username, password=password, email=email, last_name=last_name, first_name=first_name, user_type=2)
                user.staffs.address1 = address1
                user.staffs.address2 = address2
                user.staffs.phone_number = phone_number
                user.staffs.gender = gender
                user.staffs.title = title
                user.staffs.date_of_birth = date_of_birth
                user.staffs.staff_profile_pic = profile_pic_url
                user.save()
                try:
                    #email context
                    context = {
                        'user': user,
                        'username': username,
                        'password': password,
                        'head': head,
                        'logo_url': 'https://kingloth.pythonanywhere.com/static/assets/img/clients/client-4.png',
                        'year': datetime.now().year,
                    }

                    # Render the HTML email
                    html_content = render_to_string('hod_templates/staff_registration_email.html', context)

                    # Send email
                    subject = "Login Details for Great Alliance Portal"
                    email = EmailMultiAlternatives(
                        subject,
                        "",  # Text content can be left empty or used for plain text fallback
                        from_email=None,
                        to=[email]
                    )
                    email.attach_alternative(html_content, "text/html")
                    email.send()

                except smtplib.SMTPException as e:
                    messages.error(request, f"Failed to send email: {e}")
                    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

                messages.success(
                    request, message=f"Success! {user.staffs.title} {user.first_name} {user.last_name} has been successfully registered to the school system. Login credentials have been sent to {user.staffs.title} {user.last_name}'s email.")
                return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
            except Exception as e:
                logger.error(f"We encountered an issue. Please try again, or contact support if the problem persists. {e}", exc_info=True)
                messages.error(request, "We encountered an issue. Please try again, or contact support if the problem persists.")
                return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        else:
            form = AddStaffForm(request.POST)
            return render(request, "hod_templates/add_staff.html", {"form": form})

def edit_staff(request, staff_id):
    request.session['staff_id'] = staff_id
    staff = Staffs.objects.get(admin=staff_id)

    form = EditStaffForm()
    form.fields['email'].initial = staff.admin.email
    #form.fields['email2'].initial = staff.email2
    form.fields['first_name'].initial = staff.admin.first_name
    form.fields['last_name'].initial = staff.admin.last_name
    form.fields['username'].initial = staff.admin.username
    form.fields['phone_number'].initial = staff.phone_number
    #form.fields['staff_salary'].initial = staff.staff_salary
    form.fields['date_of_birth'].initial = staff.date_of_birth
    form.fields['address1'].initial = staff.address1
    form.fields['address2'].initial = staff.address2
    #form.fields['gender'].initial = staff.gender

    return render(request, "hod_templates/edit_staff.html",
                  {"staff": staff, "form": form, "id": staff_id})


def edit_staff_save(request):
    if request.method != "POST":
        return HttpResponse("<h2>Method not allowed</h2>")
    else:
        staff_id = request.session.get("staff_id")
        form = EditStaffForm(request.POST, request.FILES)
        if form.is_valid():
            first_name = form.cleaned_data["first_name"]
            last_name = form.cleaned_data["last_name"]
            #age = form.cleaned_data["age"]
            username = form.cleaned_data["username"]
            phone_number = form.cleaned_data["phone_number"]
            #staff_salary = form.cleaned_data["staff_salary"]
            date_of_birth = form.cleaned_data["date_of_birth"]
            address1 = form.cleaned_data["address1"]
            address2 = form.cleaned_data["address2"]
            #gender = form.cleaned_data["gender"]
            #email2 = form.cleaned_data["email2"]
            #primary_or_jhs_id = form.cleaned_data["primary_or_jhs_id"]
            if request.FILES.get('staff_profile_pic', False):
                staff_profile_pic = request.FILES['staff_profile_pic']
                fs = FileSystemStorage()
                filename = fs.save(staff_profile_pic.name, staff_profile_pic)
                profile_pic_url = fs.url(filename)
            else:
                profile_pic_url = None

            #class_id=form.cleaned_data["class_id"]
            #academic_year_id=form.cleaned_data["academic_year_id"]

            #try:
            user = CustomUser.objects.get(id=staff_id)
            user.first_name = first_name
            user.last_name = last_name
            user.username = username

            user.save()

            staff = Staffs.objects.get(admin=staff_id)
            staff.address1 = address1
            staff.address2 = address2
            #staff.email2 = email2
            staff.phone_number = phone_number
            #staff.staff_salary = staff_salary
            staff.date_of_birth = date_of_birth
            #staff.gender = gender
            if profile_pic_url != None:
                staff.staff_profile_pic = profile_pic_url

            staff.save()
            messages.success(request, "Staff updated successfully.")
            return HttpResponseRedirect(reverse("edit_staff", kwargs={"staff_id": staff_id}))
            #except:
            #messages.error(request, "owps an unexpected error occurred!")
            #return HttpResponseRedirect(reverse("edit_staff", kwargs={"staff_id": staff_id}))
        else:
            form = EditStaffForm(request.POST)
            staff = Staffs.objects.get(admin=staff_id)
            return render(request, "hod_templates/edit_staff.html", {"form": form, "id": staff_id, "username": staff.admin.username})


def add_student(request):
    #programmes = Programmes.objects.all()
    level = StudentLevel.objects.all().order_by("level_name").exclude(level_name="Alumni")
    form = AddStudentForm()
    return render(request, "hod_templates/add_student.html",
                  {"level": level, "form": form})

logger = logging.getLogger(__name__)

def add_student_save(request):
    if request.method != "POST":
        return HttpResponse("Method not allowed")
    else:
        student_level_id = request.POST.get("student_level_id")
        form = AddStudentForm(request.POST, request.FILES)
        if form.is_valid():
            first_name = form.cleaned_data["first_name"]
            last_name = form.cleaned_data["last_name"]
            username = (first_name[0] + last_name).lower()
            home_town = form.cleaned_data["home_town"]
            gender = form.cleaned_data["gender"]
            parent_name = form.cleaned_data["parent_name"]
            parent_phone = form.cleaned_data["parent_phone"]
            date_of_birth = form.cleaned_data["date_of_birth"]
            #profile_pic = request.FILES['profile_pic']
            #fs = FileSystemStorage()
            #filename = fs.save(profile_pic.name, profile_pic)
            #profile_pic_url = fs.url(filename)

            # Ensure the username is unique
            original_username = username
            counter = 1
            while CustomUser.objects.filter(username=username).exists():
                username = f"{original_username}{counter}"
                counter += 1

            try:
                plain_password = CustomUser.objects.make_random_password(
                    length=8, allowed_chars="abcdefghjkmnpqrstuvwxyz01234567889")
                user = CustomUser.objects.create_user(
                    username=username, password=plain_password, last_name=last_name,
                    first_name=first_name, user_type=3)

                user.students.home_town = home_town
                user.students.parent_name = parent_name
                user.students.parent_phone = parent_phone
                user.students.date_of_birth = date_of_birth
                user.students.gender = gender
                student_level_obj = StudentLevel.objects.get(id=student_level_id)
                user.students.student_level_id = student_level_obj
                user.students.plain_password = plain_password
                #user.students.profile_pic = profile_pic_url
                user.save()

                # Fetch fees for the student's level and assign to the student
                # Ensure you only retrieve one entry per level
                level_fees = Fees.objects.filter(student_level_id=student_level_obj).first()

                if level_fees:
                    Fees.objects.create(
                        student_id=user.students,
                        student_level_id=student_level_obj,
                        school_fees=level_fees.school_fees,
                        extra_classes=level_fees.extra_classes,
                        stationary=level_fees.stationary,
                        sport_culture=level_fees.sport_culture,
                        ict=level_fees.ict,
                        pta=level_fees.pta,
                        maintenance=level_fees.maintenance,
                        light_bill=level_fees.light_bill,
                        total_fees=level_fees.total_fees,
                        overall_fees=level_fees.total_fees,
                        amount_paid=Decimal('0.00'),
                        arrears_from_last_term=Decimal('0.00')
                    )
                else:
                    # Handle the case where no fees are found for the level
                    #logger.success(f"{user.admin.last_name} {user.admin.first_name} has been successfully enrolled in {student_level_obj.level_name} and added to the school's system.")
                    messages.success(request, f"{user.last_name} {user.first_name} has been successfully enrolled in {student_level_obj.level_name} and added to the school's system.")
                    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

                messages.success(request, f"{user.last_name} {user.first_name} has been successfully enrolled in {student_level_obj.level_name} and added to the school's system.")
                return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

            except Exception as e:
                #logger.error("An error occurred: %s", e, exc_info=True)
                messages.error(request, "We encountered an issue. Please try again, or contact support if the problem persists.")
                return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        else:
            messages.error(request, "We encountered an issue. Please try again, or contact support if the problem persists.")
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

def get_fee_for_level(level):
    # Retrieve the total fees for the given student level
    # Assume that Fees has been set with one entry per level
    fees_record = Fees.objects.filter(student_level_id=level).first()
    if fees_record:
        # Calculate the total fee from all individual components
        total_fees = (
            fees_record.school_fees +
            fees_record.extra_classes +
            fees_record.stationary +
            fees_record.sport_culture +
            fees_record.ict +
            fees_record.pta +
            fees_record.maintenance +
            fees_record.light_bill
        )
        return total_fees
    else:
        raise Exception("No fee record found for this level.")



def edit_student(request, student_id):
    request.session['student_id'] = student_id
    student = Students.objects.get(admin=student_id)
    programmes = Programmes.objects.all()
    level = StudentLevel.objects.all()
    #academic_year = Academic_Year.objects.all()
    #semester = Semester.objects.all()
    form = EditStudentForm()
    #form.fields['email'].initial = student.admin.email
    form.fields['first_name'].initial = student.admin.first_name
    form.fields['last_name'].initial = student.admin.last_name
    #form.fields['age'].initial = student.age
    form.fields['username'].initial = student.admin.username
    form.fields['home_town'].initial = student.home_town
    #form.fields['class_id'].initial=student.class_id.id
    form.fields['parent_name'].initial = student.parent_name
    form.fields['parent_phone'].initial = student.parent_phone
    #form.fields['academic_year_id'].initial = student.academic_year_id.id
    #form.fields['gender'].initial = student.gender
    #form.fields['date_of_birth'].initial = student.date_of_birth

    return render(request, "hod_templates/edit_student.html",
                  {"programmes": programmes, "level": level,
                   "form": form, "student": student})


def edit_student_save(request):
    if request.method != "POST":
        return HttpResponse("<h2>Method not allowed</h2>")
    else:
        student_id = request.session.get("student_id")
        student_level_id = request.POST.get("student_level_id")
        form = EditStudentForm(request.POST, request.FILES)

        if form.is_valid():
            first_name = form.cleaned_data["first_name"]
            last_name = form.cleaned_data["last_name"]
            username = form.cleaned_data["username"]
            home_town = form.cleaned_data["home_town"]
            parent_name = form.cleaned_data["parent_name"]
            parent_phone = form.cleaned_data["parent_phone"]

            #profile_pic_url = None
            #if request.FILES.get('profile_pic', False):
                #profile_pic = request.FILES['profile_pic']
                #fs = FileSystemStorage()
                #filename = fs.save(profile_pic.name, profile_pic)
                #profile_pic_url = fs.url(filename)

            try:
                user = get_object_or_404(CustomUser, id=student_id)
                user.first_name = first_name
                user.last_name = last_name
                user.username = username
                user.save()

                student = get_object_or_404(Students, admin=student_id)
                #new_level = get_object_or_404(StudentLevel, id=student_level_id)
                #old_level = student.student_level_id
                #student.student_level_id = new_level
                student.parent_name = parent_name
                student.parent_phone = parent_phone
                student.home_town = home_town

                #if profile_pic_url:
                    #student.profile_pic = profile_pic_url

                student.save()
                messages.success(request, "The student's profile has been successfully updated.")
                return HttpResponseRedirect(reverse("edit_student", kwargs={"student_id": student_id}))
            except Exception as e:
                messages.error(request, f"We encountered an issue. Please try again, or contact support if the problem persists. {str(e)}")
                return HttpResponseRedirect(reverse("edit_student", kwargs={"student_id": student_id}))
        else:
            student = get_object_or_404(Students, admin=student_id)
            return render(request, "hod_templates/edit_student.html", {"form": form, "id": student_id, "username": student.admin.username})

def delete_student(request, student_id):
    #student_id = request.session.get("student_id")
    #user = CustomUser.objects.get(id=student_id)

    request.session['student_id'] = student_id
    #student = CustomUser.objects.get(id=student_id)
    student = Students.objects.get(admin=student_id)

    if request.method == "POST":
        student_id = request.session.get("student_id")
        try:
            user = CustomUser.objects.get(id=student_id)

            user.delete()
            student = Students.objects.get(admin=student_id)
            student.delete()
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        except:
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    return render(request, "hod_templates/delete_student.html", {"id": student_id,
                                                                 "username": student.admin.username})


def delete_staff(request, staff_id):
    staff = Staffs.objects.get(admin=staff_id)

    if request.method == "POST":
        try:
            user = CustomUser.objects.get(id=staff_id)

            # Delete the Staff record
            staff.delete()

            # Delete the user record
            user.delete()

            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        except CustomUser.DoesNotExist:
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        except Staffs.DoesNotExist:
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    return render(request, "hod_templates/view_staffs.html", {"id": staff_id,
        "username": staff.admin.username})

def delete_bursar(request, bursar_id):
    bursar = Bursar.objects.get(admin=bursar_id)

    if request.method == "POST":
        try:
            user = CustomUser.objects.get(id=bursar_id)

            # Delete the Staff record
            bursar.delete()

            # Delete the user record
            user.delete()

            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        except CustomUser.DoesNotExist:
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        except Staffs.DoesNotExist:
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    return render(request, "hod_templates/view_staffs.html", {"id": bursar_id,
        "username": bursar.admin.username})

def add_level(request):
    staffs = CustomUser.objects.filter(user_type=2)
    return render(request, "hod_templates/add_level.html",{"staffs":staffs})


def add_level_save(request):
    if request.method != "POST":
        return HttpResponseRedirect(reverse("manage_session"))
    else:
        level_name = request.POST.get("level_name")
        staff_id = request.POST.get("staff_id")
        staff_obj = CustomUser.objects.get(id=staff_id)
        try:
            check_list = StudentLevel.objects.filter(level_name=level_name)
            if check_list:
                level_model = StudentLevel.objects.get(level_name=level_name)
                messages.error(request, f"The class '{level_name}' has already been registered. If you wish to make changes, please use the 'Update Class' option.")
                return HttpResponseRedirect(reverse("add_level"))
            else:
                level_model = StudentLevel(level_name=level_name, staff_id=staff_obj)
                level_model.save()
                messages.success(request, f"Success! {level_name} with a class teacher {staff_obj.last_name} {staff_obj.first_name} has been successfully saved.")
                return HttpResponseRedirect(reverse("add_level"))
        except:
            messages.error(request, "We encountered an issue. Please try again, or contact support if the problem persists.")
            return HttpResponseRedirect(reverse("add_level"))

def manage_level(request):
    student_level = StudentLevel.objects.all().order_by("level_name").exclude(level_name="Alumni")
    return render(request, "hod_templates/manage_level.html", {"student_level":student_level})
def edit_level(request, student_level_id):
    student_level = StudentLevel.objects.get(id=student_level_id)
    #academic_year = Academic_Year.objects.all()
    staffs = CustomUser.objects.filter(user_type=2)
    return render(request, "hod_templates/edit_level.html",{"student_level":student_level,"staffs":staffs})

def edit_level_save(request):
    if request.method != "POST":
        return HttpResponse("<h2>Method not allowed</h2>")
    else:
        student_level_id = request.POST.get("student_level_id")
        level_name = request.POST.get("level_name")
        staff_id = request.POST.get("staff")

        try:
            student_level = StudentLevel.objects.get(id=student_level_id)
            student_level.level_name = level_name
            staff = CustomUser.objects.get(id=staff_id)
            student_level.staff_id = staff
            student_level.save()
            messages.success(request, f"Success! {staff.last_name} {staff.first_name} has been successfully reassigned to {level_name}")
            return HttpResponseRedirect(reverse("edit_level", kwargs={"student_level_id": student_level_id}))
        except StudentLevel.DoesNotExist:
            messages.error(request, "Student level not found.")
            return HttpResponseRedirect(reverse("edit_level", kwargs={"student_level_id": student_level_id}))
        except CustomUser.DoesNotExist:
            messages.error(request, "Staff not found.")
            return HttpResponseRedirect(reverse("edit_level", kwargs={"student_level_id": student_level_id}))
        except Exception as e:
            messages.error(request, f"Something went wrong: {e}")
            return HttpResponseRedirect(reverse("edit_level", kwargs={"student_level_id": student_level_id}))

def add_course(request):
    #semester = Semester.SEMESTER_CHOICES
    semester = Semester.objects.all()
    level = StudentLevel.objects.all()
    staffs = CustomUser.objects.filter(user_type=2)
    return render(request, "hod_templates/add_course.html",
                  {"staffs": staffs, "semester": semester, "level": level})


def add_course_save(request):
    if request.method != "POST":
        return HttpResponse("<h2>Method not allowed</h2")
    else:
        course_name = request.POST.get("course_name")
        #course_code = request.POST.get("course_code")
        student_level_id = request.POST.get("level_name")
        level_model = StudentLevel.objects.get(id=student_level_id)
        staff_id = request.POST.get("staff")
        staff = CustomUser.objects.get(id=staff_id)
        level_name = level_model.level_name
        course_code = (course_name[:2] + level_name[:2] + course_name[-1]).upper()
        try:
            check_list = Courses.objects.filter(course_name__iexact=course_name, course_code=course_code,
                              student_level_id=level_model,
                              staff_id=staff)
            #__iexact lookup makes the course name comparison case-insensitive
            if check_list:
                messages.info(request, f"A subject with the name '{course_name}' already exists for the selected class and staff.")
                return HttpResponseRedirect(reverse("add_course"))
            courses = Courses(course_name=course_name, course_code=course_code,
                              student_level_id=level_model,
                              staff_id=staff)
            courses.save()
            messages.success(request, f"The subject '{course_name}' has been successfully added for the selected class and staff.")
            return HttpResponseRedirect(reverse("add_course"))
        except:
            messages.error(request, "We encountered an issue. Please try again, or contact support if the problem persists.")
            return HttpResponseRedirect(reverse("add_course"))


def edit_course(request, course_id):
    level = StudentLevel.objects.all()
    #academic_year = Academic_Year.objects.all()
    staffs = CustomUser.objects.filter(user_type=2)
    course = Courses.objects.get(id=course_id)
    return render(request, "hod_templates/edit_course.html",
                  {"course": course, "level": level, "staffs": staffs, "id": course_id})


def edit_course_save(request):
    if request.method != "POST":
        return HttpResponse("<h2>Method not allowed</>")
    else:
        course_id = request.POST.get("course_id")
        course_name = request.POST.get("course_name")
        #course_code = request.POST.get("course_code")
        #student_level_id = request.POST.get("level_name")
        staff_id = request.POST.get("staff")
        try:
            course = Courses.objects.get(id=course_id)
            course.course_name = course_name
            #level_model = StudentLevel.objects.get(id=student_level_id)
            #course.student_level_id = level_model
            staff = CustomUser.objects.get(id=staff_id)
            course.staff_id = staff
            course.save()
            try:
                staff_profile = Staffs.objects.get(admin=staff)
                staff_title = staff_profile.title
                # You can now use this title in your messages or logs
                messages.success(request, f"'{course.course_name}' has been reassigned to {staff_title} {staff.first_name} {staff.last_name}.")
                return HttpResponseRedirect(reverse("edit_course", kwargs={"course_id": course_id}))
            except Staffs.DoesNotExist:
                messages.error(request, "Staff profile not found. Please check the staff details.")
                return HttpResponseRedirect(reverse("edit_course", kwargs={"course_id": course_id}))

        except:
            messages.error(request, "We encountered an issue. Please try again, or contact support if the problem persists.")
            return HttpResponseRedirect(reverse("edit_course", kwargs={"course_id": course_id}))


def edit_programme(request, programme_id):
    staffs = CustomUser.objects.filter(user_type=2)
    programme = Programmes.objects.get(id=programme_id)
    return render(request, "hod_templates/edit_programme.html",
                  {"programme": programme, "staffs": staffs, "id": programme_id})


def edit_programme_save(request):
    if request.method != "POST":
        return HttpResponse("<h2>Method not allowed</>")
    else:
        #subject_id=request.POST.get("subject_id")
        #subject_name=request.POST.get("subject_name")

        programme_id = request.POST.get("programme_id")
        #class_name = request.POST.get("class_name")
        staff_id = request.POST.get("staff")
        try:
            programme = Programmes.objects.get(id=programme_id)
            #clas.class_name=class_name
            staff = CustomUser.objects.get(id=staff_id)
            programme.staff_id = staff
            #staff.staff_id = staff_id
            programme.save()
            messages.success(request, "Programme Info Updated.")
            return HttpResponseRedirect(reverse("edit_programme", kwargs={"programme_id": programme_id}))

        except:
            messages.error(request, "We encountered an issue. Please try again, or contact support if the problem persists.")
            return HttpResponseRedirect(reverse("edit_programme", kwargs={"programme_id": programme_id}))


def view_students(request):
    # Get the selected level if any
    selected_level_id = request.POST.get('student_level') if request.method == 'POST' else None

    # Filter students based on the selected level
    if selected_level_id:
        students = Students.objects.filter(student_level_id=selected_level_id).order_by("admin__last_name")
        males = students.filter(gender="Male")
        females = students.filter(gender="Female")
    else:
        students = Students.objects.all().order_by("student_level_id__level_name").exclude(student_level_id__level_name="Alumni")
        males = Students.objects.filter(gender="Male")
        females = Students.objects.filter(gender="Female")

    # Filter students dynamically based on search query
    search_query = request.GET.get('search_query')
    if search_query:
        students = students.filter(
            Q(admin__first_name__icontains=search_query) |
            Q(admin__last_name__icontains=search_query)
        )

    student_level = StudentLevel.objects.all().exclude(level_name="Alumni").order_by("level_name")
    total_students = students.count()
    total_males = males.count()
    total_females = females.count()

    return render(request, "hod_templates/view_students.html", {
        "students": students,
        "total_students": total_students,
        "total_males": total_males,
        "total_females": total_females,
        "student_level": student_level,
        "selected_level_id": selected_level_id
    })


def staff_permissions(request):
    leaves = StaffLeaveReport.objects.all()
    return render(request, "hod_templates/staff_permissions.html", {"leaves": leaves})


def staff_leave_view(request):
    leaves = StaffLeaveReport.objects.all()
    return render(request, "hod_templates/staff_permissions.html", {"leaves": leaves})


def staff_approve_leave(request, leave_id):
    leave = StaffLeaveReport.objects.get(id=leave_id)
    leave.leave_status = 1
    leave.save()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


def staff_disapprove_leave(request, leave_id):
    leave = StaffLeaveReport.objects.get(id=leave_id)
    leave.leave_status = 2
    leave.save()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    #return HttpResponseRedirect(reverse("manage_staffs"))


@csrf_exempt
def check_email_exist(request):
    email = request.POST.get("email")
    user_obj = CustomUser.objects.filter(email=email).exists()
    if user_obj:
        return HttpResponse(True)
    else:
        return HttpResponse(False)


@csrf_exempt
def check_email2_exist(request):
    email2 = request.POST.get("email2")
    user_obj = Staffs.objects.filter(email2=email2).exists()
    if user_obj:
        return HttpResponse(True)
    else:
        return HttpResponse(False)


@csrf_exempt
def check_username_exist(request):
    username = request.POST.get("username")
    user_obj = CustomUser.objects.filter(username=username).exists()
    if user_obj:
        return HttpResponse(True)
    else:
        return HttpResponse(False)

def profile_admin(request):
    user = CustomUser.objects.get(id=request.user.id)
    return render(request, "hod_templates/header.html", {"user": user})
def admin_profile(request):
    user = CustomUser.objects.get(id=request.user.id)
    return render(request, "hod_templates/admin_profile.html", {"user": user})


def edit_admin_profile_save(request):
    if request.method != "POST":
        return HttpResponseRedirect(reverse("admin_profile"))
    else:
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        #password = request.POST.get("password")
        #username = request.POST.get("username")
        email = request.POST.get("email")
        try:
            custom_user = CustomUser.objects.get(id=request.user.id)
            custom_user.first_name = first_name
            custom_user.last_name = last_name
            custom_user.email = email
            #custom_user.username = username
            #if password != None and password != "":
                #custom_user.set_password(password)
            custom_user.save()
            messages.success(request, "Your profile has been updated.")
            return HttpResponseRedirect(reverse("admin_profile"))
        except:
            messages.error(request, "We encountered an issue. Please try again, or contact support if the problem persists.")
            return HttpResponseRedirect(reverse("admin_profile"))


def add_programme(request):
    staffs = CustomUser.objects.filter(user_type=2)
    return render(request, "hod_templates/add_programme.html", {
        "staffs": staffs
    })


def add_programme_save(request):
    if request.method != "POST":
        return HttpResponse("Method Not Allowed")
    else:
        programme_name = request.POST.get("programme_name")
        staff_id = request.POST.get("staff_id")
        staff_obj = CustomUser.objects.get(id=staff_id)
        try:
            check_list = Programmes.objects.filter(programme_name=programme_name,
                                                   staff_id=staff_obj)
            check_programme = Programmes.objects.filter(
                programme_name=programme_name)
            if check_list:
                programme_model = Programmes.objects.get(programme_name=programme_name,
                                                         staff_id=staff_obj)
                programme_model.save()
                messages.success(
                    request, "The selected Programme and staff already exist.")
                return HttpResponseRedirect(reverse("add_programme"))
            elif check_programme:
                programme_model = Programmes.objects.get(
                    programme_name=programme_name)
                programme_model.save()
                messages.error(
                    request, "Programme you added was already added, so it has been updated with the staff you selected.")
                return HttpResponseRedirect(reverse("add_programme"))
            else:
                programme_model = Programmes(
                    programme_name=programme_name, staff_id=staff_obj)
                programme_model.save()
                messages.success(request, "Programme Saved.")
                return HttpResponseRedirect(reverse("add_programme"))
        except:
            messages.error(request, "Something went wrong!")
            return HttpResponseRedirect(reverse("add_programme"))


def add_academic_year(request):
    return render(request, "hod_templates/add_academic_year.html")


def add_academic_year_save(request):
    if request.method != "POST":
        return HttpResponseRedirect(reverse("manage_session"))
    else:
        academic_year = request.POST.get("academic_year")

        try:
            check_list = Academic_Year.objects.filter(
                academic_year=academic_year)
            if check_list:
                academic_year_model = Academic_Year.objects.get(
                    academic_year=academic_year)
                #academic_year_model.save()
                messages.info(
                    request, f"The academic year {academic_year_model.academic_year} has already been added.")
                return HttpResponseRedirect(reverse("add_academic_year"))
            else:
                academic_year_model = Academic_Year(
                    academic_year=academic_year)
                academic_year_model.save()
                messages.success(request, "Academic Year Added.")
                return HttpResponseRedirect(reverse("add_academic_year"))
        except:
            messages.error(request, "We encountered an issue. Please try again, or contact support if the problem persists.")
            return HttpResponseRedirect(reverse("add_academic_year"))

@csrf_exempt
def admin_view_attendance(request):
    #user = CustomUser.objects.get(id=request.user.id)
    #staff = Staffs.objects.get(admin=user)
    students = None
    if request.method == 'POST':
        student_level_id = request.POST.get('student_level')
        academic_year_id = request.POST.get('academic_year')
        semester_id = request.POST.get('semester')

        attendance_reports = AttendanceReport.objects.filter(
            attendance_id__student_level_id=student_level_id,
            attendance_id__academic_year_id=academic_year_id,
            attendance_id__semester_id=semester_id,
        )
        total_attendance = attendance_reports.values('attendance_id__attendance_date').distinct().count()
        students = Students.objects.filter(student_level_id=student_level_id).order_by("admin__last_name")
        attendance_data = []

        for student in students:
            #total_attendance = attendance_reports.count()
            attendance_present = attendance_reports.filter(student_id=student, status=True).count()
            attendance_absent = attendance_reports.filter(student_id=student, status=False).count()

            attendance_data.append({
                'last_name': student.admin.last_name.upper(),
                'first_name': student.admin.first_name,
                'total_attendance': total_attendance,
                'attendance_present': attendance_present,
                'attendance_absent': attendance_absent,
            })

        return JsonResponse({'attendance_data': attendance_data})

    else:
        student_levels = StudentLevel.objects.all().exclude(level_name="Alumni")
        academic_years = Academic_Year.objects.all()
        semesters = Semester.objects.all()
        settings = SchoolSettings.objects.first()
        current_academic_year = settings.current_academic_year if settings else None
        current_semester = settings.current_semester if settings else None
        context = {
            'current_academic_year': current_academic_year,
            'current_semester': current_semester,
            'student_levels': student_levels,
            'academic_years': academic_years,
            'semesters': semesters,
            'students': students,

        }
        return render(request, 'hod_templates/admin_view_attendance.html', context)



@csrf_exempt
def admin_get_attendance_dates(request):
    course = request.POST.get("course")
    academic_year_id = request.POST.get("academic_year_id")
    semester_id = request.POST.get("semester_id")
    semester_obj = Semester.objects.get(id=semester_id)
    academic_year_obj = Academic_Year.objects.get(id=academic_year_id)
    course_obj = Courses.objects.get(id=course)
    attendance = Attendance.objects.filter(
        course_id=course_obj,
        academic_year_id=academic_year_obj, semester_id=semester_obj)
    attendance_obj = []
    for attendance_single in attendance:
        data = {"id": attendance_single.id, "attendance_date": attendance_single.attendance_date,
                "academic_year_id": attendance_single.academic_year_id.id,
                "semester_id": attendance_single.semester_id.id}
        attendance_obj.append(data)
    return JsonResponse(attendance_obj, safe=False)


@csrf_exempt
def admin_get_attendance_student(request):
    attendance_date = request.POST.get("attendance_date")

    attendance = Attendance.objects.get(id=attendance_date)
    attendance_data = AttendanceReport.objects.filter(attendance_id=attendance)
    list_data = []

    for student in attendance_data:
        data_small = {"id": student.student_id.admin.id, "name": student.student_id.admin.last_name +
                      " "+student.student_id.admin.first_name, "status": student.status}
        list_data.append(data_small)
    return JsonResponse(list_data, content_type="application/json", safe=False)


def admin_view_student_results(request):
    courses = Courses.objects.all()
    #student_levels = StudentLevel.objects.filter(courses__in=courses).distinct()
    student_levels = StudentLevel.objects.all().exclude(level_name="Alumni")
    academic_years = Academic_Year.objects.all()
    semesters = Semester.objects.all()
    settings = SchoolSettings.objects.first()
    current_academic_year = settings.current_academic_year if settings else None
    current_semester = settings.current_semester if settings else None
    return render(request, "hod_templates/admin_view_student_results.html", {
        "student_levels": student_levels,
        "academic_years": academic_years,
        "semesters": semesters,
        "current_academic_year": current_academic_year,
        "current_semester": current_semester,
    })


@csrf_exempt
def admin_get_student_results(request):
    if request.method == "POST":
        student_level_id = request.POST.get("student_level")
        academic_year_id = request.POST.get("academic_year")
        semester_id = request.POST.get("semester")

        settings = SchoolSettings.objects.first()
        current_academic_year = settings.current_academic_year if settings else None
        current_semester = settings.current_semester if settings else None

        student_level = get_object_or_404(StudentLevel, id=student_level_id)
        academic_year = get_object_or_404(Academic_Year, id=academic_year_id)
        semester = get_object_or_404(Semester, id=semester_id)

        courses = Courses.objects.filter(student_level_id=student_level).order_by('course_name')
        students = Students.objects.filter(student_level_id=student_level).order_by('admin__last_name')

        student_results = StudentResults.objects.filter(
            student_id__in=students,
            course_id__in=courses,
            academic_year_id=academic_year,
            semester_id=semester
        ).select_related('student_id', 'course_id').order_by('course_id__course_name')

        # Calculate total marks for each student
        total_marks_per_student = StudentResults.objects.filter(
            student_id__in=students,
            academic_year_id=academic_year,
            semester_id=semester
        ).values('student_id').annotate(total=Sum('total_mark')).order_by('-total')

        # Create a dictionary to store student data including their total marks and overall position
        student_data = defaultdict(lambda: {'student': None, 'results': [], 'total_marks': 0, 'overall_position': None})

        # Assign total marks and student information to each student
        for idx, item in enumerate(total_marks_per_student):
            student_id = item['student_id']
            student = students.get(id=student_id)  # Get the student instance
            student_data[student_id]['student'] = student  # Add student info to the dictionary
            student_data[student_id]['total_marks'] = item['total']
            student_data[student_id]['overall_position'] = f"{idx + 1}{get_position_suffix(idx + 1)}"  # Assign overall position

        # Group individual results by student
        for result in student_results:
            student_id = result.student_id.id
            student_data[student_id]['results'].append(result)

            # Calculate position in the course
            course_results = StudentResults.objects.filter(
                course_id=result.course_id,
                academic_year_id=academic_year_id,
                semester_id=semester_id
            ).order_by('-total_mark')

            student_position_in_course = list(course_results).index(result) + 1
            result.course_position = f'{student_position_in_course}{get_position_suffix(student_position_in_course)}'

        # Check if there are no results
        if not student_data:
            messages.error(request, "No results were found for the selected criteria. Please review your selection and try again.")
            return HttpResponseRedirect("/admin_view_student_results")

        # Pass student data directly to the template
        return render(request, "hod_templates/show_results.html", {
            "student_levels": StudentLevel.objects.all().exclude(level_name="Alumni"),
            "academic_years": Academic_Year.objects.all(),
            "semesters": Semester.objects.all(),
            "student_data": dict(student_data),  # Pass the student data to the template
            "student_level_id": student_level_id,
            "academic_year_id": academic_year_id,
            "current_semester": current_semester,
            "current_academic_year": current_academic_year,
            "semester_id": semester_id,
        })

    # Handle GET requests
    settings = SchoolSettings.objects.first()
    current_academic_year = settings.current_academic_year if settings else None
    current_semester = settings.current_semester if settings else None
    return render(request, "hod_templates/show_results.html", {
        "student_levels": StudentLevel.objects.all().exclude(level_name="Alumni"),
        "academic_years": Academic_Year.objects.all(),
        "semesters": Semester.objects.all(),
        "current_academic_year": current_academic_year,
        "current_semester": current_semester,
    })





# Function to add position suffix such as 2ND, 3RD, 41ST
def get_position_suffix(position):
    if 10 <= position % 100 <= 20:  # Handle 11th, 12th, 13th, etc.
        suffix = 'TH'
    else:
        suffix = {1: 'ST', 2: 'ND', 3: 'RD'}.get(position % 10, 'TH')
    return suffix


def all_programmes(request):
    return render(request, "hod_templates/all_classes.html")


def academic_sem_selection(request):
    academic_year = Academic_Year.objects.all()
    semester = Semester.objects.all()
    return render(request, "hod_templates/academic_sem_selection.html",
                  {"academic_year": academic_year, "semester": semester})


def add_semester(request):
    semester = Semester.objects.all()
    return render(request, "hod_templates/add_semester.html",{"semester":semester})


def add_semester_save(request):
    if request.method != "POST":
        return HttpResponseRedirect(reverse("manage_session"))
    else:
        semester = request.POST.get("semester")

        try:
            check_list = Semester.objects.filter(semester=semester)
            if check_list:
                semester_model = Semester.objects.get(semester=semester)
                semester_model.save()
                messages.success(request, "Term Already Added.")
                return HttpResponseRedirect(reverse("add_semester"))
            else:
                semester_model = Semester(semester=semester)
                semester_model.save()
                messages.success(request, "Term Added")
                return HttpResponseRedirect(reverse("add_semester"))
        except:
            messages.error(request, "Error in adding semester")
            return HttpResponseRedirect(reverse("add_semester"))


def admin_view_results_of_pupils(request):
    student_results = StudentResults.objects.all()
    semester = Semester.objects.all()
    academic_year = Academic_Year.objects.all()
    subjects = Subjects.objects.all()
    return render(request, "hod_templates/student_results.html",
                  {"student_results": student_results, "semester": semester,
                   "academic_year": academic_year, "subjects": subjects})


'''def view_student_results(request):
    subject_id = request.POST.get("subject_id")
    academic_year_id = request.POST.get("academic_year_id")
    semester_id = request.POST.get("semester_id")
    subject_obj = Subjects.objects.get(id=subject_id)
    academic_year_obj = Academic_Year.objects.get(id=academic_year_id)
    semeste_obj = Semester.objects.get(id=semester_id)
    try:
        student_results = StudentResults.objects.filter(
            subject_id=subject_obj, academic_year_id=academic_year_obj,
            semester_id=semester_obj)
        console.log(student_results)
        return render(request, "hod_templates/view_student_results.html")
    except:
        messages.error(request, "Results Not Available at the Moment")
'''

class InfoListView(ListView):
    model = Students
    template_name = 'hod_templates/view_students.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["qs_json"] = json.dumps(list(Students.objects.values()))
        return context


def fees(request):
    pass

from django.shortcuts import render
from django.contrib import messages
from django.utils import timezone
from .models import Students

def alumni(request):
    try:
        year_query = request.GET.get('year')
        students = Students.objects.filter(student_level_id__level_name="Alumni")

        if year_query:
            try:
                year_query = int(year_query)
                current_year = timezone.now().year

                # Check if the year is within a reasonable range
                if year_query < 2024 or year_query > current_year:
                    raise ValueError("Year out of range")

                # Filter students based on the promotion date year
                students = students.filter(promotion_date__year=year_query)

            except ValueError:
                # Handle invalid year format or out-of-range error
                messages.error(request, f"Enter a year from 2024 to {current_year}.")
                return render(request, "hod_templates/alumni.html", {"students": students})

        if not students.exists():
            messages.error(request, f"No records found for students who completed in the year {year_query}. Please verify the year and try again.")

        # Count the number of students
        student_count = students.count()

        if student_count == 0:
            if year_query:
                messages.error(request, f"No records found for students who completed in the year {year_query}. Please verify the year and try again.")
            else:
                messages.success(request, "No alumni records are available at the moment.")

        # Render the template with students and the count
        return render(request, "hod_templates/alumni.html", {"students": students, "student_count": student_count})

    except Exception as e:
        # Catch all other errors
        messages.error(request, "An error occurred. Please try again.")
        return render(request, "hod_templates/alumni.html", {"students": students})

def fees_save(request):
    pass
