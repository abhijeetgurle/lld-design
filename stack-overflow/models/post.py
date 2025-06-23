import uuid
from typing import List

from enums.post_type import PostType
from models.user import User
from strategy.reputation_strategy import ReputationStrategy


class Post:
    def __init__(self, contents: str, user: User, type: PostType, reputation_strategy: ReputationStrategy):
        self._id = str(uuid.uuid4())
        self._contents = contents
        self._user = user
        self._type = type
        self._reputation_strategy = reputation_strategy

    @property
    def content(self):
        return self._contents

    @property
    def user(self):
        return self._user

    @property
    def type(self):
        return self._type


class Comment(Post):
    def __init__(self, contents: str, user: User, comment_reputation_strategy: ReputationStrategy):
        super().__init__(contents, user, PostType.COMMENT, comment_reputation_strategy)


class Answer(Post):
    def __init__(self, contents: str, user: User, answer_reputation_strategy: ReputationStrategy):
        super().__init__(contents, user, PostType.ANSWER, answer_reputation_strategy)
        self._votes = 0
        self._comments: List[Comment] = []

    def add_comment(self, comment: Comment):
        comment.user.increment_reputation(self._reputation_strategy.on_post())
        self._comments.append(comment)

    def delete_comment(self, comment: Comment):
        comment.user.decrement_reputation(self._reputation_strategy.on_delete())
        self._comments.remove(comment)

    def upvote(self):
        self._reputation_strategy.on_upvote()
        self._votes += 1

    def downvote(self):
        self._reputation_strategy.on_downvote()
        self._votes -= 1


class Question(Post):
    def __init__(self, contents: str, user: User, tags: List[str], question_reputation_strategy: ReputationStrategy):
        super().__init__(contents, user, PostType.QUESTION, question_reputation_strategy)
        self._votes = 0
        self._tags = tags
        self._answers: list[Answer] = []
        self._comments: list[Comment] = []

    @property
    def answers(self):
        return self._answers

    @property
    def comments(self):
        return self._comments

    def add_answer(self, answer: Answer):
        answer.user.increment_reputation(answer._reputation_strategy.on_post())
        self._answers.append(answer)

    def remove_answer(self, answer: Answer):
        answer.user.decrement_reputation(answer._reputation_strategy.on_delete())
        self._answers.remove(answer)

    def add_comment(self, comment: Comment):
        comment.user.increment_reputation(comment._reputation_strategy.on_post())
        self._comments.append(comment)

    def delete_comment(self, comment: Comment):
        print("comment: ", comment)
        comment.user.decrement_reputation(comment._reputation_strategy.on_delete())
        self._comments.remove(comment)

    def upvote(self):
        self.user.increment_reputation(self._reputation_strategy.on_upvote())
        self._votes += 1

    def downvote(self):
        self.user.decrement_reputation(self._reputation_strategy.on_downvote())
        self._votes -= 1

    def is_keyword_in_question(self, keyword: str) -> bool:
        return keyword in self._contents

    def is_tag_in_question(self, tag: str) -> bool:
        return tag in self._tags

    def is_user_question(self, user: User) -> bool:
        return user.id == self._user.id