from models.post import Question, Answer, Comment
from models.user import User
from stack_overflow import StackOverflow
from strategy.reputation_strategy import ReputationStrategy

comment_reputation_strategy: ReputationStrategy = ReputationStrategy(1, 1)
answer_reputation_strategy: ReputationStrategy = ReputationStrategy(2, 1)
question_reputation_strategy: ReputationStrategy = ReputationStrategy(3, 1)

if __name__ == "__main__":
    try:
        stack_overflow = StackOverflow(question_reputation_strategy, answer_reputation_strategy, comment_reputation_strategy)

        user = User(name="Abhi", email="abhijeetgurle@gmail.com")

        question = Question(
            contents="What is data structures?",
            user=user,
            tags=["datastructures"],
            question_reputation_strategy=question_reputation_strategy
        )
        stack_overflow.add_question(question)

        print("Questions on stack overflow: ", stack_overflow.get_questions())
        print("Reputation of user: ", user.reputation)

        answer = Answer(
            contents="Data structures are ways to store data in a computer so that it can be used efficiently.",
            user=user,
            answer_reputation_strategy=answer_reputation_strategy
        )
        stack_overflow.answer_question(question, answer)

        print("Answers for question: ", stack_overflow.get_answers_for_question(question))
        print("Reputation of user after answering: ", user.reputation)

        stack_overflow.upvote_question(question)
        print("Reputation of user after upvoting question: ", user.reputation)

        stack_overflow.downvote_question(question)
        print("Reputation of user after downvoting question: ", user.reputation)

        comment = Comment(
            contents="This is a comment on the question.",
            user=user,
            comment_reputation_strategy=comment_reputation_strategy
        )
        question.add_comment(
            comment
        )
        print("Comments for question: ", stack_overflow.get_comments_for_question(question))
        print("Reputation of user after commenting: ", user.reputation)

        question.delete_comment(comment)
        print("Reputation of user after deleting comment: ", user.reputation)

        res = stack_overflow.search_question_on_user(user)
        for q in res:
            print("Questions by user: ", q.content)

    except Exception as error:
        print(error)