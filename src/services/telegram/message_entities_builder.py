class MessageEntitiesBuilder:
    def __init__(self, text="", entities=[]):
        self.text = text
        self.entities = entities

    def add_text(
        self,
        new_text,
        type=None,
        url=None,
        user=None,
        language=None
    ):
        new_entities = self.entities.copy()
        if type is not None:
            new_entity = {
                "type": type,
                "offset": len(self.text),
                "length": len(new_text),
            }
            if url is not None:
                new_entity["url"] = url
            if user is not None:
                new_entity["user"] = user
            if language is not None:
                new_entity["language"] = language
            new_entities.append(new_entity)

        return MessageEntitiesBuilder(
            self.text + new_text,
            new_entities
        )

    def build(self):
        return self.text, self.entities
