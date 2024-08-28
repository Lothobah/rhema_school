from decimal import Decimal, InvalidOperation
import decimal
from django.utils import timezone
from io import BytesIO
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from great_alliance_portal.models import Bursar, Payment, StudentLevel, Students, Fees, SchoolSettings
from django.contrib import messages
from django.db.models import Q
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.platypus import Image
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.platypus.flowables import PageBreak
import io
import os
from reportlab.lib.fonts import tt2ps
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import datetime
from django.db.models import Sum
from django.utils.dateformat import format
from django.contrib.humanize.templatetags.humanize import intcomma
from django.http import JsonResponse

def bursar_homepage(request):
    bursar = Bursar.objects.get(admin=request.user.id)
    return render(request, "bursar_templates/bursar_homepage.html", {
        "bursar":bursar
    })
def select_level_to_view_fees(request):
    bursar = Bursar.objects.get(admin=request.user.id)
    if request.method == 'POST':
        student_level_id = request.POST.get("student_level")
        return redirect('view_fees', student_level_id=student_level_id)

    student_levels = StudentLevel.objects.all().order_by("level_name")
    return render(request, 'bursar_templates/select_level_to_view_fees.html', {'student_levels': student_levels, 'bursar': bursar})


def view_fees(request, student_level_id):
    bursar = Bursar.objects.get(admin=request.user.id)
    student_level = get_object_or_404(StudentLevel, id=student_level_id)

    # Get all students associated with the student level
    students = Students.objects.filter(student_level_id=student_level_id).order_by("admin__last_name")

    # Initialize counters
    students_with_full_payment_count = 0
    students_owing_count = 0

    # Get fees for each student
    fees_by_level = {}
    for student in students:
        # Filter fees based on the search query if present
        search_query = request.GET.get('search_query')
        if search_query:
            fees = Fees.objects.filter(
                Q(student_id=student) &
                (Q(student_id__admin__first_name__icontains=search_query) |
                 Q(student_id__admin__last_name__icontains=search_query))
            )
        else:
            fees = Fees.objects.filter(student_id=student)

        # Count students with full payment and students owing
        for fee in fees:
            if fee.overall_fees == 0:
                students_with_full_payment_count += 1
            else:
                students_owing_count += 1

        fees_by_level[student] = fees

    return render(request, 'bursar_templates/view_fees.html', {
        'student_level': student_level,
        'fees_by_level': fees_by_level,
        'bursar': bursar,
        'students_with_full_payment_count': students_with_full_payment_count,
        'students_owing_count': students_owing_count,
    })


def get_cedi_image():
    # Provide the correct path to the Cedi image
    cedi_image_path = os.path.join('great_alliance_portal', 'static', 'images', 'cedi_symbol.png')
    return Image(cedi_image_path, width=10, height=10)

def download_student_bills(request, student_level_id):
    student_level = get_object_or_404(StudentLevel, id=student_level_id)
    students = Students.objects.filter(student_level_id=student_level_id)

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, leftMargin=30, rightMargin=30)
    elements = []
    styles = getSampleStyleSheet()
    # Use standard fonts like Helvetica
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontName='Helvetica', textColor=colors.black, fontSize=15, alignment=1, spaceAfter=8)
    terminal_title_style = ParagraphStyle('Title', parent=styles['Heading1'], textColor=colors.red, fontSize=10, alignment=1, spaceAfter=5)
    student_bill = ParagraphStyle('Title', parent=styles['Heading1'], textColor=colors.black, fontSize=8, alignment=1, spaceAfter=5)
    amount_due_style = ParagraphStyle('Title', parent=styles['Heading1'], textColor=colors.black, fontSize=10, alignment=1, spaceAfter=10, leftIndent=86)
    centered_style = ParagraphStyle(
    'CenteredStyle',
    parent=styles['Heading5'],
    alignment=1,  # Center alignment
    fontName='Helvetica',
    fontSize=12,
    textColor=colors.black,
)

    image_path = os.path.join('great_alliance', 'static', 'assets', 'img', 'clients', 'client-4.png')
    if not os.path.exists(image_path):
        image_path = None

    info_col_widths = [120, 360]
    fee_col_widths = [160, 180, 140]

    current_date = datetime.now().strftime('%d-%b-%Y')

    for idx, student in enumerate(students):
        if image_path:
            logo = Image(image_path, width=50, height=50)
            elements.append(logo)

        elements.append(Paragraph("GREAT ALLIANCE PREPARATORY SCHOOL", title_style))
        elements.append(Paragraph("POST OFFICE BOX 104, DUADASO - SAMPA",terminal_title_style ))
        elements.append(Paragraph("STUDENT BILL",student_bill ))
        elements.append(Spacer(1, 4))

        # Information section
        info_data = [
            ['NAME:', f"{student.admin.first_name.upper()} {student.admin.last_name.upper()}"],
            #['ACCOUNT NUMBER:', student.admin.first_name],  # Assuming there's an account number field
            ['CLASS:', student_level.level_name.upper()],  # Assuming 'level_name' is JHS
            ['DATE PRINTED:', current_date],  # Placeholder for date printed.
        ]
        info_table = Table(info_data, colWidths=info_col_widths)
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))

        elements.append(info_table)
        elements.append(Spacer(1, 4))

        # Fees section
        fees = Fees.objects.filter(student_id=student)
        if fees.exists():
            fee_data = [
                [
                    Paragraph('ITEM', centered_style),
                    Paragraph('DEBIT GHS', centered_style),
                    #Paragraph('P', centered_style),
                    Paragraph('CREDIT GHS', centered_style)
                    #Paragraph('P', centered_style)
                ]
            ]

            for fee in fees:
                fee_data.extend([
                    ['School Fees', f"{fee.school_fees:.2f}",''],
                    ['Extra Classes', f"{fee.extra_classes:.2f}",''],
                    ['Stationary', f"{fee.stationary:.2f}",''],
                    ['Sport/culture', f"{fee.sport_culture:.2f}",''],
                    ['I.C.T', f"{fee.ict:.2f}",''],
                    ['P.T.A', f"{fee.pta:.2f}",''],
                    ['Maintenance', f"{fee.maintenance:.2f}",''],
                    ['Light Bill', fee.light_bill,''],
                    ['TOTAL', f"{fee.total_fees:.2f}",''],
                    ['Arrears From Last Term', f"{fee.arrears_from_last_term:.2f}",''],
                ])

            fee_table = Table(fee_data, colWidths=fee_col_widths)
            fee_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),  # Ensure the font is used for headers
                ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))

            elements.append(fee_table)
            elements.append(Spacer(1, 10))

            # Amount due section with overall fees
            elements.append(Paragraph(
                f"AMOUNT DUE DEBIT GHS {fee.overall_fees:.2f}"
                f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
                f"AMOUNT DUE CREDIT GHS {fee.balance_carry_forward:.2f}",
                amount_due_style
            ))
            elements.append(Spacer(1, 5))

        # Bursar section
        elements.append(Paragraph("BURSAR.........................", student_bill))
        elements.append(Spacer(1, 8))

        if idx < len(students) - 1:
            elements.append(PageBreak())

    doc.build(elements)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="student_fees_{student_level.level_name}.pdf"'
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)
    return response


def update_fees(request, fee_id):
    bursar = Bursar.objects.get(admin=request.user.id)
    fee = get_object_or_404(Fees, id=fee_id)
    settings = SchoolSettings.objects.first()
    current_academic_year = settings.current_academic_year if settings else None
    current_semester = settings.current_semester if settings else None

    if request.method == 'POST':
        amount_paid_str = request.POST.get("amount_paid")
        arrears_str = request.POST.get("arrears_from_last_term")

        try:
            amount_paid = Decimal(amount_paid_str) if amount_paid_str else Decimal('0.00')
        except InvalidOperation:
            return render(request, 'bursar_templates/update_fees.html', {'fee': fee, 'error_message': 'Invalid amount paid'})

        try:
            arrears_from_last_term = Decimal(arrears_str) if arrears_str else None
        except InvalidOperation:
            return render(request, 'bursar_templates/update_fees.html', {'fee': fee, 'error_message': 'Invalid arrears from last term'})

        if amount_paid < 0:
            return render(request, 'bursar_templates/update_fees.html', {'fee': fee, 'error_message': 'Amount paid cannot be negative'})

        if arrears_from_last_term is not None and not fee.arrears_entered:
            fee.arrears_from_last_term = arrears_from_last_term
            fee.overall_fees += arrears_from_last_term
            if arrears_from_last_term > Decimal('0.00'):
                fee.arrears_entered = True  # Set the flag to True

        if amount_paid > fee.overall_fees:
            fee.balance_carry_forward += amount_paid - fee.overall_fees
            fee.overall_fees = Decimal('0.00')
            fee.arrears_from_last_term = Decimal('0.00')
        else:
            fee.overall_fees -= amount_paid
            if fee.arrears_from_last_term:
                fee.arrears_from_last_term -= amount_paid
                if fee.arrears_from_last_term < Decimal('0.00'):
                    fee.arrears_from_last_term = Decimal('0.00')

        fee.amount_paid = fee.amount_paid + amount_paid if fee.amount_paid else amount_paid
        fee.save()

        # Create a Payment record
        Payment.objects.create(
            student=fee.student_id,
            amount_paid=amount_paid,
            semester=current_semester,
            academic_year=current_academic_year
        )

        if ((amount_paid or 0.00) == 0.00 and (arrears_from_last_term or 0.00) > 0.00) or ((amount_paid or 0.00) == 0.00 and arrears_from_last_term is None) or ((amount_paid or 0.00) == 0.00 and (arrears_from_last_term or 0.00) == 0.00):
            return redirect('view_fees', student_level_id=fee.student_id.student_level_id.id)
        else:
            messages.success(request, f"Payment of GHS{amount_paid} for {fee.student_id.admin.first_name} has been recorded, and the balance updated.")
            return render(request, 'bursar_templates/update_fees.html', {'fee': fee, 'bursar': bursar})

    return render(request, 'bursar_templates/update_fees.html', {'fee': fee, 'bursar': bursar})

def daily_payments(request):
    bursar = Bursar.objects.get(admin=request.user.id)
    settings = SchoolSettings.objects.first()
    academic_years = Payment.objects.values_list('academic_year__academic_year', flat=True).distinct()
    semesters = Payment.objects.values_list('semester__semester', flat=True).distinct()

    current_academic_year = request.GET.get('academic_year', settings.current_academic_year if settings else None)
    current_semester = request.GET.get('semester', settings.current_semester if settings else None)

    # Calculate overall payment total for the selected semester and academic year
    overall_payment_total = Payment.objects.filter(
        semester__semester=current_semester,
        academic_year__academic_year=current_academic_year
    ).aggregate(overall_total=Sum('amount_paid'))['overall_total'] or 0

    # Filter payments by selected academic year and semester
    payments_by_date = Payment.objects.filter(
        semester__semester=current_semester,
        academic_year__academic_year=current_academic_year
    ).values('date').annotate(total_paid=Sum('amount_paid')).order_by('-date')

    payments = Payment.objects.filter(
        semester__semester=current_semester,
        academic_year__academic_year=current_academic_year
    ).select_related('student__admin').values(
        'date',
        'student__admin__first_name',
        'student__admin__last_name',
        'student__student_level_id__level_name'
    ).annotate(total_paid=Sum('amount_paid')).order_by('-date', 'student__student_level_id__level_name', 'student__admin__last_name')

    daily_records = {}
    for payment in payments:
        date = payment['date']
        student_last_name = f"{payment['student__admin__last_name']}"
        student_first_name = f"{payment['student__admin__first_name']}"
        student_level = payment['student__student_level_id__level_name']
        amount_paid = payment['total_paid']
        record = {'student_last_name': student_last_name, 'student_first_name': student_first_name, 'student_level': student_level, 'total_paid': amount_paid}

        # Access total_paid directly from payments_by_date queryset
        total_paid_for_date = next((item['total_paid'] for item in payments_by_date if item['date'] == date), 0)

        if date not in daily_records:
            daily_records[date] = {'students': [], 'total_paid': total_paid_for_date}
        daily_records[date]['students'].append(record)

    context = {
        'bursar': bursar,
        'overall_payment_total': overall_payment_total,
        'daily_records': daily_records,
        'academic_years': academic_years,
        'semesters': semesters,
        'current_academic_year': current_academic_year,
        'current_semester': current_semester
    }

    return render(request, 'bursar_templates/daily_payments.html', context)

def check_fees_for_level(request):
    student_level_id = request.GET.get("student_level_id")
    if not student_level_id:
        return JsonResponse({"exists": False})

    student_level = get_object_or_404(StudentLevel, id=student_level_id)
    fees = Fees.objects.filter(student_level_id=student_level).first()

    if fees:

        data = {
            "exists": True,
            "level_name": fees.student_level_id.level_name,
            "school_fees": str(fees.school_fees),
            "extra_classes": str(fees.extra_classes),
            "stationary": str(fees.stationary),
            "sport_culture": str(fees.sport_culture),
            "ict": str(fees.ict),
            "pta": str(fees.pta),
            "maintenance": str(fees.maintenance),
            "light_bill": str(fees.light_bill),
        }
    else:
        data = {"exists": False}

    return JsonResponse(data)

def add_fees_to_students(request):
    bursar = Bursar.objects.get(admin=request.user.id)
    if request.method == 'POST':
        student_level_id = request.POST.get("student_level")
        student_level = get_object_or_404(StudentLevel, id=student_level_id)

        school_fees = Decimal(request.POST.get("school_fees"))
        extra_classes = Decimal(request.POST.get("extra_classes"))
        stationary = Decimal(request.POST.get("stationary"))
        sport_culture = Decimal(request.POST.get("sport_culture"))
        ict = Decimal(request.POST.get("ict"))
        pta = Decimal(request.POST.get("pta"))
        maintenance = Decimal(request.POST.get("maintenance"))
        light_bill = Decimal(request.POST.get("light_bill"))

        total_fees = school_fees + extra_classes + stationary + sport_culture + ict + pta + maintenance + light_bill

        # Fetch all students in the selected level
        students = Students.objects.filter(student_level_id=student_level)

        # Determine if fees need to be applied to existing students or just saved for the level
        if students.exists():
            # There are students, so update or create fee records for them
            for student in students:
                fee, created = Fees.objects.get_or_create(
                    student_id=student,
                    student_level_id=student_level,
                    defaults={
                        'school_fees': school_fees,
                        'extra_classes': extra_classes,
                        'stationary': stationary,
                        'sport_culture': sport_culture,
                        'ict': ict,
                        'pta': pta,
                        'maintenance': maintenance,
                        'light_bill': light_bill,
                        'total_fees': total_fees,
                        'overall_fees': total_fees,
                        'amount_paid': Decimal('0.00'),
                        'arrears_from_last_term': Decimal('0.00')
                    }
                )
                if not created:
                    # If the fee entry already exists, update the necessary fields
                    fee.school_fees = school_fees
                    fee.extra_classes = extra_classes
                    fee.stationary = stationary
                    fee.sport_culture = sport_culture
                    fee.ict = ict
                    fee.pta = pta
                    fee.maintenance = maintenance
                    fee.light_bill = light_bill
                    fee.total_fees = total_fees
                    #fee.overall_fees = total_fees
                    #fee.amount_paid = amount_paid
                    #fee.arrears_from_last_term = arrears_from_last_term
                    fee.save()
        else:
            # No students in this level, so create or update fees for the level
            fee, created = Fees.objects.get_or_create(
                student_level_id=student_level,
                defaults={
                    'school_fees': school_fees,
                    'extra_classes': extra_classes,
                    'stationary': stationary,
                    'sport_culture': sport_culture,
                    'ict': ict,
                    'pta': pta,
                    'maintenance': maintenance,
                    'light_bill': light_bill,
                    'total_fees': total_fees,
                    'overall_fees': total_fees,
                    'amount_paid': Decimal('0.00'),
                    'arrears_from_last_term': Decimal('0.00')
                }
            )
            if not created:
                # If the fee entry already exists for the level, update the necessary fields
                fee.school_fees = school_fees
                fee.extra_classes = extra_classes
                fee.stationary = stationary
                fee.sport_culture = sport_culture
                fee.ict = ict
                fee.pta = pta
                fee.maintenance = maintenance
                fee.light_bill = light_bill
                fee.total_fees = total_fees
                #fee.overall_fees = total_fees
                #fee.amount_paid = Decimal('0.00')
                fee.arrears_from_last_term = arrears_from_last_term
                fee.save()

        messages.success(request, f"GHS{total_fees} has been successfully applied to all students in {student_level}.")
        return redirect("add_fees_to_students")

    student_levels = StudentLevel.objects.all()
    return render(request, 'bursar_templates/add_fees_to_students.html', {"student_levels": student_levels, 'bursar': bursar})



def update_fees_for_all_levels(request):
    bursar = Bursar.objects.get(admin=request.user.id)
    if request.method == 'POST':
        student_levels = StudentLevel.objects.all()

        for level in student_levels:
            # Get all fee entries for this level
            fees_list = Fees.objects.filter(student_level_id=level.id)
            if not fees_list.exists():
                continue

            # Calculate total fees for this level
            #total_fees = sum(fee.school_fees + fee.extra_classes + fee.stationary + fee.sport_culture + fee.ict + fee.pta + fee.maintenance + fee.light_bill for fee in fees_list)
            # Get the total_fees from the first fee entry in the list
            fee = fees_list.first()
            total_fees = fee.total_fees
            # Update fees for each student in this level
            students = Students.objects.filter(student_level_id=level.id)
            for student in students:
                # Aggregate existing Fees objects
                existing_fees = Fees.objects.filter(
                    student_id=student,
                    student_level_id=level
                )

                if existing_fees.exists():
                    # Update all existing fee entries
                    for fee in existing_fees:
                        fee.total_fees = total_fees
                        fee.arrears_from_last_term = fee.overall_fees
                        if total_fees + fee.arrears_from_last_term < fee.balance_carry_forward:
                            fee.balance_carry_forward -= total_fees + fee.arrears_from_last_term
                            fee.overall_fees = Decimal('0.00')
                            fee.arrears_from_last_term = Decimal('0.00')
                        else:
                            fee.overall_fees = total_fees + fee.arrears_from_last_term - fee.balance_carry_forward
                            fee.balance_carry_forward = Decimal('0.00')
                        fee.save()

                else:
                    # Create a new Fees entry if none exists
                    Fees.objects.create(
                        student_id=student,
                        student_level_id=level,
                        total_fees=total_fees,
                        overall_fees=total_fees,
                        amount_paid=Decimal('0.00'),
                        arrears_from_last_term=Decimal('0.00'),
                        school_fees=Decimal('0.00'),
                        extra_classes=Decimal('0.00'),
                        stationary=Decimal('0.00'),
                        sport_culture=Decimal('0.00'),
                        ict=Decimal('0.00'),
                        pta=Decimal('0.00'),
                        maintenance=Decimal('0.00'),
                        light_bill=Decimal('0.00')
                    )
        messages.success(request, "Next term's fees have been applied to all students.")
        return redirect('bursar_homepage')

    return render(request, 'bursar_templates/bursar_homepage.html', {'bursar': bursar})

