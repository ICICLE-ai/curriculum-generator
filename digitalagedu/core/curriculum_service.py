class CurriculumService:
    def __init__(self, config):
        self.config = config

    def build(self):
        """
        Transform validated config into structured curriculum data.
        """

        curriculum = self.config.curriculum

        return {
            "subject": curriculum.subject,
            "grade": curriculum.grade,
            "weeks": curriculum.weeks,
            "topics": [
                {
                    "name": topic.name,
                    "description": topic.description,
                    "project": topic.project,
                    "activities": self._generate_activities(topic.name),
                }
                for topic in curriculum.topics
            ],
        }

    def _generate_activities(self, topic_name: str):
        return [
            f"Discuss the importance of {topic_name}.",
            f"Hands-on activity related to {topic_name}.",
            "Reflection and Q&A session.",
        ]
