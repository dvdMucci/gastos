2026-08-03T23:21:59+00:00
Rollback dark mode:
1) cp web/backups/base.html.pre-darkmode web/templates/base.html
2) rm web/static/css/dark-mode.css
3) opcional: quitar STATICFILES_DIRS en settings si no lo usás
