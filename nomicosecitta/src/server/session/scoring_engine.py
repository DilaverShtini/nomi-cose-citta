from src.common.constants import (
    POINTS_UNIQUE_CATEGORY,
    POINTS_UNIQUE_WORD,
    POINTS_SHARED_WORD,
)


class ScoringEngine:
    """Calculates per-round scores based on validated answers."""

    def calculate_points(self, round_data: dict, validated: dict[str, dict[str, bool]], active_usernames: set[str]) -> dict[str, int]:
        round_scores: dict[str, int] = {user: 0 for user in active_usernames}

        for category, user_valid in validated.items():
            valid_words: dict[str, str] = {
                user: round_data[category][user]["word"]
                for user, is_valid in user_valid.items()
                if is_valid
            }
            num_valid = len(valid_words)

            for user, word in valid_words.items():
                if num_valid == 1:
                    pts = POINTS_UNIQUE_CATEGORY
                else:
                    same_count = sum(1 for w in valid_words.values() if w == word)
                    pts = POINTS_SHARED_WORD if same_count > 1 else POINTS_UNIQUE_WORD

                round_scores[user] = round_scores.get(user, 0) + pts
                round_data[category][user]["score"] = pts

        return round_scores