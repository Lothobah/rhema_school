from django.shortcuts import render
from django.views import View
from great_alliance_portal.forms import EditResultForm
from great_alliance_portal.models import *
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.contrib import messages


class EditResultViewClass(View):
    def get(self, request, *args, **kwargs):
        staff_id = request.user.id
        edit_result_form = EditResultForm(staff_id=staff_id)
        academic_year = Academic_Year.objects.all()
        semester = Semester.objects.all()
        return render(request, "staff_templates/staff_edit_result.html",
                      {"form": edit_result_form, "academic_year": academic_year,
                      "semester":semester}) 

    def post(self, request, *args, **kwargs):
        form = EditResultForm(request.POST, staff_id=request.user.id)
        if form.is_valid():
            student_admin_id = form.cleaned_data['student_id']
            assignment_mark = float(form.cleaned_data['assignment_mark'])
            exam_mark = float(form.cleaned_data['exam_mark'])
            total_mark = assignment_mark + exam_mark
            course_id = form.cleaned_data['course_id']
            student_obj = Students.objects.get(admin=student_admin_id)
            course_obj = Courses.objects.get(id=course_id)
            result = StudentResults.objects.get(
                student_id=student_obj, course_id=course_obj)
            result.exam_mark = exam_mark
            result.assignment_mark = assignment_mark
            result.total_mark = total_mark
            result.save()
            messages.success(request, "Results updated")
            return HttpResponseRedirect(reverse("edit_student_result"))
        else:
            form = EditResultForm(request.POST, staff_id=request.user.id)
            messages.error(request, "Error updating results")
            return render(request, "staff_templates/staff_edit_result.html", {"form": form})
