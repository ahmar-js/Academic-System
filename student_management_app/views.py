from django.shortcuts import render,HttpResponse, redirect,HttpResponseRedirect
from django.contrib.auth import logout, authenticate, login
from .models import CustomUser, Staffs, Students, AdminHOD, feed, Courses, Subjects, FeedBackStudent, FeedBackStaffs
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import OuterRef, Subquery
from django.http import JsonResponse
def home(request):
	std = Students.objects.all().count()
	stdnt = Students.objects.all()
	crs = Courses.objects.all().count()
	stf = Staffs.objects.all().count()
	ssh = Subjects.objects.all().count()
	fdbkstd_count = FeedBackStudent.objects.all().count()
	fdbkstaff = FeedBackStaffs.objects.all()
	fdbkstudent = FeedBackStudent.objects.all()
	cours = Courses.objects.all()
	posts = feed.objects.all().order_by('-updated_at')
	# print(posts)
	# student_feedback_data = FeedBackStudent.objects.select_related('student_id').all()

	# Subquery to get the latest feedback for each student
	student_feedback_data = []
	for student in stdnt:
		latest_feedback = FeedBackStudent.objects.filter(student_id=student).order_by('-updated_at').first()
		if latest_feedback:
			student_feedback_data.append(latest_feedback)

	# paginator=Paginator(posts,2)
	# # Get Page Number
	# page_number = request.GET.get('page')
	# page_obj = paginator.get_page(page_number)
	# totalpages = page_obj.paginator.num_pages

	# student in each course 
	course_student_count = {}
	for course in cours:
		student_count = Students.objects.filter(course_id=course).count()
		course_student_count[course] = {'student_count': student_count, 'course': course}

	#course paginator	
	paginator = Paginator(list(course_student_count.values()), 3)  # Display 3 courses per page
	page_number = request.GET.get('course_page')
	page_obj = paginator.get_page(page_number)
	totalpages = page_obj.paginator.num_pages

	#feedback paginator
	feedback_paginator = Paginator(student_feedback_data, 3)
	feedback_page_number = request.GET.get('feedback_page')
	feed_back_page_obj = feedback_paginator.get_page(feedback_page_number)


	




    

	context = {
		'course': cours,
		'student':stdnt,
		'fdbk' : fdbkstd_count,
		'all_student_count' : std,
		'all_course_count' : crs,
		'all_staff_count' : stf,
		'all_subject_count' : ssh,
		'feedbackstudent' : fdbkstudent,
		'feedbackstaff' : fdbkstaff,
		'posts':posts,
		'courses': page_obj,
		'feedbacks_student_page': feed_back_page_obj,
		'student_feedback_data': student_feedback_data,
		# 'lastpage': totalpages,
		# 'pagination_list':[i+1 for i in range(totalpages)]
	}

	return render(request, 'home.html', context)

def post(request):
	posts = feed.objects.all().order_by('-updated_at')
	#posts paginator
	posts_paginator = Paginator(posts, 4)
	posts_page_number = request.GET.get('post_page')
	post_page_obj = posts_paginator.get_page(posts_page_number)
	context = {
		'posts': posts,
		'post_page': post_page_obj,
	}
	return render(request, 'post.html', context)

def contact(request):
	return render(request, 'contact.html')


def loginUser(request):
	return render(request, 'login_page.html')

def doLogin(request):
	
	print("here")
	email_id = request.GET.get('email')
	password = request.GET.get('password')
	# user_type = request.GET.get('user_type')
	print(email_id)
	print(password)
	print(request.user)
	if not (email_id and password):
		messages.error(request, "Please provide all the details!!")
		return render(request, 'login_page.html')

	user = CustomUser.objects.filter(email=email_id, password=password).last()
	if not user:
		messages.error(request, 'Invalid Login Credentials!!')
		return render(request, 'login_page.html')

	login(request, user)
	print(request.user)

	if user.user_type == CustomUser.STUDENT:
		return redirect('student_home/')
	elif user.user_type == CustomUser.STAFF:
		return redirect('staff_home/')
	elif user.user_type == CustomUser.admin:
		return redirect('admin_home/')

	return render(request, 'home.html')

	
def registration(request):
	return render(request, 'registration.html')
	

def doRegistration(request):
	first_name = request.GET.get('first_name')
	last_name = request.GET.get('last_name')
	email_id = request.GET.get('email')
	password = request.GET.get('password')
	confirm_password = request.GET.get('confirmPassword')

	print(email_id)
	print(password)
	print(confirm_password)
	print(first_name)
	print(last_name)
	if not (email_id and password and confirm_password):
		messages.error(request, 'Please provide all the details!!')
		return render(request, 'registration.html')
	
	if password != confirm_password:
		messages.error(request, 'Both passwords should match!!')
		return render(request, 'registration.html')

	is_user_exists = CustomUser.objects.filter(email=email_id).exists()

	if is_user_exists:
		messages.error(request, 'User with this email id already exists. Please proceed to login!!')
		return render(request, 'registration.html')

	user_type = get_user_type_from_email(email_id)

	if user_type is None:
		messages.error(request, "Please use valid format for the email id: '<username>.<staff|student|admin>@<domain>'")
		return render(request, 'registration.html')

	username = email_id.split('@')[0].split('.')[0]

	if CustomUser.objects.filter(username=username).exists():
		messages.error(request, 'User with this username already exists. Please use different username')
		return render(request, 'registration.html')

	user = CustomUser()
	user.username = username
	user.email = email_id
	user.password = password
	user.user_type = user_type
	user.first_name = first_name
	user.last_name = last_name
	user.save()
	
	if user_type == CustomUser.STAFF:
		Staffs.objects.create(admin=user)
	elif user_type == CustomUser.STUDENT:
		Students.objects.create(admin=user)
	elif user_type == CustomUser.admin:
		AdminHOD.objects.create(admin=user)
	return render(request, 'login_page.html')

	
def logout_user(request):
	logout(request)
	return HttpResponseRedirect('/')


def get_user_type_from_email(email_id):
	"""
	Returns CustomUser.user_type corresponding to the given email address
	email_id should be in following format:
	'<username>.<staff|student|admin>@<domain>'
	eg.: 'name.staff@jecrc.com'
	"""

	try:
		email_id = email_id.split('@')[0]
		email_user_type = email_id.split('.')[1]
		return CustomUser.EMAIL_TO_USER_TYPE_MAP[email_user_type]
	except:
		return None
