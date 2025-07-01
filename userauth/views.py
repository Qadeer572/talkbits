from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import authentication, permissions
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token

from .serializers import UserSerializer,loginSerilaizer,signupSerializers
# Create your views here.
def login_view(request):
    return render(request, 'userauth/login.html')

def signup_view(request):
    return render(request, 'userauth/signup.html')

class UserListView(APIView):
    def get(self,request):
        users = User.objects.all()
        serializer=UserSerializer(users,many=True)
        return Response(serializer.data)

class login(APIView):
    def post(self,requst):
        serializer= loginSerilaizer(data=requst.data)
        if not serializer.is_valid():
            return Response({
                'status': 'error',
                'message': serializer.errors
            }, status=400)
        
        username=serializer.validated_data['username']
        password=serializer.validated_data['password']

        user_obj=authenticate(username=username, password=password)

        if not user_obj:
            return Response({
                'status': 'error',
                'message': 'Invalid credentials'
            }, status=401)
        token, _ = Token.objects.get_or_create(user=user_obj)
        return Response({
            'status': 'success',
            'message': 'Login successful',
            'data' : {'token': str(token)}
        })

class signup(APIView):

    def post(self,request):
        serializer=signupSerializers(data=request.data)

        if not serializer.is_valid():
            return Response({
                'status': 'error',
                'message': serializer.errors
            }, status=400)
        
        firstName=serializer.validated_data['firstName']
        lastName=serializer.validated_data['lastName']
        email=serializer.validated_data['email']
        password=serializer.validated_data['password']
        
        user_obj=User(
            first_name=firstName,
            last_name=lastName,
            email=email,
            username=email
        )
        user_obj.set_password(password)
        user_obj.save()
        return Response({
            'status': 'success',
            'message': 'User created successfully'
        }, status=201)
    