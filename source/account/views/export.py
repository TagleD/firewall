import csv

import openpyxl
from django.contrib.auth import get_user_model
from django.http import HttpResponse

from webapp.models import Transaction, Report


def export_to_excel(request, pk):
    user = get_user_model().objects.get(pk=pk)

    # Получаем параметры фильтрации
    report_id = request.GET.get('report_id')
    is_fraud = request.GET.get('is_fraud')

    # Фильтруем транзакции
    transactions = Transaction.objects.filter(report__user=user)

    if is_fraud == "1":
        transactions = transactions.filter(is_fraud=True)
    elif is_fraud == "0":
        transactions = transactions.filter(is_fraud=False)

    if report_id:
        try:
            report = Report.objects.get(id=report_id, user=user)
            transactions = transactions.filter(report=report)
        except Report.DoesNotExist:
            transactions = Transaction.objects.none()

    # Создаём Excel-файл
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Транзакции"

    # Заголовки
    headers = [
        "ID", "Мошенническая", "Дата", "Сумма", "V1", "V2", "V3", "V4", "V5", "V6", "V7", "V8", "V9", "V10", "V11",
        "V12", "V13", "V14", "V15", "V16", "V17", "V18", "V19", "V20", "V21", "V22", "V23", "V24", "V25", "V26", "V27",
        "V28",
    ]
    ws.append(headers)

    # Данные
    i = 1
    for transaction in transactions:
        ws.append([
            i,
            "Да" if transaction.is_fraud else "Нет", transaction.time, transaction.amount, transaction.v1,
            transaction.v2, transaction.v3, transaction.v4, transaction.v5, transaction.v6, transaction.v7,
            transaction.v8, transaction.v9, transaction.v10, transaction.v11, transaction.v12, transaction.v13,
            transaction.v14, transaction.v15, transaction.v16, transaction.v17, transaction.v18, transaction.v19,
            transaction.v20, transaction.v21, transaction.v22, transaction.v23, transaction.v24, transaction.v25,
            transaction.v26, transaction.v27, transaction.v28,
        ])

        i += 1

    # Создаём HTTP-ответ с файлом
    response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response["Content-Disposition"] = 'attachment; filename="transactions.xlsx"'
    wb.save(response)

    return response


def export_to_csv(request, pk):
    user = get_user_model().objects.get(pk=pk)

    # Получаем параметры фильтрации
    report_id = request.GET.get('report_id')
    is_fraud = request.GET.get('is_fraud')

    # Фильтруем транзакции
    transactions = Transaction.objects.filter(report__user=user)

    if is_fraud == "1":
        transactions = transactions.filter(is_fraud=True)
    elif is_fraud == "0":
        transactions = transactions.filter(is_fraud=False)

    if report_id:
        try:
            report = Report.objects.get(id=report_id, user=user)
            transactions = transactions.filter(report=report)
        except Report.DoesNotExist:
            transactions = Transaction.objects.none()

    # Создаём HTTP-ответ с заголовками
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="transactions.csv"'

    writer = csv.writer(response)

    # Заголовки
    headers = [
        "ID", "Мошенническая", "Дата", "Сумма",
        "V1", "V2", "V3", "V4", "V5", "V6", "V7", "V8", "V9", "V10",
        "V11", "V12", "V13", "V14", "V15", "V16", "V17", "V18", "V19",
        "V20", "V21", "V22", "V23", "V24", "V25", "V26", "V27", "V28",
    ]
    writer.writerow(headers)

    # Данные
    i = 1
    for transaction in transactions:
        writer.writerow([
            i,
            "Да" if transaction.is_fraud else "Нет",
            transaction.time,
            transaction.amount,
            transaction.v1, transaction.v2, transaction.v3, transaction.v4,
            transaction.v5, transaction.v6, transaction.v7, transaction.v8, transaction.v9, transaction.v10,
            transaction.v11, transaction.v12, transaction.v13, transaction.v14, transaction.v15, transaction.v16,
            transaction.v17, transaction.v18, transaction.v19, transaction.v20, transaction.v21, transaction.v22,
            transaction.v23, transaction.v24, transaction.v25, transaction.v26, transaction.v27, transaction.v28
        ])
        i += 1

    return response
