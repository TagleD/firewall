import csv
import json

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.views.generic import TemplateView, CreateView, UpdateView
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.utils.translation import gettext_lazy as _
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from account.forms import LoginForm, CustomUserCreationForm, UserForm
from webapp.forms import CSVUploadForm
from webapp.models import Report, Transaction
from webapp.utils import predict_anomaly


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


class UserDetailView(LoginRequiredMixin, View):
    template_name = 'user_detail.html'
    paginate_by = 100  # Количество записей на страницу

    def get(self, request, pk):
        user = get_user_model().objects.get(pk=pk)
        form = CSVUploadForm()
        reports = Report.objects.filter(user=user)

        # Получаем параметры фильтрации
        report_id = request.GET.get('report_id')
        is_fraud = request.GET.get('is_fraud')

        # Фильтруем транзакции для конкретного пользователя
        transactions = Transaction.objects.filter(report__user=user)

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

        for t in transactions:
            for i in range(len(amount_bins) - 1):
                if amount_bins[i] <= t.amount < amount_bins[i + 1]:
                    if t.is_fraud:
                        fraud_amounts[i] += 1
                    else:
                        normal_amounts[i] += 1
                    break

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

        transactions = []
        count = 0
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
            print(f"Транзакция {count} обработана")
            count += 1

        Transaction.objects.bulk_create(transactions)  # Массовая вставка в базу
        return redirect(reverse('user_detail', kwargs={'pk': request.user.pk}))

    # Если форма невалидна, перерендерим страницу с ошибками
    user = get_user_model().objects.get(pk=pk)
    return render(request, self.template_name, {"user_obj": user, "form": form})


class UserUpdateView(LoginRequiredMixin, UpdateView):
    template_name = 'user_update.html'
    model = get_user_model()
    form_class = UserForm

    def get_success_url(self):
        return reverse('user_detail', kwargs={'pk': self.object.pk})
