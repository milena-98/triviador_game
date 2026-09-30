from django.core.exceptions import ValidationError
from django.test import TestCase

from questions.models import AnswerOption, Category, ChoiceQuestion, NumericQuestion


class QuestionModelTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Science')

    def test_category_name_is_unique(self):
        with self.assertRaises(Exception):
            Category.objects.create(name='Science')

    def test_choice_question_is_valid_with_four_options_and_one_correct_answer(self):
        question = ChoiceQuestion.objects.create(category=self.category, text='What is 2 + 2?')
        for value, is_correct in [
            ('3', False),
            ('4', True),
            ('5', False),
            ('6', False),
        ]:
            AnswerOption.objects.create(question=question, text=value, is_correct=is_correct)

        question.full_clean()

    def test_choice_question_requires_exactly_four_options(self):
        question = ChoiceQuestion.objects.create(category=self.category, text='Sample question')
        for i, is_correct in enumerate([False, True, False]):
            AnswerOption.objects.create(question=question, text=f'Option {i}', is_correct=is_correct)

        with self.assertRaises(ValidationError):
            question.full_clean()

    def test_choice_question_requires_exactly_one_correct_answer(self):
        question = ChoiceQuestion.objects.create(category=self.category, text='Sample question')
        for i, is_correct in enumerate([True, True, False, False]):
            AnswerOption.objects.create(question=question, text=f'Option {i}', is_correct=is_correct)

        with self.assertRaises(ValidationError):
            question.full_clean()

    def test_numeric_question_requires_integer_answer(self):
        question = NumericQuestion(category=self.category, text='What is 10 + 5?', correct_answer=15)
        question.full_clean()

    def test_deleting_category_with_questions_is_protected(self):
        question = ChoiceQuestion.objects.create(category=self.category, text='Sample question')
        AnswerOption.objects.create(question=question, text='A', is_correct=False)
        AnswerOption.objects.create(question=question, text='B', is_correct=False)
        AnswerOption.objects.create(question=question, text='C', is_correct=False)
        AnswerOption.objects.create(question=question, text='D', is_correct=True)

        with self.assertRaises(Exception):
            self.category.delete()

    def test_deleting_choice_question_removes_related_answer_options(self):
        question = ChoiceQuestion.objects.create(category=self.category, text='Sample question')
        for i, is_correct in enumerate([False, False, False, True]):
            AnswerOption.objects.create(question=question, text=f'Option {i}', is_correct=is_correct)

        question.delete()

        self.assertEqual(AnswerOption.objects.count(), 0)
