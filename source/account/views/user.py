from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, CreateView, DetailView, UpdateView
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.utils.translation import gettext_lazy as _
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy

from account.forms import LoginForm, CustomUserCreationForm, UserForm


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


class UserDetailView(LoginRequiredMixin, DetailView):
    template_name = 'user_detail.html'
    model = get_user_model()
    context_object_name = 'user_obj'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        return context


class UserUpdateView(LoginRequiredMixin, UpdateView):
    template_name = 'user_update.html'
    model = get_user_model()
    form_class = UserForm

    def get_success_url(self):
        return reverse('user_detail', kwargs={'pk': self.object.pk})
