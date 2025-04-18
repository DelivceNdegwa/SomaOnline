from decimal import Decimal
from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model

from courses import constants
from courses.utils import VideoProcessor

from users.models import Role


User = get_user_model()


class SystemSettings(models.Model):
    one_time_fee = models.DecimalField(decimal_places=1, max_digits=10)
    monthly_fee = models.DecimalField(decimal_places=1, max_digits=10)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        managed = False
        verbose_name_plural = 'SystemSettings'
        ordering = ['-created_at']
        
    # def save(self, *args, **kwargs):
    #         if not self.pk and SystemSettings.objects.exists():
    #             raise ValidationError('There is can be only one SystemSetting instance')
    #         return super(SystemSettings, self).save(*args, **kwargs)
    def save(self, *args, **kwargs):
        if self.id == 1:
            try:
                existing_instance = SystemSettings.objects.get(pk=1)
                for field in self._meta.fields:
                    if field.name != 'id':
                        setattr(existing_instance, field.name, getattr(self, field.name))
                existing_instance.save()
            except SystemSettings.DoesNotExist:
                super().save(*args, **kwargs)
        else:
            super().save(*args, **kwargs)


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    image = models.ImageField(upload_to="categories/", null=True, blank=True)
    short_description = models.CharField(max_length=150, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)
    
    class Meta:
        verbose_name_plural="Categories"
        ordering=['-created_at']
        
    
    def __str__(self):
        return self.name


class Profile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    phone_number = models.IntegerField()
    profile_image = models.ImageField(upload_to='user_profile')
    
    def __str__(self):
        return self.user.username


class Instructor(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    description = models.TextField()
    
    def __str__(self):
        return self.profile


class Course(models.Model):
    title = models.CharField(max_length=100)
    thumbnail_image = models.ImageField(upload_to="courses/", null=True)
    instructor = models.ForeignKey(Instructor, on_delete=models.CASCADE, null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="courses")
    description = models.TextField()
    ready = models.BooleanField(default=False)
    number_of_students = models.IntegerField(default=0)
    monthly_price = models.DecimalField(default=0, max_digits=10, decimal_places=1)
    one_time_price = models.DecimalField(default=0, max_digits=10, decimal_places=1)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class CourseStudent(models.Model):
    course = models.ForeignKey(Course, on_delete=models.PROTECT, related_name="course_students")
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name="student_courses")
    active = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.student.username}:{self.course.title}"


class Section(models.Model):
    title = models.CharField(max_length=100)
    course = models.ForeignKey(Course, on_delete=models.PROTECT, related_name="sections")

    def __str__(self):
        return self.title


class Video(models.Model):
    PROCESSING_STATES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('complete', 'Complete'),
    )

    processing_state = models.CharField(max_length=20, choices=PROCESSING_STATES, default='pending')
    thumbnail = models.ImageField(upload_to='thumbnails/', null=True)
    video_file = models.FileField(upload_to='videos/')
    hls_manifest = models.FileField(upload_to='hls/', blank=True, null=True)
    dash_manifest = models.FileField(upload_to='dash/', blank=True, null=True)
    
    def generate_hls(self):
        video_processor = VideoProcessor(self)
        video_processor.process(constants.HLS)
        return self.hls_manifest.url
    
    def generate_dash(self):
        video_processor = VideoProcessor(self)
        video_processor.process(constants.DASH)
        return self.dash_manifest.url
    
    def __str__(self):
        return f"{self.id}: {self.video_file}"
    
    


class Document(models.Model):
    document_file = models.FileField(upload_to='documents/')

    def __str__(self):
        return str(self.document_file)

class VideoDocument(models.Model):
    title = models.CharField(max_length=100)
    section = models.ForeignKey(Section, on_delete=models.PROTECT, null=True, related_name="lessons")
    video = models.ForeignKey(Video, on_delete=models.CASCADE, null=True, blank=True)
    document = models.ForeignKey(Document, on_delete=models.CASCADE, null=True, blank=True)
    position = models.IntegerField(null=True, blank=True)
    is_ready = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.position}:{self.title}:{self.id}"

class Review(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="reviews")
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reviews")
    rating = models.IntegerField()
    comments = models.TextField()

    def __str__(self):
        return f"Review for {self.course}"


class Question(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="questions")
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name="questions")
    question_text = models.TextField()

    def __str__(self):
        return f"Question for {self.course}"


class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="answers")
    instructor = models.ForeignKey(User, on_delete=models.CASCADE, related_name="answers")
    answer_text = models.TextField()

    def __str__(self):
        return f"Answer for {self.question}"


class Bookmark(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name="bookmarks")
    course = models.ForeignKey(Course, on_delete=models.CASCADE)

    def __str__(self):
        return f"Bookmark for {self.course}"


class Completion(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    section = models.ForeignKey(Section, on_delete=models.CASCADE)
    completion_date = models.DateTimeField()

    def __str__(self):
        return f"Completion for {self.course}"

class Message(models.Model):
    title = models.CharField(max_length=100)
    body = models.TextField()
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return self.title

class Subscription(models.Model):
    SUBSCRIPTION_CHOICES = (
        (constants.ONETIME, 'One time'),
        (constants.MONTHLY, 'Monthly')
    )
    
    PAYMENT_METHOD = (
        (constants.MPESA, 'Mpesa'),
        (constants.PAYPAL, 'Paypal')
    )
    
    PAYMENT_STATUS = (
        (constants.PENDING, "Pending"),
        (constants.COMPLETED, "Completed")
    )
    
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    payment_method = models.CharField(max_length=100, choices=PAYMENT_METHOD, default=constants.MPESA, null=True, blank=True)
    subscription_type = models.CharField(max_length=100, choices=SUBSCRIPTION_CHOICES, default=constants.MONTHLY, null=True, blank=True)  # One-time or Monthly
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    payment_status = models.CharField(choices=PAYMENT_STATUS, max_length=20, default=constants.PENDING)
    
    def __str__(self):
        return f"Subscription for {self.course}"


class Notification(models.Model):
    NOTIFICATION_CATEGORY = (
        (constants.NEW_ENROLLMENT, 'New enrollment'),
        (constants.NEW_MESSAGE, 'New message'),
        (constants.NEW_SIGNUP, 'New signup'),
        (constants.SUBSCRIPTION, 'Subscription'),
        (constants.NEW_COURSE, "New course"),
        (constants.EDITED_COURSE, "Edited course")
    )
    message = models.TextField()
    category = models.CharField(max_length=100, choices=NOTIFICATION_CATEGORY, default=constants.NEW_SIGNUP)
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)
    
    class Meta:
        ordering = ("-created_at",)
    
    def __str__(self):
        return f"{self.category}:{self.message}"
