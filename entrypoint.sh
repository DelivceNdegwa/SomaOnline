set -e
cmd="$@"

python manage.py migrate
python manage.py shell -c "
    from django.contrib.auth import get_user_model; 
    User = get_user_model()

    User.objects.create_superuser('courseadmin', 'admin@gmail.com', 'courseadmin2023')
"
python manage.py runserver 0.0.0.0:8000
exec ${cmd}
