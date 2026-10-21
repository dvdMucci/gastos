"""Helpers para datos de gráficos (Chart.js)."""
import json
from collections import defaultdict
from decimal import Decimal

from django.db.models import Sum


DEFAULT_PIE_COLORS = [
    '#e74c3c', '#3498db', '#2ecc71', '#f39c12', '#9b59b6',
    '#1abc9c', '#e67e22', '#34495e', '#e91e63', '#00bcd4',
    '#8bc34a', '#ff5722', '#607d8b', '#673ab7', '#ff9800',
    '#795548', '#009688', '#c0392b', '#2980b9', '#27ae60',
]


def _normalize_color(color, index):
    if color and isinstance(color, str) and color.startswith('#'):
        return color
    return DEFAULT_PIE_COLORS[index % len(DEFAULT_PIE_COLORS)]


def pie_context_from_rows(rows, prefix='pie'):
    """
    rows: iterable de (label, total, color_opcional, category_id_opcional)
    Devuelve keys JSON-safe para el template.
    """
    labels, data, colors, ids = [], [], [], []
    for i, row in enumerate(rows):
        label = row[0]
        total = row[1]
        color = row[2] if len(row) > 2 else None
        cat_id = row[3] if len(row) > 3 else None
        amount = float(total or 0)
        if amount <= 0:
            continue
        labels.append(label)
        data.append(round(amount, 2))
        colors.append(_normalize_color(color, i))
        ids.append(cat_id)

    return {
        f'{prefix}_labels': json.dumps(labels, ensure_ascii=False),
        f'{prefix}_data': json.dumps(data),
        f'{prefix}_colors': json.dumps(colors),
        f'{prefix}_ids': json.dumps(ids),
        f'has_{prefix}': bool(labels),
    }


def expense_category_pie(queryset, prefix='pie'):
    """Torta por categoría a partir de un queryset de Expense."""
    # Limpiar order_by: si no, Django puede romper el GROUP BY y duplicar categorías.
    rows = (
        queryset.order_by()
        .values('category_id', 'category__name', 'category__color')
        .annotate(total=Sum('amount'))
        .order_by('-total')
    )
    return pie_context_from_rows(
        (
            (r['category__name'], r['total'], r['category__color'], r['category_id'])
            for r in rows
        ),
        prefix=prefix,
    )


def subscription_category_pie(subscriptions, rate=None, prefix='pie', active_only=True):
    """
    Torta por categoría usando equivalente mensual en ARS.
    `subscriptions` puede ser queryset o lista.
    """
    totals = defaultdict(lambda: {'total': Decimal('0.00'), 'color': None, 'id': None})
    for sub in subscriptions:
        if active_only and (sub.status != 'active' or not sub.is_active()):
            continue
        monthly = sub.monthly_ars_equivalent(rate=rate)
        key = sub.category.name
        totals[key]['total'] += monthly
        totals[key]['color'] = sub.category.color
        totals[key]['id'] = sub.category_id

    ordered = sorted(totals.items(), key=lambda item: item[1]['total'], reverse=True)
    return pie_context_from_rows(
        ((name, info['total'], info['color'], info['id']) for name, info in ordered),
        prefix=prefix,
    )
