from django import forms
from django.forms import ChoiceField
#from Student_Management_System.HodViews import Courses
from great_alliance_portal.models import *
from django.forms import ModelForm

class ChoiceValidation(ChoiceField):
    def validate(self, value):
        pass


class DateInput(forms.DateInput):  # class to print date in student form
    input_type = "date"
class SchoolSettingsForm(forms.ModelForm):
    class Meta:
        model = SchoolSettings
        fields = ['current_academic_year', 'current_semester', 'school_reopening_date']
        widgets = {
            'current_academic_year': forms.Select(attrs={'class': 'form-control'}),
            'current_semester': forms.Select(attrs={'class': 'form-control'}),
            'school_reopening_date': forms.DateInput(attrs={'class': 'form-control', "type": "date"}),
        }
class PromoteStudentsForm(forms.Form):
    next_level = forms.ModelChoiceField(queryset=StudentLevel.objects.all(), label="Next Level",
        widget=forms.Select(attrs={'class': 'form-control'}))


class EnrollStudentsForm(forms.Form):
    course = forms.ModelChoiceField(
        queryset=Courses.objects.none(),
        label="Select Course",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    students = forms.ModelMultipleChoiceField(
        queryset=Students.objects.none(),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        label="Select Students"
    )

    def __init__(self, *args, **kwargs):
        staff = kwargs.pop('staff', None)
        super(EnrollStudentsForm, self).__init__(*args, **kwargs)
        if staff:
            self.fields['course'].queryset = Courses.objects.filter(staff_id=staff)
            self.fields['course'].label_from_instance = lambda obj: f"{obj.course_name} ({obj.course_code})"

        if 'course' in self.data:
            try:
                course_id = int(self.data.get('course'))
                selected_course = Courses.objects.get(id=course_id)
                students_queryset = Students.objects.filter(student_level_id=selected_course.student_level_id)
                self.fields['students'].queryset = students_queryset
            except (ValueError, TypeError, Courses.DoesNotExist):
                self.fields['students'].queryset = Students.objects.none()
        else:
            self.fields['students'].queryset = Students.objects.none()

class AddStaffForm(forms.Form):
    title_choice = (
        ("", "-----------"),
        ("Mr.", "Mr."),
        ("Mrs.", "Mrs."),
        ("Miss", "Miss"),
        ("Rev.", "Rev."),

    )
    title = forms.ChoiceField(label="Title:", choices=title_choice,
                          widget=forms.Select(attrs={"class": "form-control"}), required=True)
    first_name = forms.CharField(max_length=50, label="Other Name(s)", widget=forms.TextInput(
        attrs={"class": "form-control", "placeholder": "Other Name(s)"}))
    last_name = forms.CharField(label="Surname",
                                max_length=50, widget=forms.TextInput(attrs={"class": "form-control",
           "placeholder": "Surname"}))
    date_of_birth = forms.CharField(label="Date of Birth",
                                    widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}))
    gender_choice = (
        ("", "-----------"),
        ("Male", "Male"),
        ("Female", "Female"),
    )
    gender = forms.ChoiceField(label="Gender", choices=gender_choice,
                          widget=forms.Select(attrs={"class": "form-control"}))
    phone_number = forms.CharField(
        max_length=10, widget=forms.TextInput(
            attrs={"class": "form-control", "autocomplete": "off", "pattern": "[0-9]+",
                   "placeholder": "eg. 0240000000 "}))
    email = forms.EmailField(max_length=50, label="Email:", widget=forms.EmailInput(
        attrs={"class": "form-control", "color": "red", "autocomplete": "off",
               "placeholder": "Email"}))
    address1 = forms.CharField(max_length=50, label="Postal Address",
                               widget=forms.TextInput(attrs={"class": "form-control", "autocomplete": "off"}))
    address2 = forms.CharField(max_length=50, label="Residential Address",
                               widget=forms.TextInput(attrs={"class": "form-control", "autocomplete": "off"}))

    staff_profile_pic = forms.FileField(label="Profile Pic", max_length=50, widget=forms.FileInput(
        attrs={"class": "form-control"}
    ), required=True)


class AddBursarForm(forms.Form):
    title_choice = (
        ("", "-----------"),
        ("Mr.", "Mr."),
        ("Mrs.", "Mrs."),
        ("Miss", "Miss"),
        ("Rev.", "Rev."),

    )
    title = forms.ChoiceField(label="Title:", choices=title_choice,
                          widget=forms.Select(attrs={"class": "form-control"}), required=True)
    first_name = forms.CharField(max_length=50, label="Other Name(s)", widget=forms.TextInput(
        attrs={"class": "form-control", "placeholder": "Other Name(s)"}))
    last_name = forms.CharField(label="Surname",
                                max_length=50, widget=forms.TextInput(attrs={"class": "form-control",
                        "placeholder": "Surname"}))
    date_of_birth = forms.CharField(label="Date of Birth",
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}))
    gender_choice = (
        ("", "------------"),
        ("Male", "Male"),
        ("Female", "Female"),

    )
    gender = forms.ChoiceField(label="Gender", choices=gender_choice,
                               widget=forms.Select(attrs={"class": "form-control"}), required=True)
    '''phone_number = forms.RegexField(
    regex=r'^\d{10}$',
    max_length=10,
    widget=forms.TextInput(
        attrs={"class": "form-control", "autocomplete": "off",
               "placeholder": "eg. 0240000000"}
    ),
    error_messages={'invalid': 'Enter a valid phone number with 10 digits.'}
    )'''
    phone_number = forms.CharField(
        max_length=10, widget=forms.TextInput(
            attrs={"class": "form-control", "autocomplete": "off", "pattern": "[0-9]+",
                   "placeholder": "eg. 0240000000 "}))
    email = forms.EmailField(max_length=50, label="Email:", widget=forms.EmailInput(
        attrs={"class": "form-control", "color": "red", "autocomplete": "off",
               "placeholder": "Email"}))

    address1 = forms.CharField(max_length=50, label="Postal Address",
                               widget=forms.TextInput(attrs={"class": "form-control", "autocomplete": "off"}))
    address2 = forms.CharField(max_length=50, label="Residential Address",
                               widget=forms.TextInput(attrs={"class": "form-control", "autocomplete": "off"}))

    staff_profile_pic = forms.FileField(label="Profile Pic", max_length=50, widget=forms.FileInput(
        attrs={"class": "form-control"}
    ))

class EditBursarForm(forms.Form):
    #email = forms.EmailField(label="Email:", max_length=50, widget=forms.EmailInput(
        #attrs={"class": "form-control", "autocomplete": "off"}))
    first_name = forms.CharField(label="Surname", max_length=50, widget=forms.TextInput(
        attrs={"class": "form-control"}))
    last_name = forms.CharField(label="Other Name(s)",
                max_length=50, widget=forms.TextInput(attrs={"class": "form-control"}))

    username = forms.CharField(label="Username", max_length=50, widget=forms.TextInput(
        attrs={"class": "form-control", "autocomplete": "off"}))
    address1 = forms.CharField(label="Postal Address", max_length=50,
                               widget=forms.TextInput(attrs={"class": "form-control", "autocomplete": "off"}))
    address2 = forms.CharField(label="Residential Address", max_length=50,
                               widget=forms.TextInput(attrs={"class": "form-control", "autocomplete": "off"}))

    phone_number = forms.CharField(label="Contact:",
                                   max_length=10, widget=forms.TextInput(
                                       attrs={"class": "form-control", "autocomplete": "off", "pattern": "[0-9]+"}))

    date_of_birth = forms.CharField(label="Date of Birth",
                                    widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}))
    staff_profile_pic = forms.FileField(
        label="Profile Pic", required=False, widget=forms.FileInput(
            attrs={"class": "form-control"}
        ))


class EditStaffForm(forms.Form):
    email = forms.EmailField(label="Email:", max_length=50, widget=forms.EmailInput(
        attrs={"class": "form-control", "autocomplete": "off"}))
    first_name = forms.CharField(label="Surname", max_length=50, widget=forms.TextInput(
        attrs={"class": "form-control"}))
    last_name = forms.CharField(label="Other Name(s)",
                                max_length=50, widget=forms.TextInput(attrs={"class": "form-control"}))

    username = forms.CharField(label="Username", max_length=50, widget=forms.TextInput(
        attrs={"class": "form-control", "autocomplete": "off"}))
    address1 = forms.CharField(label="Postal Address", max_length=50,
                               widget=forms.TextInput(attrs={"class": "form-control", "autocomplete": "off"}))
    address2 = forms.CharField(label="Residential Address", max_length=50,
                               widget=forms.TextInput(attrs={"class": "form-control", "autocomplete": "off"}))

    phone_number = forms.CharField(label="Contact:",
                                   max_length=10, widget=forms.TextInput(
                                       attrs={"class": "form-control", "autocomplete": "off", "pattern": "[0-9]+"}))

    date_of_birth = forms.CharField(label="Date of Birth",
                                    widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}))
    staff_profile_pic = forms.FileField(
        label="Profile Pic", required=False, widget=forms.FileInput(
            attrs={"class": "form-control"}
        ))


class AddStudentForm(forms.Form):
    #email = forms.EmailField(label="Email", max_length=50, widget=forms.EmailInput(
        #attrs={"class": "form-control", "autocomplete": "off", "placeholder": "Student Email"}))
    last_name = forms.CharField(label="Surname:",
        max_length=50, widget=forms.TextInput(attrs={"class": "form-control",
             "placeholder": "Surname"}))
    first_name = forms.CharField(label="Other Name(s)", max_length=50, widget=forms.TextInput(
        attrs={"class": "form-control", "placeholder":
               "Other Name(s)"}), required=True)
    home_town = forms.CharField(label="Residential Address:", max_length=50, widget=forms.TextInput(
        attrs={"class": "form-control", "placeholder": "Enter student's hometown"}))
    #classes = Classes.objects.all()
    gender_choice = (
        ("", "--------------"),
        ("Male", "Male"),
        ("Female", "Female"),
    )

    date_of_birth = forms.CharField(label="Date Of Birth:",
                                    widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}), required=True)
    gender = forms.ChoiceField(label="Gender", choices=gender_choice,
                               widget=forms.Select(attrs={"class": "form-control"}), required=True )
    parent_name = forms.CharField(label="Guardian's Name:",
                                  max_length=100, widget=(
                                      forms.TextInput(attrs={"class": "form-control", "placeholder": "Gaurdians's Name "})), required=True)
    parent_phone = forms.CharField(label=" Guardian's Contact:", max_length=10,
                                   widget=forms.TextInput(attrs={"class": "form-control", "pattern": "[0-9]+",
                                                                 "placeholder": "eg. 0240000000"}))
    #academic_year=forms.ChoiceField(label="Academic Year",widget=forms.Select(attrs={"class":"form-control"}),choices=academic_year_list)
    #profile_pic = forms.FileField(label="Profile Pic:", max_length=50, widget=forms.FileInput(
        #attrs={"class": "form-control"}
    #))


class EditStudentForm(forms.Form):
    #email = forms.EmailField(label="Email", max_length=50, widget=forms.EmailInput(
        #attrs={"class": "form-control", "autocomplete": "off"}))
    first_name = forms.CharField(label="First Name", max_length=50, widget=forms.TextInput(
        attrs={"class": "form-control"}))
    last_name = forms.CharField(label="Other Name(s)", max_length=50,
                                widget=forms.TextInput(attrs={"class": "form-control"}))

    username = forms.CharField(label="Username", max_length=50, widget=forms.TextInput(
        attrs={"class": "form-control"}))
    home_town = forms.CharField(label="Home Town", max_length=50, widget=forms.TextInput(
        attrs={"class": "form-control"}))
    #profile_pic = forms.FileField(
        #label="Profile Pic", required=False, widget=forms.FileInput(
            #attrs={"class": "form-control"}
        #))
    parent_name = forms.CharField(label="Guardian's Name", max_length=100, widget=(
        forms.TextInput(attrs={"class": "form-control"})))
    parent_phone = forms.CharField(label="Guardian's Contact:", max_length=10,
                                   widget=forms.TextInput(attrs={"class": "form-control"}))


class EditResultForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.staff_id = kwargs.pop("staff_id")
        super(EditResultForm, self).__init__(*args, **kwargs)
        course_list = []
        try:
            courses = Courses.objects.filter(staff_id=self.staff_id)
            sorted_courses = courses.order_by("course_name")
            for course in sorted_courses:
                course_single = (course.id, course.course_name +
                                 "..."+course.programme_id.programme_name)
                course_list.append(course_single)
        except:
            course_list = []
        self.fields['course_id'].choices = course_list
    academic_year_list = []
    try:
        academic_years = Academic_Year.objects.all()
        for academic_year in academic_years:
            academic_year_single = (
                academic_year.id, str(academic_year.academic_year))
            academic_year_list.append(academic_year_single)
    except:
        academic_year_list = []

    semester_list = []
    try:
        semester = Semester.objects.all()
        for semester in semester:
            semester_single = (
                semester.id, str(semester.semester))
            semester_list.append(semester_single)
    except:
        academic_year_list = []
    course_id = forms.ChoiceField(
        label="Select Course", widget=forms.Select(attrs={"class": "form-control"}))
    academic_year_id = forms.ChoiceField(
        label="Academic Year", choices=academic_year_list, widget=forms.Select(attrs={"class": "form-control"}))
    semester_id = forms.ChoiceField(
        label="Semester", choices=semester_list, widget=forms.Select(attrs={"class": "form-control"}))
    student_id = ChoiceValidation(
        label="Student", widget=forms.Select(attrs={"class": "form-control"}))
    assignment_mark = forms.CharField(label="Assignment Mark", widget=forms.TextInput(
        attrs={"class": "form-control", "autocomplete": "off"}))
    exam_mark = forms.CharField(label="Exam Mark", widget=forms.TextInput(
        attrs={"class": "form-control", "autocomplete": "off"}))

## @brief This class represents the form to add a notification.


class NotificationForm(forms.ModelForm):

    class Meta:
        model = Notification
        fields = ['content']


## @brief This class represents the form to add an assignment.
class AssignmentForm(forms.ModelForm):
    required_css_class = 'required_field'
    description = forms.CharField(widget=forms.TextInput(attrs={
        "class": "form-control", "placeholder": "Enter assignment description"
    }))
    file = forms.FileField(label="Upload Assignment", widget=forms.FileInput(
        attrs={"class": "form-control"}
    ))
    deadline = forms.CharField(widget=forms.TextInput(attrs={
        "class": "form-control", "placeholder": "Enter assignment deadline"
    }))

    class Meta:
        model = Assignment
        fields = ['description', 'file', 'deadline']


## @brief This class represents the form to add a resource.
class ResourceForm(forms.ModelForm):
    required_css_class = 'required-field'
    title = forms.CharField(widget=forms.TextInput(
        attrs={"class": "form-control", "placeholder": "Enter title of resource."}), label="Title")
    file_resource = forms.FileField(label="Upload Resource", widget=forms.FileInput(
        attrs={"class": "form-control"}
    ))

    class Meta:

        model = Resources
        fields = ['title', 'file_resource']


## @brief This class represents the form to add a submission for an assignment.
class SubmissionForm(forms.ModelForm):
    required_css_class = 'required-field'
    file_submitted = forms.FileField(widget=forms.FileInput(attrs={
        "class": "form-control"
    }))

    class Meta:
        model = Submission
        fields = ['file_submitted']
