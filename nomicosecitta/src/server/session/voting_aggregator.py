class VotingAggregator:
    """Aggregates peer votes using majority rule with benefit-of-doubt fallback."""

    def aggregate(self, round_data: dict, received_votes: dict) -> dict[str, dict[str, bool]]:
        tally: dict[str, dict[str, list[bool]]] = {
            category: {user: [] for user in users}
            for category, users in round_data.items()
        }

        for voter_votes in received_votes.values():
            for category, user_votes in voter_votes.items():
                if category not in tally:
                    continue
                for target_user, is_valid in user_votes.items():
                    if target_user in tally[category]:
                        tally[category][target_user].append(bool(is_valid))

        result: dict[str, dict[str, bool]] = {}
        for category, users in tally.items():
            result[category] = {}
            for user, vote_list in users.items():
                if round_data[category][user]["status"] == "INVALID":
                    result[category][user] = False
                elif not vote_list:
                    result[category][user] = True
                else:
                    valid_count = sum(1 for v in vote_list if v)
                    result[category][user] = valid_count > len(vote_list) / 2

        return result