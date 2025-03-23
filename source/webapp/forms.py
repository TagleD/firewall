import os

from django import forms

class CSVUploadForm(forms.Form):
    report_name = forms.CharField(
        label="Report title",
        max_length=255
    )
    csv_file = forms.FileField(
        widget=forms.FileInput(
            attrs={
                'accept': '.csv',
                'class': 'custom-file-input',
                'data-text': 'Upload CSV'  # Твой текст
            }
        )
    )

    def clean_csv_file(self):
        file = self.cleaned_data.get("csv_file")

        # Проверяем, что файл имеет расширение .csv
        if file:
            ext = os.path.splitext(file.name)[1].lower()
            if ext != ".csv":
                raise forms.ValidationError("Only CSV files can be uploaded!")

        return file