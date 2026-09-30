from django.core.exceptions import ValidationError
from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class BaseQuestion(models.Model):
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='%(class)ss',
    )
    text = models.TextField()

    class Meta:
        abstract = True

    def __str__(self):
        return self.text[:80]


class ChoiceQuestion(BaseQuestion):
    def clean(self):
        super().clean()
        options = list(self.answer_options.all()) if self.pk else []
        if len(options) != 4:
            raise ValidationError('A choice question must have exactly four answer options.')
        correct_count = sum(1 for option in options if option.is_correct)
        if correct_count != 1:
            raise ValidationError('A choice question must have exactly one correct answer.')

    def __str__(self):
        return self.text[:80]


class NumericQuestion(BaseQuestion):
    correct_answer = models.IntegerField()

    def __str__(self):
        return self.text[:80]


class AnswerOption(models.Model):
    question = models.ForeignKey(
        ChoiceQuestion,
        on_delete=models.CASCADE,
        related_name='answer_options',
    )
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.text

    def clean(self):
        super().clean()
        if not self.text.strip():
            raise ValidationError({'text': 'Answer text cannot be blank.'})
