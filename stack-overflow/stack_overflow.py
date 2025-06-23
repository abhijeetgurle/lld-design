from models.post import Question, Answer, Comment
from models.user import User
from strategy.reputation_strategy import ReputationStrategy


class StackOverflow:
    def __init__(self, question_reputation_strategy: ReputationStrategy, answer_reputation_strategy: ReputationStrategy, comment_reputation_strategy: ReputationStrategy):
        self._questions: list[Question] = []
        self._comment_reputation_strategy: ReputationStrategy = comment_reputation_strategy
        self._answer_reputation_strategy: ReputationStrategy = answer_reputation_strategy
        self._question_reputation_strategy: ReputationStrategy = question_reputation_strategy

    def add_question(self, question: Question):
        question.user.increment_reputation(self._question_reputation_strategy.on_post())
        self._questions.append(question)

    def answer_question(self, question: Question, answer: Answer):
        question.add_answer(answer)

    def upvote_question(self, question: Question):
        question.upvote()

    def downvote_question(self, question: Question):
        question.downvote()

    def add_comment_on_question(self, question: Question, comment: Comment):
        question.add_comment(comment)

    def get_questions(self):
        return self._questions

    def get_answers_for_question(self, question: Question):
        return question.answers

    def get_comments_for_question(self, question: Question):
        return question.comments

    def search_question_on_keyword(self, keyword: str) -> list[Question]:
        res = []

        for question in self._questions:
            if question.is_keyword_in_question(keyword):
                res.append(question)

        return res

    def search_question_on_tag(self, tag: str) -> list[Question]:
        res = []
        for question in self._questions:
            if question.is_tag_in_question(tag):
                res.append(question)

        return res

    def search_question_on_user(self, user: User) -> list[Question]:
        res = []
        for question in self._questions:
            if question.is_user_question(user):
                res.append(question)

        return res