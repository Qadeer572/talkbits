from rest_framework import serializers
from django.contrib.auth.models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name')
class loginSerilaizer(serializers.Serializer):
    username=serializers.CharField()
    password=serializers.CharField()

class signupSerializers(serializers.Serializer):
    firstName=serializers.CharField()
    lastName=serializers.CharField()
    email=serializers.EmailField()
    password=serializers.CharField()