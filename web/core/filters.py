"""Helpers for building active-filter chips in list views."""


def current_month_bounds():
    """Return (first_day, last_day) of the current month."""
    from datetime import timedelta
    from django.utils import timezone

    today = timezone.now().date()
    first_day = today.replace(day=1)
    if today.month == 12:
        last_day = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
    else:
        last_day = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
    return first_day, last_day


def apply_default_month_to_get(get_data, filter_keys):
    """
    If no real filters are present in GET, inject current-month date bounds
    so the filter form and chips reflect the implicit default period.

    Pass period=all to skip the default month and show all records.
    Returns (data, used_default_month).
    """
    data = get_data.copy()
    if data.get('period') == 'all':
        return data, False

    has_filter = any(data.get(key) not in (None, '') for key in filter_keys)
    if has_filter:
        return data, False

    first_day, last_day = current_month_bounds()
    data['date_from'] = first_day.isoformat()
    data['date_to'] = last_day.isoformat()
    return data, True


def build_active_filter_chips(request, form, field_configs, filter_keys, used_default_month=False):
    """
    Build chips for applied filter fields.

    field_configs: iterable of (field_name, label, formatter_or_None).
    sort_order is omitted when it is the default 'newest'.
    """
    chips = []
    if not form.is_valid():
        return chips

    # Effective querystring: original GET plus injected default dates
    params = request.GET.copy()
    params.pop('period', None)
    if used_default_month:
        first_day, last_day = current_month_bounds()
        params['date_from'] = first_day.isoformat()
        params['date_to'] = last_day.isoformat()

    for field_name, label, formatter in field_configs:
        value = form.cleaned_data.get(field_name)
        if value in (None, ''):
            continue
        if field_name == 'sort_order' and value in (None, '', 'newest'):
            continue

        if formatter:
            display = formatter(value)
        elif hasattr(value, 'strftime'):
            display = value.strftime('%d/%m/%Y')
        else:
            display = str(value)

        remove_params = params.copy()
        remove_params.pop(field_name, None)
        remove_params.pop('page', None)

        still_filtered = any(
            remove_params.get(key) not in (None, '')
            for key in filter_keys
            if key != 'sort_order'
        )
        if still_filtered:
            remove_url = f'?{remove_params.urlencode()}'
        else:
            # Clearing the last meaningful filter → show all periods
            remove_url = '?period=all'

        chips.append({
            'label': label,
            'value': display,
            'remove_url': remove_url,
        })
    return chips
