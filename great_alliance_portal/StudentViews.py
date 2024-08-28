from django.shortcuts import render
from django.db.models.fields import files
from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
import json
from django.db.models import Q
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
from django.db.models import Sum
from great_alliance_portal.models import *
from django.contrib.auth.decorators import login_required
import datetime
import mimetypes
import csv
from django.template.loader import get_template
from django.views import View
from datetime import datetime

def student_homepage(request):
    student_obj = Students.objects.get(admin=request.user.id)
    #programmes = Programmes.objects.get(id=student_obj.programme_id.id)
    #courses = Courses.objects.filter() #programme_id=programmes
    attendance_total = AttendanceReport.objects.filter(
        student_id=student_obj).count()
    attendance_present = AttendanceReport.objects.filter(
        student_id=student_obj, status=True).count()
    attendance_absent = AttendanceReport.objects.filter(
        student_id=student_obj, status=False).count()
    #programme_id = Programmes.objects.get(id=student_obj.programme_id.id)
    #course = Courses.objects.filter(programme_id=programme_id).count()
    #course_data = Courses.objects.filter(programme_id=programme_id)
    #programme_obj = Programmes.objects.get(
        #id=student_obj.programme_id.id)
    #class_room = OnlineClassRoom.objects.filter(
        #course__in=course_data, is_active=True)

    return render(request, "student_templates/student_homepage.html",
                  {
                   "attendance_present": attendance_present,"attendance_absent":attendance_absent,
                   "attendance_total":attendance_total})


def courses(request):
    student_obj = Students.objects.get(admin=request.user.id)
    student_level = StudentLevel.objects.get(
    	id=student_obj.student_level_id.id)
    #programmes = Programmes.objects.get(id=student_obj.programme_id.id)
    courses = Courses.objects.filter(student_level_id=student_level)
    return render(request, "student_templates/courses.html", {"courses": courses})
## @brief view for the detail page of the course.
#
# This view is called by <course_id>/detail url.\n
# It returns the course's detail page containing forum and links to all the assignments and resources.


@login_required
def detail(request, course_id):

    student = Students.objects.get(admin=request.user.id)
    programmes = Programmes.objects.get(id=student.programme_id.id)
    #courses = student.course_list.all()
    courses = Courses.objects.filter(programme_id=programmes)
    course = Courses.objects.get(id=course_id)
    context = {
        'courses': courses,
        #'user': user,
        #'instructor': instructor,
        'student': student,
        'course': course,
        'messages': messages,

    }

    return render(request, 'student_templates/detail.html', context)


## @brief view for the assignments page of a course.
#
# This view is called by <course_id>/view_assignments url.\n
# It returns the webpage containing all the assignments of the course and links to download them and upload submissions.
@login_required
def view_assignments(request, course_id):
    course = Courses.objects.get(id=course_id)
    assignments = Assignment.objects.filter(course=course)
    context = {
        'course': course,
        'assignments': assignments,
    }
    return render(request, 'student_templates/view_assignments.html', context)


## @brief view for the resources page of a course.
#
# This view is called by <course_id>/view_resources url.\n
# It returns the webpage containing all the resources of the course and links to download them.
@login_required
def view_resources(request, course_id):
    course = Courses.objects.get(id=course_id)
    resources = Resources.objects.filter(course=course)
    context = {
        'course': course,
        'resources': resources,
    }
    return render(request, 'student_templates/view_resources.html', context)


## @brief view for the assignment's submission page.
#
# This view is called by <assignment_id>/upload_submission url.\n
# It returns the webpage containing a form to upload submission and redirects to the assignments page again after the form is submitted.
@login_required
def upload_submission(request, assignment_id):
    form = SubmissionForm(request.POST or None, request.FILES or None)
    assignment = Assignment.objects.get(id=assignment_id)
    course_id = assignment.course.id
    course = Courses.objects.get(id=course_id)
    if form.is_valid():
        submission = form.save(commit=False)
        submission.user = request.user
        submission.assignment = assignment
        submission.time_submitted = datetime.datetime.now().strftime('%H:%M, %d/%m/%y')
        submission.save()
        #return render(request, "student_templates/upload_submissions.html")
        #return view_assignments(request, course_id)
        messages.success(request,
                         "Your assignment has been submitted successfully.")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    return render(request, 'student_templates/upload_submissions.html', {'form': form, 'course': course})


def student_profile(request):
    user = CustomUser.objects.get(id=request.user.id)
    student = Students.objects.get(admin=user)
    return render(request, "student_templates/student_profile.html", {"user": user, "student": student})


def edit_student_profile_save(request):
    if request.method != "POST":
        return HttpResponseRedirect(reverse("student_profile"))
    else:

        password = request.POST.get("password")
        email = request.POST.get("email")
        parent_phone = request.POST.get("parent_phone")
        #try:
        custom_user = CustomUser.objects.get(id=request.user.id)
        #custom_user.first_name = first_name
        custom_user.email = email
        custom_user.save()
        #if password != None and password != "":
        #custom_user.set_password(password)
        #custom_user.save()
        student = Students.objects.get(admin=custom_user)
        student.parent_phone = parent_phone

        student.save()
        messages.success(
            request, "Your Profile Has Been Updated.")
        return HttpResponseRedirect(reverse("student_profile"))


def student_view_results(request):
    academic_year = Academic_Year.objects.all()
    semester = Semester.objects.all()
    user = CustomUser.objects.get(id=request.user.id)
    students = Students.objects.get(admin=user)

    return render(request, "student_templates/results.html", {
        "semester": semester, "academic_year": academic_year, "students": students, "user": user})


@csrf_exempt
def student_get_results(request):
    #subject_id = request.POST.get("subject_id")
    #class_id = request.POST.get("class_id")
    user = CustomUser.objects.get(id=request.user.id)
    students = Students.objects.get(admin=user)
    student = Students.objects.get(admin=request.user.id)
    academic_year_id = request.POST.get("academic_year_id")
    semester_id = request.POST.get("semester_id")
    semester_obj = Semester.objects.get(id=semester_id)
    academic_year_obj = Academic_Year.objects.get(id=academic_year_id)
    settings = SchoolSettings.objects.first()
    if settings and settings.school_reopening_date:
        # Ensure school_reopening_date is a datetime object
        school_reopening_date = settings.school_reopening_date
        formatted_date = school_reopening_date.strftime('%A, %b %d, %Y')
    else:
        formatted_date = None
    results = StudentResults.objects.filter(
        academic_year_id=academic_year_obj, semester_id=semester_obj, student_id=student.id)

    overrall = results.aggregate(TOTAL=Sum('total_mark'))['TOTAL']
    try:
        overrall_mark = "{:.2f}".format(overrall)
    except:
        pass
    #programmes = Programmes.objects.get(id=student.programme_id.id)
    student_level = StudentLevel.objects.get(id=student.student_level_id.id)
    courses_total = Courses.objects.filter(student_level_id=student_level).count()
    course_count = StudentResults.objects.filter(
            academic_year_id=academic_year_obj,
            semester_id=semester_obj,
            student_id=student.id
        ).values('course_id').distinct().count()
    if course_count == courses_total:
        average = overrall/courses_total
        average_mark = "{:.2f}".format(average)
    else:
        average_mark = "You will see average mark after all results are released."

    if not results:

        messages.error(request, "Results are not available at the moment!")
        return HttpResponseRedirect("student_homepage")

    else:
        return render(request, "student_templates/results_data.html", {
            "results": results, "user": "user", "students": students,
            "overrall_mark": overrall_mark, "average_mark": average_mark,
            "semester_obj": semester_obj, "academic_year_obj": academic_year_obj,
            "courses_total": courses_total,
            "course_count": course_count,
            "formatted_date": formatted_date
        })


class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return json.JSONEncoder.default(self, obj)


def join_class_room(request, course_id, student_level_id):
    student_obj = Students.objects.get(admin=request.user.id)
    attendance_total = AttendanceReport.objects.filter(
        student_id=student_obj).count()
    attendance_present = AttendanceReport.objects.filter(
        student_id=student_obj, status=True).count()
    attendance_absent = AttendanceReport.objects.filter(
        student_id=student_obj, status=False).count()
    programme = Programmes.objects.get(id=student_obj.programme_id.id)
    courses = Courses.objects.filter(programme_id=programme).count()
    course_data = Courses.objects.filter(programme_id=programme)
    student_level_obj = StudentLevel.objects.get(
        id=student_obj.student_level_id.id)
    class_room = OnlineClassRoom.objects.filter(
        course__in=course_data, is_active=True, student_level_id=student_level_obj)

    student_level_obj = StudentLevel.objects.get(id=student_level_id)
    courses = Courses.objects.filter(id=course_id)
    if courses.exists():
        student_level = StudentLevel.objects.filter(id=student_level_obj.id)
        if student_level.exists():
            course_obj = Courses.objects.get(id=course_id)
            programme = Programmes.objects.get(id=course_obj.programme_id.id)
            check_programme = Students.objects.filter(
            	admin=request.user.id, programme_id=programme.id)
            if check_programme.exists():
                student_level_check = Students.objects.filter(
                    admin=request.user.id, student_level_id=student_level_obj.id)
                if student_level_check.exists():
                    onlineclass = OnlineClassRoom.objects.get(
                    	student_level_id=student_level_id, course=course_id)
                    return render(request, "student_templates/join_class_room_start.html", {"username": request.user.username, "password": onlineclass.room_pwd, "roomid": onlineclass.room_name,
                                                                                            "class_room": class_room})

                else:
                    return HttpResponse("This Online Session is Not For You")
            else:
                return HttpResponse("This Subject is Not For You")
        else:
            return HttpResponse("Session Year Not Found")
    else:
        return HttpResponse("Subject Not Found")


def student_view_attendance(request):
    student = Students.objects.get(admin=request.user.id)
    academic_year = Academic_Year.objects.all()
    semester = Semester.objects.all()
    return render(request, "student_templates/view_attendance.html", {
        "academic_year": academic_year, "semester": semester})


def student_view_attendance_post(request):
    academic_year_id = request.POST.get("academic_year_id")
    semester_id = request.POST.get("semester_id")
    academic_year_obj = Academic_Year.objects.get(id=academic_year_id)
    semester_obj = Semester.objects.get(id=semester_id)
    student_obj = Students.objects.get(admin=request.user.id)
    #attendance_total = AttendanceReport.objects.filter(
    #student_id=student_obj).count()
    attendance_present = AttendanceReport.objects.filter(
    	student_id=student_obj, status=True).count()
    attendance_absent = AttendanceReport.objects.filter(
    	student_id=student_obj, status=False).count()
    #programme = Programmes.objects.get(id=student_obj.programme_id.id)
    #courses = Courses.objects.filter(programme_id=programme).count()
    #courses_data = Courses.objects.filter(programme_id=programme)
    student_level = StudentLevel.objects.get(
    	id=student_obj.student_level_id.id)
    courses = Courses.objects.filter(student_level_id=student_level).count()
    courses_data = Courses.objects.filter(student_level_id=student_level)
    class_room = OnlineClassRoom.objects.filter(
    	 is_active=True, student_level_id=student_level)

    course_name = []
    data_present = []
    data_absent = []
    course_data = Courses.objects.filter(student_level_id=student_obj.student_level_id)
    for course in course_data:
        attendance = Attendance.objects.filter(course_id=course.id, academic_year_id=academic_year_obj,
                                               semester_id=semester_obj)
        attendance_present_count = AttendanceReport.objects.filter(
            attendance_id__in=attendance, status=True, student_id=student_obj.id).count()
        attendance_absent_count = AttendanceReport.objects.filter(
            attendance_id__in=attendance, status=False, student_id=student_obj.id).count()
        course_name.append(course.course_name)
        data_present.append(attendance_present_count)
        data_absent.append(attendance_absent_count)

    #attendance_reports=AttendanceReport.objects.filter(attendance_id__in=attendance,student_id=stud_obj)
    return render(request, "student_templates/student_attendance_data.html",
                  {"attendance_absent": attendance_absent,
                   "attendance_present": attendance_present, "courses": courses,
                   "course_name": course_name, "data_present": data_present,
                   "data_absent": data_absent, "class_room": class_room})
