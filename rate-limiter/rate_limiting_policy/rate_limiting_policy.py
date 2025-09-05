from abc import ABC


class RateLimitingPolicy(ABC):
    """
    Base class for rate limiting policies.
    """
    def __init__(self, policy_name: str):
        self.policy_name = policy_name

    def apply_if_enabled(self, entity_data) -> bool:
        """
        Applies the policy if it is enabled.
        :param cluster_data: Data related to the cluster.
        :return: True if the policy is applied, False otherwise.
        """
        raise NotImplementedError("Subclasses should implement this method.")