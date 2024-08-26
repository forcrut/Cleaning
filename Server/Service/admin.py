from django.contrib import admin
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied
from .models import CustomUser, StaffUser, UserProfile, StaffStorage, WorkDay, Order
from settings import DAY_CHOICES

# Register your models here.

admin.site.unregister(Group)

# Permissions
class Permissions:
	def has_change_permission(self, request, obj=None) -> bool:
		return request.user.is_staff and request.user.is_superuser

	def has_view_permission(self, request, obj=None) -> bool:
		return request.user.is_superuser

	def has_add_permission(self, request, obj=None) -> bool:
		return request.user.is_staff and request.user.is_superuser

	def has_delete_permission(self, request, obj=None) -> bool:
		return request.user.is_staff and request.user.is_superuser

# Inline модели
class WorkDayInline(admin.TabularInline):
	model = WorkDay
	extra = 0
	min_num = 7
	max_num = 7
	can_delete = False
	fields = ('day', 'is_working')

	def get_formset(self, request, obj=None, **kwargs):
		formset = super().get_formset(request, obj, **kwargs)
		
		class CustomWorkDayFormSet(formset):
			def __init__(self, *args, **kwargs):
				super().__init__(*args, **kwargs)
				for form, day in zip(self.forms, list(DAY_CHOICES.keys())):
					if not form.instance.pk:
						form.fields['day'].disabled = True
						form.initial['day'] = day
		return CustomWorkDayFormSet

class UserProfileInline(admin.TabularInline):
	model = UserProfile
	extra = 0
	min_num = 1
	max_num = 1
	can_delete = False
	fields = ('id', 'phone', 'address')
	readonly_fields = ('phone', 'address')

class StaffStorageInline(admin.TabularInline):
	model = StaffStorage
	extra = 0
	min_num = 1
	max_num = 1
	can_delete = False
	fields = ('id',)

# users
@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin, Permissions):
	list_display = ('last_name', 'first_name', 'surname', 'email', 'is_active', 'creation_date')
	list_filter = ('last_name', 'is_active')
	search_fields = ('last_name', 'email')
	inlines = [UserProfileInline]
	# TODO почему не отображаются подзаголовки
	fieldsets = (
		('Основная информация', {
			'fields': ('last_name', 'first_name', 'surname'),
		}),
		('Бан', {
			'fields': ('is_active',),
		})
	)
	add_fieldsets = (
		('Основная информация', {
			'fields': ('last_name', 'first_name', 'surname'),
		}),
		('Контактная информация', {
			'fields': ('email',)
		})
	)

	def creation_date(self, obj):
		return obj.profile.creation_date

	def get_queryset(self, request):
		"""
		Переопределенный метод get_queryset, чтобы отображать только обычных пользователей.
		"""
		qs = super().get_queryset(request)
		return qs.filter(is_staff=False, is_superuser=False)

	def get_fieldsets(self, request, obj=None) -> tuple:
		if not obj:
			return self.add_fieldsets
		return self.fieldsets

	def save_model(self, request, user, form, change):
		if not change:
			user.is_staff = user.is_superuser = False
		super().save_model(request, user, form, change)

# staffes
@admin.register(StaffUser)
class StaffUserAdmin(admin.ModelAdmin, Permissions):
	list_display = ('username', 'last_name', 'first_name', 'surname', 'email', 'is_staff', 'is_active')
	list_filter = ('username', 'last_name', 'is_staff', 'is_superuser')
	search_fields = ('username', 'email')
	inlines = [StaffStorageInline, WorkDayInline]
	fieldsets = (
		('Основная информация', {
			'fields': ('username', 'last_name', 'first_name', 'surname'),
		}),
		('Дополнительно', {
			'fields': ('is_staff', 'is_active'),
		}),
	)
	add_fieldsets = (
		('Основная информация', {
			'fields': ('username', 'last_name', 'first_name', 'surname'),
		}),
		('Контактная информация', {
			'fields': ('email', 'is_staff')
		}),
	)

	def get_form(self, request, obj=None, **kwargs):
		"""
		Переопределяем метод get_form, чтобы задать is_staff по умолчанию.
		"""
		form = super().get_form(request, obj, **kwargs)
		if obj is None:
			form.base_fields['is_staff'].initial = True
			form.base_fields['is_staff'].disabled = True
		return form

	def get_queryset(self, request):
		"""
		Переопределяем метод get_queryset, чтобы отображать только сотрудников.
		"""
		qs = super().get_queryset(request)
		return qs.filter(is_staff=True, is_superuser=False)

	def get_fieldsets(self, request, obj=None) -> tuple:
		if not obj:
			return self.add_fieldsets
		return self.fieldsets

	def save_formset(self, request, form, formset, change):
		if formset.model == WorkDay and formset.is_valid():
			for form in formset:
				if form.has_changed() or not form.instance.pk:
					form.save()
		super().save_formset(request, form, formset, change)

# WorkDay
@admin.register(WorkDay)
class WorkDayAdmin(admin.ModelAdmin, Permissions):
	list_display = ('staff', 'day', 'is_working')
	list_filter = ('day', 'is_working')
	search_fields = ('staff', 'day')
	ordering = ('staff', 'day')
	readonly_fields = ('staff', 'day')

	def get_queryset(self, request):
		"""
		Переопределяем метод get_queryset, чтобы отображать только выборку с сотрудниками в staff.
		"""
		qs = super().get_queryset(request)
		return qs.filter(staff__is_staff=True, staff__is_superuser=False)

	def formfield_for_foreignkey(self, db_field, request, **kwargs):
		"""
		Для staff нужно отображать только сотрудников
		"""
		if db_field.name == 'staff':
			kwargs['queryset'] = CustomUser.objects.filter(is_staff=True, is_superuser=False)
		return super().formfield_for_foreignkey(db_field, request, **kwargs)

	def has_add_permission(self, request, obj=None) -> bool:
		return False

# Order
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin, Permissions):
	list_display = ('user', 'cleaning_date', 'info', 'price', 'status', 'staff', 'order_time')
	list_filter = ('cleaning_date', 'price', 'status')
	search_fields = ('user', 'staff')
	ordering = ('user', 'cleaning_date', 'price', 'status')
	readonly_fields = ('user', 'order_time', 'status', 'staff')

	def get_queryset(self, request):
		"""
		Переопределяем метод get_queryset, чтобы отображать только выборку с пользователями в user.
		"""
		qs = super().get_queryset(request)
		return qs.filter(user__is_staff=False, user__is_superuser=False)

	def has_add_permission(self, request, obj=None) -> bool:
		return False

# def save_model(self, request, obj, form, change):
# 		if 'password' in form.changed_data:
# 			obj.set_password(form.cleaned_data['password'])
# 		super().save_model(request, obj, form, change)
