from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns # new
from django.views.static import serve
from django.urls import path, include
from django.urls import re_path, include
from great_alliance_portal import BursarViews, views
from great_alliance_portal import HodViews, StaffViews, StudentViews, EditResultViewClass
from great_alliance_portal.HodViews import InfoListView
from great_alliance_portal.EditResultViewClass import EditResultViewClass
from great_alliance_management_system import settings
from django.contrib import admin
from django.urls import path
#from great_alliance_portal.views import ResetPasswordView
from django.contrib.auth import views as auth_views
from django.contrib.sitemaps.views import sitemap
from django.contrib.sitemaps import views as sitemap_views
from great_alliance_portal.sitemaps import StaticViewSitemap
sitemaps = {
    'static': StaticViewSitemap,
}

urlpatterns = [
    path('sitemap.xml/', sitemap, {'sitemaps': sitemaps}, name='sitemap'),
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
    re_path(r'^static/(?P<path>.*)$', serve, {'document_root': settings.STATIC_ROOT}),
    path('admin/', admin.site.urls),
    #path('account/', include('django.contrib.auth.urls')),
    path('', views.home, name="home"),
    path('login/', auth_views.LoginView.as_view(template_name='login_page.html'), name='login'),
    path('reset_password/', auth_views.PasswordResetView.as_view(
        template_name="password_reset_form.html"), name="reset_password"),
    path('password_reset_confirm/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name="password_reset_confirm.html"),
         name="password_reset_confirm"),
    path('reset_password_sent/', auth_views.PasswordResetDoneView.as_view(template_name="password_reset_done.html"),
         name="password_reset_done"),
    #students url
    path('all_attendance', StaffViews.all_attendance, name="all_attendance"),
    path('reset_password_complete/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name="password_reset_complete.html"),
         name="password_reset_complete"),
    path('do_login', views.DoLogin, name="do_login"),
    path('do_logout', views.Logout_User, name="do_logout"),
    path('update_school_settings', HodViews.update_school_settings, name="update_school_settings"),
    path('admin_homepage', HodViews.admin_homepage, name="admin_homepage"),
    path('hod_all_attendance', HodViews.hod_all_attendance, name="hod_all_attendance"),
    path('hod_view_all_attendance/<int:student_id>', HodViews.hod_view_all_attendance, name="hod_view_all_attendance"),
    #path('header_temp', HodViews.header_temp, name="header_temp"),
    path('students_by_level', HodViews.students_by_level, name='students_by_level'),
    path('student/<int:student_id>/results/', HodViews.view_student_results, name='view_student_results'),
    path('bursar_homepage', BursarViews.bursar_homepage, name="bursar_homepage"),
    path('manage_staffs', HodViews.manage_staffs, name="manage_staffs"),

    path('manage_students', HodViews.manage_students, name="manage_students"),
    path('academic_affairs', HodViews.academic_affairs, name="academic_affairs"),
    path('about', HodViews.about, name="about"),
    path('add_staff', HodViews.add_staff, name="add_staff"),
    path('add_bursar', HodViews.add_bursar, name="add_bursar"),
    path('edit_staff/<str:staff_id>', HodViews.edit_staff, name="edit_staff"),
    path('edit_staff_save', HodViews.edit_staff_save, name="edit_staff_save"),
    path('add_level', HodViews.add_level, name="add_level"),
    path('add_level_save', HodViews.add_level_save, name="add_level_save"),
    path('edit_level/<str:student_level_id>', HodViews.edit_level, name="edit_level"),
    path('edit_level_save', HodViews.edit_level_save, name="edit_level_save"),
    path('manage_level', HodViews.manage_level, name="manage_level"),
    path('fees', HodViews.fees, name="fees"),
    path('fees_save', HodViews.fees_save, name="fees_save"),
    path('add_course', HodViews.add_course, name="add_course"),
    path('add_course_save', HodViews.add_course_save, name="add_course_save"),
    path('view_staffs', HodViews.view_staffs, name="view_staffs"),
    path('view_students', HodViews.view_students, name="view_students"),
    path('view_students', InfoListView.as_view(), name='view_students'),
    path('add_student', HodViews.add_student, name="add_student"),
    path('add_student_save', HodViews.add_student_save, name="add_student_save"),
    path('add_programme', HodViews.add_programme, name="add_programme"),
    path('add_programme_save', HodViews.add_programme_save,
         name="add_programme_save"),
    path('add_academic_year', HodViews.add_academic_year, name="add_academic_year"),
    path('add_academic_year_save', HodViews.add_academic_year_save,
         name="add_academic_year_save"),
    path('add_semester', HodViews.add_semester, name="add_semester"),
    path('add_semester_save', HodViews.add_semester_save, name="add_semester_save"),
    path('alumni', HodViews.alumni, name="alumni"),
    #path('staff_feedback_message', HodViews.staff_feedback_message, name="staff_feedback_message"),
    #path('staff_feedback_message_replied',
    # HodViews.staff_feedback_message_replied, name="staff_feedback_message_replied"),
    path('staff_permissions', HodViews.staff_permissions, name="staff_permissions"),
    path('add_staff_save', HodViews.add_staff_save, name="add_staff_save"),
    path('add_bursar_save', HodViews.add_bursar_save, name="add_bursar_save"),
    path('staff_leave_view', HodViews.staff_leave_view, name="staff_leave_view"),
    path('staff_approve_leave/<str:leave_id>',
         HodViews.staff_approve_leave, name="staff_approve_leave"),
    path('staff_disapprove_leave/<str:leave_id>',
         HodViews.staff_disapprove_leave, name="staff_disapprove_leave"),
    path('check_email_exist', HodViews.check_email_exist, name="check_email_exist"),
    path('check_email2_exist', HodViews.check_email2_exist,
         name="check_email2_exist"),
    path('check_username_exist', HodViews.check_username_exist,
         name="check_username_exist"),
    path('admin_view_attendance', HodViews.admin_view_attendance,
         name="admin_view_attendance"),
    path('admin_get_attendance_dates', HodViews.admin_get_attendance_dates,
         name="admin_get_attendance_dates"),
    path('admin_get_attendance_student', HodViews.admin_get_attendance_student,
         name="admin_get_attendance_student"),
    path('admin_profile', HodViews.admin_profile, name="admin_profile"),
    path('edit_admin_profile_save', HodViews.edit_admin_profile_save,
         name="edit_admin_profile_save"),
    path('admin_view_student_results', HodViews.admin_view_student_results,
         name="admin_view_student_results"),
    path('admin_get_student_results', HodViews.admin_get_student_results,
         name="admin_get_student_results"),
    path('manage_course', HodViews.manage_course, name="manage_course"),
    path('manage_programme', HodViews.manage_programme, name="manage_programme"),
    path('edit_student/<str:student_id>',
         HodViews.edit_student, name="edit_student"),
    #path('delete_student/<str:student_id>',
    #HodViews.delete_student, name="delete_student"),
    path("delete_student/<str:student_id>",
         HodViews.delete_student, name="delete_student"),
    path("delete_staff/<str:staff_id>", HodViews.delete_staff, name="delete_staff"),
    path("delete_bursar/<str:bursar_id>", HodViews.delete_bursar, name="delete_bursar"),
    path('edit_course/<str:course_id>', HodViews.edit_course, name="edit_course"),
    path('edit_programme/<str:programme_id>', HodViews.edit_programme, name="edit_programme"),
    path('edit_programme_save', HodViews.edit_programme_save, name="edit_programme_save"),
    path('edit_course_save', HodViews.edit_course_save, name="edit_course_save"),
    path('edit_student_save', HodViews.edit_student_save, name="edit_student_save"),
    path('all_programmes', HodViews.all_programmes, name="all_programmes"),
    path('academic_sem_selection', HodViews.academic_sem_selection, name="academic_sem_selection"),
    path('admin_view_results_of_pupils', HodViews.admin_view_results_of_pupils, name="admin_view_results_of_pupils"),
    # staff urls
    path('staff_homepage', StaffViews.staff_homepage, name="staff_homepage"),
    path('staff_manage_students',
         StaffViews.staff_manage_students, name="staff_manage_students"),
    path('staff_apply_leave', StaffViews.staff_apply_leave,
         name="staff_apply_leave"),
    path('staff_apply_leave_save', StaffViews.staff_apply_leave_save,
         name="staff_apply_leave_save"),
    #url for staff to view students previous records.
    path('staff_view_students_by_level', StaffViews.staff_view_students_by_level, name='staff_view_students_by_level'),
    path('staff_view_students_results/<int:student_id>/results/', StaffViews.staff_view_students_results, name='staff_view_students_results'),
    path('staff_view_all_attendance/<int:student_id>', StaffViews.staff_view_all_attendance, name="staff_view_all_attendance"),
    path('update_fees/<int:fee_id>/', BursarViews.update_fees, name='update_fees'),
    path('daily_payments/', BursarViews.daily_payments, name='daily_payments'),
    path('view_fees/<int:student_level_id>/', BursarViews.view_fees, name='view_fees'),
    path('download_student_bills/<int:student_level_id>/', BursarViews.download_student_bills, name='download_student_bills'),
    path('select_level_to_view_fees', BursarViews.select_level_to_view_fees, name='select_level_to_view_fees'),
    path('add_fees_to_students', BursarViews.add_fees_to_students, name='add_fees_to_students'),
    path('update_fees_for_all_levels', BursarViews.update_fees_for_all_levels, name="update_fees_for_all_levels"),

    path('get_students', StaffViews.get_students, name="get_students"),
    path('profile', StaffViews.profile, name="profile"),
    path('staff_profile', StaffViews.staff_profile, name="staff_profile"),
    path('edit_staff_profile_save', StaffViews.edit_staff_profile_save,
         name="edit_staff_profile_save"),
    path('staff_about', StaffViews.staff_about, name="staff_about"),
    path('staff_take_attendance', StaffViews.staff_take_attendance,
         name="staff_take_attendance"),
    path('get_students', StaffViews.get_students, name="get_students"),
    path('get_students_by_subjects', StaffViews.get_students_by_subjects,
         name="get_students_by_subjects"),
    path('get_courses_by_level', StaffViews.get_courses_by_level, name='get_courses_by_level'),
    path('enroll-students', StaffViews.enroll_students, name='enroll_students'),
    path('view_students_and_promote', StaffViews.view_students_and_promote, name="view_students_and_promote"),
    path('get_students_for_course/<int:course_id>/', StaffViews.get_students_for_course, name='get_students_for_course'),
    path('save_attendance_data', StaffViews.save_attendance_data,
         name="save_attendance_data"),
    path('get_attendance_dates', StaffViews.get_attendance_dates,
         name="get_attendance_dates"),
    path('get_attendance_student', StaffViews.get_attendance_student,
         name="get_attendance_student"),
    path('staff_update_attendance', StaffViews.staff_update_attendance,
         name="staff_update_attendance"),
    path('save_update_attendance_data', StaffViews.save_update_attendance_data,
         name="save_update_attendance_data"),
    path('staff_add_result', StaffViews.staff_add_result, name="staff_add_result"),
    path('save_student_result', StaffViews.save_student_result,
         name="save_student_result"),
    path('edit_student_result', EditResultViewClass.as_view(),
         name="edit_student_result"),
    path('fetch_student_results', StaffViews.fetch_student_results,
         name="fetch_student_results"),
    path('staff_view_all_results', StaffViews.staff_view_all_results,
         name="staff_view_all_results"),
    path('staff_fcmtoken_save', StaffViews.staff_fcmtoken_save,
         name="staff_fcmtoken_save"),
    path('staff_firebase_token_save', StaffViews.staff_firebase_token_save,
         name="staff_firebase_token_save"),
    path('staff_courses', StaffViews.staff_courses, name="staff_courses"),
    re_path(r'^(?P<course_id>[0-9]+)/add_assignment/$',
            StaffViews.add_assignment, name='add_assignment'),
    re_path(r'^(?P<course_id>[0-9]+)/add_resource/$',
            StaffViews.add_resource, name='add_resource'),
    re_path(r'^(?P<course_id>[0-9]+)/add_notification/$',
            StaffViews.add_notification, name='add_notification'),
    re_path(r'^(?P<course_id>[0-9]+)/view_all_assignments/$',
            StaffViews.view_all_assignments, name='view_all_assignments'),
    re_path(r'^(?P<assignment_id>[0-9]+)/view_all_submissions/$',
            StaffViews.view_all_submissions, name='view_all_submissions'),
     #Newly added.
    path('staff_get_student_results', StaffViews.staff_get_student_results, name='staff_get_student_results'),
    path('download_student_results/<int:student_level_id>/<int:academic_year_id>/<int:semester_id>/', StaffViews.download_student_results, name='download_student_results'),

    #student urls
    path('student_homepage', StudentViews.student_homepage, name="student_homepage"),
    re_path(r'^(?P<course_id>[0-9]+)/detail/$',
            StudentViews.detail, name='detail'),
    #url(r'^index/$', views.index, name='index'),
    re_path(r'^(?P<assignment_id>[0-9]+)/upload_submission/$',
            StudentViews.upload_submission, name='upload_submission'),
    re_path(r'^(?P<course_id>[0-9]+)/view_assignments/$',
            StudentViews.view_assignments, name='view_assignments'),
    re_path(r'^(?P<course_id>[0-9]+)/view_resources/$',
            StudentViews.view_resources, name='view_resources'),
    path('student_profile', StudentViews.student_profile, name="student_profile"),
    path('edit_student_profile_save', StudentViews.edit_student_profile_save,
         name="edit_student_profile_save"),
    path('courses', StudentViews.courses, name="courses"),
    path('student_view_results', StudentViews.student_view_results,
         name="student_view_results"),
    path('student_get_results', StudentViews.student_get_results,
         name="student_get_results"),
    #website urls
    path('join_class_room/<int:course_id>/<int:student_level_id>',
         StudentViews.join_class_room, name="join_class_room"),
    path('student_view_attendance', StudentViews.student_view_attendance,
         name="student_view_attendance"),
    path('student_view_attendance_post', StudentViews.student_view_attendance_post,
         name="student_view_attendance_post"),
    path('web_home', views.web_home, name="web_home"),
]+static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)+static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
if not settings.DEBUG: 
     urlpatterns += re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),re_path(r'^static/(?P<path>.*)$', serve, {'document_root': settings.STATIC_ROOT}),