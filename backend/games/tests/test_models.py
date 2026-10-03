from django.core.exceptions import ValidationError
from django.test import TestCase

from accounts.models import User
from questions.models import AnswerOption, Category, ChoiceQuestion, NumericQuestion
from games.models import Game, GamePlayer, Round, RoundAnswer


class GameModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='alice', email='alice@example.com', password='secret123')
        self.other_user = User.objects.create_user(username='bob', email='bob@example.com', password='secret123')
        self.category = Category.objects.create(name='Science')

    def test_game_and_gameplayer_are_created(self):
        game = Game.objects.create(created_by=self.user)
        player = GamePlayer.objects.create(game=game, user=self.user, player_order=1)

        self.assertEqual(game.status, Game.WAITING)
        self.assertEqual(player.score, 0)
        self.assertTrue(player.is_active)

    def test_gameplayer_is_unique_per_game_and_user(self):
        game = Game.objects.create(created_by=self.user)
        GamePlayer.objects.create(game=game, user=self.user, player_order=1)

        with self.assertRaises(Exception):
            GamePlayer.objects.create(game=game, user=self.user, player_order=2)

    def test_round_requires_one_question_reference_only(self):
        game = Game.objects.create(created_by=self.user)
        choice_question = ChoiceQuestion.objects.create(category=self.category, text='What is 2 + 2?')
        numeric_question = NumericQuestion.objects.create(category=self.category, text='What is 20 + 5?', correct_answer=25)

        round_obj = Round(
            game=game,
            number=1,
            status=Round.OPEN,
            question_type=Round.CHOICE,
            choice_question=choice_question,
            numeric_question=numeric_question,
        )

        with self.assertRaises(ValidationError):
            round_obj.full_clean()

    def test_round_answer_validates_choice_answer(self):
        game = Game.objects.create(created_by=self.user)
        player = GamePlayer.objects.create(game=game, user=self.user, player_order=1)
        question = ChoiceQuestion.objects.create(category=self.category, text='What is 2 + 2?')
        option = AnswerOption.objects.create(question=question, text='4', is_correct=True)
        round_obj = Round.objects.create(
            game=game,
            number=1,
            status=Round.OPEN,
            question_type=Round.CHOICE,
            choice_question=question,
        )

        answer = RoundAnswer(
            round=round_obj,
            player=player,
            selected_option=option,
            numeric_value=None,
        )
        answer.full_clean()

    def test_round_answer_validates_numeric_answer(self):
        game = Game.objects.create(created_by=self.user)
        player = GamePlayer.objects.create(game=game, user=self.user, player_order=1)
        question = NumericQuestion.objects.create(category=self.category, text='What is 12 + 3?', correct_answer=15)
        round_obj = Round.objects.create(
            game=game,
            number=1,
            status=Round.OPEN,
            question_type=Round.NUMERIC,
            numeric_question=question,
        )

        answer = RoundAnswer(
            round=round_obj,
            player=player,
            numeric_value=15,
            selected_option=None,
        )
        answer.full_clean()
