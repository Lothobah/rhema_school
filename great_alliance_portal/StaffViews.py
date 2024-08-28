from django.shortcuts import render, redirect
from great_alliance_portal.models import *
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.core import serializers
from django.contrib import messages
import json
from django.urls import reverse
from decimal import Decimal, ROUND_HALF_UP
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .forms import PromoteStudentsForm, SubmissionForm, AssignmentForm, NotificationForm, ResourceForm, EnrollStudentsForm
import datetime
from uuid import uuid4
from django.shortcuts import get_object_or_404
#libraries for PDF document.
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, PageBreak, Table, TableStyle, Paragraph, Spacer, Image
import io
from collections import defaultdict
import os
from itertools import islice
from django.db.models import FloatField
from datetime import datetime
from django.utils import timezone

def all_attendance(request):
    user = CustomUser.objects.get(id=request.user.id)
    staff = Staffs.objects.get(admin=user)
    student_levels = StudentLevel.objects.filter(staff_id=request.user.id).exclude(level_name="Alumni")
    selected_level_id = request.GET.get('level_id', None)
    # Filter students based on the selected level
    if selected_level_id:
        students = Students.objects.filter(student_level_id=selected_level_id).order_by("gender","admin__last_name")
        if not students:
            messages.error(request, "The selected class currently has no students...")
    else:
        students = Students.objects.none()  # No students to display if no level is selected

    return render(request, "staff_templates/all_attendance.html", {"student_levels": student_levels,
    "students": students, "selected_level": selected_level_id, "staff": staff})
def staff_view_all_attendance(request, student_id):
    user = CustomUser.objects.get(id=request.user.id)
    staff = Staffs.objects.get(admin=user)
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
            messages.error(request, "No Attendance report for the selected criteria")
        attendance_present = attendance_reports.filter(status=True).count()
        attendance_absent = attendance_reports.filter(status=False).count()
        total_attendance = attendance_reports.count()
        # Chunk the attendance reports into lists of 5

        iterator = iter(attendance_reports)
        for chunk in iter(lambda: list(islice(iterator, 10)), []):
            chunked_attendance_reports.append(chunk)
    context = {
        'student': student,
        'staff': staff,
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

    return render(request, 'staff_templates/staff_view_all_attendance.html', context)


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
#use to calculate and add a prefix to the positions, eg. 1ST, 2ND
def ordinal(n):
    if 10 <= n % 100 <= 20:
        suffix = 'TH'
    else:
        suffix = {1: 'ST', 2: 'ND', 3: 'RD'}.get(n % 10, 'TH')
    return str(n) + suffix

@login_required
def view_students_and_promote(request):
    user = CustomUser.objects.get(id=request.user.id)
    staff = Staffs.objects.get(admin=user)
    teacher = CustomUser.objects.get(id=request.user.id)
    levels = StudentLevel.objects.filter(staff_id=teacher).exclude(level_name="Alumni")
    staff_assigned_to_a_level = StudentLevel.objects.filter(staff_id=request.user.id)
    student_data = []
    selected_level = None
    form = PromoteStudentsForm()
    third_term = Semester.objects.get(semester='Third Term')  # Fetch the Third Term semester object
    settings = SchoolSettings.objects.first()
    current_academic_year = settings.current_academic_year if settings else None
    if request.method == 'POST':
        if 'level' in request.POST:
            level_id = request.POST.get('level')
            if level_id:
                try:
                    selected_level = StudentLevel.objects.get(id=level_id, staff_id=request.user)
                    students = Students.objects.filter(student_level_id=selected_level)

                    for student in students:
                        total_marks = StudentResults.objects.filter(
                            student_id=student,
                            course_id__student_level_id=selected_level,
                            semester_id=third_term,
                            academic_year_id=current_academic_year
                        ).aggregate(Sum('total_mark'))['total_mark__sum'] or 0
                        student_data.append({'student': student, 'total_marks': total_marks})

                    student_data.sort(key=lambda x: x['total_marks'], reverse=True)

                    for idx, data in enumerate(student_data):
                        data['position'] = ordinal(idx + 1)

                except StudentLevel.DoesNotExist:
                    messages.error(request, "Selected level does not exist.")
                    selected_level = None

        if 'promote_students' in request.POST:
            form = PromoteStudentsForm(request.POST)
            if form.is_valid():
                next_level = form.cleaned_data['next_level']
                selected_students = request.POST.getlist('selected_students')

                for student_id in selected_students:
                    student = Students.objects.get(id=student_id)
                    # Promote the student to the new level
                    old_level = student.student_level_id
                    student.student_level_id = next_level
                    # Automatically set the promotion date to the current date
                    student.promotion_date = timezone.now().date()
                    try:
                        # Get the fee amount for the new level
                        new_fee_amount = get_fee_for_level(next_level)  # Use the new function here

                        if old_fee_record := Fees.objects.filter(student_id=student, student_level_id=old_level).first():
                            # Update the old record to reflect the new fees and potential arrears
                            arrears = old_fee_record.overall_fees - old_fee_record.amount_paid
                            old_fee_record.student_level_id = next_level
                            old_fee_record.total_fees = new_fee_amount
                            old_fee_record.arrears_from_last_term = arrears

                            if old_fee_record.total_fees + old_fee_record.arrears_from_last_term < old_fee_record.balance_carry_forward:
                                old_fee_record.balance_carry_forward -= old_fee_record.total_fees + old_fee_record.arrears_from_last_term
                                old_fee_record.overall_fees = Decimal('0.00')
                                old_fee_record.arrears_from_last_term = Decimal('0.00')
                            else:
                                old_fee_record.overall_fees = old_fee_record.total_fees + old_fee_record.arrears_from_last_term - old_fee_record.balance_carry_forward
                                old_fee_record.balance_carry_forward = Decimal('0.00')
                            old_fee_record.save()
                        else:
                            # If no old fee record exists, create a new one with arrears
                            Fees.objects.create(
                                student_id=student,
                                student_level_id=next_level,
                                total_fees=new_fee_amount,
                                arrears_from_last_term=0,
                                overall_fees=new_fee_amount
                            )

                    except Exception as e:
                        # If no fee record is found for the new level and level name is not "Alumni", show an error message and stop promotion
                        if next_level.level_name != "Alumni":
                            messages.error(request, f"Cannot promote student(s) to {next_level.level_name}. Please see the bursar to add the fees for {next_level.level_name}.")
                            return redirect('view_students_and_promote')

                    student.save()

                messages.success(request, 'Selected students have been promoted.')
                return redirect('view_students_and_promote')

    return render(request, 'staff_templates/view_students_and_promote.html', {
        'levels': levels,
        'students': student_data,
        'form': form,
        'staff': staff,
        'third_term': third_term,
        'selected_level': selected_level,
        'staff_assigned_to_a_level': staff_assigned_to_a_level
    })


def staff_view_students_by_level(request):
    user = CustomUser.objects.get(id=request.user.id)
    staff = Staffs.objects.get(admin=user)
    # Get all student levels for the dropdown
    courses = Courses.objects.filter(staff_id=request.user.id)
    levels = StudentLevel.objects.filter(courses__in=courses).distinct()
    #levels = StudentLevel.objects.all()
    # Get the selected level from the request
    selected_level_id = request.GET.get('level_id', None)

    # Filter students based on the selected level
    if selected_level_id:
        students = Students.objects.filter(student_level_id=selected_level_id).order_by("gender","admin__last_name")
    else:
        students = Students.objects.none()  # No students to display if no level is selected

    context = {
        'levels': levels,
        'students': students,
        'selected_level': selected_level_id,
        'staff': staff
    }

    return render(request, 'staff_templates/staff_view_students_by_level.html', context)

def staff_view_students_results(request, student_id):
    user = CustomUser.objects.get(id=request.user.id)
    staff = Staffs.objects.get(admin=user)
    try:
        student = Students.objects.get(id=student_id)
    except Students.DoesNotExist:
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
            messages.error(request, "No assessment for the specified academic year and semester.")
            return render(request, 'staff_templates/staff_view_students_results.html', {
                'student': student,
                'academic_years': academic_years,
                'semesters': semesters,
                'selected_academic_year': academic_year_id,
                'selected_semester': semester_id,
                'staff': staff
            })

        level_id = all_results.first().course_id.student_level_id.id
        courses = Courses.objects.filter(staff_id=request.user.id)
        staff_assigned_to_a_level = StudentLevel.objects.filter(staff_id=request.user.id)

        if staff_assigned_to_a_level:
            results = all_results
        else:
            results = all_results.filter(course_id__in=courses)

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
        'staff_assigned_to_a_level': staff_assigned_to_a_level,
        'semester': semester,
        'staff': staff,
        'academic_year': academic_year,
        'student_total_mark': student_total_mark,
        'overall_position': f'{overall_position}{get_position_suffix(overall_position)}' if overall_position else None,
    }

    return render(request, 'staff_templates/staff_view_students_results.html', context)


def get_position_suffix(position):
    if 10 <= position % 100 <= 20:
        return 'TH'
    else:
        return {1: 'ST', 2: 'ND', 3: 'RD'}.get(position % 10, 'TH')


@login_required
def get_students_for_course(request, course_id):
    try:
        course = Courses.objects.get(id=course_id)
        students = Students.objects.filter(student_level_id=course.student_level_id)
        student_data = [{'id': student.id, 'last_name': student.admin.last_name.upper(), 'first_name': student.admin.first_name} for student in students]
        return JsonResponse({'students': student_data})
    except Courses.DoesNotExist:
        return JsonResponse({'students': []})
    #'full_name': student.admin.get_full_name()

@login_required
def enroll_students(request):
    user = CustomUser.objects.get(id=request.user.id)
    staff = Staffs.objects.get(admin=user)
    if request.method == 'POST':
        form = EnrollStudentsForm(request.POST, staff=request.user)
        if form.is_valid():
            course = form.cleaned_data['course']
            students = form.cleaned_data['students']
            for student in students:
                student.courses.add(course)
            messages.success(request, 'Students have been successfully enrolled in the selected subject.')
            return redirect('enroll_students')
    else:
        form = EnrollStudentsForm(staff=request.user)
    return render(request, 'staff_templates/enroll_students.html', {'form': form, 'staff': staff})
def sidebar_rules(request):
    #staff = Staffs.objects.get(admin=request.user.id)
    staff_assigned_to_a_level = StudentLevel.objects.filter(staff_id=request.user.id)
    return render(request, "staff_templates/header.html", {"staff_assigned_to_a_level": staff_assigned_to_a_level})


@login_required
def staff_homepage(request):
    staff = Staffs.objects.get(admin=request.user.id)
    courses = Courses.objects.filter(staff_id=request.user.id)
    staff_assigned_to_a_level = StudentLevel.objects.filter(staff_id=request.user.id)

    # Get the current date
    today = datetime.today().date()

    # Find students in the staff's assigned levels
    students_with_birthday_today = Students.objects.filter(
        student_level_id__in=staff_assigned_to_a_level,
        date_of_birth__month=today.month,
        date_of_birth__day=today.day
    )

    # Create a list of birthday messages for each student
    birthday_messages = []
    for student in students_with_birthday_today:
        message = f"🎉 Happy Birthday to {student.admin.last_name.upper()} {student.admin.first_name}! Take a moment to wish them a wonderful day! 🎂"
        birthday_messages.append(message)

    course_count = courses.count()

    return render(request, "staff_templates/staff_homepage.html", {
        "course_count": course_count,
        "staff": staff,
        "staff_assigned_to_a_level": staff_assigned_to_a_level,
        "birthday_messages": birthday_messages,
    })

@csrf_exempt
def staff_fcmtoken_save(request):
    token = request.POST.get("token")
    try:
        staff = Staffs.objects.get(admin=request.user.id)
        staff.fcm_token = token
        staff.save()
        return HttpResponse("True")
    except:
        return HttpResponse("False")


def staff_about(request):
    return render(request, "staff_templates/about.html")


def staff_manage_students(request):
    return render(request, "staff_templates/manage_student.html")


def staff_apply_leave(request):
    staff_obj = Staffs.objects.get(admin=request.user.id)
    leave_data = StaffLeaveReport.objects.filter(staff_id=staff_obj)
    return render(request, "staff_templates/staff_apply_leave.html", {"leave_data": leave_data})


def staff_apply_leave_save(request):
    if request.method != "POST":
        return HttpResponseRedirect(reverse("staff_apply_leave"))
    else:
        leave_date = request.POST.get("leave_date")
        leave_reason = request.POST.get("leave_reason")

        staff_obj = Staffs.objects.get(admin=request.user.id)
        try:
            leave_report = StaffLeaveReport(
                staff_id=staff_obj, leave_date=leave_date, leave_message=leave_reason, leave_status=0)
            leave_report.save()
            messages.success(request, "Leave message sent.")
            return HttpResponseRedirect(reverse("staff_apply_leave"))
        except:
            messages.error(request, "An error occurred!")
            return HttpResponseRedirect(reverse("staff_apply_leave"))

@csrf_exempt
def get_students(request):
    student_level_id = request.POST.get("student_level")
    student_level = StudentLevel.objects.get(id=student_level_id)
    students = Students.objects.filter(student_level_id=student_level)

    student_data = serializers.serialize("python", students)
    list_data = []

    for student in students:
        data_small = {"id": student.admin.id,
                      "name": student.admin.last_name.upper()+" "+student.admin.first_name}
        list_data.append(data_small)
    return JsonResponse(list_data, content_type="application/json", safe=False)

@csrf_exempt
@login_required
def get_courses_by_level(request):
    if request.method == "POST" and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        student_level_id = request.POST.get("student_level")
        staff_id = request.user.id

        try:
            courses = Courses.objects.filter(staff_id=staff_id, student_level_id=student_level_id)
            course_list = [{"id": course.id, "course_name": course.course_name} for course in courses]
            return JsonResponse({"courses": course_list})

        except Courses.DoesNotExist:
            return JsonResponse({'error': 'No courses found for this level'}, status=404)

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error fetching courses: {e}", exc_info=True)
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request method or not AJAX'}, status=400)

@csrf_exempt
@login_required
def get_students_by_subjects(request):
    if request.method == "POST" and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        student_level_id = request.POST.get("student_level")
        course_id = request.POST.get("course_id")
        semester_id = request.POST.get("semester_id")
        academic_year_id = request.POST.get("academic_year_id")
        staff_id = request.user.id

        try:
            # Fetch the course to ensure it's taught by the logged-in staff
            course = Courses.objects.get(id=course_id, staff_id=staff_id)

            # Fetch students based on student level and course
            students = Students.objects.filter(student_level_id=student_level_id, courses=course)
            student_data = []

            for student in students:
                # Fetch results for the current student, course, academic year, and semester
                results = StudentResults.objects.filter(
                    student_id=student,
                    course_id=course,
                    academic_year_id=academic_year_id,
                    semester_id=semester_id
                ).first()

                student_info = {
                    "id": student.id,
                    "name": f"{student.admin.last_name} {student.admin.first_name}",
                    "courses": [{
                        "id": course.id,
                        "course_name": course.course_name,
                        "individual_test_score": int(results.individual_test_score) if results else '',
                        "group_work_score": int(results.group_work_score) if results else '',
                        "class_test_score": int(results.class_test_score) if results else '',
                        "project_score": int(results.project_score) if results else '',
                        "exam_mark": int(results.exam_mark * 2) if results else ''  # Adjust this if needed
                    }]
                }
                student_data.append(student_info)

            return JsonResponse({"students": student_data})

        except Courses.DoesNotExist:
            return JsonResponse({'error': 'Course not found for the selected criteria'}, status=404)

        except Students.DoesNotExist:
            return JsonResponse({'error': 'No students found for the selected criteria'}, status=404)

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error fetching students: {e}", exc_info=True)
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request method or not AJAX'}, status=400)

@login_required
def staff_take_attendance(request):
    user = CustomUser.objects.get(id=request.user.id)
    staff = Staffs.objects.get(admin=user)
    student_levels = StudentLevel.objects.filter(staff_id=request.user.id).exclude(level_name="Alumni")
    staff_assigned_to_a_level = StudentLevel.objects.filter(staff_id=request.user.id)
    academic_years = Academic_Year.objects.all()
    semesters = Semester.objects.all()

    settings = SchoolSettings.objects.first()
    current_academic_year = settings.current_academic_year if settings else None
    current_semester = settings.current_semester if settings else None

    return render(request, "staff_templates/staff_take_attendance.html",
                  {"student_levels": student_levels,
                   "academic_years": academic_years,
                   "semesters": semesters,
                   "staff": staff,
                   "current_academic_year": current_academic_year,
                   "current_semester": current_semester,
                   "staff_assigned_to_a_level": staff_assigned_to_a_level})

@csrf_exempt
def save_attendance_data(request):
    student_ids = request.POST.get("student_ids")
    student_level_id = request.POST.get("student_level_id")
    attendance_date = request.POST.get("attendance_date")
    academic_year_id = request.POST.get("academic_year_id")
    semester_id = request.POST.get("semester_id")

    student_level = StudentLevel.objects.get(id=student_level_id)
    academic_year_model = Academic_Year.objects.get(id=academic_year_id)
    semester_model = Semester.objects.get(id=semester_id)
    json_student = json.loads(student_ids)

    # Check if attendance has already been taken for this date
    existing_attendance = Attendance.objects.filter(
        student_level_id=student_level,
        attendance_date=attendance_date,
        academic_year_id=academic_year_model,
        semester_id=semester_model
    ).exists()

    if existing_attendance:
        return HttpResponse("ALREADY_TAKEN")

    try:
        attendance = Attendance(
            student_level_id=student_level,
            attendance_date=attendance_date,
            academic_year_id=academic_year_model,
            semester_id=semester_model)
        attendance.save()

        for stud in json_student:
            student = Students.objects.get(admin=stud["id"])
            attendance_report = AttendanceReport(
                student_id=student, attendance_id=attendance, status=stud["status"])
            attendance_report.save()
        return HttpResponse("OK")
    except:
        return HttpResponse("ERROR")



@csrf_exempt
def get_attendance_dates(request):
    #course = request.POST.get("course")
    student_level_id = request.POST.get("student_level_id")
    academic_year_id = request.POST.get("academic_year_id")
    semester_id = request.POST.get("semester_id")
    academic_year_obj = Academic_Year.objects.get(id=academic_year_id)
    semester_obj = Semester.objects.get(id=semester_id)
    #course_obj = Courses.objects.get(id=course)
    student_level_obj = StudentLevel.objects.get(id=student_level_id)
    attendance = Attendance.objects.filter(
        student_level_id=student_level_obj,
        academic_year_id=academic_year_obj, semester_id=semester_obj)
    attendance_obj = []
    for attendance_single in attendance:
        data = {"id": attendance_single.id, "attendance_date": attendance_single.attendance_date,
                "academic_year_id": attendance_single.academic_year_id.id, "semester_id": attendance_single.semester_id.id}
        attendance_obj.append(data)
    return JsonResponse(attendance_obj, safe=False)


@csrf_exempt
def staff_update_attendance(request):
    user = CustomUser.objects.get(id=request.user.id)
    staff = Staffs.objects.get(admin=user)
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
        students = Students.objects.filter(student_level_id=student_level_id)
        attendance_data = []

        for student in students:
            #total_attendance = attendance_reports.count()
            attendance_present = attendance_reports.filter(student_id=student, status=True).count()
            attendance_absent = attendance_reports.filter(student_id=student, status=False).count()

            attendance_data.append({
                'student_name': student.admin.get_full_name(),
                'total_attendance': total_attendance,
                'attendance_present': attendance_present,
                'attendance_absent': attendance_absent,
            })

        return JsonResponse({'attendance_data': attendance_data})

    else:
        student_levels = StudentLevel.objects.filter(staff_id=request.user.id).exclude(level_name="Alumni")
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
            'staff': staff
        }
        return render(request, 'staff_templates/staff_update_attendance.html', context)

@csrf_exempt
def get_attendance_student(request):
    attendance_date = request.POST.get("attendance_date")

    attendance = Attendance.objects.get(id=attendance_date)
    attendance_data = AttendanceReport.objects.filter(attendance_id=attendance)
    list_data = []

    for student in attendance_data:
        data_small = {"id": student.student_id.admin.id, "name": student.student_id.admin.last_name +
                      " "+student.student_id.admin.first_name, "status": student.status}
        list_data.append(data_small)
    return JsonResponse(list_data, content_type="application/json", safe=False)


@csrf_exempt
def save_update_attendance_data(request):
    student_ids = request.POST.get("student_ids")
    attendance_date = request.POST.get("attendance_date")
    attendance = Attendance.objects.get(id=attendance_date)
    json_student = json.loads(student_ids)
    try:

        for stud in json_student:
            student = Students.objects.get(admin=stud["id"])
            attendance_report = AttendanceReport.objects.get(
                student_id=student, attendance_id=attendance)
            attendance_report.status = stud['status']
            attendance_report.save()
        return HttpResponse("OK")
    except:
        return HttpResponse("ERROR")


def staff_add_result(request):
    user = CustomUser.objects.get(id=request.user.id)
    staff = Staffs.objects.get(admin=user)
    # Fetch student levels based on the courses the staff teaches
    courses = Courses.objects.filter(staff_id=request.user.id)
    student_levels = StudentLevel.objects.filter(courses__in=courses).distinct().exclude(level_name="Alumni")
    academic_years = Academic_Year.objects.all()
    semesters = Semester.objects.all()
    settings = SchoolSettings.objects.first()
    current_academic_year = settings.current_academic_year if settings else None
    current_semester = settings.current_semester if settings else None
    return render(request, "staff_templates/staff_add_result.html",
                  {"staff": staff, "user": user, "student_levels": student_levels, "academic_years": academic_years, "semesters": semesters,
                   "courses":courses,"current_academic_year":current_academic_year,"current_semester":current_semester})


def save_student_result(request):
    if request.method != "POST":
        return HttpResponseRedirect(reverse("staff_add_result"))

    semester_id = request.POST.get("semester")
    academic_year_id = request.POST.get("academic_year")
    success_messages = []
    error_messages = []

    try:
        courses_taught_by_staff = Courses.objects.filter(staff_id=request.user.id)

        for student_id in request.POST.getlist("student_id[]"):
            student_obj = get_object_or_404(Students, id=student_id)
            overral_mark = Decimal(0.0)  # Initialize overral_mark as a Decimal

            for course_id in request.POST.getlist(f"course_id_{student_id}[]"):
                course_obj = get_object_or_404(Courses, id=course_id)

                # Ensure the course is taught by the current staff
                if course_obj not in courses_taught_by_staff:
                    error_messages.append(f"You are not authorized to add results for course ID {course_id}.")
                    continue

                try:
                    # Fetch existing result from the database
                    existing_result = StudentResults.objects.filter(
                        student_id=student_obj,
                        course_id=course_obj,
                        academic_year_id=academic_year_id,
                        semester_id=semester_id
                    ).first()

                    if existing_result:
                        existing_individual_test_score = Decimal(existing_result.individual_test_score)
                        existing_group_work_score = Decimal(existing_result.group_work_score)
                        existing_class_test_score = Decimal(existing_result.class_test_score)
                        existing_project_score = Decimal(existing_result.project_score)
                        existing_exam_mark = Decimal((existing_result.exam_mark / 50) * 100)  # Reverse the percentage to get the original input value
                    else:
                        existing_individual_test_score = Decimal(0.0)
                        existing_group_work_score = Decimal(0.0)
                        existing_class_test_score = Decimal(0.0)
                        existing_project_score = Decimal(0.0)
                        existing_exam_mark = Decimal(0.0)

                    # Get the input values and keep existing values if no new input is provided
                    individual_test_score_input = request.POST.get(f'individual_test_score_{student_id}_{course_id}', '')
                    group_work_score_input = request.POST.get(f'group_work_score_{student_id}_{course_id}', '')
                    class_test_score_input = request.POST.get(f'class_test_score_{student_id}_{course_id}', '')
                    project_score_input = request.POST.get(f'project_score_{student_id}_{course_id}', '')
                    exam_mark_input = request.POST.get(f'exam_mark_{student_id}_{course_id}', '')

                    individual_test_score = Decimal(individual_test_score_input) if individual_test_score_input.strip() != '' else existing_individual_test_score
                    group_work_score = Decimal(group_work_score_input) if group_work_score_input.strip() != '' else existing_group_work_score
                    class_test_score = Decimal(class_test_score_input) if class_test_score_input.strip() != '' else existing_class_test_score
                    project_score = Decimal(project_score_input) if project_score_input.strip() != '' else existing_project_score
                    exam_mark = Decimal(exam_mark_input) if exam_mark_input.strip() != '' else existing_exam_mark

                    assignment_mark = Decimal(((individual_test_score + group_work_score + class_test_score + project_score) / 60) * 50).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
                    exam_mark_percentage = Decimal((exam_mark / 100) * 50).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
                    total_mark = assignment_mark + exam_mark_percentage
                    overral_mark += total_mark  # Adding Decimal values
                    overral_mark_average = Decimal(0.0)

                    if total_mark >= 80:
                        grade = "A"
                        remark = "EXCELLENT"
                    elif total_mark >= 70:
                        grade = "B"
                        remark = "VERY GOOD"
                    elif total_mark >= 60:
                        grade = "C"
                        remark = "GOOD"
                    elif total_mark >= 45:
                        grade = "D"
                        remark = "AVERAGE"
                    elif total_mark >= 35:
                        grade = "E"
                        remark = "PASS"
                    else:
                        grade = "F"
                        remark = "FAIL"

                    semester_obj = get_object_or_404(Semester, id=semester_id)
                    academic_year_model = get_object_or_404(Academic_Year, id=academic_year_id)

                    if existing_result:
                        existing_result.individual_test_score = individual_test_score
                        existing_result.group_work_score = group_work_score
                        existing_result.class_test_score = class_test_score
                        existing_result.project_score = project_score
                        existing_result.assignment_mark = assignment_mark
                        existing_result.exam_mark = exam_mark_percentage
                        existing_result.total_mark = total_mark
                        existing_result.overral_mark = overral_mark
                        existing_result.overral_mark_average = overral_mark_average
                        existing_result.grade = grade
                        existing_result.remark = remark
                        existing_result.save()
                    else:
                        StudentResults.objects.create(
                            student_id=student_obj,
                            course_id=course_obj,
                            individual_test_score=individual_test_score,
                            group_work_score=group_work_score,
                            class_test_score=class_test_score,
                            project_score=project_score,
                            assignment_mark=assignment_mark,
                            academic_year_id=academic_year_model,
                            exam_mark=exam_mark_percentage,
                            total_mark=total_mark,
                            overral_mark=overral_mark,
                            overral_mark_average=overral_mark_average,
                            grade=grade,
                            semester_id=semester_obj,
                            remark=remark
                        )

                    success_messages.append(f"Results added/updated successfully for course ID {course_id}.")
                except ValueError:
                    error_messages.append(f"Invalid input for student ID {student_id} and course ID {course_id}. Assignment or Exam mark must be in range!")
                    continue
    except Exception as e:
        messages.error(request, f"An error occurred: {str(e)}")
        return HttpResponseRedirect(reverse("staff_add_result"))

    if success_messages:
        messages.success(request, "Results added/updated successfully.")

    return HttpResponseRedirect(reverse("staff_add_result"))

def profile(request):
    user = CustomUser.objects.get(id=request.user.id)
    staff = Staffs.objects.get(admin=user)
    return render(request, "staff_templates/header.html", {"user": user, "staff": staff})
def staff_profile(request):
    user = CustomUser.objects.get(id=request.user.id)
    staff = Staffs.objects.get(admin=user)
    return render(request, "staff_templates/staff_profile.html", {"user": user, "staff": staff})


def edit_staff_profile_save(request):
    if request.method != "POST":
        return HttpResponseRedirect(reverse("staff_profile"))
    else:
        #first_name = request.POST.get("first_name")
        #last_name = request.POST.get("last_name")
        password = request.POST.get("password")
        address1 = request.POST.get("address1")
        address2 = request.POST.get("address2")
        email = request.POST.get("email")
        #date_of_birth = request.POST.get("date_of_birth")
        phone_number = request.POST.get("phone_number")

        try:
            custom_user = CustomUser.objects.get(id=request.user.id)

            custom_user.email = email
            custom_user.save()
            staff = Staffs.objects.get(admin=custom_user.id)
            staff.address1 = address1
            staff.address2 = address2

            staff.phone_number = phone_number
            #staff.gender = gender
            staff.save()
            messages.success(
                request, "Profile Updated.")
            return HttpResponseRedirect(reverse("staff_profile"))
        except:
            messages.error(request, "owps an error occurred!")
            return HttpResponseRedirect(reverse("staff_profile"))

#Does quasi the same things as json.loads from here: https://pypi.org/project/dynamodb-json/


class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return json.JSONEncoder.default(self, obj)


@csrf_exempt
def fetch_student_results(request):
    course_id = request.POST.get("course_id")
    student_id = request.POST.get("student_id")
    academic_year_id = request.POST.get("academic_year_id")
    semester_id = request.POST.get("semester_id")

    student_obj = get_object_or_404(Students, admin=student_id)
    academic_year_obj = get_object_or_404(Academic_Year, id=academic_year_id)
    semester_obj = get_object_or_404(Semester, id=semester_id)

    result = StudentResults.objects.filter(
        student_id=student_obj,
        course_id=course_id,
        academic_year_id=academic_year_obj,
        semester_id=semester_obj
    ).exists()

    if result:
        result = StudentResults.objects.get(
            student_id=student_obj,
            course_id=course_id,
            academic_year_id=academic_year_obj,
            semester_id=semester_obj
        )
        result_data = {
            "exam_mark": result.exam_mark,
            "assignment_mark": result.assignment_mark
        }
        return HttpResponse(json.dumps(result_data, cls=JSONEncoder))
    else:
        return HttpResponse("False")

def staff_view_all_results(request):
    user = CustomUser.objects.get(id=request.user.id)
    staff = Staffs.objects.get(admin=user)
    courses = Courses.objects.filter(staff_id=request.user.id)
    student_levels = StudentLevel.objects.filter(courses__in=courses).distinct()
    academic_years = Academic_Year.objects.all()
    semesters = Semester.objects.all()
    settings = SchoolSettings.objects.first()
    current_academic_year = settings.current_academic_year if settings else None
    current_semester = settings.current_semester if settings else None
    return render(request, "staff_templates/staff_display_results.html", {
        "student_levels": student_levels,
        "academic_years": academic_years,
        "semesters": semesters,
        "current_academic_year": current_academic_year,
        "current_semester": current_semester,
        "courses": courses,
        "staff": staff
    })

@login_required
def staff_get_student_results(request):
    user = CustomUser.objects.get(id=request.user.id)
    staff = Staffs.objects.get(admin=user)
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

        # Check if the logged-in staff member is associated with the selected level
        staff_assigned_to_level = StudentLevel.objects.filter(id=student_level_id, staff_id=request.user.id).exists()

        if staff_assigned_to_level:
            courses = Courses.objects.filter(student_level_id=student_level).order_by('course_name')
            students = Students.objects.filter(student_level_id=student_level).order_by('admin__last_name')
        else:
            courses = Courses.objects.filter(staff_id=request.user.id, student_level_id=student_level).order_by('course_name')
            students = Students.objects.filter(student_level_id=student_level).order_by('admin__last_name')

        student_results = StudentResults.objects.filter(
            student_id__in=students,
            course_id__in=courses,
            academic_year_id=academic_year,
            semester_id=semester
        ).select_related('student_id', 'course_id').order_by('course_id__course_name')

        # Group results by student
        results_by_student = defaultdict(list)

        for result in student_results:
            results_by_student[result.student_id].append(result)

        if not results_by_student:
            messages.error(request, "No results for the selected criteria.")
            return HttpResponseRedirect("/staff_get_student_results")

        return render(request, "staff_templates/staff_display_results.html", {
            "student_levels": StudentLevel.objects.filter(courses__in=Courses.objects.filter(staff_id=request.user.id)).distinct(),
            "academic_years": Academic_Year.objects.all(),
            "semesters": Semester.objects.all(),
            "results_by_student": dict(results_by_student),
            "student_level_id": student_level_id,
            "academic_year_id": academic_year_id,
            "current_semester": current_semester,
            "current_academic_year": current_academic_year,
            "semester_id": semester_id,
            "staff_assigned_to_level": staff_assigned_to_level,
            "staff": staff
        })

    # Add a response for GET requests to handle initial form display
    settings = SchoolSettings.objects.first()
    current_academic_year = settings.current_academic_year if settings else None
    current_semester = settings.current_semester if settings else None
    return render(request, "staff_templates/staff_display_results.html", {
        "student_levels": StudentLevel.objects.filter(courses__in=Courses.objects.filter(staff_id=request.user.id)).distinct(),
        "academic_years": Academic_Year.objects.all(),
        "semesters": Semester.objects.all(),
        "current_academic_year": current_academic_year,
        "current_semester": current_semester,
        "staff":staff
    })
#function to add position suffix such as 2ND, 3RD, 41ST
def get_position_suffix(position):
    if 10 <= position % 100 <= 20:  # Handle 11th, 12th, 13th, etc.
        suffix = 'TH'
    else:
        suffix = {1: 'ST', 2: 'ND', 3: 'RD'}.get(position % 10, 'TH')
    return suffix

def download_student_results(request, student_level_id, academic_year_id, semester_id):
    settings = SchoolSettings.objects.first()
    if settings and settings.school_reopening_date:
        # Ensure school_reopening_date is a datetime object
        school_reopening_date = settings.school_reopening_date
        formatted_date = school_reopening_date.strftime('%A, %b %d, %Y')
    else:
        formatted_date = None
    academic_year = get_object_or_404(Academic_Year, id=academic_year_id)
    semester = get_object_or_404(Semester, id=semester_id)
    student_level = get_object_or_404(StudentLevel, id=student_level_id)
    students = Students.objects.filter(student_level_id=student_level)
    student_total_marks = []

    attendance_reports = AttendanceReport.objects.filter(
        attendance_id__student_level_id=student_level_id,
        attendance_id__academic_year_id=academic_year_id,
        attendance_id__semester_id=semester_id,
    )

    subject_totals = {}

    for student in students:
        courses = Courses.objects.filter(student_level_id=student.student_level_id)
        student_results = StudentResults.objects.filter(
            student_id=student,
            course_id__in=courses,
            academic_year_id=academic_year,
            semester_id=semester
        )

        for result in student_results:
            if result.course_id.course_name not in subject_totals:
                subject_totals[result.course_id.course_name] = []
            subject_totals[result.course_id.course_name].append((student, result.total_mark))

        total_marks = sum(result.total_mark for result in student_results)
        total_marks = round(float(total_marks))
        student_total_marks.append((student, total_marks))

    student_total_marks.sort(key=lambda x: x[1], reverse=True)
    positions = {student.id: idx + 1 for idx, (student, _) in enumerate(student_total_marks)}

    subject_positions = {}
    for subject, marks in subject_totals.items():
        marks.sort(key=lambda x: x[1], reverse=True)
        subject_positions[subject] = {student.id: idx + 1 for idx, (student, _) in enumerate(marks)}

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, leftMargin=30, rightMargin=30)

    elements = []
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], textColor=colors.black, fontSize=15, alignment=1, spaceAfter=8)
    terminal_title_style = ParagraphStyle('Title', parent=styles['Heading1'], textColor=colors.red, fontSize=10, alignment=1, spaceAfter=5)

    image_path = os.path.join('static', 'assets', 'img', 'clients', 'client-4.png')
    if not os.path.exists(image_path):
        image_path = None

    table_width = 580  # Adjust the table width to fit the page
    info_col_widths = [120, table_width - 120]
    result_col_widths = [170, 70, 70, 70, 60, 60, 80]  # Adjust column widths to fit content

    for idx, (student, total_marks) in enumerate(student_total_marks):
        if image_path:
            logo = Image(image_path, width=50, height=50)
            elements.append(logo)

        elements.append(Paragraph("GREAT ALLIANCE PREPARATORY/JHS", title_style))
        elements.append(Paragraph("TERMINAL REPORT", terminal_title_style))
        elements.append(Spacer(1, 10))

        total_attendance = attendance_reports.values('attendance_id__attendance_date').distinct().count()
        attendance_present = attendance_reports.filter(student_id=student, status=True).count()

        position_suffix = get_position_suffix(positions[student.id])
        position_str = f"{positions[student.id]}{position_suffix}"

        #info_data with 4 columns
        info_data = [
            ['NAME:', f"{student.admin.last_name.upper()} {student.admin.first_name.upper()}",
             'ACADEMIC YEAR:', academic_year.academic_year.upper()],
            ['POSITION:', position_str,
             'TERM:', semester.semester.upper()],
            ['NO. ON ROLL:', f"{students.count()}",
             'ATTENDANCE:', f"{attendance_present} OUT OF {total_attendance}"],
            ['CLASS:', student_level.level_name.upper(),
             'SCHOOL REOPENING DATE:', formatted_date]
        ]

        # Define column widths (adjust these as needed)
        info_col_widths = [77, 226, 147, 130]

        # Create the table with the organized data
        info_table = Table(info_data, colWidths=info_col_widths)

        # Set the style for the table
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))

        elements.append(info_table)
        elements.append(Spacer(1, 10))

        student_results = StudentResults.objects.filter(
            student_id=student,
            course_id__in=courses,
            academic_year_id=academic_year,
            semester_id=semester
        ).select_related('course_id')

        if student_results.exists():
            result_data = [
                [
                    Paragraph('SUBJECTS', styles['Heading5']),
                    Paragraph('CLASS SCORE<br/>50%', styles['Heading5']),
                    Paragraph('EXAMS SCORE<br/>50%', styles['Heading5']),
                    Paragraph('TOTAL SCORE<br/>100%', styles['Heading5']),
                    Paragraph('POSITION IN<br/>SUBJECT', styles['Heading5']),
                    Paragraph('GRADE', styles['Heading5']),
                    Paragraph('REMARKS', styles['Heading5'])
                ]
            ]

            for result in student_results:
                assignment_mark_rounded = round(float(result.assignment_mark))
                exam_mark_rounded = round(float(result.exam_mark))
                total_mark_rounded = round(float(result.total_mark))

                subject_position = subject_positions[result.course_id.course_name][student.id]
                subject_position_suffix = get_position_suffix(subject_position)
                subject_position_str = f"{subject_position}{subject_position_suffix}"

                result_data.append([
                    Paragraph(result.course_id.course_name.upper(), styles['Normal']),
                    assignment_mark_rounded,
                    exam_mark_rounded,
                    total_mark_rounded,
                    subject_position_str,
                    result.grade.upper(),
                    result.remark.upper()
                ])

            # Ensure the TOTAL and other rows are appended properly
            result_data.append(['', '', 'TOTAL', total_marks, '', '', ''])

            # Determine the class teacher's remarks based on conditions
            if student_level.level_name in ["Basic 7", "Basic 8", "Basic 9"] and total_marks >= 600:
                class_teacher_remark = "EXCELLENT PERFORMANCE"
            elif student_level.level_name in ["Basic 7", "Basic 8", "Basic 9"] and total_marks >= 450:
                class_teacher_remark = "GOOD PERFORMANCE"
            elif student_level.level_name in ["Basic 7", "Basic 8", "Basic 9"] and total_marks >= 400:
                class_teacher_remark = "AVERAGE"
            else:
                class_teacher_remark = "MORE ROOM FOR IMPROVEMENT"

            # Adding additional rows for comments and signatures
            conduct_data = [
                ['CONDUCT:', '', '', '', '', '', ''],
                ['INTEREST:', '', '', '', '', '', ''],
                ["CLASS TEACHER'S REMARKS:", class_teacher_remark, '', '', '', '', ''],
                ["HEAD TEACHER'S SIGNATURE:", '', '', '', '', '', ''],
            ]

            # Append conduct_data rows to result_data
            result_data.extend(conduct_data)

            result_table = Table(result_data, colWidths=result_col_widths)
            result_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -6), 'CENTER'),
                ('ALIGN', (0, -4), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('SPAN', (1, -2), (-1, -2)),  # Merge cells from second column for 'CLASS TEACHER'S REMARKS:'
                ('SPAN', (0, -4), (-1, -4)),  # Merge cells for 'CONDUCT:'
                ('SPAN', (0, -3), (-1, -3)),  # Merge cells for 'INTEREST:'
                ('SPAN', (0, -1), (-1, -1)),  # Merge cells for 'HEAD TEACHER'S SIGNATURE:'
                ('LINEABOVE', (0, -5), (-1, -1), 1, colors.black),
                ('LINEBELOW', (0, -1), (-1, -1), 1, colors.black),
                ('LINEBEFORE', (0, -5), (0, -1), 1, colors.black),
                ('LINEAFTER', (-1, -5), (-1, -1), 1, colors.black),

                # New styles for the TOTAL row
                ('FONTNAME', (2, -5), (3, -5), 'Helvetica-Bold'),  # Make 'TOTAL' and 'total_marks' bold
                ('ALIGN', (2, -5), (2, -5), 'RIGHT'),              # Align 'TOTAL' to the right
                ('ALIGN', (3, -5), (3, -5), 'CENTER'),             # Center 'total_marks'
            ]))

            elements.append(result_table)
            elements.append(Spacer(1, 10))

        if idx < len(students) - 1:
            elements.append(PageBreak())

    doc.build(elements)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="student_results_{student_level.level_name}.pdf"'
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)
    return response



def staff_firebase_token_save(request):
    firebase_token = request.POST.get("firebase_token")
    try:
        staff = Staffs.objects.get(admin=request.user.id)
        staff.firebase_token = firebase_token
        staff.save()
        return HttpResponse("True")
    except:
        return HttpResponse("False")


def start_live_classroom(request):
    courses = Courses.objects.filter(staff_id=request.user.id)
    student_level = StudentLevel.objects.all()
    return render(request, "staff_templates/start_live_classroom.html", {"student_level": student_level, "courses": courses})


def start_live_classroom_process(request):
    student_level_id = request.POST.get("student_level")
    course = request.POST.get("course")

    course_obj = Courses.objects.get(id=course)
    student_level_obj = StudentLevel.objects.get(id=student_level_id)
    checks = OnlineClassRoom.objects.filter(
        course=course_obj, student_level_id=student_level_obj, is_active=True).exists()
    if checks:
        data = OnlineClassRoom.objects.get(
            course=course_obj, student_level_id=student_level_obj, is_active=True)
        room_pwd = data.room_pwd
        roomname = data.room_name
    else:
        room_pwd = datetime.now().strftime('%Y%m-%d%H-%M%S-') + str(uuid4())
        roomname = datetime.now().strftime('%Y%m-%d%H-%M%S-') + str(uuid4())
        staff_obj = Staffs.objects.get(admin=request.user.id)
        onlineClass = OnlineClassRoom(room_name=roomname, room_pwd=room_pwd, course=course_obj,
                                      student_level_id=student_level_obj, started_by=staff_obj, is_active=True)
        onlineClass.save()

    return render(request, "staff_templates/live_class_room_start.html", {"username": request.user.username, "password": room_pwd, "roomid": roomname, "course": course_obj.course_name, "student_level": student_level_obj})


def returnHtmlWidget(request):
    return render(request, "widget.html")


@login_required
def instructor_detail(request, course_id):
    #user = request.user
    #instructor = Instructor.objects.get(user=request.user)
    courses = Courses.objects.filter(staff_id=request.user.id)
    course = Courses.objects.get(id=course_id)

    context = {

        'course': course,
        'courses': courses,
    }

    return render(request, 'staff_templates/course_details.html', context)


## @brief view for the course's add-notification page
#
# This view is called by <course_id>/add_notification url.\n
# It returns the webpage containing a form to add notification and redirects to the course's detail page again after the form is submitted.
@login_required
def add_notification(request, course_id):
    form = NotificationForm(request.POST or None)
    course = Courses.objects.get(id=course_id)
    if form.is_valid():
        notification = form.save(commit=False)
        notification.course = course
        # get the current date,time and convert into string
        notification.time = datetime.datetime.now().strftime('%H:%M, %d/%m/%y')
        notification.save()
        return redirect('instructor_detail', course.id)

    return render(request, 'staff_templates/add_notification.html', {'course': course, 'form': form})


## @brief view for the course's add-assignment page.
#
# This view is called by <course_id>/add_assignment url.\n
# It returns the webpage containing a form to add an assignment and redirects to the course's detail page again after the form is submitted.
@login_required
def add_assignment(request, course_id):
    form = AssignmentForm(request.POST or None, request.FILES or None)
    course = Courses.objects.get(id=course_id)
    if form.is_valid():
        assignment = form.save(commit=False)
        assignment.file = request.FILES['file']
        assignment.post_time = datetime.datetime.now().strftime('%H:%M, %d/%m/%y')
        assignment.course = course
        assignment.save()
        notification = Notification()
        notification.content = "New Assignment Uploaded"
        notification.course = course
        notification.time = datetime.datetime.now().strftime('%H:%M, %d/%m/%y')
        notification.save()
        messages.success(request,
                         "Assignment uploaded.")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    return render(request, 'staff_templates/create_assignment.html', {'form': form, 'course': course})


## @brief view for the course's add-resource page.
#
# This view is called by <course_id>/add_resource url.\n
# It returns the webpage containing a form to add a resource and redirects to the course's detail page again after the form is submitted.
@login_required
def add_resource(request, course_id):
    form = ResourceForm(request.POST or None, request.FILES or None)
    staff = Staffs.objects.get(admin=request.user)
    course = Courses.objects.get(id=course_id)
    if form.is_valid():
        resource = form.save(commit=False)
        resource.file_resource = request.FILES['file_resource']
        resource.course = course
        resource.save()
        notification = Notification()
        notification.content = "New Resource Added - " + resource.title
        notification.course = course
        notification.time = datetime.datetime.now().strftime('%H:%M, %d/%m/%y')
        notification.save()
        messages.success(request,
                         "Course material uploaded.")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    return render(request, 'staff_templates/add_resource.html', {'form': form, 'course': course})


## @brief view for the assignments page of a course.
#
# This view is called by <course_id>/view_all_assignments url.\n
# It returns the webpage containing all the assignments of the course and links to their submissions and feedbacks given by the students.
@login_required
def view_all_assignments(request, course_id):
    course = Courses.objects.get(id=course_id)
    assignments = Assignment.objects.filter(course=course)
    return render(request, 'staff_templates/view_all_assignments.html', {'assignments': assignments, 'course': course})


## @brief view for the submissions page of an assignment.
#
# This view is called by <assignment_id>/view_all_submissions url.\n
# It returns the webpage containing links to all the submissions of an assignment.
@login_required
def view_all_submissions(request, assignment_id):
    assignment = Assignment.objects.get(id=assignment_id)
    submissions = Submission.objects.filter(assignment=assignment)
    course = assignment.course
    return render(request, 'staff_templates/view_all_submissions.html', {'submissions': submissions, 'course': course})


## @brief view for the feedback page containing an histogram of all the feddbacks provided by the students.
#
# This view is called by <assignment_id>/view_feedback url.\n
# It returns a webpage containing the feedback received by the students organized in the form of histogram.
@login_required
def view_feedback(request, assignment_id):
    import matplotlib.pyplot as plt
    import numpy as np
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    import matplotlib.ticker as ticker

    assignment = Assignment.objects.get(id=assignment_id)
    submissions = Submission.objects.filter(assignment=assignment)

    # extract the feedbacks from the submissions list
    feedbacks1 = list(map(lambda x: x.feedback, submissions))
    feedbacks = np.array(feedbacks1)

    fig = plt.figure(figsize=(10, 6))
    fig.suptitle('Feedback received from the students',
                 fontsize=16, fontweight='bold')
    fig.subplots_adjust(bottom=0.3)
    ax = fig.add_subplot(111)

    ax.set_xlabel('Rating(out of 10)')
    ax.set_ylabel('Number of Students')
    x = feedbacks
    ax.hist(x, bins=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11], fc='lightblue',
            alpha=1, align='left', edgecolor='black', linewidth=1.0)
    ax.set_xticks([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11])
    # sets the difference between adjacent y-tics
    ax.yaxis.set_major_locator(ticker.MultipleLocator(1))

    plt.figtext(0.2, 0.1, 'Average Rating : ' + str(round(np.mean(feedbacks), 2)),
                bbox={'facecolor': 'lightblue', 'alpha': 0.5, 'pad': 10})  # adds box in graph to display mean rating
    plt.figtext(0.5, 0.1, 'Number of Students Students who rated : ' + str(len(feedbacks1)),
                bbox={'facecolor': 'lightblue', 'alpha': 0.5, 'pad': 10})  # adds box in graph to display number of students who rated

    canvas = FigureCanvasAgg(fig)
    response = HttpResponse(content_type='image/png')
    canvas.print_png(response)  # converts the figure to http response
    return response


def staff_courses(request):
    courses = Courses.objects.filter(staff_id=request.user.id)
    return render(request, "staff_templates/staff_courses.html", {"courses": courses})
