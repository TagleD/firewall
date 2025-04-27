import csv
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.urls import reverse

from ..models import Transaction, Report
from ..forms import CSVUploadForm
from ..utils import predict_anomaly


@login_required
def upload_csv(request):
    if request.method == "POST":
        form = CSVUploadForm(request.POST, request.FILES)
        if form.is_valid():
            report_name = form.cleaned_data["report_name"]
            csv_file = request.FILES["csv_file"]
            decoded_file = csv_file.read().decode("utf-8").splitlines()
            reader = csv.reader(decoded_file)
            next(reader)  # Пропускаем заголовки CSV

            # Создаём новый отчет
            report = Report.objects.create(user=request.user, name=report_name)

            transactions = []
            for row in reader:
                time, amount = float(row[0]), float(row[29])
                features = list(map(float, row[1:29]))  # V1 - V28
                is_fraud = predict_anomaly(features)  # Анализируем транзакцию

                transaction = Transaction(
                    report=report,
                    time=time,
                    amount=amount,
                    v1=features[0], v2=features[1], v3=features[2], v4=features[3],
                    v5=features[4], v6=features[5], v7=features[6], v8=features[7],
                    v9=features[8], v10=features[9], v11=features[10], v12=features[11],
                    v13=features[12], v14=features[13], v15=features[14], v16=features[15],
                    v17=features[16], v18=features[17], v19=features[18], v20=features[19],
                    v21=features[20], v22=features[21], v23=features[22], v24=features[23],
                    v25=features[24], v26=features[25], v27=features[26], v28=features[27],
                    is_fraud=is_fraud,
                )
                transactions.append(transaction)

            Transaction.objects.bulk_create(transactions)  # Массовая вставка в базу
            return reverse('user_detail', kwargs={'pk': request.user.pk})

    else:
        form = CSVUploadForm()

    return render(request, "dashboard.html", {"form": form})
