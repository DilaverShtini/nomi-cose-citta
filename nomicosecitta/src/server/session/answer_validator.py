class AnswerValidator:
    """Performs syntactic (first-letter) validation on submitted answers."""

    def validate(self, received_answers: dict[str, dict], categories: list[str], letter: str) -> tuple[dict, dict]:
        target = letter.upper()
        round_data: dict = {}
        words_to_vote: dict = {}

        for category in categories:
            round_data[category] = {}
            words_to_vote[category] = {}

            for user, user_words in received_answers.items():
                word = str(user_words.get(category, "")).strip().upper()

                if not word or not word.startswith(target):
                    round_data[category][user] = {
                        "word": word,
                        "status": "INVALID",
                        "score": 0,
                    }
                else:
                    round_data[category][user] = {
                        "word": word,
                        "status": "PENDING_VOTE",
                        "score": 0,
                    }
                    words_to_vote[category][user] = word

        return round_data, words_to_vote