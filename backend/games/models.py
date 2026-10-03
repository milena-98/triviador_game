from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class Game(models.Model):
    WAITING = 'waiting'
    IN_PROGRESS = 'in_progress'
    FINISHED = 'finished'
    CANCELLED = 'cancelled'

    STATUS_CHOICES = [
        (WAITING, 'Waiting'),
        (IN_PROGRESS, 'In Progress'),
        (FINISHED, 'Finished'),
        (CANCELLED, 'Cancelled'),
    ]

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='games_created')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=WAITING)
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Game {self.pk}'


class GamePlayer(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='players')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='game_players')
    player_order = models.PositiveSmallIntegerField()
    score = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['game', 'user'], name='unique_game_player'),
            models.UniqueConstraint(fields=['game', 'player_order'], name='unique_game_player_order'),
        ]

    def __str__(self):
        return f'{self.user} in game {self.game_id}'


class Round(models.Model):
    PENDING = 'pending'
    OPEN = 'open'
    CLOSED = 'closed'
    EVALUATED = 'evaluated'

    ROUND_STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (OPEN, 'Open'),
        (CLOSED, 'Closed'),
        (EVALUATED, 'Evaluated'),
    ]

    CHOICE = 'choice'
    NUMERIC = 'numeric'

    QUESTION_TYPE_CHOICES = [
        (CHOICE, 'Choice'),
        (NUMERIC, 'Numeric'),
    ]

    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='rounds')
    number = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=ROUND_STATUS_CHOICES, default=PENDING)
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPE_CHOICES)
    choice_question = models.ForeignKey(
        'questions.ChoiceQuestion',
        on_delete=models.PROTECT,
        related_name='rounds',
        null=True,
        blank=True,
    )
    numeric_question = models.ForeignKey(
        'questions.NumericQuestion',
        on_delete=models.PROTECT,
        related_name='rounds',
        null=True,
        blank=True,
    )
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['game', 'number'], name='unique_round_number_per_game'),
            models.CheckConstraint(
                check=(
                    models.Q(choice_question__isnull=False, numeric_question__isnull=True)
                    | models.Q(choice_question__isnull=True, numeric_question__isnull=False)
                ),
                name='round_has_exactly_one_question',
            ),
        ]

    def clean(self):
        super().clean()
        if self.choice_question and self.numeric_question:
            raise ValidationError('A round cannot reference both choice and numeric questions.')
        if self.numeric_question and self.choice_question:
            raise ValidationError('A round cannot reference both choice and numeric questions.')

        if self.question_type == self.CHOICE and not self.choice_question:
            raise ValidationError({'choice_question': 'Choice rounds must select a choice question.'})
        if self.question_type == self.NUMERIC and not self.numeric_question:
            raise ValidationError({'numeric_question': 'Numeric rounds must select a numeric question.'})

        if self.question_type not in {self.CHOICE, self.NUMERIC}:
            raise ValidationError({'question_type': 'Question type must be choice or numeric.'})

    def __str__(self):
        return f'Round {self.number} for game {self.game_id}'


class RoundAnswer(models.Model):
    round = models.ForeignKey(Round, on_delete=models.CASCADE, related_name='answers')
    player = models.ForeignKey(GamePlayer, on_delete=models.CASCADE, related_name='answers')
    selected_option = models.ForeignKey(
        'questions.AnswerOption',
        on_delete=models.PROTECT,
        related_name='round_answers',
        null=True,
        blank=True,
    )
    numeric_value = models.IntegerField(null=True, blank=True)
    is_correct = models.BooleanField(null=True, blank=True)
    points_awarded = models.IntegerField(default=0)
    submitted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['round', 'player'], name='unique_answer_per_player_per_round'),
        ]

    def clean(self):
        super().clean()
        if self.round.question_type == Round.CHOICE:
            if not self.selected_option:
                raise ValidationError({'selected_option': 'Choice answers require a selected option.'})
            if self.selected_option.question_id != self.round.choice_question_id:
                raise ValidationError({'selected_option': 'Selected option must belong to the current round question.'})
            if self.numeric_value is not None:
                raise ValidationError({'numeric_value': 'Choice answers cannot include a numeric value.'})
        elif self.round.question_type == Round.NUMERIC:
            if self.numeric_value is None:
                raise ValidationError({'numeric_value': 'Numeric answers require a numeric value.'})
            if self.selected_option is not None:
                raise ValidationError({'selected_option': 'Numeric answers cannot include a selected option.'})

    def __str__(self):
        return f'{self.player.user} answer for round {self.round.number}'
