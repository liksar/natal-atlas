import uuid
from django import forms
from .models import City
from .timeutils import resolve_time, TimeError
from .errors import local_error
from django_countries import countries

class ChartForm(forms.Form):
    key = forms.UUIDField(widget=forms.HiddenInput, initial=uuid.uuid4)
    revision = forms.IntegerField(widget=forms.HiddenInput, initial=0)
    internal_name = forms.CharField(max_length=120)
    display_name = forms.CharField(max_length=120, required=False)
    language = forms.ChoiceField(choices=[('uk','Українська'),('en','English'),('ru','Русский')], initial='uk')
    internal_notes = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=False)
    date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    time_mode = forms.ChoiceField(choices=[('exact', 'Exact / Точний / Точное'), ('approximate', 'Approximate / Приблизний / Приблизительное'), ('unknown', 'Unknown / Невідомий / Неизвестное')])
    time = forms.TimeField(required=False, input_formats=['%H:%M'], widget=forms.TimeInput(attrs={'type': 'time'}))
    uncertainty_minutes = forms.IntegerField(required=False, min_value=1, max_value=720)
    city_id = forms.IntegerField(required=False, widget=forms.HiddenInput)
    place = forms.CharField(max_length=200)
    country = forms.ChoiceField(required=False, choices=[('', '—'), *countries])
    latitude = forms.FloatField(min_value=-90, max_value=90)
    longitude = forms.FloatField(min_value=-180, max_value=180)
    timezone = forms.CharField(max_length=64, required=False, initial='Europe/Kyiv')
    fold = forms.TypedChoiceField(required=False, coerce=int, empty_value=None, choices=[('', '—'), ('0', 'First occurrence / Перший / Первый'), ('1', 'Second occurrence / Другий / Второй')])
    manual_offset = forms.IntegerField(required=False, min_value=-840, max_value=840)
    offset_reason = forms.CharField(required=False, max_length=500)
    reason = forms.CharField(max_length=500)
    allow_duplicate = forms.BooleanField(required=False)

    def clean(self):
        d = super().clean()
        if not d.get('date') or not d.get('time_mode'):
            return d
        if not 1900 <= d['date'].year <= 2100:
            self.add_error('date', '1900–2100')
        if d['time_mode'] != 'unknown' and not d.get('time'):
            self.add_error('time', local_error('Required'))
        if d['time_mode'] == 'approximate' and not d.get('uncertainty_minutes'):
            self.add_error('uncertainty_minutes', local_error('Required'))
        if d.get('city_id'):
            try:
                city = City.objects.get(pk=d['city_id'])
                d.update(place=str(city), country=city.country, latitude=city.latitude, longitude=city.longitude, timezone=city.timezone_id, city_source=city.source_id, dataset_version=city.dataset_version)
            except City.DoesNotExist:
                self.add_error('place', local_error('Select a valid city or clear the selection for manual coordinates.'))
        else:
            d['city_source'] = 'manual'
        try:
            resolve_time(d['date'].isoformat(), '12:00' if d['time_mode'] == 'unknown' else (d.get('time').strftime('%H:%M') if d.get('time') else '12:00'), d.get('timezone', ''), d.get('fold'), d.get('manual_offset'), d.get('offset_reason', ''))
        except TimeError as exc:
            self.add_error(None, local_error(str(exc)))
        return d

    def birth_data(self):
        d = self.cleaned_data
        keys = ['time_mode', 'uncertainty_minutes', 'place', 'country', 'latitude', 'longitude', 'timezone', 'fold', 'manual_offset', 'offset_reason', 'city_source', 'dataset_version']
        result = {k: d.get(k) for k in keys}
        result.update(date=d['date'].isoformat(), time=d['time'].strftime('%H:%M') if d.get('time') and d['time_mode'] != 'unknown' else None)
        return result
