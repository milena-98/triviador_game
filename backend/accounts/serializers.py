from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import serializers

from .models import Profile

User = get_user_model()


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ('nickname', 'avatar_key')


class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'profile')
        read_only_fields = ('id', 'username', 'email', 'profile')


class RegisterSerializer(serializers.ModelSerializer):
    nickname = serializers.CharField(max_length=30)
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'nickname', 'password', 'password_confirm')

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({'password_confirm': ['Passwords do not match.']})

        if User.objects.filter(username=attrs['username']).exists():
            raise serializers.ValidationError({'username': ['A user with that username already exists.']})

        if User.objects.filter(email=attrs['email']).exists():
            raise serializers.ValidationError({'email': ['User with this email already exists.']})

        if Profile.objects.filter(nickname=attrs['nickname']).exists():
            raise serializers.ValidationError({'nickname': ['This nickname is already taken.']})

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=password,
        )
        Profile.objects.create(user=user, nickname=validated_data['nickname'])
        return user


class ProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ('nickname', 'avatar_key')

    def validate_nickname(self, value):
        if self.instance and Profile.objects.filter(nickname=value).exclude(pk=self.instance.pk).exists():
            raise serializers.ValidationError('This nickname is already taken.')
        return value
