import csv
import json
import string
import random
from ipaddress import ip_address

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum, Count
from django.views import View
from datetime import timedelta, datetime
from django.views.generic import TemplateView, CreateView, UpdateView
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.utils.translation import gettext_lazy as _
from django.shortcuts import redirect, render
from django.utils.timezone import make_aware
from django.urls import reverse, reverse_lazy
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from account.forms import LoginForm, CustomUserCreationForm, UserForm, UserSettingsForm
from webapp.forms import CSVUploadForm
from webapp.models import Report, Transaction
from webapp.utils import predict_anomaly

BASE_DATE = make_aware(datetime(2024, 9, 1, 0, 0, 0))  # 1 сентября 2024, 00:00:00 UTC


class LoginView(TemplateView):
    template_name = 'login.html'
    form_class = LoginForm

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return self.render_to_response({'form': form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)

            if user:
                login(request, user)
                next_url = request.GET.get('next')
                return redirect(next_url or 'user_detail', pk=user.pk)
            else:
                form.add_error(None, _('Invalid username or password'))

        return self.render_to_response({'form': form})


class RegisterView(CreateView):
    template_name = 'registration.html'
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('login')

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            form.save()
            return redirect(self.success_url)
        context = {'form': form}
        return self.render_to_response(context)


def logout_view(request):
    logout(request)
    return redirect('index')


KAZAKHSTAN_CITIES = [
    (43.238949, 76.889709, "Almaty, Kazakhstan"),  # Алматы
    (51.169392, 71.449074, "Astana, Kazakhstan"),  # Астана
    (47.094495, 51.923993, "Atyrau, Kazakhstan"),  # Атырау
    (50.286263, 57.167121, "Aktobe, Kazakhstan"),  # Актобе
    (42.312735, 69.587993, "Shymkent, Kazakhstan"),  # Шымкент
    (49.802063, 73.102086, "Karaganda, Kazakhstan"),  # Караганда
    (45.000000, 78.400000, "Taldykorgan, Kazakhstan"),  # Талдыкорган
    (42.902641, 71.406930, "Taraz, Kazakhstan"),  # Тараз
    (47.100000, 51.900000, "Atyrau, Kazakhstan"),  # Атырау
    (51.723756, 75.315991, "Ekibastuz, Kazakhstan"),  # Экибастуз
    (53.200000, 63.600000, "Kostanay, Kazakhstan"),  # Костанай
    (44.848831, 65.482268, "Kyzylorda, Kazakhstan"),  # Кызылорда
    (47.787863, 67.710307, "Zhezkazgan, Kazakhstan"),  # Жезказган
    (52.288940, 76.973170, "Pavlodar, Kazakhstan"),  # Павлодар
    (52.964381, 63.096894, "Rudny, Kazakhstan"),  # Рудный
    (52.348910, 71.892645, "Stepnogorsk, Kazakhstan"),  # Степногорск
    (54.880880, 69.155785, "Petropavlovsk, Kazakhstan")  # Петропавловск
]


class UserDetailView(LoginRequiredMixin, View):
    template_name = 'dashboard.html'
    paginate_by = 50  # Количество записей на страницу

    def get(self, request, pk):
        user = get_user_model().objects.get(pk=pk)
        self.paginate_by = user.pagination_count
        form = CSVUploadForm()
        reports = Report.objects.filter(user=user)

        # Получаем параметры фильтрации
        report_id = request.GET.get('report_id')
        is_fraud = request.GET.get('is_fraud')
        search_query = request.GET.get('search', "").strip()  # Поисковый запрос

        # Фильтруем транзакции для конкретного пользователя
        transactions = Transaction.objects.filter(report__user=user)

        if search_query:
            transactions = transactions.filter(connect_varchar_id__icontains=search_query)

        if is_fraud == "1":
            transactions = transactions.filter(is_fraud=True)
        elif is_fraud == "0":
            transactions = transactions.filter(is_fraud=False)

        if report_id:
            try:
                report = Report.objects.get(id=report_id, user=user)  # Проверяем, что отчёт принадлежит пользователю
                transactions = transactions.filter(report=report)
            except Report.DoesNotExist:
                transactions = Transaction.objects.none()

        # Подсчет общей стоимости мошеннических операций
        # fraud_total_amount = transactions.filter(is_fraud=True).aggregate(total_amount=Sum("amount"))["total_amount"]
        # fraud_total_amount = round(fraud_total_amount or 0, 1)

        # Подсчет данных для инфографики
        total_count = transactions.count()  # Общее количество
        fraud_count = transactions.filter(is_fraud=True).count()  # Мошеннические
        non_fraud_count = total_count - fraud_count  # Немошеннические
        fraud_percentage = round((fraud_count / total_count * 100),
                                 2) if total_count > 0 else 0  # Процент мошенничества

        # Гистограмма по суммам
        amount_ranges = ["0-20", "20-30", "30-50", "50-100", "100+"]
        amount_bins = [0, 20, 30, 50, 100, float('inf')]
        normal_amounts = [0] * 5
        fraud_amounts = [0] * 5

        # Определяем последний отчет пользователя
        last_report = reports.order_by('-created_at').first()

        if last_report:
            # Считаем прирост процента мошеннических операций после последнего отчета
            transactions_without_last = transactions.exclude(report=last_report)

            # Количество всех транзакций без последнего отчета
            total_count_without_last = transactions_without_last.count()
            fraud_count_without_last = transactions_without_last.filter(is_fraud=True).count()

            # Процент мошенничества без последнего отчета
            fraud_percentage_without_last = round(
                (fraud_count_without_last / total_count_without_last * 100), 2
            ) if total_count_without_last > 0 else 0

        else:
            fraud_percentage_without_last = 0  # Если отчетов нет, считаем, что прироста нет

        # Вычисляем разницу с текущим процентом
        fraud_percentage_change = round(fraud_percentage - fraud_percentage_without_last, 2)

        # for t in transactions:
        #     for i in range(len(amount_bins) - 1):
        #         if amount_bins[i] <= t.amount < amount_bins[i + 1]:
        #             if t.is_fraud:
        #                 fraud_amounts[i] += 1
        #             else:
        #                 normal_amounts[i] += 1
        #             break

        # Пагинация
        paginator = Paginator(transactions, self.paginate_by)
        page = request.GET.get('page')

        try:
            transactions = paginator.page(page)
        except PageNotAnInteger:
            transactions = paginator.page(1)
        except EmptyPage:
            transactions = paginator.page(paginator.num_pages)

        if not report_id:
            report = None

        if last_report:
            new_transactions = Transaction.objects.filter(
                report__user=user,
                report=last_report,
            )
        else:
            new_transactions = Transaction.objects.filter(report__user=user)  # Если отчетов нет, берем все транзакции

        # Количество новых транзакций
        new_transactions_count = new_transactions.count()

        # Количество мошеннических транзакций среди новых
        new_fraud_transactions_count = new_transactions.filter(is_fraud=True).count()

        # Подсчет общей стоимости мошеннических операций в последнем отчете
        # new_fraud_total_amount = new_transactions.filter(is_fraud=True).aggregate(total_amount=Sum("amount"))[
        #     "total_amount"]
        # new_fraud_total_amount = round(new_fraud_total_amount or 0, 1)

        return render(request, self.template_name, {
            "user_obj": user,
            "form": form,
            "reports": reports,
            "transactions": transactions,
            "report": report,
            "current_is_fraud": is_fraud,
            "total_count": total_count,
            "fraud_count": fraud_count,
            "non_fraud_count": non_fraud_count,
            "fraud_percentage": fraud_percentage,
            "amount_bins": json.dumps(amount_ranges),
            "normal_amounts": json.dumps(normal_amounts),
            "fraud_amounts": json.dumps(fraud_amounts),
            # "fraud_total_amount": fraud_total_amount,
            "new_transactions_count": new_transactions_count,
            "new_fraud_transactions_count": new_fraud_transactions_count,
            # "new_fraud_total_amount": new_fraud_total_amount,
            "fraud_percentage_change": fraud_percentage_change,
            "search_query": search_query,
        })

    def post(self, request, pk):
        """ Обрабатываем загрузку CSV """
        form = CSVUploadForm(request.POST, request.FILES)
        if form.is_valid():
            report_name = form.cleaned_data["report_name"]
            csv_file = request.FILES["csv_file"]
            decoded_file = csv_file.read().decode("utf-8").splitlines()
            reader = csv.reader(decoded_file)
            next(reader)  # Пропускаем заголовки CSV

            # Создаём новый отчет
            report = Report.objects.create(user=request.user, name=report_name)

            # Генерируем случайный 3-буквенный префикс
            prefix = ''.join(random.choices(string.ascii_uppercase, k=3))

            transactions = []
            count = 1
            for row in reader:
                time = float(row[0])
                features = list(map(float, row[1:29]))  # V1 - V28
                is_fraud, risk_score, explanation = predict_anomaly(features)  # Анализируем транзакцию
                connect_varchar_id = f"{prefix}-{count:06d}"

                transaction_time = BASE_DATE + timedelta(seconds=time)  # Считаем реальную дату

                # Проверяем наличие координат
                try:
                    latitude = float(row[29]) if row[29] else None
                    longitude = float(row[30]) if row[30] else None
                    location = str(row[31]) if row[31] else None  # Исправлено: `string` → `str`
                except (IndexError, ValueError):
                    latitude, longitude, location = None, None, None

                # Если координаты отсутствуют, выбираем случайный город Казахстана
                if latitude is None or longitude is None or location is None:
                    latitude, longitude, location = random.choice(KAZAKHSTAN_CITIES)  # Берем координаты

                # IP
                try:
                    ip = str(row[32]) if row[32] else None
                except (IndexError, ValueError):
                    ip = None

                # PORT
                try:
                    port = int(row[33]) if row[33] else None
                except (IndexError, ValueError):
                    port = None

                # BYTES
                try:
                    bytes_number = int(row[34]) if row[34] else 0  # bytes по умолчанию 0
                except (IndexError, ValueError):
                    bytes_number = 0

                # CONNECTION TIME
                try:
                    connection_time = int(row[35]) if row[35] else None
                except (IndexError, ValueError):
                    connection_time = None

                # PROTOCOL
                try:
                    protocol = row[36] if row[36] else None
                except (IndexError, ValueError):
                    protocol = None

                transaction = Transaction(
                    connect_varchar_id=connect_varchar_id,  # Формат AAA-000001
                    report=report,
                    time=transaction_time,
                    v1=features[0], v2=features[1], v3=features[2], v4=features[3],
                    v5=features[4], v6=features[5], v7=features[6], v8=features[7],
                    v9=features[8], v10=features[9], v11=features[10], v12=features[11],
                    v13=features[12], v14=features[13], v15=features[14], v16=features[15],
                    v17=features[16], v18=features[17], v19=features[18], v20=features[19],
                    v21=features[20], v22=features[21], v23=features[22], v24=features[23],
                    v25=features[24], v26=features[25], v27=features[26], v28=features[27],
                    is_fraud=is_fraud,
                    explanation=explanation,
                    risk_score=risk_score,
                    latitude=latitude,
                    longitude=longitude,
                    location=location,
                    ip_address=ip,
                    port=port,
                    bytes=bytes_number,
                    connection_time=connection_time,
                    protocol=protocol,
                )
                transactions.append(transaction)
                print(f"Транзакция {count} обработана")
                count += 1

            Transaction.objects.bulk_create(transactions)  # Массовая вставка в базу
            return redirect(reverse('user_detail', kwargs={'pk': request.user.pk}))

        # Если форма невалидна, перерендерим страницу с ошибками
        user = get_user_model().objects.get(pk=pk)
        return render(request, self.template_name, {"user_obj": user, "form": form})


class UserUpdateView(LoginRequiredMixin, UpdateView):
    template_name = 'settings.html'
    model = get_user_model()
    form_class = UserSettingsForm

    def get_success_url(self):
        return reverse('user_detail', kwargs={'pk': self.object.pk})


class UsersStatistics(LoginRequiredMixin, View):
    template_name = 'user_statistics.html'

    def get(self, request):
        User = get_user_model()
        users = User.objects.all()

        users_data = []

        for user in users:
            reports = Report.objects.filter(user=user)
            transactions = Transaction.objects.filter(report__user=user)

            total_count = transactions.count()
            fraud_count = transactions.filter(is_fraud=True).count()
            non_fraud_count = total_count - fraud_count
            fraud_percentage = round((fraud_count / total_count * 100), 2) if total_count > 0 else 0

            # Самое популярное место по транзакциям
            popular_location = transactions.values('location').annotate(loc_count=Count('id')).order_by(
                '-loc_count').first()
            if popular_location:
                popular_location = popular_location['location']
            else:
                popular_location = "Unknown"

            users_data.append({
                'user': user,
                'total_count': total_count,
                'fraud_count': fraud_count,
                'fraud_percentage': fraud_percentage,
                'popular_location': popular_location,
            })

        return render(request, self.template_name, {'users_data': users_data})
